#!/usr/bin/env python3
"""Telecharge chez Databento (GLBX.MDP3, schema "tbbo") chaque transaction du future E-mini S&P 500
(contrat le plus echange, ES.v.0) avec son sens (acheteur ou vendeur agressif) et le meilleur prix
acheteur / vendeur affiche juste avant (prix et quantites) : de quoi reconstruire le delta, le CVD,
le footprint et le desequilibre du carnet au premier niveau.

- Seance americaine seulement (9 h 30 - 16 h, heure de New York), jours les plus recents d'abord,
  tant que le cout reste sous PLAFOND dollars (cout demande a Databento avant tout telechargement).
- Les transactions brutes sont trop lourdes pour le depot : elles sont agregees ici par seconde
  (prix, volumes acheteurs / vendeurs, meilleur prix et quantites) et par minute et par prix
  (footprint). Cle : variable DATABENTO_API_KEY.
"""
import sys
import time
from pathlib import Path

import databento as db
import numpy as np
import pandas as pd

JEU, SCHEMA, SYMBOLE = "GLBX.MDP3", "tbbo", "ES.v.0"
PLAFOND, JOURS_MAX = 25.0, 25
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
    """Seance americaine du jour en UTC (tient compte de l'heure d'ete)."""
    a = pd.Timestamp(f"{jour} 09:30", tz="America/New_York").tz_convert("UTC")
    return a, a + pd.Timedelta(hours=6, minutes=30)


def main():
    client = db.Historical()
    fin = pd.Timestamp(client.metadata.get_dataset_range(dataset=JEU)["end"]).tz_convert("UTC")
    jours = [j for j in pd.bdate_range(end=fin.date() - pd.Timedelta(days=1), periods=40)[::-1]]
    choisis, total = [], 0.0
    for j in jours:
        a, z = fenetre(j.date())
        if z > fin:
            continue
        c = essayer(lambda: client.metadata.get_cost(dataset=JEU, symbols=[SYMBOLE], stype_in="continuous",
                                                     schema=SCHEMA, start=a.isoformat(), end=z.isoformat()))
        if c == 0:                                      # jour ferie
            continue
        if total + c > PLAFOND or len(choisis) >= JOURS_MAX:
            break
        choisis.append((j.date(), a, z))
        total += c
    print(f"{len(choisis)} seances retenues, cout total {total:.2f} $", flush=True)
    if not choisis:
        sys.exit("Rien a telecharger sous le plafond")
    secondes, footprint = [], []
    for j, a, z in sorted(choisis):
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
        achat = np.where(df["side"].values == "B", df["size"].values, 0)     # acheteur agressif
        vente = np.where(df["side"].values == "A", df["size"].values, 0)     # vendeur agressif
        x = pd.DataFrame({"s": t.floor("s"), "m": t.floor("min"), "prix": prix.values, "achat": achat, "vente": vente,
                          "bid": df["bid_px_00"].values, "ask": df["ask_px_00"].values,
                          "bid_q": df["bid_sz_00"].values, "ask_q": df["ask_sz_00"].values})
        g = x.groupby("s")
        secondes.append(pd.DataFrame({"prix": g["prix"].last(), "achat": g["achat"].sum(), "vente": g["vente"].sum(),
                                      "n": g.size(), "bid": g["bid"].last(), "ask": g["ask"].last(),
                                      "bid_q": g["bid_q"].last(), "ask_q": g["ask_q"].last()}))
        f = x.groupby(["m", "prix"])[["achat", "vente"]].sum().reset_index()
        footprint.append(f)
        print(f"  {j} : {len(x)} transactions, {int(achat.sum() + vente.sum())} contrats", flush=True)
    s = pd.concat(secondes)
    s.index = s.index.strftime("%Y-%m-%d %H:%M:%S")
    s.to_csv(D / "es_secondes.csv.gz", index_label="t", float_format="%.2f")
    f = pd.concat(footprint)
    f["m"] = f["m"].dt.strftime("%Y-%m-%d %H:%M")
    f.to_csv(D / "es_footprint.csv.gz", index=False, float_format="%.2f")
    print(f"Ecrit : {len(s)} secondes, {len(f)} cases de footprint", flush=True)


if __name__ == "__main__":
    main()
