#!/usr/bin/env python3
"""Le moteur regle (k = 1, 14 jours, 30 min, stop limite ou VWAP) redonne exactement la zone corrigee V1.
Lancer depuis ce dossier : python3 test_moteur.py"""
import sys
from pathlib import Path

import numpy as np

import moteur as M

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tournoi"))
from explorer import charger  # noqa: E402

J, O, H, L, C, P, X = charger("nasdaq100", fin=None)
z = M.Zone(J, O, H, L, C, P, X)
b, a = z.jouer(1.0, 14, 30, "limite ou VWAP")
b1, a1 = M.Z.zone(J, O, H, L, C, P, X)
assert np.allclose(b, b1) and np.array_equal(a, a1)
print(f"moteur regle = V1 ({int((a > 0).sum())} jours de trade) : OK")
