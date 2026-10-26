#!/usr/bin/env python3
"""Descriptif (26 octobre 2026 au soir) : une entree par seance a la premiere minute qui cloture au-dela du niveau du dernier
controle avec un volume d au moins 2 fois la moyenne des 30 minutes d avant (et sans volume), tenue jusqu a 16 h ; la limite
du jour de 1 000 $ est appliquee dans le challenge et les $ par an. Base de la version « sorties a la main » (sans les sorties
de l utilisateur). Lancer : KB=<branche de recherche> MINUTES=<nq_1min> python3 scalping/reglages_26oct_c.py"""
import os, sys, numpy as np, pandas as pd
from numba import njit
import donnees as D, partie_g as G, partie_j as J, partie_e as E, challenge_ajouts as CA, situation_bulenox as SB
d = D.minutes("NQ", chemin=os.environ["MINUTES"], debut="2011-01-01")
S = d["c"].shape[0]
sigma, vwap, href, bref, jouable = G.zone_tableaux(d)

@njit(cache=True)
def _b(C, V, sigma, href, bref, jouable, kvol):
    S, N = C.shape
    tr = np.zeros((S, 8)); nt = 0
    for s in range(S):
        if not jouable[s]: continue
        ub = lb = np.nan
        for m in range(30, 361):
            if m % 30 == 0:
                sg = sigma[s, m]; ub, lb = href[s] * (1 + sg), bref[s] * (1 - sg)
            p = C[s, m]
            e = 1 if p > ub else (-1 if p < lb else 0)
            if e != 0 and kvol > 0 and V[s, m] < kvol * V[s, m - 30:m].sum() / 30.0: e = 0
            if e != 0:
                J._ecrit(tr, nt, s, m, e, p, N - 1, C[s, N - 1], 0, 0.0); nt += 1
                break
    return tr[:nt]

fed = np.isin(d["jours"], E.fomc()); an = d["jours"].astype("datetime64[Y]").astype(int) + 1970
jo = jouable & ~fed; jours = pd.to_datetime(d["jours"]); zero = np.zeros_like(d["c"])
dep = np.flatnonzero(d["jours"] >= np.datetime64("2012-01-01")); dep13 = dep[dep <= S - 13]; dep21 = dep[dep <= S - 21]
for nom, kv in (("B : 1 entree/jour + volume, tenu jusqu'a 16 h ou -1000 $", 2.0), ("B sans volume", 0.0)):
    t = _b(d["c"], d["v"], sigma, href, bref, jouable, kv)
    Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in t])
    g = Zc[:, -1]
    ts = [g[jo & (an >= a0) & (an <= a1)] for a0, a1 in ((2011, 2022), (2023, 2026))]
    ts = [x.mean() / x.std(ddof=1) * np.sqrt(len(x)) for x in ts]
    r = SB._depuis(Zc, Zw, zero, zero, fed, dep13, 13, 4.0, 6.0, 0.0, 49500.0, 51000.0, 1000.0)
    r21 = SB._depuis(Zc, Zw, zero, zero, fed, dep21, 21, 4.0, 6.0, 0.0, 50000.0, 50000.0, 1000.0)
    x = pd.Series(np.where(jo, np.where((4 * Zw <= -1000).any(axis=1), -1000.0, 4 * Zc[:, -1]), 0.0), index=jours)
    tr = x[(x.index >= "2023-01-01") & (x != 0)]
    print(f"{nom}: trades {len(t)}, t {ts[0]:+.2f}/{ts[1]:+.2f}, jours -1000$ (15 ans) {int((Zw[jo].min(axis=1) <= -250).sum())}, "
          f"valide marge 1000 {(r==1).mean():.1%} perdu {(r==-1).mean():.1%} expire {(r==0).mean():.1%}, neuf {(r21==1).mean():.1%}, "
          f"2025 {x[x.index.year==2025].sum():+,.0f} $, 2026 {x[x.index.year==2026].sum():+,.0f} $, avr-oct {x[x.index>='2026-04-01'].sum():+,.0f} $, "
          f"2023-26 jours gagnants {(tr>0).mean():.0%} moy {tr[tr>0].mean():+,.0f} / {tr[tr<0].mean():+,.0f} $, coupes a -1000 : {(tr<=-1000).mean():.0%}")
    if kv:
        oc = x[(x.index >= "2026-10-01") & (x != 0)]
        print("   octobre :", " ".join(f"{i.day}:{v:+,.0f}" for i, v in oc.items()))
