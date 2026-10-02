#!/usr/bin/env python3
"""Moteur de la machine order flow (README.md, regles v2) : signal de chaque strategie sur la grille (seance x minute),
puis execution au marche a la seconde suivante (bid / ask reels), une position a la fois, sortie a l'horizon ou au stop."""
import numpy as np
from numba import njit

from precalcul import FENETRES, NIVEAUX, RATIOS

FAMILLES = ["toucher d'un niveau", "desequilibre", "divergence CVD", "carnet 1er niveau", "gros ordres", "empilement",
            "pic de volume"]
CONFIRMATIONS = ["aucune", "delta dans le sens du mouvement", "delta contre le mouvement"]
SORTIES = (5, 10, 15, 30, 60, 999)          # minutes ; 999 = fin de seance
STOPS = (0, 10, 20, 40)                     # ticks ; 0 = sans stop
DEBUTS = (5, 30, 90, 210)                   # 9 h 35, 10 h, 11 h, 13 h
FINS = (90, 210, 330, 375)                  # 11 h, 13 h, 15 h, 15 h 45
TICK, NS = 0.25, 23400


def decoder(u):
    f = int(u["famille"])
    return {"famille": f, "niveau": int(u["niveau"]), "confirmation": int(u["confirmation"]), "W": FENETRES[int(u["W"])],
            "seuil": round(float(u["seuil"]), 3), "sens": int(u["sens"]), "sortie": SORTIES[int(u["sortie"])],
            "stop": STOPS[int(u["stop"])], "debut": DEBUTS[int(u["debut"])], "fin": FINS[int(u["fin"])]}


def decrire(g):
    f = g["famille"]
    x = FAMILLES[f]
    if f == 0:
        x += f" : {NIVEAUX[g['niveau']]}, tolerance {1 + round(7 * g['seuil'])} ticks, confirmation {CONFIRMATIONS[g['confirmation']]}"
    elif f == 1:
        x += f" sur {g['W']} min au-dela de {0.05 + 0.45 * g['seuil']:.2f}"
    elif f == 2:
        x += f" sur {g['W']} min"
    elif f == 3:
        x += f" au-dela de {0.1 + 0.7 * g['seuil']:.2f}"
    elif f == 4:
        x += f" sur {g['W']} min, z >= {1.5 + 3.5 * g['seuil']:.1f}"
    elif f == 5:
        x += f", ratio {RATIOS[int(round(6 * g['seuil']))]}"
    elif f == 6:
        x += f", volume >= {1.5 + 3.5 * g['seuil']:.1f} fois la normale"
    h = lambda m: f"{(570 + m) // 60}h{(570 + m) % 60:02d}"
    return (x + f" ; {'suivre' if g['sens'] == 0 else 'contrer'} ; sortie "
            + ("fin de seance" if g["sortie"] == 999 else f"{g['sortie']} min") + (f", stop {g['stop']} ticks" if g["stop"] else "")
            + f" ; {h(g['debut'])}-{h(g['fin'])}")


def signal(B, g):
    """Sens (+1, -1, 0) a la cloture de chaque minute, avant le gene sens."""
    f, W, u = g["famille"], g["W"], g["seuil"]
    nj = B.nj
    d0 = np.zeros((nj, 390), np.int8)
    if f == 0:
        L = np.concatenate([np.full((nj, 1), np.nan), B.niveaux[g["niveau"]][:, :-1]], axis=1)   # niveau connu au debut de la minute
        tol = (1 + round(7 * u)) * TICK
        dessous = (B.o < L) & (B.h >= L - tol)
        dessus = (B.o > L) & (B.l <= L + tol) & ~dessous
        d0 = np.where(dessous, 1, np.where(dessus, -1, 0)).astype(np.int8)
        if g["confirmation"]:
            vol = B.achat + B.vente
            imb = np.where(vol > 0, (B.achat - B.vente) / np.where(vol > 0, vol, 1), 0) * d0
            garde = imb >= 0.1 if g["confirmation"] == 1 else imb <= -0.1
            d0 = np.where(garde, d0, 0).astype(np.int8)
    elif f == 1:
        a, v = B.somme(B.cum_achat, W), B.somme(B.cum_vente, W)
        imb = np.where(a + v > 0, (a - v) / np.where(a + v > 0, a + v, 1), 0)
        s = 0.05 + 0.45 * u
        d0 = np.where(imb >= s, 1, np.where(imb <= -s, -1, 0)).astype(np.int8)
    elif f == 2:
        dl = B.somme(B.cum_achat, W) - B.somme(B.cum_vente, W)
        c = B.c
        mx, mn = B.extremes(W)
        d0 = np.where((c >= mx) & (dl < 0), -1, np.where((c <= mn) & (dl > 0), 1, 0)).astype(np.int8)
    elif f == 3:
        s = 0.1 + 0.7 * u
        d0 = np.where(B.l1 >= s, 1, np.where(B.l1 <= -s, -1, 0)).astype(np.int8)
    elif f == 4:
        net = B.somme(B.cum_gros, W)
        sd = B.gros_sd[:, None] * np.sqrt(W)
        z = np.where(sd > 0, net / np.where(sd > 0, sd, 1), 0)
        s = 1.5 + 3.5 * u
        d0 = np.where(z >= s, 1, np.where(z <= -s, -1, 0)).astype(np.int8)
    elif f == 5:
        d0 = B.empile[int(round(6 * u))].astype(np.int8)
    elif f == 6:
        m = 1.5 + 3.5 * u
        d0 = np.where(B.pic >= m, np.sign(B.c - B.o), 0).astype(np.int8)
    d0 = np.where(np.isnan(B.c), 0, d0)
    minute = np.arange(390)[None, :]
    d0 = np.where((minute >= g["debut"]) & (minute <= g["fin"]) & ~B.change[:, None], d0, 0).astype(np.int8)
    return d0 if g["sens"] == 0 else (-d0).astype(np.int8)


@njit(cache=True)
def simuler(sig, bid, ask, sortie, stop, hasard, signes):
    """Gain net (points de NQ) de chaque seance et nombre de trades. hasard = 1 : le sens de chaque trade est remplace par
    signes[seance, minute] (controle sans information de sens)."""
    nj = sig.shape[0]
    total = np.zeros(nj)
    n = 0
    for d in range(nj):
        libre = 0
        for i in range(389):
            if sig[d, i] == 0 or i < libre:
                continue
            sens = signes[d, i] if hasard == 1 else sig[d, i]
            e = (i + 1) * 60
            x = NS - 1 if sortie == 999 else min(e + sortie * 60, NS - 1)
            entree = ask[d, e] if sens > 0 else bid[d, e]
            sortie_px = bid[d, x] if sens > 0 else ask[d, x]
            fin = x
            if stop > 0:
                for s in range(e + 1, x + 1):
                    if sens > 0 and bid[d, s] <= entree - stop * TICK:
                        sortie_px = bid[d, s]
                        fin = s
                        break
                    if sens < 0 and ask[d, s] >= entree + stop * TICK:
                        sortie_px = ask[d, s]
                        fin = s
                        break
            total[d] += sens * (sortie_px - entree) - 1.0
            n += 1
            libre = fin // 60 + 1
    return total, n


def fitness(total, n, mini=60):
    s = total.std(ddof=1)
    t = total.mean() / s * np.sqrt(len(total)) if s > 0 else 0.0
    return float(t * min(1.0, n / mini)), float(t)
