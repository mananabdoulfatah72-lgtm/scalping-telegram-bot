#!/usr/bin/env python3
"""Corrige l'heure des barres HistData deja converties (README.md) : HistData est a l'heure de New York AVEC le
changement d'heure (verifie : pic des chiffres de l'emploi et NQ Databento), pas a UTC - 5 h fixe. Les fichiers de
annees/ portaient t = heure HistData + 5 h ; on repasse a l'heure HistData puis a l'UTC vrai. Lancer une seule fois."""
from pathlib import Path

import pandas as pd

ICI = Path(__file__).resolve().parent

for f in sorted((ICI / "annees").glob("*_5m.csv.gz")):
    d = pd.read_csv(f)
    loc = pd.to_datetime(d["t"]) - pd.Timedelta(hours=5)                       # heure HistData (New York)
    utc = loc.dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC")
    ok = utc.notna()
    d = d[ok].assign(t=utc[ok].dt.strftime("%Y-%m-%d %H:%M")).drop_duplicates("t").sort_values("t")
    d.to_csv(f, index=False, compression="gzip")
    print(f"{f.name} : {len(d)} barres ({(~ok).sum()} retirees : heure qui n'existe pas ou en double au changement d'heure)")
