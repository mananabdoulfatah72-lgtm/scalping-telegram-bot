#!/usr/bin/env python3
"""Monte Carlo v2 (README.md) : moteur journalier. Meme logique que moteur_mc.parcours_mc, mais chaque seance est lue
dans les tables exactes (tables.py) au lieu d'etre rejouee minute par minute. C'est ce moteur qui tourne dans la page
(port JavaScript : moteur_jour.js) ; test_v2.py verifie qu'il redonne parcours_mc."""
import numpy as np
from numba import njit

NC = 3                                             # plafonds 0, 500, 750 $


@njit(cache=True)
def parcours_jour(lignes, gain, pire, drap, ci_master, c_mnq, e_obj, e_perte, e_bloc, f_perte, f_bloc, f_jours, f_regul,
                  f_min, f_plaf, f_reserve, f_max, retraits):
    """lignes : ligne de chaque seance du chemin dans les tables (d'un tirage). Sortie comme parcours_mc."""
    fin = lignes.shape[0]
    cash, veut, pic_eod, veille = 0.0, 0, 0.0, 0.0
    plancher = -e_perte
    jours = 0
    issue, n_ch = 0, 0
    s = 0
    while s < fin:
        a = lignes[s]
        zi = 1 if c_mnq > 0.0 and cash - plancher < c_mnq else 0
        k = (veut * 2 + zi) * NC
        if plancher - cash >= pire[a, k]:
            return -1, s + 1, False, 0, 0.0, -1, s + 1
        cash += gain[a, k]
        veut = drap[a, k] >> 1
        jours += 1
        if cash > pic_eod:
            pic_eod = cash
        plancher = min(pic_eod - e_perte, e_bloc)
        s += 1
        if cash >= e_obj and jours >= 1:
            issue, n_ch = 1, s
            break
    if issue != 1:
        return 0, fin, False, 0, 0.0, -1, fin
    cash, pic_eod, veille, base = 0.0, 0.0, 0.0, 0.0
    plancher = -f_perte
    meilleur, qual, n, recu, premier = -1e18, 0, 0, 0.0, -1
    while s < fin:
        a = lignes[s]
        zi = 1 if c_mnq > 0.0 and cash - plancher < c_mnq else 0
        k = (veut * 2 + zi) * NC + ci_master
        if plancher - cash >= pire[a, k]:
            return 1, n_ch, True, n, recu, premier, s + 1
        cash += gain[a, k]
        veut = drap[a, k] >> 1
        g = cash - veille
        veille = cash
        if drap[a, k] & 1:
            qual += 1
        if g > meilleur:
            meilleur = g
        if cash > pic_eod:
            pic_eod = cash
        plancher = min(pic_eod - f_perte, f_bloc)
        s += 1
        gain_c = cash - base
        if qual >= f_jours and gain_c > 0.0 and (f_regul == 0.0 or meilleur <= f_regul * gain_c):
            x = min(f_plaf, cash - f_reserve)
            if x >= f_min:
                cash -= x
                veille = cash
                recu += x
                n += 1
                retraits[s - 1] = x
                if premier < 0:
                    premier = s
                base, meilleur, qual = cash, -1e18, 0
                if f_max > 0 and n >= f_max:
                    return 1, n_ch, False, n, recu, premier, s
    return 1, n_ch, False, n, recu, premier, fin
