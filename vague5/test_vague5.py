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


def test_niveau_jour(DA, DS):
    """6-9. Methode corrigee : chaque trade au niveau d'aujourd'hui de son jour d'entree."""
    kN, kE = U.facteurs_jour(DS)
    kN, kE = 2.0 * kN, 5.0 * kE
    bS = U.base(DS)
    # 6. premier jour d'un achat : mode jour = mode achat (meme facteur ce jour-la)
    n6 = 0
    for d in U.departs(DS)[::40]:
        for v in ("E0", "E4"):
            t1, t2 = np.zeros(1), np.zeros(1)
            U.achat(DS, bS, d, v, plafond=500.0, h2=1, trace=t1, leviers=(2, 1, 4000.0, 0.0))
            U.achat(DS, bS, d, v, plafond=500.0, h2=1, trace=t2, leviers=(2, 1, 4000.0, 0.0), niveau="jour")
            assert abs(t1[0] - t2[0]) < 1e-6, (d, v, t1, t2)
            n6 += 1
    # 7. une position du RSI(2) garde le facteur de son entree
    b0 = U.base(DS, np.zeros(len(DS["Z"]), bool))
    v, n7 = DS["voulu"], 0
    for e in range(400, len(DS["jours"]) - 30):
        if not (v[e] == 1 and v[e - 1] == 0 and v[e - 2] == 0 and v[e - 3] == 0 and DS["dec"][e] >= 0):
            continue
        x = next((k for k in range(e + 1, e + 25) if v[k] == 0), None)
        if x is None or DS["roule_es"][e:x + 1].any() or DS["ouvert"][e - 2] != 0:
            continue
        s0, h = e - 2, x - e + 3
        def trace(aE):
            t = np.zeros(h)
            MS.parcours(s0, h, h, 4, 0.0, 0, 1, kN, aE, 1e12, 1e12, t, np.zeros(0), *b0)
            return t
        t1 = trace(kE)
        k2 = kE.copy()
        k2[e + 1:x + 1] *= 1.5
        assert np.array_equal(trace(k2), t1), e
        k3 = kE.copy()
        k3[e] *= 1.5
        assert not np.allclose(trace(k3)[2:], t1[2:])
        n7 += 1
        if n7 >= 20:
            break
    # 8. un trade de zone prend le facteur de son jour
    b1 = U.base(DS)
    n8 = 0
    for q in range(500, len(DS["jours"]) - 10, 211):
        s0 = q - 3
        def trace(aN):
            t = np.zeros(6)
            MS.parcours(s0, 6, 6, 1, 0.0, 0, 1, aN, kE, 1e12, 1e12, t, np.zeros(0), *b1)
            return t
        t1 = trace(kN)
        k2 = kN.copy()
        k2[q] *= 1.5
        t2 = trace(k2)
        i = q - s0                                   # indice de la seance q dans la trace
        assert np.array_equal(t1[:i], t2[:i]) and np.allclose(np.diff(t1)[i:], np.diff(t2)[i:])
        if t1[i] != t2[i]:
            n8 += 1
    assert n8 > 0
    # 9. pas de regard vers le futur : changer les facteurs apres la fin d'un compte ne change rien
    e_, f_ = CP.COMPTES["Topstep"][:7], F.FINANCES["Topstep"]["f"]
    bA = D4.base(DA)
    aN, aE = D4.facteurs_jour(DA)
    n9 = 0
    for d in range(300, len(DA["jours"]) - 400, 97):
        r = M4.parcours4(d, 4, 2.0 * aN, 5.0 * aE, np.zeros(0), *bA, *e_, *f_, 300, 2, 2, 4000.0, 0.0)
        bN = 2.0 * aN.copy()
        bN[d + r[6]:] *= 3.0
        assert M4.parcours4(d, 4, bN, 5.0 * aE, np.zeros(0), *bA, *e_, *f_, 300, 2, 2, 4000.0, 0.0) == r
        y = U.achat(DS, bS, d, "E4", plafond=500.0, h1=300, h2=300, leviers=(2, 1, 4000.0, 0.0), niveau="jour")
        fin = int(y[MS.FIN_EVAL]) if y[MS.ISSUE] == -1 else (int(y[MS.FIN_PRO]) if y[MS.PRO_PERDU] == 1 else 300)
        cN = kN.copy()
        cN[d + fin:] *= 3.0
        z = MS.parcours(d, 300, 300, 4, 500.0, 0, 1, cN, kE, MS.PERTE, MS.OBJECTIF, np.zeros(0), np.zeros(0), *bS,
                        2, 1, 4000.0, 0.0)
        assert np.array_equal(y, z), d
        n9 += 1
    print(f"ok : niveau du jour : premier jour = mode achat ({n6} achats) ; le RSI(2) garde le facteur de son entree"
          f" ({n7} trades) ; la zone prend celui de son jour ({n8} jours) ; rien apres la fin d'un compte ({n9} x 2)")


def test_jour_strict(DS):
    """7 bis. Le RSI(2) garde le facteur de son entree, sur MNQ (E0) et MES (E4), avec un plancher bas (300 $ sous le
    depart) souvent touche, la nuit comprise : changer les facteurs des jours suivants ne change rien jusqu'a la sortie.
    (Evaluation : pas de plafond du jour, donc pas de seconde entree du meme signal.)"""
    kN, kE = U.facteurs_jour(DS)
    kN, kE = 2.0 * kN, 5.0 * kE
    b0 = U.base(DS, np.zeros(len(DS["Z"]), bool))
    v, n, touches = DS["voulu"], 0, 0
    for e in range(400, len(DS["jours"]) - 30):
        if not (v[e] == 1 and v[e - 1] == 0 and v[e - 2] == 0 and v[e - 3] == 0 and DS["dec"][e] >= 0):
            continue
        x = next((k for k in range(e + 1, e + 25) if v[k] == 0), None)
        if x is None or DS["roule_es"][e:x + 1].any() or DS["ouvert"][e - 2] != 0:
            continue
        s0, h = e - 2, x - e + 3
        for var in (0, 4):
            def run(aN, aE):
                t = np.zeros(h)
                r = MS.parcours(s0, h, h, var, 0.0, 0, 1, aN, aE, 300.0, 1e12, t, np.zeros(0), *b0)
                return t, r
            t1, r1 = run(kN, kE)
            k2N, k2E = kN.copy(), kE.copy()
            k2N[e + 1:x + 1] *= 1.7
            k2E[e + 1:x + 1] *= 0.6
            t2, r2 = run(k2N, k2E)
            assert np.array_equal(t1, t2) and np.array_equal(r1, r2), (e, var)
            touches += int(r1[MS.ISSUE] == -1)
        n += 1
        if n >= 40:
            break
    assert touches > 0
    print(f"ok : le RSI(2) garde le facteur de son entree sur MNQ et MES ({n} trades, {touches} fois le plancher"
          f" touche en route)")


def test_activite(DS):
    """10. Regle d'activite appliquee : le compte est coupe a la 21e seance de suite sans un jour a +200 $ (S2F, finance
    des le premier jour), sauf s'il est perdu avant par le plancher."""
    bS = U.base(DS)
    n = 0
    for d in U.departs(DS)[::17]:
        tr, ret = np.zeros(504), np.zeros(504)
        r0 = U.achat(DS, bS, d, "E0", plafond=500.0, h1=504, h2=504, trace=tr, retraits=ret, s2f=True)
        r1 = U.achat(DS, bS, d, "E0", plafond=500.0, h1=504, h2=504, s2f=True, activite=1)
        veille, suite, attendu = 0.0, 0, None
        fin0 = int(r0[MS.FIN_PRO]) if r0[MS.PRO_PERDU] == 1 else 10 ** 9
        for i in range(min(504, fin0, len(DS["jours"]) - d)):
            g = tr[i] - veille
            veille = tr[i] - ret[i]
            suite = 0 if g >= 200.0 else suite + 1
            if suite >= 21:
                attendu = i + 1
                break
        if attendu is None:
            assert r1[MS.PRO_PERDU] == r0[MS.PRO_PERDU] and r1[MS.FIN_PRO] == r0[MS.FIN_PRO], d
        else:
            assert r1[MS.PRO_PERDU] == 1 and int(r1[MS.FIN_PRO]) == attendu, (d, attendu, r1[MS.FIN_PRO])
            n += 1
    assert n > 0
    print(f"ok : regle d'activite : compte coupe a la 21e seance sans jour a +200 $ ({n} comptes)")


if __name__ == "__main__":
    DA, DS = W.D4.charger(), W.DN.charger()
    W.G["D4"], W.G["DS"] = DA, DS
    assert (DA["ouvert"] == DS["ouvert"]).all()
    test_double(DA, DS)
    test_reserve(DA, DS)
    test_challenge_intact(DA, DS)
    test_double_finance(DS)
    test_niveau_jour(DA, DS)
    test_jour_strict(DS)
    test_activite(DS)
    test_sans_levier(DA, DS)
