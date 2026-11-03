#!/usr/bin/env python3
"""Supertrend 10-3 avec pyramide (audit/machine6/PYRAMIDE.md) : +1 MNQ a chaque avance de k x N dans le sens du trade,
4 MNQ au plus, limite du jour 400 $, puis challenge depuis 50 000 $ / plancher 49 000 $ suivi en temps reel.
Lancer : python3 audit/machine6/pyramide.py <minutes 15 ans.csv> <minutes recentes.csv>"""
import sys

import numba as nb
import numpy as np
import pandas as pd

N = 390
PREF = 28500.0


def jours(csv):
    d = pd.read_csv(csv, usecols=["t", "o", "h", "l", "c"])
    j = d["t"].str[:10]
    m = d["t"].str[11:13].astype(int) * 60 + d["t"].str[14:16].astype(int) - 570
    g = (m >= 0) & (m < N)
    d, j, m = d[g], j[g], m[g].to_numpy()
    J = np.array(sorted(j.unique()))
    i = pd.Index(J).get_indexer(j)
    A = {}
    for k in "ohlc":
        a = np.full((len(J), N), np.nan)
        a[i, m] = d[k].to_numpy(float)
        A[k] = a
    pres = ~np.isnan(A["c"])
    C = pd.DataFrame(A["c"]).ffill(axis=1).bfill(axis=1).to_numpy()
    O, H, L = [np.where(np.isnan(A[k]), C, A[k]) for k in "ohl"]
    ok = pres[:, 0] & pres[:, N - 1] & (pres.sum(1) >= 370)
    return J, O, H, L, C, ok


@nb.njit(cache=True)
def supertrend(H, L, C):
    S = C.shape[0]
    n = S * 78
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
        hb2, lb2 = mid + 3 * atr, mid - 3 * atr
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


@nb.njit(cache=True)
def journees(O, H, L, C, ok, st, atrs, k, umax, lim, pref):
    """Par seance : resultat, et chemins minute par minute (pire, meilleur, cloture) du resultat de la journee."""
    S = C.shape[0]
    res = np.zeros(S)
    adv, fav, clo = np.zeros((S, N)), np.zeros((S, N)), np.zeros((S, N))
    coupe = np.zeros(S, np.bool_)
    for s in range(S):
        if not ok[s]:
            continue
        ech = 2.0 * pref / O[s, 0] if pref > 0 else 2.0   # $ par point et par MNQ (au prix d'aujourd'hui, ou reel)
        pos, units = 0, 0
        prix = np.zeros(8)
        real, dernier, Nfixe = 0.0, 0.0, 0.0
        act_sortie, act_entree, act_ajout = False, 0, False
        arret = False
        for m in range(N):
            if not arret and m <= 384:
                o = O[s, m]
                if act_sortie:
                    for u in range(units):
                        real += pos * (o - prix[u]) * ech - 3.0
                    pos, units = 0, 0
                if act_entree != 0:
                    pos, units = act_entree, 1
                    prix[0] = o; dernier = o
                if act_ajout and units < umax:
                    prix[units] = o; units += 1; dernier = o
                act_sortie, act_entree, act_ajout = False, 0, False
                # pire et meilleur prix de la minute
                a = L[s, m] if pos > 0 else H[s, m]
                f = H[s, m] if pos > 0 else L[s, m]
                lat_a, lat_f, lat_c = 0.0, 0.0, 0.0
                for u in range(units):
                    lat_a += pos * (a - prix[u]) * ech - 3.0
                    lat_f += pos * (f - prix[u]) * ech - 3.0
                    lat_c += pos * (C[s, m] - prix[u]) * ech - 3.0
                if lim > 0 and units > 0 and real + lat_a <= -lim:
                    real = -lim - units * ech * 1.0       # sortie au niveau de la limite, 1 point de glissement
                    pos, units = 0, 0
                    arret = True
                    coupe[s] = True
                    adv[s, m] = real; fav[s, m] = real; clo[s, m] = real
                    continue
                adv[s, m] = real + lat_a; fav[s, m] = real + lat_f; clo[s, m] = real + lat_c
                if m == 384:
                    for u in range(units):
                        real += pos * (C[s, m] - prix[u]) * ech - 3.0
                    pos, units = 0, 0
                    clo[s, m] = real
                elif m % 5 == 4 and m // 5 <= 75:
                    i = s * 78 + m // 5
                    cible = pos if st[i] == 0 else int(st[i])
                    if cible != pos and pos != 0:
                        act_sortie = True
                    if cible != 0 and (pos == 0 or act_sortie) and m + 1 <= 360:
                        act_entree = cible
                        Nfixe = atrs[i]
                    elif pos != 0 and cible == pos and k > 0 and units < umax and m + 1 <= 360:
                        if pos * (C[s, m] - dernier) >= k * Nfixe:
                            act_ajout = True
            else:
                adv[s, m] = real; fav[s, m] = real; clo[s, m] = real
        res[s] = real
    return res, adv, fav, clo, coupe


@nb.njit(cache=True)
def challenge(debuts, adv, fav, clo, ok, nseances, solde0, haut0):
    out = np.zeros(len(debuts), np.int64)
    S = adv.shape[0]
    for z in range(len(debuts)):
        solde, haut = solde0, haut0
        issue = 0
        for q in range(nseances):
            s = debuts[z] + q
            if s >= S:
                issue = 9
                break
            fin = False
            for m in range(N):
                pl = min(haut - 2500.0, 50100.0)
                if solde + adv[s, m] <= pl:
                    issue = -1; fin = True
                    break
                if solde + fav[s, m] > haut:
                    haut = solde + fav[s, m]
                if solde + clo[s, m] >= 53050.0:
                    issue = 1; fin = True
                    break
            if fin:
                break
            solde += clo[s, N - 1]
        out[z] = issue
    return out


def tstat(x):
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x))


def main():
    J, O, H, L, C, ok = jours(sys.argv[1])
    st, atrs = supertrend(H, L, C)
    an = np.array([int(j[:4]) for j in J])
    variantes = [("1 MNQ sans ajout (temoin)", 0.0, 1), ("ajout tous les 0,5 N (Turtles)", 0.5, 4), ("ajout tous les 1 N", 1.0, 4)]
    print("15 ans (2011 - octobre 2026), limite du jour 400 $, gains au prix d'aujourd'hui")
    out = {}
    for nom, k, u in variantes:
        r, a, f, c, cp = journees(O, H, L, C, ok, st, atrs, k, u, 400.0, PREF)
        out[nom] = (a, f, c)
        x = r[ok]; x23 = r[ok & (an >= 2023)]
        print(f"  {nom:32s} {x.mean():+6.1f} $/seance (t {tstat(x):.2f}) ; depuis 2023 {x23.mean():+6.1f} $ (t {tstat(x23):.2f}) ;"
              f" pire journee {x.min():+.0f} $ ; journees coupees a -400 $ : {cp[ok].mean() * 100:.0f} %")
    print("\nChallenge depuis 50 000 $, plancher 49 000 $ (temps reel), 8 seances : reussis / echoues")
    debuts = np.where(ok & (np.arange(len(J)) > 200))[0].astype(np.int64)
    for nom in out:
        a, f, c = out[nom]
        for lab, sel in (("15 ans", debuts), ("2024-26", debuts[an[debuts] >= 2024])):
            res = challenge(sel, a, f, c, ok, 8, 50000.0, 51500.0)
            res = res[res != 9]
            print(f"  {nom:32s} {lab} : {(res == 1).mean() * 100:5.1f} % / {(res == -1).mean() * 100:5.1f} %")
    if len(sys.argv) > 2:
        J2, O2, H2, L2, C2, ok2 = jours(sys.argv[2])
        st2, atr2 = supertrend(H2, L2, C2)
        sel = np.array([j >= "2026-10-13" for j in J2])
        print("\n13 octobre - 2 novembre 2026 (export Rithmic), limite 400 $ (prix reels)")
        for nom, k, u in variantes:
            r, a, f, c, cp = journees(O2, H2, L2, C2, ok2 | sel, st2, atr2, k, u, 400.0, 0.0)
            x = r[sel]
            cum = np.cumsum(x)
            print(f"  {nom:32s} total {x.sum():+6.0f} $ ; jours gagnants {(x > 0).sum()}/{len(x)} ; plus bas du cumul {min(0, cum.min()):+.0f} $ ;"
                  f" jours : {' '.join(f'{v:+.0f}' for v in x)}")


if __name__ == "__main__":
    main()
