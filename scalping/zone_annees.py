#!/usr/bin/env python3
"""Descriptif (README.md, version 5, « La zone de bruit filtrée ») : la zone du bot sans filtre delta, annee par annee,
2011 - 20 octobre 2026, pour 1 MNQ au prix d'aujourd'hui (frais 1,5 point par aller-retour). Reprend le moteur verifie de
delta_mesures/etude.py (branche claude/affectionate-turing-tnz0mn), qui redonne la zone du bot trade par trade.
Lancer : DELTA_MESURES=<dossier delta_mesures de cette branche> KB=<branche de recherche extraite> python3 zone_annees.py.
Ecrit resultats/v5/zone_annees.txt."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.environ["DELTA_MESURES"])
import etude as DM                                                               # noqa: E402

SORTIE = Path(__file__).resolve().parent / "resultats" / "v5"


def t(x):
    x = np.asarray(x, float)
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x))


def main():
    rech = pd.read_csv(DM.RECHERCHE)
    robot = pd.read_csv(DM.ROBOT)
    robot = robot[robot["t"] <= DM.FIN + " 23:59"]
    bars = pd.concat([rech, robot[robot["t"] > rech["t"].iloc[-1]]], ignore_index=True)
    z = DM.preparer(bars)
    tr = DM.trades_zone(z, "2000-01-01", DM.FIN)
    jouables = pd.DataFrame({"jour": z["jours"][z["jouables"]]})
    dernier = float(z["C"][z["jouables"][-1], -1])
    tr["usd"] = tr["points"] / tr["prix_entree"] * dernier * 2
    j = jouables.merge(tr.groupby("jour")[["points", "usd"]].sum().reset_index(), on="jour", how="left").fillna(0.0)
    j["an"] = j["jour"].dt.year
    L = [f"Zone du bot sans filtre, 1 MNQ au prix d'aujourd'hui ({dernier:.0f}), frais 1,5 point par aller-retour, "
         f"seances jouables (0 sans trade) ; derniere seance {j['jour'].max().date()}", ""]
    for a, g in j.groupby("an"):
        L.append(f"{a}  seances {len(g):3d}  trades {(tr['jour'].dt.year == a).sum():3d}  {g['usd'].sum():+8.0f} $  t {t(g['usd']):+5.2f}")
    L.append("")
    for a0, a1 in ((2011, 2017), (2018, 2022), (2023, 2026), (2024, 2026), (2025, 2026)):
        g = j[(j["an"] >= a0) & (j["an"] <= a1)]
        L.append(f"{a0}-{a1} : t {t(g['usd']):+.2f}, {g['usd'].sum():+.0f} $, {g['usd'].mean():+.2f} $ par seance")
    pub = j[j["jour"] >= "2024-06-01"]
    L.append(f"depuis la publication de l'article (juin 2024) : t {t(pub['usd']):+.2f}, {pub['usd'].sum():+.0f} $, "
             f"{len(pub)} seances")
    r = j.set_index("jour")["usd"].rolling(252)
    roll = (r.mean() / r.std() * np.sqrt(252)).dropna()
    L.append(f"t sur 252 seances glissantes : min {roll.min():+.2f} ({roll.idxmin().date()}), max {roll.max():+.2f} "
             f"({roll.idxmax().date()}), dernier {roll.iloc[-1]:+.2f} ({roll.index[-1].date()})")
    SORTIE.mkdir(parents=True, exist_ok=True)
    (SORTIE / "zone_annees.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
