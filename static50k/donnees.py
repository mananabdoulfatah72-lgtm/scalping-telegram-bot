#!/usr/bin/env python3
"""Donnees de static50k (README.md) : minutes de seance du NQ et de l'ES alignees sur les memes seances, trades de zone et
decisions du RSI(2) du robot, et barres d'une heure apres chaque seance (16 h et 17 h, puis la nuit de 18 h a 8 h avant la
seance suivante), sur une grille d'heures commune au NQ et a l'ES."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
R0 = ICI.parent
sys.path.insert(0, str(R0 / "intraday50k"))
import commun as K  # noqa: E402

RB, P = K.RB, K.P
NA = 72                         # barres d'une heure apres une seance, au plus (long week-end avec jour ferie)


def minutes_es(jours):
    """Minutes de l'ES comme celles du NQ (tableaux du robot, minutes absentes comblees), contrat par seance."""
    d = pd.read_csv(R0 / "intraday/donnees/sp500_1min.csv.gz")
    d = d[d["t"].str[:10] <= P.FIN_DONNEES]
    j, O, H, L, C, _, _, _ = RB.tableaux(d)
    assert (j == jours).all()
    O, H, L, C = (pd.DataFrame(a).bfill(axis=1).to_numpy() for a in (O, H, L, C))
    contrat = d.groupby(pd.to_datetime(d["t"].str[:10]))["contrat"].last().reindex(jours).to_numpy()
    return O, H, L, C, contrat


def apres(jours, cn, ce):
    """Barres d'une heure apres chaque seance d : heures de 16 h et 17 h du jour d (meme contrat que la seance d), puis
    toutes les heures a partir de 18 h jusqu'avant 9 h de la seance suivante (meme contrat que la seance suivante).
    Grille commune : une heure presente pour l'un des deux marches seulement garde l'autre immobile (derniere cloture).
    Renvoie AO, AH, AL, AC (NQ), BO, BH, BL, BC (ES) en (seances x NA), na (barres), npost (barres de 16 h - 17 h)."""
    nj = len(jours)
    tabs = []
    for nom, contrat in (("nasdaq100", cn), ("sp500", ce)):
        h = pd.read_csv(R0 / f"nuit/donnees/{nom}_1h.csv.gz")
        t = pd.to_datetime(h["t"])
        k = np.searchsorted(jours + pd.Timedelta(hours=16), t, side="right") - 1    # derniere seance d avec d + 16 h <= t
        ok = (k >= 0) & (k < nj)
        kk = np.clip(k, 0, nj - 1)
        nxt = np.clip(kk + 1, 0, nj - 1)
        post = t.to_numpy() < (jours[kk] + pd.Timedelta(hours=18)).to_numpy()
        ok &= np.where(kk + 1 < nj, t.to_numpy() < (jours[nxt] + pd.Timedelta(hours=9)).to_numpy(), post)
        ok &= np.where(post, h["contrat"].to_numpy() == contrat[kk], h["contrat"].to_numpy() == contrat[nxt])
        tabs.append(h[ok].assign(k=kk[ok], t=t[ok]).set_index(["k", "t"])[["o", "h", "l", "c"]])
    grille = tabs[0].index.union(tabs[1].index).sort_values()
    out = []
    for tab in tabs:
        x = tab.reindex(grille)
        out.append(x)
    gk = grille.get_level_values(0).to_numpy()
    gt = pd.DatetimeIndex(grille.get_level_values(1))
    rang = pd.Series(np.arange(len(gk))).groupby(gk).cumcount().to_numpy()
    assert rang.max() < NA, rang.max()
    na = np.bincount(gk, minlength=nj).astype(np.int64)
    estpost = (gt < pd.DatetimeIndex(jours[gk]) + pd.Timedelta(hours=18))
    npost = np.bincount(gk[estpost], minlength=nj).astype(np.int64)
    # les barres de 16 h - 17 h viennent avant celles de la nuit (grille triee par seance puis par heure)
    return out, gk, rang, na, npost


def remplir(x, gk, rang, nj, depart):
    """Tableaux (seances x NA) ; une heure absente garde la derniere cloture (depart : cloture de la seance)."""
    A = {c: np.full((nj, NA), np.nan) for c in "ohlc"}
    for c in "ohlc":
        A[c][gk, rang] = x[c].to_numpy()
    for d in range(nj):
        prec = depart[d]
        for r in range(NA):
            if np.isnan(A["c"][d, r]):
                A["o"][d, r] = A["h"][d, r] = A["l"][d, r] = A["c"][d, r] = prec
            prec = A["c"][d, r]
    return A["o"], A["h"], A["l"], A["c"]


def charger():
    D = K.charger()
    j = D["jours"]
    nj = len(j)
    EO, EH, EL, EC, ce = minutes_es(j)
    (xn, xe), gk, rang, na, npost = apres(j, D["contrat"], ce)
    der = D["derniere"]
    AO, AH, AL, AC = remplir(xn, gk, rang, nj, D["C"][np.arange(nj), der])
    BO, BH, BL, BC = remplir(xe, gk, rang, nj, EC[np.arange(nj), der])
    roule_es = np.r_[ce[1:] != ce[:-1], False]          # la seance suivante est sur un autre contrat de l'ES
    D.update(EO=EO, EH=EH, EL=EL, EC=EC, contrat_es=ce, roule_es=roule_es, AO=AO, AH=AH, AL=AL, AC=AC, BO=BO, BH=BH,
             BL=BL, BC=BC, na=na, npost=npost)
    return D
