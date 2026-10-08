#!/usr/bin/env python3
"""Outils communs de static50k : tableaux passes au moteur, facteur de prix « au niveau d'aujourd'hui », lancement d'un
achat."""
import numpy as np

import donnees as DN
import moteur_static as M


def base(D, garde=None):
    """Tableaux du moteur (dans l'ordre de moteur_static.parcours, apres trace). garde : trades de zone gardes (None : tous)."""
    nj = len(D["jours"])
    if garde is None:
        garde = np.ones(len(D["Z"]), bool)
    zt = DN.P.tableaux_zone(D["Z"], nj, garde)
    return (D["O"], D["H"], D["L"], D["C"], D["derniere"], *zt, D["dec"], D["voulu"], D["EO"], D["EH"], D["EL"],
            D["EC"], D["roule_es"], D["AO"], D["AH"], D["AL"], D["AC"], D["BO"], D["BH"], D["BL"], D["BC"], D["na"],
            D["npost"])


def clotures(D):
    """Cloture de chaque seance (NQ, ES), calculee une fois et gardee dans D."""
    if "clotures" not in D:
        nj = len(D["jours"])
        der = D["derniere"]
        D["clotures"] = (D["C"][np.arange(nj), der], D["EC"][np.arange(nj), der])
    return D["clotures"]


def departs(D, pas=5):
    """Departs possibles : une seance sur `pas` parmi celles ou le RSI(2) est a plat, apres 260 seances d'historique."""
    nj = len(D["jours"])
    return [d for d in range(260, nj) if D["ouvert"][d] == 0][::pas]


def facteur(cl, d):
    """Niveau d'aujourd'hui : derniere cloture des donnees / cloture de la seance qui precede le depart d."""
    return cl[-1] / cl[d - 1]


def facteurs(D, d, niveau):
    """Facteurs du NQ et de l'ES pour un depart a la seance d : derniere cloture des donnees / cloture de la seance d'avant
    (niveau d'aujourd'hui), ou 1 (prix de l'epoque)."""
    if not niveau:
        return 1.0, 1.0
    cn, ce = clotures(D)
    return facteur(cn, d), facteur(ce, d)


def achat(D, b, d, variante, plafond=0.0, pessimiste=0, nuit=1, niveau=True, h1=252, h2=504, perte=M.PERTE,
          objectif=M.OBJECTIF, trace=None):
    fn, fe = facteurs(D, d, niveau)
    if trace is None:
        trace = np.zeros(0)
    return M.parcours(int(d), h1, h2, M.VARIANTES[variante] if isinstance(variante, str) else variante, plafond,
                      pessimiste, nuit, 2.0 * fn, 5.0 * fe, perte, objectif, trace, *b)
