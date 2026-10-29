#!/usr/bin/env python3
"""Partie K (README.md) : entree des la cassure des niveaux du dernier controle, coupure des que le prix revient dans la
zone (K1 : cloture de minute ; K2 : vrai stop sur la limite), sinon sortie normale du bot aux controles et a 16 h. Apres
une coupure : a, nouvelle entree a la cassure suivante ; b, rien avant le controle suivant. Memes mesures que partie_j.py.
Ecrit resultats/j/partie_k.txt.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/partie_k.py"""
import os

import numpy as np
from numba import njit

import challenge_ajouts as CA
import donnees as D
import partie_e as E
import partie_g as G
import partie_j as J
import situation_bulenox as SB

VARIANTES = {"K1a coupure a la cloture, reentree": (1, True), "K1b coupure a la cloture, attente": (1, False),
             "K2a vrai stop sur la limite, reentree": (2, True), "K2b vrai stop sur la limite, attente": (2, False)}


@njit(cache=True)
def _zone_k(O, H, L, C, sigma, vwap, href, bref, jouable, coupure, reentree, tick):
    """Memes colonnes que partie_j._zone_j (motif 2 = coupure)."""
    S, N = C.shape
    tr = np.zeros((S * 200, 8))
    nt = 0
    for s in range(S):
        if not jouable[s]:
            continue
        pos, me, px, attente = 0, -1, 0.0, False
        ub, lb = np.nan, np.nan
        for m in range(30, N):
            p = C[s, m]
            coupe = False
            if coupure == 2 and pos != 0 and m > me:
                lim = ub if pos > 0 else lb
                if (pos > 0 and L[s, m] <= lim) or (pos < 0 and H[s, m] >= lim):
                    x = (min(O[s, m], lim) - tick) if pos > 0 else (max(O[s, m], lim) + tick)
                    J._ecrit(tr, nt, s, me, pos, px, m, x, 2, 0.0)
                    nt += 1
                    pos, coupe, attente = 0, True, not reentree
            if m == N - 1:
                if pos != 0:
                    J._ecrit(tr, nt, s, me, pos, px, m, p, 0, 0.0)
                    nt += 1
                break
            entre = 0
            if m % 30 == 0:
                sg = sigma[s, m]
                ub, lb = href[s] * (1 + sg), bref[s] * (1 - sg)
                if pos != 0 and ((pos > 0 and p <= max(ub, vwap[s, m])) or (pos < 0 and p >= min(lb, vwap[s, m]))):
                    J._ecrit(tr, nt, s, me, pos, px, m, p, 0, 0.0)
                    nt += 1
                    pos = 0
                attente = False
                if pos == 0 and m <= 360 and not coupe:
                    entre = 1 if p > ub else (-1 if p < lb else 0)
            else:
                if coupure == 1 and pos != 0 and m > me and ((pos > 0 and p <= ub) or (pos < 0 and p >= lb)):
                    J._ecrit(tr, nt, s, me, pos, px, m, p, 2, 0.0)
                    nt += 1
                    pos, coupe, attente = 0, True, not reentree
                elif pos == 0 and not attente and not coupe and m < 360:
                    entre = 1 if p > ub else (-1 if p < lb else 0)
            if entre != 0:
                pos, me, px = entre, m, p
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
    situations = [("49 500 $, plus haut 51 172 $", 49500.0, 51172.0, 13), ("49 500 $, plus haut 50 600 $", 49500.0, 50600.0, 13),
                  ("challenge neuf, 21 seances", 50000.0, 50000.0, 21)]
    jeux = {"bot (controles seuls)": J._zone_j(*a, False, 0.0, False, tick, 0)}
    for nom, (cp, re) in VARIANTES.items():
        jeux[nom] = _zone_k(*a, cp, re, tick)
    L = [f"Minutes du NQ : {d['jours'][0]} - {d['jours'][-1]}.", "",
         f"{'variante':<38} {'trades':>6} {'points':>8} {'coupes':>7} {'gagn.':>6} {'t 11-22':>8} {'t 23-26':>8} {'2025':>7} "
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
        L.append(f"{nom:<38} {len(t):>6} {pts.sum():>+8.0f} {(t[:, 6] == 2).mean():>7.0%} {(pts > 0).mean():>6.0%} "
                 f"{ts[0]:>+8.2f} {ts[1]:>+8.2f} {pts[ta == 2025].sum():>+7.0f} {pts[ta == 2026].sum():>+7.0f} "
                 f"{int((Zw[jo].min(axis=1) <= -250).sum()):>11}")
        lig = f"{nom:<38}"
        for _, solde, haut, n in situations:
            r = SB._depuis(Zc, Zw, zero, zero, fed, dep[dep <= S - n], n, 4.0, 6.0, 0.0, solde, haut, 1000.0)
            lig += f"   {(r == 1).mean():6.1%} {(r == -1).mean():6.1%} {(r == 0).mean():6.1%}"
        chall.append(lig)
    L += ["", "(points bruts pour 1 MNQ, frais de 1,5 point deduits ; coupes = trades sortis par la coupure ; t des gains "
          "quotidiens au prix d'aujourd'hui, jours sans Fed ; jours -250$ = 1 000 $ en 4 MNQ)", "",
          "Challenge, 4 puis 6 MNQ, limite du jour 1 000 $, departs 2012-2026 : valide / perdu / expire",
          f"{'variante':<38}" + "".join(f"   {s[0]:<20}" for s in situations)] + chall
    (J.SORTIE / "partie_k.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
