#!/usr/bin/env python3
# Lancer depuis intraday50k/ : python3 budget30.py > budget30.txt
"""Descriptif : chance de reussir un challenge 50K a 30 $ ou moins dans le premier mois paye (21 seances), et sur un an,
selon la taille (k MNQ par source). Bulenox option 2 : zone + RSI(2) entre deux clotures (moteur intraday50k).
DayTraders Static : zone + RSI(2) original (nuit et week-end permis ; moteur de piste5, plancher fixe)."""
import sys
sys.path.insert(0, "/home/user/scalping-telegram-bot/intraday50k")
sys.path.insert(0, "/home/user/scalping-telegram-bot/protection")
import numpy as np, pandas as pd
import commun as K, moteur as M
import piste5 as S, piste2 as Q, protection as P

D = K.charger(); j = D["jours"]; nj = len(j)
zt = K.P.tableaux_zone(D["Z"], nj, np.ones(len(D["Z"]), bool))
possibles = [d for d in range(260, nj) if D["ouvert"][d] == 0]
gr = {"2023-2026": [d for d in possibles[::5] if j[d] >= pd.Timestamp("2023-01-01")],
      "2025": [d for d in possibles[::5] if j[d].year == 2025],
      "2011-2022": [d for d in possibles[::5] if j[d] <= pd.Timestamp("2022-12-31")]}
def resume(r):
    r = np.array(r)
    return f"{(r[:,0]==1).mean():4.0%} reussis / {(r[:,0]==-1).mean():4.0%} perdus"
print("=== Bulenox option 2 (fin de journee, 2 500 $, limite du jour 1 100 $) : zone + RSI(2) entre deux clotures")
for k in (1, 2, 3, 4):
    b = (D["O"]*k, D["H"]*k, D["L"]*k, D["C"]*k, D["derniere"], *zt, D["dec"], D["voulu"], D["NO"]*k, D["NH"]*k, D["NL"]*k, D["nn"])
    lig = []
    for g, dd in gr.items():
        for nmax in (21, 252):
            r = [M.challenge(d, nmax, 1, *b, 3000.0, 2500.0, 0, 100.0, 1100.0, 0.0, 1, K.P.FRAIS_ZONE*k, K.P.FRAIS_RSI*k)[:2] for d in dd]
            lig.append(f"{g} {'1 mois' if nmax==21 else '1 an'} : {resume(r)}")
    print(f"{k} MNQ par source | " + " | ".join(lig))
# DayTraders Static : moteur piste5 (meme que static50k), prix multiplies par k
jours, O, H, L, C, Z, dec, voulu, ouvert = P.donnees()
nj2 = len(jours); dates = pd.DatetimeIndex(jours)
base = (O, H, L, C, P.tableaux_zone(Z, nj2, np.ones(len(Z), bool)), dec, voulu, ouvert)
pos2 = [d for d in range(260, nj2) if ouvert[d] == 0]
gr2 = {"2023-2026": [d for d in pos2[::5] if dates[d] >= pd.Timestamp("2023-01-01")], "2025": [d for d in pos2[::5] if dates[d].year == 2025],
       "2011-2022": [d for d in pos2[::5] if dates[d] <= pd.Timestamp("2022-12-31")]}
print("=== DayTraders Static 50K (+3 750 $, plancher fixe 49 000 $, regularite 50 %, 2 jours) : zone + RSI(2) original")
for k in (1, 2):
    a = Q.zt_args((O*k, H*k, L*k, C*k, base[4], dec, voulu, ouvert))
    lig = []
    for g, dd in gr2.items():
        for nmax in (21, 252):
            out = []
            for d in dd:
                etat = S.depart(ouvert, d, 1000.0); meilleur, qual, res = -1e18, 0, (0, nmax)
                for x in range(d, min(nj2, d + nmax)):
                    perdu, eod = S.seance5(x, etat, *a[:12], 1000.0, 1, -1000.0, P.FRAIS_ZONE*k, P.FRAIS_RSI*k, 0.0, 0.0)
                    if perdu: res = (-1, x - d + 1); break
                    gg = eod - etat[10]; etat[10] = eod; meilleur = max(meilleur, gg); qual += gg >= 200
                    if eod >= 3750 and qual >= 2 and meilleur <= 0.5 * eod: res = (1, x - d + 1); break
                out.append(res)
            lig.append(f"{g} {'1 mois' if nmax==21 else '1 an'} : {resume(out)}")
    print(f"{k} MNQ par source | " + " | ".join(lig))
