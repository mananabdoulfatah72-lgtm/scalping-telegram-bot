#!/usr/bin/env python3
"""Barres de 5 minutes NQ et ES (9 h 30 - 16 h, New York) a partir des minutes Databento de intraday/donnees.

Deux fichiers par marche, dans evolution/cache/ (non versionne) :
- recherche_{marche}.npz : seances jusqu'au 31 decembre 2022 (seules donnees chargees pendant l'evolution) ;
- coffre_{marche}.npz    : toutes les seances, jusqu'en 2026 (charge une seule fois, a la fin).
On ne garde que les seances completes. Pas de trade le jour d'un changement d'echeance ni le lendemain.

Lancer depuis ce dossier : python3 donnees.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "intraday"))
import strategies as st  # noqa: E402

CACHE = ICI / "cache"
FIN_RECHERCHE = pd.Timestamp("2022-12-31")
BARRES = 78                                   # 5 minutes x 78 = 9 h 30 - 16 h
MARCHES = {"NQ": ("nasdaq100", 2.0, 0.25), "ES": ("sp500", 5.0, 0.25)}   # fichier, $ par point (micro), tick


def construire(nom):
    fichier, pt, tick = MARCHES[nom]
    J, O, H, L, C, P, X = st.charger(fichier)
    ok = st.journees_completes(P)
    ech = X["echeance"]
    J, O, H, L, C, V, ech = J[ok], O[ok], H[ok], L[ok], C[ok], X["V"][ok], ech[ok]
    n = len(J)
    o5 = O[:, ::5]
    h5 = H.reshape(n, BARRES, 5).max(axis=2)
    l5 = L.reshape(n, BARRES, 5).min(axis=2)
    c5 = C[:, 4::5]
    v5 = V.reshape(n, BARRES, 5).sum(axis=2)
    # pas de trade le jour du changement d'echeance ni le lendemain (indicateurs pollues par le saut)
    interdit = ech | np.r_[False, ech[:-1]]
    # regime de volatilite : amplitude de la veille contre la mediane des 20 seances d'avant (connu le matin)
    amp = (h5.max(axis=1) - l5.min(axis=1)) / o5[:, 0]
    amp_veille = pd.Series(amp).shift(1)
    mediane = pd.Series(amp).shift(2).rolling(20, min_periods=20).median()
    regime = np.where(amp_veille > mediane, 1, np.where(amp_veille <= mediane, 2, 0)).astype(np.int8)
    cout = 2 * (1.0 + tick * pt) / pt         # points par aller-retour
    return {"jours": J.values.astype("datetime64[D]"), "o": o5, "h": h5, "l": l5, "c": c5, "v": v5,
            "interdit": interdit, "regime": regime, "cout": np.float64(cout), "pt": np.float64(pt)}


def main():
    CACHE.mkdir(exist_ok=True)
    for nom in MARCHES:
        d = construire(nom)
        garde = d["jours"] <= np.datetime64(FIN_RECHERCHE.date())
        np.savez_compressed(CACHE / f"recherche_{nom}.npz", **{k: (v[garde] if isinstance(v, np.ndarray) and v.ndim and len(v) == len(garde) else v)
                                                               for k, v in d.items()})
        np.savez_compressed(CACHE / f"coffre_{nom}.npz", **d)
        print(f"{nom} : {len(d['jours'])} seances ({str(d['jours'][0])} -> {str(d['jours'][-1])}), dont {garde.sum()} pour la recherche ;"
              f" frais {d['cout']:.2f} points par aller-retour")


if __name__ == "__main__":
    main()
