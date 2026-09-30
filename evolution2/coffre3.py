#!/usr/bin/env python3
"""Tournoi n°3, etape 4 (README.md) : coffre 2023-2026, ouvert une seule fois, pour les survivants de explorer3.py.
Passe si t >= seuil de Bonferroni (5 % unilateral, m = nombre de survivants) et au moins 3 annees positives sur 4.

Lancer depuis ce dossier, apres explorer3.py : python3 coffre3.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

import tournoi3 as T
from explorer import charger, t_stat
from explorer3 import MARCHES, NOMS, murs

ICI = Path(__file__).resolve().parent


def main():
    surv = json.loads((ICI / "survivants3.json").read_text())
    if not surv:
        print("Aucun survivant : le coffre reste ferme.")
        return
    m = len(surv)
    seuil = float(norm.ppf(1 - 0.05 / m))
    Q = T.lire_quotidien()
    lignes, sortie = [f"Coffre 2023-2026, {m} survivant(s), seuil de Bonferroni t >= {seuil:.2f}"], []
    for marche in sorted({s["marche"] for s in surv}):
        fichier, pt = MARCHES[marche]
        J, O, H, L, C, P, X = charger(fichier, fin=None)
        res, ok, _ = T.toutes(J, O, H, L, C, P, X, T.st.cout_aller_retour(fichier), Q, murs(marche, J))
        j = pd.DatetimeIndex(J)
        c = ok & (j.year >= 2023)
        for s in (s for s in surv if s["marche"] == marche):
            r = res[s["code"]][c] / O[c, 0]
            ans = pd.Series(res[s["code"]][c] * pt, index=j[c]).groupby(j[c].year).sum()
            t = t_stat(r)
            passe = t >= seuil and (ans > 0).sum() >= 3
            sortie.append({"code": s["code"], "marche": marche, "t": t, "annees": {str(a): float(v) for a, v in ans.items()}, "passe": bool(passe)})
            lignes.append(f"  {s['code']} {NOMS[s['code']]} {marche} : t {t:+.2f} | " + " ".join(f"{a}:{v:+,.0f}$" for a, v in ans.items())
                          + f" (1 micro) | {'PASSE' if passe else 'rejete'}")
    print("\n".join(lignes))
    (ICI / "coffre3.txt").write_text("\n".join(lignes) + "\n")
    (ICI / "coffre3.json").write_text(json.dumps(sortie, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
