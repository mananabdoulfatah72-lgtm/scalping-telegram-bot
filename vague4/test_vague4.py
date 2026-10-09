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
                assert tuple(x[:4]) == tuple(y[:4]) and abs(x[4] - y[4]) < 1e-6 and x[5] == y[5], (nc, r, j[d], x, y)
                n += 1
    print(f"ok : moteur4 = financee.py sur {n} parcours (Topstep et Tradeify, sans RSI(2) et RSI(2) entre deux clotures)")


def un_jour(D, b, d, rsi):
    """Une seance sans limite (perte et limite du jour infinies), RSI(2) voulu la veille. Renvoie le cash de fin."""
    return M4.seance4(d, rsi, 1, 0.0, 0.0, -1e12, 0, 1e12, 1e12, 0.0, *b, 2.0, 5.0)[1]


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
    """3. La nuit de l'ES suit exactement la regle de commun.charger : appliquee au fichier du NQ, nuit() redonne la nuit du
    NQ d'intraday50k a l'identique ; pour l'ES, barres presentes et ouverture de 18 h proche de la cloture d'avant."""
    NO, NH, NL, nn = D4.nuit(D4.R0 / "nuit/donnees/nasdaq100_1h.csv.gz", D["jours"], D["contrat"])
    assert np.array_equal(nn, D["nn"]) and np.allclose(NO, D["NO"], equal_nan=True) and np.allclose(NL, D["NL"], equal_nan=True)
    both = (D["nn"] > 0) & (D["enn"] > 0)
    assert both.mean() > 0.97, both.mean()
    i = np.flatnonzero(both)
    i = i[i > 0]
    r = D["ENO"][i, 0] / D["EC"][i - 1, D["derniere"][i - 1]]
    assert np.nanmedian(np.abs(r - 1)) < 0.003, np.nanmedian(np.abs(r - 1))
    print(f"ok : nuit() redonne la nuit du NQ d'intraday50k ; nuit de l'ES presente pour {both.mean():.1%} des seances")


def test_largeur(D):
    """4. Partie B : la part des grandes valeurs au-dessus de leur ouverture, recalculee a la main un jour donne, et le sens
    du signal ; la decision n'utilise que les prix connus a la minute de decision (couper les donnees apres ne change
    rien)."""
    import sources_b as B
    g = pd.read_csv(D4.ICI / "donnees" / "grandes.csv.gz")
    jour = "2020-03-17"
    x = g[g["jour"] == jour]
    main_ = float((x["c30"] > x["ouverture"]).mean())
    d = int(np.flatnonzero(D["jours"] == pd.Timestamp(jour))[0])
    assert abs(B.largeur(D["jours"], 30)[d] - main_) < 1e-12 and len(x) >= 8
    sens, me = B.signaux(D, "B1 largeur a 10 h")
    attendu = 1 if main_ >= 0.9 else (-1 if main_ <= 0.1 else 0)
    assert sens[d] == (attendu if D["derniere"][d] == 389 else 0) and me == 29
    # pas de futur : les colonnes apres la decision ne servent pas
    g2 = g.copy()
    for k in range(60, 391, 30):
        g2[f"c{k}"] = np.nan if k > 30 else g2[f"c{k}"]
    assert np.array_equal(B.largeur_de(g2, D["jours"], 30), B.largeur(D["jours"], 30), equal_nan=True)
    print(f"ok : largeur du {jour} a 10 h = {main_:.0%} (a la main = moteur), sens {sens[d]:+d} ; pas de futur")


def test_chaine(D, b):
    """5. Un seul compte a la fois (un_compte.py) : chaque compte est rejoue a part, rachete a la premiere seance a plat
    apres sa fin ; la somme des flux de la chaine = la somme des argents nets ; avec un horizon d'un an, le moteur redonne
    les issues de parcours4 sans horizon."""
    import un_compte as U
    j, nj = D["jours"], len(D["jours"])
    e, f_ = U.CP.COMPTES[U.NC][:7], U.F.FINANCES[U.NC]["f"]
    prix, mensuel, act = U.F.FINANCES[U.NC]["prix"]
    part = U.F.FINANCES[U.NC]["part"]
    w0 = int(np.searchsorted(j, pd.Timestamp("2023-01-01")))
    for rsi in (0, 4):
        fl, n = U.chaine(D, b, rsi, w0, nj)
        d, tot, k = w0, 0.0, 0
        while True:
            while d < nj and D["ouvert"][d] != 0:
                d += 1
            if d >= nj:
                break
            fn, fe = D4.facteurs(D, d)
            h = min(U.H2, nj - d)
            ret = np.zeros(h)
            r = M4.parcours4(d, rsi, 2.0 * fn, 5.0 * fe, ret, *b, *e, *f_, h)
            assert abs(ret.sum() - r[4]) < 1e-6 and 1 <= r[6] <= h
            tot += r[4] * part - prix * np.ceil(r[1] / U.MOIS) - (act if r[0] == 1 else 0.0)
            d, k = d + r[6], k + 1
        assert k == n and abs(fl.sum() - tot) < 1e-6, (rsi, k, n, fl.sum(), tot)
        for d in range(w0, w0 + 200, 37):
            fn, fe = D4.facteurs(D, d)
            x = M4.parcours4(d, rsi, 2.0 * fn, 5.0 * fe, np.zeros(0), *b, *e, *f_)
            y = M4.parcours4(d, rsi, 2.0 * fn, 5.0 * fe, np.zeros(0), *b, *e, *f_, M4.UN_AN)
            assert x == y
    print(f"ok : un seul compte a la fois, {n} challenges achetes depuis {j[w0].date()} (zone + A3), flux = argents nets")


if __name__ == "__main__":
    D = D4.charger()
    b = D4.base(D)
    test_nuit_es(D)
    test_a_la_main(D, b)
    test_financee(D, b)
    test_chaine(D, b)
    if (D4.ICI / "donnees" / "grandes.csv.gz").exists():
        test_largeur(D)
