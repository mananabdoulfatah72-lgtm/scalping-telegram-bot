#!/usr/bin/env python3
"""Challenge LucidFlex 50K sans limite de temps (descriptif, 27 octobre 2026) avec la version installee du bot (cassure + volume
x1 + fenetre 5 min, une entree par seance, pas de sortie aux controles, stop a 70 points du niveau casse, 16 h) et Q1 / Q2.
Regles notees en aout 2026 (kbf/vague8/README.md, a faire confirmer par Lucid) : objectif +3 000 $, perte permise 2 000 $
comptee en fin de journee et bloquee a +100 $ (plancher = min(plus haut de fin de journee - 2 000, 50 100)), touchee a
n'importe quel moment (pire de chaque minute) ; regularite : validation en fin de journee si gain >= 3 000 $ et meilleure
journee <= 50 % du gain ; pas de limite du jour de la firme (limite du bot 1 000 $ gardee) ; pas de zone les jours de la Fed ;
objectif du bot a 0 (il continue tant que la regularite n'est pas remplie). Simulation arretee apres 252 seances (un an).
Ecrit resultats/j/lucid_27oct.txt.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/lucid_27oct.py"""
import os

import numpy as np
from numba import njit

import challenge_ajouts as CA
import donnees as D
import partie_e as E
import partie_g as G
import partie_j as J
import partie_q as PQ
import reglages_27oct_stop as ST


@njit(cache=True)
def _lucid(Zc, Zw, fed, departs, z, limite, max_seances):
    S, N = Zc.shape
    etat = np.zeros(len(departs), np.int64)
    duree = np.zeros(len(departs), np.int64)
    for k in range(len(departs)):
        bal, haut, meilleur = 50000.0, 50000.0, 0.0
        plancher = 48000.0
        d0 = departs[k]
        n = 0
        for s in range(d0, min(S, d0 + max_seances)):
            n += 1
            jour, perdu = 0.0, False
            if not fed[s]:
                for m in range(N):
                    pire = z * Zw[s, m]
                    if bal + pire <= plancher:
                        perdu = True
                        break
                    if pire <= -limite:
                        jour = -limite
                        break
                    jour = z * Zc[s, m]
            if perdu:
                etat[k] = -1
                break
            bal += jour
            meilleur = max(meilleur, jour)
            haut = max(haut, bal)
            plancher = min(haut - 2000.0, 50100.0)
            if bal <= plancher:
                etat[k] = -1
                break
            gain = bal - 50000.0
            if gain >= 3000.0 and meilleur <= 0.5 * gain:
                etat[k] = 1
                break
        duree[k] = n
    return etat, duree


def main():
    d = D.minutes("NQ", chemin=os.environ["MINUTES"], debut="2011-01-01")
    S, N = d["c"].shape
    sigma, vwap, href, bref, jouable = G.zone_tableaux(d)
    tend = PQ.tendance(d)
    fed = np.isin(d["jours"], E.fomc())
    dist = 70.0 * d["o"][:, 0] / float(d["pref"])
    dep = np.flatnonzero(d["jours"] >= np.datetime64("2012-01-01"))
    groupes = (("departs 2012 - 2025", dep[d["jours"][dep] < np.datetime64("2025-10-01")]),
               ("departs 2023 - sept. 2025", dep[(d["jours"][dep] >= np.datetime64("2023-01-01")) & (d["jours"][dep] < np.datetime64("2025-10-01"))]))
    L = ["LucidFlex 50K sans limite de temps, version installee du bot (stop 70 points du niveau), au prix d'aujourd'hui.",
         "Valide = objectif + regularite remplis ; perdu = plancher touche ; en cours = ni l'un ni l'autre apres un an.", ""]
    for f, nom in ((0, "aucun filtre (installee)"), (1, "Q1"), (2, "Q2"), (7, "Q1 + Q2")):
        t = PQ._zone_q(d["o"], d["h"], d["l"], d["c"], d["v"], sigma, vwap, href, bref, tend, jouable, 1.0, 5, f).copy()
        t[:, 4], t[:, 5], t[:, 6] = N - 1, d["c"][t[:, 0].astype(int), N - 1], 0
        s_, me, e = t[:, 0].astype(int), t[:, 1].astype(int), t[:, 2]
        ctl = (me // 30) * 30
        niv = np.where(e > 0, href[s_] * (1 + sigma[s_, ctl]), bref[s_] * (1 - sigma[s_, ctl]))
        t = ST._avec_stop(d["o"], d["h"], d["l"], d["c"], t, niv, dist, float(d["tick"]))
        Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in t])
        for z in (1.0, 2.0, 3.0):
            lig = f"{nom:<26} {int(z)} MNQ"
            for gnom, g in groupes:
                et, du = _lucid(Zc, Zw, fed, g, z, 1000.0, 252)
                ok = et == 1
                lig += (f"  | {gnom} : valide {ok.mean():5.1%}, perdu {(et == -1).mean():5.1%}, en cours {(et == 0).mean():4.1%}, "
                        f"seances pour valider {np.median(du[ok]) if ok.any() else float('nan'):.0f} (mediane)")
            L.append(lig)
        L.append("")
    (J.SORTIE / "lucid_27oct.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
