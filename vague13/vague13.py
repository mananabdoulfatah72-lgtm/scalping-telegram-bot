#!/usr/bin/env python3
"""Vague 13 (README.md) : arret a l'objectif et taille adaptative pendant le challenge Bulenox de 30 jours (Legacy et
Momentum), chaque seance comme jour d'achat, 21 tirages du filtre. Ecrit vague13.json."""
import json
import multiprocessing as mp
import sys
import time

import numpy as np

import regles13 as R

K = R.K
sys.path.insert(0, str(K.ICI))
import vague12 as V  # noqa: E402

CAND = R.candidates()
FILTRES = {"fort": 10, "moitie": 10, "aucun": 1}


def tache(args):
    ic, fil, t = args
    nom, compte, lettre = CAND[ic]
    A = K.COMPTES[compte]
    b = V.P["bases"][fil][t]
    dd = V.jours_achat(compte)
    out = np.full((len(dd), 8), np.nan)
    for k, d in enumerate(dd):
        sv = min(K.H, (V.CHOIX_SUIVI if d < V.CHOIX_FIN else V.NJ) - d)
        r, ret = R.un_achat(V.P, b, int(d), compte, lettre, sv, V.LIM[d])
        net = ret[:K.H].sum() * A["part"] - A["prix"] - (A["activation"] if r[0] == 1 else 0.0) if sv >= K.H else np.nan
        perdu12 = (float(bool(r[2]) and r[6] - r[1] <= 252) if r[0] == 1 and sv - r[1] >= 252 else np.nan)
        out[k] = (d, r[0], r[1], perdu12, float(ret[:K.H].sum() > 0) if sv >= K.H else np.nan, net, r[3], sv)
    return ic, fil, t, out


def main():
    t0 = time.time()
    V.CAND[:] = [(n, c, 4, 0.0, 0.0) for n, c, _ in CAND]          # pour V.resumer (noms et comptes)
    taches = [(ic, fil, t) for ic in range(len(CAND)) for fil, n in FILTRES.items() for t in range(n)]
    Rz = {ic: {fil: [] for fil in FILTRES} for ic in range(len(CAND))}
    with mp.get_context("fork").Pool(4) as pool:
        for k, (ic, fil, t, out) in enumerate(pool.imap_unordered(tache, taches)):
            Rz[ic][fil].append(out)
            if k % 25 == 0:
                print(f"{k + 1}/{len(taches)} taches, {time.time() - t0:.0f} s", flush=True)
    Rz = {ic: {fil: np.vstack(v) for fil, v in d.items()} for ic, d in Rz.items()}
    res = V.resumer(Rz)
    (R.ICI / "vague13.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(f"fini en {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
