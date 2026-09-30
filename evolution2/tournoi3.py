"""Strategies du tournoi n°3 (README.md) sur les tableaux minute (seances x 390) de intraday/strategies.py charger.
Chaque fonction renvoie les points nets de frais par seance (0 sans trade)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "tournoi"))
import concurrents as K1  # noqa: E402  (cassure, entree_fixe, melanger, precedente... du tournoi n°1)
from profil import profil  # noqa: E402

st = K1.st
N = 390
NAN = np.nan
DONNEES = ICI / "donnees"
TICK = 0.25


# ---------------------------------------------------------------- donnees quotidiennes (connues le matin)

def lire_quotidien():
    """GEX et DIX (SqueezeMetrics) et VIX / VIX 3 mois (CBOE), par date de cloture."""
    dg = pd.read_csv(DONNEES / "dix_gex.csv")
    dg.columns = [c.strip().lower() for c in dg.columns]
    dg["date"] = pd.to_datetime(dg["date"])
    def vix(nom):
        v = pd.read_csv(DONNEES / nom)
        v.columns = [c.strip().upper() for c in v.columns]
        return pd.Series(v["CLOSE"].astype(float).values, index=pd.to_datetime(v["DATE"], format="mixed"))
    ratio = (vix("vix.csv") / vix("vix3m.csv")).dropna()
    return {"gex": pd.Series(dg["gex"].astype(float).values, index=dg["date"]),
            "dix": pd.Series(dg["dix"].astype(float).values, index=dg["date"]),
            "vix_ratio": ratio}


def veille(J, serie):
    """Pour chaque seance d : derniere valeur publiee strictement avant d (cloture de la veille ou avant)."""
    s = serie.sort_index()
    s = s[~s.index.duplicated(keep="last")]
    i = np.searchsorted(s.index.values, pd.DatetimeIndex(J).values, side="left") - 1
    out = np.where(i >= 0, s.values[np.maximum(i, 0)], NAN)
    # une valeur de plus de 5 jours n'est plus « la veille »
    age = pd.DatetimeIndex(J).values - np.where(i >= 0, s.index.values[np.maximum(i, 0)], np.datetime64("NaT", "ns"))
    return np.where(age <= np.timedelta64(5, "D"), out, NAN)


def quantile_252(x, q):
    """Quantile q des 252 valeurs precedentes (la valeur du jour n'en fait pas partie)."""
    return pd.Series(x).rolling(252, min_periods=252).quantile(q).shift(1).values


def filtres(J, Q):
    """Masques booleens des jours retenus par chaque filtre, et jours ou le filtre est defini."""
    g, dx, vr = veille(J, Q["gex"]), veille(J, Q["dix"]), veille(J, Q["vix_ratio"])
    g_med, g_haut, dx_haut = quantile_252(g, 0.5), quantile_252(g, 2 / 3), quantile_252(dx, 0.9)
    f = {"G1": (g < 0, ~np.isnan(g)),
         "G2": (g >= g_haut, ~np.isnan(g) & ~np.isnan(g_haut)),
         "G3": (g < g_med, ~np.isnan(g) & ~np.isnan(g_med)),
         "D1": (dx >= dx_haut, ~np.isnan(dx) & ~np.isnan(dx_haut)),
         "V1": (vr >= 1.0, ~np.isnan(vr)),
         "V2": (vr <= 0.85, ~np.isnan(vr))}
    return {k: (np.nan_to_num(m, nan=0).astype(bool) & d, d) for k, (m, d) in f.items()}


# ---------------------------------------------------------------- briques

@njit(cache=True)
def rejet(O, H, L, C, ok, cout, niv_h, niv_b, stop_h, stop_b, obj_h, obj_b):
    """Premier contact d'un niveau : vente au niveau haut, achat au niveau bas (NaN : niveau absent), rempli au niveau
    lui-meme (prudent). Dans la minute d'entree, seul le stop compte ; ensuite ouverture au-dela du stop ou de
    l'objectif -> sortie a l'ouverture, puis stop avant objectif ; sortie a 16 h. Deux niveaux dans la meme minute :
    journee sautee."""
    nd = O.shape[0]
    out = np.zeros(nd)
    for d in range(nd):
        if not ok[d]:
            continue
        s = 0
        e = 0.0
        st_ = 0.0
        ob = np.nan
        m0 = -1
        for m in range(N):
            up = (not np.isnan(niv_h[d])) and H[d, m] >= niv_h[d]
            dn = (not np.isnan(niv_b[d])) and L[d, m] <= niv_b[d]
            if up and dn:
                break
            if up:
                s, e, st_, ob, m0 = -1, niv_h[d], stop_h[d], obj_h[d], m
                break
            if dn:
                s, e, st_, ob, m0 = 1, niv_b[d], stop_b[d], obj_b[d], m
                break
        if s == 0:
            continue
        sortie = np.nan
        if (s < 0 and H[d, m0] >= st_) or (s > 0 and L[d, m0] <= st_):
            sortie = st_
        else:
            for m in range(m0 + 1, N):
                o = O[d, m]
                if (s < 0 and o >= st_) or (s > 0 and o <= st_):
                    sortie = o
                    break
                if not np.isnan(ob) and ((s < 0 and o <= ob) or (s > 0 and o >= ob)):
                    sortie = o
                    break
                if (s < 0 and H[d, m] >= st_) or (s > 0 and L[d, m] <= st_):
                    sortie = st_
                    break
                if not np.isnan(ob) and ((s < 0 and L[d, m] <= ob) or (s > 0 and H[d, m] >= ob)):
                    sortie = ob
                    break
        if np.isnan(sortie):
            sortie = C[d, N - 1]
        out[d] = s * (sortie - e) - cout
    return out


def entree_par_minute(O, H, L, C, ok, cout, sens, m_entree, stop, obj):
    """entree_fixe (tournoi n°1) avec une minute d'entree propre a chaque seance, sortie a 16 h."""
    out = np.zeros(len(sens))
    for m in np.unique(m_entree[sens != 0]):
        sel = (m_entree == m) & (sens != 0)
        s = np.where(sel, sens, 0).astype(np.int64)
        out += K1.entree_fixe(O, H, L, C, ok, cout, s, int(m), stop, obj, N - 1)
    return out


def zone_valeur_veille(H, L, X, complete):
    """POC, haut et bas de la zone de valeur de la derniere seance complete du meme contrat."""
    poc, vah, val = profil(H, L, X["V"], TICK)
    prec = K1.precedente(complete, X.get("contrat"))
    return K1.de_la(poc, prec), K1.de_la(vah, prec), K1.de_la(val, prec)


def regle_80(O, H, L, C, poc, vah, val):
    """P1 : sens, minute d'entree, stop et objectif de la regle des 80 %."""
    nd = len(O)
    sens, me = np.zeros(nd, np.int64), np.zeros(nd, np.int64)
    stop, obj = np.full(nd, NAN), np.full(nd, NAN)
    o0 = O[:, 0]
    for d in np.where((o0 > vah) | (o0 < val))[0]:
        dedans = 0
        for k in range(1, 13):
            c = C[d, 30 * k - 1]
            dedans = dedans + 1 if val[d] <= c <= vah[d] else 0
            if dedans == 2:
                m = 30 * k
                if o0[d] > vah[d]:
                    sens[d], obj[d], stop[d] = -1, val[d], H[d, :m].max()
                else:
                    sens[d], obj[d], stop[d] = 1, vah[d], L[d, :m].min()
                me[d] = m
                break
    return sens, me, stop, obj


def acceptation(O, C, poc, vah, val):
    """P2 : ouverture dans la zone ; premiere demi-heure qui finit dehors -> dans ce sens, stop au POC."""
    nd = len(O)
    sens, me = np.zeros(nd, np.int64), np.zeros(nd, np.int64)
    o0 = O[:, 0]
    for d in np.where((o0 >= val) & (o0 <= vah))[0]:
        for k in range(1, 13):
            c = C[d, 30 * k - 1]
            if c > vah[d] or c < val[d]:
                sens[d], me[d] = (1 if c > vah[d] else -1), 30 * k
                break
    return sens, me, poc.copy()


def toutes(J, O, H, L, C, P, X, cout, Q, murs=None):
    """Points nets par seance de chaque strategie du tournoi n°3, et ok. Q : lire_quotidien(). murs : dict optionnel
    {"call": ..., "put": ..., "zero": ...} par seance (niveaux de la veille)."""
    complete = st.journees_completes(P)
    ok = complete & ~X["echeance"]
    nd = len(J)
    o0 = O[:, 0]
    rien = np.full(nd, NAN)
    F = filtres(J, Q)
    base = {
        "suivre 10 h": K1.entree_fixe(O, H, L, C, ok, cout, np.sign(C[:, 29] - o0).astype(np.int64), 30, rien, rien, N - 1),
        "retour 10 h 30": K1.entree_fixe(O, H, L, C, ok, cout, (-np.sign(C[:, 59] - o0)).astype(np.int64), 60, rien, rien, N - 1),
        "achat": K1.entree_fixe(O, H, L, C, ok, cout, np.ones(nd, np.int64), 0, rien, rien, N - 1),
    }
    z = st.zone_de_bruit(J, O, H, L, C, P, X)
    base["zone"] = np.where(ok, (z["brut"] - cout * z["allers"]).reindex(pd.DatetimeIndex(J)).fillna(0).values, 0.0)
    choix = {"G1": "suivre 10 h", "G2": "retour 10 h 30", "G3": "zone", "D1": "achat", "V1": "suivre 10 h", "V2": "retour 10 h 30"}
    res = {k: np.where(F[k][0], base[b], 0.0) for k, b in choix.items()}
    poc, vah, val = zone_valeur_veille(H, L, X, complete)
    s1, m1, st1, ob1 = regle_80(O, H, L, C, poc, vah, val)
    res["P1"] = entree_par_minute(O, H, L, C, ok, cout, s1, m1, st1, ob1)
    s2, m2, st2 = acceptation(O, C, poc, vah, val)
    res["P2"] = entree_par_minute(O, H, L, C, ok, cout, s2, m2, st2, rien)
    dedans = (o0 >= val) & (o0 <= vah)
    q = (vah - val) / 4
    res["P3"] = rejet(O, H, L, C, ok & dedans, cout, np.where(dedans, vah, NAN), np.where(dedans, val, NAN),
                      vah + q, val - q, poc, poc)
    if murs is not None:
        cw, pw, zg = murs["call"], murs["put"], murs["zero"]
        sous = o0 < cw
        res["W1"] = rejet(O, H, L, C, ok & sous, cout, np.where(sous, cw, NAN), rien, cw * 1.0025, rien, rien, rien)
        dessus = o0 > pw
        res["W2"] = rejet(O, H, L, C, ok & dessus, cout, rien, np.where(dessus, pw, NAN), rien, pw * 0.9975, rien, rien)
        F["W3"] = (np.nan_to_num(o0 < zg, nan=0).astype(bool) & ~np.isnan(zg), ~np.isnan(zg))
        choix["W3"] = "suivre 10 h"
        res["W3"] = np.where(F["W3"][0], base["suivre 10 h"], 0.0)
    return res, ok, {"base": base, "choix": choix, "filtres": F}
