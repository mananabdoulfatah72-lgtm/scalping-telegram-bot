#!/usr/bin/env python3
"""Plafond sans avantage : tout miser sur un seul trade (objectif et stop au maximum permis) a chaque tentative de
challenge, sur les vrais parcours minute du NQ 2011-2026, 50 MNQ, frais compris ; un stop touche = compte perdu.
Comparaison avec la theorie pour un jeu equitable : perte / (objectif + perte), ou exp(-objectif / perte) quand la
limite suit le plus haut latent (Apex). Lancer depuis intraday/ : python3 ../challenge/audace.py
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent / "intraday"))
import strategies as st
J, O, H, L, C, P, X = st.charger("nasdaq100")
ok = st.journees_completes(P) & ~X["echeance"]
idx = np.flatnonzero(ok)
PT, COUT = 2.0, 1.5
def tentative(k0, objectif, perte, sens_fn, mnq=50, jours_max=None, suiveuse_intraday=False, max_jours=400):
    solde = haut = 50000.0
    for j, d in enumerate(idx[k0:k0 + max_jours]):
        if jours_max and j >= jours_max:
            return 0
        s = sens_fn(d)
        v = mnq * PT                                      # $ par point
        if solde - (haut - perte) <= mnq * COUT * PT + 1.0:
            return -1                                        # plus assez de marge pour payer les frais : perdu
        plancher = haut - perte
        e = O[d, 0]
        frais = mnq * COUT * PT
        cible = e + s * (objectif - (solde - 50000) + frais) / v      # objectif atteint frais payes
        stop = e - s * (solde - plancher - frais - 1.0) / v           # la perte, frais compris, reste au-dessus de la limite
        fin = None
        pic = solde
        for m in range(390):
            bas, hautm = (L[d, m], H[d, m]) if s > 0 else (-H[d, m], -L[d, m])
            eb, cb, sb = s * e, s * cible, s * stop
            if suiveuse_intraday:                          # Apex : la limite suit le plus haut latent
                pic = max(pic, solde + (hautm - eb) * v)
                sb = max(sb, eb + (pic - perte - solde + frais + 1.0) / v)
            if bas <= sb:
                return -1                                           # stop touche : le compte est a sa limite, perdu
            if hautm >= cb:
                fin = cb; break
        if fin is None:
            fin = s * C[d, -1]
        solde += (fin - s * e) * v - mnq * COUT * PT
        if solde - 50000 >= objectif:
            return 1
        haut = max(haut, solde) if not suiveuse_intraday else max(haut, pic)
        if solde <= haut - perte:
            return -1
    return 0
rng = np.random.default_rng(0)
departs = range(0, len(idx) - 60, 5)
for nom, obj, perte, suiv, jm in [("Phidias (+4000 / -2500 fin de journee)", 4000, 2500, False, None),
                                  ("Topstep sans regle de regularite (+3000 / -2000)", 3000, 2000, False, None),
                                  ("Apex (+3000 / -2500 suit le plus haut latent, 30 jours)", 3000, 2500, True, 21)]:
    for sens_nom, fn in [("toujours acheteur", lambda d: 1), ("sens au hasard", lambda d: rng.choice([-1, 1]))]:
        r = np.array([tentative(k, obj, perte, fn, jours_max=jm, suiveuse_intraday=suiv) for k in departs])
        theorie = perte / (obj + perte) if not suiv else np.exp(-obj / perte)
        print(f"{nom:55s} {sens_nom:18s} : reussi {np.mean(r == 1):4.0%}, perdu {np.mean(r == -1):4.0%} (theorie sans avantage {theorie:.0%})", flush=True)
