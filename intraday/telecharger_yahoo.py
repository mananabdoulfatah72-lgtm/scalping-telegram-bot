#!/usr/bin/env python3
"""Barres horaires Yahoo des 2 dernieres annees (limite de Yahoo) pour SPY, QQQ, ES=F et NQ=F.
Pour SPY et QQQ, les barres commencent a 9 h 30, 10 h 30 ... et la derniere va de 15 h 30 a 16 h.
Ecrit intraday/donnees/yahoo_<ticker>_60m.csv.gz (t = debut de la barre, heure de New York)."""
from pathlib import Path

import pandas as pd
import yfinance as yf

SORTIE = Path(__file__).parent / "donnees"
SORTIE.mkdir(parents=True, exist_ok=True)
for ticker in ["SPY", "QQQ", "ES=F", "NQ=F"]:
    d = yf.download(ticker, period="730d", interval="60m", auto_adjust=False, progress=False, prepost=False)
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    t = d.index.tz_convert("America/New_York")
    out = pd.DataFrame({"t": t.strftime("%Y-%m-%d %H:%M"), "o": d["Open"].values, "h": d["High"].values,
                        "l": d["Low"].values, "c": d["Close"].values}).dropna()
    nom = ticker.replace("=F", "_fut").lower()
    out.to_csv(SORTIE / f"yahoo_{nom}_60m.csv.gz", index=False, compression="gzip", float_format="%.4f")
    print(f"{ticker}: {len(out)} barres du {out['t'].iloc[0]} au {out['t'].iloc[-1]} ; heures : {sorted(set(t.strftime('%H:%M')))[:12]}")
