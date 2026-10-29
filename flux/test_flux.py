#!/usr/bin/env python3
"""Controles du systeme order flow, avant tout resultat : aucun regard vers le futur (les minutes apres t et les seances
suivantes sont remplacees par du hasard, les signaux jusqu'a t ne changent pas) et execution dans l'ordre le plus
defavorable sur des minutes fabriquees.
Lancer : KB=<copie de claude/keen-babbage-r686cl> python3 flux/test_flux.py"""
import copy

import numpy as np

import donnees as D
import systeme as Y


def brouiller(m, d, k, rng):
    """Copie ou les minutes > k de la seance d et toutes les seances suivantes sont du hasard."""
    m2 = copy.deepcopy(m)
    for key in m2:
        a = m2[key]
        bruit = a * (1 + 0.01 * rng.standard_normal(a.shape))
        if key in ("o", "h", "l", "c"):
            bruit = np.round(bruit / Y.TICK) * Y.TICK
        a[d, k + 1:] = bruit[d, k + 1:]
        a[d + 1:] = bruit[d + 1:]
    m2["h"] = np.maximum.reduce([m2["h"], m2["o"], m2["c"]])
    m2["l"] = np.minimum.reduce([m2["l"], m2["o"], m2["c"]])
    return m2


def test_futur(m, info):
    rng = np.random.default_rng(7)
    X = Y.mesures(m, info)
    jouables = np.flatnonzero(X["jouable"])
    n_cmp = 0
    for essai in range(40):
        d = int(rng.choice(jouables))
        k = int(rng.integers(Y.DEBUT, Y.FIN))
        m2 = brouiller(m, d, k, rng)
        X2 = Y.mesures(m2, info)
        for nom, f in Y.SETUPS.items():
            for sans in (False, True):
                a = [s for s in f(m, X, d, sans) if s[0] <= k]
                b = [s for s in f(m2, X2, d, sans) if s[0] <= k]
                assert a == b, (nom, d, k, a, b)
                n_cmp += len(a)
    print(f"aucun regard vers le futur : 40 coupures, {n_cmp} signaux identiques avant la coupure")


def test_execution():
    n = D.NM
    base = 30000.0
    m = {k: np.full((1, n), base) for k in ("o", "h", "l", "c")}
    # achat a 30 000,25 (ouverture 30 000 + 1 tick), stop 29 997,25 (R = 3), objectif 30 006,25
    e = 100
    ent, stop, obj, R = Y.niveaux_trade(base, 1, base - 1.0)
    assert (ent, stop, obj, R) == (30000.25, 29997.25, 30006.25, 3.0), (ent, stop, obj, R)
    # minute qui touche stop et objectif : sortie au stop - 1 tick
    m["h"][0, e + 2], m["l"][0, e + 2] = 30010.0, 29990.0
    assert Y.suivre(m, 0, e, 1, ent, stop, obj) == (e + 2, 29997.0, "stop")
    # objectif touche sans etre traverse d'un tick : pas rempli ; traverse : rempli au prix de l'objectif
    m["h"][0, e + 2], m["l"][0, e + 2] = 30006.25, 29999.0
    m["h"][0, e + 3] = 30006.5
    assert Y.suivre(m, 0, e, 1, ent, stop, obj) == (e + 3, 30006.25, "objectif")
    # ouverture au-dela du stop : sortie a l'ouverture - 1 tick
    m["h"][0, e + 3] = 30001.0
    m["o"][0, e + 4], m["l"][0, e + 4] = 29995.0, 29994.0
    assert Y.suivre(m, 0, e, 1, ent, stop, obj) == (e + 4, 29994.75, "stop")
    # sortie au temps a la 30e minute (cloture - 1 tick)
    m = {k: np.full((1, n), base) for k in ("o", "h", "l", "c")}
    m["c"][0, e + 29] = 30002.0
    assert Y.suivre(m, 0, e, 1, ent, stop, obj) == (e + 29, 30001.75, "temps")
    # vente symetrique et risque trop grand
    ent, stop, obj, R = Y.niveaux_trade(base, -1, base + 10.13)
    assert (ent, stop, obj, R) == (29999.75, 30010.25, 29978.75, 10.5), (ent, stop, obj, R)
    assert Y.niveaux_trade(base, 1, base - 1.5)[3] == 3.0                    # stop ramene a 3 points au moins
    assert Y.niveaux_trade(base, 1, base - 2.85)[1:] == (29997.0, 30006.75, 3.25)   # stop arrondi vers la perte
    assert Y.niveaux_trade(base, 1, base - 40) is None                  # 40 points > 0,12 % de 30 000
    print("execution : stop avant objectif, objectif traverse d'un tick, ouverture au-dela du stop, temps, arrondis : ok")


if __name__ == "__main__":
    test_execution()
    m, info, _ = D.seances()
    test_futur(m, info)
