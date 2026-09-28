#!/usr/bin/env python3
"""Telecharge chez Databento (GLBX.MDP3, ohlcv-1h) les barres d'une heure ES et NQ (contrat le plus echange),
toutes les heures de la journee (session de nuit comprise), depuis juin 2010. Cle : DATABENTO_API_KEY (secret).
Sortie : nuit/donnees/{sp500,nasdaq100}_1h.csv.gz (t = debut de la barre, heure de New York)."""
import sys
from pathlib import Path

import databento as db
import pandas as pd

JEU, SCHEMA, PLAFOND = "GLBX.MDP3", "ohlcv-1h", 10.0
SYMBOLES = {"sp500": "ES.v.0", "nasdaq100": "NQ.v.0"}
SORTIE = Path(__file__).parent / "donnees"


def main():
    client = db.Historical()
    fin = pd.Timestamp(client.metadata.get_dataset_range(dataset=JEU)["end"]).isoformat()
    cout = client.metadata.get_cost(dataset=JEU, symbols=list(SYMBOLES.values()), stype_in="continuous",
                                    schema=SCHEMA, start="2010-06-07", end=fin)
    print(f"Cout : {cout:.2f} $", flush=True)
    if cout > PLAFOND:
        sys.exit("Trop cher : rien n'est telecharge")
    SORTIE.mkdir(exist_ok=True)
    for nom, sym in SYMBOLES.items():
        df = client.timeseries.get_range(dataset=JEU, symbols=[sym], stype_in="continuous", schema=SCHEMA,
                                         start="2010-06-07", end=fin).to_df()
        t = pd.to_datetime(df["ts_event"], utc=True) if "ts_event" in df.columns else df.index
        t = pd.DatetimeIndex(t)
        t = (t.tz_localize("UTC") if t.tz is None else t).tz_convert("America/New_York")
        prix = df[["open", "high", "low", "close"]].astype(float)
        if prix["close"].median() > 1e6:
            prix = prix / 1e9
        out = pd.DataFrame({"t": t.strftime("%Y-%m-%d %H:%M"), "o": prix["open"].values, "h": prix["high"].values,
                            "l": prix["low"].values, "c": prix["close"].values, "v": df["volume"].values,
                            "contrat": df["instrument_id"].values}).drop_duplicates("t", keep="last")
        out.to_csv(SORTIE / f"{nom}_1h.csv.gz", index=False, float_format="%.2f")
        print(f"{nom} : {len(out)} heures du {out['t'].iloc[0]} au {out['t'].iloc[-1]}", flush=True)


if __name__ == "__main__":
    main()
