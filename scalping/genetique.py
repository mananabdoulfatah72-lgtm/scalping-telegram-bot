#!/usr/bin/env python3
"""Genomes de la partie B (README.md) : tirage, mutation, croisement, boucle evolutive."""
import numpy as np

import moteur as M

ENTIERS = {M.INV: 2, M.COTES: 3, M.DEBUT: 6, M.FIN: 5, M.REGIME: 3, M.TEND: 3, M.ENTREE: 4, M.FENETRE: 3, M.DUREE: 8,
           M.PAUSE: 3}
PK = {1: (0, 6), 2: (3, 9), 3: (0, 5), 7: (0, 4), 8: (0, 4), 9: (0, 4)}           # bornes [a, b) du gene PK
PZ = {0: (1.5, 6.0), 1: (1.0, 5.0), 2: (0.0, 3.0), 4: (1.0, 5.0), 5: (0.0, 1.0), 7: (1.0, 4.0), 8: (0.0, 3.0),
      9: (0.0, 3.0)}
PX = {5: 12, 8: 2, 9: 15}
PY = {3: (0.3, 1.5), 6: (2.0, 8.0), 7: (0.5, 3.0), 8: (0.4, 0.8)}
PW = {5: 2, 8: 3}


def _famille(rng, g, fam):
    g[M.FAM] = fam
    g[M.PK] = rng.integers(*PK[fam]) if fam in PK else 0
    g[M.PZ] = rng.uniform(*PZ[fam]) if fam in PZ else 0.0
    g[M.PX] = rng.integers(PX[fam]) if fam in PX else 0
    g[M.PY] = rng.uniform(*PY[fam]) if fam in PY else 0.0
    g[M.PW] = rng.integers(PW[fam]) if fam in PW else 0


def _fenetre_ok(g):
    f = M.FINS[int(g[M.FIN])]
    return f < 0 or f > M.DEBUTS[int(g[M.DEBUT])]


def aleatoire(rng, familles):
    g = np.zeros(M.NG)
    for k, n in ENTIERS.items():
        g[k] = rng.integers(n)
    while not _fenetre_ok(g):
        g[M.FIN] = rng.integers(5)
    g[M.STOP] = rng.uniform(0.3, 3.0)
    g[M.OBJ] = 0.0 if rng.random() < 0.3 else rng.uniform(0.3, 5.0)
    _famille(rng, g, familles[rng.integers(len(familles))])
    return g


def mutation(rng, g, familles, p=0.25):
    h = g.copy()
    change = False
    while not change:
        if rng.random() < p / 2:                                  # changement de famille : nouveaux parametres
            _famille(rng, h, familles[rng.integers(len(familles))])
            change = True
        fam = int(h[M.FAM])
        for k, n in ENTIERS.items():
            if rng.random() < p:
                h[k] = rng.integers(n)
                change = True
        for k, (a, b) in ((M.STOP, (0.3, 3.0)),):
            if rng.random() < p:
                h[k] = np.clip(h[k] * np.exp(0.3 * rng.normal()), a, b) if rng.random() < 0.7 else rng.uniform(a, b)
                change = True
        if rng.random() < p:
            if h[M.OBJ] == 0.0 or rng.random() < 0.15:
                h[M.OBJ] = 0.0 if (h[M.OBJ] > 0 and rng.random() < 0.5) else rng.uniform(0.3, 5.0)
            else:
                h[M.OBJ] = np.clip(h[M.OBJ] * np.exp(0.3 * rng.normal()), 0.3, 5.0)
            change = True
        if fam in PK and rng.random() < p:
            h[M.PK] = rng.integers(*PK[fam])
            change = True
        if fam in PZ and rng.random() < p:
            a, b = PZ[fam]
            h[M.PZ] = np.clip(h[M.PZ] + 0.15 * (b - a) * rng.normal(), a, b) if rng.random() < 0.7 else rng.uniform(a, b)
            change = True
        if fam in PX and rng.random() < p:
            h[M.PX] = rng.integers(PX[fam])
            change = True
        if fam in PY and rng.random() < p:
            a, b = PY[fam]
            h[M.PY] = np.clip(h[M.PY] + 0.15 * (b - a) * rng.normal(), a, b) if rng.random() < 0.7 else rng.uniform(a, b)
            change = True
        if fam in PW and rng.random() < p:
            h[M.PW] = rng.integers(PW[fam])
            change = True
    while not _fenetre_ok(h):
        h[M.FIN] = rng.integers(5)
    return h


def croisement(rng, a, b):
    """Deux parents de la meme famille : chaque gene vient de l'un ou de l'autre."""
    m = rng.random(M.NG) < 0.5
    h = np.where(m, a, b)
    h[M.FAM] = a[M.FAM]
    while not _fenetre_ok(h):
        h[M.FIN] = rng.integers(5)
    return h


def cle(g):
    return np.round(g, 4).tobytes()


def mesurer(g, f, s0, s1):
    gain, n, w, brut, _ = M.jouer(g, f, s0, s1)
    x = gain[np.isfinite(gain)]
    sd = x.std(ddof=1) if len(x) > 2 else 0.0
    t = float(x.mean() / sd * np.sqrt(len(x))) if sd > 0 else 0.0
    return t, int(n), gain


def evoluer(f, s0, s1, rng, familles, generations=60, taille=200, elites=20, immigrants=20, min_trades=200):
    """Boucle evolutive sur [s0, s1) (entrainement). Renvoie {cle: (genome, fitness, t, trades)} de toutes les
    strategies distinctes evaluees."""
    vus = {}

    def fitness(g):
        k = cle(g)
        if k not in vus:
            t, n, _ = mesurer(g, f, s0, s1)
            vus[k] = (g, t * min(1.0, n / min_trades), t, n)
        return vus[k][1]

    pop = [aleatoire(rng, familles) for _ in range(taille)]
    for gen in range(generations):
        fit = np.array([fitness(g) for g in pop])
        ordre = np.argsort(-fit)
        pop = [pop[i] for i in ordre]
        fit = fit[ordre]
        if gen == generations - 1:
            break
        haut = pop[:taille // 2]
        fh = fit[:taille // 2]

        def tournoi():
            i = rng.integers(len(haut), size=3)
            return haut[i[np.argmax(fh[i])]]

        enfants = []
        while len(enfants) < taille - elites - immigrants:
            a = tournoi()
            if rng.random() < 0.5:
                meme = [h for h in haut if h[M.FAM] == a[M.FAM] and h is not a]
                if meme:
                    a = croisement(rng, a, meme[rng.integers(len(meme))])
            enfants.append(mutation(rng, a, familles))
        pop = pop[:elites] + enfants + [aleatoire(rng, familles) for _ in range(immigrants)]
    return vus
