#!/usr/bin/env python3
"""Monte Carlo Bulenox (README.md) : meme logique que vague4/moteur4._parcours4 (challenge puis compte Master), mais
la s-ieme seance du parcours est la vraie seance idx[s] (chemin tire au hasard par blocs de seances), et le moteur
ecrit, seance par seance, le solde du compte, son plancher et la phase. Chaque seance passe par seance4 sans
changement : nuit, zone minute par minute, plancher touche dans la seance, limite du jour, frein MES, plafond."""
import sys
from pathlib import Path

import numpy as np
from numba import njit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vague4"))
import moteur4 as M4  # noqa: E402

seance4 = M4.seance4


@njit(cache=True)
def parcours_mc(idx, rsi, kN, kE, retraits, solde, plancher_tr, phase, O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens,
                z_garde, dec, voulu, NO, NH, NL, nn, EO, EH, EL, EC, ENO, ENH, ENL, enn, reb,
                e_obj, e_perte, e_mode, e_bloc, e_dll, e_regul, e_jmin, f_perte, f_bloc, f_dll, f_jours, f_seuil, f_regul,
                f_min, plafonds, f_part, f_reserve, f_max, c_mnq, cap_f):
    """Comme _parcours4 avec q_ch = q_f = 1, seuil_f = 1e18, reserve = 0, part_cycle = 0, sans pause. idx : seances du
    chemin. retraits[s], solde[s], plancher_tr[s] : retrait, solde (depuis le depart du compte en cours) et plancher a la
    fin de la s-ieme seance ; phase[s] : 1 challenge, 2 Master, 0 apres la fin. Meme tuple de sortie que _parcours4."""
    fin = idx.shape[0]
    cash, veut, pic_rt, pic_eod, veille = 0.0, 0, 0.0, 0.0, 0.0
    plancher = -e_perte
    meilleur, jours = -1e18, 0
    issue, n_ch = 0, 0
    s = 0
    while s < fin:
        d = idx[s]
        zi = 1 if c_mnq > 0.0 and cash - plancher < c_mnq else 0
        perdu, cash, veut, pic_rt, plancher, tr = seance4(d, rsi, veut, cash, pic_rt, plancher, e_mode, e_perte, e_bloc,
                                                          e_dll, O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens,
                                                          z_garde, dec, voulu, NO, NH, NL, nn, EO, EH, EL, EC, ENO, ENH,
                                                          ENL, enn, reb, kN[d], kE[d], 1, zi)
        phase[s] = 1
        if perdu:
            solde[s], plancher_tr[s] = plancher, plancher
            return -1, s + 1, False, 0, 0.0, -1, s + 1
        g = cash - veille
        veille = cash
        jours += 1
        if g > meilleur:
            meilleur = g
        if e_mode == 0:
            if cash > pic_eod:
                pic_eod = cash
            plancher = min(pic_eod - e_perte, e_bloc)
        solde[s], plancher_tr[s] = cash, plancher
        s += 1
        if cash >= e_obj and jours >= e_jmin and (e_regul == 0.0 or meilleur <= e_regul * cash):
            issue, n_ch = 1, s
            break
    if issue != 1:
        return 0, fin, False, 0, 0.0, -1, fin
    cash, pic_eod, veille, base = 0.0, 0.0, 0.0, 0.0
    plancher = -f_perte
    meilleur, qual, n, recu, premier = -1e18, 0, 0, 0.0, -1
    while s < fin:
        d = idx[s]
        zi = 1 if c_mnq > 0.0 and cash - plancher < c_mnq else 0
        perdu, cash, veut, pic_rt, plancher, tr = seance4(d, rsi, veut, cash, 0.0, plancher, 0, f_perte, f_bloc, f_dll,
                                                          O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens, z_garde,
                                                          dec, voulu, NO, NH, NL, nn, EO, EH, EL, EC, ENO, ENH, ENL, enn,
                                                          reb, kN[d], kE[d], 1, zi, cap_f)
        phase[s] = 2
        if perdu:
            solde[s], plancher_tr[s] = plancher, plancher
            return 1, n_ch, True, n, recu, premier, s + 1
        g = cash - veille
        veille = cash
        if (f_seuil > 0.0 and g >= f_seuil) or (f_seuil == 0.0 and tr):
            qual += 1
        if g > meilleur:
            meilleur = g
        if cash > pic_eod:
            pic_eod = cash
        plancher = min(pic_eod - f_perte, f_bloc)
        s += 1
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
                retraits[s - 1] = x
                if premier < 0:
                    premier = s
                base, meilleur, qual = cash, -1e18, 0
        solde[s - 1], plancher_tr[s - 1] = cash, plancher
        if n > 0 and retraits[s - 1] > 0 and f_max > 0 and n >= f_max:
            return 1, n_ch, False, n, recu, premier, s
    return 1, n_ch, False, n, recu, premier, fin
