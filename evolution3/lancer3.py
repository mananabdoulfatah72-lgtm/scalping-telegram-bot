#!/usr/bin/env python3
"""Lance la machine n°3 (README.md, regles v2) : 8 graines sur les vraies donnees 2016-2022, 8 graines sur des seances melangees
(bruit), 80 generations. Enregistre toutes les strategies evaluees (runs/*.csv.gz) et l'histoire de chaque evolution
pour la page (tableau/data.json). Les donnees 2023-2026 ne sont jamais chargees ici.
Lancer depuis ce dossier : python3 lancer3.py"""
import json
import os
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

import genetique3 as G
import moteur3 as M

ICI = Path(__file__).resolve().parent
RUNS, TABLEAU = ICI / "runs", ICI / "tableau"
GENERATIONS = int(os.getenv("EVO_GENERATIONS", 80))
GRAINES = [int(x) for x in os.getenv("EVO_GRAINES", "1,2,3,4,5,6,7,8").split(",")]


def donnees_recherche():
    d = {m: M.charger(ICI / "cache" / f"recherche_{m}.npz") for m in G.MARCHES}
    for m in d:
        assert d[m]["jours"].max() <= np.datetime64("2022-12-31"), "le coffre ne doit pas etre charge"
    return d  # preparer() est appele apres le melange eventuel (volume de reference recalcule sur le bruit)


def melanger(d, rng):
    """Bruit : chaque seance, les barres de 5 minutes (sauf la 1re) sont remises dans le desordre, avec leur volume. Le
    resultat de la seance et la volatilite sont gardes ; VWAP et niveaux de la veille sont recalcules sur le bruit. Le
    cours du marche leader (lc) est melange avec le meme ordre que le marche (regles v2.1) : les mouvements simultanes
    restent ensemble, l'avance de l'un sur l'autre est detruite."""
    o, h, l, c, v = d["o"], d["h"], d["l"], d["c"], d["v"]
    nj, nb = o.shape
    ro = np.ones_like(o)
    ro[:, 1:] = o[:, 1:] / c[:, :-1]
    rh, rl, rc = h / o, l / o, c / o
    perm = np.concatenate([np.zeros((nj, 1), int), 1 + np.argsort(rng.random((nj, nb - 1)), axis=1)], axis=1)
    ro, rh, rl, rc, v2 = (np.take_along_axis(x, perm, axis=1) for x in (ro, rh, rl, rc, v))
    o2, h2, l2, c2 = (np.empty_like(o) for _ in range(4))
    prix = o[:, 0].copy()
    for b in range(nb):
        ob = prix * (ro[:, b] if b > 0 else 1.0)
        o2[:, b], h2[:, b], l2[:, b], c2[:, b] = ob, ob * rh[:, b], ob * rl[:, b], ob * rc[:, b]
        prix = c2[:, b]
    typ = (h2 + l2 + c2) / 3
    cv = np.cumsum(v2, axis=1)
    vw = np.where(cv > 0, np.cumsum(typ * v2, axis=1) / np.where(cv > 0, cv, 1), np.cumsum(typ, axis=1) / np.arange(1, nb + 1))
    # niveaux de la veille sur le bruit : meme seance precedente que sur les vraies donnees
    prec = d["prec"]
    hj, lj = h2.max(axis=1), l2.min(axis=1)
    ph = np.where(prec >= 0, hj[np.maximum(prec, 0)], np.nan)
    pl = np.where(prec >= 0, lj[np.maximum(prec, 0)], np.nan)
    # leader : rendements de 5 minutes melanges avec la meme permutation ; un rendement absent (leader sans cours) vaut 0,
    # puis les barres ou le leader n'avait pas de cours redeviennent absentes
    lc = d["lc"]
    absent = np.isnan(lc)
    rl = np.zeros_like(lc)
    rl[:, 1:] = np.log(lc[:, 1:] / lc[:, :-1])
    rl = np.nan_to_num(np.take_along_axis(rl, perm, axis=1), nan=0.0)
    premier = np.argmax(~absent, axis=1)
    depart = lc[np.arange(nj), premier]
    lc2 = depart[:, None] * np.exp(np.cumsum(rl, axis=1) - np.take_along_axis(np.cumsum(rl, axis=1), premier[:, None], axis=1))
    lc2[absent] = np.nan
    return {**d, "o": o2, "h": h2, "l": l2, "c": c2, "vwap": vw, "v": v2, "ph": ph, "pl": pl, "lc": lc2}


def une_evolution(args):
    graine, bruit = args
    d = donnees_recherche()
    if bruit:
        rng = np.random.default_rng(1000 + graine)
        d = {m: melanger(x, rng) for m, x in d.items()}
    d = {m: M.preparer(x) for m, x in d.items()}
    ev = G.Evaluateur(d)
    evo = G.Evolution(ev, graine)
    t0 = time.time()
    evo.demarrer()
    instantanes = []
    for _ in range(GENERATIONS):
        evo.generation()
        lead = evo.leader
        instantanes.append({"gen": evo.gen, "leader": None if lead is None else
                            {"id": lead["id"], "g": lead["g"], "fitness": round(lead["fitness"], 3),
                             "validation": round(lead["validation"]["sharpe"], 3), "trades_val": lead["validation"]["trades"]},
                            "top": [{"g": x["g"], "fitness": round(x["fitness"], 3), "porte": x["porte"],
                                     "validation": round(x["validation"]["sharpe"], 3)}
                                    for x in sorted(evo.pop, key=G.Evolution.rang, reverse=True)[:8]]})
    lignes = [{**g, "fitness": r["fitness"], "porte": r["porte"], "sharpe_ent": r["entrainement"]["sharpe"],
               "trades_ent": r["entrainement"]["trades"], "sharpe_val": r["validation"]["sharpe"],
               "trades_val": r["validation"]["trades"], "dollars_val": r["validation"]["dollars"]}
              for k, r in ev.memoire.items() for g in [dict(k)]]
    nom = f"{'bruit' if bruit else 'reel'}_{graine}"
    pd.DataFrame(lignes).to_csv(RUNS / f"{nom}.csv.gz", index=False, float_format="%.5g")
    return {"nom": nom, "graine": graine, "bruit": bruit, "backtests": ev.backtests, "duree": round(time.time() - t0, 1),
            "historique": evo.historique, "instantanes": instantanes, "nes": evo.nes, "morts": evo.morts,
            "deployes": evo.deployes, "elimines": evo.elimines}


def main():
    RUNS.mkdir(exist_ok=True)
    TABLEAU.mkdir(exist_ok=True)
    taches = [(g, b) for g in GRAINES for b in (False, True)]
    t0 = time.time()
    with Pool(int(os.getenv("EVO_PROCESSUS", os.cpu_count() or 2))) as p:
        res = []
        for r in p.imap_unordered(une_evolution, taches):
            res.append(r)
            print(f"{r['nom']:8s} : {r['backtests']} backtests en {r['duree']} s ; nes {r['nes']}, morts {r['morts']},"
                  f" deployes {r['deployes']}, elimines {r['elimines']} ; meilleure fitness {max(r['historique']['meilleure']):.2f}", flush=True)
    res.sort(key=lambda r: (r["bruit"], r["graine"]))
    (TABLEAU / "data.json").write_text(json.dumps({"runs": res, "marches": G.MARCHES, "familles": M.FAMILLES,
                                                   "generations": GENERATIONS, "duree": round(time.time() - t0, 1)},
                                                  separators=(",", ":")))
    print(f"Fini en {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
