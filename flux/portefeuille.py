#!/usr/bin/env python3
"""Partie 13 (flux/README.md) : portefeuille des meilleures candidates deja figees (S2b, H1, H5, H12, F3, zone, R1, R2,
L2), choisies par la regle fixee le 30 octobre 2026 sur l'ere 0DTE, puis mesure par annee et sur des challenges Bulenox
50K simules. Le choix se fait sur les annees memes ou on le mesure : resultat flatteur par construction.

Lancer : python3 flux/portefeuille.py <minutes NQ (t,o,h,l,c,v,contrat), au moins depuis juin 2021>"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.argv, chemin = sys.argv[:1], sys.argv[1]
import veille as V  # noqa: E402

DEBUT_0DTE = "2022-05-16"
DEPART, OBJECTIF, PERTE_MAX, LIMITE_JOUR = 50_000.0, 3_000.0, 2_500.0, 1_100.0


def challenges(x, n):
    """Un depart a chaque seance : 1 valide, -1 perdu, 0 pas fini ; et le nombre de seances."""
    x = np.maximum(np.asarray(x) * n, -LIMITE_JOUR)
    res, du = [], []
    for s0 in range(len(x)):
        solde = haut = DEPART
        r, k = 0, s0
        for k in range(s0, len(x)):
            solde += x[k]
            haut = max(haut, solde)
            if solde >= DEPART + OBJECTIF:
                r = 1
                break
            if solde <= min(haut - PERTE_MAX, DEPART + 100):
                r = -1
                break
        res.append(r)
        du.append(k - s0 + 1)
    return np.array(res), np.array(du)


def main():
    d = V.SD.minutes("NQ", chemin=chemin, debut="2021-06-01")
    M = V.gains(d)
    ok = pd.Series(d["complete"] & ~d["ech"], index=M.index)
    M = M[(M.index >= DEBUT_0DTE) & ok]
    L = ["# Partie 13 : portefeuille des meilleures candidates (ère 0DTE)", "",
         f"{len(M)} séances du {M.index[0].date()} au {M.index[-1].date()}, 1 MNQ par règle, frais compris, $ au prix "
         "d'aujourd'hui. Règle d'entrée : t ≥ 1 sur les séances jouées et au moins 3 années gagnantes sur 5.", "",
         "| Candidate | Séances jouées | Total | Par séance jouée | t | Années gagnantes | Retenue |", "|---|---|---|---|---|---|---|"]
    retenues = []
    for k in M.columns:
        x = M[k].dropna()
        t = x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 1 else np.nan
        ans = x.groupby(x.index.year).sum()
        garde = bool(t >= 1 and (ans > 0).sum() >= 3)
        if garde:
            retenues.append(k)
        L.append(f"| {V.NOMS.get(k, k)} | {len(x)} | {x.sum():+,.0f} $ | {x.mean():+,.1f} $ | {t:+.2f} | "
                 f"{(ans > 0).sum()} sur {len(ans)} | {'**oui**' if garde else 'non'} |")
    if not retenues:
        L += ["", "**Aucune candidate ne remplit la règle : pas de portefeuille.**"]
    else:
        p = M[retenues].fillna(0).sum(axis=1)
        jouees = (M[retenues].notna()).any(axis=1)
        t = p.mean() / p.std(ddof=1) * np.sqrt(len(p))
        cum = p.cumsum()
        L += ["", f"## Portefeuille : {', '.join(V.NOMS.get(k, k) for k in retenues)}", "",
              f"- Séances avec au moins un trade : {jouees.sum()} sur {len(p)} ({jouees.mean():.0%}).",
              f"- Total : {p.sum():+,.0f} $ ; par séance : {p.mean():+,.1f} $ ; t {t:+.2f}.",
              f"- Pire séance : {p.min():+,.0f} $ ; plus forte baisse du cumul : {(cum - cum.cummax()).min():+,.0f} $.", "",
              "| Année | Total | Séances gagnantes |", "|---|---|---|"]
        for an, x in p.groupby(p.index.year):
            L.append(f"| {an} | {x.sum():+,.0f} $ | {(x > 0).sum()} sur {(x != 0).sum()} jouées |")
        L += ["", "Challenges Bulenox 50K simulés (un départ à chaque séance, limite du jour arrondie à la clôture) :", "",
              "| MNQ par règle | Validés | Perdus | Pas finis | Séances pour valider (médiane) |", "|---|---|---|---|---|"]
        for n in (1, 2, 3):
            r, du = challenges(p.values, n)
            L.append(f"| {n} | {np.mean(r == 1):.0%} | {np.mean(r == -1):.0%} | {np.mean(r == 0):.0%} | "
                     f"{np.median(du[r == 1]) if (r == 1).any() else float('nan'):.0f} |")
    out = ICI / "resultats/partie13"
    out.mkdir(parents=True, exist_ok=True)
    (out / "portefeuille.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
