#!/usr/bin/env python3
"""Telecharge chez Databento (GLBX.MDP3, schema "tbbo") chaque transaction du NQ (NQ.v.0) avec son sens et le meilleur
prix acheteur / vendeur affiche juste avant (README.md). Seance americaine (9 h 30 - 16 h, New York), jours les plus
recents d'abord, en 3 telechargements de 25 $ au plus chacun (cout demande a Databento avant chaque jour).

Ecrit, pour chaque lot n : donnees/nq_secondes_n.csv.gz (par seconde), donnees/nq_footprint_n.csv.gz (minute x prix),
donnees/nq_gros_n.csv.gz (transactions d'au moins 10 contrats) ; et donnees/achats.txt (jours et couts).
Cle : variable DATABENTO_API_KEY (secret du depot, jamais ecrite ailleurs)."""
import sys
import time
from pathlib import Path

import databento as db
import numpy as np
import pandas as pd

JEU, SCHEMA, SYMBOLE = "GLBX.MDP3", "tbbo", "NQ.v.0"
PLAFOND_LOT, LOTS, GROS = 25.0, 3, 10
D = Path(__file__).parent / "donnees"


def essayer(f, essais=4):
    for k in range(essais):
        try:
            return f()
        except Exception as e:
            if k == essais - 1:
                raise
            print(f"  nouvelle tentative : {repr(e)[:120]}", flush=True)
            time.sleep(10 * (k + 1))


def fenetre(jour):
    a = pd.Timestamp(f"{jour} 09:30", tz="America/New_York").tz_convert("UTC")
    return a, a + pd.Timedelta(hours=6, minutes=30)


def main():
    client = db.Historical()
    fin = pd.Timestamp(client.metadata.get_dataset_range(dataset=JEU)["end"]).tz_convert("UTC")
    lots, courant, total_lot = [], [], 0.0
    for j in pd.bdate_range(end=fin.date() - pd.Timedelta(days=1), periods=200)[::-1]:
        a, z = fenetre(j.date())
        if z > fin:
            continue
        c = essayer(lambda: client.metadata.get_cost(dataset=JEU, symbols=[SYMBOLE], stype_in="continuous",
                                                     schema=SCHEMA, start=a.isoformat(), end=z.isoformat()))
        if c == 0:                                          # jour ferie
            continue
        if total_lot + c > PLAFOND_LOT:
            lots.append((courant, total_lot))
            if len(lots) == LOTS:
                break
            courant, total_lot = [], 0.0
        courant.append((j.date(), a, z, c))
        total_lot += c
    else:
        if courant:
            lots.append((courant, total_lot))
    lignes = [f"Achats Databento {SCHEMA} {SYMBOLE} ({pd.Timestamp.now(tz='UTC'):%Y-%m-%d %H:%M} UTC), plafond {PLAFOND_LOT:.0f} $ par lot"]
    for n, (jours, cout) in enumerate(lots, 1):
        lignes.append(f"lot {n} : {len(jours)} seances du {min(x[0] for x in jours)} au {max(x[0] for x in jours)}, {cout:.2f} $")
    lignes.append(f"total : {sum(len(x[0]) for x in lots)} seances, {sum(x[1] for x in lots):.2f} $")
    print("\n".join(lignes), flush=True)
    if not lots:
        sys.exit("Rien a telecharger sous le plafond")
    assert all(c <= PLAFOND_LOT for _, c in lots) and len(lots) <= LOTS
    for n, (jours, _) in enumerate(lots, 1):
        secondes, footprint, gros = [], [], []
        for j, a, z, _ in sorted(jours):
            df = essayer(lambda: client.timeseries.get_range(dataset=JEU, symbols=[SYMBOLE], stype_in="continuous",
                                                             schema=SCHEMA, start=a.isoformat(), end=z.isoformat())).to_df()
            if "ts_event" in df.columns:
                df = df.set_index("ts_event")
            t = pd.DatetimeIndex(df.index)
            t = (t.tz_localize("UTC") if t.tz is None else t).tz_convert("America/New_York")
            prix = df["price"].astype(float)
            if prix.median() > 1e6:
                prix = prix / 1e9
                for c in ["bid_px_00", "ask_px_00"]:
                    df[c] = df[c].astype(float) / 1e9
            sens = np.where(df["side"].values == "B", 1, np.where(df["side"].values == "A", -1, 0))   # B : acheteur agressif
            taille = df["size"].values.astype(np.int64)
            x = pd.DataFrame({"s": t.floor("s"), "m": t.floor("min"), "prix": prix.values,
                              "achat": np.where(sens > 0, taille, 0), "vente": np.where(sens < 0, taille, 0),
                              "bid": df["bid_px_00"].values, "ask": df["ask_px_00"].values,
                              "bid_q": df["bid_sz_00"].values, "ask_q": df["ask_sz_00"].values,
                              "contrat": df["instrument_id"].values})
            g = x.groupby("s")
            secondes.append(pd.DataFrame({"prix": g["prix"].last(), "haut": g["prix"].max(), "bas": g["prix"].min(),
                                          "achat": g["achat"].sum(), "vente": g["vente"].sum(), "n": g.size(),
                                          "bid": g["bid"].last(), "ask": g["ask"].last(), "bid_q": g["bid_q"].last(),
                                          "ask_q": g["ask_q"].last(), "contrat": g["contrat"].last()}))
            footprint.append(x.groupby(["m", "prix"])[["achat", "vente"]].sum().reset_index())
            k = taille >= GROS
            gros.append(pd.DataFrame({"t": t[k].strftime("%Y-%m-%d %H:%M:%S.%f").str[:23], "prix": prix.values[k],
                                      "sens": sens[k], "taille": taille[k]}))
            print(f"  lot {n}, {j} : {len(x)} transactions, {int(taille.sum())} contrats, {int(k.sum())} gros ordres", flush=True)
        s = pd.concat(secondes)
        s.index = s.index.strftime("%Y-%m-%d %H:%M:%S")
        s.to_csv(D / f"nq_secondes_{n}.csv.gz", index_label="t", float_format="%.2f")
        f = pd.concat(footprint)
        f["m"] = f["m"].dt.strftime("%Y-%m-%d %H:%M")
        f.to_csv(D / f"nq_footprint_{n}.csv.gz", index=False, float_format="%.2f")
        pd.concat(gros).to_csv(D / f"nq_gros_{n}.csv.gz", index=False, float_format="%.2f")
        print(f"lot {n} ecrit : {len(s)} secondes, {len(f)} cases de footprint", flush=True)
    (D / "achats.txt").write_text("\n".join(lignes) + "\n")


if __name__ == "__main__":
    main()
