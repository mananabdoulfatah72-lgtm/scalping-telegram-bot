#!/usr/bin/env python3
"""Partie H (README.md) : banc de 16 strategies simples d'analyse technique sur le NQ (ORB, cassures, Donchian, EMA,
MACD, Bollinger, RSI(2), Supertrend, gaps, jour interieur, NR7), 2011 - 2026, frais d'aujourd'hui, 40 + 40 jumeaux de
bruit. Ecrit resultats/h/partie_h.json et resultats/h/partie_h.txt.
Lancer : KB=<branche de recherche extraite> python3 scalping/partie_h.py [--test]"""
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
import partie_f as F
import partie_g as G

SORTIE = K.ICI / "resultats" / "h"
NOMS = {"H1": "ORB 5 min (Zarattini-Aziz)", "H2": "ORB 15 min", "H3": "ORB 30 min", "H4": "ORB 60 min (initial balance)",
        "H5": "cassure du plus haut / plus bas de la veille", "H6": "Donchian 20 / 10 (5 min)", "H7": "croisement EMA 9 / 21 (5 min)",
        "H8": "MACD 12-26-9 (5 min)", "H9": "Bollinger 20-2, retour a la moyenne (5 min)", "H10": "Bollinger 20-2, cassure (5 min)",
        "H11": "RSI(2) intraday (5 min)", "H12": "Supertrend 10-3 (5 min)", "H13": "gap and go (ecart >= 0,5 %)",
        "H14": "comblement de gap (ecart >= 0,5 %)", "H15": "jour interieur, cassure du range de la veille",
        "H16": "NR7 + ORB 30 min"}
REGLES = list(NOMS)
SEUIL_RETENUE = float(norm.ppf(1 - 0.05 / len(REGLES)))
JUMEAUX = 40
NB = 78                                                   # barres de 5 minutes par seance


# ----------------------------------------------------------------------------------------------- indicateurs
@njit(cache=True)
def _ema(x, n):
    a = 2.0 / (n + 1)
    out = np.empty_like(x)
    out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out


@njit(cache=True)
def _indicateurs(h, l, c):
    """Series continues des barres de 5 minutes : EMA 9/21, MACD et signal, moyenne et ecart-type sur 20, RSI(2) de
    Wilder, Supertrend (10, 3) (ATR de Wilder), plus haut des 20 et plus bas des 10 barres precedentes (et l'inverse)."""
    n = len(c)
    e9, e21 = _ema(c, 9), _ema(c, 21)
    macd = _ema(c, 12) - _ema(c, 26)
    sig = _ema(macd, 9)
    sma = np.full(n, np.nan)
    sd = np.full(n, np.nan)
    hh20 = np.full(n, np.nan)
    ll20 = np.full(n, np.nan)
    hh10 = np.full(n, np.nan)
    ll10 = np.full(n, np.nan)
    for i in range(n):
        if i >= 19:
            w = c[i - 19:i + 1]
            sma[i], sd[i] = w.mean(), w.std()
        if i >= 20:
            hh20[i], ll20[i] = h[i - 20:i].max(), l[i - 20:i].min()
        if i >= 10:
            hh10[i], ll10[i] = h[i - 10:i].max(), l[i - 10:i].min()
    rsi = np.full(n, np.nan)
    ag, al = 0.0, 0.0
    for i in range(1, n):
        dlt = c[i] - c[i - 1]
        gn, ls = max(dlt, 0.0), max(-dlt, 0.0)
        if i <= 2:
            ag += gn / 2
            al += ls / 2
        else:
            ag = (ag * 1 + gn) / 2
            al = (al * 1 + ls) / 2
        if i >= 2:
            rsi[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    st = np.zeros(n)
    atr = 0.0
    hb, lb = np.nan, np.nan
    d = 1.0
    for i in range(1, n):
        tr = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
        atr = tr if i == 1 else (atr * 9 + tr) / 10
        mid = (h[i] + l[i]) / 2
        hb2, lb2 = mid + 3 * atr, mid - 3 * atr
        if i > 1:
            hb2 = hb2 if (hb2 < hb or c[i - 1] > hb) else hb
            lb2 = lb2 if (lb2 > lb or c[i - 1] < lb) else lb
            if d > 0 and c[i] < lb2:
                d = -1.0
            elif d < 0 and c[i] > hb2:
                d = 1.0
        hb, lb = hb2, lb2
        st[i] = d if i >= 10 else 0.0
    return e9, e21, macd, sig, sma, sd, rsi, st, hh20, ll20, hh10, ll10


@njit(cache=True)
def _barres(O, H, L, C, ok, ech, pt, frais, ind, regle):
    """Strategies a indicateurs (H6 a H12) sur les barres de 5 minutes ; signal a la cloture de la barre b, execution a
    l'ouverture de la minute 5b + 5 ; entrees jusqu'a 15 h 30 ; a plat a 15 h 55 (cloture de la minute 384)."""
    e9, e21, macd, sig, sma, sd, rsi, st, hh20, ll20, hh10, ll10 = ind
    S = C.shape[0]
    g, cote, entree = np.full(S, np.nan), np.zeros(S), np.full(S, -1, np.int64)
    for s in range(S):
        if not ok[s]:
            continue
        pos, px, tot, nb = 0.0, 0.0, 0.0, 0
        for b in range(76):
            i = s * 78 + b
            c = C[s, 5 * b + 4]
            cible = pos
            if regle == 6:
                if pos == 0:
                    cible = 1.0 if c > hh20[i] else (-1.0 if c < ll20[i] else 0.0)
                elif (pos > 0 and c < ll10[i]) or (pos < 0 and c > hh10[i]):
                    cible = 0.0
            elif regle == 7 or regle == 8:
                a, z = (e9, e21) if regle == 7 else (macd, sig)
                if i >= 1 and a[i] > z[i] and a[i - 1] <= z[i - 1]:
                    cible = 1.0
                elif i >= 1 and a[i] < z[i] and a[i - 1] >= z[i - 1]:
                    cible = -1.0
            elif regle == 9 or regle == 10:
                if np.isnan(sma[i]):
                    continue
                up, dn = sma[i] + 2 * sd[i], sma[i] - 2 * sd[i]
                if pos == 0:
                    if regle == 9:
                        cible = 1.0 if c < dn else (-1.0 if c > up else 0.0)
                    else:
                        cible = 1.0 if c > up else (-1.0 if c < dn else 0.0)
                else:
                    mr = pos > 0 if regle == 9 else pos < 0
                    if (mr and c >= sma[i]) or (not mr and c <= sma[i]):
                        cible = 0.0
            elif regle == 11:
                if np.isnan(rsi[i]):
                    continue
                if pos == 0:
                    cible = 1.0 if rsi[i] < 10 else (-1.0 if rsi[i] > 90 else 0.0)
                elif (pos > 0 and rsi[i] > 70) or (pos < 0 and rsi[i] < 30):
                    cible = 0.0
            else:
                if st[i] != 0:                                   # toujours dans le sens du Supertrend
                    cible = st[i]
            m = 5 * b + 5
            if cible != pos and pos != 0:                      # sortie (ou retournement)
                tot += pos * (O[s, m] - px) * pt * ech[s] - frais
                nb += 1
                pos = 0.0
            if cible != 0 and pos == 0 and m <= 360:
                pos, px = cible, O[s, m]
                if entree[s] < 0:
                    cote[s], entree[s] = cible, m
        if pos != 0:
            tot += pos * (C[s, 384] - px) * pt * ech[s] - frais
            nb += 1
        if nb:
            g[s] = tot
    return g, cote, entree


@njit(cache=True)
def _gerer(O, H, L, C, s, m0, p, px, stop, obj, tick):
    """Sortie d'une position ouverte a l'ouverture de m0 : stop (avant l'objectif dans la minute), objectif limite
    (traverse d'un tick, ou ouverture au-dela), sinon cloture de 15 h 55."""
    for m in range(m0, 385):
        if not np.isnan(stop):
            if p > 0 and L[s, m] <= stop:
                return min(O[s, m], stop)
            if p < 0 and H[s, m] >= stop:
                return max(O[s, m], stop)
        if not np.isnan(obj):
            if p > 0 and (O[s, m] > obj or H[s, m] >= obj + tick):
                return max(O[s, m], obj) if O[s, m] > obj else obj
            if p < 0 and (O[s, m] < obj or L[s, m] <= obj - tick):
                return min(O[s, m], obj) if O[s, m] < obj else obj
    return C[s, 384]


@njit(cache=True)
def _seances(O, H, L, C, ok, prec, ech, pt, tick, frais, regle):
    """H1 a H5 et H13 a H16 (une position par jour, minutes)."""
    S, N = C.shape
    g, cote, entree = np.full(S, np.nan), np.zeros(S), np.full(S, -1, np.int64)
    for s in range(S):
        if not ok[s]:
            continue
        p1 = prec[s]
        p, m0, stop, obj = 0.0, -1, np.nan, np.nan
        k = 0
        if regle == 2 or regle == 3 or regle == 4 or regle == 16:
            k = 15 if regle == 2 else (60 if regle == 4 else 30)
            if regle == 16:
                if p1 < 0:
                    continue
                r1 = H[p1].max() - L[p1].min()
                q, n7 = p1, 0
                petit = True
                for _ in range(6):
                    q = prec[q]
                    if q < 0:
                        petit = False
                        break
                    if H[q].max() - L[q].min() <= r1:
                        petit = False
                    n7 += 1
                if not petit:
                    continue
        if regle == 1:
            if C[s, 4] == O[s, 0]:
                continue
            p = 1.0 if C[s, 4] > O[s, 0] else -1.0
            m0 = 5
            hi, lo = H[s, 0:5].max(), L[s, 0:5].min()
            stop = lo if p > 0 else hi
            risque = abs(O[s, 5] - stop)
            obj = O[s, 5] + p * 10 * risque if risque > 0 else np.nan
        elif k > 0:
            hi, lo = H[s, 0:k].max(), L[s, 0:k].min()
            for m in range(k, 360):
                if C[s, m] > hi:
                    p, m0, stop = 1.0, m + 1, lo
                    break
                if C[s, m] < lo:
                    p, m0, stop = -1.0, m + 1, hi
                    break
        elif regle == 5 or regle == 15:
            if p1 < 0:
                continue
            hi, lo = H[p1].max(), L[p1].min()
            if regle == 15:
                p2 = prec[p1]
                if p2 < 0 or not (hi <= H[p2].max() and lo >= L[p2].min()):
                    continue
            for m in range(0, 360):
                if C[s, m] > hi:
                    p, m0 = 1.0, m + 1
                    break
                if C[s, m] < lo:
                    p, m0 = -1.0, m + 1
                    break
            if regle == 5:
                stop = O[s, 0]
        else:
            if p1 < 0:
                continue
            gap = O[s, 0] / C[p1, N - 1] - 1
            if abs(gap) < 0.005:
                continue
            p = (1.0 if gap > 0 else -1.0) * (1.0 if regle == 13 else -1.0)
            m0 = 1
            if regle == 14:
                obj = C[p1, N - 1]
        if p == 0 or m0 < 0:
            continue
        px = O[s, m0]
        sortie = _gerer(O, H, L, C, s, m0, p, px, stop, obj, tick)
        g[s] = p * (sortie - px) * pt * ech[s] - frais
        cote[s], entree[s] = p, m0
    return g, cote, entree


def toutes(d):
    O, H, L, C = d["o"], d["h"], d["l"], d["c"]
    ok = d["complete"] & ~d["ech"]
    prec = d["prec_meme"]
    pt, tick, frais = float(d["pt"]), float(d["tick"]), float(d["frais"])
    ech = float(d["pref"]) / O[:, 0]
    S = C.shape[0]
    h5 = H.reshape(S, NB, 5).max(axis=2).reshape(-1)
    l5 = L.reshape(S, NB, 5).min(axis=2).reshape(-1)
    c5 = C[:, 4::5].reshape(-1)
    ind = _indicateurs(h5, l5, c5)
    out = {}
    for r in REGLES:
        i = int(r[1:])
        if 6 <= i <= 12:
            out[r] = _barres(O, H, L, C, ok, ech, pt, frais, ind, i)
        else:
            out[r] = _seances(O, H, L, C, ok, prec, ech, pt, tick, frais, i)
    return out


_ETAT = {}


def jumeau(args):
    sorte, k = args
    d = _ETAT["d"]
    dj = B.bruiter(d, (8000 if sorte == "permutation" else 8500) + k, sorte=sorte)
    out = toutes(dj)
    return sorte, {r: F.stats(out[r][0], d["jours"])["t"] for r in REGLES}


def test(d):
    """Changer une seance apres la minute d'entree de son premier trade ne change ni ce cote ni cette minute ; changer
    les seances suivantes ne change rien aux precedentes."""
    rng = np.random.default_rng(13)
    ref = toutes(d)
    for r in REGLES:
        cote, ent = ref[r][1], ref[r][2]
        for s in rng.choice(np.flatnonzero(ent >= 0), size=min(15, int((ent >= 0).sum())), replace=False):
            d2 = dict(d)
            e = ent[s]
            f = np.exp(rng.normal(0, 0.01, d["c"].shape[1] - e - 1))
            for col in "ohlc":
                a = d[col].copy()
                a[s, e + 1:] = d[col][s, e + 1:] * f
                d2[col] = a
            d2["h"][s] = np.maximum(d2["h"][s], np.maximum(d2["o"][s], d2["c"][s]))
            d2["l"][s] = np.minimum(d2["l"][s], np.minimum(d2["o"][s], d2["c"][s]))
            out = toutes(d2)
            assert out[r][1][s] == cote[s] and out[r][2][s] == ent[s], f"{r} seance {s}"
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
    reel = {r: F.stats(out[r][0], d["jours"]) for r in REGLES}
    _ETAT["d"] = d
    with mp.get_context("fork").Pool(int(os.getenv("PROCESSUS", "2"))) as pool:
        bruits = pool.map(jumeau, [(s, k) for s in ("permutation", "signe") for k in range(1, JUMEAUX + 1)])
    tr = G.calcul(d)[4]
    ech = float(d["pref"]) / d["o"][:, 0]
    gz = np.zeros(len(d["jours"]))
    for s, me, sg, ms in tr:
        gz[s] += sg * (d["c"][s, ms] - d["c"][s, me]) * float(d["pt"]) * ech[s] - float(d["frais"])
    jouable = d["complete"] & ~d["ech"]
    res = []
    for r in REGLES:
        v = reel[r]
        tb = np.array([b[r] for s, b in bruits if s == "permutation"], float)
        ts = np.array([b[r] for s, b in bruits if s == "signe"], float)
        bat = float(min(np.nanmean(v["t"] > tb), np.nanmean(v["t"] > ts)))
        deux = v["moy_explo"] > 0 and v["moy_controle"] > 0
        retenue = bool(v["t"] >= SEUIL_RETENUE and deux and bat >= 0.95)
        inter = bool(not retenue and v["t"] >= 1.65 and deux and bat >= 0.90)
        corr = float(np.corrcoef(np.nan_to_num(out[r][0])[jouable], gz[jouable])[0, 1])
        res.append(dict(regle=r, nom=NOMS[r], **v, bruit_95=float(np.nanquantile(tb, 0.95)),
                        signe_95=float(np.nanquantile(ts, 0.95)), bat_bruit=bat, corr_zone=corr, retenue=retenue,
                        interessante=inter))
    SORTIE.mkdir(parents=True, exist_ok=True)
    (SORTIE / "partie_h.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    L = [f"Partie H (README.md) : 16 strategies simples, NQ 2011 - 2026, 1 MNQ au prix d'aujourd'hui, frais compris. Retenue : "
         f"t >= {SEUIL_RETENUE:.2f}, positive avant et apres 2023, au-dessus de 95 % des jumeaux ; interessante : t >= 1,65, "
         "positive sur les deux periodes, au-dessus de 90 %. Zone dans les memes conventions : t 4,21 (partie G).", "",
         "regle  strategie                                        seances    t   net/seance gagnants  t <=2022 (moy.)       "
         "t >=2023 (moy.)     corr. zone  bat le bruit  verdict"]
    for x in res:
        verdict = "RETENUE" if x["retenue"] else ("interessante" if x["interessante"] else "non")
        L.append(f"{x['regle']:<5}  {x['nom']:<47} {x['trades']:6d} {x['t']:6.2f} {x['net']:8.2f} $ {x['gagnants']:6.0%}  "
                 f"{x['t_explo']:6.2f} ({x['moy_explo']:+7.2f} $)  {x['t_controle']:6.2f} ({x['moy_controle']:+7.2f} $)   "
                 f"{x['corr_zone']:+.2f}        {x['bat_bruit']:5.0%}      {verdict}")
    txt = "\n".join(L)
    (SORTIE / "partie_h.txt").write_text(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
