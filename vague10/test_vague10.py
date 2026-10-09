#!/usr/bin/env python3
"""Controle de la vague 10 : la pause arrete le bot n_pause seances quand le coussin de la veille passe sous c_pause, puis
se rearme quand le coussin repasse au-dessus. Marche synthetique de test_vague8 : un trade de zone par jour, vente les 6
premiers jours (-200 $ chacun), achat ensuite (+194 $). Objectif sonde : +100 $ ; on lit le jour ou il est atteint."""
import sys
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "vague8"))
import test_vague8 as T8  # noqa: E402

M4 = T8.M4


def test_pause():
    nj = 40
    b = list(T8.marche(nj, 98.5, 0.0))
    sens = b[9].copy()
    sens[:6] = -1
    b[9] = sens
    e = (100.0, 2000.0, 0, 0.0, 0.0, 0.0, 1)               # le plancher reste a -2 000 $ (aucun plus haut positif)
    f_ = (2000.0, 0.0, 0.0, 5, 150.0, 0.0, 500.0, np.array([2000.0]), 0.5, 0.0, 0)
    # sans pause : 6 pertes (-1 200 $), puis -1 200 + 7 x 194 = +158 -> objectif au jour 13
    # pause 5 seances sous 1 500 $ : coussin 1 400 $ apres 3 pertes -> jours 4-8 sans trade (dont 3 jours de vente),
    #   puis gains des le jour 9 : -600 + 4 x 194 = +176 -> jour 12
    # pause 5 seances sous 1 000 $ : coussin 1 000 $ apres 5 pertes (pas sous le seuil), 800 $ apres 6 -> jours 7-11 sans
    #   trade (5 jours d'achat perdus), puis -1 200 + 7 x 194 = +158 -> jour 18
    for c, n, jour in ((0.0, 0, 13), (1500.0, 5, 12), (1000.0, 5, 18)):
        r = M4.parcours4(0, 0, 2.0, 5.0, np.zeros(0), *b, *e, *f_, nj, 1, 1, 1e18, 0.0, 0, 0.0, c, n)
        assert r[0] == 1 and r[1] == jour, (c, n, r[:2], jour)
    print("ok : pause du bot (objectif aux jours 13, 12 et 18 comme calcule a la main)")


if __name__ == "__main__":
    test_pause()
