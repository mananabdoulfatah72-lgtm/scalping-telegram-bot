#!/usr/bin/env python3
"""Donnees communes de intraday50k (README.md) : minutes de seance du NQ (comme protection/), barres d'une heure de la
nuit rattachees a la seance qui suit, et RSI(2) du robot (decision, position voulue)."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
R0 = ICI.parent
os.environ.setdefault("ROBOT_DEBUT_RSI2", "2000-01-01")
os.environ.setdefault("ROBOT_DOSSIER", str(ICI / "_robot"))
sys.path.insert(0, str(R0 / "protection"))
import protection as P  # noqa: E402
import robot_main as RB  # noqa: E402

NB_NUIT = 16                    # barres de 18 h a 8 h (15) + marge
PT = RB.PT                      # $ par point pour 1 MNQ
COTE = 1.0 / PT + 0.25          # points par ordre du RSI(2) : 1 $ + 1 tick
FIN = P.FIN_DONNEES


def charger():
    """Renvoie un dict : jours, O, H, L, C (minutes comblees comme protection/), derniere (indice de la derniere minute),
    contrat (par seance), Z (trades de zone), dec, voulu, ouvert, et la nuit : NO, NH, NL, NC (barres d'une heure de la
    nuit qui precede chaque seance, meme contrat seulement), nn (nombre de barres), n18 (la premiere est celle de 18 h)."""
    d = pd.read_csv(R0 / "intraday/donnees/nasdaq100_1min.csv.gz")
    d = d[d["t"].str[:10] <= FIN]
    jours, _, _, _, _, pres, _, _ = RB.tableaux(d)
    derniere = RB.N - 1 - np.argmax(pres[:, ::-1], axis=1)
    contrat = d.groupby(pd.to_datetime(d["t"].str[:10]))["contrat"].last().reindex(jours).to_numpy()
    jours2, O, H, L, C, Z, dec, voulu, ouvert = P.donnees()
    assert (jours2 == jours).all()
    h = pd.read_csv(R0 / "nuit/donnees/nasdaq100_1h.csv.gz")
    t = pd.to_datetime(h["t"])
    j = pd.DatetimeIndex(jours)
    k = np.searchsorted(j + pd.Timedelta(hours=9), t, side="right")          # premiere seance dont 9 h est apres t
    ok = (k >= 1) & (k < len(j))
    kk = np.clip(k, 1, len(j) - 1)
    ok &= t.to_numpy() >= (j[kk - 1] + pd.Timedelta(hours=18)).to_numpy()   # apres 18 h le soir de la seance d'avant
    ok &= h["contrat"].to_numpy() == contrat[kk]                           # meme contrat que la seance qui suit
    nj = len(j)
    NO, NH, NL, NC = (np.full((nj, NB_NUIT), np.nan) for _ in range(4))
    nn = np.zeros(nj, np.int64)
    n18 = np.zeros(nj, bool)
    hh = h[ok].assign(k=kk[ok], heure=t[ok].dt.hour.to_numpy())
    for kd, g in hh.groupby("k", sort=True):
        g = g.iloc[:NB_NUIT]
        n = len(g)
        NO[kd, :n], NH[kd, :n], NL[kd, :n], NC[kd, :n] = (g[c].to_numpy() for c in "ohlc")
        nn[kd] = n
        n18[kd] = g["heure"].iloc[0] == 18
    return {"jours": j, "O": O, "H": H, "L": L, "C": C, "derniere": derniere, "contrat": contrat, "Z": Z, "dec": dec,
            "voulu": voulu, "ouvert": ouvert, "NO": NO, "NH": NH, "NL": NL, "NC": NC, "nn": nn, "n18": n18}


def rsi2_entre_deux(D):
    """RSI(2) entre deux clotures (README.md, partie 1) et original, seance par seance, pour 1 MNQ.
    Renvoie un DataFrame : gain_v, rend_v, nuit_pts, jour_pts, tenu_v (variante) ; gain_o, rend_o (original, compte a la
    seance de chaque decision, comme le robot)."""
    O, C, dec, voulu, der = D["O"], D["C"], D["dec"], D["voulu"], D["derniere"]
    NO, nn = D["NO"], D["nn"]
    nj = len(D["jours"])
    gain_v, rend_v, nuit, jour_, tenu_v = (np.zeros(nj) for _ in range(5))
    gain_o, rend_o = np.zeros(nj), np.zeros(nj)
    veut = 0                                   # position voulue apres la derniere decision
    px_prec, tenu_o = np.nan, 0
    for d in range(nj):
        # --- variante : position prise la nuit qui precede la seance d si la regle la voulait a la derniere decision
        if veut == 1:
            if nn[d] > 0:
                e = NO[d, 0]
            else:
                e = O[d, 0]                     # pas de barre de nuit : achat a 9 h 30
            if dec[d] >= 0 and voulu[d] == 0:
                s = O[d, dec[d]]                # vendue a la decision de 15 h 50
            else:
                s = C[d, der[d]]                # fermee a la derniere minute de la seance
            pts = s - e
            gain_v[d] = (pts - 2 * COTE) * PT
            rend_v[d] = pts / e - 2 * COTE / e
            nuit[d] = O[d, 0] - e
            jour_[d] = s - O[d, 0]
            tenu_v[d] = 1
        # --- original : de decision en decision, au prix d'ouverture de la minute de decision
        if dec[d] >= 0:
            px = O[d, dec[d]]
            chg = abs(voulu[d] - tenu_o)
            if tenu_o == 1:
                gain_o[d] = (px - px_prec - chg * COTE) * PT
                rend_o[d] = px / px_prec - 1 - chg * COTE / px
            else:
                gain_o[d] = -chg * COTE * PT
                rend_o[d] = -chg * COTE / px
            tenu_o, px_prec = voulu[d], px
            veut = voulu[d]
    return pd.DataFrame({"gain_v": gain_v, "rend_v": rend_v, "nuit_pts": nuit, "jour_pts": jour_, "tenu_v": tenu_v,
                         "gain_o": gain_o, "rend_o": rend_o}, index=D["jours"])


def t_stat(x):
    x = np.asarray(x, float)
    s = x.std(ddof=1)
    return 0.0 if s == 0 else x.mean() / s * np.sqrt(len(x))
