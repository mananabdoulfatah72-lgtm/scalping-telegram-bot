#!/usr/bin/env python3
"""Couche de risque R1 / R2 (audit/README.md, fixée le 1er novembre 2026 avant calcul), sur le modèle du bot de l'ami.

R1 : stop par trade à 1 % du compte (500 $), soit 500 / (2 $ x MNQ) points du prix d'entrée au prix d'aujourd'hui.
     Après le stop, le trade est traité comme écarté (le trade suivant de la zone reste celui du rejeu).
R2 : après un trade perdant, plus de trade de zone ce jour-là.
Les deux s'ajoutent à la limite de perte du jour de 1 000 $ (déjà dans le bot), vérifiée sur le plus bas / plus haut de
chaque minute. Gains au prix d'aujourd'hui (points x 30 900 / prix), frais fixes de 3 $ par MNQ.

Lancer : python3 audit/risque.py <trades du rejeu (Bot3en1.Replay)> <minutes NQ t,o,h,l,c,v,contrat> [--challenge]
"""
import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

PREF = 30900.0
FRAIS = 3.0
LIMITE = 1000.0
RISQUE = 500.0
GLISSE = 0.25          # glissement d'un tick sur un stop
GLISSE_LIMITE = 1.0    # la limite du jour attend 3 s de confirmation
LIGNE = re.compile(r"^(\d{4}-\d{2}-\d{2}) (achat|vente|sortie|stop)\b(?: (\d+)h(\d+))?(?: (\d+)h(\d+))?.*? a ([0-9.]+)")
REGLES = {"zone d'origine": (False, False), "R1": (True, False), "R2": (False, True), "R1+R2": (True, True)}


def lire_trades(f):
    out, ouvert = [], None
    for l in Path(f).read_text().splitlines():
        m = LIGNE.match(l)
        if not m or "ecarte" in l:
            continue
        j, quoi = m.group(1), m.group(2)
        h, mi = int(m.group(5) or m.group(3)), int(m.group(6) or m.group(4))
        mm = h * 60 + mi - 570
        prix = float(m.group(7))
        if quoi in ("achat", "vente"):
            ouvert = (j, 1 if quoi == "achat" else -1, mm, prix)
        elif ouvert:
            out.append(dict(jour=ouvert[0], sens=ouvert[1], me=ouvert[2], entree=ouvert[3], mx=mm, sortie=prix))
            ouvert = None
    return pd.DataFrame(out)


def lire_minutes(f, jours):
    d = pd.read_csv(f, usecols=["t", "o", "h", "l"])
    d["jour"] = d["t"].str[:10]
    d = d[d["jour"].isin(jours)]
    d["m"] = d["t"].str[11:13].astype(int) * 60 + d["t"].str[14:16].astype(int) - 570
    return {j: (g["m"].to_numpy(), g["o"].to_numpy(), g["h"].to_numpy(), g["l"].to_numpy()) for j, g in d.groupby("jour")}


def journee(trades, minutes, n, r1, r2):
    """Résultat de la journée (en $ au prix d'aujourd'hui) et pire valeur en cours de séance, pour n MNQ."""
    realise, pire, arret, perte = 0.0, 0.0, False, False
    detail = []
    for t in trades:
        if arret or (r2 and perte):
            detail.append(None)
            continue
        s, e, k = t["sens"], t["entree"], PREF / t["entree"]
        valeur = lambda px: n * (2 * s * (px - e) * k - FRAIS)
        stop = e - s * (RISQUE / (2 * n)) / k
        sortie, quoi = t["sortie"], "regle"
        g = minutes.get(t["jour"])
        if g is not None:
            mm, oo, hh, ll = g
            sel = (mm > t["me"]) & (mm <= t["mx"])
            for o, adverse in zip(oo[sel], (ll if s > 0 else hh)[sel]):
                if r1 and s * (adverse - stop) <= 0:
                    sortie = (min(o, stop) - GLISSE) if s > 0 else (max(o, stop) + GLISSE)
                    quoi = "stop 1 %"
                    break
                v = realise + valeur(adverse)
                pire = min(pire, v)
                if v <= -LIMITE:
                    niveau = e + s * ((-LIMITE - realise) / n + FRAIS) / (2 * k)
                    sortie = (min(o, niveau) - GLISSE_LIMITE) if s > 0 else (max(o, niveau) + GLISSE_LIMITE)
                    quoi, arret = "limite du jour", True
                    break
        r = valeur(sortie)
        pire = min(pire, realise + r)
        realise += r
        perte = perte or r < 0
        detail.append((quoi, r))
    return realise, pire, detail


def stats(serie):
    if len(serie) < 2:
        return serie.sum(), np.nan, np.nan
    cum = serie.cumsum()
    return serie.sum(), serie.mean() / serie.std(ddof=1) * np.sqrt(len(serie)), (cum - cum.cummax()).min()


def challenge(res4, res6, debut_idx, seances=22, fin=5):
    """Un challenge Bulenox 50K à partir de la séance debut_idx : 'reussi', 'echoue' ou 'ni l'un ni l'autre'."""
    solde, haut = 50000.0, 50000.0
    for i in range(seances):
        j = debut_idx + i
        if j >= len(res4):
            return None
        seuil = min(haut - 2500, 50100)
        r, pire = (res6[j] if i >= seances - fin else res4[j])
        if solde + pire <= seuil:
            return "echoue"
        solde += r
        if solde >= 53000:
            return "reussi"
        haut = max(haut, solde)
    return "ni l'un ni l'autre"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trades")
    ap.add_argument("minutes")
    ap.add_argument("--challenge", action="store_true")
    ap.add_argument("--detail", help="jours à détailler, AAAA-MM-JJ séparés par des virgules")
    x = ap.parse_args()
    t = lire_trades(x.trades)
    tous = sorted(pd.read_csv(x.minutes, usecols=["t"])["t"].str[:10].unique())
    tous = [j for j in tous if j >= t["jour"].min() and j <= t["jour"].max()]
    minutes = lire_minutes(x.minutes, set(t["jour"]))
    par_jour = {j: g.to_dict("records") for j, g in t.groupby("jour")}
    res = {}
    for nom, (r1, r2) in REGLES.items():
        for n in (4, 6):
            res[(nom, n)] = {j: journee(par_jour.get(j, []), minutes, n, r1, r2) for j in tous}
    P = [("2011 - 2018", "2011", "2018-12-31"), ("2019 - 2022", "2019", "2022-12-31"), ("2023 - 2026", "2023", "2026-12-31"),
         ("15 ans", "2011", "2026-12-31")]
    print("| Règles (4 MNQ, limite du jour 1 000 $) | " + " | ".join(p for p, _, _ in P) + " | t (15 ans) | Pire journée | Pire trade | Plus forte baisse |")
    print("|---" * (len(P) + 5) + "|")
    for nom in REGLES:
        d = res[(nom, 4)]
        s = pd.Series({j: v[0] for j, v in d.items()})
        cells = [f"{s[(s.index >= a) & (s.index <= b)].sum():+,.0f} $" for _, a, b in P]
        g, tt, dd = stats(s)
        pires = [r for v in d.values() for x in v[2] if x for r in [x[1]]]
        print(f"| {nom} | " + " | ".join(cells) + f" | {tt:.2f} | {s.min():+,.0f} $ | {min(pires):+,.0f} $ | {dd:+,.0f} $ |")
    if x.detail:
        for j in x.detail.split(","):
            print(f"\n{j} :")
            for nom in REGLES:
                v = res[(nom, 4)].get(j)
                if v:
                    print(f"  {nom:16s} journée {v[0]:+8,.0f} $ ; trades : " + ", ".join(
                        "pas pris" if z is None else f"{z[1]:+,.0f} $ ({z[0]})" for z in v[2]))
    if x.challenge:
        print("\n| Règles | Départs | Réussis | Échoués | Ni l'un ni l'autre (22 séances) |\n|---|---|---|---|---|")
        for depuis in ("2011", "2019"):
            for nom in REGLES:
                r4 = [res[(nom, 4)][j][:2] for j in tous]
                r6 = [res[(nom, 6)][j][:2] for j in tous]
                issues = [challenge(r4, r6, i) for i, j in enumerate(tous) if j >= depuis]
                issues = [z for z in issues if z]
                n = len(issues)
                c = [issues.count(k) / n * 100 for k in ("reussi", "echoue", "ni l'un ni l'autre")]
                print(f"| {nom} | {depuis} - 2026 ({n}) | {c[0]:.1f} % | {c[1]:.1f} % | {c[2]:.1f} % |")


if __name__ == "__main__":
    main()
