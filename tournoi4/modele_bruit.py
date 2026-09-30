#!/usr/bin/env python3
"""Question de l'utilisateur : le modele appris fait t +9,7 sur minutes melangees ; peut-on le trader ?
On entraine le modele (memes regles que la strategie 8) sur chacune des 20 versions melangees, annee par annee sur
le passe seulement, puis on le fait trader sur les VRAIES seances : 2013-2022 et 2023-2026.

Lancer depuis ce dossier : python3 modele_bruit.py
"""
import numpy as np
import pandas as pd

import strategies4 as S
from explorer import charger, t_stat

rien = None
for marche, (fichier, pt) in {"NQ": ("nasdaq100", 2.0), "ES": ("sp500", 5.0)}.items():
    J, O, H, L, C, P, X = charger(fichier, fin=None)
    complete = S.st.journees_completes(P)
    ok = complete & ~X["echeance"]
    cout = S.st.cout_aller_retour(fichier)
    Q = S.T3.lire_quotidien()
    vide = np.full(len(J), np.nan)
    an = pd.DatetimeIndex(J).year.values
    expl, coffre = ok & (an <= 2022), ok & (an >= 2023)
    s_reel = S.modele_appris(J, O, H, L, C, X, ok, complete, Q)
    pts = S.K1.entree_fixe(O, H, L, C, ok, cout, s_reel, 30, vide, vide, S.N - 1)
    print(f"{marche} - modele appris sur les vraies seances : t 2013-2022 {t_stat(pts[expl & (an >= 2013)] / O[expl & (an >= 2013), 0]):+.2f}"
          f" | t 2023-2026 {t_stat(pts[coffre] / O[coffre, 0]):+.2f}")
    rng = np.random.default_rng(2030)                 # memes 20 melanges que explorer4.py
    t_bruit, t_e, t_c, d_c = [], [], [], []
    for k in range(20):
        O2, H2, L2, C2, V2 = S.K1.melanger(O, H, L, C, X["V"], rng)
        X2 = {**X, "V": V2}
        s_b = S.modele_appris(J, O2, H2, L2, C2, X2, ok, complete, Q)                      # sur le bruit (comme le tournoi)
        p_b = S.K1.entree_fixe(O2, H2, L2, C2, ok, cout, s_b, 30, vide, vide, S.N - 1)
        m = expl & (an >= 2013)
        t_bruit.append(t_stat(p_b[m] / O2[m, 0]))
        appris = S.variables(J, O2, H2, L2, C2, X2, complete, Q)                          # appris sur le bruit...
        s = S.modele_appris(J, O, H, L, C, X, ok, complete, Q, apprendre=appris)           # ... trade sur le vrai
        p = S.K1.entree_fixe(O, H, L, C, ok, cout, s, 30, vide, vide, S.N - 1)
        t_e.append(t_stat(p[m] / O[m, 0]))
        t_c.append(t_stat(p[coffre] / O[coffre, 0]))
        d_c.append(float(p[coffre].sum() * pt))
    print(f"{marche} - le meme modele sur les 20 versions melangees : t de {min(t_bruit):+.2f} a {max(t_bruit):+.2f} (moyenne {np.mean(t_bruit):+.2f})")
    print(f"{marche} - appris sur le melange, trade sur les VRAIES seances : t 2013-2022 de {min(t_e):+.2f} a {max(t_e):+.2f}"
          f" (moyenne {np.mean(t_e):+.2f}) | t 2023-2026 de {min(t_c):+.2f} a {max(t_c):+.2f} (moyenne {np.mean(t_c):+.2f}),"
          f" en moyenne {np.mean(d_c):+,.0f} $ sur 2023-2026 pour 1 micro\n", flush=True)
