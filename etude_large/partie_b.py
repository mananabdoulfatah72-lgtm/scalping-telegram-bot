#!/usr/bin/env python3
"""etude_large/README.md, partie B (regles fixees le 22 octobre 2026, avant tout calcul) : la zone du bot (V1 sans
filtre, NQ minute, sans les jours de la Fed) avec un modele ridge de 10 informations connues a l'entree, en
walk-forward : chaque annee 2016 - 2026 est jugee par un modele appris sur les annees precedentes seulement.

Lancer : python3 etude_large/partie_b.py (numpy, pandas ; variable KB comme delta_mesures). Ecrit resultats_b.txt."""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.path.insert(0, str(RACINE / "delta_mesures"))
import etude as DM  # noqa: E402
sys.path.insert(0, str(DM.KB / "fonds"))
import fomc  # noqa: E402

FIN_ES = "2026-09-25"                     # derniere seance des minutes ES de la recherche
ES = DM.KB / "intraday" / "donnees" / "sp500_1min.csv.gz"
VIX = RACINE / "donnees_libres" / "yahoo" / "jour" / "VIX.csv.gz"
NOMS = ["10 h", "10 h 30 - 11 h 30", "12 h - 13 h 30", "force", "volatilite", "ES hors zone", "ecart d'ouverture",
        "tendance 20 j", "VIX", "premier trade"]
LAMBDA = 1.0
ANNEES = range(2016, 2027)


def zone_es(z_nq, z_es):
    """Pour chaque seance du NQ : indice de la meme seance ES (-1 si absente)."""
    pos = {j: i for i, j in enumerate(z_es["jours"])}
    return np.array([pos.get(j, -1) for j in z_nq["jours"]])


def informations(z, tr, z_es, ies, vix):
    """Les 10 informations de chaque trade, connues a la minute d'entree."""
    idx = {j: i for i, j in enumerate(z["jours"])}
    C = z["C"]
    jouables = np.zeros(len(C), bool)
    jouables[z["jouables"]] = True
    s30 = z["sigma"][:, DM.PAS]
    med = pd.Series(np.where(jouables, s30, np.nan)).rolling(252, min_periods=100).median().shift(1).values
    clot = np.where(jouables, C[:, DM.N - 1], np.nan)
    cl = pd.Series(clot).ffill()
    veille = cl.shift(1).values
    il_y_a_20 = cl.shift(21).values
    X, premier, vu = [], [], set()
    for _, t in tr.iterrows():
        i, m, s, p = idx[t["jour"]], int(t["minute_entree"]), int(t["sens"]), float(t["prix_entree"])
        sg = z["sigma"][i, m]
        if s > 0:
            force = (p - z["href"][i] * (1 + sg)) / (sg * z["href"][i])
        else:
            force = (z["bref"][i] * (1 - sg) - p) / (sg * z["bref"][i])
        k = ies[i]
        es = 0.0
        if k >= 0 and not np.isnan(z_es["sigma"][k, m]) and not np.isnan(z_es["href"][k]):
            pe, se = z_es["C"][k, m], z_es["sigma"][k, m]
            es = float((pe > z_es["href"][k] * (1 + se)) if s > 0 else (pe < z_es["bref"][k] * (1 - se)))
        ouv = C[i, 0]
        X.append([float(m == DM.PAS), float(60 <= m <= 120), float(150 <= m <= 240), force,
                  np.log(s30[i] / med[i]) if med[i] > 0 else 0.0, es,
                  s * (ouv / veille[i] - 1) / s30[i] if veille[i] > 0 else 0.0,
                  s * (veille[i] / il_y_a_20[i] - 1) if il_y_a_20[i] > 0 else 0.0,
                  np.log(vix.get(t["jour"], np.nan)), float(t["jour"] not in vu)])
        vu.add(t["jour"])
    return np.array(X, float)                 # valeur manquante : moyenne de l'apprentissage (ridge)


def ridge(Xa, ya, Xt):
    mu = np.nanmean(Xa, axis=0)
    sd = np.nanstd(Xa, axis=0)
    sd[sd == 0] = 1
    A = np.nan_to_num((Xa - mu) / sd)
    T = np.nan_to_num((Xt - mu) / sd)
    lam = LAMBDA * len(A)
    b = np.linalg.solve(A.T @ A + lam * np.eye(A.shape[1]), A.T @ (ya - ya.mean()))
    return ya.mean() + T @ b, b


def t_stat(x):
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if x.std(ddof=1) > 0 else 0.0


def main():
    rech = pd.read_csv(DM.RECHERCHE)
    robot = pd.read_csv(DM.ROBOT)
    bars = pd.concat([rech, robot[robot["t"] > rech["t"].iloc[-1]]], ignore_index=True)
    z = DM.preparer(bars)
    tr = DM.trades_zone(z, "2011-01-01", FIN_ES)
    fed = set(pd.DatetimeIndex(fomc.annonces()))
    tr = tr[~tr["jour"].isin(fed)].reset_index(drop=True)
    z_es = DM.preparer(pd.read_csv(ES))
    ies = zone_es(z, z_es)
    v = pd.read_csv(VIX, usecols=["t", "c"])
    v["t"] = pd.to_datetime(v["t"])
    vs = v.set_index("t")["c"].sort_index()
    vix = {j: float(vs[vs.index < j].iloc[-1]) for j in tr["jour"].unique()}
    X = informations(z, tr, z_es, ies, vix)
    p = tr["prix_entree"].values
    sg = z["sigma"][[{j: i for i, j in enumerate(z["jours"])}[d] for d in tr["jour"]], tr["minute_entree"].values]
    y = tr["points"].values / (p * sg)
    an = tr["jour"].dt.year.values
    garde = np.ones(len(tr), bool)
    pred = np.full(len(tr), np.nan)
    L = ["Etude large, partie B (etude_large/README.md, regles fixees le 22 octobre 2026 avant tout calcul)",
         f"Zone du bot V1 sans filtre, NQ minute, sans les jours de la Fed : {len(tr)} trades du "
         f"{tr['jour'].min().date()} au {tr['jour'].max().date()}.", "",
         "Walk-forward (apprentissage sur toutes les annees precedentes, depuis 2011) :",
         "  annee  apprentissage  trades  gardes  points tous  points gardes  difference"]
    for Y in ANNEES:
        a, t = an < Y, an == Y
        if not t.any():
            continue
        pr, b = ridge(X[a], y[a], X[t])
        pred[t] = pr
        garde[t] = pr > 0
        pts = tr["points"].values[t]
        L.append(f"  {Y}  {int(a.sum()):>12}  {int(t.sum()):>6}  {int(garde[t].sum()):>6}  {pts.sum():+11.1f}  "
                 f"{pts[garde[t]].sum():+13.1f}  {pts[garde[t]].sum() - pts.sum():+10.1f}")
    # serie quotidienne en rendement (points / prix d'entree), 2016 - fin, toutes les seances jouables hors Fed
    oos = an >= 2016
    jours = pd.DatetimeIndex([z["jours"][i] for i in z["jouables"]])
    jours = jours[(jours >= "2016-01-01") & (jours <= FIN_ES) & ~jours.isin(fed)]
    r = pd.Series(tr["points"].values / p, index=tr["jour"])
    tous = r[oos].groupby(level=0).sum().reindex(jours).fillna(0.0)
    gard = r[oos & garde].groupby(level=0).sum().reindex(jours).fillna(0.0)
    diff = gard - tous
    p1, p2 = jours.year <= 2022, jours.year >= 2023
    part = garde[oos].mean()
    c1 = t_stat(diff) >= 2.0
    c2 = diff[p1].sum() > 0 and diff[p2].sum() > 0
    c3 = part >= 0.5
    ref = float(z["C"][z["jouables"][-1], DM.N - 1])
    dollars = lambda m: float((tr["points"].values[m] / p[m] * ref * DM.RB.PT).sum())  # noqa: E731
    L += ["", "Hors echantillon 2016 - 2026 (series quotidiennes en rendement) :",
          f"  tous les trades : t {t_stat(tous):+.2f} (2016-2022 {t_stat(tous[p1]):+.2f}, 2023-2026 {t_stat(tous[p2]):+.2f}), "
          f"{dollars(oos):+,.0f} $ pour 1 MNQ au prix d'aujourd'hui",
          f"  trades gardes   : t {t_stat(gard):+.2f} (2016-2022 {t_stat(gard[p1]):+.2f}, 2023-2026 {t_stat(gard[p2]):+.2f}), "
          f"{dollars(oos & garde):+,.0f} $",
          f"  trades ecartes  : {int((oos & ~garde).sum())}, {dollars(oos & ~garde):+,.0f} $",
          "", "Decision fixee d'avance :",
          f"  1. t de la difference quotidienne {t_stat(diff):+.2f} >= 2,0 : {'oui' if c1 else 'NON'}",
          f"  2. difference positive sur 2016-2022 ({diff[p1].sum() * 1e4:+.1f} pb) et 2023-2026 ({diff[p2].sum() * 1e4:+.1f} pb) : "
          f"{'oui' if c2 else 'NON'}",
          f"  3. trades gardes {part * 100:.1f} % >= 50 % : {'oui' if c3 else 'NON'}",
          f"  -> {'ADOPTE' if c1 and c2 and c3 else 'NON ADOPTE : la zone reste telle quelle'}"]
    # information : le modele appris sur tout 2011 - 2025, et chaque information seule (correlation avec le resultat)
    a = an <= 2025
    _, b = ridge(X[a], y[a], X[a][:1])
    L += ["", "Pour information, coefficients du modele appris sur 2011 - 2025 (informations centrees reduites) et "
          "correlation de chaque information avec le resultat (2011 - 2015 | 2016 - 2026) :"]
    for k, nom in enumerate(NOMS):
        def corr(m):
            x = X[m, k]
            ok = ~np.isnan(x)
            return float(np.corrcoef(x[ok], y[m][ok])[0, 1]) if x[ok].std() > 0 else 0.0
        L.append(f"  {nom:<20} {b[k]:+.4f}   {corr(an < 2016):+.3f} | {corr(an >= 2016):+.3f}")
    (ICI / "resultats_b.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
