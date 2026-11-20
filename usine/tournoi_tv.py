#!/usr/bin/env python3
"""Tournoi des indicateurs TradingView (usine/REGLES.md, idees 9 a 15) : les 5 portes de l'usine pour chacun.
Usage : KB_MINUTES=<nasdaq100_1min.csv.gz> python3 usine/tournoi_tv.py [idee ...]"""
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import moteur as Mo  # noqa: E402,F401
import indicateurs  # noqa: E402
import portes as Po  # noqa: E402

if __name__ == "__main__":
    noms = [a for a in sys.argv[1:] if not a.startswith("--")] or list(indicateurs.IDEES)
    sys.argv = [sys.argv[0]] + noms
    Po.principal()
