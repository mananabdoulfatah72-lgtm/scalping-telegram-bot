#!/usr/bin/env python3
"""Famille des 10 tests d'avantage (ml/REGLES.md) : Benjamini-Hochberg a q = 5 %, verdict, et paquet de donnees de la page."""
import json

import numpy as np

import donnees as D

R = {k: json.load(open(D.SORTIE / f"{k}.json")) for k in ("n1", "n2", "n3", "n3_verif", "n3_compte", "n4a", "n4b", "n5")}
n3, a, s = R["n3"], R["n4a"], R["n4b"]
fam = []
for m, nom in (("M0", "M0 logistique (l'actuel)"), ("M1", "M1 logistique L1"), ("M2", "M2 XGBoost de l'article"), ("M3", "M3 XGBoost simple"), ("M4", "M4 XGBoost complexe")):
    r = n3["modeles"][m]
    fam.append(dict(nom=nom, t=r["tout"]["t"], p=r["tout"]["p"], avant=r["avant"]["t"], apres=r["apres"]["t"], periode="2014-2026"))
for k, nom in (("bollinger", "Bollinger seul"), ("bollinger_ml", "Bollinger + M2")):
    r = n3[k]; fam.append(dict(nom=nom, t=r["tout"]["t"], p=r["tout"]["p"], avant=r["avant"]["t"], apres=r["apres"]["t"], periode="2014-2026"))
for k, nom in (("transformer", "Transformer à quantiles"), ("lineaire", "Linéaire quantile")):
    r = a[k]["trading"]; fam.append(dict(nom=nom, t=r["t"], p=r["p"], avant=r["t_avant"], apres=r["t_apres"], periode="2019-2026"))
ps, ew = s["Perte de Sharpe"], s["Poids égaux"]
fam.append(dict(nom="Allocation à perte de Sharpe", t=None, p=s["test"]["p"], avant=ps["sharpe_avant"] - ew["sharpe_avant"],
                apres=ps["sharpe_apres"] - ew["sharpe_apres"], periode="2012-2026"))
p = np.array([f["p"] for f in fam]); m = len(p); o = np.argsort(p)
ok = p[o] <= 0.05 * np.arange(1, m + 1) / m
k = np.nonzero(ok)[0].max() + 1 if ok.any() else 0
rej = np.zeros(m, bool); rej[o[:k]] = True
for i, f in enumerate(fam):
    f["bh"] = bool(rej[i]); f["seuil_bh"] = float(0.05 * (int(np.nonzero(o == i)[0][0]) + 1) / m)
    f["avantage"] = bool(rej[i] and f["avant"] > 0 and f["apres"] > 0)
json.dump(dict(famille=fam, **R), open(D.SORTIE / "page.json", "w"), separators=(",", ":"))
txt = ["# Famille des 10 tests d'avantage : Benjamini-Hochberg (q = 5 %)\n",
       "| test | période | t | p unilatérale | seuil BH | survit à BH | 1re moitié | 2e moitié | avantage (règles fixées) |", "|---|---|---|---|---|---|---|---|---|"]
for f in sorted(fam, key=lambda f: f["p"]):
    txt.append(f"| {f['nom']} | {f['periode']} | {'—' if f['t'] is None else format(f['t'], '+.2f')} | {f['p']:.4f} | {f['seuil_bh']:.4f} | {'oui' if f['bh'] else 'non'} | "
               f"{f['avant']:+.2f} | {f['apres']:+.2f} | **{'OUI' if f['avantage'] else 'non'}** |")
txt.append("\n(1re et 2e moitiés : t avant / depuis 2023 ; pour l'allocation, écart de Sharpe avec les poids égaux.)")
D.ecrire("famille.md", "\n".join(txt) + "\n")
