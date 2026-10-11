#!/usr/bin/env python3
"""Labo de robustesse (README.md) : le bot rejoue avec d'autres parametres.

- zone de bruit (meme code que protection/robot_main.zone_de_bruit, version V1 du bot) avec 4 parametres : jours de la
  moyenne du mouvement (14 dans le bot), minutes entre deux controles (30), largeur de la zone (1 x le mouvement moyen)
  et sortie (zone ou VWAP, comme le bot ; ou zone seule) ; 1 MNQ, 3 $ par aller-retour, au prix d'aujourd'hui ;
- RSI(2) de nuit sur 1 MES (meme regle que robot_main.rsi2, achat a la reouverture de 18 h, vente a 9 h 30) avec 3
  parametres : moyenne longue (200), seuil du RSI (10), moyenne de sortie (5).
Controle : avec les reglages du bot, on retrouve exactement les series de la recherche (test_robustesse.py)."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

ICI = Path(__file__).resolve().parent
R0 = ICI.parent
os.environ.setdefault("ROBOT_DEBUT_RSI2", "2000-01-01")
os.environ.setdefault("ROBOT_DOSSIER", str(ICI / "_robot"))
sys.path.insert(0, str(R0 / "protection"))
sys.path.insert(0, str(R0 / "montecarlo"))
import robot_main as RB  # noqa: E402
import protection as PR  # noqa: E402

N = RB.N
FRAIS_ZONE = RB.COUT * RB.PT                       # 3 $ par aller-retour, 1 MNQ
FRAIS_NUIT = 2 * (1.0 + 0.25 * 5.0)                # 4,50 $ par nuit, 1 MES (comme moteur4)


def minutes():
    d = pd.read_csv(R0 / "intraday/donnees/nasdaq100_1min.csv.gz")
    d = d[d["t"].str[:10] <= PR.FIN_DONNEES]
    jours, O, H, L, C, P, V, ech = RB.tableaux(d)
    ok = RB.seances_completes(P)
    prec = RB.precedente(ok, np.cumsum(ech))
    veille = np.where(prec >= 0, C[np.maximum(prec, 0), N - 1], np.nan)
    ouv = O[:, 0]
    typique = (H + L + C) / 3
    cumv = np.cumsum(V, axis=1)
    vwap = np.where(cumv > 0, np.cumsum(typique * V, axis=1) / np.where(cumv > 0, cumv, 1),
                    np.cumsum(typique, axis=1) / np.arange(1, N + 1))
    return dict(jours=jours, O=O, H=H, L=L, C=C, P=P, V=V, ech=ech, ok=ok, veille=veille, vwap=vwap,
                haut=np.fmax(ouv, veille), bas=np.fmin(ouv, veille), mouv=np.abs(C / ouv[:, None] - 1))


def sigma(M, jours_moy):
    s = np.full_like(M["mouv"], np.nan)
    ok = M["ok"]
    s[ok] = pd.DataFrame(M["mouv"][ok]).rolling(jours_moy, min_periods=jours_moy).mean().shift(1).values
    return s


@njit(cache=True)
def _zone(C, jours_ok, haut, bas, sig, vwap, pas, largeur, sortie_vwap, n):
    nj = C.shape[0]
    pts, allers = np.zeros(nj), np.zeros(nj)
    for d in jours_ok:
        if np.isnan(sig[d, pas]):
            continue
        pos, entree, total, nb = 0, 0.0, 0.0, 0
        m = pas
        while m < n:
            p = C[d, m]
            ub = haut[d] * (1 + largeur * sig[d, m])
            lb = bas[d] * (1 - largeur * sig[d, m])
            sh = max(ub, vwap[d, m]) if sortie_vwap else ub
            sb = min(lb, vwap[d, m]) if sortie_vwap else lb
            if pos > 0 and p <= sh:
                total += p - entree
                pos = 0
            elif pos < 0 and p >= sb:
                total += entree - p
                pos = 0
            if pos == 0 and p > ub:
                pos, entree, nb = 1, p, nb + 1
            elif pos == 0 and p < lb:
                pos, entree, nb = -1, p, nb + 1
            m += pas
        if pos != 0:
            total += pos * (C[d, n - 1] - entree)
        pts[d], allers[d] = total, nb
    return pts, allers


def zone(M, sig, kN, pas=30, largeur=1.0, sortie_vwap=True):
    """Gain de chaque seance en $ (1 MNQ au prix d'aujourd'hui, frais compris) et nombre d'allers-retours."""
    jok = np.flatnonzero(M["ok"] & ~np.isnan(M["veille"])).astype(np.int64)
    pts, nb = _zone(M["C"], jok, M["haut"], M["bas"], sig, M["vwap"], pas, largeur, sortie_vwap, N)
    return pts * 2.0 * kN - FRAIS_ZONE * nb, nb


def decisions_rsi(M, moy_longue=200, seuil=10.0, moy_sortie=5):
    """Comme robot_main.rsi2 : minute de decision (-1 : pas de decision) et position voulue apres la decision."""
    jours, O, H, L, C, P, ech = M["jours"], M["O"], M["H"], M["L"], M["C"], M["P"], M["ech"]
    derniere = N - 1 - np.argmax(P[:, ::-1], axis=1)
    dec = derniere - 9
    fer = RB.feries_bourse(range(pd.Timestamp(jours[0]).year - 1, pd.Timestamp(jours[-1]).year + 2))
    ok = (P.sum(axis=1) >= 60) & P[:, 0] & (dec >= 2) & ~pd.DatetimeIndex(jours).normalize().isin(list(fer))
    if len(ok) and not (P[-1, N - 1] or RB.jour_court(jours[-1])):
        ok[-1] = False
    idx = np.where(ok)[0]
    dd = dec[idx]
    Cx = C[idx, dd - 1]
    seg = np.cumsum(ech)[idx]
    roule = np.r_[seg[1:] != seg[:-1], False]
    n = len(idx)
    ml = pd.Series(Cx).rolling(moy_longue).mean().to_numpy()
    ms = pd.Series(Cx).rolling(moy_sortie).mean().to_numpy()
    rsi = np.full(n, np.nan)
    dx = np.diff(Cx)
    gg, pp = np.maximum(dx, 0), np.maximum(-dx, 0)
    mg, mp = gg[:2].mean(), pp[:2].mean()
    for i in range(2, n):
        if i > 2:
            mg, mp = (mg + gg[i - 1]) / 2, (mp + pp[i - 1]) / 2
        rsi[i] = 100.0 if mp == 0 else 100 - 100 / (1 + mg / mp)
    pos = np.zeros(n, np.int64)
    tenu = False
    for t in range(n):
        if tenu and Cx[t] > ms[t]:
            tenu = False
        elif not tenu and Cx[t] > ml[t] and rsi[t] < seuil:
            tenu = True
        if roule[t]:
            tenu = False
        pos[t] = tenu
    D_dec = np.full(len(jours), -1, np.int64)
    D_vou = np.zeros(len(jours), np.int64)
    D_dec[idx] = dd
    D_vou[idx] = pos
    return D_dec, D_vou


@njit(cache=True)
def _nuit(dec, voulu, EO0, ENO0, enn, kE, frais):
    nj = dec.shape[0]
    g = np.zeros(nj)
    tenu = np.zeros(nj, np.int64)
    veut = 0
    for d in range(nj):
        if veut == 1 and enn[d] > 0:
            g[d] = (EO0[d] - ENO0[d]) * 5.0 * kE[d] - frais
            tenu[d] = 1
        if dec[d] >= 0:
            veut = voulu[d]
    return g, tenu


def nuit(D, dec, voulu, kE):
    """Gain de chaque seance du RSI(2) de nuit (1 MES, achat a 18 h, vente a 9 h 30) et nuits tenues."""
    return _nuit(dec, voulu, D["EO"][:, 0].copy(), D["ENO"][:, 0].copy(), D["enn"], kE, FRAIS_NUIT)
