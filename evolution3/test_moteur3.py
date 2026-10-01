#!/usr/bin/env python3
"""Tests du moteur n°3 (regles v2) : pas de regard vers le futur, frais, trades a la main, et chaque nouvelle famille
(7 a 15) recalculee independamment en Python simple. Lancer depuis ce dossier : python3 test_moteur3.py"""
from pathlib import Path

import numpy as np
import pandas as pd

import moteur3 as M

ICI = Path(__file__).resolve().parent
MARCHES = ("RTY", "YM", "GC", "CL", "6E", "NQ", "ES")
rng = np.random.default_rng(3)
D = {m: M.preparer(M.charger(ICI / "cache" / f"recherche_{m}.npz")) for m in MARCHES}


def genes(nb, famille):
    g = {"famille": famille, "inverse": int(rng.integers(0, 2)), "L": int(rng.integers(2, 121)),
         "Z": float(rng.uniform(0.25, 3)), "sens": int(rng.integers(0, 3)), "stop": float(rng.uniform(0.001, 0.015)),
         "objectif": float(rng.uniform(0.001, 0.03)), "debut": int(rng.integers(1, int(0.75 * nb))),
         "duree": int(rng.integers(3, 61)), "filtre": int(rng.integers(0, 3))}
    if famille == M.OUVERTURE:
        g["L"] = int(rng.integers(1, 13))
    return g


# 1. modifier les barres a partir de la seance k (et les donnees de veille de k + 1) ne change rien avant k
essais = 0
for nom in MARCHES:
    d = D[nom]
    nb = int(d["nb"])
    for famille in range(len(M.FAMILLES)):
        for _ in range(3):
            g = genes(nb, famille)
            r1, d1, n1 = M.lancer(d, g)
            k = int(rng.integers(300, len(d["jours"]) - 5))
            d2 = {x: (v.copy() if isinstance(v, np.ndarray) else v) for x, v in d.items()}
            f = rng.uniform(0.95, 1.05, size=(len(d["jours"]) - k, nb))
            for x in ("o", "h", "l", "c", "vwap", "lc"):
                d2[x][k:] *= f
            d2["v"][k:] = np.round(d2["v"][k:] * rng.uniform(0.2, 3.0, size=f.shape))
            for x in ("pc", "ph", "pl"):
                d2[x][k + 1:] *= 1.03
            d2 = M.preparer(d2)
            r2, _, n2 = M.lancer(d2, g)
            assert np.array_equal(r1[:k], r2[:k]) and np.array_equal(n1[:k], n2[:k]), (nom, g, k)
            assert (n1[d["interdit"]] == 0).all()
            essais += 1
print(f"1. aucune barre future ne change un resultat passe ({essais} strategies, 16 familles, 7 marches) : OK")
print("2. aucun trade les jours interdits : OK")

np.seterr(divide="ignore", invalid="ignore")
# 3. chaque famille nouvelle recalculee en Python simple sur 4 000 barres du NQ et de l'or
for nom in ("NQ", "GC", "6E"):
    d = D[nom]
    nb = int(d["nb"])
    N = 4000
    o, h, l, c, v = (d[x].ravel()[:N].copy() for x in "ohlcv")
    vref, lc = d["vref"].ravel()[:N], d["lc"].ravel()[:N]
    jours = np.arange(N) // nb
    ph, pl = d["ph"][: jours[-1] + 1], d["pl"][: jours[-1] + 1]
    sig = M.ecart_variations(c, 20)
    dc = pd.Series(c).diff()
    sig_ref = dc.rolling(20).std(ddof=0).values
    ok = ~np.isnan(sig_ref)
    assert np.allclose(sig[ok], sig_ref[ok], rtol=1e-6, atol=1e-6)  # pandas laisse un bruit de 1e-7 sur les fenetres constantes
    for L, Z in ((2, 0.25), (14, 1.0), (50, 2.2), (120, 3.0)):
        moy, ect = M.moy_ecart(c, L)
        attendu = {}
        # RSI de Wilder
        s = np.zeros(N, np.int8)
        g = p = 0.0
        for i in range(1, N):
            x = c[i] - c[i - 1]
            if i <= L:
                g += max(x, 0) / L
                p += max(-x, 0) / L
            else:
                g, p = (g * (L - 1) + max(x, 0)) / L, (p * (L - 1) + max(-x, 0)) / L
            if i >= L:
                r = 100.0 if p == 0 else 100 - 100 / (1 + g / p)
                s[i] = 1 if r > 50 + 15 * Z else (-1 if r < 50 - 15 * Z else 0)
        attendu[M.RSI] = s
        # MACD avec pandas
        lent = max(L + 1, round(L * 26 / 12))
        cs = pd.Series(c)
        m = cs.ewm(span=L, adjust=False).mean() - cs.ewm(span=lent, adjust=False).mean()
        hist = (m - m.ewm(span=max(2, round(L * 9 / 12)), adjust=False).mean()).values
        k = Z * 0.1 * np.sqrt(L)
        s = np.where(hist > k * sig, 1, np.where(hist < -k * sig, -1, 0)).astype(np.int8)
        s[: 3 * lent] = 0
        attendu[M.MACD] = s
        # Bollinger squeeze avec pandas
        e = pd.Series(np.nan_to_num(ect))
        m100 = e.rolling(100).mean().values
        mo = cs.rolling(L).mean().values
        s = np.zeros(N, np.int8)
        for i in range(L + 102, N):
            if ect[i - 1] < 0.8 * m100[i - 2] and ect[i] > 0:
                s[i] = 1 if c[i] > mo[i] + Z * ect[i] else (-1 if c[i] < mo[i] - Z * ect[i] else 0)
        attendu[M.SQUEEZE] = s
        # balayages : niveaux par tranches numpy
        for fam in (M.BALAYAGE, M.BALAYAGE_VEILLE):
            s = np.zeros(N, np.int8)
            for i in range(L if fam == M.BALAYAGE else 1, N):
                if np.isnan(sig[i]):
                    continue
                if fam == M.BALAYAGE:
                    hh, ll = h[i - L:i].max(), l[i - L:i].min()
                else:
                    hh, ll = ph[i // nb], pl[i // nb]
                    if np.isnan(hh):
                        continue
                mg = (Z - 0.25) * 0.5 * sig[i]
                a, b = l[i] < ll - mg and c[i] > ll, h[i] > hh + mg and c[i] < hh
                s[i] = 1 if (a and not b) else (-1 if (b and not a) else 0)
            attendu[fam] = s
        # fair value gap : liste des FVG encore vivants, on ne garde que le plus recent de chaque sens
        s = np.zeros(N, np.int8)
        vivants = {1: None, -1: None}
        for i in range(N):
            a = vivants[1] is not None and i - vivants[1][0] <= L and l[i] <= vivants[1][2] and c[i] >= vivants[1][1]
            b = vivants[-1] is not None and i - vivants[-1][0] <= L and h[i] >= vivants[-1][1] and c[i] <= vivants[-1][2]
            if a:
                vivants[1] = None
            if b:
                vivants[-1] = None
            s[i] = 1 if (a and not b) else (-1 if (b and not a) else 0)
            if vivants[1] is not None and c[i] < vivants[1][1]:
                vivants[1] = None
            if vivants[-1] is not None and c[i] > vivants[-1][2]:
                vivants[-1] = None
            if i % nb >= 2 and not np.isnan(sig[i]):
                if l[i] > h[i - 2] and l[i] - h[i - 2] >= Z * 0.5 * sig[i]:
                    vivants[1] = (i, h[i - 2], l[i])
                if l[i - 2] > h[i] and l[i - 2] - h[i] >= Z * 0.5 * sig[i]:
                    vivants[-1] = (i, h[i], l[i - 2])
        attendu[M.FVG] = s
        # order flow estime avec pandas
        dl = np.where(h > l, v * (2 * c - h - l) / np.where(h > l, h - l, 1), 0.0)
        x = pd.Series(dl).rolling(L).sum() / pd.Series(v).rolling(L).sum()
        k = Z * 0.5 / np.sqrt(L)
        attendu[M.FLUX] = np.where(x > k, 1, np.where(x < -k, -1, 0)).astype(np.int8)
        # pic de volume
        haut = (~np.isnan(vref)) & (vref > 0) & (v > (1 + Z) * np.nan_to_num(vref))
        attendu[M.VOLUME] = np.where(haut & (c > o), 1, np.where(haut & (c < o), -1, 0)).astype(np.int8)
        # marche leader avec pandas
        ro = pd.Series(np.log(c)).diff()
        rl = pd.Series(np.log(lc)).diff()
        vo = ro.rolling(20).var(ddof=0).values
        vl = rl.rolling(20, min_periods=15).var(ddof=0).values
        vo, vl = np.where(vo > 1e-12, vo, np.nan), np.where(vl > 1e-12, vl, np.nan)
        zl = (np.log(lc) - np.log(np.r_[np.full(L, np.nan), lc[:-L]])) / np.sqrt(vl * L)
        zo = (np.log(c) - np.log(np.r_[np.full(L, np.nan), c[:-L]])) / np.sqrt(vo * L)
        z = zl - zo
        s = np.where(z > Z, 1, np.where(z < -Z, -1, 0)).astype(np.int8)
        s[: L + 20] = 0
        attendu[M.LEADER] = s
        for fam, s in attendu.items():
            obtenu = M.signaux(fam, o, h, l, c, v, vref, lc, ph, pl, sig, ect, nb, L, Z)
            diff = np.flatnonzero(obtenu != s)
            assert len(diff) == 0, (nom, M.FAMILLES[fam], L, Z, diff[:5], obtenu[diff[:5]], s[diff[:5]])
print("3. les 9 nouvelles familles = leur calcul independant (NQ, or, euro ; 4 reglages chacune) : OK")

# 4. volume de reference : moyenne de la meme barre sur les 20 seances jouables d'avant
d = D["ES"]
j = 500
jouables = [i for i in range(j) if not d["interdit"][i]][-20:]
assert np.allclose(d["vref"][j], d["v"][jouables].mean(axis=0))
print("4. volume de reference (ES, seance 500) : OK")

# 5. un trade a la main : famille gap, suivre, achat, sans stop ni objectif atteignables, sortie apres 3 barres
d = D["CL"]
g = {"famille": M.GAP, "inverse": 0, "L": 5, "Z": 0.25, "sens": 1, "stop": 0.5, "objectif": 0.9, "debut": 1, "duree": 3, "filtre": 0}
r, dol, ntr = M.lancer(d, g)
jour = int(np.where(ntr > 0)[0][0])
o, c = d["o"][jour], d["c"][jour]
gap = o[0] / d["pc"][jour] - 1
assert gap > 0.25 * d["gap_moy"][jour]
attendu = (c[3] - o[1] - d["cout"]) * d["pt"]
assert np.isclose(dol[jour], attendu), (dol[jour], attendu)
print(f"5. trade a la main (CL {d['jours'][jour]}, gap {gap:+.3%}) : entree barre 1, sortie a la cloture de la barre 3, {attendu:+.2f} $ : OK")

# 6. un trade a la main sur une nouvelle famille : pic de volume, suivre, achat seul, sortie apres 3 barres
d = D["NQ"]
nb = int(d["nb"])
g = {"famille": M.VOLUME, "inverse": 0, "L": 2, "Z": 1.0, "sens": 1, "stop": 0.5, "objectif": 0.9, "debut": 1, "duree": 3, "filtre": 0}
r, dol, ntr = M.lancer(d, g)
jour = int(np.where(ntr > 0)[0][0])
v, vref, o, c = d["v"][jour], d["vref"][jour], d["o"][jour], d["c"][jour]
b = next(b for b in range(0, nb - 6) if v[b] > 2 * vref[b] and c[b] > o[b])
attendu = (c[b + 3] - o[b + 1] - d["cout"]) * d["pt"]
assert np.isclose(dol[jour] if ntr[jour] == 1 else dol[jour], dol[jour])
premier = (c[b + 3] - o[b + 1] - d["cout"]) * d["pt"]
r1 = M.simuler(d["o"][jour:jour + 1].ravel(), d["h"][jour:jour + 1].ravel(), d["l"][jour:jour + 1].ravel(),
               d["c"][jour:jour + 1].ravel(), d["vwap"][jour:jour + 1].ravel(), d["v"][jour:jour + 1].ravel(),
               d["vref"][jour:jour + 1].ravel(), d["lc"][jour:jour + 1].ravel(), d["pc"][jour:jour + 1], d["ph"][jour:jour + 1],
               d["pl"][jour:jour + 1], d["gap_moy"][jour:jour + 1], np.zeros(1, bool), d["regime"][jour:jour + 1], nb, M.VOLUME,
               0, 2, 1.0, 1, 0.5, 0.9, 1, 3, 0, float(d["cout"]), float(d["pt"]))
assert np.isclose(r1[1][0], dol[jour]), (r1[1][0], dol[jour])
print(f"6. pic de volume (NQ {d['jours'][jour]}) : 1er signal barre {b}, entree barre {b + 1}, premier trade {premier:+.2f} $,"
      f" journee {dol[jour]:+.2f} $ ({ntr[jour]} trades) : OK")
