#!/usr/bin/env python3
"""Controles de la machine 4 (README.md). Lancer depuis ce dossier : python3 test_machine4.py"""
import numpy as np
import pandas as pd

import machine4 as M


def test_pas_de_regard_vers_le_futur(D, I, P):
    """Les positions jusqu'a l'avant-derniere seance d'un chargement coupe au 30 juin 2016 sont celles du chargement
    complet de l'exploration : aucune decision ne lit une donnee posterieure."""
    C = M.charger("2016-06-30")
    Ic = M.indicateurs(C)
    T = len(C["jours"])
    assert (D["jours"][:T] == C["jours"]).all()
    rng = np.random.default_rng(1)
    idx = np.r_[rng.choice(len(P), 3000, replace=False), [np.flatnonzero(P[:, 0] == f)[0] for f in range(1, 10)]]
    for i in idx:
        a, b = M.pos_de(P[i], I, D)[:T - 1], M.pos_de(P[i], Ic, C)[:T - 1]
        assert (a == b).all(), (i, M.decrire(P[i]))
    print(f"ok : aucun regard vers le futur ({len(idx)} strategies, coupe au {C['jours'][-1].date()})")


def test_trade_a_la_main(D, I):
    """Un achat d'un MES de la cloture du 3 au 7 mars 2016 (meme contrat) : (C2 - C1) x 5 $ - 2 x (1 $ + 1 tick)."""
    j = D["jours"]
    m = M.RACINES.index("ES")
    a, b = j.get_loc(pd.Timestamp("2016-03-03")), j.get_loc(pd.Timestamp("2016-03-07"))
    pos = np.zeros(len(j), np.int8)
    pos[a:b] = 1
    PP, COTE = M.dollars(D)
    x = M.gains(pos, m, D["r"], PP, COTE, D["chg"])
    brut = pd.read_csv(M.R / "fonds/donnees/futures_1d.csv.gz", parse_dates=["date"])
    es = brut[brut.symbole == "ES.v.0"].set_index("date")
    assert es.loc["2016-03-03", "contrat"] == es.loc["2016-03-07", "contrat"]
    attendu = (es.loc["2016-03-07", "c"] - es.loc["2016-03-03", "c"]) * 5 - 2 * (1 + 0.25 * 5)
    assert abs(x[a:b + 1].sum() - attendu) < 1e-6, (x[a:b + 1].sum(), attendu)
    # meme gain recalcule seance par seance en Python pour une vraie strategie
    P1 = np.array([1, m, 0, 10, 3, 1, 0, 0, 0], np.int64)
    p = M.pos_de(P1, I, D)
    y = M.gains(p, m, D["r"], PP, COTE, D["chg"])
    z = [0.0] + [p[t - 1] * D["r"][m, t] * D["prix"][m, t - 1] * 5 - (abs(int(p[t]) - int(p[t - 1]))
          + (2 if p[t - 1] != 0 and D["chg"][m, t] else 0)) * COTE[m] for t in range(1, len(p))]
    assert np.allclose(y, np.nan_to_num(z))
    print(f"ok : trade a la main ({attendu:+.2f} $) et gains seance par seance")


def test_decalage_croise(D, P):
    """Famille croisee : changer le rendement du marche source a la seance t0 ne change aucune position jusqu'a t0
    (la source n'est lue qu'avec sa cloture de la veille)."""
    t0 = D["jours"].get_loc(pd.Timestamp("2018-02-05"))
    s = M.RACINES.index("ZN")
    E = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in D.items()}
    E["r"][s, t0] += 0.05
    I, Ie = M.indicateurs(D), M.indicateurs(E)
    rows = P[(P[:, 0] == 9) & (P[:, 2] == s)]
    change = 0
    for row in rows[::7]:
        a, b = M.pos_de(row, I, D), M.pos_de(row, Ie, E)
        assert (a[:t0 + 1] == b[:t0 + 1]).all(), M.decrire(row)
        change += int((a != b).any())
    assert change > 0
    print(f"ok : decalage d'une seance dans la famille croisee ({len(rows[::7])} strategies, {change} changent apres t0)")


def test_bruit_fidele(D):
    B, PPb, _ = M.bruiter(D, 7)
    PP, _ = M.dollars(D)
    j = D["jours"]
    fen = (j >= pd.Timestamp(M.DEBUT)) & (j <= pd.Timestamp(M.FIN_EXPLORATION))
    for m in range(len(M.RACINES)):
        assert np.allclose(np.sort(B["r"][m, fen]), np.sort(D["r"][m, fen]))
        assert np.allclose(np.sort(PPb[m, fen]), np.sort(PP[m, fen]))
        assert np.array_equal(B["r"][m, ~fen], D["r"][m, ~fen])
        q = ~np.isnan(D["prix"][m]) & fen
        assert np.array_equal(np.isnan(B["ibs"][m, ~q]), np.isnan(D["ibs"][m, ~q]))
    assert np.array_equal(B["chg"], D["chg"])
    m = M.RACINES.index("NQ")
    assert not np.allclose(B["r"][m, fen], D["r"][m, fen])
    print("ok : bruit fidele (memes rendements, prix et IBS, permutes dans 2011-2022 seulement ; echeances en place)")


def test_echeance(D):
    """Le jour d'un changement de contrat, le rendement est celui du nouveau contrat depuis sa cloture de la veille."""
    brut = pd.read_csv(M.R / "fonds/donnees/futures_1d.csv.gz", parse_dates=["date"])
    m = M.RACINES.index("CL")
    j = D["jours"]
    t = np.flatnonzero(D["chg"][m] & (j > pd.Timestamp("2015-01-01")))[0]
    c0 = brut[brut.symbole == "CL.v.0"].set_index("date")["c"]
    c1 = brut[brut.symbole == "CL.v.1"].set_index("date")["c"]
    attendu = c0.loc[j[t]] / c1.loc[j[t - 1]] - 1
    assert abs(D["r"][m, t] - attendu) < 1e-12
    assert abs(D["r"][m, t] - (c0.loc[j[t]] / c0.loc[j[t - 1]] - 1)) > 1e-6
    print(f"ok : rendement sans saut d'echeance (CL le {j[t].date()} : {attendu:+.4%})")


def test_calendrier(D, I):
    j, cal = D["jours"], I["CAL"]
    t = j.get_loc(pd.Timestamp("2015-12-30"))            # seance suivante : 31 decembre, derniere du mois
    assert cal[1, t] == -1 and cal[0, t] == 3 and cal[4, t] == 12
    t = j.get_loc(pd.Timestamp("2015-12-31"))            # suivante : 4 janvier 2016, premiere du mois
    assert cal[1, t] == 0 and cal[0, t] == 0
    t = j.get_loc(pd.Timestamp("2016-11-23"))            # suivante : 25 novembre, veille ? non ; 23 -> 25 (jeudi ferie)
    assert cal[0, t] == 4
    t = j.get_loc(pd.Timestamp("2016-11-22"))            # suivante : 23 novembre, veille de Thanksgiving
    assert cal[2, t] == 1
    t = j.get_loc(pd.Timestamp("2016-01-08"))            # suivante : lundi 11 janvier, semaine du 15 (3e vendredi)
    assert cal[3, t] == 1
    print("ok : calendrier (fin et debut de mois, veille de ferie, semaine d'echeance)")


def test_familles(D, I, P):
    for f in range(1, 10):
        rows = P[P[:, 0] == f]
        actifs = np.mean([(M.pos_de(r, I, D) != 0).any() for r in rows[:: max(1, len(rows) // 60)]])
        assert actifs > 0.5, (f, actifs)
    print("ok : chaque famille prend des positions")


if __name__ == "__main__":
    D = M.charger(M.FIN_EXPLORATION)
    I = M.indicateurs(D)
    PP, _ = M.dollars(D)
    fen = M.periodes(D["jours"]) >= 0
    ecart = [float(np.std((D["r"][m] * PP[m])[fen & ~np.isnan(D["prix"][m])])) for m in range(len(M.RACINES))]
    P = M.grille([m for m, e in enumerate(ecart) if e <= M.ECART_MAX])
    test_pas_de_regard_vers_le_futur(D, I, P)
    test_trade_a_la_main(D, I)
    test_decalage_croise(D, P)
    test_bruit_fidele(D)
    test_echeance(D)
    test_calendrier(D, I)
    test_familles(D, I, P)
