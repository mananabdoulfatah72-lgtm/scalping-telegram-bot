#!/usr/bin/env python3
"""Un ou plusieurs Static 50K (descriptif, demande de l'utilisateur du 9 octobre 2026) : retraits recus dans les 12 mois
qui suivent chaque achat, systeme retenu (E0 P500), au niveau d'aujourd'hui, frais d'activation ignores (le nombre de
challenges reussis est donne pour les compter). N comptes achetes le meme jour (memes trades : N fois le resultat d'un
seul), une semaine d'ecart ou un mois d'ecart. Sans filtre, et filtre simule aussi bon qu'en 2026 (5 tirages).
Ecrit plusieurs.txt."""
import numpy as np
import pandas as pd

import donnees as DN
import moteur_static as M
import outils as U
import static as S

ECARTS = {"le meme jour": 0, "une semaine d'ecart": 1, "un mois d'ecart": 4}   # en departs (1 depart = 5 seances)
NOMBRES = (1, 3, 5, 10)


def resultats(D, b, dd):
    R = S.lancer(D, b, dd, "E0", "P500", h2=S.H1)
    return R[:, M.RECU1], (R[:, M.ISSUE] == 1) & (R[:, M.FIN_EVAL] <= S.H1)


def main():
    D = DN.charger()
    j, nj = D["jours"], len(D["jours"])
    dd = [d for d in U.departs(D) if j[d] >= pd.Timestamp("2012-01-01") and d + S.H1 <= nj]
    scen = {"sans filtre": [U.base(D)],
            "filtre aussi bon qu'en 2026 (simule, 5 tirages)": [U.base(D, g) for g in S.gardes_simules(D, S.rho_2026())[:5]]}
    L = ["Un ou plusieurs Static 50K : retraits recus dans les 12 mois apres chaque achat (bot + plafond de 500 $ sur le"
         " compte Pro, niveau d'aujourd'hui, activation ignoree)", ""]
    for nom, bases in scen.items():
        L.append(f"=== {nom}")
        L.append("periode des premiers achats | nombre | ecart | retraits a 0 $ | mediane | moyenne | 9 sur 10 sous | "
                 "challenges reussis (moyenne) | prix des challenges")
        res = [resultats(D, b, dd) for b in bases]
        for per, a, z in (("2012-2021", "2012-01-01", "2021-12-31"), ("2023 - 2024", "2023-01-01", "2024-12-31")):
            for n in NOMBRES:
                for en, e in ECARTS.items():
                    if n == 1 and e > 0:
                        continue
                    tot, nok = [], []
                    for recu, ok in res:
                        for k in range(len(dd)):
                            if not (pd.Timestamp(a) <= j[dd[k]] <= pd.Timestamp(z)):
                                continue
                            idx = [k + i * e for i in range(n)]
                            if idx[-1] >= len(dd):
                                continue
                            tot.append(recu[idx].sum() if e > 0 else n * recu[k])
                            nok.append(ok[idx].sum() if e > 0 else n * ok[k])
                    t = np.array(tot)
                    L.append(f"{per} | {n} | {'-' if n == 1 else en} | {(t == 0).mean():.0%} | {np.median(t):,.0f} $ |"
                             f" {t.mean():,.0f} $ | {np.quantile(t, 0.9):,.0f} $ | {np.mean(nok):.1f} | {30 * n} $")
        L.append("")
    (DN.ICI / "plusieurs.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
