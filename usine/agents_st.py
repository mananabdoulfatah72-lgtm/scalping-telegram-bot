#!/usr/bin/env python3
"""Le bureau de 6 agents traduit en 3 regles ajoutees au Supertrend 10-3 (usine/REGLES.md, fixe le 20 novembre 2026).
A1 risque (stop ramene a l'entree apres 1 ATR de gain), A2 actualites (arret du jour apres une bougie de plus de 3 ATR),
A3 sortie (des qu'une cloture recule de 1 ATR depuis la meilleure cloture du trade), A123 les trois.
Usage : KB_MINUTES=<nasdaq100_1min.csv.gz> [NQ_RECENT=<nq_1min.csv.gz>] python3 usine/agents_st.py
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

N = Mo.N
PRIX = 26675.0                      # NQ du 19 novembre 2026
DOL, COUT = 2 * PRIX, 1.5 / (2 * PRIX)


@njit(cache=True)
def k_st_agents(O, H, L, C, ok, per, mult, a1, a2, a3):
    S = C.shape[0]; nb = S * 78
    h5 = np.empty(nb); l5 = np.empty(nb); c5 = np.empty(nb)
    for s in range(S):
        for b in range(78):
            hh = H[s, 5 * b]; ll = L[s, 5 * b]
            for q in range(1, 5):
                hh = max(hh, H[s, 5 * b + q]); ll = min(ll, L[s, 5 * b + q])
            h5[s * 78 + b] = hh; l5[s * 78 + b] = ll; c5[s * 78 + b] = C[s, 5 * b + 4]
    st = np.zeros(nb); atrs = np.zeros(nb); atr = 0.0; hb = np.nan; lb = np.nan; dr = 1.0
    for i in range(1, nb):                                   # identique a moteur.k_supertrend
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
        pos = 0; m_in = -1; bloque = 0; arret = False; entree = 0.0; meilleure = 0.0; arme = False
        for bb in range(76):
            i = s * 78 + bb
            v = st[i]
            cible = pos if v == 0 else int(v)
            if a2 and bb > 0 and (h5[i] - l5[i]) > 3.0 * atrs[i - 1]:
                arret = True
            sortie = False
            if pos != 0 and cible == pos:
                c = c5[i]
                if pos > 0:
                    meilleure = max(meilleure, c)
                else:
                    meilleure = min(meilleure, c)
                if a3 and pos * (meilleure - c) >= atrs[i]:
                    sortie = True
                if a1:
                    if pos * (c - entree) >= atrs[i]:
                        arme = True
                    if arme and pos * (c - entree) <= 0:
                        sortie = True
            if sortie:
                bloque = pos; cible = 0
            if bloque != 0:
                if v != 0 and int(v) != bloque:
                    bloque = 0
                else:
                    cible = 0
            if arret:
                cible = 0
            mm = 5 * bb + 5
            if cible != pos and pos != 0:
                for q in range(m_in + 1, mm):
                    pg[s, q] = pos; pi[s, q] = pos
                pg[s, mm] = pos
                pos = 0
            if cible != 0 and pos == 0 and mm <= 360:
                pos = cible; m_in = mm; pi[s, mm] = pos
                entree = O[s, mm]; meilleure = entree; arme = False
        if pos != 0:
            for q in range(m_in + 1, 385):
                pg[s, q] = pos; pi[s, q] = pos
    return pg, pi


def t_stat(x):
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else 0.0


def compte(g, p, j, d0, n, solde=52000.0, pl=50100.0, retrait=53600.0):
    sans = 0
    for q in range(n):
        d = d0 + q
        if solde + p[d] <= pl:
            return 1
        solde += g[d]; sans = 0 if j[d] else sans + 1
        if sans >= 5:
            return 2
        if solde >= retrait:
            return 0
    return 3


def principal():
    D = Dn.charger(recent=os.environ.get("NQ_RECENT") or None)
    P = Mo.deriver(D); J = D["J"]; ok = D["complete"]
    base = Mo.k_supertrend(P["O"], P["H"], P["L"], P["C"], ok, 10, 3.0)
    a0 = k_st_agents(P["O"], P["H"], P["L"], P["C"], ok, 10, 3.0, False, False, False)
    controle = bool(np.array_equal(base[0], a0[0]) and np.array_equal(base[1], a0[1]))
    variantes = {"Supertrend seul": (False, False, False), "A1 risque": (True, False, False), "A2 actualites": (False, True, False),
                 "A3 sortie": (False, False, True), "A123": (True, True, True)}
    idx = np.where(ok & (J >= "2015-01-01"))[0]; d23 = J[idx] >= "2023-01-01"
    res, R = {}, {"controle_identique_au_supertrend": controle, "variantes": {}}
    for nom, (x1, x2, x3) in variantes.items():
        pg, pi = k_st_agents(P["O"], P["H"], P["L"], P["C"], ok, 10, 3.0, x1, x2, x3)
        g, p, j = Pu.k_dollars_p(P["lg"], P["lb"], P["O"], P["H"], P["L"], pg, pi, ok, 400.0, DOL, COUT, 2.0)
        res[nom] = (g[idx], p[idx], j[idx])
    g0 = res["Supertrend seul"][0]
    for nom, (g, p, j) in res.items():
        d = g - g0
        rr = np.array([compte(g, p, j, i, 22) for i in range(len(idx) - 22)])
        cum = np.cumsum(g)
        R["variantes"][nom] = dict(par_seance=round(float(g.mean()), 1), par_seance_2023=round(float(g[d23].mean()), 1),
                                   t=round(t_stat(g), 2), difference_par_an=round(float(d.mean()) * 252), t_difference=round(t_stat(d), 2),
                                   difference_2023_par_an=round(float(d[d23].mean()) * 252), retrait_22=round(float(np.mean(rr == 0)), 3),
                                   perdu_22=round(float(np.mean((rr == 1) | (rr == 2))), 3), pire_baisse=round(float(np.min(cum - np.maximum.accumulate(cum)))),
                                   seances_tradees=round(float(j.mean()), 2))
    b = R["variantes"]["Supertrend seul"]
    for nom, v in R["variantes"].items():
        if nom == "Supertrend seul":
            continue
        v["retenue"] = bool(v["difference_par_an"] > 0 and v["t_difference"] >= 1.65 and v["difference_2023_par_an"] > 0
                            and v["perdu_22"] < b["perdu_22"] and v["retrait_22"] >= b["retrait_22"])
    d = ICI / "resultats" / "2026-11-20"; d.mkdir(parents=True, exist_ok=True)
    (d / "agents_st.json").write_text(json.dumps(R, indent=1, ensure_ascii=False))
    print(f"controle (aucune regle = Supertrend du moteur) : {controle}")
    for nom, v in R["variantes"].items():
        print(f"{nom:16s} {v['par_seance']:+6.1f} $/seance (2023+ {v['par_seance_2023']:+6.1f}) t {v['t']:+.2f} | difference {v['difference_par_an']:+6,} $/an "
              f"(t {v['t_difference']:+.2f}, 2023+ {v['difference_2023_par_an']:+,}) | 22 seances : retrait {v['retrait_22']:.0%}, perdu {v['perdu_22']:.0%} "
              f"| pire baisse {v['pire_baisse']:+,} | {'RETENUE' if v.get('retenue') else ''}")


if __name__ == "__main__":
    principal()
