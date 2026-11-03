#!/usr/bin/env python3
"""Niveau 2 (ml/REGLES.md) : queues epaisses du NQ, Bayes sur le Supertrend, cimetiere des tests multiples (bruit et vrai NQ)."""
import json
import os

import numpy as np
import pandas as pd
from scipy import stats

import donnees as D
from donnees import N

out = {}
txt = ["# Niveau 2 : probabilités et statistiques\n"]


def bh(p, q=0.05):
    """Benjamini-Hochberg : masque des hypotheses rejetees."""
    p = np.asarray(p); m = len(p); o = np.argsort(p)
    ok = p[o] <= q * np.arange(1, m + 1) / m
    k = np.nonzero(ok)[0].max() + 1 if ok.any() else 0
    r = np.zeros(m, bool); r[o[:k]] = True
    return r


# ------------------------------------------------------------------ 2a. queues epaisses
def queues(r, nom, seuils):
    r = r[np.isfinite(r)]
    mu, sd = r.mean(), r.std(ddof=1)
    jb = stats.jarque_bera(r); ks = stats.kstest(r, stats.norm(mu, sd).cdf)
    df, loc, sc = stats.t.fit(r)
    ll_n = stats.norm.logpdf(r, mu, sd).sum(); ll_t = stats.t.logpdf(r, df, loc, sc).sum()
    lignes = []
    for s in seuils:
        pn = stats.norm.cdf(s, mu, sd); pt = stats.t.cdf(s, df, loc, sc); pe = (r <= s).mean()
        lignes.append(dict(seuil=s, normale=float(pn), student=float(pt), observe=float(pe), n_obs=int((r <= s).sum())))
    return dict(nom=nom, n=int(len(r)), moyenne=float(mu), ecart=float(sd), aplatissement=float(stats.kurtosis(r)), asymetrie=float(stats.skew(r)),
                jb_p=float(jb.pvalue), ks_p=float(ks.pvalue), student_df=float(df), student_loc=float(loc), student_echelle=float(sc), ll_normale=float(ll_n), ll_student=float(ll_t),
                aic_normale=float(4 - 2 * ll_n), aic_student=float(6 - 2 * ll_t), seuils=lignes,
                histo=np.histogram(r, bins=120, range=(mu - 8 * sd, mu + 8 * sd))[0].tolist(), bornes=[float(mu - 8 * sd), float(mu + 8 * sd)])


Rr = D.radar("c")["NQ=F"].dropna()
Rr = Rr[Rr.index >= "2000-01-01"]
rq = (Rr / Rr.shift(1) - 1).to_numpy()[1:]
J, O, H, L, C, V, ok = D.nq_minutes()
c5 = C[:, 4::5]; o5 = np.column_stack([O[:, 0], c5[:, :-1]])
r5 = (c5 / o5 - 1)[ok].ravel()
out["queues"] = [queues(rq, "NQ quotidien (NQ=F, 2000 - 2026)", [-0.03, -0.05, -0.07]), queues(r5, "NQ 5 minutes (séances 2011 - 2026)", [-0.005, -0.01, -0.015])]
txt.append("## 2a. Le NQ suit-il une loi normale ?\n")
for q in out["queues"]:
    txt.append(f"**{q['nom']}** ({q['n']:,} rendements) : aplatissement en excès {q['aplatissement']:.1f} (0 pour une normale), asymétrie {q['asymetrie']:+.2f} ; "
               f"Jarque-Bera p = {q['jb_p']:.1e}, Kolmogorov-Smirnov p = {q['ks_p']:.1e} → **normalité rejetée**. "
               f"Student ajustée : {q['student_df']:.1f} degrés de liberté ; AIC normale {q['aic_normale']:,.0f} contre Student {q['aic_student']:,.0f} (plus bas = mieux).\n")
    txt.append("| baisse d'au moins | normale | Student | observé |\n|---|---|---|---|")
    for s in q["seuils"]:
        f = lambda p: "jamais" if p <= 0 else f"1 sur {1 / p:,.0f}".replace(",", " ") if 1 / p < 1e7 else f"1 sur 10^{np.log10(1 / p):.0f}"
        txt.append(f"| {-s['seuil']:.1%} | {f(s['normale'])} | {f(s['student'])} | {f(s['observe'])} ({s['n_obs']} fois) |")
    txt.append("")

# ------------------------------------------------------------------ 2b. Bayes sur le Supertrend NQ
st = pd.read_csv(os.environ.get("ST_TRADES") or (D.RACINE / "ml/st_trades.csv"))
st["usd"] = 2 * st.sens * (st.sortie - st.entree) * D.PREF / st.entree - D.FRAIS
jour = st.groupby("jour").usd.sum()
an = jour.index.str[:4].astype(int)
periodes = {"2011-2022": jour[an <= 2022], "2023-2026": jour[an >= 2023], "2011-2026": jour}
bayes = {}
for nom, x in periodes.items():
    n = len(x); m = x.mean(); s = x.std(ddof=1); w = int((x > 0).sum())
    p_taux = 1 - stats.beta.cdf(0.5, 1 + w, 1 + n - w)
    p_jeff = stats.t.cdf(m / (s / np.sqrt(n)), n - 1)
    prec = 1 / 10 ** 2 + n / s ** 2; mpost = (n * m / s ** 2) / prec; sdpost = np.sqrt(1 / prec)
    bayes[nom] = dict(seances=n, gagnantes=w, taux=w / n, p_taux_sup_50=float(p_taux), moyenne=float(m), ecart=float(s), p_mu_pos_jeffreys=float(p_jeff),
                      post_sceptique=[float(mpost), float(sdpost)], p_mu_pos_sceptique=float(stats.norm.cdf(mpost / sdpost)))
# trajectoire de l'a posteriori du gain moyen (a priori sceptique), seance apres seance
x = jour.to_numpy(); s2 = x.std(ddof=1) ** 2; traj = []
for k in range(20, len(x) + 1, 20):
    prec = 1 / 100 + k / s2; mp_ = (x[:k].sum() / s2) / prec
    traj.append([jour.index[k - 1], float(mp_), float(np.sqrt(1 / prec))])
out["bayes"] = dict(periodes=bayes, trajectoire=traj)
txt.append("## 2b. Bayes : le Supertrend NQ a-t-il un vrai avantage ? (1 MNQ, 3 $ de frais)\n")
txt.append("| période | séances | gagnantes | P(taux > 50 %) | gain moyen | P(gain moyen > 0), Jeffreys | a posteriori sceptique | P(gain moyen > 0), sceptique |")
txt.append("|---|---|---|---|---|---|---|---|")
for nom, b in bayes.items():
    txt.append(f"| {nom} | {b['seances']} | {b['taux']:.1%} | {b['p_taux_sup_50']:.0%} | {b['moyenne']:+.1f} $ | {b['p_mu_pos_jeffreys']:.1%} | "
               f"{b['post_sceptique'][0]:+.1f} ± {b['post_sceptique'][1]:.1f} $ | {b['p_mu_pos_sceptique']:.1%} |")

# ------------------------------------------------------------------ 2c. tests multiples
np.random.seed(42)
pv = []
for i in range(1000):
    r = np.random.normal(0, 0.02, 252)
    pv.append(stats.ttest_1samp(r, 0).pvalue)
pv = np.array(pv)
bruit = dict(p05=int((pv < 0.05).sum()), bonferroni=int((pv < 0.05 / 1000).sum()), bh=int(bh(pv).sum()), meilleur_p=float(pv.min()))

# 1 000 regles au hasard sur le vrai NQ
idx = np.nonzero(ok)[0]; idx = idx[idx > 0]
Cc = np.concatenate([C[idx - 1], C[idx]], axis=1)        # seance precedente puis seance du jour : regard en arriere possible des 9 h 30
rng = np.random.default_rng(7)
regles, pr, tr, moy, t_av, t_ap = [], [], [], [], [], []
anr = np.array([int(J[s][:4]) for s in idx])
for k in range(1000):
    e = int(rng.choice(np.arange(0, 301, 5))); du = int(rng.choice([15, 30, 60, 120])); lk = int(rng.choice([5, 15, 30, 60])); sens = int(rng.choice([1, -1]))
    sig = np.sign(Cc[:, N + e - 1] - Cc[:, N + e - 1 - lk]) * sens
    ent = O[idx, e]; sor = C[idx, min(N - 1, e + du - 1)]
    usd = np.where(sig != 0, sig * (sor - ent) * 2 * D.PREF / ent - D.FRAIS, 0.0)
    t_, p_ = stats.ttest_1samp(usd, 0)
    regles.append([e, du, lk, sens]); pr.append(p_); tr.append(t_); moy.append(usd.mean())
    a, b = usd[anr <= 2022], usd[anr >= 2023]
    t_av.append(stats.ttest_1samp(a, 0).statistic); t_ap.append(stats.ttest_1samp(b, 0).statistic)
pr, tr, t_av, t_ap = map(np.array, (pr, tr, t_av, t_ap))
reel = dict(p05=int((pr < 0.05).sum()), p05_gagnantes=int(((pr < 0.05) & (tr > 0)).sum()), bonferroni=int((pr < 0.05 / 1000).sum()), bh=int(bh(pr).sum()),
            bh_gagnantes=int((bh(pr) & (tr > 0)).sum()), meilleure=dict(regle=regles[int(np.argmax(tr))], t=float(tr.max()), p=float(pr[np.argmax(tr)]), usd=float(moy[int(np.argmax(tr))])))
top = np.argsort(-t_av)[:10]
reel["illustration_top10_avant"] = dict(t_avant=float(t_av[top].mean()), t_apres=float(t_ap[top].mean()))
out["multiples"] = dict(bruit=bruit, nq=reel, t_regles=[float(x) for x in tr])
txt.append("\n## 2c. Le cimetière des tests multiples\n")
txt.append(f"- **Bruit pur** (l'expérience de l'article) : {bruit['p05']} stratégies sur 1 000 ont p < 0,05 (50 attendues) ; "
           f"Bonferroni : {bruit['bonferroni']} survivante ; Benjamini-Hochberg : {bruit['bh']}.")
txt.append(f"- **Vrai NQ, 1 000 règles au hasard** : {reel['p05']} ont p < 0,05 (dont {reel['p05_gagnantes']} gagnantes) ; "
           f"Bonferroni : {reel['bonferroni']} ; Benjamini-Hochberg : {reel['bh']} (dont {reel['bh_gagnantes']} gagnantes).")
mr = reel["meilleure"]
txt.append(f"- Meilleure règle : entrée à la minute {mr['regle'][0]}, {mr['regle'][1]} min, regard {mr['regle'][2]} min, "
           f"{'suivre' if mr['regle'][3] > 0 else 'contrer'} ; t = {mr['t']:.2f}, {mr['usd']:+.1f} $ par séance.")
txt.append(f"- Illustration (hors règles fixées) : les 10 meilleures règles de 2011-2022 avaient t = {reel['illustration_top10_avant']['t_avant']:.2f} en moyenne ; "
           f"sur 2023-2026, t = {reel['illustration_top10_avant']['t_apres']:+.2f}.")

json.dump(out, open(D.SORTIE / "n2.json", "w"))
D.ecrire("n2.md", "\n".join(txt) + "\n")
