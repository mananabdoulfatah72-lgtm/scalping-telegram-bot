#!/usr/bin/env python3
"""Tests du tournoi 9 : rendements sans saut d'echeance, aucun regard vers le futur, fin de mois au calendrier, trade a la
main, placements au hasard fideles. Lancer depuis ce dossier : python3 test_tournoi9.py"""
import numpy as np
import pandas as pd

import tournoi9 as T

s = T.charger("CL")
# 1. rendement continu : jamais de saut d'echeance (le plus gros |r| reste celui d'avril 2020 ou d'un vrai choc)
grand = s.loc[s["r"].abs() > 0.15, ["date", "r", "change"]]
print(f"1. petrole : {int(s['change'].sum())} changements de contrat ; jours a plus de 15 % : {len(grand)} ({', '.join(str(d.date()) for d in grand['date'])}) : a verifier ci-dessus")
# 2. aucun regard vers le futur
rng = np.random.default_rng(9)
for m in T.CONTRATS:
    s = T.charger(m)
    for k in range(4):
        plein = T.positions(s, k)
        for cut in rng.integers(400, len(s) - 10, 4):
            c = s.iloc[:cut].copy(); c.attrs = s.attrs
            assert np.array_equal(T.positions(c, k)[:cut], plein[:cut]), (m, k, cut)
print("2. couper les donnees ne change aucune position passee (4 marches x 4 strategies x 4 coupes) : OK")
# 3. fin de mois : position tenue de l'avant-derniere a la derniere seance du mois (2019)
s = T.charger("ZN")
pos = T.positions(s, 3)
d = s["date"]
tenus = d[np.r_[False, pos[:-1] == 1]]          # seances ou l'on encaisse le rendement
annee = tenus[tenus.dt.year == 2019].dt.strftime("%m-%d").tolist()
derniers = d[d.dt.year == 2019].groupby(d.dt.month).max().dt.strftime("%m-%d").tolist()
assert annee == derniers, (annee, derniers)
print(f"3. fin de mois 2019 : rendement encaisse les jours {annee} = derniers jours de bourse : OK")
# 4. trade a la main (RSI(2) or) : P&L = somme des rendements x prix x 10 $ - frais
s = T.charger("GC")
pos = T.positions(s, 0)
rend, dol, tr, deb, dur, sens = T.journal(s, pos)
a, b = deb[0], deb[0] + dur[0]
r, prix = s["r"].to_numpy(), s["prix"].to_numpy()
attendu = sum(sens[0] * r[t] * prix[t - 1] * 10 for t in range(a + 1, b + 1)) - 2 * 2.0 - 2 * 2.0 * s["change"].to_numpy()[a + 1:b + 1].sum()
assert np.isclose(tr[0], attendu), (tr[0], attendu)
print(f"4. or, RSI(2) : 1er trade {'achat' if sens[0] > 0 else 'vente'} du {s['date'][a].date()} au {s['date'][b].date()}, {tr[0]:+.1f} $ : OK")
# 5. placements au hasard : memes durees, memes sens, sans chevauchement
q = T.placer(dur, sens, len(s), 3)
_, _, tr2, d2, du2, se2 = T.journal(s, q)
assert sorted(zip(du2, se2)) == sorted(zip(dur, sens))
print(f"5. hasard : {len(dur)} trades replaces avec les memes durees et sens : OK")
