#!/usr/bin/env python3
"""Point d'etape sur les seances neuves du 19 au 27 octobre 2026 (flux/README.md) : S1, S2 et S2b comme le bot, et la
meilleure configuration de la partie 3 choisie avec les seules seances d'avant le 17 octobre (score du reglage glissant).

Lancer : KB=<copie de claude/keen-babbage-r686cl> FLUX_EXPORTS=flux/donnees python3 flux/point_19_27oct.py"""
from pathlib import Path

import numpy as np
import pandas as pd

import donnees as D
import quant as Q
import reglages as R
import selection3 as S3
import systeme as Y

ICI = Path(__file__).resolve().parent
NEUVES = [pd.Timestamp(x) for x in ("2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23", "2026-10-26",
                                    "2026-10-27")]
SANS_VEILLE = pd.Timestamp("2026-10-19")


def ligne_jours(tr, info, jours):
    par = {j: 0.0 for j in jours}
    nb = {j: 0 for j in jours}
    for r in tr.itertuples():
        j = info["jour"][r.seance]
        if j in par:
            par[j] += r.net
            nb[j] += 1
    return " | ".join(f"{j:%d/%m} {par[j]:+.1f} ({nb[j]})" for j in jours)


def main():
    m, info, _ = D.seances()
    jours = info["jour"]
    assert all(j in set(jours) for j in NEUVES), "seances neuves absentes : FLUX_EXPORTS ?"
    idx = {j: i for i, j in enumerate(jours)}
    neuves = [idx[j] for j in NEUVES]
    X = Y.mesures(m, info)
    L = [f"Point d'etape, seances neuves : {', '.join(f'{j:%d/%m}' for j in NEUVES)} (export Rithmic du 29 octobre). "
         "Points de NQ par trade, frais compris ; 1 point = 2 $ par MNQ.", "", "Regles du bot :"]
    regles = {"S1": Y.jouer(m, info, X, Y.signaux_s1), "S2": Y.jouer(m, info, X, Y.signaux_s2)}
    regles["S2b"] = R.trades_config(R.tableaux(m, info), R.table_configs().iloc[82358])
    for nom, tr in regles.items():
        ok = [i for i in neuves if not (nom in ("S2", "S2b") and jours[i] == SANS_VEILLE)]
        t = tr[tr["seance"].isin(ok)]
        L.append(f"  {nom:<4} {len(t)} trade(s), {t['net'].sum():+.1f} pt ({2 * t['net'].sum():+,.0f} $ par MNQ)"
                 + (f", net moyen {t['net'].mean():+.2f}" if len(t) else "") + f" ; jour par jour : {ligne_jours(t, info, NEUVES)}")
    # partie 3 : meilleure configuration au 16 octobre (score du reglage glissant, G1 - G9 ensemble)
    Xq, info_q = Q.tape()
    cf = Q.table_configs()
    P, N = Q.calculer(Xq, cf)
    jou = Xq["jouable"]
    passe = np.flatnonzero(jou & (info_q["jour"] <= pd.Timestamp("2026-10-16")).to_numpy())
    n_min = np.array([0.25 if f in ("G4", "G5", "G9") else 0.5 for f in cf["famille"]]) * len(passe)
    sc, t, n, moy = S3.score(P.astype(float), N.astype(float), passe, n_min)
    sc = np.where((moy > 0) & (n > 0), sc, -np.inf)
    i = int(np.argmax(sc))
    neuves_q = [k for k, j in enumerate(info_q["jour"]) if j in set(NEUVES)]
    gain = P[i, neuves_q]
    L += ["", "Partie 3, meilleure configuration choisie avec les seances jusqu'au 16 octobre (aucune seance neuve) :",
          f"  {S3.decrire(cf.iloc[i])}",
          f"  sur le passe : {int(n[i])} trades, net moyen {moy[i]:+.2f} pt, score {sc[i]:.2f}",
          f"  seances neuves : {int(N[i, neuves_q].sum())} trade(s), {gain.sum():+.1f} pt ({2 * gain.sum():+,.0f} $ par MNQ) ; "
          + " | ".join(f"{info_q['jour'][k]:%d/%m} {P[i, k]:+.1f} ({int(N[i, k])})" for k in neuves_q)]
    texte = "\n".join(L)
    (ICI / "resultats" / "point_19_27oct.txt").write_text(texte + "\n")
    print(texte)


if __name__ == "__main__":
    main()
