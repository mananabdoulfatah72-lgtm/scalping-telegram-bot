#!/usr/bin/env python3
"""Rejoue les strategies intraday sur des challenges futures 50K intraday, avec les vrais prix :
un challenge demarre chaque jour de bourse de l'historique.

Regles simulees (septembre 2026, a verifier sur le site de chaque firme) :
- Topstep 50K : objectif +3 000 $ ; perte max 2 000 $ sous le plus haut solde de fin de journee,
  verifiee en temps reel ; perte journaliere 1 000 $ (le trade est coupe, le compte continue) ;
  regle de regularite : la meilleure journee <= 50 % du gain total ; 3 mois maximum simules.
- Apex 50K (version fin de journee) : objectif +3 000 $ ; perte max 2 500 $ sous le plus haut solde
  de fin de journee, verifiee en temps reel, bloquee a 50 100 $ ; 30 jours d'acces (21 seances).
Les frais (1 $ par ordre + 1 tick de glissement) sont deja dans les resultats nets.
Reference "sans avantage" : memes trades, moyenne ramenee a zero (meme risque, aucun avantage).
"""
import numpy as np
import pandas as pd

import strategies as st
from analyse import calculer

REGLES = {
    "Topstep 50K": {"objectif": 3000, "perte_max": 2000, "jour_max": 1000, "regularite": 0.5, "blocage": None, "jours": 63},
    "Apex 50K": {"objectif": 3000, "perte_max": 2500, "jour_max": None, "regularite": None, "blocage": 50100, "jours": 21},
}


def simuler(gain, pire, regle):
    """gain, pire : tableaux (jours) en $ pour la taille choisie. Un challenge par jour de depart."""
    r = REGLES[regle]
    H, n = r["jours"], len(gain)
    departs = np.arange(0, n - H)
    resultat = np.zeros(len(departs), int)
    duree = np.full(len(departs), np.nan)
    for k, d0 in enumerate(departs):
        solde = haut = 50000.0
        meilleur = 0.0
        for j in range(H):
            g, p = gain[d0 + j], pire[d0 + j]
            plancher = haut - r["perte_max"]
            if r["blocage"]:
                plancher = min(plancher, r["blocage"])
            if solde + p <= plancher:                    # limite touchee en cours de journee
                resultat[k] = -1
                break
            if r["jour_max"] and p <= -r["jour_max"]:    # perte du jour plafonnee
                g = -r["jour_max"]
            solde += g
            meilleur = max(meilleur, g)
            if solde <= plancher:
                resultat[k] = -1
                break
            haut = max(haut, solde)
            profit = solde - 50000
            if profit >= r["objectif"] and (not r["regularite"] or meilleur <= r["regularite"] * profit):
                resultat[k] = 1
                duree[k] = j + 1
                break
    return resultat, duree


def main():
    for nom, info in st.CONTRATS.items():
        jours, res, _ = calculer(nom)
        print(f"\n=== {nom.upper()} ({info['micro']})")
        for strat, df in res.items():
            if "pire" not in df:
                continue
            net = df["net"].reindex(jours).fillna(0).values
            pire = np.minimum(df["pire"].reindex(jours).fillna(0).values, np.minimum(net, 0))
            print(f"\n  {strat}")
            for regle in REGLES:
                for contrats in [2, 5, 10, 20]:
                    k = contrats * info["pt"]
                    ok, dur = simuler(net * k, pire * k, regle)
                    sans = net - df["net"].mean() * (net != 0)          # meme risque, avantage retire
                    ok0, _ = simuler(sans * k, pire * k, regle)
                    print(f"    {regle:12s} {contrats:2d} {info['micro']} : reussi {np.mean(ok == 1):4.0%} | perdu {np.mean(ok == -1):4.0%}"
                          f" | pas fini {np.mean(ok == 0):4.0%} | duree mediane {np.nanmedian(dur) if (ok == 1).any() else float('nan'):4.0f} seances"
                          f" || sans avantage : reussi {np.mean(ok0 == 1):4.0%}")


if __name__ == "__main__":
    main()
