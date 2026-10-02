#!/usr/bin/env python3
"""Transactions du QQQ chez Alpaca (offre gratuite, flux SIP) pour le filtre H1 (README.md, « version Alpaca ») :
fenetres de validation (avril - septembre 2026 : 99 trades de zone + 300 fenetres de controle) puis fenetres des trades
de zone de 2016 a mars 2026. Cote acheteur / vendeur par la regle du tick. Ecrit donnees_alpaca/validation.csv.gz et
donnees_alpaca/test.csv.gz (jour, minute depuis 9 h 30, achats, ventes, transactions).
Cles : ALPACA_API_KEY_ID et ALPACA_API_SECRET_KEY (secrets du depot, jamais ecrits ailleurs)."""
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ICI = Path(__file__).resolve().parent
D = ICI / "donnees_alpaca"
URL = "https://data.alpaca.markets/v2/stocks/QQQ/trades"
EXCLUES = set("BCGHMNPQRTUVWZ479")
PAR_MINUTE, FENETRE = 190, 30
CONTROLES = range(30, 390, 30)


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
                raise SystemExit(f"Alpaca refuse l'acces ({r.status_code}) : verifier les secrets ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY")
            r.raise_for_status()
            return r.json()
        raise RuntimeError(f"Alpaca : echec apres plusieurs essais ({params})")

    def transactions(self, debut, fin):
        out, token = [], None
        while True:
            p = {"start": debut, "end": fin, "limit": 10000, "feed": "sip", "sort": "asc"}
            if token:
                p["page_token"] = token
            j = self.get(p)
            out += j.get("trades") or []
            token = j.get("next_page_token")
            if not token:
                return out


def par_minute(jour, trades):
    """Regle du tick sur les transactions regulieres, agregee par minute (depuis 9 h 30, heure de New York)."""
    t = [x for x in trades if not (set(x.get("c") or []) & EXCLUES)]
    if not t:
        return pd.DataFrame(columns=["jour", "minute", "achats", "ventes", "transactions"])
    p = np.array([x["p"] for x in t], float)
    q = np.array([x["s"] for x in t], float)
    sens = np.sign(np.diff(p, prepend=p[0]))
    for i in range(1, len(sens)):               # au meme prix : le cote de la transaction precedente
        if sens[i] == 0:
            sens[i] = sens[i - 1]
    ts = pd.to_datetime([x["t"] for x in t], utc=True, format="ISO8601").tz_convert("America/New_York")
    minute = ((ts - ts.normalize()).total_seconds() // 60 - 570).astype(int)
    x = pd.DataFrame({"minute": minute, "achats": np.where(sens > 0, q, 0), "ventes": np.where(sens < 0, q, 0), "transactions": 1})
    x = x.groupby("minute", as_index=False).sum()
    x.insert(0, "jour", jour)
    return x


def bornes(jour, a, b):
    o = pd.Timestamp(f"{jour} 09:30", tz="America/New_York")
    f = lambda x: x.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")
    return f(o + pd.Timedelta(minutes=int(a))), f(o + pd.Timedelta(minutes=int(b) + 1))


def fenetres(lignes):
    """lignes : (jour, minute de decision). Fenetres de 30 minutes, fusionnees quand elles se touchent dans une seance."""
    out = []
    for j, g in pd.DataFrame(lignes, columns=["jour", "minute"]).groupby("jour"):
        blocs = []
        for m in sorted(set(g["minute"])):
            a = m - FENETRE + 1
            if blocs and a <= blocs[-1][1] + 1:
                blocs[-1][1] = m
            else:
                blocs.append([a, m])
        out += [(j, a, b) for a, b in blocs]
    return out


def telecharger(api, fen, nom):
    morceaux = []
    for k, (j, a, b) in enumerate(fen):
        morceaux.append(par_minute(j, api.transactions(*bornes(j, a, b))))
        if (k + 1) % 100 == 0:
            print(f"  {nom} : {k + 1}/{len(fen)} fenetres", flush=True)
    x = pd.concat(morceaux, ignore_index=True)
    x.to_csv(D / f"{nom}.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    print(f"{nom} : {len(fen)} fenetres, {int(x['transactions'].sum()):,} transactions", flush=True)


def main():
    D.mkdir(exist_ok=True)
    api = Alpaca()
    # validation : les 99 trades de zone d'avril - septembre 2026 et 300 fenetres de controle tirees au hasard
    zone = pd.read_csv(ICI.parent / "orderflow" / "zone_avril_septembre_2026.csv")
    jours = sorted(pd.read_csv(ICI.parent / "orderflow" / "seances_avril_septembre_2026.csv")["jour"])
    rng = np.random.default_rng(1)
    toutes = [(j, m) for j in jours for m in CONTROLES]
    controle = [toutes[i] for i in rng.choice(len(toutes), 300, replace=False)]
    pd.DataFrame(controle, columns=["jour", "minute"]).to_csv(D / "controle.csv", index=False)
    telecharger(api, fenetres(list(zip(zone["jour"], zone["minute"])) + controle), "validation")
    # test : trades de zone de 2016 a mars 2026
    t = pd.read_csv(ICI / "trades_zone.csv")
    t = t[t["jour"] >= "2016-01-01"]
    telecharger(api, fenetres(list(zip(t["jour"], t["minute"]))), "test")


if __name__ == "__main__":
    main()
