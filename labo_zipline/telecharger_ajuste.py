#!/usr/bin/env python3
"""Lance par GitHub Actions (.github/workflows/donnees-ajustees.yml) : prix journaliers ajustes des dividendes et des
divisions (Yahoo, auto_adjust) des 22 fonds de la vague 2 -> labo_zipline/donnees/ajuste.csv.gz (date, sym, o, h, l, c)."""
from pathlib import Path

import pandas as pd
import yfinance as yf

FONDS = ["SPY", "QQQ", "IWM", "EFA", "EEM", "EWJ", "EWG", "EWZ", "FXI", "TLT", "IEF", "TIP", "HYG", "LQD", "GLD", "SLV",
         "USO", "UNG", "UUP", "FXE", "FXY", "VNQ"]
d = yf.download(FONDS, start="1993-01-01", auto_adjust=True, group_by="ticker", threads=True, progress=False)
lignes = []
for s in FONDS:
    x = d[s].dropna(subset=["Close"])
    print(s, x.index[0].date(), x.index[-1].date(), len(x))
    lignes.append(pd.DataFrame({"date": x.index.strftime("%Y-%m-%d"), "sym": s, "o": x.Open.values, "h": x.High.values,
                                "l": x.Low.values, "c": x.Close.values}))
sortie = Path(__file__).resolve().parent / "donnees/ajuste.csv.gz"
sortie.parent.mkdir(exist_ok=True)
pd.concat(lignes).round(6).to_csv(sortie, index=False)
print(sortie, sortie.stat().st_size // 1000, "ko")
