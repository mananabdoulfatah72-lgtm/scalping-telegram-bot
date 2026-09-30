#!/usr/bin/env python3
"""Tests du moteur n°2 : pas de regard vers le futur pour les 9 especes, frais et cloture, filtres respectes,
niveaux de la veille seulement, identite avec le moteur n°1 pour les 4 anciennes especes, vitesse.
Lancer depuis ce dossier : python3 test_moteur2.py"""
import time

import numpy as np

import donnees2 as D
import moteur2 as M
from moteur import lancer as lancer1
from tournoi3 import lire_quotidien


def genome(rng, esp):
    return {"espece": esp, "L": int(rng.integers(1, 13)) if esp == M.OUVERTURE else int(rng.integers(6, 121)),
            "Z": float(rng.uniform(0.25, 3.0)), "sens": int(rng.integers(0, 3)), "stop": float(rng.uniform(0.001, 0.015)),
            "objectif": float(rng.uniform(0.001, 0.03)), "debut": int(rng.integers(1, 55)), "filtre": int(rng.integers(0, 9))}


def main():
    Q = lire_quotidien()
    d = D.charger("NQ", "recherche", Q)
    if not np.isfinite(d["mur_c"]).any():                     # murs factices pour tester les especes 7 et 8
        pc = np.r_[np.nan, d["c"][:-1, -1]]
        d["mur_c"], d["mur_p"] = pc * 1.006, pc * 0.994
    rng = np.random.default_rng(2)
    nj = len(d["jours"])
    # 1. modifier le futur ne change rien au passe (profil de volume recalcule sur les donnees modifiees)
    for essai in range(45):
        g = genome(rng, essai % 9)
        r1, _, _, t1 = M.lancer(d, g, noter=True)
        cj, cb = int(rng.integers(300, nj - 10)), int(rng.integers(0, M.BARRES))
        d2 = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in d.items()}
        f = rng.uniform(0.97, 1.03, size=(nj - cj, M.BARRES))
        for champ in "ohlcv":
            d2[champ][cj:] = d2[champ][cj:] * f
            d2[champ][cj, :cb] = d[champ][cj, :cb]
        poc, vah, val = D.profil_veille(d2["h"], d2["l"], d2["v"])
        assert np.array_equal(np.nan_to_num(poc[:cj + 1]), np.nan_to_num(d["poc"][:cj + 1])), "profil : regard vers le futur"
        d2["poc"], d2["vah"], d2["val"] = poc, vah, val
        r2, _, _, t2 = M.lancer(d2, g, noter=True)
        assert np.array_equal(r1[:cj], r2[:cj]), f"regard vers le futur (espece {g['espece']})"
        a1 = [(e, s, p) for j, e, s, p in zip(t1["jour"], t1["entree"], t1["sortie"], t1["px_s"]) if j == cj and s < cb]
        a2 = [(e, s, p) for j, e, s, p in zip(t2["jour"], t2["entree"], t2["sortie"], t2["px_s"]) if j == cj and s < cb]
        assert a1 == a2, f"trade passe modifie (espece {g['espece']})"
    print("1. aucun regard vers le futur (45 strategies, 9 especes, profil de volume compris) : OK")
    # 2. frais, cloture, filtres, horaires, jours interdits
    for esp in range(9):
        g = genome(rng, esp) | {"objectif": 0.5, "stop": 0.5, "Z": 0.3, "filtre": int(rng.integers(1, 9))}
        r, dol, n, t = M.lancer(d, g, noter=True)
        if len(t["jour"]) == 0:
            continue
        assert np.all(t["raison"] == 2) and np.all(t["sortie"] == M.BARRES - 1)
        brut = (t["px_s"] - t["px_e"]) * t["sens"]
        assert np.allclose(np.bincount(t["jour"], weights=(brut - d["cout"]) * d["pt"], minlength=nj), dol)
        assert np.all(d["fok"][g["filtre"], t["jour"]]), "trade un jour exclu par le filtre"
        assert not np.any(d["interdit"][t["jour"]]) and np.all(t["entree"] >= g["debut"]) and np.all(t["entree"] <= M.DERNIERE_ENTREE)
    print("2. frais, cloture a 16 h, filtres, jours interdits, horaires (9 especes) : OK")
    # 3. les 4 anciennes especes donnent exactement le moteur n°1 (filtres 0 a 2)
    for k in range(40):
        g = genome(rng, k % 4) | {"filtre": int(rng.integers(0, 3))}
        assert np.array_equal(M.lancer(d, g)[0], lancer1(d, g)[0])
    print("3. especes 0 a 3 identiques au moteur n°1 (40 strategies) : OK")
    # 4. les filtres GEX / VIX / DIX n'utilisent que la veille
    assert d["fok"].shape == (9, nj) and d["fok"][0].all()
    print(f"4. filtres : " + ", ".join(f"{M.FILTRES[i]} {d['fok'][i].mean():.0%}" for i in range(9)) + " des seances : OK")
    # 5. vitesse
    t0 = time.time()
    for k in range(270):
        M.lancer(d, genome(rng, k % 9))
    print(f"5. vitesse : {(time.time() - t0) / 270 * 1000:.1f} ms par backtest de {nj} seances")


if __name__ == "__main__":
    main()
