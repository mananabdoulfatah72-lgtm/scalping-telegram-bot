#!/usr/bin/env python3
"""Vague 12, descriptif : apres une validation en taille 4 (Legacy, sans frein en challenge), le Master en taille 1 (frein
750 $ sous le plus haut, plafond 500 $/jour). Delai jusqu'aux retraits, montants, Master perdu, gain par mois.
Achats suivis 24 mois. Ecrit master12.txt."""
import multiprocessing as mp

import numpy as np

import regles12 as K
import vague12 as V

MOIS = 21


def tache(args):
    fil, t = args
    b = V.P["bases"][fil][t]
    out = []
    for d in V.jours_achat("legacy"):
        sv = min(K.H, (V.CHOIX_SUIVI if d < V.CHOIX_FIN else V.NJ) - d)
        if sv < K.H:
            continue
        r, ret = K.un_achat(V.P, b, int(d), "legacy", 4, 0.0, 1750.0, sv, V.LIM[d])
        if r[0] != 1:
            continue
        n_ch = r[1]
        idx = np.flatnonzero(ret[:K.H] > 0)
        t_ret = [(i + 1 - n_ch) for i in idx]                 # seances apres la validation
        fin = r[6] if r[2] else K.H                           # seances depuis l'achat a la perte du Master ou fin
        out.append((d, n_ch, float(r[2] and r[6] <= K.H), fin - n_ch, len(idx),
                    t_ret[0] if len(t_ret) > 0 else np.nan, t_ret[1] if len(t_ret) > 1 else np.nan,
                    t_ret[2] if len(t_ret) > 2 else np.nan, ret[:K.H].sum(),
                    float(r[2] and r[6] - n_ch <= 252), float(r[2] and len(idx) == 0)))
    return fil, np.array(out)


def main():
    res = {}
    with mp.get_context("fork").Pool(4) as pool:
        for fil, out in pool.imap_unordered(tache, [(f, t) for f in ("fort", "moitie") for t in range(10)]):
            res.setdefault(fil, []).append(out)
    L = ["Master Bulenox en taille 1 apres une validation en taille 4 (achats Legacy suivis 24 mois). Mois de 21 seances.", ""]
    for fil, tf in (("fort", "filtre comme 2026"), ("moitie", "filtre deux fois plus faible")):
        x = np.vstack(res[fil])
        for g, (a, z) in (("achats 2012-2020", (V.D0, V.CHOIX_FIN)), ("achats 2023 - sept. 2024", (V.VERIF_DEB, V.NJ))):
            y = x[(x[:, 0] >= a) & (x[:, 0] < z)]
            m = lambda c, p=50: np.nanpercentile(y[:, c], p) / MOIS                       # noqa: E731
            L.append(f"{tf} | {g} : {len(y)} validations")
            L.append(f"  Master perdu avant tout retrait : {np.mean(y[:, 10]):.0%} ; perdu dans les 12 mois : {np.mean(y[:, 9]):.0%}"
                     f" ; perdu avant la fin des 24 mois (apres 0 a 3 retraits) : {np.mean(y[:, 2] * (y[:, 4] < 3)):.0%}")
            L.append(f"  1er retrait : {np.mean(~np.isnan(y[:, 5])):.0%} des Masters, {m(5):.1f} mois apres la validation en"
                     f" mediane (1 sur 4 apres {m(5, 75):.1f} mois)")
            L.append(f"  2e retrait : {m(6):.1f} mois ; 3e retrait : {m(7):.1f} mois apres la validation (medianes) ;"
                     f" 3 retraits atteints : {np.mean(y[:, 4] >= 3):.0%}")
            vivant = y[:, 3] / MOIS
            L.append(f"  argent recu par Master : moyenne {y[:, 8].mean():,.0f} $ ; par mois de Master entre la validation"
                     f" et le 3e retrait (ou la perte) : {np.sum(y[:, 8]) / np.sum(np.where(np.isnan(y[:, 7]), vivant, y[:, 7] / MOIS)):,.0f} $")
            L.append("")
    (K.ICI / "master12.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
