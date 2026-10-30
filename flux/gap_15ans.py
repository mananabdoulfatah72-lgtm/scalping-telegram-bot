#!/usr/bin/env python3
"""Partie 10 (flux/README.md) : la regle figee de l'ecart d'ouverture (achat le matin toutes les 15 minutes de 9 h 45 a
11 h 30, 60 minutes, si l'ecart d'ouverture divise par le range moyen des minutes de la seance depasse le seuil fige)
rejouee telle quelle sur les minutes du NQ 2011 - 2026, annees qui n'ont servi ni a la choisir ni a la confirmer.
$ par MNQ au prix de reference du projet, frais 3 $ l'aller-retour.

Lancer : python3 flux/gap_15ans.py <minutes NQ au format t,o,h,l,c,v,contrat (2011 - 2026)>"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "scalping"))
import donnees as SD  # noqa: E402


def main():
    regle = json.loads((ICI / "resultats/partie10/regles_figees.json").read_text())["regles"][0]
    seuils = {int(e): q[4] for e, q in regle["conditions"][0]["seuils"].items()}
    d = SD.minutes("NQ", chemin=sys.argv[1], debut="2011-01-01")
    O, H, L = d["o"], d["h"], d["l"]
    C = d["c"]
    ok = d["complete"] & ~d["ech"]
    pm = d["prec_meme"]
    ech = float(d["pref"]) / O[:, 0] * float(d["pt"])
    rng = np.cumsum(H - L, 1) / np.arange(1, 391)
    lignes = []
    for s in range(len(O)):
        if not ok[s] or pm[s] < 0:
            continue
        prevC = C[pm[s], 389]
        for e in range(15, 121, 15):
            a = max(rng[s, e - 1], 1.0)
            if (O[s, 0] - prevC) / a > seuils[e]:
                lignes.append((d["jours"][s], e, (O[s, min(e + 60, 389)] - O[s, e]) * ech[s] - 3.0))
    t = pd.DataFrame(lignes, columns=["jour", "e", "gain"])
    t["jour"] = pd.to_datetime(t["jour"])
    j = t.groupby("jour")["gain"].sum()

    def stat(x):
        return len(x), x.sum(), x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 1 else np.nan
    L = ["# Règle de l'écart d'ouverture (partie 10) rejouée sur 15 ans", "",
         f"{ok.sum()} séances du NQ ({pd.Timestamp(d['jours'][0]).date()} - {pd.Timestamp(d['jours'][-1]).date()}). "
         "Gains par journée (tous les trades du matin additionnés), $ pour 1 MNQ au prix d'aujourd'hui, frais compris.", "",
         "| Années | Journées jouées | Trades | Total | t par journée |", "|---|---|---|---|---|"]
    for nom, m in (("2011 - mars 2026 (jamais vues par le scan)", j.index < "2026-04-01"),
                   ("avril - juillet 2026 (exploration)", (j.index >= "2026-04-01") & (j.index <= "2026-07-15")),
                   ("juillet - octobre 2026 (confirmation)", j.index > "2026-07-15")):
        n, tot, tt = stat(j[m])
        L.append(f"| {nom} | {n} | {int(t['jour'].isin(j[m].index).sum())} | {tot:+,.0f} $ | {tt:+.2f} |")
    L += ["", "| Année | Journées | Total | t par journée |", "|---|---|---|---|"]
    for an, x in j.groupby(j.index.year):
        n, tot, tt = stat(x)
        L.append(f"| {an} | {n} | {tot:+,.0f} $ | {tt:+.2f} |")
    (ICI / "resultats/partie10/gap_15ans.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
