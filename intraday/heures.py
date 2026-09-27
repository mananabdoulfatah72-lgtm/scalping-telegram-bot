#!/usr/bin/env python3
"""Momentum de fin de seance, teste sur les barres d'une heure (S&P 500 et Nasdaq 100, 2014-2026),
avec les frais des micro-futures MES et MNQ, puis rejoue sur des challenges 50K intraday.

Regles des etudes, adaptees aux barres d'une heure (la derniere heure au lieu de la derniere
demi-heure) :
- version Gao et al. (2018) : sens = rendement entre la cloture de la veille (16 h) et 10 h ;
- version Baltussen et al. (2021) : sens = rendement entre la cloture de la veille et 15 h ;
- position de 15 h a 16 h dans ce sens, rien d'autre de la journee.
Aucun parametre n'est ajuste.

Lancer depuis ce dossier : python3 heures.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import strategies as st
from analyse import hasard, mesures
from challenge import REGLES, simuler

PUBLICATION = {"Fin de seance (Gao 2018)": "2014-11-01", "Fin de seance (Baltussen 2021)": "2021-01-01"}


def charger_heures(nom):
    d = pd.read_csv(st.DONNEES / f"{nom}_1h.csv.gz", parse_dates=["t"])
    d["jour"] = d["t"].dt.normalize()
    d["heure"] = d["t"].dt.hour
    return d.pivot_table(index="jour", columns="heure", values=["o", "h", "l", "c"])


def fin_de_seance_heures(b, heure_signal):
    """b : barres par jour et par heure de debut (9 ... 15). heure_signal : 9 (prix de 10 h) ou 14 (prix de 15 h)."""
    c16 = b[("c", 15)]                                  # prix de 16 h (fin de la barre de 15 h)
    c15 = b[("c", 14)]                                  # prix de 15 h
    veille = c16.shift(1)
    # seance complete la veille et le jour meme (pas de fermeture anticipee)
    ok = c16.notna() & c15.notna() & b[("c", heure_signal)].notna() & veille.notna()
    ok &= (b.index.to_series().diff().dt.days <= 4).values
    sens = np.sign(b[("c", heure_signal)] / veille - 1)
    brut = sens * (c16 - c15)
    pire = np.minimum(0, np.where(sens > 0, b[("l", 15)] - c15, c15 - b[("h", 15)]))
    df = pd.DataFrame({"sens": sens, "brut": brut, "risque": np.nan, "pire": pire}, index=b.index)
    return df[ok & (sens != 0)]


def main():
    sortie = {}
    for nom, info in st.CONTRATS.items():
        b = charger_heures(nom)
        cout = st.cout_aller_retour(nom)
        jours = b.index[b[("c", 15)].notna()]
        print(f"\n=== {nom.upper()} ({info['micro']}, {info['pt']:.0f} $ par point) : {len(jours)} seances "
              f"du {jours[0].date()} au {jours[-1].date()} ; frais aller-retour {cout:.2f} point")
        sortie[nom] = {}
        for strat, h in [("Fin de seance (Gao 2018)", 9), ("Fin de seance (Baltussen 2021)", 14)]:
            df = fin_de_seance_heures(b, h)
            df["net"] = df["brut"] - cout
            df["dollars"] = df["net"] * info["pt"]
            print(f"\n  {strat} - position de 15 h a 16 h")
            lignes = {}
            for lab, a, z in [("Total", None, None), ("2014-2019", None, "2020-01-01"),
                              ("2020-2026", "2020-01-01", None), ("Apres publication", PUBLICATION[strat], None)]:
                m = mesures(df, jours, a, z)
                if m:
                    lignes[lab] = m
                    print(f"    {lab:18s} trades {m['trades']:5d} | gagnants {m['gagnants']:4.0%} | brut {m['brut_pts']:+6.2f} pt"
                          f" | net {m['net_pts']:+6.2f} pt | {m['dollars_an']:+8,.0f} $/an par contrat | Sharpe {m['sharpe']:+5.2f} | t {m['t']:+5.2f}")
            annees = {int(a): float(g["dollars"].sum()) for a, g in df.groupby(df.index.year)}
            print("    par annee ($ par contrat) : " + " ".join(f"{a}:{v:+,.0f}" for a, v in annees.items()))
            p, moy = hasard(df, cout)
            print(f"    test du hasard : {p:.1%} des sens tires au hasard font aussi bien (placebo {moy:+.2f} pt)")
            # challenges
            net = df["net"].reindex(jours).fillna(0).values
            pire = np.minimum(df["pire"].reindex(jours).fillna(0).values - cout, np.minimum(net, 0))
            chal = {}
            for regle in REGLES:
                for contrats in [5, 10, 20, 40]:
                    k = contrats * info["pt"]
                    ok, dur = simuler(net * k, pire * k, regle)
                    sans = net - df["net"].mean() * (net != 0)
                    ok0, _ = simuler(sans * k, pire * k, regle)
                    chal[f"{regle} {contrats}"] = [float(np.mean(ok == 1)), float(np.mean(ok == -1)), float(np.mean(ok0 == 1))]
                    print(f"    {regle:12s} {contrats:2d} {info['micro']} : reussi {np.mean(ok == 1):4.0%} | perdu {np.mean(ok == -1):4.0%}"
                          f" | pas fini {np.mean(ok == 0):4.0%} || sans avantage : reussi {np.mean(ok0 == 1):4.0%}")
            sortie[nom][strat] = {"periodes": lignes, "annees": annees, "hasard": p, "challenges": chal}
    Path(__file__).with_name("resultats_heures.json").write_text(json.dumps(sortie, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
