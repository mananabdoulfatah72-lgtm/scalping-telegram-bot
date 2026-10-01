#!/usr/bin/env python3
"""Tests de la correction V1 : pas de regard vers le futur (moyenne sur 14 seances completes et veille), V0 identique
au backtest de reference, et si ROBOT_ZONE donne le chemin de zone/robot.py (branche main) : robot = backtest V1.
Lancer depuis ce dossier : python3 test_v1.py   (ou ROBOT_ZONE=/chemin/zone/robot.py python3 test_v1.py)"""
import importlib.util
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import journal as Z

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tournoi"))
from explorer import charger  # noqa: E402


def main():
    J, O, H, L, C, P, X = charger("nasdaq100")
    rng = np.random.default_rng(51)
    # 1. V0 = backtest de reference (dans les deux sens : memes jours, memes montants)
    b0, a0 = Z.zone(J, O, H, L, C, P, X, propre=False)
    ref = Z.st.zone_de_bruit(J, O, H, L, C, P, X)
    s0 = pd.Series(b0, index=J)[a0 > 0]
    assert set(s0.index) == set(ref.index) and np.allclose(s0.reindex(ref.index).values, ref["brut"].values)
    print("1. V0 identique au backtest de reference (memes jours, memes gains) : OK")
    # 2. V1 : la seance d ne depend d'aucune donnee posterieure
    sig, veille, vw, ok = Z.niveaux_propres(J, O, H, L, C, P, X)
    b1, a1 = Z.zone(J, O, H, L, C, P, X)
    for essai in range(5):
        d = int(rng.integers(300, len(J) - 5))
        O2, H2, L2, C2, V2 = (x.copy() for x in (O, H, L, C, X["V"]))
        f = rng.uniform(0.97, 1.03, size=(len(J) - d, Z.N))
        for x in (O2, H2, L2, C2, V2):
            x[d:] *= f
        s2, v2, _, _ = Z.niveaux_propres(J, O2, H2, L2, C2, P, {**X, "V": V2})
        assert np.array_equal(np.nan_to_num(s2[:d + 1]), np.nan_to_num(sig[:d + 1])) and np.array_equal(np.nan_to_num(v2[:d + 1]), np.nan_to_num(veille[:d + 1]))
        bb, _ = Z.zone(J, O2, H2, L2, C2, P, {**X, "V": V2})
        assert np.array_equal(bb[:d], b1[:d])
    print("2. V1 : moyenne, veille et resultats des seances passees independants du futur (5 essais) : OK")
    # 3. V1 : la veille est toujours une seance complete du meme contrat
    seg = np.cumsum(X["echeance"])
    for d in np.where(np.isfinite(veille))[0][::50]:
        k = np.where(ok[:d])[0][-1]
        assert veille[d] == C[k, Z.N - 1] and seg[k] == seg[d]
    print("3. V1 : veille = derniere seance complete du meme contrat : OK")
    # 4. robot = backtest V1 (si le robot est disponible)
    chemin = os.getenv("ROBOT_ZONE")
    if chemin and Path(chemin).exists():
        spec = importlib.util.spec_from_file_location("robot_zone", chemin)
        rb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rb)
        d = pd.read_csv(Path(__file__).resolve().parent.parent / "intraday" / "donnees" / "nasdaq100_1min.csv.gz")
        z, _, _ = rb.zone_de_bruit(*rb.tableaux(d))
        Jt, Ot, Ht, Lt, Ct, Pt, Xt = Z.st.charger("nasdaq100")
        bt, at = Z.zone(Jt, Ot, Ht, Lt, Ct, Pt, Xt)
        st_ = pd.Series(bt, index=Jt)[at > 0]
        assert set(z.index) == set(st_.index) and np.allclose(z["brut"].values, st_.reindex(z.index).values)
        print(f"4. robot = backtest V1 sur 2011-2026 ({len(z)} jours de trade, ecart nul) : OK")
    else:
        print("4. robot non teste (definir ROBOT_ZONE)")


if __name__ == "__main__":
    main()
