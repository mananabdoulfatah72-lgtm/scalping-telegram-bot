#!/usr/bin/env python3
"""Effet de la regle 1 MNQ minimum (README.md). Utilise le robot lui-meme (chemin dans ROBOT_ZONE) : serie_du_bot
pour les gains de la zone V1 et une_journee pour les comptes Phidias. Lancer depuis ce dossier :
ROBOT_ZONE=/chemin/zone/robot.py python3 taille.py"""
import importlib.util
import os
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
R = ICI.parent
AN = 252


def charger_robot():
    spec = importlib.util.spec_from_file_location("robot", os.environ["ROBOT_ZONE"])
    robot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(robot)
    return robot


def suivre(robot, d, i0, n_jours):
    """Un depart au jour i0 suivi n_jours seances avec les regles du robot. Renvoie le resume et le journal."""
    etat = {"debut": None, "derniere_date": None, "tentatives": [], "recu_total": 0.0, "gain_1_mnq": 0.0}
    robot.nouveau_challenge(etat, None)
    lignes = [robot.une_journee(etat, x, str(date.date())) for date, x in d.iloc[i0:i0 + n_jours].iterrows()]
    j = pd.DataFrame(lignes)
    ev = j["evenement"].fillna("")
    return {"valide": ev.str.startswith("CHALLENGE REUSSI").any(), "challenges": int((j["phase"] == "challenge").groupby(j["tentative"]).any().sum()),
            "perdus": int(ev.str.startswith("COMPTE PERDU").sum()), "zero": int((j["mnq"] == 0).sum()),
            "recu": etat["recu_total"]}, j


def main():
    robot = charger_robot()
    minutes = pd.read_csv(R / "intraday/donnees/nasdaq100_1min.csv.gz")
    d = robot.serie_du_bot(minutes)[0]
    sortie = []
    ecrire = lambda s="": (print(s, flush=True), sortie.append(s))
    ecrire(f"Zone corrigee V1 seule, 1 MNQ, frais reels, regles Phidias du robot. {d.index[0].date()} -> {d.index[-1].date()}, un depart par semaine, suivi 12 mois.")
    an = d.index.year
    groupes = {"departs 2011-2021": np.where((an >= 2011) & (an <= 2021))[0], "departs 2023-2025": np.where(an >= 2023)[0]}
    for nom, idx in groupes.items():
        departs = [i for i in idx[::5] if i + AN <= len(d)]
        ecrire(f"\n=== {nom} ({len(departs)} departs)")
        for regle, mini in (("ancienne (0 MNQ possible)", 0), ("nouvelle (1 MNQ minimum)", 1)):
            robot.MIN_MNQ = mini
            r = pd.DataFrame([suivre(robot, d, i, AN)[0] for i in departs])
            ecrire(f"  {regle:26s} | challenge valide en 12 mois {r['valide'].mean():4.0%} | challenges commences {r['challenges'].mean():.2f}"
                   f" | comptes perdus {r['perdus'].mean():.2f} | seances a 0 MNQ {r['zero'].mean():5.1f} sur 252"
                   f" | recu : moyenne {r['recu'].mean():6,.0f} $, mediane {r['recu'].median():6,.0f} $, rien {(r['recu'] == 0).mean():4.0%}")
    ecrire("\n=== Rejeu unique du robot depuis le 30 decembre 2022 (comme zone/README.md)")
    i0 = int(np.searchsorted(d.index, pd.Timestamp("2022-12-30"), side="right"))
    for regle, mini in (("ancienne", 0), ("nouvelle", 1)):
        robot.MIN_MNQ = mini
        res, j = suivre(robot, d, i0, len(d) - i0)
        ev = j[j["evenement"].fillna("") != ""][["date", "evenement"]]
        ecrire(f"  {regle} : solde final {j['solde'].iloc[-1]:,.0f} $ | recu {res['recu']:,.0f} $ | seances a 0 MNQ {res['zero']} | evenements :")
        for r in ev.itertuples():
            ecrire(f"     {r.date} {r.evenement}")
    (ICI / "taille.txt").write_text("\n".join(sortie) + "\n")


if __name__ == "__main__":
    main()
