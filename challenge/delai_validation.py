#!/usr/bin/env python3
"""En combien de temps le bot zone de bruit (MNQ seul, bot coussin) valide-t-il un challenge 50K ?
Rejoue bot_challenge.une_tentative sur les vrais jours 2011-2026 : un depart par semaine, au plus 2 comptes
(un deuxieme achete le lendemain d'un echec), et mesure la part des departs valides en 1, 3, 6 et 12 mois.
Donne aussi le nombre de MNQ que le bot prendrait aujourd'hui sur un compte neuf.

Lancer depuis ce dossier : python3 delai_validation.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "intraday"))
from analyse import calculer  # noqa: E402
from bot_challenge import REGLES, une_tentative  # noqa: E402

MOIS = {"1 mois": 21, "3 mois": 63, "6 mois": 126, "12 mois": 252}


def serie():
    jours, res, _ = calculer("nasdaq100")
    z = res["Zone de bruit"]
    gain = z["dollars"].reindex(jours).fillna(0)
    pire = np.minimum((z["pire"] * 2.0).reindex(jours).fillna(0).clip(upper=0), np.minimum(gain, 0))
    return pd.DataFrame({"gain": gain, "pire": pire, "risque1": gain.rolling(60, min_periods=40).std().shift(1),
                         "melange": 0.0}).dropna()


def delais(d, regle, f, comptes=2, horizon=252):
    """Pour chaque depart : nombre de seances jusqu'a la validation (NaN si pas valide dans l'horizon)."""
    out = []
    for i0 in range(0, len(d) - horizon, 5):
        k, fin_horizon, valide = i0, i0 + horizon, np.nan
        for _ in range(comptes):
            r, fin = une_tentative(d, k, regle, f, False)
            if r == 1 and fin < fin_horizon:
                valide = fin - i0 + 1
                break
            if r != -1 or fin >= fin_horizon:      # pas finie dans l'horizon (ou fin du temps Apex sans echec)
                if r == 0 and regle["jours"]:          # Apex : tentative de 30 jours ecoulee, on rachete
                    k = fin + 1
                    continue
                break
            k = fin + 1
        out.append(valide)
    return pd.Series(out, index=d.index[list(range(0, len(d) - horizon, 5))])


def main():
    d = serie()
    print(f"Zone de bruit MNQ, {d.index[0].date()} -> {d.index[-1].date()}, un depart par semaine, 2 comptes au plus\n")
    r = d["risque1"].iloc[-1]
    print(f"Aujourd'hui : un jour normal = {r:,.0f} $ de risque pour 1 MNQ. Sur un compte neuf :")
    for firme, regle in REGLES.items():
        coussin = regle["perte"]
        print("   " + firme + " : " + ", ".join(f"f={f:.2f} -> {int(np.floor(f * coussin / r))} MNQ" for f in (0.15, 0.25, 0.35)))
    print()
    for firme, regle in REGLES.items():
        for f in (0.15, 0.25, 0.35):
            for nom_p, dd in [("2011-2026", d), ("depuis 2020", d[d.index >= "2020"])]:
                x = delais(dd, regle, f)
                parts = " | ".join(f"{m} {np.mean(x <= n):4.0%}" for m, n in MOIS.items())
                med = x.median()
                print(f"  {firme:12s} f={f:.2f} {nom_p:11s} : valide en {parts}"
                      + (f" | si valide : {med:.0f} seances en mediane (~{med / 21:.1f} mois)" if np.isfinite(med) else ""), flush=True)
        print()


if __name__ == "__main__":
    main()
