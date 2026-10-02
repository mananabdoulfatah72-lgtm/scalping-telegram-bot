#!/usr/bin/env python3
"""Coffre de l'order flow NQ (README.md), ouvert une seule fois : dernier tiers des seances.
- Survivants des hypotheses H2 a H5 (survivants_of.json) : t sur les trades >= seuil de Bonferroni et gain net positif.
- Finalistes de la machine (finalistes_of.json) : t du gain net par seance >= seuil de Bonferroni et gain net positif.
- H1, filtre order flow de la zone de bruit (ajout du README avant ouverture) : ecart garde - ecarte > 0 avec t >= 1,65.
Les niveaux de la veille et les references des 5 seances d'avant sont calcules sur toutes les seances (ils ne regardent
que le passe). Ecrit coffre_of.txt et coffre_of.json. Lancer depuis ce dossier : ROBOT_ZONE=/chemin/zone/robot.py ROBOT_MINUTES=/chemin/nq_1min.csv.gz python3 coffre_of.py"""
import json
import warnings
from pathlib import Path
from statistics import NormalDist

import numpy as np

import moteur_of as M
import outils as O
import precalcul as P
import signaux as G
from explorer import NOMS, decoupe, detecter, juger_h1, zone

warnings.filterwarnings("ignore", category=RuntimeWarning)
ICI = Path(__file__).resolve().parent
SORTIES = ICI / "coffre_of.json", ICI / "coffre_of.txt"


def bonferroni(m):
    return NormalDist().inv_cdf(1 - 0.05 / m) if m else float("nan")


def main():
    assert not any(p.exists() for p in SORTIES), "le coffre a deja ete ouvert"
    surv = json.loads((ICI / "survivants_of.json").read_text())
    fin = json.loads((ICI / "finalistes_of.json").read_text())
    S = O.Seances()
    n = len(S.jours)
    k = decoupe(n)
    assert k == surv["seances_exploration"] == fin["seances_exploration"], "le decoupage a change"
    coffre = list(range(k, n))
    gros = G.lire_gros(S, O.D)
    L = [f"Coffre order flow NQ : {n - k} seances du {S.jours[k].date()} au {S.jours[-1].date()}, ouvert une fois.", ""]
    res = {"hypotheses": {}, "finalistes": []}
    hs = surv["survivants"]
    seuil = bonferroni(len(hs))
    L.append(f"Hypotheses survivantes de l'exploration : {', '.join(hs) if hs else 'aucune'}"
             + (f" ; seuil de Bonferroni {seuil:.2f}" if hs else ""))
    if hs:
        tous = detecter(S, gros, coffre)
        for h in hs:
            x = O.executer(S, tous[h])
            t = O.t_stat(x["net"]) if len(x) else 0.0
            net = float(x["net"].mean()) if len(x) else 0.0
            ok = len(x) > 0 and net > 0 and t >= seuil
            res["hypotheses"][h] = {"trades": int(len(x)), "net_pts": round(net, 3), "t": round(t, 3), "passe": bool(ok)}
            L.append(f"- {h} {NOMS[h]} : {len(x)} trades, {net:+.2f} pt net par trade ({2 * net:+.2f} $ par MNQ), t {t:+.2f}"
                     f" -> {'PASSE' if ok else 'echoue'}")
    fs = fin["finalistes"]
    seuil = bonferroni(len(fs))
    L += ["", f"Finalistes de la machine : {len(fs)}" + (f" ; seuil de Bonferroni {seuil:.2f} (t par seance)" if fs else "")]
    if fs:
        B = P.Briques(S, O.lire_footprint(O.D), gros)
        for f in fs:
            g = f["g"]
            g = {**g, "W": int(g["W"]), "seuil": float(g["seuil"])}
            sig = M.signal(B, g)[k:]
            total, ntr = M.simuler(np.ascontiguousarray(sig), np.ascontiguousarray(B.bid[k:]), np.ascontiguousarray(B.ask[k:]),
                                   g["sortie"], g["stop"], 0, np.zeros(sig.shape, np.int8))
            _, t = M.fitness(total, ntr)
            net = float(total.sum() / ntr) if ntr else 0.0
            ok = ntr > 0 and net > 0 and t >= seuil
            res["finalistes"].append({"description": f["description"], "trades": int(ntr), "net_pts": round(net, 3),
                                      "t_seances": round(t, 3), "total_pts": round(float(total.sum()), 2), "passe": bool(ok)})
            L.append(f"- {f['description']}\n  {ntr} trades, {net:+.2f} pt net par trade ({2 * net:+.2f} $ par MNQ),"
                     f" total {total.sum():+.1f} pt, t par seance {t:+.2f} -> {'PASSE' if ok else 'echoue'}")
    f1 = zone(S, coffre)
    r1 = juger_h1(f1)
    r1["passe"] = bool(r1.get("trades", 0) > 0 and (r1.get("difference") or 0) > 0 and (r1.get("t_difference") or 0) >= 1.65)
    res["H1"] = r1
    L += ["", "H1, filtre order flow de la zone de bruit (confirmation : ecart > 0 et t >= 1,65) :"]
    if r1.get("trades"):
        L.append(f"  {r1['trades']} trades de zone ; delta des 30 min dans le sens du trade : {r1['gardes']} trades, {r1['points_gardes']:+.2f} pt"
                 f" ; contre : {r1['ecartes']} trades, {r1['points_ecartes'] if r1['points_ecartes'] is not None else float('nan'):+.2f} pt"
                 f" ; tous : {r1['points_tous']:+.2f} pt. Ecart {r1['difference']:+.2f} pt, t {r1['t_difference']}"
                 f" -> {'CONFIRME' if r1['passe'] else 'non confirme'}")
    else:
        L.append("  aucun trade de zone")
    gagnants = (["H1"] if r1["passe"] else []) + [h for h, r in res["hypotheses"].items() if r["passe"]] + [f["description"] for f in res["finalistes"] if f["passe"]]
    L += ["", f"Passent le coffre : {len(gagnants)}"]
    SORTIES[0].write_text(json.dumps(res, indent=1, ensure_ascii=False))
    SORTIES[1].write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
