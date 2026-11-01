#!/usr/bin/env python3
"""Juge les corrections de pertes C1 à C7 sur des challenges Bulenox 50K simulés (critère fixé le 1er novembre 2026,
audit/README.md). Chaque variante est un rejeu de 15 ans (Bot3en1.Replay, sans le filtre delta).

Lancer : python3 audit/corrections_challenge.py <minutes NQ.csv> nom=fichier [nom=fichier ...] [--c6 fichier_avec_NIVEAU]
"""
import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import risque  # noqa: E402

NIV = re.compile(r"\[niveau de sortie ([0-9.]+)\]")


def lire(f, c6=False):
    t = risque.lire_trades(f)
    if c6:
        niv = []
        for l in Path(f).read_text().splitlines():
            if re.match(r"^\d{4}-\d{2}-\d{2} (achat|vente) \d", l) and "ecarte" not in l:
                niv.append(float(NIV.search(l).group(1)))
        t["dist"] = (t["entree"] - np.array(niv[:len(t)])).abs() * risque.PREF / t["entree"]
    return t


def journee(trades, minutes, n):
    """Comme risque.journee sans R1 / R2, avec la taille de C6 si le trade a une distance au niveau de sortie."""
    realise, pire, arret = 0.0, 0.0, False
    for t in trades:
        if arret:
            continue
        nt = n
        if "dist" in t and not pd.isna(t["dist"]):
            nt = int(min(n, np.floor(risque.RISQUE / (2 * max(t["dist"], 1e-9)))))
            if nt <= 0:
                continue
        s, e, k = t["sens"], t["entree"], risque.PREF / t["entree"]
        valeur = lambda px: nt * (2 * s * (px - e) * k - risque.FRAIS)
        sortie = t["sortie"]
        g = minutes.get(t["jour"])
        if g is not None:
            mm, oo, hh, ll = g
            sel = (mm > t["me"]) & (mm <= t["mx"])
            for o, adverse in zip(oo[sel], (ll if s > 0 else hh)[sel]):
                v = realise + valeur(adverse)
                pire = min(pire, v)
                if v <= -risque.LIMITE:
                    niveau = e + s * ((-risque.LIMITE - realise) / nt + risque.FRAIS) / (2 * k)
                    sortie = (min(o, niveau) - risque.GLISSE_LIMITE) if s > 0 else (max(o, niveau) + risque.GLISSE_LIMITE)
                    arret = True
                    break
        r = valeur(sortie)
        pire = min(pire, realise + r)
        realise += r
    return realise, pire


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("minutes")
    ap.add_argument("variantes", nargs="+")
    ap.add_argument("--c6")
    x = ap.parse_args()
    var = [v.split("=", 1) for v in x.variantes]
    trades = {nom: lire(f) for nom, f in var}
    if x.c6:
        trades["C6"] = lire(x.c6, c6=True)
    tous = sorted(pd.read_csv(x.minutes, usecols=["t"])["t"].str[:10].unique())
    debut, fin = min(t["jour"].min() for t in trades.values()), max(t["jour"].max() for t in trades.values())
    tous = [j for j in tous if debut <= j <= fin]
    minutes = risque.lire_minutes(x.minutes, set().union(*[set(t["jour"]) for t in trades.values()]))
    print("| Variante | Gain 15 ans (4 MNQ, limite du jour) | t | Pire journée | Départs | Réussis | Échoués | Ni l'un ni l'autre |")
    print("|---|---|---|---|---|---|---|---|")
    for nom, t in trades.items():
        par_jour = {j: g.to_dict("records") for j, g in t.groupby("jour")}
        r4 = [journee(par_jour.get(j, []), minutes, 4) for j in tous]
        r6 = [journee(par_jour.get(j, []), minutes, 6) for j in tous]
        s = pd.Series([r[0] for r in r4])
        g, tt, dd = risque.stats(s)
        for depuis in ("2011", "2019"):
            issues = [risque.challenge(r4, r6, i) for i, j in enumerate(tous) if j >= depuis]
            issues = [z for z in issues if z]
            c = [issues.count(k) / len(issues) * 100 for k in ("reussi", "echoue", "ni l'un ni l'autre")]
            print(f"| {nom} | {g:+,.0f} $ | {tt:.2f} | {s.min():+,.0f} $ | {depuis} - 2026 ({len(issues)}) | {c[0]:.2f} % | {c[1]:.2f} % | {c[2]:.2f} % |")


if __name__ == "__main__":
    main()
