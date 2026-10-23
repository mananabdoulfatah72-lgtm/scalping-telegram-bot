#!/usr/bin/env python3
"""VXN (volatilite implicite a 30 jours du Nasdaq 100, Cboe), cloture du jour, sources gratuites sans cle :
fichier officiel du Cboe, FRED (VXNCLS) et Yahoo (^VXN). Pour etude_large/zone_implicite/ (regles fixees avant).
Ecrit donnees_libres/vxn/{cboe,fred,yahoo}.csv.gz (t, o, h, l, c ; FRED : t, c) et resume.txt.
Lance par .github/workflows/donnees-vxn.yml."""
import io
import time
from pathlib import Path

import pandas as pd
import requests

ICI = Path(__file__).resolve().parent
SORTIE = ICI / "vxn"
CBOE = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VXN_History.csv"
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VXNCLS"


def lire(url):
    for essai in range(4):
        try:
            r = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"{url} : essai {essai + 1} ({type(e).__name__})")
            time.sleep(5 * (essai + 1))
    return None


def cboe():
    t = lire(CBOE)
    if not t:
        return None
    d = pd.read_csv(io.StringIO(t))
    d.columns = [c.strip().upper() for c in d.columns]
    return pd.DataFrame({"t": pd.to_datetime(d["DATE"]).dt.strftime("%Y-%m-%d"), "o": d["OPEN"], "h": d["HIGH"],
                         "l": d["LOW"], "c": d["CLOSE"]}).dropna(subset=["c"])


def fred():
    t = lire(FRED)
    if not t:
        return None
    d = pd.read_csv(io.StringIO(t), na_values=["."])
    return pd.DataFrame({"t": pd.to_datetime(d.iloc[:, 0]).dt.strftime("%Y-%m-%d"), "c": d.iloc[:, 1]}).dropna()


def yahoo():
    import yfinance as yf
    for essai in range(4):
        try:
            d = yf.download("^VXN", interval="1d", period="max", progress=False, auto_adjust=False,
                            multi_level_index=False, threads=False)
            if d is not None and len(d):
                return pd.DataFrame({"t": pd.DatetimeIndex(d.index).strftime("%Y-%m-%d"), "o": d["Open"].to_numpy(),
                                     "h": d["High"].to_numpy(), "l": d["Low"].to_numpy(),
                                     "c": d["Close"].to_numpy()}).dropna(subset=["c"])
        except Exception as e:
            print(f"^VXN : essai {essai + 1} ({type(e).__name__})")
        time.sleep(5 * (essai + 1))
    return None


def main():
    SORTIE.mkdir(parents=True, exist_ok=True)
    resume = []
    for nom, f in (("cboe", cboe), ("fred", fred), ("yahoo", yahoo)):
        try:
            d = f()
        except Exception as e:
            print(f"::warning::{nom} : {type(e).__name__} {e}")
            d = None
        if d is None or not len(d):
            resume.append(f"{nom} : rien")
            print(f"::warning::{nom} : rien")
            continue
        d.to_csv(SORTIE / f"{nom}.csv.gz", index=False, compression="gzip")
        ligne = f"{nom} : {len(d)} jours, {d['t'].iloc[0]} -> {d['t'].iloc[-1]}, derniere cloture {d['c'].iloc[-1]}"
        print(ligne, flush=True)
        resume.append(ligne)
    (SORTIE / "resume.txt").write_text("\n".join(resume) + "\n")


if __name__ == "__main__":
    main()
