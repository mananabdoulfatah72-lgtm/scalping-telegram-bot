"""Les 14 strategies du tournoi (regles dans README.md), sur les tableaux minute (seances x 390 minutes) de
intraday/strategies.py charger. Chaque fonction renvoie les points nets de frais par seance (0 sans trade)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "intraday"))
sys.path.insert(0, str(R / "fonds"))
import strategies as st  # noqa: E402

N = 390
NAN = np.nan


@njit(cache=True)
def cassure(O, H, L, C, ok, cout, haut, bas, stop_achat, stop_vente, debut):
    """Un trade par jour au premier niveau touche (haut : achat, bas : vente), entree au niveau ou a l'ouverture de la
    minute s'il est saute ; stop (compte aussi dans la minute d'entree) ; sortie a 16 h."""
    nd = O.shape[0]
    out = np.zeros(nd)
    for d in range(nd):
        if not ok[d] or np.isnan(haut[d]) or np.isnan(bas[d]):
            continue
        pos = 0
        e = 0.0
        stop = 0.0
        fini = False
        for m in range(debut, N):
            if pos == 0:
                up = H[d, m] > haut[d]
                dn = L[d, m] < bas[d]
                if up and dn:
                    fini = True                  # les deux niveaux dans la meme minute : journee sautee
                    break
                if up:
                    pos, e, stop = 1, max(haut[d], O[d, m]), stop_achat[d]
                    if L[d, m] <= stop:
                        out[d] = (stop - e) - cout
                        fini = True
                        break
                elif dn:
                    pos, e, stop = -1, min(bas[d], O[d, m]), stop_vente[d]
                    if H[d, m] >= stop:
                        out[d] = (e - stop) - cout
                        fini = True
                        break
            else:
                if pos > 0 and L[d, m] <= stop:
                    out[d] = (min(stop, O[d, m]) - e) - cout
                    fini = True
                    break
                if pos < 0 and H[d, m] >= stop:
                    out[d] = (e - max(stop, O[d, m])) - cout
                    fini = True
                    break
        if not fini and pos != 0:
            out[d] = pos * (C[d, N - 1] - e) - cout
    return out


@njit(cache=True)
def entree_fixe(O, H, L, C, ok, cout, sens, m_entree, stop, objectif, m_sortie):
    """Entree a l'ouverture de la minute m_entree dans le sens donne (0 : pas de trade), stop et objectif en prix
    (NaN : aucun), sortie a la cloture de la minute m_sortie. Le stop est verifie avant l'objectif."""
    nd = O.shape[0]
    out = np.zeros(nd)
    for d in range(nd):
        s = sens[d]
        if not ok[d] or s == 0:
            continue
        e = O[d, m_entree]
        sortie = NAN
        for m in range(m_entree, m_sortie + 1):
            if not np.isnan(stop[d]):
                if s > 0 and L[d, m] <= stop[d]:
                    sortie = stop[d] if m == m_entree else min(stop[d], O[d, m])
                    break
                if s < 0 and H[d, m] >= stop[d]:
                    sortie = stop[d] if m == m_entree else max(stop[d], O[d, m])
                    break
            if not np.isnan(objectif[d]):
                if s > 0 and H[d, m] >= objectif[d]:
                    sortie = objectif[d] if m == m_entree else max(objectif[d], O[d, m])
                    break
                if s < 0 and L[d, m] <= objectif[d]:
                    sortie = objectif[d] if m == m_entree else min(objectif[d], O[d, m])
                    break
        if np.isnan(sortie):
            sortie = C[d, m_sortie]
        out[d] = s * (sortie - e) - cout
    return out


@njit(cache=True)
def tendance_vwap(C, VW, ok, cout):
    """Toutes les 30 min de 10 h a 15 h 30 : du cote du prix par rapport au VWAP ; retournement si le prix change de cote."""
    nd = C.shape[0]
    out = np.zeros(nd)
    for d in range(nd):
        if not ok[d]:
            continue
        pos = 0
        e = 0.0
        tot = 0.0
        for m in range(30, 361, 30):
            p = C[d, m]
            s = 1 if p > VW[d, m] else (-1 if p < VW[d, m] else 0)
            if pos != 0 and s != pos:
                tot += pos * (p - e)
                pos = 0
            if pos == 0 and s != 0:
                pos, e = s, p
                tot -= cout
        if pos != 0:
            tot += pos * (C[d, N - 1] - e)
        out[d] = tot
    return out


def vwap(H, L, C, V):
    typ = (H + L + C) / 3
    cv = np.cumsum(V, axis=1)
    return np.where(cv > 0, np.cumsum(typ * V, axis=1) / np.where(cv > 0, cv, 1), np.cumsum(typ, axis=1) / np.arange(1, N + 1))


def toutes(J, O, H, L, C, P, X, cout):
    """Points nets par seance pour chaque strategie ; ok = seance complete et pas de changement d'echeance."""
    ok = st.journees_completes(P) & ~X["echeance"]
    nd = len(J)
    o0, c_fin = O[:, 0], C[:, N - 1]
    pc = np.r_[NAN, c_fin[:-1]]                                  # cloture de la veille
    hj, lj = H.max(axis=1), L.min(axis=1)
    h_veille, l_veille = np.r_[NAN, hj[:-1]], np.r_[NAN, lj[:-1]]
    rien = np.full(nd, NAN)
    res = {}
    for n in (15, 30, 60):
        hh, ll = H[:, :n].max(axis=1), L[:, :n].min(axis=1)
        res[f"Range d'ouverture {n} min"] = cassure(O, H, L, C, ok, cout, hh, ll, ll, hh, n)
    amp = h_veille - l_veille
    res["Cassure de Williams"] = cassure(O, H, L, C, ok, cout, o0 + 0.5 * amp, o0 - 0.5 * amp, o0, o0, 0)
    etir = pd.Series(np.minimum(hj - o0, o0 - lj)).rolling(10, min_periods=10).mean().shift(1).values
    res["Etirement de Crabel"] = cassure(O, H, L, C, ok, cout, o0 + etir, o0 - etir, o0 - etir, o0 + etir, 0)
    mil = (h_veille + l_veille) / 2
    res["Cassure de la veille"] = cassure(O, H, L, C, ok, cout, h_veille, l_veille, mil, mil, 0)
    s1h = np.sign(C[:, 59] - o0).astype(np.int64)
    res["Momentum de la 1re heure"] = entree_fixe(O, H, L, C, ok, cout, s1h, 60, rien, rien, N - 1)
    res["Tendance VWAP"] = tendance_vwap(C, vwap(H, L, C, X["V"]), ok, cout)
    gap = o0 / pc - 1
    s_cont = np.where(np.abs(gap) >= 0.0025, np.sign(gap), 0).astype(np.int64)
    res["Continuation du gap"] = entree_fixe(O, H, L, C, ok, cout, s_cont, 1, pc, rien, N - 1)
    s_fade = np.where((np.abs(gap) >= 0.0015) & (np.abs(gap) <= 0.01), -np.sign(gap), 0).astype(np.int64)
    e1 = O[:, 1]
    stop_fade = e1 * (1 + np.sign(gap) * np.abs(gap))
    res["Comblement du gap"] = entree_fixe(O, H, L, C, ok, cout, s_fade, 1, stop_fade, pc, N - 1)
    r30 = C[:, 29] / o0 - 1
    moy30 = pd.Series(np.abs(r30)).rolling(20, min_periods=20).mean().shift(1).values
    s_ext = np.where(np.abs(r30) > 1.5 * moy30, -np.sign(r30), 0).astype(np.int64)
    stop_ext = np.where(r30 > 0, H[:, :30].max(axis=1), L[:, :30].min(axis=1))
    res["Retournement apres 30 min extremes"] = entree_fixe(O, H, L, C, ok, cout, s_ext, 30, stop_ext, rien, N - 1)
    mois = pd.DatetimeIndex(J).to_period("M")
    rang = pd.Series(np.arange(nd)).groupby(mois).cumcount().values           # 0 = 1re seance du mois
    dernier = np.r_[mois[1:] != mois[:-1], True]
    s_tom = np.where(dernier | (rang <= 2), 1, 0).astype(np.int64)
    res["Tournant du mois"] = entree_fixe(O, H, L, C, ok, cout, s_tom, 0, rien, rien, N - 1)
    import fomc
    s_fed = pd.DatetimeIndex(J).isin(fomc.annonces()).astype(np.int64)
    res["Veille de la Fed (jour meme)"] = entree_fixe(O, H, L, C, ok, cout, s_fed, 0, rien, rien, 264)
    res["Achat simple intraday"] = entree_fixe(O, H, L, C, ok, cout, np.ones(nd, np.int64), 0, rien, rien, N - 1)
    z = st.zone_de_bruit(J, O, H, L, C, P, X)
    zp = (z["brut"] - cout * z["allers"]).reindex(pd.DatetimeIndex(J)).fillna(0).values
    res["Zone de bruit (reference)"] = np.where(ok, zp, 0.0)
    return res, ok


def melanger(O, H, L, C, V, rng):
    """Bruit : les minutes de chaque seance sont remises au hasard (la 1re reste en place) ; forme des minutes,
    volatilite et resultat de la seance conserves."""
    nd, n = O.shape
    ro = np.ones_like(O)
    ro[:, 1:] = O[:, 1:] / C[:, :-1]
    rh, rl, rc = H / O, L / O, C / O
    perm = np.concatenate([np.zeros((nd, 1), int), 1 + np.argsort(rng.random((nd, n - 1)), axis=1)], axis=1)
    ro, rh, rl, rc, V2 = (np.take_along_axis(x, perm, axis=1) for x in (ro, rh, rl, rc, V))
    O2, H2, L2, C2 = (np.empty_like(O) for _ in range(4))
    prix = O[:, 0].copy()
    for m in range(n):
        om = prix * (ro[:, m] if m > 0 else 1.0)
        O2[:, m], H2[:, m], L2[:, m], C2[:, m] = om, om * rh[:, m], om * rl[:, m], om * rc[:, m]
        prix = C2[:, m]
    return O2, H2, L2, C2, V2
