#!/usr/bin/env python3
"""Constantes de la machine scalping (README.md, regles du 24 octobre 2026) : marches, frais, prix de reference, periodes."""
import os
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
KB = Path(os.getenv("KB", str(ICI.parent.parent / "recherche")))     # branche de recherche extraite (donnees)
CACHE = ICI / "cache"

# nom : (fichier, $ par point du micro, tick, debut et fin de seance en minutes depuis minuit (New York), frais par
#        aller-retour en $, prix de reference, pas des niveaux ronds)
MARCHES = {
    "NQ": ("intraday/donnees/nasdaq100_1min.csv.gz", 2.0, 0.25, 570, 960, 3.00, 30900.0, 100.0),
    "ES": ("intraday/donnees/sp500_1min.csv.gz", 5.0, 0.25, 570, 960, 4.50, 7805.0, 25.0),
    "RTY": ("zone_multi/donnees/russell_1min.csv.gz", 5.0, 0.10, 570, 960, 3.00, 2851.0, 25.0),
    "YM": ("zone_multi/donnees/dow_1min.csv.gz", 0.5, 1.0, 570, 960, 3.00, 52057.0, 250.0),
    "GC": ("zone_multi/donnees/or_1min.csv.gz", 10.0, 0.10, 500, 810, 4.00, 4178.0, 10.0),
    "CL": ("zone_multi/donnees/petrole_1min.csv.gz", 100.0, 0.01, 540, 870, 4.00, 92.2, 1.0),
    "6E": ("zone_multi/donnees/euro_1min.csv.gz", 12500.0, 0.0001, 500, 900, 4.50, 1.142, 0.005),
    "BTC": ("tournoi5/donnees/bitcoin_1min.csv.gz", 0.1, 5.0, 570, 960, 3.00, 84000.0, 1000.0),       # partie B2
}
# grille des prix des donnees quand elle differe du tick du micro (relecture du 25 octobre 2026) : le 6E standard cote
# par 0,00005 ; le tick traverse et les frais restent ceux du micro
PAS = {"6E": 0.00005}
PISTES = {"B": ["NQ", "ES", "RTY", "YM", "GC", "CL", "6E"], "B2": ["BTC"]}     # la partie D est dans nuit.py
# bitcoin (version 3) : avant le micro MBT (mai 2021), seul le contrat de 5 bitcoins existait et beaucoup de minutes sont
# sans transaction ; seance complete = premiere et derniere minute presentes et au moins 300 minutes sur 390 echangees
DEBUT_ENTRAINEMENT_B2 = np.datetime64("2020-01-01")
DEBUT_VALIDATION_B2 = np.datetime64("2021-07-01")
MINUTES_MIN = {"BTC": 300}
AUTRE_INDICE = {"NQ": "ES", "ES": "NQ"}       # famille F7

DEBUT_DONNEES = np.datetime64("2016-01-01")
DEBUT_ENTRAINEMENT = np.datetime64("2017-01-01")
DEBUT_VALIDATION = np.datetime64("2021-01-01")
FIN_RECHERCHE = np.datetime64("2022-12-31")
DEBUT_COFFRE = np.datetime64("2023-01-01")


def t_stat(x):
    x = np.asarray(x, float)
    if len(x) < 3:
        return 0.0
    sd = x.std(ddof=1)
    return float(x.mean() / sd * np.sqrt(len(x))) if sd > 0 else 0.0
