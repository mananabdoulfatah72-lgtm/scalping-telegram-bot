#!/usr/bin/env python3
"""Lance l'evolution n°2 (README.md) : 5 graines sur les vraies donnees 2011-2022, 5 graines sur des donnees melangees
(bruit), 60 generations chacune, avec les especes du profil de volume (et des murs d'options s'ils sont la) et les 9
filtres. Enregistre chaque generation pour la page de suivi (tableau/data.json) et toutes les strategies evaluees
(runs/*.csv). Les donnees 2023-2026 ne sont jamais chargees ici.

Lancer depuis ce dossier : python3 lancer.py
"""
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

import donnees2 as D
import genetique2 as G
import moteur2 as M
from tournoi3 import lire_quotidien

ICI = Path(__file__).resolve().parent
SORTIE = Path(os.getenv("EVO_SORTIE", ICI))            # pour les essais du programme : un autre dossier
RUNS, TABLEAU = SORTIE / "runs", SORTIE / "tableau"
GENERATIONS = int(os.getenv("EVO_GENERATIONS", 60))
GRAINES = [int(x) for x in os.getenv("EVO_GRAINES", "1,2,3,4,5").split(",")]


def donnees_recherche():
    Q = lire_quotidien()
    d = {m: D.charger(m, "recherche", Q) for m in G.MARCHES}
    for m in d:
        assert d[m]["jours"].max() <= np.datetime64("2022-12-31"), "le coffre ne doit pas etre charge"
    return d


def n_especes(d):
    """9 especes si les murs d'options existent sur les deux marches, 7 sinon."""
    return 9 if all(np.isfinite(d[m]["mur_c"]).sum() > 250 for m in d) else 7


melanger = D.melanger2


def detail_leader(donnees, x):
    """Courbe de gain sur la validation (2019-2022) et les 3 dernieres seances avec des trades, pour la page."""
    g = x["g"]
    d = donnees[G.MARCHES[g["marche"]]]
    rend, dol, ntr, t = M.lancer(d, g, noter=True)
    val = d["jours"] > G.FIN_ENTRAINEMENT
    idx = np.where(val)[0]
    courbe = np.cumsum(dol[val])
    pas = max(1, len(courbe) // 250)
    jours_trades = sorted(set(t["jour"][np.isin(t["jour"], idx)].tolist()))[-3:]
    seances = []
    for j in jours_trades:
        sel = t["jour"] == j
        seances.append({"date": str(d["jours"][j]), "o": d["o"][j].round(2).tolist(), "h": d["h"][j].round(2).tolist(),
                        "l": d["l"][j].round(2).tolist(), "c": d["c"][j].round(2).tolist(),
                        "trades": [{"entree": int(e), "sortie": int(s), "sens": int(sn), "px_e": round(float(pe), 2),
                                    "px_s": round(float(ps), 2), "raison": int(r)}
                                   for e, s, sn, pe, ps, r in zip(t["entree"][sel], t["sortie"][sel], t["sens"][sel],
                                                                  t["px_e"][sel], t["px_s"][sel], t["raison"][sel])],
                        "dollars": round(float(dol[j]), 2)})
    risque = float(np.std(dol[val]))
    return {"courbe": courbe[::pas].round(1).tolist(), "dates": [str(d["jours"][i]) for i in idx[::pas]],
            "seances": seances, "risque_1_micro": round(risque, 1),
            "taille_50k": int(np.floor(0.25 * 2500 / risque)) if risque > 0 else 0}


def une_evolution(nature, graine, donnees, tableau, publier):
    ev = G.Evaluateur(donnees)
    evo = G.Evolution(ev, graine)
    evo.demarrer()
    genomes, gens, stats = {}, [], []
    def noter():
        for x in evo.pop:
            genomes[x["id"]] = [x["g"]["espece"], x["g"]["marche"], round(x["u"]["L"], 3), round(x["u"]["Z"], 3), x["g"]["sens"],
                                round(x["u"]["stop"], 3), round(x["u"]["objectif"], 3), round(x["u"]["debut"], 3), x["g"]["filtre"],
                                round(x["fitness"], 3), int(x["porte"]), round(x["validation"]["sharpe"], 3),
                                x["parents"][0] if x["parents"] else 0, x["parents"][1] if x["parents"] else 0, x["ne"]]
        gens.append([x["id"] for x in evo.pop])
        L = evo.leader
        stats.append({"gen": evo.gen, "backtests": ev.backtests, "nes": evo.nes, "morts": evo.morts,
                      "survivants": evo.historique["survivants"][-1], "meilleure": evo.historique["meilleure"][-1],
                      "moyenne": evo.historique["moyenne"][-1], "leader": L["id"] if L else None,
                      "descendants": sum(x["origine"] == "descendant" for x in evo.pop),
                      "immigrants": sum(x["origine"] == "immigrant" for x in evo.pop), "passent": sum(x["porte"] for x in evo.pop)})
        tableau["courant"] = {"nature": nature, "graine": graine, "gen": evo.gen, "total": GENERATIONS, "stats": stats[-1]}
        publier()
    noter()
    for _ in range(GENERATIONS):
        evo.generation()
        noter()
    # toutes les strategies evaluees (pour les finalistes et le registre des essais)
    lignes = [{**g_, "fitness": r["fitness"], "porte": r["porte"], **{f"ent_{k}": v for k, v in r["entrainement"].items()},
               **{f"val_{k}": v for k, v in r["validation"].items()}} for g_, r in ((dict(k), r) for k, r in ev.memoire.items())]
    pd.DataFrame(lignes).to_csv(RUNS / f"{nature}_{graine}.csv", index=False)
    L = evo.leader
    run = {"nature": nature, "graine": graine, "stats": stats, "backtests": ev.backtests,
           "leader": ({"id": L["id"], "g": L["g"], "entrainement": L["entrainement"], "validation": L["validation"],
                       "fitness": L["fitness"], "ne": L["ne"], **detail_leader(donnees, L)} if L else None)}
    if nature == "reel":
        run["genomes"], run["gens"] = genomes, gens
    (RUNS / f"{nature}_{graine}.json").write_text(json.dumps(run, separators=(",", ":")))
    return run


def main():
    RUNS.mkdir(parents=True, exist_ok=True)
    TABLEAU.mkdir(parents=True, exist_ok=True)
    reelles = donnees_recherche()
    G.configurer(n_especes(reelles))
    print(f"{G.N_ESPECES} especes : " + ", ".join(M.ESPECES[:G.N_ESPECES]), flush=True)
    tableau = {"debut": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "runs": {}, "courant": None, "coffre": {"ouvert": False},
               "especes": M.ESPECES[:G.N_ESPECES], "filtres": M.FILTRES}
    fichier = TABLEAU / "data.json"
    dernier = [0.0]
    def publier(force=False):
        if force or time.time() - dernier[0] > 5:
            tableau["maj"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            fichier.write_text(json.dumps(tableau, separators=(",", ":")))
            dernier[0] = time.time()
    for graine in GRAINES:
        rng = np.random.default_rng(1000 + graine)
        bruit = {m: melanger(reelles[m], rng) for m in G.MARCHES}
        run = une_evolution("placebo", graine, bruit, tableau, publier)
        tableau["runs"][f"placebo_{graine}"] = {k: run[k] for k in ("nature", "graine", "stats", "backtests", "leader")}
        publier(True)
        print(f"bruit {graine} : {run['backtests']} strategies, leader "
              + (f"Sharpe entrainement {run['leader']['entrainement']['sharpe']:.2f}, validation {run['leader']['validation']['sharpe']:.2f}"
                 if run["leader"] else "aucun"), flush=True)
    for graine in GRAINES:
        run = une_evolution("reel", graine, reelles, tableau, publier)
        tableau["runs"][f"reel_{graine}"] = {k: run[k] for k in ("nature", "graine", "stats", "backtests", "leader")}
        publier(True)
        print(f"reel {graine} : {run['backtests']} strategies, leader "
              + (f"{M.ESPECES[run['leader']['g']['espece']]} {G.MARCHES[run['leader']['g']['marche']]}, "
                 f"Sharpe entrainement {run['leader']['entrainement']['sharpe']:.2f}, validation {run['leader']['validation']['sharpe']:.2f}"
                 if run["leader"] else "aucun"), flush=True)
    tableau["courant"] = None
    publier(True)


if __name__ == "__main__":
    main()
