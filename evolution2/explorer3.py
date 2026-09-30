#!/usr/bin/env python3
"""Tournoi n°3, etapes 1 a 3 (README.md) : exploration 2011-2022, controle sur 20 versions melangees, et pour les
filtres (GEX, DIX, VIX, zero gamma) controle sur 200 tirages de jours au hasard. 2023-2026 coupes au chargement.

Lancer depuis ce dossier : python3 explorer3.py
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import tournoi3 as T
from explorer import charger, mesurer, t_stat      # tournoi/explorer.py

ICI = Path(__file__).resolve().parent
MARCHES = {"NQ": ("nasdaq100", 2.0), "ES": ("sp500", 5.0)}
N_BRUIT, N_FILTRE = 20, 200
NOMS = {"G1": "Gamma negatif : suivre", "G2": "Gamma eleve : retour", "G3": "Zone de bruit en gamma bas",
        "D1": "DIX eleve : achat", "V1": "VIX en deport : suivre", "V2": "VIX tres calme : retour",
        "P1": "Regle des 80 % (profil de volume)", "P2": "Acceptation hors zone de valeur", "P3": "Rejet des bords de la zone de valeur",
        "W1": "Rejet du call wall", "W2": "Rebond sur le put wall", "W3": "Sous le zero gamma : suivre"}


def murs(marche, J):
    f = ICI / "donnees" / f"murs_{marche}.csv"
    if not f.exists():
        return None
    m = pd.read_csv(f, parse_dates=["date"]).set_index("date")
    return {k: T.veille(J, m[k].dropna()) for k in ("call", "put", "zero")}


def main():
    t0 = time.time()
    Q = T.lire_quotidien()
    lignes = []
    for marche, (fichier, pt) in MARCHES.items():
        J, O, H, L, C, P, X = charger(fichier)
        assert J.max() <= pd.Timestamp("2022-12-31")
        cout = T.st.cout_aller_retour(fichier)
        W = murs(marche, J)
        res, ok, info = T.toutes(J, O, H, L, C, P, X, cout, Q, W)
        o0 = O[:, 0]
        bruit = {k: [] for k in res}
        rng = np.random.default_rng(2028)
        for k in range(N_BRUIT):
            O2, H2, L2, C2, V2 = T.K1.melanger(O, H, L, C, X["V"], rng)
            res2, ok2, _ = T.toutes(J, O2, H2, L2, C2, P, {**X, "V": V2}, cout, Q, W)
            for nom, pts in res2.items():
                bruit[nom].append(t_stat(pts[ok2] / O2[ok2, 0]))
            print(f"  {marche} bruit {k + 1}/{N_BRUIT} ({time.time() - t0:.0f} s)", flush=True)
        rng = np.random.default_rng(2029)
        for nom, pts in res.items():
            m = mesurer(pts, ok, o0, J, pt)
            b = np.array(bruit[nom])
            ligne = {"code": nom, "strategie": NOMS[nom], "marche": marche, **m, "bruit_max": float(b.max()),
                     "bruit_moyen": float(b.mean()), "etape1": m["t"] >= 2.0, "etape2": m["t"] >= 2.0 and m["t"] > b.max()}
            if nom in info["choix"]:                           # controle du filtre : jours au hasard, meme nombre
                garde, defini = info["filtres"][nom]
                base = info["base"][info["choix"][nom]]
                elig = np.where(defini & ok)[0]
                n = int((garde & ok).sum())
                ts = []
                for _ in range(N_FILTRE):
                    msk = np.zeros(len(J), bool)
                    msk[rng.choice(elig, n, replace=False)] = True
                    ts.append(t_stat(np.where(msk, base, 0.0)[ok] / o0[ok]))
                ligne.update({"jours_filtre": n, "filtre_p95": float(np.quantile(ts, 0.95)), "etape3": m["t"] > np.quantile(ts, 0.95)})
            else:
                ligne.update({"jours_filtre": np.nan, "filtre_p95": np.nan, "etape3": True})
            ligne["survit"] = bool(ligne["etape2"] and ligne["etape3"])
            lignes.append(ligne)
    df = pd.DataFrame(lignes)
    df.to_csv(ICI / "exploration3.csv", index=False)
    print(f"\nTournoi n°3 - exploration 2011-2022 (t sur les rendements quotidiens nets ; bruit : {N_BRUIT} melanges ;"
          f" filtre : {N_FILTRE} tirages de jours au hasard) :")
    for _, x in df.sort_values("t", ascending=False).iterrows():
        filtre = f" | filtre au hasard p95 {x['filtre_p95']:+.2f} ({int(x['jours_filtre'])} jours)" if not np.isnan(x["filtre_p95"]) else ""
        print(f"  {x['code']} {x['strategie']:38s} {x['marche']} | t {x['t']:+.2f} (2011-16 {x['t_2011_2016']:+.2f}, 2017-22 {x['t_2017_2022']:+.2f})"
              f" | {x['jours_trade']:4d} jours de trade, {x['dollars_par_jour_trade']:+7.2f} $ par jour de trade (1 micro),"
              f" jours gagnants {x['jours_gagnants']:.0%} | bruit max {x['bruit_max']:+.2f}{filtre}"
              f" | {'SURVIT' if x['survit'] else ('t>=2 mais controle rate' if x['etape1'] else 'elimine')}", flush=True)
    surv = df[df["survit"]]
    print(f"\nSurvivants : {len(surv)}" + "".join(f"\n  - {a} {b} | {c}" for a, b, c in zip(surv["code"], surv["strategie"], surv["marche"])))
    (ICI / "survivants3.json").write_text(json.dumps([{"code": a, "marche": c} for a, c in zip(surv["code"], surv["marche"])], indent=1))


if __name__ == "__main__":
    main()
