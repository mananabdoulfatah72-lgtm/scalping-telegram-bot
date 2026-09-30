#!/usr/bin/env python3
"""Etapes 1 et 2 du tournoi n°2 (README.md) : exploration 2011-2022 et controle sur 20 versions melangees.
Les annees 2023-2026 ne sont pas utilisees ici (coupees au chargement).

Lancer depuis ce dossier : python3 explorer2.py
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import concurrents2 as K
from explorer import charger, mesurer, t_stat      # tournoi/explorer.py (meme mesure que le tournoi n°1)

ICI = Path(__file__).resolve().parent
MARCHES = {"NQ": ("nasdaq100", 2.0), "ES": ("sp500", 5.0)}      # fichier, $ par point pour 1 micro
N_BRUIT = 20
PAIRE = "Paire NQ / ES en retour a la moyenne"


def zone(J, O, H, L, C, P, X, cout, ok):
    z = K.st.zone_de_bruit(J, O, H, L, C, P, X)
    zp = (z["brut"] - cout * z["allers"]).reindex(pd.DatetimeIndex(J)).fillna(0).values
    return pd.Series(np.where(ok, zp, 0.0)[ok] / O[ok, 0], index=pd.DatetimeIndex(J[ok]))


def mesurer_paire(r, ok, J):
    x = r[ok]
    j = pd.DatetimeIndex(J[ok])
    trades = x != 0
    moit = j.year <= 2016
    return {"t": t_stat(x), "jours": int(ok.sum()), "jours_trade": int(trades.sum()),
            "dollars_par_trade": float(x[trades].mean() * 50_000) if trades.any() else 0.0,      # pour 50 000 $ engages
            "dollars_total": float(x.sum() * 50_000), "t_2011_2016": t_stat(x[moit]), "t_2017_2022": t_stat(x[~moit]),
            "gagnants": float((x[trades] > 0).mean()) if trades.any() else 0.0}


def main():
    t0 = time.time()
    lignes, zones = [], {}
    for marche, (fichier, pt) in MARCHES.items():
        J, O, H, L, C, P, X = charger(fichier)
        assert J.max() <= pd.Timestamp("2022-12-31")
        cout = K.st.cout_aller_retour(fichier)
        res, ok = K.toutes(J, O, H, L, C, P, X, cout)
        o0 = O[:, 0]
        zones[marche] = zone(J, O, H, L, C, P, X, cout, ok)
        bruit = {nom: [] for nom in res}
        rng = np.random.default_rng(2026)
        for k in range(N_BRUIT):
            O2, H2, L2, C2, V2 = K.K1.melanger(O, H, L, C, X["V"], rng)
            res2, ok2 = K.toutes(J, O2, H2, L2, C2, P, {**X, "V": V2}, cout)
            for nom, pts in res2.items():
                bruit[nom].append(t_stat(pts[ok2] / O2[ok2, 0]))
            print(f"  {marche} bruit {k + 1}/{N_BRUIT} ({time.time() - t0:.0f} s)", flush=True)
        for nom, pts in res.items():
            m = mesurer(pts, ok, o0, J, pt)
            r = pts[ok] / o0[ok]
            corr = float(np.corrcoef(r, zones[marche].values)[0, 1]) if r.std() > 0 else 0.0
            b = np.array(bruit[nom])
            lignes.append({"strategie": nom, "marche": marche, **m, "bruit_max": float(b.max()), "bruit_moyen": float(b.mean()),
                           "correlation_zone": corr, "etape1": m["t"] >= 2.0, "etape2": m["t"] >= 2.0 and m["t"] > b.max()})
    # 11. la paire : un seul essai pour les deux marches ; le meme melange pour NQ et ES
    a, b = K.aligner(charger("nasdaq100"), charger("sp500"))
    ca, cb = K.st.cout_aller_retour("nasdaq100"), K.st.cout_aller_retour("sp500")
    r, okp = K.paire(a, b, ca, cb)
    m = mesurer_paire(r, okp, a[0])
    rng = np.random.default_rng(2027)
    bp = []
    for k in range(N_BRUIT):
        perm = K.ordre_hasard(len(a[0]), rng)
        a2 = (a[0],) + K.melanger_perm(*a[1:5], a[6]["V"], perm)[:4] + (a[5], a[6])
        b2 = (b[0],) + K.melanger_perm(*b[1:5], b[6]["V"], perm)[:4] + (b[5], b[6])
        r2, ok2 = K.paire(a2, b2, ca, cb)
        bp.append(t_stat(r2[ok2]))
        print(f"  paire bruit {k + 1}/{N_BRUIT} ({time.time() - t0:.0f} s)", flush=True)
    rp = pd.Series(r[okp], index=pd.DatetimeIndex(a[0][okp]))
    zq = zones["NQ"].reindex(rp.index).fillna(0)
    bp = np.array(bp)
    lignes.append({"strategie": PAIRE, "marche": "NQ+ES", **m, "bruit_max": float(bp.max()), "bruit_moyen": float(bp.mean()),
                   "correlation_zone": float(np.corrcoef(rp.values, zq.values)[0, 1]),
                   "etape1": m["t"] >= 2.0, "etape2": m["t"] >= 2.0 and m["t"] > bp.max()})
    df = pd.DataFrame(lignes)
    assert len(df) == 29
    df.to_csv(ICI / "exploration.csv", index=False)
    print(f"\nExploration 2011-2022 (t sur les rendements quotidiens nets ; bruit : {N_BRUIT} melanges) :")
    for _, x in df.sort_values("t", ascending=False).iterrows():
        unite = "pour 50 000 $" if x["marche"] == "NQ+ES" else "(1 micro)"
        print(f"  {x['strategie']:42s} {x['marche']:5s} | t {x['t']:+.2f} (2011-16 {x['t_2011_2016']:+.2f}, 2017-22 {x['t_2017_2022']:+.2f})"
              f" | {x['jours_trade']:4d} jours de trade, {x['dollars_par_trade']:+7.2f} $ par trade {unite}, gagnants {x['gagnants']:.0%}"
              f" | bruit : max {x['bruit_max']:+.2f}, moyen {x['bruit_moyen']:+.2f} | corr. zone {x['correlation_zone']:+.2f}"
              f" | {'SURVIT' if x['etape2'] else ('bat t>=2 mais pas le bruit' if x['etape1'] else 'elimine')}", flush=True)
    surv = df[df["etape2"]]
    print(f"\nSurvivants des etapes 1 et 2 : {len(surv)}" + "".join(f"\n  - {a} | {b}" for a, b in zip(surv["strategie"], surv["marche"])))
    (ICI / "survivants.json").write_text(json.dumps([{"strategie": a, "marche": b} for a, b in zip(surv["strategie"], surv["marche"])],
                                                    ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
