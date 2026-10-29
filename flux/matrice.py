#!/usr/bin/env python3
"""Matrice des gains quotidiens (en $ pour 1 contrat micro, au prix d'aujourd'hui, frais compris) de toutes les
strategies du projet qu'on peut regenerer sur le NQ de 2011 a 2026 : zone de bruit (version d'origine, controles de
30 minutes), regles G (elan hors zone), H1 - H16 (banc d'analyse technique), E1 - E9 (institutions et chercheurs ;
E5 et E6 de nuit, rangees a la date de la seance du matin), F1 - F8 (pistes inexplorees), S2b. Ecrit
FLUX_CALCUL/matrice.pkl (une colonne par strategie, NaN = pas de trade ce jour-la).

Lancer : KB=<copie de claude/keen-babbage-r686cl> python3 flux/matrice.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "scalping"))
import challenge_ajouts as CA  # noqa: E402
import partie_e as E  # noqa: E402
import partie_f as F  # noqa: E402
import partie_g as G  # noqa: E402
import partie_h as H  # noqa: E402

CALCUL = Path(__import__("os").getenv("FLUX_CALCUL", Path(__import__("tempfile").gettempdir()) / "flux_calcul"))



def zone_quotidienne(d, tr):
    """Gain de chaque seance de la zone (1 MNQ, prix d'aujourd'hui, frais) : cloture de la derniere minute des chemins."""
    clo, _ = CA.chemins(d, CA.trades_zone(d, tr))
    g = clo[:, -1].copy()
    a_trade = np.zeros(len(g), bool)
    for s, me, sg, ms in tr:
        a_trade[s] = True
    g[~a_trade] = np.nan
    return g


def s2b_quotidien(jours):
    """S2b (flux/s2b_15ans.py --quotidien, lance a part : flux/ et scalping/ ont chacun un module donnees)."""
    import subprocess
    subprocess.run([sys.executable, str(ICI / "s2b_15ans.py"), "--quotidien"], check=True, cwd=ICI)
    s = pd.read_pickle(CALCUL / "s2b_quotidien.pkl")["S2b"]
    return s.reindex(pd.DatetimeIndex(jours)).to_numpy()


def main():
    d = E.jour_nq()
    jours = pd.DatetimeIndex(d["jours"].astype("datetime64[D]"))
    cols = {}
    out_g, pos, dedans, e, tr = G.calcul(d)
    cols["ZONE"] = zone_quotidienne(d, tr)
    for r, v in out_g.items():
        cols[r] = v[0] if isinstance(v, tuple) else v
    for r, v in H.toutes(d).items():
        cols[r] = v[0]
    for r, v in F.toutes(d).items():
        cols[r] = v[0] if isinstance(v, tuple) else v
    try:                                     # E demande des donnees de nuit et des ETF qui ne sont pas toujours en cache
        _, n, ctx = E.preparer()
        oute, dates = E.toutes(d, n, ctx)
        for r, v in oute.items():
            g = v[0] if isinstance(v, tuple) else v
            dj = pd.DatetimeIndex(np.asarray(dates[r]).astype("datetime64[D]"))
            cols[r] = pd.Series(g, index=dj).groupby(level=0).sum(min_count=1).reindex(jours).to_numpy()
    except (FileNotFoundError, KeyError) as x:
        print(f"regles E absentes ({x})")
    cols["S2b"] = s2b_quotidien(jours)
    M = pd.DataFrame(cols, index=jours)
    M.index.name = "jour"
    CALCUL.mkdir(parents=True, exist_ok=True)
    M.to_pickle(CALCUL / "matrice.pkl")
    resume = pd.DataFrame({"trades_jours": M.notna().sum(), "total_$": M.sum().round(0),
                           "moyenne_jour_$": M.fillna(0).mean().round(2)})
    print(f"{M.shape[1]} strategies, {M.shape[0]} seances ({jours[0].date()} - {jours[-1].date()})")
    print(resume.to_string())


if __name__ == "__main__":
    main()
