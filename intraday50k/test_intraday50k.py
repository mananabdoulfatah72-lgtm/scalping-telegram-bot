#!/usr/bin/env python3
"""Controles de intraday50k (README.md). Lancer depuis ce dossier : python3 test_intraday50k.py"""
import numpy as np
import pandas as pd

import commun as K


def test_nuit(D):
    """Les barres de nuit sont entre 18 h le soir de la seance d'avant et 9 h le matin de la seance, du meme contrat ;
    aucune barre de la seance americaine n'y entre."""
    h = pd.read_csv(K.R0 / "nuit/donnees/nasdaq100_1h.csv.gz")
    t = pd.to_datetime(h["t"])
    j = D["jours"]
    for d in np.random.default_rng(3).choice(np.flatnonzero(D["nn"] > 0), 300, replace=False):
        a, b = j[d - 1] + pd.Timedelta(hours=18), j[d] + pd.Timedelta(hours=9)
        sel = h[(t >= a) & (t < b) & (h["contrat"] == D["contrat"][d])]
        n = D["nn"][d]
        assert n == min(len(sel), K.NB_NUIT), (j[d], n, len(sel))
        assert np.allclose(D["NO"][d, :n], sel["o"].to_numpy()[:n])
    print(f"ok : nuits ({int((D['nn'] > 0).sum())} seances avec barres de nuit, {int(D['n18'].sum())} commencent a 18 h)")


def test_alignement(D):
    """Barre d'une heure de 10 h contre minute de 10 h : meme contrat, meme prix d'ouverture (ecart median nul)."""
    h = pd.read_csv(K.R0 / "nuit/donnees/nasdaq100_1h.csv.gz")
    h = h[h["t"].str[11:16] == "10:00"]
    o = pd.Series(h["o"].to_numpy(), index=pd.to_datetime(h["t"].str[:10]))
    c = pd.Series(h["contrat"].to_numpy(), index=o.index)
    j = D["jours"]
    x = o.reindex(j).to_numpy()
    meme = c.reindex(j).to_numpy() == D["contrat"]
    ecart = np.abs(x - D["O"][:, 30])[meme & ~np.isnan(x)]
    assert np.median(ecart) == 0 and np.mean(ecart < 1.0) > 0.98, (np.median(ecart), np.mean(ecart < 1.0))
    print(f"ok : alignement barres d'une heure / minutes ({len(ecart)} seances, ecart median {np.median(ecart):.2f} pt)")


def test_original(D, R):
    """L'original recalcule ici redonne le RSI(2) du robot sur 2023 - 25 septembre 2026 (+11 098,5 $, protection/)."""
    v = R.loc[R.index >= "2023-01-01", "gain_o"].sum()
    assert abs(v - 11098.5) < 1.0, v
    print(f"ok : original 2023 - sept. 2026 = {v:+,.1f} $ (comme le robot)")


def test_trade_a_la_main(D, R):
    """Un jour tenu par la variante, recalcule a la main : (sortie - barre de nuit) x 2 $ - 2 ordres x (1 $ + 1 tick)."""
    d = int(np.flatnonzero((R["tenu_v"] == 1).to_numpy() & (D["nn"] > 0) & (D["dec"] >= 0) & (D["voulu"] == 0))[5])
    s = D["O"][d, D["dec"][d]]
    attendu = (s - D["NO"][d, 0]) * 2 - 2 * (1 + 0.25 * 2)
    assert abs(R["gain_v"].iloc[d] - attendu) < 1e-9, (R["gain_v"].iloc[d], attendu)
    d2 = int(np.flatnonzero((R["tenu_v"] == 1).to_numpy() & (D["nn"] > 0) & (D["voulu"] == 1) & (D["dec"] >= 0))[5])
    s2 = D["C"][d2, D["derniere"][d2]]
    attendu2 = (s2 - D["NO"][d2, 0]) * 2 - 3.0
    assert abs(R["gain_v"].iloc[d2] - attendu2) < 1e-9
    print(f"ok : jours a la main ({D['jours'][d].date()} vendu a 15 h 50 : {attendu:+.2f} $ ;"
          f" {D['jours'][d2].date()} ferme a la derniere minute : {attendu2:+.2f} $)")


def test_moteur(D, R):
    """1. Zone seule, sans limite : meme valeur finale que le moteur de protection/ avec le RSI(2) coupe.
    2. Zone + RSI(2) entre deux clotures, sans limite : valeur finale = somme des gains par seance (gains_jour).
    3. RSI(2) seul (zone coupee) : gains_jour = la variante de commun.rsi2_entre_deux, seance par seance."""
    import moteur as M
    nj = len(D["jours"])
    zt = K.P.tableaux_zone(D["Z"], nj, np.ones(len(D["Z"]), bool))
    j = D["jours"]
    d0 = int(np.searchsorted(j, pd.Timestamp("2023-01-03")))
    zero = np.zeros(nj, np.int64)
    ref = K.P.jouer(d0, nj, D["O"], D["H"], D["L"], D["C"], *zt, D["dec"], zero, zero, 1e12, 1e12, 0, np.nan, 0.0,
                    0.0, 0, 0, 0, 0, 0.0, 0.0, 0.0, K.P.FRAIS_ZONE, K.P.FRAIS_RSI, K.P.GLISSE)[4]
    a = (D["O"], D["H"], D["L"], D["C"], D["derniere"], *zt, D["dec"], D["voulu"], D["NO"], D["NH"], D["NL"], D["nn"])
    moi = M.challenge(d0, nj, 0, *a, 1e12, 1e12, 0, 1e12, 0.0, 0.0, 0, K.P.FRAIS_ZONE, K.P.FRAIS_RSI)[3]
    assert abs(moi - ref) < 1e-6, (moi, ref)
    g = M.gains_jour(1, D["O"], D["C"], D["derniere"], *zt, D["dec"], D["voulu"], D["NO"], D["nn"], K.P.FRAIS_ZONE,
                     K.P.FRAIS_RSI)
    moi2 = M.challenge(d0, nj, 1, *a, 1e12, 1e12, 0, 1e12, 0.0, 0.0, 0, K.P.FRAIS_ZONE, K.P.FRAIS_RSI)[3]
    assert abs(moi2 - g[d0:].sum()) < 1e-6, (moi2, g[d0:].sum())
    zt0 = K.P.tableaux_zone(D["Z"], nj, np.zeros(len(D["Z"]), bool))
    g0 = M.gains_jour(1, D["O"], D["C"], D["derniere"], *zt0, D["dec"], D["voulu"], D["NO"], D["nn"], K.P.FRAIS_ZONE,
                      K.P.FRAIS_RSI)
    assert np.allclose(g0, R["gain_v"].to_numpy()), np.abs(g0 - R["gain_v"].to_numpy()).max()
    print(f"ok : moteur (zone seule 2023 - sept. 2026 {moi:+,.1f} $ comme protection/ ; zone + RSI(2) entre deux"
          f" clotures {moi2:+,.1f} $ = somme des seances ; RSI(2) seul = partie 1)")


if __name__ == "__main__":
    D = K.charger()
    R = K.rsi2_entre_deux(D)
    test_nuit(D)
    test_alignement(D)
    test_original(D, R)
    test_trade_a_la_main(D, R)
    test_moteur(D, R)
