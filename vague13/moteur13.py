#!/usr/bin/env python3
"""Vague 13 (README.md) : le challenge et le compte finance de vague4/moteur4._parcours4, separes en deux fonctions
pour ajouter les leviers du challenge et garder la trace seance par seance (solde, plancher, taille) :
- defi13 : challenge avec limite de seances, arret a l'objectif (plafond du jour = objectif + marge - solde), taille
  adaptative (protection sous un coussin, fin de course, prudence pres du but) ;
- master13 : compte finance, recopie de la boucle de _parcours4 (sans pause : Bulenox n'en a pas).
Sans levier, defi13 puis master13 redonnent exactement parcours4 (test_vague13.py). Les seances passent toujours par
moteur4.seance4, sans changement."""
import sys
from pathlib import Path

import numpy as np
from numba import njit

R0 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R0 / "vague4"))
import moteur4 as M4  # noqa: E402

seance4 = M4.seance4


@njit(cache=True)
def defi13(debut, lim, rsi, kN, kE, O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu, NO, NH, NL,
           nn, EO, EH, EL, EC, ENO, ENH, ENL, enn, reb, e_obj, e_perte, e_mode, e_bloc, e_dll, e_regul, e_jmin, q_ch,
           c_mnq, arret_obj, marge, q_bas, seuil_bas, q_fin, n_fin, q_but, seuil_but, t_solde, t_plancher, t_taille):
    """Renvoie (issue 1 valide / -1 perdu / 0 expire, seances jouees, position voulue pour la nuit, seance suivante).
    t_solde, t_plancher, t_taille (taille >= lim) : solde et plancher a la fin de chaque seance, taille jouee."""
    nj = O.shape[0]
    fin = min(nj, debut + lim)
    cash, veut, pic_rt, pic_eod, veille = 0.0, 0, 0.0, 0.0, 0.0
    plancher = -e_perte
    meilleur, jours = -1e18, 0
    d = debut
    while d < fin:
        zi = 1 if c_mnq > 0.0 and cash - plancher < c_mnq else 0
        qc = q_ch
        reste = lim - (d - debut)
        if seuil_but > 0.0 and e_obj - cash < seuil_but:
            qc = q_but
        if n_fin > 0 and reste <= n_fin:
            qc = q_fin
        if seuil_bas > 0.0 and cash - plancher < seuil_bas:
            qc = q_bas
        cap = e_obj + marge - cash if arret_obj == 1 else 0.0
        if cap < 0.0:
            cap = 0.0
        perdu, cash, veut, pic_rt, plancher, tr = seance4(d, rsi, veut, cash, pic_rt, plancher, e_mode, e_perte, e_bloc,
                                                          e_dll, O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens,
                                                          z_garde, dec, voulu, NO, NH, NL, nn, EO, EH, EL, EC, ENO, ENH,
                                                          ENL, enn, reb, kN[d], kE[d], qc, zi, cap)
        s = d - debut
        t_solde[s], t_plancher[s], t_taille[s] = cash, plancher, qc * (1 - 2 * zi)
        if perdu:
            return -1, s + 1, veut, d + 1
        g = cash - veille
        veille = cash
        jours += 1
        if g > meilleur:
            meilleur = g
        if e_mode == 0:
            if cash > pic_eod:
                pic_eod = cash
            plancher = min(pic_eod - e_perte, e_bloc)
            t_plancher[s] = plancher
        d += 1
        if cash >= e_obj and jours >= e_jmin and (e_regul == 0.0 or meilleur <= e_regul * cash):
            return 1, d - debut, veut, d
    return 0, fin - debut, veut, fin


@njit(cache=True)
def master13(debut, d, veut, fin, rsi, kN, kE, retraits, O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens, z_garde,
             dec, voulu, NO, NH, NL, nn, EO, EH, EL, EC, ENO, ENH, ENL, enn, reb, f_perte, f_bloc, f_dll, f_jours,
             f_seuil, f_regul, f_min, plafonds, f_part, f_reserve, f_max, part_cycle, c_mnq_f, cap_f):
    """Compte finance de la seance d a fin (exclue), taille 1, comme la 2e boucle de _parcours4 (q_f = 1, sans pause,
    sans reserve). Renvoie (perdu, retraits, recu, seance du 1er retrait depuis l'achat, seances jouees depuis l'achat).
    retraits[s] : retrait a la fin de la s-ieme seance apres l'achat (debut)."""
    cash, pic_eod, veille, base = 0.0, 0.0, 0.0, 0.0
    plancher = -f_perte
    meilleur, qual, n, recu, premier = -1e18, 0, 0, 0.0, -1
    while d < fin:
        zi = 1 if c_mnq_f > 0.0 and cash - plancher < c_mnq_f else 0
        perdu, cash, veut, pic_rt, plancher, tr = seance4(d, rsi, veut, cash, 0.0, plancher, 0, f_perte, f_bloc, f_dll,
                                                          O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens, z_garde,
                                                          dec, voulu, NO, NH, NL, nn, EO, EH, EL, EC, ENO, ENH, ENL, enn,
                                                          reb, kN[d], kE[d], 1, zi, cap_f)
        if perdu:
            return True, n, recu, premier, d - debut + 1
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
                x = min(x, f_part * (gain if part_cycle == 1 else cash))
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
                    return False, n, recu, premier, d - debut
    return False, n, recu, premier, fin - debut
