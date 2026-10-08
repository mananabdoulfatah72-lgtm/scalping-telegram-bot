#!/usr/bin/env python3
"""Lecture de static50k (ecrite APRES les resultats, descriptive, aucune decision) : argent net par annee d'achat, et un
programme « un Static achete chaque mois pendant 12 mois » rejoue sur l'historique, pour la candidate retenue (E0 P500),
le bot tel quel (E0 P0) et la zone seule (E1 P500), au niveau d'aujourd'hui. Ecrit lecture.txt."""
import numpy as np
import pandas as pd

import donnees as DN
import moteur_static as M
import outils as U
import static as S


def main():
    D = DN.charger()
    j, nj = D["jours"], len(D["jours"])
    b0 = U.base(D)
    dd = [d for d in U.departs(D) if j[d] >= pd.Timestamp("2012-01-01") and d + S.H1 <= nj]
    L = ["Lecture (descriptive, ecrite apres les resultats) : au niveau d'aujourd'hui, 12 mois apres chaque achat", ""]
    for vc in (("E0", "P500"), ("E0", "P0"), ("E1", "P500")):
        R = S.lancer(D, b0, dd, vc[0], vc[1], h2=S.H1)
        ok = (R[:, M.ISSUE] == 1) & (R[:, M.FIN_EVAL] <= S.H1)
        net = R[:, M.RECU1] - S.PRIX - S.ACTIVATION * ok
        x = pd.DataFrame({"annee": j[dd].year, "net": net, "ok": ok, "ko": R[:, M.ISSUE] == -1,
                          "retrait": R[:, M.RECU1] > 0, "n580": net >= S.EUROS_500}, index=j[dd])
        L.append(f"=== {vc[0]} {vc[1]} : par annee d'achat (achats | argent net moyen | evaluation reussie / perdue |"
                 f" au moins un retrait | net >= 580 $)")
        for a, g in x.groupby("annee"):
            L.append(f"{a} | {len(g)} | {g['net'].mean():+,.0f} $ | {g['ok'].mean():.0%} / {g['ko'].mean():.0%} |"
                     f" {g['retrait'].mean():.0%} | {g['n580'].mean():.0%}")
        # programme : 12 achats, un tous les 4 departs (environ un par mois), argent net total sur les 12 achats
        prog = []
        for i in range(len(dd) - 44):
            idx = list(range(i, i + 48, 4))
            prog.append((j[dd[i]], net[idx].sum(), (net[idx] >= S.EUROS_500).sum()))
        P = pd.DataFrame(prog, columns=["debut", "total", "comptes_580"]).set_index("debut")
        for nom, a, b in (("programmes commences en 2012-2020", "2012", "2020"),
                          ("programmes commences en 2023 - sept. 2024", "2023", "2024-09-30")):
            q = P.loc[a:b, "total"]
            c = P.loc[a:b, "comptes_580"]
            L.append(f"programme 12 achats (1 par mois, 360 $ d'achats), {nom} ({len(q)}) : total net median {q.median():+,.0f} $,"
                     f" 10 % les plus mauvais <= {q.quantile(0.1):+,.0f} $, 10 % les meilleurs >= {q.quantile(0.9):+,.0f} $,"
                     f" programmes perdants {(q < 0).mean():.0%} ; comptes a +580 $ par programme : mediane {c.median():.0f} sur 12")
        L.append("")
    (DN.ICI / "lecture.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
