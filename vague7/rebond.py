#!/usr/bin/env python3
"""Signal du rebond apres forte baisse (vague 7, README.md), exactement comme zone/robot.py sur main (fonctions tableaux,
seances_completes, precedente, rebond) : achat de 1 MNQ a l'ouverture de 9 h 30, vente a la cloture de la derniere
minute, le jour qui suit une seance dont le mouvement ouverture -> cloture est sous le 10e centile des 252 valeurs
precedentes ; seance de reference = derniere seance complete ; pas de rebond un jour incomplet (jour court)."""
from pathlib import Path

import numpy as np
import pandas as pd

R0 = Path(__file__).resolve().parent.parent
N = 390
FICHIER = R0 / "intraday/donnees/nasdaq100_1min.csv.gz"


def tableaux(d):
    """Comme robot.tableaux : (jours, ouvertures de 9 h 30, clotures de la derniere minute, minutes presentes)."""
    t = pd.to_datetime(d["t"])
    jour = t.dt.normalize()
    minute = (t.dt.hour * 60 + t.dt.minute - 570).values
    jours = np.sort(jour.unique())
    ij = np.searchsorted(jours, jour.values)
    tab = {}
    for col in "oc":
        a = np.full((len(jours), N), np.nan)
        a[ij, minute] = d[col].values
        tab[col] = a
    presentes = ~np.isnan(tab["c"])
    C = pd.DataFrame(tab["c"]).ffill(axis=1).values
    O = np.where(np.isnan(tab["o"]), C, tab["o"])
    return pd.DatetimeIndex(jours), O, C, presentes


def signal(jours, O, C, P):
    """Booleen par seance : rebond achete ce jour-la (robot.rebond, version executable)."""
    complete = P[:, 0] & P[:, N - 1] & (P.sum(axis=1) >= 370)
    idx = np.where(complete, np.arange(len(complete)), -1)
    prec = np.r_[-1, np.maximum.accumulate(idx)[:-1]]
    mouv = C[:, N - 1] / O[:, 0] - 1
    rv = np.where(prec >= 0, mouv[np.maximum(prec, 0)], np.nan)
    v = np.isfinite(rv)
    seuil = np.full(len(jours), np.nan)
    seuil[v] = pd.Series(rv[v]).rolling(252, min_periods=252).quantile(0.1).shift(1).values
    with np.errstate(invalid="ignore"):
        return (rv <= seuil) & complete


def pour(D):
    """Signal aligne sur les seances de D (donnees de la recherche), en int64 (0 ou 1)."""
    if "rebond" not in D:
        d = pd.read_csv(FICHIER, usecols=["t", "o", "c"])
        jours, O, C, P = tableaux(d)
        s = pd.Series(signal(jours, O, C, P), index=jours)
        D["rebond"] = s.reindex(pd.DatetimeIndex(D["jours"])).fillna(False).astype(np.int64).values
    return D["rebond"]
