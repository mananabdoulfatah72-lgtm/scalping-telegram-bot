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


def facteurs_jour(D):
    """Vague 5 : facteur de chaque seance d (derniere cloture des donnees / cloture de la seance d'avant), NQ et ES."""
    if "facteurs_jour" not in D:
        cn, ce = clotures(D)
        avant_n, avant_e = np.r_[cn[0], cn[:-1]], np.r_[ce[0], ce[:-1]]
        D["facteurs_jour"] = (cn[-1] / avant_n, ce[-1] / avant_e)
    return D["facteurs_jour"]


def facteurs(D, d, niveau):
    """Facteurs du NQ et de l'ES pour un depart a la seance d : derniere cloture des donnees / cloture de la seance d'avant
    (niveau d'aujourd'hui), ou 1 (prix de l'epoque)."""
    if not niveau:
        return 1.0, 1.0
    cn, ce = clotures(D)
    return facteur(cn, d), facteur(ce, d)


def achat(D, b, d, variante, plafond=0.0, pessimiste=0, nuit=1, niveau=True, h1=252, h2=504, perte=M.PERTE,
          objectif=M.OBJECTIF, trace=None, retraits=None, s2f=False, leviers=(1, 1, 1e18, 0.0)):
    """Un achat : Static puis Pro Static (pessimiste=1 : Pro pessimiste), ou S2F 50K (s2f=True). leviers : (m_eval, m_pro,
    seuil_m, reserve) de la vague 5 (par defaut : aucun). niveau : True (niveau d'aujourd'hui, facteur fixe au depart),
    False (prix de l'epoque) ou "jour" (vague 5 : chaque trade au facteur de son jour d'entree)."""
    if niveau == "jour":
        fn, fe = facteurs_jour(D)
    else:
        fn, fe = facteurs(D, d, niveau)
    if trace is None:
        trace = np.zeros(0)
    if retraits is None:
        retraits = np.zeros(0)
    return M.parcours(int(d), h1, h2, M.VARIANTES[variante] if isinstance(variante, str) else variante, plafond,
                      2 if s2f else pessimiste, nuit, 2.0 * fn, 5.0 * fe, perte, objectif, trace, retraits, *b,
                      *leviers)
