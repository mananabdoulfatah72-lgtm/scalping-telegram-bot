#!/usr/bin/env python3
"""Moteur de la zone V1 (zone/robot.py zone_de_bruit) avec les variantes de entree_tardive/README.md : H1, E1, E2, S1,
L1, et R, RL pour information. Meme logique que Moteur.cs (Zone, ZoneDecision, SortieZone) : le chemin "virtuel" est
le chemin sans filtre de la variante ; un trade ecarte (delta contre) ou non pris (L1) reste virtuel jusqu'a sa sortie
et bloque les nouvelles entrees. Decision a la minute m : uniquement des donnees jusqu'a la cloture de la minute m.

Usage : preparer(barres) -> tableaux par seance ; jouer(...) par seance et par variante."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ZONE = Path(__file__).resolve().parent.parent / "zone"
sys.path.insert(0, str(ZONE))
sys.dont_write_bytecode = True          # pas de __pycache__ dans zone/
import robot as RB  # noqa: E402  (import sans effet de bord : constantes et fonctions, main() seulement sous __main__)

N, PAS, COUT, JOURS_MOYENNE = RB.N, RB.PAS, RB.COUT, RB.JOURS_MOYENNE
MOMENTS = set(range(PAS, N, PAS))            # 30, 60, ..., 360
DERNIERE_ENTREE = 360

# entree : "moments" (contrôles de 30 min) ou "minutes" (chaque fin de minute de 30 a 360)
# sortie : "moments" (contrôles + 16 h) ou "minutes" (chaque fin de minute apres l'entree, jusqu'a 388, + 16 h)
# ligne : l'entree demande un prix au-dela de la ligne de sortie (E2)
# dep_max : depassement maximal a l'entree (L1) ; relance / relance_dep_max : R et RL
VARIANTES = {
    "H1": dict(entree="moments", sortie="moments", ligne=False, dep_max=None, relance=False, relance_dep_max=None),
    "E1": dict(entree="minutes", sortie="moments", ligne=False, dep_max=None, relance=False, relance_dep_max=None),
    "E2": dict(entree="minutes", sortie="minutes", ligne=True, dep_max=None, relance=False, relance_dep_max=None),
    "S1": dict(entree="moments", sortie="minutes", ligne=False, dep_max=None, relance=False, relance_dep_max=None),
    "L1": dict(entree="moments", sortie="moments", ligne=False, dep_max=1.0, relance=False, relance_dep_max=None),
    "R": dict(entree="moments", sortie="moments", ligne=False, dep_max=None, relance=True, relance_dep_max=None),
    "RL": dict(entree="moments", sortie="moments", ligne=False, dep_max=None, relance=True, relance_dep_max=1.0),
}


def preparer(d):
    """Tableaux de la zone, calcules exactement comme robot.py zone_de_bruit (memes fonctions et memes lignes)."""
    jours, O, H, L, C, P, V, echeance = RB.tableaux(d)
    ok = RB.seances_completes(P)
    ouverture = O[:, 0]
    prec = RB.precedente(ok, np.cumsum(echeance))
    veille = np.where(prec >= 0, C[np.maximum(prec, 0), N - 1], np.nan)
    mouvement = np.abs(C / ouverture[:, None] - 1)
    sigma = np.full_like(mouvement, np.nan)
    sigma[ok] = pd.DataFrame(mouvement[ok]).rolling(JOURS_MOYENNE, min_periods=JOURS_MOYENNE).mean().shift(1).values
    typique = (H + L + C) / 3
    cumv = np.cumsum(V, axis=1)
    prix_moyen = np.where(cumv > 0, np.cumsum(typique * V, axis=1) / np.where(cumv > 0, cumv, 1),
                          np.cumsum(typique, axis=1) / np.arange(1, N + 1))
    haut_ref, bas_ref = np.fmax(ouverture, veille), np.fmin(ouverture, veille)
    jouables = np.where(ok & ~np.isnan(veille) & ~np.isnan(sigma[:, PAS]))[0]
    return dict(jours=jours, H=H, L=L, C=C, sigma=sigma, vwap=prix_moyen, haut_ref=haut_ref, bas_ref=bas_ref,
                jouables=jouables)


def delta_30(par_minute):
    """Delta des 30 minutes qui finissent a chaque minute m (minutes max(0, m-29)..m), comme Moteur.cs Delta."""
    c = np.r_[0.0, np.cumsum(par_minute)]
    m = np.arange(N)
    return c[m + 1] - c[np.maximum(0, m - 29)]


def jouer(jour, H, L, C, sigma, vwap, href, bref, delta30, var, nom):
    """Une seance, une variante. H, L, C, sigma, vwap : listes de 390 valeurs ; delta30 : liste ou None (pas de filtre).
    Renvoie (trades, pire_net, pire_brut) : chaque trade du chemin virtuel (garde = tenu ou non), et le plus bas de la
    journee (realise + latent aux plus bas / plus hauts des minutes), net (1,5 point compte a l'entree) et brut."""
    v = VARIANTES[var]
    e_min = v["entree"] == "minutes"
    s_min = v["sortie"] == "minutes"
    trades = []
    virt = tenu = 0
    t = None                       # trade virtuel en cours (dict)
    e_tenu = 0.0
    real = real_b = 0.0            # realise net, realise brut
    pire = pire_b = 0.0
    creux = 0.0                    # pire excursion du trade tenu (points bruts)

    def depasse(sens, p, s):
        return (p - href * (1 + s)) / (href * s) if sens > 0 else (bref * (1 - s) - p) / (bref * s)

    def sortir(m, p):
        nonlocal virt, tenu, real, real_b, t
        t["minute_sortie"], t["prix_sortie"] = m, p
        if tenu:
            brut = tenu * (p - e_tenu)
            real += brut - COUT
            real_b += brut
            t["points"] = brut - COUT
            t["pire_excursion"] = min(creux, 0.0)
        else:
            t["points"] = t["sens"] * (p - t["prix_entree"]) - COUT     # gain du virtuel (information)
            t["pire_excursion"] = np.nan
        trades.append(t)
        t = None
        virt = tenu = 0

    for m in range(PAS, N):
        if tenu:                                   # minute m entiere en position (entree avant m)
            ex = (L[m] - e_tenu) if tenu > 0 else (e_tenu - H[m])
            if ex < creux:
                creux = ex
            if real + ex - COUT < pire:
                pire = real + ex - COUT
            if real_b + ex < pire_b:
                pire_b = real_b + ex
        p = C[m]
        if m == N - 1:
            if virt:
                sortir(m, p)
            break
        moment = m in MOMENTS
        s = sigma[m]
        ub, lb = href * (1 + s), bref * (1 - s)
        # 1. sortie (puis relance) aux minutes de contrôle de sortie de la variante
        if virt and (s_min or moment):
            vw = vwap[m]
            if (virt > 0 and p <= max(ub, vw)) or (virt < 0 and p >= min(lb, vw)):
                sortir(m, p)
            elif v["relance"] and delta30 is not None and not tenu:
                dr = delta30[m]
                dep = depasse(virt, p, s)
                if np.sign(dr) == virt and (v["relance_dep_max"] is None or dep <= v["relance_dep_max"]):
                    tenu, e_tenu, creux = virt, p, 0.0
                    t.update(garde=True, relance=True, minute_entree=m, prix_entree=p, depassement_entree=dep,
                             delta30_entree=dr)
                    if real - COUT < pire:
                        pire = real - COUT
        # 2. entree
        if not virt and m <= DERNIERE_ENTREE and (e_min or moment):
            if v["ligne"]:
                vw = vwap[m]
                sens = 1 if p > max(ub, vw) else (-1 if p < min(lb, vw) else 0)
            else:
                sens = 1 if p > ub else (-1 if p < lb else 0)
            if sens:
                dep = depasse(sens, p, s)
                dr = delta30[m] if delta30 is not None else np.nan
                garde = (delta30 is None or np.sign(dr) == sens) and (v["dep_max"] is None or dep <= v["dep_max"])
                virt = sens
                t = dict(jour=jour, variante=nom, minute_signal=m, prix_signal=p, sens=sens, depassement_signal=dep,
                         delta30_signal=dr, garde=bool(garde), relance=False, minute_entree=m, prix_entree=p,
                         depassement_entree=dep, delta30_entree=dr)
                if garde:
                    tenu, e_tenu, creux = sens, p, 0.0
                    if real - COUT < pire:
                        pire = real - COUT
    return trades, pire, pire_b


def jouer_tout(z, var, nom=None, deltas=None, jours_choisis=None):
    """Toutes les seances jouables (ou celles de jours_choisis). deltas : dict jour (Timestamp) -> delta30 (390), ou None
    (pas de filtre). Un jour sans delta dans deltas a un delta nul : trades ecartes (comme Moteur.cs, delta 0)."""
    nom = nom or var
    tout, jours = [], []
    zero = [0.0] * N
    for d in z["jouables"]:
        j = z["jours"][d]
        if jours_choisis is not None and j not in jours_choisis:
            continue
        dl = None
        if deltas is not None:
            x = deltas.get(j)
            dl = list(x) if x is not None else zero
        tr, pire, pire_b = jouer(j, z["H"][d].tolist(), z["L"][d].tolist(), z["C"][d].tolist(), z["sigma"][d].tolist(),
                                 z["vwap"][d].tolist(), float(z["haut_ref"][d]), float(z["bas_ref"][d]), dl, var, nom)
        tout += tr
        g = [x["points"] for x in tr if x["garde"]]
        jours.append(dict(jour=j, points=float(sum(g)), trades=len(g), pire=pire, pire_brut=pire_b))
    colonnes = ["jour", "variante", "sens", "garde", "relance", "minute_signal", "prix_signal", "minute_entree",
                "prix_entree", "minute_sortie", "prix_sortie", "points", "depassement_signal", "depassement_entree",
                "delta30_signal", "delta30_entree", "pire_excursion"]
    return pd.DataFrame(tout, columns=colonnes), pd.DataFrame(jours)
