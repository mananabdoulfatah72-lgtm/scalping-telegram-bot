#!/usr/bin/env python3
"""Partie 1 (README.md) : RSI(2) entre deux clotures contre l'original, 1 MNQ. Ecrit rsi2_entre_deux.txt.
Lancer depuis ce dossier : python3 rsi2_jour.py"""
import numpy as np
import pandas as pd

import commun as K

COFFRE = "2023-01-01"


def main():
    D = K.charger()
    R = K.rsi2_entre_deux(D)
    j = R.index
    debut = j[np.argmax(D["voulu"] == 1)]
    m = j >= debut
    L = [f"RSI(2) entre deux clotures, NQ 1 MNQ, du {debut.date()} au {j[-1].date()}", "",
         f"controle des donnees : seances {len(j)} ; nuits avec barres {int((D['nn'] > 0).sum())} ;"
         f" dont premiere barre a 18 h : {int(D['n18'].sum())}"]
    tenus = R["tenu_v"] == 1
    sans_nuit = tenus & (D["nn"] == 0)
    L.append(f"jours tenus par la variante : {int(tenus[m].sum())} ; dont sans barre de nuit (achat a 9 h 30) :"
             f" {int(sans_nuit[m].sum())}")
    res = {}
    for nom, mm in (("toute la periode", m), ("2023 - sept. 2026", j >= COFFRE), ("2011-2022", m & (j < COFFRE))):
        a, b = R.loc[mm, "gain_o"].sum(), R.loc[mm, "gain_v"].sum()
        ta, tb = K.t_stat(R.loc[mm, "rend_o"]), K.t_stat(R.loc[mm, "rend_v"])
        res[nom] = (ta, tb, a, b)
        L.append(f"{nom} : original t {ta:+.2f}, {a:+,.0f} $ ; entre deux clotures t {tb:+.2f}, {b:+,.0f} $"
                 f" ({b / a:.0%} de l'original) ; t des $ quotidiens : {K.t_stat(R.loc[mm, 'gain_o']):+.2f} /"
                 f" {K.t_stat(R.loc[mm, 'gain_v']):+.2f}")
    ta, tb, a, b = res["toute la periode"]
    rec = res["2023 - sept. 2026"][3]
    c1, c2, c3 = tb >= 2, b >= 0.5 * a, rec > 0
    ok = c1 and c2 and c3
    L += ["", f"-> {'UTILISABLE' if ok else 'PAS UTILISABLE'} (t >= 2 : {'oui' if c1 else 'non'} ; au moins la moitie des"
          f" dollars : {'oui' if c2 else 'non'} ; positif sur 2023 - sept. 2026 : {'oui' if c3 else 'non'})", "",
          "D'ou vient le gain de la variante (points, jours tenus) : nuit 18 h -> 9 h 30 | seance 9 h 30 -> sortie",
          f"  toute la periode : {R.loc[m & tenus, 'nuit_pts'].sum():+,.0f} pt | {R.loc[m & tenus, 'jour_pts'].sum():+,.0f} pt"
          f" ; frais {int(tenus[m].sum()) * 2 * K.COTE:,.0f} pt",
          "", "Annee par annee ($ pour 1 MNQ) : annee | original | entre deux clotures | jours tenus"]
    for y in sorted(set(j[m].year)):
        mm = m & (j.year == y)
        L.append(f"{y} | {R.loc[mm, 'gain_o'].sum():+,.0f} | {R.loc[mm, 'gain_v'].sum():+,.0f} | {int(tenus[mm].sum())}")
    pire = R.loc[m & tenus, "gain_v"].nsmallest(5)
    L += ["", "Pires jours de la variante ($, 1 MNQ) : " + " ; ".join(f"{d.date()} {v:+,.0f}" for d, v in pire.items())]
    (K.ICI / "rsi2_entre_deux.txt").write_text("\n".join(L) + "\n")
    R.to_csv(K.ICI / "rsi2_entre_deux.csv.gz", float_format="%.4f")
    print("\n".join(L))


if __name__ == "__main__":
    main()
