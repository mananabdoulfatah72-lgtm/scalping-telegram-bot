"""Chargement independant des fichiers bruts (contre-revue). Aucune fonction de l'etude n'est importee."""
import glob, os, datetime as dt
import numpy as np, pandas as pd

KB = os.environ["KB"]; AT = os.environ["AT"]; OP = os.environ["OP"]
REPO = "/home/user/scalping-telegram-bot"
ICI = os.path.dirname(os.path.abspath(__file__))
PREF = 28500.0

def nq_brut():
    f = os.path.join(ICI, "nq_brut.pkl")
    if os.path.exists(f):
        return pd.read_pickle(f)
    a = pd.read_csv(f"{KB}/intraday/donnees/nasdaq100_1min.csv.gz")
    b = pd.read_csv(f"{REPO}/zone/robot/nq_1min.csv.gz")
    fin_a = a.t.str[:10].max()
    d = pd.concat([a, b[b.t.str[:10] > fin_a]], ignore_index=True)
    d["jour"] = d.t.str[:10]
    d["m"] = d.t.str[11:13].astype(int) * 60 + d.t.str[14:16].astype(int) - 570
    d = d[(d.m >= 0) & (d.m < 390)].reset_index(drop=True)
    d.to_pickle(f)
    return d

def cfd_brut(nom="usatechidxusd"):
    f = os.path.join(ICI, f"cfd_{nom}.pkl")
    if os.path.exists(f):
        return pd.read_pickle(f)
    d = pd.concat([pd.read_csv(x) for x in sorted(glob.glob(f"{KB}/sessions24/annees/{nom}_*_5m.csv.gz"))], ignore_index=True)
    d["utc"] = pd.to_datetime(d.t, format="%Y-%m-%d %H:%M")
    d = d.sort_values("utc", kind="stable").drop_duplicates("utc", keep="first").reset_index(drop=True)
    d.to_pickle(f)
    return d

def _nieme_dimanche(annee, mois, n):
    j = dt.date(annee, mois, 1)
    j += dt.timedelta(days=(6 - j.weekday()) % 7)      # premier dimanche
    return j + dt.timedelta(days=7 * (n - 1))

def decalage_ny(utc):
    """Decalage (heures) New York - UTC pour des instants UTC (regle americaine depuis 2007), code a la main."""
    utc = pd.DatetimeIndex(utc)
    off = np.full(len(utc), -5, dtype=int)
    an = utc.year.to_numpy()
    for a in np.unique(an):
        deb = pd.Timestamp(_nieme_dimanche(int(a), 3, 2)) + pd.Timedelta(hours=7)   # 2 h locale (EST) = 7 h UTC
        fin = pd.Timestamp(_nieme_dimanche(int(a), 11, 1)) + pd.Timedelta(hours=6)  # 2 h locale (EDT) = 6 h UTC
        g = (utc >= deb) & (utc < fin)
        off[g] = -4
    return off

def vol_brut():
    out = {}
    rad = pd.concat([pd.read_csv(x) for x in sorted(glob.glob(f"{OP}/radar/donnees/jour/yahoo/*.csv.gz"))])
    for n in ("VIX", "VIX3M", "VXN"):
        if n == "VXN":
            d = pd.read_csv(f"{AT}/donnees_libres/vxn/cboe.csv.gz")
        else:
            d = pd.read_csv(f"{AT}/donnees_libres/yahoo/jour/{n}.csv.gz")
        s = pd.Series(d.c.to_numpy(float), index=d.t.str[:10])
        r = rad[rad.serie == f"^{n}:c"]
        r = pd.Series(r.valeur.to_numpy(float), index=r.date.to_numpy())
        out[n] = (s, r)
    return out
