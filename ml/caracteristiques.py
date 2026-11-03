"""Bougies de 15 minutes du NQ et les 22 variables du niveau 3 (ml/REGLES.md), toutes connues a la cloture de la bougie."""
import numba as nb
import numpy as np
import pandas as pd

import donnees as D

N, NB = 390, 26
NOMS = ["rendement 15 min", "rendement 1 h", "rendement 4 h", "RSI 14 (centré)", "MACD histogramme", "position dans Bollinger",
        "ATR / prix", "largeur Bollinger (rang)", "écart EMA 8 - EMA 55", "heure (sinus)", "heure (cosinus)",
        "distance au VWAP (ATR)", "rendement depuis l'ouverture", "gap d'ouverture", "séance précédente", "volatilité du jour / 20 j",
        "rendement 5 séances", "jour de la semaine", "sens du Supertrend", "distance au Supertrend (ATR)", "position dans la zone",
        "BRUIT TÉMOIN"]
ACTUELLES = list(range(11))


def ema(x, n):
    a = 2 / (n + 1); o = np.empty_like(x); o[0] = x[0]
    for i in range(1, len(x)):
        o[i] = a * x[i] + (1 - a) * o[i - 1]
    return o


@nb.njit(cache=True)
def supertrend_ligne(H, L, C):
    """Supertrend 10-3 sur barres de 5 min continues (meme calcul que audit/machine6/pyramide.py), avec la ligne."""
    S = C.shape[0]; n = S * 78
    h5, l5, c5 = np.empty(n), np.empty(n), np.empty(n)
    for s in range(S):
        for b in range(78):
            i = s * 78 + b
            h5[i] = H[s, 5 * b:5 * b + 5].max(); l5[i] = L[s, 5 * b:5 * b + 5].min(); c5[i] = C[s, 5 * b + 4]
    d_, ligne = np.zeros(n), np.full(n, np.nan)
    atr, hb, lb, d = 0.0, np.nan, np.nan, 1.0
    for i in range(1, n):
        tr = max(h5[i] - l5[i], abs(h5[i] - c5[i - 1]), abs(l5[i] - c5[i - 1]))
        atr = tr if i == 1 else (atr * 9 + tr) / 10
        mid = (h5[i] + l5[i]) / 2
        hb2, lb2 = mid + 3 * atr, mid - 3 * atr
        if i > 1:
            hb2 = hb2 if (hb2 < hb or c5[i - 1] > hb) else hb
            lb2 = lb2 if (lb2 > lb or c5[i - 1] < lb) else lb
            if d > 0 and c5[i] < lb2:
                d = -1.0
            elif d < 0 and c5[i] > hb2:
                d = 1.0
        hb, lb = hb2, lb2
        d_[i] = d if i >= 10 else 0.0
        ligne[i] = lb if d > 0 else hb
    return d_, ligne


def indicateurs(o, h, l, c):
    """Memes formules que terminal/prep2.py (le signal ML actuel)."""
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
    I["macd_h"] = macd - sig
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(abs(h - pc), abs(l - pc)))
    atr = np.zeros_like(c); atr[13] = tr[:14].mean()
    for i in range(14, len(c)):
        atr[i] = (atr[i - 1] * 13 + tr[i]) / 14
    atr[:13] = np.nan
    I["atr"] = atr
    bw = (I["bb_h"] - I["bb_b"]) / I["bb_m"]
    I["bbw_rang"] = pd.Series(bw).rolling(500, min_periods=100).rank(pct=True).to_numpy() * 100
    return I


def construire(csv=None):
    J, O, H, L, C, V, ok = D.nq_minutes(csv)
    S = len(J)
    o = O[:, 0::15][:, :NB].ravel(); c = C[:, 14::15][:, :NB].ravel()
    h = H.reshape(S, NB, 15).max(2).ravel(); l = L.reshape(S, NB, 15).min(2).ravel(); v = V.reshape(S, NB, 15).sum(2).ravel()
    I = indicateurs(o, h, l, c)
    n = len(c); sess = np.repeat(np.arange(S), NB); b = np.tile(np.arange(NB), S)
    an = np.array([int(j[:4]) for j in J])[sess]
    fin = 15 * b + 14                                                    # minute de cloture de la bougie
    lr = np.log(c / np.r_[c[0], c[:-1]])
    F = np.full((n, len(NOMS)), np.nan)
    F[:, 0] = lr
    F[:, 1] = pd.Series(lr).rolling(4).sum().to_numpy()
    F[:, 2] = pd.Series(lr).rolling(16).sum().to_numpy()
    F[:, 3] = (I["rsi"] - 50) / 50
    F[:, 4] = I["macd_h"] / c * 100
    F[:, 5] = (c - I["bb_m"]) / (I["bb_h"] - I["bb_m"])
    F[:, 6] = I["atr"] / c * 100
    F[:, 7] = I["bbw_rang"] / 100
    F[:, 8] = (I["ema8"] - I["ema55"]) / c * 100
    F[:, 9] = np.sin(2 * np.pi * b / NB); F[:, 10] = np.cos(2 * np.pi * b / NB)
    # VWAP de la seance jusqu'a la cloture de la bougie
    ty = (H + L + C) / 3
    cv = np.cumsum(V, 1); ctv = np.cumsum(ty * V, 1); cty = np.cumsum(ty, 1)
    vw = np.where(cv > 0, ctv / np.maximum(cv, 1e-9), cty / np.arange(1, N + 1))[:, 14::15][:, :NB].ravel()
    F[:, 11] = (c - vw) / I["atr"]
    F[:, 12] = np.log(c / O[sess, 0])
    prevC = np.r_[np.nan, C[:-1, N - 1]]; prevO = np.r_[np.nan, O[:-1, 0]]
    F[:, 13] = np.log(O[:, 0] / prevC)[sess]
    F[:, 14] = np.log(prevC / prevO)[sess]
    # volatilite realisee depuis l'ouverture, rapportee a la moyenne des 20 seances precedentes a la meme heure
    r1 = np.diff(np.log(np.column_stack([O[:, 0], C])), axis=1)
    rv = np.sqrt(np.cumsum(r1 ** 2, 1))[:, 14::15][:, :NB]
    moy = pd.DataFrame(rv).rolling(20).mean().shift(1).to_numpy()
    F[:, 15] = (rv / moy).ravel()
    c5 = np.r_[np.full(5, np.nan), C[:-5, N - 1]]
    F[:, 16] = np.log(c / c5[sess])
    F[:, 17] = pd.to_datetime(pd.Series(J)).dt.dayofweek.to_numpy()[sess]
    dST, ligne = supertrend_ligne(H, L, C)
    k5 = sess * 78 + 3 * b + 2
    F[:, 18] = dST[k5]
    F[:, 19] = (c - ligne[k5]) / I["atr"]
    # zone de bruit : 14 seances completes precedentes (comme le bot 3 en 1)
    mv = np.abs(C[:, 29::30][:, :12] / O[:, [0]] - 1)
    zh = np.full((S, 12), np.nan); zb = np.full((S, 12), np.nan)
    comp = np.nonzero(ok)[0]
    for s in range(S):
        prec = comp[comp < s]
        if len(prec) < 14:
            continue
        sig = mv[prec[-14:]].mean(0); veille = C[prec[-1], N - 1]
        rh, rb = max(O[s, 0], veille), min(O[s, 0], veille)
        zh[s] = rh * (1 + sig); zb[s] = rb * (1 - sig)
    kz = np.clip((fin + 1) // 30 - 1, 0, 11)
    hz, bz = zh[sess, kz], zb[sess, kz]
    F[:, 20] = (c - (hz + bz) / 2) / ((hz - bz) / 2)
    F[:, 21] = np.random.default_rng(11).normal(size=n)
    fut = np.r_[c[4:], np.full(4, np.nan)]
    meme = b <= NB - 5
    y = (fut > c).astype(float)
    okb = ok[sess] & meme & np.isfinite(F).all(1) & np.isfinite(fut)
    return dict(J=J, ok=ok, sess=sess, b=b, an=an, o=o, h=h, l=l, c=c, v=v, I=I, F=F, fut=fut, y=y, okb=okb, meme=meme, S=S)
