"""Regle d'adoption de usine/REGLES.md (ajouts du 16 novembre 2026) : faut-il changer la largeur de bande du bot ?

Usage : KB_MINUTES=<nasdaq100_1min.csv.gz> python3 usine/adoption.py
Compare chaque candidat au reglage du bot (k = 1,0 ; 14 jours) de 2015 a la derniere seance, 1 MNQ, limite 1 000 $.
Ecrit usine/resultats/<date>/adoption.json.
"""
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import donnees as Dn  # noqa: E402
import moteur as Mo  # noqa: E402
import portes as Po  # noqa: E402

REFERENCE = {"k": 1.0, "jours": 14}
T_MIN = 1.65


def dollars(P, strat, reglage):
    pg, pi = strat["f"](P, **reglage)
    return Mo.k_dollars(P["lg"], P["lb"], P["O"], P["H"], P["L"], pg, pi, P["ok"], strat["limite"])


def principal():
    D = Dn.charger(); P = Mo.deriver(D); J = D["J"]; ok = D["complete"]
    dossier = ICI / "resultats" / dt.date.today().isoformat(); dossier.mkdir(parents=True, exist_ok=True)
    strat = Mo.STRATEGIES["zone"]
    candidats = {"A": ("zone", {"k": 1.4, "jours": 30})}
    f8 = sorted((ICI / "resultats").glob("*/zone_large.json"))
    if f8:
        r8 = json.loads(f8[-1].read_text())
        if r8["verdict"] == "passe les 5 portes":
            candidats["B"] = ("zone_large", r8["portes"]["1"]["reglage_centre"])
        else:
            print(f"Candidat B ecarte : l'idee 8 est {r8['verdict']}.")
    sel = ok & (J >= Po.WF_DEBUT); r23 = sel & (J >= "2023-01-01")
    g0, _, j0 = dollars(P, strat, REFERENCE)
    p5_0 = Po.porte5(D, P, strat, REFERENCE, J)
    v0 = p5_0["variantes"][p5_0["jouee"]]
    perdus = lambda v, cle: v[cle]["plancher"] + v[cle]["inactivite"]  # noqa: E731
    R = {"reference": dict(reglage=REFERENCE, gain_par_an=float(g0[sel].mean() * 252), seances_tradees=float(j0[sel].mean()),
                           jouee=p5_0["jouee"], neuf_250=v0["neuf_250"], marge_700_22=v0["marge_700_22"]), "candidats": {}}
    print(f"Reference {REFERENCE} : {g0[sel].mean() * 252:+,.0f} $/an, trade {j0[sel].mean():.0%} des seances ; "
          f"Master neuf 250 : retrait {v0['neuf_250']['retrait']:.1%}, perdus {perdus(v0, 'neuf_250'):.1%} ; "
          f"marge 700 sur 22 : perdus {perdus(v0, 'marge_700_22'):.1%}")
    for nom, (idee, reglage) in candidats.items():
        s = Mo.STRATEGIES[idee]
        g, _, j = dollars(P, s, reglage)
        d = g[sel] - g0[sel]; d23 = g[r23] - g0[r23]
        p5 = Po.porte5(D, P, s, reglage, J); v = p5["variantes"][p5["jouee"]]
        c1 = bool(d.mean() > 0 and Po.t_stat(d) >= T_MIN and d23.mean() > 0)
        c2 = bool(perdus(v, "neuf_250") <= perdus(v0, "neuf_250") and perdus(v, "marge_700_22") <= perdus(v0, "marge_700_22"))
        c3 = bool(v["neuf_250"]["retrait"] >= v0["neuf_250"]["retrait"])
        R["candidats"][nom] = dict(idee=idee, reglage=reglage, gain_par_an=float(g[sel].mean() * 252),
                                   seances_tradees=float(j[sel].mean()), difference_par_an=float(d.mean() * 252),
                                   t_difference=Po.t_stat(d), difference_par_an_depuis_2023=float(d23.mean() * 252),
                                   jouee=p5["jouee"], neuf_250=v["neuf_250"], marge_700_22=v["marge_700_22"],
                                   condition_1=c1, condition_2=c2, condition_3=c3, adopte=bool(c1 and c2 and c3))
        print(f"Candidat {nom} {reglage} : {g[sel].mean() * 252:+,.0f} $/an, trade {j[sel].mean():.0%} des seances ; "
              f"difference {d.mean() * 252:+,.0f} $/an (t {Po.t_stat(d):.2f}), depuis 2023 {d23.mean() * 252:+,.0f} $/an ; "
              f"Master neuf 250 : retrait {v['neuf_250']['retrait']:.1%}, perdus {perdus(v, 'neuf_250'):.1%} ; "
              f"marge 700 sur 22 : perdus {perdus(v, 'marge_700_22'):.1%} ; conditions {c1}, {c2}, {c3} => "
              f"{'ADOPTE' if c1 and c2 and c3 else 'non adopte'}")
    (dossier / "adoption.json").write_text(json.dumps(R, ensure_ascii=False, default=float))


if __name__ == "__main__":
    principal()
