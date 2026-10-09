#!/usr/bin/env python3
"""Vague 10, diagnostic : comment meurent les comptes 50K achetes en 2025 (bot zone 1 MNQ + RSI(2) de nuit sur 1 MES,
filtre simule aussi bon qu'en 2026, 10 tirages). Pour chaque compte : challenge perdu avec la regle de regularite et sans
elle (combien de challenges ont atteint l'objectif mais etaient bloques par la regularite) ; mois ou le challenge est
perdu ; mois ou le compte finance est perdu. Ecrit diagnostic2025.txt."""
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "vague8"))
import vague8 as V8  # noqa: E402

W, D4, M4, S = V8.W, V8.D4, V8.M4, V8.S


def main():
    W.regler("regles")
    D = D4.charger()
    j = D["jours"]
    kN, kE = D4.facteurs_jour(D)
    gardes = S.gardes_simules(D, S.rho_2026())[:10]
    bases = [D4.base(D, g) for g in gardes]
    G = V8.groupes(D)
    L = []
    for compte in ("LucidFlex 50K", "Topstep 50K", "FundedNext Legacy 50K"):
        c = dict(compte=compte, zone="zone MNQ", k=2)
        e, f_, part, prix, c_mnq, pc = V8.reglages(c)
        for gnom in ("achats 2012-2021", "achats 2025 - mars 2026"):
            cap = V8.fin_groupe(D, gnom)
            mort_ch, mort_f, n, perdu, perdu_sans, bloque = Counter(), Counter(), 0, 0, 0, 0
            for b in bases:
                for d in G[gnom]:
                    sv = min(V8.H_SUIVI, cap - d)
                    r = M4.parcours4(d, 4, 2.0 * kN, 5.0 * kE, np.zeros(0), *b, *e, *f_, sv, 1, 1, 1e18, 0.0, pc, 0.0)
                    e0 = e[:5] + (0.0,) + e[6:]
                    r0 = M4.parcours4(d, 4, 2.0 * kN, 5.0 * kE, np.zeros(0), *b, *e0, *f_, sv, 1, 1, 1e18, 0.0, pc, 0.0)
                    n += 1
                    if r[0] == -1:
                        perdu += 1
                        mort_ch[str(pd.Timestamp(j[d + r[1] - 1]).to_period("M"))] += 1
                        if r0[0] == 1:
                            bloque += 1
                    if r0[0] == -1:
                        perdu_sans += 1
                    if r[0] == 1 and r[2]:
                        mort_f[str(pd.Timestamp(j[d + r[6] - 1]).to_period("M"))] += 1
            L += [f"=== {compte}, garder 4 000 $ | {gnom} ({n} achats x tirages)",
                  f"challenge perdu : {perdu / n:.0%} avec la regle de regularite, {perdu_sans / n:.0%} sans elle ;"
                  f" challenges perdus qui auraient ete reussis sans la regle : {bloque / max(perdu, 1):.0%}"]
            if gnom.startswith("achats 2025"):
                L.append("mois ou le challenge est perdu : " + ", ".join(f"{k} {v}" for k, v in sorted(mort_ch.items())))
                L.append("mois ou le compte finance est perdu : " + ", ".join(f"{k} {v}" for k, v in sorted(mort_f.items())))
    (ICI / "diagnostic2025.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
