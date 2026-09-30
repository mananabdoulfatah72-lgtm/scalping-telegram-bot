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
    (NaN : aucun), sortie a la cloture de la minute m_sortie. Si l'ouverture d'une minute est deja au-dela d'un
    niveau, sortie a l'ouverture ; sinon le stop est verifie avant l'objectif."""
    nd = O.shape[0]
    out = np.zeros(nd)
    for d in range(nd):
        s = sens[d]
        if not ok[d] or s == 0:
            continue
        e = O[d, m_entree]
        sortie = NAN
        a_stop, a_obj = not np.isnan(stop[d]), not np.isnan(objectif[d])
        for m in range(m_entree, m_sortie + 1):
            o = O[d, m]
            # le cours ouvre deja au-dela du stop ou de l'objectif (minute d'entree comprise) : sortie a ce prix
            if a_stop and ((s > 0 and o <= stop[d]) or (s < 0 and o >= stop[d])):
                sortie = o
                break
            if a_obj and ((s > 0 and o >= objectif[d]) or (s < 0 and o <= objectif[d])):
                sortie = o
                break
            if a_stop and ((s > 0 and L[d, m] <= stop[d]) or (s < 0 and H[d, m] >= stop[d])):   # stop avant objectif
                sortie = stop[d]
                break
            if a_obj and ((s > 0 and H[d, m] >= objectif[d]) or (s < 0 and L[d, m] <= objectif[d])):
                sortie = objectif[d]
                break
        if np.isnan(sortie):
            sortie = C[d, m_sortie]
        out[d] = s * (sortie - e) - cout
    return out


@njit(cache=True)
def tendance_vwap(O, C, VW, ok, cout):
    """Toutes les 30 min de 10 h a 15 h 30 : du cote du prix par rapport au VWAP (cloture de la minute m, comme la zone
    de bruit), execution a l'ouverture de la minute suivante ; retournement si le prix change de cote."""
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
            px = O[d, m + 1]
            if pos != 0 and s != pos:
                tot += pos * (px - e)
                pos = 0
            if pos == 0 and s != 0:
                pos, e = s, px
                tot -= cout
        if pos != 0:
            tot += pos * (C[d, N - 1] - e)
        out[d] = tot
    return out


def vwap(H, L, C, V):
    typ = (H + L + C) / 3
    cv = np.cumsum(V, axis=1)
    return np.where(cv > 0, np.cumsum(typ * V, axis=1) / np.where(cv > 0, cv, 1), np.cumsum(typ, axis=1) / np.arange(1, N + 1))


def precedente(complete, contrat=None):
    """Indice de la derniere seance complete avant chaque seance (-1 : aucune, ou autre contrat). Les lignes des jours
    feries de la CME (arret a 13 h) et des fermetures anticipees ne servent jamais de veille."""
    idx = np.where(complete, np.arange(len(complete)), -1)
    prec = np.r_[-1, np.maximum.accumulate(idx)[:-1]]
    if contrat is not None:
        prec = np.where((prec >= 0) & (contrat[np.maximum(prec, 0)] == contrat), prec, -1)
    return prec


def de_la(x, prec):
    """x pris a la seance prec (NaN si prec = -1)."""
    return np.where(prec >= 0, x[np.maximum(prec, 0)], NAN)


def glissant_complet(x, complete, n, f="mean"):
    """Statistique des n dernieres seances completes avant chaque seance (NaN pour les seances incompletes)."""
    out = np.full(len(x), NAN)
    out[complete] = pd.Series(x[complete]).rolling(n, min_periods=n).agg(f).shift(1).values
    return out


def toutes(J, O, H, L, C, P, X, cout):
    """Points nets par seance pour chaque strategie ; ok = seance complete et pas de changement d'echeance."""
    complete = st.journees_completes(P)
    ok = complete & ~X["echeance"]
    nd = len(J)
    prec = precedente(complete, X.get("contrat"))
    o0, c_fin = O[:, 0], C[:, N - 1]
    pc = de_la(c_fin, prec)                                      # cloture de la veille (derniere seance complete)
    hj, lj = H.max(axis=1), L.min(axis=1)
    h_veille, l_veille = de_la(hj, prec), de_la(lj, prec)
    rien = np.full(nd, NAN)
    res = {}
    for n in (15, 30, 60):
        hh, ll = H[:, :n].max(axis=1), L[:, :n].min(axis=1)
        res[f"Range d'ouverture {n} min"] = cassure(O, H, L, C, ok, cout, hh, ll, ll, hh, n)
    amp = h_veille - l_veille
    res["Cassure de Williams"] = cassure(O, H, L, C, ok, cout, o0 + 0.5 * amp, o0 - 0.5 * amp, o0, o0, 0)
    etir = glissant_complet(np.minimum(hj - o0, o0 - lj), complete, 10)
    res["Etirement de Crabel"] = cassure(O, H, L, C, ok, cout, o0 + etir, o0 - etir, o0 - etir, o0 + etir, 0)
    mil = (h_veille + l_veille) / 2
    res["Cassure de la veille"] = cassure(O, H, L, C, ok, cout, h_veille, l_veille, mil, mil, 0)
    s1h = np.sign(C[:, 59] - o0).astype(np.int64)
    res["Momentum de la 1re heure"] = entree_fixe(O, H, L, C, ok, cout, s1h, 60, rien, rien, N - 1)
    res["Tendance VWAP"] = tendance_vwap(O, C, vwap(H, L, C, X["V"]), ok, cout)
    gap = o0 / pc - 1
    s_cont = np.where(np.abs(gap) >= 0.0025, np.sign(np.nan_to_num(gap)), 0).astype(np.int64)
    res["Continuation du gap"] = entree_fixe(O, H, L, C, ok, cout, s_cont, 1, pc, rien, N - 1)
    s_fade = np.where((np.abs(gap) >= 0.0015) & (np.abs(gap) <= 0.01), -np.sign(np.nan_to_num(gap)), 0).astype(np.int64)
    e1 = O[:, 1]
    stop_fade = e1 * (1 + np.sign(gap) * np.abs(gap))
    res["Comblement du gap"] = entree_fixe(O, H, L, C, ok, cout, s_fade, 1, stop_fade, pc, N - 1)
    r30 = C[:, 29] / o0 - 1
    moy30 = glissant_complet(np.abs(r30), complete, 20)
    s_ext = np.where(np.abs(r30) > 1.5 * moy30, -np.sign(r30), 0).astype(np.int64)
    stop_ext = np.where(r30 > 0, H[:, :30].max(axis=1), L[:, :30].min(axis=1))
    res["Retournement apres 30 min extremes"] = entree_fixe(O, H, L, C, ok, cout, s_ext, 30, stop_ext, rien, N - 1)
    # tournant du mois : rang parmi les seances completes du mois (les lignes de jours feries ne comptent pas)
    mois = pd.DatetimeIndex(J).to_period("M")
    ic = np.where(complete)[0]
    mc = mois[ic]
    rang, dernier = np.full(nd, 99), np.zeros(nd, bool)
    rang[ic] = pd.Series(np.arange(len(ic))).groupby(mc).cumcount().values          # 0 = 1re seance du mois
    dernier[ic] = np.r_[mc[1:] != mc[:-1], True]
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


def ordre_hasard(nd, rng, n=N):
    """Ordre des minutes au hasard pour chaque seance, la 1re minute restant en place."""
    return np.concatenate([np.zeros((nd, 1), int), 1 + np.argsort(rng.random((nd, n - 1)), axis=1)], axis=1)


def melanger_perm(O, H, L, C, V, perm, tick=0.25):
    """Remet les minutes de chaque seance dans l'ordre perm ; forme des minutes, volatilite et resultat de la seance
    conserves. Prix arrondis au tick, comme les vrais (les egalites exactes restent possibles)."""
    ro = np.ones_like(O)
    ro[:, 1:] = O[:, 1:] / C[:, :-1]
    rh, rl, rc = H / O, L / O, C / O
    ro, rh, rl, rc, V2 = (np.take_along_axis(x, perm, axis=1) for x in (ro, rh, rl, rc, V))
    O2, H2, L2, C2 = (np.empty_like(O) for _ in range(4))
    prix = O[:, 0].copy()
    for m in range(O.shape[1]):
        om = prix * (ro[:, m] if m > 0 else 1.0)
        O2[:, m], H2[:, m], L2[:, m], C2[:, m] = om, om * rh[:, m], om * rl[:, m], om * rc[:, m]
        prix = C2[:, m]
    arr = lambda x: np.round(x / tick) * tick
    return arr(O2), arr(H2), arr(L2), arr(C2), V2


def melanger(O, H, L, C, V, rng):
    """Bruit : les minutes de chaque seance sont remises au hasard (la 1re reste en place)."""
    return melanger_perm(O, H, L, C, V, ordre_hasard(O.shape[0], rng))
