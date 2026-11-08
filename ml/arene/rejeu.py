#!/usr/bin/env python3
"""Etape 1 de l'arene : rejouer chaque bot jour par jour (2014 - 2 nov. 2026), 1 MNQ, limite du bot 400 $, avec les regles
du compte finance Bulenox (Master 50K, Option 2), et l'afficher en direct dans la page de l'arene."""
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
DX.dire("Je lis les minutes du NQ (2011 - 2 nov. 2026) et je reconstruis les trois bots.")
B = BT.Base(os.environ["CACHE_DOSSIER"])
PAS = 5
jours = [B.J[s] for s in B.test][::PAS]
DX.maj(force=True, jours=jours, curseur=0, pied=[("compte", "Master 50K Option 2 : plancher 2 500 $ en fin de journée, bloqué à 50 100 $ ; limite de la firme 1 100 $/jour ; constance 40 % au retrait"),
                                                 ("bots", "1 MNQ, limite du bot 400 $, 3 $ de frais"), ("période", f"{B.J[B.test[0]]} → {B.J[B.test[-1]]} ({len(B.test)} séances)")])
BOTS = [("st", "Supertrend NQ", BT.supertrend, "#3cc8ff"), ("zone", "Bot 3 en 1 (zone)", BT.zone, "#b48cff"), ("xgb", "XGBoost NQ", BT.xgboost, "#ffa028")]
sortie = {}
for k, (ident, nom, f, coul) in enumerate(BOTS):
    DX.dire(f"{nom} : je reconstruis tous ses trades et je les rejoue minute par minute (limite du jour, plancher du compte).", "c")
    tr = f(B)
    res, dip, ntr = BT.journees(B, tr, 1, 400.0)
    j = res[B.test]; d = dip[B.test]; cum = np.cumsum(j)
    L = DX.ligne(ident, nom, "référence", coul)
    DX.dire(f"{nom} : {len(tr):,} trades depuis 2011 ; je rejoue les {len(j):,} séances de 2014 à aujourd'hui.".replace(",", " "))
    # rejeu visible : la crete avance seance par seance ; vie reelle du compte finance (retraits au-dessus de 52 600 $, compte
    # grille remplace le lendemain), annoncee au fil de l'eau
    solde, haut, base, meilleur, depuis, ncompte, debut, retire, annee = 50000.0, 50000.0, 50000.0, 0.0, 0, 1, 0, 0.0, 2014
    for i in range(len(j)):
        an_i = int(B.J[B.test[i]][:4])
        if an_i != annee:
            DX.dire(f"{nom} : fin {annee}, {retire:,.0f} $ retirés depuis 2014, compte n° {ncompte}.".replace(",", " ")); annee = an_i
        plancher = min(haut - 2500.0, 50100.0)
        if solde + d[i] <= plancher:
            DX.dire(f"{nom} : compte financé n° {ncompte} grillé le {B.J[B.test[i]]} (après {i - debut} séances) ; un nouveau compte repart le lendemain.", "b")
            ncompte += 1; solde, haut, base, meilleur, depuis, debut = 50000.0, 50000.0, 50000.0, 0.0, 0, i + 1
            continue
        solde += j[i]; depuis += 1; meilleur = max(meilleur, j[i]); haut = max(haut, solde)
        if depuis >= 20 and solde > 52600 and solde - base > 0 and meilleur <= 0.4 * (solde - base):
            retire += solde - 52600; solde = base = 52600.0; meilleur = 0.0; depuis = 0
        if i % (PAS * 6) == 0 or i == len(j) - 1:
            L["courbe"] = [round(float(x), 1) for x in cum[: i + 1: PAS]]
            DX.maj(relief=True, curseur=i // PAS, progression=(k + (i + 1) / len(j)) / len(BOTS),
                   phase=f"Étape 1 : rejeu de {nom}", detail=f"séance du {B.J[B.test[i]]} · cumul {cum[i]:+,.0f} $ · compte n° {ncompte} · retiré {retire:,.0f} $".replace(",", " "))
            time.sleep(0.04)
    m = BT.mesures(B, res, dip)
    L["stats"] = m; L["tri"] = m["survie_60"] + m["t"] / 100
    sortie[ident] = dict(nom=nom, **m)
    DX.dire(f"{nom} : {m['par_seance']:+.1f} $ par séance, t {m['t']:.2f} (depuis 2023 : {m['t_apres']:.2f}) ; compte neuf encore en vie après 60 séances : "
            f"{m['survie_60']:.0%} ; en vrai (retraits réguliers) : {m['retire_an']:,.0f} $ retirés par an, {m['grilles']} comptes grillés en 13 ans ; "
            f"du 11 août au 2 nov. : {m['periode']:+,.0f} $.".replace(",", " "), "h" if m["survie_60"] > 0.8 and m["grilles"] <= 1 else "a")
    DX.maj(relief=True, force=True)
json.dump(sortie, open(os.path.join(DOSSIER, "etape1.json"), "w"))
DX.dire("Étape 1 terminée. Étape suivante : les variantes, avec leurs règles écrites avant le calcul.", "a")
DX.maj(force=True, phase="Étape 1 terminée", detail="classement des trois bots sur le compte financé ; préparation des variantes", progression=1.0)
