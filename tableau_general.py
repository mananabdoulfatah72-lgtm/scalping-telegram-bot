#!/usr/bin/env python3
"""Page d'accueil du depot (README.md) : tous les robots en argent virtuel sur une seule page, avec le
resultat de chaque jour. Relance a la fin de chaque workflow de robot."""
from pathlib import Path

import pandas as pd

ICI = Path(__file__).parent
DEPART = 50_000.0
ROBOTS = [
    ("Melange tendance + achat", "futures, 19 marches, garde la nuit", "tendance/robot/journal_melange.csv",
     "tendance/robot/TABLEAU_DE_BORD.md"),
    ("Tendance seule", "futures, 19 marches, garde la nuit", "tendance/robot/journal.csv",
     "tendance/robot/TABLEAU_DE_BORD.md"),
    ("Version 7", "5 actions technologie par mois, 50 % investi", "version7/robot/journal.csv",
     "version7/robot/TABLEAU_DE_BORD.md"),
    ("Zone de bruit + challenge Phidias 50K", "Nasdaq MNQ, intraday", "zone/robot/journal.csv",
     "zone/robot/TABLEAU_DE_BORD.md"),
]


def lire(chemin):
    p = ICI / chemin
    if not p.exists():
        return None
    j = pd.read_csv(p)
    return j if len(j) else None


def main():
    resume, par_jour = [], {}
    for nom, quoi, journal, detail in ROBOTS:
        j = lire(journal)
        if j is None:
            resume.append(f"| {nom} | {quoi} | lance, premiere seance a venir | | | | [detail]({detail}) |")
            continue
        dernier = j.iloc[-1]
        if nom.startswith("Zone"):
            depuis = j["gain"].sum()
            solde = f"{dernier['solde']:,.0f} $ ({dernier['phase']} n°{int(dernier['tentative'])})"
        else:
            depuis = dernier["solde"] - DEPART
            solde = f"{dernier['solde']:,.0f} $"
        resume.append(f"| {nom} | {quoi} | {j['date'].iloc[0]} | {solde} | {dernier['gain']:+,.0f} $ ({dernier['date']}) |"
                      f" {depuis:+,.0f} $ | [detail]({detail}) |")
        par_jour[nom] = j.groupby("date")["gain"].sum()
    lignes = [
        "# Tableau de bord des robots (argent virtuel)",
        "",
        "Chaque robot suit un compte **virtuel** de 50 000 $ : aucun ordre reel, aucun argent engage. Cette page est "
        "mise a jour chaque soir de semaine apres la cloture americaine (GitHub Actions).",
        "",
        "| Robot | Ce qu'il fait | Demarre le | Solde virtuel | Dernier jour | Depuis le depart | Detail |",
        "|---|---|---|---|---|---|---|",
        *resume,
        "",
    ]
    if par_jour:
        t = pd.DataFrame(par_jour).sort_index().tail(15).iloc[::-1]
        lignes += ["## Resultat de chaque jour ($)", "",
                   "| Date | " + " | ".join(t.columns) + " |", "|---|" + "---|" * len(t.columns)]
        for date, r in t.iterrows():
            lignes.append(f"| {date} | " + " | ".join("" if pd.isna(v) else f"{v:+,.0f}" for v in r) + " |")
        lignes.append("")
    lignes += [
        "Pour juger un robot, il faut plusieurs mois : des jours et des semaines negatifs sont normaux. Le detail de "
        "chaque robot compare son resultat a ce que donnait son historique.",
        "",
        "Recherche et backtests : branche `claude/keen-babbage-r686cl`.",
        "",
    ]
    (ICI / "README.md").write_text("\n".join(lignes))


if __name__ == "__main__":
    main()
