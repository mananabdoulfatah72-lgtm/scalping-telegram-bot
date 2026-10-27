#!/usr/bin/env python3
"""Meme simulation LucidFlex 50K que lucid_27oct.py pour les versions precedentes du bot (descriptif). Ajoute a resultats/j/lucid_27oct.txt."""
import os, numpy as np
import donnees as D, partie_g as G, partie_e as E, challenge_ajouts as CA, reglages_26oct_b as RB, reglages_26oct_g as RG, reglages_27oct_sans_sortie as SS, lucid_27oct as LU
d = D.minutes("NQ", chemin=os.environ["MINUTES"], debut="2011-01-01")
sigma, vwap, href, bref, jouable = G.zone_tableaux(d)
fed = np.isin(d["jours"], E.fomc())
dep = np.flatnonzero(d["jours"] >= np.datetime64("2012-01-01"))
g1 = dep[d["jours"][dep] < np.datetime64("2025-10-01")]
g2 = dep[(d["jours"][dep] >= np.datetime64("2023-01-01")) & (d["jours"][dep] < np.datetime64("2025-10-01"))]
for nom, t in (("bot d'avant (controles)", RB._zone_jv(d["c"], d["v"], sigma, vwap, href, bref, jouable, False, 0.0)),
               ("version A (cassure+volume x2, sorties d'origine)", RB._zone_jv(d["c"], d["v"], sigma, vwap, href, bref, jouable, True, 2.0)),
               ("ta regle, sortie au niveau casse aux controles", RG._zone_fw(d["c"], d["v"], sigma, href, bref, jouable, 1.0, 5, 30)),
               ("ta regle, sans sortie ni stop (16 h ou -1000)", SS._zone_ss(d["c"], d["v"], sigma, href, bref, jouable, 1.0, 5))):
    Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in t])
    for z in (1.0, 2.0):
        out = []
        for g in (g1, g2):
            et, du = LU._lucid(Zc, Zw, fed, g, z, 1000.0, 252)
            out.append(f"valide {(et==1).mean():5.1%} perdu {(et==-1).mean():5.1%} ({np.median(du[et==1]):.0f} seances)")
        print(f"{nom:<50} {int(z)} MNQ : 2012-2025 {out[0]} | 2023-2025 {out[1]}")
