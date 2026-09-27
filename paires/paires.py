#!/usr/bin/env python3
"""Trading de paires par cointegration (methode Engle-Granger + test ADF), teste periode par periode.

Regles de manuel, fixees a l'avance :
- tous les 6 mois, sur les 12 mois precedents : regression log(A) = a + b log(B), puis test de
  cointegration d'Engle-Granger sur l'ecart (valeurs critiques correctes pour un ecart estime) ;
- si p < 5 %, on trade les 6 mois suivants : on vend l'ecart quand il depasse +2 ecarts-types, on
  l'achete sous -2, on sort au retour a la moyenne, stop a 4 ecarts-types, sortie en fin de periode ;
- positions : 1 $ reparti entre A et B selon b (neutre au marche) ; frais par jambe et par ordre.

Lancer depuis ce dossier : python3 paires.py
"""
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, coint

warnings.filterwarnings("ignore")
ICI = Path(__file__).parent
GROUPES = {
    "Futures (proxys ETF)": {"frais_pb": 2.0, "paires": [("SPY", "QQQ"), ("SPY", "IWM"), ("SPY", "DIA"), ("GLD", "SLV"),
                                                          ("IEF", "TLT"), ("SHY", "IEF"), ("FXA", "FXC"), ("FXE", "FXF"), ("FXE", "FXB")]},
    "Actions (paires classiques)": {"frais_pb": 5.0, "paires": [("V", "MA"), ("KO", "PEP"), ("XOM", "CVX"), ("HD", "LOW"), ("GS", "MS"),
                                                                 ("UPS", "FDX"), ("JPM", "BAC"), ("T", "VZ"), ("MCD", "YUM"),
                                                                 ("WMT", "TGT"), ("COST", "BJ")]},
}
FORMATION, TRADING = 252, 126


def prix():
    etf = pd.read_csv(ICI.parent / "tendance" / "donnees" / "prix.csv.gz", parse_dates=["date"])
    etf = etf.pivot(index="date", columns="ticker", values="adjclose")
    act = pd.read_csv(ICI / "donnees" / "actions.csv.gz", index_col=0, parse_dates=True)
    return etf.join(act, how="outer").sort_index()


def trader_paire(p, a, b, frais):
    """Renvoie (rendements quotidiens de la paire, liste des trades, stats des tests)."""
    d = np.log(p[[a, b]].dropna())
    r = p[[a, b]].pct_change().reindex(d.index)
    rend = pd.Series(0.0, index=d.index)
    trades, tests = [], []
    for debut in range(FORMATION, len(d) - 20, TRADING):
        f = d.iloc[debut - FORMATION:debut]
        beta, alpha = np.polyfit(f[b], f[a], 1)
        ecart_f = f[a] - alpha - beta * f[b]
        p_eg = coint(f[a], f[b])[1]                          # test correct (ecart estime)
        p_adf = adfuller(ecart_f, autolag="AIC")[1]          # test "naif" des videos
        t = d.iloc[debut:debut + TRADING]
        ecart_t = t[a] - alpha - beta * t[b]
        tests.append({"p_eg": p_eg, "p_adf": p_adf,
                      "p_eg_apres": coint(t[a], t[b])[1] if len(t) > 60 else np.nan})
        if p_eg >= 0.05 or beta <= 0:
            continue
        z = (ecart_t - ecart_f.mean()) / ecart_f.std()
        wa, wb = 1 / (1 + beta), beta / (1 + beta)
        pos, entree, jour_entree, cumul = 0, None, None, 0.0
        for i in range(len(t) - 1):
            zi = z.iloc[i]
            if pos == 0 and abs(zi) > 2 and abs(zi) < 4:
                pos, jour_entree, cumul = (-1 if zi > 0 else 1), t.index[i], -frais * 2 / 1e4
                rend.loc[t.index[i]] -= frais * 2 / 1e4
            elif pos != 0 and (np.sign(zi) == pos or abs(zi) >= 4 or i == len(t) - 2):
                rend.loc[t.index[i]] -= frais * 2 / 1e4
                cumul -= frais * 2 / 1e4
                trades.append({"debut": jour_entree, "fin": t.index[i], "gain": cumul, "stop": abs(zi) >= 4})
                pos = 0
            if pos != 0:
                g = pos * (wa * r[a].loc[t.index[i + 1]] - wb * r[b].loc[t.index[i + 1]])
                rend.loc[t.index[i + 1]] += g
                cumul += g
    return rend, trades, tests


def stats(x, lab):
    x = x[x.index >= x.ne(0).idxmax()] if x.ne(0).any() else x
    if x.std() == 0 or len(x) < 60:
        print(f"    {lab:14s} pas assez de trades")
        return
    cum = (1 + x).cumprod()
    print(f"    {lab:14s} Sharpe {x.mean() / x.std() * np.sqrt(252):+5.2f} | gain/an {x.mean() * 252:+6.1%} | "
          f"risque {x.std() * np.sqrt(252):5.1%} | pire baisse {(cum / cum.cummax() - 1).min():6.1%}")


def main():
    p = prix()
    for groupe, g in GROUPES.items():
        tous, rends, tests = [], {}, []
        for a, b in g["paires"]:
            if a not in p or b not in p or p[[a, b]].dropna().shape[0] < FORMATION + TRADING:
                print(f"  {a}/{b} : donnees absentes")
                continue
            rend, trades, t = trader_paire(p, a, b, g["frais_pb"])
            rends[f"{a}/{b}"] = rend
            tous += [dict(tr, paire=f"{a}/{b}") for tr in trades]
            tests += t
        tr = pd.DataFrame(tous)
        te = pd.DataFrame(tests)
        porte = pd.DataFrame(rends).fillna(0).mean(axis=1)
        print(f"\n=== {groupe} : {len(rends)} paires, {len(te)} periodes de 6 mois testees")
        print(f"  Test naif des videos (ADF, valeurs critiques -2,86) : {np.mean(te.p_adf < 0.05):.0%} des periodes 'cointegrees'")
        print(f"  Test correct (Engle-Granger)                       : {np.mean(te.p_eg < 0.05):.0%} des periodes cointegrees")
        sel = te[te.p_eg < 0.05]
        print(f"  Parmi elles, encore cointegrees les 6 mois suivants  : {np.mean(sel.p_eg_apres < 0.05):.0%}")
        if len(tr):
            print(f"  Trades : {len(tr)} | gagnants {np.mean(tr.gain > 0):.0%} | gain moyen {tr.gain.mean():+.2%} (frais compris)"
                  f" | stops {np.mean(tr.stop):.0%}")
            print("  Par paire : " + " ".join(f"{k} {v.gain.sum():+.0%}" for k, v in tr.groupby("paire")))
        print("  Portefeuille (toutes les paires, meme poids) :")
        for lab, a, z in [("2006-2026", "2006-01-01", None), ("2006-2012", "2006-01-01", "2013-01-01"),
                          ("2013-2019", "2013-01-01", "2020-01-01"), ("2020-2026", "2020-01-01", None)]:
            x = porte[porte.index >= a]
            if z:
                x = x[x.index < z]
            stats(x, lab)


if __name__ == "__main__":
    main()
