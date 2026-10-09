#!/usr/bin/env python3
"""Vague 8, descriptif : sensibilite a la lecture de la regle des 50 % de LucidFlex. Les sources se contredisent : 50 % du
gain du cycle (lecture prudente, utilisee partout) ou 50 % du gain total sur le compte (lecture plus large, pipback).
Memes calculs que vague8.py pour les LucidFlex sures de la vague 8 et la meilleure 50K. Ecrit sensibilite.txt."""
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import vague8 as V8  # noqa: E402

W, D4, S = V8.W, V8.D4, V8.S


def main():
    W.regler("regles")
    D = D4.charger()
    W.G["D4"] = D
    W.G["bases"] = {V8.BON: [D4.base(D, g) for g in S.gardes_simules(D, S.rho_2026())[:V8.TIRAGES]]}
    W.G["groupes"] = V8.groupes(D)
    CC = [dict(compte="LucidFlex 50K", zone="zone MNQ", k=2), dict(compte="LucidFlex 100K", zone="zone MNQ", k=1),
          dict(compte="LucidFlex 150K", zone="zone MNQ", k=0)]
    L = ["Sensibilite : LucidFlex avec 50 % du gain TOTAL (au lieu de 50 % du gain du cycle) ; filtre simule aussi bon"
         " qu'en 2026, 10 tirages", ""]
    for pc in (1, 0):
        for k, v in list(V8.COMPTES.items()):
            if k.startswith("LucidFlex"):
                V8.COMPTES[k] = v[:5] + (pc,)
        t1 = [(c, V8.BON, g) for c in CC for g in W.G["groupes"]]
        t2 = [(c, V8.BON, fw) for c in CC for fw in V8.FEN]
        o1, o2 = V8.lancer(V8.achats, t1), V8.lancer(V8.chaine, t2)
        L.append("=== 50 % du gain " + ("du cycle (vague 8)" if pc else "total"))
        L += [f"{V8.nom(c)} | {g} | " + V8.t_achats(x) for (c, _, g), x in zip(t1, o1)]
        L += [f"{V8.nom(c)} | {fw} | " + W.texte(x) for (c, _, fw), x in zip(t2, o2)]
        L.append("")
        print("\n".join(L[-8:]), flush=True)
    (ICI / "sensibilite.txt").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
