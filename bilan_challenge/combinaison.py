#!/usr/bin/env python3
"""Combinaison des pistes qui tiennent sur le NQ (regles : COMBINAISON.md, ecrites avant ce calcul).

Zone de bruit (Bot 3 en 1, reglages actuels, sans le filtre delta) et Supertrend 10-3 en 5 minutes, chacun avec sa
limite de perte du jour, seuls puis sur le meme compte Master Bulenox (option 2). La nuit (16 h -> 9 h 30) n'a que
son gain par seance.

Usage : SCRATCH=<dossier de travail : st_detail.py, lm/, zone_c2q1_15ans.txt, series_par_seance.csv> python3 combinaison.py
"""
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
S = Path(os.environ["SCRATCH"])
sys.path.insert(0, str(S)); sys.path.insert(0, str(S / "lm/chantier"))
import st_detail as X  # noqa: E402
import rejeu_periode as RP  # noqa: E402

N = 390
J = [str(j) for j in X.J]; nj = X.nj; idx = {j: d for d, j in enumerate(J)}
DEBUT, FIN = "2012-02-20", "2026-09-25"

# trades de chaque seance : (sens, a, b, entree, sortie) ; le trade vit sur les minutes a..b
ZONE = [[] for _ in range(nj)]
for j, sens, a, b, e, x in RP.trades_bot(S / "zone_c2q1_15ans.txt")[0]:
    ZONE[idx[j]].append((sens, a, b, e, x))
ST = [[] for _ in range(nj)]
for i in range(len(X.T)):
    ST[int(X.T[i, 0])].append((int(X.T[i, 1]), int(X.T[i, 2]) + 1, int(X.T[i, 3]), X.T[i, 4], X.T[i, 5]))


def chemins(trades, n, lim):
    """Pour chaque seance : valeur du bot en $ (realise + latent) au plus bas et au plus haut de chaque minute, gain du
    jour, et s'il a trade. n MNQ, gains au prix d'aujourd'hui, 3 $ de frais par MNQ ; limite du jour comme le bot."""
    vL = np.zeros((nj, N)); vH = np.zeros((nj, N)); gain = np.zeros(nj); joue = np.zeros(nj, bool)
    for d in range(nj):
        real = 0.0; fin = 0; arret = False
        for s, a, b, e, x in trades[d]:
            if arret:
                break
            joue[d] = True; k = 28500.0 / e; sorti = False
            vL[d, fin:a] = real; vH[d, fin:a] = real
            for m in range(a, b + 1):
                bas = real + n * (2 * s * (X.L[d, m] - e) * k - 3.0)
                haut = real + n * (2 * s * (X.H[d, m] - e) * k - 3.0)
                if (bas if s > 0 else haut) <= -lim:
                    niv = e + s * ((-lim - real) / n + 3.0) / (2 * k)
                    sortie = (min(X.O[d, m], niv) - 1.0) if s > 0 else (max(X.O[d, m], niv) + 1.0)
                    real += n * (2 * s * (sortie - e) * k - 3.0); arret = sorti = True
                    vL[d, m:] = real; vH[d, m:] = real; fin = N
                    break
                vL[d, m] = bas; vH[d, m] = haut
            if not sorti:
                real += n * (2 * s * (x - e) * k - 3.0); fin = b + 1
        if fin < N:
            vL[d, fin:] = real; vH[d, fin:] = real
        gain[d] = real
    return vL, vH, gain, joue


Z1 = chemins(ZONE, 1, 1000.0); Z2 = chemins(ZONE, 2, 1000.0); S1 = chemins(ST, 1, 400.0)
COMBOS = {"A  Zone 1 MNQ seule": [Z1], "B  Supertrend 1 MNQ seul": [S1], "C  Zone 1 + Supertrend 1": [Z1, S1],
          "D  Zone 2 + Supertrend 1": [Z2, S1]}


def journees(parts):
    vL = sum(p[0] for p in parts); vH = sum(p[1] for p in parts)
    pire = np.minimum(np.minimum(vL, vH).min(axis=1), 0.0)
    return sum(p[2] for p in parts), pire, np.any([p[3] for p in parts], axis=0)


def master(gain, pire, joue, departs, ns=250, inactivite=True):
    """Option 2 depuis 51 000 $ / plancher 49 200 $. Renvoie les parts (retrait, plancher, inactivite, ni l'un ni l'autre)
    et le nombre median de seances jusqu'au retrait."""
    r = [0, 0, 0, 0]; duree = []
    for i in departs:
        solde, haut, sans, issue = 51000.0, 51700.0, 0, 3
        for q in range(ns):
            d = i + q
            if solde + pire[d] <= min(haut - 2500.0, 50100.0):
                issue = 1
                break
            solde += gain[d]
            sans = 0 if joue[d] else sans + 1
            if inactivite and sans >= 5:
                issue = 2
                break
            if solde >= 53600.0:
                issue = 0; duree.append(q + 1)
                break
            if solde > haut:
                haut = solde
        r[issue] += 1
    n = len(departs)
    return [x / n * 100 for x in r], (float(np.median(duree)) if duree else float("nan"))


def stats(s):
    x = s.to_numpy(); n = len(x); m = x.mean(); e = x.std(ddof=1); r = s[s.index >= "2023-01-01"].to_numpy()
    cum = np.cumsum(x); an = s.groupby(s.index.str[:4]).sum()
    return (m * 252, m / e * math.sqrt(n), r.mean() / r.std(ddof=1) * math.sqrt(len(r)),
            (cum - np.maximum.accumulate(cum)).min(), x.min(), [k for k, v in an.items() if v < 0])


L = []
# 1. gain par seance, 20 fevr. 2012 -> 25 sept. 2026
ok = [d for d in range(nj) if X.complete[d] and DEBUT <= J[d] <= FIN]
jours = [J[d] for d in ok]
ser = pd.DataFrame({"Zone": Z1[2][ok], "Zone x2": Z2[2][ok], "Supertrend 5 min": S1[2][ok]}, index=jours)
autres = pd.read_csv(S / "series_par_seance.csv", index_col=0)
nuit = autres[[c for c in autres.columns if c.startswith("Nuit")][0]].reindex(jours).fillna(0.0)
ser["Nuit"] = nuit.to_numpy()
ser["NQ (acheter et conserver)"] = autres["Acheter et conserver le NQ"].reindex(jours).fillna(0.0).to_numpy()
L += ["1. Gain par seance pour 1 MNQ, prix d'aujourd'hui, frais compris (" + f"{jours[0]} -> {jours[-1]}, {len(jours)} seances)", "",
      "Correlations entre les gains du jour :", ser[["Zone", "Supertrend 5 min", "Nuit", "NQ (acheter et conserver)"]].corr().round(2).to_string(), ""]
PORT = {"A  Zone 1 MNQ seule": ser["Zone"], "B  Supertrend 1 MNQ seul": ser["Supertrend 5 min"],
        "C  Zone 1 + Supertrend 1": ser["Zone"] + ser["Supertrend 5 min"], "D  Zone 2 + Supertrend 1": ser["Zone x2"] + ser["Supertrend 5 min"],
        "E  Zone + Supertrend + Nuit": ser["Zone"] + ser["Supertrend 5 min"] + ser["Nuit"], "F  Zone + Nuit": ser["Zone"] + ser["Nuit"],
        "   Nuit seule (information)": ser["Nuit"]}
L.append(f"{'combinaison':30s} {'par an':>10s} {'t':>6s} {'t 2023+':>8s} {'pire baisse':>12s} {'pire seance':>12s}  annees perdantes")
for nom, s in PORT.items():
    an, t, t23, dd, pj, perd = stats(s)
    L.append(f"{nom:30s} {an:+10,.0f} {t:6.2f} {t23:8.2f} {dd:+12,.0f} {pj:+12,.0f}  {len(perd)} ({', '.join(perd) or 'aucune'})")
# semaines et mois perdants de C contre A et B
for nom in ("A  Zone 1 MNQ seule", "B  Supertrend 1 MNQ seul", "C  Zone 1 + Supertrend 1"):
    s = PORT[nom]; mois = s.groupby(s.index.str[:7]).sum()
    L.append(f"   mois perdants {nom[:1]} : {(mois < 0).mean() * 100:.0f} % ; pire mois {mois.min():+,.0f} $ ; mois median {mois.median():+,.0f} $")

# 2. compte Master, option 2
L += ["", "2. Master Bulenox, option 2, depuis 51 000 $ / plancher 49 200 $, 250 seances :",
      "   53 600 $ atteint / perdu par le plancher / perdu par l'inactivite / ni l'un ni l'autre (%), seances jusqu'au retrait (mediane)"]
for a0 in ("2011", "2023"):
    dep = [i for i in range(nj) if J[i] >= a0 and X.complete[i] and i + 250 <= nj]
    L.append(f"   departs depuis {a0} ({len(dep)}) :")
    for nom, parts in COMBOS.items():
        g, p, j = journees(parts)
        r, med = master(g, p, j, dep)
        ligne = f"     {nom:28s} {r[0]:5.1f} / {r[1]:5.1f} / {r[2]:5.1f} / {r[3]:5.1f}   ({med:.0f} seances)"
        if nom.startswith("A"):
            r2, _ = master(g, p, j, dep, inactivite=False)
            ligne += f"   | sans la regle d'inactivite : {r2[0]:.1f} / {r2[1]:.1f} / - / {r2[3]:.1f}"
        L.append(ligne)
# seances sans trade
for nom, parts in COMBOS.items():
    j = journees(parts)[2]; comp = [d for d in range(nj) if X.complete[d]]
    L.append(f"   seances sans trade, {nom[:1]} : {(~j[comp]).mean() * 100:.0f} %")
(ICI / "combinaison.txt").write_text("\n".join(L) + "\n")
print("\n".join(L))
