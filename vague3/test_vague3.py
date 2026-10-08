#!/usr/bin/env python3
"""Controles de la vague 3 (README.md), sur l'exploration seulement. Lancer depuis ce dossier : python3 test_vague3.py"""
import numpy as np
import pandas as pd

import vague3 as V

T8 = V.T8


def jours_en_position(s, pos):
    d = pd.DatetimeIndex(s["date"])
    return [x.date().isoformat() for x in d[pos != 0]]


def test_echeance(nq):
    """W1, octobre 2022 : 3e vendredi le 21 ; achat a la decision du vendredi 14, vente a celle du 21."""
    pos = V.w1_echeance(nq)
    d = pd.DatetimeIndex(nq["date"])
    m = (d >= "2022-10-10") & (d <= "2022-10-25")
    assert jours_en_position(nq[m], pos[m]) == ["2022-10-14", "2022-10-17", "2022-10-18", "2022-10-19", "2022-10-20"]
    # avril 2022 : 3e vendredi 15 = Vendredi saint (ferie) -> vente a la decision du jeudi 14
    m = (d >= "2022-04-04") & (d <= "2022-04-20")
    assert jours_en_position(nq[m], pos[m]) == ["2022-04-08", "2022-04-11", "2022-04-12", "2022-04-13"], \
        jours_en_position(nq[m], pos[m])
    print("ok : W1 echeance des options (octobre 2022, avril 2022 avec le Vendredi saint)")


def test_fed(nq):
    """W2 : annonce du 21 septembre 2022 (mercredi). Semaine 0 = 20 au 26 septembre ; semaine 1 = 27 sept. au 3 oct. ;
    semaine 2 = 4 au 10 octobre. Le 19 septembre est 37 seances apres l annonce du 27 juillet : hors des semaines 0 a 6. En position a la decision t si la seance t+1 est en semaine paire."""
    d = pd.DatetimeIndex(nq["date"])
    sem = V.semaines_fed(nq["date"], V.fomc.annonces())
    x = pd.Series(sem, index=d)["2022-09-16":"2022-10-12"]
    attendu = {"2022-09-19": -1, "2022-09-20": 0, "2022-09-21": 0, "2022-09-26": 0, "2022-09-27": 1, "2022-10-03": 1,
               "2022-10-04": 2, "2022-10-10": 2, "2022-10-11": 3}
    for j, w in attendu.items():
        assert x[j] == w, (j, x[j], w)
    pos = V.w2_fed(nq)
    p = pd.Series(pos, index=d)
    assert p["2022-09-19"] == 1 and p["2022-09-26"] == 0 and p["2022-10-03"] == 1 and p["2022-10-10"] == 0
    print("ok : W2 semaines du cycle de la Fed (septembre - octobre 2022)")


def test_reequilibrage(nq, es):
    """W3 / W4 : recalcul a la main de l'ecart ES - ZN d'un mois, et fenetre des 5 dernieres seances."""
    d = pd.DatetimeIndex(nq["date"])
    ec = V.es_aligne(nq, es)
    zv, zj = V.zn(nq["date"], V.FIN_EXPLORATION), V.zn(nq["date"], V.FIN_EXPLORATION, False)
    f = pd.read_csv(V.R / "fonds/donnees/futures_1d.csv.gz")
    z = f[f["symbole"] == "ZN.v.0"].set_index("date")["c"]
    a = int(np.flatnonzero(d == "2019-05-31")[0])           # derniere seance de mai 2019
    b = int(np.flatnonzero(d == "2019-06-28")[0])           # derniere seance de juin 2019
    dec = b - 4
    assert d[dec] == pd.Timestamp("2019-06-24")
    zn_veille = z[z.index < "2019-06-24"].iloc[-1]
    zn_base = z[z.index <= "2019-05-31"].iloc[-1]
    assert zv[dec] == zn_veille and zj[a] == zn_base
    e_main = (ec[dec] / ec[a] - 1) - (zn_veille / zn_base - 1)
    for sens in (1, -1):
        pos = V.reequilibrage(nq, ec, zv, zj, sens)
        assert set(np.unique(pos)) <= {0, sens}
        fen = pos[dec:b]
        assert (fen == 0).all() or (fen == sens).all()
        assert pos[b] == 0 and pos[dec - 1] == 0
    print(f"ok : W3 / W4 ecart ES - ZN de juin 2019 a la main ({e_main:+.4f}), fenetre du 24 au 28 juin")


def test_pas_de_futur(nq, es, p):
    """Couper les donnees a une date ne change aucune position avant cette date (seuils glissants compris)."""
    coupe = "2018-06-30"
    nq2 = nq[nq["date"] <= coupe].reset_index(drop=True)
    es2 = es[es["date"] <= coupe].reset_index(drop=True)
    p2 = p[p["date"] <= coupe].reset_index(drop=True)
    for x in (nq2, es2, p2):
        x.attrs.update(nq.attrs if x is nq2 else (es.attrs if x is es2 else p.attrs))
    p2.loc[len(p2) - 1, "roule"] = True
    for k in range(7):
        a = V.positions(k, nq, es, p, V.FIN_EXPLORATION)
        b = V.positions(k, nq2, es2, p2, coupe)
        n = len(b) - 6                                      # la fin coupee change les dernieres seances (fenetres)
        assert np.array_equal(a[:n], b[:n]), V.SOURCES[k]
    print("ok : aucun regard vers le futur (7 sources, donnees coupees au 30 juin 2018)")


def test_journal_vente(nq):
    """Une vente qui baisse de x % gagne x % moins les frais ; le hasard respecte le sens et les durees."""
    pos = np.zeros(len(nq), np.int8)
    pos[100:103] = -1
    rend, dol, tr, e, so = V.journal(nq, pos)
    P = nq["P"].to_numpy()
    attendu = (-(P[103] - P[100]) - 2 * nq.attrs["cote"]) * nq.attrs["pt"]
    assert abs(tr[0] - attendu) < 1e-9 and abs(dol.sum() - attendu) < 1e-6
    q = T8.placer(np.array([3, 5], np.int64), T8.echeances(nq), 7) * np.int8(-1)
    assert q.min() == -1 and (q != 0).sum() == 8
    print("ok : journal d'une vente et placements au hasard dans le meme sens")


if __name__ == "__main__":
    nq, es, p = V.charger()
    test_echeance(nq)
    test_fed(nq)
    test_reequilibrage(nq, es)
    test_journal_vente(nq)
    test_pas_de_futur(nq, es, p)
