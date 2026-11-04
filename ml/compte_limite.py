#!/usr/bin/env python3
"""Bot XGBoost NQ, situation du compte au 4 novembre 2026 : solde 50 500 $, plus haut 51 000 $, plancher 48 500 $
(suiveur Option 1 sur le latent), objectif 53 000 $. Quelle limite du jour ? 1 ou 2 MNQ. Depart a chaque seance de 2023 a juin 2026,
memes trades que le dossier (moyenne des 10 modeles, marche en avant purgee), rejoues minute par minute."""
import json
import os

import numpy as np

import caracteristiques as K
import donnees as D

X = K.construire()
F, c, fut, sess, b, an, ok, J = (X[k] for k in ("F", "c", "fut", "sess", "b", "an", "ok", "J"))
F = F[:, :21]
_, O, H, L, C, V, _ = D.nq_minutes()
utile = ok[sess] & X["meme"] & np.isfinite(F).all(1) & np.isfinite(fut)
p = np.load(os.environ.get("CACHE_DOSSIER", "dossier_p.npy"))
sig = np.where(p > 0.55, 1, np.where(p < 0.45, -1, 0)) * (utile & (an >= 2014))
par = {}; libre = -1
for i in np.nonzero(sig)[0]:
    if i <= libre:
        continue
    s, bq, sens = sess[i], b[i], int(sig[i])
    m0, m1 = 15 * (bq + 1), 15 * (bq + 4) + 14
    e = O[s, m0]; ech = 2 * D.PREF / e; ext = []
    for q in range(4):
        a, z = m0 + 15 * q, min(m0 + 15 * q + 14, m1)
        lo, hi = L[s, a:z + 1].min(), H[s, a:z + 1].max()
        ext.append((((lo if sens > 0 else hi) - e) * sens * ech, ((hi if sens > 0 else lo) - e) * sens * ech))
    par.setdefault(s, []).append((sens * (C[s, m1] - e) * ech - D.FRAIS, ext)); libre = i + 3


def challenge(debut, limite, taille=1, solde=50500.0, haut=51000.0, cible=53000.0):
    for n, s in enumerate([s for s in range(len(J)) if ok[s] and s >= debut]):
        jour = 0.0
        for res, ext in par.get(s, []):
            if jour <= -limite:
                break
            res = res * taille
            for pire, meil in ext:
                pire, meil = pire * taille, meil * taille
                if jour + pire <= -limite:                     # la limite coupe aussi le trade en cours (comme le bot)
                    res = -limite - jour; break
                haut = max(haut, solde + meil)
                if solde + pire <= min(haut - 2500, 50100):
                    return "echec", n + 1
            solde += res; jour += res; haut = max(haut, solde)
            if solde >= cible:
                return "reussite", n + 1
    return "en cours", 0


departs = [s for s in range(len(J)) if ok[s] and "2023-01-01" <= J[s] <= "2026-06-30"]
res = {}
for taille in (1, 2):
    for lim in (300, 400, 500, 600, 800, 2000):
        iss = [challenge(d, float(lim), taille) for d in departs]
        r = [x[0] for x in iss]; dur = [x[1] for x in iss if x[0] == "reussite"]
        res[f"{taille}|{lim}"] = dict(taille=taille, limite=lim, reussite=r.count("reussite") / len(r), echec=r.count("echec") / len(r),
                                      seances=float(np.median(dur)) if dur else None)
        print(taille, lim, res[f"{taille}|{lim}"], flush=True)
json.dump(res, open(D.SORTIE / "compte_limite.json", "w"))
txt = ["# Bot XGBoost NQ : quelle limite du jour pour le compte à 50 500 $ (plancher 48 500 $, objectif 53 000 $) ?\n",
       f"Départ à chacune des {len(departs)} séances de janvier 2023 à juin 2026, plancher suiveur sur le latent (Option 1). La limite coupe aussi le trade en cours.\n",
       "| MNQ | limite du jour | objectif atteint | plancher touché | séances pour réussir (médiane) |", "|---|---|---|---|---|"]
for r in res.values():
    lim = r["limite"]
    txt.append(f"| {r['taille']} | {'aucune (toute la marge)' if lim == 2000 else f'{lim} $'} | {r['reussite']:.0%} | {r['echec']:.0%} | {r['seances'] or '—'} |")
D.ecrire("compte_limite.md", "\n".join(txt) + "\n")
