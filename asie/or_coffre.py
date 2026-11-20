#!/usr/bin/env python3
"""Test unique de l'or sur le coffre (asie/README.md, fixe le 20 novembre 2026 avant d'ouvrir 2023 - 2026) : achat a
18 h 00, vente a 23 h 30 (New York), lundi - jeudi soir. Usage : ASIE_DONNEES=<dossier> python3 asie/or_coffre.py"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import machine7 as M7  # noqa: E402

s = dict(nom="R1 xauusd achat 18:00->23:30", famille="R1", marche="xauusd", sens=1, sortie="23:30")
M = M7.Marche("xauusd")
d = M7.jouer(s, M, M7.DEBUT_COFFRE, M7.FIN)
an = pd.DatetimeIndex(d["jour"]).year
mgc = d["brut"] - 4.0 / (10 * d["e"])                     # MGC : 1 $ par ordre + 1 tick (1 $) par ordre, 10 onces
R = {"soirs": int(len(d)), "prix_or": [round(float(d["e"].iloc[0]), 1), round(float(d["e"].iloc[-1]), 1)],
     "brut_moyen_pb": round(float(d["brut"].mean()) * 1e4, 2)}
for nom, x in (("frais_2pb", d["r"]), ("frais_MGC", mgc)):
    par_an = {int(y): round(float(x[an == y].sum()) * 1e4, 1) for y in (2023, 2024, 2025, 2026)}
    dol = float((x * 10 * d["e"]).sum())                   # dollars pour 1 MGC (10 onces)
    R[nom] = dict(t=round(M7.t_stat(x), 2), net_moyen_pb=round(float(x.mean()) * 1e4, 2), par_an_pb=par_an,
                  dollars_1_MGC=round(dol), annees_positives=sum(v > 0 for v in par_an.values()))
R["passe"] = bool(R["frais_2pb"]["t"] >= 1.64 and R["frais_2pb"]["annees_positives"] >= 3)
(ICI / "or_coffre.json").write_text(json.dumps(R, indent=1, ensure_ascii=False))
print(json.dumps(R, indent=1, ensure_ascii=False))
