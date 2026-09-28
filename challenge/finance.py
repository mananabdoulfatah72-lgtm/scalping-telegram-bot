#!/usr/bin/env python3
"""Apres la validation : combien le compte finance Phidias 50K rapporte en 12 mois, avec le meme bot.

Hypotheses (a verifier chez Phidias) : limite de perte 2 500 $ sous le plus haut de fin de journee,
bloquee a 50 100 $ une fois le solde monte a 52 600 $ ; retrait possible chaque mois de tout ce qui
depasse 52 600 $ (on garde 2 500 $ de coussin au-dessus de la limite bloquee), si la meilleure
journee depuis le dernier retrait ne depasse pas 30 % du gain de la periode ; tu touches 80 % du retrait.
Un compte qui touche sa limite est perdu : les retraits s'arretent.

Deux bots : 'zone' (zone de bruit MNQ seule) et 'multi' (zone de bruit + un panier de sources de
nuit : tendance + achat, veille de la Fed, actions pilotees par la volatilite, carry). Le panier
contient des sources qui ont echoue de peu aux tests du fonds : c'est un choix optimiste.

Lancer depuis ce dossier : python3 finance.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import bot_challenge as B

sys.path.insert(0, str(B.R / "fonds"))
PART = 0.80


def panier(d):
    """Sources de nuit, chacune a meme risque, puis ramenees a 12 % par an (connu la veille)."""
    import sources as SRC
    from moteur import au_risque
    sl = {}
    for f in (SRC.veille_fomc, SRC.vol_geree, SRC.carry40):
        x = au_risque(f()[0], 0.10)
        sl[f.__name__] = x[x.index >= x.ne(0).idxmax()]
    sl["melange"] = d["melange"]
    p = pd.DataFrame(sl).reindex(d.index).mean(axis=1).fillna(0)
    return au_risque(p, 0.12).reindex(d.index).fillna(0)


def une_tentative_multi(d, i0, regle, f):
    return B.une_tentative(d, i0, regle, f, True)


def finance(d, i0, f, avec_nuit):
    g, p, s1, mel = (d[c].values for c in ("gain", "pire", "risque1", "melange"))
    sig = 0.12 / np.sqrt(B.AN)
    solde = haut = 50000.0
    recu, meilleur, gain_periode = 0.0, 0.0, 0.0
    for j, k in enumerate(range(i0, min(len(g), i0 + B.AN))):
        plancher = 50100.0 if haut >= 52600 else haut - 2500
        coussin = solde - plancher
        budget = f * coussin
        part = 0.5 if avec_nuit else 1.0
        n = int(np.clip(np.floor(part * budget / s1[k]), 0, 50)) if s1[k] > 0 else 0
        expo = (1 - part) * budget / (sig * 50000) if avec_nuit else 0.0
        jour = n * g[k] + expo * mel[k] * 50000
        creux = n * p[k] + min(0.0, expo * mel[k] * 50000)
        if solde + creux <= plancher or solde + jour <= plancher:
            return recu, True
        solde += jour
        haut = max(haut, solde)
        meilleur, gain_periode = max(meilleur, jour), gain_periode + jour
        if (j + 1) % 21 == 0 and solde > 52600 and gain_periode > 0 and meilleur <= 0.3 * gain_periode:
            retrait = solde - 52600
            recu += PART * retrait
            solde -= retrait
            meilleur, gain_periode = 0.0, 0.0
    return recu, False


def main():
    d = B.donnees()
    dm = d.copy()
    dm["melange"] = panier(d)
    regle = B.REGLES["Phidias 50K"]
    for nom, dd, nuit in [("zone de bruit seule", d, False), ("zone + melange 50/50", d, True), ("multi (zone + panier)", dm, True)]:
        for f in (0.15, 0.25):
            une = np.array([B.une_tentative(dd, i, regle, f, nuit)[0] for i in range(0, len(dd) - B.AN, 5)])
            res = [finance(dd, i, f, nuit) for i in range(0, len(dd) - B.AN, 5)]
            recu = np.array([r for r, _ in res])
            perdu = np.array([p for _, p in res])
            print(f"{nom:24s} f={f:.2f} | challenge : reussi {np.mean(une == 1):4.0%}, saute {np.mean(une == -1):4.0%}"
                  f" | compte finance, 12 mois : recu en moyenne {recu.mean():6,.0f} $ | median {np.median(recu):6,.0f} $"
                  f" | rien touche {np.mean(recu == 0):4.0%} | compte perdu {perdu.mean():4.0%}")


if __name__ == "__main__":
    main()
