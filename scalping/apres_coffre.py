#!/usr/bin/env python3
"""Descriptif APRES l'ouverture du coffre (README.md) : ce n'est pas un test et cela ne peut retenir aucune strategie.
Pour quelques marches, toutes les strategies eligibles en exploration (vraies donnees, bruit par permutation, bruit par
signe) sont jouees sur le vrai coffre : si celles choisies sur les vraies donnees ne font pas mieux que celles choisies
sur bruit, l'exploration n'a trouve aucune structure qui dure. Ecrit resultats/apres_coffre.txt."""
import numpy as np

import coffre as CO
import commun as K
import machine as MA
import moteur as M

L = ["Apres le coffre (descriptif) : strategies eligibles en exploration, jouees sur le vrai coffre 2023 - fin des donnees", "",
     "piste marche  origine       strategies   t median au coffre   t > 0   t >= 1,65   t >= 2,73"]
for piste, marche in (("D", "NQ"), ("D", "ES"), ("B", "NQ"), ("B", "ES"), ("B", "YM")):
    d = dict(np.load(MA.fichier(piste, marche, "complet")))
    f = M.indicateurs(d)
    s0 = int(np.searchsorted(d["jours"], K.DEBUT_COFFRE))
    s1 = len(d["jours"])
    for so in MA.SORTES:
        el = CO.union_eligibles(CO.lire(piste, marche, so))
        ts = []
        for x in el:
            gain, n, w, _, _ = M.jouer(np.asarray(x["genome"], float), f, s0, s1)
            ts.append(K.t_stat(gain[np.isfinite(gain)]))
        ts = np.array(ts)
        if len(ts):
            L.append(f"{piste:<5} {marche:<6}  {so:<12} {len(ts):9d}   {np.median(ts):17.2f}   {np.mean(ts > 0):5.0%}   "
                     f"{np.mean(ts >= 1.65):8.1%}   {np.mean(ts >= 2.73):8.1%}")
        else:
            L.append(f"{piste:<5} {marche:<6}  {so:<12}         0")
txt = "\n".join(L)
(MA.SORTIE / "apres_coffre.txt").write_text(txt + "\n")
print(txt)
