#!/usr/bin/env python3
"""Vague 12 (README.md) : version du bot pour un challenge de 30 jours (taille 1 a 4 en challenge, retour a 1 au Master),
Bulenox Legacy et Momentum, comparee a Goat EOD et FundedNext Flex (sans limite de temps). Chaque seance comme jour
d'achat (une sur deux pour les comptes sans limite), 21 tirages du filtre. Ecrit vague12.json et vague12.txt."""
import json
import multiprocessing as mp
import sys
import time

import numpy as np

import regles12 as K

P = K.MC.preparer()
D0, D1, LIM, GROUPES = K.achats(P)
NJ = len(P["jours"])
CAND = K.candidates()
CHOIX_FIN, CHOIX_SUIVI = GROUPES["choix 2012-2021"][1], GROUPES["choix 2012-2021"][2]
VERIF_DEB = GROUPES["verification 2023 - aout 2026"][0]
FILTRES = {"fort": 10, "moitie": 10, "aucun": 1}


def jours_achat(compte):
    pas = 1 if K.COMPTES[compte]["trente"] else 2
    dd = [d for d in range(D0, D1, pas) if d < CHOIX_FIN or d >= VERIF_DEB]
    return np.array(dd, np.int64)


def tache(args):
    ic, fil, t = args
    nom, compte, q, c_ch, c_f = CAND[ic]
    A = K.COMPTES[compte]
    b = P["bases"][fil][t]
    dd = jours_achat(compte)
    out = np.full((len(dd), 8), np.nan)
    for k, d in enumerate(dd):
        sv = min(K.H, (CHOIX_SUIVI if d < CHOIX_FIN else NJ) - d)
        r, ret = K.un_achat(P, b, int(d), compte, q, c_ch, c_f, sv, LIM[d])
        net = ret[:K.H].sum() * A["part"] - A["prix"] - (A["activation"] if r[0] == 1 else 0.0) if sv >= K.H else np.nan
        perdu12 = (float(bool(r[2]) and r[6] - r[1] <= 252) if r[0] == 1 and sv - r[1] >= 252 else np.nan)
        out[k] = (d, r[0], r[1], perdu12, float(ret[:K.H].sum() > 0) if sv >= K.H else np.nan, net, r[3], sv)
    return ic, fil, t, out


def resumer(R):
    """R[ic][fil] : tableau (achats de tous les tirages) -> mesures par groupe."""
    res = {}
    for ic, (nom, compte, q, c_ch, c_f) in enumerate(CAND):
        res[nom] = {}
        for fil in FILTRES:
            x = R[ic][fil]
            res[nom][fil] = {}
            for g, (a, z, _) in GROUPES.items():
                m = (x[:, 0] >= a) & (x[:, 0] < z)
                y = x[m]
                iss = y[:, 1]
                val = iss == 1
                full = ~np.isnan(y[:, 5])
                p12 = y[val, 3]
                p12 = p12[~np.isnan(p12)]
                res[nom][fil][g] = dict(
                    achats=int(m.sum()), valide=float(np.mean(val)), perdu=float(np.mean(iss == -1)),
                    expire=float(np.mean(iss == 0)), seances_med=float(np.median(y[val, 2])) if val.any() else None,
                    suivis24=int(full.sum()),
                    retrait24=float(np.mean(y[full, 4])) if full.any() else None,
                    net_moy=float(np.mean(y[full, 5])) if full.any() else None,
                    net_med=float(np.median(y[full, 5])) if full.any() else None,
                    perdants=float(np.mean(y[full, 5] < 0)) if full.any() else None,
                    master_perdu12=float(np.mean(p12)) if len(p12) else None)
    return res


def main():
    t0 = time.time()
    taches = [(ic, fil, t) for ic in range(len(CAND)) for fil, n in FILTRES.items() for t in range(n)]
    R = {ic: {fil: [] for fil in FILTRES} for ic in range(len(CAND))}
    with mp.get_context("fork").Pool(4) as pool:
        for k, (ic, fil, t, out) in enumerate(pool.imap_unordered(tache, taches)):
            R[ic][fil].append(out)
            if k % 25 == 0:
                print(f"{k + 1}/{len(taches)} taches, {time.time() - t0:.0f} s", flush=True)
    R = {ic: {fil: np.vstack(v) for fil, v in d.items()} for ic, d in R.items()}
    res = resumer(R)
    (K.ICI / "vague12.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(f"fini en {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
