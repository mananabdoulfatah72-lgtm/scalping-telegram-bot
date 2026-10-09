#!/usr/bin/env python3
"""Vague 9 : la regle retenue (pas de trade de zone les jours d'annonce de la Fed) recalculee avec le moteur exact de
la vague 8 (plancher contrôle minute par minute, retraits, prix) sur LucidFlex, Topstep et FundedNext Legacy 50K, zone
1 MNQ, coussin garde 0, 1x, 2x ; avec et sans la regle. Ecrit vague9_exact.txt."""
import sys
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI.parent / "vague8"))
import socle9 as S9  # noqa: E402
import vague8 as V8  # noqa: E402

W, D4 = V8.W, V8.D4


def main():
    W.regler("regles")
    D, T, a3, gardes = S9.charger()
    C, _, _ = S9.conditions(D, T, gardes)
    fed = C["pas un jour de la Fed"]
    W.G["D4"] = D
    W.G["groupes"] = V8.groupes(D)
    SC = {"bot": [D4.base(D, g) for g in gardes], "bot sans les jours de la Fed": [D4.base(D, g & fed) for g in gardes]}
    W.G["bases"] = SC
    CC = [dict(compte=k, zone="zone MNQ", k=kk) for k in ("LucidFlex 50K", "Topstep 50K", "FundedNext Legacy 50K")
          for kk in (0, 1, 2)]
    t1 = [(c, sc, g) for c in CC for sc in SC for g in W.G["groupes"]]
    t2 = [(c, sc, fw) for c in CC for sc in SC for fw in V8.FEN]
    o1, o2 = V8.lancer(V8.achats, t1), V8.lancer(V8.chaine, t2)
    L = ["Vague 9 : regle retenue (pas de zone les jours de la Fed), moteur exact de la vague 8, filtre simule (10 tirages)", ""]
    for c in CC:
        for sc in SC:
            L.append(f"=== {V8.nom(c)} | {sc}")
            L += [f"  {g} : " + V8.t_achats(x) for (c_, s_, g), x in zip(t1, o1) if c_ == c and s_ == sc]
            L += [f"  {fw} : " + W.texte(x) for (c_, s_, fw), x in zip(t2, o2) if c_ == c and s_ == sc]
    (ICI / "vague9_exact.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
