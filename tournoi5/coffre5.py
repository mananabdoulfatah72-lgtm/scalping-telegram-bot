#!/usr/bin/env python3
"""Tournoi n°5, etape 3 (README.md) : coffre 2023-2026, une seule fois, pour les survivants (survivants5.json).
Passe si t >= seuil de Bonferroni (m = nombre de survivants) et au moins 3 annees positives sur 4.
Lancer depuis ce dossier, quand toutes les familles ont ete explorees : python3 coffre5.py"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

import strategies5 as S
from explorer import t_stat

ICI = Path(__file__).resolve().parent
MARCHE_B = {"B1": "RTY", "B2": "YM", "B3": "GC", "B4": "CL", "B5": "6E"}


def serie(code):
    """Rendements quotidiens nets et jours retenus, sur toutes les donnees."""
    if code in MARCHE_B or code in ("C1", "D1"):
        marche = MARCHE_B.get(code, "CL" if code == "C1" else "BTC")
        J, O, H, L, C, P, V, ech, comp, con = S.charger_minutes(marche)
        cout = S.cout_micro(marche)
        if code in MARCHE_B:
            p, ok = S.fin_de_seance(O, H, L, C, comp, ech, con, cout)
        elif code == "C1":
            p, ok = S.rapport_eia(J, O, H, L, C, comp, ech, cout)
        else:
            p, ok = S.bitcoin(O, H, L, C, comp, ech, cout)
        return J, p / O[:, 0], ok
    if code in ("A1", "A2"):
        heures = {d: S.lire_heures(d) for d in S.DEVISES}
        J = S.jours_ouvres(heures)
        fix = S.heure_fixing(J)
        r, ok = S.trade_heure(heures, J, fix + (-1 if code == "A1" else 0), -1 if code == "A1" else 1)
        return J, r, ok
    h = S.lire_heures("ZN")
    J = S.jours_ouvres({"ZN": h})
    adj = pd.DatetimeIndex(J).isin(S.adjudications())
    r, ok = S.zn_trade(h, J, *((9, 13, -1) if code == "E1" else (13, 15, 1)))
    return J, np.where(adj, r, 0.0), ok


def main():
    surv = json.loads((ICI / "survivants5.json").read_text()) if (ICI / "survivants5.json").exists() else []
    if not surv:
        print("Aucun survivant : le coffre reste ferme.")
        return
    seuil = float(norm.ppf(1 - 0.05 / len(surv)))
    lignes, sortie = [f"Coffre 2023-2026 : {len(surv)} survivant(s), seuil de Bonferroni t >= {seuil:.2f}"], []
    for s in surv:
        J, r, ok = serie(s["code"])
        j = pd.DatetimeIndex(J)
        c = ok & (j.year >= 2023)
        t = t_stat(r[c])
        ans = pd.Series(r[c], index=j[c]).groupby(j[c].year).sum()
        passe = t >= seuil and (ans > 0).sum() >= 3
        sortie.append({**s, "t": t, "annees": {str(a): float(v) for a, v in ans.items()}, "passe": bool(passe)})
        lignes.append(f"  {s['code']} {s['marche']} : t {t:+.2f} | " + " ".join(f"{a}:{v:+.1%}" for a, v in ans.items())
                      + f" (somme des rendements) | {'PASSE' if passe else 'rejete'}")
    print("\n".join(lignes))
    (ICI / "coffre5.txt").write_text("\n".join(lignes) + "\n")
    (ICI / "coffre5.json").write_text(json.dumps(sortie, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
