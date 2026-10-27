#!/usr/bin/env python3
"""Descriptif (27 octobre 2026) : entrer des la cassure ou attendre une confirmation par le volume, avec les sorties de la version
installee (une entree par seance, pas de sortie aux controles, stop a 70 points du niveau casse, 16 h, limite du jour 1 000 $).
Variantes : cassure sans volume ; volume x1 sur la minute de cassure seulement (fenetre 0) ; fenetres 3, 5 (installee) et 10.
Mesures : precision, t sur 2011-2022 et 2023-2026, $ en 4 MNQ, Bulenox (49 500 $, marge 1 000 $, 13 seances) et LucidFlex 50K
sans limite de temps en 2 MNQ. Ecrit resultats/j/confirmation_27oct.txt.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/confirmation_27oct.py"""
import os

import numpy as np
import pandas as pd

import challenge_ajouts as CA
import donnees as D
import lucid_27oct as LU
import partie_e as E
import partie_g as G
import partie_j as J
import reglages_26oct_g as RG
import reglages_27oct_stop as ST
import situation_bulenox as SB


def main():
    d = D.minutes("NQ", chemin=os.environ["MINUTES"], debut="2011-01-01")
    S, N = d["c"].shape
    sigma, vwap, href, bref, jouable = G.zone_tableaux(d)
    fed = np.isin(d["jours"], E.fomc())
    an = d["jours"].astype("datetime64[Y]").astype(int) + 1970
    jo = jouable & ~fed
    jours = pd.to_datetime(d["jours"])
    ech = float(d["pref"]) / d["o"][:, 0]
    dist = 70.0 * d["o"][:, 0] / float(d["pref"])
    dep = np.flatnonzero(d["jours"] >= np.datetime64("2012-01-01"))
    dep13 = dep[dep <= S - 13]
    depl = dep[d["jours"][dep] < np.datetime64("2025-10-01")]
    zero = np.zeros_like(d["c"])
    L = ["Sorties de la version installee (stop 70 points du niveau, pas de sortie aux controles), 4 MNQ, prix d'aujourd'hui", "",
         f"{'entree':<34} {'trades':>6} {'gagnants':>8} {'au-dela':>7} {'t 11-22':>8} {'t 23-26':>8} {'2023-26':>9} {'2026':>8} "
         f"{'Bulenox':>8} {'Lucid 2 MNQ':>11}"]
    for nom, k, W in (("des la cassure, sans volume", 0.0, 0), ("cassure + volume, minute seule", 1.0, 0),
                      ("volume, fenetre 3 min", 1.0, 3), ("volume, fenetre 5 min (installee)", 1.0, 5), ("volume, fenetre 10 min", 1.0, 10)):
        t = RG._zone_fw(d["c"], d["v"], sigma, href, bref, jouable, k, W, 30).copy()
        t[:, 4], t[:, 5], t[:, 6] = N - 1, d["c"][t[:, 0].astype(int), N - 1], 0
        s_, me, e = t[:, 0].astype(int), t[:, 1].astype(int), t[:, 2]
        ctl = (me // 30) * 30
        niv = np.where(e > 0, href[s_] * (1 + sigma[s_, ctl]), bref[s_] * (1 - sigma[s_, ctl]))
        au_dela = (e * (t[:, 3] - niv) * ech[s_])[an[s_] >= 2023].mean()
        t = ST._avec_stop(d["o"], d["h"], d["l"], d["c"], t, niv, dist, float(d["tick"]))
        Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in t])
        g = Zc[:, -1]
        ts = [g[jo & (an >= a0) & (an <= a1)] for a0, a1 in ((2011, 2022), (2023, 2026))]
        ts = [x.mean() / x.std(ddof=1) * np.sqrt(len(x)) for x in ts]
        r = SB._depuis(Zc, Zw, zero, zero, fed, dep13, 13, 4.0, 6.0, 0.0, 49500.0, 51000.0, 1000.0)
        lu, _ = LU._lucid(Zc, Zw, fed, depl, 2.0, 1000.0, 252)
        x = pd.Series(np.where(jo, np.where((4 * Zw <= -1000).any(axis=1), -1000.0, 4 * Zc[:, -1]), 0.0), index=jours)
        tr = x[(x != 0) & (x.index >= "2023-01-01")]
        L.append(f"{nom:<34} {len(t):>6} {(tr > 0).mean():>8.0%} {au_dela:>6.1f}p {ts[0]:>+8.2f} {ts[1]:>+8.2f} "
                 f"{x[x.index >= '2023-01-01'].sum():>+9,.0f} {x[x.index.year == 2026].sum():>+8,.0f} {(r == 1).mean():>8.1%} {(lu == 1).mean():>11.1%}")
    L += ["", "(gagnants : journees avec trade 2023-2026 ; au-dela : entree au-dela du niveau, points moyens 2023-2026 ; t des gains "
          "quotidiens, jours sans Fed ; Bulenox : 49 500 $, marge 1 000 $, 13 seances, 4 puis 6 MNQ ; Lucid : LucidFlex 50K sans "
          "limite de temps, 2 MNQ, departs 2012 - sept. 2025)"]
    (J.SORTIE / "confirmation_27oct.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
