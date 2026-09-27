#!/usr/bin/env python3
"""Momentum de fin de seance sur les barres horaires Yahoo de SPY et QQQ (oct. 2023 - sept. 2026),
converties en points de futures S&P (MES) et Nasdaq (MNQ), frais des micro-futures compris.

- Baltussen et al. (2021), regle exacte : sens = rendement entre la cloture de la veille (16 h) et
  15 h 30 ; position de 15 h 30 a 16 h (la derniere barre de SPY/QQQ va de 15 h 30 a 16 h).
- Variante Gao et al. (2018) : sens = rendement entre la cloture de la veille et 10 h 30 (Yahoo n'a
  pas de prix a 10 h) ; meme position.
Toute la periode est posterieure aux deux publications : c'est un test hors echantillon.

Lancer depuis ce dossier : python3 test_yahoo.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import strategies as st
from analyse import hasard, mesures
from challenge import REGLES, simuler

D = Path(__file__).parent / "donnees"
PAIRES = {"sp500": ("spy", "es_fut"), "nasdaq100": ("qqq", "nq_fut")}


def barres(nom):
    d = pd.read_csv(D / f"yahoo_{nom}_60m.csv.gz", parse_dates=["t"])
    d["jour"], d["hm"] = d["t"].dt.normalize(), d["t"].dt.strftime("%H:%M")
    return d


def main():
    sortie = {}
    for indice, (etf, fut) in PAIRES.items():
        info = st.CONTRATS[indice]
        cout = st.cout_aller_retour(indice)
        e = barres(etf)
        close = e.pivot_table(index="jour", columns="hm", values="c")
        haut = e.pivot_table(index="jour", columns="hm", values="h")
        bas = e.pivot_table(index="jour", columns="hm", values="l")
        # niveau du futures pour convertir les rendements en points (cloture du jour la plus proche)
        f = barres(fut).groupby("jour")["c"].last()
        niveau = f.reindex(close.index, method="nearest")
        c16, c1530 = close["15:30"], close["14:30"]         # prix de 16 h et de 15 h 30
        veille = c16.shift(1)
        ok = c16.notna() & c1530.notna() & veille.notna() & close["09:30"].notna()
        jours = close.index[c16.notna()]
        print(f"\n=== {indice.upper()} via {etf.upper()} ({info['micro']}) : {len(jours)} seances "
              f"du {jours[0].date()} au {jours[-1].date()} ; frais aller-retour {cout:.2f} point")
        sortie[indice] = {}
        for strat, signal in [("Baltussen 2021 (regle exacte)", c1530), ("Gao 2018 (variante 10 h 30)", close["09:30"])]:
            sens = np.sign(signal / veille - 1)
            r = (c16 - c1530) / c1530                          # rendement de la derniere demi-heure
            brut = sens * r * niveau
            pire = np.minimum(0, np.where(sens > 0, bas["15:30"] / c1530 - 1, 1 - haut["15:30"] / c1530)) * niveau
            df = pd.DataFrame({"sens": sens, "brut": brut, "risque": np.nan, "pire": pire})[ok & (sens != 0)].dropna(subset=["sens", "brut", "pire"])
            df["net"] = df["brut"] - cout
            df["dollars"] = df["net"] * info["pt"]
            m = mesures(df, jours)
            p, moy = hasard(df, cout)
            annees = {int(a): float(g["dollars"].sum()) for a, g in df.groupby(df.index.year)}
            print(f"\n  {strat}")
            print(f"    trades {m['trades']} | gagnants {m['gagnants']:.0%} | brut {m['brut_pts']:+.2f} pt | net {m['net_pts']:+.2f} pt"
                  f" | {m['dollars_an']:+,.0f} $/an par contrat | Sharpe {m['sharpe']:+.2f} | t {m['t']:+.2f}")
            print(f"    brut sans frais : t {df['brut'].mean() / (df['brut'].std() / np.sqrt(len(df))):+.2f}")
            print("    par annee ($ par contrat) : " + " ".join(f"{a}:{v:+,.0f}" for a, v in annees.items()))
            print(f"    test du hasard : {p:.1%} des sens tires au hasard font aussi bien")
            net = df["net"].reindex(jours).fillna(0).values
            pr = np.minimum(df["pire"].reindex(jours).fillna(0).values - cout, np.minimum(net, 0))
            chal = {}
            for regle in REGLES:
                for n in [5, 10, 20, 40]:
                    k = n * info["pt"]
                    res, _ = simuler(net * k, pr * k, regle)
                    sans = net - df["net"].mean() * (net != 0)
                    res0, _ = simuler(sans * k, pr * k, regle)
                    chal[f"{regle} {n}"] = [float(np.mean(res == 1)), float(np.mean(res == -1)), float(np.mean(res0 == 1))]
                    print(f"    {regle:12s} {n:2d} {info['micro']} : reussi {np.mean(res == 1):4.0%} | perdu {np.mean(res == -1):4.0%}"
                          f" || sans avantage : reussi {np.mean(res0 == 1):4.0%}")
            sortie[indice][strat] = {"mesures": m, "hasard": p, "annees": annees, "challenges": chal}
    Path(__file__).with_name("resultats_yahoo.json").write_text(json.dumps(sortie, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
