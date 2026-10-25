#!/usr/bin/env python3
"""Parties B, B2 et D (README.md) : une machine par marche, 4 graines sur les vraies donnees, 4 sur le bruit par
permutation et 4 sur le bruit par signe (version 3), exploration seulement (caches recherche_*, coupes au 31 decembre
2022). Ecrit resultats/machine_<piste>_<marche>_<reel|bruit|signe>_<graine>.npz.
Lancer : python3 scalping/machine.py B B2 D"""
import multiprocessing as mp
import sys
import time

import numpy as np

import bruit as B
import commun as K
import donnees as D
import genetique as G
import moteur as M
import nuit as NU

SORTIE = K.ICI / "resultats"
GRAINES = 4
GRAINE_BRUIT = {"bruit": 1000, "signe": 5000}
SORTES = ("reel", "bruit", "signe")


def marches(piste):
    return list(NU.MARCHES_NUIT) if piste == "D" else K.PISTES[piste]


def familles(piste, marche):
    if piste == "D":
        return [0, 1, 2, 3, 4, 5, 8, 9]
    return list(range(10)) if marche in K.AUTRE_INDICE else [x for x in range(10) if x != 7]


def fichier(piste, marche, quoi="recherche"):
    return K.CACHE / (f"{quoi}_nuit_{marche}.npz" if piste == "D" else f"{quoi}_{marche}.npz")


def charger(piste, marche, sorte, graine):
    d = dict(np.load(fichier(piste, marche)))
    assert d["jours"].max() <= K.FIN_RECHERCHE
    if sorte != "reel":
        gr = GRAINE_BRUIT[sorte] + graine
        if piste != "D" and marche in K.AUTRE_INDICE:
            q = dict(np.load(fichier(piste, "NQ")))
            e = dict(np.load(fichier(piste, "ES")))
            q, e = B.bruiter_paire(q, e, gr, sorte="permutation" if sorte == "bruit" else "signe")
            q["autre_c"] = D.aligner_autre(q, e)
            e["autre_c"] = D.aligner_autre(e, q)
            d = q if marche == "NQ" else e
        else:
            d = B.bruiter(d, gr, sorte="permutation" if sorte == "bruit" else "signe")
    return d


def bornes(jours, piste="B"):
    i = lambda x: int(np.searchsorted(jours, x))                                  # noqa: E731
    if piste == "D":
        return i(NU.DEBUT_ENTRAINEMENT_NUIT), i(NU.DEBUT_VALIDATION_NUIT), i(K.FIN_RECHERCHE + np.timedelta64(1, "D"))
    if piste == "B2":
        return i(K.DEBUT_ENTRAINEMENT_B2), i(K.DEBUT_VALIDATION_B2), i(K.FIN_RECHERCHE + np.timedelta64(1, "D"))
    return i(K.DEBUT_ENTRAINEMENT), i(K.DEBUT_VALIDATION), i(K.FIN_RECHERCHE + np.timedelta64(1, "D"))


def tache(args):
    piste, marche, sorte, graine, generations, taille = args
    t0 = time.time()
    d = charger(piste, marche, sorte, graine)
    f = M.indicateurs(d)
    s0, sv, s1 = bornes(d["jours"], piste)
    rng = np.random.default_rng({"reel": 0, "bruit": 100, "signe": 200}[sorte] + graine)
    vus = G.evoluer(f, s0, sv, rng, familles(piste, marche), generations=generations, taille=taille)
    genomes = np.array([v[0] for v in vus.values()])
    fit = np.array([v[1] for v in vus.values()])
    t_tr = np.array([v[2] for v in vus.values()])
    n_tr = np.array([v[3] for v in vus.values()])
    t_v = np.full(len(genomes), np.nan)
    n_v = np.zeros(len(genomes), np.int64)
    score = np.full(len(genomes), np.nan)
    net_tr = np.full(len(genomes), np.nan)
    gagn = np.full(len(genomes), np.nan)
    for i in np.flatnonzero((t_tr >= 2.0) & (n_tr >= 200)):
        gain, n, w, brut, _ = M.jouer(genomes[i], f, s0, s1)
        va = gain[sv - s0:]
        _, n_v[i], _ = G.mesurer(genomes[i], f, sv, s1)
        t_v[i] = K.t_stat(va[np.isfinite(va)])
        score[i] = K.t_stat(gain[np.isfinite(gain)])
        net_tr[i] = np.nansum(gain) / max(n, 1)
        gagn[i] = w / max(n, 1)
    SORTIE.mkdir(exist_ok=True)
    np.savez_compressed(SORTIE / f"machine_{piste}_{marche}_{sorte}_{graine}.npz", genomes=genomes, fit=fit, t_tr=t_tr,
                        n_tr=n_tr, t_v=t_v, n_v=n_v, score=score, net_trade=net_tr, gagnants=gagn)
    elig = (t_tr >= 2) & (n_tr >= 200) & (t_v >= 1) & (n_v >= 50)
    return (f"{piste} {marche} {sorte} {graine} : {len(genomes)} strategies distinctes en {time.time() - t0:.0f} s, "
            f"meilleur t entrainement {t_tr.max():.2f}, eligibles {int(elig.sum())}, meilleur score "
            f"{np.nanmax(np.where(elig, score, np.nan)) if elig.any() else float('nan'):.2f}")


def main():
    pistes = [a for a in sys.argv[1:] if a in ("B", "B2", "D")] or ["B"]
    sortes = [s for s in SORTES if f"--{s}" in sys.argv] or list(SORTES)       # --reel, --bruit, --signe
    generations, taille = 60, 200
    taches = [(p, m, s, g, generations, taille) for g in range(1, GRAINES + 1) for p in pistes for m in marches(p)
              for s in sortes if not (SORTIE / f"machine_{p}_{m}_{s}_{g}.npz").exists()]
    t0 = time.time()
    with mp.get_context("fork").Pool(4) as pool:
        for k, msg in enumerate(pool.imap_unordered(tache, taches)):
            print(f"[{k + 1}/{len(taches)} {time.time() - t0:.0f} s] {msg}", flush=True)


if __name__ == "__main__":
    main()
