#!/usr/bin/env python3
"""Partie L (README.md) : entree a la cassure (comme J0), sortie aux seuls controles quand le prix repasse le niveau casse
a l'entree (L1), le VWAP (L2) ou max(ouverture, veille) (L3) ; a = un trade par seance, b = reentree a une cassure
suivante. References : le bot d'avant (controles) et le bot installe (J0). Ecrit resultats/j/partie_l.txt.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/partie_l.py"""
import os

import numpy as np
from numba import njit

import challenge_ajouts as CA
import donnees as D
import partie_e as E
import partie_g as G
import partie_j as J
import situation_bulenox as SB

VARIANTES = {"L1a niveau casse, 1 trade/jour": (1, True), "L1b niveau casse, reentree": (1, False),
             "L2a VWAP, 1 trade/jour": (2, True), "L2b VWAP, reentree": (2, False),
             "L3a retour fort, 1 trade/jour": (3, True), "L3b retour fort, reentree": (3, False)}


@njit(cache=True)
def _zone_l(O, H, L, C, sigma, vwap, href, bref, jouable, sortie, un_par_jour):
    S, N = C.shape
    tr = np.zeros((S * 60, 8))
    nt = 0
    for s in range(S):
        if not jouable[s]:
            continue
        pos, me, px, niveau, fait = 0, -1, 0.0, np.nan, False
        ub, lb = np.nan, np.nan
        for m in range(30, N):
            p = C[s, m]
            if m == N - 1:
                if pos != 0:
                    J._ecrit(tr, nt, s, me, pos, px, m, p, 0, 0.0)
                    nt += 1
                break
            entre, sorti = 0, False
            libre = not (un_par_jour and fait)
            if m % 30 == 0:
                sg = sigma[s, m]
                ub, lb = href[s] * (1 + sg), bref[s] * (1 - sg)
                if pos != 0:
                    if sortie == 1:
                        lim = niveau
                    elif sortie == 2:
                        lim = vwap[s, m]
                    else:
                        lim = href[s] if pos > 0 else bref[s]
                    if (pos > 0 and p <= lim) or (pos < 0 and p >= lim):
                        J._ecrit(tr, nt, s, me, pos, px, m, p, 0, 0.0)
                        nt += 1
                        pos, sorti = 0, True
                if pos == 0 and not sorti and libre and m <= 360:
                    entre = 1 if p > ub else (-1 if p < lb else 0)
            elif pos == 0 and libre and m < 360:
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
    dep = np.flatnonzero(d["jours"] >= np.datetime64("2012-01-01"))
    situations = [("49 500 $, marge 1 000 $", 49500.0, 51000.0, 13), ("49 500 $, plus haut 51 172 $", 49500.0, 51172.0, 13),
                  ("49 500 $, plus haut 50 600 $", 49500.0, 50600.0, 13), ("challenge neuf, 21 seances", 50000.0, 50000.0, 21)]
    jeux = {"bot d'avant (controles seuls)": J._zone_j(*a, False, 0.0, False, tick, 0),
            "bot installe (J0, cassure)": J._zone_j(*a, True, 0.0, False, tick, 0)}
    for nom, (so, un) in VARIANTES.items():
        jeux[nom] = _zone_l(*a, so, un)
    L = [f"Minutes du NQ : {d['jours'][0]} - {d['jours'][-1]}.", "",
         f"{'variante':<32} {'trades':>6} {'points':>8} {'gagn.':>6} {'duree med':>9} {'t 11-22':>8} {'t 23-26':>8} {'2025':>7} "
         f"{'2026':>7} {'jours -250$':>11}"]
    chall = []
    zero = np.zeros_like(d["c"])
    for nom, t in jeux.items():
        pts = t[:, 2] * (t[:, 5] - t[:, 3]) - float(d["frais"]) / float(d["pt"])
        Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in t])
        g = Zc[:, -1]
        ts = [g[jo & (an >= a0) & (an <= a1)] for a0, a1 in ((2011, 2022), (2023, 2026))]
        ts = [x.mean() / x.std(ddof=1) * np.sqrt(len(x)) for x in ts]
        ta = an[t[:, 0].astype(int)]
        L.append(f"{nom:<32} {len(t):>6} {pts.sum():>+8.0f} {(pts > 0).mean():>6.0%} {np.median(t[:, 4] - t[:, 1]):>7.0f} m "
                 f"{ts[0]:>+8.2f} {ts[1]:>+8.2f} {pts[ta == 2025].sum():>+7.0f} {pts[ta == 2026].sum():>+7.0f} "
                 f"{int((Zw[jo].min(axis=1) <= -250).sum()):>11}")
        lig = f"{nom:<32}"
        for _, solde, haut, n in situations:
            r = SB._depuis(Zc, Zw, zero, zero, fed, dep[dep <= S - n], n, 4.0, 6.0, 0.0, solde, haut, 1000.0)
            lig += f"   {(r == 1).mean():6.1%} {(r == -1).mean():6.1%} {(r == 0).mean():6.1%}"
        chall.append(lig)
    L += ["", "(points bruts pour 1 MNQ, frais de 1,5 point deduits ; duree mediane d'un trade en minutes ; t des gains "
          "quotidiens au prix d'aujourd'hui, jours sans Fed ; jours -250$ = 1 000 $ en 4 MNQ)", "",
          "Challenge, 4 puis 6 MNQ, limite du jour 1 000 $, departs 2012-2026 : valide / perdu / expire",
          f"{'variante':<32}" + "".join(f"   {s[0]:<20}" for s in situations)] + chall
    (J.SORTIE / "partie_l.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
