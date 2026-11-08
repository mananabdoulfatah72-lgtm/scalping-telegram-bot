"""Vague 4, diagnostic (ne decide rien) : W1 avec 10 graines du modele, et leur moyenne."""
#!/usr/bin/env python3
"""Arene, vague 4 (ml/arene/VAGUE4.md, regles fixees avant calcul) : le meme Supertrend NQ, en mieux. W1 tri des signaux par
apprentissage en marche avant, W2 taille selon l'agitation, W3 les deux. Mesure 2017 - 2026, en direct dans l'arene.
MINUTES_NQ=... CACHE_DOSSIER=... python3 vague4.py <dossier de l'arene>"""
import glob
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from scipy import stats

import bots as BT
from direct import Direct

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import donnees as Dn  # noqa: E402

R = Path(__file__).resolve().parents[2]
DOSSIER = None
B = BT.Base(os.environ["CACHE_DOSSIER"])
O, H, L, C, V = B.O, B.H, B.L, B.C, B.V
F = B.X["F"]; ATR = B.atr
aj = B.an[B.test]; n = len(B.test); jours = [B.J[s] for s in B.test]; W = aj >= 2017; d17 = int(np.argmax(W))
d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(R / "radar/donnees/jour/yahoo/*.csv.gz")))])
v = d[d.serie.isin(["^VIX:c", "^VIX3M:c"])].pivot_table(index="date", columns="serie", values="valeur"); v.index = pd.to_datetime(v.index)
tous = pd.to_datetime([B.J[s] for s in range(len(B.J))])
veille = v.reindex(tous.union(v.index)).ffill().shift(1).reindex(tous)
ECART_VIX = (veille["^VIX:c"] - veille["^VIX3M:c"]).to_numpy()
ST = sorted(BT.supertrend(B), key=lambda t: (t[0], t[2]))
# ------------------------------------------------------------------ W1 : variables connues avant chaque entree, etiquettes
X, y, an_t = [], [], []
for k, (s, sens, m, _, fin, e, x) in enumerate(ST):
    if k == 0 or ST[k - 1][0] != s:
        nb_avant, res_avant = 0, 0.0
    g = BT.bougie_avant(s, m)
    tp = (H[s, :m] + L[s, :m] + C[s, :m]) / 3; vv = V[s, :m]
    vw = (tp * vv).sum() / vv.sum() if vv.sum() > 0 else tp.mean()
    atr = ATR[g] if g >= 0 and np.isfinite(ATR[g]) and ATR[g] > 0 else np.nan
    gap = O[s, 0] / C[s - 1, 389] - 1 if s > 0 and B.ok[s - 1] else np.nan
    X.append(np.r_[F[g] if g >= 0 else np.full(F.shape[1], np.nan),
                   sens, m, sens * (O[s, m] - vw) / atr, sens * (O[s, m] / O[s, 0] - 1), sens * gap, ECART_VIX[s], nb_avant, res_avant])
    pnl = sens * (x - e) * 2.0 * Dn.PREF / e - Dn.FRAIS
    y.append(int(pnl > 0)); an_t.append(int(B.J[s][:4]))
    nb_avant += 1; res_avant += pnl
X, y, an_t = np.array(X, float), np.array(y), np.array(an_t)
OKs = np.nonzero(B.ok)[0]
cl = pd.Series(C[OKs, 389], index=OKs)
rv = cl.pct_change().rolling(20).std().shift(1)
rang = rv.rolling(252, min_periods=126).rank(pct=True)
TAILLE = np.ones(len(B.J), int)
TAILLE[OKs] = np.where(rang.to_numpy() < 0.5, 2, 1)


def journees_taille(tr, frais=3.0, taille_var=False):
    r1, d1, n1 = BT.journees(B, tr, 1, 400.0, frais)
    if not taille_var:
        return r1, d1, n1
    r2, d2, _ = BT.journees(B, tr, 2, 800.0, frais)
    return np.where(TAILLE == 2, r2, r1), np.where(TAILLE == 2, d2, d1), n1


def mesures(tr, taille_var=False):
    r, dp, ntr = journees_taille(tr, 3.0, taille_var); r6 = journees_taille(tr, 6.0, taille_var)[0]
    j, dd, tt = r[B.test], dp[B.test], ntr[B.test] > 0
    jw, dw = j[W], dd[W]; cum = np.cumsum(jw); a = aj[W]
    vie = BT.vie(np.vstack([j, j, j]), np.vstack([dd, dd, dd]), tt, debut=d17)
    idx = pd.to_datetime(np.array(jours)[W]); sj = pd.Series(jw, index=idx)
    sem = sj.groupby([idx.isocalendar().year.values, idx.isocalendar().week.values]).sum(); mo = sj.groupby(idx.to_period("M")).sum()
    m = dict(par_seance=float(jw.mean()), t=BT.tst(jw), t_avant=BT.tst(jw[a <= 2022]), t_apres=BT.tst(jw[a >= 2023]), t_frais6=BT.tst(r6[B.test][W]),
             annees_pos=int(sum(jw[a == yy].sum() > 0 for yy in range(2017, 2027))), seances_tradees=float(tt[W].mean()),
             jours_positifs=float((jw[tt[W]] > 0).mean()), semaines_positives=float((sem > 0).mean()), mois_positifs=float((mo > 0).mean()),
             pire_semaine=float(sem.min()), pire_jour=float(jw.min()), pire_baisse=float((cum - np.maximum.accumulate(cum)).min()),
             survie_60=float(1 - BT.grilles_depuis(jw, dw, 60).mean()), grille_250=float(BT.grilles_depuis(jw, dw, 250).mean()),
             periode=float(j[np.array([x >= "2026-08-11" for x in jours])].sum()), net_an=vie["net_an"], grilles_an=vie["grilles_an"])
    return j, m




def trier(probas):
    g = np.ones(len(ST), bool); seuils = {}
    for Y in range(2017, 2027):
        app, test = an_t < Y, an_t == Y
        g[test] = probas[test] > y[app].mean()
    return [t for t, k in zip(ST, g) if k]


P = []
for graine in range(10):
    p = np.full(len(ST), np.nan)
    for Y in range(2017, 2027):
        app, test = an_t < Y, an_t == Y
        mdl = xgb.XGBClassifier(n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                                min_child_weight=20, random_state=graine, n_jobs=4, eval_metric="logloss")
        mdl.fit(X[app], y[app]); p[test] = mdl.predict_proba(X[test])[:, 1]
    P.append(p)
    _, m = mesures(trier(p))
    print(f"graine {graine} : t {m['t']:.2f}, depuis 2023 {m['t_apres']:.2f}, séances {m['seances_tradees']:.0%}, survie {m['survie_60']:.0%}, "
          f"grillé 1 an {m['grille_250']:.0%}, {m['grilles_an']:.2f} grillés/an, net {m['net_an']:,.0f} $/an, 11/08-02/11 {m['periode']:+,.0f} $".replace(",", " "), flush=True)
_, m = mesures(trier(np.mean(P, axis=0)))
print(f"moyenne des 10 graines : t {m['t']:.2f}, depuis 2023 {m['t_apres']:.2f}, séances {m['seances_tradees']:.0%}, survie {m['survie_60']:.0%}, "
      f"grillé 1 an {m['grille_250']:.0%}, {m['grilles_an']:.2f} grillés/an, net {m['net_an']:,.0f} $/an, années positives {m['annees_pos']}/10, "
      f"semaines positives {m['semaines_positives']:.0%}, 11/08-02/11 {m['periode']:+,.0f} $".replace(",", " "))
mdl = xgb.XGBClassifier(n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, min_child_weight=20,
                        random_state=0, n_jobs=4, eval_metric="logloss").fit(X[an_t < 2026], y[an_t < 2026])
sys.path.insert(0, str(R / "ml")); import caracteristiques as K  # noqa: E402
noms = list(K.NOMS) + ["sens", "minute d'entrée", "écart à la VWAP (ATR)", "rendement depuis l'ouverture", "écart d'ouverture", "VIX − VIX 3 mois", "trades déjà pris", "résultat du jour"]
imp = sorted(zip(mdl.feature_importances_, noms), reverse=True)[:8]
print("ce que le tri regarde le plus :", " ; ".join(f"{nm} {v:.0%}" for v, nm in imp))
