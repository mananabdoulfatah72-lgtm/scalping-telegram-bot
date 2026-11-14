"""Supertrend 10-3, 1 MNQ, limite de perte du jour 400 $, avec un plafond de gain du jour (regle fixee avant le calcul,
voir bilan_challenge/SUPERTREND.md) : a la cloture de chaque minute, si le resultat du jour (realise + latent, frais
compris) atteint le plafond, la position est fermee au prix de cloture et plus rien ce jour-la."""
import numpy as np

import st_detail as X

J, T, nj, sim = X.J, X.T, X.nj, X.sim
PRIS = np.ones(len(T), np.bool_)
CAPS = (0, 300, 500, 800, 1200, 2000)


def journee(dd, t, lim, cap, reel=False):
    jv, arret, plaf = 0.0, False, False
    for i in range(X.jd[dd], X.jf[dd]):
        if arret:
            break
        s, me, mx, e, sortie = int(T[i, 1]), int(T[i, 2]), int(T[i, 3]), T[i, 4], T[i, 5]
        k = 1.0 if reel else 28500.0 / e
        for mm in range(me + 1, mx + 1):
            o, adv, cc = X.O[dd, mm], (X.L[dd, mm] if s > 0 else X.H[dd, mm]), X.C[dd, mm]
            if lim and jv + t * (2 * s * (adv - e) * k - 3.0) <= -lim:
                niv = e + s * ((-lim - jv) / t + 3.0) / (2 * k)
                sortie = (min(o, niv) - 1.0) if s > 0 else (max(o, niv) + 1.0); arret = True
                break
            if cap and jv + t * (2 * s * (cc - e) * k - 3.0) >= cap:
                sortie = cc; arret = plaf = True
                break
        jv += t * (2 * s * (sortie - e) * k - 3.0)
        if cap and jv >= cap:
            arret = plaf = True
    return jv, plaf


ok = [dd for dd in range(nj) if X.complete[dd]]
print("A. 15 ans, 1 MNQ, limite de perte 400 $ : $/seance (t) | depuis 2023 | meilleure seance | pire serie | plus forte baisse | seances plafonnees")
for cap in CAPS:
    R = [journee(dd, 1, 400, cap) for dd in ok]
    s = np.array([r[0] for r in R]); r23 = np.array([v for dd, v in zip(ok, s) if J[dd] >= "2023-01-01"])
    cum = np.cumsum(s); serie = pire = 0.0
    for v in s:
        serie = serie + v if v < 0 else (0.0 if v > 0 else serie); pire = min(pire, serie)
    print(f"  plafond {cap or 'aucun':>5} : {s.mean():+5.1f} $ (t {s.mean() / s.std() * np.sqrt(len(s)):.2f}) | {r23.mean():+5.1f} $ (t {r23.mean() / r23.std() * np.sqrt(len(r23)):.2f})"
          f" | {s.max():+6,.0f} $ | {pire:+7,.0f} $ | {(cum - np.maximum.accumulate(cum)).min():+8,.0f} $ | {np.mean([r[1] for r in R]) * 100:4.1f} %")
d0 = int(np.searchsorted(J, "2026-10-13"))
print("  mois du challenge (13 oct. -> 13 nov., vrais $) : " + " ; ".join(
    f"plafond {cap or 'aucun'} {sum(journee(dd, 1, 400, cap, True)[0] for dd in range(d0, nj)):+,.0f} $" for cap in CAPS))

print("\nB. Master : 51 000 $, plancher 49 200 $ (Option 1) -> 53 600 $ avant le plancher ? atteint / perdu / ni l'un ni l'autre (%)")
for a0 in ("2011", "2023"):
    for ns in (66, 250):
        deb = [i for i in range(nj) if J[i] >= a0 and X.complete[i] and i + ns <= nj]
        ligne = []
        for cap in CAPS:
            p = X.prm(1, 400); p[9] = cap
            iss = np.array([sim.fenetre(i, ns, p, 51000.0, 51700.0, *X.ARGS, PRIS, 53550.0, 2500.0, 50100.0, 0)[0] for i in deb])
            ligne.append(f"{cap or 'aucun'} : {(iss == 1).mean() * 100:3.0f}/{(iss == -1).mean() * 100:3.0f}/{(iss == 0).mean() * 100:3.0f}")
        print(f"  departs {a0}+, {ns} seances : " + " | ".join(ligne))
