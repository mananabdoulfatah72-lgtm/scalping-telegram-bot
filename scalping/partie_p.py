#!/usr/bin/env python3
"""Partie P (README.md) : L1a avec un vrai stop pose a l'entree, en % du prix d'entree ou sous le niveau casse avec une
marge (fraction de la largeur de la zone). Choix du stop sur le t de 2011-2022, jugement sur 2023-2026 et dans le
challenge. Ecrit resultats/j/partie_p.txt.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/partie_p.py"""
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
import situation_bulenox as SB

# nom : (mode 0 aucun / 1 % du prix / 2 marge sous le niveau, parametre)
CANDIDATS = {"aucun stop (L1a)": (0, 0.0), "stop 0,10 %": (1, 0.0010), "stop 0,15 %": (1, 0.0015), "stop 0,20 %": (1, 0.0020),
             "stop 0,30 %": (1, 0.0030), "stop 0,40 %": (1, 0.0040), "niveau - 0,25 largeur": (2, 0.25),
             "niveau - 0,5 largeur": (2, 0.5), "niveau - 1 largeur": (2, 1.0)}


@njit(cache=True)
def _zone_p(O, H, L, C, sigma, href, bref, jouable, mode, param, tick):
    S, N = C.shape
    tr = np.zeros((S * 2, 8))
    nt = 0
    for s in range(S):
        if not jouable[s]:
            continue
        pos, me, px, niveau, stop, fait = 0, -1, 0.0, np.nan, np.nan, False
        ub, lb, sg = np.nan, np.nan, np.nan
        for m in range(30, N):
            p = C[s, m]
            if pos != 0 and m > me and not np.isnan(stop) and ((pos > 0 and L[s, m] <= stop) or (pos < 0 and H[s, m] >= stop)):
                x = (min(O[s, m], stop) - tick) if pos > 0 else (max(O[s, m], stop) + tick)
                J._ecrit(tr, nt, s, me, pos, px, m, x, 2, 0.0)
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
                if pos != 0 and ((pos > 0 and p <= niveau) or (pos < 0 and p >= niveau)):
                    J._ecrit(tr, nt, s, me, pos, px, m, p, 0, 0.0)
                    nt += 1
                    pos = 0
                if pos == 0 and not fait and m <= 360:
                    entre = 1 if p > ub else (-1 if p < lb else 0)
            elif pos == 0 and not fait and m < 360:
                entre = 1 if p > ub else (-1 if p < lb else 0)
            if entre != 0:
                pos, me, px, fait = entre, m, p, True
                niveau = ub if entre > 0 else lb
                if mode == 1:
                    stop = px - entre * param * px
                elif mode == 2:
                    stop = niveau - entre * param * (href[s] if entre > 0 else bref[s]) * sg
                else:
                    stop = np.nan
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
    dep13_23 = dep13[d["jours"][dep13] >= np.datetime64("2023-01-01")]
    zero = np.zeros_like(d["c"])
    jeux = {nom: _zone_p(d["o"], d["h"], d["l"], d["c"], sigma, href, bref, jouable, mo, pa, tick) for nom, (mo, pa) in CANDIDATS.items()}
    controle = np.array_equal(jeux["aucun stop (L1a)"], PM._zone_m(d["c"], d["v"], sigma, href, bref, jouable, 1, 0.0))
    res = {}
    for nom, t in jeux.items():
        pts = t[:, 2] * (t[:, 5] - t[:, 3]) - float(d["frais"]) / float(d["pt"])
        pa = pts * ech[t[:, 0].astype(int)]
        Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in t])
        g = Zc[:, -1]
        ts = []
        for a0, a1 in ((2011, 2022), (2023, 2026)):
            x = g[jo & (an >= a0) & (an <= a1)]
            ts.append(x.mean() / x.std(ddof=1) * np.sqrt(len(x)))
        ta = an[t[:, 0].astype(int)]
        r23 = ta >= 2023
        ch = [SB._depuis(Zc, Zw, zero, zero, fed, x, 13, 4.0, 6.0, 0.0, 49500.0, 51000.0, 1000.0) for x in (dep13, dep13_23)]
        j4 = np.where(jo, np.where((4 * Zw <= -1000).any(axis=1), -1000.0, 4 * Zc[:, -1]), 0.0)
        x26 = pd.Series(j4, index=jours)
        res[nom] = dict(t1=ts[0], t2=ts[1], pts=pts.sum(), gagn=(pts > 0).mean(), perte=pa[r23 & (pa < 0)].mean(),
                        pire=pa[r23].min(), stop=(t[:, 6] == 2).mean(), j1000=int((Zw[jo].min(axis=1) <= -250).sum()),
                        v=(ch[0] == 1).mean(), p=(ch[0] == -1).mean(), e=(ch[0] == 0).mean(), v23=(ch[1] == 1).mean(),
                        a26=x26[x26.index >= "2026-01-01"].sum(), m7=x26[x26.index >= "2026-04-01"].sum())
    choix = max((n for n in res), key=lambda n: res[n]["t1"])
    L = [f"Minutes du NQ : {d['jours'][0]} - {d['jours'][-1]}. Controle : aucun stop = L1a de partie_m : {'oui' if controle else 'NON'}.",
         f"Stop choisi sur 2011-2022 (meilleur t) : {choix}", "",
         f"{'candidat':<24} {'t 11-22':>8} {'t 23-26':>8} {'points':>7} {'gagn.':>6} {'stoppes':>8} {'perte moy':>9} {'pire':>6} "
         f"{'j. -1000$':>9} {'valide':>7} {'perdu':>6} {'expire':>7} {'valide 23-26':>12} {'2026 4MNQ':>10} {'avr-oct':>8}"]
    for n, r in res.items():
        L.append(f"{n:<24} {r['t1']:>+8.2f} {r['t2']:>+8.2f} {r['pts']:>+7.0f} {r['gagn']:>6.0%} {r['stop']:>8.0%} {r['perte']:>+9.1f} "
                 f"{r['pire']:>+6.0f} {r['j1000']:>9} {r['v']:>7.1%} {r['p']:>6.1%} {r['e']:>7.1%} {r['v23']:>12.1%} "
                 f"{r['a26']:>+10,.0f} {r['m7']:>+8,.0f}")
    L += ["", "(t des gains quotidiens, jours sans Fed ; points bruts 1 MNQ frais deduits ; perte moyenne et pire trade : 2023-2026, "
          "points au prix d'aujourd'hui ; j. -1000$ = journees a -1 000 $ en 4 MNQ sur 15 ans ; challenge : 49 500 $, marge "
          "1 000 $, 13 seances, 4 puis 6 MNQ, limite du jour 1 000 $ ; 2026 et avril-octobre : $ en 4 MNQ au prix d'aujourd'hui)"]
    (J.SORTIE / "partie_p.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
