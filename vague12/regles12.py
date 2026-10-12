#!/usr/bin/env python3
"""Vague 12 (README.md) : comptes, candidates et achats, communs au calcul (vague12.py) et aux controles
(test_vague12.py). Le moteur est vague4/moteur4 (parcours4) avec la limite du challenge (lim_ch) et le frein du compte
finance (c_mnq_f) ajoutes pour cette vague ; les donnees et le filtre simule sont ceux du Monte Carlo (montecarlo.py)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
R0 = ICI.parent
sys.path.insert(0, str(R0 / "montecarlo"))
import montecarlo as MC  # noqa: E402

B, M4 = MC.B, MC.M4
H = 504                                             # argent net d'un achat : sur ses 24 premiers mois
PLAFOND = 500.0                                     # plafond du jour sur le Master Bulenox (vague 11)
F_MOMENTUM = (2250.0, 100.0, 1200.0, 5, 150.0, 0.35, 1000.0, np.array([1500.0, 1500.0, 1500.0, 1e9]), 0.0, 2600.0, 3)
F_FLEX = (1500.0, 0.0, 0.0, 5, 200.0, 0.0, 250.0, np.array([1500.0]), 0.5, 1500.0, 5)
F_SANS = (0.0, 0.0, 0.0, 10, 0.0, 0.0, 1e9, np.array([1e9]), 0.0, 0.0, 1)      # compte finance non simule (Goat)
COMPTES = {
    "legacy": dict(nom="Bulenox Legacy 50K option 2", E=(3000.0, 2500.0, 0, 100.0, 1100.0, 0.0, 1), F=B.F, frein=1750.0,
                   trente=True, prix=19.25, activation=148.0, part=1.0, cap=PLAFOND, cycle=0, finance=True),
    "momentum": dict(nom="Bulenox Momentum EOD 50K", E=(3000.0, 2250.0, 0, 100.0, 1200.0, 0.0, 1), F=F_MOMENTUM,
                     frein=1500.0, trente=True, prix=143.0, activation=0.0, part=1.0, cap=PLAFOND, cycle=0, finance=True),
    "momentum_masterlegacy": dict(nom="Bulenox Momentum EOD 50K (Master aux regles Legacy)",
                                  E=(3000.0, 2250.0, 0, 100.0, 1200.0, 0.0, 1), F=B.F, frein=1500.0, trente=True,
                                  prix=143.0, activation=0.0, part=1.0, cap=PLAFOND, cycle=0, finance=True),
    "goat": dict(nom="Goat Funded Futures EOD 50K", E=(3000.0, 2000.0, 0, 100.0, 0.0, 0.5, 1), F=F_SANS, frein=1250.0,
                 trente=False, prix=34.5, activation=0.0, part=1.0, cap=0.0, cycle=0, finance=False),
    "flex": dict(nom="FundedNext Futures Flex 50K", E=(2500.0, 1500.0, 0, 0.0, 0.0, 0.40, 1), F=F_FLEX, frein=750.0,
                 trente=False, prix=69.99, activation=0.0, part=0.95, cap=0.0, cycle=1, finance=True),
}


def candidates():
    """(nom, compte, taille en challenge, seuil du frein en challenge, seuil du frein au compte finance)."""
    L = []
    for c in ("legacy", "momentum", "momentum_masterlegacy"):
        fr = COMPTES[c]["frein"]
        for q in (1, 2, 3, 4):
            for avec in (True, False):
                L.append((f"{c} | taille {q} | {'frein' if avec else 'sans frein'}", c, q, fr if avec else 0.0, fr))
    L.append(("goat | taille 1 | frein", "goat", 1, 1250.0, 1250.0))
    L.append(("goat | taille 1 | sans frein", "goat", 1, 0.0, 0.0))
    L.append(("flex | taille 1 | zone toujours sur MES", "flex", 1, 1e18, 1e18))
    L.append(("flex | taille 1 | zone MNQ, frein", "flex", 1, 750.0, 750.0))
    return L


def achats(P):
    """Jours d'achat : chaque seance du 3 janvier 2012 au 26 aout 2026 (les 30 jours tiennent dans les donnees), groupes,
    fin du suivi de chaque groupe (choix : rien apres le 31 decembre 2022) et seances dans les 30 jours de chaque achat."""
    j = P["jours"]
    nj = len(j)
    t = pd.Timestamp
    i = lambda x: int(np.searchsorted(j, t(x)))                                          # noqa: E731
    d0, d1 = i("2012-01-03"), i("2026-08-27")
    lim = np.array([i(j[d] + pd.Timedelta(days=30)) - d for d in range(nj)])
    groupes = {"choix 2012-2021": (i("2012-01-01"), i("2022-01-01"), i("2023-01-01")),
               "verification 2023 - aout 2026": (i("2023-01-01"), d1, nj),
               "2025": (i("2025-01-01"), i("2026-01-01"), nj)}
    return d0, d1, lim, groupes


def un_achat(P, b, d, compte, q, c_ch, c_f, sv, lim):
    """Un achat le jour d : sortie de parcours4 et retraits seance par seance (sv seances de suivi)."""
    A = COMPTES[compte]
    ret = np.zeros(max(sv, 1))
    r = M4.parcours4(d, 4, P["kN"], P["kE"], ret, *b, *A["E"], *A["F"], sv, q, 1, 1e18, 0.0, A["cycle"], c_ch, 0.0, 0,
                     A["cap"], int(lim) if A["trente"] else 0, c_f)
    return r, ret
