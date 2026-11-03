#!/usr/bin/env python3
"""Donnees du graphique pro (15 min), des paysages 3D et du signal d'apprentissage automatique (walk-forward)."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

S = Path("/tmp/claude-0/-home-user-scalping-telegram-bot/73d2fc28-0760-5668-987b-2a927564efe7/scratchpad")
sys.path.insert(0, "/home/user/scalping-telegram-bot/audit/machine6")
import pyramide as P  # noqa: E402

N = 390
NB = 26                                   # barres de 15 min par seance
DERNIERES = 60


def charger(csv):
    J, O, H, L, C, ok = P.jours(csv)
    d = pd.read_csv(csv, usecols=["t", "v"])
    j = d.t.str[:10]; m = d.t.str[11:13].astype(int) * 60 + d.t.str[14:16].astype(int) - 570
    g = (m >= 0) & (m < N)
    V = np.zeros((len(J), N)); V[pd.Index(J).get_indexer(j[g]), m[g].to_numpy()] = d.v[g].to_numpy(float)
    return J, O, H, L, C, V, ok


def barres15(O, H, L, C, V):
    S_ = O.shape[0]
    o = O[:, 0::15][:, :NB].ravel(); c = C[:, 14::15][:, :NB].ravel()
    h = H.reshape(S_, NB, 15).max(2).ravel(); l = L.reshape(S_, NB, 15).min(2).ravel(); v = V.reshape(S_, NB, 15).sum(2).ravel()
    return o, h, l, c, v


def ema(x, n):
    a = 2 / (n + 1); out = np.empty_like(x); out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out


def indicateurs(o, h, l, c):
    I = {f"ema{n}": ema(c, n) for n in (8, 13, 21, 34, 55, 89)}
    s = pd.Series(c)
    mid = s.rolling(20).mean(); sd = s.rolling(20).std(ddof=0)
    I["bb_h"] = (mid + 2 * sd).to_numpy(); I["bb_m"] = mid.to_numpy(); I["bb_b"] = (mid - 2 * sd).to_numpy()
    d = np.diff(c, prepend=c[0]); up = np.maximum(d, 0); dn = np.maximum(-d, 0)
    au = np.zeros_like(c); ad = np.zeros_like(c)
    au[14] = up[1:15].mean(); ad[14] = dn[1:15].mean()
    for i in range(15, len(c)):
        au[i] = (au[i - 1] * 13 + up[i]) / 14; ad[i] = (ad[i - 1] * 13 + dn[i]) / 14
    rsi = np.where(ad == 0, 100, 100 - 100 / (1 + au / np.where(ad == 0, 1, ad))); rsi[:15] = np.nan
    I["rsi"] = rsi
    macd = ema(c, 12) - ema(c, 26); sig = ema(macd, 9)
    I["macd"] = macd; I["macd_s"] = sig; I["macd_h"] = macd - sig
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(abs(h - pc), abs(l - pc)))
    atr = np.zeros_like(c); atr[13] = tr[:14].mean()
    for i in range(14, len(c)):
        atr[i] = (atr[i - 1] * 13 + tr[i]) / 14
    atr[:13] = np.nan
    I["atr"] = atr
    bw = (I["bb_h"] - I["bb_b"]) / I["bb_m"]
    I["bbw"] = bw
    I["bbw_rang"] = pd.Series(bw).rolling(500, min_periods=100).rank(pct=True).to_numpy() * 100
    return I


# ------------------------------------------------------------------ apprentissage automatique : regression logistique walk-forward
def logistique(X, y, l2=1.0, iters=12):
    w = np.zeros(X.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-X @ w))
        g = X.T @ (p - y) + l2 * np.r_[0, w[1:]]
        Hm = (X * (p * (1 - p))[:, None]).T @ X + l2 * np.diag(np.r_[0, np.ones(len(w) - 1)])
        w -= np.linalg.solve(Hm, g)
    return w


def ml(J, o, h, l, c, I, ok):
    n = len(c); sess = np.repeat(np.arange(len(J)), NB); b = np.tile(np.arange(NB), len(J))
    an = np.array([int(J[s][:4]) for s in sess])
    lr = np.log(c / np.r_[c[0], c[:-1]])
    f = {
        "rendement 15 min": lr,
        "rendement 1 h": pd.Series(lr).rolling(4).sum().to_numpy(),
        "rendement 4 h": pd.Series(lr).rolling(16).sum().to_numpy(),
        "RSI 14 (centre)": (I["rsi"] - 50) / 50,
        "MACD histogramme": I["macd_h"] / c * 100,
        "position dans Bollinger": (c - I["bb_m"]) / (I["bb_h"] - I["bb_m"]),
        "ATR / prix": I["atr"] / c * 100,
        "largeur Bollinger (rang)": I["bbw_rang"] / 100,
        "ecart EMA 8 - EMA 55": (I["ema8"] - I["ema55"]) / c * 100,
        "heure (sinus)": np.sin(2 * np.pi * b / NB),
        "heure (cosinus)": np.cos(2 * np.pi * b / NB),
    }
    noms = list(f)
    F = np.column_stack([f[k] for k in noms])
    fut = np.r_[c[4:], np.full(4, np.nan)]
    meme = (b <= NB - 5)                       # la cible reste dans la seance
    y = (fut > c).astype(float)
    okb = ok[sess] & meme & np.isfinite(F).all(1) & np.isfinite(fut)
    proba = np.full(n, np.nan)
    res = []
    poids = None
    tous = []
    for Y in range(2014, 2027):
        tr = okb & (an < Y); te = (an == Y) & np.isfinite(F).all(1)
        mu, sd = F[tr].mean(0), F[tr].std(0) + 1e-12
        Xtr = np.column_stack([np.ones(tr.sum()), (F[tr] - mu) / sd])
        w = logistique(Xtr, y[tr])
        Xte = np.column_stack([np.ones(te.sum()), (F[te] - mu) / sd])
        proba[te] = 1 / (1 + np.exp(-Xte @ w))
        ev = te & okb
        p = proba[ev]; yy = y[ev]
        pts = (fut[ev] - c[ev])
        sig = np.where(p > 0.55, 1, np.where(p < 0.45, -1, 0))
        usd = sig[sig != 0] * pts[sig != 0] * 2 * 28500 / c[ev][sig != 0] - 3
        tous.append((Y, usd))
        res.append(dict(annee=Y, barres=int(ev.sum()), precision=float(((p > .5) == (yy == 1)).mean() * 100),
                        hausse=float(yy.mean() * 100), signaux=int((sig != 0).sum()),
                        par_signal=float(usd.mean()) if len(usd) else 0.0,
                        t=float(usd.mean() / usd.std(ddof=1) * np.sqrt(len(usd))) if len(usd) > 2 else 0.0,
                        total=float(usd.sum())))
        poids = w[1:]
        modele = dict(w=[float(v) for v in w], mu=[float(v) for v in mu], sd=[float(v) for v in sd], noms=noms)
    ordre = np.argsort(-np.abs(poids))
    def bilan(sel):
        u = np.concatenate([x for Y, x in tous if sel(Y)])
        return dict(signaux=int(len(u)), par_signal=float(u.mean()), t=float(u.mean() / u.std(ddof=1) * np.sqrt(len(u))), total=float(u.sum()))
    json.dump(modele, open(S / "terminal/modele_ml.json", "w"))
    return proba, res, [[noms[i], float(poids[i])] for i in ordre], dict(tout=bilan(lambda Y: True), avant2023=bilan(lambda Y: Y < 2023), depuis2023=bilan(lambda Y: Y >= 2023))


def paquet(J, O, H, L, C, V, ok, avec_ml):
    o, h, l, c, v = barres15(O, H, L, C, V)
    I = indicateurs(o, h, l, c)
    out = {}
    if avec_ml:
        proba, res, poids, bil = ml(J, o, h, l, c, I, ok)
        out["ml"] = dict(annees=res, poids=poids, bilan=bil)
        print("bilan ML", bil)
    k0 = (len(J) - DERNIERES) * NB
    r = lambda x, d=2: [None if not np.isfinite(t) else round(float(t), d) for t in x[k0:]]
    out["jours"] = list(J[-DERNIERES:])
    out["complete"] = [bool(x) for x in ok[-DERNIERES:]]
    out["barres"] = [[round(float(a), 2), round(float(b_), 2), round(float(cc), 2), round(float(d), 2), int(e)] for a, b_, cc, d, e in zip(o[k0:], h[k0:], l[k0:], c[k0:], v[k0:])]
    out["ind"] = {k: r(I[k], 1 if k in ("rsi", "bbw_rang") else 2) for k in I if k not in ("bbw",)}
    out["ind"]["bbw"] = r(I["bbw"] * 100, 3)
    if avec_ml:
        out["proba"] = r(proba, 3)
    # profils de volume des seances (cases de 25 points, prix typique de chaque minute)
    s0 = len(J) - DERNIERES
    lo = np.floor(L[s0:].min() / 25) * 25; hi = np.ceil(H[s0:].max() / 25) * 25
    nb = int((hi - lo) / 25)
    prof = []
    for s in range(s0, len(J)):
        tp = (H[s] + L[s] + C[s]) / 3
        k = np.clip(((tp - lo) / 25).astype(int), 0, nb - 1)
        p = np.bincount(k, weights=V[s], minlength=nb)
        prof.append([int(x) for x in p])
    out["profils"] = dict(bas=float(lo), pas=25, cases=nb, valeurs=prof)
    return out


D = {}
J, O, H, L, C, V, ok = charger(str(S / "depuis13/minutes.csv"))
D["NQ"] = paquet(J, O, H, L, C, V, ok, True)
print("NQ", D["NQ"]["jours"][0], "->", D["NQ"]["jours"][-1], "; ML :", [(r["annee"], round(r["precision"], 1), round(r["par_signal"], 1), round(r["t"], 2)) for r in D["NQ"]["ml"]["annees"]])
J2, O2, H2, L2, C2, V2, ok2 = charger(str(S / "kb/intraday/donnees/sp500_1min.csv.gz"))
D["ES"] = paquet(J2, O2, H2, L2, C2, V2, ok2, False)
print("ES", D["ES"]["jours"][0], "->", D["ES"]["jours"][-1])


def propre(x):
    if isinstance(x, dict):
        return {k: propre(v) for k, v in x.items()}
    if isinstance(x, list):
        return [propre(v) for v in x]
    if isinstance(x, float) and not np.isfinite(x):
        return None
    return x


json.dump(propre(D), open(S / "terminal/donnees2.json", "w"), separators=(",", ":"), allow_nan=False)
print("ok", (S / "terminal/donnees2.json").stat().st_size // 1024, "Ko")
