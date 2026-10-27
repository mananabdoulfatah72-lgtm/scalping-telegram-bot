#!/usr/bin/env python3
"""Descriptif (27 octobre 2026) : ce que Q1 (sens de l'ouverture) et Q2 (tendance de fond) apportent a la version installee
(cassure + volume x1 + fenetre 5 min, une entree par seance, pas de sortie aux controles, stop a 70 points du niveau casse,
16 h, limite du jour 1 000 $). Les entrees viennent de partie_q._zone_q (une entree par seance : elles ne dependent pas des
sorties). Ecrit resultats/j/reglages_27oct_q12_stop.txt.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/reglages_27oct_q12_stop.py"""
import os

import numpy as np
import pandas as pd

import challenge_ajouts as CA
import donnees as D
import partie_e as E
import partie_g as G
import partie_j as J
import partie_q as PQ
import reglages_27oct_sans_sortie as SS
import reglages_27oct_stop as ST
import situation_bulenox as SB


def main():
    d = D.minutes("NQ", chemin=os.environ["MINUTES"], debut="2011-01-01")
    S, N = d["c"].shape
    sigma, vwap, href, bref, jouable = G.zone_tableaux(d)
    tend = PQ.tendance(d)
    fed = np.isin(d["jours"], E.fomc())
    an = d["jours"].astype("datetime64[Y]").astype(int) + 1970
    jo = jouable & ~fed
    jours = pd.to_datetime(d["jours"])
    ech = float(d["pref"]) / d["o"][:, 0]
    dep = np.flatnonzero(d["jours"] >= np.datetime64("2012-01-01"))
    dep13 = dep[dep <= S - 13]
    zero = np.zeros_like(d["c"])
    dist = 70.0 * d["o"][:, 0] / float(d["pref"])
    ref = SS._zone_ss(d["c"], d["v"], sigma, href, bref, jouable, 1.0, 5)
    L = ["Version installee (stop 70 points du niveau, pas de sortie aux controles), 4 MNQ, prix d'aujourd'hui, limite du jour 1 000 $", "",
         f"{'filtre':<22} {'trades':>6} {'par an':>6} {'gagnants':>8} {'gain moy':>9} {'perte moy':>9} {'j. -1000$':>9} {'t 11-22':>8} {'t 23-26':>8} "
         f"{'15 ans':>9} {'2023-26':>9} {'2025':>8} {'2026':>8} {'valide':>7} {'perdu':>6} {'expire':>7}"]
    for f, nom in ((0, "aucun (installee)"), (1, "Q1 sens de l'ouverture"), (2, "Q2 tendance de fond"), (7, "Q1 + Q2")):
        t = PQ._zone_q(d["o"], d["h"], d["l"], d["c"], d["v"], sigma, vwap, href, bref, tend, jouable, 1.0, 5, f).copy()
        t[:, 4], t[:, 5], t[:, 6] = N - 1, d["c"][t[:, 0].astype(int), N - 1], 0
        if f == 0:
            assert np.array_equal(t[:, :4], ref[:, :4])
        s_, me, e = t[:, 0].astype(int), t[:, 1].astype(int), t[:, 2]
        ctl = (me // 30) * 30
        niv = np.where(e > 0, href[s_] * (1 + sigma[s_, ctl]), bref[s_] * (1 - sigma[s_, ctl]))
        t = ST._avec_stop(d["o"], d["h"], d["l"], d["c"], t, niv, dist, float(d["tick"]))
        Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in t])
        g = Zc[:, -1]
        ts = [g[jo & (an >= a0) & (an <= a1)] for a0, a1 in ((2011, 2022), (2023, 2026))]
        ts = [x.mean() / x.std(ddof=1) * np.sqrt(len(x)) for x in ts]
        r = SB._depuis(Zc, Zw, zero, zero, fed, dep13, 13, 4.0, 6.0, 0.0, 49500.0, 51000.0, 1000.0)
        x = pd.Series(np.where(jo, np.where((4 * Zw <= -1000).any(axis=1), -1000.0, 4 * Zc[:, -1]), 0.0), index=jours)
        tr = x[(x != 0) & (x.index >= "2023-01-01")]
        L.append(f"{nom:<22} {len(t):>6} {len(t) / 15.8:>6.0f} {(tr > 0).mean():>8.0%} {tr[tr > 0].mean():>+9,.0f} {tr[tr < 0].mean():>+9,.0f} "
                 f"{int((Zw[jo].min(axis=1) <= -250).sum()):>9} {ts[0]:>+8.2f} {ts[1]:>+8.2f} {x.sum():>+9,.0f} "
                 f"{x[x.index >= '2023-01-01'].sum():>+9,.0f} {x[x.index.year == 2025].sum():>+8,.0f} {x[x.index.year == 2026].sum():>+8,.0f} "
                 f"{(r == 1).mean():>7.1%} {(r == -1).mean():>6.1%} {(r == 0).mean():>7.1%}")
    L += ["", "(gagnants, gain et perte moyens : journees avec trade de 2023-2026 ; j. -1000$ : 15 ans ; challenge : 49 500 $, marge "
          "1 000 $, 13 seances, 4 puis 6 MNQ, departs 2012-2026)"]
    (J.SORTIE / "reglages_27oct_q12_stop.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
