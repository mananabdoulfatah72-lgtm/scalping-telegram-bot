#!/usr/bin/env python3
"""Liste des trades de la zone de bruit (code du robot, zone/robot.py sur main, fonction zone_de_bruit V1) sur les barres
d'une minute du NQ de la recherche (intraday/donnees/nasdaq100_1min.csv.gz), avant la periode deja utilisee par l'etude
order flow (orderflow/, avril - octobre 2026). Ecrit trades_zone.csv : jour, minute de decision (depuis 9 h 30), sens,
points apres les frais du robot (1,5 point par aller-retour).
Lancer depuis ce dossier : ROBOT_ZONE=/chemin/zone/robot.py python3 trades_zone.py"""
import importlib.util
import os
import re
from pathlib import Path

import pandas as pd

ICI = Path(__file__).resolve().parent
FIN = "2026-03-31"                      # derniere seance avant l'etude order flow (avril - octobre 2026)
MOTIF = re.compile(r"(achat|vente) (\d+)h(\d+) a ([\d,.]+) -> sortie (\d+)h(\d+) a ([\d,.]+)")


def main():
    spec = importlib.util.spec_from_file_location("robot", os.environ["ROBOT_ZONE"])
    robot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(robot)
    m = pd.read_csv(ICI.parent / "intraday" / "donnees" / "nasdaq100_1min.csv.gz")
    m = m[m["t"].str[:10] <= FIN]
    jj, O, H, L, C, P, V, ech = robot.tableaux(m)
    _, trades, _ = robot.zone_de_bruit(jj, O, H, L, C, P, V, ech)
    out = []
    for j, liste in trades.items():
        for texte in liste:
            x = MOTIF.match(texte)
            if x:
                sens = 1 if x.group(1) == "achat" else -1
                e, s = float(x.group(4).replace(",", "")), float(x.group(7).replace(",", ""))
                out.append({"jour": str(pd.Timestamp(j).date()), "minute": int(x.group(2)) * 60 + int(x.group(3)) - 570,
                            "sens": sens, "points": round(sens * (s - e) - robot.COUT, 2)})
    t = pd.DataFrame(out).sort_values(["jour", "minute"]).reset_index(drop=True)
    t.to_csv(ICI / "trades_zone.csv", index=False)
    print(f"{len(t)} trades de zone du {t['jour'].iloc[0]} au {t['jour'].iloc[-1]} sur {t['jour'].nunique()} seances")


if __name__ == "__main__":
    main()
