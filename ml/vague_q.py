#!/usr/bin/env python3
"""Vague Q (ml/VAGUE_Q.md, regles fixees avant calcul) : Q1 l'assemblage sur l'ES, Q2 + contexte macro et volatilite,
Q3a / Q3b tenue de 30 min / 2 h, Q4 saisonnalite de la meme demi-heure. Decision : BH sur les 5, deux moities, hasard,
et pour les variantes, battre le bot actuel."""
import json
import os

import numpy as np
import pandas as pd
import xgboost as xgb
from scipy import stats

import caracteristiques as K
import donnees as D

S_ = os.environ["SCRATCH"]
ES_CSV = os.environ.get("MINUTES_ES", S_ + "/kb/intraday/donnees/sp500_1min.csv.gz")
PARAMS = dict(n_estimators=100, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, reg_alpha=1.0, reg_lambda=1.0,
              tree_method="hist", n_jobs=4)
rng_perm = np.random.default_rng(31)


def tstat(v):
    return float(v.mean() / v.std(ddof=1) * np.sqrt(len(v))) if len(v) > 2 and v.std() > 0 else 0.0


class Marche:
    def __init__(self, X, pref, point):
        self.X = X; self.pref = pref; self.point = point
        self.an_j = np.array([int(j[:4]) for j in X["J"]])
        so = np.nonzero(X["ok"])[0]; self.test_s = so[self.an_j[so] >= 2014]
        self.jours = [X["J"][s] for s in self.test_s]

    def marche_avant(self, Fm, h, nom):
        X = self.X; c, sess, b, an = X["c"], X["sess"], X["b"], X["an"]
        fut = np.r_[c[h:], np.full(h, np.nan)]
        y = (fut > c).astype(float)
        utile = X["ok"][sess] & (b <= 25 - h) & np.isfinite(Fm).all(1) & np.isfinite(fut)
        cache = f"{S_}/vq_{nom}.npy"
        if os.path.exists(cache):
            p = np.load(cache)
        else:
            p = np.full(len(c), np.nan)
            for Y in range(2014, 2027):
                if not (self.an_j == Y).any():
                    continue
                tr = utile & (sess < int(np.argmax(self.an_j == Y)) - 21)
                te = an == Y
                p[te] = np.mean([xgb.XGBClassifier(**PARAMS, random_state=g).fit(Fm[tr], y[tr], verbose=False).predict_proba(Fm[te])[:, 1] for g in range(10)], 0)
                print(nom, Y, flush=True)
            np.save(cache, p)
        sig = np.where(p > 0.55, 1, np.where(p < 0.45, -1, 0)) * (utile & (an >= 2014))
        return sig, fut

    def jouer(self, sig, fut, h):
        X = self.X; o, sess = X["o"], X["sess"]
        usd = np.zeros(len(o)); libre = -1
        for i in np.nonzero(sig)[0]:
            if i <= libre:
                continue
            e = o[i + 1]
            usd[i] = sig[i] * (fut[i] - e) * self.point * self.pref / e - D.FRAIS; libre = i + h - 1
        return np.bincount(sess, weights=usd, minlength=X["S"])[self.test_s]

    def hasard(self, sig, fut, h, n=1000):
        X = self.X; an = X["an"]; ts = []
        for _ in range(n):
            s2 = np.zeros_like(sig)
            for Y in np.unique(an[sig != 0]):
                cand = np.nonzero((an == Y) & np.isfinite(fut) & (X["b"] <= 25 - h) & X["ok"][X["sess"]])[0]
                vals = np.zeros(len(cand), int); k = sig[cand]; vals[:] = k
                s2[cand] = rng_perm.permutation(vals)
            ts.append(tstat(self.jouer(s2, fut, h)))
        return np.array(ts)


def bilan(m, jour, ts=None):
    aj = m.an_j[m.test_s]
    t = tstat(jour)
    r = dict(seances=len(jour), par_seance=float(jour.mean()), t=t, p=float(1 - stats.t.cdf(t, len(jour) - 1)),
             t_avant=tstat(jour[aj <= 2022]), t_apres=tstat(jour[aj >= 2023]), ecart=float(jour.std(ddof=1)),
             pire_baisse=float((np.cumsum(jour) - np.maximum.accumulate(np.cumsum(jour))).min()))
    if ts is not None:
        r["hasard_99"] = float(np.percentile(ts, 99)); r["bat_hasard"] = bool(t > np.percentile(ts, 99))
    return r


# ------------------------------------------------------------------ NQ : bot actuel (reference), Q2, Q3a, Q3b, Q4
XN = K.construire(); NQ = Marche(XN, 28500.0, 2.0)
F21 = XN["F"][:, :21]
p_bot = np.load(S_ + "/dossier_p.npy")
fut1 = np.r_[XN["c"][4:], np.full(4, np.nan)]
utile_bot = XN["ok"][XN["sess"]] & XN["meme"] & np.isfinite(F21).all(1) & np.isfinite(fut1)
sig_bot = np.where(p_bot > 0.55, 1, np.where(p_bot < 0.45, -1, 0)) * (utile_bot & (XN["an"] >= 2014))
jour_bot = NQ.jouer(sig_bot, fut1, 4)
print("bot actuel", bilan(NQ, jour_bot), flush=True)

# Q2 : contexte macro et volatilite connu avant l'ouverture
R = D.radar("c"); R = R.loc[R["SPY"].dropna().index].ffill()
rang = lambda x: x.rolling(252, min_periods=126).rank(pct=True)
M = pd.DataFrame({
    "rang du VIX": rang(R["^VIX"]), "VIX / VIX 3 mois": R["^VIX"] / R["^VIX3M"], "rang du VVIX": rang(R["^VVIX"]),
    "variation du VIX": np.log(R["^VIX"] / R["^VIX"].shift(1)), "taux 10 ans sur 5 j": R["^TNX"] - R["^TNX"].shift(5),
    "dollar sur 5 j": np.log(R["DX-Y.NYB"] / R["DX-Y.NYB"].shift(5)),
    "crédit sur 5 j": np.log(R["HYG"] / R["HYG"].shift(5)) - np.log(R["LQD"] / R["LQD"].shift(5)),
    "semi-conducteurs sur 5 j": np.log(R["SMH"] / R["SMH"].shift(5)) - np.log(R["QQQ"] / R["QQQ"].shift(5))})
dates = M.index.values
pos = np.searchsorted(dates, pd.to_datetime(pd.Series(XN["J"])).values, side="left") - 1     # derniere cloture AVANT la seance
Mv = np.where((pos >= 0)[:, None], M.to_numpy()[np.clip(pos, 0, None)], np.nan)
F29 = np.column_stack([F21, Mv[XN["sess"]]])
res, series = {}, {}
for nom, Fm, h in (("Q2 assemblage + macro", F29, 4), ("Q3a assemblage 30 min", F21, 2), ("Q3b assemblage 2 h", F21, 8)):
    sig, fut = NQ.marche_avant(Fm, h, nom.split()[0])
    jour = NQ.jouer(sig, fut, h)
    ts = NQ.hasard(sig, fut, h)
    res[nom] = bilan(NQ, jour, ts); series[nom] = jour
    d = jour - jour_bot; res[nom]["t_contre_bot"] = tstat(d); res[nom]["correlation_bot"] = float(np.corrcoef(jour, jour_bot)[0, 1])
    print(nom, res[nom], flush=True)

# Q4 : saisonnalite de la meme demi-heure (Heston, Korajczyk, Sadka)
_, O, H, L, C, V, okm = D.nq_minutes()
r30 = np.log(C[:, 29::30][:, :13] / O[:, 0::30][:, :13])
comp = np.nonzero(okm)[0]
gain = np.zeros((len(O), 13)); signe = np.zeros((len(O), 13), int)
for s in NQ.test_s:
    prec = comp[comp < s][-20:]
    if len(prec) < 20:
        continue
    m, sd = r30[prec].mean(0), r30[prec].std(0, ddof=1)
    tt = m / (sd / np.sqrt(20))
    for k in range(13):
        if abs(tt[k]) >= 1:
            e, x = O[s, 30 * k], C[s, 30 * k + 29]
            signe[s, k] = int(np.sign(m[k])); gain[s, k] = signe[s, k] * (x - e) * 2 * 28500 / e - D.FRAIS
G = (C[:, 29::30][:, :13] - O[:, 0::30][:, :13]) * 2 * 28500 / O[:, 0::30][:, :13]     # gain brut d'un achat sur chaque demi-heure
jour4 = gain.sum(1)[NQ.test_s]
ts4 = []
for _ in range(1000):
    g2 = np.zeros(len(O))
    for Y in range(2014, 2027):
        ss = NQ.test_s[NQ.an_j[NQ.test_s] == Y]
        sg = signe[ss].ravel(); sg = rng_perm.permutation(sg).reshape(len(ss), 13)
        g2[ss] = np.where(sg != 0, sg * G[ss] - D.FRAIS, 0.0).sum(1)
    ts4.append(tstat(g2[NQ.test_s]))
res["Q4 même demi-heure"] = bilan(NQ, jour4, np.array(ts4)); series["Q4 même demi-heure"] = jour4
res["Q4 même demi-heure"]["correlation_bot"] = float(np.corrcoef(jour4, jour_bot)[0, 1])
print("Q4", res["Q4 même demi-heure"], flush=True)

# ------------------------------------------------------------------ Q1 : l'assemblage sur l'ES (MES)
XE = K.construire(ES_CSV); ES = Marche(XE, 7800.0, 5.0)
sig, fut = ES.marche_avant(XE["F"][:, :21], 4, "Q1")
jour1 = ES.jouer(sig, fut, 4)
res["Q1 assemblage sur l'ES"] = bilan(ES, jour1, ES.hasard(sig, fut, 4))
bot_par_date = pd.Series(jour_bot, index=NQ.jours)
commun = pd.Series(jour1, index=ES.jours).to_frame("es").join(bot_par_date.rename("nq"), how="inner")
res["Q1 assemblage sur l'ES"]["correlation_bot"] = float(commun.corr().iloc[0, 1])
print("Q1", res["Q1 assemblage sur l'ES"], flush=True)

# ------------------------------------------------------------------ decision
noms = list(res); pv = np.array([res[n]["p"] for n in noms]); o_ = np.argsort(pv)
okbh = pv[o_] <= 0.05 * np.arange(1, len(pv) + 1) / len(pv); kk = np.nonzero(okbh)[0].max() + 1 if okbh.any() else 0
for r_, n in enumerate(noms):
    rr = res[n]; rr["bh"] = bool(n in [noms[i] for i in o_[:kk]])
    rr["retenu"] = bool(rr["bh"] and rr["t_avant"] > 0 and rr["t_apres"] > 0 and rr["bat_hasard"] and (rr.get("t_contre_bot", 9) >= 2 if n[:2] in ("Q2", "Q3") else True))
res["bot actuel (référence)"] = bilan(NQ, jour_bot)
json.dump(res, open(D.SORTIE / "vague_q.json", "w"))
txt = ["# Vague Q : nouveaux setups quant (règles : ml/VAGUE_Q.md)\n",
       "| setup | $ par séance | t | p | t 2014-22 | t 2023-26 | 99e centile du hasard | contre le bot (t) | corrélation avec le bot | BH | retenu |",
       "|---|---|---|---|---|---|---|---|---|---|---|"]
for n in noms:
    r = res[n]
    txt.append(f"| {n} | {r['par_seance']:+.1f} | {r['t']:+.2f} | {r['p']:.4f} | {r['t_avant']:+.2f} | {r['t_apres']:+.2f} | {r['hasard_99']:+.2f} | "
               f"{r.get('t_contre_bot', float('nan')):+.2f} | {r.get('correlation_bot', float('nan')):+.2f} | {'oui' if r['bh'] else 'non'} | **{'OUI' if r['retenu'] else 'non'}** |")
b = res["bot actuel (référence)"]
txt.append(f"\nRéférence, le bot XGBoost NQ actuel : {b['par_seance']:+.1f} $ par séance, t {b['t']:.2f} ({b['t_avant']:+.2f} / {b['t_apres']:+.2f}).")
D.ecrire("vague_q.md", "\n".join(txt) + "\n")
