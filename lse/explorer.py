#!/usr/bin/env python3
"""London Strategic Edge (LSE) : le NQ y est-il, depuis quand, et son delta ressemble-t-il au vrai ?

1. Catalogue des futures du coffre LSE : lignes du NQ / Nasdaq (ticks, premier et dernier tick).
2. Ticks du NQ sur deux seances deja connues chez Databento (29 et 30 septembre 2026) : colonnes, volume.
3. Cote agresseur deduit (au prix vendeur ou au-dessus = achat ; au prix acheteur ou en dessous = vente ; entre les
   deux : regle du tick), delta par minute de 9 h 30 a 16 h (New York), compare a Databento
   (orderflow/donnees/nq_secondes_1.csv.gz) : correlation, meme signe du delta des 30 minutes.
Cle : variable LSE_API_KEY (secret du depot, jamais ecrite ni affichee). Ecrit lse/resultats.txt, lse/catalogue_nq.csv.
Lancer depuis la racine du depot."""
import os
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
R = ICI.parent
L = []


def dire(x=""):
    print(x, flush=True)
    L.append(str(x))


def finir():
    (ICI / "resultats.txt").write_text("\n".join(L) + "\n")
    sys.exit(0)


cle = os.environ.get("LSE_API_KEY", "").strip()
if not cle:
    dire("Secret LSE_API_KEY absent : rien n'a ete demande a LSE.")
    finir()

from lse import LSE  # noqa: E402

client = LSE(api_key=cle)
dire("London Strategic Edge : exploration pour le filtre delta (NQ)")
# 1. catalogue
try:
    cat = pd.DataFrame(client.datasets())
    dire(f"Coffre : {len(cat)} lignes ; classes : " + ", ".join(f"{k} {v}" for k, v in cat["dataset"].value_counts().items()))
    fut = cat[cat["dataset"].astype(str).str.contains("futur", case=False)]
    nq = cat[cat["symbol"].astype(str).str.contains("NQ|NDX|NAS|US100|USTEC|NASDAQ", case=False, regex=True)]
    nq.to_csv(ICI / "catalogue_nq.csv", index=False)
    dire(f"Futures : {len(fut)} lignes. Exemples : " + ", ".join(fut["symbol"].astype(str).head(60)))
    dire("Lignes NQ / Nasdaq :")
    for r in nq.itertuples(index=False):
        dire("- " + " | ".join(f"{k}={getattr(r, k)}" for k in nq.columns))
except Exception as e:
    dire(f"ERREUR catalogue : {e!r}")
    traceback.print_exc()
    finir()
if nq.empty:
    dire("Aucun NQ dans le coffre.")
    finir()
# le NQ des futures en priorite, puis celui qui a le plus de ticks
nq = nq.assign(f=nq["dataset"].astype(str).str.contains("futur", case=False)).sort_values(["f", "ticks"], ascending=False)
choix = nq.iloc[0]
dire(f"Choisi : {choix['symbol']} ({choix['dataset']}), premier tick {choix.get('first_tick')}, dernier {choix.get('last_tick')}")
# 2. ticks de deux seances connues
try:
    df = client.history(choix["symbol"], dataset=choix["dataset"], timeframe="tick",
                        start="2026-09-29T13:00:00", end="2026-09-30T21:00:00", dest=str(ICI / "_tmp"))
except Exception as e:
    dire(f"ERREUR ticks : {e!r}")
    finir()
dire(f"Ticks recus : {len(df)} ; colonnes : {list(df.columns)}")
dire("Premieres lignes :")
for line in df.head(5).to_string().splitlines():
    dire("  " + line)
cols = {c.lower(): c for c in df.columns}
tcol = next((cols[c] for c in ("timestamp", "time", "ts", "datetime", "t") if c in cols), None)
pcol, bcol, acol = cols.get("price"), cols.get("bid"), cols.get("ask")
vcol = next((cols[c] for c in ("volume", "size", "qty", "quantity") if c in cols), None)
scol = next((cols[c] for c in ("side", "aggressor", "aggressor_side") if c in cols), None)
if tcol is None or pcol is None or vcol is None:
    dire("Colonnes de temps, prix ou volume introuvables : comparaison impossible.")
    finir()
x = pd.DataFrame({"t": pd.to_datetime(df[tcol], utc=True), "p": pd.to_numeric(df[pcol], errors="coerce"),
                  "v": pd.to_numeric(df[vcol], errors="coerce"), "i": np.arange(len(df))})
if bcol and acol:
    x["b"], x["a"] = pd.to_numeric(df[bcol], errors="coerce"), pd.to_numeric(df[acol], errors="coerce")
x = x.dropna(subset=["t", "p", "v"]).sort_values("t").reset_index(drop=True)
x["t"] = x["t"].dt.tz_convert("America/New_York")
x = x[(x.t.dt.hour * 60 + x.t.dt.minute >= 570) & (x.t.dt.hour * 60 + x.t.dt.minute < 960)].reset_index(drop=True)
dire(f"Ticks de 9 h 30 a 16 h : {len(x)} ; volume total {x.v.sum():,.0f} ; ticks a volume nul : {(x.v == 0).mean():.1%}")
if scol:
    s = df[scol].iloc[x["i"].to_numpy()].astype(str).str.upper().reset_index(drop=True)
    sens = np.where(s.str.startswith(("B", "A")), 1, np.where(s.str.startswith(("S",)), -1, 0))
    dire(f"Cote agresseur fourni ({scol}) : valeurs {s.value_counts().head(5).to_dict()}")
else:
    sens = np.zeros(len(x))
    if bcol and acol:
        sens = np.where(x.p >= x.a, 1, np.where(x.p <= x.b, -1, 0))
    dp = np.sign(x.p.diff().fillna(0).to_numpy())
    dern = 0
    for i in range(len(sens)):                       # entre les deux (ou sans cotation) : regle du tick
        if dp[i] != 0:
            dern = dp[i]
        if sens[i] == 0:
            sens[i] = dern
    dire(f"Cote deduit : au prix vendeur ou acheteur pour {np.mean((x.p >= x.get('a', np.inf)) | (x.p <= x.get('b', -np.inf))):.1%} des ticks")
x["jour"], x["minute"] = x.t.dt.strftime("%Y-%m-%d"), x.t.dt.hour * 60 + x.t.dt.minute - 570
x["delta"] = sens * x.v
lse = x.groupby(["jour", "minute"]).agg(delta_lse=("delta", "sum"), v_lse=("v", "sum")).reset_index()
d = pd.read_csv(R / "orderflow/donnees/nq_secondes_1.csv.gz", usecols=["t", "achat", "vente"])
d["t"] = pd.to_datetime(d["t"])
d = d[(d.t >= "2026-09-29") & (d.t < "2026-10-01")]
d["jour"], d["minute"] = d.t.dt.strftime("%Y-%m-%d"), d.t.dt.hour * 60 + d.t.dt.minute - 570
db = d.groupby(["jour", "minute"]).agg(achat=("achat", "sum"), vente=("vente", "sum")).reset_index()
db["delta_db"], db["v_db"] = db.achat - db.vente, db.achat + db.vente
m = db.merge(lse, on=["jour", "minute"])
if m.empty:
    dire("Aucune minute commune avec Databento.")
    finir()
dire(f"Minutes communes avec Databento : {len(m)} ; volume LSE / Databento : {m.v_lse.sum() / m.v_db.sum():.3f}")
dire(f"Delta d'une minute : correlation {np.corrcoef(m.delta_db, m.delta_lse)[0, 1]:.3f}, meme signe {(np.sign(m.delta_db) == np.sign(m.delta_lse)).mean():.1%}")
r = []
for _, g in m.groupby("jour"):
    g = g.sort_values("minute")
    a, b = g.delta_db.rolling(30).sum(), g.delta_lse.rolling(30).sum()
    ok = a.notna() & (a != 0) & (b != 0)
    r.append(pd.DataFrame({"a": a[ok], "b": b[ok]}))
r = pd.concat(r)
if len(r):
    dire(f"Delta des 30 minutes (celui du filtre) : {len(r)} fenetres, meme signe {(np.sign(r.a) == np.sign(r.b)).mean():.1%},"
         f" correlation {np.corrcoef(r.a, r.b)[0, 1]:.3f}")
finir()
