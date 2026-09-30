#!/usr/bin/env python3
"""Tests du tournoi n°4 : range de la nuit sans minute de la seance, mois en cours et fin de mois sans regard vers le
futur, regression logistique exacte, modele appris sans regard vers le futur, marche aleatoire.
Lancer depuis ce dossier : python3 test_strategies4.py"""
import numpy as np
import pandas as pd

import strategies4 as S
from concurrents2 import aligner
from explorer import charger
from test_concurrents import marche_aleatoire     # tournoi/
from test_tournoi3 import faux_quotidien           # evolution2/

N = S.N


def main():
    rng = np.random.default_rng(31)
    J, O, H, L, C, P, X = charger("nasdaq100")
    cout = S.st.cout_aller_retour("nasdaq100")
    complete = S.st.journees_completes(P)
    ok = complete & ~X["echeance"]
    # 1. range de la nuit : barres de 18 h a 8 h seulement, meme contrat
    onh, onl = S.range_nuit("nasdaq100", J, X["contrat"])
    h = pd.read_csv(S.R / "nuit" / "donnees" / "nasdaq100_1h.csv.gz")
    t = pd.to_datetime(h["t"])
    for d in rng.choice(np.where(np.isfinite(onh))[0], 50, replace=False):
        j = pd.Timestamp(J[d])
        sel = (t >= j - pd.Timedelta(hours=6)) & (t < j + pd.Timedelta(hours=9)) & (h["contrat"].values == X["contrat"][d])
        assert onh[d] == h["h"][sel].max() and onl[d] == h["l"][sel].min(), d
    assert np.all(onh[np.isfinite(onh)] >= onl[np.isfinite(onh)])
    print(f"1. range de la nuit = barres de 18 h a 8 h du meme contrat (50 seances), defini {np.isfinite(onh).mean():.0%} des seances : OK")
    # 2. mois en cours : connu a l'ouverture ; fin de mois : 4 seances au plus
    mtd = S.mois_en_cours(J, C, complete, X["contrat"])
    mois = pd.DatetimeIndex(J).to_period("M")
    prem = np.r_[True, mois[1:] != mois[:-1]]
    assert np.all(mtd[prem] == 0)
    d = int(np.where(prem & complete)[0][50])
    if complete[d + 1] and X["contrat"][d] == X["contrat"][d - 1] and mois[d + 1] == mois[d]:
        assert abs(mtd[d + 1] - (C[d, N - 1] / C[d - 1, N - 1] - 1)) < 1e-12
    C2 = C.copy()
    C2[d + 5:] *= 1.05
    assert np.array_equal(S.mois_en_cours(J, C2, complete, X["contrat"])[:d + 6], mtd[:d + 6])
    fin = S.derniers_jours(J, complete)
    assert pd.Series(fin).groupby(mois).sum().max() <= 4
    print("2. mouvement du mois connu a l'ouverture, 4 dernieres seances par mois : OK")
    # 3. regression logistique : retrouve les coefficients sur des donnees simulees
    Xs = rng.normal(size=(20000, 3))
    w_vrai = np.array([0.3, 1.0, -0.5, 0.0])
    ys = (rng.random(20000) < 1 / (1 + np.exp(-(w_vrai[0] + Xs @ w_vrai[1:])))).astype(float)
    w = S.logistique(Xs, ys, lam=0.0)
    assert np.allclose(w, w_vrai, atol=0.06), w
    print(f"3. regression logistique : coefficients retrouves ({np.round(w, 2)}) : OK")
    # 4. modele appris : sens de la seance d independant des minutes a partir de 10 h et des seances suivantes
    Q = S.T3.lire_quotidien()
    s8 = S.modele_appris(J, O, H, L, C, X, ok, complete, Q)
    for essai in range(3):
        d = int(rng.choice(np.where(s8 != 0)[0]))
        O2, H2, L2, C2, V2 = (x.copy() for x in (O, H, L, C, X["V"]))
        for x in (O2, H2, L2, C2, V2):
            x[d, 30:] *= 1.02
            x[d + 1:] *= 1.02
        s = S.modele_appris(J, O2, H2, L2, C2, {**X, "V": V2}, ok, complete, Q)
        assert np.array_equal(s[:d + 1], s8[:d + 1]), d
    print(f"4. modele appris : decisions independantes de la suite (3 essais) ; {int((s8 != 0).sum())} seances tradees : OK")
    # 5. aucune seance passee modifiee par le futur (toutes les strategies)
    nuit = (onh, onl)
    res, _, _ = S.toutes(J, O, H, L, C, P, X, cout, Q, nuit)
    for essai in range(3):
        d, k = int(rng.integers(400, len(J) - 5)), int(rng.integers(0, N))
        O2, H2, L2, C2, V2 = (x.copy() for x in (O, H, L, C, X["V"]))
        f = rng.uniform(0.98, 1.02, size=(len(J) - d, N))
        for x, y in ((O2, O), (H2, H), (L2, L), (C2, C), (V2, X["V"])):
            x[d:] *= f
            x[d, :k] = y[d, :k]
        res2, _, _ = S.toutes(J, O2, H2, L2, C2, P, {**X, "V": V2}, cout, Q, nuit)
        for nom in res:
            assert np.array_equal(res[nom][:d], res2[nom][:d]), nom
    print(f"5. aucune seance passee modifiee par le futur (3 essais, {len(res)} strategies) : OK")
    # 6. marche aleatoire : aucune strategie ne gagne avant frais (paire en continuation comprise)
    Jm, Om, Hm, Lm, Cm, Pm, Xm, pas = marche_aleatoire(12000, np.random.default_rng(32))
    Qm = faux_quotidien(Jm, np.random.default_rng(33))
    pc = np.r_[np.nan, Cm[:-1, -1]]
    e = np.abs(np.random.default_rng(34).normal(0, 0.004, len(Jm)))
    nuitm = (pc * (1 + e), pc * (1 - e))
    rm, okm, _ = S.toutes(Jm, Om, Hm, Lm, Cm, Pm, Xm, 0.0, Qm, nuitm)
    tb = lambda x: float(x[okm].mean() / x[okm].std() * np.sqrt(okm.sum())) if x[okm].std() > 0 else 0.0
    ts = {k: tb(v / Om[:, 0]) for k, v in rm.items()}
    b = marche_aleatoire(12000, np.random.default_rng(35), correle=pas)
    rp, okp = S.paire_suivre((Jm, Om, Hm, Lm, Cm, Pm, Xm), b[:7], 0.0, 0.0)
    tp = float(rp[okp].mean() / rp[okp].std() * np.sqrt(okp.sum()))
    assert max(ts.values()) < 4 and tp < 4, (ts, tp)
    print("6. marche aleatoire (12 000 seances) : t brut " + ", ".join(f"{k} {v:+.1f}" for k, v in ts.items())
          + f", paire en continuation {tp:+.1f} : OK")


if __name__ == "__main__":
    main()
