"""Zone de bruit corrigee (V1) avec reglages : largeur k, nombre de jours de la moyenne, intervalle entre les
controles, type de stop suiveur. Memes regles que zone_failles/journal.py zone(propre=True) pour k = 1, 14 jours,
30 min, stop limite ou VWAP (verifie par test_moteur.py)."""
import sys
from pathlib import Path

import numpy as np
from numba import njit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "zone_failles"))
import journal as Z  # noqa: E402

N = 390
STOPS = {"limite ou VWAP": 0, "VWAP seul": 1, "limite seule": 2}


@njit(cache=True)
def zone_nb(C, ouv, veille, vwap, sigma, ok, k, pas, stop):
    nd = C.shape[0]
    brut = np.zeros(nd)
    allers = np.zeros(nd)
    for d in range(nd):
        if not ok[d] or np.isnan(veille[d]) or np.isnan(sigma[d, pas]):
            continue
        hr = max(ouv[d], veille[d])
        br = min(ouv[d], veille[d])
        pos = 0
        entree = 0.0
        tot = 0.0
        n = 0
        for m in range(pas, N, pas):
            p = C[d, m]
            ub = hr * (1 + k * sigma[d, m])
            lb = br * (1 - k * sigma[d, m])
            if stop == 0:
                lim_l, lim_c = max(ub, vwap[d, m]), min(lb, vwap[d, m])
            elif stop == 1:
                lim_l, lim_c = vwap[d, m], vwap[d, m]
            else:
                lim_l, lim_c = ub, lb
            if pos > 0 and p <= lim_l:
                tot += p - entree
                pos = 0
            elif pos < 0 and p >= lim_c:
                tot += entree - p
                pos = 0
            if pos == 0:
                if p > ub:
                    pos, entree, n = 1, p, n + 1
                elif p < lb:
                    pos, entree, n = -1, p, n + 1
        if pos != 0:
            tot += pos * (C[d, N - 1] - entree)
        brut[d] = tot
        allers[d] = n
    return brut, allers


class Zone:
    """Prepare les niveaux une fois par nombre de jours, puis joue n'importe quel reglage."""

    def __init__(self, J, O, H, L, C, P, X):
        self.J, self.C, self.ouv = J, C, O[:, 0]
        self.niv = {n: Z.niveaux_propres(J, O, H, L, C, P, X, jours_moyenne=n) for n in (7, 14, 28)}

    def jouer(self, k, n, pas, stop):
        sigma, veille, vwap, ok = self.niv[n]
        return zone_nb(self.C, self.ouv, veille, vwap, sigma, ok, float(k), int(pas), STOPS[stop])
