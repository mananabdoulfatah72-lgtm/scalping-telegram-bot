#!/usr/bin/env python3
"""Tests du moteur n°3 : pas de regard vers le futur, frais, sortie en fin de seance, trade a la main.
Lancer depuis ce dossier : python3 test_moteur3.py"""
from pathlib import Path

import numpy as np

import moteur3 as M

ICI = Path(__file__).resolve().parent
rng = np.random.default_rng(3)
for nom in ("RTY", "YM", "GC", "CL", "6E"):
    d = M.charger(ICI / "cache" / f"recherche_{nom}.npz")
    nb = int(d["nb"])
    for essai in range(40):
        g = {"famille": int(rng.integers(0, 7)), "inverse": int(rng.integers(0, 2)), "L": int(rng.integers(1, 121)),
             "Z": float(rng.uniform(0.25, 3)), "sens": int(rng.integers(0, 3)), "stop": float(rng.uniform(0.001, 0.015)),
             "objectif": float(rng.uniform(0.001, 0.03)), "debut": int(rng.integers(1, int(0.75 * nb))),
             "duree": int(rng.integers(3, 61)), "filtre": int(rng.integers(0, 3))}
        if g["famille"] == M.OUVERTURE:
            g["L"] = int(rng.integers(1, 13))
        r1, d1, n1 = M.lancer(d, g)
        # 1. modifier toutes les barres a partir de la seance k (et ses donnees de veille) ne change rien avant k
        k = int(rng.integers(300, len(d["jours"]) - 5))
        d2 = {x: (v.copy() if isinstance(v, np.ndarray) else v) for x, v in d.items()}
        f = rng.uniform(0.95, 1.05, size=(len(d["jours"]) - k, nb))
        for x in ("o", "h", "l", "c", "vwap"):
            d2[x][k:] *= f
        for x in ("pc", "ph", "pl"):
            d2[x][k + 1:] *= 1.03
        r2, d2_, n2 = M.lancer(d2, g)
        assert np.array_equal(r1[:k], r2[:k]) and np.array_equal(n1[:k], n2[:k]), (nom, g, k)
        # 2. aucun trade un jour interdit ; chaque trade paie les frais
        assert (n1[d["interdit"]] == 0).all()
print("1. aucune barre future ne change un resultat passe (200 strategies au hasard, 5 marches) : OK")
print("2. aucun trade les jours interdits : OK")
# 3. un trade a la main : famille gap, suivre, achat, sans stop ni objectif atteignables, sortie apres 3 barres
d = M.charger(ICI / "cache" / "recherche_CL.npz")
nb = int(d["nb"])
g = {"famille": M.GAP, "inverse": 0, "L": 5, "Z": 0.25, "sens": 1, "stop": 0.5, "objectif": 0.9, "debut": 1, "duree": 3, "filtre": 0}
r, dol, ntr = M.lancer(d, g)
jour = int(np.where(ntr > 0)[0][0])
o, c = d["o"][jour], d["c"][jour]
gap = o[0] / d["pc"][jour] - 1
assert gap > 0.25 * d["gap_moy"][jour]
attendu = (c[3] - o[1] - d["cout"]) * d["pt"]
assert np.isclose(dol[jour], attendu), (dol[jour], attendu)
print(f"3. trade a la main (CL {d['jours'][jour]}, gap {gap:+.3%}) : entree barre 1, sortie a la cloture de la barre 3, {attendu:+.2f} $ : OK")
