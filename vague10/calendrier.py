#!/usr/bin/env python3
"""Vague 10, descriptif : calendrier d'un seul achat Bulenox 50K (frein MES des 750 $ sous le plus haut, bot de la vague 10)
: mois du 1er, 2e et 3e retrait apres l'achat, ecart entre retraits, montants. Ecrit calendrier.txt."""
import sys
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import budget30 as B  # noqa: E402

V8, S9, W, D4, M4 = B.V8, B.S9, B.W, B.D4, B.M4


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
        val, r1, r2, r3, ec, mt = [], [], [], [], [], []
        for b in bases:
            for d in G[g]:
                sv = min(V8.H_SUIVI, cap - d)
                if sv < V8.H:
                    continue                                   # seulement les achats suivis 24 mois
                ret = np.zeros(sv)
                r = M4.parcours4(d, 4, 2.0 * kN, 5.0 * kE, ret, *b, *B.E, *B.F, sv, 1, 1, 1e18, 0.0, 0, 1750.0)
                if r[0] != 1:
                    continue
                val.append(r[1])
                idx = np.flatnonzero(ret > 0)
                for k, lst in enumerate((r1, r2, r3)):
                    if len(idx) > k:
                        lst.append(idx[k] + 1)
                ec += list(np.diff(idx))
                mt += list(ret[idx])
        m = lambda x: np.median(x) / V8.MOIS                                              # noqa: E731
        L.append(f"{g} (achats valides et suivis 24 mois, {len(val)}) : validation au mois {m(val):.1f} ; 1er retrait au mois"
                 f" {m(r1):.1f} ({len(r1) / len(val):.0%} en ont un) ; 2e au mois {m(r2):.1f} ({len(r2) / len(val):.0%}) ;"
                 f" 3e au mois {m(r3):.1f} ({len(r3) / len(val):.0%}) ; ecart entre retraits {m(ec):.1f} mois ;"
                 f" montant moyen {np.mean(mt):,.0f} $")
        print(L[-1], flush=True)
    (ICI / "calendrier.txt").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
