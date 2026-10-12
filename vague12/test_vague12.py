#!/usr/bin/env python3
"""Controles de la vague 12 (README.md). Lancer depuis ce dossier : python3 test_vague12.py.
1. Limite tres longue = pas de limite : memes sorties et memes retraits.
2. Avec la limite de 30 jours, un achat est valide si et seulement si, sans limite, il valide dans les 30 jours ; dans ce
   cas, sorties et retraits identiques. Sinon il expire (issue 0), sauf s'il etait perdu avant la limite.
3. Frein du compte finance egal au frein du challenge (c_mnq_f) = ancien appel sans c_mnq_f.
4. Taille 1, frein, Legacy : le moteur minute par minute avec la limite redonne le moteur journalier exact du Monte
   Carlo (tables.npz) sur des achats du filtre 'fort:0' (meme issue, memes seances pour valider)."""
import sys

import numpy as np

import regles12 as K

sys.path.insert(0, str(K.R0 / "montecarlo"))
import moteur_jour as MJ  # noqa: E402


def main():
    P = K.MC.preparer()
    d0, d1, lim, _ = K.achats(P)
    rng = np.random.default_rng(12)
    jours = rng.choice(np.arange(d0, d1), 300, replace=False)
    b = P["bases"]["fort"][0]
    nj = len(P["jours"])
    A = K.COMPTES["legacy"]
    for q in (1, 3):
        n_val = 0
        for d in jours:
            sv = min(K.H, nj - d)
            ret0 = np.zeros(sv)
            r0 = K.M4.parcours4(d, 4, P["kN"], P["kE"], ret0, *b, *A["E"], *A["F"], sv, q, 1, 1e18, 0.0, 0, 1750.0, 0.0,
                                0, 500.0, 0, 1750.0)
            retL = np.zeros(sv)
            rL = K.M4.parcours4(d, 4, P["kN"], P["kE"], retL, *b, *A["E"], *A["F"], sv, q, 1, 1e18, 0.0, 0, 1750.0, 0.0,
                                0, 500.0, 10**6, 1750.0)
            assert rL == r0 and np.array_equal(retL, ret0), ("limite longue", d, q)
            r1, ret1 = K.un_achat(P, b, d, "legacy", q, 1750.0, 1750.0, sv, lim[d])
            if r0[0] == 1 and r0[1] <= lim[d]:
                assert r1 == r0 and np.array_equal(ret1, ret0), ("valide dans les 30 jours", d, q)
                n_val += 1
            elif r0[0] == -1 and r0[1] <= lim[d]:
                assert r1[0] == -1 and r1[1] == r0[1], ("perdu dans les 30 jours", d, q)
            else:
                assert r1[0] == 0 and r1[3] == 0 and ret1.sum() == 0.0, ("expire", d, q, r0, r1)
            ret2 = np.zeros(sv)
            r2 = K.M4.parcours4(d, 4, P["kN"], P["kE"], ret2, *b, *A["E"], *A["F"], sv, q, 1, 1e18, 0.0, 0, 1750.0)
            ret3 = np.zeros(sv)
            r3 = K.M4.parcours4(d, 4, P["kN"], P["kE"], ret3, *b, *A["E"], *A["F"], sv, q, 1, 1e18, 0.0, 0, 1750.0, 0.0,
                                0, 0.0, 0, 1750.0)
            assert r2 == r3 and np.array_equal(ret2, ret3), ("c_mnq_f", d, q)
        print(f"ok : taille {q}, 300 achats : limite longue = pas de limite ; 30 jours coherents ({n_val} valides) ;"
              " c_mnq_f = ancien appel")
    z = np.load(K.R0 / "montecarlo" / "tables.npz")
    t = list(z["tirages"]).index("fort:0")
    j_tab = z["seances"]
    ret = np.zeros(64)
    n = 0
    for d in jours:
        sv = min(K.H, nj - d)
        r1, _ = K.un_achat(P, b, d, "legacy", 1, 1750.0, 1750.0, sv, lim[d])
        row = int(np.searchsorted(j_tab, d))
        assert j_tab[row] == d
        lig = np.arange(row, row + lim[d], dtype=np.int64)
        rj = MJ.parcours_jour(lig, z["gain"][t], z["pire"][t], z["drap"][t], 0, 1750.0, 3000.0, 2500.0, 100.0, 2500.0,
                              100.0, 10, .4, 1000.0, 1500.0, 2600.0, 3, ret)
        iss_j = rj[0]
        assert r1[0] == iss_j, ("tables", d, r1, rj)
        if iss_j == 1:
            assert r1[1] == rj[1], ("seances pour valider", d)
            n += 1
    print(f"ok : taille 1, Legacy, 300 achats : moteur minute + limite = moteur journalier exact ({n} valides)")
    print("tous les controles passent")


if __name__ == "__main__":
    main()
