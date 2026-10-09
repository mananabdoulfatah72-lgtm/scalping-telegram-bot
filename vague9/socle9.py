#!/usr/bin/env python3
"""Vague 9 (README.md) : socle. Resultat de chaque trade de zone (1 MNQ et 1 MES, au niveau d'aujourd'hui de son jour),
resultat du RSI(2) de nuit sur 1 MES (A3) par seance, conditions connues avant chaque trade, filtre delta simule, et
mesure rapide de l'objectif sur un 50K (12 mois sans toucher le seuil, avec au moins +6 000 $)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

ICI = Path(__file__).resolve().parent
R0 = ICI.parent
sys.path.insert(0, str(R0 / "vague6"))
sys.path.insert(0, str(R0 / "evolution2"))
sys.path.insert(0, str(R0 / "fonds"))
import vague6 as V6  # noqa: E402

D4, M4, S = V6.D4, V6.M4, V6.S
TIRAGES = 10
UN_AN = 252


def charger():
    V6.W.regler("regles")
    D = D4.charger()
    kN, kE = D4.facteurs_jour(D)
    Z = D["Z"]
    d, me, ms, sens = (Z[k].to_numpy() for k in ("d", "me", "ms", "sens"))
    T = dict(d=d, me=me, ms=ms, sens=sens,
             mnq=sens * (D["C"][d, ms] - D["C"][d, me]) * 2.0 * kN[d] - M4.FRAIS_ZONE,
             mes=sens * (D["EC"][d, ms] - D["EC"][d, me]) * 5.0 * kE[d] - M4.FRAIS_ZONE_ES)
    T["rang"] = pd.Series(np.ones(len(d))).groupby(d).cumsum().to_numpy().astype(int)
    # RSI(2) de nuit sur 1 MES seul (zone coupee), par seance
    bz = D4.base(D, np.zeros(len(d), bool))
    nj = len(D["jours"])
    a3, veut = np.zeros(nj), 0
    for j in range(nj):
        _, c, veut, _, _, _ = M4.seance4(j, 4, veut, 0.0, 0.0, -1e18, 0, 2000.0, 0.0, 0.0, *bz, 2.0 * kN[j], 5.0 * kE[j], 1)
        a3[j] = c
    gardes = S.gardes_simules(D, S.rho_2026())[:TIRAGES]
    return D, T, a3, gardes


def journalier(nj, T, a3, choisi, mes_sinon, garde):
    """Gain de chaque seance : A3 + trades de zone gardes par le filtre delta ; parmi eux, les trades `choisi` en MNQ,
    les autres en MES si mes_sinon, sinon pas pris."""
    pris = garde & choisi
    g = a3 + np.bincount(T["d"][pris], weights=T["mnq"][pris], minlength=nj)
    if mes_sinon:
        p2 = garde & ~choisi
        g = g + np.bincount(T["d"][p2], weights=T["mes"][p2], minlength=nj)
    return g


@njit(cache=True)
def objectif(g, debuts, perte, bloc, cible, duree):
    """Pour chaque debut : 1 si le compte tient `duree` seances sans que le solde de fin de seance touche le plancher
    (perte sous le plus haut de fin de seance, bloque a `bloc`) et finit a au moins `cible` ; 0 sinon. Renvoie aussi
    perdu (1/0) et le gain final."""
    n = debuts.shape[0]
    ok, perdu, fin = np.zeros(n), np.zeros(n), np.zeros(n)
    for i in range(n):
        cash, pic, pl = 0.0, 0.0, -perte
        mort = False
        for k in range(debuts[i], debuts[i] + duree):
            cash += g[k]
            if cash <= pl:
                mort = True
                break
            if cash > pic:
                pic = cash
                pl = min(pic - perte, bloc)
        perdu[i] = 1.0 if mort else 0.0
        fin[i] = cash
        ok[i] = 1.0 if (not mort and cash >= cible) else 0.0
    return ok, perdu, fin


def debuts(D, a, z):
    """Debuts une seance sur cinq de a a z, avec 12 mois de suivi dans les donnees."""
    j = D["jours"]
    nj = len(j)
    dd = np.arange(260, nj - UN_AN)[::5]
    return dd[(j[dd] >= pd.Timestamp(a)) & (j[dd] <= pd.Timestamp(z))].astype(np.int64)


def conditions(D, T, gardes):
    """Conditions binaires par trade, toutes connues avant l'entree (README.md)."""
    import tournoi3 as T3
    import fomc
    j = D["jours"]
    nj = len(j)
    d, sens = T["d"], T["sens"]
    der = D["derniere"]
    O, H, L, C = D["O"], D["H"], D["L"], D["C"]
    cl = D["cl_nq"]
    veille = np.r_[np.nan, cl[:-1]]
    mins = np.arange(H.shape[1])
    hh = np.nanmax(np.where(mins <= der[:, None], H, np.nan), axis=1)
    ll = np.nanmin(np.where(mins <= der[:, None], L, np.nan), axis=1)
    rng = (hh - ll) / cl
    agit = pd.Series(rng).rolling(14).mean().shift(1).to_numpy()            # mouvement moyen des 14 seances d'avant
    q = lambda x, p: T3.quantile_252(x, p)                                   # noqa: E731
    gap = np.abs(O[:, 0] / veille - 1)
    r_veille = np.r_[np.nan, (cl / O[np.arange(nj), 0] - 1)[:-1]]
    Q = T3.lire_quotidien()
    vix = pd.read_csv(R0 / "evolution2" / "donnees" / "vix.csv")
    vix = pd.Series(vix["CLOSE"].astype(float).values, index=pd.to_datetime(vix["DATE"], format="mixed"))
    v = T3.veille(j, vix)
    vr = T3.veille(j, Q["vix_ratio"])
    gx = T3.veille(j, Q["gex"])
    ma50 = pd.Series(cl).rolling(50).mean().shift(1).to_numpy()
    fed = pd.DatetimeIndex(j).isin(fomc.annonces())
    nh = np.nanmax(D["NH"], axis=1)
    nl = np.nanmin(D["NL"], axis=1)
    nuit = (nh - nl) / veille
    nuit_sens = np.sign(O[:, 0] - veille)
    wd = pd.DatetimeIndex(j).weekday
    jour = {
        "seances agitees (tiers haut)": agit > q(agit, 2 / 3),
        "seances pas calmes (hors tiers bas)": agit > q(agit, 1 / 3),
        "grand ecart d'ouverture (tiers haut)": gap > q(gap, 2 / 3),
        "ecart d'ouverture pas petit": gap > q(gap, 1 / 3),
        "veille en hausse": r_veille > 0,
        "veille en baisse": r_veille < 0,
        "VIX haut (tiers haut)": v > q(v, 2 / 3),
        "VIX pas bas": v > q(v, 1 / 3),
        "VIX en deport (>= VIX 3 mois)": vr >= 1,
        "GEX sous sa mediane": gx < q(gx, 0.5),
        "pas un jour de la Fed": ~fed,
        "NQ au-dessus de sa moyenne 50 j": cl_avant(cl) > ma50,
        "NQ sous sa moyenne 50 j": cl_avant(cl) < ma50,
        "pas le lundi": wd != 0,
        "vendredi": wd == 4,
        "nuit agitee (tiers haut)": nuit > q(nuit, 2 / 3),
    }
    out = {k: np.nan_to_num(x.astype(float), nan=0.0).astype(bool)[d] for k, x in jour.items()}
    trade = {
        "1er trade du jour": T["rang"] == 1,
        "achats": sens > 0,
        "ventes": sens < 0,
        "contre la seance de la veille": np.sign(r_veille[d]) == -sens,
        "dans le sens de la veille": np.sign(r_veille[d]) == sens,
        "entree avant 12 h": T["me"] < 150,
        "entree apres 12 h": T["me"] >= 150,
        "dans le sens de la moyenne 50 j": np.sign(cl_avant(cl) - ma50)[d] == sens,
        "contre la moyenne 50 j": np.sign(cl_avant(cl) - ma50)[d] == -sens,
        "dans le sens de l'ecart d'ouverture": nuit_sens[d] == sens,
        "contre l'ecart d'ouverture": nuit_sens[d] == -sens,
    }
    out.update(trade)
    # courbe de la zone elle-meme (filtre delta du tirage compris) : somme des 20 / 60 seances d'avant > 0
    cz = []
    for g in gardes:
        zj = np.bincount(d[g], weights=T["mnq"][g], minlength=nj)
        c20 = pd.Series(zj).rolling(20).sum().shift(1).to_numpy()
        c60 = pd.Series(zj).rolling(60).sum().shift(1).to_numpy()
        cz.append({"zone gagnante sur 20 seances": np.nan_to_num(c20, nan=0.0)[d] > 0,
                   "zone gagnante sur 60 seances": np.nan_to_num(c60, nan=0.0)[d] > 0})
    defini = {"VIX": np.isfinite(v), "GEX": np.isfinite(gx) & np.isfinite(q(gx, 0.5)), "agit": np.isfinite(q(agit, 2 / 3))}
    return out, cz, defini


def cl_avant(cl):
    """Cloture de la veille (connue avant la seance)."""
    return np.r_[np.nan, cl[:-1]]
