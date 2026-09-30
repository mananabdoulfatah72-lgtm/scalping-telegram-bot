"""Profil de volume d'une seance (README.md) : le volume de chaque barre est reparti a parts egales sur les ticks
entre son plus bas et son plus haut ; POC = prix au plus fort volume ; zone de valeur = 70 % du volume, construite
depuis le POC en ajoutant a chaque pas les deux lignes les plus chargees (au-dessus ou au-dessous)."""
import numpy as np
from numba import njit


@njit(cache=True)
def profil(H, L, V, tick, part=0.70):
    """H, L, V : seances x barres. Renvoie (poc, haut, bas) de chaque seance (NaN si pas de volume)."""
    nd, nb = H.shape
    poc = np.full(nd, np.nan)
    haut = np.full(nd, np.nan)
    bas = np.full(nd, np.nan)
    for d in range(nd):
        lo = L[d, 0]
        hi = H[d, 0]
        for m in range(nb):
            if L[d, m] < lo:
                lo = L[d, m]
            if H[d, m] > hi:
                hi = H[d, m]
        n = int(round((hi - lo) / tick)) + 1
        hist = np.zeros(n)
        total = 0.0
        for m in range(nb):
            if V[d, m] <= 0:
                continue
            a = int(round((L[d, m] - lo) / tick))
            b = int(round((H[d, m] - lo) / tick))
            part_m = V[d, m] / (b - a + 1)
            for k in range(a, b + 1):
                hist[k] += part_m
            total += V[d, m]
        if total <= 0:
            continue
        p = 0
        for k in range(1, n):
            if hist[k] > hist[p]:
                p = k
        acc = hist[p]
        up = p
        dn = p
        while acc < part * total and (up < n - 1 or dn > 0):
            s_up = 0.0
            for k in range(up + 1, min(n, up + 3)):
                s_up += hist[k]
            s_dn = 0.0
            for k in range(max(0, dn - 2), dn):
                s_dn += hist[k]
            if up >= n - 1 or (dn > 0 and s_dn > s_up):
                acc += s_dn
                dn = max(0, dn - 2)
            else:
                acc += s_up
                up = min(n - 1, up + 2)
        poc[d] = lo + p * tick
        haut[d] = lo + up * tick
        bas[d] = lo + dn * tick
    return poc, haut, bas
