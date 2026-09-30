#!/usr/bin/env python3
"""Donnees du tournoi n°5 (README.md), par GitHub Actions :
- barres d'une heure (Databento, GLBX.MDP3, contrat le plus echange) des devises 6E 6B 6J 6A 6C 6S et du ZN, depuis juin 2010 ;
- minutes du bitcoin CME (BTC) depuis decembre 2017, gardees de 9 h a 16 h 30 (New York), si le budget le permet ;
- dates des adjudications du Tresor (fiscaldata.treasury.gov, gratuit).
Le cout est demande avant : plafond total 25 $ ; le bitcoin est abandonne en premier si c'est trop cher.
Cle : DATABENTO_API_KEY (secret). Sorties : tournoi5/donnees/."""
import json
import sys
import time
import urllib.request
from pathlib import Path

import databento as db
import pandas as pd

JEU, PLAFOND = "GLBX.MDP3", 25.0
HEURE = {"6E": "6E.v.0", "6B": "6B.v.0", "6J": "6J.v.0", "6A": "6A.v.0", "6C": "6C.v.0", "6S": "6S.v.0", "ZN": "ZN.v.0"}
SORTIE = Path(__file__).parent / "donnees"


def heure_ny(df):
    t = pd.to_datetime(df["ts_event"], utc=True) if "ts_event" in df.columns else df.index
    t = pd.DatetimeIndex(t)
    return (t.tz_localize("UTC") if t.tz is None else t).tz_convert("America/New_York")


def en_tableau(df, garde=None):
    t = heure_ny(df)
    prix = df[["open", "high", "low", "close"]].astype(float)
    if prix["close"].median() > 1e6:
        prix = prix / 1e9
    g = slice(None) if garde is None else garde(t)
    return pd.DataFrame({"t": t[g].strftime("%Y-%m-%d %H:%M"), "o": prix["open"].values[g], "h": prix["high"].values[g],
                         "l": prix["low"].values[g], "c": prix["close"].values[g], "v": df["volume"].values[g],
                         "contrat": df["instrument_id"].values[g]})


def plage(client, sym, schema, debut, fin):
    """Demande annee par annee (le serveur coupe les tres longues demandes), avec 4 essais par annee."""
    morceaux = []
    a0, a1 = int(debut[:4]), int(fin[:4])
    for a in range(a0, a1 + 1):
        deb, fi = (debut if a == a0 else f"{a}-01-01"), (fin if a == a1 else f"{a + 1}-01-01")
        for essai in range(4):
            try:
                df = client.timeseries.get_range(dataset=JEU, symbols=[sym], stype_in="continuous", schema=schema, start=deb, end=fi).to_df()
                break
            except Exception as e:                   # noqa: BLE001
                print(f"  {sym} {a} : essai {essai + 1} rate ({e})", flush=True)
                time.sleep(2 ** (essai + 2))
        else:
            raise RuntimeError(f"{sym} {a} : 4 essais rates")
        if not df.empty:
            morceaux.append(df)
    return pd.concat(morceaux)


def adjudications():
    url = ("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query"
           "?fields=auction_date,security_type,security_term,closing_time_comp&filter=auction_date:gte:2010-01-01"
           "&page[size]=10000&sort=auction_date")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
            data = json.loads(r.read())["data"]
        a = pd.DataFrame(data)
        a.to_csv(SORTIE / "adjudications.csv", index=False)
        print(f"adjudications : {len(a)} lignes, types {a['security_type'].value_counts().to_dict()}", flush=True)
    except Exception as e:                           # noqa: BLE001
        print(f"adjudications : ECHEC {e}", flush=True)


def main():
    SORTIE.mkdir(exist_ok=True)
    adjudications()
    client = db.Historical()
    fin = pd.Timestamp(client.metadata.get_dataset_range(dataset=JEU)["end"]).isoformat()
    c_h = client.metadata.get_cost(dataset=JEU, symbols=list(HEURE.values()), stype_in="continuous", schema="ohlcv-1h",
                                   start="2010-06-06", end=fin)
    c_b = client.metadata.get_cost(dataset=JEU, symbols=["BTC.v.0"], stype_in="continuous", schema="ohlcv-1m",
                                   start="2017-12-17", end=fin)
    lignes = [f"Cout barres d'une heure (6 devises + ZN) : {c_h:.2f} $", f"Cout minutes bitcoin : {c_b:.2f} $"]
    print("\n".join(lignes), flush=True)
    avec_btc = c_h + c_b <= PLAFOND
    if c_h > PLAFOND:
        (SORTIE / "couts.txt").write_text("\n".join(lignes + ["Trop cher : rien n'est telecharge"]) + "\n")
        sys.exit(0)
    lignes.append(f"Bitcoin {'telecharge' if avec_btc else 'abandonne (plafond)'} ; total {c_h + (c_b if avec_btc else 0):.2f} $")
    for nom, sym in HEURE.items():
        out = en_tableau(plage(client, sym, "ohlcv-1h", "2010-06-06", fin)).drop_duplicates("t", keep="last")
        out.to_csv(SORTIE / f"{nom}_1h.csv.gz", index=False, float_format="%.8g")
        lignes.append(f"{nom} : {len(out)} heures du {out['t'].iloc[0]} au {out['t'].iloc[-1]}")
        print(lignes[-1], flush=True)
    if avec_btc:
        df = plage(client, "BTC.v.0", "ohlcv-1m", "2017-12-17", fin)
        morceaux = [en_tableau(df, lambda t: ((t.hour * 60 + t.minute) >= 540) & ((t.hour * 60 + t.minute) < 990) & (t.dayofweek < 5))]
        out = pd.concat(morceaux, ignore_index=True).drop_duplicates("t", keep="last")
        out.to_csv(SORTIE / "bitcoin_1min.csv.gz", index=False, float_format="%.8g")
        lignes.append(f"bitcoin : {len(out)} minutes du {out['t'].iloc[0]} au {out['t'].iloc[-1]}")
        print(lignes[-1], flush=True)
    (SORTIE / "couts.txt").write_text("\n".join(lignes) + "\n")


if __name__ == "__main__":
    main()
