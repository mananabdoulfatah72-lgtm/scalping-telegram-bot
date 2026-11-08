#!/usr/bin/env python3
"""Etape 1 de l'arene (version corrigee apres la double relecture) : rejouer chaque bot jour par jour (2014 - 2 nov. 2026),
1 MNQ, limite du bot 400 $, avec les regles du compte finance Bulenox (Master 50K, Option 2), et l'afficher en direct."""
import json
import os
import sys
import time

import numpy as np

import bots as BT
from direct import Direct

DOSSIER = sys.argv[1]
DX = Direct(DOSSIER)
DX.maj(force=True, phase="Étape 1 : préparation", detail="lecture de 15 ans de minutes du NQ et des journaux des bots")
DX.dire("Je lis les minutes du NQ (2011 - 2 nov. 2026) et je reconstruis les trois bots (moteur corrigé après la double relecture).")
B = BT.Base(os.environ["CACHE_DOSSIER"])
PAS = 5
jours = [B.J[s] for s in B.test][::PAS]
DX.maj(force=True, jours=jours, curseur=0, pied=[
    ("compte", "Master 50K Option 2 : plancher 2 500 $ en fin de journée, bloqué à 50 100 $ ; limite de la firme 1 100 $/jour"),
    ("retraits", "10 jours de trading, 1 000 $ minimum, 52 600 $ gardés, 3 premiers plafonnés à 1 500 $, constance 40 % ; compte grillé = requalification payée (100 $ par mois, 148 $ d'activation)"),
    ("bots", "1 MNQ, limite du bot 400 $, 3 $ de frais, 1 point de glissement à la sortie forcée"),
    ("période", f"{B.J[B.test[0]]} → {B.J[B.test[-1]]} ({len(B.test)} séances)")])
BOTS = [("st", "Supertrend NQ", BT.supertrend, "#3cc8ff"), ("zone", "Bot 3 en 1 (zone)", BT.zone, "#b48cff"), ("xgb", "XGBoost NQ", BT.xgboost, "#ffa028")]
sortie = {}
for k, (ident, nom, f, coul) in enumerate(BOTS):
    DX.dire(f"{nom} : je reconstruis tous ses trades et je les rejoue minute par minute (limite du jour, plancher du compte).", "c")
    tr = f(B)
    res, dip, ntr = BT.journees(B, tr, 1, 400.0)
    j = res[B.test]; cum = np.cumsum(j)
    L = DX.ligne(ident, nom, "référence", coul)
    DX.dire(f"{nom} : {len(tr):,} trades ; je rejoue les {len(j):,} séances de 2014 à aujourd'hui.".replace(",", " "))
    annee = None
    for i in range(len(j)):
        a = B.J[B.test[i]][:4]
        if a != annee:
            if annee:
                DX.dire(f"{nom} : {annee} terminée, {j[np.array([B.J[s][:4] == annee for s in B.test])].sum():+,.0f} $ sur l'année.".replace(",", " "))
            annee = a
        if i % (PAS * 6) == 0 or i == len(j) - 1:
            L["courbe"] = [round(float(x), 1) for x in cum[: i + 1: PAS]]
            DX.maj(relief=True, curseur=i // PAS, progression=(k + (i + 1) / len(j)) / len(BOTS), phase=f"Étape 1 : rejeu de {nom}",
                   detail=f"séance du {B.J[B.test[i]]} · cumul {cum[i]:+,.0f} $".replace(",", " "))
            time.sleep(0.04)
    m = BT.mesures(B, res, dip, ntr)
    L["stats"] = m; L["tri"] = m["survie_60"] - m["grilles_an"]
    sortie[ident] = dict(nom=nom, **m)
    DX.dire(f"{nom} : {m['par_seance']:+.1f} $ par séance, t {m['t']:.2f} (depuis 2023 : {m['t_apres']:.2f}) ; compte neuf encore en vie après 60 séances "
            f"{m['survie_60']:.0%}, grillé dans l'année {m['grille_250']:.0%} ; vie réelle : net {m['net_an']:,.0f} $ par an, {m['grilles_an']:.2f} masters grillés par an ; "
            f"du 11 août au 2 nov. : {m['periode']:+,.0f} $.".replace(",", " "), "h" if m["grille_250"] < 0.3 else "a")
    DX.maj(relief=True, force=True)
json.dump(sortie, open(os.path.join(DOSSIER, "etape1.json"), "w"))
DX.dire("Étape 1 terminée. Étape suivante : les variantes.", "a")
DX.maj(force=True, phase="Étape 1 terminée", detail="trois bots rejoués sur le compte financé", progression=1.0)
