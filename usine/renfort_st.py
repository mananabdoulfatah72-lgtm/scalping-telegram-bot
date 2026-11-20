#!/usr/bin/env python3
"""Le « scalpeur qui s'empile » du bureau de 6 agents, sur le Supertrend 10-3 : 1 MNQ de plus quand une cloture de 5 minutes
est a 1 ATR ou plus en gain depuis l'entree (une seule fois par trade, pas apres 15 h 30), garde jusqu'a la sortie du
Supertrend. Avec ou sans l'arret du jour apres une bougie de plus de 3 ATR (A2). Limite du jour 400 $.
Controle : sans renfort ni A2, le code redonne exactement le Supertrend du moteur.
Usage : KB_MINUTES=<nasdaq100_1min.csv.gz> NQ_RECENT=<nq_1min.csv.gz> python3 usine/renfort_st.py
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
from numba import njit

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import donnees as Dn  # noqa: E402
import moteur as Mo  # noqa: E402
import pupitre as Pu  # noqa: E402
import agents_st as A  # noqa: E402

N = Mo.N


@njit(cache=True)
def k_st_renfort(O, H, L, C, ok, per, mult, renfort, a2):
    S = C.shape[0]; nb = S * 78
    h5 = np.empty(nb); l5 = np.empty(nb); c5 = np.empty(nb)
    for s in range(S):
        for b in range(78):
            hh = H[s, 5 * b]; ll = L[s, 5 * b]
            for q in range(1, 5):
                hh = max(hh, H[s, 5 * b + q]); ll = min(ll, L[s, 5 * b + q])
            h5[s * 78 + b] = hh; l5[s * 78 + b] = ll; c5[s * 78 + b] = C[s, 5 * b + 4]
    st = np.zeros(nb); atrs = np.zeros(nb); atr = 0.0; hb = np.nan; lb = np.nan; dr = 1.0
    for i in range(1, nb):
        tr = max(h5[i] - l5[i], abs(h5[i] - c5[i - 1]), abs(l5[i] - c5[i - 1]))
        atr = tr if i == 1 else (atr * (per - 1) + tr) / per
        atrs[i] = atr
        mid = (h5[i] + l5[i]) / 2; hb2 = mid + mult * atr; lb2 = mid - mult * atr
        if i > 1:
            hb2 = hb2 if (hb2 < hb or c5[i - 1] > hb) else hb
            lb2 = lb2 if (lb2 > lb or c5[i - 1] < lb) else lb
            if dr > 0 and c5[i] < lb2:
                dr = -1.0
            elif dr < 0 and c5[i] > hb2:
                dr = 1.0
        hb = hb2; lb = lb2
        st[i] = dr if i >= per else 0.0
    pg = np.zeros((S, N), np.int8); pi = np.zeros((S, N), np.int8)
    for s in range(S):
        if not ok[s]:
            continue
        pos = 0; taille = 0; cur = 0; dq = 0; entree = 0.0; ajoute = False; arret = False
        for bb in range(76):
            i = s * 78 + bb; v = st[i]; mm = 5 * bb + 5
            if a2 and bb > 0 and (h5[i] - l5[i]) > 3.0 * atrs[i - 1]:
                arret = True
            cible = pos if v == 0 else int(v)
            if arret:
                cible = 0
            if cible != pos and pos != 0:
                pos = 0; taille = 0
            if cible != 0 and pos == 0 and mm <= 360:
                pos = cible; taille = 1; entree = O[s, mm]; ajoute = False
            elif renfort and pos != 0 and not ajoute and mm <= 360 and pos * (c5[i] - entree) >= atrs[i]:
                taille = 2; ajoute = True
            nouv = pos * taille
            if nouv != cur:
                for q in range(dq, mm):
                    pg[s, q] = cur; pi[s, q] = cur
                pg[s, mm] = cur; pi[s, mm] = nouv; dq = mm + 1; cur = nouv
        if cur != 0:
            for q in range(dq, 385):
                pg[s, q] = cur; pi[s, q] = cur
    return pg, pi


def principal():
    D = Dn.charger(recent=os.environ.get("NQ_RECENT") or None)
    P = Mo.deriver(D); J = D["J"]; ok = D["complete"].copy()
    i19 = np.where(J == "2026-11-19")[0]
    if len(i19):
        ok[i19[0]] = True
    O, H, L, C = P["O"], P["H"], P["L"], P["C"]
    base = Mo.k_supertrend(O, H, L, C, ok, 10, 3.0)
    t0 = k_st_renfort(O, H, L, C, ok, 10, 3.0, False, False)
    controle = bool(np.array_equal(base[0], t0[0]) and np.array_equal(base[1], t0[1]))
    idx = np.where(ok & (J >= "2015-01-01"))[0]; m = (J[idx] >= "2026-10-13") & (J[idx] <= "2026-11-19"); d23 = J[idx] >= "2023-01-01"
    V = {"Supertrend 10-3 (ton bot)": (False, False), "Supertrend + renfort (1 MNQ de plus a +1 ATR)": (True, False),
         "Supertrend + arret apres bougie folle (A2)": (False, True), "Supertrend + renfort + A2": (True, True)}
    res = {"controle_identique_au_supertrend": controle}
    G = {}
    for nom, (rf, a2) in V.items():
        pg, pi = k_st_renfort(O, H, L, C, ok, 10, 3.0, rf, a2)
        g, p, j = Pu.k_dollars_p(P["lg"], P["lb"], O, H, L, pg, pi, ok, 400.0, A.DOL, A.COUT, 2.0)
        G[nom] = (np.nan_to_num(g[idx]), np.nan_to_num(p[idx]), j[idx])
    g0 = G["Supertrend 10-3 (ton bot)"][0]
    G["Supertrend a 2 MNQ tout le temps"] = (2 * g0, 2 * G["Supertrend 10-3 (ton bot)"][1], G["Supertrend 10-3 (ton bot)"][2])
    for nom, (g, p, j) in G.items():
        rr = np.array([A.compte(g, p, j, i, 22) for i in range(len(idx) - 22)]); r23 = rr[d23[:len(rr)]]
        cum = np.cumsum(g); dif = g - g0
        res[nom] = dict(mois=round(float(g[m].sum())), par_an=round(float(g.mean()) * 252), par_an_2023=round(float(g[d23].mean()) * 252),
                        t=round(A.t_stat(g), 2), t_difference=round(A.t_stat(dif), 2), pire_baisse=round(float(np.min(cum - np.maximum.accumulate(cum)))),
                        retrait_22=round(float(np.mean(rr == 0)), 3), perdu_22=round(float(np.mean((rr == 1) | (rr == 2))), 3),
                        retrait_22_2023=round(float(np.mean(r23 == 0)), 3), perdu_22_2023=round(float(np.mean((r23 == 1) | (r23 == 2))), 3))
    d = ICI / "resultats" / "2026-11-20"; (d / "renfort_st.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(f"controle : {controle}")
    print(f"{'bot':48s} | mois | $/an 2015+ | $/an 2023+ | t | t ecart | pire baisse | 22 seances 2015+ : retrait / perdu | 2023+ : retrait / perdu")
    for nom, v in res.items():
        if nom.startswith("controle"):
            continue
        print(f"{nom:48s} | {v['mois']:+7,} | {v['par_an']:+7,} | {v['par_an_2023']:+7,} | {v['t']:+.2f} | {v['t_difference']:+.2f} | {v['pire_baisse']:+8,} | "
              f"{v['retrait_22']:.0%} / {v['perdu_22']:.0%} | {v['retrait_22_2023']:.0%} / {v['perdu_22_2023']:.0%}")


if __name__ == "__main__":
    principal()
