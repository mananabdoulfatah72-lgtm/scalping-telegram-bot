#!/usr/bin/env python3
"""Descriptif : le delta des transactions Ironbeam (export d'Optimus Flow, donnees_rithmic/) compare minute par minute
au delta Databento (orderflow/donnees/nq_secondes_1.csv.gz) sur les seances communes. Ecrit validation_ironbeam.txt.
Lancer depuis la racine du depot."""
import glob

import numpy as np
import pandas as pd

d = pd.read_csv("orderflow/donnees/nq_secondes_1.csv.gz", usecols=["t", "achat", "vente"])
d["t"] = pd.to_datetime(d["t"])
d["jour"], d["minute"] = d.t.dt.strftime("%Y-%m-%d"), d.t.dt.hour * 60 + d.t.dt.minute - 570
db = d.groupby(["jour", "minute"])[["achat", "vente"]].sum().reset_index()
db["delta_db"] = db.achat - db.vente
ib = pd.concat([pd.read_csv(f) for f in glob.glob("filtre_h1/donnees_rithmic/transactions_*.csv")])
ib = ib.groupby(["jour", "minute"], as_index=False)[["achats", "ventes"]].sum()
ib["delta_ib"] = ib.achats - ib.ventes
m = db.merge(ib, on=["jour", "minute"])
r = []
for _, g in m.groupby("jour"):
    g = g.sort_values("minute")
    a, b = g.delta_db.rolling(30).sum(), g.delta_ib.rolling(30).sum()
    ok = a.notna() & (a != 0) & (b != 0)
    r.append(pd.DataFrame({"a": a[ok], "b": b[ok]}))
r = pd.concat(r)
L = [f"Ironbeam contre Databento : {m.jour.nunique()} seances communes ({m.jour.min()} - {m.jour.max()}), {len(m)} minutes",
     f"- volume Databento / Ironbeam : {(m.achat + m.vente).sum() / (m.achats + m.ventes).sum():.3f}",
     f"- delta d'une minute : correlation {np.corrcoef(m.delta_db, m.delta_ib)[0, 1]:.3f}, meme signe {(np.sign(m.delta_db) == np.sign(m.delta_ib)).mean():.1%}",
     f"- delta des 30 minutes (celui du filtre), a chaque minute : {len(r)} fenetres, meme signe {(np.sign(r.a) == np.sign(r.b)).mean():.1%},"
     f" correlation {np.corrcoef(r.a, r.b)[0, 1]:.3f}"]
open("filtre_h1/validation_ironbeam.txt", "w").write("\n".join(L) + "\n")
print("\n".join(L))
