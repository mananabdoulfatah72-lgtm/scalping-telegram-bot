#!/usr/bin/env python3
"""Optimisation glissante de la zone de bruit (README.md, parties 1 et 2).
Lancer depuis ce dossier : python3 glissante.py"""
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import moteur as M

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tournoi"))
from explorer import charger, t_stat  # noqa: E402

ICI = Path(__file__).resolve().parent
GRILLE = list(itertools.product((0.75, 1.0, 1.25, 1.5), (7, 14, 28), (15, 30, 60), tuple(M.STOPS)))
V1 = (1.0, 14, 30, "limite ou VWAP")
COUT, PT = 1.5, 2.0


def nom(g):
    return f"k {g[0]:g}, {g[1]} j, {g[2]} min, stop {g[3]}"


def main():
    J, O, H, L, C, P, X = charger("nasdaq100", fin=None)
    ok = M.Z.st.journees_completes(P) & ~X["echeance"]
    an = pd.DatetimeIndex(J).year.values
    z = M.Zone(J, O, H, L, C, P, X)
    R, D = {}, {}
    for g in GRILLE:
        b, a = z.jouer(*g)
        R[g] = np.where(ok, (b - COUT * a) / O[:, 0], 0.0)
        D[g] = np.where(ok, (b - COUT * a) * PT, 0.0)
    t_sur = lambda r, m: t_stat(r[m])
    sortie = []
    ecrire = lambda s="": (print(s, flush=True), sortie.append(s))
    hors = {v: np.zeros(len(J)) for v in ("G1", "G2", "G3")}
    hors_d = {v: np.zeros(len(J)) for v in ("G1", "G2", "G3")}
    ecrire("Choix de chaque 1er janvier (selon les seules annees passees) :")
    for y in range(2014, 2027):
        jeu = ok & (an == y)
        for v, debut in (("G1", 2011), ("G2", y - 4), ("G3", 2011)):
            app = ok & (an >= debut) & (an < y)
            classement = sorted(GRILLE, key=lambda g: t_sur(R[g], app), reverse=True)
            choix = classement[:10] if v == "G3" else classement[:1]
            hors[v][jeu] = np.mean([R[g][jeu] for g in choix], axis=0)
            hors_d[v][jeu] = np.mean([D[g][jeu] for g in choix], axis=0)
            if v != "G3":
                ecrire(f"  {y} {v} : {nom(choix[0])} (t passe {t_sur(R[choix[0]], app):+.2f})")
            else:
                ecrire(f"  {y} G3 : 10 reglages, dont {nom(choix[0])} en tete")
    per = {"2014-2022": ok & (an >= 2014) & (an <= 2022), "2023-2026": ok & (an >= 2023), "2014-2026": ok & (an >= 2014)}
    ecrire("\nResultats HORS ECHANTILLON (t des rendements quotidiens nets, frais reels) :")
    ecrire("  " + " | ".join(f"{'':22s}" if i == 0 else "" for i in range(1)) + " | ".join(f"{p:>10s}" for p in per) + " | 2023-2026, 1 MNQ")
    lignes = {"V1 (reglage d'origine corrige)": (R[V1], D[V1]), **{v: (hors[v], hors_d[v]) for v in hors}}
    for n_, (r, d) in lignes.items():
        ecrire(f"  {n_:32s} | " + " | ".join(f"{t_sur(r, m):+10.2f}" for m in per.values()) + f" | {d[per['2023-2026']].sum():+,.0f} $")
    ecrire("\nCritere d'adoption (README.md) :")
    adoptee = None
    for v in hors:
        e1 = t_sur(hors[v], per["2014-2022"]) > t_sur(R[V1], per["2014-2022"])
        e2 = t_sur(hors[v], per["2023-2026"]) > t_sur(R[V1], per["2023-2026"])
        diff = t_sur(hors[v] - R[V1], per["2014-2026"])
        passe = e1 and e2 and diff >= 1.65
        ecrire(f"  {v} : mieux que V1 sur 2014-2022 {'OUI' if e1 else 'non'} | sur 2023-2026 {'OUI' if e2 else 'non'} |"
               f" t de la difference {diff:+.2f} {'OUI' if diff >= 1.65 else 'non'} => {'ADOPTEE' if passe else 'rejetee'}")
        if passe and adoptee is None:
            adoptee = v
    ecrire(f"\nVerdict : {adoptee + ' remplace V1' if adoptee else 'V1 reste (aucune optimisation ne fait mieux hors echantillon)'}")
    oracle = max(GRILLE, key=lambda g: t_sur(R[g], per["2023-2026"]))
    ecrire(f"\nPour information, l'ORACLE (reglage choisi APRES avoir vu 2023-2026) : {nom(oracle)}"
           f" -> t 2023-2026 {t_sur(R[oracle], per['2023-2026']):+.2f} ; mais t 2014-2022 {t_sur(R[oracle], per['2014-2022']):+.2f}")
    rang_v1 = sorted(GRILLE, key=lambda g: t_sur(R[g], per["2023-2026"]), reverse=True).index(V1) + 1
    ecrire(f"V1 est {rang_v1}e sur {len(GRILLE)} reglages sur 2023-2026 ; mediane des 108 reglages : t {np.median([t_sur(R[g], per['2023-2026']) for g in GRILLE]):+.2f}")
    ecrire("\nRobustesse : t 2023-2026 selon chaque reglage, les autres a la valeur d'origine")
    for i, nomr in enumerate(("largeur k", "jours", "intervalle", "stop")):
        vals = sorted({g[i] for g in GRILLE}, key=str)
        ecrire(f"  {nomr:10s} : " + " | ".join(f"{v}: {t_sur(R[tuple(v if j == i else V1[j] for j in range(4))], per['2023-2026']):+.2f}"
                                                for v in vals))
    (ICI / "glissante.txt").write_text("\n".join(sortie) + "\n")


if __name__ == "__main__":
    main()
