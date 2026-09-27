#!/usr/bin/env python3
"""Barres d'une heure (Dukascopy, UTC) -> heure de New York, jours de semaine, 9 h - 16 h.
Ecrit intraday/donnees/<indice>_1h.csv.gz (t = debut de la barre, heure de New York)."""
from pathlib import Path

import pandas as pd

SORTIE = Path(__file__).parent / "donnees"
NOMS = {"usa500idxusd": "sp500", "usatechidxusd": "nasdaq100"}

for inst, nom in NOMS.items():
    d = pd.read_csv(f"brut_h/{inst}.csv").drop_duplicates("timestamp").sort_values("timestamp")
    t = pd.to_datetime(d["timestamp"], unit="ms", utc=True).dt.tz_convert("America/New_York")
    garde = ((t.dt.dayofweek < 5) & (t.dt.hour >= 9) & (t.dt.hour <= 15)).values
    d, t = d[garde], t[garde]
    out = pd.DataFrame({"t": t.dt.strftime("%Y-%m-%d %H:%M").values, "o": d["open"].round(2).values,
                        "h": d["high"].round(2).values, "l": d["low"].round(2).values, "c": d["close"].round(2).values})
    SORTIE.mkdir(parents=True, exist_ok=True)
    out.to_csv(SORTIE / f"{nom}_1h.csv.gz", index=False, compression="gzip")
    print(f"{nom}: {len(out)} barres, du {out['t'].iloc[0]} au {out['t'].iloc[-1]}")
