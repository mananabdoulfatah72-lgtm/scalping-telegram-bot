#!/usr/bin/env python3
"""Tests du tournoi 8 : prix de decision, aucun regard vers le futur, trade a la main, placements au hasard fideles.
Lancer depuis ce dossier : python3 test_tournoi8.py"""
import numpy as np
import pandas as pd

import tournoi8 as T

s = T.charger("NQ")
m = pd.read_csv(T.MARCHES["NQ"][0])
m = m[m["t"].str[:10] <= T.FIN_EXPLORATION]
# 1. prix : jour normal -> execution a l'ouverture de 15 h 50, cloture de 15 h 49 ; jour court -> 10 minutes avant la fin
for jour in ("2019-06-12", "2019-11-29"):
    x = m[m["t"].str[:10] == jour]
    ligne = s[s["date"] == pd.Timestamp(jour)].iloc[0]
    derniere = x["t"].iloc[-1][11:16]
    h, mi = map(int, derniere.split(":"))
    dec = f"{(h * 60 + mi - 9) // 60:02d}:{(h * 60 + mi - 9) % 60:02d}"
    avant = f"{(h * 60 + mi - 10) // 60:02d}:{(h * 60 + mi - 10) % 60:02d}"
    assert ligne["P"] == x[x["t"].str[11:16] == dec]["o"].iloc[0] and ligne["C"] == x[x["t"].str[11:16] == avant]["c"].iloc[0], (jour, ligne)
    y = x[(x["t"].str[11:16] < dec)]
    assert ligne["H"] == y["h"].max() and ligne["L"] == y["l"].min()
    print(f"1. {jour} : derniere minute {derniere}, decision {dec}, P = ouverture, C = cloture de {avant}, haut/bas avant : OK")
# 2. aucun regard vers le futur : couper les donnees a la seance k ne change aucune position avant k - 1
rng = np.random.default_rng(8)
for k_strat in range(5):
    plein = T.positions(s, k_strat)
    for k in rng.integers(400, len(s) - 10, 5):
        coupe = s.iloc[:k].copy()
        coupe.attrs = s.attrs
        p = T.positions(coupe, k_strat)
        # la derniere position de la serie coupee est fermee (fin des donnees = changement de contrat suppose)
        assert np.array_equal(p[:k - 1], plein[:k - 1]), (T.STRATEGIES[k_strat], k)
print("2. couper les donnees ne change aucune position passee (5 strategies x 5 coupes) : OK")
# 3. trade a la main (IBS) : premiere entree, sortie a la decision suivante
pos = T.positions(s, 2)
rend, dol, trades, e, so = T.journal(s, pos)
a, b = e[0], so[0]
ibs = (s["C"][a] - s["L"][a]) / (s["H"][a] - s["L"][a])
assert ibs < 0.2 and pos[a] == 1
attendu = ((s["P"][b] - s["P"][a]) - 2 * s.attrs["cote"]) * s.attrs["pt"]
assert np.isclose(trades[0], attendu) and np.isclose(dol[a] + dol[a + 1:b + 1].sum(), attendu)
print(f"3. IBS : entree le {s['date'][a].date()} (IBS {ibs:.2f}) a {s['P'][a]}, sortie le {s['date'][b].date()} a {s['P'][b]},"
      f" {attendu:+.1f} $ net : OK")
# 4. placements au hasard : memes trades, memes durees, sans chevauchement ni passage d'echeance
pos = T.positions(s, 0)
_, _, trades, e, so = T.journal(s, pos)
d = (so - e).astype(np.int64)
interdit = T.echeances(s)
for g in range(20):
    q = T.placer(d, interdit, g)
    _, _, tr, e2, s2 = T.journal(s, q)
    assert sorted(s2 - e2) == sorted(d) and not (q.astype(bool) & interdit).any()
print(f"4. hasard : {len(d)} trades replaces 20 fois avec les memes durees, jamais a cheval sur une echeance : OK")
# 5. veilles de ferie : vendredi saint 2019 (19 avril) -> jeudi 18 ; MLK 2019 (21 janvier) -> vendredi 18 ; 4 juillet 2019 -> 3
v = T.veilles_de_ferie(s)
dates = set(s["date"][v].dt.strftime("%Y-%m-%d"))
assert {"2019-04-18", "2019-01-18", "2019-07-03", "2019-11-27", "2019-12-24"} <= dates, sorted(d for d in dates if d.startswith("2019"))
print(f"5. veilles de ferie 2019 : {sorted(x for x in dates if x.startswith('2019'))} : OK")
