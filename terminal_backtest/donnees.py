#!/usr/bin/env python3
"""Barres quotidiennes reelles de 4 futures CME (NQ, ES, GC, CL), en prix continus ajustes des changements de contrat.

Source : fonds/donnees/futures_1d.csv.gz de la branche claude/keen-babbage-r686cl (Databento ; .v.0 = contrat le plus
echange, .v.1 = le 2e). Le jour ou le contrat le plus echange change, le rendement est celui du NOUVEAU contrat depuis
sa propre cloture de la veille (il etait alors le 2e), comme fonds/sources.py : tout l'historique d'avant est multiplie
par cloture_nouveau(veille) / cloture_ancien(veille). Calendrier commun : les seances cotees sur les 4 marches.
Chaque marche porte aussi r[] : 1 sur la premiere barre d'un nouveau contrat (le backtest y compte le cout du passage
d'un contrat a l'autre pour une position gardee).

Usage : python3 donnees.py <futures_1d.csv.gz>   -> ecrit data.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
MARCHES = [("NQ", "Nasdaq-100", "NQ · micro MNQ"), ("ES", "S&P 500", "ES · micro MES"),
           ("GC", "Or", "GC · micro MGC"), ("CL", "Pétrole brut", "CL · micro MCL")]


def continu(d, racine):
    x0 = d[d.symbole == f"{racine}.v.0"].drop_duplicates("date").set_index("date").sort_index()
    x1 = d[d.symbole == f"{racine}.v.1"].drop_duplicates("date").set_index("date").sort_index().reindex(x0.index)
    o, h, l, c = (x0[k].to_numpy(float) for k in "ohlc")
    id0, id1, c1 = x0.contrat.to_numpy(), x1.contrat.to_numpy(), x1.c.to_numpy(float)
    n = len(c); ratio = np.ones(n); exact = approche = 0
    for t in range(1, n):
        if id0[t] != id0[t - 1]:
            if id1[t - 1] == id0[t] and c1[t - 1] > 0 and c[t - 1] > 0:
                ratio[t] = c1[t - 1] / c[t - 1]; exact += 1
            else:                                   # 2e contrat inconnu la veille : ecart de nuit neutralise
                ratio[t] = o[t] / c[t - 1]; approche += 1
    f = np.ones(n); acc = 1.0
    for t in range(n - 1, -1, -1):
        f[t] = acc; acc *= ratio[t]
    change = np.zeros(n, int); change[1:] = (id0[1:] != id0[:-1]).astype(int)   # 1re barre d'un nouveau contrat
    return pd.DataFrame({"o": o * f, "h": h * f, "l": l * f, "c": c * f, "r": change}, index=x0.index), exact, approche


def principal(source):
    d = pd.read_csv(source)
    series, infos = {}, {}
    for r, _, _ in MARCHES:
        s, exact, approche = continu(d, r)
        assert (s[list("ohlc")].values > 0).all(), f"{r} : prix nul ou negatif"
        series[r] = s; infos[r] = (exact, approche)
    jours = sorted(set.intersection(*(set(s.index) for s in series.values())))
    out = {"source": "Databento, contrats CME les plus échangés, barres quotidiennes, prix ajustés des changements de contrat",
           "dates": jours, "marches": []}
    for r, nom, contrat in MARCHES:
        s = series[r].loc[jours]
        mauvais = int(((s.h < s[["o", "c"]].max(axis=1) - 1e-9) | (s.l > s[["o", "c"]].min(axis=1) + 1e-9)).sum())
        ret = s.c.pct_change().abs()
        print(f"{r}: {len(s)} seances {jours[0]} -> {jours[-1]} ; changements de contrat exacts {infos[r][0]}, approches {infos[r][1]} ; "
              f"barres incoherentes {mauvais} ; plus forte variation {ret.max() * 100:.1f} % le {ret.idxmax()} ; "
              f"dernier prix ajuste {s.c.iloc[-1]:.2f}")
        # un changement de contrat tombe parfois un jour absent du calendrier commun : il est reporte a la seance suivante
        tous = series[r]["r"]; rr = []
        avant = None
        for j in jours:
            m = tous[(tous.index > avant) & (tous.index <= j)] if avant is not None else tous[tous.index <= j].iloc[-1:]
            rr.append(int(m.sum() > 0) if avant is not None else 0); avant = j
        out["marches"].append({"id": r, "nom": nom, "contrat": contrat,
                               **{k: [round(float(v), 6) for v in s[k]] for k in "ohlc"}, "r": rr})
    (ICI / "data.json").write_text(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
    print("data.json :", (ICI / "data.json").stat().st_size // 1024, "Ko ;", len(jours), "seances communes")


if __name__ == "__main__":
    principal(sys.argv[1])
