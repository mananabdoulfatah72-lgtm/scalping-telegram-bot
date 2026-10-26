#!/usr/bin/env python3
"""Resultats annee par annee de la configuration installee le 26 octobre 2026 (reglages_26oct_g.py, fenetre 5, volume x1,
une entree par seance, sortie au niveau casse aux controles, 16 h), en 4 MNQ, avec la limite de perte du jour de 1 000 $.
Deux echelles : au prix d'aujourd'hui (mouvements en % ramenes au NQ d'aujourd'hui) et aux prix de l'epoque. Descriptif.
Ecrit resultats/j/reglages_26oct_annees.txt.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/reglages_26oct_annees.py"""
import os

import numpy as np
import pandas as pd

import challenge_ajouts as CA
import donnees as D
import partie_e as E
import partie_g as G
import partie_j as J
import reglages_26oct_g as RG


def main():
    d = D.minutes("NQ", chemin=os.environ["MINUTES"], debut="2011-01-01")
    sigma, vwap, href, bref, jouable = G.zone_tableaux(d)
    fed = np.isin(d["jours"], E.fomc())
    jo = jouable & ~fed
    jours = pd.to_datetime(d["jours"])
    t = RG._zone_fw(d["c"], d["v"], sigma, href, bref, jouable, 1.0, 5, 30)
    Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in t])
    ech = float(d["pref"]) / d["o"][:, 0]
    L = ["Configuration installee (fenetre 5 min, volume x1, une entree par seance), 4 MNQ, frais deduits, limite du jour 1 000 $,",
         "pas de trade les jours de la Fed. « Prix d'aujourd'hui » : chaque journee ramenee au NQ a 30 900 ; « epoque » : vrais prix.", "",
         f"{'annee':<6} {'trades':>6} {'jours gagnants':>14} {'jours a -1000':>13} {'$ prix aujourd hui':>18} {'pire baisse':>11} "
         f"{'meilleur mois':>13} {'pire mois':>10} {'$ prix epoque':>13}"]
    j4 = pd.Series(np.where(jo, np.where((4 * Zw <= -1000).any(axis=1), -1000.0, 4 * Zc[:, -1]), 0.0), index=jours)
    j4e = pd.Series(np.where(jo, np.where((4 * Zw / ech[:, None] <= -1000).any(axis=1), -1000.0, 4 * Zc[:, -1] / ech), 0.0), index=jours)
    an_t = pd.to_datetime(d["jours"][t[:, 0].astype(int)]).year
    tot, tote = 0.0, 0.0
    for y in range(2011, 2027):
        x = j4[j4.index.year == y]
        xe = j4e[j4e.index.year == y]
        tr = x[x != 0]
        eq = x.cumsum()
        dd = (eq - eq.cummax()).min()
        m = x.groupby(x.index.month).sum()
        tot += x.sum()
        tote += xe.sum()
        L.append(f"{y:<6} {int((an_t == y).sum()):>6} {(tr > 0).mean():>14.0%} {int((tr <= -1000).sum()):>13} {x.sum():>+18,.0f} "
                 f"{dd:>+11,.0f} {m.max():>+13,.0f} {m.min():>+10,.0f} {xe.sum():>+13,.0f}")
    eq = j4.cumsum()
    L += ["", f"Total 2011 - 23 octobre 2026 : {tot:+,.0f} $ au prix d'aujourd'hui ({tot / 15.8:+,.0f} $ par an en moyenne), "
          f"{tote:+,.0f} $ aux prix de l'epoque.",
          f"Pire baisse depuis un sommet sur toute la periode (prix d'aujourd'hui) : {(eq - eq.cummax()).min():+,.0f} $.",
          f"Depuis 2023 : {j4[j4.index >= '2023-01-01'].sum():+,.0f} $ ; annees perdantes : "
          + ", ".join(str(y) for y in range(2011, 2027) if j4[j4.index.year == y].sum() < 0)]
    (J.SORTIE / "reglages_26oct_annees.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
