#!/usr/bin/env python3
"""Deuxieme moteur pour Z9 / Z10 (VAGUE2.md) : rejeu zipline (execution a la cloture suivante, plus prudent que le calcul
pandas qui joue a la cloture du signal) et memes quatre criteres. python3 contre_verif.py <dossier de travail>"""
import glob
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent; TRAV = Path(sys.argv[1]).resolve()
ZL = str(Path(sys.executable).parent / "zipline")
env = dict(os.environ, ZIPLINE_ROOT=str(TRAV / "zipline_root"), LABO_CSV=str(TRAV / "csv"))
d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(ICI.parent / "radar/donnees/jour/yahoo/*.csv.gz")))])
irx = d[d.serie == "^IRX:c"].set_index("date").valeur; irx.index = pd.to_datetime(irx.index)


def nw(y, x, lags=5):
    X = np.column_stack([np.ones(len(y)), x]); XtX = np.linalg.inv(X.T @ X); b = XtX @ X.T @ y; u = y - X @ b
    S = (X * u[:, None]).T @ (X * u[:, None])
    for l in range(1, lags + 1):
        G = (X[l:] * u[l:, None]).T @ (X[:-l] * u[:-l, None]); S += (1 - l / (lags + 1)) * (G + G.T)
    return b, b / np.sqrt(np.diag(XtX @ S @ XtX))


for actif, z in (("BTC", "Z9"), ("ETH", "Z10")):
    sortie = TRAV / "resultats" / f"elan_{actif}.pickle"
    r = subprocess.run([ZL, "-e", str(ICI / "extension.py"), "run", "-f", str(ICI / "elan_crypto.py"), "-b", "crypto", "--start", "2018-12-01",
                        "--end", "2026-10-29", "--capital-base", "10000", "--no-benchmark", "--trading-calendar", "24/7", "-o", str(sortie)],
                       env=dict(env, ACTIF=actif, FAMILLE="crypto"), capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-1500:]); continue
    p = pd.read_pickle(sortie); p.index = pd.to_datetime(p.period_open).dt.tz_localize(None).dt.normalize()
    c = pd.read_csv(TRAV / "csv/crypto/daily" / f"{actif}.csv", parse_dates=["date"]).set_index("date").close
    c.index = c.index + pd.Timedelta(days=1)                                   # dates reelles
    rb = c.pct_change().reindex(p.index)
    rf = (irx.reindex(p.index.union(irx.index)).ffill().shift(1).reindex(p.index).fillna(0) / 100 / 365)
    # piege du calendrier 24/7 (mesure dans VAGUE2.md) : zipline valorise le portefeuille de la seance J a la cloture
    # reelle de J+1 (alors que la strategie voit et execute a la cloture de J) : le rendement etiquete J est celui de J+1
    ret = p.returns.shift(1)
    cash = (p.ending_cash / p.portfolio_value).clip(0, 1).shift(1)
    rs = ret + rf * cash.shift(1).fillna(1)                                    # l'argent hors marche rapporte le taux sans risque
    sel = (p.index >= "2019-01-01") & ret.notna(); es, eb = (rs - rf)[sel].to_numpy(), (rb - rf)[sel].to_numpy()
    b, t = nw(es, eb); m = len(es) // 2
    a1, a2 = nw(es[:m], eb[:m])[0][0] * 365, nw(es[m:], eb[m:])[0][0] * 365
    sh, shb = es.mean() / es.std() * np.sqrt(365), eb.mean() / eb.std() * np.sqrt(365)
    ntr = sum(len(l) for l in p.transactions)
    print(f"{z} {actif} dans zipline (exécution à la clôture suivante) : alpha {b[0] * 365:+.1%}/an t {t[0]:.2f} | Sharpe {sh:.2f} contre {shb:.2f} | "
          f"moitiés {a1:+.1%} {a2:+.1%} | {ntr} transactions | capital {p.portfolio_value.iloc[-1]:,.0f} $"
          + (" → MÊME VERDICT" if t[0] >= 2 and sh > shb and a1 > 0 and a2 > 0 else " → verdict différent"))
