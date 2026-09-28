#!/usr/bin/env python3
"""Etape 1 : recherche sur les secteurs americains, sans strategie (protocole dans README.md).

1. Etat des secteurs et des industries a la derniere date : force relative 3 et 6 mois, momentum
   12-1, distance a la moyenne 200 jours, volatilite, beta, sensibilite aux taux, baisse depuis le
   plus haut d'un an ; classement.
2. Taux de base 1999-2026 : le secteur le plus fort des 3 ou 6 derniers mois bat-il SPY ensuite ?

Lancer depuis ce dossier : python3 recherche.py   (ecrit recherche.json)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).parent
sys.path.insert(0, str(ICI))
import univers as U  # noqa: E402

M3, M6, AN = 63, 126, 252
FIN = "2026-09-25"      # derniere seance complete avant le telechargement (la ligne du 28 septembre est partielle)


def charger():
    d = pd.read_csv(ICI / "donnees" / "prix.csv.gz", parse_dates=["date"])
    adj = d.pivot(index="date", columns="ticker", values="adjclose")
    close = d.pivot(index="date", columns="ticker", values="close")
    jours = adj[U.MARCHE].dropna().index
    jours = jours[jours <= FIN]
    return adj.reindex(jours), close.reindex(jours)


def etat(adj, close, tickers):
    p = adj[tickers]
    spy = adj[U.MARCHE]
    r = p.pct_change(fill_method=None)
    t = p.index[-1]
    lignes = {}
    hebdo = p.resample("W-FRI").last().pct_change(fill_method=None).iloc[-104:]
    dtaux = close["^TNX"].resample("W-FRI").last().diff().iloc[-104:]
    spy_r = spy.pct_change(fill_method=None)
    for k in tickers:
        x = p[k]
        if x.iloc[-AN - 30:].isna().any():             # toutes les seances de la derniere annee, memes dates que SPY
            continue
        r3, r6 = x.iloc[-1] / x.iloc[-1 - M3] - 1, x.iloc[-1] / x.iloc[-1 - M6] - 1
        s3, s6 = spy.iloc[-1] / spy.iloc[-1 - M3] - 1, spy.iloc[-1] / spy.iloc[-1 - M6] - 1
        rk = r[k].iloc[-AN:]
        beta = np.cov(rk.fillna(0), spy_r.iloc[-AN:].fillna(0))[0, 1] / spy_r.iloc[-AN:].var()
        h = pd.concat([hebdo[k], dtaux], axis=1).dropna()
        sens = np.polyfit(h.iloc[:, 1], h.iloc[:, 0], 1)[0] * 0.10 if len(h) > 50 else np.nan
        lignes[k] = {
            "nom": U.SECTEURS.get(k, k), "rs3": r3 - s3, "rs6": r6 - s6, "r3": r3, "r6": r6,
            "mom12_1": x.iloc[-22] / x.iloc[-AN] - 1, "vs_mm200": x.iloc[-1] / x.iloc[-200:].mean() - 1,
            "vol": rk.std() * np.sqrt(AN), "beta": beta, "taux_+0,10": sens,
            "baisse_1an": x.iloc[-1] / x.iloc[-AN:].max() - 1,
        }
    t_ = pd.DataFrame(lignes).T
    t_["rang"] = (t_["rs3"].astype(float).rank(ascending=False) + t_["rs6"].astype(float).rank(ascending=False)) / 2
    return t_.sort_values("rang"), t


def taux_de_base(adj):
    """Chaque fin de mois : le(s) secteur(s) le(s) plus fort(s) sur 3 ou 6 mois, ecart avec SPY le mois suivant."""
    p = adj[list(U.SECTEURS) + [U.MARCHE]]
    fins = p.groupby(p.index.to_period("M")).tail(1).index
    if p.index[-1] != p.index[-1] + pd.offsets.BMonthEnd(0):   # dernier mois incomplet : on ne l'utilise pas
        fins = fins[:-1]
    pm = p.reindex(fins)
    suivant = pm.shift(-1) / pm - 1
    ecart = suivant[list(U.SECTEURS)].sub(suivant[U.MARCHE], axis=0)
    res = {}
    for nom, fen in [("3 mois", 3), ("6 mois", 6)]:
        force = pm[list(U.SECTEURS)] / pm[list(U.SECTEURS)].shift(fen) - 1
        for n in (1, 3):
            choix = force.rank(axis=1, ascending=False) <= n
            e = (ecart.where(choix).mean(axis=1)).dropna()
            e = e[e.index >= "1999-06-30"]
            t = e.mean() / e.std() * np.sqrt(len(e))
            res[f"top {n} sur {nom}"] = {"mois": int(len(e)), "ecart_mensuel": float(e.mean()), "t": float(t),
                                         "mois_gagnants": float((e > 0).mean()),
                                         "depuis_2010": float(e[e.index >= "2010"].mean()),
                                         "t_depuis_2010": float(e[e.index >= "2010"].mean() / e[e.index >= "2010"].std()
                                                                * np.sqrt((e.index >= "2010").sum()))}
    # evenement : un secteur depasse SPY de plus de 10 points sur 3 mois
    rs3 = (pm[list(U.SECTEURS)] / pm[list(U.SECTEURS)].shift(3) - 1).sub(pm[U.MARCHE] / pm[U.MARCHE].shift(3) - 1, axis=0)
    suivant3 = (pm.shift(-3) / pm - 1)
    ecart3 = suivant3[list(U.SECTEURS)].sub(suivant3[U.MARCHE], axis=0)
    ev = rs3 > 0.10
    e1, e3 = ecart.where(ev).stack().dropna(), ecart3.where(ev).stack().dropna()   # pandas 3 garde les vides
    res["evenement +10 pts sur 3 mois"] = {
        "cas": int(len(e1)), "ecart_1_mois": float(e1.mean()), "t_1_mois": float(e1.mean() / e1.std() * np.sqrt(len(e1))),
        "ecart_3_mois": float(e3.mean()), "gagnants_3_mois": float((e3 > 0).mean())}
    return res


def main():
    adj, close = charger()
    sect, t = etat(adj, close, list(U.SECTEURS))
    print(f"Etat des secteurs au {t.date()} (classes par force relative 3 et 6 mois contre SPY) :")
    for k, x in sect.iterrows():
        print(f"  {k:5s} {x['nom']:22s} | 3 mois {x['rs3']:+6.1%} | 6 mois {x['rs6']:+6.1%} | mom 12-1 {x['mom12_1']:+6.1%}"
              f" | vs moy 200j {x['vs_mm200']:+6.1%} | vol {x['vol']:5.1%} | beta {x['beta']:4.2f}"
              f" | si taux 10 ans +0,10 pt : {x['taux_+0,10']:+.2%} | baisse 1 an {x['baisse_1an']:+6.1%}")
    ind, _ = etat(adj, close, U.INDUSTRIES)
    print("\nIndustries (ETF), les 8 plus fortes et les 5 plus faibles :")
    for k, x in pd.concat([ind.head(8), ind.tail(5)]).iterrows():
        print(f"  {k:5s} | 3 mois {x['rs3']:+6.1%} | 6 mois {x['rs6']:+6.1%} | vs moy 200j {x['vs_mm200']:+6.1%} | vol {x['vol']:5.1%}")
    base = taux_de_base(adj)
    print("\nTaux de base 1999-2026 : acheter le(s) secteur(s) le(s) plus fort(s), ecart avec SPY le mois suivant")
    for k, v in base.items():
        if k.startswith("top"):
            print(f"  {k:16s} : {v['ecart_mensuel']:+.2%}/mois (t {v['t']:+.2f}), {v['mois_gagnants']:.0%} des mois gagnants"
                  f" | depuis 2010 : {v['depuis_2010']:+.2%}/mois (t {v['t_depuis_2010']:+.2f})")
    v = base["evenement +10 pts sur 3 mois"]
    print(f"  secteur a plus de 10 points au-dessus de SPY sur 3 mois ({v['cas']} cas) : mois suivant {v['ecart_1_mois']:+.2%}"
          f" (t {v['t_1_mois']:+.2f}) ; 3 mois suivants {v['ecart_3_mois']:+.2%}, gagnant {v['gagnants_3_mois']:.0%} des cas")
    sortie = {"date": str(t.date()), "secteurs": sect.astype(object).to_dict(orient="index"),
              "industries": ind.astype(object).to_dict(orient="index"), "taux_de_base": base,
              "premier": sect.index[0]}
    (ICI / "recherche.json").write_text(json.dumps(sortie, indent=1, ensure_ascii=False, default=float))


if __name__ == "__main__":
    main()
