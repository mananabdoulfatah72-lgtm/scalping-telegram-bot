"""Supertrend 10-3 sur le compte Master Bulenox de l'utilisateur : solde 51 000 $, plancher 49 200 $ (plus haut 51 700 $).
Seuil du 1er retrait : 53 600 $ (garder 52 600 $ + retrait de 1 000 $ au moins, contrat du 23 octobre 2026)."""
import numpy as np
import pandas as pd

import st_detail as X

J, T, nj, sim = X.J, X.T, X.nj, X.sim
PRIS = np.ones(len(T), np.bool_)


def journee(dd, t, lim, reel=False):
    jv, arret = 0.0, False
    for i in range(X.jd[dd], X.jf[dd]):
        if arret:
            break
        s, me, mx, e, sortie = int(T[i, 1]), int(T[i, 2]), int(T[i, 3]), T[i, 4], T[i, 5]
        k = 1.0 if reel else 28500.0 / e
        for mm in range(me + 1, mx + 1):
            o, adv = X.O[dd, mm], (X.L[dd, mm] if s > 0 else X.H[dd, mm])
            if lim and jv + t * (2 * s * (adv - e) * k - 3.0) <= -lim:
                niv = e + s * ((-lim - jv) / t + 3.0) / (2 * k)
                sortie = (min(o, niv) - 1.0) if s > 0 else (max(o, niv) + 1.0); arret = True
                break
        jv += t * (2 * s * (sortie - e) * k - 3.0)
    return jv


def stats(s):
    cum = np.cumsum(s); best = serie = 0; somme = pire = 0.0
    for v in s:
        if v < 0:
            serie += 1; somme += v
        elif v > 0:
            serie = 0; somme = 0.0
        best = max(best, serie); pire = min(pire, somme)
    return s.mean(), s.mean() / s.std() * np.sqrt(len(s)), s.min(), best, pire, (cum - np.maximum.accumulate(cum)).min()


# A. ce que fait la limite du jour, sur 15 ans et depuis 2023 (1 MNQ, gains au prix d'aujourd'hui)
ok = [dd for dd in range(nj) if X.complete[dd]]
print("A. 1 MNQ, 15 ans (3 952 seances) | depuis 2023 : $/seance, t, pire seance, plus longue serie perdante, pire serie, plus forte baisse")
DJ = {}
for lim in (0, 300, 400, 600, 800):
    s = np.array([journee(dd, 1, lim) for dd in ok]); DJ[lim] = s
    r = np.array([v for dd, v in zip(ok, s) if J[dd] >= "2023-01-01"])
    a, b = stats(s), stats(r)
    print(f"  limite {lim or 'aucune':>6} : {a[0]:+5.1f} $ t {a[1]:.2f}, pire {a[2]:+6,.0f} $, serie {a[3]}, pire serie {a[4]:+7,.0f} $, baisse {a[5]:+8,.0f} $"
          f" | {b[0]:+5.1f} $ t {b[1]:.2f}, pire {b[2]:+6,.0f} $, pire serie {b[4]:+7,.0f} $, baisse {b[5]:+8,.0f} $")
d0 = int(np.searchsorted(J, "2026-10-13"))
for lim in (0, 400):
    s = np.array([journee(dd, 1, lim, True) for dd in range(d0, nj)]); st = stats(s)
    print(f"  periode 13 oct. -> 13 nov., vrais $, limite {lim or 'aucune'} : total {s.sum():+,.0f} $, pire seance {st[2]:+,.0f} $, "
          f"pire serie {st[4]:+,.0f} $, plus forte baisse {st[5]:+,.0f} $, seances a la limite {(s <= -400).sum() if lim else 0}")

# B. le Master depuis 51 000 $ / plancher 49 200 $ : 1er retrait possible (53 600 $) avant le plancher ?
print("\nB. Master : solde 51 000 $, plancher 49 200 $ -> 53 600 $ (1er retrait) avant le plancher ? reussi / perdu / ni l'un ni l'autre, seances (mediane)")
for regle, eod in (("plancher suivi en temps reel (Option 1)", 0), ("plancher suivi en fin de journee", 1)):
    for a0 in ("2011", "2023"):
        for ns in (22, 66, 250):
            deb = [i for i in range(nj) if J[i] >= a0 and X.complete[i] and i + ns <= nj]
            if len(deb) < 50:
                continue
            ligne = []
            for t, lim in ((1, 400), (1, 1e9), (1, 300), (2, 800)):
                p = X.prm(t, lim); p[12] = eod
                R = [sim.fenetre(i, ns, p, 51000.0, 51700.0, *X.ARGS, PRIS, 53550.0, 2500.0, 50100.0, 0) for i in deb]
                iss = np.array([r[0] for r in R]); q = np.array([r[2] for r in R])
                med = np.median(q[iss == 1]) + 1 if (iss == 1).any() else float("nan")
                ligne.append(f"{t} MNQ/{'aucune' if lim > 1e8 else int(lim)} {(iss == 1).mean() * 100:3.0f}/{(iss == -1).mean() * 100:3.0f}/{(iss == 0).mean() * 100:3.0f} ({med:.0f})")
            print(f"  {regle}, departs {a0}+, {ns} seances ({len(deb)} departs) : " + " | ".join(ligne))

# C. regle des 40 % (meilleure journee <= 40 % du gain depuis le debut du Master, ici 50 000 $), 1 MNQ / 400, jour par jour
s400 = dict(zip(ok, DJ[400])); att = []; retard = []
for i in [i for i in ok if i + 250 <= nj]:
    solde, best, n = 51000.0, 0.0, 0
    for dd in range(i, i + 250):
        g = s400.get(dd, 0.0); solde += g; best = max(best, g); n += 1
        if solde <= 49200:
            break
        if solde >= 53600:
            att.append(best <= 0.4 * (solde - 50000))
            k = dd
            while k < i + 250 and solde >= 53600 and best > 0.4 * (solde - 50000):
                k += 1; g = s400.get(k, 0.0); solde += g; best = max(best, g)
            retard.append(k - dd)
            break
att = np.array(att)
print(f"\nC. Regle des 40 % au moment d'atteindre 53 600 $ (1 MNQ / 400, fin de journee) : retrait permis tout de suite dans {att.mean() * 100:.0f} % des cas ; "
      f"sinon {np.median([r for r, a in zip(retard, att) if not a]) if (~att).any() else 0:.0f} seances de plus en mediane")
