#!/usr/bin/env python3
"""Tournoi n°4, etapes 1 a 3 (README.md) : exploration 2011-2022, controle sur 20 versions melangees, et pour les
strategies 3 et 7 tirages de jours au hasard. 2023-2026 coupes au chargement.

Lancer depuis ce dossier : python3 explorer4.py
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import strategies4 as S
from explorer import charger, mesurer, t_stat      # tournoi/explorer.py

ICI = Path(__file__).resolve().parent
MARCHES = {"NQ": ("nasdaq100", 2.0), "ES": ("sp500", 5.0)}
N_BRUIT, N_JOURS = 20, 200
NOMS = {"1": "Meme demi-heure (debut et fin)", "2": "Meme demi-heure (toute la journee)", "3": "Reequilibrage de fin de mois",
        "4": "Fin de seance apres grand mouvement", "5": "Cassure du range de la nuit", "6": "Rejet du range de la nuit",
        "7": "Rebond apres forte baisse", "8": "Modele appris a 10 h"}


def main():
    t0 = time.time()
    Q = S.T3.lire_quotidien()
    lignes = []
    for marche, (fichier, pt) in MARCHES.items():
        J, O, H, L, C, P, X = charger(fichier)
        assert J.max() <= pd.Timestamp("2022-12-31")
        cout = S.st.cout_aller_retour(fichier)
        nuit = S.range_nuit(fichier, J, X.get("contrat"))
        res, ok, jours = S.toutes(J, O, H, L, C, P, X, cout, Q, nuit)
        o0 = O[:, 0]
        bruit = {k: [] for k in res}
        rng = np.random.default_rng(2030)
        for k in range(N_BRUIT):
            O2, H2, L2, C2, V2 = S.K1.melanger(O, H, L, C, X["V"], rng)
            res2, ok2, _ = S.toutes(J, O2, H2, L2, C2, P, {**X, "V": V2}, cout, Q, nuit)
            for nom, pts in res2.items():
                bruit[nom].append(t_stat(pts[ok2] / O2[ok2, 0]))
            print(f"  {marche} bruit {k + 1}/{N_BRUIT} ({time.time() - t0:.0f} s)", flush=True)
        rng = np.random.default_rng(2031)
        for nom, pts in res.items():
            m = mesurer(pts, ok, o0, J, pt)
            b = np.array(bruit[nom])
            ligne = {"code": nom, "strategie": NOMS[nom], "marche": marche, **m, "bruit_max": float(b.max()),
                     "bruit_moyen": float(b.mean()), "etape1": m["t"] >= 2.0}
            if nom in jours:                               # ouverture -> cloture : tirages de jours au hasard
                base, garde, elig = jours[nom]
                pool = np.where(elig & ok)[0]
                n = int((garde & ok).sum())
                ts = []
                for _ in range(N_JOURS):
                    msk = np.zeros(len(J), bool)
                    msk[rng.choice(pool, n, replace=False)] = True
                    ts.append(t_stat(np.where(msk, base, 0.0)[ok] / o0[ok]))
                p95 = float(np.quantile(ts, 0.95))
                ligne.update({"jours_hasard_p95": p95, "etape2": m["t"] >= 2.0 and m["t"] > p95})
            else:
                ligne.update({"jours_hasard_p95": np.nan, "etape2": m["t"] >= 2.0 and m["t"] > b.max()})
            lignes.append(ligne)
    df = pd.DataFrame(lignes)
    assert len(df) == 16
    df.to_csv(ICI / "exploration4.csv", index=False)
    print(f"\nTournoi n°4 - exploration 2011-2022 (t sur les rendements quotidiens nets ; bruit : {N_BRUIT} melanges ;"
          f" strategies 3 et 7 : {N_JOURS} tirages de jours au hasard) :")
    for _, x in df.sort_values("t", ascending=False).iterrows():
        ctrl = (f"jours au hasard p95 {x['jours_hasard_p95']:+.2f}" if not np.isnan(x["jours_hasard_p95"]) else f"bruit max {x['bruit_max']:+.2f}")
        print(f"  {x['code']} {x['strategie']:38s} {x['marche']} | t {x['t']:+.2f} (2011-16 {x['t_2011_2016']:+.2f}, 2017-22 {x['t_2017_2022']:+.2f})"
              f" | {x['jours_trade']:4d} jours de trade, {x['dollars_par_jour_trade']:+7.2f} $ par jour de trade (1 micro),"
              f" jours gagnants {x['jours_gagnants']:.0%} | {ctrl}"
              f" | {'SURVIT' if x['etape2'] else ('t>=2 mais controle rate' if x['etape1'] else 'elimine')}", flush=True)
    surv = df[df["etape2"]]
    print(f"\nSurvivants : {len(surv)}" + "".join(f"\n  - {a} {b} | {c}" for a, b, c in zip(surv["code"], surv["strategie"], surv["marche"])))
    (ICI / "survivants4.json").write_text(json.dumps([{"code": a, "marche": c} for a, c in zip(surv["code"], surv["marche"])], indent=1))


if __name__ == "__main__":
    main()
