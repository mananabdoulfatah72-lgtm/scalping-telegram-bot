#!/usr/bin/env python3
"""Niveau 4b (ml/REGLES.md) : allocation de portefeuille entrainee directement sur le Sharpe (perte = - Sharpe),
contre poids egaux, inverse de la volatilite et Markowitz (variance minimale, Sharpe maximal), 16 ETF, test 2012 - 2026."""
import json
import os
import time

import numpy as np
import torch
import torch.nn as nn
from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf

import donnees as D

torch.set_num_threads(4)
t0 = time.time()
ETF = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "IEF", "SHY", "LQD", "HYG", "TIP", "GLD", "SLV", "USO", "VNQ", "UUP"]
P = D.radar("c")[ETF]
P = P.loc[P["SPY"].dropna().index].ffill()
P = P.loc[P.notna().all(1).idxmax():]
R = (P / P.shift(1) - 1).iloc[1:].fillna(0.0)
dates = R.index; Rn = R.to_numpy(); n, k = Rn.shape
an = dates.year.to_numpy()
FEN, LOT = 60, 63
print(f"{k} ETF, {n} jours depuis {dates[0].date()}")


class Allocateur(nn.Module):
    def __init__(self):
        super().__init__()
        self.r = nn.Sequential(nn.Flatten(), nn.Linear(FEN * k, 64), nn.ReLU(), nn.Linear(64, k))

    def forward(self, x):
        return torch.softmax(self.r(x), -1)


def entrees(idx):                                     # rendements des 60 jours AVANT le jour idx
    o = idx[:, None] - np.arange(FEN, 0, -1)[None, :]
    return torch.tensor(Rn[o] * 100, dtype=torch.float32)


W = {nm: np.full((n, k), np.nan) for nm in ("Perte de Sharpe", "Poids égaux", "Inverse volatilité", "Markowitz variance min.", "Markowitz Sharpe max.")}
ANNEES = list(range(2012, 2027))
CACHE = os.environ.get("CACHE_N4B", "")
deja = bool(CACHE) and os.path.exists(CACHE)
if deja:
    z = np.load(CACHE); W = {nm: z[f"w{i}"] for i, nm in enumerate(W)}
for Y in ([] if deja else ANNEES):
    tr = np.nonzero((an < Y) & (np.arange(n) >= FEN))[0]; te = np.nonzero(an == Y)[0]
    torch.manual_seed(5); rng = np.random.default_rng(5)
    net = Allocateur(); opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    blocs = [tr[i:i + LOT] for i in range(0, len(tr) - LOT + 1, LOT)]
    for ep in range(30):
        for j in rng.permutation(len(blocs)):
            idx = blocs[j]
            w = net(entrees(idx)); rp = (w * torch.tensor(Rn[idx], dtype=torch.float32)).sum(1)
            loss = -rp.mean() / (rp.std() + 1e-8)
            opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad():
        W["Perte de Sharpe"][te] = net(entrees(te)).numpy()
    print(Y, f"{time.time() - t0:.0f} s", flush=True)

# references, estimees sur les 252 jours precedents, recalculees chaque jour
debut = int(np.argmax(an >= 2012))
w_mv = w_ms = np.ones(k) / k
cons = ({"type": "eq", "fun": lambda w: w.sum() - 1},); bornes = [(0, 1)] * k
for t in ([] if deja else range(debut, n)):
    h = Rn[t - 252:t]
    W["Poids égaux"][t] = 1 / k
    iv = 1 / (h.std(0) + 1e-9); W["Inverse volatilité"][t] = iv / iv.sum()
    S = LedoitWolf().fit(h).covariance_; mu = h.mean(0)
    w_mv = minimize(lambda w: w @ S @ w, w_mv, jac=lambda w: 2 * S @ w, bounds=bornes, constraints=cons, method="SLSQP").x
    w_ms = minimize(lambda w: -(w @ mu) / np.sqrt(w @ S @ w + 1e-12), w_ms, bounds=bornes, constraints=cons, method="SLSQP").x
    W["Markowitz variance min."][t] = np.clip(w_mv, 0, None) / np.clip(w_mv, 0, None).sum()
    W["Markowitz Sharpe max."][t] = np.clip(w_ms, 0, None) / np.clip(w_ms, 0, None).sum()
print(f"references : {time.time() - t0:.0f} s")
if CACHE and not deja:
    np.savez(CACHE, **{f"w{i}": W[nm] for i, nm in enumerate(W)})


def serie(w, Rs):
    rp = (w * Rs).sum(1)
    drift = np.vstack([w[:1], w[:-1] * (1 + Rs[:-1]) / (1 + rp[:-1, None])])
    rot = np.abs(w - drift).sum(1)
    return rp - 0.0005 * rot, rot


sel = np.arange(debut, n)
res = {}
nets = {}
for nm, w in W.items():
    r, rot = serie(w[sel], Rn[sel])
    nets[nm] = r
    sh = lambda v: float(v.mean() / v.std(ddof=1) * np.sqrt(252))
    a_ = an[sel]
    res[nm] = dict(sharpe=sh(r), sharpe_avant=sh(r[a_ <= 2022]), sharpe_apres=sh(r[a_ >= 2023]), rendement=float((1 + r).prod() ** (252 / len(r)) - 1),
                   vol=float(r.std() * np.sqrt(252)), rotation=float(rot.mean() * 252), pire_baisse=float((np.cumprod(1 + r) / np.maximum.accumulate(np.cumprod(1 + r)) - 1).min()),
                   courbe=np.cumprod(1 + r)[::5].round(4).tolist(), poids_moyens=dict(zip(ETF, np.nanmean(w[sel], 0).round(3).tolist())))
# difference de Sharpe (perte de Sharpe - poids egaux), bootstrap par blocs de 21 jours
rng = np.random.default_rng(9); a, e = nets["Perte de Sharpe"], nets["Poids égaux"]; m = len(a); diffs = []
for _ in range(2000):
    dep = rng.integers(0, m - 21, m // 21 + 1); ix = (dep[:, None] + np.arange(21)).ravel()[:m]
    sa, se = a[ix], e[ix]
    diffs.append(sa.mean() / sa.std() * np.sqrt(252) - se.mean() / se.std() * np.sqrt(252))
diffs = np.array(diffs)
res["test"] = dict(difference=float(res["Perte de Sharpe"]["sharpe"] - res["Poids égaux"]["sharpe"]), p=float((diffs <= 0).mean()))
res["dates"] = [str(d.date()) for d in dates[sel][::5]]
json.dump(res, open(D.SORTIE / "n4b.json", "w"))
txt = [f"# Niveau 4b : allocation à perte de Sharpe, {k} ETF, test 2012 - 2026 (5 points de base par unité de rotation)\n",
       "| méthode | Sharpe net | 2012-2022 | 2023-2026 | rendement annuel | volatilité | pire baisse | rotation par an |", "|---|---|---|---|---|---|---|---|"]
for nm in W:
    r = res[nm]
    txt.append(f"| {nm} | {r['sharpe']:.2f} | {r['sharpe_avant']:.2f} | {r['sharpe_apres']:.2f} | {r['rendement']:+.1%} | {r['vol']:.1%} | {r['pire_baisse']:.1%} | {r['rotation']:.1f} |")
txt.append(f"\nPerte de Sharpe moins poids égaux : {res['test']['difference']:+.2f} de Sharpe ; bootstrap par blocs : p = {res['test']['p']:.3f}.")
txt.append("Poids moyens du réseau : " + ", ".join(f"{a_} {b_:.0%}" for a_, b_ in sorted(res["Perte de Sharpe"]["poids_moyens"].items(), key=lambda x: -x[1])[:6]) + ".")
D.ecrire("n4b.md", "\n".join(txt) + f"\n\n(calcul : {time.time() - t0:.0f} s)\n")
