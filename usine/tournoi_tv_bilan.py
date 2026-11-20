#!/usr/bin/env python3
"""Bilan du tournoi des indicateurs TradingView : une ligne par indicateur (dernier calcul), a cote de la zone et du
Supertrend. Usage : python3 usine/tournoi_tv_bilan.py"""
import json
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))

IDEES = ["tv_squeeze", "tv_utbot", "tv_ssl", "tv_rangefilter", "tv_wavetrend", "tv_hull", "tv_chandelier", "supertrend", "zone"]


def dernier(idee):
    f = sorted((ICI / "resultats").glob(f"*/{idee}.json"))
    return json.loads(f[-1].read_text()) if f else None


def ligne(R):
    p = R["portes"]; p1 = p["1"]
    x = [R["titre"], f"PF {p1['pf_meilleur']:.3f}, t {p1['t_meilleur']:.2f}, plateau {'oui' if p1['plateau'] else 'non'}",
         f"{p['2']['p']:.1%}" if "2" in p else "-",
         f"PF {p['3']['pf']:.3f}, {p['3']['gain_par_an']:+,.0f} $/an" if "3" in p else "-",
         f"{p['4']['p']:.1%}" if "4" in p else "-", R["verdict"]]
    if "bot" in R.get("portes", {}).get("1", {}) or "pf_bot" in p1:
        x.insert(2, f"PF {p1.get('pf_bot', float('nan')):.3f}")
    else:
        x.insert(2, "-")
    return "| " + " | ".join(x) + " |"


def principal():
    L = ["| Indicateur | Porte 1 (2011-2014, meilleur reglage) | Reglage par defaut, 2011-2014 | Porte 2 (permutations qui font aussi bien) | Porte 3 (2015 -> 2026) | Porte 4 | Verdict |",
         "|---|---|---|---|---|---|---|"]
    for i in IDEES:
        R = dernier(i)
        if R:
            L.append(ligne(R))
    print("\n".join(L))


if __name__ == "__main__":
    principal()
