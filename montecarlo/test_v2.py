#!/usr/bin/env python3
"""Controles du Monte Carlo v2 (README.md). Lancer depuis ce dossier : python3 test_v2.py.
1. Le moteur journalier (tables exactes) redonne le moteur minute par minute (moteur_mc.parcours_mc) sur des chemins
   tires au hasard : memes issues, memes seances, memes retraits, pour plusieurs reglages (frein, plafond, filtre).
2. Ecrit vecteurs_test.json : des chemins et leurs sorties, pour controler le port JavaScript (test_js.mjs)."""
import json

import numpy as np

import montecarlo as MC
import moteur_jour as MJ

B = MC.B


def regles(c_mnq, cap):
    E, F = B.E, B.F
    return dict(e_obj=E[0], e_perte=E[1], e_bloc=E[3], f_perte=F[0], f_bloc=F[1], f_jours=int(F[3]), f_regul=F[5],
                f_min=F[6], f_plaf=float(F[7][0]), f_reserve=F[9], f_max=int(F[10]), c_mnq=c_mnq, cap=cap)


def jour(idx, T, t, R, j0):
    ret = np.zeros(MC.H)
    lig = (idx - j0).astype(np.int64)
    ci = {0.0: 0, 500.0: 1, 750.0: 2}[R["cap"]]
    r = MJ.parcours_jour(lig, T["gain"][t], T["pire"][t], T["drap"][t], ci, R["c_mnq"], R["e_obj"], R["e_perte"],
                         R["e_bloc"], R["f_perte"], R["f_bloc"], R["f_jours"], R["f_regul"], R["f_min"], R["f_plaf"],
                         R["f_reserve"], R["f_max"], ret)
    return r, ret


def exact(idx, b, R, P):
    ret, so, pl, ph = np.zeros(MC.H), np.zeros(MC.H), np.zeros(MC.H), np.zeros(MC.H, np.int64)
    r = MC.MM.parcours_mc(idx, 4, P["kN"], P["kE"], ret, so, pl, ph, *b, *B.E, *B.F, R["c_mnq"], R["cap"])
    return r, ret


def main():
    P = MC.preparer()
    z = np.load("tables.npz")
    T = {k: z[k] for k in ("gain", "pire", "drap")}
    j0 = int(z["seances"][0])
    tir = list(z["tirages"])
    rng = np.random.default_rng(11)
    n_ok = n_tot = 0
    ecarts = []
    vecteurs = []
    for c_mnq, cap in ((1750.0, 500.0), (0.0, 0.0), (2000.0, 750.0), (1250.0, 0.0)):
        R = regles(c_mnq, cap)
        for t, nom in enumerate(tir):
            fil, i = nom.split(":")
            b = P["bases"][fil][int(i)]
            for _ in range(60):
                idx = MC.tirer_chemin(rng, P["pools"]["tout"])
                r1, ret1 = jour(idx, T, t, R, j0)
                r2, ret2 = exact(idx, b, R, P)
                same = (tuple(int(x) for x in (r1[0], r1[1], r1[2], r1[3], r1[5], r1[6])) ==
                        tuple(int(x) for x in (r2[0], r2[1], r2[2], r2[3], r2[5], r2[6]))
                        and np.allclose(ret1, ret2, atol=1e-6))
                n_tot += 1
                n_ok += same
                if not same:
                    ecarts.append((c_mnq, cap, nom, r1, r2))
                if len(vecteurs) < 600 and rng.random() < 0.12:
                    vecteurs.append({"t": t, "lignes": (idx - j0).tolist(), "regles": R,
                                     "r": [float(x) for x in r1], "ret": [[int(s), float(ret1[s])] for s in np.flatnonzero(ret1)]})
    print(f"moteur journalier = moteur minute par minute : {n_ok} / {n_tot} achats identiques")
    for e in ecarts[:5]:
        print("ecart", e)
    assert n_ok >= 0.999 * n_tot
    (MC.ICI / "vecteurs_test.json").write_text(json.dumps(vecteurs))
    (MC.ICI / "controle_v2.json").write_text(json.dumps({"identiques": int(n_ok), "total": int(n_tot)}))
    print(f"ok : {len(vecteurs)} vecteurs de test ecrits pour le port JavaScript")


if __name__ == "__main__":
    main()
