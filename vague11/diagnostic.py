#!/usr/bin/env python3
"""Vague 11, diagnostic : qu'est-ce qui ralentit les retraits du compte Master Bulenox 50K ? (bot de la vague 10, frein MES
des 750 $ sous le plus haut, un seul achat). On enleve une regle a la fois pour voir laquelle freine : regularite 40 %,
minimum de 1 000 $, plafond de 1 500 $ ; et on essaie 2 MNQ sur le Master quand le coussin est grand. Ecrit diagnostic.txt."""
import sys
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "vague10"))
import budget30 as B  # noqa: E402

V8, S9, W, D4, M4 = B.V8, B.S9, B.W, B.D4, B.M4


def F(regul=0.40, mini=1000.0, plaf=1500.0):
    return (2500.0, 100.0, 1100.0, 10, 0.0, regul, mini, np.array([plaf, plaf, plaf, 1e9]), 0.0, 2600.0, 3)


VARIANTES = {"regles Bulenox (reference)": (F(), 1, 1e18),
             "sans la regle des 40 %": (F(regul=0.0), 1, 1e18),
             "minimum 500 $ au lieu de 1 000 $": (F(mini=500.0), 1, 1e18),
             "plafond 3 000 $ au lieu de 1 500 $": (F(plaf=3000.0), 1, 1e18),
             "2 MNQ sur le Master des 4 000 $ de coussin": (F(), 2, 4000.0),
             "2 MNQ sur le Master des 3 500 $ de coussin": (F(), 2, 3500.0)}


def main():
    W.regler("regles")
    D, T, a3, gardes = S9.charger()
    C, _, _ = S9.conditions(D, T, gardes)
    bases = [D4.base(D, g & C["pas un jour de la Fed"]) for g in gardes]
    kN, kE = D4.facteurs_jour(D)
    G = V8.groupes(D)
    L = []
    for g in ("achats 2012-2021", "achats 2023 - mars 2026"):
        cap = V8.fin_groupe(D, g)
        for nom, (f_, qf, sf) in VARIANTES.items():
            iss, r1, r3, perdu12 = [], [], [], []
            for b in bases:
                for d in G[g]:
                    sv = min(V8.H_SUIVI, cap - d)
                    if sv < V8.H:
                        continue
                    ret = np.zeros(sv)
                    r = M4.parcours4(d, 4, 2.0 * kN, 5.0 * kE, ret, *b, *B.E, *f_, sv, 1, qf, sf, 0.0, 0, 1750.0)
                    iss.append(r[0])
                    if r[0] != 1:
                        continue
                    idx = np.flatnonzero(ret > 0)
                    r1.append(idx[0] + 1 if len(idx) else np.nan)
                    r3.append(idx[2] + 1 if len(idx) > 2 else np.nan)
                    if sv - r[1] >= 252:
                        fin = r[6] if r[2] else sv
                        perdu12.append(bool(r[2]) and fin - r[1] <= 252)
            r1, r3 = np.array(r1), np.array(r3)
            L.append(f"{g} | {nom} : challenge perdu {np.mean(np.array(iss) == -1):.0%} ; 1er retrait au mois"
                     f" {np.nanmedian(r1) / 21:.1f} ; 3e retrait au mois {np.nanmedian(r3) / 21:.1f} (atteint"
                     f" {np.mean(~np.isnan(r3)):.0%}) ; Master perdu en 12 mois {np.mean(perdu12):.0%}")
            print(L[-1], flush=True)
    (ICI / "diagnostic.txt").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
