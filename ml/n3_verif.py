#!/usr/bin/env python3
"""Verifications ajoutees APRES le niveau 3 (hors regles fixees) : le resultat de M2 / M3 vient-il d'un bug ou d'une
execution irrealiste ? Etiquettes melangees, entree a l'ouverture de la bougie suivante, frais doubles, une seule position
a la fois, variables decalees d'une bougie."""
import json

import numpy as np
import xgboost as xgb
from scipy import stats

import caracteristiques as K
import donnees as D

X = K.construire()
F, y, c, o, fut, sess, b, an, okb, ok, J = (X[k] for k in ("F", "y", "c", "o", "fut", "sess", "b", "an", "okb", "ok", "J"))
ANNEES = list(range(2014, 2027)); PURGE = 21
an_j = np.array([int(j[:4]) for j in J])
debut_an = {Y: int(np.argmax(an_j == Y)) for Y in ANNEES}
CFG = {"M2": dict(n_estimators=100, max_depth=4), "M3": dict(n_estimators=50, max_depth=3)}


def marche_avant(cfg, Fm, ym, graine_melange=None):
    p = np.full(len(c), np.nan)
    for Y in ANNEES:
        tr = okb & (sess < debut_an[Y] - PURGE)
        yt = ym[tr].copy()
        if graine_melange is not None:
            np.random.default_rng(graine_melange + Y).shuffle(yt)
        m = xgb.XGBClassifier(learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, reg_alpha=1.0, reg_lambda=1.0,
                              tree_method="hist", n_jobs=4, random_state=0, **cfg).fit(Fm[tr], yt, verbose=False)
        te = an == Y
        p[te] = m.predict_proba(Fm[te])[:, 1]
    return p


sess_ok = np.nonzero(ok)[0]; test_s = sess_ok[an_j[sess_ok] >= 2014]


def stat(jour):
    x = jour[test_s]; a = x[an_j[test_s] <= 2022]; z = x[an_j[test_s] >= 2023]
    t = lambda v: float(v.mean() / v.std(ddof=1) * np.sqrt(len(v)))
    return dict(par_seance=float(x.mean()), t=t(x), t_avant=t(a), t_apres=t(z), ecart=float(x.std(ddof=1)), pire=float(x.min()))


def trader(p, entree="cloture", frais=D.FRAIS, une_seule=False):
    ev = okb & (an >= 2014) & np.isfinite(p)
    sig = np.where(p > 0.55, 1, np.where(p < 0.45, -1, 0)) * ev
    px = c if entree == "cloture" else np.r_[o[1:], np.nan]          # ouverture de la bougie suivante (meme seance : b <= 21)
    usd = np.zeros(len(c))
    if not une_seule:
        k = sig != 0
        usd[k] = sig[k] * (fut[k] - px[k]) * 2 * D.PREF / px[k] - frais
    else:
        libre = -1
        for i in np.nonzero(sig)[0]:
            if i <= libre:
                continue
            usd[i] = sig[i] * (fut[i] - px[i]) * 2 * D.PREF / px[i] - frais
            libre = i + 3
    return stat(np.bincount(sess, weights=usd, minlength=X["S"])), int((usd != 0).sum())


res = {}
for m, cfg in CFG.items():
    p = marche_avant(cfg, F, y)
    res[m] = {"tel quel (clôture de la bougie)": trader(p), "entrée à l'ouverture de la bougie suivante": trader(p, "suivante"),
              "frais doublés (6 $)": trader(p, frais=6.0), "suivante + 6 $": trader(p, "suivante", 6.0),
              "une seule position à la fois": trader(p, une_seule=True), "une seule + suivante + 6 $": trader(p, "suivante", 6.0, True)}
    res[m]["étiquettes mélangées (doit donner ~0)"] = trader(marche_avant(cfg, F, y, graine_melange=100))
    Fd = np.vstack([np.full((1, F.shape[1]), np.nan), F[:-1]])           # variables de la bougie precedente
    res[m]["variables décalées d'une bougie"] = trader(marche_avant(cfg, Fd, y))
    print(m, flush=True)
json.dump(res, open(D.SORTIE / "n3_verif.json", "w"))
txt = ["# Niveau 3 : vérifications ajoutées après coup (hors règles fixées)\n"]
for m, r in res.items():
    txt.append(f"## {m}\n\n| test | signaux | $ par séance | écart type par séance | pire séance | t 2014-2026 | t 2014-2022 | t 2023-2026 |\n|---|---|---|---|---|---|---|---|")
    for nm, (s, n) in r.items():
        txt.append(f"| {nm} | {n:,} | {s['par_seance']:+.1f} | {s['ecart']:.0f} | {s['pire']:+.0f} | {s['t']:+.2f} | {s['t_avant']:+.2f} | {s['t_apres']:+.2f} |")
    txt.append("")
D.ecrire("n3_verif.md", "\n".join(txt))
