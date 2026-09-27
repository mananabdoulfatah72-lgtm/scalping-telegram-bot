#!/usr/bin/env python3
"""Taux d'interet a 3 mois (OECD, via FRED, mensuels) des pays des devises testees.
Ecrit tendance/donnees/taux_3m.csv (une colonne par pays, en % par an)."""
import io
from pathlib import Path

import pandas as pd
import requests

SERIES = {"US": "IR3TIB01USM156N", "AU": "IR3TIB01AUM156N", "EZ": "IR3TIB01EZM156N", "GB": "IR3TIB01GBM156N",
          "JP": "IR3TIB01JPM156N", "CA": "IR3TIB01CAM156N", "CH": "IR3TIB01CHM156N"}
colonnes = {}
for pays, sid in SERIES.items():
    txt = requests.get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}", timeout=60).text
    d = pd.read_csv(io.StringIO(txt))
    d.columns = ["date", pays]
    d["date"] = pd.to_datetime(d["date"])
    colonnes[pays] = pd.to_numeric(d.set_index("date")[pays], errors="coerce")
    print(f"{pays}: {colonnes[pays].dropna().index[0].date()} -> {colonnes[pays].dropna().index[-1].date()}")
sortie = Path(__file__).parent / "donnees" / "taux_3m.csv"
pd.DataFrame(colonnes).to_csv(sortie)
print("->", sortie)
