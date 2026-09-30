"""Moteur de l'evolution n°2 (README.md) : le moteur de evolution/moteur.py, avec 5 especes de plus (profil de volume
de la veille, murs d'options) et un filtre choisi parmi 9 (volatilite, GEX, VIX, DIX). Memes regles d'execution :
signal a la cloture de la barre j, execution a l'ouverture de j + 1, une position a la fois, stop avant objectif, tout
ferme a 16 h, frais par aller-retour."""
import sys
from pathlib import Path

import numpy as np
from numba import njit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "evolution"))
from moteur import BARRES, CANAL, DERNIERE_ENTREE, MOMENTUM, OUVERTURE, RETOUR, _moy_ecart, charger  # noqa: E402,F401

ZV_RETOUR, ZV_ACCEPT, POC_RETOUR, MUR_REJET, MUR_CASSURE = 4, 5, 6, 7, 8
ESPECES = ["momentum", "retour a la moyenne", "cassure de canal", "range d'ouverture", "retour dans la zone de valeur",
           "acceptation hors zone de valeur", "retour au POC", "rejet des murs d'options", "cassure des murs d'options"]
FILTRES = ["aucun", "jours agites", "jours calmes", "GEX bas", "GEX haut", "VIX en deport", "VIX en contango", "DIX haut", "DIX bas"]


@njit(cache=True)
def simuler2(o, h, l, c, interdit, fok, poc, vah, val, mur_c, mur_p, espece, L, Z, sens, stop, objectif, debut, filtre, cout, pt,
            noter, t_jour, t_entree, t_sortie, t_sens, t_px_e, t_px_s, t_raison):
    """Renvoie (rendement net par seance, $ net par seance pour 1 micro, trades par seance, nombre de trades notes).
    sens : 0 les deux, 1 achat seul, 2 vente seule. filtre : ligne de fok (jours permis), 0 = tous les jours.
    poc, vah, val : profil de volume de la seance precedente ; mur_c, mur_p : call wall et put wall (NaN : absents).
    Si noter : les trades sont ecrits dans les tableaux t_* (raison : 0 stop, 1 objectif, 2 cloture)."""
    n = c.shape[0]
    nj = n // BARRES
    rend = np.zeros(nj)
    dollars = np.zeros(nj)
    ntr = np.zeros(nj, np.int32)
    moy, ect = _moy_ecart(c, L)
    _, sig20 = _moy_ecart(c, 20)
    pos = 0
    entree = 0.0
    px_stop = 0.0
    px_obj = 0.0
    i_entree = 0
    k = 0
    orb_h = 0.0
    orb_l = 0.0
    for i in range(n):
        b = i % BARRES
        d = i // BARRES
        if b == 0:
            orb_h = h[i]
            orb_l = l[i]
        elif b < L and espece == OUVERTURE:
            if h[i] > orb_h:
                orb_h = h[i]
            if l[i] < orb_l:
                orb_l = l[i]
        entre_ici = False
        # 1) entree a l'ouverture de la barre i, sur le signal de la cloture de la barre i - 1 (meme seance)
        if pos == 0 and b >= 1 and b >= debut and b <= DERNIERE_ENTREE and not interdit[d]:
            permis = fok[filtre, d]
            j = i - 1
            s = 0
            if permis and j >= L - 1 and not np.isnan(ect[j]) and ect[j] > 0:
                if espece == MOMENTUM or espece == RETOUR:
                    z = (c[j] - moy[j]) / ect[j]
                    if z > Z:
                        s = 1
                    elif z < -Z:
                        s = -1
                    if espece == RETOUR:
                        s = -s
                elif espece == CANAL and j >= L and not np.isnan(sig20[j]):
                    hh = h[j - L]
                    ll = l[j - L]
                    for m in range(j - L + 1, j):
                        if h[m] > hh:
                            hh = h[m]
                        if l[m] < ll:
                            ll = l[m]
                    if c[j] > hh + Z * sig20[j]:
                        s = 1
                    elif c[j] < ll - Z * sig20[j]:
                        s = -1
            if permis and espece == OUVERTURE and (j % BARRES) >= L - 1 and not np.isnan(sig20[j]):
                if c[j] > orb_h + Z * sig20[j]:
                    s = 1
                elif c[j] < orb_l - Z * sig20[j]:
                    s = -1
            if permis and espece >= ZV_RETOUR and not np.isnan(sig20[j]):
                zs = Z * sig20[j]
                if espece == ZV_RETOUR and not np.isnan(vah[d]):
                    o_jour = o[d * BARRES]
                    if o_jour > vah[d] and c[j] < vah[d] - zs:
                        s = -1
                    elif o_jour < val[d] and c[j] > val[d] + zs:
                        s = 1
                elif espece == ZV_ACCEPT and not np.isnan(vah[d]):
                    if c[j] > vah[d] + zs:
                        s = 1
                    elif c[j] < val[d] - zs:
                        s = -1
                elif espece == POC_RETOUR and not np.isnan(poc[d]) and vah[d] > val[d]:
                    x = (c[j] - poc[d]) / (vah[d] - val[d])
                    if x > Z:
                        s = -1
                    elif x < -Z:
                        s = 1
                elif espece == MUR_REJET:
                    haut = (not np.isnan(mur_c[d])) and h[j] >= mur_c[d] - zs and c[j] < mur_c[d]
                    bas = (not np.isnan(mur_p[d])) and l[j] <= mur_p[d] + zs and c[j] > mur_p[d]
                    if haut and not bas:
                        s = -1
                    elif bas and not haut:
                        s = 1
                elif espece == MUR_CASSURE:
                    if (not np.isnan(mur_c[d])) and c[j] > mur_c[d] + zs:
                        s = 1
                    elif (not np.isnan(mur_p[d])) and c[j] < mur_p[d] - zs:
                        s = -1
            if (sens == 1 and s < 0) or (sens == 2 and s > 0):
                s = 0
            if s != 0:
                pos = s
                entree = o[i]
                px_stop = entree * (1.0 - s * stop)
                px_obj = entree * (1.0 + s * objectif)
                i_entree = i
                entre_ici = True
        # 2) gestion de la position dans la barre i (stop avant objectif, cloture a 16 h)
        if pos != 0:
            sortie = np.nan
            raison = -1
            if pos > 0:
                if (not entre_ici) and o[i] <= px_stop:
                    sortie = o[i]
                    raison = 0
                elif l[i] <= px_stop:
                    sortie = px_stop
                    raison = 0
                elif h[i] >= px_obj:
                    sortie = px_obj
                    raison = 1
            else:
                if (not entre_ici) and o[i] >= px_stop:
                    sortie = o[i]
                    raison = 0
                elif h[i] >= px_stop:
                    sortie = px_stop
                    raison = 0
                elif l[i] <= px_obj:
                    sortie = px_obj
                    raison = 1
            if np.isnan(sortie) and b == BARRES - 1:
                sortie = c[i]
                raison = 2
            if not np.isnan(sortie):
                points = pos * (sortie - entree) - cout
                rend[d] += points / entree
                dollars[d] += points * pt
                ntr[d] += 1
                if noter and k < t_jour.shape[0]:
                    t_jour[k] = d
                    t_entree[k] = i_entree % BARRES
                    t_sortie[k] = b
                    t_sens[k] = pos
                    t_px_e[k] = entree
                    t_px_s[k] = sortie
                    t_raison[k] = raison
                    k += 1
                pos = 0
    return rend, dollars, ntr, k


def lancer(donnees, g, noter=False, max_trades=200000):
    """g : dict de genes. donnees : dict du marche (tableaux seances x 78, niveaux et filtres par seance)."""
    t = [np.zeros(max_trades if noter else 1, dt) for dt in (np.int32, np.int32, np.int32, np.int8, np.float64, np.float64, np.int8)]
    rend, dol, ntr, k = simuler2(donnees["o"].ravel(), donnees["h"].ravel(), donnees["l"].ravel(), donnees["c"].ravel(),
                                 donnees["interdit"], donnees["fok"], donnees["poc"], donnees["vah"], donnees["val"],
                                 donnees["mur_c"], donnees["mur_p"], int(g["espece"]), int(g["L"]), float(g["Z"]), int(g["sens"]),
                                 float(g["stop"]), float(g["objectif"]), int(g["debut"]), int(g["filtre"]),
                                 float(donnees["cout"]), float(donnees["pt"]), noter, *t)
    trades = None
    if noter:
        trades = {"jour": t[0][:k], "entree": t[1][:k], "sortie": t[2][:k], "sens": t[3][:k], "px_e": t[4][:k],
                  "px_s": t[5][:k], "raison": t[6][:k]}
    return rend, dol, ntr, trades
