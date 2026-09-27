#!/usr/bin/env python3
"""Garde la seance americaine (9 h 30 - 16 h, heure de New York) des prix minute Dukascopy
et ecrit intraday/donnees/<indice>_1min.csv.gz (colonnes t, o, h, l, c ; t = heure de New York)."""
import glob
from pathlib import Path

import pandas as pd

SORTIE = Path(__file__).parent / "donnees"
NOMS = {"usa500idxusd": "sp500", "usatechidxusd": "nasdaq100"}


def main():
    SORTIE.mkdir(parents=True, exist_ok=True)
    for inst, nom in NOMS.items():
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
            print(f"{nom}: aucune donnee")
            continue
        d = pd.concat(morceaux).drop_duplicates("timestamp").sort_values("timestamp")
        t = pd.to_datetime(d["timestamp"], unit="ms", utc=True).dt.tz_convert("America/New_York")
        minutes = t.dt.hour * 60 + t.dt.minute
        garde = (t.dt.dayofweek < 5) & (minutes >= 9 * 60 + 30) & (minutes < 16 * 60)
        d = d[garde.values]
        t = t[garde.values]
        out = pd.DataFrame({"t": t.dt.strftime("%Y-%m-%d %H:%M").values,
                            "o": d["open"].round(2).values, "h": d["high"].round(2).values,
                            "l": d["low"].round(2).values, "c": d["close"].round(2).values})
        out.to_csv(SORTIE / f"{nom}_1min.csv.gz", index=False, compression="gzip")
        jours = out["t"].str[:10].nunique()
        print(f"{nom}: {len(out)} minutes, {jours} seances, du {out['t'].iloc[0]} au {out['t'].iloc[-1]}")


if __name__ == "__main__":
    main()
