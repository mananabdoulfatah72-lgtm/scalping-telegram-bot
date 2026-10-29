#!/usr/bin/env python3
"""Partie 3 du systeme order flow (flux/README.md) : vague quant. Familles G1 a G8 sur le vrai tape (Databento + export
Rithmic) et G2b (VPIN par barres) sur les barres gratuites de 2011 - 2026, sur les vraies donnees et 8 jumeaux de bruit.
Range le gain net et le nombre de trades de chaque configuration par seance dans FLUX_CALCUL (hors du depot).

Lancer : KB=<copie de claude/keen-babbage-r686cl> python3 flux/quant.py"""
import itertools
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

import donnees as D
import reglages as R

ICI = Path(__file__).resolve().parent
GRAINES = tuple(range(21, 29))
CHECK15 = np.arange(30, 361, 15)

GESTION = list(itertools.product((15, 30, 60, 0), (0.0, 0.5, 1.0), (0.0, 1.0, 2.0), (1, -1)))   # duree (0 = 15 h 59)
GESTION_G5 = list(itertools.product((0,), (0.0, 0.5, 1.0), (0.0,), (1, -1)))
GESTION_G9 = [(0, 0.0, 0.0, 1), (0, 0.0, 0.0, -1)]
FAMILLES = {
    "G1": list(itertools.product((30, 60), (5, 15, 30), ("residu", "flux"), (1.0, 1.5, 2.0))),
    "G2": [(n, "haut", q) for n in (10, 25, 50) for q in (50, 75, 90)] + [(n, "bas", q) for n in (10, 25, 50) for q in (25, 50)],
    "G3": list(itertools.product((15, 30, 60), (5, 15, 30), (80, 90, 95), ("libre", "accord", "desaccord"))),
    "G4": list(itertools.product((29, 59, 89), (0, 70, 85), ("libre", "accord", "desaccord"))),
    "G5": list(itertools.product((329, 359), ("jour", "60 min", "ouverture"), (0, 70, 85), ("libre", "accord"))),
    "G6": list(itertools.product((10, 25, 50), (5, 15, 30), (90, 95, 99))),
    "G7": list(itertools.product((1.0, 1.5, 2.0), (5, 15, 30), ("desaccord", "accord", "libre"))),
    "G8": list(itertools.product((5, 15, 30), (90, 95), (0.25, 0.5), ("partout", "extreme", "vwap"))),
    "G9": list(itertools.product(("seance", "derniere heure"), (0, 70, 85), ("libre", "accord", "desaccord"))),
}
N_MIN = {"G4": 25, "G5": 25, "G9": 25, "G2b": 200}


def table_configs(familles=None):
    lignes = []
    for fam, liste in FAMILLES.items():
        if familles and fam not in familles:
            continue
        for i, sg in enumerate(liste):
            for j, g in enumerate(GESTION_G5 if fam == "G5" else GESTION_G9 if fam == "G9" else GESTION):
                lignes.append((fam, i, j, sg, *g))
    return pd.DataFrame(lignes, columns=["famille", "i_signal", "i_gestion", "signal", "duree", "stop_u", "objectif_u",
                                         "sens"])


def table_g2b():
    t = table_configs(["G2"])
    t["famille"] = "G2b"
    return t


# ---------------------------------------------------------------------------------------------- gros lots
def gros_lots(jours):
    """Flux net par minute des transactions d'au moins 10, 25 et 50 contrats (Databento) ; NaN sans donnees."""
    g = pd.concat([pd.read_csv(p) for p in sorted(D.OF.glob("nq_gros_*.csv.gz"))], ignore_index=True)   # lots disjoints
    t = pd.to_datetime(g["t"])
    jour = t.dt.normalize()
    minute = ((t - jour).dt.total_seconds() // 60 - 570).astype(int).to_numpy()
    ok = (minute >= 0) & (minute < D.NM) & jour.isin(jours).to_numpy()
    g, jour, minute = g[ok], jour[ok], minute[ok]
    ij = jours.get_indexer(jour)
    S = len(jours)
    present = np.zeros(S, bool)
    present[np.unique(ij)] = True
    out = {}
    for taille in (10, 25, 50):
        a = np.zeros((S, D.NM))
        k = g["taille"].to_numpy() >= taille
        np.add.at(a, (ij[k], minute[k]), (g["sens"].to_numpy() * g["taille"].to_numpy())[k])
        a[~present] = np.nan
        out[taille] = a
    return out


# ---------------------------------------------------------------------------------------------- mesures
def retourner(o, h, l, c, graine, par_seance=False):
    """Bruit par signe (partie 2) : renvoie les prix et le masque des minutes retournees. par_seance : chaque seance
    repart de sa vraie premiere minute (15 ans : sinon le prix bruite derive trop, jusqu'a devenir negatif)."""
    S = o.shape[0]
    rng = np.random.default_rng(graine)
    flip = rng.random((S, D.NM)) < 0.5
    flip[:, 0] = False
    if par_seance:
        cprev = np.concatenate([o[:, :1], c[:, :-1]], axis=1)
        do, dh, dl, dc = o - cprev, h - cprev, l - cprev, c - cprev
        do, dh, dl, dc = (np.where(flip, -do, do), np.where(flip, -dl, dh), np.where(flip, -dh, dl),
                          np.where(flip, -dc, dc))
        c2 = o[:, :1] + np.cumsum(dc, axis=1)
        p2 = np.concatenate([o[:, :1], c2[:, :-1]], axis=1)
        return p2 + do, p2 + dh, p2 + dl, c2, flip
    of, hf, lf, cf, ff = (x.ravel() for x in (o, h, l, c, flip))
    cprev = np.concatenate([[of[0]], cf[:-1]])
    do, dh, dl, dc = of - cprev, hf - cprev, lf - cprev, cf - cprev
    do, dh, dl, dc = (np.where(ff, -do, do), np.where(ff, -dl, dh), np.where(ff, -dh, dl), np.where(ff, -dc, dc))
    c2 = of[0] + np.cumsum(dc)
    p2 = np.concatenate([[of[0]], c2[:-1]])
    return (p2 + do).reshape(S, D.NM), (p2 + dh).reshape(S, D.NM), (p2 + dl).reshape(S, D.NM), c2.reshape(S, D.NM), flip


def sigma60(dc):
    """Ecart-type (ddof 1) des Δc des minutes max(1, t - 59) a t."""
    S = dc.shape[0]
    x = dc.copy()
    x[:, 0] = 0.0
    c1 = np.cumsum(x, axis=1)
    c2 = np.cumsum(x * x, axis=1)
    t = np.arange(D.NM)
    debut = np.maximum(1, t - 59)
    n = t - debut + 1
    s1 = c1 - np.where(debut - 1 >= 0, c1[:, debut - 1], 0.0)
    s2 = c2 - np.where(debut - 1 >= 0, c2[:, debut - 1], 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        var = (s2 - s1 * s1 / n) / (n - 1)
    out = np.sqrt(np.maximum(var, 0.0))
    out[:, :2] = np.nan
    return out


def rang_precedent(valeurs, jouable_debut, k=5, minutes=slice(30, None)):
    """Percentiles 0..100 des valeurs (seance x minute) des k seances precedentes (minutes donnees)."""
    S = valeurs.shape[0]
    Q = np.full((S, 101), np.nan)
    for d in range(k, S):
        x = valeurs[d - k:d, minutes].ravel()
        x = x[np.isfinite(x)]
        if len(x) > 50 and np.isfinite(valeurs[d - k:d, minutes]).all():
            Q[d] = np.percentile(x, np.arange(101))
    return Q


@njit(cache=True)
def vpin_calc(achats, ventes, vb, debut):
    """VPIN et flux signe des n derniers seaux (n = 10, 25, 50) a la fin de chaque minute, seaux de volume vb[s]
    remplis dans l'ordre des seances (minutes partagees au prorata). Seances < debut : pas de seau."""
    S, M = achats.shape
    ns = (10, 25, 50)
    vp = np.full((3, S, M), np.nan)
    fl = np.full((3, S, M), np.nan)
    cap = S * M * 4 + 10
    imb = np.zeros(cap)
    sgn = np.zeros(cap)
    nb = 0
    ba, bv, rempli = 0.0, 0.0, 0.0
    for s in range(debut, S):
        V = vb[s]
        if not (V > 0):
            continue
        for t in range(M):
            a, v = achats[s, t], ventes[s, t]
            tot = a + v
            while tot > 1e-12:
                place = V - rempli
                part = min(1.0, place / tot)
                ba += a * part
                bv += v * part
                rempli += tot * part
                a -= a * part
                v -= v * part
                tot = a + v
                if rempli >= V - 1e-9:
                    imb[nb] = abs(ba - bv) / V
                    sgn[nb] = ba - bv
                    nb += 1
                    ba, bv, rempli = 0.0, 0.0, 0.0
            for j in range(3):
                n = ns[j]
                if nb >= n:
                    s1, s2 = 0.0, 0.0
                    for i in range(nb - n, nb):
                        s1 += imb[i]
                        s2 += sgn[i]
                    vp[j, s, t] = s1 / n
                    fl[j, s, t] = s2
    return vp, fl


def mesures(o, h, l, c, achats, ventes, jouable, bl=None, scale=None):
    S = o.shape[0]
    v = achats + ventes
    delta = achats - ventes
    cd = np.cumsum(delta, axis=1)
    dc = np.zeros_like(c)
    dc[:, 1:] = c[:, 1:] - c[:, :-1]
    s1 = sigma60(dc)
    typ = (h + l + c) / 3
    cv = np.cumsum(v, axis=1)
    sur = np.where(cv > 0, cv, 1)
    vwap = np.where(cv > 0, np.cumsum(typ * v, axis=1) / sur, typ)
    sigv = np.sqrt(np.maximum(np.where(cv > 0, np.cumsum(typ * typ * v, axis=1) / sur, 0) - vwap * vwap, 0))
    jvol = v.sum(axis=1)
    vb = np.full(S, np.nan)
    for d in range(5, S):
        vb[d] = np.median(jvol[d - 5:d]) / 50
    vp, fl = vpin_calc(achats, ventes, vb, 5)
    X = dict(o=o, h=h, l=l, c=c, v=v, delta=delta, cd=cd, dc=dc, s1=s1, u=s1 * math.sqrt(30), vwap=vwap, sigv=sigv,
             vp=vp, fl=fl, jouable=jouable, scale=np.ones(S) if scale is None else scale)
    # seuils glissants des 5 seances precedentes
    X["Qd"] = {W: rang_precedent(np.where(np.arange(D.NM) >= W, cd - np.roll(cd, W, axis=1), cd), jouable)
               for W in (5, 15, 30, 60)}
    X["Qvp"] = {}
    for j, n in enumerate((10, 25, 50)):
        snap = np.full((S, D.NM), np.nan)
        snap[:, CHECK15] = vp[j][:, CHECK15]
        Q = np.full((S, 101), np.nan)
        for d in range(5, S):
            x = vp[j][d - 5:d][:, CHECK15].ravel()
            if np.isfinite(x).all():
                Q[d] = np.percentile(x, np.arange(101))
        X["Qvp"][n] = Q
    # comparaisons aux 20 seances d'avant (G4, G5)
    X["ok20"] = np.arange(S) >= 20
    if bl is not None:
        X["bl"] = bl
        X["Qbl"] = {}
        for taille in (10, 25, 50):
            cb = np.cumsum(np.nan_to_num(bl[taille]), axis=1)
            cb[~np.isfinite(bl[taille]).all(axis=1)] = np.nan
            X["cbl" + str(taille)] = cb
            for W in (5, 15, 30):
                X["Qbl"][(taille, W)] = rang_precedent(np.where(np.arange(D.NM) >= W, cb - np.roll(cb, W, axis=1), cb),
                                                       jouable)
    return X


def tape(graine=None):
    """Vrai tape (G1 - G8) : seances, mesures (bruit par signe si graine)."""
    m, info, _ = D.seances()
    o, h, l, c = (m[k].astype(float) for k in ("o", "h", "l", "c"))
    a, v_ = m["achats"].astype(float), m["ventes"].astype(float)
    bl = gros_lots(info["jour"].pipe(pd.DatetimeIndex))
    if graine is not None:
        o, h, l, c, flip = retourner(o, h, l, c, graine)
        a, v_ = np.where(flip, v_, a), np.where(flip, a, v_)
        bl = {k: np.where(flip, -x, x) for k, x in bl.items()}
    Q = rang_precedent(np.where(a + v_ > 0, (a - v_) / np.maximum(a + v_, 1), 0.0), None)
    jouable = (~info["mince"].to_numpy()) & (~info["change"].to_numpy()) & np.isfinite(Q[:, 0])
    return mesures(o, h, l, c, a, v_, jouable, bl), info


# ---------------------------------------------------------------------------------------------- barres gratuites (G2b)
def barres_15_ans():
    """Barres d'une minute du NQ 2011 - 28 octobre 2026 (recherche + robot), seances completes de 390 minutes."""
    a = pd.read_csv(D.KB / "intraday" / "donnees" / "nasdaq100_1min.csv.gz")
    b = pd.read_csv(ICI.parent / "zone" / "robot" / "nq_1min.csv.gz")
    x = pd.concat([a, b[b["t"] > a["t"].max()]], ignore_index=True)
    x["jour"] = x["t"].str[:10]
    n = x.groupby("jour")["t"].transform("size")
    x = x[n == 390]
    jours = pd.DatetimeIndex(sorted(x["jour"].unique()))
    S = len(jours)
    arr = {k: x[k].to_numpy(float).reshape(S, 390) for k in ("o", "h", "l", "c", "v")}
    contrat = x.groupby("jour")["contrat"].agg(lambda s: s.mode().iloc[0]).to_numpy()
    change = np.r_[False, contrat[1:] != contrat[:-1]]
    return arr, jours, change


@njit(cache=True)
def _erf(x):
    out = np.empty_like(x)
    for i in range(x.shape[0]):
        for j in range(x.shape[1]):
            out[i, j] = math.erf(x[i, j])
    return out


def bvc(c, v):
    """Classification du volume par barres : achats = volume x Φ(Δc / σΔ), σΔ des 5 seances d'avant."""
    S = c.shape[0]
    dc = np.zeros_like(c)
    dc[:, 1:] = c[:, 1:] - c[:, :-1]
    sd = np.full(S, np.nan)
    for d in range(5, S):
        sd[d] = dc[d - 5:d, 1:].std(ddof=1)
    z = dc / np.where(np.isfinite(sd) & (sd > 0), sd, np.nan)[:, None]
    phi = 0.5 * (1 + _erf(np.nan_to_num(z) / math.sqrt(2)))
    phi[~np.isfinite(sd)] = 0.5
    achats = v * phi
    return achats, v - achats


def libre(graine=None):
    arr, jours, change = barres_15_ans()
    o, h, l, c, v = arr["o"], arr["h"], arr["l"], arr["c"], arr["v"]
    if graine is not None:
        o, h, l, c, _ = retourner(o, h, l, c, graine, par_seance=True)
    a, s = bvc(c, v)
    jouable = ~change & (np.arange(len(jours)) >= 6)
    X = mesures(o, h, l, c, a, s, jouable, scale=30000.0 / o[:, 0])
    return X, jours


# ---------------------------------------------------------------------------------------------- signaux
@njit(cache=True)
def _croise(cond, s_out, t_out, side_out, n, s, t, side, prev):
    if cond and not prev:
        s_out[n], t_out[n], side_out[n] = s, t, side
        return n + 1, True
    return n, cond


@njit(cache=True)
def sig_g1(c, dc, delta, cd, s1, jouable, L, W, typ, k, so, to, do_):
    S, M = c.shape
    n = 0
    for s in range(S):
        if not jouable[s]:
            continue
        p1 = np.zeros(M + 1)
        p2 = np.zeros(M + 1)
        for t in range(M):
            p1[t + 1] = p1[t] + (dc[s, t] * delta[s, t] if t >= 1 else 0.0)
            p2[t + 1] = p2[t] + (delta[s, t] * delta[s, t] if t >= 1 else 0.0)
        prev = False
        for t in range(max(30, L, W), 361):
            a1 = max(1, t - L + 1)
            num = p1[t + 1] - p1[a1]
            den = p2[t + 1] - p2[a1]
            if den <= 0 or not (s1[s, t] > 0):
                prev = False
                continue
            lam = num / den
            pi = lam * (cd[s, t] - cd[s, t - W])
            a = c[s, t] - c[s, t - W]
            z = (a - pi) / (s1[s, t] * math.sqrt(W)) if typ == 0 else pi / (s1[s, t] * math.sqrt(W))
            cond = abs(z) >= k
            side = 1 if z > 0 else -1
            if cond and not prev:
                so[n], to[n], do_[n] = s, t, side
                n += 1
            prev = cond
    return n


@njit(cache=True)
def sig_g2(vp, fl, Qvp, jouable, j, haut, q, checks, so, to, do_):
    S = vp.shape[1]
    n = 0
    for s in range(S):
        if not jouable[s] or not np.isfinite(Qvp[s, 0]):
            continue
        for t in checks:
            x = vp[j, s, t]
            if not np.isfinite(x):
                continue
            ok = x >= Qvp[s, q] if haut else x <= Qvp[s, q]
            if ok and fl[j, s, t] != 0:
                so[n], to[n], do_[n] = s, t, 1 if fl[j, s, t] > 0 else -1
                n += 1
    return n


@njit(cache=True)
def sig_g3(o, c, cd, Q, jouable, W, C, q, prix, so, to, do_):
    S = c.shape[0]
    n = 0
    for s in range(S):
        if not jouable[s] or not np.isfinite(Q[s, 0]):
            continue
        for t in range(30, 361, C):
            x = cd[s, t] - cd[s, t - W] if t >= W else cd[s, t]          # avant W minutes : depuis 9 h 30
            side = 1 if x >= Q[s, q] else (-1 if x <= Q[s, 100 - q] else 0)
            if side == 0:
                continue
            mv = c[s, t] - c[s, t - W] if t >= W else c[s, t] - o[s, 0]
            if prix == 1 and not (mv * side > 0):
                continue
            if prix == 2 and not (mv * side < 0):
                continue
            so[n], to[n], do_[n] = s, t, side
            n += 1
    return n


@njit(cache=True)
def sig_g45(o, c, cd, jouable, ok20, t, mesure, q, prix, so, to, do_):
    """G4 (mesure 0 : delta depuis l'ouverture) et G5 (0 jour, 1 : 60 dernieres minutes, 2 : premiere demi-heure),
    compares aux 20 seances d'avant ; q = 0 : signe seul."""
    S = c.shape[0]
    n = 0
    val = np.empty(S)
    mvt = np.empty(S)
    for s in range(S):
        if mesure == 0:
            val[s], mvt[s] = cd[s, t], c[s, t] - o[s, 0]
        elif mesure == 1:
            val[s], mvt[s] = cd[s, t] - cd[s, t - 60], c[s, t] - c[s, t - 60]
        else:
            val[s], mvt[s] = cd[s, 29], c[s, 29] - o[s, 0]
    for s in range(20, S):
        if not jouable[s] or not ok20[s]:
            continue
        x = val[s]
        if q == 0:
            side = 1 if x > 0 else (-1 if x < 0 else 0)
        else:
            hi = np.percentile(val[s - 20:s], q)
            lo = np.percentile(val[s - 20:s], 100 - q)
            side = 1 if x >= hi else (-1 if x <= lo else 0)
        if side == 0:
            continue
        if prix == 1 and not (mvt[s] * side > 0):
            continue
        if prix == 2 and not (mvt[s] * side < 0):
            continue
        so[n], to[n], do_[n] = s, t, side
        n += 1
    return n


@njit(cache=True)
def sig_g6(cb, Q, jouable, W, q, so, to, do_):
    S = cb.shape[0]
    n = 0
    for s in range(S):
        if not jouable[s] or not np.isfinite(Q[s, 0]) or not np.isfinite(cb[s, 0]):
            continue
        prev_h, prev_b = False, False
        for t in range(29, 361):
            x = cb[s, t] - cb[s, t - W] if t >= W else cb[s, t]
            ch, cbas = x >= Q[s, q] and x > 0, x <= Q[s, 100 - q] and x < 0
            if t >= 30:
                if ch and not prev_h:
                    so[n], to[n], do_[n] = s, t, 1
                    n += 1
                elif cbas and not prev_b:
                    so[n], to[n], do_[n] = s, t, -1
                    n += 1
            prev_h, prev_b = ch, cbas
    return n


@njit(cache=True)
def sig_g7(c, cd, vwap, sigv, jouable, k, W, mode, so, to, do_):
    S = c.shape[0]
    n = 0
    for s in range(S):
        if not jouable[s]:
            continue
        for t in range(30, 361):
            haut_t, haut_p = vwap[s, t] + k * sigv[s, t], vwap[s, t - 1] + k * sigv[s, t - 1]
            bas_t, bas_p = vwap[s, t] - k * sigv[s, t], vwap[s, t - 1] - k * sigv[s, t - 1]
            exc = 0
            if c[s, t] > haut_t and c[s, t - 1] <= haut_p:
                exc = 1
            elif c[s, t] < bas_t and c[s, t - 1] >= bas_p:
                exc = -1
            if exc == 0:
                continue
            f = cd[s, t] - cd[s, t - W]
            if mode == 0:                     # desaccord : flux contre le franchissement, retour
                if f * exc > 0:
                    continue
                side = -exc
            elif mode == 1:                   # accord : flux avec le franchissement, cassure
                if not (f * exc > 0):
                    continue
                side = exc
            else:
                side = -exc
            so[n], to[n], do_[n] = s, t, side
            n += 1
    return n


@njit(cache=True)
def sig_g8(h, l, c, cd, s1, u, vwap, Qabs, jouable, W, q, k, lieu, so, to, do_):
    S = c.shape[0]
    n = 0
    for s in range(S):
        if not jouable[s] or not np.isfinite(Qabs[s, 0]):
            continue
        hi, lo = -1e18, 1e18
        for j in range(30):
            hi, lo = max(hi, h[s, j]), min(lo, l[s, j])
        prev = False
        for t in range(30, 361):
            hi, lo = max(hi, h[s, t]), min(lo, l[s, t])
            f = cd[s, t] - cd[s, t - W]
            cond = abs(f) >= Qabs[s, q] and abs(c[s, t] - c[s, t - W]) <= k * s1[s, t] * math.sqrt(W) and f != 0
            if cond and lieu == 1:
                cond = min(hi - c[s, t], c[s, t] - lo) <= 0.5 * u[s, t]
            if cond and lieu == 2:
                cond = abs(c[s, t] - vwap[s, t]) <= 0.5 * u[s, t]
            if cond and not prev:
                so[n], to[n], do_[n] = s, t, -1 if f > 0 else 1
                n += 1
            prev = cond
    return n


@njit(cache=True)
def sig_g9(o, c, cd, v, jouable, ok20, mesure, q, prix, so, to, do_):
    """Desequilibre de la seance precedente (0) ou de sa derniere heure (1), compare aux 20 seances d'avant elle ;
    signal a la minute 0 de la seance (entree a l'ouverture de 9 h 31)."""
    S = c.shape[0]
    val = np.full(S, np.nan)
    mvt = np.zeros(S)
    for s in range(S):
        if mesure == 0:
            tot = 0.0
            for t in range(390):
                tot += v[s, t]
            val[s] = cd[s, 389] / tot if tot > 0 else 0.0
        else:
            tot = 0.0
            for t in range(330, 390):
                tot += v[s, t]
            val[s] = (cd[s, 389] - cd[s, 329]) / tot if tot > 0 else 0.0
        mvt[s] = c[s, 389] - o[s, 0]
    n = 0
    for s in range(21, S):
        if not jouable[s] or not ok20[s]:
            continue
        x = val[s - 1]
        if q == 0:
            side = 1 if x > 0 else (-1 if x < 0 else 0)
        else:
            hi = np.percentile(val[s - 21:s - 1], q)
            lo = np.percentile(val[s - 21:s - 1], 100 - q)
            side = 1 if x >= hi else (-1 if x <= lo else 0)
        if side == 0:
            continue
        if prix == 1 and not (mvt[s - 1] * side > 0):
            continue
        if prix == 2 and not (mvt[s - 1] * side < 0):
            continue
        so[n], to[n], do_[n] = s, 0, side
        n += 1
    return n


def signaux(X, fam, sg):
    S = X["c"].shape[0]
    taille = S * 400
    so, to, do_ = np.zeros(taille, np.int64), np.zeros(taille, np.int64), np.zeros(taille, np.int64)
    jou = X["jouable"]
    if fam == "G1":
        L, W, typ, k = sg
        n = sig_g1(X["c"], X["dc"], X["delta"], X["cd"], X["s1"], jou, L, W, 0 if typ == "residu" else 1, k, so, to, do_)
    elif fam in ("G2", "G2b"):
        nn, regime, q = sg
        j = (10, 25, 50).index(nn)
        n = sig_g2(X["vp"], X["fl"], X["Qvp"][nn], jou, j, regime == "haut", q, CHECK15, so, to, do_)
    elif fam == "G3":
        W, C, q, prix = sg
        n = sig_g3(X["o"], X["c"], X["cd"], X["Qd"][W], jou, W, C, q, ("libre", "accord", "desaccord").index(prix), so, to, do_)
    elif fam == "G4":
        t, q, prix = sg
        n = sig_g45(X["o"], X["c"], X["cd"], jou, X["ok20"], t, 0, q, ("libre", "accord", "desaccord").index(prix),
                    so, to, do_)
    elif fam == "G5":
        t, mes, q, prix = sg
        n = sig_g45(X["o"], X["c"], X["cd"], jou, X["ok20"], t, ("jour", "60 min", "ouverture").index(mes), q,
                    ("libre", "accord").index(prix), so, to, do_)
    elif fam == "G6":
        taille_l, W, q = sg
        n = sig_g6(X["cbl" + str(taille_l)], X["Qbl"][(taille_l, W)], jou, W, q, so, to, do_)
    elif fam == "G7":
        k, W, mode = sg
        n = sig_g7(X["c"], X["cd"], X["vwap"], X["sigv"], jou, k, W, ("desaccord", "accord", "libre").index(mode),
                   so, to, do_)
    elif fam == "G9":
        mes, q, prix = sg
        n = sig_g9(X["o"], X["c"], X["cd"], X["v"], jou, X["ok20"], ("seance", "derniere heure").index(mes), q,
                   ("libre", "accord", "desaccord").index(prix), so, to, do_)
    else:
        W, q, k, lieu = sg
        if "Qabs" not in X:
            X["Qabs"] = {w: rang_precedent(np.abs(np.where(np.arange(D.NM) >= w, X["cd"] - np.roll(X["cd"], w, axis=1),
                                                           X["cd"])), jou) for w in (5, 15, 30)}
        n = sig_g8(X["h"], X["l"], X["c"], X["cd"], X["s1"], X["u"], X["vwap"], X["Qabs"][W], jou, W, q, k,
                   ("partout", "extreme", "vwap").index(lieu), so, to, do_)
    return so, to, do_, n


# ---------------------------------------------------------------------------------------------- gestion
@njit(cache=True)
def suivre(o, h, l, c, s, e, side, ent, stop, obj, fin):
    for x in range(e, fin + 1):
        if side > 0:
            if stop > 0 and x > e and o[s, x] <= stop:
                return x, o[s, x] - 0.25
            if stop > 0 and l[s, x] <= stop:
                return x, stop - 0.25
            if obj > 0 and h[s, x] >= obj + 0.25:
                return x, obj
        else:
            if stop > 0 and x > e and o[s, x] >= stop:
                return x, o[s, x] + 0.25
            if stop > 0 and h[s, x] >= stop:
                return x, stop + 0.25
            if obj > 0 and l[s, x] <= obj - 0.25:
                return x, obj
    return fin, c[s, fin] - side * 0.25


@njit(cache=True)
def jouer(o, h, l, c, u, scale, so, to, do_, nsig, H, ks, ko, sens, P, N, trades):
    libre_s, libre_t = -1, 0
    nt = 0
    for i in range(nsig):
        s, t = so[i], to[i]
        if s == libre_s and t < libre_t:
            continue
        e = t + 1
        if e > 389 or ((ks > 0 or ko > 0) and not (u[s, t] > 0)):
            continue
        fin = 389 if H == 0 else min(e + H - 1, 389)
        x_garde = e
        for k in range(2):
            side = do_[i] * sens * (1 if k == 0 else -1)
            ent = o[s, e] + side * 0.25
            if ks > 0:
                d = max(0.25, ks * u[s, t])
                st = np.floor((ent - d) / 0.25) * 0.25 if side > 0 else np.ceil((ent + d) / 0.25) * 0.25
            else:
                st = -1.0
            if ko > 0:
                ob = ent + side * ko * u[s, t]
                ob = np.ceil(ob / 0.25) * 0.25 if side > 0 else np.floor(ob / 0.25) * 0.25
            else:
                ob = -1.0
            x, sor = suivre(o, h, l, c, s, e, side, ent, st, ob, fin)
            net = side * (sor - ent) * scale[s] - 1.0
            if k == 0:
                x_garde = x
                P[s] += net
                N[s] += 1
                if trades.shape[0] > 0:
                    trades[nt, 0], trades[nt, 1], trades[nt, 2] = s, t, net
            else:
                trades[nt, 3] = net
            if trades.shape[0] == 0:
                break
        nt += 1
        libre_s, libre_t = s, x_garde
    return nt


@njit(cache=True)
def gestion_toutes(o, h, l, c, u, scale, so, to, do_, n, G, P, N):
    vide = np.zeros((0, 4))
    for j in range(G.shape[0]):
        jouer(o, h, l, c, u, scale, so, to, do_, n, int(G[j, 0]), G[j, 1], G[j, 2], int(G[j, 3]), P[j], N[j], vide)


def calculer(X, configs):
    S = X["c"].shape[0]
    P = np.zeros((len(configs), S), np.float32)
    N = np.zeros((len(configs), S), np.int16)
    for (fam, i), lignes in configs.groupby(["famille", "i_signal"]).groups.items():
        sg = configs.loc[lignes[0], "signal"]
        so, to, do_, n = signaux(X, fam, sg)
        G = configs.loc[lignes, ["duree", "stop_u", "objectif_u", "sens"]].to_numpy(float)
        Pi, Ni = np.zeros((len(G), S)), np.zeros((len(G), S))
        gestion_toutes(X["o"], X["h"], X["l"], X["c"], X["u"], X["scale"], so, to, do_, n, G, Pi, Ni)
        P[lignes], N[lignes] = Pi, Ni
    return P, N


def trades_config(X, cfg):
    so, to, do_, n = signaux(X, cfg["famille"], cfg["signal"])
    S = X["c"].shape[0]
    tr = np.zeros((max(n, 1), 4))
    nt = jouer(X["o"], X["h"], X["l"], X["c"], X["u"], X["scale"], so, to, do_, n, int(cfg["duree"]), float(cfg["stop_u"]),
               float(cfg["objectif_u"]), int(cfg["sens"]), np.zeros(S), np.zeros(S), tr)
    return pd.DataFrame(tr[:nt], columns=["seance", "signal", "net", "net_inverse"]).astype({"seance": int, "signal": int})


def main():
    R.CALCUL.mkdir(parents=True, exist_ok=True)
    cf = table_configs()
    cf.to_pickle(R.CALCUL / "q_configs.pkl")
    cb = table_g2b()
    cb.to_pickle(R.CALCUL / "q_configs_g2b.pkl")
    for nom, graine in [("reel", None)] + [(f"bruit{g}", g) for g in GRAINES]:
        t0 = time.time()
        X, info = tape(graine)
        if graine is None:
            info.to_pickle(R.CALCUL / "q_info.pkl")
            np.save(R.CALCUL / "q_jouable.npy", X["jouable"])
            np.save(R.CALCUL / "q_gros.npy", np.isfinite(X["cbl10"][:, 0]))
        P, N = calculer(X, cf)
        np.savez_compressed(R.CALCUL / f"q_{nom}.npz", P=P, N=N)
        t1 = time.time()
        X, jours = libre(graine)
        if graine is None:
            pd.Series(jours).to_pickle(R.CALCUL / "q_jours_g2b.pkl")
            np.save(R.CALCUL / "q_jouable_g2b.npy", X["jouable"])
        P, N = calculer(X, cb)
        np.savez_compressed(R.CALCUL / f"q_g2b_{nom}.npz", P=P, N=N)
        print(f"{nom} : tape {len(cf)} configurations en {t1 - t0:.0f} s, G2b {len(cb)} en {time.time() - t1:.0f} s",
              flush=True)


if __name__ == "__main__":
    main()
