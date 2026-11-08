#!/usr/bin/env python3
"""Diagnostic de Z12 (VAGUE2.md), pas une regle : premieres annees d'un compte finance neuf (comme terminal/prep3.py),
Bot 3 en 1 de base contre Bot 3 en 1 sans les jours de VIX inverse ; B3 et B3 + VIX sont montres a titre indicatif
(la combinaison n'a pas ete fixee d'avance). MINUTES_NQ=... CACHE_DOSSIER=... python3 diagnostic_z12.py"""
import glob
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "ml/arene")); sys.path.insert(0, str(R / "ml"))
import bots as BT  # noqa: E402

d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(R / "radar/donnees/jour/yahoo/*.csv.gz")))])
v = d[d.serie.isin(["^VIX:c", "^VIX3M:c"])].pivot_table(index="date", columns="serie", values="valeur"); v.index = pd.to_datetime(v.index)
ecart = (v["^VIX:c"] - v["^VIX3M:c"]).dropna()
B = BT.Base(os.environ["CACHE_DOSSIER"]); aj = B.an[B.test]; n = len(B.test)
jours = pd.to_datetime([B.J[s] for s in range(len(B.J))])
inverse = (ecart.reindex(jours.union(ecart.index)).ffill().shift(1).reindex(jours) >= 0).to_numpy()
zt = BT.zone(B)
sensp = lambda g: 0 if not np.isfinite(B.p[g]) else (1 if B.p[g] > 0.5 else -1)
b3 = [t for t in zt if sensp(BT.bougie_avant(t[0], t[2])) == t[1]]
CAS = {"Bot 3 en 1": zt, "Z12 · sans VIX inversé": [t for t in zt if not inverse[t[0]]],
       "B3 · accord XGBoost": b3, "B3 + Z12 (indicatif)": [t for t in b3 if not inverse[t[0]]]}


def parcours(r, dp, tr, i0, i1):
    phase = 1; solde = haut = base_ = 50000.0; meil = 0.0; jr = 0; nret = 0; ret = fr = 0.0; g = 0; dq = 0; prem = -1
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
            if prem < 0: prem = i - i0
    return ret - fr, g, prem


print(f"{int(inverse[B.test].sum())} séances sur {n} avec le VIX inversé la veille ({inverse[B.test].mean():.1%})")
print(f"{'':26s} {'1 an dès 2017':>28s} {'2 ans dès 2017':>28s} {'1 an dès 2023':>28s}   (net retiré · grillé · aucun retrait)")
for nom, tr in CAS.items():
    r, dp, ntr = BT.journees(B, tr, 1, 400.0); r, dp, t_ = r[B.test], dp[B.test], (ntr[B.test] > 0)
    lig = []
    for h, deb in ((250, int(np.argmax(aj >= 2017))), (500, int(np.argmax(aj >= 2017))), (250, int(np.argmax(aj >= 2023)))):
        x = np.array([parcours(r, dp, t_, i0, i0 + h) for i0 in range(deb, n - h, 20)], float)
        lig.append(f"{x[:, 0].mean():8,.0f} $ · {(x[:, 1] > 0).mean():4.0%} · {(x[:, 2] < 0).mean():4.0%}".replace(",", " "))
    ans = {a: r[aj == a].sum() for a in range(2014, 2027)}
    print(f"{nom:26s} " + "   ".join(lig) + f"   années négatives : {', '.join(str(a) for a, s in ans.items() if s < 0) or 'aucune'}")
