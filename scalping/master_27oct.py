#!/usr/bin/env python3
"""Compte Master Bulenox 50K (descriptif, 27 octobre 2026) avec la version installee du bot (cassure + volume x1 + fenetre 5 min,
une entree par seance, pas de sortie aux controles, stop a 70 points du niveau casse, 16 h) et Q1 / Q2. Regles notees dans les
recherches (kbf/intraday50k/financee.py, « Bulenox option 2 ») : perte 2 500 $ en fin de journee bloquee a +100 $, touchee a
n'importe quel moment ; cycle de 10 jours avec un trade ; meilleur jour <= 40 % du gain du cycle ; solde garde >= 52 600 $ ;
retrait entre 1 000 $ et 1 500 $ ; compte reel apres 3 retraits (la simulation s'arrete la) ; 100 % pour le trader. Limite du jour
du bot 1 000 $ ; plafond du jour 500 $ (reglage conseille du Master) ou aucun ; frein non simule (0). Un an de compte finance
apres chaque depart (2012 - sept. 2025). Ecrit resultats/j/master_27oct.txt.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/master_27oct.py"""
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
def _master(Zc, Zw, trade, fed, departs, z, plafond, limite, horizon):
    S, N = Zc.shape
    n_dep = len(departs)
    perdu = np.zeros(n_dep, np.bool_)
    nret = np.zeros(n_dep, np.int64)
    recu = np.zeros(n_dep)
    premier = np.full(n_dep, -1, np.int64)
    for k in range(n_dep):
        cash, haut, base, veille = 0.0, 0.0, 0.0, 0.0
        plancher = -2500.0
        meilleur, qual = -1e18, 0
        for s in range(departs[k], min(S, departs[k] + horizon)):
            jour, fini = 0.0, False
            if not fed[s]:
                for m in range(N):
                    pire = z * Zw[s, m]
                    clo = z * Zc[s, m]
                    if cash + pire <= plancher:
                        fini = True
                        break
                    if pire <= -limite:
                        jour = -limite
                        break
                    if plafond > 0 and clo >= plafond:
                        jour = plafond
                        break
                    jour = clo
            if fini:
                perdu[k] = True
                break
            cash += jour
            if trade[s] and not fed[s]:
                qual += 1
            g = cash - veille
            veille = cash
            if g > meilleur:
                meilleur = g
            if cash > haut:
                haut = cash
            plancher = min(haut - 2500.0, 100.0)
            if cash <= plancher:
                perdu[k] = True
                break
            gain = cash - base
            if qual >= 10 and gain > 0.0 and meilleur <= 0.40 * gain:
                x = min(1500.0, cash - 2600.0)
                if x >= 1000.0:
                    cash -= x
                    veille = cash
                    recu[k] += x
                    nret[k] += 1
                    if premier[k] < 0:
                        premier[k] = s - departs[k] + 1
                    base, meilleur, qual = cash, -1e18, 0
                    if nret[k] >= 3:
                        break
    return perdu, nret, recu, premier


def main():
    d = D.minutes("NQ", chemin=os.environ["MINUTES"], debut="2011-01-01")
    S, N = d["c"].shape
    sigma, vwap, href, bref, jouable = G.zone_tableaux(d)
    tend = PQ.tendance(d)
    fed = np.isin(d["jours"], E.fomc())
    dist = 70.0 * d["o"][:, 0] / float(d["pref"])
    dep = np.flatnonzero(d["jours"] >= np.datetime64("2012-01-01"))
    groupes = (("departs 2012 - sept. 2025", dep[(d["jours"][dep] < np.datetime64("2025-10-01")) & (dep + 252 <= S)]),
               ("departs 2023 - sept. 2025", dep[(d["jours"][dep] >= np.datetime64("2023-01-01")) & (dep + 252 <= S)]))
    L = ["Compte Master Bulenox 50K, un an apres chaque depart, version installee du bot (stop 70 points du niveau).",
         "perdu = compte finance perdu dans l'annee ; retraits = moyenne ; recu = moyenne recue (100 % pour le trader, 3 retraits au plus,"
         " puis compte reel) ; 1er retrait = mediane des seances avant le premier retrait (comptes qui en ont un).", ""]
    for f, nom in ((0, "aucun filtre (installee)"), (1, "Q1"), (2, "Q2"), (7, "Q1 + Q2")):
        t = PQ._zone_q(d["o"], d["h"], d["l"], d["c"], d["v"], sigma, vwap, href, bref, tend, jouable, 1.0, 5, f).copy()
        t[:, 4], t[:, 5], t[:, 6] = N - 1, d["c"][t[:, 0].astype(int), N - 1], 0
        s_, me, e = t[:, 0].astype(int), t[:, 1].astype(int), t[:, 2]
        ctl = (me // 30) * 30
        niv = np.where(e > 0, href[s_] * (1 + sigma[s_, ctl]), bref[s_] * (1 - sigma[s_, ctl]))
        t = ST._avec_stop(d["o"], d["h"], d["l"], d["c"], t, niv, dist, float(d["tick"]))
        Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in t])
        trade = np.zeros(S, np.bool_)
        trade[s_] = True
        for z in (1.0, 2.0):
            for plafond in (500.0, 0.0):
                lig = f"{nom:<24} {int(z)} MNQ, plafond {'500 $' if plafond else 'aucun':<6}"
                for gnom, g in groupes:
                    pe, nr, rc, pr = _master(Zc, Zw, trade, fed, g, z, plafond, 1000.0, 252)
                    lig += (f" | {gnom} : perdu {pe.mean():5.1%}, retraits {nr.mean():.2f}, recu {rc.mean():>6,.0f} $, au moins un retrait "
                            f"{(nr > 0).mean():5.1%}, 1er retrait {np.median(pr[pr > 0]) if (pr > 0).any() else float('nan'):.0f} seances")
                L.append(lig)
        L.append("")
    (J.SORTIE / "master_27oct.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
