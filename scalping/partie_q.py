#!/usr/bin/env python3
"""Partie Q (README.md) : la configuration installee (reglages_26oct_g.py) avec un filtre de plus sur la minute qui confirme
l'entree : Q1 ecart d'ouverture, Q2 tendance de fond (veille contre moyenne de 20 clotures), Q3 VWAP, Q4 bougie de force,
Q5 pas trop loin du niveau, Q6 matin. Decision fixee dans le README. Ecrit resultats/j/partie_q.txt.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/partie_q.py"""
import os

import numpy as np
import pandas as pd
from numba import njit

import challenge_ajouts as CA
import donnees as D
import partie_e as E
import partie_g as G
import partie_j as J
import reglages_26oct_g as RG
import situation_bulenox as SB

NOMS = {0: "installee (aucun filtre)", 1: "Q1 ecart d'ouverture", 2: "Q2 tendance de fond", 3: "Q3 VWAP", 4: "Q4 bougie de force",
        5: "Q5 pas trop loin", 6: "Q6 matin (avant 12 h)"}


@njit(cache=True)
def _zone_q(O, H, L, C, V, sigma, vwap, href, bref, tend, jouable, kvol, W, filtre):
    S, N = C.shape
    tr = np.zeros((S, 8))
    nt = 0
    for s in range(S):
        if not jouable[s]:
            continue
        pos, me, px, niveau, fait = 0, -1, 0.0, np.nan, False
        ub, lb, sg = np.nan, np.nan, np.nan
        fin, sf = -1, 0
        for m in range(30, N):
            p = C[s, m]
            if m == N - 1:
                if pos != 0:
                    J._ecrit(tr, nt, s, me, pos, px, m, p, 0, 0.0)
                    nt += 1
                break
            if m % 30 == 0:
                sg = sigma[s, m]
                ub, lb = href[s] * (1 + sg), bref[s] * (1 - sg)
                if pos != 0 and pos * (p - niveau) <= 0:
                    J._ecrit(tr, nt, s, me, pos, px, m, p, 0, 0.0)
                    nt += 1
                    pos = 0
            if pos == 0 and not fait and m <= 360:
                q = C[s, m - 1]
                e = 1 if p > ub else (-1 if p < lb else 0)
                if e == 0:
                    fin = -1
                else:
                    if (e > 0 and q <= ub) or (e < 0 and q >= lb):
                        fin, sf = m + W, e
                    ok = sf == e and m <= fin and V[s, m] >= kvol * V[s, m - 30:m].sum() / 30.0
                    if ok and filtre == 1:
                        ok = (O[s, 0] >= href[s]) if e > 0 else (O[s, 0] <= bref[s])
                    elif ok and filtre == 2:
                        ok = tend[s] == e
                    elif ok and filtre == 3:
                        ok = (p > vwap[s, m]) if e > 0 else (p < vwap[s, m])
                    elif ok and filtre == 4:
                        rg = H[s, m] - L[s, m]
                        ok = (p - L[s, m] >= 2.0 / 3.0 * rg) if e > 0 else (H[s, m] - p >= 2.0 / 3.0 * rg)
                    elif ok and filtre == 5:
                        ok = e * (p - (ub if e > 0 else lb)) <= 0.25 * (href[s] if e > 0 else bref[s]) * sg
                    elif ok and filtre == 6:
                        ok = m <= 150
                    if ok:
                        pos, me, px, fait = e, m, p, True
                        niveau = ub if e > 0 else lb
    return tr[:nt]


def tendance(d):
    """+1 si la cloture de la derniere seance complete est au-dessus de la moyenne des 20 dernieres clotures completes, -1 sinon,
    0 si moins de 20 seances."""
    C, ok = d["c"], d["complete"]
    idx = np.flatnonzero(ok)
    t = np.zeros(len(ok), np.int64)
    for s in range(len(ok)):
        n = int(np.searchsorted(idx, s))
        if n >= 20:
            cl = C[idx[n - 20:n], -1]
            t[s] = 1 if cl[-1] > cl.mean() else -1
    return t


def main():
    d = D.minutes("NQ", chemin=os.environ["MINUTES"], debut="2011-01-01")
    S = d["c"].shape[0]
    sigma, vwap, href, bref, jouable = G.zone_tableaux(d)
    tend = tendance(d)
    fed = np.isin(d["jours"], E.fomc())
    an = d["jours"].astype("datetime64[Y]").astype(int) + 1970
    jo = jouable & ~fed
    jours = pd.to_datetime(d["jours"])
    dep = np.flatnonzero(d["jours"] >= np.datetime64("2012-01-01"))
    dep13 = dep[dep <= S - 13]
    zero = np.zeros_like(d["c"])
    base = RG._zone_fw(d["c"], d["v"], sigma, href, bref, jouable, 1.0, 5, 30)
    res = {}
    for f, nom in NOMS.items():
        t = _zone_q(d["o"], d["h"], d["l"], d["c"], d["v"], sigma, vwap, href, bref, tend, jouable, 1.0, 5, f)
        if f == 0:
            controle = np.array_equal(t, base)
        pts = t[:, 2] * (t[:, 5] - t[:, 3]) - float(d["frais"]) / float(d["pt"])
        Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in t])
        g = Zc[:, -1]
        ts = [g[jo & (an >= a0) & (an <= a1)] for a0, a1 in ((2011, 2022), (2023, 2026))]
        ts = [x.mean() / x.std(ddof=1) * np.sqrt(len(x)) for x in ts]
        r = SB._depuis(Zc, Zw, zero, zero, fed, dep13, 13, 4.0, 6.0, 0.0, 49500.0, 51000.0, 1000.0)
        x = pd.Series(np.where(jo, np.where((4 * Zw <= -1000).any(axis=1), -1000.0, 4 * Zc[:, -1]), 0.0), index=jours)
        res[nom] = dict(n=len(t), pts=pts.sum(), g=(pts > 0).mean(), t1=ts[0], t2=ts[1], j=int((Zw[jo].min(axis=1) <= -250).sum()),
                        v=(r == 1).mean(), p=(r == -1).mean(), a23=x[x.index >= "2023-01-01"].sum(), a26=x[x.index.year == 2026].sum())
    b = res[NOMS[0]]
    L = [f"Minutes du NQ : {d['jours'][0]} - {d['jours'][-1]}. Controle : sans filtre = reglages_26oct_g : {'oui' if controle else 'NON'}.", "",
         f"{'filtre':<26} {'trades':>6} {'points':>7} {'gagn.':>6} {'t 11-22':>8} {'t 23-26':>8} {'j. -1000$':>9} {'valide':>7} {'perdu':>6} "
         f"{'2023-26 4MNQ':>13} {'2026 4MNQ':>10}  decision"]
    for nom, r in res.items():
        passe = r["t1"] > b["t1"] and r["t2"] > b["t2"] and r["v"] >= b["v"]
        L.append(f"{nom:<26} {r['n']:>6} {r['pts']:>+7.0f} {r['g']:>6.0%} {r['t1']:>+8.2f} {r['t2']:>+8.2f} {r['j']:>9} {r['v']:>7.1%} "
                 f"{r['p']:>6.1%} {r['a23']:>+13,.0f} {r['a26']:>+10,.0f}  {'-' if nom == NOMS[0] else ('PASSE' if passe else 'non')}")
    L += ["", "(t des gains quotidiens, jours sans Fed ; j. -1000$ = journees a -1 000 $ en 4 MNQ sur 15 ans ; challenge : 49 500 $, marge "
          "1 000 $, 13 seances, 4 puis 6 MNQ, departs 2012-2026 ; $ en 4 MNQ au prix d'aujourd'hui, limite du jour 1 000 $)"]
    (J.SORTIE / "partie_q.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
