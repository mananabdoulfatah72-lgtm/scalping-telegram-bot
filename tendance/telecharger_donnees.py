#!/usr/bin/env python3
"""Telecharge l'historique quotidien des marches utilises par le systeme de tendance.

- ETF (cours ajustes des dividendes) : servent a calculer les rendements depuis 20 ans.
- Futures en continu (=F) : servent a connaitre la taille en dollars des contrats micro.
- BTC / ETH au comptant, taux court americain (^IRX) et taux 10 ans (^TNX).

Sortie : tendance/donnees/prix.csv.gz (colonnes date, ticker, close, adjclose)
Lance par le workflow .github/workflows/donnees-tendance.yml (Yahoo n'est pas joignable ailleurs).
"""
import io
import sys
import time
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

ETF = ["SPY", "QQQ", "IWM", "DIA", "GLD", "SLV", "USO", "UNG", "CPER", "DBC", "DBA",
       "IEF", "TLT", "SHY", "FXE", "FXA", "FXB", "FXY", "FXC", "FXF", "UUP"]
FUTURES = ["ES=F", "NQ=F", "RTY=F", "YM=F", "GC=F", "SI=F", "CL=F", "NG=F", "HG=F",
           "ZN=F", "ZB=F", "ZF=F", "ZT=F", "6E=F", "6A=F", "6B=F", "6J=F", "6C=F", "6S=F",
           "BTC=F", "ETH=F"]
AUTRES = ["BTC-USD", "ETH-USD", "^IRX", "^TNX"]
SORTIE = Path(__file__).parent / "donnees" / "prix.csv.gz"


def yahoo(ticker):
    for essai in range(4):
        try:
            df = yf.download(ticker, start="1998-01-01", auto_adjust=False, progress=False, threads=False)
            if df is not None and len(df) > 50:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                return pd.DataFrame({"close": df["Close"], "adjclose": df["Adj Close"]})
        except Exception as e:  # noqa: BLE001
            print(f"  essai {essai + 1} {ticker}: {e}")
        time.sleep(5 * (essai + 1))
    return None


def stooq(ticker):
    """Repli pour les ETF americains si Yahoo refuse."""
    url = f"https://stooq.com/q/d/l/?s={ticker.lower()}.us&i=d"
    try:
        txt = requests.get(url, timeout=30).text
        df = pd.read_csv(io.StringIO(txt), parse_dates=["Date"], index_col="Date")
        return pd.DataFrame({"close": df["Close"], "adjclose": df["Close"]})
    except Exception as e:  # noqa: BLE001
        print(f"  stooq {ticker}: {e}")
        return None


def main():
    morceaux, manquants = [], []
    for t in ETF + FUTURES + AUTRES:
        df = yahoo(t)
        if df is None and t in ETF:
            df = stooq(t)
        if df is None:
            manquants.append(t)
            continue
        df = df.dropna()
        df.index.name = "date"
        df["ticker"] = t
        morceaux.append(df.reset_index())
        print(f"{t:8s} {df.index[0].date()} -> {df.index[-1].date()} ({len(df)} jours)")
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    tout = pd.concat(morceaux)[["date", "ticker", "close", "adjclose"]]
    tout.to_csv(SORTIE, index=False, compression="gzip", float_format="%.6g")
    print(f"\n{len(tout)} lignes -> {SORTIE}")
    if manquants:
        print("MANQUANTS:", ", ".join(manquants))
    return 0 if len(manquants) < 5 else 1


if __name__ == "__main__":
    sys.exit(main())
