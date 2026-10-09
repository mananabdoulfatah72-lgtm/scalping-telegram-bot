#!/usr/bin/env python3
"""Vague 4, partie B (README.md) : sources de largeur des 10 plus grosses valeurs du Nasdaq 100, sur le NQ (1 MNQ),
exploration 2016-2022 avec 1 000 tirages au hasard du sens de chaque trade. Le coffre (2023 - sept. 2026) n'est lu que
pour les survivantes, une seule fois (coffre=True). Ecrit partie_b.txt."""
import sys

import numpy as np
import pandas as pd

import donnees4 as D4

K = D4.K
COUT = 1.5                                  # points par aller-retour (comme la zone)
SORTIE = 384                                # cloture de la minute de 15 h 54 : sortie a 15 h 55
SOURCES = {"B1 largeur a 10 h": 30, "B2 largeur a 11 h": 90, "B3 hausse etroite a 10 h 30": 60}
N_HASARD = 1000


def largeur(jours, minute):
    """Part des grandes valeurs au-dessus de leur ouverture de 9 h 30, a la fin de la minute `minute` - 1 (colonne c{minute}),
    par seance ; NaN si moins de 8 valeurs connues."""
    g = pd.read_csv(D4.ICI / "donnees" / "grandes.csv.gz")
    g["haut"] = (g[f"c{minute}"] > g["ouverture"]).astype(float)
    g.loc[g[f"c{minute}"].isna() | g["ouverture"].isna(), "haut"] = np.nan
    x = g.groupby("jour")["haut"].agg(["mean", "count"])
    part = x["mean"].where(x["count"] >= 8)
    return part.reindex(pd.DatetimeIndex(jours).strftime("%Y-%m-%d")).to_numpy()


def signaux(D, nom):
    """Sens (+1, -1, 0) de chaque seance pour la source nom, et minute d'entree."""
    m = SOURCES[nom]
    part = largeur(D["jours"], m)
    O, C, der = D["O"], D["C"], D["derniere"]
    plein = der == 389
    sens = np.zeros(len(part), np.int64)
    if nom.startswith("B3"):
        nq = C[:, m - 1] - O[:, 0]
        sens[(nq > 0) & (part <= 0.3)] = -1
        sens[(nq < 0) & (part >= 0.7)] = 1
    else:
        sens[part >= 0.9] = 1
        sens[part <= 0.1] = -1
    sens[~plein | np.isnan(part)] = 0
    return sens, m - 1


def rendements(D, sens, me):
    C = D["C"]
    e, s = C[:, me], C[:, SORTIE]
    r = np.where(sens != 0, sens * (s / e - 1) - COUT / e, 0.0)
    dol = np.where(sens != 0, (sens * (s - e) - COUT) * 2.0, 0.0)
    return r, dol


def t_stat(x):
    s = x.std()
    return float(x.mean() / s * np.sqrt(len(x))) if s > 0 else 0.0


def evaluer(D, nom, debut, fin, graine=11):
    j = D["jours"]
    sens, me = signaux(D, nom)
    per = (j >= pd.Timestamp(debut)) & (j <= pd.Timestamp(fin))
    r, dol = rendements(D, sens, me)
    r, dol, sp = r[per], dol[per], sens[per]
    t = t_stat(r)
    rng = np.random.default_rng(graine)
    C = D["C"][per]
    e, s = C[:, me], C[:, SORTIE]
    brut = np.where(sp != 0, s / e - 1, 0.0)
    frais = np.where(sp != 0, COUT / e, 0.0)
    ts = np.array([t_stat(np.where(sp != 0, rng.choice([-1, 1], len(sp)) * brut - frais, 0.0)) for _ in range(N_HASARD)])
    annees = pd.Series(dol, index=j[per]).groupby(j[per].year).sum()
    return {"t": t, "hasard": float((ts < t).mean()), "trades": int((sp != 0).sum()), "achats": int((sp == 1).sum()),
            "dollars": float(dol.sum()), "annees": annees}


def main(coffre=False):
    D = D4.charger()
    L = ["Vague 4, partie B : largeur des 10 plus grosses valeurs du Nasdaq 100, NQ 1 MNQ, sortie 15 h 55, 1,5 point de frais",
         "", "=== Exploration 2016-2022 (survie : t >= 2 et t au-dessus de 95 % de 1 000 tirages du sens)",
         "source | trades (dont achats) | t | bat le hasard | $ pour 1 MNQ (prix de l'epoque) | verdict"]
    surv = []
    for nom in SOURCES:
        x = evaluer(D, nom, "2016-01-01", "2022-12-31")
        ok = x["t"] >= 2 and x["hasard"] >= 0.95
        L.append(f"{nom} | {x['trades']} ({x['achats']}) | {x['t']:+.2f} | {x['hasard']:.1%} | {x['dollars']:+,.0f} | "
                 + ("SURVIT" if ok else "eliminee"))
        if ok:
            surv.append(nom)
    L.append(f"Survivantes : {len(surv)}")
    if surv and coffre:
        seuil = {1: 1.65, 2: 1.96, 3: 2.13}[len(surv)]
        L += ["", f"=== Coffre 2023 - sept. 2026 (t >= {seuil}, positif 3 annees sur 4)"]
        for nom in surv:
            x = evaluer(D, nom, "2023-01-01", "2026-12-31")
            pos = int((x["annees"] > 0).sum())
            L.append(f"{nom} | t {x['t']:+.2f} | annees positives {pos}/{len(x['annees'])} | {x['dollars']:+,.0f} $ -> "
                     + ("PASSE" if x["t"] >= seuil and pos >= 3 else "echoue"))
    (D4.ICI / "partie_b.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main(coffre="--coffre" in sys.argv)
