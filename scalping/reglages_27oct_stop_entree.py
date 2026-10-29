#!/usr/bin/env python3
"""Descriptif (27 octobre 2026) : (1) de combien le prix d'entree depasse le niveau casse dans la configuration installee ;
(2) stop a 70 points du niveau casse (installe) contre stop a 70 points du prix d'entree, gains laisses jusqu'a 16 h, limite du
jour 1 000 $. Points ramenes au prix de chaque jour (x ouverture / 30 900). Ecrit resultats/j/reglages_27oct_stop_entree.txt.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/reglages_27oct_stop_entree.py"""
import os

import numpy as np
import pandas as pd

import challenge_ajouts as CA
import donnees as D
import partie_e as E
import partie_g as G
import partie_j as J
import reglages_27oct_sans_sortie as SS
import reglages_27oct_stop as ST
import situation_bulenox as SB


def main():
    d = D.minutes("NQ", chemin=os.environ["MINUTES"], debut="2011-01-01")
    S = d["c"].shape[0]
    sigma, vwap, href, bref, jouable = G.zone_tableaux(d)
    fed = np.isin(d["jours"], E.fomc())
    an = d["jours"].astype("datetime64[Y]").astype(int) + 1970
    jo = jouable & ~fed
    jours = pd.to_datetime(d["jours"])
    tick = float(d["tick"])
    ech = float(d["pref"]) / d["o"][:, 0]
    dep = np.flatnonzero(d["jours"] >= np.datetime64("2012-01-01"))
    dep13 = dep[dep <= S - 13]
    zero = np.zeros_like(d["c"])
    base = SS._zone_ss(d["c"], d["v"], sigma, href, bref, jouable, 1.0, 5)
    s_, me, e = base[:, 0].astype(int), base[:, 1].astype(int), base[:, 2]
    ctl = (me // 30) * 30
    niv = np.where(e > 0, href[s_] * (1 + sigma[s_, ctl]), bref[s_] * (1 - sigma[s_, ctl]))
    ecart = e * (base[:, 3] - niv) * ech[s_]                     # points au-dela du niveau, au prix d'aujourd'hui
    r23 = an[s_] >= 2023
    q = np.percentile(ecart[r23], [50, 75, 90])
    L = ["(1) Entree au-dela du niveau casse, 2023 - 2026 (points au prix d'aujourd'hui ; 1 point = 8 $ en 4 MNQ) :",
         f"  moyenne {ecart[r23].mean():.1f} points, mediane {q[0]:.1f}, 3 entrees sur 4 a moins de {q[1]:.1f}, 9 sur 10 a moins de {q[2]:.1f}, "
         f"maximum {ecart[r23].max():.1f} ; entrees a plus de 20 points : {(ecart[r23] > 20).mean():.0%}, a plus de 40 points : {(ecart[r23] > 40).mean():.0%}",
         "", "(2) Stop a 70 points : du niveau casse (installe) ou du prix d'entree, 4 MNQ :"]
    dist = 70.0 * d["o"][:, 0] / float(d["pref"])
    jeux = {"stop niveau casse +/- 70 (installe)": ST._avec_stop(d["o"], d["h"], d["l"], d["c"], base, niv, dist, tick),
            "stop prix d'entree +/- 70": ST._avec_stop(d["o"], d["h"], d["l"], d["c"], base, base[:, 3], dist, tick)}
    for nom, t in jeux.items():
        pts = t[:, 2] * (t[:, 5] - t[:, 3]) - float(d["frais"]) / float(d["pt"])
        pu = pts * 8 * ech[t[:, 0].astype(int)]
        stp = t[:, 6] == 2
        Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in t])
        g = Zc[:, -1]
        ts = [g[jo & (an >= a0) & (an <= a1)] for a0, a1 in ((2011, 2022), (2023, 2026))]
        ts = [x.mean() / x.std(ddof=1) * np.sqrt(len(x)) for x in ts]
        r = SB._depuis(Zc, Zw, zero, zero, fed, dep13, 13, 4.0, 6.0, 0.0, 49500.0, 51000.0, 1000.0)
        x = pd.Series(np.where(jo, np.where((4 * Zw <= -1000).any(axis=1), -1000.0, 4 * Zc[:, -1]), 0.0), index=jours)
        tr = x[(x != 0) & (x.index >= "2023-01-01")]
        L += [f"  {nom} : stoppes {stp.mean():.0%} ; perte au stop (2023-2026) moyenne {pu[r23 & stp].mean():+,.0f} $, mediane "
              f"{np.median(pu[r23 & stp]):+,.0f} $, pire {pu[r23 & stp].min():+,.0f} $",
              f"    2023-2026 : jours gagnants {(tr > 0).mean():.0%}, gain moyen {tr[tr > 0].mean():+,.0f} $, perte moyenne {tr[tr < 0].mean():+,.0f} $, "
              f"jours a -1 000 $ {(tr <= -1000).mean():.0%} ; t {ts[0]:+.2f} / {ts[1]:+.2f}",
              f"    total 2011-2026 {x.sum():+,.0f} $, depuis 2023 {x[x.index >= '2023-01-01'].sum():+,.0f} $, 2026 {x[x.index.year == 2026].sum():+,.0f} $, "
              f"avril-octobre 2026 {x[x.index >= '2026-04-01'].sum():+,.0f} $ ; challenge marge 1 000 $ : valide {(r == 1).mean():.1%} perdu {(r == -1).mean():.1%}"]
    # exemples d'octobre 2026, les deux stops
    h = lambda m: f"{(570 + int(m)) // 60}h{(570 + int(m)) % 60:02d}"
    L += ["", "Octobre 2026 (heure de New York, 4 MNQ) : entree, niveau casse, stop niveau / stop entree -> resultat"]
    a_, b_ = jeux["stop niveau casse +/- 70 (installe)"], jeux["stop prix d'entree +/- 70"]
    for i in np.flatnonzero(d["jours"][s_] >= np.datetime64("2026-10-01")):
        res = []
        for t in (a_, b_):
            p = (t[i, 2] * (t[i, 5] - t[i, 3]) - 1.5) * 8 * ech[s_[i]]
            res.append(f"{'stop ' + h(t[i, 4]) if t[i, 6] == 2 else '16 h'} {p:+,.0f} $")
        L.append(f"  {d['jours'][s_[i]]} {'achat' if e[i] > 0 else 'vente'} {h(me[i])} a {base[i, 3]:.2f}, niveau {niv[i]:.2f} "
                 f"({ecart[i]:.0f} pts au-dela), stops {niv[i] - e[i] * dist[s_[i]]:.2f} / {base[i, 3] - e[i] * dist[s_[i]]:.2f} : "
                 f"{res[0]}  |  {res[1]}")
    (J.SORTIE / "reglages_27oct_stop_entree.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
