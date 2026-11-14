"""Supertrend NQ 10-3 (5 min) : rejeu propre et compte Bulenox Option 1 (plancher = plus haut LATENT - 2 500 $, minute par
minute, bloque a 50 100 $ ; objectif 53 000 $, le bot ferme a 53 050 $). Regles du trade identiques a
audit/machine6/supertrend.py (lui-meme identique trade par trade au moteur C# sur 9 628 trades)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

S = Path(__file__).parent
sys.path.insert(0, str(S / "op/audit/machine6"))
import sim  # noqa: E402  (simulateur Option 1 numba de la machine v6)

N, FR = 390, 3.0
# 1. minutes NQ : 15 ans (kb) jusqu'au 23 sept. 2025, puis le fichier de main (a jour au 13 nov. 2026)
a = pd.read_csv(S / "kb/intraday/donnees/nasdaq100_1min.csv.gz", usecols=["t", "o", "h", "l", "c"])
b = pd.read_csv("/home/user/scalping-telegram-bot/zone/robot/nq_1min.csv.gz", usecols=["t", "o", "h", "l", "c"])
x = a.merge(b, on="t", suffixes=("_a", "_b"))
print(f"recouvrement kb/main : {len(x)} minutes, ecart max des clotures {np.abs(x.c_a - x.c_b).max():.2f} pts")
d = pd.concat([a[a.t < "2025-09-24"], b], ignore_index=True)
# faux prix : barre loin de la cloture d'avant ET de sa propre cloture (> 300 pts et > 1 %)
pc = d.c.shift(1)
for col in ("o", "h", "l"):
    ecart = np.minimum((d[col] - pc).abs(), (d[col] - d.c).abs())
    faux = (ecart > 300) & (ecart > 0.01 * d.c) & (d.t.str[:10] == d.t.shift(1).str[:10])
    for i in d.index[faux]:
        print(f"faux prix corrige : {d.t[i]} {col}={d.at[i, col]} (cloture d'avant {pc[i]}, cloture {d.c[i]})")
        d.at[i, col] = pc[i] if col == "o" else np.nan
d["o"] = d.o.fillna(pc)
d["h"] = d.h.fillna(d[["o", "c"]].max(axis=1)); d["l"] = d.l.fillna(d[["o", "c"]].min(axis=1))
d["h"] = d[["h", "o", "c"]].max(axis=1); d["l"] = d[["l", "o", "c"]].min(axis=1)
b2 = d[d.t >= "2025-09-24"].merge(pd.read_csv("/home/user/scalping-telegram-bot/zone/robot/nq_1min.csv.gz")[["t", "v", "contrat"]], on="t")
b2[["t", "o", "h", "l", "c", "v", "contrat"]].to_csv(S / "nq_propre.csv.gz", index=False)

# 2. tableaux par seance (comme sim.charger)
jour = d.t.str[:10]; m = d.t.str[11:13].astype(int) * 60 + d.t.str[14:16].astype(int) - 570
g = (m >= 0) & (m < N); d, jour, m = d[g], jour[g], m[g]
J = np.array(sorted(jour.unique())); idx = pd.Index(J).get_indexer(jour); nj = len(J)
A = {}
for col in "ohlc":
    A[col] = np.full((nj, N), np.nan); A[col][idx, m.to_numpy()] = d[col].to_numpy(float)
pres = ~np.isnan(A["c"])
C = pd.DataFrame(A["c"]).ffill(axis=1).bfill(axis=1).to_numpy()
O, H, L = [np.where(np.isnan(A[k]), C, A[k]) for k in "ohl"]
complete = pres[:, 0] & pres[:, N - 1] & (pres.sum(1) >= 370)

# 3. Supertrend 10-3 sur bougies de 5 min mises bout a bout (copie de supertrend.py)
h5 = H.reshape(nj, 78, 5).max(2).ravel(); l5 = L.reshape(nj, 78, 5).min(2).ravel(); c5 = C[:, 4::5].ravel()
st = np.zeros(len(c5)); atr, hb, lb, dr = 0.0, np.nan, np.nan, 1.0
for i in range(1, len(c5)):
    tr = max(h5[i] - l5[i], abs(h5[i] - c5[i - 1]), abs(l5[i] - c5[i - 1]))
    atr = tr if i == 1 else (atr * 9 + tr) / 10
    mid = (h5[i] + l5[i]) / 2; hb2, lb2 = mid + 3 * atr, mid - 3 * atr
    if i > 1:
        hb2 = hb2 if (hb2 < hb or c5[i - 1] > hb) else hb
        lb2 = lb2 if (lb2 > lb or c5[i - 1] < lb) else lb
        if dr > 0 and c5[i] < lb2:
            dr = -1.0
        elif dr < 0 and c5[i] > hb2:
            dr = 1.0
    hb, lb = hb2, lb2
    st[i] = dr if i >= 10 else 0.0
T = []
for s in range(nj):
    if not complete[s]:
        continue
    pos, m_in = 0, -1
    for bb in range(76):
        cible = pos if st[s * 78 + bb] == 0 else int(st[s * 78 + bb]); mm = 5 * bb + 5
        if cible != pos and pos != 0:
            T.append((s, pos, m_in - 1, mm - 1, O[s, m_in], O[s, mm])); pos = 0
        if cible != 0 and pos == 0 and mm <= 360:
            pos, m_in = cible, mm
    if pos != 0:
        T.append((s, pos, m_in - 1, 384, O[s, m_in], C[s, 384]))
T = np.array(T, float); td = T[:, 0].astype(np.int64)
jd = np.searchsorted(td, np.arange(nj), "left").astype(np.int64); jf = np.searchsorted(td, np.arange(nj), "right").astype(np.int64)
ARGS = (O, H, L, C, jd, jf, T[:, 1].astype(np.int64), T[:, 2].astype(np.int64), T[:, 3].astype(np.int64), T[:, 4], T[:, 5],
        np.ones(len(T)), T[:, 4])
print(f"Supertrend : {len(T)} trades sur {complete.sum()} seances completes ({J[0]} -> {J[-1]})")


def prm(t, lim):
    return np.array([t, lim, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0, 28500.0, 0], float)


def fenetre(d0, n, t, lim, solde, haut, reel=True, trace=None):
    """Portage Python de sim.fenetre (Option 1, cote defavorable d'abord). reel=True : vrais dollars (k = 1)."""
    for q in range(n):
        dd = d0 + q
        if dd >= nj:
            return 9, solde, q, haut
        plancher = min(haut - 2500, 50100); jv = 0.0; arret = False
        for i in range(jd[dd], jf[dd]):
            if arret:
                break
            s, me, mx, e, sortie = int(T[i, 1]), int(T[i, 2]), int(T[i, 3]), T[i, 4], T[i, 5]
            k = 1.0 if reel else 28500.0 / e; sorti = False; pire_lat = 0.0; quoi = "retournement" if mx < 384 else "15 h 55"
            for mm in range(me + 1, mx + 1):
                o, hh, ll, cc = O[dd, mm], H[dd, mm], L[dd, mm], C[dd, mm]
                fav, adv = (hh, ll) if s > 0 else (ll, hh)
                lat = t * (2 * s * (adv - e) * k - FR); pire_lat = min(pire_lat, lat)
                if solde + jv + lat <= plancher:
                    if trace is not None:
                        trace.append((J[dd], s, me + 1, mm, e, adv, jv + lat, pire_lat, "PLANCHER TOUCHE", solde + jv + lat, plancher))
                    return -1, solde + jv + lat, q, haut
                if jv + lat <= -lim:
                    niv = e + s * ((-lim - jv) / t + FR) / (2 * k)
                    sortie = (min(o, niv) - 1.0) if s > 0 else (max(o, niv) + 1.0); sorti = arret = True; quoi = "limite du jour"
                    break
                vf = solde + jv + t * (2 * s * (fav - e) * k - FR)
                if vf > haut:
                    haut = vf; plancher = min(haut - 2500, 50100)
                if solde + jv + t * (2 * s * (cc - e) * k - FR) >= 53050:
                    if trace is not None:
                        trace.append((J[dd], s, me + 1, mm, e, cc, jv + t * (2 * s * (cc - e) * k - FR), pire_lat, "OBJECTIF", solde + jv + t * (2 * s * (cc - e) * k - FR), plancher))
                    return 1, solde + jv + t * (2 * s * (cc - e) * k - FR), q, haut
            r = t * (2 * s * (sortie - e) * k - FR); jv += r
            if trace is not None:
                trace.append((J[dd], s, me + 1, mx + 1 if quoi != "limite du jour" else mm, e, sortie, r, pire_lat, quoi, solde + jv, plancher))
            if solde + jv >= 53050:
                return 1, solde + jv, q, haut
        solde += jv
    return 0, solde, n, haut


# 4. controle : le portage Python redonne le simulateur numba sur 400 fenetres prises au hasard
rng = np.random.default_rng(1); ok = 0; deb = rng.choice(np.arange(200, nj - 30), 400, replace=False)
for z in deb:
    r1 = sim.fenetre(int(z), 22, prm(2, 800), 50000.0, 50000.0, *ARGS, np.ones(len(T), np.bool_), 53000.0, 2500.0, 50100.0, 0)
    r2 = fenetre(int(z), 22, 2, 800, 50000.0, 50000.0, reel=False)
    ok += (r1[0] == r2[0]) and abs(r1[1] - r2[1]) < 0.01
print(f"controle portage Python = simulateur numba : {ok}/400 fenetres identiques")
np.savez(S / "st_cache.npz", O=O, H=H, L=L, C=C, J=J, T=T, complete=complete)
