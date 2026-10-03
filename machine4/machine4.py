#!/usr/bin/env python3
"""Machine 4 (README.md) : tres grande recherche d'une 4e source pour le bot 3 en 1, sur les barres journalieres des 40
futures CME (Databento), avec un jumeau de bruit (seances permutees) et deux paliers au coffre.

  python3 machine4.py exploration   2011-2022 seulement (rien apres le 31 decembre 2022 n'est lu) : vraies donnees et
                                    8 bruits -> exploration4.txt, candidates4.json
  python3 machine4.py coffre        ouvre 2023 - septembre 2026 une seule fois pour les 10 candidates et les 80 placebos
                                    -> coffre4.txt, coffre4.json

Decision a la cloture, executee a ce prix (+ 1 tick et 1 $ par ordre) ; la position tenue apres la cloture t gagne le
rendement de t + 1 ; un passage d'echeance en position coute un aller-retour (comme tournoi9). Lancer depuis ce dossier."""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit, prange

ICI = Path(__file__).resolve().parent
R = ICI.parent
sys.path.insert(0, str(R / "tournoi8"))
sys.path.insert(0, str(R / "tournoi9"))
sys.path.insert(0, str(R / "fonds"))
from tournoi8 import feries  # noqa: E402
from tournoi9 import rsi_wilder  # noqa: E402
from sources import SPEC  # noqa: E402

DEBUT, FIN_EXPLORATION, DEBUT_COFFRE = "2011-01-01", "2022-12-31", "2023-01-01"
PERIODES = (("2011-01-01", "2014-12-31"), ("2015-01-01", "2018-12-31"), ("2019-01-01", "2022-12-31"))
ANNEES_COFFRE = (2023, 2024, 2025, 2026)
RACINES = tuple(SPEC)                                   # 40 marches, ordre fixe
# contrat trade : ($ par point, tick). Micro quand il existe, sinon le contrat standard de fonds/sources.py
MICRO = {"ES": (5.0, 0.25), "NQ": (2.0, 0.25), "RTY": (5.0, 0.1), "YM": (0.5, 1.0), "GC": (10.0, 0.1),
         "SI": (1000.0, 0.005), "HG": (2500.0, 0.0005), "CL": (100.0, 0.01), "6E": (12500.0, 0.0001),
         "6A": (10000.0, 0.0001), "6B": (6250.0, 0.0001), "BTC": (0.1, 5.0), "ETH": (0.1, 0.5)}
NOM_MICRO = {"ES": "MES", "NQ": "MNQ", "RTY": "M2K", "YM": "MYM", "GC": "MGC", "SI": "SIL", "HG": "MHG", "CL": "MCL",
             "6E": "M6E", "6A": "M6A", "6B": "M6B", "BTC": "MBT", "ETH": "MET"}
ECART_MAX = 400.0
MIN_TRADES, CORR_BOT_MAX, CORR_GRAPPE_MAX, N_CANDIDATES, N_BRUITS = 50, 0.3, 0.5, 10, 8
SEUILS_T = (2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0)
T_RETENUE, T_INTERESSANTE, FDR_MAX = 2.58, 1.0, 0.30

MA_K = (3, 5, 10, 20, 50, 100, 200)
EXT_N = (3, 5, 7, 10, 15, 20)
CAS_N = (10, 20, 40, 55, 100, 150, 250)
RET_L = (1, 2, 5, 10, 20, 40, 60, 120, 250)
FAMILLES = {1: "RSI court", 2: "IBS", 3: "plus bas de n jours", 4: "grand mouvement", 5: "cassure", 6: "tendance",
            7: "calendrier", 8: "volatilite", 9: "croisee"}


def contrat(racine):
    if racine in MICRO:
        return MICRO[racine]
    return float(SPEC[racine][2]), float(SPEC[racine][1])


# ----------------------------------------------------------------------------- donnees

def _serie(x, fer):
    """Comme tournoi9.charger : cloture du contrat le plus echange, rendement continu (le jour d'un changement : nouveau
    contrat depuis la veille), changement, IBS de la seance ; seances courtes des jours feries fusionnees avec la suivante."""
    c0 = x[x.symbole.str.endswith(".0")].set_index("date").sort_index()
    c0 = c0[~c0.index.duplicated(keep="last")]
    c1 = x[x.symbole.str.endswith(".1")].set_index("date").sort_index()
    c1 = c1[~c1.index.duplicated(keep="last")].reindex(c0.index)
    meme = (c0["contrat"] == c0["contrat"].shift(1)).to_numpy()
    roule = (c0["contrat"] == c1["contrat"].shift(1)).to_numpy() & ~meme
    r = np.where(meme, c0["c"] / c0["c"].shift(1) - 1, np.where(roule, c0["c"] / c1["c"].shift(1) - 1, np.nan))
    r = np.where(np.abs(r) > 0.5, np.nan, r)
    etendue = (c0["h"] - c0["l"]).to_numpy()
    ibs = np.where(etendue > 0, (c0["c"] - c0["l"]).to_numpy() / np.where(etendue > 0, etendue, 1.0), np.nan)
    s = pd.DataFrame({"date": c0.index, "prix": c0["c"].to_numpy(), "r": np.nan_to_num(r), "change": ~meme, "ibs": ibs})
    s = s.reset_index(drop=True)
    s.loc[0, "change"] = False
    est_ferie = s["date"].isin(fer).to_numpy()
    r_, ch_ = s["r"].to_numpy().copy(), s["change"].to_numpy().copy()
    for i in np.flatnonzero(est_ferie):
        if i + 1 < len(s):
            r_[i + 1] = (1 + r_[i]) * (1 + r_[i + 1]) - 1
            ch_[i + 1] = ch_[i + 1] or ch_[i]
    return s.assign(r=r_, change=ch_)[~est_ferie].reset_index(drop=True)


def charger(jusqu_au):
    """Les 40 marches sur le calendrier commun (seances du ES). Rien apres `jusqu_au` n'est lu. Renvoie un dict de
    tableaux (M, T) : prix (cloture, report du dernier), r (rendement continu), chg (changement d'echeance), ibs."""
    d = pd.read_csv(R / "fonds/donnees/futures_1d.csv.gz", parse_dates=["date"])
    d = d[d["date"] <= pd.Timestamp(jusqu_au)]
    d["racine"] = d["symbole"].str.split(".").str[0]
    fer = list(feries(range(2009, 2028)))
    series = {k: _serie(g, fer) for k, g in d.groupby("racine") if k in SPEC}
    jours = pd.DatetimeIndex(series["ES"]["date"])
    M, T = len(RACINES), len(jours)
    prix = np.full((M, T), np.nan)
    r = np.zeros((M, T))
    chg = np.zeros((M, T), np.int8)
    ibs = np.full((M, T), np.nan)
    for m, k in enumerate(RACINES):
        if k not in series:                                                # pas encore cote a cette date
            continue
        s = series[k]
        j = np.searchsorted(jours.values, s["date"].values, side="left")   # seance commune suivante (ou la meme)
        ok = j < T
        s, j = s[ok], j[ok]
        rr = np.ones(T)
        np.multiply.at(rr, j, 1 + s["r"].to_numpy())
        r[m] = rr - 1
        np.maximum.at(chg[m], j, s["change"].to_numpy().astype(np.int8))
        dernier = pd.Series(np.arange(len(j))).groupby(j).last()           # la derniere seance fusionnee donne prix, IBS
        prix[m, dernier.index] = s["prix"].to_numpy()[dernier.values]
        ibs[m, dernier.index] = s["ibs"].to_numpy()[dernier.values]
        prix[m] = pd.Series(prix[m]).ffill().to_numpy()
    r[np.isnan(prix)] = 0.0
    return {"jours": jours, "prix": prix, "r": r, "chg": chg, "ibs": ibs}


def calendrier(jours):
    """Pour chaque seance t, attributs de la seance suivante (celle dont le rendement est gagne) : jour de la semaine,
    rang autour du changement de mois (-5..-1 = dernieres seances, 0..7 = premieres, 99 sinon), veille de ferie,
    semaine de l'echeance des options (1) ou la suivante (2), mois. Le calendrier (jours ouvres hors feries) donne la
    seance qui suit la derniere."""
    fer = np.array(sorted(feries(range(2009, 2029))), dtype="datetime64[D]")
    j = jours.values.astype("datetime64[D]")
    suiv = np.r_[j[1:], np.busday_offset(j[-1], 1, roll="forward", holidays=fer)]
    sv = pd.DatetimeIndex(suiv)
    debut_mois = sv.to_period("M").to_timestamp().values.astype("datetime64[D]")
    mois_suiv = (sv.to_period("M") + 1).to_timestamp().values.astype("datetime64[D]")
    apres = np.busday_count(suiv + 1, mois_suiv, holidays=fer)             # seances apres, dans le mois
    avant = np.busday_count(debut_mois, suiv, holidays=fer)                 # seances avant, dans le mois
    tom = np.where(apres < 5, -(apres + 1), np.where(avant < 8, avant, 99))
    veille = np.isin(np.busday_offset(suiv, 1, roll="forward"), fer)
    opex = np.zeros(len(j), np.int64)
    for i, x in enumerate(sv):
        v = pd.date_range(x.replace(day=1), periods=31, freq="D")
        v = v[(v.month == x.month) & (v.dayofweek == 4)][2]                 # 3e vendredi
        if v - pd.Timedelta(days=4) <= x <= v:
            opex[i] = 1
        elif v + pd.Timedelta(days=3) <= x <= v + pd.Timedelta(days=7):
            opex[i] = 2
    return np.vstack([sv.dayofweek.values, tom, veille.astype(np.int64), opex, sv.month.values]).astype(np.int64)


def indicateurs(D):
    """Indicateurs sur la serie continue A = produit des (1 + r), NaN avant la premiere cotation du marche."""
    prix, r = D["prix"], D["r"]
    M, T = prix.shape
    A = np.full((M, T), np.nan)
    rr = np.where(np.isnan(prix), np.nan, r)
    out = {k: np.full((len(v), M, T), np.nan) for k, v in (("RSI", (2, 3, 4, 5)), ("MA", MA_K), ("MINI", EXT_N),
                                                            ("MAXI", EXT_N), ("PMAX", CAS_N), ("PMIN", CAS_N), ("RL", RET_L))}
    SIG, VOL, MED = (np.full((M, T), np.nan) for _ in range(3))
    for m in range(M):
        ok = np.flatnonzero(~np.isnan(prix[m]))
        if len(ok) == 0:
            continue
        a0 = ok[0]
        A[m, a0:] = np.cumprod(1 + r[m, a0:])
        sA, sr = pd.Series(A[m]), pd.Series(rr[m])
        for i, n in enumerate((2, 3, 4, 5)):
            out["RSI"][i, m, a0:] = rsi_wilder(A[m, a0:], n)
        for i, k in enumerate(MA_K):
            out["MA"][i, m] = sA.rolling(k).mean().to_numpy()
        for i, n in enumerate(EXT_N):
            out["MINI"][i, m] = sA.rolling(n).min().to_numpy()
            out["MAXI"][i, m] = sA.rolling(n).max().to_numpy()
        for i, n in enumerate(CAS_N):
            out["PMAX"][i, m] = sA.rolling(n).max().shift(1).to_numpy()
            out["PMIN"][i, m] = sA.rolling(n).min().shift(1).to_numpy()
        for i, L in enumerate(RET_L):
            out["RL"][i, m] = (sA / sA.shift(L) - 1).to_numpy()
        SIG[m] = sr.rolling(60).std().to_numpy()                             # ecart-type des 60 dernieres seances (t compris)
        v20 = sr.rolling(20).std()
        VOL[m] = v20.to_numpy()
        MED[m] = v20.rolling(250).median().shift(1).to_numpy()
    out.update(A=A, SIG=SIG, VOL=VOL, MED=MED, IBS=D["ibs"], CAL=calendrier(D["jours"]))
    return out


def dollars(D):
    """PP[m, t] : $ gagnes pour un rendement de 1 sur la seance t avec 1 contrat (cloture de la veille x $ par point) ;
    COTE[m] : $ par ordre (1 $ + 1 tick)."""
    M, T = D["prix"].shape
    PP = np.zeros((M, T))
    COTE = np.zeros(M)
    for m, k in enumerate(RACINES):
        pt, tick = contrat(k)
        PP[m, 1:] = np.nan_to_num(D["prix"][m, :-1]) * pt
        COTE[m] = 1.0 + tick * pt
    return PP, COTE


def bruiter(D, graine, debut=DEBUT, fin=FIN_EXPLORATION):
    """Jumeau de bruit : pour chaque marche, les seances cotees de [debut, fin] sont permutees au hasard ; chacune garde
    son rendement, son IBS et son prix de depart (via PP). Dates, echeances et calendrier restent en place."""
    rng = np.random.default_rng(graine)
    jours = D["jours"]
    fen = np.flatnonzero((jours >= pd.Timestamp(debut)) & (jours <= pd.Timestamp(fin)))
    PP, COTE = dollars(D)
    B = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in D.items()}
    for m in range(len(RACINES)):
        idx = fen[~np.isnan(D["prix"][m, fen])]
        p = rng.permutation(len(idx))
        B["r"][m, idx] = D["r"][m, idx[p]]
        B["ibs"][m, idx] = D["ibs"][m, idx[p]]
        PP[m, idx] = PP[m, idx[p]]
    return B, PP, COTE


def bot_quotidien(jours):
    b = pd.read_csv(ICI / "bot_quotidien.csv", parse_dates=["date"]).set_index("date")["gain"]
    v = b.reindex(jours)
    return np.nan_to_num(v.to_numpy()), (~v.isna()).to_numpy()


def periodes(jours, coffre=False):
    per = np.full(len(jours), -1, np.int64)
    if coffre:
        for i, a in enumerate(ANNEES_COFFRE):
            per[jours.year == a] = i
    else:
        for i, (a, b) in enumerate(PERIODES):
            per[(jours >= pd.Timestamp(a)) & (jours <= pd.Timestamp(b))] = i
    return per


# ----------------------------------------------------------------------------- strategies

def grille(tradables):
    """Une ligne par strategie : [famille, marche, p1..p7]."""
    L = []
    for m in tradables:
        for n in range(4):
            for s in (5, 10, 15, 20, 25, 30):
                for f in range(4):
                    for e in range(8):
                        for c in range(3):
                            L.append((1, m, n, s, f, e, c, 0, 0))
        for x in range(5):
            for f in range(4):
                for e in range(5):
                    for c in range(3):
                        L.append((2, m, x, f, e, c, 0, 0, 0))
        for n in range(6):
            for e in range(7):
                for f in range(4):
                    for c in range(3):
                        L.append((3, m, n, e, f, c, 0, 0, 0))
        for z in range(5):
            for a in range(2):
                for g in range(3):
                    for h in range(5):
                        for f in range(4):
                            L.append((4, m, z, a, g, h, f, 0, 0))
        for n in range(7):
            for e in range(7):
                for c in range(3):
                    L.append((5, m, n, e, c, 0, 0, 0, 0))
        for i in range(7):
            for c in range(3):
                L.append((6, m, 0, i, c, 0, 0, 0, 0))
        for i in range(4):
            for c in range(3):
                L.append((6, m, 1, i, c, 0, 0, 0, 0))
        for sens in range(2):
            for w in range(5):
                L.append((7, m, 0, w, sens, 0, 0, 0, 0))
            for a in range(-5, 0):
                for n in range(1, 9):
                    L.append((7, m, 1, (a + 5) * 8 + n - 1, sens, 0, 0, 0, 0))
            L.append((7, m, 2, 0, sens, 0, 0, 0, 0))
            L.append((7, m, 3, 0, sens, 0, 0, 0, 0))
            L.append((7, m, 4, 0, sens, 0, 0, 0, 0))
            for mo in range(1, 13):
                L.append((7, m, 5, mo, sens, 0, 0, 0, 0))
        for g in range(2):
            for sens in range(2):
                for f in range(2):
                    L.append((8, m, g, sens, f, 0, 0, 0, 0))
    for m in tradables:
        for s in range(len(RACINES)):
            if s == m:
                continue
            for li in range(5):
                for z in range(3):
                    for a in range(2):
                        for g in range(3):
                            for h in range(3):
                                L.append((9, m, s, li, z, a, g, h, 0))
    return np.array(L, np.int64)


@njit(cache=True)
def _filtre(f, m, t, A, MA, sens):
    """Filtre de tendance : aucun (0), moyenne des 50 (1), 100 (2) ou 200 (3) cloture ; achat au-dessus, vente en dessous."""
    if f == 0:
        return True
    k = 3 + f                                       # MA_K : 50 -> 4, 100 -> 5, 200 -> 6
    if sens > 0:
        return A[m, t] > MA[k, m, t]
    return A[m, t] < MA[k, m, t]


@njit(cache=True)
def _permis(cote, d):
    """Sens permis : 0 achats seuls, 1 ventes seules, 2 les deux."""
    return (cote == 2) or (cote == 0 and d > 0) or (cote == 1 and d < 0)


@njit(cache=True)
def positions(row, A, Rr, RSI, MA, MINI, MAXI, PMAX, PMIN, RL, SIG, VOL, MED, IBS, CAL):
    """Position (-1, 0, 1) tenue apres la cloture t (gagne le rendement de t + 1)."""
    fam, m = row[0], row[1]
    T = A.shape[1]
    pos = np.zeros(T, np.int8)
    H_RSI = (1, 2, 3, 5, 10)
    H_IBS = (1, 2, 3, 5)
    H_EXT = (3, 5, 7, 10)
    H_GM = (1, 2, 3, 5, 10)
    H_CAS = (5, 10, 20, 40)
    H_X = (1, 2, 5)
    X_IBS = (0.10, 0.15, 0.20, 0.25, 0.30)
    Z_GM = (1.0, 1.5, 2.0, 2.5, 3.0)
    L_X = (1.0, 2.0, 5.0, 10.0, 20.0)
    if fam == 6 or fam == 7 or fam == 8:            # familles a position quotidienne
        for t in range(T):
            if np.isnan(A[m, t]):
                continue
            s = 0
            if fam == 6:
                if row[2] == 0:
                    v = RL[2 + row[3], m, t]        # L = 5, 10, 20, 40, 60, 120, 250
                else:
                    a = (1, 2, 3, 4)[row[3]]
                    v = MA[a, m, t] - MA[a + 2, m, t]   # 5/20, 10/50, 20/100, 50/200
                if v > 0:
                    s = 1
                elif v < 0:
                    s = -1
                if row[4] == 0 and s < 0:
                    s = 0
                if row[4] == 1 and s > 0:
                    s = 0
            elif fam == 7:
                typ, val = row[2], row[3]
                ok = False
                if typ == 0:
                    ok = CAL[0, t] == val
                elif typ == 1:
                    a = val // 8 - 5
                    n = val % 8 + 1
                    ok = CAL[1, t] != 99 and a <= CAL[1, t] <= a + n - 1
                elif typ == 2:
                    ok = CAL[2, t] == 1
                elif typ == 3:
                    ok = CAL[3, t] == 1
                elif typ == 4:
                    ok = CAL[3, t] == 2
                else:
                    ok = CAL[4, t] == val
                if ok:
                    s = 1 if row[4] == 0 else -1
            else:
                bas = VOL[m, t] < MED[m, t]
                haut = VOL[m, t] > MED[m, t]
                if (row[2] == 0 and bas) or (row[2] == 1 and haut):
                    s = 1 if row[3] == 0 else -1
                    if row[4] == 1 and not _filtre(3, m, t, A, MA, s):
                        s = 0
            pos[t] = s
        return pos
    p = 0
    tenu = 0
    for t in range(1, T):
        if np.isnan(A[m, t]):
            continue
        # 1. sortie
        if p != 0:
            tenu += 1
            sortie = False
            if fam == 1:
                e = row[5]
                if e < 3:
                    k = e                           # MA_K : 3, 5, 10
                    sortie = A[m, t] > MA[k, m, t] if p > 0 else A[m, t] < MA[k, m, t]
                else:
                    sortie = tenu >= H_RSI[e - 3]
            elif fam == 2:
                e = row[4]
                if e < 4:
                    sortie = tenu >= H_IBS[e]
                else:
                    sortie = A[m, t] > MA[1, m, t] if p > 0 else A[m, t] < MA[1, m, t]
            elif fam == 3:
                e = row[3]
                if e < 4:
                    k = e                           # EXT_N : 3, 5, 7, 10
                    sortie = A[m, t] >= MAXI[k, m, t] if p > 0 else A[m, t] <= MINI[k, m, t]
                else:
                    sortie = tenu >= (3, 5, 10)[e - 4]
            elif fam == 4:
                sortie = tenu >= H_GM[row[5]]
            elif fam == 5:
                e = row[3]
                if e < 4:
                    sortie = tenu >= H_CAS[e]
                else:
                    k = e - 2                       # MA_K : 10 -> 2, 20 -> 3, 50 -> 4
                    sortie = A[m, t] < MA[k, m, t] if p > 0 else A[m, t] > MA[k, m, t]
            else:
                sortie = tenu >= H_X[row[7]]
            if sortie:
                p = 0
        # 2. entree
        d = 0
        if fam == 1:
            v = RSI[row[2], m, t]
            if v < row[3]:
                d = 1
            elif v > 100 - row[3]:
                d = -1
            if d != 0 and not (_permis(row[6], d) and _filtre(row[4], m, t, A, MA, d)):
                d = 0
        elif fam == 2:
            v = IBS[m, t]
            x = X_IBS[row[2]]
            if v < x:
                d = 1
            elif v > 1 - x:
                d = -1
            if d != 0 and not (_permis(row[5], d) and _filtre(row[3], m, t, A, MA, d)):
                d = 0
        elif fam == 3:
            n = row[2]
            if A[m, t] <= MINI[n, m, t]:
                d = 1
            elif A[m, t] >= MAXI[n, m, t]:
                d = -1
            if d != 0 and not (_permis(row[5], d) and _filtre(row[4], m, t, A, MA, d)):
                d = 0
        elif fam == 4:
            z = Rr[m, t] / SIG[m, t - 1] if SIG[m, t - 1] > 0 else 0.0
            zz = Z_GM[row[2]]
            g = row[4]
            if z >= zz and g != 2:
                d = 1
            elif z <= -zz and g != 1:
                d = -1
            if row[3] == 1:
                d = -d
            if d != 0 and not _filtre(row[6], m, t, A, MA, d):
                d = 0
        elif fam == 5:
            n = row[2]
            if A[m, t] > PMAX[n, m, t]:
                d = 1
            elif A[m, t] < PMIN[n, m, t]:
                d = -1
            if d != 0 and not _permis(row[4], d):
                d = 0
        else:
            s = row[2]
            L = L_X[row[3]]
            z = RL[row[3], s, t - 1] / (SIG[s, t - 1] * np.sqrt(L)) if SIG[s, t - 1] > 0 else 0.0   # source : cloture de la veille
            zz = (0.0, 1.0, 2.0)[row[4]]
            g = row[6]
            if z > 0 and z >= zz and g != 2:
                d = 1
            elif z < 0 and z <= -zz and g != 1:
                d = -1
            if row[5] == 1:
                d = -d
        if d != 0:
            if p == 0:
                p = d
                tenu = 0
            elif p == d:
                tenu = 0                            # entree dans le sens tenu : prolonge, sans frais
        pos[t] = p
    return pos


@njit(cache=True)
def gains(pos, m, Rr, PP, COTE, CHG):
    """$ net de chaque seance pour 1 contrat ; ordres executes a la cloture ; echeance en position : aller-retour."""
    T = pos.shape[0]
    x = np.zeros(T)
    for t in range(1, T):
        av = pos[t - 1]
        ordres = abs(pos[t] - av) + (2 if (av != 0 and CHG[m, t] != 0) else 0)
        x[t] = av * Rr[m, t] * PP[m, t] - ordres * COTE[m]
    return x


@njit(cache=True)
def mesurer(pos, m, Rr, PP, COTE, CHG, per, bot, bm):
    """[n, somme, somme des carres, trades, sx, sxx, sb, sbb, sxb, nb (seances du bot), p0, p1, p2, p3]."""
    out = np.zeros(14)
    x = gains(pos, m, Rr, PP, COTE, CHG)
    for t in range(1, pos.shape[0]):
        if per[t] < 0:
            continue
        v = x[t]
        out[0] += 1
        out[1] += v
        out[2] += v * v
        if pos[t] != 0 and pos[t] != pos[t - 1]:
            out[3] += 1
        out[10 + per[t]] += v
        if bm[t]:
            b = bot[t]
            out[4] += v
            out[5] += v * v
            out[6] += b
            out[7] += b * b
            out[8] += v * b
            out[9] += 1
    return out


@njit(parallel=True, cache=True)
def tout_mesurer(P, A, Rr, PP, COTE, CHG, RSI, MA, MINI, MAXI, PMAX, PMIN, RL, SIG, VOL, MED, IBS, CAL, per, bot, bm):
    out = np.zeros((P.shape[0], 14))
    for i in prange(P.shape[0]):
        pos = positions(P[i], A, Rr, RSI, MA, MINI, MAXI, PMAX, PMIN, RL, SIG, VOL, MED, IBS, CAL)
        out[i] = mesurer(pos, P[i, 1], Rr, PP, COTE, CHG, per, bot, bm)
    return out


def args(I, D, PP, COTE):
    return (I["A"], D["r"], PP, COTE, D["chg"], I["RSI"], I["MA"], I["MINI"], I["MAXI"], I["PMAX"], I["PMIN"], I["RL"],
            I["SIG"], I["VOL"], I["MED"], I["IBS"], I["CAL"])


def pos_de(row, I, D):
    return positions(np.asarray(row, np.int64), I["A"], D["r"], I["RSI"], I["MA"], I["MINI"], I["MAXI"], I["PMAX"],
                     I["PMIN"], I["RL"], I["SIG"], I["VOL"], I["MED"], I["IBS"], I["CAL"])


def resumer(S):
    """t du gain quotidien, correlation avec le bot, periodes positives."""
    n, s, ss = S[:, 0], S[:, 1], S[:, 2]
    moy = s / np.maximum(n, 1)
    var = np.maximum(ss / np.maximum(n, 1) - moy ** 2, 0) * n / np.maximum(n - 1, 1)
    t = np.where(var > 0, moy / np.sqrt(np.where(var > 0, var, 1)) * np.sqrt(n), 0.0)
    nb = S[:, 9]
    num = nb * S[:, 8] - S[:, 4] * S[:, 6]
    den = (nb * S[:, 5] - S[:, 4] ** 2) * (nb * S[:, 7] - S[:, 6] ** 2)
    corr = np.where(den > 0, num / np.sqrt(np.where(den > 0, den, 1)), 0.0)
    return t, corr


def decrire(row):
    f, m = int(row[0]), int(row[1])
    k = RACINES[m]
    nom = f"{k} ({NOM_MICRO.get(k, k)})"
    sens = ("achats seuls", "ventes seules", "achats et ventes")
    filt = ("sans filtre", "filtre 50", "filtre 100", "filtre 200")
    if f == 1:
        e = int(row[5])
        so = f"sortie clot. > moy. {(3, 5, 10)[e]}" if e < 3 else f"sortie apres {(1, 2, 3, 5, 10)[e - 3]} s."
        return f"{nom} RSI({row[2] + 2}) < {row[3]} (vente > {100 - row[3]}), {so}, {filt[row[4]]}, {sens[row[6]]}"
    if f == 2:
        e = int(row[4])
        so = f"sortie apres {(1, 2, 3, 5)[e]} s." if e < 4 else "sortie clot. > moy. 5"
        return f"{nom} IBS < {(0.10, 0.15, 0.20, 0.25, 0.30)[row[2]]:.2f}, {so}, {filt[row[3]]}, {sens[row[5]]}"
    if f == 3:
        e = int(row[3])
        so = f"sortie au plus haut des {(3, 5, 7, 10)[e]}" if e < 4 else f"sortie apres {(3, 5, 10)[e - 4]} s."
        return f"{nom} plus bas des {EXT_N[row[2]]} clotures, {so}, {filt[row[4]]}, {sens[row[5]]}"
    if f == 4:
        g = ("hausse ou baisse", "hausse seule", "baisse seule")[row[4]]
        return (f"{nom} mouvement du jour >= {(1.0, 1.5, 2.0, 2.5, 3.0)[row[2]]} e.-t. ({g}), "
                f"{'suivre' if row[3] == 0 else 'contrer'} {(1, 2, 3, 5, 10)[row[5]]} s., {filt[row[6]]}")
    if f == 5:
        e = int(row[3])
        so = f"sortie apres {(5, 10, 20, 40)[e]} s." if e < 4 else f"sortie clot. < moy. {(10, 20, 50)[e - 4]}"
        return f"{nom} cassure des {CAS_N[row[2]]} seances, {so}, {sens[row[4]]}"
    if f == 6:
        q = f"signe du rendement sur {RET_L[2 + row[3]]} s." if row[2] == 0 else \
            f"moyenne {('5/20', '10/50', '20/100', '50/200')[row[3]]}"
        return f"{nom} tendance : {q}, {sens[row[4]]}"
    if f == 7:
        typ, val = int(row[2]), int(row[3])
        if typ == 0:
            q = ("lundi", "mardi", "mercredi", "jeudi", "vendredi")[val]
        elif typ == 1:
            a, n = val // 8 - 5, val % 8 + 1
            q = f"changement de mois, seances {a} a {a + n - 1} (0 = 1re du mois)"
        elif typ == 2:
            q = "veille de ferie"
        elif typ == 3:
            q = "semaine de l'echeance des options"
        elif typ == 4:
            q = "semaine apres l'echeance des options"
        else:
            q = f"mois {val}"
        return f"{nom} calendrier : {q}, {'achat' if row[4] == 0 else 'vente'}"
    if f == 8:
        return (f"{nom} volatilite 20 s. {'sous' if row[2] == 0 else 'au-dessus de'} sa mediane, "
                f"{'achat' if row[3] == 0 else 'vente'}{', filtre 200' if row[4] else ''}")
    g = ("hausse ou baisse", "hausse seule", "baisse seule")[row[6]]
    return (f"{nom} si {RACINES[row[2]]} a bouge de >= {(0, 1, 2)[row[4]]} e.-t. sur {(1, 2, 5, 10, 20)[row[3]]} s. "
            f"jusqu'a la veille ({g}) : {'suivre' if row[5] == 0 else 'contrer'} {(1, 2, 5)[row[7]]} s.")


# ----------------------------------------------------------------------------- tri

def eligibles(S):
    t, corr = resumer(S)
    positives = (S[:, 10:13] > 0).sum(axis=1)
    ok = (S[:, 3] >= MIN_TRADES) & (positives >= 2) & (np.abs(corr) <= CORR_BOT_MAX)
    return ok, t, corr


def grappes(P, S, ok, t, I, D, PP, COTE, per, n_max=N_CANDIDATES):
    """Les n_max meilleures eligibles par t, sans deux candidates correlees a plus de 0,5 (gain quotidien de l'exploration)."""
    ordre = np.argsort(-np.where(ok, t, -np.inf))
    pris, series = [], []
    fen = per >= 0
    for i in ordre:
        if not ok[i] or len(pris) >= n_max:
            break
        x = gains(pos_de(P[i], I, D), int(P[i, 1]), D["r"], PP, COTE, D["chg"])[fen]
        if all(abs(np.corrcoef(x, y)[0, 1]) <= CORR_GRAPPE_MAX for y in series):
            pris.append(int(i))
            series.append(x)
    return pris


def exploration():
    t0 = time.time()
    D = charger(FIN_EXPLORATION)
    jours = D["jours"]
    assert jours[-1] <= pd.Timestamp(FIN_EXPLORATION)
    I = indicateurs(D)
    PP, COTE = dollars(D)
    per = periodes(jours)
    bot, bm = bot_quotidien(jours)
    fen = per >= 0
    ecart = {k: float(np.std((D["r"][m] * PP[m])[fen & ~np.isnan(D["prix"][m])])) for m, k in enumerate(RACINES)}
    tradables = [m for m, k in enumerate(RACINES) if ecart[k] <= ECART_MAX]
    P = grille(tradables)
    print(f"{len(RACINES)} marches, {len(tradables)} tradables, {len(P)} strategies ; {len(jours)} seances "
          f"({jours[0].date()} - {jours[-1].date()}) ; chargement {time.time() - t0:.0f} s", flush=True)
    S = tout_mesurer(P, *args(I, D, PP, COTE), per, bot, bm)
    ok, t, corr = eligibles(S)
    pris = grappes(P, S, ok, t, I, D, PP, COTE, per)
    print(f"vraies donnees : {ok.sum()} eligibles, meilleur t {t[ok].max():.2f} ({time.time() - t0:.0f} s)", flush=True)
    bruits = []
    for g in range(N_BRUITS):
        B, PPb, COTEb = bruiter(D, 1000 + g)
        Ib = indicateurs(B)
        Sb = tout_mesurer(P, *args(Ib, B, PPb, COTEb), per, bot, bm)
        okb, tb, corrb = eligibles(Sb)
        prisb = grappes(P, Sb, okb, tb, Ib, B, PPb, COTEb, per)
        bruits.append({"graine": 1000 + g, "t": tb[okb], "fam": P[okb, 0], "pris": prisb,
                       "pris_t": [float(tb[i]) for i in prisb], "eligibles": int(okb.sum())})
        print(f"bruit {g + 1}/{N_BRUITS} : {okb.sum()} eligibles, meilleur t {tb[okb].max():.2f} ({time.time() - t0:.0f} s)",
              flush=True)

    def fdr(seuil):
        reel = int((t[ok] >= seuil).sum())
        bruit = float(np.mean([(b["t"] >= seuil).sum() for b in bruits]))
        return reel, bruit, (bruit / reel if reel else float("inf"))

    L = [f"Machine 4, exploration 2011-2022 : {len(P)} strategies sur {len(tradables)} marches tradables "
         f"(40 sources pour la famille croisee), {len(jours)} seances jusqu'au {jours[-1].date()}", "",
         "Marches tradables (ecart-type du gain journalier d'un contrat, 2011-2022) : " +
         ", ".join(f"{RACINES[m]} {ecart[RACINES[m]]:.0f} $" for m in tradables),
         "Ecartes (> 400 $) : " + ", ".join(f"{k} {v:.0f} $" for k, v in ecart.items() if v > ECART_MAX), "",
         "Strategies par famille : eligibles reelles / eligibles sur bruit (moyenne des 8) / meilleur t reel / meilleur t bruit (moyenne)"]
    for f, nom in FAMILLES.items():
        sel = P[:, 0] == f
        e_r = int((ok & sel).sum())
        e_b = np.mean([(b["fam"] == f).sum() for b in bruits])
        m_r = float(t[ok & sel].max()) if e_r else float("nan")
        m_b = np.mean([b["t"][b["fam"] == f].max() if (b["fam"] == f).any() else np.nan for b in bruits])
        L.append(f"- {f} {nom} : {int(sel.sum())} strategies ; {e_r} / {e_b:.0f} ; {m_r:.2f} / {m_b:.2f}")
    L += ["", "Taux de fausses decouvertes : seuil t | eligibles reelles au-dessus | sur bruit (moyenne des 8) | part attendue de fausses"]
    for s_ in SEUILS_T:
        a, b, q = fdr(s_)
        L.append(f"- t >= {s_:.1f} : {a} | {b:.1f} | {min(q, 9.99):.0%}" + ("" if a else " (aucune reelle)"))
    L += ["", f"Meilleur t sur chaque bruit : " + ", ".join(f"{max(b['t']):.2f}" for b in bruits), "",
          "10 candidates (t decroissant, correlation entre elles <= 0,5) :"]
    cands = []
    for i in pris:
        a, b, q = fdr(t[i])
        x = S[i]
        ans = len(jours[fen]) / 252
        cands.append({"row": P[i].tolist(), "desc": decrire(P[i]), "t": float(t[i]), "corr_bot": float(corr[i]),
                      "trades": int(x[3]), "par_an": float(x[1] / ans), "periodes": [float(v) for v in x[10:13]],
                      "fdr": float(min(q, 9.99))})
        L.append(f"- t {t[i]:.2f} | {decrire(P[i])} | {int(x[3])} trades | {x[1] / ans:+,.0f} $/an | periodes "
                 + " / ".join(f"{v:+,.0f}" for v in x[10:13]) + f" | corr. bot {corr[i]:+.2f} | fausses attendues a ce t : {min(q, 9.99):.0%}")
    placebos = [{"graine": b["graine"], "row": P[i].tolist(), "desc": decrire(P[i]), "t": tt}
                for b in bruits for i, tt in zip(b["pris"], b["pris_t"])]
    L += ["", f"Duree : {time.time() - t0:.0f} s"]
    (ICI / "exploration4.txt").write_text("\n".join(L) + "\n")
    (ICI / "candidates4.json").write_text(json.dumps({"tradables": [RACINES[m] for m in tradables], "n_strategies": len(P),
                                                       "candidates": cands, "placebos": placebos}, indent=1))
    print("\n".join(L))


def coffre():
    c = json.loads((ICI / "candidates4.json").read_text())
    D = charger("2100-01-01")
    jours = D["jours"]
    I = indicateurs(D)
    PP, COTE = dollars(D)
    per = periodes(jours, coffre=True)
    bot, bm = bot_quotidien(jours)
    ans = (per >= 0).sum() / 252

    def juger(items):
        P = np.array([x["row"] for x in items], np.int64)
        S = tout_mesurer(P, *args(I, D, PP, COTE), per, bot, bm)
        t, corr = resumer(S)
        res = []
        for x, s, tt, cc in zip(items, S, t, corr):
            pos_an = int((s[10:14] > 0).sum())
            # placebos : pas de taux de fausses decouvertes propre, seul le coffre compte (palier le plus facile a passer)
            retenue = tt >= T_RETENUE and pos_an >= 3 and x.get("fdr", 0.0) <= FDR_MAX
            inter = tt >= T_INTERESSANTE and pos_an >= 3
            res.append(dict(x, coffre_t=float(tt), coffre_corr_bot=float(cc), coffre_par_an=float(s[1] / ans),
                            coffre_annees=[float(v) for v in s[10:14]], coffre_trades=int(s[3]),
                            palier="retenue" if retenue else "interessante" if inter else "rejetee"))
        return res

    reel, plac = juger(c["candidates"]), juger(c["placebos"])
    L = [f"Machine 4, coffre {DEBUT_COFFRE} - {jours[-1].date()} (ouvert une fois) : 10 candidates et {len(plac)} placebos", "",
         "Candidates : t exploration | t coffre | $/an au coffre | 2023 / 2024 / 2025 / 2026 | corr. bot | palier"]
    for x in reel:
        L.append(f"- {x['desc']} | {x['t']:.2f} | {x['coffre_t']:+.2f} | {x['coffre_par_an']:+,.0f} | "
                 + " / ".join(f"{v:+,.0f}" for v in x["coffre_annees"]) + f" | {x['coffre_corr_bot']:+.2f} | {x['palier'].upper()}")
    for p_ in ("retenue", "interessante"):
        n_r = sum(x["palier"] == p_ or (p_ == "interessante" and x["palier"] == "retenue") for x in reel)
        n_p = sum(x["palier"] == p_ or (p_ == "interessante" and x["palier"] == "retenue") for x in plac)
        L.append(f"Palier {p_} ou mieux : {n_r} sur 10 candidates ; {n_p} sur {len(plac)} placebos ({n_p / len(plac):.0%}),"
                 f" soit {10 * n_p / len(plac):.1f} attendus sur 10 sans aucune information")
    L += ["", "Placebos (regles choisies sur bruit, jugees sur le vrai coffre) : t coffre moyen "
          f"{np.mean([x['coffre_t'] for x in plac]):+.2f}, mediane {np.median([x['coffre_t'] for x in plac]):+.2f}"]
    (ICI / "coffre4.txt").write_text("\n".join(L) + "\n")
    (ICI / "coffre4.json").write_text(json.dumps({"candidates": reel, "placebos": plac}, indent=1))
    print("\n".join(L))


if __name__ == "__main__":
    {"exploration": exploration, "coffre": coffre}[sys.argv[1]]()
