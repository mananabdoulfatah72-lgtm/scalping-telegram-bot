#!/usr/bin/env python3
"""Resultats des strategies intraday sur les vrais prix minute, frais des micro-futures compris.

Lancer depuis ce dossier : python3 analyse.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import strategies as st

# Date de premiere diffusion de chaque etude : ce qui suit est "apres publication"
PUBLICATION = {
    "Fin de seance (Gao 2018)": "2014-11-01",       # premiere version SSRN, nov. 2014
    "Fin de seance (Baltussen 2021)": "2021-01-01",  # SSRN, janv. 2021
    "OPR 5 minutes": "2023-04-01",                   # SSRN, avril 2023
    "Zone de bruit": "2024-05-01",                   # SSRN, mai 2024
}


def calculer(nom):
    J, O, H, L, C, P, X = st.charger(nom)
    cout = st.cout_aller_retour(nom)
    pt = st.CONTRATS[nom]["pt"]
    res = {
        "Fin de seance (Gao 2018)": st.fin_de_seance(J, O, H, L, C, P, 29, X),
        "Fin de seance (Baltussen 2021)": st.fin_de_seance(J, O, H, L, C, P, 359, X),
        "OPR 5 minutes": st.opr5(J, O, H, L, C, P),
        "Zone de bruit": st.zone_de_bruit(J, O, H, L, C, P, X),
    }
    for df in res.values():
        allers = df["allers"] if "allers" in df else 1
        df["net"] = df["brut"] - cout * allers
        df["dollars"] = df["net"] * pt                    # pour 1 contrat micro
    jours_ok = pd.DatetimeIndex(J[st.journees_completes(P)])
    return jours_ok, res, cout


def hasard_opr(nom, df, n=100, graine=0):
    """Test du hasard de l'OPR : memes jours, memes stops et objectifs, mais sens tire au hasard."""
    J, O, H, L, C, P, X = st.charger(nom)
    rng = np.random.default_rng(graine)
    cout = st.cout_aller_retour(nom)
    base = np.sign(C[:, 4] - O[:, 0])
    moyennes = []
    for _ in range(n):
        sens = np.where(base != 0, rng.choice([-1.0, 1.0], size=len(base)), 0.0)
        p = st.opr5(J, O, H, L, C, P, sens=sens)
        moyennes.append((p["brut"] - cout).mean())
    moyennes = np.array(moyennes)
    return float(np.mean(moyennes >= df["net"].mean())), float(moyennes.mean())


def mesures(df, jours, debut=None, fin=None):
    sel = np.ones(len(df), bool)
    tous = jours
    if debut:
        sel &= df.index >= debut
        tous = tous[tous >= debut]
    if fin:
        sel &= df.index < fin
        tous = tous[tous < fin]
    d = df[sel]
    if len(d) < 20:
        return None
    quotidien = d["dollars"].reindex(tous).fillna(0)       # jours sans trade = 0
    annees = len(tous) / 252
    t = d["net"].mean() / (d["net"].std() / np.sqrt(len(d)))
    out = {
        "trades": int(len(d)), "gagnants": float((d["net"] > 0).mean()),
        "brut_pts": float(d["brut"].mean()), "net_pts": float(d["net"].mean()),
        "dollars_an": float(d["dollars"].sum() / annees), "sharpe": float(quotidien.mean() / quotidien.std() * np.sqrt(252)),
        "t": float(t),
    }
    if "risque" in d and d["risque"].notna().any():
        out["R_brut"] = float((d["brut"] / d["risque"]).mean())
        out["R_net"] = float((d["net"] / d["risque"]).mean())
    return out


def hasard(df, cout, n=2000, graine=0):
    """Test du hasard pour les strategies a un trade par jour : sens tire au hasard."""
    rng = np.random.default_rng(graine)
    mouvement = (df["brut"] * df["sens"]).values          # mouvement du marche pendant le trade
    reel = df["net"].mean()
    signes = rng.choice([-1.0, 1.0], size=(n, len(mouvement)))
    placebo = (signes * mouvement).mean(axis=1) - cout
    return float(np.mean(placebo >= reel)), float(placebo.mean())


def main():
    sortie = {}
    for nom, info in st.CONTRATS.items():
        jours, res, cout = calculer(nom)
        print(f"\n=== {nom.upper()} (contrat {info['micro']}, {info['pt']:.0f} $ par point) : "
              f"{len(jours)} seances du {jours[0].date()} au {jours[-1].date()} ; "
              f"frais aller-retour = {cout:.2f} point")
        sortie[nom] = {}
        for strat, df in res.items():
            lignes = {}
            for lab, a, b in [("Total", None, None), ("2010-2014", None, "2015-01-01"),
                              ("2015-2019", "2015-01-01", "2020-01-01"), ("2020-2026", "2020-01-01", None),
                              ("Apres publication", PUBLICATION[strat], None)]:
                m = mesures(df, jours, a, b)
                if m:
                    lignes[lab] = m
            annees = {int(a): float(g["dollars"].sum()) for a, g in df.groupby(df.index.year)}
            ligne_h = None
            if "sens" in df and df["risque"].isna().all():      # un trade par jour, sans stop
                ligne_h = hasard(df, cout)
            elif strat == "OPR 5 minutes":
                ligne_h = hasard_opr(nom, df)
            sortie[nom][strat] = {"periodes": lignes, "annees": annees, "hasard": ligne_h}
            print(f"\n  {strat}")
            for lab, m in lignes.items():
                extra = f" | R brut {m['R_brut']:+.3f} net {m['R_net']:+.3f}" if "R_brut" in m else ""
                print(f"    {lab:18s} trades {m['trades']:5d} | gagnants {m['gagnants']:4.0%} | brut {m['brut_pts']:+6.2f} pt"
                      f" | net {m['net_pts']:+6.2f} pt | {m['dollars_an']:+8,.0f} $/an par contrat | Sharpe {m['sharpe']:+5.2f}"
                      f" | t {m['t']:+5.2f}{extra}")
            print("    par annee ($ par contrat) : " + " ".join(f"{a}:{v:+,.0f}" for a, v in annees.items()))
            if ligne_h:
                print(f"    test du hasard : {ligne_h[0]:.1%} des sens tires au hasard font aussi bien (moyenne placebo {ligne_h[1]:+.2f} pt)")
    Path(__file__).with_name("resultats.json").write_text(json.dumps(sortie, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
