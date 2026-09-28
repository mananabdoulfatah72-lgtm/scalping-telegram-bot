#!/usr/bin/env python3
"""Telecharge (Yahoo) les cours quotidiens depuis 1998 : SPY, 11 ETF de secteurs, ETF d'industries,
les 15-20 plus grosses actions de chaque secteur, taux, VIX, petrole, cuivre, or, dollar.
Sortie : secteurs/donnees/prix.csv.gz (date, ticker, close, adjclose, volume)."""
import sys
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).parent))
import univers as U  # noqa: E402

SORTIE = Path(__file__).parent / "donnees" / "prix.csv.gz"


def main():
    tickers = [U.MARCHE] + list(U.SECTEURS) + U.INDUSTRIES + sorted({a for l in U.ACTIONS.values() for a in l}) + U.MACRO
    morceaux, manquants = [], []
    for k in range(0, len(tickers), 25):
        lot = tickers[k:k + 25]
        for essai in range(4):
            try:
                df = yf.download(lot, start="1998-01-01", auto_adjust=False, progress=False, group_by="ticker", threads=True)
                break
            except Exception as e:  # noqa: BLE001
                print(f"  essai {essai + 1} : {e}", flush=True)
                time.sleep(10 * (essai + 1))
        for t in lot:
            try:
                x = df[t][["Close", "Adj Close", "Volume"]].dropna(subset=["Close"])
            except Exception:  # noqa: BLE001
                x = None
            if x is None or len(x) < 50:
                manquants.append(t)
                continue
            x = x.rename(columns={"Close": "close", "Adj Close": "adjclose", "Volume": "volume"})
            x["ticker"] = t
            morceaux.append(x.reset_index().rename(columns={"Date": "date"}))
        print(f"{min(k + 25, len(tickers))}/{len(tickers)}", flush=True)
    d = pd.concat(morceaux)[["date", "ticker", "close", "adjclose", "volume"]]
    d.to_csv(SORTIE, index=False, float_format="%.6g")
    print(f"{d['ticker'].nunique()} tickers, {len(d)} lignes ; manquants : {manquants}", flush=True)


if __name__ == "__main__":
    main()
