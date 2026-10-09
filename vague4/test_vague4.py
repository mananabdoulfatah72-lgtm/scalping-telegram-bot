#!/usr/bin/env python3
"""Controles de la vague 4 (README.md). Lancer depuis ce dossier : python3 test_vague4.py"""
import sys

import numpy as np
import pandas as pd

import donnees4 as D4
import moteur4 as M4

K = D4.K
sys.path.insert(0, str(D4.R0 / "intraday50k"))
import comptes as CP  # noqa: E402
import financee as F  # noqa: E402


def test_financee(D, b):
    """1. Sans RSI(2) et avec le RSI(2) entre deux clotures sur MNQ : memes issues, retraits et montants que financee.py
    (prix multiplies dans les tableaux pour financee, facteur dans ptN pour le nouveau moteur)."""
    j, nj = D["jours"], len(D["jours"])
    zt = K.P.tableaux_zone(D["Z"], nj, np.ones(len(D["Z"]), bool))
    dd = [d for d in range(260, nj) if D["ouvert"][d] == 0 and j[d] >= pd.Timestamp("2023-01-01")
          and d + M4.UN_AN < nj][::10]
    n = 0
    for nc in ("Topstep", "Tradeify Growth"):
        e, f_ = CP.COMPTES[nc][:7], F.FINANCES[nc]["f"]
        for r in (0, 1):
            for d in dd:
                fn, fe = D4.facteurs(D, d)
                s = slice(d, d + M4.UN_AN + 1)
                a = (D["O"][s] * fn, D["H"][s] * fn, D["L"][s] * fn, D["C"][s] * fn, D["derniere"][s], zt[0][s], zt[1][s],
                     *zt[2:], D["dec"][s], D["voulu"][s], D["NO"][s] * fn, D["NH"][s] * fn, D["NL"][s] * fn, D["nn"][s])
                x = F.parcours(0, r, *a, *e, *f_, K.P.FRAIS_ZONE, K.P.FRAIS_RSI)
                y = M4.parcours4(d, r, 2.0 * fn, 5.0 * fe, np.zeros(0), *b, *e, *f_)
                assert x[:4] == y[:4] and abs(x[4] - y[4]) < 1e-6 and x[5] == y[5], (nc, r, j[d], x, y)
                n += 1
    print(f"ok : moteur4 = financee.py sur {n} parcours (Topstep et Tradeify, sans RSI(2) et RSI(2) entre deux clotures)")


def un_jour(D, b, d, rsi):
    """Une seance sans limite (perte et limite du jour infinies), RSI(2) voulu la veille. Renvoie le cash de fin."""
    return M4.seance4(d, rsi, 1, 0.0, 0.0, -1e12, 0, 1e12, 1e12, 0.0, *b[:13], *b[13:17], *b[17:25], 2.0, 5.0)[1]


def test_a_la_main(D, b):
    """2. Un trade de nuit seulement (A2) et un trade entre deux clotures sur MES (A1), recalcules a la main."""
    j = D["jours"]
    nj = len(j)
    d = next(x for x in range(300, nj) if D["nn"][x] > 3 and D["enn"][x] > 3 and D["dec"][x] >= 0)
    z = un_jour(D, b, d, 0)
    a2 = un_jour(D, b, d, 2) - z
    main2 = (D["O"][d, 0] - D["NO"][d, 0]) * 2.0 - 2 * M4.ORDRE_NQ
    assert abs(a2 - main2) < 1e-9, (a2, main2)
    a1 = un_jour(D, b, d, 3) - z
    sortie = D["EO"][d, D["dec"][d]] if D["voulu"][d] == 0 else D["EC"][d, D["derniere"][d]]
    main1 = (sortie - D["ENO"][d, 0]) * 5.0 - 2 * M4.ORDRE_ES
    assert abs(a1 - main1) < 1e-9, (a1, main1)
    print(f"ok : le {j[d].date()}, RSI(2) de nuit seulement sur MNQ {main2:+.2f} $ et entre deux clotures sur MES"
          f" {main1:+.2f} $ (a la main = moteur)")


def test_nuit_es(D):
    """3. La nuit de l'ES suit la meme regle que celle du NQ : memes seances avec des barres a peu pres, prix proches."""
    both = (D["nn"] > 0) & (D["enn"] > 0)
    assert both.mean() > 0.97, both.mean()
    r = D["ENO"][both, 0] / D["EC"][np.flatnonzero(both) - 1, D["derniere"][np.flatnonzero(both) - 1]]
    assert np.nanmedian(np.abs(r - 1)) < 0.003, np.nanmedian(np.abs(r - 1))
    print(f"ok : nuit de l'ES presente pour {both.mean():.1%} des seances, ouverture de 18 h proche de la cloture d'avant")


if __name__ == "__main__":
    D = D4.charger()
    b = D4.base(D)
    test_nuit_es(D)
    test_a_la_main(D, b)
    test_financee(D, b)
