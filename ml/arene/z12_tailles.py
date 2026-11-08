#!/usr/bin/env python3
"""Z12 (labo_zipline/VAGUE2.md) a 1, 2, 3, 4 et 5 MNQ sur le compte finance Bulenox, contre le Bot 3 en 1 seul : limite
du bot 400 $ par MNQ sans depasser la limite de la firme (1 100 $), meme vie reelle que l'arene (retraits, constance 40 %,
requalification a la meme taille), premieres annees d'un compte neuf, et la periode du 11 aout au 2 novembre 2026.
Calcul descriptif (aucun choix n'est fait ici). MINUTES_NQ=... CACHE_DOSSIER=... python3 z12_tailles.py <sortie.json>"""
import glob
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import bots as BT

R = Path(__file__).resolve().parents[2]
d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(R / "radar/donnees/jour/yahoo/*.csv.gz")))])
v = d[d.serie.isin(["^VIX:c", "^VIX3M:c"])].pivot_table(index="date", columns="serie", values="valeur"); v.index = pd.to_datetime(v.index)
B = BT.Base(os.environ["CACHE_DOSSIER"]); aj = B.an[B.test]; n = len(B.test); jours = [B.J[s] for s in B.test]
tous = pd.to_datetime([B.J[s] for s in range(len(B.J))])
veille = v.reindex(tous.union(v.index)).ffill().shift(1).reindex(tous)                   # cloture de la veille
INV = (veille["^VIX:c"] >= veille["^VIX3M:c"]).to_numpy()
zt = BT.zone(B); TR = {"zone": zt, "Z12": [t for t in zt if not INV[t[0]]]}
per = np.array([j >= "2026-08-11" for j in jours])


def parcours(r, dp, tr, i0, i1):
    phase = 1; solde = haut = base_ = 50000.0; meil = 0.0; jr = 0; nret = 0; ret = fr = 0.0; g = 0; dq = 0
    for i in range(i0, i1):
        pl = min(haut - 2500, 50100)
        if phase == 0:
            if dq % 20 == 0: fr += 100
            dq += 1
        if solde + dp[i] <= pl:
            if phase == 1: g += 1
            phase = 0; dq = 0; solde = haut = base_ = 50000.0; meil = 0.0; jr = 0; continue
        solde += r[i]; haut = max(haut, solde)
        if phase == 0:
            if solde >= 53000: fr += 148; phase = 1; solde = haut = base_ = 50000.0; meil = 0.0; jr = 0; nret = 0
            continue
        jr += tr[i]; meil = max(meil, r[i]); dispo = solde - 52600
        if nret < 3: dispo = min(dispo, 1500)
        if jr >= 10 and dispo >= 1000 and solde - base_ > 0 and meil <= 0.4 * (solde - base_):
            ret += dispo; solde -= dispo; base_ = solde; meil = 0.0; jr = 0; nret += 1
    return ret - fr, g


out = {"tailles": {}, "periode": {"jours": [j for j, p in zip(jours, per) if p]}}
d17, d23 = int(np.argmax(aj >= 2017)), int(np.argmax(aj >= 2023))
print(f"{'':12s} {'MNQ':>3s} {'limite':>7s} {'$/séance':>9s} {'net/an':>9s} {'grillés/an':>10s} {'survie 60':>9s} {'grillé 1 an':>11s} "
      f"{'1re année':>10s} {'grillé 1 an dès 2023':>20s} {'11/08→02/11':>12s} {'pire jour':>9s}")
for k, tr in TR.items():
    out["tailles"][k] = {}
    for t in (1, 2, 3, 4, 5):
        lim = min(400.0 * t, 1100.0)
        r, dp, ntr = BT.journees(B, tr, t, lim); m = BT.mesures(B, r, dp, ntr)
        j, dd, trd = r[B.test], dp[B.test], ntr[B.test] > 0
        x17 = np.array([parcours(j, dd, trd, i0, i0 + 250) for i0 in range(d17, n - 250, 20)])
        x23 = np.array([parcours(j, dd, trd, i0, i0 + 250) for i0 in range(d23, n - 250, 20)])
        e = dict(limite=lim, par_seance=m["par_seance"], net_an=m["net_an"], grilles_an=m["grilles_an"], survie_60=m["survie_60"],
                 grille_250=m["grille_250"], net_1an=float(x17[:, 0].mean()), grille_1an_2023=float((x23[:, 1] > 0).mean()),
                 periode=float(j[per].sum()), pire_jour=float(j.min()), pire_baisse=m["pire_baisse"],
                 jours_periode=[round(float(a), 1) for a in j[per]], trades_periode=[int(a) for a in ntr[B.test][per]])
        out["tailles"][k][str(t)] = e
        print(f"{'Z12' if k == 'Z12' else 'Bot 3 en 1':12s} {t:3d} {lim:7,.0f} {e['par_seance']:+9.1f} {e['net_an']:9,.0f} {e['grilles_an']:10.2f} "
              f"{e['survie_60']:9.0%} {e['grille_250']:11.0%} {e['net_1an']:10,.0f} {e['grille_1an_2023']:20.0%} {e['periode']:+12,.0f} {e['pire_jour']:+9,.0f}".replace(",", " "))
pj = [i for i, p in enumerate(per) if p]
out["periode"]["vix"] = [None if np.isnan(veille["^VIX:c"].iloc[B.test[i]]) else round(float(veille["^VIX:c"].iloc[B.test[i]]), 2) for i in pj]
out["periode"]["vix3m"] = [None if np.isnan(veille["^VIX3M:c"].iloc[B.test[i]]) else round(float(veille["^VIX3M:c"].iloc[B.test[i]]), 2) for i in pj]
out["periode"]["inverse"] = [bool(INV[B.test[i]]) for i in pj]
print("séances du 11 août au 2 nov. :", len(pj), "dont VIX inversé la veille :", sum(out["periode"]["inverse"]),
      [jours[i] for i in pj if INV[B.test[i]]])
json.dump(out, open(sys.argv[1], "w"), separators=(",", ":"))
