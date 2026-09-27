#!/usr/bin/env python3
"""Chiffres du rapport sur la zone de bruit (Nasdaq 100, MNQ) : courbe de gains, statistiques,
t de Student et sa correction pour les essais multiples, bootstrap par blocs, journee exemple.

Lancer depuis ce dossier : python3 rapport_zone.py  (ecrit rapport_zone.json)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

import strategies as st
from analyse import calculer

NOM = "nasdaq100"
PT = st.CONTRATS[NOM]["pt"]


def stats_periode(df, jours, a=None, z=None):
    sel = np.ones(len(df), bool)
    tous = jours
    if a:
        sel &= df.index >= a; tous = tous[tous >= a]
    if z:
        sel &= df.index < z; tous = tous[tous < z]
    d = df[sel]
    q = d["dollars"].reindex(tous).fillna(0)
    eq = q.cumsum()
    return {"jours_trades": int(len(d)), "t": float(d["net"].mean() / d["net"].std() * np.sqrt(len(d))),
            "net_pts": float(d["net"].mean()), "dollars_an": float(q.sum() / (len(tous) / 252)),
            "sharpe": float(q.mean() / q.std() * np.sqrt(252)), "pire_baisse": float((eq - eq.cummax()).min())}


def bootstrap_blocs(x, n=20000, bloc=20, graine=0):
    """p-valeur d'un gain moyen >= observe si l'avantage etait nul (blocs de 20 jours : garde les
    periodes agitees ensemble)."""
    rng = np.random.default_rng(graine)
    x = np.asarray(x, float)
    y = x - x.mean()
    nb = int(np.ceil(len(x) / bloc))
    debuts = rng.integers(0, len(x) - bloc, size=(n, nb))
    idx = (debuts[:, :, None] + np.arange(bloc)).reshape(n, -1)[:, :len(x)]
    moy = y[idx].mean(axis=1)
    return float(np.mean(moy >= x.mean())), moy


def journee_exemple(J, O, H, L, C, P, X, jour):
    d = int(np.where(J == pd.Timestamp(jour))[0][0])
    ouv = O[d, 0]
    veille = st.cloture_veille(C, X)[d]
    sigma = pd.DataFrame(np.abs(C / O[:, 0][:, None] - 1)).rolling(14).mean().shift(1).values[d]
    typique, V = (H[d] + L[d] + C[d]) / 3, X["V"][d]
    vwap = np.cumsum(typique * V) / np.maximum(np.cumsum(V), 1)
    ub = max(ouv, veille) * (1 + sigma)
    lb = min(ouv, veille) * (1 - sigma)
    trades, pos, entree, t_in = [], 0, 0.0, 0
    for m in range(30, st.N, 30):
        p = C[d, m]
        if pos > 0 and p <= max(ub[m], vwap[m]) or pos < 0 and p >= min(lb[m], vwap[m]):
            trades.append({"sens": pos, "entree_min": t_in, "entree": float(entree), "sortie_min": m, "sortie": float(p)}); pos = 0
        if pos == 0 and p > ub[m]:
            pos, entree, t_in = 1, p, m
        elif pos == 0 and p < lb[m]:
            pos, entree, t_in = -1, p, m
    if pos:
        trades.append({"sens": pos, "entree_min": t_in, "entree": float(entree), "sortie_min": st.N - 1, "sortie": float(C[d, -1])})
    r = lambda a: [round(float(v), 2) for v in a]
    return {"jour": jour, "prix": r(C[d]), "haut": r(ub), "bas": r(lb), "vwap": r(vwap), "trades": trades,
            "veille": float(veille), "ouverture": float(ouv)}


def main():
    jours, res, cout = calculer(NOM)
    df = res["Zone de bruit"]
    q = df["dollars"].reindex(jours).fillna(0)
    eq = q.cumsum()
    out = {"cout_pts": cout, "debut": str(jours[0].date()), "fin": str(jours[-1].date()), "seances": int(len(jours))}
    out["periodes"] = {lab: stats_periode(df, jours, a, z) for lab, a, z in [
        ("2011-2026", None, None), ("2011-2014", None, "2015-01-01"), ("2015-2019", "2015-01-01", "2020-01-01"),
        ("2020-2026", "2020-01-01", None), ("depuis mai 2024", "2024-05-01", None)]}
    g = df["dollars"]
    out["jours_avec_trade"] = float(len(df) / len(jours))
    out["allers_par_jour"] = float(df["allers"].mean())
    out["jours_gagnants"] = float((g > 0).mean())
    out["gain_moyen_jour_gagnant"] = float(g[g > 0].mean())
    out["perte_moyenne_jour_perdant"] = float(g[g <= 0].mean())
    out["meilleur_jour"] = [str(g.idxmax().date()), float(g.max())]
    out["pire_jour"] = [str(g.idxmin().date()), float(g.min())]
    out["pire_moment_intraday"] = float(df["pire"].min() * PT)
    out["ecart_type_trade_pts"] = float(df["net"].std())
    top = g.nlargest(int(len(g) * 0.01))
    out["top1pct"] = {"n": int(len(top)), "somme": float(top.sum()), "total": float(g.sum()),
                      "reste_par_jour_pts": float(df["net"].drop(top.index).mean())}
    out["top10"] = [[str(k.date()), round(float(v))] for k, v in g.nlargest(10).items()]
    creux = eq - eq.cummax()
    out["pire_baisse"] = {"dollars": float(creux.min()), "date": str(creux.idxmin().date()),
                          "debut": str(eq[:creux.idxmin()].idxmax().date())}
    hauts = eq.cummax()
    nouveau = (eq >= hauts).values
    plus_long, cour = 0, 0
    for v in nouveau:
        cour = 0 if v else cour + 1
        plus_long = max(plus_long, cour)
    out["plus_longue_attente_seances"] = int(plus_long)
    out["annees"] = {int(a): round(float(v)) for a, v in g.groupby(g.index.year).sum().items()}
    out["courbe"] = [[str(k.date()), round(float(v), 1)] for k, v in eq.resample("W-FRI").last().dropna().items()]
    # t : probabilite d'etre du au hasard, seul et avec essais multiples
    t = out["periodes"]["2011-2026"]["t"]
    out["p_seul"] = float(1 - norm.cdf(t))
    out["seuil_8"] = float(norm.ppf(0.95 ** (1 / 8)))
    out["seuil_12"] = float(norm.ppf(0.95 ** (1 / 12)))
    out["p_8"] = float(1 - (1 - out["p_seul"]) ** 8)
    out["p_12"] = float(1 - (1 - out["p_seul"]) ** 12)
    p_boot, moy = bootstrap_blocs(q.values)
    out["p_bootstrap"] = p_boot
    out["bootstrap_hist"] = np.histogram(moy, bins=40)[0].tolist()
    out["bootstrap_bords"] = [round(float(b), 2) for b in np.histogram(moy, bins=40)[1]]
    out["moyenne_jour_dollars"] = float(q.mean())
    # annees de suivi reel pour confirmer (t = 2) selon le Sharpe
    out["annees_pour_t2"] = {k: float((2 / out["periodes"][k]["sharpe"]) ** 2) for k in ["2011-2026", "2020-2026"]}
    # 5 MNQ sur 2020-2026
    q5 = q[q.index >= "2020-01-01"] * 5
    e5 = q5.cumsum()
    out["cinq_mnq_2020"] = {"par_an": float(q5.sum() / (len(q5) / 252)), "pire_baisse": float((e5 - e5.cummax()).min()),
                            "pire_jour": float(q5.min()), "par_mois": float(q5.sum() / (len(q5) / 21))}
    J, O, H, L, C, P, X = st.charger(NOM)
    out["exemple"] = journee_exemple(J, O, H, L, C, P, X, out["top10"][0][0] if False else "2025-04-04")
    Path(__file__).with_name("rapport_zone.json").write_text(json.dumps(out, ensure_ascii=False))
    court = {k: v for k, v in out.items() if k not in ("courbe", "exemple", "bootstrap_hist", "bootstrap_bords")}
    print(json.dumps(court, indent=1, ensure_ascii=False))
    print("exemple trades :", out["exemple"]["trades"])


if __name__ == "__main__":
    main()
