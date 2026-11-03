"""Chargement des donnees du labo ML : NQ minute (seances 9 h 30 - 16 h New York) et radar quotidien (Yahoo)."""
import glob
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "audit/machine6"))
import pyramide as P  # noqa: E402  (jours(), supertrend() : moteur verifie)

N = 390
PREF = 28500.0          # dollars "au prix d'aujourd'hui"
FRAIS = 3.0             # $ par aller-retour et par MNQ
SORTIE = Path(__file__).resolve().parent / "resultats"
SORTIE.mkdir(exist_ok=True)


def chemin_minutes():
    """Minutes NQ 2011 -> 2 nov. 2026 (variable MINUTES_NQ), sinon l'historique du robot du depot."""
    return os.environ.get("MINUTES_NQ") or str(RACINE / "zone/robot/nq_1min.csv.gz")


def nq_minutes(csv=None):
    """J (jours), O, H, L, C, V (seances x 390), ok (seance complete)."""
    csv = csv or chemin_minutes()
    J, O, H, L, C, ok = P.jours(csv)
    d = pd.read_csv(csv, usecols=["t", "v"])
    j = d.t.str[:10]
    m = d.t.str[11:13].astype(int) * 60 + d.t.str[14:16].astype(int) - 570
    g = (m >= 0) & (m < N)
    V = np.zeros((len(J), N))
    V[pd.Index(J).get_indexer(j[g]), m[g].to_numpy()] = d.v[g].to_numpy(float)
    return J, O, H, L, C, V, ok


def radar(champ="c"):
    """Cours quotidiens du radar : DataFrame dates x series (champ c = cloture)."""
    morceaux = []
    for f in sorted(glob.glob(str(RACINE / "radar/donnees/jour/yahoo/*.csv.gz"))):
        d = pd.read_csv(f)
        d = d[d.serie.str.endswith(":" + champ)]
        morceaux.append(d)
    d = pd.concat(morceaux)
    d["serie"] = d.serie.str[:-2]
    t = d.pivot_table(index="date", columns="serie", values="valeur", aggfunc="last")
    t.index = pd.to_datetime(t.index)
    return t.sort_index()


def ecrire(nom, texte):
    (SORTIE / nom).write_text(texte)
    print(texte)
