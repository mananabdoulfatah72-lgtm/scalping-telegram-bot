#!/usr/bin/env python3
"""Telecharge chez Databento (GLBX.MDP3) les donnees de la phase 3 du fonds :
1. barres journalieres de 40 futures CME depuis juin 2010 : contrat le plus echange (v.0) et le
   deuxieme (v.1), pour les rendements et le carry ;
2. le symbole de chaque contrat (ex. CLZ5), pour connaitre son echeance ;
3. barres minute du deuxieme contrat ES autour des annonces de la Fed tombees un jour de
   changement d'echeance (14 jours exclus en phase 2).
La cle est lue dans DATABENTO_API_KEY. Le cout est demande avant ; arret si > PLAFOND dollars.

Les barres journalieres passent par une commande groupee ("batch") : Databento la prepare de son cote
(les requetes directes prenaient jusqu'a 9 minutes par marche). Le numero de la commande est garde
dans donnees/commande_databento.json ; si elle n'est pas prete, relancer plus tard reprend au meme point.
"""
import json
import sys
import time
from pathlib import Path

import databento as db
import pandas as pd

JEU = "GLBX.MDP3"
PLAFOND = 15.0
DEBUT = "2010-06-06"
D = Path(__file__).parent / "donnees"
RACINES = ["ES", "NQ", "RTY", "YM", "NKD", "ZT", "ZF", "ZN", "TN", "ZB", "UB",
           "6E", "6J", "6B", "6A", "6C", "6S", "6N", "6M", "CL", "BZ", "HO", "RB", "NG",
           "GC", "SI", "HG", "PL", "PA", "ZC", "ZW", "ZS", "ZM", "ZL", "KE", "LE", "HE", "GF", "BTC", "ETH"]
FOMC_ECHEANCE = ["2012-03-13", "2018-06-13", "2022-06-15", "2022-12-14", "2023-06-14", "2023-12-13", "2024-09-18",
                 "2024-12-18", "2025-03-19", "2025-06-18", "2025-09-17", "2026-03-18", "2026-06-17", "2026-09-16"]


def essayer(f, essais=4):
    """Relance une requete en cas d'erreur passagere du serveur (ex. 504)."""
    for k in range(essais):
        try:
            return f()
        except Exception as e:
            if k == essais - 1:
                raise
            print(f"  nouvelle tentative apres : {repr(e)[:120]}", flush=True)
            time.sleep(10 * (k + 1))


def en_df(store):
    df = store.to_df()
    if "ts_event" in df.columns:
        df = df.set_index("ts_event")
    df.index = pd.DatetimeIndex(df.index)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    if df["close"].median() > 1e7:                      # prix en entiers (1e-9) selon la version
        for c in ["open", "high", "low", "close"]:
            df[c] = df[c] / 1e9
    return df


def main():
    client = db.Historical()
    fin = str(pd.Timestamp(client.metadata.get_dataset_range(dataset=JEU)["end"]).date())
    symboles = [f"{r}.v.{k}" for r in RACINES for k in (0, 1)]
    cout = client.metadata.get_cost(dataset=JEU, symbols=symboles, stype_in="continuous", schema="ohlcv-1d",
                                    start=DEBUT, end=fin)
    cout_min = sum(client.metadata.get_cost(dataset=JEU, symbols=["ES.v.1"], stype_in="continuous", schema="ohlcv-1m",
                                            start=str((pd.Timestamp(d) - pd.Timedelta(days=5)).date()),
                                            end=str((pd.Timestamp(d) + pd.Timedelta(days=1)).date()))
                   for d in FOMC_ECHEANCE)
    print(f"Cout : barres journalieres {cout:.2f} $ + minutes ES {cout_min:.2f} $", flush=True)
    if cout + cout_min > PLAFOND:
        sys.exit("Trop cher : rien n'a ete telecharge")
    D.mkdir(exist_ok=True)
    # 1. barres journalieres : commande groupee chez Databento
    etat_f = D / "commande_databento.json"
    etat = json.loads(etat_f.read_text()) if etat_f.exists() else {}
    if not etat.get("commande"):
        job = client.batch.submit_job(dataset=JEU, symbols=symboles, schema="ohlcv-1d", start=DEBUT, end=fin,
                                      stype_in="continuous", encoding="dbn", compression="zstd", split_duration="none")
        etat = {"commande": job["id"], "fin": fin}
        etat_f.write_text(json.dumps(etat))
        print(f"Commande envoyee : {job['id']}", flush=True)
    fin = etat.get("fin", fin)
    pret = False
    for k in range(50):                                   # jusqu'a 50 minutes d'attente
        jobs = {j["id"]: j for j in client.batch.list_jobs()}
        statut = jobs.get(etat["commande"], {}).get("state", "inconnu")
        print(f"  commande {etat['commande']} : {statut}", flush=True)
        if statut == "done":
            pret = True
            break
        if statut in ("expired", "inconnu") and k > 2:
            etat_f.unlink()
            sys.exit("Commande introuvable ou expiree : relancer pour en envoyer une nouvelle")
        time.sleep(60)
    if not pret:
        print("Commande pas encore prete : relancer le telechargement plus tard.", flush=True)
        return
    fichiers = client.batch.download(job_id=etat["commande"], output_dir=D / "tmp")
    dbn = [f for f in fichiers if str(f).endswith((".dbn.zst", ".dbn"))]
    df = pd.concat([en_df(db.DBNStore.from_file(f)) for f in dbn])
    df = df[df.index.dayofweek < 5]
    # 2. symbole de chaque contrat (echeance)
    ids = sorted(int(i) for i in out["contrat"].unique())
    noms = {}
    for k in range(0, len(ids), 500):
        try:
            res = client.symbology.resolve(dataset=JEU, symbols=[str(i) for i in ids[k:k + 500]], stype_in="instrument_id",
                                           stype_out="raw_symbol", start_date=DEBUT, end_date=fin)
            for i, lst in res.get("result", {}).items():
                noms[i] = [x["s"] for x in lst]
        except Exception as e:                           # on continue : le carry sera saute si absent
            print("symbologie :", repr(e)[:300], flush=True)
    (D / "contrats.json").write_text(json.dumps(noms))
    print(f"Symboles trouves pour {len(noms)} contrats sur {len(ids)}", flush=True)

    # 3. deuxieme contrat ES autour des annonces de la Fed tombees un jour de changement d'echeance
    morceaux = []
    for d in FOMC_ECHEANCE:
        m = en_df(essayer(lambda: client.timeseries.get_range(
            dataset=JEU, symbols=["ES.v.1"], stype_in="continuous", schema="ohlcv-1m",
            start=str((pd.Timestamp(d) - pd.Timedelta(days=5)).date()), end=str((pd.Timestamp(d) + pd.Timedelta(days=1)).date()))))
        t = m.index.tz_convert("America/New_York")
        minute = t.hour * 60 + t.minute
        garde = (minute >= 570) & (minute < 960)
        morceaux.append(pd.DataFrame({"t": t[garde].strftime("%Y-%m-%d %H:%M"), "c": m["close"].values[garde],
                                      "contrat": m["instrument_id"].values[garde]}))
    pd.concat(morceaux).to_csv(D / "es_v1_fomc.csv.gz", index=False)
    print("Minutes ES v.1 : ok", flush=True)
    import shutil
    shutil.rmtree(D / "tmp", ignore_errors=True)
    etat_f.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
