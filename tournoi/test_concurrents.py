#!/usr/bin/env python3
"""Tests du tournoi : pas de regard vers le futur (entre seances, et dans la seance sur un marche aleatoire),
cassure et entree a heure fixe comparees a des versions Python simples, achat simple exact.
Lancer depuis ce dossier : python3 test_concurrents.py"""
import numpy as np
import pandas as pd

import concurrents as K
from explorer import charger


def cassure_simple(O, H, L, C, d, cout, haut, bas, sa, sv, debut):
    pos = 0
    for m in range(debut, 390):
        if pos == 0:
            up, dn = H[d, m] > haut, L[d, m] < bas
            if up and dn:
                return 0.0
            if up:
                pos, e, stop = 1, max(haut, O[d, m]), sa
                if L[d, m] <= stop:
                    return stop - e - cout
            elif dn:
                pos, e, stop = -1, min(bas, O[d, m]), sv
                if H[d, m] >= stop:
                    return e - stop - cout
        elif pos > 0 and L[d, m] <= stop:
            return min(stop, O[d, m]) - e - cout
        elif pos < 0 and H[d, m] >= stop:
            return e - max(stop, O[d, m]) - cout
    return pos * (C[d, 389] - e) - cout if pos else 0.0


def entree_fixe_simple(O, H, L, C, d, cout, s, me, stop, obj, ms):
    e = O[d, me]
    for m in range(me, ms + 1):
        o = O[d, m]
        if not np.isnan(stop) and (o <= stop if s > 0 else o >= stop):
            return s * (o - e) - cout
        if not np.isnan(obj) and (o >= obj if s > 0 else o <= obj):
            return s * (o - e) - cout
        if not np.isnan(stop) and (L[d, m] <= stop if s > 0 else H[d, m] >= stop):
            return s * (stop - e) - cout
        if not np.isnan(obj) and (H[d, m] >= obj if s > 0 else L[d, m] <= obj):
            return s * (obj - e) - cout
    return s * (C[d, ms] - e) - cout


def marche_aleatoire(nd, rng, correle=None, pas=64):
    """Seances synthetiques de 390 minutes ou le prix est une martingale, tick par tick (+/- 0,25 a chaque pas,
    64 pas par minute) : le chemin passe par chaque tick, un ordre a un niveau est donc servi a ce niveau. Aucune
    strategie honnete ne peut y gagner avant frais. Saut de nuit rappele vers 5000 (seule la nuit est previsible).
    correle : pas d'un autre marche, pour une paire (80 % des pas en commun). Renvoie (J, O, H, L, C, P, X, pas)."""
    J = pd.bdate_range("1975-01-01", periods=nd)
    O, H, L, C = (np.empty((nd, 390)) for _ in range(4))
    tous = np.empty((nd, 390 * pas), np.int8)
    depart = 5000.0
    for d0 in range(0, nd, 500):
        d1 = min(nd, d0 + 500)
        z = (rng.integers(0, 2, (d1 - d0, 390 * pas), dtype=np.int8) * 2 - 1).astype(np.int8)
        if correle is not None:
            commun = rng.random((d1 - d0, 390 * pas)) < 0.8
            z = np.where(commun, correle[d0:d1], z).astype(np.int8)
        tous[d0:d1] = z
        chemin = np.cumsum(z, axis=1, dtype=np.int32).reshape(d1 - d0, 390, pas)
        ouv = np.concatenate([np.zeros((d1 - d0, 1), np.int32), chemin[:, :-1, -1]], axis=1)
        hh = np.maximum(chemin.max(axis=2), ouv)
        ll = np.minimum(chemin.min(axis=2), ouv)
        for i in range(d1 - d0):
            d = d0 + i
            if d > 0:
                depart = C[d - 1, -1] + np.round((rng.normal(0, 20) - 0.05 * (C[d - 1, -1] - 5000)) / 0.25) * 0.25
            O[d], H[d], L[d], C[d] = (depart + 0.25 * x for x in (ouv[i], hh[i], ll[i], chemin[i, :, -1]))
    P = np.ones((nd, 390), bool)
    X = {"V": rng.integers(50, 500, (nd, 390)).astype(float), "echeance": np.zeros(nd, bool), "contrat": None}
    return J, O, H, L, C, P, X, tous


def controle_martingale(toutes, nd=12000, seuil=4.0):
    """Regard vers le futur dans la seance : sur un marche aleatoire, chaque strategie doit avoir un t brut < seuil.
    Deux tricheurs plantes (sens pris sur la cloture de 16 h ; sens pris sur la minute d'entree elle-meme) doivent
    etre detectes, pour montrer que le controle a assez de puissance."""
    rng = np.random.default_rng(11)
    J, O, H, L, C, P, X, _ = marche_aleatoire(nd, rng)
    res, ok = toutes(J, O, H, L, C, P, X, 0.0)
    rien = np.full(nd, np.nan)
    tr1 = K.entree_fixe(O, H, L, C, ok, 0.0, np.sign(C[:, -1] - O[:, 60]).astype(np.int64), 60, rien, rien, 389)
    tr2 = K.entree_fixe(O, H, L, C, ok, 0.0, np.sign(C[:, 60] - O[:, 60]).astype(np.int64), 60, rien, rien, 389)
    t = lambda x: float(x[ok].mean() / x[ok].std() * np.sqrt(ok.sum())) if x[ok].std() > 0 else 0.0
    t1, t2 = t(tr1 / O[:, 0]), t(tr2 / O[:, 0])
    assert t1 > seuil and t2 > seuil, (t1, t2)
    ts = {nom: t(pts / O[:, 0]) for nom, pts in res.items()}
    for nom, v in ts.items():
        assert v < seuil, f"regard vers le futur probable : {nom} (t brut {v:+.2f} sur un marche aleatoire)"
    return ts, t1, t2


def main():
    J, O, H, L, C, P, X = charger("nasdaq100")
    cout = K.st.cout_aller_retour("nasdaq100")
    res, ok = K.toutes(J, O, H, L, C, P, X, cout)
    # 1. cassure : identique a la version simple (range d'ouverture 30 min) sur 300 seances
    hh, ll = H[:, :30].max(axis=1), L[:, :30].min(axis=1)
    rng = np.random.default_rng(3)
    for d in rng.choice(np.where(ok)[0], 300, replace=False):
        assert abs(res["Range d'ouverture 30 min"][d] - cassure_simple(O, H, L, C, d, cout, hh[d], ll[d], ll[d], hh[d], 30)) < 1e-9
    print("1. cassure = version simple (300 seances) : OK")
    # 2. achat simple = cloture - ouverture - frais
    a = res["Achat simple intraday"]
    assert np.allclose(a[ok], C[ok, 389] - O[ok, 0] - cout) and np.all(a[~ok] == 0)
    print("2. achat simple exact, rien les jours exclus : OK")
    # 3. modifier une seance a partir de la minute k ne change aucune seance anterieure
    for essai in range(10):
        d, k = int(rng.integers(100, len(J) - 5)), int(rng.integers(0, 390))
        O2, H2, L2, C2 = (x.copy() for x in (O, H, L, C))
        f = rng.uniform(0.98, 1.02, size=(len(J) - d, 390))
        for x in (O2, H2, L2, C2):
            x[d:, :] *= f
        for x, y in ((O2, O), (H2, H), (L2, L), (C2, C)):
            x[d, :k] = y[d, :k]
        res2, _ = K.toutes(J, O2, H2, L2, C2, P, X, cout)
        for nom in res:
            assert np.array_equal(res[nom][:d], res2[nom][:d]), f"regard vers le futur : {nom}"
    print("3. aucune seance passee modifiee par le futur (10 essais, 15 strategies) : OK")
    # 4. entree a heure fixe : identique a la version simple (stops et objectifs deja franchis a l'ouverture compris)
    nd = len(J)
    for essai in range(2000):
        d = int(rng.choice(np.where(ok)[0]))
        me, ms = int(rng.integers(0, 380)), 389
        s = int(rng.choice([-1, 1]))
        e = O[d, me]
        pas = abs(rng.normal(0, 0.003)) * e
        stop = e - s * pas if rng.random() < 0.8 else np.nan
        obj = e + s * abs(rng.normal(0, 0.003)) * e if rng.random() < 0.6 else np.nan
        if rng.random() < 0.1:                           # niveau deja franchi a l'entree
            stop = e + s * 0.5
        sv, st_, ob = np.zeros(nd, np.int64), np.full(nd, np.nan), np.full(nd, np.nan)
        sv[d], st_[d], ob[d] = s, stop, obj
        a = K.entree_fixe(O, H, L, C, ok, cout, sv, me, st_, ob, ms)[d]
        assert abs(a - entree_fixe_simple(O, H, L, C, d, cout, s, me, stop, obj, ms)) < 1e-9, (d, me, s, stop, obj)
    print("4. entree a heure fixe = version simple (2000 cas tires au hasard) : OK")
    # 5. dans la seance : marche aleatoire
    ts, t1, t2 = controle_martingale(K.toutes)
    print(f"5. marche aleatoire (12 000 seances) : tricheurs detectes (t {t1:+.1f} et {t2:+.1f}), aucune strategie au-dessus"
          f" de 4 (max {max(ts.values()):+.2f}) : OK")


if __name__ == "__main__":
    main()
