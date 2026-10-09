#!/usr/bin/env python3
"""Controle de la vague 11 : plafond de gain du jour (marche synthetique de test_vague8 : un trade de zone par jour,
achat a la minute 10, vente a la minute 20 qui cloture 98,5 points plus haut, soit +194 $ sur MNQ apres frais).
Plafond 100 $ : le trade est ferme a +100 $ (ordre limite) moins 3,50 $ de frais (aller-retour + 1 tick) ; plafond 300 $ :
pas touche ; sur le compte finance seulement (le challenge n'est pas plafonne)."""
import sys
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "vague8"))
import test_vague8 as T8  # noqa: E402

M4 = T8.M4


def test_plafond():
    b = T8.marche(30, 98.5, 0.0)
    jour = lambda cap: M4.seance4(0, 0, 0, 0.0, 0.0, -1e12, 0, 1e12, 1e12, 0.0, *b, 2.0, 5.0, 1, 0, cap)[1]  # noqa: E731
    assert abs(jour(0.0) - 194.0) < 1e-9
    assert abs(jour(100.0) - (100.0 - M4.FRAIS_ZONE - M4.TICK_NQ)) < 1e-9, jour(100.0)
    assert abs(jour(300.0) - 194.0) < 1e-9
    # parcours : challenge de 2 jours (objectif 300 $) non plafonne, puis finance plafonne a 100 $ par jour
    e = (300.0, 2000.0, 0, 0.0, 0.0, 0.0, 1)
    f_ = (2000.0, 0.0, 0.0, 5, 50.0, 0.0, 1e9, np.array([1e9]), 0.0, 0.0, 0)        # aucun retrait (minimum enorme)
    r = M4.parcours4(0, 0, 2.0, 5.0, np.zeros(0), *b, *e, *f_, 30, 1, 1, 1e18, 0.0, 0, 0.0, 0.0, 0, 100.0)
    assert r[0] == 1 and r[1] == 2, r
    print("ok : plafond du jour (ferme a +100 $ moins les frais ; pas touche a 300 $ ; challenge non plafonne)")


if __name__ == "__main__":
    test_plafond()
