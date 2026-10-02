#!/usr/bin/env python3
"""Tournoi 8 (README.md) : 5 strategies de plusieurs jours sur NQ et ES, exploration 2011-2022 seulement.

Une decision par seance, 10 minutes avant la fin (15 h 50 un jour normal) : indicateurs sur la cloture de la minute
d'avant, execution a l'ouverture de la minute de decision. Position fermee a la derniere decision d'un contrat (pas de
rendement a cheval sur deux echeances). Controle : 1 000 placements au hasard des memes trades (memes durees).

Ecrit exploration8.txt, exploration8.csv et survivants8.json. Lancer depuis ce dossier : python3 tournoi8.py
Le coffre (2023-2026) est lu seulement par coffre8.py."""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

ICI = Path(__file__).resolve().parent
R = ICI.parent
FIN_EXPLORATION = "2022-12-31"
FRAIS_ORDRE = 1.0
# marche : (fichier minutes, $ par point du micro, tick, debut de l'exploration)
MARCHES = {
    "NQ": (R / "intraday/donnees/nasdaq100_1min.csv.gz", 2.0, 0.25, "2011-01-01"),
    "ES": (R / "intraday/donnees/sp500_1min.csv.gz", 5.0, 0.25, "2011-01-01"),
    "RTY": (R / "zone_multi/donnees/russell_1min.csv.gz", 5.0, 0.10, "2016-01-01"),
    "YM": (R / "zone_multi/donnees/dow_1min.csv.gz", 0.5, 1.0, "2016-01-01"),
}
DECISION = ("NQ", "ES")            # marches du tri ; RTY et YM : robustesse, a titre descriptif
STRATEGIES = ["RSI(2)", "Double 7", "IBS", "Rebond de 5 jours", "Veille de jour ferie"]
N_HASARD, T_MIN, PART_HASARD = 1000, 2.0, 0.95


# ----------------------------------------------------------------------------- calendrier
def feries(annees):
    """Jours feries de la Bourse de New York (README.md), avec leurs reports."""
    from pandas.tseries.holiday import GoodFriday
    out = set()
    for a in annees:
        def nieme(mois, jour_sem, n):            # n-ieme jour_sem (0 = lundi) du mois ; n = -1 : le dernier
            j = pd.date_range(f"{a}-{mois:02d}-01", periods=31, freq="D")
            j = j[(j.month == mois) & (j.dayofweek == jour_sem)]
            return j[n]

        def reporte(d, samedi_vendredi=True):
            if d.dayofweek == 6:
                return d + pd.Timedelta(days=1)
            if d.dayofweek == 5:
                return d - pd.Timedelta(days=1) if samedi_vendredi else None
            return d
        jours = [reporte(pd.Timestamp(f"{a}-01-01"), samedi_vendredi=False), nieme(1, 0, 2), nieme(2, 0, 2),
                 GoodFriday.dates(f"{a}-01-01", f"{a}-12-31")[0], nieme(5, 0, -1), reporte(pd.Timestamp(f"{a}-07-04")),
                 nieme(9, 0, 0), nieme(11, 3, 3), reporte(pd.Timestamp(f"{a}-12-25"))]
        if a >= 2022:
            jours.append(reporte(pd.Timestamp(f"{a}-06-19")))
        out |= {d.normalize() for d in jours if d is not None}
    return out


# ----------------------------------------------------------------------------- donnees
def charger(nom, jusqu_au=FIN_EXPLORATION):
    """Une ligne par seance : date, contrat, prix d'execution P (ouverture de la minute de decision), cloture C,
    plus haut H et plus bas L depuis 9 h 30 jusqu'a la minute d'avant. Les lignes apres `jusqu_au` ne sont pas lues."""
    fichier, pt, tick, debut = MARCHES[nom]
    d = pd.read_csv(fichier)
    jour = d["t"].str[:10]
    d = d[(jour >= debut) & (jour <= jusqu_au)]
    t = pd.to_datetime(d["t"])
    m = (t.dt.hour * 60 + t.dt.minute - 570).to_numpy()
    garde = (m >= 0) & (m < 390)
    d, t, m = d[garde], t[garde], m[garde]
    jours_d = t.dt.normalize().to_numpy()
    jours = np.unique(jours_d)
    ij = np.searchsorted(jours, jours_d)
    tab = {k: np.full((len(jours), 390), np.nan) for k in "ohlc"}
    for k in "ohlc":
        tab[k][ij, m] = d[k].to_numpy()
    present = ~np.isnan(tab["c"])
    contrat = pd.Series(d["contrat"].to_numpy()).groupby(ij).last().reindex(range(len(jours))).to_numpy()
    cf = pd.DataFrame(tab["c"]).ffill(axis=1).to_numpy()
    derniere = 389 - np.argmax(present[:, ::-1], axis=1)
    dec = derniere - 9
    ferie = pd.DatetimeIndex(jours).normalize().isin(list(feries(range(2010, 2027))))
    ok = (present.sum(axis=1) >= 60) & present[:, 0] & (dec >= 2) & ~ferie
    lignes = np.arange(len(jours))
    P = np.where(present[lignes, dec], tab["o"][lignes, dec], cf[lignes, dec - 1])
    C = cf[lignes, dec - 1]
    masque = np.arange(390)[None, :] < dec[:, None]
    H = np.nanmax(np.where(masque, tab["h"], np.nan), axis=1)
    L = np.nanmin(np.where(masque, tab["l"], np.nan), axis=1)
    s = pd.DataFrame({"date": pd.DatetimeIndex(jours), "contrat": contrat, "P": P, "C": C, "H": H, "L": L})[ok].reset_index(drop=True)
    s.attrs.update(nom=nom, pt=pt, cote=(FRAIS_ORDRE / pt + tick))    # cote : points par ordre (frais + glissement)
    return s


def echeances(s):
    """roule[t] : la seance t+1 est sur un autre contrat (pas de position de t a t+1)."""
    c = s["contrat"].to_numpy()
    return np.r_[c[1:] != c[:-1], True]


def veilles_de_ferie(s):
    """veille[k] : le jour ouvre qui suit la seance k (lundi pour un vendredi) est un jour ferie de la Bourse. Calcule
    avec le seul calendrier, connu d'avance (aucune donnee future)."""
    dates = pd.DatetimeIndex(s["date"])
    suivant = dates + pd.offsets.BDay(1)
    return np.asarray(suivant.normalize().isin(list(feries(range(2010, 2028)))))


# ----------------------------------------------------------------------------- strategies
def rsi_wilder(c, n):
    out = np.full(len(c), np.nan)
    d = np.diff(c)
    g, p = np.maximum(d, 0), np.maximum(-d, 0)
    if len(d) < n:
        return out
    mg, mp = g[:n].mean(), p[:n].mean()
    for i in range(n, len(c)):
        if i > n:
            mg = (mg * (n - 1) + g[i - 1]) / n
            mp = (mp * (n - 1) + p[i - 1]) / n
        out[i] = 100.0 if mp == 0 else 100 - 100 / (1 + mg / mp)
    return out


def positions(s, k):
    """Position (0 ou 1) tenue de la decision t a la decision t+1, pour la strategie k (README.md)."""
    C, H, L = (s[x].to_numpy() for x in "CHL")
    n = len(C)
    roule = echeances(s)
    meme = np.r_[False, ~roule[:-1]]                 # meme[t] : t et t-1 sur le meme contrat
    pos = np.zeros(n, np.int8)
    if k in (0, 1):
        m200 = pd.Series(C).rolling(200).mean().to_numpy()
        if k == 0:
            r2, m5 = rsi_wilder(C, 2), pd.Series(C).rolling(5).mean().to_numpy()
            entree = (C > m200) & (r2 < 10)
            sortie = C > m5
        else:
            entree = (C > m200) & (C <= pd.Series(C).rolling(7).min().to_numpy())
            sortie = C >= pd.Series(C).rolling(7).max().to_numpy()
        tenu = False
        for t in range(n):
            if tenu and sortie[t]:
                tenu = False
            elif not tenu and entree[t]:
                tenu = True
            if roule[t]:                              # fermeture a la derniere decision du contrat
                tenu = False
            pos[t] = tenu
    elif k == 2:
        ibs = (C - L) / np.where(H > L, H - L, np.nan)
        pos[:] = (ibs < 0.2) & ~roule
    elif k == 3:
        r = np.where(meme, C / np.r_[np.nan, C[:-1]] - 1, np.nan)
        reste = 0
        for t in range(n):
            hist = r[max(0, t - 252):t]
            hist = hist[~np.isnan(hist)]
            if not np.isnan(r[t]) and len(hist) >= 200 and r[t] <= np.quantile(hist, 0.10):
                reste = 5
            pos[t] = reste > 0 and not roule[t]
            reste = max(0, reste - 1)
    elif k == 4:
        veille = veilles_de_ferie(s)
        pos[:-1] = veille[1:] & ~roule[:-1]
    return pos


def journal(s, pos):
    """Rendement net (fraction du prix) et $ net (1 micro) realises a chaque seance, et $ de chaque trade."""
    P = s["P"].to_numpy()
    pt, cote = s.attrs["pt"], s.attrs["cote"]
    n = len(P)
    avant = np.r_[0, pos[:-1]].astype(float)          # position tenue de t-1 a t
    var = np.r_[0.0, P[1:] / P[:-1] - 1]
    pts = np.r_[0.0, P[1:] - P[:-1]]
    chg = np.abs(pos.astype(float) - avant)
    rend = avant * var - chg * cote / P
    dol = (avant * pts - chg * cote) * pt
    # trades : suites de positions a 1
    entrees = np.flatnonzero((pos == 1) & (avant == 0))
    sorties = np.flatnonzero((pos == 0) & (avant == 1))
    trades = [((P[b] - P[a]) - 2 * cote) * pt for a, b in zip(entrees, sorties)]
    return rend, dol, np.array(trades), entrees, sorties


def t_stat(x):
    s = x.std()
    return float(x.mean() / s * np.sqrt(len(x))) if s > 0 else 0.0


# ----------------------------------------------------------------------------- hasard des dates
@njit(cache=True)
def placer(durees, interdit, graine):
    """Place les trades (durees en seances) a des departs tires au hasard, sans chevauchement, sans toucher une seance
    interdite (passage d'echeance), avec au moins une seance libre entre deux trades. Renvoie la position."""
    np.random.seed(graine)
    n = interdit.shape[0]
    occ = np.zeros(n, np.bool_)
    ordre = np.random.permutation(durees.shape[0])
    for q in ordre:
        d = durees[q]
        for _ in range(20000):
            a = np.random.randint(1, n - d - 1)
            libre = not occ[a - 1] and not occ[a + d]
            if libre:
                for k in range(a, a + d):
                    if occ[k] or interdit[k]:
                        libre = False
                        break
            if libre:
                for k in range(a, a + d):
                    occ[k] = True
                break
    return occ.astype(np.int8)


def hasard(s, entrees, sorties, rng_graine):
    durees = (sorties - entrees).astype(np.int64)
    interdit = echeances(s)
    ts = np.empty(N_HASARD)
    rates = 0
    for i in range(N_HASARD):
        pos = placer(durees, interdit, rng_graine + i)
        r, _, _, e, _ = journal(s, pos)
        rates += len(e) != len(durees)
        ts[i] = t_stat(r)
    if rates:
        print(f"  (attention : {rates} placements au hasard sur {N_HASARD} n'ont pas pu poser tous les trades)")
    return ts


# ----------------------------------------------------------------------------- mesures
def mesures(rend, dol, trades, pos):
    cum = np.cumsum(dol)
    pic = np.maximum.accumulate(np.r_[0.0, cum])[1:]
    gains, pertes = trades[trades > 0], trades[trades <= 0]
    return {"t": round(t_stat(rend), 3), "sharpe": round(float(rend.mean() / rend.std() * np.sqrt(252)) if rend.std() > 0 else 0.0, 3),
            "dollars_1_micro": round(float(dol.sum()), 1), "perte_max_1_micro": round(float((cum - pic).min()), 1),
            "en_position": round(float(pos.mean()), 3), "trades": int(len(trades)),
            "trades_gagnants": round(float(len(gains) / len(trades)), 3) if len(trades) else 0.0,
            "gain_moyen": round(float(gains.mean()), 1) if len(gains) else 0.0,
            "perte_moyenne": round(float(pertes.mean()), 1) if len(pertes) else 0.0}


def main():
    lignes, sortie = [], []
    survivants = []
    for nom in MARCHES:
        s = charger(nom)
        assert s["date"].max() <= pd.Timestamp(FIN_EXPLORATION), "le coffre ne doit pas etre lu"
        lignes.append(f"{nom} : {len(s)} seances du {s['date'].min().date()} au {s['date'].max().date()},"
                      f" {int(echeances(s)[:-1].sum())} changements d'echeance, frais {2 * s.attrs['cote']:.3g} points par aller-retour")
        for k, strat in enumerate(STRATEGIES):
            pos = positions(s, k)
            rend, dol, trades, entrees, sorties = journal(s, pos)
            x = mesures(rend, dol, trades, pos)
            ts = hasard(s, entrees, sorties, 1000 * (k + 1) + 17 * len(nom))
            x["hasard_part_battue"] = round(float((ts < x["t"]).mean()), 3)
            x["hasard_t_95"] = round(float(np.quantile(ts, 0.95)), 3)
            x["hasard_t_median"] = round(float(np.median(ts)), 3)
            decision = nom in DECISION
            survit = decision and x["t"] >= T_MIN and x["hasard_part_battue"] >= PART_HASARD
            x.update(marche=nom, strategie=strat, tri=decision, survit=survit)
            sortie.append(x)
            if survit:
                survivants.append({"marche": nom, "strategie": k, "nom": strat})
            print(f"{nom:3s} {strat:22s} t {x['t']:+5.2f}  hasard : bat {x['hasard_part_battue']:5.1%} (t 95 % {x['hasard_t_95']:+.2f})"
                  f"  {x['trades']:4d} trades  {x['dollars_1_micro']:+9.0f} $  {'SURVIT' if survit else ''}", flush=True)
    df = pd.DataFrame(sortie)
    df.to_csv(ICI / "exploration8.csv", index=False)
    texte = lignes + ["", "Exploration 2011-2022 (RTY et YM : 2016-2022, a titre descriptif). Survie : t >= 2 et t reel au-dessus de"
                      " 95 % des 1 000 placements au hasard des memes trades.", ""]
    texte.append(f"{'marche':6s} {'strategie':22s} {'t':>6s} {'Sharpe':>6s} {'bat le hasard':>13s} {'t 95% hasard':>12s} {'trades':>6s}"
                 f" {'en pos.':>7s} {'gagnants':>8s} {'gain moy':>8s} {'perte moy':>9s} {'total $':>9s} {'perte max $':>11s}  verdict")
    for x in sortie:
        texte.append(f"{x['marche']:6s} {x['strategie']:22s} {x['t']:+6.2f} {x['sharpe']:+6.2f} {x['hasard_part_battue']:13.1%}"
                     f" {x['hasard_t_95']:+12.2f} {x['trades']:6d} {x['en_position']:7.1%} {x['trades_gagnants']:8.0%}"
                     f" {x['gain_moyen']:+8.0f} {x['perte_moyenne']:+9.0f} {x['dollars_1_micro']:+9.0f} {x['perte_max_1_micro']:+11.0f}  "
                     + ("SURVIT" if x["survit"] else ("elimine" if x["tri"] else "(descriptif)")))
    texte += ["", f"Survivants : {len(survivants)}" + "".join(f"\n  {v['marche']} {v['nom']}" for v in survivants)]
    (ICI / "exploration8.txt").write_text("\n".join(texte) + "\n")
    (ICI / "survivants8.json").write_text(json.dumps(survivants, indent=1, ensure_ascii=False))
    print("\n".join(texte[-(len(survivants) + 1):]))


if __name__ == "__main__":
    main()
