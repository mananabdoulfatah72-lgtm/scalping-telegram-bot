#!/usr/bin/env python3
"""Telecharge les bougies d'une minute du DOGE/USDT (Binance, archive publique data.binance.vision)
depuis juillet 2019 et les regroupe en bougies de 5 minutes (heure UTC) : donnees/doge_5min.csv.gz."""
import io
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

D = Path(__file__).parent / "donnees"
BASE = "https://data.binance.vision/data/spot"


def lire(url):
    for k in range(4):
        r = requests.get(url, timeout=60)
        if r.status_code == 404:
            return None
        if r.ok:
            z = zipfile.ZipFile(io.BytesIO(r.content))
            return pd.read_csv(z.open(z.namelist()[0]), header=None, usecols=range(6),
                               names=["t", "o", "h", "l", "c", "v"])
        time.sleep(3 * (k + 1))
    raise RuntimeError(f"echec {url} ({r.status_code})")


def main():
    morceaux = []
    fin = pd.Timestamp.utcnow().tz_localize(None).normalize()
    for m in pd.period_range("2019-07", (fin - pd.offsets.MonthBegin(1)).strftime("%Y-%m"), freq="M"):
        x = lire(f"{BASE}/monthly/klines/DOGEUSDT/1m/DOGEUSDT-1m-{m}.zip")
        if x is None:
            for j in pd.date_range(m.start_time, m.end_time.normalize(), freq="D"):
                y = lire(f"{BASE}/daily/klines/DOGEUSDT/1m/DOGEUSDT-1m-{j.date()}.zip")
                if y is not None:
                    morceaux.append(y)
        else:
            morceaux.append(x)
        print(m, flush=True)
    for j in pd.date_range(fin.replace(day=1), fin - pd.Timedelta(days=1), freq="D"):
        y = lire(f"{BASE}/daily/klines/DOGEUSDT/1m/DOGEUSDT-1m-{j.date()}.zip")
        if y is not None:
            morceaux.append(y)
    d = pd.concat(morceaux)
    unite = "us" if d["t"].max() > 1e15 else "ms"          # l'archive passe aux microsecondes en 2025
    d["t"] = pd.to_datetime(d["t"].where(d["t"] > 1e15, d["t"] * 1000), unit="us")
    d = d.drop_duplicates("t").set_index("t").sort_index()
    b = d.resample("5min").agg({"o": "first", "h": "max", "l": "min", "c": "last", "v": "sum"}).dropna()
    b.to_csv(D / "doge_5min.csv.gz", float_format="%.6g")
    print(f"{len(d)} minutes -> {len(b)} bougies de 5 minutes, du {b.index[0]} au {b.index[-1]} (UTC) [{unite}]", flush=True)


if __name__ == "__main__":
    main()
