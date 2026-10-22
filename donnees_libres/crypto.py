#!/usr/bin/env python3
"""Bitcoin et ether au comptant, barres de 5 minutes, gratuites et sans cle : Coinbase Exchange (BTC-USD, ETH-USD, en
dollars, l'une des bourses du prix de reference des futures CME). Secours : Binance (data.binance.vision, BTCUSDT /
ETHUSDT) si Coinbase ne repond pas.
Ecrit donnees_libres/crypto/<symbole>_<annee>_5m.csv.gz : t (debut de la barre, heure de New York), o, h, l, c, v ;
et donnees_libres/crypto/resume.txt. Lance par .github/workflows/donnees-crypto.yml (argument : BTC ou ETH)."""
import io
import sys
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

ICI = Path(__file__).resolve().parent
D = ICI / "crypto"
DEBUT = datetime(2017, 1, 1, tzinfo=timezone.utc)
FIN = datetime(2026, 10, 21, tzinfo=timezone.utc)
PAQUET = timedelta(minutes=5 * 300)
S = requests.Session()
S.headers.update({"User-Agent": "recherche-etude-large/1.0"})


def coinbase(produit):
    lignes, t, erreurs = [], DEBUT, 0
    while t < FIN:
        fin = min(t + PAQUET, FIN)
        try:
            r = S.get(f"https://api.exchange.coinbase.com/products/{produit}/candles",
                      params={"granularity": 300, "start": t.isoformat(), "end": fin.isoformat()}, timeout=30)
        except requests.RequestException:
            r = None
        if r is None or r.status_code == 429 or r.status_code >= 500:
            erreurs += 1
            if erreurs > 50:
                raise RuntimeError("Coinbase ne repond plus")
            time.sleep(2 + erreurs)
            continue
        r.raise_for_status()
        lignes += r.json()
        t = fin
        time.sleep(0.12)
    d = pd.DataFrame(lignes, columns=["t", "l", "h", "o", "c", "v"])
    d["t"] = pd.to_datetime(d["t"], unit="s", utc=True)
    return d


def binance(paire):
    morceaux = []
    m = datetime(DEBUT.year, DEBUT.month, 1)
    while m < FIN.replace(tzinfo=None):
        u = f"https://data.binance.vision/data/spot/monthly/klines/{paire}/5m/{paire}-5m-{m:%Y-%m}.zip"
        r = S.get(u, timeout=60)
        if r.status_code == 200:
            z = zipfile.ZipFile(io.BytesIO(r.content))
            x = pd.read_csv(z.open(z.namelist()[0]), header=None, usecols=range(6))
            x.columns = ["t", "o", "h", "l", "c", "v"]
            unite = "us" if x["t"].iloc[0] > 1e14 else "ms"
            x["t"] = pd.to_datetime(x["t"], unit=unite, utc=True)
            morceaux.append(x)
        m = (m + timedelta(days=32)).replace(day=1)
    return pd.concat(morceaux, ignore_index=True)


def main():
    nom = sys.argv[1]
    D.mkdir(parents=True, exist_ok=True)
    try:
        d, source = coinbase(f"{nom}-USD"), f"Coinbase {nom}-USD"
    except Exception as e:  # noqa: BLE001
        print(f"Coinbase en echec ({e}) : Binance")
        d, source = binance(f"{nom}USDT"), f"Binance {nom}USDT"
    d = d.drop_duplicates("t").sort_values("t")
    d["t"] = d["t"].dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d %H:%M")
    d = d[["t", "o", "h", "l", "c", "v"]]
    resume = []
    for an, x in d.groupby(d["t"].str[:4]):
        x.to_csv(D / f"{nom.lower()}_{an}_5m.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
        resume.append(f"{nom} ({source}) {an} : {len(x)} barres ({x['t'].iloc[0]} -> {x['t'].iloc[-1]}, New York)")
    (D / f"resume_{nom.lower()}.txt").write_text("\n".join(resume) + "\n")
    print("\n".join(resume))


if __name__ == "__main__":
    main()
