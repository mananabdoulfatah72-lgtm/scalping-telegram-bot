#!/usr/bin/env python3
"""Barres d'une minute Dukascopy (UTC) -> barres de 5 minutes (UTC). Ecrit sessions24/donnees/<code>_5m.csv.gz
(t = debut de la barre en UTC, o, h, l, c). Usage : python3 sessions24/preparer.py <code dukascopy>"""
import glob
import sys
from pathlib import Path

import pandas as pd

SORTIE = Path(__file__).parent / "donnees"


def main(inst):
    morceaux = []
    for f in sorted(glob.glob(f"brut/{inst}_*.csv")):
        try:
            d = pd.read_csv(f)
        except pd.errors.EmptyDataError:
            print(f"{f}: vide")
            continue
        if not d.empty:
            morceaux.append(d)
    if not morceaux:
        sys.exit(f"{inst}: aucune donnee")
    d = pd.concat(morceaux).drop_duplicates("timestamp").sort_values("timestamp")
    t = pd.to_datetime(d["timestamp"], unit="ms", utc=True)
    d = d.set_index(t)[["open", "high", "low", "close"]]
    b = d.resample("5min", label="left", closed="left").agg({"open": "first", "high": "max", "low": "min",
                                                              "close": "last"}).dropna()
    nd = 5 if b["close"].median() < 50 else 3
    out = pd.DataFrame({"t": b.index.strftime("%Y-%m-%d %H:%M"), "o": b["open"].round(nd), "h": b["high"].round(nd),
                        "l": b["low"].round(nd), "c": b["close"].round(nd)})
    SORTIE.mkdir(parents=True, exist_ok=True)
    out.to_csv(SORTIE / f"{inst}_5m.csv.gz", index=False, compression="gzip")
    print(f"{inst}: {len(out)} barres de 5 min, du {out['t'].iloc[0]} au {out['t'].iloc[-1]} (UTC)")


if __name__ == "__main__":
    main(sys.argv[1])
