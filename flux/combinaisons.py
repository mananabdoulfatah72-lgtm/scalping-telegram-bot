#!/usr/bin/env python3
"""Partie 4 (flux/README.md) : combinaisons de strategies en walk-forward (M1 portefeuille des solides, M2 meilleure
combinaison), temoins fixes (ZONE seule, toutes), et controle sans avantage (200 tirages). Lit FLUX_CALCUL/matrice.pkl.

Lancer : python3 flux/combinaisons.py   (apres flux/matrice.py)"""
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
CALCUL = Path(os.getenv("FLUX_CALCUL", Path(tempfile.gettempdir()) / "flux_calcul"))
ANNEES_JOUEES = list(range(2014, 2027))
TIRAGES = 200


def t_stat(x):
    x = np.asarray(x, float)
    s = x.std(ddof=1) if len(x) > 1 else 0.0
    return float(x.mean() / s * np.sqrt(len(x))) if s > 0 else 0.0


def m1(X, ans):
    """Strategies au t >= 2 et positives au moins 2 annees sur 3 sur le passe."""
    choix = []
    for j in range(X.shape[1]):
        x = X[:, j]
        par_an = pd.Series(x).groupby(ans).sum()
        if t_stat(x) >= 2 and (par_an > 0).mean() >= 2 / 3:
            choix.append(j)
    return choix


def m2(X, ans, k_max=4):
    """Glouton : meilleur t, puis ajout de la strategie qui augmente le plus le t de la somme (4 au plus)."""
    ts = [t_stat(X[:, j]) for j in range(X.shape[1])]
    j0 = int(np.argmax(ts))
    if ts[j0] <= 0:
        return []
    choix, somme, t_cour = [j0], X[:, j0].copy(), ts[j0]
    while len(choix) < k_max:
        meilleur, jm = t_cour, None
        for j in range(X.shape[1]):
            if j in choix:
                continue
            tj = t_stat(somme + X[:, j])
            if tj > meilleur:
                meilleur, jm = tj, j
        if jm is None:
            break
        choix.append(jm)
        somme += X[:, jm]
        t_cour = meilleur
    return choix


def walk_forward(X, ans, methode):
    """Serie hors echantillon (annees 2014 - 2026) et strategies choisies chaque annee."""
    hors, choix_par_an = [], {}
    for Y in ANNEES_JOUEES:
        passe, joue = ans < Y, ans == Y
        if not joue.any():
            continue
        choix = methode(X[passe], ans[passe])
        choix_par_an[Y] = choix
        hors.append(X[joue][:, choix].sum(axis=1) if choix else np.zeros(joue.sum()))
    return np.concatenate(hors), choix_par_an


def resume(x, ans_hors):
    par_an = pd.Series(x).groupby(ans_hors).sum()
    cum = np.cumsum(x)
    return dict(t=t_stat(x), total=float(x.sum()), annees_pos=int((par_an > 0).sum()), annees=len(par_an),
                baisse=float((cum - np.maximum.accumulate(cum)).min()), par_an=par_an)


def main():
    M = pd.read_pickle(CALCUL / "matrice.pkl").fillna(0.0)
    noms = list(M.columns)
    X = M.to_numpy()
    ans = M.index.year.to_numpy()
    hors_msk = np.isin(ans, ANNEES_JOUEES)
    ans_hors = ans[hors_msk]
    res = {}
    res["ZONE seule"] = (X[hors_msk, noms.index("ZONE")], None)
    res["Toutes, 1 MNQ chacune"] = (X[hors_msk].sum(axis=1), None)
    for nom, f in (("M1 portefeuille des solides", m1), ("M2 meilleure combinaison", m2)):
        res[nom] = walk_forward(X, ans, f)
    # controle sans avantage : decalage commun d'au moins un an, puis chaque serie recentree sur zero
    rng = np.random.default_rng(2026)
    n = len(X)
    nul = {"M1 portefeuille des solides": [], "M2 meilleure combinaison": []}
    for _ in range(TIRAGES):
        k = int(rng.integers(252, n - 252))
        Xs = np.roll(X, k, axis=0)
        Xs = Xs - Xs.mean(axis=0)
        for nom, f in (("M1 portefeuille des solides", m1), ("M2 meilleure combinaison", m2)):
            nul[nom].append(t_stat(walk_forward(Xs, ans, f)[0]))
    z = resume(res["ZONE seule"][0], ans_hors)
    L = [f"Partie 4 : combinaisons de {len(noms)} strategies (NQ, $ par MNQ au prix d'aujourd'hui, frais compris), "
         f"walk-forward, annees jouees {ANNEES_JOUEES[0]} - {M.index[-1].date()} ({hors_msk.sum()} seances).", "",
         f"{'methode':<30} {'t':>6} {'total $':>10} {'annees +':>9} {'pire baisse $':>14} {'95e sans avantage':>18}"]
    decisions = {}
    for nom, (x, choix) in res.items():
        r = resume(x, ans_hors)
        p95 = np.percentile(nul[nom], 95) if nom in nul else float("nan")
        L.append(f"{nom:<30} {r['t']:+6.2f} {r['total']:+10,.0f} {r['annees_pos']:>4} / {r['annees']:<3} {r['baisse']:+14,.0f} "
                 f"{p95:+18.2f}")
        if nom in nul:
            ok = [r["t"] >= 2, r["t"] > z["t"], r["annees_pos"] >= 9, r["t"] > p95]
            decisions[nom] = ok
    L.append("")
    for nom, ok in decisions.items():
        L.append(f"Decision fixee a l'avance, {nom} : {'RETENUE' if all(ok) else 'non retenue'} "
                 f"(t >= 2 {ok[0]}, mieux que ZONE seule {ok[1]}, 9 annees positives {ok[2]}, au-dessus du hasard {ok[3]})")
    L.append("")
    for nom in ("M1 portefeuille des solides", "M2 meilleure combinaison"):
        L.append(f"{nom}, strategies choisies chaque annee :")
        for Y, ch in res[nom][1].items():
            L.append(f"  {Y} : {', '.join(noms[j] for j in ch) if ch else 'aucune'}")
    L.append("")
    L.append("Annee par annee ($ par MNQ) :")
    L.append("  annee  " + "  ".join(f"{k[:14]:>14}" for k in res))
    for Y in ANNEES_JOUEES:
        L.append(f"  {Y}   " + "  ".join(f"{resume(v[0], ans_hors)['par_an'].get(Y, 0):+14,.0f}" for v in res.values()))
    L.append("")
    L.append("Classement des strategies seules sur 2014 - 2026 (descriptif, t des gains quotidiens) :")
    ts = sorted(((t_stat(X[hors_msk, j]), noms[j], X[hors_msk, j].sum()) for j in range(len(noms))), reverse=True)
    for t, nm, tot in ts:
        L.append(f"  {nm:<5} t {t:+5.2f}, total {tot:+9,.0f} $")
    texte = "\n".join(L)
    (ICI / "resultats" / "combinaisons.txt").write_text(texte + "\n")
    print(texte)


if __name__ == "__main__":
    main()
