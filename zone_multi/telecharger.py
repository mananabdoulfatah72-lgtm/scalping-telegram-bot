#!/usr/bin/env python3
"""Telecharge chez Databento (GLBX.MDP3, ohlcv-1m, contrat le plus echange) les barres d'une minute de RTY, YM,
GC, CL et 6E, garde la seance de chaque marche (README.md). ES et NQ viennent de intraday/donnees.
Le cout est demande avant : si le total depasse PLAFOND, la periode commence plus tard (meme debut pour tous).
Cle : DATABENTO_API_KEY (secret). Sortie : zone_multi/donnees/{nom}_1min.csv.gz (t, o, h, l, c, v, contrat)."""
import sys
from pathlib import Path

import databento as db
import pandas as pd

JEU, SCHEMA, PLAFOND = "GLBX.MDP3", "ohlcv-1m", 70.0
MARCHES = {"russell": ("RTY.v.0", 570, 960), "dow": ("YM.v.0", 570, 960), "or": ("GC.v.0", 500, 810),
           "petrole": ("CL.v.0", 540, 870), "euro": ("6E.v.0", 500, 900)}
SORTIE = Path(__file__).parent / "donnees"


def main():
    client = db.Historical()
    fin = pd.Timestamp(client.metadata.get_dataset_range(dataset=JEU)["end"]).isoformat()
    symboles = [v[0] for v in MARCHES.values()]
    debut = None
    for annee in range(2011, 2024):
        cout = client.metadata.get_cost(dataset=JEU, symbols=symboles, stype_in="continuous", schema=SCHEMA,
                                        start=f"{annee}-01-01", end=fin)
        print(f"Cout des 5 marches depuis {annee} : {cout:.2f} $", flush=True)
        if cout <= PLAFOND:
            debut = f"{annee}-01-01"
            break
    if debut is None:
        sys.exit("Trop cher : rien n'est telecharge")
    SORTIE.mkdir(exist_ok=True)
    bornes = [debut] + [f"{a}-01-01" for a in range(int(debut[:4]) + 1, int(fin[:4]) + 1)] + [fin]
    for nom, (sym, m0, m1) in MARCHES.items():
        morceaux = []
        for a, b in zip(bornes[:-1], bornes[1:]):
            df = client.timeseries.get_range(dataset=JEU, symbols=[sym], stype_in="continuous", schema=SCHEMA,
                                             start=a, end=b).to_df()
            if df.empty:
                continue
            t = pd.to_datetime(df["ts_event"], utc=True) if "ts_event" in df.columns else df.index
            t = pd.DatetimeIndex(t)
            t = (t.tz_localize("UTC") if t.tz is None else t).tz_convert("America/New_York")
            minute = t.hour * 60 + t.minute
            garde = (minute >= m0) & (minute < m1) & (t.dayofweek < 5)
            prix = df[["open", "high", "low", "close"]].astype(float)
            if prix["close"].median() > 1e6:
                prix = prix / 1e9
            morceaux.append(pd.DataFrame({
                "t": t[garde].strftime("%Y-%m-%d %H:%M"), "o": prix["open"].values[garde], "h": prix["high"].values[garde],
                "l": prix["low"].values[garde], "c": prix["close"].values[garde], "v": df["volume"].values[garde],
                "contrat": df["instrument_id"].values[garde]}))
        out = pd.concat(morceaux, ignore_index=True).drop_duplicates("t", keep="last")
        out.to_csv(SORTIE / f"{nom}_1min.csv.gz", index=False, float_format="%.6g")
        print(f"{nom} ({sym}) : {len(out)} minutes du {out['t'].iloc[0]} au {out['t'].iloc[-1]}", flush=True)


if __name__ == "__main__":
    main()
