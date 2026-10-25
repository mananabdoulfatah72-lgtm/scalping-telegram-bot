#!/usr/bin/env python3
"""Descriptif (README.md, version 5) : le panier des strategies eligibles de la version 4, joue sur le coffre 2023 - fin
des donnees deja ouvert. Panier = moyenne des gains quotidiens de toutes les eligibles d'un couple piste-marche (chacune
pour 1/N contrat, ses frais comptes). Pas un test : le coffre est connu. Ecrit resultats/ensemble_v4.txt."""
import numpy as np

import coffre as CO
import commun as K
import machine as MA
import moteur as M

L = ["Panier des eligibles de la version 4 (descriptif, coffre deja ouvert) : t en exploration (2017 - 2022) et au coffre",
     ""]
for piste, marche in (("B", "NQ"), ("D", "NQ"), ("B", "ES"), ("B", "YM"), ("D", "ES")):
    d = dict(np.load(MA.fichier(piste, marche, "complet")))
    f = M.indicateurs(d)
    s0c = int(np.searchsorted(d["jours"], K.DEBUT_COFFRE))
    s1 = len(d["jours"])
    s0e = int(np.searchsorted(d["jours"], K.DEBUT_ENTRAINEMENT))
    for so in MA.SORTES:
        el = CO.union_eligibles(CO.lire(piste, marche, so))
        if not el:
            continue
        G, E = [], []
        for x in el:
            g = np.asarray(x["genome"], float)
            G.append(np.nan_to_num(M.jouer(g, f, s0c, s1)[0]))
            E.append(np.nan_to_num(M.jouer(g, f, s0e, s0c)[0]))
        G, E = np.array(G), np.array(E)
        ens, ense = G.mean(0), E.mean(0)
        ans = d["jours"][s0c:s1].astype("datetime64[Y]")
        par_an = {str(a)[:4]: ens[ans == a].sum() for a in np.unique(ans)}
        c = np.corrcoef(G)[np.triu_indices(len(G), 1)] if len(G) > 1 else np.array([1.0])
        L.append(f"{piste} {marche} {so:<6} n={len(el):5d} ensemble exploration t {K.t_stat(ense):6.2f} | coffre t "
                 f"{K.t_stat(ens):6.2f} moyenne {ens.mean():+.2f} $/seance ; corr moyenne entre strategies {np.nanmean(c):.2f} ; "
                 + " ".join(f"{a}:{v:+.0f}" for a, v in par_an.items()))
        print(L[-1], flush=True)
(MA.SORTIE / "ensemble_v4.txt").write_text("\n".join(L) + "\n")
