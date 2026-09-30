#!/usr/bin/env python3
"""Tests du tournoi n°5 : heure du fixing selon les changements d'heure, pas de regard vers le futur (fin de seance,
rapport EIA), marche aleatoire. Lancer depuis ce dossier : python3 test_strategies5.py"""
import numpy as np
import pandas as pd

import strategies5 as S
from test_concurrents import marche_aleatoire     # tournoi/


def main():
    # 1. heure du fixing de Londres a New York
    h = S.heure_fixing(pd.DatetimeIndex(["2024-01-15", "2024-03-20", "2024-07-01", "2024-10-30", "2024-11-05"]))
    assert list(h) == [11, 12, 11, 12, 11], h
    print("1. fixing de 16 h a Londres : 11 h a New York, 12 h les semaines de decalage des changements d'heure : OK")
    # 2. pas de regard vers le futur (donnees reelles CL)
    J, O, H, L, C, P, V, ech, comp, con = S.charger_minutes("CL")
    cout = S.cout_micro("CL")
    rng = np.random.default_rng(41)
    b1, _ = S.fin_de_seance(O, H, L, C, comp, ech, con, cout)
    c1, _ = S.rapport_eia(J, O, H, L, C, comp, ech, cout)
    for essai in range(5):
        d, k = int(rng.integers(100, len(J) - 5)), int(rng.integers(0, O.shape[1]))
        O2, H2, L2, C2 = (x.copy() for x in (O, H, L, C))
        f = rng.uniform(0.98, 1.02, size=(len(J) - d, O.shape[1]))
        for x, y in ((O2, O), (H2, H), (L2, L), (C2, C)):
            x[d:] *= f
            x[d, :k] = y[d, :k]
        assert np.array_equal(S.fin_de_seance(O2, H2, L2, C2, comp, ech, con, cout)[0][:d], b1[:d])
        assert np.array_equal(S.rapport_eia(J, O2, H2, L2, C2, comp, ech, cout)[0][:d], c1[:d])
    n = O.shape[1]
    O2 = O.copy(); O2[:, n - 30:] *= 1.05                          # la fin de seance ne change pas le sens
    s_av = np.sign(C[:, n - 31] / S.K1.de_la(C[:, n - 1], S.K1.precedente(comp, con)) - 1)
    assert np.isfinite(s_av).sum() > 1000
    print("2. fin de seance et rapport EIA : aucune seance passee modifiee par le futur (5 essais) : OK")
    # 3. marche aleatoire : rien ne gagne avant frais
    Jm, Om, Hm, Lm, Cm, Pm, Xm, _ = marche_aleatoire(12000, np.random.default_rng(42))
    comp = np.ones(len(Jm), bool); ech = np.zeros(len(Jm), bool); con = np.zeros(len(Jm), int)
    tb = lambda r, ok: float(r[ok].mean() / r[ok].std() * np.sqrt(ok.sum()))
    rb, okb = S.fin_de_seance(Om, Hm, Lm, Cm, comp, ech, con, 0.0)
    rc, okc = S.rapport_eia(Jm, Om, Hm, Lm, Cm, comp, ech, 0.0)
    tbv, tcv = tb(rb / Om[:, 0], okb), tb(rc / Om[:, 0], okc)
    assert tbv < 4 and tcv < 4
    print(f"3. marche aleatoire (12 000 seances) : t brut fin de seance {tbv:+.2f}, rapport EIA {tcv:+.2f} : OK")


if __name__ == "__main__":
    main()
