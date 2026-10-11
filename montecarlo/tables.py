#!/usr/bin/env python3
"""Monte Carlo v2 (README.md) : resultat exact de chaque vraie seance du bot, pour le moteur journalier de la page.

Pour chaque seance du 3 janvier 2012 au 25 septembre 2026, chaque tirage du filtre delta (4 aussi bons qu'en 2026,
4 deux fois plus faibles, 1 sans filtre) et chaque combinaison :
- position RSI(2) de nuit tenue en entrant (0/1) ;
- zone sur MNQ ou sur MES (frein) ;
- plafond du jour 0, 500 ou 750 $ ;
on appelle moteur4.seance4 (sans changement) avec la limite du jour de 1 100 $ :
- gain de la seance ;
- pire point : le plus bas de la valeur du compte dans la seance, relatif au depart, trouve par bisection sur le
  plancher (la seance est perdue si et seulement si plancher - solde >= pire point) ;
- au moins un trade (jour qui compte pour les retraits) et position voulue pour la nuit suivante.
Ecrit tables.npz."""
import sys
import time
import multiprocessing as mp
from pathlib import Path

import numpy as np
from numba import njit

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import montecarlo as MC  # noqa: E402

M4 = MC.M4
seance4 = M4.seance4
CAPS = np.array([0.0, 500.0, 750.0])
DLL = 1100.0
NB_FORT, NB_MOITIE = 10, 10
DEBUT, FIN = "2012-01-03", "2026-09-25"


@njit(cache=True)
def _tables(seances, kN, kE, caps, dll, O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu, NO, NH,
            NL, nn, EO, EH, EL, EC, ENO, ENH, ENL, enn, reb, gain, pire, drap):
    nc = caps.shape[0]
    for a in range(seances.shape[0]):
        d = seances[a]
        for veut in range(2):
            for zi in range(2):
                for ci in range(nc):
                    k = (veut * 2 + zi) * nc + ci
                    perdu, cash, v2, pr, pl, tr = seance4(d, 4, veut, 0.0, 0.0, -1e12, 0, 2500.0, 100.0, dll, O, H, L, C,
                                                          der, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu, NO,
                                                          NH, NL, nn, EO, EH, EL, EC, ENO, ENH, ENL, enn, reb, kN[d],
                                                          kE[d], 1, zi, caps[ci])
                    gain[a, k] = cash
                    drap[a, k] = (1 if tr else 0) + 2 * v2
                    p0 = seance4(d, 4, veut, 0.0, 0.0, -1e-9, 0, 2500.0, 100.0, dll, O, H, L, C, der, z_deb, z_fin,
                                 z_me, z_ms, z_sens, z_garde, dec, voulu, NO, NH, NL, nn, EO, EH, EL, EC, ENO, ENH, ENL,
                                 enn, reb, kN[d], kE[d], 1, zi, caps[ci])[0]
                    if not p0:
                        pire[a, k] = 0.0
                        continue
                    lo, hi = -20000.0, -1e-9                 # perdu(lo) faux, perdu(hi) vrai
                    for _ in range(36):
                        mi = 0.5 * (lo + hi)
                        if seance4(d, 4, veut, 0.0, 0.0, mi, 0, 2500.0, 100.0, dll, O, H, L, C, der, z_deb, z_fin, z_me,
                                   z_ms, z_sens, z_garde, dec, voulu, NO, NH, NL, nn, EO, EH, EL, EC, ENO, ENH, ENL, enn,
                                   reb, kN[d], kE[d], 1, zi, caps[ci])[0]:
                            hi = mi
                        else:
                            lo = mi
                    pire[a, k] = hi


def un_tirage(args):
    fil, i = args
    b = MC.P["bases"][fil][i]
    s = MC.P["seances"]
    nk = 4 * len(CAPS)
    gain, pire, drap = np.zeros((len(s), nk)), np.zeros((len(s), nk)), np.zeros((len(s), nk), np.int8)
    _tables(s, MC.P["kN"], MC.P["kE"], CAPS, DLL, *b, gain, pire, drap)
    return gain, pire, drap


def seances(P):
    j = P["jours"]
    import pandas as pd
    return np.flatnonzero((j >= pd.Timestamp(DEBUT)) & (j <= pd.Timestamp(FIN))).astype(np.int64)


def main():
    t0 = time.time()
    P = MC.preparer()
    P["seances"] = seances(P)
    tirages = [("fort", i) for i in range(NB_FORT)] + [("moitie", i) for i in range(NB_MOITIE)] + [("aucun", 0)]
    with mp.get_context("fork").Pool(4) as pool:
        res = pool.map(un_tirage, tirages, chunksize=1)
    gain = np.stack([r[0] for r in res])
    pire = np.stack([r[1] for r in res])
    drap = np.stack([r[2] for r in res])
    np.savez_compressed(ICI / "tables.npz", gain=gain, pire=pire, drap=drap, seances=P["seances"], caps=CAPS,
                        jours=np.array([str(P["jours"][d].date()) for d in P["seances"]]),
                        tirages=np.array([f"{f}:{i}" for f, i in tirages]))
    print(f"tables : {gain.shape} ({time.time() - t0:.0f} s) ; pire point min {pire.min():.0f} $, gain min/max"
          f" {gain.min():.0f} / {gain.max():.0f} $")


if __name__ == "__main__":
    main()
