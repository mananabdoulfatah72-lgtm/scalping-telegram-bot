#!/usr/bin/env python3
"""Dossier de preuves du bot XGBoost NQ (moyenne de 10 modeles, 21 variables), avant le passage en reel.
Marche en avant purgee 2014 - 2026, une position a la fois, entree a l'ouverture de la bougie suivante, sortie 1 h apres,
1 MNQ, 3 $ de frais (dollars au prix d'aujourd'hui). Rien ici ne change la regle : ce sont des mesures."""
import json
import os

import numpy as np
import pandas as pd
import xgboost as xgb
from scipy import stats

import caracteristiques as K
import donnees as D

X = K.construire()
F, y, c, o, fut, sess, b, an, ok, J = (X[k] for k in ("F", "y", "c", "o", "fut", "sess", "b", "an", "ok", "J"))
F = F[:, :21]
an_j = np.array([int(j[:4]) for j in J])
utile = ok[sess] & X["meme"] & np.isfinite(F).all(1) & np.isfinite(fut)
CACHE = os.environ.get("CACHE_DOSSIER", "dossier_p.npy")
if os.path.exists(CACHE):
    p = np.load(CACHE)
else:
    p = np.full(len(c), np.nan)
    for Y in range(2014, 2027):
        tr = utile & (sess < int(np.argmax(an_j == Y)) - 21)
        p[an == Y] = np.mean([xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                                                reg_alpha=1.0, reg_lambda=1.0, tree_method="hist", n_jobs=4, random_state=g)
                              .fit(F[tr], y[tr], verbose=False).predict_proba(F[an == Y])[:, 1] for g in range(10)], 0)
        print(Y, flush=True)
    np.save(CACHE, p)
sess_ok = np.nonzero(ok)[0]; test_s = sess_ok[an_j[sess_ok] >= 2014]
ev = utile & (an >= 2014)


def trades(seuil=0.55, frais=D.FRAIS, signaux=None):
    """Liste des trades (indice de bougie, sens, $) d'une position a la fois."""
    sig = signaux if signaux is not None else np.where(p > seuil, 1, np.where(p < 1 - seuil, -1, 0)) * ev
    out = []; libre = -1
    for i in np.nonzero(sig)[0]:
        if i <= libre:
            continue
        e = o[i + 1]
        out.append((i, int(sig[i]), sig[i] * (fut[i] - e) * 2 * D.PREF / e - frais)); libre = i + 3
    return out


def par_seance(tl):
    usd = np.zeros(len(c))
    for i, s_, u in tl:
        usd[i] = u
    return np.bincount(sess, weights=usd, minlength=X["S"])[test_s]


def tstat(v):
    return float(v.mean() / v.std(ddof=1) * np.sqrt(len(v))) if len(v) > 2 and v.std() > 0 else 0.0


T = trades(); jour = par_seance(T); jours = [J[s] for s in test_s]
u = np.array([t[2] for t in T])
out = {}
# 1. resume
cum = np.cumsum(jour); dd = cum - np.maximum.accumulate(cum)
mois = pd.Series(jour, index=pd.to_datetime(jours)).resample("ME").sum()
serie = (jour > 0).astype(int); perte_suite = max((len(g) for g in "".join(map(str, serie)).split("1")), default=0)
out["resume"] = dict(seances=len(jour), trades=len(T), trades_par_seance=len(T) / len(jour), par_seance=float(jour.mean()), t=tstat(jour),
                     sharpe=float(jour.mean() / jour.std(ddof=1) * np.sqrt(252)), total=float(jour.sum()), pire_baisse=float(dd.min()),
                     taux_gagnant=float((u > 0).mean()), gain_moyen=float(u[u > 0].mean()), perte_moyenne=float(u[u <= 0].mean()),
                     facteur_profit=float(u[u > 0].sum() / -u[u <= 0].sum()), pire_seance=float(jour.min()), meilleure_seance=float(jour.max()),
                     ecart_seance=float(jour.std(ddof=1)), mois_positifs=float((mois > 0).mean()), pire_mois=float(mois.min()),
                     seances_perdantes_de_suite=int(perte_suite), seances_sans_trade=float((jour == 0).mean()))
# 2. annee par annee
out["annees"] = {}
for Y in range(2014, 2027):
    v = jour[an_j[test_s] == Y]
    out["annees"][Y] = dict(seances=len(v), usd=float(v.sum()), par_seance=float(v.mean()), t=tstat(v))
# 3. calibration : quand le modele dit x %, le NQ monte-t-il x % du temps ?
bornes = [0, .40, .45, .50, .55, .60, 1]
cal = []
for a_, b_ in zip(bornes[:-1], bornes[1:]):
    k = ev & (p >= a_) & (p < b_)
    cal.append(dict(de=a_, a=b_, bougies=int(k.sum()), proba_moyenne=float(p[k].mean()) if k.any() else None, hausse_reelle=float(y[k].mean()) if k.any() else None))
out["calibration"] = cal
# 4. contre le hasard : memes nombres de signaux (achats et ventes) places au hasard dans chaque annee, 1 000 fois
rng = np.random.default_rng(21); sig0 = np.where(p > 0.55, 1, np.where(p < 0.45, -1, 0)) * ev
t_hasard = []
for _ in range(1000):
    s2 = np.zeros(len(c), int)
    for Y in range(2014, 2027):
        cand = np.nonzero(ev & (an == Y))[0]; vals = sig0[ev & (an == Y)]
        s2[cand] = rng.permutation(vals)
    t_hasard.append(tstat(par_seance(trades(signaux=s2))))
t_hasard = np.array(t_hasard)
out["hasard"] = dict(t_modele=out["resume"]["t"], t_hasard_moyen=float(t_hasard.mean()), t_hasard_max=float(t_hasard.max()),
                     p=float((t_hasard >= out["resume"]["t"]).mean()), centiles=[float(np.percentile(t_hasard, q)) for q in (50, 95, 99)])
# 5. seuil et frais : la courbe doit etre reguliere (un vrai signal), pas un pic isole
out["seuils"] = {str(s_): (lambda tl: dict(trades=len(tl), par_trade=float(np.mean([t[2] for t in tl])), t=tstat(par_seance(tl))))(trades(s_)) for s_ in (0.52, 0.53, 0.55, 0.57, 0.60)}
out["frais"] = {str(f_): tstat(par_seance(trades(frais=f_))) for f_ in (1.5, 3.0, 4.5, 6.0)}
# 6. achats et ventes, regimes de volatilite (ATR / prix a l'entree, tiers calcules sur 2014 - 2026)
ach = [t for t in T if t[1] > 0]; ven = [t for t in T if t[1] < 0]
out["sens"] = {"achats": dict(trades=len(ach), par_trade=float(np.mean([t[2] for t in ach])), t=tstat(par_seance(ach))),
               "ventes": dict(trades=len(ven), par_trade=float(np.mean([t[2] for t in ven])), t=tstat(par_seance(ven)))}
vol = F[:, 6]; q1, q2 = np.nanpercentile(vol[ev], [33.3, 66.7])
out["volatilite"] = {}
for nom, sel in (("calme", lambda v: v < q1), ("normale", lambda v: (v >= q1) & (v < q2)), ("agitee", lambda v: v >= q2)):
    tl = [t for t in T if sel(vol[t[0]])]
    out["volatilite"][nom] = dict(trades=len(tl), par_trade=float(np.mean([t[2] for t in tl])), t=tstat(par_seance(tl)))
# 7. correlation avec le Supertrend (resultat par seance)
st = pd.read_csv(D.RACINE / "ml/st_trades.csv"); st["usd"] = 2 * st.sens * (st.sortie - st.entree) * D.PREF / st.entree - D.FRAIS
stj = st.groupby("jour").usd.sum().reindex(jours).fillna(0).to_numpy()
out["correlation_supertrend"] = float(np.corrcoef(jour, stj)[0, 1])
comb = jour + stj
out["ensemble_avec_supertrend"] = dict(par_seance=float(comb.mean()), t=tstat(comb), sharpe=float(comb.mean() / comb.std(ddof=1) * np.sqrt(252)))
out["courbe"] = cum[::5].round(0).tolist(); out["dates"] = jours[::5]
json.dump(out, open(D.SORTIE / "dossier.json", "w"))
r = out["resume"]
txt = ["# Dossier de preuves du bot XGBoost NQ (moyenne de 10 modèles)\n",
       f"Marche en avant purgée 2014 - 2026 ({r['seances']} séances), une position à la fois, entrée à la bougie suivante, 1 MNQ, 3 $ de frais.\n",
       f"- {r['trades']} trades ({r['trades_par_seance']:.1f} par séance, {r['seances_sans_trade']:.0%} des séances sans trade) ; {r['par_seance']:+.1f} $ par séance ; t = {r['t']:.2f} ; Sharpe annuel {r['sharpe']:.2f}",
       f"- trades gagnants {r['taux_gagnant']:.1%} ; gain moyen {r['gain_moyen']:+.0f} $, perte moyenne {r['perte_moyenne']:+.0f} $ ; facteur de profit {r['facteur_profit']:.2f}",
       f"- écart type par séance {r['ecart_seance']:.0f} $ ; pire séance {r['pire_seance']:+.0f} $ ; meilleure {r['meilleure_seance']:+.0f} $ ; pire baisse cumulée {r['pire_baisse']:+.0f} $",
       f"- mois positifs {r['mois_positifs']:.0%} ; pire mois {r['pire_mois']:+.0f} $ ; séances perdantes d'affilée au pire {r['seances_perdantes_de_suite']}\n",
       "## Année par année\n\n| année | séances | $ | $ par séance | t |\n|---|---|---|---|---|"]
for Y, a_ in out["annees"].items():
    txt.append(f"| {Y} | {a_['seances']} | {a_['usd']:+,.0f} | {a_['par_seance']:+.1f} | {a_['t']:+.2f} |")
txt.append("\n## Calibration\n\n| probabilité annoncée | bougies | moyenne annoncée | hausse réelle |\n|---|---|---|---|")
for k in cal:
    txt.append(f"| {k['de']:.0%} - {k['a']:.0%} | {k['bougies']:,} | {k['proba_moyenne']:.1%} | {k['hausse_reelle']:.1%} |" if k["bougies"] else f"| {k['de']:.0%} - {k['a']:.0%} | 0 | — | — |")
h = out["hasard"]
txt.append(f"\n## Contre le hasard (1 000 tirages, mêmes signaux placés au hasard dans chaque année)\n\nt du modèle {h['t_modele']:.2f} ; hasard : moyenne {h['t_hasard_moyen']:+.2f}, 99e centile {h['centiles'][2]:+.2f}, maximum {h['t_hasard_max']:+.2f} ; p = {h['p']:.3f}")
txt.append("\n## Seuil et frais\n\n" + " ; ".join(f"seuil {k} : {v['trades']} trades, {v['par_trade']:+.1f} $ par trade, t {v['t']:+.2f}" for k, v in out["seuils"].items()))
txt.append("Frais par aller-retour : " + " ; ".join(f"{k} $ : t {v:+.2f}" for k, v in out["frais"].items()))
txt.append("\n## Achats, ventes, volatilité\n\n" + " ; ".join(f"{k} : {v['trades']} trades, {v['par_trade']:+.1f} $ par trade, t {v['t']:+.2f}" for k, v in {**out["sens"], **out["volatilite"]}.items()))
e = out["ensemble_avec_supertrend"]
txt.append(f"\nCorrélation avec le Supertrend (par séance) : {out['correlation_supertrend']:+.2f} ; les deux ensemble (1 MNQ chacun) : {e['par_seance']:+.1f} $ par séance, t {e['t']:.2f}, Sharpe {e['sharpe']:.2f}.")
D.ecrire("dossier.md", "\n".join(txt) + "\n")
