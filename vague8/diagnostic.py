#!/usr/bin/env python3
"""Vague 8, diagnostic (README.md) : le bot seul (zone 1 MNQ + RSI(2) de nuit sur 1 MES), sans compte autour, chaque trade
au niveau d'aujourd'hui de son jour d'entree, filtre simule aussi bon qu'en 2026 (premier tirage) et sans filtre : gain et
pire baisse par annee, part de la zone et du RSI(2), la baisse de 2025, les mois depuis octobre 2024. Ecrit diagnostic.txt."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "vague6"))
import vague6 as V6  # noqa: E402

D4, M4 = V6.D4, V6.M4


def journal(D, b, rsi, kN, kE):
    """Gain de chaque seance, sans plancher ni limite."""
    nj = len(D["jours"])
    g, veut = np.zeros(nj), 0
    for d in range(nj):
        _, c, veut, _, _, _ = M4.seance4(d, rsi, veut, 0.0, 0.0, -1e18, 0, 2000.0, 0.0, 0.0, *b, 2.0 * kN[d],
                                         5.0 * kE[d], 1)
        g[d] = c
    return pd.Series(g, index=D["jours"])


def main():
    V6.W.regler("regles")
    D = D4.charger()
    kN, kE = D4.facteurs_jour(D)
    L = [f"Cours du dernier jour : NQ {D['cl_nq'][-1]:,.2f} (1 MNQ = {2 * D['cl_nq'][-1]:,.0f} $), ES {D['cl_es'][-1]:,.2f}"
         f" (1 MES = {5 * D['cl_es'][-1]:,.0f} $)"]
    der = D["derniere"]
    i = np.arange(len(der))
    rng = (np.nanmax(np.where(np.arange(D["H"].shape[1]) <= der[:, None], D["H"], np.nan), axis=1)
           - np.nanmin(np.where(np.arange(D["L"].shape[1]) <= der[:, None], D["L"], np.nan), axis=1)) * 2.0 * kN
    L.append(f"Ecart plus haut - plus bas d'une seance, au niveau d'aujourd'hui : {np.mean(rng[i >= len(i) - 252]):,.0f} $"
             f" par MNQ en moyenne sur les 252 dernieres seances")
    gardes = {"filtre aussi bon qu'en 2026 (simule, 1er tirage)": V6.S.gardes_simules(D, V6.S.rho_2026())[0],
              "sans filtre": None}
    for nom, gg in gardes.items():
        b = D4.base(D, gg)
        bz = D4.base(D, np.zeros(len(D["Z"]), bool))
        z, a, t = journal(D, b, 0, kN, kE), journal(D, bz, 4, kN, kE), journal(D, b, 4, kN, kE)
        L += ["", f"=== {nom}", "annee | gain | pire baisse | zone | RSI(2) de nuit | jours a -500 $ ou pire | pire jour"]
        for y in range(2012, 2027):
            s = t[t.index.year == y]
            e = s.cumsum()
            L.append(f"{y} | {s.sum():+,.0f} $ | {(e - e.cummax()).min():+,.0f} $ | {z[z.index.year == y].sum():+,.0f} $ |"
                     f" {a[a.index.year == y].sum():+,.0f} $ | {(s <= -500).sum()} | {s.min():+,.0f} $")
        s = t["2025"]
        e = s.cumsum()
        fin = (e - e.cummax()).idxmin()
        deb = e[:fin].idxmax()
        L.append(f"Pire baisse de 2025 : du {deb.date()} au {fin.date()} ({len(s[deb:fin]) - 1} seances) ; zone"
                 f" {z[deb:fin].iloc[1:].sum():+,.0f} $, RSI(2) {a[deb:fin].iloc[1:].sum():+,.0f} $")
        m = t.groupby(t.index.to_period("M")).sum()
        L.append("Par mois : " + " ; ".join(f"{p} {v:+,.0f}" for p, v in m["2024-10":].items()))
    (ICI / "diagnostic.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
