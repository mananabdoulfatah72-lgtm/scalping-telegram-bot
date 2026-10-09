#!/usr/bin/env python3
"""Controles de la vague 8 (README.md). Lancer depuis ce dossier : python3 test_vague8.py. Le controle 1 (resultats
d'avant redonnes) se fait aussi avec test_vague4.py a test_vague7.py et en relancant vague7/prudent.py (diff)."""
import numpy as np
import pandas as pd

import vague8 as V8

M4, D4 = V8.M4, V8.D4
N = 391


def marche(nj, hausse_nq, hausse_es):
    """NQ plat a 1 000 points, ES plat a 500 ; un trade de zone par seance, achat a la minute 10, vente a la minute 20 ;
    la minute 20 cloture a 1 000 + hausse_nq (NQ) et 500 + hausse_es (ES). Pas de nuit, pas de RSI(2), pas de rebond."""
    O = np.full((nj, N), 1000.0)
    H, L, C = O.copy(), O.copy(), O.copy()
    C[:, 20] = H[:, 20] = 1000.0 + hausse_nq
    EO = np.full((nj, N), 500.0)
    EH, EL, EC = EO.copy(), EO.copy(), EO.copy()
    EC[:, 20] = EH[:, 20] = 500.0 + hausse_es
    der = np.full(nj, N - 1, np.int64)
    z_deb, z_fin = np.arange(nj, dtype=np.int64), np.arange(1, nj + 1, dtype=np.int64)
    z_me, z_ms = np.full(nj, 10, np.int64), np.full(nj, 20, np.int64)
    z_sens, z_garde = np.ones(nj, np.int64), np.ones(nj, np.int64)
    dec, voulu = np.full(nj, -1, np.int64), np.zeros(nj, np.int64)
    nuit = np.full((nj, 3), np.nan)
    zero = np.zeros(nj, np.int64)
    return (O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu, nuit, nuit, nuit, zero,
            EO, EH, EL, EC, nuit, nuit, nuit, zero, zero)


def un_jour(b, zi, qz=1):
    return M4.seance4(0, 0, 0, 0.0, 0.0, -1e12, 0, 1e12, 1e12, 0.0, *b, 2.0, 5.0, qz, zi)[1]


def test_mes_synthetique():
    """2. Un trade de zone sur MES = sens x (sortie - entree de l'ES) x 5 $ - 4,50 $ ; sur MNQ, comme avant."""
    b = marche(3, 100.0, 20.0)
    assert abs(un_jour(b, 1) - (20.0 * 5.0 - 4.5)) < 1e-9, un_jour(b, 1)
    assert abs(un_jour(b, 0) - (100.0 * 2.0 - 3.0)) < 1e-9, un_jour(b, 0)
    assert abs(un_jour(b, 1, 2) - 2 * (20.0 * 5.0 - 4.5)) < 1e-9
    # vente : le pire point de la minute est le plus haut ; un plancher juste sous ce pire point arrete le compte
    b2 = list(marche(3, 0.0, 0.0))
    b2[9] = -b2[9]                                          # vente
    EH = b2[18].copy()
    EH[0, 15] = 540.0                                      # +40 points contre la vente a la minute 15
    b2[18] = EH
    perdu = M4.seance4(0, 0, 0, 0.0, 0.0, -199.0, 0, 1e12, 1e12, 0.0, *b2, 2.0, 5.0, 1, 1)[0]
    vivant = M4.seance4(0, 0, 0, 0.0, 0.0, -201.0, 0, 1e12, 1e12, 0.0, *b2, 2.0, 5.0, 1, 1)[0]
    assert perdu and not vivant
    print("ok : zone sur MES = (sortie - entree) x 5 $ - 4,50 $ ; une vente sur MES est suivie a son plus haut")


def test_mes_reel(D):
    """2 bis. Sur les vraies donnees, une seance avec un seul trade de zone : moteur = calcul a la main sur l'ES."""
    b = D4.base(D)
    kN, kE = D4.facteurs_jour(D)
    Z = D["Z"]
    d = int(Z["d"].value_counts().loc[lambda s: s == 1].index[100])
    z = Z[Z["d"] == d].iloc[0]
    x = M4.seance4(d, 0, 0, 0.0, 0.0, -1e12, 0, 1e12, 1e12, 0.0, *b, 2.0 * kN[d], 5.0 * kE[d], 1, 1)[1]
    main = z["sens"] * (D["EC"][d, z["ms"]] - D["EC"][d, z["me"]]) * 5.0 * kE[d] - 4.5
    assert abs(x - main) < 1e-9, (x, main)
    print(f"ok : le {D['jours'][d].date()}, trade de zone sur MES {main:+.2f} $ (a la main = moteur)")


def test_coussin():
    """3. Challenge (plancher bloque au depart, objectif probe) : +95,50 $ par jour sur MES, +194 $ sur MNQ. Avec
    c = 2 300 $ : MES pendant 25 jours (2 387,50 $), puis MNQ ; objectif 2 775,50 $ atteint au 27e jour. Toujours MNQ :
    15e jour ; toujours MES : 30e jour."""
    b = marche(40, 98.5, 20.0)
    g_es, g_nq = 20.0 * 5.0 - 4.5, 98.5 * 2.0 - 3.0
    assert abs(g_es - 95.5) < 1e-9 and abs(g_nq - 194.0) < 1e-9
    obj = 25 * g_es + 2 * g_nq
    e = (obj, 2000.0, 0, 0.0, 0.0, 0.0, 1)
    f_ = V8.COMPTES["LucidFlex 50K"][1]
    attendu = {2300.0: 27, 0.0: int(np.ceil(obj / g_nq)), 1e18: int(np.ceil(obj / g_es))}
    for c, n in attendu.items():
        r = M4.parcours4(0, 0, 2.0, 5.0, np.zeros(0), *b, *e, *f_, 40, 1, 1, 1e18, 0.0, 1, c)
        assert r[0] == 1 and r[1] == n, (c, r[:2], n)
    print(f"ok : taille selon le coussin (c = 2 300 $ : objectif au jour 27 ; MNQ toujours : {attendu[0.0]} ;"
          f" MES toujours : {attendu[1e18]})")


def test_coussin_garde():
    """4. Compte finance LucidFlex 50K, +194 $ par jour sur MNQ : aucun retrait ne laisse moins de K $ au-dessus du
    plancher bloque a +100 $ ; avec K = 0, le premier retrait est 50 % du gain (6e jour, 582 $)."""
    nj = 120
    b = marche(nj, 98.5, 0.0)
    g = 194.0
    for k in V8.COUSSINS:
        c = dict(compte="LucidFlex 50K", zone="zone MNQ", k=k)
        e, f_, part, prix, c_mnq, pc = V8.reglages(c)
        e = (50.0,) + e[1:5] + (0.0,) + e[6:]                 # challenge reussi le 1er jour (sans regularite)
        ret = np.zeros(nj)
        r = M4.parcours4(0, 0, 2.0, 5.0, ret, *b, *e, *f_, nj, 1, 1, 1e18, 0.0, pc, c_mnq)
        assert r[0] == 1 and r[1] == 1 and not r[2] and r[3] >= 3, (k, r)
        idx = np.flatnonzero(ret)
        for i in idx:
            jours = i + 1 - r[1]                              # seances du compte finance a la fin de la seance i
            cash = g * jours - ret[:i + 1].sum()
            assert cash - 100.0 >= k * 2000.0 - 1e-9, (k, i, cash)
        if k == 0:
            assert idx[0] + 1 - r[1] == 6 and abs(ret[idx[0]] - 0.5 * 6 * g) < 1e-9, (idx[0], ret[idx[0]])
    print("ok : coussin garde apres chaque retrait (K = 0, 2 000, 4 000 $)")


def test_comptes():
    """5. Parametres des comptes = README."""
    C = V8.COMPTES
    assert C["LucidFlex 100K"][0][:2] == (6000.0, 3000.0) and C["LucidFlex 150K"][0][:2] == (9000.0, 4500.0)
    for k, (perte, seuil, plaf, prix) in {"LucidFlex 50K": (2000.0, 150.0, 2000.0, 146.0),
                                          "LucidFlex 100K": (3000.0, 200.0, 2500.0, 293.0),
                                          "LucidFlex 150K": (4500.0, 250.0, 3000.0, 407.0)}.items():
        e, f_, part, pr, pp, pc = C[k]
        assert e[1] == perte and e[3] == 100.0 and e[4] == 0.0 and e[5] == 0.5, k
        assert f_[0] == perte and f_[1] == 100.0 and f_[2] == 0.0 and f_[3] == 5 and f_[4] == seuil, k
        assert f_[6] == 500.0 and list(f_[7]) == [plaf] and f_[8] == 0.5 and part == 0.9 and pr[0] == prix, k
        assert pp == perte and pc == 1
    assert C["Topstep 50K"][4:] == (2000.0, 0) and C["FundedNext Legacy 50K"][4:] == (2000.0, 0)
    c = dict(compte="LucidFlex 150K", zone="zone MES sous 1,5x", k=2)
    e, f_, part, prix, c_mnq, pc = V8.reglages(c)
    assert c_mnq == 6750.0 and f_[9] == 100.0 + 9000.0
    assert V8.reglages(dict(compte="Topstep 50K", zone="zone MES", k=1))[1][9] == 2000.0
    assert len(V8.candidates()) == 60
    print("ok : parametres des comptes et des candidates")


def test_defaut(D):
    """1 bis. Par defaut (zone sur MNQ, c_mnq = 0), le moteur redonne exactement les sorties du moteur d'avant la vague 8
    (commit 1053118, ref_moteur_avant.json : 213 achats, LucidFlex, Topstep 3x/2x, FundedNext sans RSI(2), filtre simule
    1er tirage), retraits seance par seance compris."""
    import json
    b = D4.base(D, V8.S.gardes_simules(D, V8.S.rho_2026())[0])
    kN, kE = D4.facteurs_jour(D)
    ref = json.loads((V8.ICI / "ref_moteur_avant.json").read_text())
    for o in ref:
        nc, rsi, qc, qf, sf, pc = o["conf"]
        e, f_ = V8.V6.INTRADAY[nc][:2]
        ret = np.zeros(504)
        r = M4.parcours4(o["d"], rsi, 2.0 * kN, 5.0 * kE, ret, *b, *e, *f_, 504, qc, qf, sf, 0.0, pc)
        assert [float(x) for x in r] == o["r"], (o["conf"], o["d"], r, o["r"])
        assert {str(i): v for i, v in enumerate(ret.tolist()) if v != 0.0} == o["ret"], (o["conf"], o["d"])
    print(f"ok : par defaut, moteur = moteur d'avant la vague 8 sur {len(ref)} achats (sorties et retraits identiques)")


if __name__ == "__main__":
    test_mes_synthetique()
    test_coussin()
    test_coussin_garde()
    test_comptes()
    V8.W.regler("regles")
    D = D4.charger()
    test_mes_reel(D)
    test_defaut(D)
    assert pd.Timestamp(D["jours"][-1]) == pd.Timestamp("2026-09-25")
    print("tous les controles passent")
