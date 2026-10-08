#!/usr/bin/env python3
"""Moteur des comptes 50K « intraday » (README.md, partie 2) : zone de bruit en minutes de seance, RSI(2) entre deux
clotures (achat a 18 h, nuit en barres d'une heure, ferme a la derniere minute de chaque seance). Valeurs relatives au
solde de depart (0 = 50 000 $)."""
import numpy as np
from numba import njit

PT = 2.0                        # $ par point pour 1 MNQ
GLISSE = 0.25 * PT              # 1 tick de plus pour une sortie forcee par la limite du jour


@njit(cache=True)
def challenge(debut, nmax, avec_rsi, O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu,
              NO, NH, NL, nn, objectif, perte, mode, blocage, dll, regul, jmin, frais_zone, frais_rsi):
    """Un challenge qui commence a la seance `debut` (RSI(2) a plat). mode 1 : plancher suivi en direct (plus haut,
    gains latents compris) ; mode 0 : plancher = plus haut solde de cloture - perte, surveille en direct. Plancher
    bloque a `blocage`. dll > 0 : limite du jour douce (tout ferme, plus rien jusqu'a 18 h). regul > 0 : meilleur jour
    <= regul x gain pour reussir. Renvoie (issue 1/-1/0, seances jouees, marge minimale, valeur finale)."""
    nj = O.shape[0]
    cash = 0.0
    zp, ze, rp, re = 0, 0.0, 0, 0.0
    veut = 0
    pic_rt, pic_eod, veille = 0.0, 0.0, 0.0
    plancher = -perte
    meilleur, jours, marge = -1e18, 0, 1e18
    fin = min(nj, debut + nmax)
    for d in range(debut, fin):
        arret = False
        depart_jour = veille
        # ---------------- nuit : RSI(2) achete a la reouverture (18 h) si la regle le voulait a la derniere decision
        if avec_rsi == 1 and veut == 1:
            if nn[d] > 0:
                re = NO[d, 0]
                cash -= frais_rsi
                rp = 1
                for k in range(nn[d]):
                    a = cash - PT * re
                    hautv, basv = a + PT * NH[d, k], a + PT * NL[d, k]
                    ouv = a + PT * NO[d, k]
                    if mode == 1:
                        if hautv > pic_rt:
                            pic_rt = hautv
                        plancher = min(pic_rt - perte, blocage)
                    if dll > 0.0 and basv <= depart_jour - dll:
                        x = depart_jour - dll if ouv > depart_jour - dll else ouv
                        cash = x - frais_rsi - GLISSE
                        rp = 0
                        arret = True
                        basv = cash
                    if basv - plancher < marge:
                        marge = basv - plancher
                    if basv <= plancher:
                        return -1, d - debut + 1, marge, basv
                    if arret:
                        break
            else:
                re = O[d, 0]
                cash -= frais_rsi
                rp = 1
        # ---------------- seance : minutes de 9 h 30 a la derniere minute
        k = z_deb[d]
        actif = -1
        dmin = der[d]
        for t in range(dmin + 1):
            if t == dec[d]:
                if rp == 1 and voulu[d] == 0:
                    cash += (O[d, t] - re) * PT - frais_rsi
                    rp = 0
                veut = voulu[d]
            n = zp + rp
            a = cash - PT * (zp * ze + rp * re)
            ouv = a + PT * n * O[d, t]
            if n > 0:
                hautv, basv = a + PT * n * H[d, t], a + PT * n * L[d, t]
            elif n < 0:
                hautv, basv = a + PT * n * L[d, t], a + PT * n * H[d, t]
            else:
                hautv, basv = a, a
            if mode == 1:
                if hautv > pic_rt:
                    pic_rt = hautv
                plancher = min(pic_rt - perte, blocage)
            if dll > 0.0 and n != 0 and basv <= depart_jour - dll:
                x = depart_jour - dll if ouv > depart_jour - dll else ouv
                cash = x - (frais_zone if zp != 0 else 0.0) - (frais_rsi if rp != 0 else 0.0) - GLISSE * (abs(zp) + rp)
                zp, rp, arret = 0, 0, True
                if actif >= 0:
                    actif = -2
                basv = cash
            if basv - plancher < marge:
                marge = basv - plancher
            if basv <= plancher:
                return -1, d - debut + 1, marge, basv
            # zone : sortie puis entree a la cloture de la minute
            if actif >= 0 and z_ms[actif] == t:
                cash += zp * (C[d, t] - ze) * PT - frais_zone
                zp, actif = 0, -1
            while k < z_fin[d] and z_me[k] < t:
                k += 1
            if k < z_fin[d] and z_me[k] == t:
                if not arret and z_garde[k] == 1 and zp == 0:
                    zp, ze, actif = z_sens[k], C[d, t], k
                k += 1
        # fin de seance : tout est a plat (RSI(2) ferme a la derniere minute ; zone deja sortie)
        if rp == 1:
            cash += (C[d, dmin] - re) * PT - frais_rsi
            rp = 0
        if zp != 0:
            cash += zp * (C[d, dmin] - ze) * PT - frais_zone
            zp = 0
        eod = cash
        g = eod - veille
        veille = eod
        jours += 1
        if g > meilleur:
            meilleur = g
        if mode == 0:
            if eod > pic_eod:
                pic_eod = eod
            plancher = min(pic_eod - perte, blocage)
        if eod >= objectif and jours >= jmin and (regul == 0.0 or meilleur <= regul * eod):
            return 1, d - debut + 1, marge, eod
    return 0, fin - debut, marge, veille


@njit(cache=True)
def gains_jour(avec_rsi, O, C, der, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu, NO, nn, frais_zone, frais_rsi):
    """Gain de chaque seance du bot sans compte (controle) : meme logique que challenge() avec une perte infinie."""
    nj = O.shape[0]
    out = np.zeros(nj)
    veut = 0
    for d in range(nj):
        g = 0.0
        rp, re = 0, 0.0
        if avec_rsi == 1 and veut == 1:
            re = NO[d, 0] if nn[d] > 0 else O[d, 0]
            g -= frais_rsi
            rp = 1
        if dec[d] >= 0:
            if rp == 1 and voulu[d] == 0:
                g += (O[d, dec[d]] - re) * PT - frais_rsi
                rp = 0
            veut = voulu[d]
        if rp == 1:
            g += (C[d, der[d]] - re) * PT - frais_rsi
        for k in range(z_deb[d], z_fin[d]):
            if z_garde[k] == 1:
                g += z_sens[k] * (C[d, z_ms[k]] - C[d, z_me[k]]) * PT - frais_zone
        out[d] = g
    return out
