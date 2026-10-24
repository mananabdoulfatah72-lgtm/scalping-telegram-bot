#!/usr/bin/env python3
"""Controles de la machine scalping (README.md). Lancer : python3 scalping/test_scalping.py"""
import numpy as np

import bruit as B
import commun as K
import genetique as G
import machine as MA
import moteur as M


def _seance_seule(f, s):
    return M.jouer


def test_coupure():
    for nom in K.MARCHES:
        r = np.load(K.CACHE / f"recherche_{nom}.npz")
        c = np.load(K.CACHE / f"complet_{nom}.npz")
        assert r["jours"].max() <= K.FIN_RECHERCHE, nom
        n = len(r["jours"])
        for k in ("o", "h", "l", "c", "v"):
            assert np.array_equal(r[k], c[k][:n], equal_nan=True), (nom, k)
    print("coupure du coffre : ok (caches de recherche jusqu'au 31 decembre 2022, identiques au cache complet avant)")


def test_pas_de_futur(n_essais=150):
    """Changer les minutes apres T d'une seance ne change aucune decision prise jusqu'a T."""
    rng = np.random.default_rng(11)
    for nom in ("NQ", "GC"):
        d = dict(np.load(K.CACHE / f"recherche_{nom}.npz"))
        f = M.indicateurs(d)
        s0, _, s1 = MA.bornes(d["jours"])
        jouables = np.flatnonzero(f["jouable"][s0:s1]) + s0
        familles = list(range(10)) if nom in K.AUTRE_INDICE else [x for x in range(10) if x != 7]
        verifies = 0
        for i in range(n_essais):
            g = G.aleatoire(rng, familles) if i < n_essais - 6 else np.r_[[10 + i - (n_essais - 6)], np.zeros(M.NG - 1)]
            s = int(jouables[rng.integers(len(jouables))])
            T = int(rng.integers(20, d["c"].shape[1] - 5))
            d2 = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in d.items()}
            n = d["c"].shape[1]
            pas = np.exp(np.cumsum(rng.normal(0, 0.002, n - T - 1)))
            base = d["c"][s, T]
            for k, fac in (("o", 1.0), ("h", 1.003), ("l", 0.997), ("c", 1.0)):
                d2[k][s, T + 1:] = np.round(base * pas * fac / d["tick"]) * d["tick"]
            d2["v"][s, T + 1:] = rng.integers(1, 5000, n - T - 1)
            f2 = M.indicateurs(d2)
            _, _, _, _, j1 = M.jouer(g, f, s, s + 1, journal=500)
            _, _, _, _, j2 = M.jouer(g, f2, s, s + 1, journal=500)
            e1 = [tuple(x[[1, 3, 4]]) for x in j1 if x[1] <= T]
            e2 = [tuple(x[[1, 3, 4]]) for x in j2 if x[1] <= T]
            assert e1 == e2, (nom, g, s, T, e1, e2)
            x1 = [tuple(x) for x in j1 if x[2] <= T]
            x2 = [tuple(x) for x in j2 if x[2] <= T]
            assert x1 == x2, (nom, g, s, T)
            verifies += len(e1)
        print(f"pas de regard vers le futur ({nom}) : ok, {n_essais} essais, {verifies} entrees comparees")


def test_execution_a_la_main():
    """Seance fabriquee : stop et objectif touches dans la meme minute -> stop (ordre le plus defavorable)."""
    d = dict(np.load(K.CACHE / "recherche_NQ.npz"))
    f = M.indicateurs(d)
    s0, _, s1 = MA.bornes(d["jours"])
    s = int(np.flatnonzero(f["jouable"][s0:s1])[0] + s0)
    g = np.zeros(M.NG)
    g[M.FAM] = 9
    g[M.PX] = 3                     # evenement 10 h 00 : signal a la cloture de 9 h 59 (minute 29)
    g[M.PK] = 0                     # k = 1
    g[M.PZ] = 0.0
    g[M.DEBUT] = 0
    g[M.FIN] = 4
    g[M.STOP] = 1.0
    g[M.OBJ] = 1.0
    g[M.DUREE] = 7
    gain, n, _, _, j = M.jouer(g, f, s, s + 1, journal=5)
    assert n == 1 and j[0, 1] == 30
    sens = int(j[0, 3])
    ent = f["O"][s, 30]
    assert j[0, 4] == ent
    u = f["sig"][s, 29] * np.sqrt(15) * f["C"][s, 29]
    stp = ent - sens * max(u, 0.5)
    tgt = ent + sens * max(u, 0.5)
    # rejoue a la main
    t = 30
    while True:
        o, h, l, c = f["O"][s, t], f["H"][s, t], f["L"][s, t], f["C"][s, t]
        if sens == 1:
            if t > 30 and o <= stp:
                sortie = o
                break
            if l <= stp:
                sortie = stp
                break
            if h >= tgt + 0.25:
                sortie = tgt
                break
        else:
            if t > 30 and o >= stp:
                sortie = o
                break
            if h >= stp:
                sortie = stp
                break
            if l <= tgt - 0.25:
                sortie = tgt
                break
        if t >= 30 + 30 - 1:
            sortie = c
            break
        t += 1
    assert j[0, 2] == t and abs(j[0, 5] - sortie) < 1e-9, (j, t, sortie)
    attendu = sens * (sortie - ent) * 2.0 * f["echelle"][s] - 3.0
    assert abs(gain[0] - attendu) < 1e-9
    print("execution refaite a la main : ok")


def test_regles_a_simples():
    """A1 et A3 refaites avec numpy, sans le moteur."""
    for nom in ("NQ", "ES"):
        d = dict(np.load(K.CACHE / f"recherche_{nom}.npz"))
        f = M.indicateurs(d)
        s0, _, s1 = MA.bornes(d["jours"])
        O, C, lr = f["O"], f["C"], f["lr"]
        N = C.shape[1]
        tot1, n1, tot3, n3 = 0.0, 0, 0.0, 0
        for s in range(s0, s1):
            if not f["jouable"][s]:
                continue
            r = np.log(C[s, 14] / O[s, 0])
            if np.isfinite(f["thr1"][s]) and abs(r) >= f["thr1"][s] and r != 0:
                dd = -np.sign(r)
                tot1 += dd * (C[s, N - 1] - O[s, 15]) * f["pt"] * f["echelle"][s] - f["frais"]
                n1 += 1
            r = lr[s, 30]
            if np.isfinite(f["thr3"][s]) and abs(r) >= f["thr3"][s] and r != 0:
                dd = np.sign(r)
                tot3 += dd * (C[s, 31] - O[s, 31]) * f["pt"] * f["echelle"][s] - f["frais"]
                n3 += 1
        for fam, tot, n in ((10, tot1, n1), (12, tot3, n3)):
            g = np.zeros(M.NG)
            g[M.FAM] = fam
            gain, nn, _, _, _ = M.jouer(g, f, s0, s1)
            assert nn == n and abs(np.nansum(gain) - tot) < 1e-6, (nom, fam, nn, n, np.nansum(gain), tot)
    print("A1 et A3 refaites a la main : ok")


def test_bruit():
    q = dict(np.load(K.CACHE / "recherche_NQ.npz"))
    e = dict(np.load(K.CACHE / "recherche_ES.npz"))
    q2, e2 = B.bruiter_paire(q, e, 7)
    for d, d2 in ((q, q2), (e, e2)):
        cpl = d["complete"]
        n = d["c"].shape[1]
        ans = d["jours"].astype("datetime64[Y]")
        src = d2["src"]
        for a in np.unique(ans):
            idx = np.flatnonzero((ans == a) & cpl)
            for m in (1, 100, n - 1):
                assert sorted(src[idx, m]) == sorted(idx)          # chaque barre source utilisee une fois par minute
                assert (ans[src[idx, m]] == a).all()
        assert np.allclose(np.round(d2["c"] / d["tick"]) * d["tick"], d2["c"])
        assert (d2["h"] >= np.maximum(d2["o"], d2["c"]) - 1e-9).all() and (d2["l"] <= np.minimum(d2["o"], d2["c"]) + 1e-9).all()
    # meme seance source pour NQ et ES aux dates communes
    jq, je = q["jours"], e["jours"]
    communs = np.intersect1d(jq[q["complete"]], je[e["complete"]])
    iq = np.searchsorted(jq, communs)
    ie = np.searchsorted(je, communs)
    for m in (1, 50, 389):
        assert np.array_equal(jq[q2["src"][iq, m]], je[e2["src"][ie, m]])
    print("bruit : ok (permutation par annee et par minute, prix au tick, meme source pour NQ et ES)")


def marche_aleatoire(rng, d, pas=30):
    """Chemin aleatoire de `pas` pas par minute (volatilite en U, aucune derive), arrondi au tick, puis barres d'une minute
    (ouverture, plus haut, plus bas, cloture du chemin) : aucune information, ni entre minutes ni dans la minute."""
    S, N = d["c"].shape
    u = 0.0004 * (1 + 1.5 * (np.linspace(-1, 1, N) ** 2)) / np.sqrt(pas)
    tk = d["tick"]
    O = np.empty((S, N)); H = np.empty((S, N)); L = np.empty((S, N)); C = np.empty((S, N)); X = np.empty((S, N))
    niveau = 10000.0
    for s in range(S):
        z = rng.normal(0, 1, (N, pas)) * u[:, None]
        chemin = niveau * np.exp(np.cumsum(z.ravel())).reshape(N, pas)
        chemin = np.round(chemin / tk) * tk
        O[s] = np.r_[np.round(niveau / tk) * tk, chemin[:-1, -1]]
        H[s] = np.maximum(chemin.max(axis=1), O[s])
        L[s] = np.minimum(chemin.min(axis=1), O[s])
        C[s] = chemin[:, -1]
        X[s] = np.round(C[s] * np.exp(rng.normal(0, 1, N) * u * 3) / tk) * tk
        niveau = C[s, -1]
    return dict(d, o=O, h=H, l=L, c=C, v=rng.integers(100, 10000, (S, N)).astype(float), autre_c=X)


def test_marche_aleatoire(n=600):
    """Marche sans aucune information : aucune strategie ne doit sortir du hasard."""
    rng = np.random.default_rng(3)
    d = marche_aleatoire(rng, dict(np.load(K.CACHE / "recherche_NQ.npz")))
    f = M.indicateurs(d)
    s0, _, s1 = MA.bornes(d["jours"])
    ts, ent = [], []
    for i in range(n):
        g = G.aleatoire(rng, list(range(10)))
        t, k, _ = G.mesurer(g, f, s0, s1)
        if k >= 200:
            ts.append(t)
            ent.append(int(g[M.ENTREE]))
    ts, ent = np.array(ts), np.array(ent)
    print(f"marche aleatoire : {len(ts)} strategies avec au moins 200 trades, t median {np.median(ts):.2f}, "
          f"plus haut {ts.max():.2f}, part au-dessus de 2 : {np.mean(ts >= 2):.1%} ; au marche : t median "
          f"{np.median(ts[ent == 0]):.2f} ; a cours limite : t median {np.median(ts[ent > 0]):.2f}")
    assert ts.max() < 4.0 and np.median(ts) < 0.0


if __name__ == "__main__":
    test_coupure()
    test_bruit()
    test_regles_a_simples()
    test_execution_a_la_main()
    test_pas_de_futur()
    test_marche_aleatoire()
    print("tous les controles passent")
