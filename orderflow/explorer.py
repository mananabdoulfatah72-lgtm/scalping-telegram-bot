#!/usr/bin/env python3
"""Order flow NQ (README.md) : exploration sur les deux premiers tiers des seances. Le coffre (dernier tiers) n'est pas
charge. Ecrit exploration_of.txt et survivants_of.json.
Lancer depuis ce dossier : ROBOT_ZONE=/chemin/zone/robot.py ROBOT_MINUTES=/chemin/nq_1min.csv.gz python3 explorer.py"""
import importlib.util
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

import outils as O
import signaux as G

ICI = Path(__file__).resolve().parent
NOMS = {"H2": "Absorption sur un niveau, retournement (15 min)", "H3": "Suivre les gros ordres (15 min)",
        "H4": "Divergence du CVD sur nouveau plus haut / bas (15 min)", "H5": "Suivre le delta de 15 minutes (30 min)"}


def decoupe(n):
    return (2 * n) // 3


def mesurer(S, trades, graine):
    x = O.executer(S, trades)
    if len(x) == 0:
        return {"trades": 0}, x
    ts = O.hasard(S, trades, n=1000, graine=graine)
    t = O.t_stat(x["net"])
    return {"trades": int(len(x)), "brut_pts": round(float(x["brut"].mean()), 3), "ecart_pts": round(float(x["ecart"].mean()), 3),
            "net_pts": round(float(x["net"].mean()), 3), "net_dollars_mnq": round(float(x["net"].mean() * 2), 2),
            "gagnants": round(float((x["net"] > 0).mean()), 3), "t": round(t, 3),
            "hasard_part_battue": round(float((ts < t).mean()), 3), "hasard_t_95": round(float(np.quantile(ts, 0.95)), 3)}, x


def detecter(S, gros, seances):
    return {"H2": G.h2_absorption(S, seances), "H3": G.h3_gros_ordres(S, gros, seances),
            "H4": G.h4_divergence(S, seances), "H5": G.h5_delta15(S, seances)}


def zone(S, seances):
    spec = importlib.util.spec_from_file_location("robot", os.environ["ROBOT_ZONE"])
    robot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(robot)
    minutes = pd.read_csv(os.environ["ROBOT_MINUTES"])
    z = G.trades_zone(robot, minutes, S.jours[list(seances)])
    return G.h1_filtre(S, z)


def juger_h1(f):
    if f.empty:
        return {"trades": 0}
    g, e = f[f["garde"]]["points"], f[~f["garde"]]["points"]
    diff = g.mean() - e.mean() if len(g) and len(e) else float("nan")
    se = np.sqrt(g.var(ddof=1) / len(g) + e.var(ddof=1) / len(e)) if len(g) > 1 and len(e) > 1 else float("nan")
    return {"trades": int(len(f)), "gardes": int(len(g)), "ecartes": int(len(e)), "points_gardes": round(float(g.mean()), 2) if len(g) else None,
            "points_ecartes": round(float(e.mean()), 2) if len(e) else None, "points_tous": round(float(f["points"].mean()), 2),
            "difference": round(float(diff), 2), "t_difference": round(float(diff / se), 2) if se and se > 0 else None}


def main():
    S = O.Seances()
    n = len(S.jours)
    k = decoupe(n)
    S.restreindre(k)
    gros = G.lire_gros(S, O.D)
    gros = gros[gros["jour"] <= S.jours[-1]]
    seances = list(range(k))
    lignes = [f"Order flow NQ, exploration : {k} seances du {S.jours[0].date()} au {S.jours[-1].date()} (le coffre, {n - k} seances, n'est pas charge).",
              f"Execution au marche : achat au meilleur vendeur, vente au meilleur acheteur, a la seconde qui suit le signal, + 0,5 point par ordre (1 $ MNQ).", ""]
    res, survivants = {}, []
    for i, (h, tr) in enumerate(detecter(S, gros, seances).items()):
        m, x = mesurer(S, tr, graine=100 * (i + 1))
        survit = m["trades"] > 0 and m["net_pts"] > 0 and m["t"] >= 2 and m["hasard_part_battue"] >= 0.95
        m["survit"] = bool(survit)
        res[h] = m
        if survit:
            survivants.append(h)
        if m["trades"]:
            lignes.append(f"{h} {NOMS[h]} : {m['trades']} trades | brut {m['brut_pts']:+.2f} pt | ecart paye {m['ecart_pts']:.2f} pt |"
                          f" net {m['net_pts']:+.2f} pt ({m['net_dollars_mnq']:+.2f} $ par MNQ) | gagnants {m['gagnants']:.0%} | t {m['t']:+.2f} |"
                          f" bat le hasard {m['hasard_part_battue']:.1%} -> {'SURVIT' if survit else 'elimine'}")
        else:
            lignes.append(f"{h} {NOMS[h]} : aucun signal -> elimine")
    f = zone(S, seances)
    r1 = juger_h1(f)
    res["H1"] = r1
    if r1["trades"]:
        lignes += ["", f"H1 filtre order flow de la zone de bruit : {r1['trades']} trades de zone ; delta des 30 min dans le sens du trade :"
                   f" {r1['gardes']} trades, {r1['points_gardes']:+.2f} pt en moyenne ; contre : {r1['ecartes']} trades, {r1['points_ecartes']:+.2f} pt"
                   f" (tous : {r1['points_tous']:+.2f} pt). Difference {r1['difference']:+.2f} pt, t {r1['t_difference']}"
                   " (echantillon petit : descriptif)."]
    lignes += ["", f"Survivants (H2 a H5) : {', '.join(survivants) if survivants else 'aucun'}"]
    (ICI / "exploration_of.txt").write_text("\n".join(lignes) + "\n")
    (ICI / "survivants_of.json").write_text(json.dumps({"survivants": survivants, "resultats": res, "seances_exploration": k,
                                                        "seances_total": n}, indent=1, ensure_ascii=False))
    print("\n".join(lignes))


if __name__ == "__main__":
    main()
