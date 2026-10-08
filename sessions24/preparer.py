#!/usr/bin/env python3
"""Barres d'une minute Dukascopy (UTC) -> barres de 5 minutes (UTC).
- python3 sessions24/preparer.py <code> <annee> : brut/<code>_<annee>.csv -> sessions24/annees/<code>_<annee>_5m.csv.gz
- python3 sessions24/preparer.py <code> fusion  : toutes les annees -> sessions24/donnees/<code>_5m.csv.gz
(t = debut de la barre en UTC, o, h, l, c). Les erreurs sont aussi ecrites comme annotations GitHub (::error::)."""
import glob
import sys
import traceback
from pathlib import Path

import pandas as pd

ICI = Path(__file__).resolve().parent
ANNEES, SORTIE = ICI / "annees", ICI / "donnees"


def heures(col):
    """Horodatage Dukascopy : nombre depuis 1970 (unite deduite de sa taille : s, ms, us ou ns) ou texte ISO."""
    x = pd.to_numeric(col, errors="coerce")
    if x.notna().mean() > 0.99:
        m = float(x.median())
        unite = "ns" if m > 1e17 else ("us" if m > 1e14 else ("ms" if m > 1e11 else "s"))
        return pd.to_datetime(x.astype("int64"), unit=unite, utc=True)
    return pd.to_datetime(col, utc=True, format="mixed")


def cinq_minutes(d):
    cols = {c.lower(): c for c in d.columns}
    tcol = cols.get("timestamp") or cols.get("time") or cols.get("date") or d.columns[0]
    t = heures(d[tcol])
    x = pd.DataFrame({k: pd.to_numeric(d[cols[k]], errors="coerce").to_numpy() for k in ("open", "high", "low", "close")},
                     index=pd.DatetimeIndex(t))
    x = x[~x.index.duplicated(keep="last")].sort_index().dropna()
    b = x.resample("5min", label="left", closed="left").agg({"open": "first", "high": "max", "low": "min",
                                                              "close": "last"}).dropna()
    nd = 5 if len(b) and b["close"].median() < 50 else 3
    return pd.DataFrame({"t": b.index.strftime("%Y-%m-%d %H:%M").to_numpy(), "o": b["open"].round(nd).to_numpy(),
                         "h": b["high"].round(nd).to_numpy(), "l": b["low"].round(nd).to_numpy(),
                         "c": b["close"].round(nd).to_numpy()})


def annee(inst, y):
    f = Path(f"brut/{inst}_{y}.csv")
    if not f.exists() or f.stat().st_size == 0:
        print(f"::warning::{inst} {y} : pas de fichier brut")
        return
    d = pd.read_csv(f)
    if d.empty:
        print(f"::warning::{inst} {y} : fichier vide")
        return
    print(f"{inst} {y} : colonnes {list(d.columns)}, {len(d)} lignes, premiere ligne {d.iloc[0].tolist()}")
    out = cinq_minutes(d)
    ANNEES.mkdir(parents=True, exist_ok=True)
    out.to_csv(ANNEES / f"{inst}_{y}_5m.csv.gz", index=False, compression="gzip")
    print(f"{inst} {y} : {len(out)} barres de 5 min ({out['t'].iloc[0]} -> {out['t'].iloc[-1]})")


def fusion(inst):
    fichiers = sorted(glob.glob(str(ANNEES / f"{inst}_*_5m.csv.gz")))
    if not fichiers:
        print(f"::error::{inst} : aucune annee preparee")
        sys.exit(1)
    d = pd.concat([pd.read_csv(f) for f in fichiers]).drop_duplicates("t", keep="last").sort_values("t")
    SORTIE.mkdir(parents=True, exist_ok=True)
    d.to_csv(SORTIE / f"{inst}_5m.csv.gz", index=False, compression="gzip")
    print(f"{inst} : {len(d)} barres de 5 min, {len(fichiers)} annees, du {d['t'].iloc[0]} au {d['t'].iloc[-1]} (UTC)")


if __name__ == "__main__":
    try:
        if sys.argv[2] == "fusion":
            fusion(sys.argv[1])
        else:
            annee(sys.argv[1], int(sys.argv[2]))
    except Exception as e:
        msg = traceback.format_exc().replace("\n", " | ")
        print(f"::error::preparer {sys.argv[1:]} : {type(e).__name__} {e} -- {msg[-600:]}")
        sys.exit(1)
