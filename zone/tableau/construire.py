#!/usr/bin/env python3
"""Construit le tableau de bord en direct du robot zone de bruit (page HTML autonome) a partir des fichiers du robot
(zone/robot/) et du backtest de reference (reference.json, rejeu 2023-2026 pour 1 MNQ).

Lancer depuis la racine du depot : python3 zone/tableau/construire.py [sortie.html]
(par defaut zone/tableau/tableau.html, fichier genere, non suivi par git). La page est ensuite publiee comme artefact."""
import json
import os
import re
import sys
from pathlib import Path

import pandas as pd

ICI = Path(__file__).resolve().parent
ROBOT = Path(os.getenv("TABLEAU_ROBOT", ICI.parent / "robot"))   # dossier du robot (par defaut zone/robot)


def trades_du_jour(tableau):
    """Lignes de la section "## Trades du ..." du tableau de bord du robot."""
    m = re.search(r"^## Trades du (\S+)\n\n((?:- .*\n?)+)", tableau, re.M)
    return {"date": m.group(1), "lignes": [x[2:] for x in m.group(2).strip().splitlines()]} if m else None


def main():
    sortie = Path(sys.argv[1]) if len(sys.argv) > 1 else ICI / "tableau.html"
    journal = pd.read_csv(ROBOT / "journal.csv") if (ROBOT / "journal.csv").exists() else pd.DataFrame()
    if len(journal) and "gain_rebond_1_mnq" not in journal:
        journal["gain_rebond_1_mnq"] = 0.0
    journal = journal.fillna({"evenement": "", "gain_rebond_1_mnq": 0.0})
    niv = ROBOT / "niveaux.json"
    tab = (ROBOT / "TABLEAU_DE_BORD.md").read_text() if (ROBOT / "TABLEAU_DE_BORD.md").exists() else ""
    donnees = {
        "construit": pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "etat": json.loads((ROBOT / "etat.json").read_text()),
        "journal": journal.to_dict("records"),
        "niveaux": json.loads(niv.read_text()) if niv.exists() else None,
        "trades": trades_du_jour(tab),
        "reference": json.loads((ICI / "reference.json").read_text()),
    }
    texte = json.dumps(donnees, ensure_ascii=False, separators=(",", ":"), allow_nan=False).replace("</", "<\\/")
    modele = (ICI / "modele.html").read_text()
    assert modele.count("/*DONNEES*/null") == 1
    sortie.write_text(modele.replace("/*DONNEES*/null", texte))
    print(f"{sortie} : {len(journal)} seances, derniere {donnees['etat']['derniere_date']}")


if __name__ == "__main__":
    main()
