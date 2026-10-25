#!/usr/bin/env python3
"""Version 5 (README.md) : la meme machine que la version 4, sur les caches complets. La machine ne cherche que sur
l'entrainement (jour 2017 - 2022, bitcoin 2020 - 2022, nuit 2013 - 2022) ; chaque admise (t >= 2 et 200 trades sur
l'entrainement) est jouee sur le controle (2023 - fin des donnees), dont on garde les gains quotidiens. 6 graines (11 a
16) par sorte : vrai, bruit par permutation, bruit par signe. Ecrit resultats/v5/machine_<piste>_<marche>_<sorte>_<graine>.npz.
Lancer : python3 scalping/vague5.py B B2 D"""
import multiprocessing as mp
import sys
import time

import numpy as np

import bruit as B
import commun as K
import donnees as D
import genetique as G
import machine as MA
import moteur as M
import nuit as NU

SORTIE = MA.SORTIE / "v5"
GRAINES = range(11, 17)
DEBUT_CONTROLE = np.datetime64("2023-01-01")
DEBUT_ENTRAINEMENT = {"B": K.DEBUT_ENTRAINEMENT, "B2": K.DEBUT_ENTRAINEMENT_B2, "D": NU.DEBUT_ENTRAINEMENT_NUIT}
ANNEES = (2023, 2024, 2025, 2026)
T_ADMISSION, N_ADMISSION = 2.0, 200


def charger(piste, marche, sorte, graine):
    """Comme machine.charger, sur les caches complets : le bruit couvre aussi le controle."""
    d = dict(np.load(MA.fichier(piste, marche, "complet")))
    if sorte != "reel":
        gr = MA.GRAINE_BRUIT[sorte] + graine
        so = "permutation" if sorte == "bruit" else "signe"
        if piste != "D" and marche in K.AUTRE_INDICE:
            q = dict(np.load(MA.fichier(piste, "NQ", "complet")))
            e = dict(np.load(MA.fichier(piste, "ES", "complet")))
            q, e = B.bruiter_paire(q, e, gr, sorte=so)
            q["autre_c"] = D.aligner_autre(q, e)
            e["autre_c"] = D.aligner_autre(e, q)
            d = q if marche == "NQ" else e
        else:
            d = B.bruiter(d, gr, sorte=so)
    return d


def bornes(jours, piste):
    i = lambda x: int(np.searchsorted(jours, x))                                  # noqa: E731
    return i(DEBUT_ENTRAINEMENT[piste]), i(DEBUT_CONTROLE), len(jours)


def tache(args):
    piste, marche, sorte, graine, generations, taille = args
    t0 = time.time()
    d = charger(piste, marche, sorte, graine)
    f = M.indicateurs(d)
    s0, sc, s1 = bornes(d["jours"], piste)
    rng = np.random.default_rng({"reel": 0, "bruit": 100, "signe": 200}[sorte] + graine)
    vus = G.evoluer(f, s0, sc, rng, MA.familles(piste, marche), generations=generations, taille=taille)
    genomes = np.array([v[0] for v in vus.values()])
    t_tr = np.array([v[2] for v in vus.values()])
    n_tr = np.array([v[3] for v in vus.values()])
    adm = np.flatnonzero((t_tr >= T_ADMISSION) & (n_tr >= N_ADMISSION))
    ans = d["jours"][sc:s1].astype("datetime64[Y]").astype(int) + 1970
    gains = np.zeros((len(adm), s1 - sc), np.float32)        # gains quotidiens au controle, NaN = seance non jouable
    t_c = np.zeros(len(adm))
    n_c = np.zeros(len(adm), np.int64)
    par_an = np.zeros((len(adm), len(ANNEES)))
    for k, i in enumerate(adm):
        gain, n, _, _, _ = M.jouer(genomes[i], f, sc, s1)
        gains[k] = gain
        x = gain[np.isfinite(gain)]
        t_c[k] = K.t_stat(x)
        n_c[k] = n
        par_an[k] = [np.nansum(gain[ans == a]) for a in ANNEES]
    SORTIE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(SORTIE / f"machine_{piste}_{marche}_{sorte}_{graine}.npz", genomes=genomes[adm], t_tr=t_tr[adm],
                        n_tr=n_tr[adm], t_c=t_c, n_c=n_c, par_an=par_an, gains=gains, jours=d["jours"][sc:s1],
                        distinctes=len(genomes))
    return (f"{piste} {marche} {sorte} {graine} : {len(genomes)} strategies distinctes en {time.time() - t0:.0f} s, "
            f"admises {len(adm)}, meilleur t entrainement {t_tr.max():.2f}, meilleur t controle "
            f"{t_c.max() if len(adm) else float('nan'):.2f}")


def main():
    pistes = [a for a in sys.argv[1:] if a in ("B", "B2", "D")] or ["B"]
    sortes = [s for s in MA.SORTES if f"--{s}" in sys.argv] or list(MA.SORTES)
    generations, taille = 60, 200
    taches = [(p, m, s, g, generations, taille) for g in GRAINES for p in pistes for m in MA.marches(p) for s in sortes
              if not (SORTIE / f"machine_{p}_{m}_{s}_{g}.npz").exists()]
    t0 = time.time()
    with mp.get_context("fork").Pool(4) as pool:
        for k, msg in enumerate(pool.imap_unordered(tache, taches)):
            print(f"[{k + 1}/{len(taches)} {time.time() - t0:.0f} s] {msg}", flush=True)


if __name__ == "__main__":
    main()
