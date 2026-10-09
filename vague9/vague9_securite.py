#!/usr/bin/env python3
"""Vague 9, second jugement (README.md) : la regle qui perd le moins de comptes sur le choix parmi celles dont le gain
median sur 12 mois reste >= 6 000 $, controlee par le jumeau de bruit et par des filtres au hasard. Ecrit
vague9_securite.txt."""
import sys
import time
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import vague9 as V9  # noqa: E402

G = V9.G


def choisir(res):
    ok = [r for r in res if r[3]["choix"][2] >= V9.CIBLE]
    return min(ok, key=lambda r: (r[3]["choix"][1], -r[3]["choix"][0])) if ok else None


def main():
    t0 = time.time()
    V9.preparer()
    R = V9.regles()
    base = V9.mesurer_masques([np.ones(len(G["T"]["d"]), bool)] * len(G["gardes"]), False)
    best = choisir(V9.lancer(R, "M"))
    pj = []
    for s in range(V9.JUMEAUX):
        G["MJ"] = V9.jumeau(1000 + s)
        b = choisir(V9.lancer(R, "MJ"))
        pj.append(b[3]["choix"][1] if b else 1.0)
        print(f"jumeau {s + 1} : {pj[-1]:.1%} ({time.time() - t0:.0f} s)", flush=True)
    battus = sum(best[3]["choix"][1] < p for p in pj)
    c, mes, part, r = best
    rng = np.random.default_rng(11)
    nt = len(G["T"]["d"])
    pl = []
    for _ in range(V9.PLACEBOS):
        ch = []
        for i in range(len(G["gardes"])):
            k = int(np.logical_and.reduce(G["M"][i][list(c)]).sum())
            m = np.zeros(nt, bool)
            m[rng.choice(nt, k, replace=False)] = True
            ch.append(m)
        pl.append(V9.mesurer_masques(ch, mes)["verification"][1])
    v = r["verification"]
    pct = float(np.mean(np.array(pl) > v[1]))
    ok1, ok2, ok3 = battus >= 9, v[1] < base["verification"][1] and v[2] >= V9.CIBLE, pct >= 0.90
    f = lambda x: f"objectif tenu {x[0]:.0%}, perdu {x[1]:.0%}, gain median {x[2]:+,.0f} $"     # noqa: E731
    L = ["Vague 9, second jugement : perdre le moins de comptes (gain median sur 12 mois >= 6 000 $ sur le choix)", "",
         "Bot de depart : " + " | ".join(f"{k} : {f(x)}" for k, x in base.items()),
         f"Regle choisie : {V9.nom_regle(c, mes)} (trades gardes {part:.0%})",
         "  " + " | ".join(f"{k} : {f(x)}" for k, x in r.items()),
         f"1. Jumeau de bruit : perdu {r['choix'][1]:.1%} sur le choix ; meilleures des 10 recherches melangees :"
         f" {', '.join(f'{p:.1%}' for p in pj)} -> battue(s) {battus}/10 ({'oui' if ok1 else 'non'}, il faut 9)",
         f"2. Verification : {f(v)} contre {f(base['verification'])} ({'oui' if ok2 else 'non'})",
         f"3. Filtres au hasard : la regle perd moins de comptes que {pct:.0%} d'entre eux ({'oui' if ok3 else 'non'},"
         f" il faut 90 %)",
         f"=> {'RETENUE : a recalculer avec le moteur exact' if ok1 and ok2 and ok3 else 'NON RETENUE'}"]
    (ICI / "vague9_securite.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
