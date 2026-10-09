#!/usr/bin/env python3
"""Controles de la vague 5 (README.md). Lancer depuis ce dossier : python3 test_vague5.py
(test_static.py et test_vague4.py sont a lancer aussi : sans levier, les moteurs redonnent leurs resultats d'avant.)"""
import numpy as np
import pandas as pd

import socle
import vague5 as W

D4, M4, U, MS, CP, F = W.D4, W.M4, W.U, W.MS, W.CP, W.F


def test_sans_levier(DA, DS):
    """1. Sans levier, une chaine de vague5 = la meme chaine de socle (etape 1), au flux pres, pour chaque compte."""
    j = DA["jours"]
    w0 = int(np.searchsorted(j, pd.Timestamp("2023-01-01")))
    bA, bS = D4.base(DA), U.base(DS)
    paires = [(W.REFERENCES["Topstep"], bA, socle.lien_intraday(DA, bA, "Topstep", 4), False),
              (W.REFERENCES["Static"], bS, socle.lien_static(DS, bS, "E0", 500.0, 0, (30.0, 30.0)), True),
              (W.REFERENCES["S2F"], bS, socle.lien_static(DS, bS, "E0", 500.0, 2, (570.0, 342.0)), True)]
    for c, b, ancien, statique in paires:
        f1, _, n1 = W.chaine(DA, W.lien(c, b), w0, len(j))
        f2, n2 = socle.chaine(DA, ancien, w0, len(j), statique)
        assert n1 == n2 and np.allclose(f1, f2), (W.nom(c), n1, n2, f1.sum(), f2.sum())
    print(f"ok : sans levier, vague5 = socle sur les trois comptes ({n1} achats S2F depuis {j[w0].date()})")


def test_double(DA, DS):
    """2. Taille 2x sans aucune limite : exactement deux fois le gain de chaque jour (zone, RSI(2) de nuit sur MES, frais)."""
    bA = D4.base(DA)
    n = 0
    for d in range(300, len(DA["jours"]), 97):
        z1 = M4.seance4(d, 0, 1, 0.0, 0.0, -1e12, 0, 1e12, 1e12, 0.0, *bA, 2.0, 5.0, 1)[1]
        z2 = M4.seance4(d, 0, 1, 0.0, 0.0, -1e12, 0, 1e12, 1e12, 0.0, *bA, 2.0, 5.0, 2)[1]
        a1 = M4.seance4(d, 4, 1, 0.0, 0.0, -1e12, 0, 1e12, 1e12, 0.0, *bA, 2.0, 5.0, 1)[1]
        a2 = M4.seance4(d, 4, 1, 0.0, 0.0, -1e12, 0, 1e12, 1e12, 0.0, *bA, 2.0, 5.0, 2)[1]
        assert abs(z2 - 2 * z1) < 1e-9 and abs(a2 - 2 * a1) < 1e-9, (d, z1, z2, a1, a2)
        n += int(a1 != z1)
    bS = U.base(DS)
    for v in ("E0", "E4"):
        for d in U.departs(DS)[100::400]:
            t1, t2 = np.zeros(300), np.zeros(300)
            U.achat(DS, bS, d, v, perte=1e12, objectif=1e12, h2=300, trace=t1)
            U.achat(DS, bS, d, v, perte=1e12, objectif=1e12, h2=300, trace=t2, leviers=(2, 1, 1e18, 0.0))
            assert np.allclose(t2, 2 * t1, atol=1e-6) and np.abs(t1).sum() > 0, (v, d)
    assert n > 0
    print(f"ok : 2x sans limite = deux fois le gain (Topstep : zone seule et zone + A3, {n} seances avec un trade de A3 ;"
          f" Static : E0 et E4, 300 seances par depart, nuit comprise)")


def test_reserve(DA, DS):
    """3. Reserve de 1 000 $ : chaque retrait est de 1 000 $ de moins que le plus grand retrait permis par les regles."""
    bS = U.base(DS)
    nS = nP = 0
    for d in U.departs(DS)[::7]:
        for s2f in (False, True):
            tr, ret = np.zeros(504), np.zeros(504)
            r = U.achat(DS, bS, d, "E0", plafond=500.0, h2=504, trace=tr, retraits=ret, s2f=s2f,
                        leviers=(1, 1, 1e18, 1000.0))
            for s in np.flatnonzero(ret):
                eod, x = tr[s], ret[s]
                if s2f:
                    assert abs(x - (min(MS.MAX_RET, eod - 1000.0) - 1000.0)) < 1e-6 and x >= 500.0, (d, s, eod, x)
                    nS += 1
                else:
                    assert abs(x - (min(MS.MAX_RET, np.floor((eod - 2000.0) / 500.0) * 500.0) - 1000.0)) < 1e-6, (d, s)
                    assert x >= 500.0 and eod - x >= 3000.0 - 1e-6
                    nP += 1
            if r[MS.ISSUE] == 1 and not s2f:
                assert int(r[MS.FIN_EVAL]) <= 504
    e, f_ = CP.COMPTES["Topstep"][:7], F.FINANCES["Topstep"]["f"]
    bA = D4.base(DA)
    nT = 0
    for d in range(300, len(DA["jours"]) - 300, 23):
        fn, fe = D4.facteurs(DA, d)
        r0, r1 = np.zeros(252), np.zeros(252)
        M4.parcours4(d, 4, 2.0 * fn, 5.0 * fe, r0, *bA, *e, *f_, 252, 1, 1, 1e18, 0.0)
        M4.parcours4(d, 4, 2.0 * fn, 5.0 * fe, r1, *bA, *e, *f_, 252, 1, 1, 1e18, 1000.0)
        i0, i1 = np.flatnonzero(r0), np.flatnonzero(r1)
        if len(i0) == 0:
            continue
        attendu = r0[i0[0]] - 1000.0              # meme seance, 1 000 $ de moins (si au moins le minimum de 125 $)
        if attendu >= 125.0:
            assert len(i1) and i1[0] == i0[0] and abs(r1[i1[0]] - attendu) < 1e-6, (d, x0, r1[i1[0]] if len(i1) else 0)
            nT += 1
    print(f"ok : reserve de 1 000 $ (Pro Static : {nP} retraits, S2F : {nS}, Topstep : {nT} premiers retraits)")


def test_challenge_intact(DA, DS):
    """4. La taille du compte finance ne change rien au challenge : meme issue, meme duree."""
    e, f_ = CP.COMPTES["Topstep"][:7], F.FINANCES["Topstep"]["f"]
    bA, bS = D4.base(DA), U.base(DS)
    n = 0
    for d in range(300, len(DA["jours"]) - 300, 31):
        fn, fe = D4.facteurs(DA, d)
        x = M4.parcours4(d, 4, 2.0 * fn, 5.0 * fe, np.zeros(0), *bA, *e, *f_)
        y = M4.parcours4(d, 4, 2.0 * fn, 5.0 * fe, np.zeros(0), *bA, *e, *f_, 252, 1, 2, 0.0, 1000.0)
        assert x[:2] == y[:2]
        n += 1
    for d in U.departs(DS)[::9]:
        x = U.achat(DS, bS, d, "E0", plafond=500.0)
        y = U.achat(DS, bS, d, "E0", plafond=500.0, leviers=(1, 2, 0.0, 1000.0))
        assert x[MS.ISSUE] == y[MS.ISSUE] and x[MS.FIN_EVAL] == y[MS.FIN_EVAL]
        n += 1
    print(f"ok : la taille du compte finance ne change pas le challenge ({n} achats, Topstep et Static)")


def test_double_finance(DS):
    """5. Compte finance (S2F, finance des le premier jour, plafond du jour de 500 $) : le premier jour, le coussin vaut
    2 500 $ ; avec un seuil de 2 500 $, il est joue en 2x avec un plafond de 1 000 $ (deux fois le gain du jour quand la
    limite du jour n'est pas touchee) ; avec un seuil de 2 501 $, il reste en 1x."""
    bS = U.base(DS)
    n = egal = 0
    for d in U.departs(DS)[::3]:
        t = {}
        for seuil in (2500.0, 2501.0, 1e18):
            t[seuil] = np.zeros(1)
            U.achat(DS, bS, d, "E0", plafond=500.0, h2=1, trace=t[seuil], s2f=True, leviers=(1, 2, seuil, 0.0))
        assert t[2501.0][0] == t[1e18][0]
        if t[1e18][0] != 0.0:
            n += 1
            if abs(t[2500.0][0] - 2 * t[1e18][0]) < 1e-6:
                egal += 1
            else:                                    # 2x : la limite du jour de 1 250 $ a pu etre touchee
                assert -2500.0 < t[2500.0][0] <= -1250.0 + 1e-6, (d, t)        # arrete a la limite (ou dessous)
    assert egal >= 0.9 * n, (egal, n)
    print(f"ok : compte finance en 2x au-dessus du seuil ({egal} premiers jours sur {n} exactement doubles, les autres"
          f" arretes par la limite du jour)")


if __name__ == "__main__":
    DA, DS = W.D4.charger(), W.DN.charger()
    W.G["D4"], W.G["DS"] = DA, DS
    assert (DA["ouvert"] == DS["ouvert"]).all()
    test_double(DA, DS)
    test_reserve(DA, DS)
    test_challenge_intact(DA, DS)
    test_double_finance(DS)
    test_sans_levier(DA, DS)
