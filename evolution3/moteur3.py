"""Moteur de backtest de la machine n°3 (README.md) : barres de 5 minutes, 7 familles d'hypotheses, numba.
Signal a la cloture de la barre j, entree a l'ouverture de la barre j + 1 (meme seance), une position a la fois,
stop avant objectif, sortie forcee apres `duree` barres et a la fin de la seance, frais par aller-retour."""
import numpy as np
from numba import njit

FAMILLES = ["ecart a la moyenne", "cassure de canal", "range d'ouverture", "ecart au VWAP", "mouvement depuis l'ouverture",
            "gap", "niveaux de la veille"]
MOYENNE, CANAL, OUVERTURE, VWAP, DEPUIS, GAP, VEILLE = range(7)


@njit(cache=True)
def moy_ecart(c, L):
    """Moyenne et ecart-type glissants de c sur L barres (barre courante comprise), calcul exact par fenetre."""
    n = c.shape[0]
    moy = np.full(n, np.nan)
    ect = np.full(n, np.nan)
    s = 0.0
    s2 = 0.0
    ref = c[0]
    for i in range(n):
        if i % 2048 == 0 and i >= L:
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
def ecart_variations(c, n=20):
    """Ecart-type des variations de prix sur les n dernieres barres (barre courante comprise)."""
    N = c.shape[0]
    dc = np.zeros(N)
    for i in range(1, N):
        dc[i] = c[i] - c[i - 1]
    _, e = moy_ecart(dc, n)
    return e


@njit(cache=True)
def simuler(o, h, l, c, vwap, pc, ph, pl, gap_moy, interdit, regime, nb, famille, inverse, L, Z, sens, stop, objectif,
            debut, duree, filtre, cout, pt):
    """Renvoie (rendement net par seance, $ net par seance pour 1 micro, trades par seance).
    sens : 0 les deux, 1 achat seul, 2 vente seule ; filtre : 0 aucun, 1 jours agites, 2 jours calmes."""
    n = c.shape[0]
    nj = n // nb
    rend = np.zeros(nj)
    dollars = np.zeros(nj)
    ntr = np.zeros(nj, np.int32)
    moy, ect = moy_ecart(c, L)
    sig = ecart_variations(c, 20)
    derniere = nb - 6
    pos = 0
    entree = 0.0
    px_stop = 0.0
    px_obj = 0.0
    i_entree = 0
    orb_h = 0.0
    orb_l = 0.0
    o_jour = 0.0
    deja_gap = False
    for i in range(n):
        b = i % nb
        d = i // nb
        if b == 0:
            orb_h = h[i]
            orb_l = l[i]
            o_jour = o[i]
            deja_gap = False
        elif b < L:
            if h[i] > orb_h:
                orb_h = h[i]
            if l[i] < orb_l:
                orb_l = l[i]
        entre_ici = False
        if pos == 0 and b >= 1 and b >= debut and b <= derniere and not interdit[d]:
            j = i - 1
            bj = j % nb
            s = 0
            permis = (filtre == 0 or regime[d] == filtre) and not np.isnan(sig[j]) and sig[j] > 0
            if permis:
                if famille == MOYENNE:
                    if j >= L - 1 and ect[j] > 0:
                        z = (c[j] - moy[j]) / ect[j]
                        if z > Z:
                            s = 1
                        elif z < -Z:
                            s = -1
                elif famille == CANAL:
                    if j >= L:
                        hh = h[j - L]
                        ll = l[j - L]
                        for m in range(j - L + 1, j):
                            if h[m] > hh:
                                hh = h[m]
                            if l[m] < ll:
                                ll = l[m]
                        if c[j] > hh + Z * sig[j]:
                            s = 1
                        elif c[j] < ll - Z * sig[j]:
                            s = -1
                elif famille == OUVERTURE:
                    if bj >= L - 1:
                        if c[j] > orb_h + Z * sig[j]:
                            s = 1
                        elif c[j] < orb_l - Z * sig[j]:
                            s = -1
                elif famille == VWAP:
                    dv = c[j] - vwap[j]
                    if dv > Z * sig[j]:
                        s = 1
                    elif dv < -Z * sig[j]:
                        s = -1
                elif famille == DEPUIS:
                    mv = c[j] - o_jour
                    if mv > Z * sig[j]:
                        s = 1
                    elif mv < -Z * sig[j]:
                        s = -1
                elif famille == GAP:
                    if not deja_gap and not np.isnan(pc[d]) and not np.isnan(gap_moy[d]) and gap_moy[d] > 0:
                        g = o_jour / pc[d] - 1.0
                        if g > Z * gap_moy[d]:
                            s = 1
                        elif g < -Z * gap_moy[d]:
                            s = -1
                elif famille == VEILLE:
                    if not np.isnan(ph[d]):
                        if c[j] > ph[d] + Z * sig[j]:
                            s = 1
                        elif c[j] < pl[d] - Z * sig[j]:
                            s = -1
            if inverse == 1:
                s = -s
            if (sens == 1 and s < 0) or (sens == 2 and s > 0):
                s = 0
            if s != 0:
                pos = s
                entree = o[i]
                px_stop = entree * (1.0 - s * stop)
                px_obj = entree * (1.0 + s * objectif)
                i_entree = i
                entre_ici = True
                if famille == GAP:
                    deja_gap = True
        if pos != 0:
            sortie = np.nan
            if pos > 0:
                if (not entre_ici) and o[i] <= px_stop:
                    sortie = o[i]
                elif l[i] <= px_stop:
                    sortie = px_stop
                elif h[i] >= px_obj:
                    sortie = px_obj
            else:
                if (not entre_ici) and o[i] >= px_stop:
                    sortie = o[i]
                elif h[i] >= px_stop:
                    sortie = px_stop
                elif l[i] <= px_obj:
                    sortie = px_obj
            if np.isnan(sortie) and (b == nb - 1 or i - i_entree + 1 >= duree):
                sortie = c[i]
            if not np.isnan(sortie):
                points = pos * (sortie - entree) - cout
                rend[d] += points / entree
                dollars[d] += points * pt
                ntr[d] += 1
                pos = 0
    return rend, dollars, ntr


def lancer(d, g):
    """g : dict de genes decodes ; d : dict du marche (tableaux seances x barres, aplatis ici)."""
    return simuler(d["o"].ravel(), d["h"].ravel(), d["l"].ravel(), d["c"].ravel(), d["vwap"].ravel(), d["pc"], d["ph"],
                   d["pl"], d["gap_moy"], d["interdit"], d["regime"], int(d["nb"]), int(g["famille"]), int(g["inverse"]),
                   int(g["L"]), float(g["Z"]), int(g["sens"]), float(g["stop"]), float(g["objectif"]), int(g["debut"]),
                   int(g["duree"]), int(g["filtre"]), float(d["cout"]), float(d["pt"]))


def charger(chemin):
    z = np.load(chemin)
    return {k: z[k] for k in z.files}
