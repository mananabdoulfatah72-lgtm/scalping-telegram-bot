#!/usr/bin/env python3
"""LucidFlex 50K sans limite de temps (memes regles que lucid_27oct.py) avec le bot de base : zone V1 aux controles et filtre delta
H1 (descriptif, 27 octobre 2026). Le vrai delta n'existe que depuis avril 2026 : comme filtre_h1/scenario.py, on simule un signal
correle au resultat de chaque trade de zone (rho cale sur avril - septembre 2026) et on ecarte les 20 % de trades au signal le
plus defavorable ; 20 tirages. Un trade ecarte n'est pas tenu (comme le bot : le trade reste virtuel jusqu'a sa sortie).
Ecrit resultats/j/lucid_27oct_filtre.txt.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/lucid_27oct_filtre.py"""
import os

import numpy as np
import pandas as pd
from scipy.stats import norm

import challenge_ajouts as CA
import commun as K
import donnees as D
import lucid_27oct as LU
import partie_e as E
import partie_g as G
import partie_j as J
import reglages_26oct_b as RB


def main():
    z26 = pd.read_csv(K.KB / "orderflow" / "zone_avril_septembre_2026.csv")
    g26 = z26["garde"].astype(bool)
    ecart = (z26["points"][g26].mean() - z26["points"][~g26].mean()) / z26["points"].std()
    part = float((~g26).mean())
    q = norm.ppf(part)
    rho = ecart / (norm.pdf(q) / part + norm.pdf(q) / (1 - part))
    d = D.minutes("NQ", chemin=os.environ["MINUTES"], debut="2011-01-01")
    sigma, vwap, href, bref, jouable = G.zone_tableaux(d)
    fed = np.isin(d["jours"], E.fomc())
    dep = np.flatnonzero(d["jours"] >= np.datetime64("2012-01-01"))
    groupes = (("departs 2012 - 2025", dep[d["jours"][dep] < np.datetime64("2025-10-01")]),
               ("departs 2023 - sept. 2025", dep[(d["jours"][dep] >= np.datetime64("2023-01-01")) & (d["jours"][dep] < np.datetime64("2025-10-01"))]))
    t = RB._zone_jv(d["c"], d["v"], sigma, vwap, href, bref, jouable, False, 0.0)
    pts = t[:, 2] * (t[:, 5] - t[:, 3]) - 1.5
    an = d["jours"][t[:, 0].astype(int)].astype("datetime64[Y]").astype(int)
    zr = pts / pd.Series(pts).groupby(an).transform("std").to_numpy()
    L = [f"Effet du vrai delta en avril - septembre 2026 : {part:.0%} des trades ecartes, rho = {rho:.2f}. "
         f"{len(t)} trades de zone V1 (2011 - 23 octobre 2026), 20 tirages par scenario.", "",
         "LucidFlex 50K sans limite de temps (objectif 3 000 $, perte 2 000 $ en fin de journee bloquee a +100 $, regularite 50 %),"
         " bot de base (zone aux controles), limite du bot 1 000 $, pas de zone les jours de la Fed :", ""]
    scen = (("sans filtre", None), ("filtre aussi bon qu'en 2026", rho), ("filtre deux fois moins bon", rho / 2),
            ("filtre inutile (20 % au hasard)", 0.0))
    for nom, r in scen:
        tirages = [np.ones(len(t), bool)] if r is None else []
        rng = np.random.default_rng(7)
        if r is not None:
            for _ in range(20):
                tirages.append(r * zr + np.sqrt(1 - r ** 2) * rng.standard_normal(len(zr)) > q)
        for z in (1.0, 2.0):
            res = {g: [] for g, _ in groupes}
            for garde in tirages:
                tt = t[garde]
                Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in tt])
                for gnom, g in groupes:
                    et, du = LU._lucid(Zc, Zw, fed, g, z, 1000.0, 252)
                    res[gnom].append(((et == 1).mean(), (et == -1).mean(), np.median(du[et == 1]) if (et == 1).any() else np.nan))
            lig = f"{nom:<32} {int(z)} MNQ"
            for gnom, _ in groupes:
                a = np.array(res[gnom])
                lig += f"  | {gnom} : valide {a[:, 0].mean():5.1%}, perdu {a[:, 1].mean():5.1%}, {np.nanmean(a[:, 2]):.0f} seances (mediane)"
            L.append(lig)
    (J.SORTIE / "lucid_27oct_filtre.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
