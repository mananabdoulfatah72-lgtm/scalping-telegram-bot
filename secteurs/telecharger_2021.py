#!/usr/bin/env python3
"""Telecharge (Yahoo) les actions de l'univers technologie de septembre 2021 absentes de prix.csv.gz
(test T6 de la fenetre 5 ans, README.md). Fichier separe : prix.csv.gz reste fige.
Sortie : secteurs/donnees/prix_2021.csv.gz (date, ticker, close, adjclose, volume)."""
import sys
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).parent))
import univers as U  # noqa: E402

SORTIE = Path(__file__).parent / "donnees" / "prix_2021.csv.gz"


def main():
    deja = set(pd.read_csv(Path(__file__).parent / "donnees" / "prix.csv.gz", usecols=["ticker"])["ticker"])
    tickers = [t for t in U.XLK_2021 if t not in deja]
    morceaux = []
    for t in tickers:
        for essai in range(4):
            x = yf.download(t, start="1998-01-01", end="2026-09-26", auto_adjust=False, progress=False, threads=False)
            if x is not None and len(x) >= 50:
                break
            time.sleep(10 * (essai + 1))
        else:
            sys.exit(f"{t} introuvable ; rien n'est enregistre")
        if isinstance(x.columns, pd.MultiIndex):
            x.columns = x.columns.get_level_values(0)
        x = x[["Close", "Adj Close", "Volume"]].rename(columns={"Close": "close", "Adj Close": "adjclose", "Volume": "volume"})
        x["ticker"] = t
        morceaux.append(x.reset_index().rename(columns={"Date": "date"}))
    d = pd.concat(morceaux)[["date", "ticker", "close", "adjclose", "volume"]]
    d.to_csv(SORTIE, index=False, float_format="%.6g")
    print(f"{tickers} : {len(d)} lignes", flush=True)


if __name__ == "__main__":
    main()
