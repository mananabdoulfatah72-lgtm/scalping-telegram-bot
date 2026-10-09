#!/usr/bin/env python3
"""Moteur de la vague 4 (README.md) : comptes qui obligent a tout fermer chaque soir (Topstep, Tradeify), challenge puis
compte finance, avec la zone (1 MNQ) et le RSI(2) en quatre facons. Meme logique qu'intraday50k/financee.py (seance et
parcours), avec en plus :
- rsi : 0 aucun ; 1 entre deux clotures sur MNQ (= financee.py) ; 2 de nuit seulement sur MNQ (vente a 9 h 30) ;
  3 entre deux clotures sur MES ; 4 de nuit seulement sur MES ;
- les prix sont multiplies par un facteur par depart via ptN / ptE ($ par point x facteur), comme static50k ;
- retraits[s] : retrait recu a la fin de la s-ieme seance apres l'achat (tableau vide : non enregistre)."""
import numpy as np
from numba import njit

UN_AN = 252
FRAIS_ZONE = 3.0
ORDRE_NQ, ORDRE_ES = 1.0 + 0.25 * 2.0, 1.0 + 0.25 * 5.0
TICK_NQ, TICK_ES = 0.25 * 2.0, 0.25 * 5.0


@njit(cache=True)
def seance4(d, rsi, veut, cash, pic_rt, plancher, mode, perte, blocage, dll, O, H, L, C, der, z_deb, z_fin, z_me, z_ms,
            z_sens, z_garde, dec, voulu, NO, NH, NL, nn, EO, EH, EL, EC, ENO, ENH, ENL, enn, ptN, ptE):
    """Une seance (nuit + journee). Renvoie (perdu, cash fin de seance, veut, pic_rt, plancher, au moins un trade)."""
    es = rsi == 3 or rsi == 4
    nuit_seule = rsi == 2 or rsi == 4
    pr = ptE if es else ptN
    ordre = ORDRE_ES if es else ORDRE_NQ
    tick = TICK_ES if es else TICK_NQ
    arret = False
    depart_jour = cash
    trade = False
    zp, ze, rp, re = 0, 0.0, 0, 0.0
    if rsi > 0 and veut == 1:
        nb = enn[d] if es else nn[d]
        if nb > 0:
            trade = True
            re = ENO[d, 0] if es else NO[d, 0]
            cash -= ordre
            rp = 1
            for k in range(nb):
                o = ENO[d, k] if es else NO[d, k]
                h = ENH[d, k] if es else NH[d, k]
                lo = ENL[d, k] if es else NL[d, k]
                a = cash - pr * re
                hautv, basv = a + pr * h, a + pr * lo
                ouv = a + pr * o
                if mode == 1:
                    if hautv > pic_rt:
                        pic_rt = hautv
                    plancher = min(pic_rt - perte, blocage)
                if dll > 0.0 and basv <= depart_jour - dll:
                    x = depart_jour - dll if ouv > depart_jour - dll else ouv
                    cash = x - ordre - tick
                    rp = 0
                    arret = True
                    basv = cash
                if basv <= plancher:
                    return True, basv, veut, pic_rt, plancher, trade
                if arret:
                    break
        elif not nuit_seule:
            trade = True
            re = EO[d, 0] if es else O[d, 0]
            cash -= ordre
            rp = 1
    k = z_deb[d]
    actif = -1
    dmin = der[d]
    for t in range(dmin + 1):
        if t == 0 and nuit_seule and rp == 1:                 # de nuit seulement : vente a l'ouverture de 9 h 30
            cash += ((EO[d, 0] if es else O[d, 0]) - re) * pr - ordre
            rp = 0
        if t == dec[d]:
            if rp == 1 and voulu[d] == 0:
                cash += ((EO[d, t] if es else O[d, t]) - re) * pr - ordre
                rp = 0
            veut = voulu[d]
        nq = zp + (rp if not es else 0)
        ne = rp if es else 0
        a = cash - ptN * (zp * ze + (rp * re if not es else 0.0)) - (pr * ne * re if es else 0.0)
        ouv = a + ptN * nq * O[d, t] + (ptE * ne * EO[d, t] if es else 0.0)
        if nq > 0:
            hn, bn = H[d, t], L[d, t]
        else:
            hn, bn = L[d, t], H[d, t]
        hautv = a + ptN * nq * hn + (ptE * ne * EH[d, t] if es else 0.0)
        basv = a + ptN * nq * bn + (ptE * ne * EL[d, t] if es else 0.0)     # deux contrats : pires points additionnes
        if mode == 1:
            if hautv > pic_rt:
                pic_rt = hautv
            plancher = min(pic_rt - perte, blocage)
        if dll > 0.0 and (zp != 0 or rp != 0) and basv <= depart_jour - dll:
            x = depart_jour - dll if ouv > depart_jour - dll else ouv
            cash = x - (FRAIS_ZONE if zp != 0 else 0.0) - (ordre if rp != 0 else 0.0) - TICK_NQ * abs(zp) - tick * rp
            zp, rp, arret = 0, 0, True
            if actif >= 0:
                actif = -2
            basv = cash
        if basv <= plancher:
            return True, basv, veut, pic_rt, plancher, trade
        if actif >= 0 and z_ms[actif] == t:
            cash += zp * (C[d, t] - ze) * ptN - FRAIS_ZONE
            zp, actif = 0, -1
        while k < z_fin[d] and z_me[k] < t:
            k += 1
        if k < z_fin[d] and z_me[k] == t:
            if not arret and z_garde[k] == 1 and zp == 0:
                zp, ze, actif = z_sens[k], C[d, t], k
                trade = True
            k += 1
    if rp == 1:
        cash += ((EC[d, dmin] if es else C[d, dmin]) - re) * pr - ordre
    if zp != 0:
        cash += zp * (C[d, dmin] - ze) * ptN - FRAIS_ZONE
    return False, cash, veut, pic_rt, plancher, trade


@njit(cache=True)
def parcours4(debut, rsi, ptN, ptE, retraits, O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu,
              NO, NH, NL, nn, EO, EH, EL, EC, ENO, ENH, ENL, enn,
              e_obj, e_perte, e_mode, e_bloc, e_dll, e_regul, e_jmin, f_perte, f_bloc, f_dll, f_jours, f_seuil, f_regul,
              f_min, plafonds, f_part, f_reserve, f_max):
    """Challenge puis compte finance, sur UN_AN seances apres l'achat (comme financee.parcours). Renvoie (issue du
    challenge, seances du challenge, compte finance perdu, nombre de retraits, recu brut, seance du 1er retrait)."""
    nj = O.shape[0]
    fin = min(nj, debut + UN_AN)
    cash, veut, pic_rt, pic_eod, veille = 0.0, 0, 0.0, 0.0, 0.0
    plancher = -e_perte
    meilleur, jours = -1e18, 0
    issue, n_ch = 0, 0
    d = debut
    while d < fin:
        perdu, cash, veut, pic_rt, plancher, tr = seance4(d, rsi, veut, cash, pic_rt, plancher, e_mode, e_perte, e_bloc,
                                                          e_dll, O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens,
                                                          z_garde, dec, voulu, NO, NH, NL, nn, EO, EH, EL, EC, ENO, ENH,
                                                          ENL, enn, ptN, ptE)
        if perdu:
            return -1, d - debut + 1, False, 0, 0.0, -1
        g = cash - veille
        veille = cash
        jours += 1
        if g > meilleur:
            meilleur = g
        if e_mode == 0:
            if cash > pic_eod:
                pic_eod = cash
            plancher = min(pic_eod - e_perte, e_bloc)
        d += 1
        if cash >= e_obj and jours >= e_jmin and (e_regul == 0.0 or meilleur <= e_regul * cash):
            issue, n_ch = 1, d - debut
            break
    if issue != 1:
        return 0, fin - debut, False, 0, 0.0, -1
    cash, pic_eod, veille, base = 0.0, 0.0, 0.0, 0.0
    plancher = -f_perte
    meilleur, qual, n, recu, premier = -1e18, 0, 0, 0.0, -1
    while d < fin:
        perdu, cash, veut, pic_rt, plancher, tr = seance4(d, rsi, veut, cash, 0.0, plancher, 0, f_perte, f_bloc, f_dll,
                                                          O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens, z_garde,
                                                          dec, voulu, NO, NH, NL, nn, EO, EH, EL, EC, ENO, ENH, ENL, enn,
                                                          ptN, ptE)
        if perdu:
            return 1, n_ch, True, n, recu, premier
        g = cash - veille
        veille = cash
        if (f_seuil > 0.0 and g >= f_seuil) or (f_seuil == 0.0 and tr):
            qual += 1
        if g > meilleur:
            meilleur = g
        if cash > pic_eod:
            pic_eod = cash
        plancher = min(pic_eod - f_perte, f_bloc)
        d += 1
        gain = cash - base
        if qual >= f_jours and gain > 0.0 and (f_regul == 0.0 or meilleur <= f_regul * gain):
            plaf = plafonds[min(n, len(plafonds) - 1)]
            x = min(plaf, cash - f_reserve)
            if f_part > 0.0:
                x = min(x, f_part * cash)
            if x >= f_min:
                cash -= x
                veille = cash
                recu += x
                n += 1
                if d - debut - 1 < retraits.shape[0]:
                    retraits[d - debut - 1] = x
                if premier < 0:
                    premier = d - debut
                base, meilleur, qual = cash, -1e18, 0
                if f_max > 0 and n >= f_max:
                    return 1, n_ch, False, n, recu, premier
    return 1, n_ch, False, n, recu, premier
