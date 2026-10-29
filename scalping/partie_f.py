#!/usr/bin/env python3
"""Partie F (README.md) : 8 pistes inexplorees sur le NQ (niveaux de la semaine et du mois, pivots, Turtle Soup, volume,
regime du matin, frog in the pan, Open-Drive), meme cadre que la partie E (partie_e.py) : NQ depuis 2011, 1 contrat micro
au prix d'aujourd'hui, frais 1 $ + 1 tick par ordre, 40 jumeaux par permutation et 40 par signe. Ecrit
resultats/f/partie_f.json et resultats/f/partie_f.txt.
Lancer : KB=<branche de recherche extraite> python3 scalping/partie_f.py [--test]"""
import json
import multiprocessing as mp
import os
import sys

import numpy as np
from numba import njit
from scipy.stats import norm

import bruit as B
import commun as K
import partie_e as E

SORTIE = K.ICI / "resultats" / "f"
REGLES = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8"]
NOMS = {"F1": "cassure de la semaine precedente", "F2": "cassure du mois precedent", "F3": "pivots R1/S1, version tendance",
        "F4": "Turtle Soup (extreme de 20 seances)", "F5": "retournement d'un grand mouvement a fort volume",
        "F6": "regime du matin (ratio de variance)", "F7": "frog in the pan (10 h 30)", "F8": "Open-Drive (Dalton)"}
SEUIL_RETENUE = float(norm.ppf(1 - 0.05 / len(REGLES)))
FIN_EXPLO = E.FIN_EXPLO
JUMEAUX = 40


# ----------------------------------------------------------------------------------------------- niveaux
def niveaux(d):
    """Plus haut et plus bas de la semaine et du mois precedents (seances completes, toutes du contrat du jour), et des
    20 seances completes precedentes avec l'age de leur extreme."""
    jours, H, L, cpl, ctr = d["jours"], d["h"], d["l"], d["complete"], d["contrat"]
    S = len(jours)
    hj, lj = H.max(axis=1), L.min(axis=1)
    jd = jours.astype("int64")
    lundi = jours - ((jd + 3) % 7).astype("timedelta64[D]")
    mois = jours.astype("datetime64[M]")
    out = {k: np.full(S, np.nan) for k in ("sh", "sl", "mh", "ml", "h20", "l20")}
    for cle, groupe, mini, h, l in (("s", lundi, 3, "sh", "sl"), ("m", mois, 15, "mh", "ml")):
        index = {}
        for i in np.flatnonzero(cpl):
            index.setdefault(groupe[i], []).append(i)
        for s in range(S):
            prec = groupe[s] - (np.timedelta64(7, "D") if cle == "s" else np.timedelta64(1, "M"))
            ii = index.get(prec, [])
            if len(ii) >= mini and (ctr[ii] == ctr[s]).all():
                out[h][s], out[l][s] = hj[ii].max(), lj[ii].min()
    idx = np.flatnonzero(cpl)
    for j in range(20, len(idx) + 1):
        s_suiv = idx[j] if j < len(idx) else None
        fen = idx[j - 20:j]
        cibles = range(fen[-1] + 1, (s_suiv + 1) if s_suiv is not None else S)
        for s in cibles:
            if not (ctr[fen] == ctr[s]).all():
                continue
            # position 19 = la seance d'avant ; age >= 4 seances <=> position <= 16
            ah, al = 19 - int(np.argmax(hj[fen])), 19 - int(np.argmin(lj[fen]))
            out["h20"][s] = hj[fen].max() if ah >= 3 else np.nan
            out["l20"][s] = lj[fen].min() if al >= 3 else np.nan
    return out


def volume_ref(d):
    """F5 : rendement et volume des fenetres de 30 minutes finissant a 10 h, 10 h 30 ... 15 h 30, et leurs references
    (moyenne du volume sur 14 seances completes precedentes, 80e centile de |r| sur 60)."""
    O, C, V, cpl = d["o"], d["c"], d["v"], d["complete"]
    ks = np.arange(29, 360, 30)
    base = np.where(ks[None, :] == 29, O[:, [0]], C[:, np.maximum(ks - 30, 0)])
    R = C[:, ks] / base - 1
    cv = np.cumsum(V, axis=1)
    VV = cv[:, ks] - np.where(ks >= 30, cv[:, np.maximum(ks - 30, 0)], 0.0)
    vref = np.full(R.shape, np.nan)
    rref = np.full(R.shape, np.nan)
    idx = np.flatnonzero(cpl)
    for t in range(len(cpl)):
        n = int(np.searchsorted(idx, t))                  # seances completes strictement avant t
        if n >= 14:
            vref[t] = VV[idx[n - 14:n]].mean(axis=0)
        if n >= 60:
            rref[t] = np.quantile(np.abs(R[idx[n - 60:n]]), 0.8, axis=0)
    return R, VV, vref, rref


# ----------------------------------------------------------------------------------------------- regles (numba)
@njit(cache=True)
def _cassure(O, C, ok, hh, ll, ech, pt, frais):
    S, N = C.shape
    g, cote, entree = np.full(S, np.nan), np.zeros(S), np.full(S, -1, np.int64)
    for s in range(S):
        if not ok[s] or np.isnan(hh[s]) or np.isnan(ll[s]) or O[s, 0] >= hh[s] or O[s, 0] <= ll[s]:
            continue
        for m in range(0, 330):
            p = 1.0 if C[s, m] > hh[s] else (-1.0 if C[s, m] < ll[s] else 0.0)
            if p != 0:
                g[s] = p * (C[s, 384] - O[s, m + 1]) * pt * ech[s] - frais
                cote[s], entree[s] = p, m + 1
                break
    return g, cote, entree


@njit(cache=True)
def _soup(O, H, L, C, ok, h20, l20, ech, pt, tick, frais):
    S, N = C.shape
    g, cote, entree = np.full(S, np.nan), np.zeros(S), np.full(S, -1, np.int64)
    for s in range(S):
        if not ok[s]:
            continue
        sous, dessus = False, False
        bas, haut = 1e18, -1e18
        for m in range(0, 360):
            bas, haut = min(bas, L[s, m]), max(haut, H[s, m])
            if not np.isnan(l20[s]) and L[s, m] <= l20[s] - tick:
                sous = True
            if not np.isnan(h20[s]) and H[s, m] >= h20[s] + tick:
                dessus = True
            p = 0.0
            if sous and C[s, m] > l20[s]:
                p, stop = 1.0, bas - tick
            elif dessus and C[s, m] < h20[s]:
                p, stop = -1.0, haut + tick
            if p != 0:
                px, sortie = O[s, m + 1], C[s, N - 1]
                for k in range(m + 1, N):
                    if p > 0 and L[s, k] <= stop:
                        sortie = min(O[s, k], stop)
                        break
                    if p < 0 and H[s, k] >= stop:
                        sortie = max(O[s, k], stop)
                        break
                g[s] = p * (sortie - px) * pt * ech[s] - frais
                cote[s], entree[s] = p, m + 1
                break
    return g, cote, entree


@njit(cache=True)
def _volume(O, C, ok, R, VV, vref, rref, ech, pt, frais):
    S, N = C.shape
    g, cote, entree = np.full(S, np.nan), np.zeros(S), np.full(S, -1, np.int64)
    for s in range(S):
        if not ok[s]:
            continue
        tot, nb = 0.0, 0
        for w in range(12):
            k = 29 + 30 * w
            if np.isnan(vref[s, w]) or np.isnan(rref[s, w]) or vref[s, w] <= 0:
                continue
            if VV[s, w] / vref[s, w] >= 1.5 and abs(R[s, w]) >= rref[s, w] and R[s, w] != 0:
                p = -1.0 if R[s, w] > 0 else 1.0
                tot += p * (C[s, min(k + 30, N - 1)] - O[s, k + 1]) * pt * ech[s] - frais
                if nb == 0:
                    cote[s], entree[s] = p, k + 1
                nb += 1
        if nb:
            g[s] = tot
    return g, cote, entree


@njit(cache=True)
def _matin(O, H, L, C, ok, ech, pt, tick, frais, regle):
    """regle 6 : ratio de variance a 12 h ; 7 : frog in the pan a 10 h 30 ; 8 : Open-Drive a 9 h 45."""
    S, N = C.shape
    g, cote, entree = np.full(S, np.nan), np.zeros(S), np.full(S, -1, np.int64)
    for s in range(S):
        if not ok[s]:
            continue
        p, e = 0.0, -1
        if regle == 6:
            r1 = np.empty(150)
            r1[0] = np.log(C[s, 0] / O[s, 0])
            for m in range(1, 150):
                r1[m] = np.log(C[s, m] / C[s, m - 1])
            r10 = np.empty(15)
            for j in range(15):
                r10[j] = np.log(C[s, 10 * j + 9] / (O[s, 0] if j == 0 else C[s, 10 * j - 1]))
            v1 = r1.var()
            if v1 <= 0:
                continue
            vr = r10.var() / (10.0 * v1)
            sens = 1.0 if C[s, 149] > O[s, 0] else (-1.0 if C[s, 149] < O[s, 0] else 0.0)
            p, e = (sens if vr > 1.0 else -sens), 150
        elif regle == 7:
            r = C[s, 59] / O[s, 0] - 1.0
            if r == 0:
                continue
            pos, neg = 0, 0
            prev = O[s, 0]
            for m in range(60):
                if C[s, m] > prev:
                    pos += 1
                elif C[s, m] < prev:
                    neg += 1
                prev = C[s, m]
            sg = 1.0 if r > 0 else -1.0
            if sg * (neg - pos) / 60.0 < 0:
                p, e = sg, 60
        else:
            lo, hi = L[s, 0:15].min(), H[s, 0:15].max()
            if lo >= O[s, 0] - tick and C[s, 14] > O[s, 0]:
                p, e = 1.0, 15
            elif hi <= O[s, 0] + tick and C[s, 14] < O[s, 0]:
                p, e = -1.0, 15
        if p == 0:
            continue
        g[s] = p * (C[s, 384] - O[s, e]) * pt * ech[s] - frais
        cote[s], entree[s] = p, e
    return g, cote, entree


# ----------------------------------------------------------------------------------------------- calcul
def toutes(d):
    O, H, L, C = d["o"], d["h"], d["l"], d["c"]
    ok = d["complete"] & ~d["ech"]
    pt, tick, frais = float(d["pt"]), float(d["tick"]), float(d["frais"])
    ech = float(d["pref"]) / O[:, 0]
    nv = niveaux(d)
    prec = d["prec_meme"]
    a = prec >= 0
    k = np.maximum(prec, 0)
    hp, lp, cp = H[k].max(axis=1), L[k].min(axis=1), C[k, -1]
    piv = (hp + lp + cp) / 3
    r1 = np.where(a, 2 * piv - lp, np.nan)
    s1 = np.where(a, 2 * piv - hp, np.nan)
    R, VV, vref, rref = volume_ref(d)
    out = {"F1": _cassure(O, C, ok, nv["sh"], nv["sl"], ech, pt, frais),
           "F2": _cassure(O, C, ok, nv["mh"], nv["ml"], ech, pt, frais),
           "F3": _cassure(O, C, ok, r1, s1, ech, pt, frais),
           "F4": _soup(O, H, L, C, ok, nv["h20"], nv["l20"], ech, pt, tick, frais),
           "F5": _volume(O, C, ok, R, VV, vref, rref, ech, pt, frais),
           "F6": _matin(O, H, L, C, ok, ech, pt, tick, frais, 6),
           "F7": _matin(O, H, L, C, ok, ech, pt, tick, frais, 7),
           "F8": _matin(O, H, L, C, ok, ech, pt, tick, frais, 8)}
    return out


def stats(g, jours):
    m = np.isfinite(g)
    x, j = g[m], jours[m]
    e, c = x[j <= FIN_EXPLO], x[j > FIN_EXPLO]
    t = lambda y: float(K.t_stat(y)) if len(y) > 2 else float("nan")             # noqa: E731
    return dict(trades=int(len(x)), t=t(x), net=float(x.mean()) if len(x) else float("nan"), total=float(x.sum()),
                n_explo=int(len(e)), moy_explo=float(e.mean()) if len(e) else float("nan"), t_explo=t(e),
                n_controle=int(len(c)), moy_controle=float(c.mean()) if len(c) else float("nan"), t_controle=t(c),
                gagnants=float((x > 0).mean()) if len(x) else float("nan"))


_ETAT = {}


def jumeau(args):
    sorte, k = args
    d = _ETAT["d"]
    dj = B.bruiter(d, (6000 if sorte == "permutation" else 6500) + k, sorte=sorte)
    out = toutes(dj)
    return sorte, {r: stats(out[r][0], d["jours"])["t"] for r in REGLES}


def test(d):
    """(1) Pour des seances tirees au hasard, changer cette seance apres la minute d'entree ne change ni le cote ni la
    minute d'entree ; (2) changer les seances suivantes ne change rien aux seances precedentes."""
    rng = np.random.default_rng(11)
    ref = toutes(d)
    for r in REGLES:
        cote, ent = ref[r][1], ref[r][2]
        for s in rng.choice(np.flatnonzero(ent >= 0), size=min(25, int((ent >= 0).sum())), replace=False):
            d2 = dict(d)
            e = ent[s]
            f = np.exp(rng.normal(0, 0.01, d["c"].shape[1] - e - 1))
            for col in "ohlcv":
                a = d[col].copy()
                a[s, e + 1:] = d[col][s, e + 1:] * (f if col != "v" else rng.uniform(0, 3, len(f)))
                d2[col] = a
            d2["h"][s] = np.maximum(d2["h"][s], np.maximum(d2["o"][s], d2["c"][s]))
            d2["l"][s] = np.minimum(d2["l"][s], np.minimum(d2["o"][s], d2["c"][s]))
            out = toutes(d2)
            assert out[r][1][s] == cote[s] and out[r][2][s] == ent[s], f"{r} seance {s} : depend de l'apres-entree"
    s0 = len(d["jours"]) // 2
    d2 = dict(d)
    for col in "ohlc":
        a = d[col].copy()
        a[s0:] = d[col][s0:] * np.exp(rng.normal(0, 0.01, d[col][s0:].shape))
        d2[col] = a
    d2["h"] = np.maximum(d2["h"], np.maximum(d2["o"], d2["c"]))
    d2["l"] = np.minimum(d2["l"], np.minimum(d2["o"], d2["c"]))
    out = toutes(d2)
    for r in REGLES:
        a, b = ref[r][0][:s0], out[r][0][:s0]
        assert np.array_equal(np.isnan(a), np.isnan(b)) and np.allclose(a[np.isfinite(a)], b[np.isfinite(b)]), r
    print("tests : aucune decision ne depend de l'apres-entree ni des seances suivantes")


def main():
    d = E.jour_nq()
    if "--test" in sys.argv:
        test(d)
        return
    out = toutes(d)
    reel = {r: stats(out[r][0], d["jours"]) for r in REGLES}
    _ETAT["d"] = d
    with mp.get_context("fork").Pool(int(os.getenv("PROCESSUS", "2"))) as pool:
        bruits = pool.map(jumeau, [(s, k) for s in ("permutation", "signe") for k in range(1, JUMEAUX + 1)])
    res = []
    for r in REGLES:
        v = reel[r]
        tb = np.array([b[r] for s, b in bruits if s == "permutation"], float)
        ts = np.array([b[r] for s, b in bruits if s == "signe"], float)
        bat = float(min(np.nanmean(v["t"] > tb), np.nanmean(v["t"] > ts)))
        deux = v["moy_explo"] > 0 and v["moy_controle"] > 0
        retenue = bool(v["t"] >= SEUIL_RETENUE and deux and bat >= 0.95)
        inter = bool(not retenue and v["t"] >= 1.65 and deux and bat >= 0.90)
        res.append(dict(regle=r, nom=NOMS[r], **v, bruit_95=float(np.nanquantile(tb, 0.95)),
                        signe_95=float(np.nanquantile(ts, 0.95)), bat_bruit=bat, retenue=retenue, interessante=inter))
    SORTIE.mkdir(parents=True, exist_ok=True)
    (SORTIE / "partie_f.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    L = [f"Partie F (README.md) : 8 regles, NQ, 1 contrat micro au prix d'aujourd'hui, frais compris. Retenue : t >= "
         f"{SEUIL_RETENUE:.2f}, positive avant et apres 2023, au-dessus de 95 % des jumeaux de chaque bruit ; interessante : "
         "t >= 1,65, positive sur les deux periodes, au-dessus de 90 % des jumeaux.", "",
         "regle  nom                                              trades     t   net/trade  gagnants   t <=2022 (moy.)  "
         "      t >=2023 (moy.)      95e perm 95e signe bat le bruit  verdict"]
    for x in res:
        verdict = "RETENUE" if x["retenue"] else ("interessante" if x["interessante"] else "non")
        L.append(f"{x['regle']:<5}  {x['nom']:<47} {x['trades']:6d} {x['t']:6.2f} {x['net']:8.2f} $ {x['gagnants']:8.0%}  "
                 f"{x['t_explo']:6.2f} ({x['moy_explo']:+7.2f} $)  {x['t_controle']:6.2f} ({x['moy_controle']:+7.2f} $)  "
                 f"   {x['bruit_95']:6.2f} {x['signe_95']:7.2f}   {x['bat_bruit']:6.0%}      {verdict}")
    txt = "\n".join(L)
    (SORTIE / "partie_f.txt").write_text(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
