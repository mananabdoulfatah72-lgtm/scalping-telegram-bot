#!/usr/bin/env python3
"""Controles de la vague 7 (README.md). Lancer depuis ce dossier : python3 test_vague7.py
(Controle 2 : lancer aussi les controles des vagues 4, 5, 6 et du Static, et comparer vague5_regles.txt et vague6.txt.)"""
import importlib.util
import subprocess
import tempfile

import numpy as np
import pandas as pd

import vague7 as V7

RB, W, D4, M4, U, MS = V7.RB, V7.W, V7.D4, V7.V6.M4, V7.U, V7.V6.MS


def test_signal():
    """1. Signal = celui du robot (zone/robot.py sur main) ; il ne depend que du passe."""
    code = subprocess.run(["git", "show", "origin/main:zone/robot.py"], capture_output=True, text=True, check=True,
                          cwd=V7.ICI).stdout
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code)
    spec = importlib.util.spec_from_file_location("robot_main", f.name)
    robot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(robot)
    d = pd.read_csv(RB.FICHIER)
    jr, Or, Hr, Lr, Cr, Pr, Vr, ech = robot.tableaux(d)
    attendu = set(robot.rebond(jr, Or, Lr, Cr, Pr)[0])
    j, O, C, P = RB.tableaux(d[["t", "o", "c"]])
    s = RB.signal(j, O, C, P)
    assert set(j[s]) == attendu, (len(attendu), int(s.sum()))
    for k in range(400, len(j), 157):                    # couper les donnees apres la seance k ne change pas son signal
        assert RB.signal(j[:k + 1], O[:k + 1], C[:k + 1], P[:k + 1])[k] == s[k], k
    print(f"ok : signal du rebond = robot sur {len(j)} seances ({len(attendu)} rebonds) ; rien du futur")


def test_jour_de_rebond(DA, DS):
    """3. Un jour de rebond sans limite : (cloture - ouverture) x 2 $ x facteur du jour - 3 $, par MNQ, sur les deux
    moteurs (zone et RSI(2) coupes)."""
    s = RB.pour(DA)
    kN, kE = D4.facteurs_jour(DA)
    der = DA["derniere"]
    bA = D4.base(DA, np.zeros(len(DA["Z"]), bool), rebond=s)
    bS = U.base(DS, np.zeros(len(DS["Z"]), bool), rebond=s)
    n = 0
    for d in np.flatnonzero(s)[5::23]:
        attendu = (DA["C"][d, der[d]] - DA["O"][d, 0]) * 2.0 * kN[d] - 3.0
        for q in (1, 2):
            x = M4.seance4(d, 0, 0, 0.0, 0.0, -1e12, 0, 1e12, 1e12, 0.0, *bA, 2.0 * kN[d], 5.0 * kE[d], q)[1]
            assert abs(x - q * attendu) < 1e-6, (d, q, x, attendu)
        t = np.zeros(1)
        U.achat(DS, bS, d, "E1", perte=1e12, objectif=1e12, h2=1, trace=t, niveau="jour")
        assert abs(t[0] - attendu) < 1e-6, (d, t[0], attendu)
        n += 1
    print(f"ok : jour de rebond recalcule a la main sur les deux moteurs ({n} jours, 1 et 2 MNQ)")


if __name__ == "__main__":
    test_signal()
    DA, DS = D4.charger(), W.DN.charger()
    test_jour_de_rebond(DA, DS)
