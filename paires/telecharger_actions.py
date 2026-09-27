#!/usr/bin/env python3
"""Cours journaliers ajustes (Yahoo) des actions des paires classiques, depuis 2005.
Ecrit paires/donnees/actions.csv.gz (colonnes = tickers)."""
from pathlib import Path

import pandas as pd
import yfinance as yf

TICKERS = ["V", "MA", "KO", "PEP", "XOM", "CVX", "HD", "LOW", "GS", "MS", "UPS", "FDX",
           "JPM", "BAC", "T", "VZ", "MCD", "YUM", "WMT", "TGT", "COST", "BJ"]
d = yf.download(TICKERS, start="2005-01-01", auto_adjust=True, progress=False)["Close"]
sortie = Path(__file__).parent / "donnees" / "actions.csv.gz"
sortie.parent.mkdir(parents=True, exist_ok=True)
d.to_csv(sortie, compression="gzip", float_format="%.4f")
print(d.notna().sum().to_string())
