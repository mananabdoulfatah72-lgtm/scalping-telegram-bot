#!/usr/bin/env python3
"""Le modele du bot W1 (vague 5, P3 : W1 sans la variable VIX), en version de production :
- variables calculees au moment exact de la decision (cloture de la minute qui precede l'entree), sans le bruit temoin du
  labo (colonne 22) ni le VIX : 21 variables du labo + sens, minute d'entree, ecart a la VWAP (ATR), rendement depuis
  l'ouverture, ecart d'ouverture, trades deja pris, resultat du jour (28 variables) ;
- diagnostic : la meme marche en avant (2017 - 2026, 10 graines) avec ces variables doit donner le meme ordre de grandeur que P3 ;
- modele final : 10 graines appris sur tous les trades du Supertrend (2011 -> 2 nov. 2026), seuil = part de trades gagnants ;
  exporte pour le C# (bot3en1/W1.Core/modele_w1.json) avec une reference trade par trade pour le test d'identite.
MINUTES_NQ=... CACHE_DOSSIER=... python3 w1_prod.py <reference_w1.csv>"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

import bots as BT
import w1 as W

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import caracteristiques as K  # noqa: E402
import donnees as Dn  # noqa: E402

R = Path(__file__).resolve().parents[2]
NOMS = list(K.NOMS[:21]) + ["sens", "minute d'entrée", "écart à la VWAP (ATR)", "rendement depuis l'ouverture", "écart d'ouverture",
                            "trades déjà pris", "résultat du jour"]
B = BT.Base(os.environ["CACHE_DOSSIER"])
O, H, L, C, V, F, ATR = B.O, B.H, B.L, B.C, B.V, B.X["F"], B.atr
ST = sorted(BT.supertrend(B), key=lambda t: (t[0], t[2]))


def pnl(sens, e, x):
    return sens * (x - e) * 2.0 * Dn.PREF / e - Dn.FRAIS


X, y, an = [], [], []
for k, (s, sens, m, _, fin, e, x) in enumerate(ST):
    if k == 0 or ST[k - 1][0] != s:
        nb_avant, res_avant = 0, 0.0
    c = C[s, m - 1]                                                      # derniere cloture connue a la decision
    g = BT.bougie_avant(s, m)
    tp = (H[s, :m] + L[s, :m] + C[s, :m]) / 3; vv = V[s, :m]
    vw = (tp * vv).sum() / vv.sum() if vv.sum() > 0 else tp.mean()
    atr = ATR[g] if g >= 0 and np.isfinite(ATR[g]) and ATR[g] > 0 else np.nan
    gap = O[s, 0] / C[s - 1, 389] - 1 if s > 0 and B.ok[s - 1] else np.nan
    res_dec = res_avant
    if k > 0 and ST[k - 1][0] == s and ST[k - 1][4] == m - 1:          # le trade precedent se ferme a cette meme minute :
        p_ = ST[k - 1]; res_dec = res_avant - pnl(p_[1], p_[5], p_[6]) + pnl(p_[1], p_[5], c)   # valorise a la cloture connue
    X.append(np.r_[F[g, :21] if g >= 0 else np.full(21, np.nan), sens, m, sens * (c - vw) / atr, sens * (c / O[s, 0] - 1), sens * gap,
                   nb_avant, res_dec])
    r_ = pnl(sens, e, x); y.append(int(r_ > 0)); an.append(int(B.J[s][:4]))
    nb_avant += 1; res_avant += r_
X, y, an = np.array(X, float), np.array(y), np.array(an)

# ------------------------------------------------------------------ diagnostic : marche en avant avec les variables de production
p = W.probas(X, y, an); W1p, garde = W.tri(ST, p, y, an)
aj = B.an[B.test]; FEN = aj >= 2017; d17 = int(np.argmax(FEN)); jours = [B.J[s] for s in B.test]
r, dp, ntr = BT.journees(B, W1p, 1, 400.0)
j, dd, tt = r[B.test], dp[B.test], ntr[B.test] > 0
vie = BT.vie(np.vstack([j, j, j]), np.vstack([dd, dd, dd]), tt, debut=d17)
jw = j[FEN]
r6 = BT.journees(B, W1p, 1, 400.0, 6.0)[0][B.test][FEN]; cum = np.cumsum(jw); a_ = aj[FEN]
idx = pd.to_datetime(np.array(jours)[FEN]); sj = pd.Series(jw, index=idx)
sem = sj.groupby([idx.isocalendar().year.values, idx.isocalendar().week.values]).sum()
r_st = BT.journees(B, ST, 1, 400.0)[0][B.test][FEN]; cst = np.cumsum(r_st)
DIAG = dict(t=BT.tst(jw), t_avant=BT.tst(jw[a_ <= 2022]), t_apres=BT.tst(jw[a_ >= 2023]), t_frais6=BT.tst(r6),
            annees_pos=int(sum(jw[a_ == yy].sum() > 0 for yy in range(2017, 2027))), seances=float(tt[FEN].mean()),
            semaines_positives=float((sem > 0).mean()), pire_baisse=float((cum - np.maximum.accumulate(cum)).min()),
            pire_baisse_st=float((cst - np.maximum.accumulate(cst)).min()), periode=float(j[np.array([x >= "2026-08-11" for x in jours])].sum()))
print("règles de P3 sur la version de production :", {k: round(v, 2) for k, v in DIAG.items()})
print(f"production, marche en avant 2017 - 2026 : t {BT.tst(jw):.2f}, depuis 2023 {BT.tst(j[aj >= 2023]):.2f}, séances {tt[FEN].mean():.0%}, "
      f"survie {1 - BT.grilles_depuis(jw, dd[FEN], 60).mean():.0%}, grillé 1 an {BT.grilles_depuis(jw, dd[FEN], 250).mean():.0%}, "
      f"{vie['grilles_an']:.2f} grillés/an, net {vie['net_an']:,.0f} $/an (P3 de la vague 5 : t 3,73, depuis 2023 1,72, 76 %, survie 84 %, "
      f"0,31 grillé/an, 6 194 $/an)".replace(",", " "), flush=True)

# ------------------------------------------------------------------ modele final et export pour le C#
seuil = float(y.mean()); modeles, finals = [], []
for gr in W.GRAINES:
    f = xgb.XGBClassifier(random_state=gr, **W.PARAMS).fit(X, y); finals.append(f)
    m_ = json.loads(f.get_booster().save_raw("json").decode())
    base = float(str(m_["learner"]["learner_model_param"]["base_score"]).strip("[]"))
    modeles.append(dict(graine=gr, base=base, arbres=[dict(g=t["left_children"], d=t["right_children"], v=t["split_indices"], s=t["split_conditions"],
                                                           m=[bool(z) for z in t["default_left"]]) for t in m_["learner"]["gradient_booster"]["model"]["trees"]]))


def predire(x):                                       # meme parcours que le C# (flottants 32 bits, NaN -> branche par defaut)
    x32 = np.asarray(x, dtype=np.float32); ps = []
    for md in modeles:
        tot = np.float32(0)
        for a in md["arbres"]:
            n = 0
            while a["g"][n] != -1:
                v = x32[a["v"][n]]
                n = (a["g"][n] if a["m"][n] else a["d"][n]) if np.isnan(v) else (a["g"][n] if v < np.float32(a["s"][n]) else a["d"][n])
            tot = np.float32(tot + np.float32(a["s"][n]))
        ps.append(1 / (1 + np.exp(-(np.log(md["base"] / (1 - md["base"])) + float(tot)))))
    return float(np.mean(ps))


pf = np.mean([f.predict_proba(X)[:, 1] for f in finals], 0)
pm = np.array([predire(x) for x in X[-1500:]])
print("parcours maison contre XGBoost (1 500 trades) : écart max", float(np.abs(pm - pf[-1500:]).max()))
dossier = R / "bot3en1/W1.Core"; dossier.mkdir(exist_ok=True)
json.dump(dict(modeles=modeles, variables=NOMS, seuil=seuil, entraine_jusqua=B.J[ST[-1][0]], trades=len(ST),
               reglages="moyenne de 10 modeles (graines 0 a 9) ; chacun 200 arbres, profondeur 3, pas 0,05, sous-echantillons 0,8 / 0,8, au moins 20 par feuille"),
          open(dossier / "modele_w1.json", "w"), separators=(",", ":"))
ref = an >= 2023
with open(sys.argv[1], "w") as fo:
    fo.write("jour,minute,sens," + ",".join(f"f{k}" for k in range(X.shape[1])) + ",p,pris\n")
    for i in np.nonzero(ref)[0]:
        s, sens, m = ST[i][0], ST[i][1], ST[i][2]
        fo.write(f"{B.J[s]},{m},{sens}," + ",".join("nan" if not np.isfinite(v) else repr(float(v)) for v in X[i]) + f",{float(pf[i])!r},{int(pf[i] > seuil)}\n")
json.dump(dict(diagnostic=dict(**DIAG, net_an=vie["net_an"], grilles_an=vie["grilles_an"]), seuil=seuil, trades=len(ST), garde_final=float((pf > seuil).mean())),
          open(R / "ml/arene/resultats/w1_prod.json", "w"))
print(f"modèle final : {len(ST)} trades jusqu'au {B.J[ST[-1][0]]}, seuil {seuil:.3f}, garde {np.mean(pf > seuil):.0%} des trades (dans l'échantillon)")
