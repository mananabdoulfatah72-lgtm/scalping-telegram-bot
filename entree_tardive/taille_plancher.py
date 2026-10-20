#!/usr/bin/env python3
"""Descriptif (aucune regle fixee a l'avance) : challenge Bulenox depuis 0 avec 16 seances, selon le plancher deja
atteint et la taille jouee. Meme moteur et memes tirages du filtre que chances.py (filtre aussi bon qu'en 2026), sans
RSI(2) de nuit, limite du jour du bot 1 000 $, arret a +3 050 $. Ecrit taille_plancher.txt. Lancement : comme challenge.py."""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np  # noqa: E402

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import chances as CS  # noqa: E402

R13 = CS.R13
# (nom, q_ch, q_bas, seuil_bas, q_fin, n_fin) ; le reste des leviers comme la version D (arret a l'objectif, marge 50)
TAILLES = [("4 MNQ, 6 les 5 dernieres (reglage actuel)", 4, 0, 0.0, 6, 5),
           ("4 MNQ sans fin de course", 4, 0, 0.0, 0, 0),
           ("3 MNQ, 6 les 5 dernieres", 3, 0, 0.0, 6, 5),
           ("3 MNQ sans fin de course", 3, 0, 0.0, 0, 0),
           ("2 MNQ, 6 les 5 dernieres", 2, 0, 0.0, 6, 5),
           ("4 MNQ, 2 sous 1 250 $ de coussin, 6 les 5 dernieres", 4, 2, 1250.0, 6, 5)]


def main():
    K = R13.K
    P = K.MC.preparer()
    d0, d1, _, groupes = K.achats(P)
    args = R13.args_defi("legacy", "D")
    compte = (*args[:4], 1000.0, *args[5:7])
    lv = list(args[7:])                       # q_ch, c_mnq, arret_obj, marge, q_bas, seuil_bas, q_fin, n_fin, q_but, seuil_but
    defi = CS.defi_pic()
    L = [__doc__.splitlines()[0], "Valide / perdu / expire en % des departs (10 tirages du filtre aussi bon qu'en 2026).", ""]
    for pic0 in (0.0, 500.0, 1000.0, 1500.0):
        L.append(f"== plus haut de fin de journee {50000 + pic0:,.0f} $, plancher {50000 + pic0 - 2500:,.0f} $, solde 50 000 $")
        for nom, q, qb, sb, qf, nf in TAILLES:
            lev = (q, lv[1], lv[2], lv[3], qb, sb, qf, nf, lv[8], lv[9])
            cells = []
            for g in ("choix 2012-2021", "verification 2023 - aout 2026"):
                a, z = groupes[g][:2]
                dd = np.arange(max(a, d0), min(z, d1), dtype=np.int64)
                iss = np.array([defi(int(d), 16, 0, P["kN"], P["kE"], *b, *compte, *lev, np.zeros(17), np.zeros(17),
                                     np.zeros(17, np.int64), pic0)[0] for b in P["bases"]["fort"] for d in dd])
                cells.append(f"{g[:12]} {100 * (iss == 1).mean():5.1f} / {100 * (iss == -1).mean():5.1f} / {100 * (iss == 0).mean():5.1f}")
            L.append(f"    {nom:<52} " + "  |  ".join(cells))
        L.append("")
    (ICI / "taille_plancher.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
