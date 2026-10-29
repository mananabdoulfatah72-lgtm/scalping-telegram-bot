#!/usr/bin/env python3
"""Partie J (README.md) : la zone du bot, mais entree des la cassure des niveaux du dernier controle, avec un objectif a
R fois le risque (risque = distance a la ligne de sortie du bot a l'entree). Sorties aux controles inchangees. Mesures sur
15 ans et dans le challenge Bulenox (memes chemins que situation_bulenox.py). Ecrit resultats/j/partie_j.txt.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/partie_j.py"""
import os

import numpy as np
from numba import njit

import challenge_ajouts as CA
import commun as K
import donnees as D
import partie_e as E
import partie_g as G
import situation_bulenox as SB

SORTIE = K.ICI / "resultats" / "j"
# nom : (cassure, R, vrai stop, risque : 0 ligne de sortie, 1 VWAP, 2 largeur de la zone)
VARIANTES = {"bot (controles seuls)": (False, 0.0, False, 0), "J0 cassure sans objectif": (True, 0.0, False, 0),
             "J2 cassure, objectif 2 x risque": (True, 2.0, False, 0), "J3 cassure, objectif 3 x risque": (True, 3.0, False, 0),
             "J2s idem + vrai stop (info)": (True, 2.0, True, 0), "J3s idem + vrai stop (info)": (True, 3.0, True, 0),
             "JV2 risque au VWAP, 2 x": (True, 2.0, False, 1), "JV3 risque au VWAP, 3 x": (True, 3.0, False, 1),
             "JM2 risque = largeur zone, 2 x": (True, 2.0, False, 2), "JM3 risque = largeur zone, 3 x": (True, 3.0, False, 2)}


@njit(cache=True)
def _ecrit(tr, nt, s, me, sens, px, mx, xp, motif, risque):
    tr[nt, 0], tr[nt, 1], tr[nt, 2], tr[nt, 3] = s, me, sens, px
    tr[nt, 4], tr[nt, 5], tr[nt, 6], tr[nt, 7] = mx, xp, motif, risque


@njit(cache=True)
def _zone_j(O, H, L, C, sigma, vwap, href, bref, jouable, cassure, R, stop_dur, tick, mode):
    """Trades reels (seance, minute d'entree, sens, prix d'entree, minute de sortie, prix de sortie, motif 0 controle ou
    16 h / 1 objectif / 2 stop, risque). Entree a la cloture de la minute ; objectif et stop a partir de la minute suivante."""
    S, N = C.shape
    tr = np.zeros((S * 60, 8))
    nt = 0
    for s in range(S):
        if not jouable[s]:
            continue
        virt, tenu, me = 0, 0, -1
        px, obj, sl, risque = 0.0, np.nan, np.nan, 0.0
        ub, lb, sg = np.nan, np.nan, np.nan
        for m in range(30, N):
            p = C[s, m]
            if tenu != 0 and m > me:
                if stop_dur and not np.isnan(sl) and ((tenu > 0 and L[s, m] <= sl) or (tenu < 0 and H[s, m] >= sl)):
                    x = (min(O[s, m], sl) - tick) if tenu > 0 else (max(O[s, m], sl) + tick)
                    _ecrit(tr, nt, s, me, tenu, px, m, x, 2, risque)
                    nt += 1
                    tenu = 0
                elif not np.isnan(obj) and ((tenu > 0 and H[s, m] >= obj + tick) or (tenu < 0 and L[s, m] <= obj - tick)):
                    _ecrit(tr, nt, s, me, tenu, px, m, obj, 1, risque)
                    nt += 1
                    tenu = 0
            if m == N - 1:
                if tenu != 0:
                    _ecrit(tr, nt, s, me, tenu, px, m, p, 0, risque)
                    nt += 1
                break
            entre = 0
            if m % 30 == 0:
                sg = sigma[s, m]
                ub, lb = href[s] * (1 + sg), bref[s] * (1 - sg)
                if virt != 0 and ((virt > 0 and p <= max(ub, vwap[s, m])) or (virt < 0 and p >= min(lb, vwap[s, m]))):
                    if tenu != 0:
                        _ecrit(tr, nt, s, me, tenu, px, m, p, 0, risque)
                        nt += 1
                    virt, tenu = 0, 0
                if virt == 0 and m <= 360:
                    entre = 1 if p > ub else (-1 if p < lb else 0)
            elif cassure and virt == 0 and m < 360:
                entre = 1 if p > ub else (-1 if p < lb else 0)
            if entre != 0:
                virt, tenu, me, px = entre, entre, m, p
                ligne = max(ub, vwap[s, m]) if entre > 0 else min(lb, vwap[s, m])
                risque = entre * (px - ligne)
                if mode == 1:
                    risque = entre * (px - vwap[s, m])
                elif mode == 2:
                    risque = (href[s] if entre > 0 else bref[s]) * sg
                obj = px + entre * R * risque if (R > 0 and risque > 0) else np.nan
                sl = ligne if (stop_dur and risque > 0) else np.nan
    return tr[:nt]


def main():
    d = D.minutes("NQ", chemin=os.environ["MINUTES"], debut="2011-01-01")
    S = d["c"].shape[0]
    sigma, vwap, href, bref, jouable = G.zone_tableaux(d)
    # controle : le bot recalcule ici = zone de partie_g (verifiee contre le robot)
    t0 = _zone_j(d["o"], d["h"], d["l"], d["c"], sigma, vwap, href, bref, jouable, False, 0.0, False, float(d["tick"]), 0)
    ref = G.calcul(d)[4]
    a = {(int(x[0]), int(x[1]), int(x[2]), int(x[4])) for x in t0}
    b = {tuple(int(v) for v in x) for x in ref}
    fed = np.isin(d["jours"], E.fomc())
    an = d["jours"].astype("datetime64[Y]").astype(int) + 1970
    jo = jouable & ~fed
    dep = np.flatnonzero(d["jours"] >= np.datetime64("2012-01-01"))
    situations = [("49 500 $, plus haut 51 172 $, 13 seances", 49500.0, 51172.0, 13),
                  ("49 500 $, plus haut 50 600 $, 13 seances", 49500.0, 50600.0, 13),
                  ("challenge neuf, 21 seances", 50000.0, 50000.0, 21)]
    L = [f"Minutes du NQ : {d['jours'][0]} - {d['jours'][-1]} ({S} seances). Controle : bot recalcule {len(a)} trades, zone de "
         f"partie_g {len(b)}, communs {len(a & b)}.", "",
         f"{'variante':<34} {'trades':>6} {'points':>8} {'objectif':>8} {'risque med':>10} {'t 11-22':>8} {'t 23-26':>8} "
         f"{'2025':>7} {'2026':>7} {'jours -250$':>11}"]
    chall = []
    zero = np.zeros_like(d["c"])
    for nom, (cas, R, sd, mo) in VARIANTES.items():
        t = _zone_j(d["o"], d["h"], d["l"], d["c"], sigma, vwap, href, bref, jouable, cas, R, sd, float(d["tick"]), mo)
        pts = t[:, 2] * (t[:, 5] - t[:, 3]) - float(d["frais"]) / float(d["pt"])
        Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in t])
        g = Zc[:, -1]
        ts = []
        for a0, a1 in ((2011, 2022), (2023, 2026)):
            x = g[jo & (an >= a0) & (an <= a1)]
            ts.append(x.mean() / x.std(ddof=1) * np.sqrt(len(x)))
        pa = {y: pts[an[t[:, 0].astype(int)] == y].sum() for y in (2025, 2026)}
        L.append(f"{nom:<34} {len(t):>6} {pts.sum():>+8.0f} {(t[:, 6] == 1).mean():>8.0%} {np.median(t[:, 7]):>10.2f} "
                 f"{ts[0]:>+8.2f} {ts[1]:>+8.2f} {pa[2025]:>+7.0f} {pa[2026]:>+7.0f} {int((Zw[jo].min(axis=1) <= -250).sum()):>11}")
        lig = f"{nom:<34}"
        for _, solde, haut, n in situations:
            dd = dep[dep <= S - n]
            r = SB._depuis(Zc, Zw, zero, zero, fed, dd, n, 4.0, 6.0, 0.0, solde, haut, 1000.0)
            lig += f"   {(r == 1).mean():6.1%} {(r == -1).mean():6.1%} {(r == 0).mean():6.1%}"
        chall.append(lig)
    L += ["", "(points bruts pour 1 MNQ, frais de 1,5 point deduits ; t des gains quotidiens au prix d'aujourd'hui, jours sans "
          "Fed ; jours -250$ = 1 000 $ en 4 MNQ, au pire de chaque minute)", "",
          "Challenge, 4 puis 6 MNQ, limite du jour 1 000 $, departs 2012-2026 : valide / perdu / expire",
          f"{'variante':<34}" + "".join(f"   {s[0][:27]:<20}" for s in situations)] + chall
    SORTIE.mkdir(parents=True, exist_ok=True)
    (SORTIE / "partie_j.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
