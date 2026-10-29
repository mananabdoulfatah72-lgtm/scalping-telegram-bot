#!/usr/bin/env python3
"""Situation du challenge Bulenox (situation_bulenox.py) avec la zone qui entre a la cassure, a chaque fin de minute (E1 de
entree_tardive/, branche claude/elegant-ptolemy-g94s8t), au lieu des seuls controles de 30 minutes (H1). Sorties inchangees
(controles et 16 h). Trades lus dans entree_tardive/trades/{H1,E1}_15ans.csv (2011 - 19 octobre 2026, sans filtre).
Lancer : KB=<branche de recherche> ET=<dossier des trades> SOLDE=49500 HAUT=51172 SEANCES=13 python3 scalping/situation_cassure.py"""
import os
from pathlib import Path

import numpy as np
import pandas as pd

import challenge_ajouts as CA
import commun as K
import partie_e as E
import partie_g as G
import situation_bulenox as SB


def trades_csv(d, chemin):
    t = pd.read_csv(chemin)
    idx = {j: s for s, j in enumerate(d["jours"].astype("datetime64[D]").astype(str))}
    t = t[t["jour"].isin(idx)]
    return [(idx[j], int(me), float(sg), int(ms)) for j, me, sg, ms in
            zip(t["jour"], t["minute_entree"], t["sens"], t["minute_sortie"])]


def main():
    solde, haut = float(os.getenv("SOLDE", "49500")), float(os.getenv("HAUT", "51172"))
    n, limite = int(os.getenv("SEANCES", "13")), float(os.getenv("LIMITE", "1000"))
    et = Path(os.environ["ET"])
    d = E.jour_nq()
    S = d["c"].shape[0]
    h1 = trades_csv(d, et / "H1_15ans.csv")
    e1 = trades_csv(d, et / "E1_15ans.csv")
    # controle : H1 lu dans le fichier = zone recalculee ici (partie_g), sur les seances communes
    tr = G.calcul(d)[4]
    fin = max(s for s, *_ in h1)
    a, b = set(map(tuple, h1)), {(int(s), int(me), float(sg), int(ms)) for s, me, sg, ms in tr if s <= fin}
    fed = np.isin(d["jours"], E.fomc())
    dep = np.flatnonzero((d["jours"] >= np.datetime64("2012-01-01")) & (np.arange(S) <= fin + 1 - n))
    dep23 = dep[d["jours"][dep] >= np.datetime64("2023-01-01")]
    plancher = 50100.0 if haut >= 52600.0 else haut - 2500.0
    L = [f"Controle : {len(a)} trades H1 lus, {len(b)} recalcules, {len(a & b)} communs.",
         f"Situation : solde {solde:,.0f} $, plus haut {haut:,.0f} $, plancher {plancher:,.0f} $, {n} seances, limite du jour "
         f"{limite:,.0f} $, 4 puis 6 MNQ (2 puis 4 et 6 puis 8 en plus).", "",
         f"{'zone':<40} {'MNQ':<9} {'2012-2026 : valide  perdu  expire':<34} {'2023-2026 : valide  perdu  expire'}"]
    zero = np.zeros((S, d["c"].shape[1]))
    for nom, t in (("controles de 30 min (le bot)", h1), ("entree a la cassure, chaque minute (E1)", e1)):
        Zc, Zw = CA.chemins(d, CA.trades_zone(d, t))
        for z1, z2 in ((4, 6), (2, 4), (6, 8)):
            r = [SB._depuis(Zc, Zw, zero, zero, fed, x, n, float(z1), float(z2), 0.0, solde, haut, limite) for x in (dep, dep23)]
            v = [((q == 1).mean(), (q == -1).mean(), (q == 0).mean()) for q in r]
            L.append(f"{nom:<40} {f'{z1} puis {z2}':<9} {v[0][0]:7.1%} {v[0][1]:7.1%} {v[0][2]:7.1%}    "
                     f"{v[1][0]:7.1%} {v[1][1]:7.1%} {v[1][2]:7.1%}")
    out = K.ICI / "resultats" / "i" / f"situation_cassure_{solde:.0f}_haut{haut:.0f}.txt"
    out.write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
