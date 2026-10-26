#!/usr/bin/env python3
"""Q1, Q2 et Q1 + Q2 ajoutes a la configuration installee (partie Q), descriptif. Q1 + Q2 n'etait pas dans les regles fixees
de la partie Q : mesure apres coup, a la demande de l'utilisateur. Ecrit resultats/j/reglages_27oct_q12.txt et les trades
(reference du rejeu C# Q1=1 / Q2=1).
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/reglages_27oct_q12.py"""
import os

import numpy as np
import pandas as pd

import challenge_ajouts as CA
import donnees as D
import partie_e as E
import partie_g as G
import partie_j as J
import partie_q as PQ
import situation_bulenox as SB


def main():
    d = D.minutes("NQ", chemin=os.environ["MINUTES"], debut="2011-01-01")
    S = d["c"].shape[0]
    sigma, vwap, href, bref, jouable = G.zone_tableaux(d)
    tend = PQ.tendance(d)
    fed = np.isin(d["jours"], E.fomc())
    an = d["jours"].astype("datetime64[Y]").astype(int) + 1970
    jo = jouable & ~fed
    jours = pd.to_datetime(d["jours"])
    dep = np.flatnonzero(d["jours"] >= np.datetime64("2012-01-01"))
    dep13, dep21 = dep[dep <= S - 13], dep[dep <= S - 21]
    zero = np.zeros_like(d["c"])
    L = [f"Minutes du NQ : {d['jours'][0]} - {d['jours'][-1]}.", "",
         f"{'configuration':<26} {'trades':>6} {'gagn.':>6} {'t 11-22':>8} {'t 23-26':>8} {'j. -1000$':>9} {'valide':>7} {'perdu':>6} "
         f"{'expire':>7} {'neuf 21 s.':>10} " + " ".join(f"{y:>9}" for y in range(2018, 2027))]
    for f, nom in ((0, "installee"), (1, "+ Q1"), (2, "+ Q2"), (7, "+ Q1 + Q2")):
        t = PQ._zone_q(d["o"], d["h"], d["l"], d["c"], d["v"], sigma, vwap, href, bref, tend, jouable, 1.0, 5, f)
        pts = t[:, 2] * (t[:, 5] - t[:, 3]) - float(d["frais"]) / float(d["pt"])
        Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in t])
        g = Zc[:, -1]
        ts = [g[jo & (an >= a0) & (an <= a1)] for a0, a1 in ((2011, 2022), (2023, 2026))]
        ts = [x.mean() / x.std(ddof=1) * np.sqrt(len(x)) for x in ts]
        r = SB._depuis(Zc, Zw, zero, zero, fed, dep13, 13, 4.0, 6.0, 0.0, 49500.0, 51000.0, 1000.0)
        r21 = SB._depuis(Zc, Zw, zero, zero, fed, dep21, 21, 4.0, 6.0, 0.0, 50000.0, 50000.0, 1000.0)
        x = pd.Series(np.where(jo, np.where((4 * Zw <= -1000).any(axis=1), -1000.0, 4 * Zc[:, -1]), 0.0), index=jours)
        L.append(f"{nom:<26} {len(t):>6} {(pts > 0).mean():>6.0%} {ts[0]:>+8.2f} {ts[1]:>+8.2f} {int((Zw[jo].min(axis=1) <= -250).sum()):>9} "
                 f"{(r == 1).mean():>7.1%} {(r == -1).mean():>6.1%} {(r == 0).mean():>7.1%} {(r21 == 1).mean():>10.1%} "
                 + " ".join(f"{x[x.index.year == y].sum():>+9,.0f}" for y in range(2018, 2027)))
        if f:
            pd.DataFrame({"jour": d["jours"][t[:, 0].astype(int)].astype(str), "minute_entree": t[:, 1].astype(int),
                          "sens": t[:, 2].astype(int), "prix_entree": t[:, 3], "minute_sortie": t[:, 4].astype(int),
                          "prix_sortie": t[:, 5], "points": pts}).to_csv(J.SORTIE / f"reglages_27oct_q{f}_trades.csv", index=False)
    L += ["", "(t des gains quotidiens, jours sans Fed ; j. -1000$ = journees a -1 000 $ en 4 MNQ sur 15 ans ; challenge : 49 500 $, marge "
          "1 000 $, 13 seances, 4 puis 6 MNQ, departs 2012-2026 ; neuf 21 s. = challenge neuf de 21 seances ; $ par an en 4 MNQ au prix "
          "d'aujourd'hui, limite du jour 1 000 $)"]
    (J.SORTIE / "reglages_27oct_q12.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
