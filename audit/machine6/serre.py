#!/usr/bin/env python3
"""Descriptif (3 novembre 2026) : Supertrend plus serre (ligne a 1 ; 1,5 ; 2 ; 3 ATR), meme regle sinon, 1 MNQ, frais compris,
avec et sans la limite de 400 $, et challenge depuis 50 000 $ / plancher 49 000 $ (8 seances). Aucun reglage n'est choisi ici :
seule la ligne a 3 ATR a ete testee avant (partie H)."""
import sys
import numba as nb
import numpy as np
import pyramide as P


@nb.njit(cache=True)
def supertrend(H, L, C, mult):
    S = C.shape[0]; n = S * 78
    h5, l5, c5 = np.empty(n), np.empty(n), np.empty(n)
    for s in range(S):
        for b in range(78):
            i = s * 78 + b
            h5[i] = H[s, 5 * b:5 * b + 5].max(); l5[i] = L[s, 5 * b:5 * b + 5].min(); c5[i] = C[s, 5 * b + 4]
    st, atrs = np.zeros(n), np.zeros(n)
    atr, hb, lb, d = 0.0, np.nan, np.nan, 1.0
    for i in range(1, n):
        tr = max(h5[i] - l5[i], abs(h5[i] - c5[i - 1]), abs(l5[i] - c5[i - 1]))
        atr = tr if i == 1 else (atr * 9 + tr) / 10
        mid = (h5[i] + l5[i]) / 2
        hb2, lb2 = mid + mult * atr, mid - mult * atr
        if i > 1:
            hb2 = hb2 if (hb2 < hb or c5[i - 1] > hb) else hb
            lb2 = lb2 if (lb2 > lb or c5[i - 1] < lb) else lb
            if d > 0 and c5[i] < lb2:
                d = -1.0
            elif d < 0 and c5[i] > hb2:
                d = 1.0
        hb, lb = hb2, lb2
        st[i] = d if i >= 10 else 0.0
        atrs[i] = atr
    return st, atrs


J, O, H, L, C, ok = P.jours(sys.argv[1])
an = np.array([int(j[:4]) for j in J])
deb = np.where(ok & (np.arange(len(J)) > 200))[0].astype(np.int64)
print("1 MNQ, gains au prix d'aujourd'hui, 3 $ de frais par aller-retour")
for mult in (1.0, 1.5, 2.0, 3.0):
    st, atr = supertrend(H, L, C, mult)
    chg = np.zeros(len(J))
    for s in np.where(ok)[0]:
        seg = st[s * 78:s * 78 + 76]
        chg[s] = 1 + np.sum(seg[1:] != seg[:-1])
    lignes = []
    for lim in (0.0, 400.0):
        r, a, f, c, cp = P.journees(O, H, L, C, ok, st, atr, 0.0, 1, lim, P.PREF)
        x, x23 = r[ok], r[ok & (an >= 2023)]
        res = P.challenge(deb, a, f, c, ok, 8, 50000.0, 51500.0); res = res[res != 9]
        lignes.append(f"limite {int(lim) or 'aucune':>6} : {x.mean():+6.1f} $/seance (t {P.tstat(x):+.2f}), depuis 2023 {x23.mean():+6.1f} $ (t {P.tstat(x23):+.2f}),"
                      f" challenge {(res == 1).mean() * 100:4.1f} % / {(res == -1).mean() * 100:4.1f} %")
    print(f"ligne a {mult} ATR : {chg[ok].mean():.1f} trades par seance, frais {chg[ok].mean() * 3:.0f} $ par seance")
    for l in lignes:
        print("   ", l)
