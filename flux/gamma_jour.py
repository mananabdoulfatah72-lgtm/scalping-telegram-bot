#!/usr/bin/env python3
"""Partie 12 (flux/README.md) : retournement des jours de gamma haut toute la journee (M1-M3) et son miroir, l'elan des
jours de gamma bas (M4), fixes le 30 octobre 2026 avant tout calcul. Gains additionnes par journee, t sur les journees.

Lancer : python3 flux/gamma_jour.py <minutes NQ 2011 - 2026 (t,o,h,l,c,v,contrat)>"""
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "scalping"))
import donnees as SD  # noqa: E402
import gamma_0dte as G  # noqa: E402

FRAIS = 3.0
REGLES = {"M1 gamma >= 80 %, contre, 30 min": (lambda g: g >= 0.8, -1, 30, range(30, 361, 30)),
          "M2 gamma >= 60 %, contre, 30 min": (lambda g: g >= 0.6, -1, 30, range(30, 361, 30)),
          "M3 gamma >= 80 %, contre, 15 min": (lambda g: g >= 0.8, -1, 15, range(15, 376, 15)),
          "M4 gamma <= 20 %, avec, 30 min": (lambda g: g <= 0.2, 1, 30, range(30, 361, 30))}


def rang_veille(jours):
    r = G.gex().dropna()
    i = r.index.searchsorted(jours, side="left") - 1
    g = np.where(i >= 0, r.values[np.maximum(i, 0)], np.nan)
    return np.where((jours - r.index[np.maximum(i, 0)]).days <= 7, g, np.nan)


def journees(d, g, regle):
    cond, signe, pas, entrees = regle
    O = d["o"]
    ok = d["complete"] & ~d["ech"]
    ech = float(d["pref"]) / O[:, 0] * float(d["pt"])
    jour = np.zeros(len(O))
    n = np.zeros(len(O), int)
    actif = ok & np.asarray([bool(cond(x)) if np.isfinite(x) else False for x in g])
    for e in entrees:
        mv = O[:, e] - O[:, e - pas]                       # mouvement des `pas` dernieres minutes (ouvertures)
        sens = signe * np.sign(mv)
        sortie = O[:, min(e + pas, 389)]
        gain = sens * (sortie - O[:, e]) * ech - FRAIS
        pris = actif & (sens != 0)
        jour += np.where(pris, gain, 0.0)
        n += pris
    return pd.Series(np.where(actif, jour, np.nan), index=pd.DatetimeIndex(d["jours"].astype("datetime64[D]"))), n


def main():
    d = SD.minutes("NQ", chemin=sys.argv[1], debut="2011-01-01")
    jours = pd.DatetimeIndex(d["jours"].astype("datetime64[D]"))
    g = rang_veille(jours)
    seuil = NormalDist().inv_cdf(1 - 0.05 / len(REGLES))
    L = ["# Partie 12 : retournement des jours de gamma haut, toute la journée", "",
         f"$ pour 1 MNQ au prix d'aujourd'hui, frais de 3 $ par trade. t sur les journées. Barre sur l'ère 0DTE : t ≥ {seuil:.2f}, "
         "gain moyen positif, 3 années gagnantes sur 5.", "",
         "| Règle | Période | Journées | Trades | Total | Par journée | t | Années |", "|---|---|---|---|---|---|---|---|"]
    for nom, regle in REGLES.items():
        x, n = journees(d, g, regle)
        for per, m in (("2011 - mai 2022", jours < G.DEBUT_0DTE), ("ère 0DTE", jours >= G.DEBUT_0DTE)):
            y = x[m].dropna()
            t = y.mean() / y.std(ddof=1) * np.sqrt(len(y)) if len(y) > 1 else np.nan
            ans = y.groupby(y.index.year).sum()
            verdict = ""
            if per == "ère 0DTE":
                verdict = " **PASSE**" if (t >= seuil and y.mean() > 0 and (ans > 0).sum() >= 3) else " échoue"
            txt = ", ".join(f"{k} {v:+,.0f}" for k, v in ans.items()) if per == "ère 0DTE" else ""
            L.append(f"| {nom} | {per}{verdict} | {len(y)} | {int(n[m].sum())} | {y.sum():+,.0f} $ | {y.mean():+,.1f} $ | "
                     f"{t:+.2f} | {txt} |")
    out = ICI / "resultats/partie12"
    out.mkdir(parents=True, exist_ok=True)
    (out / "gamma_jour.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
