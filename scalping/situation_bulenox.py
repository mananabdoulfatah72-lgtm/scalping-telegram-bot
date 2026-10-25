#!/usr/bin/env python3
"""Chances de valider le challenge Bulenox 50K depuis la situation de l'utilisateur (descriptif). Memes chemins minute par
minute que challenge_ajouts.py (zone sans filtre, pas de zone les jours de la Fed, limite du jour 1 000 $, plancher a
2 500 $ sous le plus haut de fin de journee, bloque a 50 100 $, objectif 53 000 $ + 50 $), en partant de chaque seance
historique avec le solde, le plus haut et le nombre de seances restantes de l'utilisateur.
Lancer : KB=<branche de recherche> SOLDE=50600 HAUT=51172 SEANCES=14 python3 scalping/situation_bulenox.py"""
import os

import numpy as np
from numba import njit

import challenge_ajouts as CA
import commun as K
import partie_e as E
import partie_g as G
import partie_h as H


@njit(cache=True)
def _depuis(Zc, Zw, Ac, Aw, fed, departs, n, z1, z2, a, solde, haut0):
    S, N = Zc.shape
    res = np.zeros(len(departs), np.int64)
    for k in range(len(departs)):
        d0 = departs[k]
        d1 = min(d0 + n, S)
        bal, haut = solde, haut0
        plancher = 50100.0 if haut >= 52600.0 else haut - 2500.0
        etat = 0
        for s in range(d0, d1):
            z = z2 if s >= d1 - 5 else z1
            if fed[s]:
                z = 0.0
            jour, fini = 0.0, False
            for m in range(N):
                pire = z * Zw[s, m] + a * Aw[s, m]
                clo = z * Zc[s, m] + a * Ac[s, m]
                if bal + pire <= plancher:
                    etat, fini = -1, True
                    break
                if pire <= -1000.0:
                    jour = -1000.0
                    break
                if bal + clo >= 53050.0:
                    etat, fini = 1, True
                    break
                jour = clo
            if fini:
                break
            bal += jour
            haut = max(haut, bal)
            plancher = 50100.0 if haut >= 52600.0 else haut - 2500.0
            if bal <= plancher:
                etat = -1
                break
        res[k] = etat
    return res


def main():
    solde = float(os.getenv("SOLDE", "50600"))
    haut = float(os.getenv("HAUT", "51172"))
    n = int(os.getenv("SEANCES", "14"))
    d = E.jour_nq()
    S = d["c"].shape[0]
    ok = d["complete"] & ~d["ech"]
    Zc, Zw = CA.chemins(d, CA.trades_zone(d, G.calcul(d)[4]))
    Oc, Ow = CA.chemins(d, CA.trades_seances(d, ok, "H1"))
    fed = np.isin(d["jours"], E.fomc())
    dep_tous = np.flatnonzero((d["jours"] >= np.datetime64("2012-01-01")) & (np.arange(S) <= S - n))
    dep_23 = dep_tous[d["jours"][dep_tous] >= np.datetime64("2023-01-01")]
    zero = np.zeros_like(Zc)
    plancher = 50100.0 if haut >= 52600.0 else haut - 2500.0
    L = [f"Situation : solde {solde:,.0f} $, plus haut de fin de journee {haut:,.0f} $, plancher {plancher:,.0f} $ "
         f"(marge {solde - plancher:,.0f} $), objectif 53 000 $ (encore {53000 - solde:,.0f} $), {n} seances restantes.",
         f"Sans aucun avantage, la chance d'atteindre l'objectif avant le plancher vaut au plus marge / (marge + reste) = "
         f"{(solde - plancher) / (solde - plancher + 53050 - solde):.0%} (sans limite de temps).", "",
         f"{'reglage':<44} {'2012-2026 : valide  perdu  expire':<34} {'2023-2026 : valide  perdu  expire'}"]
    configs = [("zone 1 MNQ", 1, 1, 0, None), ("zone 2 puis 4 MNQ", 2, 4, 0, None), ("zone 3 puis 5 MNQ", 3, 5, 0, None),
               ("zone 4 puis 6 MNQ (reglage actuel)", 4, 6, 0, None), ("zone 5 puis 7 MNQ", 5, 7, 0, None),
               ("zone 6 puis 8 MNQ", 6, 8, 0, None), ("zone 8 puis 10 MNQ", 8, 10, 0, None),
               ("zone 4 puis 6 + ORB 5 min 2 MNQ", 4, 6, 2, (Oc, Ow))]
    for nom, z1, z2, a, aj in configs:
        Ac, Aw = aj if aj else (zero, zero)
        t = []
        for dep in (dep_tous, dep_23):
            r = _depuis(Zc, Zw, Ac, Aw, fed, dep, n, float(z1), float(z2), float(a), solde, haut)
            t.append(((r == 1).mean(), (r == -1).mean(), (r == 0).mean()))
        L.append(f"{nom:<44} {t[0][0]:7.1%} {t[0][1]:7.1%} {t[0][2]:7.1%}    {t[1][0]:7.1%} {t[1][1]:7.1%} {t[1][2]:7.1%}")
    out = K.ICI / "resultats" / "i" / "situation_bulenox.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
