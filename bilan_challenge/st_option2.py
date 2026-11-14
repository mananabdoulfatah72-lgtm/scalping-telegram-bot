"""Supertrend 10-3, 1 MNQ, sur le Master de l'utilisateur en OPTION 2 (plancher = plus haut solde de FIN DE JOURNEE
- 2 500 $, fixe pendant la seance, bloque a 50 100 $ ; perdu si la valeur du compte le touche pendant la seance).
Depart 51 000 $, plancher 49 200 $ (plus haut de fin de journee 51 700 $), 1er retrait possible a 53 600 $.
Question : faut-il baisser la limite de perte du jour sous 400 $ ? Et une garde du plancher protege-t-elle mieux ?"""
import numpy as np
import pandas as pd

import st_detail as X

J, T, nj, sim = X.J, X.T, X.nj, X.sim
PRIS = np.ones(len(T), np.bool_)
LIMS = (150, 200, 250, 300, 400, 500, 600, 800, 0)


def journee(dd, lim):
    jv, arret, coupe = 0.0, False, False
    for i in range(X.jd[dd], X.jf[dd]):
        if arret:
            break
        s, me, mx, e, sortie = int(T[i, 1]), int(T[i, 2]), int(T[i, 3]), T[i, 4], T[i, 5]
        k = 28500.0 / e
        for mm in range(me + 1, mx + 1):
            o, adv = X.O[dd, mm], (X.L[dd, mm] if s > 0 else X.H[dd, mm])
            if lim and jv + (2 * s * (adv - e) * k - 3.0) <= -lim:
                niv = e + s * ((-lim - jv) + 3.0) / (2 * k)
                sortie = (min(o, niv) - 1.0) if s > 0 else (max(o, niv) + 1.0); arret = coupe = True
                break
        jv += 2 * s * (sortie - e) * k - 3.0
    return jv, coupe


ok = [dd for dd in range(nj) if X.complete[dd]]
print("A. 15 ans, 1 MNQ (gains au prix d'aujourd'hui) : par seance (t) | depuis 2023 | pire seance | plus longue serie perdante | "
      "pire serie | plus forte baisse | seances coupees par la limite")
for lim in LIMS:
    R = [journee(dd, lim) for dd in ok]; s = np.array([r[0] for r in R])
    r23 = np.array([v for dd, v in zip(ok, s) if J[dd] >= "2023-01-01"]); cum = np.cumsum(s)
    best = serie = 0; somme = pire = 0.0
    for v in s:
        if v < 0:
            serie += 1; somme += v
        elif v > 0:
            serie = 0; somme = 0.0
        best = max(best, serie); pire = min(pire, somme)
    print(f"  limite {lim or 'aucune':>6} : {s.mean():+5.1f} $ (t {s.mean() / s.std() * np.sqrt(len(s)):.2f}) | {r23.mean():+5.1f} $ | {s.min():+6,.0f} $ | "
          f"{best:2d} | {pire:+7,.0f} $ | {(cum - np.maximum.accumulate(cum)).min():+8,.0f} $ | {np.mean([r[1] for r in R]) * 100:4.1f} %")

print("\nB. Master en Option 2 : 51 000 $ / plancher 49 200 $ -> 53 600 $ ? atteint / perdu / ni l'un ni l'autre (%) ; 1 MNQ")
for a0 in ("2011", "2023"):
    for ns in (22, 66, 250):
        deb = [i for i in range(nj) if J[i] >= a0 and X.complete[i] and i + ns <= nj]
        ligne = []
        for lim, g in [(l, 0) for l in LIMS] + [(400, 150)]:
            p = X.prm(1, lim if lim else 1e9); p[12] = 1; p[2] = g
            R = [sim.fenetre(i, ns, p, 51000.0, 51700.0, *X.ARGS, PRIS, 53550.0, 2500.0, 50100.0, 0) for i in deb]
            iss = np.array([r[0] for r in R])
            nom = f"{lim or 'aucune'}" + (" + garde" if g else "")
            ligne.append(f"{nom} {(iss == 1).mean() * 100:.0f}/{(iss == -1).mean() * 100:.0f}/{(iss == 0).mean() * 100:.0f}")
        print(f"  departs {a0}+, {ns:3d} seances : " + " | ".join(ligne))

# C. exemples concrets du mois du challenge (moteur C#, vrais prix), heure de New York
c = pd.read_csv(X.S / "rejeu/supertrend_propre.csv")
for j in ("2026-11-05", "2026-10-13", "2026-11-10"):
    print(f"\nC. {j} :")
    for r in c[c.jour == j].itertuples():
        h = lambda m: f"{9 + (30 + m) // 60}h{(30 + m) % 60:02d}"
        print(f"   {'achat' if r.sens > 0 else 'vente'} a {h(r.m_in)} a {r.entree:,.2f}, sortie a {h(r.m_out)} a {r.sortie:,.2f} : "
              f"{r.sens * (r.sortie - r.entree):+.2f} points = {2 * r.sens * (r.sortie - r.entree) - 3:+,.0f} $ a 1 MNQ")
