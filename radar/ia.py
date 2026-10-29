#!/usr/bin/env python3
"""Radar, modele d'apprentissage (radar/README.md, protocole du 29 octobre 2026) : pour chacun des 49 couples
entree-duree, une regression logistique (L2) et des arbres de decision boostes (HistGradientBoostingClassifier, reglages
par defaut) voient toutes les variables et predisent le sens du mouvement. Entraines sur toutes les seances avant
l'annee Y, ils predisent l'annee Y (2015 - 2026). Trade quand la probabilite s'ecarte de 0,5 plus que pour 70 % des
seances d'entrainement. Selection sur 2015 - 2022 (t >= 3,3), coffre 2023 - 2026 seulement avec --coffre.

Lancer : RADAR_CALCUL=<dossier de variables.npz> python3 radar/ia.py [--coffre]"""
import argparse
import time
import warnings
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

import scan as SC

warnings.filterwarnings("ignore", category=RuntimeWarning)
ICI = Path(__file__).resolve().parent
CALCUL = SC.CALCUL
RESULTATS = ICI / "resultats"
ANNEES = range(2015, 2027)
BARRE_OOS = 3.3


def predire(X, y, ok, annees, modele):
    """Probabilites hors echantillon (annee par annee) et seuil d'ecart de chaque annee."""
    p = np.full(len(y), np.nan)
    delta = np.full(len(y), np.nan)
    for Y in ANNEES:
        tr = ok & (annees < Y) & np.isfinite(y)
        te = ok & (annees == Y)
        if tr.sum() < 500 or te.sum() == 0:
            continue
        Xtr, Xte = X[tr], X[te]
        fin = np.isfinite(Xtr)
        garde = (fin.sum(0) >= 100) & (np.nanstd(np.where(fin, Xtr, np.nan), 0) > 0)   # variables deja presentes
        Xtr, Xte = Xtr[:, garde], Xte[:, garde]
        if modele == "logistique":
            m = np.nanmean(Xtr, 0)
            s = np.nanstd(Xtr, 0)
            s = np.where(s > 0, s, 1.0)
            Xtr = np.clip(np.nan_to_num((Xtr - m) / s), -5, 5)
            Xte = np.clip(np.nan_to_num((Xte - m) / s), -5, 5)
            mod = LogisticRegression(max_iter=2000)
        else:
            mod = HistGradientBoostingClassifier(random_state=0)
        mod.fit(Xtr, y[tr] > 0)
        ptr = mod.predict_proba(Xtr)[:, 1]
        p[te] = mod.predict_proba(Xte)[:, 1]
        delta[te] = np.quantile(np.abs(ptr - 0.5), 0.7)
    return p, delta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coffre", action="store_true")
    a = ap.parse_args()
    d = SC.charger()
    annees = np.asarray(d["jours"].year)
    ok = d["ok"].astype(bool)
    cache = CALCUL / "ia_predictions.npz"
    if cache.exists():
        z = np.load(cache)
        P, D = z["P"], z["D"]
    else:
        P = np.full((2, len(d["cles"]), len(annees)), np.nan)
        D = np.full_like(P, np.nan)
        t0 = time.time()
        for ih, (e, H) in enumerate(d["cles"]):
            ie = list(d["entrees"]).index(e)
            X = np.column_stack([d["cube"][ie].astype(float), d["B"].astype(float)])
            g = d["gains"][ih]
            for im, modele in enumerate(("logistique", "arbres")):
                P[im, ih], D[im, ih] = predire(X, g, ok & np.isfinite(g), annees, modele)
            print(f"{e} min, {H or 'cloture'} : {time.time() - t0:.0f} s", flush=True)
        np.savez_compressed(cache, P=P, D=D)
    lignes = []
    for im, modele in enumerate(("logistique", "arbres")):
        for ih, (e, H) in enumerate(d["cles"]):
            g = d["gains"][ih]
            p, dl = P[im, ih], D[im, ih]
            sens = np.where(p > 0.5 + dl, 1.0, np.where(p < 0.5 - dl, -1.0, 0.0))
            net = np.where((sens != 0) & np.isfinite(g) & ok, sens * g - SC.FRAIS, np.nan)
            oos = (annees >= 2015) & (annees <= 2022)
            n, m, t = SC.t_serie(net[oos])
            lignes.append(dict(modele=modele, e=e, H=H, n_oos=n, moy_oos=m, t_oos=t, ih=ih, im=im))
    T = pd.DataFrame(lignes).sort_values("t_oos", ascending=False)
    retenus = T[T["t_oos"] >= BARRE_OOS]
    L = ["Radar, modele d'apprentissage (radar/README.md, protocole du 29 octobre 2026)", "",
         f"98 modeles (49 couples entree-duree x 2), predictions hors echantillon 2015 - 2022, barre t >= {BARRE_OOS}",
         f"Retenus : {len(retenus)}", "", "Les 15 meilleurs hors echantillon 2015 - 2022 :", ""]
    for _, r in T.head(15).iterrows():
        h, mi = divmod(570 + int(r["e"]), 60)
        L.append(f"  {r['modele']:<10} {h} h {mi:02d}, {'cloture' if r['H'] == 0 else str(int(r['H'])) + ' min':<8} "
                 f"n {int(r['n_oos']):4d}  moy {r['moy_oos']:+7.2f} $  t {r['t_oos']:5.2f}")
    if a.coffre and len(retenus):
        mm = len(retenus)
        seuil = NormalDist().inv_cdf(1 - 0.05 / mm)
        L += ["", f"COFFRE 2023 - 2026 : seuil t >= {seuil:.2f} (Bonferroni pour {mm}), 3 annees sur 4", ""]
        for _, r in retenus.iterrows():
            ih, im = int(r["ih"]), int(r["im"])
            g, p, dl = d["gains"][ih], P[im, ih], D[im, ih]
            sens = np.where(p > 0.5 + dl, 1.0, np.where(p < 0.5 - dl, -1.0, 0.0))
            net = np.where((sens != 0) & np.isfinite(g) & ok & (annees >= 2023), sens * g - SC.FRAIS, np.nan)
            n, m, t = SC.t_serie(net)
            ans = pd.Series(net, index=d["jours"]).dropna().groupby(lambda j: j.year).sum()
            passe = m > 0 and t >= seuil and (ans > 0).sum() >= 3
            L.append(f"  {'PASSE' if passe else 'echoue'}  {r['modele']} {int(r['e'])} min {int(r['H'])}  n {n}  "
                     f"moy {m:+.2f} $  t {t:.2f}  " + ", ".join(f"{y} {v:+.0f}" for y, v in ans.items()))
    RESULTATS.mkdir(parents=True, exist_ok=True)
    (RESULTATS / ("ia_coffre.txt" if a.coffre else "ia.txt")).write_text("\n".join(L) + "\n")
    T.to_csv(RESULTATS / "ia_modeles.csv", index=False, float_format="%.4f")
    print("\n".join(L))


if __name__ == "__main__":
    main()
