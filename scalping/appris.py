#!/usr/bin/env python3
"""Partie C (README.md, regles v2) : regression logistique reapprise chaque annee sur les annees precedentes seulement,
signe du mouvement des 15 minutes suivantes, trading de 9 h 45 a 15 h 30 au marche, sortie a 15 minutes ou au stop
de 2 u. Exploration 2017-2022 (Russell 2018-2022, bitcoin 2021-2022), 20 jumeaux par permutation et 20 par signe,
Benjamini-Hochberg sur les 8 marches.
  python3 scalping/appris.py exploration   -> resultats/appris.txt, resultats/appris.json
Le coffre est joue par coffre.py (fonction jouer_appris) avec les memes fonctions."""
import json
import multiprocessing as mp
import sys
from math import erf, sqrt

import numpy as np
from numba import njit

import bruit as B
import commun as K
import donnees as D
import moteur as M

H_CIBLE = 15
T0 = 15                       # 15 minutes apres l'ouverture (9 h 45 pour les indices)
FIN_AVANT = 30                # jusqu'a 30 minutes avant la fin (15 h 30 pour les indices)
SEUIL = 0.55
LAMBDA = 1.0
JUMEAUX = 20                  # par sorte de bruit
GRAINE = 3000
NV = 15


def variables(f):
    """Tableau (S, N, NV) des variables connues a la cloture de chaque minute."""
    O, H, L, C, V = f["O"], f["H"], f["L"], f["C"], f["V"]
    S, N = C.shape
    sp = np.where(f["sigp"] > 0, f["sigp"], np.nan)
    X = np.zeros((S, N, NV))
    lc = np.log(C)
    lo = np.log(O[:, :1])
    for j, k in enumerate((1, 5, 15, 30)):
        base = np.concatenate([np.repeat(lo, k, axis=1), lc[:, :-k]], axis=1) if k < N else np.repeat(lo, N, axis=1)
        X[:, :, j] = (lc - base) / (sp * np.sqrt(k))
    X[:, :, 4] = (C - f["vwap"]) / C / (sp * np.sqrt(30))
    rng_ = f["hh"] - f["ll"]
    X[:, :, 5] = np.where(rng_ > 0, (C - f["ll"]) / np.where(rng_ > 0, rng_, 1) - 0.5, 0.0)
    u = f["sig"] * np.sqrt(15) * C
    for j, lv in enumerate((f["ph"], f["pl"], f["pc"])):
        X[:, :, 6 + j] = np.clip((C - lv[:, None]) / u, -10, 10)
    X[:, :, 9] = np.clip(np.log((V + 1) / (f["vm"] + 1)), -5, 5)
    X[:, :, 10] = np.log(np.clip(f["rg"], 0.05, 20))
    tt = np.arange(N) / N
    X[:, :, 11] = tt
    X[:, :, 12] = tt ** 2
    X[:, :, 13] = np.where(H > L, (C - O) / np.where(H > L, H - L, 1), 0.0)
    if f["X"].shape[0] == S:
        lx = np.log(f["X"])
        base = np.concatenate([np.full((S, 5), np.nan), lx[:, :-5]], axis=1)
        X[:, :, 14] = (lx - base) / (np.where(f["sxp"] > 0, f["sxp"], np.nan) * np.sqrt(5))
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    return np.clip(X, -20, 20)


def cible(f):
    C, O = f["C"], f["O"]
    S, N = C.shape
    y = np.full((S, N), np.nan)
    t = np.arange(N - H_CIBLE)
    y[:, t] = np.sign(np.log(C[:, t + H_CIBLE] / O[:, t + 1]))
    return y


def apprendre(X, y, lam=LAMBDA, iters=25):
    """Regression logistique L2 (constante non penalisee) par Newton. Renvoie (moyennes, ecarts, poids)."""
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd[sd == 0] = 1.0
    Z = np.c_[np.ones(len(X)), (X - mu) / sd]
    yy = (y > 0).astype(float)
    w = np.zeros(Z.shape[1])
    P = np.eye(Z.shape[1]) * lam
    P[0, 0] = 0.0
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(Z @ w, -30, 30)))
        g = Z.T @ (p - yy) + P @ w
        Hs = (Z * (p * (1 - p))[:, None]).T @ Z + P
        pas = np.linalg.solve(Hs, g)
        w -= pas
        if np.abs(pas).max() < 1e-8:
            break
    return mu, sd, w


def probas(X, modele):
    mu, sd, w = modele
    z = w[0] + ((X - mu) / sd) @ w[1:]
    return 1 / (1 + np.exp(-np.clip(z, -30, 30)))


@njit(cache=True)
def executer(p, s0, s1, O, H, L, C, sig, jouable, echelle, pt, tick, pas, frais, seuil, t0, t1, hmax, journal):
    """Trading de la partie C sur [s0, s1) : sans position, achat au marche a t + 1 si p >= seuil, vente si
    p <= 1 - seuil (t + 1 entre t0 et t1) ; stop 2 u (ordre le plus defavorable) ; sortie a la cloture de t_entree + hmax - 1."""
    S, N = C.shape
    gain = np.zeros(s1 - s0)
    ntr = 0
    nwin = 0
    nj = 0
    h = 0.5 * pas
    for s in range(s0, s1):
        if not jouable[s]:
            gain[s - s0] = np.nan
            continue
        pos = 0
        attente = 0
        stp = 0.0
        ent = 0.0
        e = 0
        ds = 0.0
        for t in range(N):
            if attente != 0:
                pos = attente
                ent = O[s, t]
                e = t
                stp = M._vers_perte(ent - pos * ds, pos, tick)       # stop au tick, vers la perte
                attente = 0
            if pos != 0:
                sortie = np.nan
                if pos == 1:
                    if t > e and O[s, t] <= stp + h:
                        sortie = O[s, t]
                    elif L[s, t] <= stp + h:
                        sortie = stp
                else:
                    if t > e and O[s, t] >= stp - h:
                        sortie = O[s, t]
                    elif H[s, t] >= stp - h:
                        sortie = stp
                if not np.isfinite(sortie) and (t >= e + hmax - 1 or t == N - 1):
                    sortie = C[s, t]
                if np.isfinite(sortie):
                    g_ = pos * (sortie - ent) * pt * echelle[s] - frais
                    gain[s - s0] += g_
                    ntr += 1
                    if g_ > 0:
                        nwin += 1
                    if journal.shape[0] > 1 and nj < journal.shape[0]:
                        journal[nj, 0] = s
                        journal[nj, 1] = e
                        journal[nj, 2] = t
                        journal[nj, 3] = pos
                        journal[nj, 4] = ent
                        journal[nj, 5] = sortie
                        nj += 1
                    pos = 0
            if pos != 0 or t + 1 < t0 or t + 1 > t1 or t + 1 > N - 3:
                continue
            q = p[s, t]
            if not np.isfinite(q):
                continue
            d = 1 if q >= seuil else (-1 if q <= 1.0 - seuil else 0)
            if d != 0:
                attente = d
                ds = max(2.0 * sig[s, t] * np.sqrt(15.0) * C[s, t], 2.0 * tick)
    return gain, ntr, nwin


def walk_forward(f, annees, premiere_annee):
    """Probabilites (S, N) pour les annees `annees`, chaque annee apprise sur [premiere_annee, annee)."""
    X = variables(f)
    y = cible(f)
    S, N = f["C"].shape
    ans = f["jours"].astype("datetime64[Y]").astype(int) + 1970
    p = np.full((S, N), np.nan)
    tgrid = np.arange(T0 - 1, N - FIN_AVANT, 5)        # minutes de decision t (entree a t + 1, de T0 a N - 30)
    for a in annees:
        app = np.flatnonzero(f["jouable"] & (ans >= premiere_annee) & (ans < a))
        Xa = X[app][:, tgrid].reshape(-1, NV)
        ya = y[app][:, tgrid].reshape(-1)
        ok = np.isfinite(ya) & (ya != 0)
        if ok.sum() < 1000:
            continue
        modele = apprendre(Xa[ok], ya[ok])
        jo = np.flatnonzero(ans == a)
        p[jo] = probas(X[jo].reshape(-1, NV), modele).reshape(len(jo), N)
    return p


def resultat(f, p, annees):
    ans = f["jours"].astype("datetime64[Y]").astype(int) + 1970
    s0 = int(np.flatnonzero(ans >= annees[0])[0])
    s1 = int(np.flatnonzero(ans <= annees[-1])[-1]) + 1
    jr = np.zeros((1, 6))
    gain, n, w = executer(p, s0, s1, f["O"], f["H"], f["L"], f["C"], f["sig"], f["jouable"], f["echelle"], f["pt"],
                          f["tick"], f["pas"], f["frais"], SEUIL, T0, f["C"].shape[1] - FIN_AVANT, H_CIBLE, jr)
    x = gain[np.isfinite(gain)]
    return dict(t=K.t_stat(x), trades=int(n), net_trade=float(np.nansum(gain) / max(n, 1)), gagnants=float(w / max(n, 1)),
                total=float(np.nansum(gain)))


def periode(marche):
    if marche == "BTC":                       # version 3 : seances completes rares avant 2020
        return list(range(2021, 2023)), 2020
    if marche == "RTY":                       # version 4 : donnees depuis juillet 2017, pas de modele 2017
        return list(range(2018, 2023)), 2017
    return list(range(2017, 2023)), 2016


def charger(marche, graine=None, sorte="permutation", quoi="recherche"):
    d = dict(np.load(K.CACHE / f"{quoi}_{marche}.npz"))
    if quoi == "recherche":
        assert d["jours"].max() <= K.FIN_RECHERCHE
    if graine is not None:
        if marche in K.AUTRE_INDICE:
            q = dict(np.load(K.CACHE / f"{quoi}_NQ.npz"))
            e = dict(np.load(K.CACHE / f"{quoi}_ES.npz"))
            q, e = B.bruiter_paire(q, e, graine, sorte=sorte)
            q["autre_c"] = D.aligner_autre(q, e)
            e["autre_c"] = D.aligner_autre(e, q)
            d = q if marche == "NQ" else e
        else:
            d = B.bruiter(d, graine, sorte=sorte)
    return d


def tache(args):
    marche, graine, sorte = args
    f = M.indicateurs(charger(marche, graine, sorte))
    annees, prem = periode(marche)
    return marche, graine, sorte, resultat(f, walk_forward(f, annees, prem), annees)


def exploration():
    marches = list(K.MARCHES)
    taches = [(m, None, "reel") for m in marches] + [(m, GRAINE + (0 if s == "permutation" else 500) + k, s)
                                                     for m in marches for s in ("permutation", "signe")
                                                     for k in range(1, JUMEAUX + 1)]
    with mp.get_context("fork").Pool(4) as pool:
        res = pool.map(tache, taches)
    reel = {m: r for m, g, s, r in res if g is None}
    tests = []
    for m in marches:
        r = reel[m]
        tb = np.array([x["t"] for mm, g, s, x in res if mm == m and s == "permutation"])
        ts = np.array([x["t"] for mm, g, s, x in res if mm == m and s == "signe"])
        tests.append(dict(marche=m, p=0.5 * (1 - erf(r["t"] / sqrt(2))), bruit_95=float(np.quantile(tb, 0.95)),
                          signe_95=float(np.quantile(ts, 0.95)),
                          bat_bruit=float(min(np.mean(r["t"] > tb), np.mean(r["t"] > ts))), **r))
    ordre = np.argsort([x["p"] for x in tests])
    kmax = 0
    for rang, i in enumerate(ordre, start=1):
        if tests[i]["p"] <= 0.10 * rang / len(tests):
            kmax = rang
    for rang, i in enumerate(ordre, start=1):
        tests[i]["bh"] = rang <= kmax
    for x in tests:
        x["survivante"] = bool(x["t"] >= 2 and x["bh"] and x["bat_bruit"] >= 0.95)
    out = K.ICI / "resultats"
    out.mkdir(exist_ok=True)
    (out / "appris.json").write_text(json.dumps(tests, indent=1))
    L = ["Partie C, modele appris chaque annee sur le passe, exploration 2017-2022 (Russell 2018-2022, bitcoin "
         "2021-2022), 20 jumeaux par "
         "permutation et 20 par signe, Benjamini-Hochberg a 10 % sur 8 marches", "",
         "marche  trades    t    net/trade  gagnants  95e perm. 95e signe  bat le bruit  BH  survivante"]
    for x in tests:
        L.append(f"{x['marche']:<6} {x['trades']:7d} {x['t']:6.2f} {x['net_trade']:9.2f} $ {x['gagnants']:7.0%} "
                 f"{x['bruit_95']:9.2f} {x['signe_95']:9.2f} {x['bat_bruit']:10.0%}   {'oui' if x['bh'] else 'non'}  "
                 f"{'OUI' if x['survivante'] else 'non'}")
    txt = "\n".join(L)
    (out / "appris.txt").write_text(txt + "\n")
    print(txt)


if __name__ == "__main__":
    {"exploration": exploration}[sys.argv[1]]()
