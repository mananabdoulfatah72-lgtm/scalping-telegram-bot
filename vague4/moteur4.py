#!/usr/bin/env python3
"""Moteur de la vague 4 (README.md) : comptes qui obligent a tout fermer chaque soir (Topstep, Tradeify), challenge puis
compte finance, avec la zone (1 MNQ) et le RSI(2) en quatre facons. Meme logique qu'intraday50k/financee.py (seance et
parcours), avec en plus :
- rsi : 0 aucun ; 1 entre deux clotures sur MNQ (= financee.py) ; 2 de nuit seulement sur MNQ (vente a 9 h 30) ;
  3 entre deux clotures sur MES ; 4 de nuit seulement sur MES ;
- les prix sont multiplies par un facteur via ptN / ptE ($ par point x facteur), comme static50k : un nombre (le meme
  pour tout le parcours) ou un tableau par seance (vague 5 : chaque seance a son facteur ; ici, rien ne reste ouvert
  d'une seance a l'autre) ;
- retraits[s] : retrait recu a la fin de la s-ieme seance apres l'achat (tableau vide : non enregistre)."""
import numpy as np
from numba import njit

UN_AN = 252
FRAIS_ZONE = 3.0
ORDRE_NQ, ORDRE_ES = 1.0 + 0.25 * 2.0, 1.0 + 0.25 * 5.0
TICK_NQ, TICK_ES = 0.25 * 2.0, 0.25 * 5.0


@njit(cache=True)
def seance4(d, rsi, veut, cash, pic_rt, plancher, mode, perte, blocage, dll, O, H, L, C, der, z_deb, z_fin, z_me, z_ms,
            z_sens, z_garde, dec, voulu, NO, NH, NL, nn, EO, EH, EL, EC, ENO, ENH, ENL, enn, ptN, ptE, qz=1):
    """Une seance (nuit + journee), qz contrats par nouvelle entree (zone et RSI(2)). Renvoie (perdu, cash fin de seance,
    veut, pic_rt, plancher, au moins un trade)."""
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
            cash -= ordre * qz
            rp = qz
            for k in range(nb):
                o = ENO[d, k] if es else NO[d, k]
                h = ENH[d, k] if es else NH[d, k]
                lo = ENL[d, k] if es else NL[d, k]
                a = cash - pr * rp * re
                hautv, basv = a + pr * rp * h, a + pr * rp * lo
                ouv = a + pr * rp * o
                if mode == 1:
                    if hautv > pic_rt:
                        pic_rt = hautv
                    plancher = min(pic_rt - perte, blocage)
                if dll > 0.0 and basv <= depart_jour - dll:
                    x = depart_jour - dll if ouv > depart_jour - dll else ouv
                    cash = x - (ordre + tick) * rp
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
            cash -= ordre * qz
            rp = qz
    k = z_deb[d]
    actif = -1
    dmin = der[d]
    for t in range(dmin + 1):
        if t == 0 and nuit_seule and rp > 0:                  # de nuit seulement : vente a l'ouverture de 9 h 30
            cash += (((EO[d, 0] if es else O[d, 0]) - re) * pr - ordre) * rp
            rp = 0
        if t == dec[d]:
            if rp > 0 and voulu[d] == 0:
                cash += (((EO[d, t] if es else O[d, t]) - re) * pr - ordre) * rp
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
        if dll > 0.0 and (nq != 0 or ne != 0) and basv <= depart_jour - dll:     # comme financee : position nette
            x = depart_jour - dll if ouv > depart_jour - dll else ouv
            cash = x - FRAIS_ZONE * abs(zp) - ordre * rp - TICK_NQ * abs(zp) - tick * rp
            zp, rp, arret = 0, 0, True
            if actif >= 0:
                actif = -2
            basv = cash
        if basv <= plancher:
            return True, basv, veut, pic_rt, plancher, trade
        if actif >= 0 and z_ms[actif] == t:
            cash += zp * (C[d, t] - ze) * ptN - FRAIS_ZONE * abs(zp)
            zp, actif = 0, -1
        while k < z_fin[d] and z_me[k] < t:
            k += 1
        if k < z_fin[d] and z_me[k] == t:
            if not arret and z_garde[k] == 1 and zp == 0:
                zp, ze, actif = z_sens[k] * qz, C[d, t], k
                trade = True
            k += 1
    if rp > 0:
        cash += (((EC[d, dmin] if es else C[d, dmin]) - re) * pr - ordre) * rp
    if zp != 0:
        cash += zp * (C[d, dmin] - ze) * ptN - FRAIS_ZONE * abs(zp)
    return False, cash, veut, pic_rt, plancher, trade


def parcours4(debut, rsi, ptN, ptE, retraits, *reste):
    """Voir _parcours4. ptN, ptE : $ par point (nombre : le meme pour tout le parcours ; tableau : par seance)."""
    nj = reste[0].shape[0]
    kN = np.full(nj, float(ptN)) if np.ndim(ptN) == 0 else np.asarray(ptN, np.float64)
    kE = np.full(nj, float(ptE)) if np.ndim(ptE) == 0 else np.asarray(ptE, np.float64)
    return _parcours4(debut, rsi, kN, kE, retraits, *reste)


@njit(cache=True)
def _parcours4(debut, rsi, kN, kE, retraits, O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu,
              NO, NH, NL, nn, EO, EH, EL, EC, ENO, ENH, ENL, enn,
              e_obj, e_perte, e_mode, e_bloc, e_dll, e_regul, e_jmin, f_perte, f_bloc, f_dll, f_jours, f_seuil, f_regul,
              f_min, plafonds, f_part, f_reserve, f_max, horizon=UN_AN, q_ch=1, q_f=1, seuil_f=1e18, reserve=0.0):
    """Challenge puis compte finance, sur horizon seances apres l'achat (UN_AN : comme financee.parcours). Leviers de la
    vague 5 (par defaut : aucun) : q_ch fois la taille de chaque nouvelle entree (zone et RSI(2)) pendant le challenge ;
    sur le compte finance, q_f fois les jours ou le coussin (solde de la veille - plancher) est d'au moins seuil_f, 1 fois
    sinon ; reserve : chaque retrait est de reserve $ de moins que le plus grand retrait permis. Renvoie
    (issue du challenge, seances du challenge, compte finance perdu, nombre de retraits, recu brut, seance du 1er retrait,
    seances jouees depuis l'achat a la fin du suivi ou a la perte du compte finance)."""
    nj = O.shape[0]
    fin = min(nj, debut + horizon)
    cash, veut, pic_rt, pic_eod, veille = 0.0, 0, 0.0, 0.0, 0.0
    plancher = -e_perte
    meilleur, jours = -1e18, 0
    issue, n_ch = 0, 0
    d = debut
    while d < fin:
        perdu, cash, veut, pic_rt, plancher, tr = seance4(d, rsi, veut, cash, pic_rt, plancher, e_mode, e_perte, e_bloc,
                                                          e_dll, O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens,
                                                          z_garde, dec, voulu, NO, NH, NL, nn, EO, EH, EL, EC, ENO, ENH,
                                                          ENL, enn, kN[d], kE[d], q_ch)
        if perdu:
            return -1, d - debut + 1, False, 0, 0.0, -1, d - debut + 1
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
        return 0, fin - debut, False, 0, 0.0, -1, fin - debut
    cash, pic_eod, veille, base = 0.0, 0.0, 0.0, 0.0
    plancher = -f_perte
    meilleur, qual, n, recu, premier = -1e18, 0, 0, 0.0, -1
    while d < fin:
        qz = q_f if cash - plancher >= seuil_f else 1
        perdu, cash, veut, pic_rt, plancher, tr = seance4(d, rsi, veut, cash, 0.0, plancher, 0, f_perte, f_bloc, f_dll,
                                                          O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens, z_garde,
                                                          dec, voulu, NO, NH, NL, nn, EO, EH, EL, EC, ENO, ENH, ENL, enn,
                                                          kN[d], kE[d], qz)
        if perdu:
            return 1, n_ch, True, n, recu, premier, d - debut + 1
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
            x -= reserve                                      # vague 5 : retirer `reserve` $ de moins que permis
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
                    return 1, n_ch, False, n, recu, premier, d - debut
    return 1, n_ch, False, n, recu, premier, fin - debut
