#!/usr/bin/env python3
"""Configuration choisie par l'utilisateur le 26 octobre 2026 (descriptif, apres les parties J a P) : entree a la cassure
confirmee par le volume (x2, partie M), une entree par seance (laisser courir, partie L), sortie des qu'une minute cloture
de l'autre cote du niveau casse (partie N, N1), sinon 16 h. Comparee a N1 sans volume, a L1a et au bot d'avant. Sert aussi
de reference au rejeu C# (Bot3en1.Replay). Ecrit resultats/j/reglages_26oct.txt et resultats/j/reglages_26oct_trades.csv.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/reglages_26oct.py"""
import os

import numpy as np
import pandas as pd
from numba import njit

import challenge_ajouts as CA
import donnees as D
import partie_e as E
import partie_g as G
import partie_j as J
import partie_m as PM
import partie_n as PN
import situation_bulenox as SB


@njit(cache=True)
def _zone_final(C, V, sigma, href, bref, jouable, kvol):
    S, N = C.shape
    tr = np.zeros((S * 2, 8))
    nt = 0
    for s in range(S):
        if not jouable[s]:
            continue
        pos, me, px, niveau, fait = 0, -1, 0.0, np.nan, False
        ub, lb = np.nan, np.nan
        for m in range(30, N):
            p = C[s, m]
            if pos != 0 and m > me and pos * (p - niveau) <= 0:
                J._ecrit(tr, nt, s, me, pos, px, m, p, 2, 0.0)
                nt += 1
                pos = 0
            if m == N - 1:
                if pos != 0:
                    J._ecrit(tr, nt, s, me, pos, px, m, p, 0, 0.0)
                    nt += 1
                break
            entre = 0
            if m % 30 == 0:
                sg = sigma[s, m]
                ub, lb = href[s] * (1 + sg), bref[s] * (1 - sg)
                if pos == 0 and not fait and m <= 360:
                    entre = 1 if p > ub else (-1 if p < lb else 0)
            elif pos == 0 and not fait and m < 360:
                entre = 1 if p > ub else (-1 if p < lb else 0)
                if entre != 0 and kvol > 0 and V[s, m] < kvol * V[s, m - 30:m].sum() / 30.0:
                    entre = 0
            if entre != 0:
                pos, me, px, fait = entre, m, p, True
                niveau = ub if entre > 0 else lb
    return tr[:nt]


def main():
    d = D.minutes("NQ", chemin=os.environ["MINUTES"], debut="2011-01-01")
    S = d["c"].shape[0]
    sigma, vwap, href, bref, jouable = G.zone_tableaux(d)
    a = (d["o"], d["h"], d["l"], d["c"], sigma, vwap, href, bref, jouable)
    tick = float(d["tick"])
    fed = np.isin(d["jours"], E.fomc())
    an = d["jours"].astype("datetime64[Y]").astype(int) + 1970
    jo = jouable & ~fed
    jours = pd.to_datetime(d["jours"])
    ech = float(d["pref"]) / d["o"][:, 0]
    dep = np.flatnonzero(d["jours"] >= np.datetime64("2012-01-01"))
    dep13 = dep[dep <= S - 13]
    zero = np.zeros_like(d["c"])
    n1 = PN._zone_n(d["o"], d["h"], d["l"], d["c"], sigma, href, bref, jouable, 1, tick)
    jeux = {"bot d'avant (controles seuls)": J._zone_j(*a, False, 0.0, False, tick, 0),
            "L1a laisser courir": PM._zone_m(d["c"], d["v"], sigma, href, bref, jouable, 1, 0.0),
            "N1 sortie immediate": _zone_final(d["c"], d["v"], sigma, href, bref, jouable, 0.0),
            "CHOIX : N1 + volume x2": _zone_final(d["c"], d["v"], sigma, href, bref, jouable, 2.0)}
    controle = np.array_equal(jeux["N1 sortie immediate"][:, [0, 1, 2, 3, 4, 5]], n1[:, [0, 1, 2, 3, 4, 5]])
    L = [f"Minutes du NQ : {d['jours'][0]} - {d['jours'][-1]}. Controle : N1 recalcule = N1 de partie_n : {'oui' if controle else 'NON'}.", "",
         f"{'configuration':<30} {'trades':>6} {'points':>7} {'gagn.':>6} {'gain moy':>8} {'perte moy':>9} {'t 11-22':>8} {'t 23-26':>8} "
         f"{'j. -1000$':>9} {'valide':>7} {'perdu':>6} {'expire':>7} {'2025 4MNQ':>10} {'2026 4MNQ':>10} {'avr-oct':>8}"]
    mois = []
    for nom, t in jeux.items():
        pts = t[:, 2] * (t[:, 5] - t[:, 3]) - float(d["frais"]) / float(d["pt"])
        pa = pts * ech[t[:, 0].astype(int)]
        r23 = an[t[:, 0].astype(int)] >= 2023
        Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in t])
        g = Zc[:, -1]
        ts = [g[jo & (an >= a0) & (an <= a1)] for a0, a1 in ((2011, 2022), (2023, 2026))]
        ts = [x.mean() / x.std(ddof=1) * np.sqrt(len(x)) for x in ts]
        r = SB._depuis(Zc, Zw, zero, zero, fed, dep13, 13, 4.0, 6.0, 0.0, 49500.0, 51000.0, 1000.0)
        x = pd.Series(np.where(jo, np.where((4 * Zw <= -1000).any(axis=1), -1000.0, 4 * Zc[:, -1]), 0.0), index=jours)
        L.append(f"{nom:<30} {len(t):>6} {pts.sum():>+7.0f} {(pts > 0).mean():>6.0%} {pa[r23 & (pa > 0)].mean():>+8.1f} "
                 f"{pa[r23 & (pa < 0)].mean():>+9.1f} {ts[0]:>+8.2f} {ts[1]:>+8.2f} {int((Zw[jo].min(axis=1) <= -250).sum()):>9} "
                 f"{(r == 1).mean():>7.1%} {(r == -1).mean():>6.1%} {(r == 0).mean():>7.1%} {x[x.index.year == 2025].sum():>+10,.0f} "
                 f"{x[x.index.year == 2026].sum():>+10,.0f} {x[x.index >= '2026-04-01'].sum():>+8,.0f}")
        y = x[x.index >= "2026-01-01"]
        mois.append(f"{nom:<30} " + " ".join(f"{str(p)[5:]}:{v:>+7,.0f}" for p, v in y.groupby(y.index.to_period("M")).sum().items()))
        if nom.startswith("CHOIX"):
            oc = x[(x.index >= "2026-10-01") & (x != 0)]
            octobre = " ".join(f"{i.day}:{v:+,.0f}" for i, v in oc.items())
            pd.DataFrame({"jour": d["jours"][t[:, 0].astype(int)].astype(str), "minute_entree": t[:, 1].astype(int),
                          "sens": t[:, 2].astype(int), "prix_entree": t[:, 3], "minute_sortie": t[:, 4].astype(int),
                          "prix_sortie": t[:, 5], "points": pts}).to_csv(J.SORTIE / "reglages_26oct_trades.csv", index=False)
    L += ["", "(points bruts 1 MNQ frais deduits ; gain et perte moyens : 2023-2026, points au prix d'aujourd'hui ; t des gains "
          "quotidiens, jours sans Fed ; j. -1000$ = journees a -1 000 $ en 4 MNQ sur 15 ans ; challenge : 49 500 $, marge 1 000 $, "
          "13 seances, 4 puis 6 MNQ, limite du jour 1 000 $ ; $ en 4 MNQ au prix d'aujourd'hui, limite du jour 1 000 $)", "",
          "2026 mois par mois, 4 MNQ :"] + mois + ["", f"Octobre 2026 jour par jour, configuration choisie, 4 MNQ : {octobre}"]
    (J.SORTIE / "reglages_26oct.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
