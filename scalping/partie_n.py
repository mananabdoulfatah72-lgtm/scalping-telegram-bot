#!/usr/bin/env python3
"""Partie N (README.md) : L1a (entree a la cassure, une par seance) avec sortie immediate au retour de l'autre cote du niveau
casse : N1 a la cloture de la minute, N2 vrai stop sur le niveau ; sinon 16 h. References : L1a et le bot d'avant.
Ecrit resultats/j/partie_n.txt.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/partie_n.py"""
import os

import numpy as np
import pandas as pd
from numba import njit

import challenge_ajouts as CA
import donnees as D
import partie_e as E
import partie_g as G
import partie_j as J
import partie_m as PM
import situation_bulenox as SB


@njit(cache=True)
def _zone_n(O, H, L, C, sigma, href, bref, jouable, mode, tick):
    S, N = C.shape
    tr = np.zeros((S * 2, 8))
    nt = 0
    for s in range(S):
        if not jouable[s]:
            continue
        pos, me, px, niveau, fait = 0, -1, 0.0, np.nan, False
        ub, lb = np.nan, np.nan
        for m in range(30, N):
            p = C[s, m]
            if pos != 0 and m > me:
                if mode == 2 and ((pos > 0 and L[s, m] <= niveau) or (pos < 0 and H[s, m] >= niveau)):
                    x = (min(O[s, m], niveau) - tick) if pos > 0 else (max(O[s, m], niveau) + tick)
                    J._ecrit(tr, nt, s, me, pos, px, m, x, 2, 0.0)
                    nt += 1
                    pos = 0
                elif mode == 1 and pos * (p - niveau) <= 0:
                    J._ecrit(tr, nt, s, me, pos, px, m, p, 2, 0.0)
                    nt += 1
                    pos = 0
            if m == N - 1:
                if pos != 0:
                    J._ecrit(tr, nt, s, me, pos, px, m, p, 0, 0.0)
                    nt += 1
                break
            entre = 0
            if m % 30 == 0:
                sg = sigma[s, m]
                ub, lb = href[s] * (1 + sg), bref[s] * (1 - sg)
                if pos == 0 and not fait and m <= 360:
                    entre = 1 if p > ub else (-1 if p < lb else 0)
            elif pos == 0 and not fait and m < 360:
                entre = 1 if p > ub else (-1 if p < lb else 0)
            if entre != 0:
                pos, me, px, fait = entre, m, p, True
                niveau = ub if entre > 0 else lb
    return tr[:nt]


def main():
    d = D.minutes("NQ", chemin=os.environ["MINUTES"], debut="2011-01-01")
    S = d["c"].shape[0]
    sigma, vwap, href, bref, jouable = G.zone_tableaux(d)
    a = (d["o"], d["h"], d["l"], d["c"], sigma, vwap, href, bref, jouable)
    tick = float(d["tick"])
    fed = np.isin(d["jours"], E.fomc())
    an = d["jours"].astype("datetime64[Y]").astype(int) + 1970
    jo = jouable & ~fed
    jours = pd.to_datetime(d["jours"])
    dep = np.flatnonzero(d["jours"] >= np.datetime64("2012-01-01"))
    situations = [("49 500 $, marge 1 000 $", 49500.0, 51000.0, 13), ("challenge neuf, 21 seances", 50000.0, 50000.0, 21)]
    jeux = {"bot d'avant (controles seuls)": J._zone_j(*a, False, 0.0, False, tick, 0),
            "L1a laisser courir (installe)": PM._zone_m(d["c"], d["v"], sigma, href, bref, jouable, 1, 0.0),
            "N1 sortie a la cloture de minute": _zone_n(d["o"], d["h"], d["l"], d["c"], sigma, href, bref, jouable, 1, tick),
            "N2 vrai stop sur le niveau": _zone_n(d["o"], d["h"], d["l"], d["c"], sigma, href, bref, jouable, 2, tick)}
    ech = float(d["pref"]) / d["o"][:, 0]
    L = [f"Minutes du NQ : {d['jours'][0]} - {d['jours'][-1]}.", "",
         f"{'variante':<32} {'trades':>6} {'points':>8} {'gagn.':>6} {'gain moy':>8} {'perte moy':>9} {'pire':>7} "
         f"{'t 11-22':>8} {'t 23-26':>8} {'2025':>7} {'2026':>7} {'jours -250$':>11}"]
    chall, mois = [], []
    zero = np.zeros_like(d["c"])
    for nom, t in jeux.items():
        pts = t[:, 2] * (t[:, 5] - t[:, 3]) - float(d["frais"]) / float(d["pt"])
        pa = pts * ech[t[:, 0].astype(int)]                       # points au prix d'aujourd'hui
        Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in t])
        g = Zc[:, -1]
        ts = [g[jo & (an >= a0) & (an <= a1)] for a0, a1 in ((2011, 2022), (2023, 2026))]
        ts = [x.mean() / x.std(ddof=1) * np.sqrt(len(x)) for x in ts]
        ta = an[t[:, 0].astype(int)]
        r23 = ta >= 2023
        L.append(f"{nom:<32} {len(t):>6} {pts.sum():>+8.0f} {(pts > 0).mean():>6.0%} {pa[r23 & (pa > 0)].mean():>+8.1f} "
                 f"{pa[r23 & (pa < 0)].mean():>+9.1f} {pa[r23].min():>+7.0f} {ts[0]:>+8.2f} {ts[1]:>+8.2f} "
                 f"{pts[ta == 2025].sum():>+7.0f} {pts[ta == 2026].sum():>+7.0f} {int((Zw[jo].min(axis=1) <= -250).sum()):>11}")
        lig = f"{nom:<32}"
        for _, solde, haut, n in situations:
            r = SB._depuis(Zc, Zw, zero, zero, fed, dep[dep <= S - n], n, 4.0, 6.0, 0.0, solde, haut, 1000.0)
            lig += f"   {(r == 1).mean():6.1%} {(r == -1).mean():6.1%} {(r == 0).mean():6.1%}"
        chall.append(lig)
        j4 = np.where(jo, np.where((4 * Zw <= -1000).any(axis=1), -1000.0, 4 * Zc[:, -1]), 0.0)
        x = pd.Series(j4, index=jours)
        x = x[x.index >= "2026-01-01"]
        m = x.groupby(x.index.to_period("M")).sum()
        mois.append(f"{nom:<32} " + " ".join(f"{str(p)[5:]}:{v:>+7,.0f}" for p, v in m.items()) + f"   total {x.sum():+,.0f} $")
    L += ["", "(points bruts pour 1 MNQ, frais deduits ; gain moy, perte moy et pire trade : 2023-2026, points au prix "
          "d'aujourd'hui ; t des gains quotidiens, jours sans Fed ; jours -250$ = 1 000 $ en 4 MNQ)", "",
          "Challenge, 4 puis 6 MNQ, limite du jour 1 000 $, departs 2012-2026 : valide / perdu / expire",
          f"{'variante':<32}" + "".join(f"   {s[0]:<20}" for s in situations)] + chall
    L += ["", "2026 mois par mois, 4 MNQ, prix d'aujourd'hui, limite du jour 1 000 $, sans les jours de la Fed :"] + mois
    (J.SORTIE / "partie_n.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
