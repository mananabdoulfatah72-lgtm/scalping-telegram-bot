#!/usr/bin/env python3
"""Telecharge chez Databento (jeu GLBX.MDP3) les barres d'une minute des futures E-mini S&P 500 (ES)
et E-mini Nasdaq 100 (NQ) de la CME, contrat le plus echange a chaque date (ES.v.0, NQ.v.0), puis
garde la seance americaine 9 h 30 - 16 h (heure de New York).

- La cle API est lue dans la variable d'environnement DATABENTO_API_KEY ; elle n'est jamais ecrite.
- Le cout est demande a Databento avant tout telechargement : si le total depasse PLAFOND dollars,
  la periode commence plus tard jusqu'a passer sous le plafond.
- Sortie : donnees/{sp500,nasdaq100}_1min.csv.gz, colonnes t (heure de New York), o, h, l, c,
  v (volume) et contrat (identifiant du contrat, pour reperer les changements d'echeance).
"""
import sys
from pathlib import Path

import pandas as pd
import databento as db

JEU, SCHEMA = "GLBX.MDP3", "ohlcv-1m"
SYMBOLES = {"sp500": "ES.v.0", "nasdaq100": "NQ.v.0"}
PLAFOND = 40.0                                   # dollars de credit Databento au maximum
DONNEES = Path(__file__).parent / "donnees"


def main():
    client = db.Historical()
    plage = client.metadata.get_dataset_range(dataset=JEU)
    fin = str(pd.Timestamp(plage["end"]).date())
    debut = None
    for annee in range(2010, 2026):
        d = "2010-06-07" if annee == 2010 else f"{annee}-01-01"
        cout = client.metadata.get_cost(dataset=JEU, symbols=list(SYMBOLES.values()), stype_in="continuous",
                                        schema=SCHEMA, start=d, end=fin)
        print(f"Cout ES + NQ du {d} au {fin} : {cout:.2f} $", flush=True)
        if cout <= PLAFOND:
            debut = d
            break
    if debut is None:
        sys.exit("Trop cher : rien n'a ete telecharge")
    DONNEES.mkdir(exist_ok=True)
    bornes = [debut] + [f"{a}-01-01" for a in range(int(debut[:4]) + 1, int(fin[:4]) + 1)] + [fin]
    for nom, sym in SYMBOLES.items():
        morceaux = []
        for a, b in zip(bornes[:-1], bornes[1:]):
            if a >= b:
                continue
            df = client.timeseries.get_range(dataset=JEU, symbols=[sym], stype_in="continuous",
                                             schema=SCHEMA, start=a, end=b).to_df()
            if df.empty:
                continue
            t = pd.to_datetime(df["ts_event"], utc=True) if "ts_event" in df.columns else df.index
            t = pd.DatetimeIndex(t)
            t = (t.tz_localize("UTC") if t.tz is None else t).tz_convert("America/New_York")
            minute = t.hour * 60 + t.minute
            garde = (minute >= 570) & (minute < 960) & (t.dayofweek < 5)
            prix = df[["open", "high", "low", "close"]].astype(float)
            if prix["close"].median() > 1e6:          # prix en entiers (1e-9) selon la version
                prix = prix / 1e9
            morceaux.append(pd.DataFrame({
                "t": t[garde].strftime("%Y-%m-%d %H:%M"),
                "o": prix["open"].values[garde], "h": prix["high"].values[garde],
                "l": prix["low"].values[garde], "c": prix["close"].values[garde],
                "v": df["volume"].values[garde], "contrat": df["instrument_id"].values[garde]}))
            print(f"  {sym} {a} -> {b} : {int(garde.sum())} minutes de seance", flush=True)
        out = pd.concat(morceaux, ignore_index=True).drop_duplicates("t", keep="last")
        out.to_csv(DONNEES / f"{nom}_1min.csv.gz", index=False, float_format="%.2f")
        print(f"{nom} : {len(out)} minutes du {out['t'].iloc[0]} au {out['t'].iloc[-1]}", flush=True)


if __name__ == "__main__":
    main()
