#!/usr/bin/env python3
"""RSI(2) sans week-end (README.md) : memes signaux que le RSI(2) du tournoi 8, mais la position tenue a la decision de
la derniere seance de la semaine est fermee a cette decision (15 h 50) et rouverte a l'ouverture de 9 h 30 de la seance
suivante. Utilisable si t >= 2 sur les rendements nets quotidiens et au moins la moitie des dollars de l'original.
Ecrit sans_weekend.txt. Lancer depuis ce dossier : python3 sans_weekend.py"""
from pathlib import Path

import numpy as np
import pandas as pd

import tournoi8 as T

ICI = Path(__file__).resolve().parent
COFFRE = "2023-01-01"


def ouvertures(s):
    """Ouverture de la premiere minute (9 h 30) de chaque seance de s."""
    d = pd.read_csv(T.MARCHES["NQ"][0], usecols=["t", "o"])
    d = d[d["t"].str[11:16] == "09:30"]
    o = pd.Series(d["o"].to_numpy(), index=pd.to_datetime(d["t"].str[:10]))
    return o.reindex(pd.DatetimeIndex(s["date"])).to_numpy()


def journaux(s, pos, O):
    """Rendement net et $ net (1 MNQ) par seance, pour l'original et pour la variante, et nombre de vendredis fermes."""
    P = s["P"].to_numpy()
    pt, cote = s.attrs["pt"], s.attrs["cote"]
    sem = pd.DatetimeIndex(s["date"]).to_period("W-SUN").to_numpy()
    fin_sem = np.r_[sem[1:] != sem[:-1], False]                   # la seance suivante est dans une autre semaine
    avant = np.r_[0, pos[:-1]].astype(float)
    chg = np.abs(pos.astype(float) - avant)
    pts = np.r_[0.0, P[1:] - P[:-1]]
    dol = (avant * pts - chg * cote) * pt
    rend = avant * np.r_[0.0, P[1:] / P[:-1] - 1] - chg * cote / P
    # variante : de t (fin de semaine, position tenue) a t+1, on ne garde que ouverture -> decision de t+1
    coupe = np.r_[False, (pos[:-1] == 1) & fin_sem[:-1]]          # coupe[t+1] : le segment t -> t+1 passe le week-end
    if np.isnan(O[coupe]).any():
        raise SystemExit(f"ouverture de 9 h 30 manquante pour {int(np.isnan(O[coupe]).sum())} seances")
    pts_v = np.where(coupe, P - O, pts)
    dol_v = (avant * pts_v - chg * cote) * pt - coupe * 2 * cote * pt
    base = np.where(coupe, O, np.r_[P[0], P[:-1]])
    rend_v = avant * np.where(coupe, P / O - 1, np.r_[0.0, P[1:] / P[:-1] - 1]) - chg * cote / P - coupe * 2 * cote / base
    return rend, dol, rend_v, dol_v, coupe


def main():
    s = T.charger("NQ", jusqu_au="2026-12-31")
    pos = T.positions(s, 0)
    O = ouvertures(s)
    rend, dol, rend_v, dol_v, coupe = journaux(s, pos, O)
    dates = pd.DatetimeIndex(s["date"])
    debut = dates[np.argmax(pos)]
    garde = dates >= debut                                         # a partir du premier signal (moyenne de 200 seances)
    L = [f"RSI(2) sans week-end, NQ 1 MNQ, du {debut.date()} au {dates[-1].date()}", ""]
    res = {}
    for nom, m in (("toute la periode", garde), ("coffre 2023-2026", dates >= COFFRE)):
        a, b = dol[m].sum(), dol_v[m].sum()
        ta, tb = T.t_stat(rend[m]), T.t_stat(rend_v[m])
        res[nom] = (ta, tb, a, b)
        L += [f"{nom} : original t {ta:+.2f}, {a:+,.0f} $ ; sans week-end t {tb:+.2f}, {b:+,.0f} $"
              f" ({b / a:.0%} de l'original) ; vendredis fermes {int(coupe[m].sum())}"]
    ta, tb, a, b = res["toute la periode"]
    ok = tb >= T.T_MIN and b >= 0.5 * a
    L += ["", f"-> {'UTILISABLE' if ok else 'PAS UTILISABLE'} (t >= {T.T_MIN:.0f} : {'oui' if tb >= T.T_MIN else 'non'} ;"
          f" au moins la moitie des dollars : {'oui' if b >= 0.5 * a else 'non'})", "",
          "Annee par annee ($ pour 1 MNQ) : annee | original | sans week-end | vendredis fermes"]
    an = dates.year
    for y in sorted(set(an[garde])):
        m = garde & (an == y)
        L.append(f"{y} | {dol[m].sum():+,.0f} | {dol_v[m].sum():+,.0f} | {int(coupe[m].sum())}")
    gap = (s["P"].to_numpy() - O)[coupe]
    perdu = (np.r_[0.0, s["P"].to_numpy()[1:] - s["P"].to_numpy()[:-1]] - (s["P"].to_numpy() - O))[coupe]
    L += ["", f"Week-ends passes en position : {int(coupe.sum())} ; mouvement du vendredi 15 h 50 au lundi 9 h 30 :"
          f" moyenne {perdu.mean():+.1f} pt, total {perdu.sum():+,.0f} pt ; journee du lundi gardee : moyenne {gap.mean():+.1f} pt"]
    (ICI / "sans_weekend.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
