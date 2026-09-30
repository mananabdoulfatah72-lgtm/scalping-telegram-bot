#!/usr/bin/env python3
"""Tests du tournoi : pas de regard vers le futur, cassure comparee a une version Python simple, achat simple exact.
Lancer depuis ce dossier : python3 test_concurrents.py"""
import numpy as np

import concurrents as K
from explorer import charger


def cassure_simple(O, H, L, C, d, cout, haut, bas, sa, sv, debut):
    pos = 0
    for m in range(debut, 390):
        if pos == 0:
            up, dn = H[d, m] > haut, L[d, m] < bas
            if up and dn:
                return 0.0
            if up:
                pos, e, stop = 1, max(haut, O[d, m]), sa
                if L[d, m] <= stop:
                    return stop - e - cout
            elif dn:
                pos, e, stop = -1, min(bas, O[d, m]), sv
                if H[d, m] >= stop:
                    return e - stop - cout
        elif pos > 0 and L[d, m] <= stop:
            return min(stop, O[d, m]) - e - cout
        elif pos < 0 and H[d, m] >= stop:
            return e - max(stop, O[d, m]) - cout
    return pos * (C[d, 389] - e) - cout if pos else 0.0


def main():
    J, O, H, L, C, P, X = charger("nasdaq100")
    cout = K.st.cout_aller_retour("nasdaq100")
    res, ok = K.toutes(J, O, H, L, C, P, X, cout)
    # 1. cassure : identique a la version simple (range d'ouverture 30 min) sur 300 seances
    hh, ll = H[:, :30].max(axis=1), L[:, :30].min(axis=1)
    rng = np.random.default_rng(3)
    for d in rng.choice(np.where(ok)[0], 300, replace=False):
        assert abs(res["Range d'ouverture 30 min"][d] - cassure_simple(O, H, L, C, d, cout, hh[d], ll[d], ll[d], hh[d], 30)) < 1e-9
    print("1. cassure = version simple (300 seances) : OK")
    # 2. achat simple = cloture - ouverture - frais
    a = res["Achat simple intraday"]
    assert np.allclose(a[ok], C[ok, 389] - O[ok, 0] - cout) and np.all(a[~ok] == 0)
    print("2. achat simple exact, rien les jours exclus : OK")
    # 3. modifier une seance a partir de la minute k ne change aucune seance anterieure
    for essai in range(10):
        d, k = int(rng.integers(100, len(J) - 5)), int(rng.integers(0, 390))
        O2, H2, L2, C2 = (x.copy() for x in (O, H, L, C))
        f = rng.uniform(0.98, 1.02, size=(len(J) - d, 390))
        for x in (O2, H2, L2, C2):
            x[d:, :] *= f
        for x, y in ((O2, O), (H2, H), (L2, L), (C2, C)):
            x[d, :k] = y[d, :k]
        res2, _ = K.toutes(J, O2, H2, L2, C2, P, X, cout)
        for nom in res:
            assert np.array_equal(res[nom][:d], res2[nom][:d]), f"regard vers le futur : {nom}"
    print("3. aucune seance passee modifiee par le futur (10 essais, 15 strategies) : OK")


if __name__ == "__main__":
    main()
