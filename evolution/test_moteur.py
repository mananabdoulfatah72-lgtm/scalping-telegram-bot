#!/usr/bin/env python3
"""Tests du moteur : pas de regard vers le futur, frais, fermeture a 16 h, vitesse.
Lancer depuis ce dossier : python3 test_moteur.py"""
import time
from pathlib import Path

import numpy as np

import moteur as M

ICI = Path(__file__).resolve().parent


def genome_hasard(rng, espece):
    return {"espece": espece, "L": int(rng.integers(1, 13)) if espece == M.OUVERTURE else int(rng.integers(6, 121)),
            "Z": float(rng.uniform(0.25, 3.0)), "sens": int(rng.integers(0, 3)), "stop": float(rng.uniform(0.001, 0.015)),
            "objectif": float(rng.uniform(0.001, 0.03)), "debut": int(rng.integers(1, 55)), "filtre": int(rng.integers(0, 3))}


def main():
    d = M.charger(ICI / "cache" / "recherche_NQ.npz")
    rng = np.random.default_rng(1)
    nj = len(d["jours"])
    # 1. modifier le futur ne change rien au passe
    for essai in range(40):
        g = genome_hasard(rng, essai % 4)
        r1, _, n1, t1 = M.lancer(d, g, noter=True)
        coupe_j = int(rng.integers(200, nj - 10))
        coupe_b = int(rng.integers(0, M.BARRES))
        d2 = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in d.items()}
        facteur = rng.uniform(0.97, 1.03, size=(nj - coupe_j, M.BARRES))
        for champ in "ohlc":
            a = d2[champ]
            a[coupe_j:, :] = a[coupe_j:, :] * facteur
            a[coupe_j, :coupe_b] = d[champ][coupe_j, :coupe_b]      # la seance coupee garde ses barres passees
        r2, _, n2, t2 = M.lancer(d2, g, noter=True)
        assert np.array_equal(r1[:coupe_j], r2[:coupe_j]), f"regard vers le futur (espece {g['espece']})"
        # trades de la seance coupee sortis avant la coupure : identiques
        avant1 = [(e, s, px) for j, e, s, px in zip(t1["jour"], t1["entree"], t1["sortie"], t1["px_s"]) if j == coupe_j and s < coupe_b]
        avant2 = [(e, s, px) for j, e, s, px in zip(t2["jour"], t2["entree"], t2["sortie"], t2["px_s"]) if j == coupe_j and s < coupe_b]
        assert avant1 == avant2, "trade passe modifie par une barre future"
    print("1. aucun regard vers le futur (40 strategies, 4 especes) : OK")
    # 2. frais et fermeture a 16 h ; pas de position la nuit ; pas de trade les jours interdits
    g = genome_hasard(rng, M.MOMENTUM) | {"objectif": 0.5, "stop": 0.5, "Z": 0.5}      # ni stop ni objectif atteints
    r, dol, n, t = M.lancer(d, g, noter=True)
    assert np.all(t["raison"] == 2) and np.all(t["sortie"] == M.BARRES - 1), "sortie hors cloture"
    brut = (t["px_s"] - t["px_e"]) * t["sens"]
    assert np.allclose(np.bincount(t["jour"], weights=(brut - d["cout"]) * d["pt"], minlength=nj), dol), "frais mal comptes"
    assert not np.any(d["interdit"][t["jour"]]), "trade un jour interdit"
    assert np.all(t["entree"] >= g["debut"]) and np.all(t["entree"] <= M.DERNIERE_ENTREE), "entree hors horaires"
    print("2. frais, cloture a 16 h, jours interdits, horaires : OK")
    # 3. vitesse
    t0 = time.time()
    for k in range(200):
        M.lancer(d, genome_hasard(rng, k % 4))
    print(f"3. vitesse : {(time.time() - t0) / 200 * 1000:.1f} ms par backtest de {nj} seances")


if __name__ == "__main__":
    main()
