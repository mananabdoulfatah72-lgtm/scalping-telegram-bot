#!/usr/bin/env python3
"""Realisme de la partie D (README.md, fixe avant l'ouverture du coffre), descriptif, exploration 2013-2022 seulement :
les cotations CFD de nuit (HistData) ressemblent-elles au vrai future (barres d'une heure Databento du NQ et de l'ES) ?
Correlation des rendements horaires de nuit, et autocorrelation d'une heure a la suivante dans chaque source (un exces
de retour a la moyenne sur le CFD trahirait du bruit de cotation, non tradable). Ecrit resultats/realisme_nuit.txt."""
import numpy as np
import pandas as pd

import commun as K
import nuit as NU

L = ["Realisme des cotations de nuit (CFD HistData) face au future (Databento, barres d'une heure), 2013-2022", ""]
for nom, fich in (("NQ", "nasdaq100_1h.csv.gz"), ("ES", "sp500_1h.csv.gz")):
    fu = pd.read_csv(K.KB / "nuit" / "donnees" / fich)
    fu["t"] = pd.to_datetime(fu["t"])
    fu = fu[(fu["t"] >= "2013-01-01") & (fu["t"] < "2023-01-01")].set_index("t")["c"]
    d = np.load(K.CACHE / f"recherche_nuit_{nom}.npz")
    jours = pd.DatetimeIndex(d["jours"])
    rows = []
    for i in np.flatnonzero(d["complete"] & (jours >= "2013-01-01")):
        veille = jours[i] - pd.Timedelta(days=3 if jours[i].dayofweek == 0 else 1)
        for b in range(11, 184, 12):                    # cloture de chaque heure pleine : 18 h 55 ... 8 h 55
            h = (18 * 60 + 5 * b) // 60 % 24
            jour = veille if h >= 18 else jours[i]
            rows.append((jour + pd.Timedelta(hours=h), d["c"][i, b]))
    cf = pd.Series(dict(rows)).sort_index()
    # barre horaire du future datee de son debut : sa cloture correspond a la cloture CFD de la meme heure
    df = pd.DataFrame({"cfd": cf, "fut": fu.reindex(cf.index)}).dropna()
    df["nuit"] = (df.index - pd.Timedelta(hours=18)).normalize()
    meme = df["nuit"].eq(df["nuit"].shift(1)).values
    r = np.log(df[["cfd", "fut"]]).diff()
    r[~meme] = np.nan                                  # pas de rendement d'une nuit a l'autre
    lag = r.shift(1)
    lag[~meme] = np.nan
    r, lag = r[np.isfinite(r).all(axis=1)], lag[np.isfinite(r).all(axis=1)]
    ok = lag.notna().all(axis=1)
    a_cfd = np.corrcoef(r.loc[ok, "cfd"], lag.loc[ok, "cfd"])[0, 1]
    a_fut = np.corrcoef(r.loc[ok, "fut"], lag.loc[ok, "fut"])[0, 1]
    c = np.corrcoef(r["cfd"], r["fut"])[0, 1]
    L.append(f"{nom} : {len(r)} heures de nuit communes ; correlation CFD / future {c:.3f} ; ecart-type CFD / future "
             f"{r['cfd'].std() / r['fut'].std():.3f} ; autocorrelation d'une heure a la suivante : CFD {a_cfd:+.3f}, "
             f"future {a_fut:+.3f}")
txt = "\n".join(L)
(K.ICI / "resultats" / "realisme_nuit.txt").write_text(txt + "\n")
print(txt)
