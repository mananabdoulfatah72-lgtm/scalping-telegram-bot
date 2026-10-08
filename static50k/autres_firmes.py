#!/usr/bin/env python3
"""Descriptif (README.md, « Les autres firmes ») : intraday50k/financee.py (Bulenox option 2, Topstep, Tradeify Growth ;
bot zone + RSI(2) entre deux clotures) rejoue au niveau d'aujourd'hui sur les departs de verification de static50k.
Argent net = retraits (part du trader) - prix (mois d'abonnement compris) - activation. Ecrit autres_firmes.txt."""
import sys

import numpy as np
import pandas as pd

import donnees as DN
import outils as U

sys.path.insert(0, str(DN.R0 / "intraday50k"))
import comptes as CP  # noqa: E402
import financee as F  # noqa: E402

K = DN.K


def main():
    D = K.charger()
    j, nj = D["jours"], len(D["jours"])
    der = D["derniere"]
    cn = D["C"][np.arange(nj), der]
    zt = K.P.tableaux_zone(D["Z"], nj, np.ones(len(D["Z"]), bool))
    dd = [d for d in U.departs(D) if j[d] >= pd.Timestamp("2023-01-01") and d + F.UN_AN <= nj]
    L = [f"Comptes intraday (financee.py) sur les {len(dd)} departs de verification de static50k (2023 - sept. 2025),"
         " 12 mois apres l'achat", "compte | bot | prix | achats | challenge reussi | au moins un retrait | retraits"
         " moyens (part du trader) | argent net moyen | net >= 580 $"]
    for nc, fin_ in F.FINANCES.items():
        e = CP.COMPTES[nc][:7]
        prix, mensuel, activation = fin_["prix"]
        for nb, r in CP.BOTS.items():
            for niveau in (True, False):
                out = []
                for d in dd:
                    f = U.facteur(cn, d) if niveau else 1.0
                    s = slice(d, min(nj, d + F.UN_AN + 1))
                    a = (D["O"][s] * f, D["H"][s] * f, D["L"][s] * f, D["C"][s] * f, der[s], zt[0][s], zt[1][s],
                         *zt[2:], D["dec"][s], D["voulu"][s], D["NO"][s] * f, D["NH"][s] * f, D["NL"][s] * f, D["nn"][s])
                    out.append(F.parcours(0, r, *a, *e, *fin_["f"], K.P.FRAIS_ZONE, K.P.FRAIS_RSI))
                R = pd.DataFrame(out, columns=["issue", "seances", "perdu_f", "n", "recu", "premier"])
                ok = R["issue"] == 1
                mois = np.ceil(R["seances"] / 21.0) if mensuel else 1.0
                net = R["recu"] * fin_["part"] - (prix * mois + np.where(ok, activation, 0.0))
                L.append(f"{nc} | {nb} | {'aujourd hui' if niveau else 'epoque'} | {len(dd)} | {ok.mean():.0%} |"
                         f" {(R['n'] > 0).mean():.0%} | {(R['recu'] * fin_['part']).mean():,.0f} $ | {net.mean():+,.0f} $ |"
                         f" {(net >= 580).mean():.0%}")
                print(L[-1], flush=True)
    (DN.ICI / "autres_firmes.txt").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
