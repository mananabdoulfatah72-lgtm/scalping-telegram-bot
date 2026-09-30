#!/usr/bin/env python3
"""Etapes 1 et 2 du tournoi (README.md) : exploration 2011-2022 et controle sur 20 versions melangees.
Les annees 2023-2026 ne sont pas utilisees ici (coupees au chargement).

Lancer depuis ce dossier : python3 explorer.py
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import concurrents as K

ICI = Path(__file__).resolve().parent
FIN = np.datetime64("2022-12-31")
MARCHES = {"NQ": ("nasdaq100", 2.0), "ES": ("sp500", 5.0)}      # fichier, $ par point pour 1 micro
N_BRUIT = 20


def charger(fichier, fin=FIN):
    J, O, H, L, C, P, X = K.st.charger(fichier)
    g = J.values <= fin if fin is not None else np.ones(len(J), bool)
    X2 = {"V": X["V"][g], "echeance": X["echeance"][g], "contrat": X["contrat"][g] if X["contrat"] is not None else None}
    return J[g], O[g], H[g], L[g], C[g], P[g], X2


def t_stat(x):
    return float(x.mean() / x.std() * np.sqrt(len(x))) if x.std() > 0 else 0.0


def mesurer(pts, ok, o0, J, pt):
    r = pts[ok] / o0[ok]
    j = pd.DatetimeIndex(J[ok])
    trades = pts[ok] != 0
    moit = j.year <= 2016
    return {"t": t_stat(r), "jours": int(ok.sum()), "jours_trade": int(trades.sum()),
            "dollars_par_trade": float((pts[ok][trades] * pt).mean()) if trades.any() else 0.0,
            "dollars_total": float((pts[ok] * pt).sum()), "t_2011_2016": t_stat(r[moit]), "t_2017_2022": t_stat(r[~moit]),
            "gagnants": float((pts[ok][trades] > 0).mean()) if trades.any() else 0.0}


def main():
    t0 = time.time()
    lignes, series = [], {}
    for marche, (fichier, pt) in MARCHES.items():
        J, O, H, L, C, P, X = charger(fichier)
        assert J.max() <= pd.Timestamp("2022-12-31")
        cout = K.st.cout_aller_retour(fichier)
        res, ok = K.toutes(J, O, H, L, C, P, X, cout)
        o0 = O[:, 0]
        bruit = {nom: [] for nom in res}
        rng = np.random.default_rng(2026)
        for k in range(N_BRUIT):
            O2, H2, L2, C2, V2 = K.melanger(O, H, L, C, X["V"], rng)
            res2, ok2 = K.toutes(J, O2, H2, L2, C2, P, {**X, "V": V2}, cout)
            for nom, pts in res2.items():
                bruit[nom].append(t_stat(pts[ok2] / O2[ok2, 0]))
            print(f"  {marche} bruit {k + 1}/{N_BRUIT} ({time.time() - t0:.0f} s)", flush=True)
        zone = res["Zone de bruit (reference)"][ok] / o0[ok]
        for nom, pts in res.items():
            m = mesurer(pts, ok, o0, J, pt)
            r = pts[ok] / o0[ok]
            corr = float(np.corrcoef(r, zone)[0, 1]) if r.std() > 0 else 0.0
            b = np.array(bruit[nom])
            ligne = {"strategie": nom, "marche": marche, **m, "bruit_max": float(b.max()), "bruit_moyen": float(b.mean()),
                     "correlation_zone": corr, "etape1": m["t"] >= 2.0, "etape2": m["t"] >= 2.0 and m["t"] > b.max()}
            lignes.append(ligne)
            series[f"{nom} | {marche}"] = r
    df = pd.DataFrame(lignes)
    df.to_csv(ICI / "exploration.csv", index=False)
    print(f"\nExploration 2011-2022 (t sur les rendements quotidiens nets ; bruit : {N_BRUIT} melanges) :")
    for _, x in df.sort_values("t", ascending=False).iterrows():
        print(f"  {x['strategie']:36s} {x['marche']} | t {x['t']:+.2f} (2011-16 {x['t_2011_2016']:+.2f}, 2017-22 {x['t_2017_2022']:+.2f})"
              f" | {x['jours_trade']:4d} jours de trade, {x['dollars_par_trade']:+7.2f} $ par trade (1 micro), gagnants {x['gagnants']:.0%}"
              f" | bruit : max {x['bruit_max']:+.2f}, moyen {x['bruit_moyen']:+.2f} | corr. zone {x['correlation_zone']:+.2f}"
              f" | {'SURVIT' if x['etape2'] else ('bat t>=2 mais pas le bruit' if x['etape1'] else 'elimine')}", flush=True)
    surv = df[df["etape2"]]
    print(f"\nSurvivants des etapes 1 et 2 : {len(surv)}" + "".join(f"\n  - {a} | {b}" for a, b in zip(surv["strategie"], surv["marche"])))
    (ICI / "survivants.json").write_text(json.dumps([{"strategie": a, "marche": b} for a, b in zip(surv["strategie"], surv["marche"])],
                                                    ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
