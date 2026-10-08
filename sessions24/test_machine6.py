#!/usr/bin/env python3
"""Controles de la vague 2 (README.md) sur des prix fabriques. Lancer depuis ce dossier : python3 test_machine6.py"""
import numpy as np
import pandas as pd

import machine5 as M5
import machine6 as M6
from test_machine5 import faux_marche


def test_nombre():
    S = M6.strategies()
    f = pd.Series([s["famille"] for s in S]).value_counts().to_dict()
    attendu = {"G1": 32, "G2": 16, "G3": 16, "G4": 20, "G5": 12, "G6": 12, "G7": 64, "G8": 32, "G9": 64, "G10": 8,
               "G11": 56, "G12": 28, "G13": 8}
    assert len(S) == 368 and f == attendu and len({s["nom"] for s in S}) == 368, f
    print("ok : 368 strategies dans 13 familles")


def test_calendriers():
    g = M6.gotobi("2023-09-01", "2023-09-30")
    assert [d.day for d in g] == [5, 8, 15, 20, 25, 29], list(g)      # 10 (dim.) -> 8 (ven.) ; 30 (sam.) -> 29
    j = M6.ouvres("2023-01-01", "2023-12-31")
    fm = M6.fins_de_mois(j, 1)
    assert fm[0] == pd.Timestamp("2023-01-31") and fm[3] == pd.Timestamp("2023-04-28") and len(fm) == 12
    assert len(M6.fins_de_mois(j, 2)) == 24 and M6.debuts_de_mois(j)[3] == pd.Timestamp("2023-04-03")
    assert list(M6.troisiemes_vendredis("2023-01-01", "2023-03-31").day) == [20, 17, 17]
    f = M6.fomc("2013-01-01", "2026-12-31")
    assert len(f) > 100 and (f.dayofweek <= 4).all() and pd.Timestamp("2022-03-16") in f
    print(f"ok : calendriers (gotobi, fins et debuts de mois, 3e vendredi, {len(f)} annonces de la Fed depuis 2013)")


def test_effet_retrouve():
    """Le dollar monte (EUR/USD baisse) de 15 h a 16 h (Londres) seulement le dernier jour ouvre du mois : G1 « avant,
    sans condition, 1 jour » le retrouve et bat le placebo de dates ; « apres » ne voit rien avant frais."""
    fins = set(M6.fins_de_mois(M6.ouvres("2012-01-01", "2016-12-31"), 1))
    def effet(t):
        loc = t.tz_convert(M5.LONDRES)
        m = loc.hour * 60 + loc.minute
        fin = pd.DatetimeIndex(loc.tz_localize(None).normalize()).isin(list(fins))
        return np.where(fin & (m >= 15 * 60) & (m < 16 * 60), -2e-4, 0.0)
    M = faux_marche("eurusd", effet, fin="2016-12-31")
    spx = faux_marche("usa500idxusd", None, graine=4, fin="2016-12-31")
    S = {s["nom"]: s for s in M6.strategies()}
    s = S["G1 fin de mois avant fixing sans 1 jour(s) eurusd"]
    d = M6.periode(M6.jouer(s, M, spx), "2012-01-01", "2016-12-31")
    t = M5.t_stat(M6.par_jour(d))
    p, n = M6.placebo(s, M, spx, d, "2012-01-01", "2016-12-31")
    assert t > 5 and p < 0.01 and len(d) >= 55, (t, p, len(d))
    s2 = S["G1 fin de mois apres fixing sans 1 jour(s) eurusd"]
    d2 = M6.periode(M6.jouer(s2, M, spx), "2012-01-01", "2016-12-31")
    t2 = M5.t_stat(M6.par_jour(d2.assign(r=d2["r"] + 1.5e-4)))
    assert abs(t2) < 3, t2
    print(f"ok : effet de fin de mois retrouve (t {t:+.1f}, placebo p {p:.3f} sur {n} tirages, {len(d)} trades) ;"
          f" apres le fixing, avant frais, t {t2:+.2f}")


def test_pas_de_futur():
    """Seuils glissants (G7) et signaux de reaction : changer les prix apres une date ne change aucun trade d'avant."""
    S = {s["nom"]: s for s in M6.strategies()}
    noms = ["G7 choc 8 h 30 continuation sortie 11:00 centile 80 gbpusd", "G8 choc 10 h retournement sortie 12:00 gbpusd",
            "G11 ecart du week-end comblement sortie lundi 09:30 grand gbpusd", "G12 vendredi 12:00-15:55 retournement gbpusd",
            "G1 fin de mois avant fixing S&P 2 jour(s) gbpusd", "G2 debut de mois 15:00-16:00 S&P gbpusd"]
    spx = faux_marche("usa500idxusd", None, graine=4, fin="2014-12-31")
    M = faux_marche("gbpusd", None, graine=3, fin="2014-12-31")
    coupe = pd.Timestamp("2013-06-03", tz="UTC")
    k = int((coupe - M.t0) / M5.PAS)
    M2 = faux_marche("gbpusd", None, graine=3, fin="2014-12-31")
    spx2 = faux_marche("usa500idxusd", None, graine=4, fin="2014-12-31")
    rng = np.random.default_rng(9)
    for X in (M2, spx2):
        for a in (X.O, X.H, X.L, X.C):
            a[k:] = a[k:] * np.exp(rng.normal(0, 0.01, len(a) - k))
    for nom in noms:
        s = S[nom]
        a = M6.periode(M6.jouer(s, M, spx), "2012-01-01", "2013-05-25")
        b = M6.periode(M6.jouer(s, M2, spx2), "2012-01-01", "2013-05-25")
        assert len(a) > 10 and len(a) == len(b) and np.allclose(a["r"].to_numpy(), b["r"].to_numpy()), nom
    print(f"ok : aucun regard vers le futur ({len(noms)} strategies, seuils glissants compris)")


def test_ecart_week_end():
    """Ecart du week-end recalcule a la main sur le premier vendredi de 2013 : derniere cloture avant 17 h (New York),
    premiere ouverture apres la pause, sortie a l'ouverture de lundi 9 h 30."""
    M = faux_marche("eurusd", None, graine=5, fin="2013-03-31")
    S = {s["nom"]: s for s in M6.strategies()}
    s = S["G11 ecart du week-end comblement sortie lundi 09:30 tout eurusd"]
    d = M6.jouer(s, M, None)
    v = pd.Timestamp("2013-01-04")
    c = M6.cloture_avant(M, M5.heure_utc(pd.DatetimeIndex([v]), M5.NY, "17:00"))[0]
    o, io = M6.ouverture_apres(M, M5.heure_utc(pd.DatetimeIndex([v + pd.Timedelta(days=2)]), M5.NY, "15:00"))
    sortie = M6.prix(M, M5.heure_utc(pd.DatetimeIndex([v + pd.Timedelta(days=3)]), M5.NY, "09:30"))[0]
    attendu = -np.sign(o[0] / c - 1) * (sortie / o[0] - 1) - 1.5e-4
    x = d[d["jour_local"] == v + pd.Timedelta(days=3)]
    assert len(x) == 1 and abs(x["r"].iloc[0] - attendu) < 1e-12, (x, attendu)
    print(f"ok : ecart du week-end a la main (ecart {o[0] / c - 1:+.5f}, resultat {attendu * 1e4:+.2f} pb)")


if __name__ == "__main__":
    test_nombre()
    test_calendriers()
    test_effet_retrouve()
    test_pas_de_futur()
    test_ecart_week_end()
