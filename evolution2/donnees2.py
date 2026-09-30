"""Donnees de l'evolution n°2 : les barres de 5 minutes de evolution/cache (seances completes), plus, pour chaque
seance, le profil de volume de la seance precedente, les murs d'options de la veille et les 9 filtres (README.md).
Tout est connu avant l'ouverture de la seance."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "evolution"))
import moteur as M1  # noqa: E402
import tournoi3 as T  # noqa: E402
from profil import profil  # noqa: E402

TICK = 0.25


def regime_vol(o, h, l):
    """Amplitude de la veille contre la mediane des 20 seances d'avant (comme evolution/donnees.py) : 1 agite, 2 calme."""
    amp = (h.max(axis=1) - l.min(axis=1)) / o[:, 0]
    veille = pd.Series(amp).shift(1)
    med = pd.Series(amp).shift(2).rolling(20, min_periods=20).median()
    return np.where(veille > med, 1, np.where(veille <= med, 2, 0)).astype(np.int8)


def profil_veille(h, l, v):
    poc, vah, val = profil(h, l, v, TICK)
    dec = lambda x: np.r_[np.nan, x[:-1]]
    return dec(poc), dec(vah), dec(val)


def matrice_filtres(jours, regime, Q):
    J = pd.DatetimeIndex(jours)
    g, dx, vr = T.veille(J, Q["gex"]), T.veille(J, Q["dix"]), T.veille(J, Q["vix_ratio"])
    g_med, dx_med = T.quantile_252(g, 0.5), T.quantile_252(dx, 0.5)
    with np.errstate(invalid="ignore"):
        lignes = [np.ones(len(J), bool), regime == 1, regime == 2,
                  g < g_med, g >= g_med, vr >= 1.0, vr < 1.0, dx >= dx_med, dx < dx_med]
    return np.array([np.nan_to_num(x, nan=0).astype(bool) for x in lignes])


def murs(marche, jours):
    f = ICI / "donnees" / f"murs_{marche}.csv"
    n = len(jours)
    if not f.exists():
        return np.full(n, np.nan), np.full(n, np.nan)
    m = pd.read_csv(f, parse_dates=["date"]).set_index("date")
    J = pd.DatetimeIndex(jours)
    return T.veille(J, m["call"].dropna()), T.veille(J, m["put"].dropna())


def preparer(d, marche, Q):
    """d : dict d'un cache evolution (recherche_* ou coffre_*). Ajoute poc, vah, val, mur_c, mur_p, fok."""
    poc, vah, val = profil_veille(d["h"], d["l"], d["v"])
    mc, mp = murs(marche, d["jours"])
    return {**d, "poc": poc, "vah": vah, "val": val, "mur_c": mc, "mur_p": mp, "fok": matrice_filtres(d["jours"], d["regime"], Q)}


def charger(marche, nature, Q):
    return preparer(M1.charger(ICI.parent / "evolution" / "cache" / f"{nature}_{marche}.npz"), marche, Q)


def melanger2(d, rng):
    """Bruit : dans chaque seance, les barres de 5 minutes (et leur volume) sont remises au hasard, la 1re restant en
    place ; volatilite et resultat de la seance conserves. Regime de volatilite et profil de volume recalcules sur les
    barres melangees ; GEX, DIX, VIX et murs inchanges."""
    o, h, l, c, v = d["o"], d["h"], d["l"], d["c"], d["v"]
    nj, nb = o.shape
    ro = np.ones_like(o)
    ro[:, 1:] = o[:, 1:] / c[:, :-1]
    rh, rl, rc = h / o, l / o, c / o
    perm = np.concatenate([np.zeros((nj, 1), int), 1 + np.argsort(rng.random((nj, nb - 1)), axis=1)], axis=1)
    ro, rh, rl, rc, v2 = (np.take_along_axis(x, perm, axis=1) for x in (ro, rh, rl, rc, v))
    o2, h2, l2, c2 = (np.empty_like(o) for _ in range(4))
    prix = o[:, 0].copy()
    for b in range(nb):
        ob = prix * (ro[:, b] if b > 0 else 1.0)
        o2[:, b], h2[:, b], l2[:, b], c2[:, b] = ob, ob * rh[:, b], ob * rl[:, b], ob * rc[:, b]
        prix = c2[:, b]
    arr = lambda x: np.round(x / TICK) * TICK
    o2, h2, l2, c2 = arr(o2), arr(h2), arr(l2), arr(c2)
    regime = regime_vol(o2, h2, l2)
    fok = d["fok"].copy()
    fok[1], fok[2] = regime == 1, regime == 2
    poc, vah, val = profil_veille(h2, l2, v2)
    return {**d, "o": o2, "h": h2, "l": l2, "c": c2, "v": v2, "regime": regime, "fok": fok, "poc": poc, "vah": vah, "val": val}
