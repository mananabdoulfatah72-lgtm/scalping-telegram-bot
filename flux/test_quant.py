#!/usr/bin/env python3
"""Controles de la partie 3, avant tout resultat : aucun regard vers le futur (minutes apres t et seances suivantes
remplacees par du hasard : signaux identiques jusqu'a t, pour les 9 familles du tape et pour G2b) et gestion en unites
de volatilite sur des minutes fabriquees.
Lancer : KB=<copie de claude/keen-babbage-r686cl> python3 flux/test_quant.py"""
import numpy as np

import donnees as D
import quant as Q


def brouille(arrs, d, k, rng):
    out = []
    for a in arrs:
        b = a.copy()
        bruit = np.round(a * (1 + 0.01 * rng.standard_normal(a.shape)) / 0.25) * 0.25
        b[d, k + 1:] = bruit[d, k + 1:]
        b[d + 1:] = bruit[d + 1:]
        out.append(b)
    return out


def comparer(X, X2, familles, d, k):
    n = 0
    for fam in familles:
        for sg in Q.FAMILLES["G2" if fam == "G2b" else fam]:
            a = Q.signaux(X, fam, sg)
            b = Q.signaux(X2, fam, sg)
            ga = [(s, t, x) for s, t, x in zip(a[0][:a[3]], a[1][:a[3]], a[2][:a[3]]) if s < d or (s == d and t <= k)]
            gb = [(s, t, x) for s, t, x in zip(b[0][:b[3]], b[1][:b[3]], b[2][:b[3]]) if s < d or (s == d and t <= k)]
            assert ga == gb, (fam, sg, d, k, len(ga), len(gb))
            n += len(ga)
    return n


def test_futur_tape():
    m, info, _ = D.seances()
    o, h, l, c = (m[x].astype(float) for x in ("o", "h", "l", "c"))
    a, v = m["achats"].astype(float), m["ventes"].astype(float)
    bl = Q.gros_lots(info["jour"].pipe(lambda j: __import__("pandas").DatetimeIndex(j)))
    X, _ = Q.tape()
    jou = X["jouable"]
    rng = np.random.default_rng(5)
    total = 0
    for essai in range(6):
        d = int(rng.choice(np.flatnonzero(jou[25:]) + 25))
        k = int(rng.integers(30, 360))
        o2, h2, l2, c2 = brouille((o, h, l, c), d, k, rng)
        h2, l2 = np.maximum.reduce([h2, o2, c2]), np.minimum.reduce([l2, o2, c2])
        a2, v2 = (np.abs(x) for x in brouille((a, v), d, k, rng))
        bl2 = {t: brouille((x,), d, k, rng)[0] for t, x in bl.items()}
        X2 = Q.mesures(o2, h2, l2, c2, a2, v2, jou, bl2)
        total += comparer(X, X2, [f for f in Q.FAMILLES if f != "G2b"], d, k)
    print(f"tape : aucun regard vers le futur, 6 coupures, {total} signaux identiques avant la coupure (G1 - G9)")


def test_futur_g2b():
    arr, jours, change = Q.barres_15_ans()
    o, h, l, c, v = arr["o"], arr["h"], arr["l"], arr["c"], arr["v"]
    a, s = Q.bvc(c, v)
    jou = ~change & (np.arange(len(jours)) >= 6)
    sl = slice(0, 300)                                  # 300 premieres seances : assez pour le controle
    X = Q.mesures(o[sl], h[sl], l[sl], c[sl], a[sl], s[sl], jou[sl], scale=30000.0 / o[sl, 0])
    rng = np.random.default_rng(6)
    d, k = 200, 200
    o2, h2, l2, c2, v2 = brouille((o[sl], h[sl], l[sl], c[sl], v[sl]), d, k, rng)
    h2, l2 = np.maximum.reduce([h2, o2, c2]), np.minimum.reduce([l2, o2, c2])
    a2, s2 = Q.bvc(c2, np.abs(v2))
    X2 = Q.mesures(o2, h2, l2, c2, a2, s2, jou[sl], scale=30000.0 / o2[:, 0])
    n = comparer(X, X2, ["G2b"], d, k)
    print(f"G2b : aucun regard vers le futur, {n} signaux identiques avant la coupure")


def test_gestion():
    S = 1
    base = 30000.0
    o, h, l, c = (np.full((S, 390), base) for _ in range(4))
    u = np.full((S, 390), 40.0)
    sc = np.ones(S)
    so, to, do_ = np.array([0]), np.array([100]), np.array([1])
    tr = np.zeros((1, 4))
    # achat a 30 000,25, stop 0,5 u = 20 points -> 29 980,25 arrondi vers la perte 29 980,25 ; objectif 1 u -> 30 040,25
    h[0, 105], l[0, 105] = 30041.0, 29999.0
    Q.jouer(o, h, l, c, u, sc, so, to, do_, 1, 30, 0.5, 1.0, 1, np.zeros(S), np.zeros(S), tr)
    assert abs(tr[0, 2] - (30040.25 - 30000.25 - 1.0)) < 1e-9, tr
    # meme minute stop et objectif : stop - 1 tick
    l[0, 105] = 29970.0
    Q.jouer(o, h, l, c, u, sc, so, to, do_, 1, 30, 0.5, 1.0, 1, np.zeros(S), np.zeros(S), tr)
    assert abs(tr[0, 2] - (29980.0 - 30000.25 - 1.0)) < 1e-9, tr
    # sans stop ni objectif, jusqu'a 15 h 59 ; prix au niveau d'aujourd'hui (x 2)
    h[0, 105], l[0, 105] = base, base
    c[0, 389] = 30010.0
    Q.jouer(o, h, l, c, u, np.array([2.0]), so, to, do_, 1, 0, 0.0, 0.0, 1, np.zeros(S), np.zeros(S), tr)
    assert abs(tr[0, 2] - ((30009.75 - 30000.25) * 2 - 1.0)) < 1e-9, tr
    # sens inverse et resultat inverse (placebo)
    Q.jouer(o, h, l, c, u, sc, so, to, do_, 1, 0, 0.0, 0.0, -1, np.zeros(S), np.zeros(S), tr)
    assert abs(tr[0, 2] - (29999.75 - 30010.25 - 1.0)) < 1e-9 and abs(tr[0, 3] - (30009.75 - 30000.25 - 1.0)) < 1e-9, tr
    print("gestion : stop et objectif en u, stop avant objectif, sortie a 15 h 59, prix d'aujourd'hui, sens inverse : ok")


if __name__ == "__main__":
    test_gestion()
    test_futur_tape()
    test_futur_g2b()
