#!/usr/bin/env python3
"""Vague 4, partie B (README.md) : minutes des 10 plus grosses valeurs du Nasdaq 100 chez Alpaca (offre gratuite, flux
SIP), 2016 - septembre 2026, de 9 h 30 a 16 h (heure de New York). On garde, par valeur et par seance, l'ouverture de
9 h 30 et la cloture de chaque demi-heure (minutes 9 h 59, 10 h 29, ..., 15 h 59). Ecrit donnees/grandes.csv.gz.
Cles : ALPACA_API_KEY_ID et ALPACA_API_SECRET_KEY (secrets du depot, jamais ecrits ailleurs)."""
import os
import time
from pathlib import Path

import pandas as pd
import requests

ICI = Path(__file__).resolve().parent
URL = "https://data.alpaca.markets/v2/stocks/bars"
VALEURS = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "TSLA", "COST", "NFLX"]
PAR_MINUTE = 190


class Alpaca:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update({"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY_ID"],
                               "APCA-API-SECRET-KEY": os.environ["ALPACA_API_SECRET_KEY"]})
        self.appels = []

    def get(self, params):
        for essai in range(6):
            now = time.time()
            self.appels = [x for x in self.appels if now - x < 60]
            if len(self.appels) >= PAR_MINUTE:
                time.sleep(60 - (now - self.appels[0]) + 0.1)
            self.appels.append(time.time())
            r = self.s.get(URL, params=params, timeout=60)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(5 * (essai + 1))
                continue
            if r.status_code in (401, 403):
                raise SystemExit(f"Alpaca refuse l'acces ({r.status_code})")
            r.raise_for_status()
            return r.json()
        raise RuntimeError(f"Alpaca : echec apres plusieurs essais ({params})")

    def barres(self, symbole, debut, fin):
        out, token = [], None
        while True:
            p = {"symbols": symbole, "timeframe": "1Min", "start": debut, "end": fin, "limit": 10000, "feed": "sip",
                 "adjustment": "raw", "sort": "asc"}
            if token:
                p["page_token"] = token
            j = self.get(p)
            out += (j.get("bars") or {}).get(symbole) or []
            token = j.get("next_page_token")
            if not token:
                return out


def resume(barres):
    """Par seance : ouverture de 9 h 30 et cloture de chaque demi-heure (derniere minute connue avant la fin)."""
    if not barres:
        return pd.DataFrame()
    d = pd.DataFrame(barres)
    t = pd.to_datetime(d["t"], utc=True).dt.tz_convert("America/New_York")
    m = t.dt.hour * 60 + t.dt.minute - 570
    d = d.assign(jour=t.dt.strftime("%Y-%m-%d"), m=m)
    d = d[(d["m"] >= 0) & (d["m"] < 390)]
    lignes = []
    for jour, g in d.groupby("jour"):
        g = g.sort_values("m")
        x = {"jour": jour, "ouverture": g["o"].iloc[0] if g["m"].iloc[0] == 0 else float("nan")}
        for k in range(1, 14):
            h = g[g["m"] <= 30 * k - 1]
            x[f"c{30 * k}"] = h["c"].iloc[-1] if len(h) else float("nan")
        lignes.append(x)
    return pd.DataFrame(lignes)


def main():
    a = Alpaca()
    (ICI / "donnees").mkdir(exist_ok=True)
    tout = []
    for s in VALEURS:
        for annee in range(2016, 2027):
            debut, fin = f"{annee}-01-01T00:00:00Z", (f"{annee + 1}-01-01T00:00:00Z" if annee < 2026 else "2026-10-01T00:00:00Z")
            r = resume(a.barres(s, debut, fin))
            if len(r):
                tout.append(r.assign(valeur=s))
            print(f"{s} {annee} : {len(r)} seances", flush=True)
    pd.concat(tout).to_csv(ICI / "donnees" / "grandes.csv.gz", index=False, float_format="%.4f",
                           compression={"method": "gzip", "mtime": 0})


if __name__ == "__main__":
    main()
