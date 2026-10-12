#!/usr/bin/env python3
"""Vague 13 (README.md) : candidates et achat complet (challenge defi13 puis Master master13), sur les donnees, le
filtre simule et les comptes de la vague 12 (vague12/regles12.py)."""
import sys
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "vague12"))
sys.path.insert(0, str(ICI))
import regles12 as K  # noqa: E402
import moteur13 as M13  # noqa: E402

MARGE = 50.0
LEVIERS = {   # (arret a l'objectif, protection, fin de course, prudence pres du but)
    "A": (0, False, False, False), "B": (1, False, False, False), "C": (1, True, False, False),
    "D": (1, False, True, False), "E": (1, True, True, False), "F": (1, False, False, True)}


def candidates():
    return [(f"{c} | {l}", c, l) for c in ("legacy", "momentum") for l in LEVIERS]


def args_defi(compte, lettre):
    A = K.COMPTES[compte]
    arret, prot, finc, but = LEVIERS[lettre]
    return (*A["E"], 4, 0.0, arret, MARGE, 2 if prot else 0, A["E"][1] / 2 if prot else 0.0, 6 if finc else 0,
            5 if finc else 0, 2 if but else 0, 1000.0 if but else 0.0)


def un_achat(P, b, d, compte, lettre, sv, lim, traces=False):
    """Achat le jour d : (issue, seances du challenge, Master perdu, retraits, recu, 1er retrait, fin), retraits par
    seance (sv seances), et si traces : solde, plancher, taille du challenge."""
    A = K.COMPTES[compte]
    ts, tp, tt = np.zeros(lim + 1), np.zeros(lim + 1), np.zeros(lim + 1, np.int64)
    iss, nch, veut, d2 = M13.defi13(d, int(lim), 4, P["kN"], P["kE"], *b, *args_defi(compte, lettre), ts, tp, tt)
    ret = np.zeros(max(sv, 1))
    if iss != 1:
        r = (iss, nch, False, 0, 0.0, -1, nch)
    else:
        F = A["F"]
        perdu, n, recu, prem, fin = M13.master13(d, d2, veut, min(len(P["jours"]), d + sv), 4, P["kN"], P["kE"], ret, *b,
                                                 *F[:9], F[9], F[10], A["cycle"], A["frein"], A["cap"])
        r = (1, nch, perdu, n, recu, prem, fin)
    return (r, ret, (ts[:nch], tp[:nch], tt[:nch])) if traces else (r, ret)
