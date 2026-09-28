#!/usr/bin/env python3
"""Bot de challenge 50K : zone de bruit MNQ (intraday) et melange tendance + achat (garde la nuit),
dimensionnes avec un COUSSIN : chaque jour, le risque pris est une fraction f de la distance entre le
solde et la limite de perte (plus on s'eloigne de la limite, plus on prend ; plus on s'en approche,
moins on prend). Rejoue sur les vrais prix : une serie de tentatives commence chaque jour de
l'historique ; apres un echec, une nouvelle tentative commence le lendemain ; on regarde si un
challenge est reussi dans les 12 mois, et combien de tentatives il a fallu.

Regles (septembre 2026, a verifier chez chaque firme) :
- Topstep 50K : objectif 3 000 $, perte max 2 000 $ sous le plus haut de fin de journee (verifiee en
  cours de journee), perte journaliere 1 000 $ (trade coupe), meilleure journee <= 50 % du gain,
  intraday seulement.
- Apex 50K : objectif 3 000 $, perte max 2 500 $ sous le plus haut (bloquee a 50 100 $), 30 jours
  (21 seances) par tentative, intraday seulement.
- Phidias 50K : objectif 4 000 $, perte max 2 500 $ sous le plus haut de fin de journee, pas de
  limite de temps ; positions de nuit supposees permises (a verifier).
Limites : le melange est suppose divisible (pas de contrats entiers) : c'est optimiste.

Lancer depuis ce dossier : python3 bot_challenge.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "intraday"))
sys.path.insert(0, str(R / "tendance"))
sys.path.insert(0, str(R / "fonds"))

REGLES = {
    "Topstep 50K": dict(objectif=3000, perte=2000, blocage=None, jours=None, jour_max=1000, regularite=0.5, nuit=False),
    "Apex 50K": dict(objectif=3000, perte=2500, blocage=50100, jours=21, jour_max=None, regularite=None, nuit=False),
    "Phidias 50K": dict(objectif=4000, perte=2500, blocage=None, jours=None, jour_max=None, regularite=None, nuit=True),
}
FRACTIONS = [0.15, 0.25, 0.35]      # risque d'une journee (1 ecart-type) = f x coussin
AN = 252


def donnees():
    from analyse import calculer
    import sources as SRC
    import systeme as S
    from moteur import au_risque, portefeuille
    jours, res, _ = calculer("nasdaq100")
    z = res["Zone de bruit"]
    gain = z["dollars"].reindex(jours).fillna(0)                        # $ pour 1 MNQ, frais compris
    pire = (z["pire"] * 2.0).reindex(jours).fillna(0).clip(upper=0)      # pire moment du jour, $ pour 1 MNQ
    pire = np.minimum(pire, np.minimum(gain, 0))
    risque1 = gain.rolling(60, min_periods=40).std().shift(1)           # ecart-type prevu, $ par MNQ et par jour
    r = SRC.rendements()
    m = lambda net: au_risque(net, 0.10)[lambda x: x.index >= x.ne(0).idxmax()]
    mel = portefeuille({"t": m(S.backtest(r)[0]), "a": m(S.backtest(r, toujours_acheteur=True)[0])})
    mel = mel.reindex(jours).fillna(0)                                   # rendement pour 12 % de risque par an
    d = pd.DataFrame({"gain": gain, "pire": pire, "risque1": risque1, "melange": mel}).dropna()
    return d


def une_tentative(d, i0, regle, f, avec_melange):
    """Renvoie (resultat, jour de fin) : +1 reussi, -1 perdu, 0 temps ecoule."""
    g, p, s1, mel = (d[c].values for c in ("gain", "pire", "risque1", "melange"))
    solde = haut = 50000.0
    meilleur, jmax = 0.0, (regle["jours"] or 10 ** 6)
    sig_mel = 0.12 / np.sqrt(AN)                                         # ecart-type journalier du melange
    for k in range(i0, min(len(g), i0 + jmax)):
        plancher = haut - regle["perte"]
        if regle["blocage"]:
            plancher = min(plancher, regle["blocage"])
        coussin = solde - plancher
        budget = f * coussin
        part_z = 0.5 if avec_melange else 1.0
        n = int(np.clip(np.floor(part_z * budget / s1[k]), 0, 50)) if s1[k] > 0 else 0
        expo = (1 - part_z) * budget / (sig_mel * 50000) if avec_melange else 0.0
        jour = n * g[k] + expo * mel[k] * 50000
        creux = n * p[k] + min(0.0, expo * mel[k] * 50000)
        if regle["jour_max"] and creux <= -regle["jour_max"]:
            jour = max(jour, -regle["jour_max"])
        if solde + creux <= plancher or solde + jour <= plancher:
            return -1, k
        solde += jour
        meilleur = max(meilleur, jour)
        haut = max(haut, solde)
        profit = solde - 50000
        if profit >= regle["objectif"] and (not regle["regularite"] or meilleur <= regle["regularite"] * profit):
            return 1, k
    return 0, min(len(g), i0 + jmax) - 1


def sur_un_an(d, regle, f, avec_melange):
    """Pour chaque jour de depart : tentatives successives pendant 12 mois."""
    res = []
    for i0 in range(0, len(d) - AN, 5):                                  # un depart par semaine
        k, n_tent, ok = i0, 0, False
        while k < i0 + AN:
            n_tent += 1
            r, fin = une_tentative(d, k, regle, f, avec_melange)
            if r == 1 and fin < i0 + AN:
                ok = True
                break
            k = fin + 1
            if r == 0 and regle["jours"] is None:
                break
        res.append((ok, n_tent, (fin - i0 + 1) if ok else np.nan))
    return pd.DataFrame(res, columns=["reussi", "tentatives", "jours"])


def sans_avantage(d):
    """Meme bot, memes mouvements, mais gain moyen ramene a zero (reference : ce que donnent les
    tentatives repetees sans aucun avantage)."""
    z = d.copy()
    actif = z["gain"] != 0
    moy = z.loc[actif, "gain"].mean()
    z.loc[actif, "gain"] -= moy
    z.loc[actif, "pire"] -= moy
    z["melange"] -= z["melange"].mean()
    return z


def main():
    d = donnees()
    d0 = sans_avantage(d)
    print(f"Historique : {d.index[0].date()} -> {d.index[-1].date()} ({len(d)} seances), un depart par semaine\n")
    for nom, regle in REGLES.items():
        for mel in ([False, True] if regle["nuit"] else [False]):
            quoi = "zone de bruit + melange" if mel else "zone de bruit MNQ"
            for f in FRACTIONS:
                une = [une_tentative(d, i, regle, f, mel)[0] for i in range(0, len(d) - AN, 5)]
                an = sur_un_an(d, regle, f, mel)
                an0 = sur_un_an(d0, regle, f, mel)
                print(f"{nom:12s} {quoi:24s} f={f:.2f} | 1 tentative : reussie {np.mean(np.array(une) == 1):4.0%}, perdue {np.mean(np.array(une) == -1):4.0%}"
                      f" | en 12 mois : valide {an['reussi'].mean():4.0%} (sans avantage {an0['reussi'].mean():4.0%})"
                      f" | tentatives {an['tentatives'].mean():.1f} (max {an['tentatives'].max()})"
                      f" | {an['jours'].median():.0f} seances en mediane")
        print()


if __name__ == "__main__":
    main()
