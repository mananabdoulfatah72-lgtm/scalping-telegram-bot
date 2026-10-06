#!/usr/bin/env python3
"""London Strategic Edge, choix du cote agresseur (filtre_h1/README.md, source London Strategic Edge) : 5 regles
candidates fixees d'avance (T, V, VL, VA, VA1), etalonnage les 29-30 septembre 2026, validation les 22-25 septembre
2026 contre Databento (orderflow/donnees/nq_secondes_1.csv.gz) ; source acceptee si la regle retenue a le meme signe
que Databento sur le delta des 30 minutes dans au moins 95 % des fenetres de validation.
Cle : LSE_API_KEY (secret du depot). Ecrit lse/cote.txt et lse/minutes_lse.csv. Lancer depuis la racine du depot."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
R = ICI.parent
TICK, SEUIL = 0.25, 0.95
REGLES = ("T", "V", "VL", "VA", "VA1")
ETALONNAGE = [("2026-09-29T12:00:00", "2026-09-30T21:00:00")]
VALIDATION = [("2026-09-22T12:00:00", "2026-09-23T21:00:00"), ("2026-09-24T12:00:00", "2026-09-25T21:00:00")]
L = []


def dire(x=""):
    print(x, flush=True)
    L.append(str(x))


def finir():
    (ICI / "cote.txt").write_text("\n".join(L) + "\n")
    sys.exit(0)


def cotes(x):
    """Cote (+1 achat, -1 vente) de chaque tick selon chaque regle."""
    p, a = x["price"].to_numpy(float), x["ask"].to_numpy(float)
    ap = np.r_[np.nan, a[:-1]]
    dp = np.sign(np.diff(p, prepend=p[0]))
    tick = pd.Series(np.where(dp == 0, np.nan, dp)).ffill().fillna(0).to_numpy()
    out = {"T": tick}
    v = np.where(np.isnan(ap), tick, np.where(p >= ap, 1, -1))
    out["V"] = v
    out["VL"] = np.where(np.isnan(ap), tick, np.where(p >= ap, 1, np.where(p <= ap - TICK, -1, tick)))
    out["VA"] = np.where(np.isnan(a), tick, np.where(p >= a, 1, -1))
    out["VA1"] = np.where(np.isnan(a), tick, np.where(p >= a - TICK, 1, -1))
    return out


def minutes(client, debut, fin):
    df = client.history("NQ.F", dataset="futures", timeframe="tick", start=debut, end=fin, dest=str(ICI / "_tmp"))
    x = pd.DataFrame({"t": pd.to_datetime(df["ts"], utc=True), "price": pd.to_numeric(df["price"], errors="coerce"),
                      "volume": pd.to_numeric(df["volume"], errors="coerce"), "ask": pd.to_numeric(df["ask"], errors="coerce")})
    x = x.dropna(subset=["t", "price", "volume"]).sort_values("t", kind="stable").reset_index(drop=True)
    c = cotes(x)
    x["t"] = x["t"].dt.tz_convert("America/New_York")
    m = x.t.dt.hour * 60 + x.t.dt.minute - 570
    garde = (m >= 0) & (m < 390)
    y = pd.DataFrame({"jour": x.t.dt.strftime("%Y-%m-%d"), "minute": m, "v": x["volume"]})
    for k in REGLES:
        y[k] = c[k] * x["volume"].to_numpy()
    y = y[garde]
    dire(f"  {debut[:10]} - {fin[:10]} : {len(df)} ticks, {int(garde.sum())} de 9 h 30 a 16 h")
    return y.groupby(["jour", "minute"], as_index=False).sum()


def accord(lse, db, regle):
    m = db.merge(lse, on=["jour", "minute"])
    r = []
    for _, g in m.groupby("jour"):
        g = g.sort_values("minute")
        a, b = g["delta_db"].rolling(30).sum(), g[regle].rolling(30).sum()
        ok = a.notna() & (a != 0) & (b != 0)
        r.append(pd.DataFrame({"a": a[ok], "b": b[ok]}))
    r = pd.concat(r)
    return float((np.sign(r.a) == np.sign(r.b)).mean()), len(r), float(np.corrcoef(m["delta_db"], m[regle])[0, 1])


cle = os.environ.get("LSE_API_KEY", "").strip()
if not cle:
    dire("Secret LSE_API_KEY absent.")
    finir()
from lse import LSE  # noqa: E402

client = LSE(api_key=cle)
d = pd.read_csv(R / "orderflow/donnees/nq_secondes_1.csv.gz", usecols=["t", "achat", "vente"])
d["t"] = pd.to_datetime(d["t"])
d["jour"], d["minute"] = d.t.dt.strftime("%Y-%m-%d"), d.t.dt.hour * 60 + d.t.dt.minute - 570
db = d.groupby(["jour", "minute"]).agg(achat=("achat", "sum"), vente=("vente", "sum")).reset_index()
db["delta_db"] = db.achat - db.vente
dire("London Strategic Edge : choix du cote agresseur (NQ.F) contre Databento")
dire("Etalonnage :")
et = pd.concat([minutes(client, a, b) for a, b in ETALONNAGE])
res = {k: accord(et, db, k) for k in REGLES}
for k, (acc, n, c) in res.items():
    dire(f"- {k} : meme signe sur 30 min {acc:.1%} de {n} fenetres ; correlation du delta d'une minute {c:.3f}")
choix = max(REGLES, key=lambda k: res[k][0])
dire(f"Regle retenue a l'etalonnage : {choix}")
dire("Validation :")
va = pd.concat([minutes(client, a, b) for a, b in VALIDATION])
acc, n, c = accord(va, db, choix)
dire(f"- {choix} : meme signe sur 30 min {acc:.1%} de {n} fenetres ; correlation {c:.3f}")
for k in REGLES:
    if k != choix:
        a2, n2, c2 = accord(va, db, k)
        dire(f"  (pour information : {k} {a2:.1%})")
dire(f"-> source {'ACCEPTEE' if acc >= SEUIL else 'REFUSEE'} (seuil {SEUIL:.0%}) avec la regle {choix}")
pd.concat([et, va]).to_csv(ICI / "minutes_lse.csv", index=False)
finir()
