#!/usr/bin/env python3
"""Tests du tournoi n°3 : profil de volume et rejet compares a des versions Python simples, donnees quotidiennes sans
regard vers le futur, decisions de la regle des 80 % independantes de la suite, marche aleatoire.
Lancer depuis ce dossier : python3 test_tournoi3.py"""
import numpy as np
import pandas as pd

import tournoi3 as T
from explorer import charger
from profil import profil
from test_concurrents import marche_aleatoire   # tournoi/

N = T.N


def profil_simple(h, l, v, tick):
    lo, hi = l.min(), h.max()
    prix = np.round(np.arange(lo, hi + tick / 2, tick) / tick) * tick
    hist = np.zeros(len(prix))
    for a, b, x in zip(l, h, v):
        if x <= 0:
            continue
        i, j = int(round((a - lo) / tick)), int(round((b - lo) / tick))
        hist[i:j + 1] += x / (j - i + 1)
    p = int(np.argmax(hist))
    acc, up, dn = hist[p], p, p
    while acc < 0.7 * hist.sum() and (up < len(hist) - 1 or dn > 0):
        s_up, s_dn = hist[up + 1:up + 3].sum(), hist[max(0, dn - 2):dn].sum()
        if up >= len(hist) - 1 or (dn > 0 and s_dn > s_up):
            acc, dn = acc + s_dn, max(0, dn - 2)
        else:
            acc, up = acc + s_up, min(len(hist) - 1, up + 2)
    return prix[p], prix[up], prix[dn]


def rejet_simple(O, H, L, C, d, cout, nh, nb, sh, sb, oh, ob):
    for m in range(N):
        up, dn = not np.isnan(nh) and H[d, m] >= nh, not np.isnan(nb) and L[d, m] <= nb
        if up and dn:
            return 0.0
        if up or dn:
            s, e, stop, obj = (-1, nh, sh, oh) if up else (1, nb, sb, ob)
            if (H[d, m] >= stop) if s < 0 else (L[d, m] <= stop):
                return s * (stop - e) - cout
            for k in range(m + 1, N):
                o = O[d, k]
                if (o >= stop) if s < 0 else (o <= stop):
                    return s * (o - e) - cout
                if not np.isnan(obj) and ((o <= obj) if s < 0 else (o >= obj)):
                    return s * (o - e) - cout
                if (H[d, k] >= stop) if s < 0 else (L[d, k] <= stop):
                    return s * (stop - e) - cout
                if not np.isnan(obj) and ((L[d, k] <= obj) if s < 0 else (H[d, k] >= obj)):
                    return s * (obj - e) - cout
            return s * (C[d, N - 1] - e) - cout
    return 0.0


def faux_quotidien(J, rng):
    j = pd.DatetimeIndex(J)
    return {"gex": pd.Series(rng.normal(2e9, 2e9, len(j)), index=j), "dix": pd.Series(rng.normal(0.43, 0.02, len(j)), index=j),
            "vix_ratio": pd.Series(rng.normal(0.9, 0.08, len(j)), index=j)}


def main():
    rng = np.random.default_rng(21)
    J, O, H, L, C, P, X = charger("nasdaq100")
    cout = T.st.cout_aller_retour("nasdaq100")
    ok = T.st.journees_completes(P) & ~X["echeance"]
    # 1. profil de volume
    poc, vah, val = profil(H, L, X["V"], T.TICK)
    for d in rng.choice(np.where(ok)[0], 150, replace=False):
        assert (poc[d], vah[d], val[d]) == profil_simple(H[d], L[d], X["V"][d], T.TICK), d
    h = np.array([[10.0, 10.5, 11.0]]); l = np.array([[9.5, 10.0, 10.5]]); v = np.array([[100.0, 300.0, 100.0]])
    print(f"   exemple : POC {profil(h, l, v, 0.25)[0][0]}, zone {profil(h, l, v, 0.25)[2][0]}-{profil(h, l, v, 0.25)[1][0]}")
    assert val[ok].min() > 0 and np.all(val[ok] <= poc[ok]) and np.all(poc[ok] <= vah[ok])
    print("1. profil de volume = version simple (150 seances), bas <= POC <= haut : OK")
    # 2. rejet
    for essai in range(1500):
        d = int(rng.choice(np.where(ok)[0]))
        e = O[d, 0]
        nh = e * (1 + abs(rng.normal(0, 0.004))) if rng.random() < 0.7 else np.nan
        nb = e * (1 - abs(rng.normal(0, 0.004))) if rng.random() < 0.7 else np.nan
        sh, sb = (nh * 1.002 if not np.isnan(nh) else np.nan), (nb * 0.998 if not np.isnan(nb) else np.nan)
        oh, ob = (e if rng.random() < 0.5 else np.nan), (e if rng.random() < 0.5 else np.nan)
        arr = lambda x: np.where(np.arange(len(J)) == d, x, np.nan)
        okd = np.arange(len(J)) == d
        a = T.rejet(O, H, L, C, okd, cout, arr(nh), arr(nb), arr(sh), arr(sb), arr(oh), arr(ob))[d]
        assert abs(a - rejet_simple(O, H, L, C, d, cout, nh, nb, sh, sb, oh, ob)) < 1e-9, d
    print("2. rejet = version simple (1500 cas) : OK")
    # 3. donnees quotidiennes : valeur publiee strictement avant la seance
    s = pd.Series([1.0, 2.0, 3.0], index=pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"]))
    v = T.veille(pd.DatetimeIndex(["2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07", "2020-01-20"]), s)
    assert np.isnan(v[0]) and v[1] == 1 and v[2] == 2 and v[3] == 3 and np.isnan(v[4])
    print("3. GEX / DIX / VIX : valeur de la veille, jamais du jour, perimee apres 5 jours : OK")
    # 4. regle des 80 % et acceptation : decisions independantes des minutes a partir de l'entree
    complete = T.st.journees_completes(P)
    zv = T.zone_valeur_veille(H, L, X, complete)
    s1, m1, st1, ob1 = T.regle_80(O, H, L, C, *zv)
    s2, m2, st2 = T.acceptation(O, C, *zv)
    for sens, me, nom in ((s1, m1, "regle des 80 %"), (s2, m2, "acceptation")):
        for d in rng.choice(np.where(sens != 0)[0], 40, replace=False):
            O2, H2, L2, C2 = (x.copy() for x in (O, H, L, C))
            for x in (O2, H2, L2, C2):
                x[d, me[d]:] *= 1.03
            a = T.regle_80(O2, H2, L2, C2, *zv) if nom == "regle des 80 %" else T.acceptation(O2, C2, *zv)
            assert a[0][d] == sens[d] and a[1][d] == me[d], (nom, d)
            if nom == "regle des 80 %":
                assert a[2][d] == st1[d] and a[3][d] == ob1[d]
    print("4. regle des 80 % et acceptation : sens, heure, stop et objectif connus avant l'entree (80 cas) : OK")
    # 5. aucune seance passee modifiee par le futur
    Q = T.lire_quotidien()
    res, _, _ = T.toutes(J, O, H, L, C, P, X, cout, Q)
    for essai in range(4):
        d, k = int(rng.integers(300, len(J) - 5)), int(rng.integers(0, N))
        O2, H2, L2, C2, V2 = (x.copy() for x in (O, H, L, C, X["V"]))
        f = rng.uniform(0.98, 1.02, size=(len(J) - d, N))
        for x, y in ((O2, O), (H2, H), (L2, L), (C2, C), (V2, X["V"])):
            x[d:] *= f
            x[d, :k] = y[d, :k]
        res2, _, _ = T.toutes(J, O2, H2, L2, C2, P, {**X, "V": V2}, cout, Q)
        for nom in res:
            assert np.array_equal(res[nom][:d], res2[nom][:d]), nom
    print(f"5. aucune seance passee modifiee par le futur (4 essais, {len(res)} strategies) : OK")
    # 6. marche aleatoire : aucune strategie ne gagne avant frais
    Jm, Om, Hm, Lm, Cm, Pm, Xm, _ = marche_aleatoire(12000, np.random.default_rng(22))
    Qm = faux_quotidien(Jm, np.random.default_rng(23))
    pc = np.r_[np.nan, Cm[:-1, -1]]                     # niveaux fixes a partir de la cloture de la veille
    mur = {"call": pc * 1.01, "put": pc * 0.99, "zero": pc * (1 + np.random.default_rng(24).normal(0, 0.01, len(Jm)))}
    rm, okm, _ = T.toutes(Jm, Om, Hm, Lm, Cm, Pm, Xm, 0.0, Qm, mur)
    ts = {k: float(x[okm].mean() / x[okm].std() * np.sqrt(okm.sum())) if x[okm].std() > 0 else 0.0
          for k, x in ((k, v / Om[:, 0]) for k, v in rm.items())}
    assert max(ts.values()) < 4, ts
    print("6. marche aleatoire (12 000 seances) : t brut max " + f"{max(ts.values()):+.2f} (" +
          ", ".join(f"{k} {v:+.1f}" for k, v in ts.items()) + ") : OK")


if __name__ == "__main__":
    main()
