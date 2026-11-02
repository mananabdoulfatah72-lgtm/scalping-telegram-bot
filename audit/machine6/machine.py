#!/usr/bin/env python3
"""Machine v6 : vagues (algorithme genetique), tournoi sur 2020 - 2023, controles. Le coffre est ouvert par coffre.py.
Regles : audit/machine6/REGLES.md (fixees le 2 novembre 2026 avant tout calcul)."""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import base as B
import sim

GENES = [  # nom, valeurs (dans l'ordre des pas), index de la valeur de base, famille
    ("T", [1, 2, 3, 4, 5, 6], 3, "g"), ("L", [300, 400, 500, 600, 700, 800, 900, 1000], 7, "g"),
    ("G", [0, 150, 300], 0, "g"), ("S", [0, 0.5, 1, 1.5], 0, "g"), ("P", [0, 1, 2, 3], 0, "g"),
    ("B", [0, 1, 2], 0, "g"), ("R", [0, 1, 2], 0, "g"), ("N", [1, 2, 0], 2, "g"), ("J", [0, 1], 0, "g"),
    ("O", [0, 500, 750, 1000, 1500], 0, "g"), ("GC", [0, 200, 350, 500], 0, "c"),
    ("F1", [0, 0.1, 0.25], 0, "f"), ("F2", [99, 1.5, 1.0], 0, "f"), ("F3", [360, 330, 270, 210], 0, "f"),
    ("F4", [30, 60], 0, "f"), ("F5", [0, 1, 2], 0, "f"), ("F6", [0, 1, 2], 0, "f")]
NG = len(GENES)
BASE = tuple(g[2] for g in GENES)
D = B.D
SIGH = np.where(np.isnan(D["med"]), True, D["sig_jour"] > D["med"])
SIGB = np.where(np.isnan(D["med"]), True, D["sig_jour"] < D["med"])
td = D["t_jour"]
PER = {"ent": B.debuts(2011, 2019), "tou": B.debuts(2020, 2023), "cof": B.debuts(2024, 2026)}


def valeurs(g):
    return {GENES[i][0]: GENES[i][1][g[i]] for i in range(NG)}


def parametres(g, pess=0, gl=0.0):
    v = valeurs(g)
    p = B.prm(T=v["T"], L=v["L"], G=v["G"], S=v["S"], P=v["P"], B=v["B"], R=v["R"], N=v["N"], Jr=v["J"], O=v["O"],
              pess=pess, gl=gl, GC=v["GC"])
    pris = (D["t_dep"] >= v["F1"]) & (D["t_dep"] <= v["F2"]) & (D["t_me"] <= v["F3"]) & (D["t_me"] >= v["F4"])
    if v["F5"] == 1:
        pris &= SIGH[td]
    elif v["F5"] == 2:
        pris &= SIGB[td]
    if v["F6"] == 1:
        pris &= D["gap"][td] < 1
    elif v["F6"] == 2:
        pris &= D["gap"][td] >= 0.5
    return p, pris


def score(g, per, pess=0, gl=0.0):
    p, pris = parametres(g, pess, gl)
    r, e, x, n, bl = B.issues(p, PER[per], pris)
    return r - 0.5 * e, r, e, bl


def complexite(g):
    return sum(1 for i in range(NG) if g[i] != BASE[i])


def vague(arg):
    famille, graine = arg
    rng = np.random.default_rng(1000 * graine + {"g": 1, "f": 2, "t": 3, "t2": 4}[famille])
    libres = [i for i in range(NG) if (famille == "t" and GENES[i][3] != "c") or famille == "t2" or GENES[i][3] == famille]
    cache = {}

    def note(g):
        if g not in cache:
            cache[g] = score(g, "ent")[0] - 0.5 * complexite(g)
        return cache[g]

    def hasard():
        g = list(BASE)
        for i in libres:
            g[i] = int(rng.integers(len(GENES[i][1])))
        return tuple(g)

    def muter(g):
        g = list(g)
        for _ in range(1 + int(rng.random() < 0.3)):
            i = libres[int(rng.integers(len(libres)))]
            g[i] = int(np.clip(g[i] + (1 if rng.random() < 0.5 else -1), 0, len(GENES[i][1]) - 1))
        return tuple(g)

    pop = [BASE] + [hasard() for _ in range(119)]
    for gen in range(40):
        notes = [note(g) for g in pop]
        ordre = np.argsort(notes)[::-1]
        nouv = [pop[ordre[0]], pop[ordre[1]]]
        while len(nouv) < 120:
            def choisir():
                c = rng.integers(len(pop), size=3)
                return pop[c[np.argmax([notes[k] for k in c])]]
            a, b = choisir(), choisir()
            enf = tuple(a[i] if rng.random() < 0.5 else b[i] for i in range(NG))
            nouv.append(muter(enf))
        pop = nouv
    return famille, graine, cache


def main():
    out = Path(__file__).parent / "resultats"
    out.mkdir(exist_ok=True)
    taches = [(f, s) for f in ("g", "f", "t", "t2") for s in range(6)]
    with Pool(4) as pool:
        res = pool.map(vague, taches)
    tous = {}
    lignes = []
    for famille, graine, cache in res:
        meilleur = max(cache, key=cache.get)
        lignes.append(f"vague {famille} graine {graine} : {len(cache)} genomes, meilleur {cache[meilleur]:+.2f} {valeurs(meilleur)}")
        for g, v in cache.items():
            tous[g] = v
    lignes.append(f"\ngenomes distincts evalues (toutes vagues) : {len(tous)}")
    top = sorted(tous, key=tous.get, reverse=True)[:32]
    # tournoi : elimination directe sur 2020 - 2023, tete de serie 1 contre 32, 2 contre 31...
    sc = {g: score(g, "tou")[0] for g in top}
    tour = top
    lignes.append("\nTournoi (2020 - 2023), score = P(reussite) - 0,5 x P(echec) :")
    while len(tour) > 4:
        suiv = []
        for i in range(len(tour) // 2):
            a, b = tour[i], tour[-1 - i]
            gagnant = a if (sc[a], -complexite(a)) >= (sc[b], -complexite(b)) else b
            suiv.append(gagnant)
        tour = suiv
        lignes.append(f"  tour de {len(suiv) * 2} -> {len(suiv)} : " + ", ".join(f"{sc[g]:+.1f}" for g in suiv))
    temoins = {"a 4 MNQ / 1000": (3, 7), "b 6 MNQ / 1000": (5, 7), "c 2 MNQ / 500": (1, 2)}
    tem = {}
    for nom, (ti, li) in temoins.items():
        g = list(BASE); g[0], g[1] = ti, li; g = tuple(g)
        tem[nom] = g
    meilleur_tem_tou = max(score(g, "tou")[0] for g in tem.values())
    finalistes = []
    for g in tour:
        s_ent, r_ent, e_ent, bl_ent = score(g, "ent")
        s_tou, r_tou, e_tou, bl_tou = score(g, "tou")
        c1 = s_tou > meilleur_tem_tou
        voisins, voisins2 = [], []
        for i in range(NG):
            ordre = [1, 2, 3, 4, 0] if GENES[i][0] == "O" else list(range(len(GENES[i][1])))
            pos = ordre.index(g[i])
            for dlt in (-1, 1):
                j = g[i] + dlt
                if 0 <= j < len(GENES[i][1]):
                    v = list(g); v[i] = j; v = tuple(v)
                    voisins.append((GENES[i][0], GENES[i][1][j], score(v, "ent")[0] + score(v, "tou")[0]))
                if 0 <= pos + dlt < len(ordre):
                    j2 = ordre[pos + dlt]
                    v = list(g); v[i] = j2; v = tuple(v)
                    voisins2.append((GENES[i][0], GENES[i][1][j2], score(v, "ent")[0] + score(v, "tou")[0]))
        ref = s_ent + s_tou
        pire_v = min(voisins, key=lambda z: z[2])
        pire_v2 = min(voisins2, key=lambda z: z[2])
        c2 = pire_v2[2] >= ref - 0.1 * abs(ref)
        c2_ecrit = pire_v[2] >= ref - 0.1 * abs(ref)
        s_st = score(g, "tou", pess=1, gl=0.25)[0]
        c3 = s_st > meilleur_tem_tou
        p, pris = parametres(g)
        j = sim.journees(p, *B.ARGS, pris, B.nj)
        j = j[np.arange(B.nj) >= B.premier]
        t = j.mean() / j.std(ddof=1) * np.sqrt(len(j))
        c4 = t >= 3
        finalistes.append(dict(genome=list(g), valeurs=valeurs(g), complexite=complexite(g), ent=[s_ent, r_ent, e_ent],
                               tou=[s_tou, r_tou, e_tou], stress_tou=s_st, pire_voisin=pire_v, pire_voisin_corrige=pire_v2, controle2_ecrit=bool(c2_ecrit), bloques_tou=bl_tou, t_15ans=t,
                               controles=[bool(c1), bool(c2), bool(c3), bool(c4)]))
        lignes.append(f"\nFINALISTE {valeurs(g)}\n  entrainement : score {s_ent:+.1f} (reussis {r_ent:.1f} %, echoues {e_ent:.1f} %)"
                      f"\n  tournoi      : score {s_tou:+.1f} (reussis {r_tou:.1f} %, echoues {e_tou:.1f} %)"
                      f"\n  1. bat le meilleur temoin sur 2020 - 2023 ({meilleur_tem_tou:+.1f}) : {c1}"
                      f"\n  2. pire voisin (lecture corrigee) {pire_v2[0]}={pire_v2[1]} : {pire_v2[2]:+.1f} contre {ref:+.1f} : {c2}"
                      f" ; lecture ecrite {pire_v[0]}={pire_v[1]} : {pire_v[2]:+.1f} : {c2_ecrit}"
                      f"\n     comptes en vie bloques pres du plancher (tournoi) : {bl_tou:.0f} %"
                      f"\n  3. pessimiste + 1 tick : {s_st:+.1f} : {c3}\n  4. t des journees 15 ans : {t:.2f} : {c4}")
    for nom, g in tem.items():
        s1, r1, e1, _ = score(g, "ent"); s2, r2, e2, _ = score(g, "tou")
        lignes.append(f"\ntemoin {nom} : entrainement {s1:+.1f} ({r1:.1f} % / {e1:.1f} %), tournoi {s2:+.1f} ({r2:.1f} % / {e2:.1f} %)")
    (out / "vagues_tournoi.txt").write_text("\n".join(lignes) + "\n")
    json.dump(dict(finalistes=finalistes, temoins={k: list(v) for k, v in tem.items()}, n_genomes=len(tous),
                   top32=[list(g) for g in top]), open(out / "finalistes.json", "w"), indent=1, default=float)
    print("\n".join(lignes))


if __name__ == "__main__":
    main()
