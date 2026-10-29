#!/usr/bin/env python3
"""Demande de l'utilisateur du 27 octobre 2026 (descriptif) : configuration installee (reglages_26oct_g.py : cassure, volume x1,
fenetre de 5 minutes, une entree par seance) mais sans sortie aux controles : la position est gardee jusqu'a 16 h, sauf si la
perte du jour atteint 1 000 $ (appliquee dans le challenge et les $ par an). Comparee a la sortie aux controles. Reference du
rejeu C# (... SANS_SORTIE=1). Ecrit resultats/j/reglages_27oct_sans_sortie.txt et _trades.csv.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/reglages_27oct_sans_sortie.py"""
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


@njit(cache=True)
def _zone_ss(C, V, sigma, href, bref, jouable, kvol, W):
    S, N = C.shape
    tr = np.zeros((S, 8))
    nt = 0
    for s in range(S):
        if not jouable[s]:
            continue
        ub, lb = np.nan, np.nan
        fin, sf = -1, 0
        for m in range(30, 361):
            if m % 30 == 0:
                sg = sigma[s, m]
                ub, lb = href[s] * (1 + sg), bref[s] * (1 - sg)
            p, q = C[s, m], C[s, m - 1]
            e = 1 if p > ub else (-1 if p < lb else 0)
            if e == 0:
                fin = -1
                continue
            if (e > 0 and q <= ub) or (e < 0 and q >= lb):
                fin, sf = m + W, e
            if sf == e and m <= fin and V[s, m] >= kvol * V[s, m - 30:m].sum() / 30.0:
                J._ecrit(tr, nt, s, m, e, p, N - 1, C[s, N - 1], 0, 0.0)
                nt += 1
                break
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
    dep13 = dep[dep <= S - 13]
    dep25 = dep13[d["jours"][dep13] >= np.datetime64("2025-01-01")]
    zero = np.zeros_like(d["c"])
    jeux = {"sortie aux controles (installee)": RG._zone_fw(d["c"], d["v"], sigma, href, bref, jouable, 1.0, 5, 30),
            "SANS SORTIE : 16 h ou -1 000 $": _zone_ss(d["c"], d["v"], sigma, href, bref, jouable, 1.0, 5)}
    L = [f"Minutes du NQ : {d['jours'][0]} - {d['jours'][-1]}. Memes entrees dans les deux cas : "
         f"{'oui' if np.array_equal(jeux['sortie aux controles (installee)'][:, :4], jeux['SANS SORTIE : 16 h ou -1 000 $'][:, :4]) else 'NON'}.", ""]
    for nom, t in jeux.items():
        pts = t[:, 2] * (t[:, 5] - t[:, 3]) - float(d["frais"]) / float(d["pt"])
        Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in t])
        g = Zc[:, -1]
        ts = [g[jo & (an >= a0) & (an <= a1)] for a0, a1 in ((2011, 2022), (2023, 2026))]
        ts = [x.mean() / x.std(ddof=1) * np.sqrt(len(x)) for x in ts]
        r = SB._depuis(Zc, Zw, zero, zero, fed, dep13, 13, 4.0, 6.0, 0.0, 49500.0, 51000.0, 1000.0)
        r25 = SB._depuis(Zc, Zw, zero, zero, fed, dep25, 13, 4.0, 6.0, 0.0, 49500.0, 51000.0, 1000.0)
        x = pd.Series(np.where(jo, np.where((4 * Zw <= -1000).any(axis=1), -1000.0, 4 * Zc[:, -1]), 0.0), index=jours)
        tr = x[(x != 0) & (x.index >= "2023-01-01")]
        eq = x.cumsum()
        L += [f"{nom} : {len(t)} trades, t {ts[0]:+.2f} / {ts[1]:+.2f}, journees a -1 000 $ (15 ans) {int((Zw[jo].min(axis=1) <= -250).sum())}, "
              f"pire baisse {(eq - eq.cummax()).min():+,.0f} $",
              f"  2023-2026 : jours gagnants {(tr > 0).mean():.0%}, gain moyen {tr[tr > 0].mean():+,.0f} $, perte moyenne {tr[tr < 0].mean():+,.0f} $, "
              f"jours coupes a -1 000 $ {(tr <= -1000).mean():.0%}",
              "  par an (4 MNQ) : " + " ".join(f"{y}:{x[x.index.year == y].sum():+,.0f}" for y in range(2018, 2027)),
              f"  total 2011-2026 {x.sum():+,.0f} $, depuis 2023 {x[x.index >= '2023-01-01'].sum():+,.0f} $",
              f"  challenge marge 1 000 $ : valide {(r == 1).mean():.1%} perdu {(r == -1).mean():.1%} expire {(r == 0).mean():.1%} ; "
              f"departs depuis 2025 : valide {(r25 == 1).mean():.1%} perdu {(r25 == -1).mean():.1%}",
              "  octobre 2026 : " + " ".join(f"{i.day}:{v:+,.0f}" for i, v in x[(x.index >= '2026-10-01') & (x != 0)].items())
              + f"   total {x[x.index >= '2026-10-01'].sum():+,.0f} $", ""]
        if nom.startswith("SANS"):
            pd.DataFrame({"jour": d["jours"][t[:, 0].astype(int)].astype(str), "minute_entree": t[:, 1].astype(int),
                          "sens": t[:, 2].astype(int), "prix_entree": t[:, 3], "minute_sortie": t[:, 4].astype(int),
                          "prix_sortie": t[:, 5], "points": pts}).to_csv(J.SORTIE / "reglages_27oct_sans_sortie_trades.csv", index=False)
    (J.SORTIE / "reglages_27oct_sans_sortie.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
