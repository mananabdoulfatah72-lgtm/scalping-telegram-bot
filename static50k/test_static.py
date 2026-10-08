#!/usr/bin/env python3
"""Controles de static50k (README.md). Lancer depuis ce dossier : python3 test_static.py"""
import numpy as np
import pandas as pd

import donnees as DN
import moteur_static as M
import outils as U

K = DN.K
INF = 1e12


def gains_zone(D, garde=None):
    """Gain de chaque seance de la zone seule, 1 MNQ, au prix de l'epoque (comme protection/)."""
    Z, C = D["Z"], D["C"]
    d, me, ms, s = (Z[k].to_numpy() for k in ("d", "me", "ms", "sens"))
    ms = np.minimum(ms, D["derniere"][d])
    g = s * (C[d, ms] - C[d, me]) * 2.0 - M.FRAIS_ZONE
    out = np.zeros(len(D["jours"]))
    np.add.at(out, d, g if garde is None else g * garde)
    return out


def test_gains(D, b):
    """1. Sans compte, au prix de l'epoque : zone seule = protection/ (+10 668,5 $ sur 2023 - sept. 2026), et zone + RSI(2)
    = zone + RSI(2) d'origine les jours ou le RSI(2) est a plat apres sa decision (cumul identique)."""
    j = D["jours"]
    d0 = int(np.argmax((j >= pd.Timestamp("2023-01-01")) & (D["ouvert"] == 0)))
    n = len(j) - d0
    gz = gains_zone(D)
    for nuit in (0, 1):
        tr = np.zeros(n)
        U.achat(D, b, d0, "E1", nuit=nuit, niveau=False, h1=n, h2=n, perte=INF, objectif=INF, trace=tr)
        assert abs(tr[-1] - gz[d0:].sum()) < 1e-6 and abs(tr[-1] - 10668.5) < 1e-6, (tr[-1], gz[d0:].sum())
        assert np.allclose(tr, np.cumsum(gz[d0:]))
        tr0 = np.zeros(n)
        U.achat(D, b, d0, "E0", nuit=nuit, niveau=False, h1=n, h2=n, perte=INF, objectif=INF, trace=tr0)
        R = K.rsi2_entre_deux(D)
        cum = np.cumsum(gz[d0:] + R["gain_o"].to_numpy()[d0:])
        plat = np.zeros(len(j), bool)
        tenu = 0
        for d in range(len(j)):
            if D["dec"][d] >= 0:
                tenu = D["voulu"][d]
            plat[d] = tenu == 0
        ok = plat[d0:]
        assert np.allclose(tr0[ok], cum[ok]), np.abs(tr0[ok] - cum[ok]).max()
    print(f"ok : zone seule {tr[-1]:+,.1f} $ (2023 - sept. 2026) ; zone + RSI(2) = zone + RSI(2) d'origine sur les "
          f"{ok.sum()} seances a plat, avec et sans les barres de nuit")


def test_budget30(D, b):
    """2. Sans les barres de nuit, au prix de l'epoque : l'evaluation E0 redonne intraday50k/budget30.py (Static, 1 MNQ)."""
    import piste2 as Q
    import piste5 as S
    P = DN.P
    j = D["jours"]
    jours, O, H, L, C, Z, dec, voulu, ouvert = P.donnees()
    nj = len(jours)
    a = Q.zt_args((O, H, L, C, P.tableaux_zone(Z, nj, np.ones(len(Z), bool)), dec, voulu, ouvert))
    possibles = [d for d in range(260, nj) if ouvert[d] == 0]
    dd = [d for d in possibles[::5] if j[d] >= pd.Timestamp("2023-01-01")]
    diff = 0
    for d in dd:
        etat = S.depart(ouvert, d, 1000.0)
        meilleur, qual, res = -1e18, 0, (0, 252)
        for x in range(d, min(nj, d + 252)):
            perdu, eod = S.seance5(x, etat, *a[:12], 1000.0, 1, -1000.0, P.FRAIS_ZONE, P.FRAIS_RSI, 0.0, 0.0)
            if perdu:
                res = (-1, x - d + 1)
                break
            gg = eod - etat[10]
            etat[10] = eod
            meilleur = max(meilleur, gg)
            qual += gg >= 200
            if eod >= 3750 and qual >= 2 and meilleur <= 0.5 * eod:
                res = (1, x - d + 1)
                break
        r = U.achat(D, b, d, "E0", nuit=0, niveau=False, h2=252)
        mine = (int(r[M.ISSUE]), int(r[M.FIN_EVAL]))
        if res[0] == 0:
            res = (0, min(nj, d + 252) - d)
        diff += mine != res
    assert diff == 0, diff
    print(f"ok : evaluation E0 sans la nuit = budget30 sur {len(dd)} departs de 2023 - 2026")


def test_mes(D, b):
    """3a. Premier trade du RSI(2) sur MES apres 2023, recalcule a la main : ouverture de la minute de decision a l'achat
    et a la vente, 5 $ par point, 2,25 $ par ordre."""
    j = D["jours"]
    d0 = int(np.argmax((j >= pd.Timestamp("2023-01-01")) & (D["ouvert"] == 0)))
    n = 300
    t4, t1 = np.zeros(n), np.zeros(n)
    U.achat(D, b, d0, "E4", nuit=1, niveau=False, h1=n, h2=n, perte=INF, objectif=INF, trace=t4)
    U.achat(D, b, d0, "E1", nuit=1, niveau=False, h1=n, h2=n, perte=INF, objectif=INF, trace=t1)
    dec, voulu = D["dec"], D["voulu"]
    a = next(d for d in range(d0, len(j)) if dec[d] >= 0 and voulu[d] == 1)
    v = next(d for d in range(a + 1, len(j)) if dec[d] >= 0 and voulu[d] == 0)
    assert not D["roule_es"][a:v + 1].any()
    main_ = (D["EO"][v, dec[v]] - D["EO"][a, dec[a]]) * 5.0 - 2 * M.ORDRE_ES
    ecart = t4[v - d0] - t1[v - d0]
    assert abs(ecart - main_) < 1e-6, (ecart, main_)
    print(f"ok : trade du RSI(2) sur MES du {j[a].date()} au {j[v].date()} : {main_:+.2f} $ (a la main = moteur)")


def marche_synthetique(nj, hausse):
    """Marche plat a 1 000 points ; un trade de zone par seance, achat a la minute 10, vente a la minute 20 ; la minute 20
    cloture a 1 000 + hausse. Pas de RSI(2), pas de nuit."""
    N = 391
    O = np.full((nj, N), 1000.0)
    H, L, C = O.copy(), O.copy(), O.copy()
    C[:, 20] = 1000.0 + hausse
    H[:, 20] = 1000.0 + hausse
    der = np.full(nj, N - 1, np.int64)
    z_deb, z_fin = np.arange(nj, dtype=np.int64), np.arange(1, nj + 1, dtype=np.int64)
    z_me, z_ms = np.full(nj, 10, np.int64), np.full(nj, 20, np.int64)
    z_sens, z_garde = np.ones(nj, np.int64), np.ones(nj, np.int64)
    dec, voulu = np.full(nj, -1, np.int64), np.zeros(nj, np.int64)
    A = np.full((nj, DN.NA), 1000.0)
    return (O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu, O, H, L, C, np.zeros(nj, np.bool_),
            A, A, A, A, A, A, A, A, np.zeros(nj, np.int64), np.zeros(nj, np.int64))


def test_retraits():
    """3b. Retraits du compte Pro a la main : +300 $ par seance (151,5 points, 3 $ de frais). Evaluation (objectif 300 $
    pour le test) reussie a la 2e seance. Pro : 2 700 $ a la 9e seance (8 jours a +200 $, meilleur jour 300 <= 30 %)
    -> retrait de 500 $ (garder 52 000 $) ; puis 4 600 $ a la 8e seance du cycle suivant -> 2 000 $ (le maximum)."""
    b = marche_synthetique(40, 151.5)
    tr = np.zeros(40)
    r = M.parcours(0, 40, 40, 1, 0.0, 0, 1, 2.0, 5.0, 1000.0, 300.0, tr, *b)
    assert r[M.ISSUE] == 1 and r[M.FIN_EVAL] == 2, r
    # Pro : seances 3, 4, ... ; valeur apres k seances = 300 k
    assert r[M.PREMIER] == 2 + 9, r[M.PREMIER]
    assert abs(tr[2 + 9 - 1] - 2700.0) < 1e-9
    # cycle 2 : depart 2 200 $, 8 seances -> 4 600 $ -> 2 000 $ ; cycle 3 : depart 2 600, 8 seances -> 5 000 -> 2 000
    # cycle 4 : 3 000 + 2 400 = 5 400 a la seance 11 + 24 = 35 -> 2 000 ; seance 40 : pas encore (5 seances)
    assert r[M.RECU1] == 500 + 2000 + 2000 + 2000 and r[M.NRET1] == 4, (r[M.RECU1], r[M.NRET1])
    # plafond de 500 $ : le trade de +300 $ ne le touche pas ; plafond de 200 $ : chaque jour s'arrete a +200 $ - frais
    r2 = M.parcours(0, 40, 40, 1, 200.0, 0, 1, 2.0, 5.0, 1000.0, 300.0, np.zeros(40), *b)
    g = 200.0 - M.FRAIS_ZONE - M.TICK_NQ
    assert r2[M.ISSUE] == 1
    tr2 = np.zeros(40)
    M.parcours(0, 40, 40, 1, 200.0, 0, 1, 2.0, 5.0, 1000.0, 300.0, tr2, *b)
    assert abs(tr2[3] - tr2[2] - g) < 1e-9, (tr2[3] - tr2[2], g)
    print(f"ok : retraits a la main (500 $ a la 9e seance du compte Pro, puis 3 x 2 000 $) ; plafond du jour {g:+.2f} $")


def test_pessimiste():
    """3c. Compte Pro pessimiste : apres le premier retrait (valeur 2 200 $), le plancher passe a 1 200 $."""
    b = marche_synthetique(30, 151.5)
    O, H, L, C = (x.copy() for x in b[:4])
    L[14, 15] = 0.0                    # 4e seance du cycle 2 (valeur 3 100 $) : creux de -2 000 $ pendant le trade
    b2 = (O, H, L, C) + b[4:]
    r = M.parcours(0, 30, 30, 1, 0.0, 0, 1, 2.0, 5.0, 1000.0, 300.0, np.zeros(30), *b2)
    rp = M.parcours(0, 30, 30, 1, 0.0, 1, 1, 2.0, 5.0, 1000.0, 300.0, np.zeros(30), *b2)
    assert r[M.PRO_PERDU] == 0 and rp[M.PRO_PERDU] == 1 and rp[M.FIN_PRO] == 15, (r, rp)
    print("ok : compte Pro pessimiste perdu par un creux que le compte normal supporte")


def test_futur(D, b):
    """4. Changer les prix apres une date ne change aucune valeur de fin de journee avant cette date."""
    j = D["jours"]
    d0 = int(np.argmax((j >= pd.Timestamp("2024-01-01")) & (D["ouvert"] == 0)))
    coupe = int(np.searchsorted(j, pd.Timestamp("2024-07-01")))
    rng = np.random.default_rng(3)
    b2 = list(b)
    for i in (0, 1, 2, 3, 13, 14, 15, 16, 18, 19, 20, 21, 22, 23, 24, 25):
        x = b[i].copy()
        x[coupe:] = x[coupe:] * np.exp(rng.normal(0, 0.01, x[coupe:].shape))
        b2[i] = x
    bouge = 0
    for v in ("E0", "E5", "E6"):
        t1, t2 = np.zeros(400), np.zeros(400)
        U.achat(D, b, d0, v, plafond=500.0, trace=t1)
        U.achat(D, tuple(b2), d0, v, plafond=500.0, trace=t2)
        k = coupe - d0 - 1
        assert np.array_equal(t1[:k], t2[:k]), v
        bouge += not np.array_equal(t1, t2)
    print(f"ok : aucun regard vers le futur (E0, E5, E6, plafond 500 $ ; {bouge} parcours changes apres la date)")


def test_niveau(D, b):
    """5. Facteur de prix : passer 2 x f $ par point = multiplier tous les prix par f ; f = 1 = prix de l'epoque."""
    j = D["jours"]
    d = int(np.argmax((j >= pd.Timestamp("2019-01-01")) & (D["ouvert"] == 0)))
    fn, fe = U.facteurs(D, d, True)
    b2 = list(b)
    for i in (0, 1, 2, 3, 18, 19, 20, 21):
        b2[i] = b[i] * fn
    for i in (13, 14, 15, 16, 22, 23, 24, 25):
        b2[i] = b[i] * fe
    for v in ("E0", "E4", "E6"):
        r1 = U.achat(D, b, d, v, plafond=500.0, niveau=True)
        r2 = U.achat(D, tuple(b2), d, v, plafond=500.0, niveau=False)
        assert np.allclose(r1, r2), (v, r1, r2)
    r3 = U.achat(D, b, d, "E0", niveau=False)
    r4 = M.parcours(d, 252, 504, 0, 0.0, 0, 1, 2.0, 5.0, M.PERTE, M.OBJECTIF, np.zeros(0), *b)
    assert np.array_equal(r3, r4)
    print(f"ok : niveau d'aujourd'hui (facteurs NQ {fn:.2f}, ES {fe:.2f} en janvier 2019) = prix multiplies")


if __name__ == "__main__":
    D = DN.charger()
    b = U.base(D)
    test_retraits()
    test_pessimiste()
    test_gains(D, b)
    test_budget30(D, b)
    test_mes(D, b)
    test_futur(D, b)
    test_niveau(D, b)
