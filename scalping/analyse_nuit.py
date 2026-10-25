#!/usr/bin/env python3
"""Descriptif (README.md, partie D) : les finalistes de nuit ne font-elles qu'acheter la derive de nuit ? Sur
l'exploration seulement (2013-2022) : gains des achats et des ventes, part des achats, correlation quotidienne avec un
achat simple de 18 h a 9 h 20, et t de cet achat simple. Ecrit resultats/analyse_nuit.txt."""
import json

import numpy as np

import commun as K
import machine as MA
import moteur as M


def main():
    sel = json.loads((MA.SORTIE / "finalistes.json").read_text())
    L = ["Finalistes de nuit (partie D) : d'ou vient le gain, exploration 2013-2022 seulement", ""]
    for x in sel["finalistes"]:
        if x["partie"] != "D":
            continue
        d = dict(np.load(MA.fichier("D", x["marche"])))
        f = M.indicateurs(d)
        s0, _, s1 = MA.bornes(d["jours"], "D")
        gain, n, w, brut, j = M.jouer(np.asarray(x["genome"], float), f, s0, s1, journal=200000)
        pts = j[:, 3] * (j[:, 5] - j[:, 4]) * f["pt"] * f["echelle"][j[:, 0].astype(int)] - f["frais"]
        achat = j[:, 3] > 0
        # achat simple de la nuit : ouverture de 18 h -> cloture de 9 h 15, 1 contrat, frais compris
        simple = (f["C"][:, -1] - f["O"][:, 0]) * f["pt"] * f["echelle"] - f["frais"]
        jou = np.flatnonzero(f["jouable"][s0:s1]) + s0
        g = gain[jou - s0]
        sp = simple[jou]
        c = np.corrcoef(g, sp)[0, 1] if g.std() > 0 else float("nan")
        dur = j[:, 2] - j[:, 1] + 1
        L.append(f"{x['marche']} score {x['score']:.2f} : {n} trades, achats {achat.mean():.0%} ; gain des achats "
                 f"{pts[achat].sum():+,.0f} $ ({pts[achat].mean() if achat.any() else 0:+.2f} $ par trade), des ventes "
                 f"{pts[~achat].sum():+,.0f} $ ({pts[~achat].mean() if (~achat).any() else 0:+.2f} $ par trade) ; duree "
                 f"mediane {np.median(dur) * 5:.0f} min")
        L.append(f"      correlation quotidienne avec l'achat simple de la nuit {c:+.2f} ; achat simple : t "
                 f"{K.t_stat(sp):.2f}, {sp.sum():+,.0f} $ sur la periode")
        L.append(f"      {x['description']}")
    txt = "\n".join(L)
    (MA.SORTIE / "analyse_nuit.txt").write_text(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
