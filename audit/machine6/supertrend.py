#!/usr/bin/env python3
"""Le Supertrend 10-3 (5 min) de la partie H (scalping/partie_h.py, regle H12), rejoue minute par minute dans le
simulateur du challenge (sim.py) : memes regles d'execution que la partie H (signal a la cloture de la barre de 5 min,
execution a l'ouverture suivante, entrees jusqu'a 15 h 30, a plat a 15 h 55, indicateur continu d'une seance a l'autre)."""
import numpy as np
import base as B
import sim

D = B.D
O, H, L, C = D["O"], D["H"], D["L"], D["C"]
S = O.shape[0]
# barres de 5 minutes de toutes les seances, mises bout a bout
h5 = H.reshape(S, 78, 5).max(2).ravel()
l5 = L.reshape(S, 78, 5).min(2).ravel()
c5 = C[:, 4::5].ravel()
n = len(c5)
st = np.zeros(n)
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
    st[i] = d if i >= 10 else 0.0
# seances jouees : completes, hors changement de contrat (comme la partie H)
cont = np.array([str(x) for x in np.load(B.SCR + "/machine6_cache.npz", allow_pickle=True)["jours"]])
T = []
ok = D["complete"].copy()
for s in range(S):
    if not ok[s]:
        continue
    pos, m_in = 0, -1
    for b in range(76):
        cible = pos if st[s * 78 + b] == 0 else int(st[s * 78 + b])
        m = 5 * b + 5
        if cible != pos and pos != 0:
            T.append((s, pos, m_in - 1, m - 1, O[s, m_in], O[s, m]))
            pos = 0
        if cible != 0 and pos == 0 and m <= 360:
            pos, m_in = cible, m
    if pos != 0:
        T.append((s, pos, m_in - 1, 384, O[s, m_in], C[s, 384]))
T = np.array(T, float)
td = T[:, 0].astype(np.int64)
ARGS = (O, H, L, C, np.searchsorted(td, np.arange(S), "left").astype(np.int64), np.searchsorted(td, np.arange(S), "right").astype(np.int64),
        T[:, 1].astype(np.int64), T[:, 2].astype(np.int64), T[:, 3].astype(np.int64), T[:, 4], T[:, 5], np.ones(len(T)), T[:, 4])
pris = np.ones(len(T), np.bool_)

def issues(p, deb, nseances=8, solde0=50000.0, haut0=51500.0):
    r, marge = sim.lot(deb, nseances, p, solde0, haut0, *ARGS, pris, 53000.0, 2500.0, 50100.0)
    r = r[r != 9]
    return (r == 1).mean() * 100, (r == -1).mean() * 100

if __name__ == "__main__":
    j = sim.journees(B.prm(T=1, L=1e9, pref=30900.0), *ARGS, pris, S)
    jt = np.zeros(S, bool); jt[np.unique(td)] = True
    g = j[jt]
    an = B.annee[jt]
    t = lambda x: x.mean() / x.std(ddof=1) * np.sqrt(len(x))
    print(f"verification (partie H : t 2,92, +28,6 $ par seance, 2,4 allers-retours) : {len(T)} trades, {jt.sum()} seances,"
          f" {len(T) / jt.sum():.1f} trades par seance, +{g.mean():.1f} $ par seance, t {t(g):.2f}, <=2022 t {t(g[an <= 2022]):.2f}, >=2023 t {t(g[an >= 2023]):.2f}")
    print("\nChallenge depuis 50 000 $, plancher 49 000 $ (temps reel), 8 seances : reussis / echoues (%)")
    per = {"2011-19": B.debuts(2011, 2019), "2020-23": B.debuts(2020, 2023), "2024-26": B.debuts(2024, 2026)}
    for nom, kw in [("Supertrend 1 MNQ, limite 1000", dict(T=1, L=1000)), ("Supertrend 2 MNQ, limite 1000", dict(T=2, L=1000)),
                    ("Supertrend 3 MNQ, limite 1000", dict(T=3, L=1000)), ("Supertrend 4 MNQ, limite 1000", dict(T=4, L=1000)),
                    ("Supertrend 6 MNQ, limite 1000", dict(T=6, L=1000)), ("Supertrend 4 MNQ, limite 700", dict(T=4, L=700)),
                    ("Supertrend 6 MNQ, limite 700", dict(T=6, L=700))]:
        print(f"  {nom:32s}" + "   ".join(f"{k} {r:4.1f} / {e:4.1f}" for k, d in per.items() for r, e in [issues(B.prm(**kw), d)]))
    print("  (zone, meme simulateur : 4 MNQ / 1000 -> 2011-19 14.4 / 35.9, 2020-23 17.9 / 51.3, 2024-26 15.6 / 48.5 ;"
          " 6 MNQ / 1000 -> 20.7 / 52.8, 20.6 / 63.8, 20.3 / 63.5)")
