#!/usr/bin/env python3
"""Derive de nuit (regles fixees dans README.md) : achat a la reouverture de 18 h, vente a 9 h le lendemain
(barres d'une heure Databento, ES et NQ, contrats micro MES et MNQ). Si le critere est rempli : bot coussin
de challenge 50K (meme code que challenge/).

Lancer depuis ce dossier : python3 analyse.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "challenge"))
MICRO = {"sp500": {"nom": "MES", "pt": 5.0}, "nasdaq100": {"nom": "MNQ", "pt": 2.0}}
TICK, FRAIS_ORDRE = 0.25, 1.0
PERIODES = [("2010", "2015"), ("2015", "2020"), ("2020", "2027")]


def nuits(nom):
    b = pd.read_csv(ICI / "donnees" / f"{nom}_1h.csv.gz", parse_dates=["t"]).set_index("t").sort_index()
    pt = MICRO[nom]["pt"]
    cout = 2 * (FRAIS_ORDRE + TICK * pt)                     # $ par aller-retour pour 1 micro
    soirs = b.index[b.index.hour == 18]
    lignes = []
    for s in soirs:
        lendemain = s.normalize() + pd.Timedelta(days=1)
        if s.dayofweek == 4:                                  # vendredi soir : pas de seance le samedi
            continue
        sortie = lendemain + pd.Timedelta(hours=9)
        if sortie not in b.index:
            continue
        nuit = b.loc[s:sortie - pd.Timedelta(hours=1)]
        if b.at[s, "contrat"] != b.at[sortie, "contrat"] or (nuit["contrat"] != b.at[s, "contrat"]).any():
            continue                                          # changement d'echeance pendant la nuit
        e, x = b.at[s, "o"], b.at[sortie, "o"]
        # seance americaine precedente : de l'ouverture de la barre de 9 h a la cloture de la barre de 15 h
        veille = s.normalize()
        seance = b.loc[veille + pd.Timedelta(hours=9):veille + pd.Timedelta(hours=15)]
        sens_seance = np.nan
        if len(seance) == 7 and (seance["contrat"] == b.at[s, "contrat"]).all():
            sens_seance = seance["c"].iloc[-1] / seance["o"].iloc[0] - 1
        lignes.append({"soir": s, "gain": (x - e) * pt - cout, "pire": (nuit["l"].min() - e) * pt - cout,
                       "rendement": x / e - 1, "seance_veille": sens_seance})
    n = pd.DataFrame(lignes).set_index("soir")
    # rendement moyen de chaque heure de la nuit (information)
    r = b["c"] / b["o"] - 1
    heures = r.groupby(r.index.hour).mean()
    return n, heures


def mesurer(nom, n):
    g = n["gain"]
    t = lambda x: x.mean() / x.std() * np.sqrt(len(x))
    print(f"  {nom} ({MICRO[nom]['nom']}) : {len(g)} nuits | {g.mean():+.2f} $ par nuit et par micro (t {t(g):+.2f})"
          f" | gagnantes {(g > 0).mean():.0%} | pire nuit {n['pire'].min():,.0f} $")
    ok = t(g) >= 2
    for a, z in PERIODES:
        x = g[(g.index >= a) & (g.index < z)]
        print(f"     {a}-{int(z) - 1} : {x.mean():+.2f} $ (t {t(x):+.2f}, {len(x)} nuits)")
        ok &= x.mean() > 0
    baisse, hausse = n.loc[n["seance_veille"] < 0, "rendement"], n.loc[n["seance_veille"] > 0, "rendement"]
    print(f"     information : nuit apres une seance en baisse {baisse.mean():+.3%} ({len(baisse)}) ;"
          f" apres une seance en hausse {hausse.mean():+.3%} ({len(hausse)})")
    return bool(ok)


def challenge(nom, n):
    from bot_challenge import FRACTIONS, REGLES, sans_avantage, sur_un_an, une_tentative
    from finance import finance
    g = n["gain"]
    d = pd.DataFrame({"gain": g, "pire": np.minimum(n["pire"], np.minimum(g, 0)).clip(upper=0),
                      "risque1": g.rolling(60, min_periods=40).std().shift(1), "melange": 0.0}).dropna()
    d0 = sans_avantage(d)
    for firme, regle in REGLES.items():
        for f in FRACTIONS:
            une = np.array([une_tentative(d, i, regle, f, False)[0] for i in range(0, len(d) - 252, 5)])
            an, an0 = sur_un_an(d, regle, f, False), sur_un_an(d0, regle, f, False)
            deux = (an["reussi"] & (an["tentatives"] <= 2)).mean()
            ligne = (f"  {nom[:6]} {firme:12s} f={f:.2f} | 1 tentative : reussie {np.mean(une == 1):4.0%}, perdue {np.mean(une == -1):5.1%}"
                     f" | en 12 mois : valide {an['reussi'].mean():4.0%} (2 comptes max {deux:4.0%} ; sans avantage {an0['reussi'].mean():4.0%})")
            if firme.startswith("Phidias"):
                res = [finance(d, i, f, False) for i in range(0, len(d) - 252, 5)]
                recu = np.array([r for r, _ in res])
                ligne += f" | finance 12 mois : recu {recu.mean():,.0f} $ en moyenne, rien {np.mean(recu == 0):.0%}"
            print(ligne, flush=True)
        print()


def main():
    resultats = {}
    for nom in MICRO:
        n, heures = nuits(nom)
        resultats[nom] = n
        print(f"{nom} : rendement moyen de chaque heure (heure de New York, debut de barre) :")
        print("   " + " ".join(f"{h}h:{v * 1e4:+.1f}" for h, v in heures.items()) + "  (points de base)")
    print("\n1. Achat a 18 h, vente a 9 h le lendemain (1 micro, frais compris) :")
    ok = all([mesurer(nom, n) for nom, n in resultats.items()])
    print(f"\nCritere (t >= 2 et positif dans les 3 periodes, sur ES et NQ) : {'REMPLI' if ok else 'NON REMPLI'}\n")
    if ok:
        print("2. Challenge 50K (bot coussin, un depart par semaine, regles a verifier) :")
        for nom, n in resultats.items():
            challenge(nom, n)


if __name__ == "__main__":
    main()
