#!/usr/bin/env python3
"""Bougies journalieres gratuites du radar (Yahoo, radar/donnees/jour/yahoo) -> CSV au format du bundle csvdir de zipline.
python3 extraire.py <dossier> : ecrit <dossier>/crypto/daily/{BTC,ETH,SOL}.csv et <dossier>/etf/daily/{QQQ,...}.csv"""
import glob
import json
import sys
from pathlib import Path

import pandas as pd

ICI = Path(__file__).resolve().parent
SORTIE = Path(sys.argv[1])
# zipline n'achete que des parts entieres : une part = 0,001 BTC, 0,01 ETH, 1 SOL (rendements inchanges)
ECHELLE = {"BTC": 1000.0, "ETH": 100.0, "SOL": 1.0}
ACTIFS = {"crypto": {"BTC": "BTC-USD", "ETH": "ETH-USD", "SOL": "SOL-USD"},
          "etf": {s: s for s in ("QQQ", "SPY", "IWM", "GLD", "TLT", "SMH")}}

d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(ICI.parent / "radar/donnees/jour/yahoo/*.csv.gz")))])
d[["sym", "champ"]] = d.serie.str.rsplit(":", n=1, expand=True)
for bundle, actifs in ACTIFS.items():
    (SORTIE / bundle / "daily").mkdir(parents=True, exist_ok=True)
    for nom, sym in actifs.items():
        x = d[d.sym == sym].pivot_table(index="date", columns="champ", values="valeur", aggfunc="last").dropna(subset=["o", "h", "l", "c"])
        x = x[x.index >= "2015-01-01"].sort_index()
        k = ECHELLE.get(nom, 1.0)
        v = x["v"].fillna(0) / (x["c"] / k if bundle == "crypto" else 1)      # volume des cryptos : dollars -> parts
        dates = pd.to_datetime(x.index)
        if bundle == "crypto":
            # calendrier 24/7 de zipline : a la cloture de la seance J, data.current() rend la ligne datee J-1 ; on date
            # donc la bougie du jour J au jour J-1 pour que la strategie voie bien la cloture du jour (verifie par sonde.py)
            dates = dates - pd.Timedelta(days=1)
        df = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "open": x.o.values / k, "high": x[["h", "o", "c"]].max(axis=1).values / k,
                           "low": x[["l", "o", "c"]].min(axis=1).values / k, "close": x.c.values / k,
                           "volume": v.clip(upper=4e9).round().astype("int64").values, "dividend": 0.0, "split": 1.0})
        df.to_csv(SORTIE / bundle / "daily" / f"{nom}.csv", index=False)
        print(bundle, nom, df.date.iloc[0], "->", df.date.iloc[-1], len(df), "bougies")
json.dump(ECHELLE, open(SORTIE / "echelles.json", "w"))
