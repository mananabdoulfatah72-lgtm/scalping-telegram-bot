#!/usr/bin/env python3
"""Controles du Monte Carlo (README.md). Lancer depuis ce dossier : python3 test_montecarlo.py.
1. Sur un chemin qui suit le vrai calendrier (idx = depart, depart + 1, ...), parcours_mc redonne exactement
   moteur4.parcours4 (issue, seances, retraits seance par seance), avec et sans filtre, sur 300 achats.
2. Les traces sont coherentes : solde au-dessus du plancher tant que le compte vit, phase 1 puis 2, retraits egaux a la
   somme recue.
3. Les chemins tires au hasard n'utilisent que des seances du groupe choisi, par blocs de seances consecutives."""
import numpy as np

import montecarlo as MC

M4, MM = MC.M4, MC.MM


def test_egal_moteur(P):
    rng = np.random.default_rng(3)
    nj = len(P["D"]["jours"])
    H = MC.H
    n = 0
    for b in (P["bases"]["fort"][0], P["bases"]["aucun"][0]):
        for d in rng.choice(np.arange(260, nj - H), 150, replace=False):
            ret = np.zeros(H)
            r = M4.parcours4(int(d), 4, P["kN"], P["kE"], ret, *b, *MC.B.E, *MC.B.F, H, 1, 1, 1e18, 0.0, 0,
                             MC.FREIN, 0.0, 0, MC.PLAFOND)
            t = MC.un_chemin(np.arange(d, d + H), b, P)
            assert tuple(float(x) for x in r) == tuple(float(x) for x in t["r"]), (d, r, t["r"])
            assert np.array_equal(ret, t["ret"]), d
            n += 1
    print(f"ok : chemin au vrai calendrier = moteur exact sur {n} achats (issues et retraits identiques)")


def test_traces(P):
    rng = np.random.default_rng(5)
    for _ in range(200):
        idx = MC.tirer_chemin(rng, P["pools"]["tout"])
        t = MC.un_chemin(idx, P["bases"]["fort"][rng.integers(10)], P)
        r, ph, so, pl = t["r"], t["phase"], t["solde"], t["plancher"]
        fin = int(r[6]) if r[0] != 0 else MC.H
        assert (ph[:fin] > 0).all() and (ph[fin:] == 0).all()
        assert np.all(np.diff(ph[:fin]) >= 0)
        vivant = fin - 1 if (r[0] == -1 or r[2]) else fin
        assert np.all(so[:vivant] > pl[:vivant] - 1e-9)
        assert abs(t["ret"].sum() - r[4]) < 1e-9
    print("ok : traces coherentes (phase, solde au-dessus du plancher, retraits)")


def test_blocs(P):
    rng = np.random.default_rng(9)
    j = P["D"]["jours"]
    for nom, pool in P["pools"].items():
        a, z = MC.REGIMES[nom][1:]
        for _ in range(50):
            idx = MC.tirer_chemin(rng, pool)
            assert len(idx) == MC.H
            assert (j[idx] >= np.datetime64(a)).all() and (j[idx] <= np.datetime64(z)).all(), nom
            pas = np.diff(idx).reshape(-1)
            assert np.all(pas[np.arange(len(pas)) % MC.BLOC != MC.BLOC - 1] == 1)
    print("ok : chemins tires par blocs de seances consecutives, dans le bon groupe")


if __name__ == "__main__":
    P = MC.preparer()
    test_egal_moteur(P)
    test_traces(P)
    test_blocs(P)
    print("tous les controles passent")
