#!/usr/bin/env python3
"""Partie 11 (flux/README.md) : regles tirees de la recherche sur l'ere 0DTE, fixees le 30 octobre 2026 avant tout
calcul. Gamma des teneurs de marche (GEX de SqueezeMetrics de la veille, rang sur 252 seances) : elan en gamma bas,
retournement en gamma haut, en fin de seance (L1, L2) et l'apres-midi (L3, L4) ; retournement de l'ouverture apres une
forte nuit (L5). Jugement sur le 16 mai 2022 - 29 octobre 2026.

Lancer : python3 flux/gamma_0dte.py <minutes NQ 2011 - 2026 (t,o,h,l,c,v,contrat)>"""
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "scalping"))
import donnees as SD  # noqa: E402

PLACE = 0.8591989517211914
SEUIL = 0.80                           # gamma haut (L2)
DEBUT_0DTE = "2022-05-16"
FRAIS = 3.0


def gex():
    fs = sorted((ICI.parent / "radar/donnees/jour/alt").glob("*.csv.gz"))
    t = pd.concat([pd.read_csv(f) for f in fs])
    s = t[t["serie"] == "squeeze:gex"].assign(date=lambda x: pd.to_datetime(x["date"])).set_index("date")["valeur"]
    s = s.sort_index().astype(float)
    rang = s.rolling(253, min_periods=200).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True)
    return rang


def main():
    d = SD.minutes("NQ", chemin=sys.argv[1], debut="2011-01-01")
    jours = pd.DatetimeIndex(d["jours"].astype("datetime64[D]"))
    O, H, L, C = d["o"], d["h"], d["l"], d["c"]
    ok = d["complete"] & ~d["ech"]
    pm = d["prec_meme"]
    ech = float(d["pref"]) / O[:, 0] * float(d["pt"])
    r = gex().dropna()
    i = r.index.searchsorted(jours, side="left") - 1                 # derniere valeur datee avant la seance
    g = np.where(i >= 0, r.values[np.maximum(i, 0)], np.nan)
    age = (jours - r.index[np.maximum(i, 0)]).days
    g = np.where(age <= 7, g, np.nan)
    sens_jour = np.sign(C[:, 359] - O[:, 0])
    hi, lo = H[:, :240].max(1), L[:, :240].min(1)
    place = (C[:, 239] - lo) / np.where(hi > lo, hi - lo, np.nan)
    pos = np.where(place > PLACE, 1, np.where(place < 1 - PLACE, -1, 0))
    prevC = np.where(pm >= 0, C[np.maximum(pm, 0), 389], np.nan)
    ecart = O[:, 0] / prevC - 1
    rg_ecart = pd.Series(ecart).rolling(253, min_periods=200).apply(lambda x: (x[:-1] < x[-1]).mean() if np.isfinite(x[-1]) else np.nan, raw=True).values
    fin = (C[:, 389] - O[:, 360]) * ech
    apm = (O[:, 360] - O[:, 240]) * ech
    ouv = (O[:, 30] - O[:, 0]) * ech
    regles = {
        "L1 fin de séance, gamma bas": np.where(g <= 0.2, sens_jour, 0) * fin,
        "L2 fin de séance, gamma haut": np.where(g >= SEUIL, -sens_jour, 0) * fin,
        "L3 après-midi, gamma bas": np.where(g <= 0.4, pos, 0) * apm,
        "L4 après-midi, gamma haut": np.where(g >= 0.6, -pos, 0) * apm,
        "L5 ouverture après la nuit": np.where(rg_ecart >= 0.9, -1, np.where(rg_ecart <= 0.1, 1, 0)) * ouv,
    }
    actif = {
        "L1 fin de séance, gamma bas": (g <= 0.2) & (sens_jour != 0),
        "L2 fin de séance, gamma haut": (g >= SEUIL) & (sens_jour != 0),
        "L3 après-midi, gamma bas": (g <= 0.4) & (pos != 0),
        "L4 après-midi, gamma haut": (g >= 0.6) & (pos != 0),
        "L5 ouverture après la nuit": (rg_ecart >= 0.9) | (rg_ecart <= 0.1),
    }
    seuil = NormalDist().inv_cdf(1 - 0.05 / 5)
    L = ["# Partie 11 : règles de la recherche sur l'ère 0DTE", "",
         f"Minutes du NQ, {ok.sum()} séances jouables ; $ pour 1 MNQ au prix d'aujourd'hui, frais de 3 $ compris. "
         f"Barre sur l'ère 0DTE (depuis le {DEBUT_0DTE}) : t ≥ {seuil:.2f}, gain moyen positif, 3 années gagnantes sur 5.",
         "", "| Règle | Période | Trades | Total | Moyenne | t | Années |", "|---|---|---|---|---|---|---|"]
    for nom, x in regles.items():
        a = actif[nom] & ok & np.isfinite(x)
        net = pd.Series(np.where(a, x - FRAIS, np.nan), index=jours).dropna()
        for per, m in (("2011 - mai 2022", net.index < DEBUT_0DTE), ("ère 0DTE", net.index >= DEBUT_0DTE)):
            y = net[m]
            n, moy = len(y), y.mean()
            t = moy / y.std(ddof=1) * np.sqrt(n) if n > 1 else np.nan
            ans = y.groupby(y.index.year).sum()
            txt = ", ".join(f"{k} {v:+,.0f}" for k, v in ans.items()) if per == "ère 0DTE" else ""
            verdict = ""
            if per == "ère 0DTE":
                verdict = " **PASSE**" if (t >= seuil and moy > 0 and (ans > 0).sum() >= 3) else " échoue"
            L.append(f"| {nom} | {per}{verdict} | {n} | {y.sum():+,.0f} $ | {moy:+,.1f} $ | {t:+.2f} | {txt} |")
    out = ICI / "resultats/partie11"
    out.mkdir(parents=True, exist_ok=True)
    (out / "gamma_0dte.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
