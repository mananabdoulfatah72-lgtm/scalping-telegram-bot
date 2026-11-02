#!/usr/bin/env python3
"""Descriptif apres le coffre (pas un test) : plateau autour du champion (6 MNQ, garde en temps reel 350 $) et regle
manuelle equivalente (limite du jour = solde - plancher - marge, recalculee chaque matin)."""
import numpy as np
import base as B
import machine as M

deb = np.concatenate([M.PER[k] for k in ("ent", "tou", "cof")])
def ligne(nom, **kw):
    out = []
    for k, d in (("2011-19", M.PER["ent"]), ("2020-23", M.PER["tou"]), ("2024-26", M.PER["cof"])):
        r, e, x, n, bl = B.issues(B.prm(**kw), d)
        out.append(f"{k} {r:4.1f} / {e:4.1f}")
    return f"{nom:34s} " + "   ".join(out)
L = ["Reussis / echoues (%), depart 50 000 $, plancher 49 000 $, 8 seances, drawdown suiveur en temps reel", ""]
L.append("Garde en temps reel, 6 MNQ, limite 1 000 $ :")
for gc in (0, 200, 350, 500, 700):
    L.append(ligne(f"  marge {gc} $", T=6, L=1000, GC=gc))
L.append("Garde en temps reel 350 $, limite 1 000 $ :")
for t in (2, 3, 4, 5, 6):
    L.append(ligne(f"  {t} MNQ", T=t, L=1000, GC=350))
L.append("Regle manuelle (limite du jour = solde - plancher - marge, chaque matin), 6 MNQ :")
for g in (150, 300, 350, 500):
    L.append(ligne(f"  marge {g} $", T=6, L=1000, G=g))
L.append("Limite fixe, 6 MNQ, sans garde :")
for l in (500, 650, 800, 1000):
    L.append(ligne(f"  limite {l} $", T=6, L=l))
open("resultats/plateau.txt", "w").write("\n".join(L) + "\n")
print("\n".join(L))
