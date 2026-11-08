"""W1 (ml/arene/VAGUE4.md, VAGUE5.md) : les signaux du Supertrend NQ tries par apprentissage. Variables connues avant chaque
entree, etiquettes, apprentissage en marche avant (moyenne des probabilites de 10 graines), tri. C'est aussi la reference
du bot Quantower (bot3en1/W1.*) : le moteur C# doit retrouver ces variables et ces probabilites."""
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

import bots as BT

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "ml"))
import caracteristiques as K  # noqa: E402
import donnees as Dn  # noqa: E402

NOMS = list(K.NOMS) + ["sens", "minute d'entrée", "écart à la VWAP (ATR)", "rendement depuis l'ouverture", "écart d'ouverture",
                       "VIX − VIX 3 mois (veille)", "trades déjà pris", "résultat du jour"]
I_VIX = len(K.NOMS) + 5
PARAMS = dict(n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, min_child_weight=20,
              n_jobs=4, eval_metric="logloss")
GRAINES = range(10)


def ecart_vix(B):
    """VIX moins VIX a 3 mois a la cloture de la veille de chaque seance (radar, Yahoo)."""
    d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(R / "radar/donnees/jour/yahoo/*.csv.gz")))])
    v = d[d.serie.isin(["^VIX:c", "^VIX3M:c"])].pivot_table(index="date", columns="serie", values="valeur"); v.index = pd.to_datetime(v.index)
    tous = pd.to_datetime([B.J[s] for s in range(len(B.J))])
    veille = v.reindex(tous.union(v.index)).ffill().shift(1).reindex(tous)
    return (veille["^VIX:c"] - veille["^VIX3M:c"]).to_numpy()


def variables(B, ST, ecart):
    """Une ligne par trade du Supertrend (tries par seance puis minute d'entree) : 22 variables du labo a la derniere bougie
    de 15 min terminee avant l'entree, puis 8 variables du trade. Renvoie X, etiquette (gagnant apres frais), annee."""
    O, H, L, C, V, F, ATR = B.O, B.H, B.L, B.C, B.V, B.X["F"], B.atr
    X, y, an = [], [], []
    for k, (s, sens, m, _, fin, e, x) in enumerate(ST):
        if k == 0 or ST[k - 1][0] != s:
            nb_avant, res_avant = 0, 0.0
        g = BT.bougie_avant(s, m)
        tp = (H[s, :m] + L[s, :m] + C[s, :m]) / 3; vv = V[s, :m]
        vw = (tp * vv).sum() / vv.sum() if vv.sum() > 0 else tp.mean()
        atr = ATR[g] if g >= 0 and np.isfinite(ATR[g]) and ATR[g] > 0 else np.nan
        gap = O[s, 0] / C[s - 1, 389] - 1 if s > 0 and B.ok[s - 1] else np.nan
        X.append(np.r_[F[g] if g >= 0 else np.full(F.shape[1], np.nan),
                       sens, m, sens * (O[s, m] - vw) / atr, sens * (O[s, m] / O[s, 0] - 1), sens * gap, ecart[s], nb_avant, res_avant])
        pnl = sens * (x - e) * 2.0 * Dn.PREF / e - Dn.FRAIS
        y.append(int(pnl > 0)); an.append(int(B.J[s][:4]))
        nb_avant += 1; res_avant += pnl
    return np.array(X, float), np.array(y), np.array(an)


def probas(X, y, an, colonnes=None, annees=range(2017, 2027), graines=GRAINES):
    """Marche en avant : chaque annee Y, apprend sur les trades des annees < Y ; moyenne des probabilites des graines."""
    Xc = X if colonnes is None else X[:, colonnes]
    p = np.zeros(len(y)); vu = np.zeros(len(y), bool)
    for Y in annees:
        app, test = an < Y, an == Y
        if not test.any():
            continue
        acc = np.zeros(test.sum())
        for g in graines:
            acc += xgb.XGBClassifier(random_state=g, **PARAMS).fit(Xc[app], y[app]).predict_proba(Xc[test])[:, 1]
        p[test] = acc / len(graines); vu |= test
    p[~vu] = np.nan
    return p


def tri(ST, p, y, an, annees=range(2017, 2027)):
    """Garde un trade si sa probabilite depasse la part de trades gagnants de l'apprentissage ; avant 2017, tout est garde."""
    garde = np.ones(len(ST), bool)
    for Y in annees:
        test = an == Y
        if test.any():
            garde[test] = p[test] > y[an < Y].mean()
    return [t for t, k in zip(ST, garde) if k], garde
