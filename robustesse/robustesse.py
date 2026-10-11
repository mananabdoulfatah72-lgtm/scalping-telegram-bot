#!/usr/bin/env python3
"""Labo de robustesse du bot 3 en 1 (README.md). Ecrit robustesse.json (donnees de la page) et robustesse.txt.

Tout est en $ par seance, au prix d'aujourd'hui, sur les seances du 3 janvier 2012 au 25 septembre 2026 :
zone de bruit 1 MNQ (pas de zone les jours de la Fed), RSI(2) de nuit 1 MES. Le filtre delta est simule comme dans les
vagues 9 a 11 (10 tirages aussi bons qu'en 2026). Les variantes de parametres sont jouees sans filtre (il ne depend pas
des parametres de la zone) : c'est la meme grille pour toutes, donc la comparaison reste juste.

Parties :
1. courbe du bot (equite, baisses, statistiques, annees, glissant) et le virtuel en direct face au cone du backtest ;
2. permutation des parametres : 180 zones x 80 RSI(2) = 14 400 bots ;
3. matrice de suroptimisation : PBO par validation croisee combinatoire (Bailey, Borwein, Lopez de Prado, Zhu 2014),
   16 blocs, 12 870 decoupages ; Sharpe degonfle (Bailey et Lopez de Prado 2014) ;
4. hors echantillon : choix sur 2012-2021 puis 2023-2026, et walk-forward (choix glissant, 12 reglages) ;
5. tests de permutation : signes des trades de zone, nuits du RSI(2) tirees au hasard, ordre des jours ;
6. portefeuille : zone, RSI(2) de nuit et suivi de tendance multi-marches ; 7. correlations."""
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit, prange
from scipy.stats import norm, skew, kurtosis, spearmanr

ICI = Path(__file__).resolve().parent
R0 = ICI.parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(R0 / "vague9"))
sys.path.insert(0, str(R0 / "fonds"))
sys.path.insert(0, str(R0 / "tendance"))
import variantes as V  # noqa: E402
import socle9 as S9  # noqa: E402

DEBUT, FIN = "2012-01-03", "2026-09-25"
CHOIX_FIN, VERIF_DEBUT = "2021-12-31", "2023-01-01"
G_JOURS = (5, 7, 10, 14, 20, 30)
G_PAS = (15, 30, 60)
G_LARG = (0.6, 0.8, 1.0, 1.2, 1.5)
G_SORTIE = (True, False)
R_LONG = (100, 150, 200, 250)
R_SEUIL = (5.0, 10.0, 15.0, 20.0, 30.0)
R_SORTIE = (3, 5, 7, 10)
BASE_Z = (14, 30, 1.0, True)
BASE_R = (200, 10.0, 5)
NB_BLOCS = 16
AN = 252


# ----------------------------------------------------------------------------- outils
def stats(x, jours):
    x = np.asarray(x, float)
    c = np.cumsum(x)
    pic = np.maximum.accumulate(np.r_[0.0, c])[1:]
    dd = pic - c
    sous = dd > 1e-9
    duree, run = 0, 0
    for s in sous:
        run = run + 1 if s else 0
        duree = max(duree, run)
    mois = pd.Series(x, index=jours).groupby(jours.to_period("M")).sum()
    nz = x[x != 0]
    neg = np.minimum(x, 0)
    serie, pire_serie = 0, 0
    for v in mois.values:
        serie = serie + 1 if v < 0 else 0
        pire_serie = max(pire_serie, serie)
    sd = x.std()
    return {
        "total": float(c[-1]), "an": float(x.mean() * AN), "sharpe": float(x.mean() / sd * np.sqrt(AN)) if sd > 0 else 0.0,
        "sortino": float(x.mean() / np.sqrt((neg ** 2).mean()) * np.sqrt(AN)) if (neg ** 2).mean() > 0 else 0.0,
        "dd": float(dd.max()), "dd_duree": int(duree), "calmar": float(x.mean() * AN / dd.max()) if dd.max() > 0 else 0.0,
        "pf": float(x[x > 0].sum() / -x[x < 0].sum()) if (x < 0).any() else 0.0,
        "jours_gagnants": float((nz > 0).mean()) if len(nz) else 0.0, "jours_actifs": float(len(nz) / len(x)),
        "mois_positifs": float((mois > 0).mean()), "meilleur_jour": float(x.max()), "pire_jour": float(x.min()),
        "meilleur_mois": float(mois.max()), "pire_mois": float(mois.min()), "pire_serie_mois": int(pire_serie),
        "var95": float(np.percentile(nz, 5)) if len(nz) else 0.0,
        "cvar95": float(nz[nz <= np.percentile(nz, 5)].mean()) if len(nz) else 0.0,
        "asymetrie": float(skew(x)), "kurtosis": float(kurtosis(x)), "ulcer": float(np.sqrt((dd ** 2).mean())),
    }


def sh(x):
    s = x.std()
    return float(x.mean() / s * np.sqrt(AN)) if s > 0 else 0.0


@njit(parallel=True, cache=True)
def _cscv(Sb, Qb, nb, decoupes, base):
    ns, nc = Sb.shape
    nd = decoupes.shape[0]
    sr_is, sr_oos, omega, rang_base, sr_base_oos = np.zeros(nd), np.zeros(nd), np.zeros(nd), np.zeros(nd), np.zeros(nd)
    for k in prange(nd):
        dans = np.zeros(ns, np.bool_)
        for b in decoupes[k]:
            dans[b] = True
        nA, nB = 0.0, 0.0
        for b in range(ns):
            if dans[b]:
                nA += nb[b]
            else:
                nB += nb[b]
        a = np.empty(nc)
        o = np.empty(nc)
        meilleur, im = -1e18, 0
        for c in range(nc):
            sA, qA, sB, qB = 0.0, 0.0, 0.0, 0.0
            for b in range(ns):
                if dans[b]:
                    sA += Sb[b, c]
                    qA += Qb[b, c]
                else:
                    sB += Sb[b, c]
                    qB += Qb[b, c]
            mA, mB = sA / nA, sB / nB
            vA, vB = qA / nA - mA * mA, qB / nB - mB * mB
            a[c] = mA / np.sqrt(vA) if vA > 0 else 0.0
            o[c] = mB / np.sqrt(vB) if vB > 0 else 0.0
            if a[c] > meilleur:
                meilleur, im = a[c], c
        sous, egal, sous_b, egal_b = 0, 0, 0, 0
        for c in range(nc):
            if o[c] < o[im]:
                sous += 1
            elif o[c] == o[im]:
                egal += 1
            if o[c] < o[base]:
                sous_b += 1
            elif o[c] == o[base]:
                egal_b += 1
        sr_is[k], sr_oos[k] = a[im], o[im]
        omega[k] = (sous + 0.5 * egal) / nc
        rang_base[k] = (sous_b + 0.5 * egal_b) / nc
        sr_base_oos[k] = o[base]
    return sr_is, sr_oos, omega, rang_base, sr_base_oos


@njit(cache=True)
def _sr_decoupe(Sb, Qb, nb, dans):
    ns, nc = Sb.shape
    nA, nB = 0.0, 0.0
    for b in range(ns):
        if dans[b]:
            nA += nb[b]
        else:
            nB += nb[b]
    a, o = np.empty(nc), np.empty(nc)
    for c in range(nc):
        sA, qA, sB, qB = 0.0, 0.0, 0.0, 0.0
        for b in range(ns):
            if dans[b]:
                sA += Sb[b, c]
                qA += Qb[b, c]
            else:
                sB += Sb[b, c]
                qB += Qb[b, c]
        mA, mB = sA / nA, sB / nB
        vA, vB = qA / nA - mA * mA, qB / nB - mB * mB
        a[c] = mA / np.sqrt(vA) if vA > 0 else 0.0
        o[c] = mB / np.sqrt(vB) if vB > 0 else 0.0
    return a, o


def pbo(Sb, Qb, nb, base, rng, nom):
    decoupes = np.array(list(itertools.combinations(range(NB_BLOCS), NB_BLOCS // 2)), np.int64)
    sr_is, sr_oos, omega, rang_base, sr_base_oos = _cscv(Sb, Qb, nb, decoupes, base)
    om = np.clip(omega, 1e-4, 1 - 1e-4)
    lam = np.log(om / (1 - om))
    pente, ordo = np.polyfit(sr_is, sr_oos, 1)
    # matrice : decile du rang dans l'echantillon x decile du rang hors echantillon, sur 400 decoupages
    nc = Sb.shape[1]
    mat = np.zeros((10, 10))
    for k in rng.choice(len(decoupes), 400, replace=False):
        dans = np.zeros(NB_BLOCS, np.bool_)
        dans[decoupes[k]] = True
        a, o = _sr_decoupe(Sb, Qb, nb, dans)
        ra = np.argsort(np.argsort(a)) * 10 // nc
        ro = np.argsort(np.argsort(o)) * 10 // nc
        np.add.at(mat, (ra, ro), 1)
    mat /= mat.sum(axis=1, keepdims=True)
    ech = rng.choice(len(decoupes), min(1500, len(decoupes)), replace=False)
    print(f"  PBO {nom} : {np.mean(lam <= 0):.1%} ({len(decoupes)} decoupages, {nc} bots)", flush=True)
    return {"pbo": float(np.mean(lam <= 0)), "p_perte": float(np.mean(sr_oos <= 0)), "n": int(nc), "decoupes": int(len(decoupes)),
            "lam_hist": np.histogram(lam, bins=np.linspace(-8, 8, 33))[0].tolist(),
            "nuage": [[round(float(sr_is[k]) * np.sqrt(AN), 3), round(float(sr_oos[k]) * np.sqrt(AN), 3)] for k in ech],
            "pente": float(pente), "ordonnee": float(ordo * np.sqrt(AN)),
            "is_moy": float(sr_is.mean() * np.sqrt(AN)), "oos_moy": float(sr_oos.mean() * np.sqrt(AN)),
            "rang_oos_meilleur": float(omega.mean()), "rang_base_hist": np.histogram(rang_base, bins=np.linspace(0, 1, 21))[0].tolist(),
            "rang_base_moy": float(rang_base.mean()), "base_oos_neg": float(np.mean(sr_base_oos <= 0)), "matrice": np.round(mat, 4).tolist()}


def blocs_stats(X, bornes):
    S = np.stack([X[a:b].sum(axis=0) for a, b in bornes])
    Q = np.stack([(X[a:b] ** 2).sum(axis=0) for a, b in bornes])
    return S, Q


def dsr(x, V, N):
    """Sharpe degonfle : probabilite que le vrai Sharpe depasse le meilleur Sharpe attendu du hasard parmi N essais."""
    s = x.mean() / x.std()
    g3, g4 = skew(x), kurtosis(x) + 3
    T = len(x)
    gam = 0.5772156649
    if N <= 1:
        s0 = 0.0
    else:
        s0 = np.sqrt(V) * ((1 - gam) * norm.ppf(1 - 1 / N) + gam * norm.ppf(1 - 1 / (N * np.e)))
    return float(norm.cdf((s - s0) * np.sqrt(T - 1) / np.sqrt(1 - g3 * s + (g4 - 1) / 4 * s * s))), float(s0 * np.sqrt(AN))


def n_eff(X):
    c = np.corrcoef(X, rowvar=False)
    c = np.nan_to_num(c)
    ev = np.linalg.eigvalsh(c)
    ev = np.clip(ev, 0, None)
    return float(ev.sum() ** 2 / (ev ** 2).sum())


def vers_int(a):
    return [int(round(v)) for v in a]


# ----------------------------------------------------------------------------- calcul
def main():
    t0 = time.time()
    rng = np.random.default_rng(2026)
    D, T, a3, gardes = S9.charger()
    C9, _, _ = S9.conditions(D, T, gardes)
    pf = C9["pas un jour de la Fed"]
    M = V.minutes()
    kN, kE = S9.D4.facteurs_jour(D)
    jours_tous = pd.DatetimeIndex(D["jours"])
    nj = len(jours_tous)
    sel = np.flatnonzero((jours_tous >= pd.Timestamp(DEBUT)) & (jours_tous <= pd.Timestamp(FIN)))
    j = jours_tous[sel]
    import fomc
    fed = jours_tous.isin(fomc.annonces())
    i_choix = j <= pd.Timestamp(CHOIX_FIN)
    i_verif = j >= pd.Timestamp(VERIF_DEBUT)
    L = []

    # --- series du bot
    z_brut = np.bincount(T["d"][pf], weights=T["mnq"][pf], minlength=nj)
    tirs = [np.bincount(T["d"][g & pf], weights=T["mnq"][g & pf], minlength=nj) for g in gardes]
    sh_tirs = [sh((t + a3)[sel]) for t in tirs]
    k_med = int(np.argsort(sh_tirs)[len(tirs) // 2])               # tirage median : une vraie serie (la moyenne lisse)
    z_f = tirs[k_med]
    bot = z_f + a3
    bot_brut = z_brut + a3
    zv_base = V.zone(M, V.sigma(M, 14), kN)[0] * ~fed
    assert np.abs(zv_base - z_brut).max() < 1e-6
    series = {"bot": bot, "bot_brut": bot_brut, "zone_f": z_f, "zone_brut": z_brut, "nuit": a3}
    cum_tirs = np.array([np.cumsum((t + a3)[sel]) for t in tirs])
    eq = {"dates": [str(d.date()) for d in j], "series": {k: vers_int(np.cumsum(v[sel])) for k, v in series.items()},
          "bande": [vers_int(cum_tirs.min(axis=0)), vers_int(cum_tirs.max(axis=0))]}
    c = np.cumsum(bot[sel])
    eq["baisse"] = vers_int(np.maximum.accumulate(np.r_[0.0, c])[1:] - c)
    eq["stats"] = {k: {"tout": stats(v[sel], j), "choix": stats(v[sel][i_choix], j[i_choix]), "verif": stats(v[sel][i_verif], j[i_verif])}
                   for k, v in series.items()}
    st_t = [stats((t + a3)[sel], j) for t in tirs]
    eq["tirages"] = {"median": k_med, "an": [x["an"] for x in st_t], "sharpe": [x["sharpe"] for x in st_t], "dd": [x["dd"] for x in st_t]}
    annees = {}
    for a in range(2012, 2027):
        m = j.year == a
        annees[a] = {k: {"pnl": float(v[sel][m].sum()), "sharpe": sh(v[sel][m]), "dd": stats(v[sel][m], j[m])["dd"]}
                     for k, v in series.items()}
    eq["annees"] = annees
    bs = pd.Series(bot[sel], index=j)
    roul = bs.rolling(AN).sum()
    roul_sh = bs.rolling(AN).mean() / bs.rolling(AN).std() * np.sqrt(AN)
    hebdo = np.arange(AN, len(j), 5)
    eq["glissant"] = {"i": hebdo.tolist(), "pnl": vers_int(roul.values[hebdo]), "sharpe": [round(float(v), 3) for v in roul_sh.values[hebdo]]}
    L.append(f"Bot (filtre simule) : {eq['stats']['bot']['tout']['an']:,.0f} $/an, Sharpe {eq['stats']['bot']['tout']['sharpe']:.2f}, "
             f"baisse max {eq['stats']['bot']['tout']['dd']:,.0f} $ ; sans filtre {eq['stats']['bot_brut']['tout']['an']:,.0f} $/an, "
             f"Sharpe {eq['stats']['bot_brut']['tout']['sharpe']:.2f}")
    print(L[-1], f"({time.time() - t0:.0f} s)", flush=True)

    # --- le virtuel en direct face au cone (zone sans filtre + RSI(2) sur MNQ entre deux decisions, comme le robot)
    import robot_main as RB
    tab, _ = RB.rsi2(M["jours"], M["O"], M["H"], M["L"], M["C"], M["P"], M["ech"])
    rsi_mnq = np.zeros(nj)
    ix = np.searchsorted(jours_tous, tab.index)
    rsi_mnq[ix] = tab["gain_rsi2"].to_numpy() * kN[ix]
    z_robot = np.bincount(T["d"], weights=T["mnq"], minlength=nj)
    ref = (z_robot + rsi_mnq)[sel]
    nb_c, lon = 20000, 60
    deb = rng.integers(0, len(ref) - 5, (nb_c, lon // 5))
    chemins = np.concatenate([ref[deb[:, k:k + 1] + np.arange(5)] for k in range(lon // 5)], axis=1).cumsum(axis=1)
    import subprocess
    journal = pd.read_csv(pd.io.common.StringIO(subprocess.run(["git", "show", "origin/main:zone/robot/journal.csv"],
                                                                capture_output=True, text=True, cwd=R0).stdout))
    live = {"dates": journal["date"].tolist(), "gains": journal["gain"].astype(float).tolist(),
            "cone": {str(p): vers_int(np.percentile(chemins, p, axis=0)) for p in (5, 25, 50, 75, 95)}}

    # --- permutation des parametres
    sig = {lj: V.sigma(M, lj) for lj in G_JOURS}
    zp, zv = [], []
    for lj in G_JOURS:
        for pas in G_PAS:
            for la in G_LARG:
                for so in G_SORTIE:
                    zp.append((lj, pas, la, so))
                    zv.append(V.zone(M, sig[lj], kN, pas, la, so)[0] * ~fed)
    Z = np.array(zv).T[sel]
    rp, rv = [], []
    for ml in R_LONG:
        for se in R_SEUIL:
            for ms in R_SORTIE:
                rp.append((ml, se, ms))
                dec, vou = V.decisions_rsi(M, ml, se, ms)
                rv.append(V.nuit(D, dec, vou, kE)[0])
    R = np.array(rv).T[sel]
    iz, ir = zp.index(BASE_Z), rp.index(BASE_R)
    assert np.abs(R[:, ir] - a3[sel]).max() < 1e-6
    print(f"grilles : {Z.shape[1]} zones, {R.shape[1]} RSI(2) ({time.time() - t0:.0f} s)", flush=True)

    def mesures(X):
        return {"an": [round(float(v), 1) for v in X.mean(axis=0) * AN],
                "sharpe": [round(sh(X[:, k]), 3) for k in range(X.shape[1])],
                "dd": [round(stats(X[:, k], j)["dd"], 0) for k in range(X.shape[1])],
                "an_choix": [round(float(v), 1) for v in X[i_choix].mean(axis=0) * AN],
                "an_verif": [round(float(v), 1) for v in X[i_verif].mean(axis=0) * AN],
                "sh_choix": [round(sh(X[i_choix, k]), 3) for k in range(X.shape[1])],
                "sh_verif": [round(sh(X[i_verif, k]), 3) for k in range(X.shape[1])]}
    grille = {"zone": {"params": [[p[0], p[1], p[2], int(p[3])] for p in zp], "base": iz, **mesures(Z)},
              "rsi": {"params": [list(p) for p in rp], "base": ir, **mesures(R)},
              "axes": {"jours": G_JOURS, "pas": G_PAS, "largeur": G_LARG, "long": R_LONG, "seuil": R_SEUIL, "sortie": R_SORTIE}}
    # 14 400 bots : Sharpe et $/an de chaque combinaison (sans filtre)
    mz, mr = Z.mean(axis=0), R.mean(axis=0)
    vz, vr = Z.var(axis=0), R.var(axis=0)
    cov = (Z - mz).T @ (R - mr) / len(j)
    moy_c = (mz[:, None] + mr[None, :]) * AN
    sh_c = (mz[:, None] + mr[None, :]) / np.sqrt(vz[:, None] + vr[None, :] + 2 * cov) * np.sqrt(AN)
    base_sh = float(sh_c[iz, ir])
    grille["bots"] = {"sh_hist": np.histogram(sh_c.ravel(), bins=np.linspace(-0.6, 1.6, 45))[0].tolist(), "sh_bornes": [-0.6, 1.6],
                      "an_hist": np.histogram(moy_c.ravel(), bins=np.linspace(-4000, 10000, 57))[0].tolist(), "an_bornes": [-4000, 10000],
                      "base_sh": base_sh, "base_an": float(moy_c[iz, ir]), "rang_sh": float((sh_c < base_sh).mean()),
                      "rang_an": float((moy_c < moy_c[iz, ir]).mean()), "part_positifs": float((moy_c > 0).mean()),
                      "part_sh05": float((sh_c > 0.5).mean()), "med_sh": float(np.median(sh_c)), "max_sh": float(sh_c.max()),
                      "meilleur": [int(x) for x in np.unravel_index(np.argmax(sh_c), sh_c.shape)]}
    L.append(f"Permutation : 14 400 bots, {grille['bots']['part_positifs']:.0%} gagnants, Sharpe median {grille['bots']['med_sh']:.2f}, "
             f"bot = {base_sh:.2f} (rang {grille['bots']['rang_sh']:.0%})")
    print(L[-1], flush=True)

    # --- matrice de suroptimisation (CSCV) et Sharpe degonfle
    bornes = [(int(a[0]), int(a[-1]) + 1) for a in np.array_split(np.arange(len(j)), NB_BLOCS)]
    nb = np.array([b - a for a, b in bornes], float)
    Sz, Qz = blocs_stats(Z, bornes)
    Sr, Qr = blocs_stats(R, bornes)
    X = np.stack([Z[a:b].T @ R[a:b] for a, b in bornes])
    nzc, nrc = Z.shape[1], R.shape[1]
    Sb = (Sz[:, :, None] + Sr[:, None, :]).reshape(NB_BLOCS, -1)
    Qb = (Qz[:, :, None] + Qr[:, None, :] + 2 * X).reshape(NB_BLOCS, -1)
    sur = {"bots": pbo(Sb, Qb, nb, iz * nrc + ir, rng, "14 400 bots"), "zone": pbo(Sz, Qz, nb, iz, rng, "zones"),
           "rsi": pbo(Sr, Qr, nb, ir, rng, "RSI(2)")}
    L.append(f"PBO : bots {sur['bots']['pbo']:.0%}, zones {sur['zone']['pbo']:.0%}, RSI(2) {sur['rsi']['pbo']:.0%}")
    Vsr = float((sh_c.ravel() / np.sqrt(AN)).var())
    ech = rng.choice(nzc * nrc, 1500, replace=False)
    Xe = Z[:, ech // nrc] + R[:, ech % nrc]
    ne = {"bots": n_eff(Xe), "zone": n_eff(Z), "rsi": n_eff(R)}
    ev = np.sort(np.clip(np.linalg.eigvalsh(np.nan_to_num(np.corrcoef(Xe, rowvar=False))), 0, None))[::-1]
    ne["bots95"] = int(np.searchsorted(np.cumsum(ev) / ev.sum(), 0.95) + 1)
    Ns = np.unique(np.round(np.logspace(0, 6, 49)).astype(int))
    courbe = [[int(n), dsr(bot_brut[sel], Vsr, n)[0], dsr(bot[sel], Vsr, n)[0], dsr(bot_brut[sel], Vsr, n)[1]] for n in Ns]
    marques = {"1": 1, "grille": nzc * nrc, "n_eff": ne["bots95"], "recherche": 800000}
    sur["dsr"] = {"courbe": courbe, "V": Vsr, "n_eff": ne, "marques": {k: [float(v), dsr(bot_brut[sel], Vsr, v)[0], dsr(bot[sel], Vsr, v)[0]]
                                                                       for k, v in marques.items()},
                  "sr_brut": sh(bot_brut[sel]), "sr_filtre": sh(bot[sel]), "skew": float(skew(bot_brut[sel])),
                  "kurt": float(kurtosis(bot_brut[sel])), "T": int(len(j))}
    # matrice : Sharpe degonfle selon le nombre d'essais N et la dispersion des Sharpe entre essais (annuelle)
    disp = [0.1, 0.2, 0.3, 0.4, 0.5, 0.75, 1.0, 1.5]
    Nm = [1, 10, 100, 1000, 10000, 100000, 1000000]
    sur["dsr"]["matrice"] = {"dispersion": disp, "N": Nm,
                             "brut": [[round(dsr(bot_brut[sel], (dd_ / np.sqrt(AN)) ** 2, n)[0], 4) for n in Nm] for dd_ in disp],
                             "filtre": [[round(dsr(bot[sel], (dd_ / np.sqrt(AN)) ** 2, n)[0], 4) for n in Nm] for dd_ in disp],
                             "seuil": [[round(dsr(bot_brut[sel], (dd_ / np.sqrt(AN)) ** 2, n)[1], 2) for n in Nm] for dd_ in disp],
                             "grille": float(np.sqrt(Vsr) * np.sqrt(AN))}
    L.append(f"Sharpe degonfle (sans filtre) : N=1 {sur['dsr']['marques']['1'][1]:.1%}, N grille {sur['dsr']['marques']['grille'][1]:.1%}, "
             f"N effectif {ne['bots95']:.0f} -> {sur['dsr']['marques']['n_eff'][1]:.1%}, N=800 000 {sur['dsr']['marques']['recherche'][1]:.1%}")
    print(L[-1], f"({time.time() - t0:.0f} s)", flush=True)
    # correlation entre variantes (ordre de la grille)
    cz = np.round(np.nan_to_num(np.corrcoef(Z, rowvar=False)), 2)
    cr = np.round(np.nan_to_num(np.corrcoef(R, rowvar=False)), 2)
    sur["corr_variantes"] = {"zone": cz.tolist(), "rsi": cr.tolist(), "moy_zone": float(cz[np.triu_indices(nzc, 1)].mean()),
                             "moy_rsi": float(cr[np.triu_indices(nrc, 1)].mean())}

    # --- hors echantillon : choix 2012-2021 -> verification 2023-2026
    def sharpe_bots(a, b):
        Zw, Rw = Z[a:b], R[a:b]
        mz_, mr_ = Zw.mean(axis=0), Rw.mean(axis=0)
        cv_ = (Zw - mz_).T @ (Rw - mr_) / len(Zw)
        v_ = Zw.var(axis=0)[:, None] + Rw.var(axis=0)[None, :] + 2 * cv_
        return (mz_[:, None] + mr_[None, :]) / np.sqrt(np.maximum(v_, 1e-12)), (mz_[:, None] + mr_[None, :])
    a_c, b_c = 0, int(i_choix.sum())
    a_v = int(np.argmax(i_verif))
    s_is, m_is = sharpe_bots(a_c, b_c)
    s_oos, m_oos = sharpe_bots(a_v, len(j))
    best = np.unravel_index(np.argmax(s_is), s_is.shape)
    ech2 = rng.choice(nzc * nrc, 3000, replace=False)
    hors = {"meilleur": [int(best[0]), int(best[1])], "is_sh": float(s_is[best] * np.sqrt(AN)), "oos_sh": float(s_oos[best] * np.sqrt(AN)),
            "is_an": float(m_is[best] * AN), "oos_an": float(m_oos[best] * AN),
            "base_is_sh": float(s_is[iz, ir] * np.sqrt(AN)), "base_oos_sh": float(s_oos[iz, ir] * np.sqrt(AN)),
            "base_is_an": float(m_is[iz, ir] * AN), "base_oos_an": float(m_oos[iz, ir] * AN),
            "rang_oos_meilleur": float((s_oos < s_oos[best]).mean()), "rang_oos_base": float((s_oos < s_oos[iz, ir]).mean()),
            "corr_rang": float(spearmanr(s_is.ravel(), s_oos.ravel())[0]),
            "nuage": [[round(float(s_is.ravel()[k] * np.sqrt(AN)), 3), round(float(s_oos.ravel()[k] * np.sqrt(AN)), 3)] for k in ech2],
            "oos_med": float(np.median(s_oos) * np.sqrt(AN)), "top10_oos": float(np.median(s_oos.ravel()[np.argsort(s_is.ravel())[-144:]]) * np.sqrt(AN))}
    L.append(f"Hors echantillon : meilleur bot 2012-2021 Sharpe {hors['is_sh']:.2f} -> 2023-2026 {hors['oos_sh']:.2f} ; bot "
             f"{hors['base_is_sh']:.2f} -> {hors['base_oos_sh']:.2f} ; correlation des rangs {hors['corr_rang']:.2f}")
    print(L[-1], flush=True)

    # --- walk-forward : choix glissant sur W ans, joue la periode suivante
    debut_oos = pd.Timestamp("2015-01-01")
    wf = []
    for W in (1, 2, 3, 5):
        for pas_m in (3, 6, 12):
            debuts = pd.date_range(debut_oos, pd.Timestamp(FIN), freq=f"{pas_m}MS")
            oos, is_an, choix = np.zeros(0), [], []
            for d0 in debuts:
                d1 = d0 + pd.DateOffset(months=pas_m)
                a = int(np.searchsorted(j, d0 - pd.DateOffset(years=W)))
                b = int(np.searchsorted(j, d0))
                e = int(np.searchsorted(j, d1))
                if e <= b:
                    continue
                s_, m_ = sharpe_bots(a, b)
                k = np.unravel_index(np.argmax(s_), s_.shape)
                is_an.append(float(m_[k] * AN))
                oos = np.r_[oos, Z[b:e, k[0]] + R[b:e, k[1]]]
                choix.append([str(d0.date()), int(k[0]), int(k[1]), round(float(s_[k] * np.sqrt(AN)), 2),
                              round(float((Z[b:e, k[0]] + R[b:e, k[1]]).sum()), 0)])
            b0 = int(np.searchsorted(j, debut_oos))
            fixe = (Z[b0:, iz] + R[b0:, ir])
            moyen = Z[b0:].mean(axis=1) + R[b0:].mean(axis=1)
            st = stats(oos, j[b0:b0 + len(oos)])
            wf.append({"W": W, "pas": pas_m, "an": st["an"], "sharpe": st["sharpe"], "dd": st["dd"],
                       "efficacite": float(st["an"] / np.mean(is_an)) if np.mean(is_an) > 0 else 0.0,
                       "courbe": vers_int(np.cumsum(oos)[::5]), "choix": choix,
                       "base_an": float(fixe.mean() * AN), "base_sh": sh(fixe), "moyen_an": float(moyen.mean() * AN), "moyen_sh": sh(moyen),
                       "part_base": float(np.mean([c_[1] == iz and c_[2] == ir for c_ in choix]))})
    b0 = int(np.searchsorted(j, debut_oos))
    hors["wf"] = wf
    hors["wf_dates"] = [str(d.date()) for d in j[b0::5]]
    hors["wf_fixe"] = vers_int(np.cumsum(Z[b0:, iz] + R[b0:, ir])[::5])
    hors["wf_moyen"] = vers_int(np.cumsum(Z[b0:].mean(axis=1) + R[b0:].mean(axis=1))[::5])
    d3 = next(w for w in wf if w["W"] == 3 and w["pas"] == 12)
    L.append(f"Walk-forward (3 ans, 12 mois) : {d3['an']:,.0f} $/an, Sharpe {d3['sharpe']:.2f}, efficacite {d3['efficacite']:.0%} ; "
             f"bot fixe {d3['base_an']:,.0f} $/an ; bot moyen de la grille {d3['moyen_an']:,.0f} $/an")
    print(L[-1], f"({time.time() - t0:.0f} s)", flush=True)

    # --- tests de permutation
    dans = np.isin(T["d"], sel) & pf
    g = T["mnq"][dans] + V.FRAIS_ZONE                                  # gain brut de chaque trade
    reel_z = float(T["mnq"][dans].sum())
    nul_z = np.array([(np.where(rng.random(len(g)) < 0.5, g, -g) - V.FRAIS_ZONE).sum() for _ in range(20000)])
    EO0, ENO0, enn = D["EO"][:, 0], D["ENO"][:, 0], D["enn"]
    nuit_si = np.where(enn > 0, (EO0 - ENO0) * 5.0 * kE - V.FRAIS_NUIT, 0.0)[sel]
    possibles = np.flatnonzero(enn[sel] > 0)
    tenues = int((a3[sel] != 0).sum())
    reel_n = float(a3[sel].sum())
    nul_n = np.array([nuit_si[rng.choice(possibles, tenues, replace=False)].sum() for _ in range(20000)])
    bsel = bot[sel]
    dd_mel = []
    for _ in range(5000):
        cc = np.cumsum(rng.permutation(bsel))
        dd_mel.append((np.maximum.accumulate(np.r_[0.0, cc])[1:] - cc).max())
    dd_mel = np.array(dd_mel)
    dd_reel = eq["stats"]["bot"]["tout"]["dd"]

    def hist(x, reel, nb_=40):
        lo, hi = min(x.min(), reel), max(x.max(), reel)
        h, e = np.histogram(x, bins=np.linspace(lo, hi, nb_ + 1))
        return {"h": h.tolist(), "bornes": [float(lo), float(hi)]}
    perm = {"zone": {"reel": reel_z, "p": float((nul_z >= reel_z).mean()), "n": int(len(g)), "nul_moy": float(nul_z.mean()), **hist(nul_z, reel_z)},
            "nuit": {"reel": reel_n, "p": float((nul_n >= reel_n).mean()), "n": tenues, "possibles": int(len(possibles)),
                     "nul_moy": float(nul_n.mean()), **hist(nul_n, reel_n)},
            "ordre": {"reel": dd_reel, "rang": float((dd_mel < dd_reel).mean()), "med": float(np.median(dd_mel)),
                      "p95": float(np.percentile(dd_mel, 95)), **hist(dd_mel, dd_reel)}}
    L.append(f"Permutation : zone p = {perm['zone']['p']:.4f} ({reel_z:,.0f} $ contre {nul_z.mean():,.0f} $ au hasard) ; "
             f"nuits p = {perm['nuit']['p']:.4f} ({reel_n:,.0f} $ contre {nul_n.mean():,.0f} $) ; baisse max reelle {dd_reel:,.0f} $, "
             f"melanges : mediane {np.median(dd_mel):,.0f} $, 95 % {np.percentile(dd_mel, 95):,.0f} $")
    print(L[-1], f"({time.time() - t0:.0f} s)", flush=True)

    # --- portefeuille et correlations
    import systeme as SY
    close, adj = SY.charger()
    r = SY.rendements_futures(close, adj)
    net, _, _ = SY.backtest(r, cible=0.12)
    tend = net.reindex(jours_tous).fillna(0.0).to_numpy() * 50000.0
    cl = D["cl_nq"]
    ctr = D["contrat"]
    achat = np.zeros(nj)
    for d in range(1, nj):
        achat[d] = ((cl[d] - cl[d - 1]) if ctr[d] == ctr[d - 1] else (cl[d] - D["O"][d, 0])) * 2.0 * kN[d]
    vix = pd.read_csv(R0 / "evolution2" / "donnees" / "vix.csv")
    vix = pd.Series(vix["CLOSE"].astype(float).values, index=pd.to_datetime(vix["DATE"], format="mixed")).sort_index()
    dvix = vix.diff().reindex(jours_tous).fillna(0.0).to_numpy()
    noms = ["Bot (filtre simulé)", "Zone filtrée", "Zone sans filtre", "RSI(2) de nuit", "Tendance multi-marchés", "Achat permanent NQ", "VIX (variation)"]
    Ms = np.array([bot, z_f, z_brut, a3, tend, achat, dvix]).T[sel]
    jour_crise = (achat[sel] / (2.0 * kN[sel] * cl[sel]) < -0.02)
    mois_df = pd.DataFrame(Ms, index=j).groupby(j.to_period("M")).sum()
    zs, ns_ = pd.Series(z_f[sel], index=j), pd.Series(a3[sel], index=j)
    roul_zn = zs.rolling(AN).corr(ns_)
    roul_zb = zs.rolling(AN).corr(pd.Series(achat[sel], index=j))
    corr = {"noms": noms, "jour": np.round(np.corrcoef(Ms, rowvar=False), 3).tolist(),
            "mois": np.round(mois_df.corr().values, 3).tolist(),
            "spearman": np.round(spearmanr(Ms)[0], 3).tolist(),
            "crise": np.round(np.corrcoef(Ms[jour_crise], rowvar=False), 3).tolist(), "n_crise": int(jour_crise.sum()),
            "glissant": {"i": hebdo.tolist(), "zone_nuit": [round(float(v), 3) for v in np.nan_to_num(roul_zn.values[hebdo])],
                         "zone_nq": [round(float(v), 3) for v in np.nan_to_num(roul_zb.values[hebdo])]}}
    # portefeuilles : zone filtree (x 1 MNQ), RSI(2) de nuit (x 1 MES), tendance (x 50 000 $ a 12 %/an)
    zsl, nsl, tsl = z_f[sel], a3[sel], tend[sel]
    pts = []
    for wz in np.round(np.arange(0, 2.01, 0.1), 2):
        for wn in np.arange(0, 4.01, 0.5):
            for wt in np.arange(0, 1.01, 0.125):
                if wz == 0 and wn == 0 and wt == 0:
                    continue
                x = wz * zsl + wn * nsl + wt * tsl
                cc = np.cumsum(x)
                ddm = (np.maximum.accumulate(np.r_[0.0, cc])[1:] - cc).max()
                pts.append([float(wz), float(wn), float(wt), round(float(x.mean() * AN), 0), round(float(ddm), 0), round(sh(x), 3),
                            round(sh(x[i_choix]), 3), round(sh(x[i_verif]), 3)])
    P_ = np.array(pts)
    k_is = int(np.argmax(P_[:, 6]))
    cov3 = np.cov(np.array([zsl, nsl, tsl]))
    w_bot = np.array([1.0, 1.0, 0.0])
    contrib = w_bot * (cov3 @ w_bot) / (w_bot @ cov3 @ w_bot)
    sd3 = np.sqrt(np.diag(cov3))
    w_rp = (1 / sd3) / (1 / sd3).sum() * 3
    port = {"points": pts, "max_sh_choix": k_is, "contrib_bot": contrib[:2].tolist(), "ecart_types": sd3.tolist(), "parite": w_rp.tolist(),
            "stats": {"tendance": stats(tsl, j), "zone_f": stats(zsl, j), "nuit": stats(nsl, j)}}
    L.append(f"Portefeuille : meilleur Sharpe 2012-2021 = zone {P_[k_is,0]}, nuit {P_[k_is,1]}, tendance {P_[k_is,2]} "
             f"-> Sharpe 2023-2026 {P_[k_is,7]:.2f} ; bot (1, 1, 0) {sh(zsl + nsl):.2f} ; correlation zone/nuit {corr['jour'][1][3]:.2f}, "
             f"zone/tendance {corr['jour'][1][4]:.2f}")
    print(L[-1], f"({time.time() - t0:.0f} s)", flush=True)

    out = {"equite": eq, "direct": live, "grille": grille, "suroptimisation": sur, "hors": hors, "permutation": perm,
           "portefeuille": port, "correlations": corr,
           "periodes": {"debut": DEBUT, "fin": FIN, "choix_fin": CHOIX_FIN, "verif_debut": VERIF_DEBUT, "blocs": NB_BLOCS}}
    (ICI / "robustesse.json").write_text(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
    (ICI / "robustesse.txt").write_text("\n".join(L) + "\n")
    print(f"fin ({time.time() - t0:.0f} s) ; robustesse.json {(ICI / 'robustesse.json').stat().st_size / 1e6:.2f} Mo")


if __name__ == "__main__":
    main()
