#!/usr/bin/env python3
"""Tournoi 8 : ouverture du coffre 2023 - septembre 2026, une seule fois, pour les survivants de tournoi8.py (README.md).
Un survivant passe si t >= seuil de Bonferroni pour m survivants et resultat positif au moins 3 annees sur 4.
Ecrit coffre8.txt et coffre8.json. Lancer depuis ce dossier, apres tournoi8.py : python3 coffre8.py"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

import tournoi8 as T

ICI = Path(__file__).resolve().parent
DEBUT_COFFRE = pd.Timestamp("2023-01-01")


def main():
    survivants = json.loads((ICI / "survivants8.json").read_text())
    m = len(survivants)
    lignes, sortie = [f"Coffre 2023 - septembre 2026, ouvert une fois pour {m} survivant(s)."], []
    if not m:
        lignes.append("Aucun survivant : coffre non ouvert.")
    seuil = float(norm.ppf(1 - 0.05 / m)) if m else None
    for v in survivants:
        s = T.charger(v["marche"], jusqu_au="2026-12-31")
        pos = T.positions(s, v["strategie"])
        rend, dol, trades, e, so = T.journal(s, pos)
        k = (s["date"] >= DEBUT_COFFRE).to_numpy()
        ke = k[e] if len(e) else np.array([], bool)
        x = T.mesures(rend[k], dol[k], trades[ke[:len(trades)]], pos[k])
        annees = pd.Series(dol[k], index=s["date"][k].dt.year).groupby(level=0).sum()
        x["annees"] = {int(a): round(float(b), 1) for a, b in annees.items()}
        x["seuil_t"] = round(seuil, 3)
        x["passe"] = bool(x["t"] >= seuil and (annees > 0).sum() >= 3)
        x.update(marche=v["marche"], strategie=v["nom"])
        sortie.append(x)
        lignes += ["", f"{v['marche']} {v['nom']} : t {x['t']:+.2f} (seuil {seuil:.2f}), Sharpe {x['sharpe']:+.2f}, {x['trades']} trades,"
                   f" {x['dollars_1_micro']:+.0f} $ pour 1 micro, perte max {x['perte_max_1_micro']:+.0f} $, en position {x['en_position']:.0%},"
                   f" trades gagnants {x['trades_gagnants']:.0%}, gain moyen {x['gain_moyen']:+.0f} $ / perte moyenne {x['perte_moyenne']:+.0f} $",
                   "  annees : " + ", ".join(f"{a} {b:+.0f} $" for a, b in x["annees"].items()),
                   f"  VERDICT : {'PASSE' if x['passe'] else 'ELIMINE'}"]
    (ICI / "coffre8.txt").write_text("\n".join(lignes) + "\n")
    (ICI / "coffre8.json").write_text(json.dumps(sortie, indent=1, ensure_ascii=False))
    print("\n".join(lignes))


if __name__ == "__main__":
    main()
