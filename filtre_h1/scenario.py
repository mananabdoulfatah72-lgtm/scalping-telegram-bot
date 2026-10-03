#!/usr/bin/env python3
"""Scenario (descriptif, pas un test) : ce que le filtre delta apporterait au bot s'il etait aussi bon sur 2011-2026
qu'en avril - septembre 2026, deux fois moins bon, ou inutile. Le vrai delta n'existe pas avant 2026 : on simule un
signal correle au resultat de chaque trade de zone (correlation rho, calee sur l'effet mesure en 2026) et on ecarte les
20 % de trades au signal le plus defavorable, comme le vrai filtre (20 sur 99). 20 tirages par scenario.
Meme simulation de challenge que protection/piste6.py. Ecrit scenario.txt. Lancer depuis ce dossier."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "protection"))
import piste6 as P6  # noqa: E402
import protection as P  # noqa: E402
import robot_main as RB  # noqa: E402

# 1. effet mesure en avril - septembre 2026 (99 trades de zone, vrai delta Databento)
z26 = pd.read_csv(ICI.parent / "orderflow" / "zone_avril_septembre_2026.csv")
g = z26["garde"].astype(bool)
ecart_mesure = (z26["points"][g].mean() - z26["points"][~g].mean()) / z26["points"].std()
part = float((~g).mean())
q = norm.ppf(part)
facteur = norm.pdf(q) / part + norm.pdf(q) / (1 - part)        # ecart des moyennes (en ecarts-types) = rho x facteur
rho_mesure = ecart_mesure / facteur

# 2. trades de zone 2011-2026 et leur resultat en points
jours, O, H, L, C, Z, dec, voulu, ouvert = P.donnees()
nj = len(jours)
dates = pd.DatetimeIndex(jours)
d, me, ms, s = (Z[k].to_numpy() for k in ("d", "me", "ms", "sens"))
pts = s * (C[d, ms] - C[d, me]) - RB.COUT
annee = dates[d].year
norme = pd.Series(pts).groupby(annee).transform("std").to_numpy()   # le NQ a decuple : resultat en ecarts-types de l'annee
zr = pts / norme
a6 = (O, H, L, C)
fz, fr = P.FRAIS_ZONE, P.FRAIS_RSI
possibles = [x for x in range(260, nj) if ouvert[x] == 0]
departs = possibles[::P.PAS_DEPART]
expl = [x for x in departs if dates[x] <= pd.Timestamp("2022-12-31")]
coffre = [x for x in departs if dates[x] >= pd.Timestamp("2023-01-01")]
complets = [x for x in possibles if dates[x] >= pd.Timestamp("2023-01-01") and x + P.MAX_SEANCES <= nj][::2]
zero = np.zeros(nj)


def mesurer(garde):
    zt = P.tableaux_zone(Z, nj, garde)
    a = a6 + tuple(zt) + (dec, voulu, ouvert)
    gain = P6.gains_du_bot(*a, fz, fr)
    out = {"par_jour": gain[260:].mean(), "par_jour_23": gain[dates >= pd.Timestamp("2023-01-01")].mean()}
    for nom, ds in (("t1", expl), ("t2", coffre)):
        r = [P6.trail(int(x), P.MAX_SEANCES, *a, zero, fz, fr) for x in ds]
        iss = np.array([v[0] for v in r])
        dur = [v[1] - x for v, x in zip(r, ds) if v[0] == 1]
        out[nom] = (100 * (iss == 1).mean(), 100 * (iss == -1).mean(), float(np.median(dur)) if dur else np.nan)
    sf = [P6.s2f(int(x), P.MAX_SEANCES, *a, zero, fz, fr) for x in complets]
    out["s2f"] = (np.mean([v[2] - 57.0 for v in sf]), 100 * np.mean([v[1] > 0 for v in sf]))
    return out


scen = {"sans filtre (bot actuel sans le delta)": None,
        "filtre aussi bon qu'en 2026": rho_mesure,
        "filtre deux fois moins bon": rho_mesure / 2,
        "filtre inutile (le bot ecarte 20 % des trades au hasard)": 0.0}
L = [f"Effet mesure en avril - septembre 2026 : {part:.0%} des trades ecartes, ecart gardes - ecartes de {ecart_mesure:.2f}"
     f" ecart-type par trade -> correlation du signal avec le resultat rho = {rho_mesure:.2f}",
     f"{len(Z)} trades de zone du {dates[0].date()} au {dates[-1].date()} ; 20 tirages par scenario", "",
     "scenario | $ par seance du bot (2012-2026 / 2023-2026) | Trail 2011-2022 : reussis / perdus / seances pour reussir"
     " (mediane) | Trail 2023-2026 : idem | S2F + 12 mois : recu / au moins un retrait"]
for nom, rho in scen.items():
    tirages = [np.ones(len(Z), bool)] if rho is None else []
    if rho is not None:
        rng = np.random.default_rng(7)
        for _ in range(20):
            sig = rho * zr + np.sqrt(1 - rho ** 2) * rng.standard_normal(len(zr))
            tirages.append(sig > q)
    R = [mesurer(gd) for gd in tirages]
    m = lambda k, i=None: np.nanmean([r[k] if i is None else r[k][i] for r in R])  # noqa: E731
    L.append(f"{nom} | {m('par_jour'):+.1f} $ / {m('par_jour_23'):+.1f} $ | {m('t1', 0):.1f} / {m('t1', 1):.1f} / "
             f"{m('t1', 2):.0f} | {m('t2', 0):.1f} / {m('t2', 1):.1f} / {m('t2', 2):.0f} | {m('s2f', 0):+,.0f} $ / {m('s2f', 1):.0f} %")
    print(L[-1], flush=True)
(ICI / "scenario.txt").write_text("\n".join(L) + "\n")
print("\n".join(L[:2]))
