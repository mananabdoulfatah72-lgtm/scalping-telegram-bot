#!/usr/bin/env python3
"""Moteur de static50k (README.md) : un achat DayTraders Static 50K suivi seance par seance (minutes de 9 h 30 a 16 h, puis
barres d'une heure de 16 h a 8 h), evaluation puis compte Pro Static, pour une variante du bot. Valeurs relatives au solde
de depart (0 = 50 000 $). Les prix sont multiplies par un facteur par depart via ptN / ptE ($ par point x facteur)."""
import numpy as np
from numba import njit

FRAIS_ZONE = 3.0                # $ par aller-retour de zone et par MNQ (1,5 point)
ORDRE_NQ = 1.0 + 0.25 * 2.0     # $ par ordre du RSI(2) et par MNQ : 1 $ + 1 tick
ORDRE_ES = 1.0 + 0.25 * 5.0     # $ par ordre et par MES : 1 $ + 1 tick
TICK_NQ, TICK_ES = 0.25 * 2.0, 0.25 * 5.0     # glissement d'une sortie forcee, par contrat
OBJECTIF, PERTE = 3750.0, 1000.0
SEUIL_PRO, GARDE_PRO, MAX_RET = 2600.0, 2000.0, 2000.0
VARIANTES = {"E0": 0, "E1": 1, "E2": 2, "E3": 3, "E4": 4, "E5": 5, "E6": 6}

# colonnes du resultat
ISSUE, FIN_EVAL, PRO_PERDU, FIN_PRO, RECU1, RECU2, NRET1, PREMIER, INACTIF = range(9)
NCOL = 9


@njit(cache=True)
def _rsi_choix(variante, coussin):
    """Instrument (0 MNQ, 1 MES) et nombre de contrats d'une nouvelle entree du RSI(2) ; 0 contrat : pas d'entree."""
    if variante == 0:
        return 0, 1
    if variante == 1:
        return 0, 0
    if variante == 2:
        return 0, 1 if coussin >= 2000.0 else 0
    if variante == 3:
        return 0, 1 if coussin >= 3000.0 else 0
    if variante == 4:
        return 1, 1
    if variante == 5:
        return (1, 1) if coussin < 3000.0 else (0, 1)
    if coussin < 3000.0:            # variante 6
        return 0, 0
    n = int(coussin // 2000.0)
    return 0, min(max(n, 1), 3)


@njit(cache=True)
def _zone_taille(variante, coussin):
    if variante == 6:
        n = int(coussin // 2000.0)
        return min(max(n, 1), 3)
    return 1


@njit(cache=True)
def _sortie_rsi(rq, ri):
    """Frais et glissement d'une sortie forcee du RSI(2)."""
    return rq * ((ORDRE_NQ + TICK_NQ) if ri == 0 else (ORDRE_ES + TICK_ES))


@njit(cache=True)
def _heure(cash, rq, re, ri, ptN, ptE, AO, AH, AL, BO, BH, BL, p, b, plancher, cap):
    """Une barre d'une heure (seul le RSI(2) peut etre en position) : d'abord le plancher sur le plus bas (prudent : si la
    barre touche le plancher et le plafond, le compte est perdu), puis le plafond du jour (cap > 0 : niveau a atteindre).
    Renvoie (perdu, cash, rq, plafond touche)."""
    if rq == 0:
        return False, cash, rq, False
    if ri == 0:
        a, o, h, l = cash - ptN * rq * re, AO[p, b], AH[p, b], AL[p, b]
        k = ptN * rq
    else:
        a, o, h, l = cash - ptE * rq * re, BO[p, b], BH[p, b], BL[p, b]
        k = ptE * rq
    if a + k * l <= plancher:
        return True, a + k * l, rq, False
    if cap > 0.0 and a + k * h >= cap:
        x = cap if a + k * o < cap else a + k * o
        return False, x - _sortie_rsi(rq, ri), 0, True
    return False, cash, rq, False


@njit(cache=True)
def parcours(debut, h1, h2, variante, plafond_pro, pessimiste, avec_nuit, ptN, ptE, perte, objectif, trace,
             O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu,
             EO, EH, EL, EC, roule_es, AO, AH, AL, AC, BO, BH, BL, BC, na, npost):
    """Un achat a la seance `debut` (RSI(2) a plat). Suivi jusqu'a h2 seances. Renvoie un tableau (voir colonnes).
    perte, objectif : ceux de l'evaluation (controles : tres grands = sans compte). trace[s - 1] : valeur de fin de
    journee de la s-ieme seance (avant un retrait), pour les controles."""
    res = np.zeros(NCOL)
    res[FIN_EVAL], res[PREMIER] = -1.0, -1.0
    nj = O.shape[0]
    fin = min(nj, debut + h2)
    phase = 0                       # 0 evaluation, 1 compte Pro
    cash = 0.0
    zp, ze, actif = 0, 0.0, -1      # zone : contrats signes, prix d'entree, trade en cours
    rq, re, ri = 0, 0.0, 0          # RSI(2) : contrats, prix d'entree, instrument (0 MNQ, 1 MES)
    plancher = -perte
    veille = 0.0
    meilleur, qualif, base = -1e18, 0, 0.0
    bloque = False
    arret = False
    veut = 0
    sans_qualif, inactif = 0, False
    for d in range(debut, fin):
        s = d - debut + 1                   # seances jouees depuis l'achat
        cap = veille + plafond_pro if (phase == 1 and plafond_pro > 0.0) else 0.0
        # ======================= barres de la nuit (de 18 h la veille a 8 h) : journee de trading d
        arret = False
        if avec_nuit == 1 and d > debut:
            p = d - 1
            for b in range(npost[p], na[p]):
                perdu, cash, rq, touche = _heure(cash, rq, re, ri, ptN, ptE, AO, AH, AL, BO, BH, BL, p, b, plancher,
                                                 0.0 if arret else cap)
                if perdu:
                    return _perdu(res, phase, s, inactif)
                arret = arret or touche
        # ======================= seance : minutes de 9 h 30 a la derniere minute
        k = z_deb[d]
        dmin = der[d]
        for t in range(dmin + 1):
            nq = (rq if ri == 0 else 0)
            ne = (rq if ri == 1 else 0)
            if t == dec[d]:
                veut = voulu[d]
                if bloque and veut == 0:
                    bloque = False
                if rq > 0 and (veut == 0 or (ri == 1 and roule_es[d])):
                    if ri == 0:
                        cash += rq * ((O[d, t] - re) * ptN - ORDRE_NQ)
                    else:
                        cash += rq * ((EO[d, t] - re) * ptE - ORDRE_ES)
                    rq = 0
                elif rq == 0 and veut == 1 and not bloque and not arret:
                    vo = cash + ptN * zp * (O[d, t] - ze)
                    inst, n = _rsi_choix(variante, vo - plancher)
                    if n > 0 and not (inst == 1 and roule_es[d]):
                        rq, ri = n, inst
                        if inst == 0:
                            re = O[d, t]
                            cash -= n * ORDRE_NQ
                        else:
                            re = EO[d, t]
                            cash -= n * ORDRE_ES
                nq = (rq if ri == 0 else 0)
                ne = (rq if ri == 1 else 0)
            n_nq = zp + nq
            a = cash - ptN * (zp * ze + nq * re) - ptE * ne * re
            ouv = a + ptN * n_nq * O[d, t] + ptE * ne * EO[d, t]
            if n_nq >= 0:
                haut_n, bas_n = H[d, t], L[d, t]
            else:
                haut_n, bas_n = L[d, t], H[d, t]
            bas = a + ptN * n_nq * bas_n + ptE * ne * EL[d, t]       # pires points additionnes (prudent)
            if n_nq != 0 and ne > 0:
                # deux contrats : on ne sait pas si leurs meilleurs points sont au meme moment -> ouverture ou cloture
                haut = max(ouv, a + ptN * n_nq * C[d, t] + ptE * ne * EC[d, t])
            else:
                haut = a + ptN * n_nq * haut_n + ptE * ne * EH[d, t]
            if bas <= plancher:                                       # le plancher d'abord (prudent)
                return _perdu(res, phase, s, inactif)
            if cap > 0.0 and not arret and (zp != 0 or rq > 0) and haut >= cap:
                x = cap if ouv < cap else ouv
                cash = x - abs(zp) * (FRAIS_ZONE + TICK_NQ) - _sortie_rsi(rq, ri)
                zp, rq, arret, actif = 0, 0, True, -1
            # zone : sortie puis entree a la cloture de la minute
            if actif >= 0 and z_ms[actif] == t:
                cash += zp * (C[d, t] - ze) * ptN - abs(zp) * FRAIS_ZONE
                zp, actif = 0, -1
            while k < z_fin[d] and z_me[k] < t:
                k += 1
            if k < z_fin[d] and z_me[k] == t:
                if z_garde[k] == 1 and zp == 0 and not arret:
                    vc = cash + (ptN * nq * (C[d, t] - re) if ri == 0 else ptE * ne * (EC[d, t] - re))
                    n = _zone_taille(variante, vc - plancher)
                    zp, ze, actif = z_sens[k] * n, C[d, t], k
                k += 1
        # fin de seance : la zone est fermee a la derniere minute
        if zp != 0:
            cash += zp * (C[d, dmin] - ze) * ptN - abs(zp) * FRAIS_ZONE
            zp = 0
        actif = -1
        # ======================= barres de 16 h et 17 h (fin de la journee de trading d)
        pn, pe = C[d, dmin], EC[d, dmin]
        if avec_nuit == 1:
            for b in range(npost[d]):
                perdu, cash, rq, touche = _heure(cash, rq, re, ri, ptN, ptE, AO, AH, AL, BO, BH, BL, d, b, plancher,
                                                 0.0 if arret else cap)
                if perdu:
                    return _perdu(res, phase, s, inactif)
                arret = arret or touche
                pn, pe = AC[d, b], BC[d, b]
        eod = cash + (rq * (pn - re) * ptN if ri == 0 else rq * (pe - re) * ptE)
        if s <= trace.shape[0]:
            trace[s - 1] = eod
        g = eod - veille
        veille = eod
        if g > meilleur:
            meilleur = g
        if g >= 200.0:
            qualif += 1
            sans_qualif = 0
        else:
            sans_qualif += 1
        if phase == 0:
            if eod >= objectif and qualif >= 2 and meilleur <= 0.5 * eod:
                res[ISSUE], res[FIN_EVAL] = 1.0, s
                phase = 1
                cash, zp, rq, veille = 0.0, 0, 0, 0.0
                plancher = -PERTE
                meilleur, qualif, base = -1e18, 0, 0.0
                bloque = veut == 1
                sans_qualif = 0
        else:
            if sans_qualif >= 21 and s <= h1:
                inactif = True
            gain = eod - base
            if eod >= SEUIL_PRO and qualif >= 8 and meilleur <= 0.3 * gain:
                x = min(MAX_RET, np.floor((eod - GARDE_PRO) / 500.0) * 500.0)
                if x >= 500.0:
                    cash -= x
                    veille = eod - x
                    if s <= h1:
                        res[RECU1] += x
                        res[NRET1] += 1
                    res[RECU2] += x
                    if res[PREMIER] < 0:
                        res[PREMIER] = s
                    base, meilleur, qualif = veille, -1e18, 0
                    if pessimiste == 1:
                        plancher = veille - PERTE
    if phase == 1:
        res[FIN_PRO] = -1.0
    if res[ISSUE] == 0.0:
        res[FIN_EVAL] = fin - debut
    res[INACTIF] = 1.0 if inactif else 0.0
    return res


@njit(cache=True)
def _perdu(res, phase, s, inactif):
    res[INACTIF] = 1.0 if inactif else 0.0
    if phase == 0:
        res[ISSUE], res[FIN_EVAL] = -1.0, s
    else:
        res[PRO_PERDU], res[FIN_PRO] = 1.0, s
    return res
