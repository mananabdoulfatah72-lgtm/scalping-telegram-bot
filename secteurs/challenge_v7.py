#!/usr/bin/env python3
"""La version 7 peut-elle valider un challenge 50K ? Rejoue ses vrais rendements quotidiens (frais compris,
sans les interets des liquidites : un compte de prop firm n'en paie pas) sur des regles de challenge.

- Une tentative commence chaque semaine ; on regarde si elle reussit, echoue ou n'a pas fini en 12 mois.
- Exposition fixe : m x la version 7 sur 50 000 $ (m = 1 : 25 000 $ en actions, 25 000 $ non investis).
- Pertes verifiees en fin de journee seulement (optimiste : les firmes les verifient en cours de journee).
- "Sans avantage" : memes mouvements, rendement moyen ramene a zero (ce que donne le hasard).

Regles (a verifier chez chaque firme, septembre 2026) :
- futures (Topstep, Apex, Phidias 50K) : la version 7 achete des ACTIONS et les garde un mois ; ces
  comptes ne traitent que des futures, et Topstep et Apex interdisent de garder la nuit. Le calcul
  "Phidias" ci-dessous suppose quand meme que c'est permis, pour montrer l'effet de la perte max.
- actions en CFD, compte "swing" (nuit et week-end permis) : phase 1 +10 %, phase 2 +5 %, perte max
  10 % du depart (fixe), perte journaliere 5 %. Les frais de financement des CFD (environ 5-8 %/an
  sur le montant investi) ne sont PAS comptes : c'est optimiste.

Lancer depuis ce dossier : python3 challenge_v7.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from strategies import CASH, DEBUT_HIST, FENETRES, Etude, simuler  # noqa: E402

CAPITAL = 50_000.0
AN = 252
REGLES = {
    "Phidias 50K (si la nuit et les actions etaient permises)":
        [dict(objectif=4000, perte=2500, suiveuse=True, jour_max=None)],
    "CFD actions swing 2 phases (+10 % puis +5 %)":
        [dict(objectif=5000, perte=5000, suiveuse=False, jour_max=2500),
         dict(objectif=2500, perte=5000, suiveuse=False, jour_max=2500)],
}
EXPOSITIONS = [0.25, 0.5, 1.0]


def rendements_v7(debut_hist, de, a):
    et = Etude("XLK", debut_hist=debut_hist)
    w = et.poids(7)
    net, contrib = simuler(et.r, w, et.frais)
    x = net - contrib[CASH]                          # sans les interets des liquidites
    return x[(x.index > de) & (x.index <= a)]


def phase(r, i0, regle, m, fin):
    """+1 reussie, -1 perdue, 0 pas finie avant fin ; et le jour ou elle s'arrete."""
    solde = haut = CAPITAL
    for k in range(i0, fin):
        jour = m * r[k] * CAPITAL
        if regle["jour_max"] and jour <= -regle["jour_max"]:
            return -1, k
        solde += jour
        plancher = (haut if regle["suiveuse"] else CAPITAL) - regle["perte"]
        if regle["suiveuse"]:
            plancher = min(plancher, CAPITAL)             # la perte max suiveuse se bloque au depart
        if solde <= plancher:
            return -1, k
        haut = max(haut, solde)
        if solde - CAPITAL >= regle["objectif"]:
            return 1, k
    return 0, fin


def tentatives(r, phases, m):
    res = []
    for i0 in range(0, len(r) - AN, 5):
        k, issue = i0, 1
        for regle in phases:
            issue, k = phase(r, k, regle, m, i0 + AN)
            if issue != 1:
                break
            k += 1
        res.append((issue, k - i0))
    return pd.DataFrame(res, columns=["issue", "jours"])


def main():
    fen5 = FENETRES["5ans"]
    series = {"5 ans (2021-2026, periode ou la version 7 a ete choisie)": rendements_v7(fen5, pd.Timestamp("2021-09-30"), pd.Timestamp("2026-09-25")),
              "avant (2006-2021, hors fenetre)": rendements_v7(DEBUT_HIST, pd.Timestamp("2006-01-31"), pd.Timestamp("2021-09-30"))}
    for nom_s, x in series.items():
        r = x.values
        r0 = r - r.mean()
        print(f"\n=== {nom_s} : {len(r)} seances, version 7 sans interets {(1 + x).prod() ** (AN / len(x)) - 1:+.1%}/an,"
              f" ecart-type d'une journee {r.std() * CAPITAL:,.0f} $ pour m = 1")
        for nom_r, phases in REGLES.items():
            print(f"  {nom_r}")
            for m in EXPOSITIONS:
                t, t0 = tentatives(r, phases, m), tentatives(r0, phases, m)
                ok = t["issue"] == 1
                print(f"    m = {m:4.2f} ({m * 25_000:6,.0f} $ en actions) : reussi {ok.mean():4.0%} | perdu {(t['issue'] == -1).mean():4.0%}"
                      f" | pas fini en 12 mois {(t['issue'] == 0).mean():4.0%}"
                      f" | sans avantage : reussi {(t0['issue'] == 1).mean():4.0%}"
                      + (f" | {t.loc[ok, 'jours'].median():.0f} seances en mediane si reussi" if ok.any() else ""))


if __name__ == "__main__":
    main()
