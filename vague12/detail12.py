#!/usr/bin/env python3
"""Vague 12, descriptif : ce que devient UN achat de la version retenue (Bulenox Legacy, taille 4 sans frein en
challenge, puis taille 1 avec frein et plafond 500 $ au Master), compare au bot tel quel. Achats suivis 24 mois
seulement. Ecrit detail12.txt."""
import multiprocessing as mp

import numpy as np

import regles12 as K
import vague12 as V

CAS = [("taille 4 sans frein (version 30 jours)", 4, 0.0), ("taille 1 frein (bot tel quel)", 1, 1750.0)]


def tache(args):
    q, c_ch, fil, t = args
    b = V.P["bases"][fil][t]
    out = []
    for d in V.jours_achat("legacy"):
        lim_suivi = V.CHOIX_SUIVI if d < V.CHOIX_FIN else V.NJ
        sv = min(K.H, lim_suivi - d)
        if sv < K.H:
            continue
        r, ret = K.un_achat(V.P, b, int(d), "legacy", q, c_ch, 1750.0, sv, V.LIM[d])
        out.append((d, r[0], r[3], ret[:K.H].sum() - 19.25 - (148.0 if r[0] == 1 else 0.0)))
    return q, fil, np.array(out)


def main():
    taches = [(q, c, fil, t) for _, q, c in CAS for fil, n in (("fort", 10), ("moitie", 10)) for t in range(n)]
    res = {}
    with mp.get_context("fork").Pool(4) as pool:
        for q, fil, out in pool.imap_unordered(tache, taches):
            res.setdefault((q, fil), []).append(out)
    L = ["Un achat Bulenox Legacy 50K (19,25 $ + 148 $ a la reussite), suivi 24 mois. Part des achats :", ""]
    for nom, q, _ in CAS:
        for fil, tf in (("fort", "filtre comme 2026"), ("moitie", "filtre deux fois plus faible")):
            x = np.vstack(res[(q, fil)])
            for g, (a, z) in (("achats 2012-2020", (V.D0, V.CHOIX_FIN)), ("achats 2023 - sept. 2024", (V.VERIF_DEB, V.NJ))):
                y = x[(x[:, 0] >= a) & (x[:, 0] < z)]
                iss, n, net = y[:, 1], y[:, 2], y[:, 3]
                L.append(f"{nom} | {tf} | {g} ({len(y)} achats x tirages)")
                L.append(f"  challenge rate (perdu ou expire, -19 $) : {np.mean(iss != 1):.0%}")
                L.append(f"  valide puis Master perdu avant tout retrait (-167 $) : {np.mean((iss == 1) & (n == 0)):.0%}")
                for k in (1, 2, 3):
                    L.append(f"  {k} retrait(s) : {np.mean((iss == 1) & (n == k)):.0%}")
                L.append(f"  net : moyenne {net.mean():+,.0f} $, 3 achats sur 4 sous {np.percentile(net, 75):+,.0f} $,"
                         f" 1 sur 10 au-dessus de {np.percentile(net, 90):+,.0f} $")
                L.append(f"  deux achats de suite (le 2e le mois suivant si le 1er rate) : au moins une validation"
                         f" {deux(y, x):.0%}")
                L.append("")
    (K.ICI / "detail12.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


def deux(y, x):
    """Approximation : chance de valider au 1er achat ou au 2e, fait 22 seances plus tard, en multipliant les chances
    d'echec de ces deux jours d'achat (moyennes sur les tirages du filtre)."""
    par_jour = {}
    for d, v in zip(x[:, 0].astype(int), x[:, 1] == 1):
        par_jour.setdefault(d, []).append(v)
    p = {d: np.mean(v) for d, v in par_jour.items()}
    jours = sorted(set(y[:, 0].astype(int)))
    vals = [1 - (1 - p[d]) * (1 - p[d + 22]) for d in jours if d + 22 in p]
    return float(np.mean(vals)) if vals else float("nan")


if __name__ == "__main__":
    main()
