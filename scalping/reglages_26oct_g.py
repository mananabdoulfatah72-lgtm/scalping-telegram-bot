#!/usr/bin/env python3
"""Regle de l'utilisateur avec fenetre de confirmation (26 octobre 2026 au soir, descriptif). Comme reglages_26oct_f.py, mais
si la minute qui franchit le niveau n'a pas le volume, une des W minutes suivantes peut confirmer, tant que le prix clot
toujours au-dela du niveau (sinon la fenetre se ferme ; il faudra une nouvelle cassure). W = 5 fixe avant calcul (« quelques
minutes ») ; W = 0, 3, 10 et les multiples 0,8 / 1,2 et la moyenne sur 20 ou 40 minutes : sensibilite seulement.
Reference du rejeu C# (CASSURE=1 VOLUME=1 VOLMULT=1 SANS_TARDIVE=1 COURIR=1 FENETRE=5). Ecrit resultats/j/reglages_26oct_g.txt.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/reglages_26oct_g.py"""
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
def _zone_fw(C, V, sigma, href, bref, jouable, kvol, W, nvol):
    S, N = C.shape
    tr = np.zeros((S, 8))
    nt = 0
    for s in range(S):
        if not jouable[s]:
            continue
        pos, me, px, niveau, fait = 0, -1, 0.0, np.nan, False
        ub, lb = np.nan, np.nan
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
                    if sf == e and m <= fin and (kvol <= 0 or V[s, m] >= kvol * V[s, max(0, m - nvol):m].sum() / nvol):
                        pos, me, px, fait = e, m, p, True
                        niveau = ub if e > 0 else lb
    return tr[:nt]


def main():
    d = D.minutes("NQ", chemin=os.environ["MINUTES"], debut="2011-01-01")
    S = d["c"].shape[0]
    sigma, vwap, href, bref, jouable = G.zone_tableaux(d)
    fed = np.isin(d["jours"], E.fomc())
    an = d["jours"].astype("datetime64[Y]").astype(int) + 1970
    jo = jouable & ~fed
    jours = pd.to_datetime(d["jours"])
    dep = np.flatnonzero(d["jours"] >= np.datetime64("2012-01-01"))
    dep13 = dep[dep <= S - 13]
    dep25 = dep13[d["jours"][dep13] >= np.datetime64("2025-01-01")]
    zero = np.zeros_like(d["c"])
    a = (d["c"], d["v"], sigma, href, bref, jouable)
    jeux = {"bot d'avant": RB._zone_jv(d["c"], d["v"], sigma, vwap, href, bref, jouable, False, 0.0),
            "version A": RB._zone_jv(d["c"], d["v"], sigma, vwap, href, bref, jouable, True, 2.0)}
    for W in (0, 3, 5, 10):
        jeux[f"regle x1, fenetre {W} min" + (" (CHOIX)" if W == 5 else "")] = _zone_fw(*a, 1.0, W, 30)
    for k in (0.8, 1.2):
        jeux[f"regle x{k:g}, fenetre 5 min"] = _zone_fw(*a, k, 5, 30)
    for nv in (20, 40):
        jeux[f"regle x1, fenetre 5, moy {nv} min"] = _zone_fw(*a, 1.0, 5, nv)
    L = [f"Minutes du NQ : {d['jours'][0]} - {d['jours'][-1]}.", "",
         f"{'configuration':<34} {'trades':>6} {'points':>7} {'t 11-22':>8} {'t 23-26':>8} {'j. -1000$':>9} "
         f"{'2023 4MNQ':>10} {'2024 4MNQ':>10} {'2025 4MNQ':>10} {'2026 4MNQ':>10} {'valide 12-26':>12} {'valide 25-26':>12}"]
    for nom, t in jeux.items():
        pts = t[:, 2] * (t[:, 5] - t[:, 3]) - float(d["frais"]) / float(d["pt"])
        Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in t])
        g = Zc[:, -1]
        ts = [g[jo & (an >= a0) & (an <= a1)] for a0, a1 in ((2011, 2022), (2023, 2026))]
        ts = [x.mean() / x.std(ddof=1) * np.sqrt(len(x)) for x in ts]
        r = SB._depuis(Zc, Zw, zero, zero, fed, dep13, 13, 4.0, 6.0, 0.0, 49500.0, 51000.0, 1000.0)
        r25 = SB._depuis(Zc, Zw, zero, zero, fed, dep25, 13, 4.0, 6.0, 0.0, 49500.0, 51000.0, 1000.0)
        x = pd.Series(np.where(jo, np.where((4 * Zw <= -1000).any(axis=1), -1000.0, 4 * Zc[:, -1]), 0.0), index=jours)
        L.append(f"{nom:<34} {len(t):>6} {pts.sum():>+7.0f} {ts[0]:>+8.2f} {ts[1]:>+8.2f} {int((Zw[jo].min(axis=1) <= -250).sum()):>9} "
                 + " ".join(f"{x[x.index.year == y].sum():>+10,.0f}" for y in (2023, 2024, 2025, 2026))
                 + f" {(r == 1).mean():>12.1%} {(r25 == 1).mean():>12.1%}")
        if "(CHOIX)" in nom:
            oc = x[(x.index >= "2026-10-01") & (x != 0)]
            octobre = " ".join(f"{i.day}:{v:+,.0f}" for i, v in oc.items()) + f"   total {oc.sum():+,.0f} $"
            pd.DataFrame({"jour": d["jours"][t[:, 0].astype(int)].astype(str), "minute_entree": t[:, 1].astype(int),
                          "sens": t[:, 2].astype(int), "prix_entree": t[:, 3], "minute_sortie": t[:, 4].astype(int),
                          "prix_sortie": t[:, 5], "points": pts}).to_csv(J.SORTIE / "reglages_26oct_g_trades.csv", index=False)
    L += ["", "(points bruts 1 MNQ frais deduits ; t des gains quotidiens, jours sans Fed ; j. -1000$ = journees a -1 000 $ en 4 MNQ "
          "sur 15 ans ; $ par an en 4 MNQ au prix d'aujourd'hui, limite du jour 1 000 $ ; valide : 49 500 $, marge 1 000 $, 13 seances, "
          "4 puis 6 MNQ, departs 2012-2026 et depuis 2025)", "", f"Octobre 2026 jour par jour, CHOIX, 4 MNQ : {octobre}"]
    (J.SORTIE / "reglages_26oct_g.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
