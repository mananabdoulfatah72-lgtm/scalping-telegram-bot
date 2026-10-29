#!/usr/bin/env python3
"""Partie 2 du systeme order flow (flux/README.md) : 89 100 reglages des trois familles, sur les vraies donnees et sur
4 jumeaux de bruit par signe. Calcule, pour chaque reglage, le gain net et le nombre de trades de chaque seance, et les
range hors du depot (FLUX_CALCUL, par defaut le dossier temporaire). La selection (selection.py) ne lit que A.

Lancer : KB=<copie de claude/keen-babbage-r686cl> python3 flux/reglages.py"""
import itertools
import os
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

import donnees as D

TICK, COM, GLISSE, R_MAX = 0.25, 0.5, 0.25, 0.0012
CALCUL = Path(os.getenv("FLUX_CALCUL", Path(tempfile.gettempdir()) / "flux_calcul"))
GRAINES = (11, 12, 13, 14)

# gestion commune : objectif (multiple de R, 0 = aucun), duree, stop minimum, derniere minute de signal, sens
GESTION = list(itertools.product((1.0, 1.5, 2.0, 3.0, 0.0), (10, 30, 60), (3.0, 6.0, 10.0), (330, 150), (1, -1)))
F1 = list(itertools.product((15, 30, 60), (1, 0), (3, 5, 10), (5, 10, 20, 30), (0.0, 1.0, 1.5), (1, 0)))
F2 = list(itertools.product(("veille", "heure", "les deux"), (0, 60, 75, 90), (2, 5, 10)))
F3 = list(itertools.product((0, 30, 60), (80, 90, 95), (0.5, 1.0, 2.0)))


def table_configs():
    lignes = []
    for fam, liste in (("F1", F1), ("F2", F2), ("F3", F3)):
        for i, sg in enumerate(liste):
            for j, g in enumerate(GESTION):
                lignes.append((fam, i, j, sg, *g))
    return pd.DataFrame(lignes, columns=["famille", "i_signal", "i_gestion", "signal", "objectif", "duree", "stop_min",
                                         "t_max", "sens"])


# ---------------------------------------------------------------------------------------------- donnees et bruit
def tableaux(m, info, graine=None):
    """Tableaux du calcul ; avec une graine, jumeau de bruit par signe (README, partie 2)."""
    S = len(info)
    o, h, l, c = (m[k].astype(np.float64).copy() for k in ("o", "h", "l", "c"))
    a, v_ = m["achats"].astype(np.float64).copy(), m["ventes"].astype(np.float64).copy()
    fb, fh = m["ventes_bas2"].copy(), m["achats_haut2"].copy()
    if graine is not None:
        rng = np.random.default_rng(graine)
        flip = rng.random((S, D.NM)) < 0.5
        flip[:, 0] = False
        F = S * D.NM
        of, hf, lf, cf, ff = (x.ravel() for x in (o, h, l, c, flip))
        cprev = np.concatenate([[of[0]], cf[:-1]])
        do, dh, dl, dc = of - cprev, hf - cprev, lf - cprev, cf - cprev
        do, dh, dl, dc = (np.where(ff, -do, do), np.where(ff, -dl, dh), np.where(ff, -dh, dl), np.where(ff, -dc, dc))
        c2 = of[0] + np.cumsum(dc)
        p2 = np.concatenate([[of[0]], c2[:-1]])
        o, h, l, c = ((p2 + x).reshape(S, D.NM) for x in (do, dh, dl, dc))
        c = c2.reshape(S, D.NM)
        a, v_ = np.where(flip, v_, a), np.where(flip, a, v_)
        fb, fh = np.where(flip, fh, fb), np.where(flip, fb, fh)
        assert F == o.size
    v = a + v_
    delta = a - v_
    imb = np.where(v > 0, delta / np.where(v > 0, v, 1), 0.0)
    typ = (h + l + c) / 3
    cv = np.cumsum(v, axis=1)
    vwap = np.where(cv > 0, np.cumsum(typ * v, axis=1) / np.where(cv > 0, cv, 1), typ)
    cd = np.cumsum(delta, axis=1)
    med30 = np.full((S, D.NM), np.inf)
    fen = np.lib.stride_tricks.sliding_window_view(v, 30, axis=1)          # fen[:, j] = v[:, j:j+30]
    med30[:, 30:] = np.median(fen[:, :D.NM - 30], axis=2)
    Qi, Qb, Qh = np.full((S, 101), np.nan), np.full((S, 101), np.nan), np.full((S, 101), np.nan)
    fp_ok = np.isfinite(fb).all(axis=1)
    for d in range(5, S):
        Qi[d] = np.percentile(imb[d - 5:d, 30:].ravel(), np.arange(101))
        if fp_ok[d - 5:d].all():
            Qb[d] = np.percentile(fb[d - 5:d, 30:].ravel(), np.arange(101))
            Qh[d] = np.percentile(fh[d - 5:d, 30:].ravel(), np.arange(101))
    jouable = (~info["mince"].to_numpy()) & (~info["change"].to_numpy()) & np.isfinite(Qi[:, 0])
    PDH = np.r_[np.nan, h[:-1].max(axis=1)]
    PDL = np.r_[np.nan, l[:-1].min(axis=1)]
    return dict(o=o, h=h, l=l, c=c, v=v, imb=imb, vwap=vwap, cd=cd, med30=med30, fb=np.nan_to_num(fb, nan=-1.0),
                fh=np.nan_to_num(fh, nan=-1.0), Qi=Qi, Qb=Qb, Qh=Qh, fp_ok=fp_ok & np.isfinite(Qb[:, 0]),
                jouable=jouable, PDH=PDH, PDL=PDL, IBH=h[:, :60].max(axis=1), IBL=l[:, :60].min(axis=1))


# ---------------------------------------------------------------------------------------------- signaux (numba)
@njit(cache=True)
def sig_f1(T, W, vw, k, qa, vm, cp, out_s, out_t, out_side, out_stop):
    o, h, l, c, v, imb, vwap, cd, med30, Qi, jouable = (T[0], T[1], T[2], T[3], T[4], T[5], T[6], T[7], T[8], T[9],
                                                         T[10])
    S = o.shape[0]
    n = 0
    for s in range(S):
        if jouable[s, 0] == 0:
            continue
        for t in range(30, 331):
            dw = cd[s, t] - (cd[s, t - W] if t - W >= 0 else 0.0)
            vol_ok = v[s, t] >= vm * med30[s, t]
            mil = (h[s, t] + l[s, t]) / 2
            lo, hi = 1e18, -1e18
            for j in range(t - k, t):
                lo = min(lo, l[s, j])
                hi = max(hi, h[s, j])
            if ((vw == 0 or c[s, t] > vwap[s, t]) and dw > 0 and l[s, t] <= lo and imb[s, t] <= Qi[s, qa] and vol_ok
                    and (cp == 0 or c[s, t] >= mil)):
                out_s[n], out_t[n], out_side[n], out_stop[n] = s, t, 1, l[s, t] - 0.25
                n += 1
            elif ((vw == 0 or c[s, t] < vwap[s, t]) and dw < 0 and h[s, t] >= hi and imb[s, t] >= Qi[s, 100 - qa]
                  and vol_ok and (cp == 0 or c[s, t] <= mil)):
                out_s[n], out_t[n], out_side[n], out_stop[n] = s, t, -1, h[s, t] + 0.25
                n += 1
    return n


@njit(cache=True)
def sig_f2(T, niveaux, qa, fw, PDH, PDL, IBH, IBL, out_s, out_t, out_side, out_stop):
    h, l, c, imb, Qi, jouable = T[1], T[2], T[3], T[5], T[9], T[10]
    S = h.shape[0]
    n = 0
    bt = np.zeros(4, np.int64)
    bside = np.zeros(4, np.int64)
    bstop = np.zeros(4)
    for s in range(S):
        if jouable[s, 0] == 0 or s == 0:
            continue
        nb = 0
        for lv in range(4):                       # 0 PDH, 1 PDL, 2 IBH, 3 IBL
            if (niveaux == 0 and lv >= 2) or (niveaux == 1 and lv < 2):
                continue
            L = PDH[s] if lv == 0 else PDL[s] if lv == 1 else IBH[s] if lv == 2 else IBL[s]
            haut = lv == 0 or lv == 2
            debut = 30 if lv < 2 else 60
            for b in range(debut, 331):
                if haut:
                    casse = h[s, b] >= L + 0.25 and c[s, b - 1] <= L
                else:
                    casse = l[s, b] <= L - 0.25 and c[s, b - 1] >= L
                if not casse:
                    continue
                if qa == 0 or (haut and imb[s, b] >= Qi[s, qa]) or ((not haut) and imb[s, b] <= Qi[s, 100 - qa]):
                    for f in range(b, min(b + fw, 330) + 1):
                        if (haut and c[s, f] <= L - 0.25) or ((not haut) and c[s, f] >= L + 0.25):
                            ext = -1e18 if haut else 1e18
                            for j in range(b, f + 1):
                                ext = max(ext, h[s, j]) if haut else min(ext, l[s, j])
                            bt[nb] = f
                            bside[nb] = -1 if haut else 1
                            bstop[nb] = ext + 0.25 if haut else ext - 0.25
                            nb += 1
                            break
                break
        # tri par minute, puis sens, puis stop, comme sorted() de la partie 1 (au plus 4 signaux)
        for i in range(nb):
            for j in range(nb - 1 - i):
                if (bt[j] > bt[j + 1] or (bt[j] == bt[j + 1] and (bside[j] > bside[j + 1] or (
                        bside[j] == bside[j + 1] and bstop[j] > bstop[j + 1])))):
                    bt[j], bt[j + 1] = bt[j + 1], bt[j]
                    bside[j], bside[j + 1] = bside[j + 1], bside[j]
                    bstop[j], bstop[j + 1] = bstop[j + 1], bstop[j]
        for i in range(nb):
            out_s[n], out_t[n], out_side[n], out_stop[n] = s, bt[i], bside[i], bstop[i]
            n += 1
    return n


@njit(cache=True)
def sig_f3(T, E, qf, rj, fb, fh, Qb, Qh, fp_ok, out_s, out_t, out_side, out_stop):
    h, l, c, jouable = T[1], T[2], T[3], T[10]
    S = h.shape[0]
    n = 0
    for s in range(S):
        if jouable[s, 0] == 0 or not fp_ok[s]:
            continue
        for t in range(30, 331):
            d0 = 0 if E == 0 else t - E
            lo, hi = 1e18, -1e18
            for j in range(d0, t):
                lo = min(lo, l[s, j])
                hi = max(hi, h[s, j])
            if l[s, t] < lo and fb[s, t] >= Qb[s, qf] and c[s, t] >= l[s, t] + rj:
                out_s[n], out_t[n], out_side[n], out_stop[n] = s, t, 1, l[s, t] - 0.25
                n += 1
            elif h[s, t] > hi and fh[s, t] >= Qh[s, qf] and c[s, t] <= h[s, t] - rj:
                out_s[n], out_t[n], out_side[n], out_stop[n] = s, t, -1, h[s, t] + 0.25
                n += 1
    return n


# ---------------------------------------------------------------------------------------------- gestion (numba)
@njit(cache=True)
def suivre(o, h, l, c, s, e, side, entree, stop, obj, H):
    fin = min(e + H - 1, 389)
    for x in range(e, fin + 1):
        if side > 0:
            if x > e and o[s, x] <= stop:
                return x, o[s, x] - 0.25
            if l[s, x] <= stop:
                return x, stop - 0.25
            if obj > 0 and h[s, x] >= obj + 0.25:
                return x, obj
        else:
            if x > e and o[s, x] >= stop:
                return x, o[s, x] + 0.25
            if h[s, x] >= stop:
                return x, stop + 0.25
            if obj > 0 and l[s, x] <= obj - 0.25:
                return x, obj
    return fin, c[s, fin] - side * 0.25


@njit(cache=True)
def geometrie(o_e, orig, stop_s, rmin):
    """Risque R du trade dans le sens du setup (regle de la partie 1) ; -1 si R depasse 0,12 % du prix."""
    ent = o_e + orig * 0.25
    if orig > 0:
        st = np.floor(min(stop_s, ent - rmin) / 0.25) * 0.25
    else:
        st = np.ceil(max(stop_s, ent + rmin) / 0.25) * 0.25
    R = abs(ent - st)
    if R > 0.0012 * ent:
        return -1.0
    return R


@njit(cache=True)
def jouer(o, h, l, c, sig_s, sig_t, sig_side, sig_stop, nsig, S, tm, H, rmin, tmax, sens, P, N, trades):
    """Une position a la fois. P, N : gain net et trades par seance. trades (si non vide) : seance, signal, net, net du
    sens inverse, une ligne par trade."""
    libre_s, libre_t = -1, 0
    nt = 0
    for i in range(nsig):
        s, t = sig_s[i], sig_t[i]
        if t > tmax:
            continue
        if s == libre_s and t < libre_t:
            continue
        e = t + 1
        orig = sig_side[i]
        R = geometrie(o[s, e], orig, sig_stop[i], rmin)
        if R < 0:
            continue
        net2 = np.zeros(2)
        x_garde = 0
        for k in range(2):
            side = orig * sens * (1 if k == 0 else -1)
            ent = o[s, e] + side * 0.25
            st = ent - side * R
            if tm > 0:
                ob = ent + side * tm * R
                ob = np.ceil(ob / 0.25) * 0.25 if side > 0 else np.floor(ob / 0.25) * 0.25
            else:
                ob = -1.0
            x, sor = suivre(o, h, l, c, s, e, side, ent, st, ob, H)
            net2[k] = side * (sor - ent) - 1.0
            if k == 0:
                x_garde = x
            if trades.shape[0] == 0:
                break
        P[s] += net2[0]
        N[s] += 1
        if trades.shape[0] > 0:
            trades[nt, 0], trades[nt, 1], trades[nt, 2], trades[nt, 3] = s, t, net2[0], net2[1]
        nt += 1
        libre_s, libre_t = s, x_garde
    return nt


@njit(cache=True)
def gestion_toutes(o, h, l, c, sig_s, sig_t, sig_side, sig_stop, nsig, S, G, P_out, N_out):
    vide = np.zeros((0, 4))
    for j in range(G.shape[0]):
        jouer(o, h, l, c, sig_s, sig_t, sig_side, sig_stop, nsig, S, G[j, 0], int(G[j, 1]), G[j, 2], int(G[j, 3]),
              int(G[j, 4]), P_out[j], N_out[j], vide)


# ---------------------------------------------------------------------------------------------- calcul
def pile(X):
    jou = np.repeat(X["jouable"][:, None].astype(np.float64), D.NM, axis=1)
    return (X["o"], X["h"], X["l"], X["c"], X["v"], X["imb"], X["vwap"], X["cd"], X["med30"], X["Qi"], jou)


def signaux(X, fam, sg):
    S = X["o"].shape[0]
    taille = S * 301
    out = (np.zeros(taille, np.int64), np.zeros(taille, np.int64), np.zeros(taille, np.int64), np.zeros(taille))
    T = pile(X)
    if fam == "F1":
        W, vw, k, qa, vm, cp = sg
        n = sig_f1(T, W, vw, k, qa, vm, cp, *out)
    elif fam == "F2":
        niv, qa, fw = sg
        n = sig_f2(T, {"veille": 0, "heure": 1, "les deux": 2}[niv], qa, fw, X["PDH"], X["PDL"], X["IBH"], X["IBL"], *out)
    else:
        E, qf, rj = sg
        n = sig_f3(T, E, qf, rj, X["fb"], X["fh"], X["Qb"], X["Qh"], X["fp_ok"], *out)
    return (*out, n)


def calculer(X, configs):
    S = X["o"].shape[0]
    G = np.array(GESTION, dtype=np.float64)
    P = np.zeros((len(configs), S), np.float32)
    N = np.zeros((len(configs), S), np.int16)
    for fam, liste in (("F1", F1), ("F2", F2), ("F3", F3)):
        for i, sg in enumerate(liste):
            ss, st, sd, sp, n = signaux(X, fam, sg)
            Pi = np.zeros((len(G), S))
            Ni = np.zeros((len(G), S))
            gestion_toutes(X["o"], X["h"], X["l"], X["c"], ss, st, sd, sp, n, S, G, Pi, Ni)
            lignes = configs.index[(configs["famille"] == fam) & (configs["i_signal"] == i)].to_numpy()
            P[lignes], N[lignes] = Pi, Ni
    return P, N


def trades_config(X, cfg):
    """Trades d'une configuration, avec le resultat du meme trade en sens inverse (placebo)."""
    ss, st, sd, sp, n = signaux(X, cfg["famille"], cfg["signal"])
    S = X["o"].shape[0]
    tr = np.zeros((S * 301, 4))
    nt = jouer(X["o"], X["h"], X["l"], X["c"], ss, st, sd, sp, n, S, float(cfg["objectif"]), int(cfg["duree"]),
               float(cfg["stop_min"]), int(cfg["t_max"]), int(cfg["sens"]), np.zeros(S), np.zeros(S), tr)
    return pd.DataFrame(tr[:nt], columns=["seance", "signal", "net", "net_inverse"]).astype({"seance": int, "signal": int})


def main():
    CALCUL.mkdir(parents=True, exist_ok=True)
    m, info, _ = D.seances()
    configs = table_configs()
    configs.to_pickle(CALCUL / "configs.pkl")
    info.to_pickle(CALCUL / "info.pkl")
    for nom, graine in [("reel", None)] + [(f"bruit{g}", g) for g in GRAINES]:
        t0 = time.time()
        X = tableaux(m, info, graine)
        P, N = calculer(X, configs)
        np.savez_compressed(CALCUL / f"{nom}.npz", P=P, N=N)
        if graine is None:
            np.save(CALCUL / "jouable.npy", X["jouable"])
            np.save(CALCUL / "fp_ok.npy", X["fp_ok"])
        print(f"{nom} : {len(configs)} configurations en {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
