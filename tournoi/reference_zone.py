#!/usr/bin/env python3
"""Zone de bruit de reference, meme mesure que le tournoi (rendements quotidiens nets en % du prix), sur 2011-2022,
2017-2022, 2023-2026 et 2011-2026, et somme des rendements par annee sur 2023-2026. Information de l'etape 4 du
README ; ecrit reference_zone_coffre.txt.

Lancer depuis ce dossier : python3 reference_zone.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

import concurrents as K
from explorer import charger, t_stat, zone_reference

lignes = ["Information (README, etape 4) : la zone de bruit de reference, meme mesure (rendements quotidiens nets en % du prix)"]
for marche, fichier in (("NQ", "nasdaq100"), ("ES", "sp500")):
    J, O, H, L, C, P, X = charger(fichier, fin=None)
    ok = K.st.journees_completes(P) & ~X["echeance"]
    z = zone_reference(J, O, H, L, C, P, X, K.st.cout_aller_retour(fichier), ok)
    for nom, a, b in (("2011-2022", 2011, 2022), ("2017-2022", 2017, 2022), ("2023-2026", 2023, 2026), ("2011-2026", 2011, 2026)):
        x = z[(z.index.year >= a) & (z.index.year <= b)]
        lignes.append(f"  {marche} {nom} : t {t_stat(x.values):+.2f}")
    an = z[z.index.year >= 2023].groupby(z.index[z.index.year >= 2023].year).sum()
    lignes.append(f"  {marche} 2023-2026 par annee (somme des rendements) : " + " ".join(f"{a}:{v:+.1%}" for a, v in an.items()))
texte = "\n".join(lignes)
print(texte)
(Path(__file__).resolve().parent / "reference_zone_coffre.txt").write_text(texte + "\n")
