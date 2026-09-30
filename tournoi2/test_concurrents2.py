#!/usr/bin/env python3
"""Tests du tournoi n°2 : pas de regard vers le futur (a la barre, entre seances, et dans la seance sur un marche
aleatoire), calculs compares a des versions Python simples (Supertrend de TradingView, Donchian, paire), achat
permanent exact.
Lancer depuis ce dossier : python3 test_concurrents2.py"""
import numpy as np
import pandas as pd

import concurrents2 as K
from explorer2 import charger
from test_concurrents import controle_martingale, marche_aleatoire   # tournoi/

N = K.N


def supertrend_pine(h, l, c, n, f):
    """Traduction ligne a ligne de ta.supertrend (Pine v5) ; renvoie +1 en tendance haussiere, -1 sinon."""
    m = len(c)
    tr = np.r_[h[0] - l[0], np.maximum.reduce([h[1:] - l[1:], abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])])]
    atr = np.full(m, np.nan)
    atr[n - 1] = tr[:n].mean()
    for i in range(n, m):
        atr[i] = (atr[i - 1] * (n - 1) + tr[i]) / n
    up_p, lo_p, st_p = 0.0, 0.0, np.nan
    out = np.zeros(m, int)
    for i in range(m):
        if np.isnan(atr[i]):
            continue
        src = (h[i] + l[i]) / 2
        up, lo = src + f * atr[i], src - f * atr[i]
        lo = lo if (lo > lo_p or c[i - 1] < lo_p) else lo_p
        up = up if (up < up_p or c[i - 1] > up_p) else up_p
        if i == 0 or np.isnan(atr[i - 1]):
            direction = 1
        elif st_p == up_p:
            direction = -1 if c[i] > up else 1
        else:
            direction = 1 if c[i] < lo else -1
        st_p = lo if direction == -1 else up
        up_p, lo_p = up, lo
        out[i] = -direction
    return out


def donchian_simple(o5, h5, l5, c5, ok, complete, d):
    ic = np.where(complete)[0]
    h, l, c = h5[ic].ravel(), l5[ic].ravel(), c5[ic].ravel()
    q = np.zeros(K.NB, int)
    if not ok[d]:
        return q
    j = int(np.searchsorted(ic, d))
    pos = 0
    for b in range(K.NB - 1):
        i = j * K.NB + b
        if i < 20:
            continue
        hh20, ll20, hh10, ll10 = h[i - 20:i].max(), l[i - 20:i].min(), h[i - 10:i].max(), l[i - 10:i].min()
        if pos > 0 and c[i] < ll10:
            pos = 0
        elif pos < 0 and c[i] > hh10:
            pos = 0
        if pos == 0 and 1 <= b + 1 <= 66:
            pos = 1 if c[i] > hh20 else (-1 if c[i] < ll20 else 0)
        q[b + 1] = pos
    return q


def paire_simple(a, b, d, seuil, ca, cb):
    Oa, Ca, Ob, Cb = a[1], a[4], b[1], b[4]
    pos, tot = 0, 0.0
    for m in range(30, N):
        x = np.log(Ca[d, m - 1] / Oa[d, 0]) - np.log(Cb[d, m - 1] / Ob[d, 0])
        if pos and np.sign(x) != pos:
            tot += 0.5 * (-pos * (Oa[d, m] / ea - 1) + pos * (Ob[d, m] / eb - 1))
            pos = 0
        if not pos and m in range(30, 331, 30) and abs(x) > seuil:
            pos, ea, eb = (1 if x > 0 else -1), Oa[d, m], Ob[d, m]
            tot -= 0.5 * (ca / ea + cb / eb)
    if pos:
        tot += 0.5 * (-pos * (Ca[d, N - 1] / ea - 1) + pos * (Cb[d, N - 1] / eb - 1))
    return tot


def main():
    J, O, H, L, C, P, X = charger("nasdaq100")
    cout = K.st.cout_aller_retour("nasdaq100")
    complete = K.st.journees_completes(P)
    ok = complete & ~X["echeance"]
    o5, h5, l5, c5 = K.barres5(O, H, L, C)
    rng = np.random.default_rng(5)
    # 1. barres de 5 minutes
    d = 1234
    assert np.isclose(h5[d, 3], H[d, 15:20].max()) and np.isclose(c5[d, 3], C[d, 19]) and np.isclose(o5[d, 3], O[d, 15])
    print("1. barres de 5 minutes : OK")
    # 2. achat permanent : cloture - ouverture de 9 h 35 - frais
    un = np.ones((len(J), K.NB), bool)
    q = K.positions(un, ~un, ~un, ~un, ok)
    pts = K.points(q, o5, C[:, N - 1], cout)
    assert np.allclose(pts[ok], C[ok, N - 1] - O[ok, 5] - cout) and np.all(pts[~ok] == 0)
    print("2. achat permanent exact, rien les jours exclus : OK")
    # 3. Supertrend = traduction de TradingView
    h, l, c = h5.ravel()[:20000], l5.ravel()[:20000], c5.ravel()[:20000]
    a, b = K.supertrend(h, l, c, 10, 3.0), supertrend_pine(h, l, c, 10, 3.0)
    assert np.array_equal(a[9:], b[9:]), np.where(a != b)[0][:10]
    print(f"3. Supertrend = traduction de ta.supertrend ({len(c)} barres, {int((np.diff(a[9:]) != 0).sum())} retournements) : OK")
    # 4. Donchian = version simple
    _, sig = K.signaux5(O, H, L, C, complete)
    qd = K.positions(*sig["Canal de Donchian 20 / 10"], ok)
    for d in rng.choice(np.where(ok)[0], 200, replace=False):
        assert np.array_equal(qd[d], donchian_simple(o5, h5, l5, c5, ok, complete, d)), d
    print("4. Donchian = version simple (200 seances) : OK")
    # 5. regard vers le futur a la barre : modifier les minutes >= 5k de la seance d (et la suite) ne change pas
    #    les positions tenues jusqu'a la barre k incluse (entree a l'ouverture de la barre k)
    for essai in range(6):
        d, k = int(rng.integers(100, len(J) - 5)), int(rng.integers(1, K.NB))
        O2, H2, L2, C2 = (x.copy() for x in (O, H, L, C))
        f = rng.uniform(0.98, 1.02, size=(len(J) - d, N))
        for x, y in ((O2, O), (H2, H), (L2, L), (C2, C)):
            x[d:] *= f
            x[d, :5 * k] = y[d, :5 * k]
        O2[d, 5 * k] = O[d, 5 * k]                       # le prix d'execution de la barre k est connu
        _, sig2 = K.signaux5(O2, H2, L2, C2, complete)
        for nom in sig:
            q1, q2 = K.positions(*sig[nom], ok), K.positions(*sig2[nom], ok)
            assert np.array_equal(q1[:d], q2[:d]) and np.array_equal(q1[d, :k + 1], q2[d, :k + 1]), f"regard vers le futur : {nom}"
    print("5. positions jusqu'a la barre k independantes de la suite (6 essais, 7 indicateurs) : OK")
    # 6. regard vers le futur a la seance, toutes les strategies
    res, _ = K.toutes(J, O, H, L, C, P, X, cout)
    for essai in range(6):
        d, k = int(rng.integers(100, len(J) - 5)), int(rng.integers(0, N))
        O2, H2, L2, C2 = (x.copy() for x in (O, H, L, C))
        V2 = X["V"].copy()
        f = rng.uniform(0.98, 1.02, size=(len(J) - d, N))
        for x, y in ((O2, O), (H2, H), (L2, L), (C2, C), (V2, X["V"])):
            x[d:] *= f
            x[d, :k] = y[d, :k]
        res2, _ = K.toutes(J, O2, H2, L2, C2, P, {**X, "V": V2}, cout)
        for nom in res:
            assert np.array_equal(res[nom][:d], res2[nom][:d]), f"regard vers le futur : {nom}"
    print(f"6. aucune seance passee modifiee par le futur (6 essais, {len(res)} strategies) : OK")
    # 7. paire = version simple, et pas de regard vers le futur
    a, b = K.aligner(charger("nasdaq100"), charger("sp500"))
    ca, cb = cout, K.st.cout_aller_retour("sp500")
    r, okp = K.paire(a, b, ca, cb)
    fin = np.log(a[4][:, N - 1] / a[1][:, 0]) - np.log(b[4][:, N - 1] / b[1][:, 0])
    comp = K.st.journees_completes(a[5]) & K.st.journees_completes(b[5])
    seuil = np.full(len(fin), np.nan)                     # ecart-type des 20 dernieres seances completes
    ic = np.where(comp)[0]
    for k, d in enumerate(ic):
        if k >= 20:
            seuil[d] = 1.5 * np.std(fin[ic[k - 20:k]], ddof=1)
    for d in rng.choice(np.where(okp & ~np.isnan(seuil))[0], 300, replace=False):
        assert abs(r[d] - paire_simple(a, b, d, seuil[d], ca, cb)) < 1e-12, d
    d = 2000
    a2 = (a[0], a[1].copy(), a[2], a[3], a[4].copy(), a[5], a[6])
    a2[1][d:] *= 1.01
    a2[4][d:] *= 1.013
    r2, _ = K.paire(a2, b, ca, cb)
    assert np.array_equal(r[:d], r2[:d])
    print(f"7. paire = version simple (300 seances, {int((r != 0).sum())} seances avec trade), pas de regard vers le futur : OK")
    # 8. dans la seance : marche aleatoire (14 strategies, puis la paire sur deux marches aleatoires lies)
    ts, t1, t2 = controle_martingale(K.toutes)
    rng = np.random.default_rng(12)
    a = marche_aleatoire(12000, rng)
    b = marche_aleatoire(12000, rng, correle=a[7])
    rp, okp = K.paire(a[:7], b[:7], 0.0, 0.0)
    tp = float(rp[okp].mean() / rp[okp].std() * np.sqrt(okp.sum()))
    assert tp < 4.0, tp
    print(f"8. marche aleatoire (12 000 seances) : tricheurs detectes (t {t1:+.1f} et {t2:+.1f}), aucune strategie au-dessus"
          f" de 4 (max {max(ts.values()):+.2f}, paire {tp:+.2f}, {int((rp != 0).sum())} seances de trade) : OK")


if __name__ == "__main__":
    main()
