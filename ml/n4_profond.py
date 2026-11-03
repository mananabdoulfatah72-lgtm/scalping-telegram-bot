#!/usr/bin/env python3
"""Niveau 4a (ml/REGLES.md) : transformer causal a quantiles (TFT allege) code a la main en PyTorch, contre la regression
lineaire quantile et les quantiles fixes, marche en avant purgee 2019 - 2026."""
import json
import math
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as Fn
from scipy import stats
from sklearn.linear_model import QuantileRegressor

import caracteristiques as K
import donnees as D

torch.set_num_threads(4)
t0 = time.time()
X = K.construire()
F, c, fut, sess, b, an, okb, ok, J = (X[k] for k in ("F", "c", "fut", "sess", "b", "an", "okb", "ok", "J"))
F = F[:, :21]                                   # sans le bruit temoin
Q = torch.tensor([0.1, 0.5, 0.9])
T_SEQ, DM, TETES = 32, 32, 4
cible = 1e4 * np.log(fut / c)                   # rendement de l'heure suivante, en points de base
an_j = np.array([int(j[:4]) for j in J]); ANNEES = list(range(2019, 2027)); PURGE = 21
debut_an = {Y: int(np.argmax(an_j == Y)) for Y in ANNEES}
utile = okb & (np.arange(len(c)) >= T_SEQ - 1)


class Attention(nn.Module):
    """Attention multi-tetes causale ecrite a la main : softmax(Q K^T / racine(d)) V, futur masque."""
    def __init__(self, d, h):
        super().__init__(); self.h, self.dk = h, d // h
        self.q, self.k, self.v, self.o = (nn.Linear(d, d) for _ in range(4))

    def forward(self, x):
        B, T, d = x.shape
        sep = lambda z: z.view(B, T, self.h, self.dk).transpose(1, 2)
        q, k, v = sep(self.q(x)), sep(self.k(x)), sep(self.v(x))
        s = q @ k.transpose(-2, -1) / math.sqrt(self.dk)
        s = s.masked_fill(torch.triu(torch.ones(T, T, dtype=torch.bool), 1), float("-inf"))
        a = torch.softmax(s, -1)
        return self.o((a @ v).transpose(1, 2).reshape(B, T, d))


class Bloc(nn.Module):
    def __init__(self, d, h):
        super().__init__(); self.n1, self.n2 = nn.LayerNorm(d), nn.LayerNorm(d); self.att = Attention(d, h)
        self.ff = nn.Sequential(nn.Linear(d, 2 * d), nn.GELU(), nn.Linear(2 * d, d)); self.dr = nn.Dropout(0.1)

    def forward(self, x):
        x = x + self.dr(self.att(self.n1(x)))
        return x + self.dr(self.ff(self.n2(x)))


class TFTLeger(nn.Module):
    """Selection de variables (porte softmax par bougie), plongement, position apprise, 2 blocs d'attention causale,
    sortie : quantiles 10 / 50 / 90 % (ordonnes par construction)."""
    def __init__(self, nv, d=DM, h=TETES, T=T_SEQ):
        super().__init__()
        self.E = nn.Parameter(torch.randn(nv, d) * 0.1); self.Eb = nn.Parameter(torch.zeros(nv, d))
        self.porte = nn.Linear(nv, nv); self.pos = nn.Parameter(torch.zeros(T, d))
        self.blocs = nn.ModuleList([Bloc(d, h) for _ in range(2)]); self.n = nn.LayerNorm(d); self.sortie = nn.Linear(d, 3)

    def forward(self, x):
        w = torch.softmax(self.porte(x), -1)                          # (B, T, nv) : poids de chaque variable
        e = x.unsqueeze(-1) * self.E + self.Eb                         # (B, T, nv, d)
        h = (w.unsqueeze(-1) * e).sum(2) + self.pos
        for bl in self.blocs:
            h = bl(h)
        z = self.sortie(self.n(h[:, -1]))
        m = z[:, 1]
        return torch.stack([m - Fn.softplus(z[:, 0]), m, m + Fn.softplus(z[:, 2])], 1), w


def pinball(pred, y):
    e = y.unsqueeze(1) - pred
    return torch.maximum(Q * e, (Q - 1) * e).mean()


def pinball_np(pred, y):
    e = y[:, None] - pred; q = Q.numpy()
    return np.maximum(q * e, (q - 1) * e).mean(0)


def sequences(idx, Z):
    o = idx[:, None] - np.arange(T_SEQ - 1, -1, -1)[None, :]
    return torch.tensor(Z[o], dtype=torch.float32)


res = {"annees": {}}
pred_tf = np.full((len(c), 3), np.nan); pred_li = np.full((len(c), 3), np.nan); pred_cl = np.full((len(c), 3), np.nan)
poids_var = None
for Y in ANNEES:
    tr = np.nonzero(utile & (sess < debut_an[Y] - PURGE))[0]; te = np.nonzero(utile & (an == Y))[0]
    mu, sd = np.nanmean(F[tr], 0), np.nanstd(F[tr], 0) + 1e-9
    Z = np.nan_to_num((F - mu) / sd).clip(-8, 8)
    ytr = torch.tensor(cible[tr], dtype=torch.float32)
    torch.manual_seed(3); np.random.seed(3)
    net = TFTLeger(Z.shape[1]); opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    for ep in range(6):
        net.train(); perm = np.random.permutation(len(tr))
        for k in range(0, len(tr), 512):
            j = perm[k:k + 512]
            p, _ = net(sequences(tr[j], Z)); loss = pinball(p, ytr[j])
            opt.zero_grad(); loss.backward(); opt.step()
    net.eval()
    with torch.no_grad():
        out, ww = [], []
        for k in range(0, len(te), 2048):
            p, w = net(sequences(te[k:k + 2048], Z)); out.append(p.numpy()); ww.append(w[:, -1].mean(0).numpy())
        pred_tf[te] = np.vstack(out)
        if Y == 2026:
            poids_var = np.mean(ww, 0)
    # base lineaire quantile (exacte) sur la derniere bougie, et quantiles fixes de l'entrainement
    for qi, q in enumerate([0.1, 0.5, 0.9]):
        sous = tr[::3]                                                # un tiers de l'entrainement : le solveur exact reste rapide
        qr = QuantileRegressor(quantile=q, alpha=0.0, solver="highs").fit(Z[sous], cible[sous])
        pred_li[te, qi] = qr.predict(Z[te])
        pred_cl[te, qi] = np.quantile(cible[tr], q)
    yt = cible[te]
    res["annees"][Y] = {nm: dict(pinball=float(pinball_np(P_[te], yt).mean()), couverture=float(((yt >= P_[te, 0]) & (yt <= P_[te, 2])).mean()))
                        for nm, P_ in (("transformer", pred_tf), ("lineaire", pred_li), ("fixe", pred_cl))}
    print(Y, {k: round(v["pinball"], 3) for k, v in res["annees"][Y].items()}, f"{time.time() - t0:.0f} s", flush=True)

ev = utile & (an >= 2019)
sess_ok = np.nonzero(ok)[0]; test_s = sess_ok[an_j[sess_ok] >= 2019]


def trading(P_):
    m = P_[:, 1]; sig = np.where(ev & np.isfinite(m) & (np.abs(m) > 1.0), np.sign(np.nan_to_num(m)), 0)
    usd = np.where(sig != 0, sig * (fut - c) * 2 * D.PREF / c - D.FRAIS, 0.0)
    jour = np.bincount(sess, weights=np.nan_to_num(usd), minlength=X["S"])[test_s]
    tt = lambda v: float(v.mean() / v.std(ddof=1) * np.sqrt(len(v)))
    a, z = jour[an_j[test_s] <= 2022], jour[an_j[test_s] >= 2023]
    t = tt(jour)
    return dict(signaux=int((sig != 0).sum()), par_seance=float(jour.mean()), t=t, p=float(1 - stats.t.cdf(t, len(jour) - 1)),
                t_avant=tt(a), t_apres=tt(z), sharpe=float(jour.mean() / jour.std(ddof=1) * np.sqrt(252)), courbe=np.cumsum(jour).round(1).tolist())


yt = cible[ev]
for nm, P_ in (("transformer", pred_tf), ("lineaire", pred_li), ("fixe", pred_cl)):
    res[nm] = dict(pinball=float(pinball_np(P_[ev], yt).mean()), par_quantile=pinball_np(P_[ev], yt).tolist(),
                   couverture=float(((yt >= P_[ev, 0]) & (yt <= P_[ev, 2])).mean()), trading=trading(P_) if nm != "fixe" else None)
res["poids_variables_2026"] = sorted([[K.NOMS[i], float(poids_var[i])] for i in range(21)], key=lambda x: -x[1])
res["parametres"] = int(sum(p.numel() for p in TFTLeger(21).parameters()))
json.dump(res, open(D.SORTIE / "n4a.json", "w"))
txt = [f"# Niveau 4a : transformer causal à quantiles ({res['parametres']:,} paramètres), test 2019 - 2026\n",
       "| modèle | perte pinball (plus bas = mieux) | couverture 10-90 % (cible 80 %) | signaux | $ par séance | t | p | t 2019-2022 | t 2023-2026 |",
       "|---|---|---|---|---|---|---|---|---|"]
for nm, lab in (("transformer", "Transformer (TFT allégé)"), ("lineaire", "Régression linéaire quantile"), ("fixe", "Quantiles fixes")):
    r = res[nm]; tr_ = r["trading"]
    txt.append(f"| {lab} | {r['pinball']:.4f} | {r['couverture']:.1%} | " + (f"{tr_['signaux']:,} | {tr_['par_seance']:+.1f} | {tr_['t']:+.2f} | {tr_['p']:.3f} | {tr_['t_avant']:+.2f} | {tr_['t_apres']:+.2f} |" if tr_ else "— | — | — | — | — | — |"))
txt.append("\nPar année (pinball) : " + " ; ".join(f"{Y} T {v['transformer']['pinball']:.3f} / L {v['lineaire']['pinball']:.3f} / F {v['fixe']['pinball']:.3f}" for Y, v in res["annees"].items()))
txt.append("\nPoids moyens de la sélection de variables (2026, dernière bougie) : " + ", ".join(f"{n} {w:.1%}" for n, w in res["poids_variables_2026"][:8]) + ".")
D.ecrire("n4a.md", "\n".join(txt) + f"\n\n(calcul : {time.time() - t0:.0f} s)\n")
