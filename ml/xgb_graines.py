#!/usr/bin/env python3
"""Ajoute apres coup : le resultat de M2 depend-il du hasard de l'entrainement (graine des sous-echantillons) ?
Marche en avant purgee 2014 - 2026, graines 0 a 9, avec et sans la variable temoin, puis la moyenne des 10 modeles.
Une position a la fois, entree a l'ouverture de la bougie suivante, 3 $ de frais."""
import json

import numpy as np
import xgboost as xgb

import caracteristiques as K
import donnees as D

X = K.construire()
F, y, c, o, fut, sess, b, an, ok, J = (X[k] for k in ("F", "y", "c", "o", "fut", "sess", "b", "an", "ok", "J"))
an_j = np.array([int(j[:4]) for j in J])
sess_ok = np.nonzero(ok)[0]; test_s = sess_ok[an_j[sess_ok] >= 2014]


def marche(Fm, graine):
    utile = ok[sess] & X["meme"] & np.isfinite(Fm).all(1) & np.isfinite(fut)
    p = np.full(len(c), np.nan)
    for Y in range(2014, 2027):
        tr = utile & (sess < int(np.argmax(an_j == Y)) - 21)
        m = xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, reg_alpha=1.0,
                              reg_lambda=1.0, tree_method="hist", n_jobs=4, random_state=graine).fit(Fm[tr], y[tr], verbose=False)
        p[an == Y] = m.predict_proba(Fm[an == Y])[:, 1]
    return p, utile


def bilan(p, utile):
    sig = np.where(p > 0.55, 1, np.where(p < 0.45, -1, 0)) * (utile & (an >= 2014))
    usd = np.zeros(len(c)); libre = -1
    for i in np.nonzero(sig)[0]:
        if i <= libre:
            continue
        usd[i] = sig[i] * (fut[i] - o[i + 1]) * 2 * D.PREF / o[i + 1] - D.FRAIS; libre = i + 3
    j = np.bincount(sess, weights=usd, minlength=X["S"])[test_s]
    t = lambda v: float(v.mean() / v.std(ddof=1) * np.sqrt(len(v)))
    return dict(par_seance=float(j.mean()), t=t(j), t_avant=t(j[an_j[test_s] <= 2022]), t_apres=t(j[an_j[test_s] >= 2023]),
                apres_usd=float(j[an_j[test_s] >= 2023].mean()))


res = {}
for nom, Fm in (("22 variables (avec témoin)", F), ("21 variables (sans témoin)", F[:, :21])):
    ps, lignes = [], []
    for g in range(10):
        p, utile = marche(Fm, g); ps.append(p); lignes.append(bilan(p, utile))
        print(nom, g, {k: round(v, 2) for k, v in lignes[-1].items()}, flush=True)
    moy = np.nanmean(np.vstack(ps), 0)
    res[nom] = dict(graines=lignes, ensemble=bilan(moy, utile))
    print(nom, "ensemble", res[nom]["ensemble"], flush=True)
json.dump(res, open(D.SORTIE / "xgb_graines.json", "w"))
txt = ["# M2 : le résultat dépend-il du hasard de l'entraînement ? (ajouté après coup)\n",
       "Une position à la fois, entrée à la bougie suivante, 3 $ de frais. Graines 0 à 9 du sous-échantillonnage de XGBoost.\n"]
for nom, r in res.items():
    tt = np.array([g["t"] for g in r["graines"]]); ta = np.array([g["t_apres"] for g in r["graines"]])
    txt.append(f"## {nom}\n\n| graine | $ par séance | t 2014-2026 | t 2014-2022 | t 2023-2026 | $ par séance 2023-2026 |\n|---|---|---|---|---|---|")
    for k, g in enumerate(r["graines"]):
        txt.append(f"| {k} | {g['par_seance']:+.1f} | {g['t']:+.2f} | {g['t_avant']:+.2f} | {g['t_apres']:+.2f} | {g['apres_usd']:+.1f} |")
    e = r["ensemble"]
    txt.append(f"| **moyenne des 10 modèles** | {e['par_seance']:+.1f} | {e['t']:+.2f} | {e['t_avant']:+.2f} | {e['t_apres']:+.2f} | {e['apres_usd']:+.1f} |")
    txt.append(f"\nt 2014-2026 : de {tt.min():+.2f} à {tt.max():+.2f} ; t 2023-2026 : de {ta.min():+.2f} à {ta.max():+.2f} (médiane {np.median(ta):+.2f}).\n")
D.ecrire("xgb_graines.md", "\n".join(txt))
