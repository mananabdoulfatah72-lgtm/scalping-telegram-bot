#!/usr/bin/env python3
"""Partie B (README.md) : une machine par marche, 4 graines sur les vraies donnees et 4 sur bruit, exploration 2017-2022
seulement (cache recherche_*). Ecrit resultats/machine_<marche>_<reel|bruit>_<graine>.npz.
Lancer : python3 scalping/machine.py [generations] [taille]"""
import multiprocessing as mp
import sys
import time

import numpy as np

import bruit as B
import commun as K
import donnees as D
import genetique as G
import moteur as M

SORTIE = K.ICI / "resultats"
GRAINES = 4
GRAINE_BRUIT = 1000


def charger(marche, sorte, graine):
    d = dict(np.load(K.CACHE / f"recherche_{marche}.npz"))
    assert d["jours"].max() <= K.FIN_RECHERCHE
    if sorte == "bruit":
        if marche in K.AUTRE_INDICE:
            q = dict(np.load(K.CACHE / "recherche_NQ.npz"))
            e = dict(np.load(K.CACHE / "recherche_ES.npz"))
            q, e = B.bruiter_paire(q, e, GRAINE_BRUIT + graine)
            q["autre_c"] = D.aligner_autre(q, e)
            e["autre_c"] = D.aligner_autre(e, q)
            d = q if marche == "NQ" else e
        else:
            d = B.bruiter(d, GRAINE_BRUIT + graine)
    return d


def bornes(jours):
    i = lambda x: int(np.searchsorted(jours, x))                                  # noqa: E731
    return i(K.DEBUT_ENTRAINEMENT), i(K.DEBUT_VALIDATION), i(K.FIN_RECHERCHE + np.timedelta64(1, "D"))


def tache(args):
    marche, sorte, graine, generations, taille = args
    t0 = time.time()
    d = charger(marche, sorte, graine)
    f = M.indicateurs(d)
    s0, sv, s1 = bornes(d["jours"])
    familles = list(range(10)) if marche in K.AUTRE_INDICE else [x for x in range(10) if x != 7]
    rng = np.random.default_rng(graine if sorte == "reel" else 100 + graine)
    vus = G.evoluer(f, s0, sv, rng, familles, generations=generations, taille=taille)
    genomes = np.array([v[0] for v in vus.values()])
    fit = np.array([v[1] for v in vus.values()])
    t_tr = np.array([v[2] for v in vus.values()])
    n_tr = np.array([v[3] for v in vus.values()])
    t_v = np.full(len(genomes), np.nan)
    n_v = np.zeros(len(genomes), np.int64)
    score = np.full(len(genomes), np.nan)
    net_tr = np.full(len(genomes), np.nan)
    gagn = np.full(len(genomes), np.nan)
    cand = np.flatnonzero((t_tr >= 2.0) & (n_tr >= 200))
    for i in cand:
        gain, n, w, brut, _ = M.jouer(genomes[i], f, s0, s1)
        tr, va = gain[:sv - s0], gain[sv - s0:]
        _, n_v[i], _ = G.mesurer(genomes[i], f, sv, s1)
        x = va[np.isfinite(va)]
        t_v[i] = K.t_stat(x)
        score[i] = K.t_stat(gain[np.isfinite(gain)])
        net_tr[i] = np.nansum(gain) / max(n, 1)
        gagn[i] = w / max(n, 1)
    SORTIE.mkdir(exist_ok=True)
    np.savez_compressed(SORTIE / f"machine_{marche}_{sorte}_{graine}.npz", genomes=genomes, fit=fit, t_tr=t_tr, n_tr=n_tr,
                        t_v=t_v, n_v=n_v, score=score, net_trade=net_tr, gagnants=gagn)
    elig = (t_tr >= 2) & (n_tr >= 200) & (t_v >= 1) & (n_v >= 50)
    return (f"{marche} {sorte} {graine} : {len(genomes)} strategies distinctes en {time.time() - t0:.0f} s, meilleur t "
            f"entrainement {t_tr.max():.2f}, eligibles {int(elig.sum())}, meilleur score "
            f"{np.nanmax(np.where(elig, score, np.nan)) if elig.any() else float('nan'):.2f}")


def main():
    generations = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    taille = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    taches = [(m, s, g, generations, taille) for g in range(1, GRAINES + 1) for m in K.MARCHES for s in ("reel", "bruit")]
    t0 = time.time()
    with mp.get_context("fork").Pool(4) as pool:
        for k, msg in enumerate(pool.imap_unordered(tache, taches)):
            print(f"[{k + 1}/{len(taches)} {time.time() - t0:.0f} s] {msg}", flush=True)


if __name__ == "__main__":
    main()
