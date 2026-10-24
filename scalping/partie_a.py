#!/usr/bin/env python3
"""Partie A (README.md) : les 6 regles des etudes, sur NQ et ES, exploration 2017-2022, 40 jumeaux de bruit,
Benjamini-Hochberg a 10 % sur les 12 tests. Ecrit resultats/partie_a.json et resultats/partie_a.txt."""
import json
import multiprocessing as mp
from math import erf, sqrt

import numpy as np

import bruit as B
import commun as K
import donnees as D
import machine as MA
import moteur as M

REGLES = {10: "A1 retournement apres une grande ouverture (Grant, Wolf, Yu)", 11: "A2 minute extreme, contre 1 minute",
          12: "A3 saut de 10 h 00, suivi de 10 h 01 a 10 h 02", 13: "A4 mouvement de 10 minutes extreme, contre 10 minutes",
          14: "A5a niveau rond, rebond (ordre limite)", 15: "A5b niveau rond, cassure"}
JUMEAUX = 40
GRAINE = 2000


def mesures(f, s0, s1):
    out = {}
    for fam in REGLES:
        g = np.zeros(M.NG)
        g[M.FAM] = fam
        gain, n, w, brut, _ = M.jouer(g, f, s0, s1)
        x = gain[np.isfinite(gain)]
        out[fam] = dict(t=K.t_stat(x), trades=int(n), net_trade=float(np.nansum(gain) / max(n, 1)),
                        brut_trade=float(brut / max(n, 1)), gagnants=float(w / max(n, 1)), total=float(np.nansum(gain)))
    return out


def jumeau(k):
    q = dict(np.load(K.CACHE / "recherche_NQ.npz"))
    e = dict(np.load(K.CACHE / "recherche_ES.npz"))
    q, e = B.bruiter_paire(q, e, GRAINE + k)
    res = {}
    for nom, d in (("NQ", q), ("ES", e)):
        s0, _, s1 = MA.bornes(d["jours"])
        res[nom] = {fam: v["t"] for fam, v in mesures(M.indicateurs(d), s0, s1).items()}
    return res


def main():
    reel = {}
    for nom in ("NQ", "ES"):
        d = dict(np.load(K.CACHE / f"recherche_{nom}.npz"))
        assert d["jours"].max() <= K.FIN_RECHERCHE
        s0, _, s1 = MA.bornes(d["jours"])
        reel[nom] = mesures(M.indicateurs(d), s0, s1)
    with mp.get_context("fork").Pool(4) as pool:
        bruits = pool.map(jumeau, range(1, JUMEAUX + 1))
    tests = []
    for nom in ("NQ", "ES"):
        for fam, v in reel[nom].items():
            tb = np.array([b[nom][fam] for b in bruits])
            p = 0.5 * (1 - erf(v["t"] / sqrt(2)))
            tests.append(dict(marche=nom, regle=fam, nom=REGLES[fam], p=p, bruit_95=float(np.quantile(tb, 0.95)),
                              bat_bruit=float(np.mean(v["t"] > tb)), **v))
    # Benjamini-Hochberg a 10 %
    ordre = np.argsort([x["p"] for x in tests])
    m = len(tests)
    kmax = 0
    for r, i in enumerate(ordre, start=1):
        if tests[i]["p"] <= 0.10 * r / m:
            kmax = r
    for r, i in enumerate(ordre, start=1):
        tests[i]["bh"] = r <= kmax
    for x in tests:
        x["survivante"] = bool(x["t"] >= 2 and x["bh"] and x["bat_bruit"] >= 0.95)
    (MA.SORTIE).mkdir(exist_ok=True)
    (MA.SORTIE / "partie_a.json").write_text(json.dumps(tests, indent=1, ensure_ascii=False))
    L = ["Partie A, exploration 2017-2022 (gains au prix d'aujourd'hui, frais compris), 40 jumeaux de bruit, "
         "Benjamini-Hochberg a 10 % sur 12 tests", "",
         "marche  regle                                                  trades   t     net/trade  brut/trade  gagnants"
         "  bruit 95e  bat le bruit  BH  survivante"]
    for x in tests:
        L.append(f"{x['marche']:<6}  {x['nom']:<54} {x['trades']:6d} {x['t']:6.2f} {x['net_trade']:9.2f} $ "
                 f"{x['brut_trade']:9.2f} $ {x['gagnants']:8.0%} {x['bruit_95']:9.2f} {x['bat_bruit']:10.0%}   "
                 f"{'oui' if x['bh'] else 'non'}  {'OUI' if x['survivante'] else 'non'}")
    txt = "\n".join(L)
    (MA.SORTIE / "partie_a.txt").write_text(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
