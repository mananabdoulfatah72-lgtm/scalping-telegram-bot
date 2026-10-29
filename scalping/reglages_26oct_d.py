#!/usr/bin/env python3
"""Version A2 (26 octobre 2026 au soir, demande de l'utilisateur ; descriptif) : la version A (reglages_26oct_b.py) sans entree
tardive. Une entree n'est prise qu'a la minute ou le prix franchit le niveau du dernier controle (cloture de la minute d'avant
encore du bon cote du niveau, celle-ci au-dela), avec un volume d'au moins 2 fois la moyenne des 30 minutes d'avant, aux
controles comme entre eux. Sorties d'origine (controles : limite ou VWAP ; 16 h), plusieurs trades possibles par seance.
Reference du rejeu C# (CASSURE=1 VOLUME=1 SANS_TARDIVE=1). Ecrit resultats/j/reglages_26oct_d.txt et _trades.csv.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/reglages_26oct_d.py"""
import os

import numpy as np
import pandas as pd
from numba import njit

import challenge_ajouts as CA
import donnees as D
import partie_e as E
import partie_g as G
import partie_j as J
import reglages_26oct_b as RB
import situation_bulenox as SB


@njit(cache=True)
def _zone_a2(C, V, sigma, vwap, href, bref, jouable, kvol):
    S, N = C.shape
    tr = np.zeros((S * 60, 8))
    nt = 0
    for s in range(S):
        if not jouable[s]:
            continue
        virt, me, px = 0, -1, 0.0
        ub, lb = np.nan, np.nan
        for m in range(30, N):
            p = C[s, m]
            if m == N - 1:
                if virt != 0:
                    J._ecrit(tr, nt, s, me, virt, px, m, p, 0, 0.0)
                    nt += 1
                break
            if m % 30 == 0:
                sg = sigma[s, m]
                ub, lb = href[s] * (1 + sg), bref[s] * (1 - sg)
                if virt != 0 and ((virt > 0 and p <= max(ub, vwap[s, m])) or (virt < 0 and p >= min(lb, vwap[s, m]))):
                    J._ecrit(tr, nt, s, me, virt, px, m, p, 0, 0.0)
                    nt += 1
                    virt = 0
            if virt == 0 and m <= 360:
                q = C[s, m - 1]
                e = 1 if (p > ub and q <= ub) else (-1 if (p < lb and q >= lb) else 0)
                if e != 0 and kvol > 0 and V[s, m] < kvol * V[s, m - 30:m].sum() / 30.0:
                    e = 0
                if e != 0:
                    virt, me, px = e, m, p
    return tr[:nt]


def main():
    d = D.minutes("NQ", chemin=os.environ["MINUTES"], debut="2011-01-01")
    S = d["c"].shape[0]
    sigma, vwap, href, bref, jouable = G.zone_tableaux(d)
    fed = np.isin(d["jours"], E.fomc())
    an = d["jours"].astype("datetime64[Y]").astype(int) + 1970
    jo = jouable & ~fed
    jours = pd.to_datetime(d["jours"])
    ech = float(d["pref"]) / d["o"][:, 0]
    dep = np.flatnonzero(d["jours"] >= np.datetime64("2012-01-01"))
    dep13, dep21 = dep[dep <= S - 13], dep[dep <= S - 21]
    zero = np.zeros_like(d["c"])
    arg = (d["c"], d["v"], sigma, vwap, href, bref, jouable)
    jeux = {"bot d'avant (controles seuls)": RB._zone_jv(*arg, False, 0.0), "A : cassure + volume": RB._zone_jv(*arg, True, 2.0),
            "A2 : A sans entree tardive": _zone_a2(*arg, 2.0), "A2 sans volume": _zone_a2(*arg, 0.0)}
    L = [f"Minutes du NQ : {d['jours'][0]} - {d['jours'][-1]}.", "",
         f"{'configuration':<30} {'trades':>6} {'points':>7} {'gagn.':>6} {'gain moy':>8} {'perte moy':>9} {'t 11-22':>8} {'t 23-26':>8} "
         f"{'j. -1000$':>9} {'valide':>7} {'perdu':>6} {'expire':>7} {'neuf 21 s.':>10} {'2025 4MNQ':>10} {'2026 4MNQ':>10} {'avr-oct':>8}"]
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
        r21 = SB._depuis(Zc, Zw, zero, zero, fed, dep21, 21, 4.0, 6.0, 0.0, 50000.0, 50000.0, 1000.0)
        x = pd.Series(np.where(jo, np.where((4 * Zw <= -1000).any(axis=1), -1000.0, 4 * Zc[:, -1]), 0.0), index=jours)
        L.append(f"{nom:<30} {len(t):>6} {pts.sum():>+7.0f} {(pts > 0).mean():>6.0%} {pa[r23 & (pa > 0)].mean():>+8.1f} "
                 f"{pa[r23 & (pa < 0)].mean():>+9.1f} {ts[0]:>+8.2f} {ts[1]:>+8.2f} {int((Zw[jo].min(axis=1) <= -250).sum()):>9} "
                 f"{(r == 1).mean():>7.1%} {(r == -1).mean():>6.1%} {(r == 0).mean():>7.1%} {(r21 == 1).mean():>10.1%} "
                 f"{x[x.index.year == 2025].sum():>+10,.0f} {x[x.index.year == 2026].sum():>+10,.0f} {x[x.index >= '2026-04-01'].sum():>+8,.0f}")
        y = x[x.index >= "2026-01-01"]
        mois.append(f"{nom:<30} " + " ".join(f"{str(p)[5:]}:{v:>+7,.0f}" for p, v in y.groupby(y.index.to_period("M")).sum().items()))
        if nom.startswith("A2 :"):
            oc = x[(x.index >= "2026-10-01") & (x != 0)]
            octobre = " ".join(f"{i.day}:{v:+,.0f}" for i, v in oc.items())
            pd.DataFrame({"jour": d["jours"][t[:, 0].astype(int)].astype(str), "minute_entree": t[:, 1].astype(int),
                          "sens": t[:, 2].astype(int), "prix_entree": t[:, 3], "minute_sortie": t[:, 4].astype(int),
                          "prix_sortie": t[:, 5], "points": pts}).to_csv(J.SORTIE / "reglages_26oct_d_trades.csv", index=False)
    L += ["", "(memes definitions que reglages_26oct_b.txt)", "", "2026 mois par mois, 4 MNQ :"] + mois
    L += ["", f"Octobre 2026 jour par jour, A2, 4 MNQ : {octobre}"]
    (J.SORTIE / "reglages_26oct_d.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
