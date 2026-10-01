#!/usr/bin/env python3
"""Tests du rebond du robot (zone/robot.py sur main, version executable de la piste S4). Chemin du robot dans ROBOT_ZONE.
1. l'achat annonce la veille (sur les seules donnees connues) est exactement le trade compte le lendemain ;
2. sur les jours communs avec la piste S4, memes gains ; les seuls jours en plus ou en moins viennent des jours de
   changement de contrat (S4 les ecarte) et du seuil qui en depend ;
3. chiffres de la version executable (README.md).
Lancer depuis ce dossier : ROBOT_ZONE=/chemin/zone/robot.py python3 test_rebond.py"""
import importlib.util
import os

import numpy as np
import pandas as pd

import sources as SRC

N = 390


def main():
    spec = importlib.util.spec_from_file_location("robot", os.environ["ROBOT_ZONE"])
    robot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(robot)
    J, O, H, L, C, P, X = SRC.charger("nasdaq100", fin=None)
    d = pd.read_csv(SRC.R / "intraday/donnees/nasdaq100_1min.csv.gz")
    jr, Or, Hr, Lr, Cr, Pr, Vr, ech = robot.tableaux(d)
    assert (jr == J).all()
    rb = robot.rebond(jr, Or, Lr, Cr, Pr)[0]
    # 1. annonce de la veille = trade du lendemain
    court = np.array([robot.jour_court(pd.Timestamp(j)) for j in J])
    ecarts = [str(J[k].date()) for k in range(300, len(J))
              if (robot.rebond(jr[:k], Or[:k], Lr[:k], Cr[:k], Pr[:k])[1] and not court[k]) != (J[k] in rb)]
    assert not ecarts, ecarts
    print(f"1. annonce de la veille = trade du lendemain sur {len(J) - 300} seances : OK")
    # 2. comparaison avec S4
    s4 = SRC.rebond(J, O, H, L, C, P, X, SRC.COUT)
    exe = pd.Series({j: x["brut"] - SRC.COUT for j, x in rb.items()}).reindex(J).fillna(0).values
    communs = [J.get_loc(j) for j in rb if s4[J.get_loc(j)] != 0]
    assert np.allclose(exe[communs], s4[communs])
    print(f"2. {len(communs)} jours communs avec S4, memes gains : OK ; {len(rb)} jours executables,"
          f" {int((s4 != 0).sum())} jours S4 a gain non nul")
    # 3. chiffres
    an = pd.DatetimeIndex(J).year.values
    ok = SRC.S4.st.journees_completes(P)
    brut, allers = SRC.Z.zone(J, O, H, L, C, P, X)
    v1 = brut - SRC.COUT * allers
    r1, r2 = (np.where(ok, x / O[:, 0], 0.0) for x in (v1, v1 + exe))
    c = ok & (an >= 2023)
    dollars = (exe * SRC.PT)[c].sum()
    print(f"3. 2023-2026 : rebond {dollars:+,.0f} $ (1 MNQ) ; t zone {SRC.t_stat(r1[c]):+.2f}, zone + rebond {SRC.t_stat(r2[c]):+.2f},"
          f" t de l'apport {SRC.t_stat((r2 - r1)[c]):+.2f}")
    assert round(dollars) == 6420


if __name__ == "__main__":
    main()
