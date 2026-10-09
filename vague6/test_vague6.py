#!/usr/bin/env python3
"""Controles de la vague 6 (README.md). Lancer depuis ce dossier : python3 test_vague6.py
(Lancer aussi static50k/test_static.py, vague4/test_vague4.py, vague5/test_vague5.py, et verifier que
`python3 vague5.py regles` redonne vague5_regles.txt a l'identique.)"""
import sys

import numpy as np

import vague6 as V6

W, D4, M4, U, MS = V6.W, V6.D4, V6.M4, V6.U, V6.MS
sys.path.insert(0, str(V6.ICI.parent / "static50k"))
import test_static as TS  # noqa: E402

G = MS.FRAIS_ZONE + MS.TICK_NQ                      # frais d'une sortie forcee de zone (1 MNQ)


def parcours_s2l(b, n, regle=3, reserve=0.0):
    tr, ret = np.zeros(n), np.zeros(n)
    r = MS.parcours(0, n, n, 1, 0.0, regle, 1, 2.0, 5.0, 0.0, 0.0, tr, ret, *b, 1, 1, 1e18, reserve, 0)
    return r, tr, ret


def test_s2l():
    """2. S2L sur le marche synthetique de test_static (+300 $ par seance, un trade de zone de la minute 10 a 20)."""
    b = TS.marche_synthetique(40, 151.5)
    # evaluation reussie a la 10e seance (3 000 $, 10 jours a +200 $, meilleur jour 300 <= 25 %)
    r, tr, ret = parcours_s2l(b, 40)
    assert r[MS.ISSUE] == 1 and r[MS.FIN_EVAL] == 10 and r[MS.PRO_PERDU] == 0, r
    # live a partir de la seance 11 : 8e seance live = seance 18 (2 400 $) -> retrait 1 400 $ (garder 1 000 $) ; puis
    # 600 $ toutes les deux seances (1 300 $ < 1 500 $, 1 600 $ -> 600 $)
    attendu = {18: 1400.0} | {k: 600.0 for k in range(20, 41, 2)}
    assert {int(k) + 1: v for k, v in zip(np.flatnonzero(ret), ret[ret > 0])} == attendu, ret
    # reserve de 1 000 $ : 400 $ a la seance 18 (< 500 $), donc 700 $ a la 19e, puis 600 $ toutes les deux seances
    r, tr, ret = parcours_s2l(b, 40, reserve=1000.0)
    attendu = {19: 700.0} | {k: 600.0 for k in range(21, 41, 2)}
    assert {int(k) + 1: v for k, v in zip(np.flatnonzero(ret), ret[ret > 0])} == attendu, ret
    # plancher suivi en direct : seance 3 (veille +600), plus haut a +3 100 $ (minute 15) -> plancher 0 (arrete au
    # depart) ; creux a -200 $ (minute 16) -> evaluation perdue ; sans le plus haut, le meme creux ne fait rien
    O, H, L, C = (x.copy() for x in b[:4])
    H[2, 15] = 1000.0 + 1250.0
    L[2, 16] = 1000.0 - 400.0
    r, tr, _ = parcours_s2l((O, H, L, C) + b[4:], 40)
    assert r[MS.ISSUE] == -1 and r[MS.FIN_EVAL] == 3, r
    H[2, 15] = 1000.0
    r, tr, _ = parcours_s2l((O, H, L, C) + b[4:], 40)
    assert r[MS.ISSUE] == 1 and abs(tr[2] - 900.0) < 1e-9, (r, tr[:4])
    # limite du jour douce : creux a -500 $ (veille +600, limite -400) -> tout ferme a -400 $, le compte continue ;
    # definitive (regle 4) : evaluation perdue
    O, H, L, C = (x.copy() for x in b[:4])
    L[2, 15] = 1000.0 - 550.0
    r, tr, _ = parcours_s2l((O, H, L, C) + b[4:], 40)
    assert r[MS.ISSUE] != -1 and abs(tr[2] - (-400.0 - G)) < 1e-9, (r, tr[:4])
    r, tr, _ = parcours_s2l((O, H, L, C) + b[4:], 40, regle=4)
    assert r[MS.ISSUE] == -1 and r[MS.FIN_EVAL] == 3, r
    print("ok : S2L a la main (evaluation a la 10e seance ; retraits a partir de la 8e seance live, 1 000 $ + reserve"
          " gardes ; plancher suivi en direct arrete au depart ; limite du jour douce et definitive)")


def test_comptes(DA):
    """3. Parametres de FundedNext et LucidFlex = README ; un retrait de FundedNext depasse 2 000 $."""
    e, f_, part, prix = V6.INTRADAY["FundedNext Legacy"]
    assert e == (3000.0, 2000.0, 0, 0.0, 0.0, 0.40, 1) and part == 0.8 and prix == (200.0, False, 0.0)
    assert f_[:7] == (2000.0, 0.0, 0.0, 5, 200.0, 0.0, 250.0) and list(f_[7]) == [6000.0] and f_[8:] == (0.5, 0.0, 0)
    e2, f2, part2, prix2 = V6.INTRADAY["LucidFlex"]
    assert e2 == (3000.0, 2000.0, 0, 100.0, 0.0, 0.50, 1) and part2 == 0.9 and prix2 == (140.0, False, 0.0)
    assert f2[:7] == (2000.0, 100.0, 0.0, 5, 150.0, 0.0, 500.0) and list(f2[7]) == [2000.0] and f2[8:] == (0.5, 0.0, 0)
    bA = D4.base(DA)
    kN, kE = D4.facteurs_jour(DA)
    gros = 0
    for d in range(300, len(DA["jours"]) - 300, 13):
        ret = np.zeros(252)
        M4.parcours4(d, 4, 2.0 * kN, 5.0 * kE, ret, *bA, *e, *f_, 252, 2, 2, V6.SEUIL, 0.0)
        gros += int((ret > 2000.0).any())
        if gros >= 3:
            break
    assert gros >= 3
    print("ok : FundedNext Legacy et LucidFlex = README ; des retraits de FundedNext depassent 2 000 $")


def test_triple(DA, DS):
    """4. Taille 3x sans aucune limite : trois fois le gain de chaque jour (zone + A3 ; Static E4, nuit comprise)."""
    bA = D4.base(DA)
    for d in range(300, len(DA["jours"]), 101):
        a1 = M4.seance4(d, 4, 1, 0.0, 0.0, -1e12, 0, 1e12, 1e12, 0.0, *bA, 2.0, 5.0, 1)[1]
        a3 = M4.seance4(d, 4, 1, 0.0, 0.0, -1e12, 0, 1e12, 1e12, 0.0, *bA, 2.0, 5.0, 3)[1]
        assert abs(a3 - 3 * a1) < 1e-9, (d, a1, a3)
    bS = U.base(DS)
    for d in U.departs(DS)[100::500]:
        t1, t3 = np.zeros(200), np.zeros(200)
        U.achat(DS, bS, d, "E4", perte=1e12, objectif=1e12, h2=200, trace=t1, niveau="jour")
        U.achat(DS, bS, d, "E4", perte=1e12, objectif=1e12, h2=200, trace=t3, niveau="jour", leviers=(3, 1, 1e18, 0.0))
        assert np.allclose(t3, 3 * t1, atol=1e-6) and np.abs(t1).sum() > 0, d
    print("ok : 3x sans limite = trois fois le gain (zone + A3 ; Static E4 au niveau du jour, nuit comprise)")


if __name__ == "__main__":
    test_s2l()
    DA, DS = D4.charger(), W.DN.charger()
    test_comptes(DA)
    test_triple(DA, DS)
