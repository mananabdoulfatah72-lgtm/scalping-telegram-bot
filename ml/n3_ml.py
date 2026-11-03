#!/usr/bin/env python3
"""Niveau 3 (ml/REGLES.md) : 5 modeles en marche en avant purgee (2014 - 2026), SHAP contre un bruit temoin,
Bollinger seul et Bollinger + ML, frais compris."""
import json
import time

import numpy as np
import xgboost as xgb
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

import caracteristiques as K
import donnees as D

t0 = time.time()
X = K.construire()
F, y, c, fut, sess, b, an, okb, ok, J = (X[k] for k in ("F", "y", "c", "fut", "sess", "b", "an", "okb", "ok", "J"))
print(f"donnees : {len(c)} bougies, {okb.sum()} utilisables, {time.time() - t0:.0f} s")
ANNEES = list(range(2014, 2027))
PURGE = 21
debut_an = {Y: int(np.argmax(np.array([int(j[:4]) for j in J]) == Y)) for Y in ANNEES}


def logistique_newton(Xm, yv, l2=1.0, iters=12):           # identique a terminal/prep2.py (M0)
    w = np.zeros(Xm.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-Xm @ w))
        g = Xm.T @ (p - yv) + l2 * np.r_[0, w[1:]]
        Hm = (Xm * (p * (1 - p))[:, None]).T @ Xm + l2 * np.diag(np.r_[0, np.ones(len(w) - 1)])
        w -= np.linalg.solve(Hm, g)
    return w


XGB = {"M2": dict(n_estimators=100, max_depth=4), "M3": dict(n_estimators=50, max_depth=3), "M4": dict(n_estimators=1000, max_depth=6)}
MODELES = ["M0", "M1", "M2", "M3", "M4"]
proba = {m: np.full(len(c), np.nan) for m in MODELES}
modele_2026 = None
for Y in ANNEES:
    tr = okb & (sess < debut_an[Y] - PURGE)
    te = (an == Y) & np.isfinite(F[:, K.ACTUELLES]).all(1)
    teX = an == Y
    # M0 : logistique, 11 variables actuelles
    A = F[:, K.ACTUELLES]; mu, sd = A[tr].mean(0), A[tr].std(0) + 1e-12
    w = logistique_newton(np.column_stack([np.ones(tr.sum()), (A[tr] - mu) / sd]), y[tr])
    proba["M0"][te] = 1 / (1 + np.exp(-np.column_stack([np.ones(te.sum()), (A[te] - mu) / sd]) @ w))
    # M1 : logistique L1, 22 variables
    mu, sd = F[tr].mean(0), F[tr].std(0) + 1e-12
    lr_ = LogisticRegression(l1_ratio=1.0, C=0.1, solver="saga", max_iter=300, tol=1e-3).fit((F[tr] - mu) / sd, y[tr])
    Zt = np.nan_to_num((F[teX] - mu) / sd)
    proba["M1"][teX] = lr_.predict_proba(Zt)[:, 1]
    # M2 - M4 : XGBoost (les NaN restent des NaN : XGBoost sait faire)
    for m, cfg in XGB.items():
        mdl = xgb.XGBClassifier(learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, reg_alpha=1.0, reg_lambda=1.0,
                                tree_method="hist", n_jobs=4, random_state=0, **cfg)
        mdl.fit(F[tr], y[tr], verbose=False)
        proba[m][teX] = mdl.predict_proba(F[teX])[:, 1]
        if m == "M2" and Y == 2026:
            modele_2026 = mdl
    print(f"{Y} : entrainement {tr.sum()} bougies, {time.time() - t0:.0f} s", flush=True)

# ------------------------------------------------------------------ evaluation (meme regle de trading pour tous)
sess_ok = np.nonzero(ok)[0]
an_s = np.array([int(j[:4]) for j in J])
test_s = sess_ok[(an_s[sess_ok] >= 2014)]


def bilan(par_seance, sel):
    x = par_seance[sel]
    t = x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if x.std() > 0 else 0.0
    return dict(seances=int(len(x)), par_seance=float(x.mean()), t=float(t), p=float(1 - stats.t.cdf(t, len(x) - 1)),
                sharpe=float(x.mean() / x.std(ddof=1) * np.sqrt(252)) if x.std() > 0 else 0.0, total=float(x.sum()))


def evaluer(p):
    ev = okb & (an >= 2014) & np.isfinite(p)
    sig = np.where(p > 0.55, 1, np.where(p < 0.45, -1, 0)) * ev
    usd = np.where(sig != 0, sig * (fut - c) * 2 * D.PREF / c - D.FRAIS, 0.0)
    usd = np.nan_to_num(usd)
    jour = np.bincount(sess, weights=usd, minlength=X["S"])
    brut = np.bincount(sess, weights=np.nan_to_num(np.where(sig != 0, sig * (fut - c) * 2 * D.PREF / c, 0.0)), minlength=X["S"])
    r = dict(precision=float(((p[ev] > 0.5) == (y[ev] == 1)).mean()), auc=float(roc_auc_score(y[ev], p[ev])), signaux=int((sig != 0).sum()),
             tout=bilan(jour, test_s), avant=bilan(jour, test_s[an_s[test_s] <= 2022]), apres=bilan(jour, test_s[an_s[test_s] >= 2023]),
             brut=bilan(brut, test_s), annees={})
    for Y in ANNEES:
        e = ev & (an == Y)
        r["annees"][Y] = dict(precision=float(((p[e] > 0.5) == (y[e] == 1)).mean()), auc=float(roc_auc_score(y[e], p[e])),
                              usd=float(jour[test_s[an_s[test_s] == Y]].sum()))
    r["courbe"] = np.cumsum(jour[test_s]).round(1).tolist()
    return r


res = {m: evaluer(proba[m]) for m in MODELES}

# ------------------------------------------------------------------ SHAP exact des arbres (M2, 2026) contre le bruit temoin
e26 = okb & (an == 2026)
contrib = modele_2026.get_booster().predict(xgb.DMatrix(F[e26]), pred_contribs=True)[:, :-1]
imp = np.abs(contrib).mean(0)
shap = sorted([[K.NOMS[i], float(imp[i])] for i in range(len(K.NOMS))], key=lambda x: -x[1])
seuil_bruit = float(imp[-1])


# ------------------------------------------------------------------ Bollinger (retour a la moyenne) seul et filtre par M2
def bollinger(filtre):
    I = X["I"]; n = len(c); usd = np.zeros(n); brut = np.zeros(n); nb_ = 0
    i = 0
    while i < n:
        s, bb = sess[i], b[i]
        if not ok[s] or an[i] < 2014 or bb >= 25 or not np.isfinite(I["bb_h"][i]):
            i += 1; continue
        sens = 1 if c[i] < I["bb_b"][i] else -1 if c[i] > I["bb_h"][i] else 0
        if sens and filtre:
            p = proba["M2"][i]
            if not np.isfinite(p) or (sens > 0 and p <= 0.5) or (sens < 0 and p >= 0.5):
                sens = 0
        if not sens:
            i += 1; continue
        j = i + 1
        while True:
            fin_seance = b[j] == 25
            revenu = (sens > 0 and c[j] >= I["bb_m"][j]) or (sens < 0 and c[j] <= I["bb_m"][j])
            if revenu or j - i >= 8 or fin_seance:
                break
            j += 1
        g = sens * (c[j] - c[i]) * 2 * D.PREF / c[i]
        brut[i] = g; usd[i] = g - D.FRAIS; nb_ += 1
        i = j + 1 if b[j] < 25 else j + 1
    jour = np.bincount(sess, weights=usd, minlength=X["S"]); jb = np.bincount(sess, weights=brut, minlength=X["S"])
    return dict(trades=nb_, tout=bilan(jour, test_s), avant=bilan(jour, test_s[an_s[test_s] <= 2022]), apres=bilan(jour, test_s[an_s[test_s] >= 2023]),
                brut=bilan(jb, test_s), courbe=np.cumsum(jour[test_s]).round(1).tolist())


bb_seul, bb_ml = bollinger(False), bollinger(True)
json.dump(dict(modeles=res, shap=shap, seuil_bruit=seuil_bruit, bollinger=bb_seul, bollinger_ml=bb_ml,
               jours=[J[s] for s in test_s]), open(D.SORTIE / "n3.json", "w"))

# ------------------------------------------------------------------ texte
NOMS_M = {"M0": "M0 logistique, 11 variables (l'actuel)", "M1": "M1 logistique L1, 22 variables", "M2": "M2 XGBoost de l'article (100 × 4)",
          "M3": "M3 XGBoost simple (50 × 3)", "M4": "M4 XGBoost complexe (1 000 × 6)"}
txt = ["# Niveau 3 : ML tabulaire, marche en avant purgée (test 2014 - 2026)\n",
       f"{int((okb & (an >= 2014)).sum()):,} bougies de test ; cible : hausse dans l'heure ; signal à 0,55 / 0,45 ; 1 MNQ par signal, 3 $ de frais.\n",
       "| modèle | précision | AUC | signaux | $ par séance | t 2014-2026 | p | Sharpe | t 2014-2022 | t 2023-2026 | $ par séance avant frais |",
       "|---|---|---|---|---|---|---|---|---|---|---|"]
for m in MODELES:
    r = res[m]
    txt.append(f"| {NOMS_M[m]} | {r['precision']:.1%} | {r['auc']:.3f} | {r['signaux']:,} | {r['tout']['par_seance']:+.1f} | {r['tout']['t']:+.2f} | {r['tout']['p']:.3f} | "
               f"{r['tout']['sharpe']:+.2f} | {r['avant']['t']:+.2f} | {r['apres']['t']:+.2f} | {r['brut']['par_seance']:+.1f} |")
txt.append("\n## SHAP (M2 entraîné pour 2026, bougies de 2026) : importance moyenne |SHAP|\n")
for nm, v in shap:
    txt.append(f"- {nm} : {v:.4f}{'  ← bruit témoin' if nm == 'BRUIT TÉMOIN' else ('  (pas mieux que le bruit)' if v <= seuil_bruit else '')}")
txt.append("\n## Bollinger (retour à la moyenne, 15 min) seul et filtré par M2\n")
txt.append("| stratégie | trades | $ par séance avant frais | $ par séance après frais | t | Sharpe | t 2014-2022 | t 2023-2026 |\n|---|---|---|---|---|---|---|---|")
for nm, r in (("Bollinger seul", bb_seul), ("Bollinger + M2", bb_ml)):
    txt.append(f"| {nm} | {r['trades']:,} | {r['brut']['par_seance']:+.1f} | {r['tout']['par_seance']:+.1f} | {r['tout']['t']:+.2f} | {r['tout']['sharpe']:+.2f} | {r['avant']['t']:+.2f} | {r['apres']['t']:+.2f} |")
D.ecrire("n3.md", "\n".join(txt) + f"\n\n(calcul : {time.time() - t0:.0f} s)\n")
