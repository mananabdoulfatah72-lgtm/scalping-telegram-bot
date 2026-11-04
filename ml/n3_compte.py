#!/usr/bin/env python3
"""Ajoute apres coup (hors regles fixees) : M2 joue sur le compte Bulenox reel, a cote du Supertrend, dans les memes
conditions. Depart a chaque seance de 2023 a juin 2026 : solde 50 000 $, plus haut 51 500 $, plancher 49 000 $,
objectif 53 050 $, limite du jour 400 $ (plus de nouveau trade quand la journee touche -400 $).
Plancher Option 1 : min(plus haut - 2 500, 50 100), le plus haut suivant le latent (extremes des bougies pendant les trades).
1 MNQ, une seule position a la fois, 3 $ de frais, dollars au prix d'aujourd'hui."""
import json

import numpy as np
import pandas as pd
import xgboost as xgb

import caracteristiques as K
import donnees as D

X = K.construire()
F, y, c, o, h, l, fut, sess, b, an, okb, ok, J = (X[k] for k in ("F", "y", "c", "o", "h", "l", "fut", "sess", "b", "an", "okb", "ok", "J"))
an_j = np.array([int(j[:4]) for j in J])
# le modele du bot : 21 variables (sans le temoin), moyenne de 10 modeles (graines 0 a 9), marche en avant purgee
F = F[:, :21]
okb = ok[sess] & X["meme"] & np.isfinite(F).all(1) & np.isfinite(fut)
p = np.full(len(c), np.nan)
for Y in range(2023, 2027):
    tr = okb & (sess < int(np.argmax(an_j == Y)) - 21)
    ps = [xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, reg_alpha=1.0, reg_lambda=1.0,
                            tree_method="hist", n_jobs=4, random_state=g).fit(F[tr], y[tr], verbose=False).predict_proba(F[an == Y])[:, 1] for g in range(10)]
    p[an == Y] = np.mean(ps, 0)

# trades de M2 : signal a la cloture, entree a l'ouverture de la bougie suivante, sortie a la cloture 4 bougies apres
trades_m2 = {}                                      # seance -> liste de (sens, entree, sortie, [(pire, meilleur) par bougie])
sig = np.where(p > 0.55, 1, np.where(p < 0.45, -1, 0)) * (okb & (an >= 2023))
libre = -1
for i in np.nonzero(sig)[0]:
    if i <= libre:
        continue
    e = o[i + 1]; ech = 2 * D.PREF / e; s = sig[i]
    ext = [((l[k] - e) * s * ech if s > 0 else (h[k] - e) * s * ech, (h[k] - e) * s * ech if s > 0 else (l[k] - e) * s * ech) for k in range(i + 1, i + 5)]
    trades_m2.setdefault(sess[i], []).append((s * (c[i + 4] - e) * ech - D.FRAIS, ext))
    libre = i + 3

# trades du Supertrend (moteur verifie) avec les extremes minute par minute
Jm, O, H, L, C, V, okm = D.nq_minutes()
ix = {j: k for k, j in enumerate(Jm)}
st = pd.read_csv(D.RACINE / "ml/st_trades.csv")
trades_st = {}
for r in st.itertuples():
    if r.jour < "2023-01-01" or r.jour not in ix:
        continue
    s_ = ix[r.jour]; ech = 2 * D.PREF / r.entree
    hh, ll = H[s_, r.m_in:r.m_out], L[s_, r.m_in:r.m_out]
    pire = ((ll if r.sens > 0 else hh) - r.entree) * r.sens * ech; meil = ((hh if r.sens > 0 else ll) - r.entree) * r.sens * ech
    # la vraie session index dans X (meme liste de jours)
    trades_st.setdefault(s_, []).append((r.sens * (r.sortie - r.entree) * ech - D.FRAIS, [(float(pire.min()), float(meil.max()))]))


def challenge(trades, debut, solde=50000.0, haut=51500.0, cible=53050.0, limite=400.0, fin_de_journee=False):
    seances = [s for s in range(len(J)) if ok[s] and J[s] >= J[debut]]
    for n, s in enumerate(seances):
        jour = 0.0
        for res, ext in trades.get(s, []):
            if jour <= -limite:
                break
            for pire, meil in ext:
                if not fin_de_journee:
                    haut = max(haut, solde + meil)            # Option 1 : le plancher suit le latent en direct
                plancher = min(haut - 2500, 50100)
                if solde + pire <= plancher:
                    return "echec", n + 1
            solde += res; jour += res
            if not fin_de_journee:
                haut = max(haut, solde)
            if solde >= cible:
                return "reussite", n + 1
        if fin_de_journee:
            haut = max(haut, solde)
    return "en cours", len(seances)


departs = [s for s in range(len(J)) if ok[s] and "2023-01-01" <= J[s] <= "2026-06-30"]
res = {}
for nom, tr in (("XGBoost NQ (10 modèles)", trades_m2), ("Supertrend NQ", trades_st)):
    issues = [challenge(tr, d) for d in departs]
    k = pd.Series([i[0] for i in issues]).value_counts(normalize=True).to_dict()
    jours = [i[1] for i in issues if i[0] == "reussite"]
    res[nom] = dict(reussite=k.get("reussite", 0.0), echec=k.get("echec", 0.0), en_cours=k.get("en cours", 0.0),
                    seances_reussite=float(np.median(jours)) if jours else None, departs=len(departs),
                    par_seance=float(np.mean([sum(t[0] for t in tr.get(s, [])) for s in departs])))
# compte neuf Bulenox 50K (Option 1) : 50 000 $, plancher 47 500 $, objectif 53 000 $, limite du jour 400 ou 800 $
neuf = {}
for nom, tr in (("XGBoost NQ (10 modèles)", trades_m2), ("Supertrend NQ", trades_st)):
    for lim, eod in ((400.0, False), (800.0, False), (400.0, True), (800.0, True)):
        issues = [challenge(tr, d, 50000.0, 50000.0, 53000.0, lim, eod) for d in departs]
        k = pd.Series([i[0] for i in issues]).value_counts(normalize=True).to_dict()
        jours = [i[1] for i in issues if i[0] == "reussite"]
        neuf[f"{nom}, limite {lim:.0f} $, plancher {'fin de journée' if eod else 'en direct'}"] = dict(reussite=k.get("reussite", 0.0), echec=k.get("echec", 0.0), seances_reussite=float(np.median(jours)) if jours else None)
res["compte_neuf"] = neuf
res["compte_actuel_fin_de_journee"] = {nom: pd.Series([challenge(tr, d, fin_de_journee=True)[0] for d in departs]).value_counts(normalize=True).to_dict()
                                       for nom, tr in (("XGBoost NQ (10 modèles)", trades_m2), ("Supertrend NQ", trades_st))}
json.dump(res, open(D.SORTIE / "n3_compte.json", "w"))
txt = ["# XGBoost NQ (le bot) et Supertrend sur ton compte (ajouté après coup, hors règles fixées)\n",
       f"Départ à chacune des {len(departs)} séances de janvier 2023 à juin 2026 : solde 50 000 $, plancher 49 000 $ (suiveur Option 1 sur le latent), "
       "objectif 53 050 $, limite du jour 400 $, 1 MNQ, une position à la fois, 3 $ de frais.\n",
       "| stratégie | $ par séance (2023-2026) | objectif atteint | plancher touché | ni l'un ni l'autre à la fin des données | séances pour réussir (médiane) |", "|---|---|---|---|---|---|"]
for nom, r in [(k, v) for k, v in res.items() if k not in ("compte_neuf", "compte_actuel_fin_de_journee")]:
    txt.append(f"| {nom} | {r['par_seance']:+.1f} | {r['reussite']:.0%} | {r['echec']:.0%} | {r['en_cours']:.0%} | {r['seances_reussite'] or '—'} |")
txt.append("\nCompte neuf Bulenox 50K : 50 000 $, plancher 47 500 $ (suiveur), objectif 53 000 $.\n")
txt.append("| stratégie | objectif atteint | plancher touché | séances pour réussir (médiane) |\n|---|---|---|---|")
for nom, r in neuf.items():
    txt.append(f"| {nom} | {r['reussite']:.0%} | {r['echec']:.0%} | {r['seances_reussite'] or '—'} |")
txt.append("\nTon compte actuel si le plancher ne bougeait qu'en fin de journée : " + " ; ".join(f"{k} : objectif {v.get('reussite', 0):.0%}, plancher {v.get('echec', 0):.0%}" for k, v in res["compte_actuel_fin_de_journee"].items()))
D.ecrire("n3_compte.md", "\n".join(txt) + "\n")
