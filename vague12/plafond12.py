#!/usr/bin/env python3
"""Vague 12, descriptif (ne sert pas a choisir) : chance de valider en 30 jours selon la taille, de 1 a 8, Bulenox Legacy
sans frein, challenge seulement, filtre comme 2026 (10 tirages). Montre ou la taille cesse d'aider. Ecrit plafond12.txt."""
import multiprocessing as mp

import numpy as np

import regles12 as K
import vague12 as V

TAILLES = (1, 2, 3, 4, 5, 6, 8)


def tache(args):
    q, t = args
    A = K.COMPTES["legacy"]
    out = []
    for d in V.jours_achat("legacy"):
        lim = int(V.LIM[d])
        ret = np.zeros(lim + 1)
        r = K.M4.parcours4(int(d), 4, V.P["kN"], V.P["kE"], ret, *V.P["bases"]["fort"][t], *A["E"], *A["F"], lim + 1, q, 1,
                           1e18, 0.0, 0, 0.0, 0.0, 0, 0.0, lim, 0.0)
        out.append((d, r[0]))
    return q, np.array(out)


def main():
    res = {}
    with mp.get_context("fork").Pool(4) as pool:
        for q, out in pool.imap_unordered(tache, [(q, t) for q in TAILLES for t in range(10)]):
            res.setdefault(q, []).append(out)
    L = ["Bulenox Legacy, sans frein, challenge de 30 jours, filtre comme 2026 : validé / perdu / expiré selon la taille", ""]
    for g, (a, z) in (("2012-2021", (V.D0, V.CHOIX_FIN)), ("2023 - août 2026", (V.VERIF_DEB, V.NJ))):
        L.append(f"achats {g}")
        for q in TAILLES:
            x = np.vstack(res[q]); y = x[(x[:, 0] >= a) & (x[:, 0] < z), 1]
            L.append(f"  taille {q} : validé {np.mean(y == 1):.0%}, perdu {np.mean(y == -1):.0%}, expiré {np.mean(y == 0):.0%}")
        L.append("")
    (K.ICI / "plafond12.txt").write_text("\n".join(L) + "\n"); print("\n".join(L))


if __name__ == "__main__":
    main()
