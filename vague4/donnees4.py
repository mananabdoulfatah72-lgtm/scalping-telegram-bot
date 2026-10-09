#!/usr/bin/env python3
"""Donnees de la vague 4 : celles d'intraday50k (minutes du NQ, zone, RSI(2), nuit du NQ) et de static50k (minutes de l'ES),
plus la nuit de l'ES rattachee a la seance qui suit, exactement comme commun.charger le fait pour le NQ."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
R0 = ICI.parent
sys.path.insert(0, str(R0 / "static50k"))
import donnees as DS  # noqa: E402

K = DS.K


def nuit(fichier, jours, contrat):
    """Barres d'une heure de la nuit qui precede chaque seance (de 18 h la seance d'avant a 9 h), meme contrat que la
    seance qui suit, au plus K.NB_NUIT barres : meme regle que commun.charger."""
    h = pd.read_csv(fichier)
    t = pd.to_datetime(h["t"])
    j = pd.DatetimeIndex(jours)
    k = np.searchsorted(j + pd.Timedelta(hours=9), t, side="right")
    ok = (k >= 1) & (k < len(j))
    kk = np.clip(k, 1, len(j) - 1)
    ok &= t.to_numpy() >= (j[kk - 1] + pd.Timedelta(hours=18)).to_numpy()
    ok &= h["contrat"].to_numpy() == contrat[kk]
    nj = len(j)
    NO, NH, NL = (np.full((nj, K.NB_NUIT), np.nan) for _ in range(3))
    nn = np.zeros(nj, np.int64)
    hh = h[ok].assign(k=kk[ok])
    for kd, g in hh.groupby("k", sort=True):
        g = g.iloc[:K.NB_NUIT]
        n = len(g)
        NO[kd, :n], NH[kd, :n], NL[kd, :n] = (g[c].to_numpy() for c in "ohl")
        nn[kd] = n
    return NO, NH, NL, nn


def charger():
    D = K.charger()
    j = D["jours"]
    EO, EH, EL, EC, ce = DS.minutes_es(j)
    ENO, ENH, ENL, enn = nuit(R0 / "nuit/donnees/sp500_1h.csv.gz", j, ce)
    D.update(EO=EO, EH=EH, EL=EL, EC=EC, contrat_es=ce, ENO=ENO, ENH=ENH, ENL=ENL, enn=enn)
    der = D["derniere"]
    nj = len(j)
    D["cl_nq"] = D["C"][np.arange(nj), der]
    D["cl_es"] = EC[np.arange(nj), der]
    return D


def base(D, garde=None):
    """Tableaux de parcours4, apres (debut, rsi, ptN, ptE, retraits)."""
    nj = len(D["jours"])
    if garde is None:
        garde = np.ones(len(D["Z"]), bool)
    zt = K.P.tableaux_zone(D["Z"], nj, garde)
    return (D["O"], D["H"], D["L"], D["C"], D["derniere"], *zt, D["dec"], D["voulu"], D["NO"], D["NH"], D["NL"], D["nn"],
            D["EO"], D["EH"], D["EL"], D["EC"], D["ENO"], D["ENH"], D["ENL"], D["enn"])


def facteurs(D, d):
    """Niveau d'aujourd'hui (comme static50k) : derniere cloture des donnees / cloture de la seance d'avant le depart."""
    return D["cl_nq"][-1] / D["cl_nq"][d - 1], D["cl_es"][-1] / D["cl_es"][d - 1]
