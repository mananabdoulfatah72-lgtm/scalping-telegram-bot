"""Descriptif (pas un test) : le compte Master dans sa situation du 11 novembre 2026 (solde 50 700 $, plus haut de fin
de journee 51 800 $, plancher 49 300 $, marge 1 400 $), rejoue depuis chaque seance de 2017 a 2026 avec le bot seul.
Usage : python3 situation.py [solde] [plus_haut]"""
import sys

import numpy as np

import compte as Cp
import donnees as D

SOLDE = float(sys.argv[1]) if len(sys.argv) > 1 else 50700.0
HAUT = float(sys.argv[2]) if len(sys.argv) > 2 else 51800.0
B = Cp.Banc("2026-11-02")
L = [f"Situation du compte : solde {SOLDE:,.0f} $, plus haut de fin de journée {HAUT:,.0f} $, plancher {min(HAUT - 2500, 50000):,.0f} $, "
     f"marge {SOLDE - min(HAUT - 2500, 50000):,.0f} $.".replace(",", " "),
     "Le bot seul (Z12F, limite du jour 1 000 $), rejoué depuis chaque séance de 2017 à novembre 2026, 120 séances au plus.",
     "La règle d'inactivité n'est pas comptée ici (elle se règle à part). Descriptif, pas un test.", "",
     f"{'taille':<34}{'perdu par le plancher':>22}{'solde ≥ 53 600 $':>18}{'ni l un ni l autre':>20}{'séances (médiane) jusqu à 53 600 $':>36}"]
for nom, n, frein in (("1 MNQ, frein (demi-taille)", 1.0, 750.0), ("1 MNQ, sans frein", 1.0, 0.0), ("2 MNQ, frein", 2.0, 750.0), ("2 MNQ, sans frein", 2.0, 0.0),
                      ("4 MNQ, frein", 4.0, 750.0), ("4 MNQ, sans frein", 4.0, 0.0)):
    R0, D0 = B.journees(B.zf, n, 1000.0); R1, D1 = B.journees(B.zf, n / 2, 1000.0)
    issue = []; duree = []
    for i0 in range(B.d17, B.n - 120, 5):
        solde, haut, fin = SOLDE, HAUT, "rien"
        for i in range(i0, i0 + 120):
            pl = min(haut - 2500.0, 50000.0)
            R, Dp = (R1, D1) if frein > 0 and solde - pl < 2500.0 - frein else (R0, D0)
            if solde + Dp[i] <= pl:
                fin = "perdu"; break
            solde += R[i]; haut = max(haut, solde)
            if solde >= 53600.0:
                fin = "retrait"; duree.append(i - i0 + 1); break
        issue.append(fin)
    issue = np.array(issue)
    L.append(f"{nom:<34}{(issue == 'perdu').mean():>21.0%} {(issue == 'retrait').mean():>17.0%} {(issue == 'rien').mean():>19.0%} {np.median(duree) if duree else float('nan'):>35.0f}")
(D.ICI / "resultats/situation.txt").write_text("\n".join(L) + "\n")
print("\n".join(L))
