#!/usr/bin/env python3
"""Partie M (README.md) : L1a (entree a la cassure, une par seance, sortie au niveau casse aux controles), avec une
confirmation de l'entree entre deux controles : cloture d'une bougie de 1, 5 ou 15 minutes au-dela du niveau, et
eventuellement un volume d'au moins k fois la moyenne des 30 minutes d'avant. Ecrit resultats/j/partie_m.txt.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/partie_m.py"""
import os

import numpy as np
from numba import njit

import challenge_ajouts as CA
import donnees as D
import partie_e as E
import partie_g as G
import partie_j as J
import situation_bulenox as SB

VARIANTES = {"M1 (= L1a) bougie 1 min": (1, 0.0), "M5 bougie 5 min": (5, 0.0), "M15 bougie 15 min": (15, 0.0),
             "M1V 1 min + volume x2": (1, 2.0), "M5V 5 min + volume x1,5": (5, 1.5)}


@njit(cache=True)
def _zone_m(C, V, sigma, href, bref, jouable, pas, kvol):
    S, N = C.shape
    tr = np.zeros((S * 4, 8))
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
            entre = 0
            if m % 30 == 0:
                sg = sigma[s, m]
                ub, lb = href[s] * (1 + sg), bref[s] * (1 - sg)
                if pos != 0 and ((pos > 0 and p <= niveau) or (pos < 0 and p >= niveau)):
                    J._ecrit(tr, nt, s, me, pos, px, m, p, 0, 0.0)
                    nt += 1
                    pos = 0
                if pos == 0 and not fait and m <= 360:
                    entre = 1 if p > ub else (-1 if p < lb else 0)
            elif pos == 0 and not fait and m < 360 and m % pas == pas - 1:
                entre = 1 if p > ub else (-1 if p < lb else 0)
                if entre != 0 and kvol > 0:
                    a = m - pas + 1
                    vol = V[s, a:m + 1].sum()
                    moy = V[s, a - 30:a].sum() * pas / 30.0
                    if vol < kvol * moy:
                        entre = 0
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
    situations = [("49 500 $, marge 1 000 $", 49500.0, 51000.0, 13), ("challenge neuf, 21 seances", 50000.0, 50000.0, 21)]
    import partie_l as PL
    l1a = PL._zone_l(*a, 1, True)
    jeux = {"bot d'avant (controles seuls)": J._zone_j(*a, False, 0.0, False, tick, 0)}
    for nom, (pas, kv) in VARIANTES.items():
        jeux[nom] = _zone_m(d["c"], d["v"], sigma, href, bref, jouable, pas, kv)
    controle = np.array_equal(jeux["M1 (= L1a) bougie 1 min"], l1a)
    L = [f"Minutes du NQ : {d['jours'][0]} - {d['jours'][-1]}. Controle : M1 = L1a de partie_l : {'oui' if controle else 'NON'}.",
         "", f"{'variante':<32} {'trades':>6} {'a la cassure':>12} {'points':>8} {'gagn.':>6} {'t 11-22':>8} {'t 23-26':>8} "
         f"{'2025':>7} {'2026':>7} {'jours -250$':>11}"]
    chall = []
    zero = np.zeros_like(d["c"])
    for nom, t in jeux.items():
        pts = t[:, 2] * (t[:, 5] - t[:, 3]) - float(d["frais"]) / float(d["pt"])
        Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in t])
        g = Zc[:, -1]
        ts = [g[jo & (an >= a0) & (an <= a1)] for a0, a1 in ((2011, 2022), (2023, 2026))]
        ts = [x.mean() / x.std(ddof=1) * np.sqrt(len(x)) for x in ts]
        ta = an[t[:, 0].astype(int)]
        L.append(f"{nom:<32} {len(t):>6} {int((t[:, 1] % 30 != 0).sum()):>12} {pts.sum():>+8.0f} {(pts > 0).mean():>6.0%} "
                 f"{ts[0]:>+8.2f} {ts[1]:>+8.2f} {pts[ta == 2025].sum():>+7.0f} {pts[ta == 2026].sum():>+7.0f} "
                 f"{int((Zw[jo].min(axis=1) <= -250).sum()):>11}")
        lig = f"{nom:<32}"
        for _, solde, haut, n in situations:
            r = SB._depuis(Zc, Zw, zero, zero, fed, dep[dep <= S - n], n, 4.0, 6.0, 0.0, solde, haut, 1000.0)
            lig += f"   {(r == 1).mean():6.1%} {(r == -1).mean():6.1%} {(r == 0).mean():6.1%}"
        chall.append(lig)
    L += ["", "(points bruts pour 1 MNQ, frais de 1,5 point deduits ; « a la cassure » = entrees entre deux controles ; t des "
          "gains quotidiens au prix d'aujourd'hui, jours sans Fed ; jours -250$ = 1 000 $ en 4 MNQ)", "",
          "Challenge, 4 puis 6 MNQ, limite du jour 1 000 $, departs 2012-2026 : valide / perdu / expire",
          f"{'variante':<32}" + "".join(f"   {s[0]:<20}" for s in situations)] + chall
    (J.SORTIE / "partie_m.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
