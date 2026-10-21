#!/usr/bin/env python3
"""Barres de 5 minutes de la seance americaine (9 h 30 - 16 h, New York) des ETF qui suivent chaque famille de futures
CME, chez Alpaca (offre gratuite, flux SIP), du 4 janvier 2016 a la veille. Ajustees des divisions (pas des dividendes :
sans effet sur un trade du jour). Ecrit donnees_libres/etf_5min/<ETF>.csv.gz (t heure de New York, o, h, l, c, v, n,
vw) et donnees_libres/etf_5min/resume.txt. Lance par .github/workflows/donnees-libres.yml.
Cles : ALPACA_API_KEY_ID et ALPACA_API_SECRET_KEY (secrets du depot, jamais ecrits ailleurs)."""
import os
import time
from pathlib import Path

import pandas as pd
import requests

ICI = Path(__file__).resolve().parent
SORTIE = ICI / "etf_5min"
URL = "https://data.alpaca.markets/v2/stocks/{}/bars"
PAR_MINUTE = 190
# ETF -> future CME qu'il suit
ETF = {
    "SPY": "ES", "QQQ": "NQ", "DIA": "YM", "IWM": "RTY",
    "TLT": "ZB", "IEF": "ZN", "IEI": "ZF", "SHY": "ZT",
    "GLD": "GC", "SLV": "SI", "CPER": "HG", "PPLT": "PL", "PALL": "PA",
    "USO": "CL", "BNO": "BZ", "UNG": "NG", "UGA": "RB",
    "FXE": "6E", "FXY": "6J", "FXB": "6B", "FXA": "6A", "FXC": "6C", "FXF": "6S", "UUP": "DX",
    "CORN": "ZC", "SOYB": "ZS", "WEAT": "ZW",
    "VXX": "VX", "BITO": "BTC",
}


class Alpaca:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update({"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY_ID"],
                               "APCA-API-SECRET-KEY": os.environ["ALPACA_API_SECRET_KEY"]})
        self.appels = []

    def get(self, url, params):
        for essai in range(8):
            now = time.time()
            self.appels = [x for x in self.appels if now - x < 60]
            if len(self.appels) >= PAR_MINUTE:
                time.sleep(60 - (now - self.appels[0]) + 0.1)
            self.appels.append(time.time())
            try:
                r = self.s.get(url, params=params, timeout=60)
            except requests.RequestException:
                time.sleep(5 * (essai + 1))
                continue
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(5 * (essai + 1))
                continue
            r.raise_for_status()
            return r.json()
        raise RuntimeError(f"Alpaca : pas de reponse pour {url}")


def barres(api, etf, debut, fin):
    params = {"timeframe": "5Min", "start": debut, "end": fin, "limit": 10000, "adjustment": "split", "feed": "sip"}
    lignes = []
    while True:
        x = api.get(URL.format(etf), params)
        lignes += x.get("bars") or []
        jeton = x.get("next_page_token")
        if not jeton:
            break
        params["page_token"] = jeton
    if not lignes:
        return pd.DataFrame()
    d = pd.DataFrame(lignes)
    t = pd.to_datetime(d["t"], utc=True).dt.tz_convert("America/New_York")
    hm = t.dt.hour * 60 + t.dt.minute
    d = d[(hm >= 570) & (hm < 960)].copy()
    d["t"] = t[d.index].dt.strftime("%Y-%m-%d %H:%M")
    return d[["t", "o", "h", "l", "c", "v", "n", "vw"]]


def main():
    SORTIE.mkdir(parents=True, exist_ok=True)
    api = Alpaca()
    fin = (pd.Timestamp.now(tz="UTC").normalize() - pd.Timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    resume = []
    for etf, fut in ETF.items():
        try:
            d = barres(api, etf, "2016-01-01T00:00:00Z", fin)
        except Exception as e:
            print(f"::warning::{etf} : ECHEC {type(e).__name__} {str(e)[:200]}")
            resume.append(f"{etf} ({fut}) : ECHEC {type(e).__name__}")
            continue
        if d.empty:
            resume.append(f"{etf} ({fut}) : aucune barre")
            continue
        d.to_csv(SORTIE / f"{etf}.csv.gz", index=False, compression="gzip")
        jours = d["t"].str[:10]
        ligne = (f"{etf} ({fut}) : {len(d)} barres, {jours.nunique()} seances, {d['t'].iloc[0]} -> {d['t'].iloc[-1]},"
                 f" barres par seance (mediane) {int(jours.value_counts().median())}")
        print(ligne, flush=True)
        resume.append(ligne)
    (SORTIE / "resume.txt").write_text("\n".join(resume) + "\n")


if __name__ == "__main__":
    main()
