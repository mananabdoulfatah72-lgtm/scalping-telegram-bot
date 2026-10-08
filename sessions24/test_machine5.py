#!/usr/bin/env python3
"""Controles de la machine 5 sur des prix fabriques (README.md). Lancer depuis ce dossier : python3 test_machine5.py"""
import numpy as np
import pandas as pd

import machine5 as M5


def faux_marche(code, effet=None, graine=1, fin="2016-12-31"):
    """Marche au hasard en barres de 5 min (jours de semaine), avec un effet optionnel : effet(t_utc) -> rendement ajoute."""
    t = pd.date_range("2012-01-02", fin, freq="5min", tz="UTC")
    t = t[t.dayofweek < 5]
    rng = np.random.default_rng(graine)
    r = rng.normal(0, 3e-4, len(t))
    if effet is not None:
        r = r + effet(t)
    p = 1.2 * np.exp(np.cumsum(r))
    o = np.r_[1.2, p[:-1]]
    d = pd.DataFrame({"t": t.strftime("%Y-%m-%d %H:%M"), "o": o, "h": np.maximum(o, p) * 1.0001,
                      "l": np.minimum(o, p) * 0.9999, "c": p})
    return M5.Marche(code, d)


def test_heures():
    j = pd.DatetimeIndex(["2015-07-15", "2015-01-15"])
    assert list(M5.heure_utc(j, M5.LONDRES, "16:00").strftime("%H:%M")) == ["15:00", "16:00"]
    assert list(M5.heure_utc(j, M5.TOKYO, "09:55").strftime("%H:%M")) == ["00:55", "00:55"]
    assert list(M5.heure_utc(j, M5.FRANCFORT, "14:15").strftime("%H:%M")) == ["12:15", "13:15"]
    assert list(M5.heure_utc(j, M5.NY, "09:30").strftime("%H:%M")) == ["13:30", "14:30"]
    print("ok : heures des fixings et des sessions en UTC (heure d'ete et d'hiver)")


def test_effet_retrouve():
    """Le dollar monte (EUR/USD baisse de 1 pb par barre) dans l'heure avant le fixing WM/Reuters : F1 « avant » le
    retrouve (t eleve, placebo p faible) ; sans effet, rien."""
    def effet(t):
        loc = t.tz_convert(M5.LONDRES)
        m = loc.hour * 60 + loc.minute
        return np.where((m >= 15 * 60) & (m < 16 * 60), -1e-4, 0.0)
    S = {s["nom"]: s for s in M5.strategies()}
    s = S["F1 fixing WM/Reuters 16 h avant eurusd"]
    M = faux_marche("eurusd", effet)
    d = M5.jouer(s, M, "2012-01-01", "2016-12-31")
    t = M5.t_stat(M5.par_jour(d))
    p, n = M5.placebo(s, M, d)
    assert t > 5 and p < 0.01, (t, p)
    M0 = faux_marche("eurusd", None)
    d0 = M5.jouer(s, M0, "2012-01-01", "2016-12-31")
    brut = d0.assign(r=d0["r"] + 1.5e-4)                           # avant frais (1,5 pb par aller-retour)
    t0 = M5.t_stat(M5.par_jour(brut))
    assert abs(t0) < 3.5 and len(d0) > 1000, (t0, len(d0))
    print(f"ok : effet du fixing retrouve (t {t:+.1f}, placebo p {p:.3f} sur {n}) ; sans effet, avant frais, t {t0:+.2f}")


def test_cassure_a_la_main():
    """Fourchette 100-101 sur 2 barres ; cloture a 101,5 -> achat a l'ouverture suivante (101,6) ; stop a 100 touche
    deux barres plus loin, ouverture deja dessous (99,8) -> sortie a 99,8."""
    O = np.array([100.5, 100.2, 100.8, 101.6, 101.0, 99.8, 99.0, 99.1])
    H = np.array([101.0, 100.9, 101.6, 101.7, 101.1, 100.1, 99.5, 99.3])
    L = np.array([100.0, 100.1, 100.7, 101.0, 100.4, 99.7, 98.9, 99.0])
    C = np.array([100.2, 100.8, 101.5, 101.1, 100.5, 99.9, 99.2, 99.1])
    s, pe, ps, bs = M5.cassures(O, H, L, C, np.array([0]), np.array([2]), np.array([7]), 2)
    assert s[0] == 1 and pe[0] == 101.6 and ps[0] == 99.8 and bs[0] == 5, (s, pe, ps, bs)
    s2, pe2, ps2, bs2 = M5.cassures(O, H, L, C, np.array([0]), np.array([2]), np.array([5]), 2)
    assert s2[0] == 1 and ps2[0] == O[5] and bs2[0] == 5            # pas de stop avant la fin : sortie a l'ouverture de fin
    print("ok : cassure recalculee a la main (entree, stop deja depasse, sortie de fin de session)")


def test_pas_de_futur():
    """Changer les prix apres la sortie d'un trade ne change pas ce trade (fenetres, cassures, suite de sessions)."""
    M = faux_marche("gbpusd", None, graine=3, fin="2013-12-31")
    S = M5.strategies()
    noms = ["F1 fixing BCE 14 h 15 les deux gbpusd", "F3 cassure Londres 30 min gbpusd", "F4 Asie -> Londres sortie 12:00 gbpusd",
            "F5 Tokyo -> Londres continuation gbpusd", "F5 Londres -> New York retournement gbpusd",
            "F5 New York -> Tokyo continuation gbpusd"]
    for nom in noms:
        s = next(x for x in S if x["nom"] == nom)
        d = M5.jouer(s, M, "2012-01-01", "2013-06-30")
        coupe = M.t0 + pd.Timedelta(days=200)
        k = int((coupe - M.t0) / M5.PAS)
        M2 = faux_marche("gbpusd", None, graine=3, fin="2013-12-31")
        rng = np.random.default_rng(9)
        for a in (M2.O, M2.H, M2.L, M2.C):
            a[k:] = a[k:] * np.exp(rng.normal(0, 0.01, len(a) - k))
        d2 = M5.jouer(s, M2, "2012-01-01", "2013-06-30")
        avant = d["jour"] < pd.Timestamp(coupe.tz_convert(None).normalize()) - pd.Timedelta(days=2)
        avant2 = d2["jour"] < pd.Timestamp(coupe.tz_convert(None).normalize()) - pd.Timedelta(days=2)
        assert avant.sum() > 50 and np.allclose(d.loc[avant, "r"].to_numpy(), d2.loc[avant2, "r"].to_numpy()), nom
    print(f"ok : aucun regard vers le futur ({len(noms)} strategies)")


def test_nombre():
    S = M5.strategies()
    f = pd.Series([s["famille"] for s in S]).value_counts().to_dict()
    assert len(S) == 158 and f == {"F5": 48, "F3": 44, "F1": 36, "F2": 12, "F4": 16, "F6": 2}, f
    assert len({s["nom"] for s in S}) == 158
    print("ok : 158 strategies (F1 36, F2 12, F3 44, F4 16, F5 48, F6 2 ; Dow Jones retire)")


if __name__ == "__main__":
    test_heures()
    test_nombre()
    test_cassure_a_la_main()
    test_effet_retrouve()
    test_pas_de_futur()
