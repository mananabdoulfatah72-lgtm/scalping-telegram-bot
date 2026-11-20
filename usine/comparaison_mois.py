#!/usr/bin/env python3
"""Tous les bots codes dans l'usine, sur le mois du Supertrend (13 octobre -> 19 novembre 2026) et sur 2015 - 2026 :
gain a 1 MNQ, et chances du compte de l'utilisateur (52 000 $, plancher 50 100 $, retrait a 53 600 $, 22 seances).
Reglages : ceux du bot, ou le centre du plateau choisi par l'usine sur 2011 - 2014 (registre.csv) ; aucun reglage sur le mois.
Usage : KB_MINUTES=<nasdaq100_1min.csv.gz> NQ_RECENT=<nq_1min.csv.gz> python3 usine/comparaison_mois.py
"""
import csv
import json
import os
import sys
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import donnees as Dn  # noqa: E402
import moteur as Mo  # noqa: E402
import pupitre as Pu  # noqa: E402
import indicateurs  # noqa: E402,F401
import agents_st as A  # noqa: E402

DEBUT_MOIS, FIN_MOIS = "2026-10-13", "2026-11-19"


def centres():
    c = {}
    for r in csv.DictReader(open(ICI / "registre.csv")):
        if r.get("centre"):
            try:
                c[r["idee"]] = json.loads(r["centre"])
            except json.JSONDecodeError:
                pass
    return c


def principal():
    D = Dn.charger(recent=os.environ.get("NQ_RECENT") or None)
    P = Mo.deriver(D); J = D["J"]; ok = D["complete"].copy()
    i19 = np.where(J == "2026-11-19")[0]
    if len(i19):
        ok[i19[0]] = True                                   # 19 novembre : minutes jusqu'a 15 h 46
    P["ok"] = ok
    O, H, L, C = P["O"], P["H"], P["L"], P["C"]
    cen = centres()
    bots = {"Supertrend 10-3 (ton bot)": (Mo.k_supertrend(O, H, L, C, ok, 10, 3.0), 400.0)}
    for nom, fl in (("Supertrend + stop ramene a l'entree (A1)", (True, False, False)), ("Supertrend + arret apres bougie folle (A2)", (False, True, False)),
                    ("Supertrend + sortie quand l'elan s'arrete (A3)", (False, False, True))):
        bots[nom] = (A.k_st_agents(O, H, L, C, ok, 10, 3.0, *fl), 400.0)
    Z = Mo.STRATEGIES["zone"]
    bots["Zone de bruit (G2 sans le frein)"] = (Z["f"](P, **Z["bot"]), Z["limite"])
    for cle, v in Mo.STRATEGIES.items():
        if cle in ("zone", "supertrend", "zone_large"):
            continue
        if v.get("bot"):
            bots[f"{v['titre']}, reglage par defaut"] = (v["f"](P, **v["bot"]), v["limite"])
        if cle in cen and cen[cle] != v.get("bot"):
            bots[f"{v['titre']}, reglage de l'usine {cen[cle]}"] = (v["f"](P, **cen[cle]), v["limite"])
    idx = np.where(ok & (J >= "2015-01-01"))[0]; m = (J[idx] >= DEBUT_MOIS) & (J[idx] <= FIN_MOIS); d23 = J[idx] >= "2023-01-01"
    res = {}
    G = {}
    for nom, ((pg, pi), lim) in bots.items():
        g, p, j = Pu.k_dollars_p(P["lg"], P["lb"], O, H, L, pg, pi, ok, lim, A.DOL, A.COUT, 2.0)
        G[nom] = (np.nan_to_num(g[idx]), np.nan_to_num(p[idx]), j[idx])
    g0 = G["Supertrend 10-3 (ton bot)"]; gz = G["Zone de bruit (G2 sans le frein)"]
    G["Zone + Supertrend ensemble"] = (gz[0] + g0[0], gz[1] + g0[1], gz[2] | g0[2])
    G["Supertrend a 2 MNQ"] = (2 * g0[0], 2 * g0[1], g0[2])
    for nom, (g, p, j) in G.items():
        rr = np.array([A.compte(g, p, j, i, 22) for i in range(len(idx) - 22)])
        r23 = rr[d23[:len(rr)]]
        cum = np.cumsum(g)
        res[nom] = dict(mois=round(float(g[m].sum())), seances_mois=int(m.sum()), par_an=round(float(g.mean()) * 252), par_an_2023=round(float(g[d23].mean()) * 252),
                        t=round(A.t_stat(g), 2), pire_baisse=round(float(np.min(cum - np.maximum.accumulate(cum)))),
                        retrait_22=round(float(np.mean(rr == 0)), 3), perdu_22=round(float(np.mean((rr == 1) | (rr == 2))), 3),
                        retrait_22_2023=round(float(np.mean(r23 == 0)), 3), perdu_22_2023=round(float(np.mean((r23 == 1) | (r23 == 2))), 3),
                        pire_mois=round(float(min(np.convolve(g, np.ones(26), "valid")))))
    d = ICI / "resultats" / "2026-11-20"; d.mkdir(parents=True, exist_ok=True)
    (d / "comparaison_mois.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(f"{'bot':62s} | mois | $/an 2015+ | $/an 2023+ | t | pire baisse | pire mois | 22 seances depuis 2023 : retrait / perdu")
    for nom, v in sorted(res.items(), key=lambda kv: -kv[1]["mois"]):
        print(f"{nom[:62]:62s} | {v['mois']:+7,} | {v['par_an']:+7,} | {v['par_an_2023']:+7,} | {v['t']:+.2f} | {v['pire_baisse']:+8,} | {v['pire_mois']:+7,} | "
              f"{v['retrait_22_2023']:.0%} / {v['perdu_22_2023']:.0%}")


if __name__ == "__main__":
    principal()
