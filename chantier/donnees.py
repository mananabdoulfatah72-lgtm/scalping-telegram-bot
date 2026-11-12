"""Chargement des donnees du chantier. Rien n'est telecharge : tout vient des branches du depot.

Variables d'environnement (dossiers ou les branches sont extraites, par exemple avec `git worktree add`) :
  KB = claude/keen-babbage-r686cl      (minutes du NQ 2011 - 2026, Nasdaq et or 24 h en 5 minutes)
  AT = claude/affectionate-turing-tnz0mn (VIX, VIX3M, VXN, bitcoin)
  OP = claude/optimistic-ptolemy-xs24ra  (radar : VIX et VXN de 2026, journal de rejeu de la zone)
  CACHE = dossier des caches .npz (par defaut : chantier/cache, non suivi par git)
"""
import datetime as dt
import glob
import os
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
KB = Path(os.environ.get("KB", RACINE.parent / "kb"))
AT = Path(os.environ.get("AT", RACINE.parent / "at"))
OP = Path(os.environ.get("OP", RACINE.parent / "op"))
CACHE = Path(os.environ.get("CACHE", ICI / "cache"))
CACHE.mkdir(parents=True, exist_ok=True)

N = 390                 # minutes d'une seance 9 h 30 - 16 h
PREF = 28500.0          # prix de reference : gains "au prix d'aujourd'hui" (comme l'arene)
FRAIS = 3.0             # $ par aller-retour et par MNQ
TICK = 0.25
NY = ZoneInfo("America/New_York")
FIN_EXPLO = "2022-12-31"


def nq_minutes():
    """Minutes du NQ en seance. Renvoie un dict : J (dates), O H L C V (seances x 390), ok (seance complete),
    contrat (identifiant du contrat de la seance). Minutes manquantes recopiees a plat (volume 0)."""
    f = CACHE / "nq_minutes.npz"
    if f.exists():
        z = np.load(f, allow_pickle=False)
        return {k: z[k] for k in z.files}
    a = pd.read_csv(KB / "intraday/donnees/nasdaq100_1min.csv.gz")
    b = pd.read_csv(RACINE / "zone/robot/nq_1min.csv.gz")
    fin_a = a.t.str[:10].max()
    d = pd.concat([a, b[b.t.str[:10] > fin_a]], ignore_index=True)
    jour = d.t.str[:10].to_numpy()
    m = (d.t.str[11:13].astype(int) * 60 + d.t.str[14:16].astype(int) - 570).to_numpy()
    g = (m >= 0) & (m < N)
    d, jour, m = d[g], jour[g], m[g]
    J = np.unique(jour)
    s = np.searchsorted(J, jour)
    S = len(J)
    O = np.full((S, N), np.nan); H = O.copy(); L = O.copy(); C = O.copy(); V = np.zeros((S, N))
    O[s, m] = d.o.to_numpy(); H[s, m] = d.h.to_numpy(); L[s, m] = d.l.to_numpy(); C[s, m] = d.c.to_numpy()
    V[s, m] = d.v.to_numpy(float)
    nb = np.isfinite(C).sum(1)
    ok = np.isfinite(C[:, 0]) & np.isfinite(C[:, N - 1]) & (nb >= 370)
    contrat = np.zeros(S, np.int64)
    cc = d.contrat.to_numpy()
    contrat[s[::-1]] = cc[::-1]                       # premier contrat vu dans la seance
    for i in range(S):                                # recopie a plat des minutes manquantes
        if not np.isfinite(C[i]).all():
            c = pd.Series(C[i]).ffill().bfill().to_numpy()
            trou = ~np.isfinite(O[i])
            O[i, trou] = H[i, trou] = L[i, trou] = c[trou]; C[i] = c
    out = dict(J=J.astype("U10"), O=O, H=H, L=L, C=C, V=V, ok=ok, contrat=contrat)
    np.savez_compressed(f, **out)
    return out


def _dimanche(a, mois, n):
    """n-ieme dimanche du mois (n = 0 : le dernier), en jours depuis 1970."""
    if n:
        d = dt.date(a, mois, 1); d += dt.timedelta(days=(6 - d.weekday()) % 7 + 7 * (n - 1))
    else:
        d = dt.date(a + (mois == 12), mois % 12 + 1, 1) - dt.timedelta(days=1); d -= dt.timedelta(days=(d.weekday() + 1) % 7)
    return (d - dt.date(1970, 1, 1)).days


def heures_corrigees(t):
    """Les fichiers 24 h du depot (Dukascopy) sont en avance de 60 minutes, depuis 2019, pendant les semaines ou les
    Etats-Unis et l'Europe n'ont pas la meme heure d'ete : du 2e au dernier dimanche de mars, et du dernier dimanche
    d'octobre au 1er dimanche de novembre. Constat de la contre-revue (12 novembre 2026) : sur ces 139 seances, les
    rendements de 5 minutes du fichier suivent le future NQ a +60 minutes (correlation 1,00) et pas a l'heure du
    fichier ; aucun cas ailleurs ; meme decalage sur tous les marches 24 h. On ajoute donc 60 minutes a ces barres."""
    t = np.asarray(t, dtype="int64").copy()
    for a in range(2019, pd.Timestamp(int(t.max()) * 60, unit="s").year + 1):
        for d, f in ((_dimanche(a, 3, 2), _dimanche(a, 3, 0)), (_dimanche(a, 10, 0), _dimanche(a, 11, 1))):
            t[(t >= d * 1440) & (t < f * 1440)] += 60
    assert (np.diff(t) > 0).all(), "heures corrigees : barres en double"
    return t


def cfd(nom="usatechidxusd", brut=False):
    """Barres de 5 minutes 24 h (Dukascopy, UTC). Renvoie t (minutes depuis 1970, UTC), o, h, l, c.
    Les heures sont corrigees (voir `heures_corrigees`) ; brut=True rend les heures du fichier."""
    t, o, h, l, c = _cfd_brut(nom)
    return (t if brut else heures_corrigees(t)), o, h, l, c


def _cfd_brut(nom):
    f = CACHE / f"cfd_{nom}.npz"
    if f.exists():
        z = np.load(f)
        return z["t"], z["o"], z["h"], z["l"], z["c"]
    d = pd.concat([pd.read_csv(x) for x in sorted(glob.glob(str(KB / f"sessions24/annees/{nom}_*_5m.csv.gz")))])
    t = (pd.to_datetime(d.t).astype("datetime64[s]").astype("int64") // 60).to_numpy()
    o, h, l, c = (d[k].to_numpy(float) for k in "ohlc")
    i = np.argsort(t, kind="stable")
    t, o, h, l, c = t[i], o[i], h[i], l[i], c[i]
    g = np.r_[True, np.diff(t) > 0]
    t, o, h, l, c = t[g], o[g], h[g], l[g], c[g]
    np.savez_compressed(f, t=t, o=o, h=h, l=l, c=c)
    return t, o, h, l, c


def heure_ny(t_min):
    """Pour des minutes UTC depuis 1970 : (date de New York 'AAAA-MM-JJ', minute de la journee, jour de semaine 0=lundi)."""
    idx = pd.to_datetime(np.asarray(t_min, dtype="int64") * 60, unit="s", utc=True).tz_convert(NY)
    return idx.strftime("%Y-%m-%d").to_numpy(), (idx.hour * 60 + idx.minute).to_numpy(), idx.dayofweek.to_numpy()


def clotures(noms=("VIX", "VIX3M", "VXN")):
    """Clotures quotidiennes des indices de volatilite : DataFrame indexe par date (texte), colonnes = noms."""
    out = {}
    rad = pd.concat([pd.read_csv(x) for x in sorted(glob.glob(str(OP / "radar/donnees/jour/yahoo/*.csv.gz")))])
    for n in noms:
        s = pd.Series(dtype=float)
        p = AT / f"donnees_libres/yahoo/jour/{n}.csv.gz"
        if p.exists():
            d = pd.read_csv(p); s = pd.Series(d.c.to_numpy(float), index=d.t.str[:10])
        if n == "VXN":
            d = pd.read_csv(AT / "donnees_libres/vxn/cboe.csv.gz"); s = pd.Series(d.c.to_numpy(float), index=d.t.str[:10])
        r = rad[rad.serie == f"^{n}:c"]
        r = pd.Series(r.valeur.to_numpy(float), index=r.date.to_numpy())
        s = pd.concat([s, r[~r.index.isin(s.index)]]).sort_index()
        out[n] = s[~s.index.duplicated()]
    return pd.DataFrame(out).sort_index()


def minutes_marche(chemin):
    """Minutes d'un autre marche (meme format que le NQ) : DataFrame t, o, h, l, c."""
    return pd.read_csv(KB / chemin, usecols=["t", "o", "h", "l", "c"])


def tstat(v):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    s = v.std(ddof=1) if len(v) > 1 else 0.0
    return float(v.mean() / (s / np.sqrt(len(v)))) if s > 0 else 0.0


def bh(pvals, q=0.05):
    """Benjamini-Hochberg : tableau de booleens (retenu ou non)."""
    p = np.asarray(pvals, float); n = len(p); o = np.argsort(p)
    seuil = q * (np.arange(1, n + 1)) / n
    passe = p[o] <= seuil
    k = np.nonzero(passe)[0].max() + 1 if passe.any() else 0
    out = np.zeros(n, bool); out[o[:k]] = True
    return out


def p_unilateral(t):
    """p unilaterale d'un t (loi normale : echantillons de plus de 500 seances)."""
    from math import erf, sqrt
    return 0.5 * (1 - erf(t / sqrt(2)))
