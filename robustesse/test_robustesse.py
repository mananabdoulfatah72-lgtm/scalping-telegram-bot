#!/usr/bin/env python3
"""Controles du labo (README.md). Lancer depuis ce dossier : python3 test_robustesse.py.
1. La zone parametree, avec les reglages du bot (14 jours, 30 min, x1, sortie VWAP), redonne exactement les trades de
   zone de la recherche (gain de chaque seance a 1e-6 $ pres, meme nombre d'allers-retours).
2. Le RSI(2) parametre, avec les reglages du bot (200, 10, 5), redonne exactement les decisions du robot et le gain de
   chaque nuit du RSI(2) de nuit sur MES (moteur4.seance4)."""
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vague9"))
import variantes as V
import socle9 as S9


def main():
    D, T, a3, _ = S9.charger()
    M = V.minutes()
    assert (M["jours"] == D["jours"]).all()
    kN, kE = S9.D4.facteurs_jour(D)
    nj = len(D["jours"])
    ref = np.bincount(T["d"], weights=T["mnq"], minlength=nj)
    z, nb = V.zone(M, V.sigma(M, 14), kN)
    assert np.abs(z - ref).max() < 1e-6 and int(nb.sum()) == len(T["d"])
    print(f"ok : zone parametree = zone du bot ({len(T['d'])} trades, ecart max {np.abs(z - ref).max():.1e} $)")
    dec, vou = V.decisions_rsi(M)
    assert (dec == D["dec"]).all() and (vou == D["voulu"]).all()
    g, tenu = V.nuit(D, dec, vou, kE)
    assert np.abs(g - a3).max() < 1e-6
    print(f"ok : RSI(2) parametre = RSI(2) de nuit du bot ({int(tenu.sum())} nuits, ecart max {np.abs(g - a3).max():.1e} $)")
    print("tous les controles passent")


if __name__ == "__main__":
    main()
