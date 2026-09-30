"""Moteur de backtest intraday (barres de 5 minutes), accelere avec numba. Regles dans README.md.

Une strategie = 9 genes : espece, marche, L, Z, sens, stop, objectif, debut, filtre.
Signal a la cloture de la barre j, execution a l'ouverture de la barre j + 1, une position a la fois,
stop verifie avant l'objectif, tout ferme a 16 h, frais par aller-retour.
"""
import numpy as np
from numba import njit

BARRES = 78
DERNIERE_ENTREE = 66                      # 15 h 00
MOMENTUM, RETOUR, CANAL, OUVERTURE = 0, 1, 2, 3
ESPECES = ["momentum", "retour a la moyenne", "cassure de canal", "range d'ouverture"]


@njit(cache=True)
def _moy_ecart(c, L):
    """Moyenne et ecart-type glissants de c sur L barres (barre courante comprise), recalcules regulierement."""
    n = c.shape[0]
    moy = np.full(n, np.nan)
    ect = np.full(n, np.nan)
    s = 0.0
    s2 = 0.0
    ref = c[0]
    for i in range(n):
        if i % 2048 == 0 and i >= L:          # recalcul exact pour eviter la derive des sommes
            ref = c[i]
            s = 0.0
            s2 = 0.0
            for k in range(i - L + 1, i + 1):
                x = c[k] - ref
                s += x
                s2 += x * x
        else:
            x = c[i] - ref
            s += x
            s2 += x * x
            if i >= L:
                y = c[i - L] - ref
                s -= y
                s2 -= y * y
        if i >= L - 1:
            m = s / L
            v = s2 / L - m * m
            moy[i] = m + ref
            ect[i] = np.sqrt(v) if v > 0 else 0.0
    return moy, ect


@njit(cache=True)
def simuler(o, h, l, c, interdit, regime, espece, L, Z, sens, stop, objectif, debut, filtre, cout, pt,
            noter, t_jour, t_entree, t_sortie, t_sens, t_px_e, t_px_s, t_raison):
    """Renvoie (rendement net par seance, $ net par seance pour 1 micro, trades par seance, nombre de trades notes).
    sens : 0 les deux, 1 achat seul, 2 vente seule. filtre : 0 aucun, 1 jours agites, 2 jours calmes.
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
            permis = filtre == 0 or regime[d] == filtre
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
    """g : dict de genes. donnees : dict du marche (tableaux 2D seances x 78 aplatis ici)."""
    t = [np.zeros(max_trades if noter else 1, dt) for dt in (np.int32, np.int32, np.int32, np.int8, np.float64, np.float64, np.int8)]
    rend, dol, ntr, k = simuler(donnees["o"].ravel(), donnees["h"].ravel(), donnees["l"].ravel(), donnees["c"].ravel(),
                                donnees["interdit"], donnees["regime"], int(g["espece"]), int(g["L"]), float(g["Z"]),
                                int(g["sens"]), float(g["stop"]), float(g["objectif"]), int(g["debut"]), int(g["filtre"]),
                                float(donnees["cout"]), float(donnees["pt"]), noter, *t)
    trades = None
    if noter:
        trades = {"jour": t[0][:k], "entree": t[1][:k], "sortie": t[2][:k], "sens": t[3][:k], "px_e": t[4][:k],
                  "px_s": t[5][:k], "raison": t[6][:k]}
    return rend, dol, ntr, trades


def charger(chemin):
    z = np.load(chemin)
    return {k: z[k] for k in z.files}
