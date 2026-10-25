#!/usr/bin/env python3
"""Partie E (README.md) : les 10 regles issues des 5 agents (flux institutionnels, recherche, praticiens, fonds et HFT,
audit), sur le NQ depuis 2011, 40 jumeaux de bruit par permutation et 40 par signe. Ecrit resultats/e/partie_e.json et
resultats/e/partie_e.txt.

Conventions (celles de la machine) : signal a la cloture d'une minute (ou d'une barre de 5 minutes la nuit), entree a
l'ouverture suivante ; ordre stop rempli a son niveau, ou a l'ouverture si elle le depasse ; objectif limite rempli
seulement si le prix le traverse d'un tick (ou a l'ouverture si elle est deja au-dela) ; dans une meme minute, stop avant
objectif ; 1 contrat micro, gain au prix d'aujourd'hui (x pref / ouverture de la seance), frais 1 $ + 1 tick par ordre.
Lancer : KB=<branche de recherche extraite> DONNEES_LIBRES=<donnees_libres> python3 scalping/partie_e.py [--test]"""
import json
import multiprocessing as mp
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit
from scipy.stats import norm

import bruit as B
import commun as K
import donnees as D

LIBRES = Path(os.getenv("DONNEES_LIBRES", str(K.KB.parent / "donnees_libres")))
SORTIE = K.ICI / "resultats" / "e"
REGLES = ["E1", "E1b", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9"]
NOMS = {"E1": "gamma d'heure en heure (contre si GEX > 0, avec si < 0)", "E1b": "gamma en fin de seance (contre a 15 h 30 si GEX > 0)",
        "E2": "conference de presse de la Fed (suivre 14 h - 14 h 30)", "E3": "retournement de l'annonce de la Fed",
        "E4": "reequilibrage 60/40 de fin de mois", "E5": "nuit avant NFP et ISM (achat)",
        "E6": "derive de 2 h a 3 h apres une fin de seance vendeuse", "E7": "regle des 80 % (Market Profile)",
        "E8": "Oops de Larry Williams", "E9": "cassure des extremes de la nuit"}
DEBUT = {"E1": "2011-05-01", "E1b": "2011-05-01", "E2": "2013-01-01", "E3": "2013-01-01", "E4": "2016-01-01"}
PUBLICATION = {"E1": "2024-01-01", "E1b": "2022-01-01", "E2": "2020-06-01", "E3": "2022-01-01", "E4": "2025-03-01",
               "E5": "2019-06-01", "E6": "2020-02-01"}
FIN_EXPLO = np.datetime64("2022-12-31")
JUMEAUX = 40
SEUIL_RETENUE = float(norm.ppf(1 - 0.05 / len(REGLES)))
NUIT = "NQ"


# ----------------------------------------------------------------------------------------------- donnees
def jour_nq():
    """Minutes du NQ depuis 2011 (meme fichier et meme construction que la machine, debut avance)."""
    f = K.CACHE / "e_NQ.npz"
    if f.exists():
        return dict(np.load(f))
    ancien = K.DEBUT_DONNEES
    K.DEBUT_DONNEES = np.datetime64("2011-01-01")
    try:
        d = D.minutes("NQ")
    finally:
        K.DEBUT_DONNEES = ancien
    np.savez_compressed(f, **d)
    return d


def nuit_nq():
    return dict(np.load(K.CACHE / f"complet_nuit_{NUIT}.npz"))


def gex():
    g = pd.read_csv(K.KB / "evolution2" / "donnees" / "dix_gex.csv", usecols=["date", "gex"])
    return g["date"].to_numpy().astype("datetime64[D]"), g["gex"].to_numpy(float)


def fomc():
    sys.path.insert(0, str(K.KB / "fonds"))
    import fomc as F                                                              # noqa: E402
    return np.array(F.annonces().values.astype("datetime64[D]"))


def clotures_etf(nom):
    """Cloture de 16 h (barre de 15 h 55) de chaque seance, ETF en 5 minutes (Alpaca)."""
    b = pd.read_csv(LIBRES / "etf_5min" / f"{nom}.csv.gz", usecols=["t", "c"])
    b = b[b["t"].str[11:16] == "15:55"]
    return pd.Series(b["c"].to_numpy(float), index=pd.to_datetime(b["t"].str[:10]).values.astype("datetime64[D]"))


def dates_nfp(annees):
    """Regle du BLS : rapport publie le 3e vendredi qui suit la semaine (dimanche - samedi) contenant le 12 du mois."""
    out = []
    for a in annees:
        for m in range(1, 13):
            d12 = pd.Timestamp(a, m, 12)
            samedi = d12 + pd.Timedelta(days=(5 - d12.weekday()) % 7)
            out.append((samedi + pd.Timedelta(days=20)).to_datetime64().astype("datetime64[D]"))
    return np.array(sorted(out))


def contexte(d, n, g_dates, g_val, fomc_dates, spy, ief):
    """Informations exogenes (connues avant le trade) et correspondances jour / nuit, calculees une fois."""
    jours = d["jours"]
    S = len(jours)
    ctx = {}
    # GEX de la veille : derniere valeur publiee avant le jour de la seance (au plus 5 jours avant)
    i = np.searchsorted(g_dates, jours) - 1
    ok = (i >= 0) & ((jours - g_dates[np.maximum(i, 0)]).astype(int) <= 5)
    ctx["gex"] = np.where(ok, g_val[np.maximum(i, 0)], np.nan)
    assert (g_dates[np.maximum(i, 0)][ok] < jours[ok]).all()
    an = jours.astype("datetime64[Y]").astype(int) + 1970
    mois = jours.astype("datetime64[M]").astype(int) % 12 + 1
    est_fomc = np.isin(jours, fomc_dates)
    ctx["fomc_conf"] = est_fomc & (((an >= 2013) & (an <= 2018) & np.isin(mois, [3, 6, 9, 12])) | (an >= 2019))
    ctx["fomc_tout"] = est_fomc & (an >= 2013)
    # E4 : signal du lendemain, a partir des 5 dernieres seances de chaque mois (calendrier des seances du NQ)
    sig = np.zeros(S)
    mm = jours.astype("datetime64[M]")
    for s in range(S - 1):
        if mm[s] == mm[-1]:                       # mois en cours a la fin des donnees : ses 5 derniers jours sont inconnus
            continue
        fin_mois = np.flatnonzero(mm == mm[s])
        if s not in fin_mois[-5:]:
            continue
        avant = jours[mm < mm[s]]
        if not len(avant):
            continue
        j0, j1 = avant[-1], jours[s]
        if j0 in spy.index and j1 in spy.index and j0 in ief.index and j1 in ief.index:
            ra, ro = spy[j1] / spy[j0] - 1, ief[j1] / ief[j0] - 1
            w = 0.6 * (1 + ra) / (0.6 * (1 + ra) + 0.4 * (1 + ro))
            sig[s + 1] = -1.0 if w > 0.6 else (1.0 if w < 0.6 else 0.0)
    ctx["e4"] = sig
    # nuits : sortie de E5 (8 h 30 pour le NFP, 9 h 20 pour l'ISM), seance de jour precedente (E6), nuit du matin (E9)
    nj = n["jours"]
    nfp = dates_nfp(range(2011, 2028))
    premier = np.array([jours[mm == m][0] for m in np.unique(mm)])                 # 1er jour de seance du mois
    sortie = np.full(len(nj), -1, np.int64)
    sortie[np.isin(nj, premier)] = 183
    sortie[np.isin(nj, nfp)] = 173
    ctx["e5_sortie"] = sortie
    ip = np.searchsorted(jours, nj) - 1                                           # seance de jour qui precede la nuit
    ctx["nuit_prec_jour"] = np.where(ip >= 0, ip, -1)
    k = np.searchsorted(nj, jours)
    meme = (k < len(nj)) & (nj[np.minimum(k, len(nj) - 1)] == jours)
    ctx["jour_nuit"] = np.where(meme, k, -1)
    return ctx


# ----------------------------------------------------------------------------------------------- regles (numba)
@njit(cache=True)
def _signe(x):
    return 1.0 if x > 0 else (-1.0 if x < 0 else 0.0)


@njit(cache=True)
def _e1(O, C, ok, gexv, ech, pt, frais, pref, fin_seule):
    S, N = C.shape
    g = np.full(S, np.nan)
    cote = np.zeros(S)
    entree = np.full(S, -1, np.int64)
    for s in range(S):
        if not ok[s] or np.isnan(gexv[s]):
            continue
        tot, nb = 0.0, 0
        for k in (59, 119, 179, 239, 299, 359):
            if fin_seule and k != 359:
                continue
            r = C[s, k] / (O[s, 0] if k == 59 else C[s, k - 60]) - 1.0
            p = -_signe(r) if gexv[s] > 0 else _signe(r)
            if p == 0:
                continue
            x = min(k + 60, N - 1)
            tot += p * (C[s, x] - O[s, k + 1]) * pt * ech[s] - frais
            if nb == 0:
                cote[s], entree[s] = p, k + 1
            nb += 1
        if nb:
            g[s] = tot
    return g, cote, entree


@njit(cache=True)
def _e1b(O, C, ok, gexv, prec, ech, pt, frais):
    S, N = C.shape
    g = np.full(S, np.nan)
    cote = np.zeros(S)
    entree = np.full(S, -1, np.int64)
    for s in range(S):
        if not ok[s] or np.isnan(gexv[s]) or gexv[s] <= 0 or prec[s] < 0:
            continue
        p = -_signe(C[s, 359] / C[prec[s], N - 1] - 1.0)
        if p == 0:
            continue
        g[s] = p * (C[s, N - 1] - O[s, 360]) * pt * ech[s] - frais
        cote[s], entree[s] = p, 360
    return g, cote, entree


@njit(cache=True)
def _fenetre(O, C, ok, quand, prec, ech, pt, frais, mode):
    """mode 2 : E2 (suivre 14 h - 14 h 30, de 14 h 30 a 15 h 30) ; mode 3 : E3 (contre 24 h, de 13 h 50 a 16 h) ;
    mode 4 : E4 (signal donne, de 9 h 30 a 16 h)."""
    S, N = C.shape
    g = np.full(S, np.nan)
    cote = np.zeros(S)
    entree = np.full(S, -1, np.int64)
    for s in range(S):
        if not ok[s] or quand[s] == 0:
            continue
        if mode == 2:
            p, e, x = _signe(C[s, 299] / C[s, 269] - 1.0), 300, 359
        elif mode == 3:
            if prec[s] < 0:
                continue
            p, e, x = -_signe(C[s, 259] / C[prec[s], 259] - 1.0), 260, N - 1
        else:
            p, e, x = quand[s], 0, N - 1
        if p == 0:
            continue
        g[s] = p * (C[s, x] - O[s, e]) * pt * ech[s] - frais
        cote[s], entree[s] = p, e
    return g, cote, entree


@njit(cache=True)
def _nuit(On, Cn, okn, e, x, ech, pt, frais):
    """Achat a l'ouverture de la barre e, vente a la cloture de la barre x[n] (x < 0 : pas de trade)."""
    S = Cn.shape[0]
    g = np.full(S, np.nan)
    cote = np.zeros(S)
    entree = np.full(S, -1, np.int64)
    for s in range(S):
        if not okn[s] or x[s] < 0:
            continue
        g[s] = (Cn[s, x[s]] - On[s, e[s]]) * pt * ech[s] - frais
        cote[s], entree[s] = 1.0, e[s]
    return g, cote, entree


@njit(cache=True)
def _e7(O, H, L, C, ok, prec, ech, pt, tick, frais):
    S, N = C.shape
    g = np.full(S, np.nan)
    cote = np.zeros(S)
    entree = np.full(S, -1, np.int64)
    for s in range(S):
        p0 = prec[s]
        if not ok[s] or p0 < 0:
            continue
        b = 0.0002 * C[p0, N - 1]
        lo_b = int(np.floor(L[p0].min() / b))
        hi_b = int(np.floor(H[p0].max() / b))
        nb = hi_b - lo_b + 1
        cnt = np.zeros(nb)
        for i in range(13):
            a = int(np.floor(L[p0, 30 * i:30 * i + 30].min() / b)) - lo_b
            z = int(np.floor(H[p0, 30 * i:30 * i + 30].max() / b)) - lo_b
            cnt[a:z + 1] += 1.0
        mx = cnt.max()
        centre = (nb - 1) / 2.0
        poc, meilleur = 0, 1e18
        for j in range(nb):                                  # POC : la case la plus remplie, la plus proche du centre
            if cnt[j] == mx and abs(j - centre) < meilleur:
                poc, meilleur = j, abs(j - centre)
        cible, acc, lo, hi = 0.7 * cnt.sum(), cnt[poc], poc, poc
        while acc < cible:
            up = cnt[hi + 1] if hi + 1 < nb else -1.0
            dn = cnt[lo - 1] if lo - 1 >= 0 else -1.0
            if up >= dn:
                hi += 1
                acc += up
            else:
                lo -= 1
                acc += dn
        vah, val = (hi + lo_b + 1) * b, (lo + lo_b) * b
        if O[s, 0] > vah:
            p = -1.0
        elif O[s, 0] < val:
            p = 1.0
        else:
            continue
        k = -1
        for i in range(1, 13):
            c1, c2 = C[s, 30 * i - 1], C[s, 30 * i + 29]
            if val <= c1 <= vah and val <= c2 <= vah:
                k = 30 * i + 29
                break
        if k < 0 or k + 1 > 360:
            continue
        if p < 0:
            stop = H[s, k - 59:k + 1].max() + tick
            obj = val
        else:
            stop = L[s, k - 59:k + 1].min() - tick
            obj = vah
        px = O[s, k + 1]
        sortie = np.nan
        for m in range(k + 1, 385):
            if p < 0:
                if H[s, m] >= stop:
                    sortie = max(O[s, m], stop)
                    break
                if O[s, m] < obj:
                    sortie = O[s, m]
                    break
                if L[s, m] <= obj - tick:
                    sortie = obj
                    break
            else:
                if L[s, m] <= stop:
                    sortie = min(O[s, m], stop)
                    break
                if O[s, m] > obj:
                    sortie = O[s, m]
                    break
                if H[s, m] >= obj + tick:
                    sortie = obj
                    break
        if np.isnan(sortie):
            sortie = C[s, 384]
        g[s] = p * (sortie - px) * pt * ech[s] - frais
        cote[s], entree[s] = p, k + 1
    return g, cote, entree


@njit(cache=True)
def _e8(O, H, L, C, ok, prec, ech, pt, tick, frais):
    S, N = C.shape
    g = np.full(S, np.nan)
    cote = np.zeros(S)
    entree = np.full(S, -1, np.int64)
    for s in range(S):
        p0 = prec[s]
        if not ok[s] or p0 < 0:
            continue
        ph, pl = H[p0].max(), L[p0].min()
        if O[s, 0] < pl:
            p, stop = 1.0, pl + tick
        elif O[s, 0] > ph:
            p, stop = -1.0, ph - tick
        else:
            continue
        for m in range(0, 361):
            if p > 0 and H[s, m] >= stop:
                g[s] = (C[s, N - 1] - max(O[s, m], stop)) * pt * ech[s] - frais
                cote[s], entree[s] = p, m
                break
            if p < 0 and L[s, m] <= stop:
                g[s] = (min(O[s, m], stop) - C[s, N - 1]) * pt * ech[s] - frais
                cote[s], entree[s] = p, m
                break
    return g, cote, entree


@njit(cache=True)
def _e9(O, C, ok, onh, onl, plast, ech, pt, frais):
    S, N = C.shape
    g = np.full(S, np.nan)
    cote = np.zeros(S)
    entree = np.full(S, -1, np.int64)
    for s in range(S):
        if not ok[s] or np.isnan(plast[s]):
            continue
        lh, ll = O[s, 0] * onh[s] / plast[s], O[s, 0] * onl[s] / plast[s]
        if O[s, 0] >= lh or O[s, 0] <= ll:
            continue
        for m in range(0, 330):
            p = 1.0 if C[s, m] > lh else (-1.0 if C[s, m] < ll else 0.0)
            if p != 0:
                g[s] = p * (C[s, 384] - O[s, m + 1]) * pt * ech[s] - frais
                cote[s], entree[s] = p, m + 1
                break
    return g, cote, entree


# ----------------------------------------------------------------------------------------------- calcul
def toutes(d, n, ctx):
    """Gains par seance (NaN sans trade), cote et minute d'entree du premier trade, pour chaque regle."""
    O, H, L, C = d["o"], d["h"], d["l"], d["c"]
    jours = d["jours"]
    ok = d["complete"] & ~d["ech"]
    prec = d["prec_meme"]
    pt, tick, frais = float(d["pt"]), float(d["tick"]), float(d["frais"])
    ech = float(d["pref"]) / O[:, 0]
    debut = {r: np.datetime64(DEBUT.get(r, "2011-01-01")) for r in REGLES}
    okr = {r: ok & (jours >= debut[r]) for r in REGLES}
    out = {}
    out["E1"] = _e1(O, C, okr["E1"], ctx["gex"], ech, pt, frais, float(d["pref"]), False)
    out["E1b"] = _e1b(O, C, okr["E1b"], ctx["gex"], prec, ech, pt, frais)
    out["E2"] = _fenetre(O, C, okr["E2"], ctx["fomc_conf"].astype(np.float64), prec, ech, pt, frais, 2)
    out["E3"] = _fenetre(O, C, okr["E3"], ctx["fomc_tout"].astype(np.float64), prec, ech, pt, frais, 3)
    out["E4"] = _fenetre(O, C, okr["E4"], ctx["e4"], prec, ech, pt, frais, 4)
    out["E7"] = _e7(O, H, L, C, okr["E7"], prec, ech, pt, tick, frais)
    out["E8"] = _e8(O, H, L, C, okr["E8"], prec, ech, pt, tick, frais)
    # nuit
    On, Hn, Ln, Cn = n["o"], n["h"], n["l"], n["c"]
    okn = n["complete"]
    echn = float(n["pref"]) / On[:, 0]
    ptn, fraisn = float(n["pt"]), float(n["frais"])
    S_n = len(n["jours"])
    out["E5"] = _nuit(On, Cn, okn, np.zeros(S_n, np.int64), ctx["e5_sortie"], echn, ptn, fraisn)
    # E6 : derniere heure de la seance de jour precedente dans le tiers bas des 252 seances completes precedentes
    lh = np.where(d["complete"], C[:, -1] / C[:, 329] - 1, np.nan)
    idx_c = np.flatnonzero(d["complete"])
    seuil = np.full(len(jours), np.nan)
    for j, s in enumerate(idx_c):
        if j >= 252:
            seuil[s] = np.quantile(lh[idx_c[j - 252:j]], 1 / 3)
    ip = ctx["nuit_prec_jour"]
    cond = (ip >= 0) & (lh[np.maximum(ip, 0)] <= seuil[np.maximum(ip, 0)])
    out["E6"] = _nuit(On, Cn, okn, np.full(S_n, 96, np.int64), np.where(cond, 107, -1).astype(np.int64), echn, ptn,
                      fraisn)
    # E9 : extremes de la nuit du matin, ramenes au future
    jn = ctx["jour_nuit"]
    a = (jn >= 0)
    a[a] = okn[jn[a]]
    k = np.maximum(jn, 0)
    onh = np.where(a, Hn[k].max(axis=1), np.nan)
    onl = np.where(a, Ln[k].min(axis=1), np.nan)
    plast = np.where(a, Cn[k, -1], np.nan)
    out["E9"] = _e9(O, C, ok, onh, onl, plast, ech, pt, frais)
    out = {r: out[r] for r in REGLES}
    dates = {r: (n["jours"] if r in ("E5", "E6") else jours) for r in REGLES}
    return out, dates


def stats(g, dates, r):
    m = np.isfinite(g)
    x, j = g[m], dates[m]
    t = K.t_stat(x) if len(x) > 2 else float("nan")
    e, c = x[j <= FIN_EXPLO], x[j > FIN_EXPLO]
    pub = x[j >= np.datetime64(PUBLICATION[r])] if r in PUBLICATION else np.array([])
    return dict(trades=int(len(x)), t=float(t), net=float(x.mean()) if len(x) else float("nan"),
                total=float(x.sum()), n_explo=int(len(e)), moy_explo=float(e.mean()) if len(e) else float("nan"),
                t_explo=float(K.t_stat(e)) if len(e) > 2 else float("nan"), n_controle=int(len(c)),
                moy_controle=float(c.mean()) if len(c) else float("nan"),
                t_controle=float(K.t_stat(c)) if len(c) > 2 else float("nan"),
                n_pub=int(len(pub)), t_pub=float(K.t_stat(pub)) if len(pub) > 2 else float("nan"),
                gagnants=float((x > 0).mean()) if len(x) else float("nan"))


_ETAT = {}


def jumeau(args):
    sorte, k = args
    d, n, ctx = _ETAT["d"], _ETAT["n"], _ETAT["ctx"]
    so = "permutation" if sorte == "permutation" else "signe"
    base = 3000 if sorte == "permutation" else 3500
    dj = B.bruiter(d, base + k, sorte=so)
    nj = B.bruiter(n, base + 1000 + k, sorte=so)
    out, dates = toutes(dj, nj, ctx)
    return sorte, {r: stats(out[r][0], dates[r], r)["t"] for r in REGLES}


def preparer():
    d, n = jour_nq(), nuit_nq()
    g_dates, g_val = gex()
    ctx = contexte(d, n, g_dates, g_val, fomc(), clotures_etf("SPY"), clotures_etf("IEF"))
    return d, n, ctx


def test(d, n, ctx):
    """Sans regard vers le futur : (1) changer tout ce qui suit la minute d'entree d'une seance ne change ni le cote ni la
    minute d'entree ; (2) changer les seances suivantes ne change rien aux seances precedentes."""
    rng = np.random.default_rng(7)
    ref, _ = toutes(d, n, ctx)
    d2 = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in d.items()}
    n2 = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in n.items()}
    for r in REGLES:
        cote, ent = ref[r][1], ref[r][2]
        dd = n2 if r in ("E5", "E6") else d2
        src = n if r in ("E5", "E6") else d
        P = np.flatnonzero(ent >= 0)[::2]              # une seance sur deux parmi celles qui tradent
        for s in P:
            e = ent[s]
            f = np.exp(rng.normal(0, 0.01, dd["c"].shape[1] - e - 1))
            for col in "ohlc":
                dd[col][s, e + 1:] = src[col][s, e + 1:] * f
            dd["h"][s] = np.maximum(dd["h"][s], np.maximum(dd["o"][s], dd["c"][s]))
            dd["l"][s] = np.minimum(dd["l"][s], np.minimum(dd["o"][s], dd["c"][s]))
        out, _ = toutes(d2, n2, ctx)
        # seances controlees : celles modifiees dont la veille ne l'a pas ete (E1b, E3, E7, E8 lisent la veille) ;
        # E1 trade plusieurs fois par seance : seul son premier trade est controle
        prec = d["prec_meme"] if r not in ("E5", "E6") else np.full(len(n["jours"]), -1)
        Q = np.array([s for s in P if prec[s] < 0 or prec[s] not in set(P)], int)
        assert len(Q) > 0
        assert (out[r][1][Q] == cote[Q]).all() and (out[r][2][Q] == ent[Q]).all(), f"{r} : la decision depend de l'apres-entree"
        for col in "ohlc":
            d2[col][:] = d[col]
            n2[col][:] = n[col]
    s0 = len(d["jours"]) // 2
    for col in "ohlc":
        d2[col][s0:] = d[col][s0:] * np.exp(rng.normal(0, 0.01, d[col][s0:].shape))
    d2["h"] = np.maximum(d2["h"], np.maximum(d2["o"], d2["c"]))
    d2["l"] = np.minimum(d2["l"], np.minimum(d2["o"], d2["c"]))
    out, _ = toutes(d2, n, ctx)
    for r in REGLES:
        if r in ("E5", "E6"):
            continue
        a, b = ref[r][0][:s0], out[r][0][:s0]
        assert np.array_equal(np.isnan(a), np.isnan(b)) and np.allclose(a[np.isfinite(a)], b[np.isfinite(b)]), r
    print("tests : aucune decision ne depend de l'apres-entree ni des seances suivantes")


def main():
    d, n, ctx = preparer()
    if "--test" in sys.argv:
        test(d, n, ctx)
        return
    out, dates = toutes(d, n, ctx)
    reel = {r: stats(out[r][0], dates[r], r) for r in REGLES}
    _ETAT.update(d=d, n=n, ctx=ctx)
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
    # pour information (aucune decision) : E2 et E3 avec les jours de changement de contrat, qui excluent 15 reunions de
    # la Fed sur 85 (la regle fixee les exclut, comme pour toutes les seances)
    d_info = dict(d, ech=np.zeros_like(d["ech"]))
    out_i, dates_i = toutes(d_info, n, ctx)
    info = {r: stats(out_i[r][0], dates_i[r], r) for r in ("E2", "E3")}
    SORTIE.mkdir(parents=True, exist_ok=True)
    (SORTIE / "partie_e.json").write_text(json.dumps(dict(regles=res, info_avec_changements=info), indent=1,
                                                     ensure_ascii=False))
    L = [f"Partie E (README.md) : 10 regles, NQ, 1 contrat micro au prix d'aujourd'hui, frais compris. Retenue : t >= "
         f"{SEUIL_RETENUE:.2f}, positive avant et apres 2023, au-dessus de 95 % des jumeaux de chaque bruit ; interessante : "
         "t >= 1,65, positive sur les deux periodes, au-dessus de 90 % des jumeaux.", "",
         "regle  nom                                                     trades     t   net/trade  gagnants   t <=2022 "
         "(moy.)        t >=2023 (moy.)      t apres publication   95e perm 95e signe bat le bruit  verdict"]
    for x in res:
        verdict = "RETENUE" if x["retenue"] else ("interessante" if x["interessante"] else "non")
        L.append(f"{x['regle']:<5}  {x['nom']:<54} {x['trades']:6d} {x['t']:6.2f} {x['net']:8.2f} $ {x['gagnants']:8.0%}  "
                 f"{x['t_explo']:6.2f} ({x['moy_explo']:+7.2f} $)  {x['t_controle']:6.2f} ({x['moy_controle']:+7.2f} $)  "
                 f"{x['t_pub']:6.2f} ({x['n_pub']:4d} tr.)     {x['bruit_95']:6.2f} {x['signe_95']:7.2f}   {x['bat_bruit']:6.0%}"
                 f"      {verdict}")
    L += ["", "Pour information (pas de decision) : la Fed avec les jours de changement de contrat"]
    for r, v in info.items():
        L.append(f"{r:<5}  {NOMS[r]:<54} {v['trades']:6d} {v['t']:6.2f} {v['net']:8.2f} $  ; <=2022 t {v['t_explo']:.2f}, "
                 f">=2023 t {v['t_controle']:.2f}, apres publication t {v['t_pub']:.2f}")
    txt = "\n".join(L)
    (SORTIE / "partie_e.txt").write_text(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
