#!/usr/bin/env python3
"""Signal 7 : bandes de VWAP sur le future ES, barres d'une minute 2011-2026 (regles dans README.md).

Cloture au-dessus de VWAP + 2 ecarts-types -> vente ; en dessous de VWAP - 2 ecarts-types -> achat ;
sortie au retour au VWAP ou a 15 h 55 ; pas d'entree avant 10 h. Frais MES : 0,9 point par aller-retour.

Lancer depuis ce dossier : python3 vwap.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "intraday"))
import strategies as st  # noqa: E402

COUT = st.cout_aller_retour("sp500")          # 0,9 point
PT = st.CONTRATS["sp500"]["pt"]               # 5 $ par point (MES)


def trades_vwap(J, O, H, L, C, P, X):
    ok = st.journees_completes(P)
    typique = (H + L + C) / 3
    V = X["V"]
    cv = np.cumsum(V, axis=1)
    vwap = np.cumsum(typique * V, axis=1) / np.maximum(cv, 1)
    var = np.cumsum(V * typique ** 2, axis=1) / np.maximum(cv, 1) - vwap ** 2
    sig = np.sqrt(np.maximum(var, 0))
    lignes = []
    for d in np.where(ok)[0]:
        pos, entree, t0 = 0, 0.0, 0
        for m in range(30, 386):
            p = C[d, m]
            if pos and ((pos < 0 and p <= vwap[d, m]) or (pos > 0 and p >= vwap[d, m]) or m == 385):
                lignes.append((J[d], pos, pos * (p - entree), m - t0))
                pos = 0
                continue
            if not pos and m < 385 and sig[d, m] > 0:
                if p > vwap[d, m] + 2 * sig[d, m]:
                    pos, entree, t0 = -1, p, m
                elif p < vwap[d, m] - 2 * sig[d, m]:
                    pos, entree, t0 = 1, p, m
    return pd.DataFrame(lignes, columns=["jour", "sens", "brut", "minutes"])


def main():
    J, O, H, L, C, P, X = st.charger("sp500")
    t = trades_vwap(J, O, H, L, C, P, X)
    t["net"] = t["brut"] - COUT
    rng = np.random.default_rng(0)
    mouvement = (t["brut"] * t["sens"]).values
    placebo = np.array([(rng.choice([-1.0, 1.0], len(t)) * mouvement).mean() - COUT for _ in range(2000)])
    print(f"Bandes de VWAP sur ES (MES), {J[0].date()} -> {J[-1].date()} : {len(t)} trades, "
          f"duree moyenne {t['minutes'].mean():.0f} minutes, frais {COUT:.2f} point par aller-retour")
    for lab, a, z in [("2011-2026", "2011", "2027"), ("2011-2014", "2011", "2015"), ("2015-2019", "2015", "2020"),
                      ("2020-2026", "2020", "2027")]:
        x = t[(t["jour"] >= a) & (t["jour"] < z)]
        tt = x["net"].mean() / x["net"].std() * np.sqrt(len(x))
        ans = (x["jour"].max() - x["jour"].min()).days / 365.25
        print(f"  {lab} : {len(x):5d} trades | gagnants {np.mean(x['net'] > 0):.0%} | brut {x['brut'].mean():+.2f} pt"
              f" | net {x['net'].mean():+.2f} pt (t {tt:+.2f}) | {x['net'].sum() * PT / ans:+,.0f} $/an par MES")
    print(f"  placebo (sens au hasard, memes trades) : {np.mean(placebo < t['net'].mean()):.0%} font moins bien")
    annees = t.groupby(t["jour"].dt.year)["net"].sum() * PT
    print("  par annee ($ par MES) : " + " ".join(f"{a}:{v:+,.0f}" for a, v in annees.items()))


if __name__ == "__main__":
    main()
