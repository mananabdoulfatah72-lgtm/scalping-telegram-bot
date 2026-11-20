#!/usr/bin/env python3
"""Neuf familles classiques de suivi de tendance jamais codees dans le projet, avec leurs reglages de manuel (aucun reglage
sur le mois), dans le cadre du Supertrend : etat a la cloture de chaque bougie de 5 minutes, position a l'ouverture de la
minute suivante, pas d'entree apres 15 h 30, a plat a 15 h 55, limite du jour 400 $, 1 MNQ.
Usage : KB_MINUTES=<nasdaq100_1min.csv.gz> NQ_RECENT=<nq_1min.csv.gz> python3 usine/familles_tendance.py
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
from numba import njit

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import donnees as Dn  # noqa: E402
import moteur as Mo  # noqa: E402
import pupitre as Pu  # noqa: E402
import indicateurs as I  # noqa: E402
import agents_st as A  # noqa: E402

B = I.B


@njit(cache=True)
def garder(haut, bas):
    """+1 quand haut, -1 quand bas, sinon l'etat precedent (stop and reverse)."""
    st = np.zeros(haut.shape[0]); e = 0.0
    for i in range(haut.shape[0]):
        if haut[i]:
            e = 1.0
        elif bas[i]:
            e = -1.0
        st[i] = e
    return st


@njit(cache=True)
def psar(h, l, pas, maxi):
    n = h.shape[0]; st = np.zeros(n); up = True; sar = l[0]; ep = h[0]; af = pas
    for i in range(1, n):
        sar = sar + af * (ep - sar)
        if up:
            sar = min(sar, l[i - 1], l[i - 2] if i > 1 else l[i - 1])
            if l[i] < sar:
                up = False; sar = ep; ep = l[i]; af = pas
            elif h[i] > ep:
                ep = h[i]; af = min(af + pas, maxi)
        else:
            sar = max(sar, h[i - 1], h[i - 2] if i > 1 else h[i - 1])
            if h[i] > sar:
                up = True; sar = ep; ep = h[i]; af = pas
            elif l[i] < ep:
                ep = l[i]; af = min(af + pas, maxi)
        st[i] = 1.0 if up else -1.0
    return st


@njit(cache=True)
def dmi(h, l, c, n, seuil):
    m = h.shape[0]; pdm = np.zeros(m); ndm = np.zeros(m)
    for i in range(1, m):
        u = h[i] - h[i - 1]; d = l[i - 1] - l[i]
        pdm[i] = u if (u > d and u > 0) else 0.0
        ndm[i] = d if (d > u and d > 0) else 0.0
    tr = I.vrai_range(h, l, c); atr = I.rma(tr, n)
    pdi = 100 * I.rma(pdm, n) / atr; ndi = 100 * I.rma(ndm, n) / atr
    dx = 100 * np.abs(pdi - ndi) / np.maximum(pdi + ndi, 1e-12)
    adx = np.full(m, np.nan); s = 0.0; k = 0
    for i in range(m):
        if np.isnan(dx[i]):
            continue
        if k < n:
            s += dx[i]; k += 1
            if k == n:
                adx[i] = s / n
        else:
            adx[i] = (adx[i - 1] * (n - 1) + dx[i]) / n
    st = np.zeros(m)
    for i in range(m):
        if adx[i] > seuil:
            st[i] = 1.0 if pdi[i] > ndi[i] else -1.0
    return st


@njit(cache=True)
def supertrend_15(h5, l5, c5, per, mult):
    """Supertrend sur des bougies de 15 minutes (3 bougies de 5 minutes alignees sur 9 h 30), etat reporte sur les bougies de 5 minutes."""
    n15 = h5.shape[0] // 3; h = np.empty(n15); l = np.empty(n15); c = np.empty(n15)
    for k in range(n15):
        h[k] = max(h5[3 * k], h5[3 * k + 1], h5[3 * k + 2]); l[k] = min(l5[3 * k], l5[3 * k + 1], l5[3 * k + 2]); c[k] = c5[3 * k + 2]
    st15 = np.zeros(n15); atr = 0.0; hb = np.nan; lb = np.nan; dr = 1.0
    for i in range(1, n15):
        tr = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
        atr = tr if i == 1 else (atr * (per - 1) + tr) / per
        mid = (h[i] + l[i]) / 2; hb2 = mid + mult * atr; lb2 = mid - mult * atr
        if i > 1:
            hb2 = hb2 if (hb2 < hb or c[i - 1] > hb) else hb
            lb2 = lb2 if (lb2 > lb or c[i - 1] < lb) else lb
            if dr > 0 and c[i] < lb2:
                dr = -1.0
            elif dr < 0 and c[i] > hb2:
                dr = 1.0
        hb = hb2; lb = lb2
        st15[i] = dr if i >= per else 0.0
    st = np.zeros(h5.shape[0]); e = 0.0
    for i in range(h5.shape[0]):
        if i % 3 == 2:
            e = st15[i // 3]
        st[i] = e
    return st


def etats(P):
    o, h, l, c = I.barres5(P["O"], P["H"], P["L"], P["C"])
    vw = P["vwap"][:, 4::5].reshape(-1)[: c.shape[0]]                # VWAP de la seance a la cloture de chaque bougie
    tr = I.vrai_range(h, l, c)
    E = {}
    E["Croisement de moyennes EMA 9 / 21"] = np.sign(I.ema(c, 9) - I.ema(c, 21))
    macd = I.ema(c, 12) - I.ema(c, 26)
    E["MACD 12-26-9"] = np.sign(macd - I.ema(macd, 9))
    hh = np.r_[np.nan, I.plus_haut(h, 20)[:-1]]; ll = np.r_[np.nan, I.plus_bas(l, 20)[:-1]]
    E["Canal de Donchian 20 (tortues)"] = garder(c > hh, c < ll)
    E["Parabolic SAR 0,02 / 0,2"] = psar(h, l, 0.02, 0.2)
    mid = I.ema(c, 20); atr = I.rma(tr, 10)
    E["Canal de Keltner EMA 20 +/- 2 ATR"] = garder(c > mid + 2 * atr, c < mid - 2 * atr)
    E["ADX / DMI 14, ADX > 20"] = dmi(h, l, c, 14, 20.0)
    E["Prix contre le VWAP de la seance"] = np.sign(c - vw)
    hc = (o + h + l + c) / 4; ho = np.empty_like(hc); ho[0] = (o[0] + c[0]) / 2
    for i in range(1, len(hc)):
        ho[i] = (ho[i - 1] + hc[i - 1]) / 2
    E["Heikin-Ashi (couleur de la bougie)"] = np.sign(hc - ho)
    E["Supertrend 10-3 en bougies de 15 minutes"] = supertrend_15(h, l, c, 10, 3.0)
    return {k: np.nan_to_num(v) for k, v in E.items()}


def principal():
    D = Dn.charger(recent=os.environ.get("NQ_RECENT") or None)
    P = Mo.deriver(D); J = D["J"]; ok = D["complete"].copy()
    i19 = np.where(J == "2026-11-19")[0]
    if len(i19):
        ok[i19[0]] = True
    P["ok"] = ok
    idx = np.where(ok & (J >= "2015-01-01"))[0]; m = (J[idx] >= "2026-10-13") & (J[idx] <= "2026-11-19"); d23 = J[idx] >= "2023-01-01"
    pos = {k: I.k_positions(v, ok) for k, v in etats(P).items()}
    pos["Supertrend 10-3 (ton bot, reference)"] = Mo.k_supertrend(P["O"], P["H"], P["L"], P["C"], ok, 10, 3.0)
    res = {}
    for nom, (pg, pi) in pos.items():
        g, p, j = Pu.k_dollars_p(P["lg"], P["lb"], P["O"], P["H"], P["L"], pg, pi, ok, 400.0, A.DOL, A.COUT, 2.0)
        g, p, j = np.nan_to_num(g[idx]), np.nan_to_num(p[idx]), j[idx]
        rr = np.array([A.compte(g, p, j, i, 22) for i in range(len(idx) - 22)]); r23 = rr[d23[:len(rr)]]
        cum = np.cumsum(g)
        res[nom] = dict(mois=round(float(g[m].sum())), par_an=round(float(g.mean()) * 252), par_an_2023=round(float(g[d23].mean()) * 252),
                        t=round(A.t_stat(g), 2), pire_baisse=round(float(np.min(cum - np.maximum.accumulate(cum)))),
                        retrait_22_2023=round(float(np.mean(r23 == 0)), 3), perdu_22_2023=round(float(np.mean((r23 == 1) | (r23 == 2))), 3),
                        trades_par_seance=round(float((np.diff(pi, axis=1) != 0).sum(axis=1)[idx].mean() / 2), 1))
    d = ICI / "resultats" / "2026-11-20"; d.mkdir(parents=True, exist_ok=True)
    (d / "familles_tendance.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(f"{'famille':45s} | mois | $/an 2015+ | $/an 2023+ | t | pire baisse | 22 seances depuis 2023 : retrait / perdu")
    for nom, v in sorted(res.items(), key=lambda kv: -kv[1]["mois"]):
        print(f"{nom[:45]:45s} | {v['mois']:+7,} | {v['par_an']:+7,} | {v['par_an_2023']:+7,} | {v['t']:+.2f} | {v['pire_baisse']:+8,} | "
              f"{v['retrait_22_2023']:.0%} / {v['perdu_22_2023']:.0%}")


if __name__ == "__main__":
    principal()
