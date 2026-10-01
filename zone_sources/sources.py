#!/usr/bin/env python3
"""Nouvelles sources d'avantage pour la zone de bruit (README.md). Lancer depuis ce dossier : python3 sources.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

R = Path(__file__).resolve().parent.parent
for d in ("zone_failles", "tournoi", "tournoi4"):
    sys.path.insert(0, str(R / d))
import journal as Z  # noqa: E402
from explorer import charger, t_stat  # noqa: E402
import strategies4 as S4  # noqa: E402

ICI = Path(__file__).resolve().parent
N = 390
COUT, PT = 1.5, 2.0
PERIODES = {"2011-2016": (2011, 2016), "2017-2022": (2017, 2022), "2023-2026": (2023, 2026)}


@njit(cache=True)
def zone_masque(C, ouv, veille, vwap, sigma, ok, perm_a, perm_v, pas=30):
    """Zone corrigee V1 (k = 1, stop limite ou VWAP) ; une entree a l'achat (a la vente) n'est permise que si
    perm_a (perm_v) est vrai a ce controle. Les sorties ne changent pas."""
    nd = C.shape[0]
    brut = np.zeros(nd)
    allers = np.zeros(nd)
    for d in range(nd):
        if not ok[d] or np.isnan(veille[d]) or np.isnan(sigma[d, pas]):
            continue
        hr = max(ouv[d], veille[d])
        br = min(ouv[d], veille[d])
        pos = 0
        entree = 0.0
        tot = 0.0
        n = 0
        for m in range(pas, N, pas):
            p = C[d, m]
            ub = hr * (1 + sigma[d, m])
            lb = br * (1 - sigma[d, m])
            if pos > 0 and p <= max(ub, vwap[d, m]):
                tot += p - entree
                pos = 0
            elif pos < 0 and p >= min(lb, vwap[d, m]):
                tot += entree - p
                pos = 0
            if pos == 0:
                if p > ub and perm_a[d, m]:
                    pos, entree, n = 1, p, n + 1
                elif p < lb and perm_v[d, m]:
                    pos, entree, n = -1, p, n + 1
        if pos != 0:
            tot += pos * (C[d, N - 1] - entree)
        brut[d] = tot
        allers[d] = n
    return brut, allers


def glissant_complet(x, ok, n):
    """Moyenne des n dernieres seances completes avant chaque seance, colonne par colonne (x : seances x k)."""
    out = np.full(x.shape, np.nan)
    out[ok] = pd.DataFrame(x[ok]).rolling(n, min_periods=n).mean().shift(1).values
    return out


def permissions(J, O, H, L, C, P, X, niv, es):
    sigma, veille, vwap, ok = niv
    nd = len(J)
    vrai = np.ones((nd, N), bool)
    perms = {}
    # S1 : l'ES hors de sa propre zone, du meme cote, au meme controle
    Je, Oe, He, Le, Ce, Pe, Xe = es
    se, ve, _, oke = Z.niveaux_propres(Je, Oe, He, Le, Ce, Pe, Xe)
    i = pd.DatetimeIndex(Je).get_indexer(pd.DatetimeIndex(J))
    pa, pv = np.zeros((nd, N), bool), np.zeros((nd, N), bool)
    g = i >= 0
    hr_e, br_e = np.fmax(Oe[:, 0], ve), np.fmin(Oe[:, 0], ve)
    ub_e, lb_e = hr_e[:, None] * (1 + se), br_e[:, None] * (1 - se)
    with np.errstate(invalid="ignore"):
        pa[g] = (Ce > ub_e)[i[g]] & oke[i[g], None]
        pv[g] = (Ce < lb_e)[i[g]] & oke[i[g], None]
    perms["S1"] = (pa, pv)
    # S2 : volume des 30 minutes avant le controle au-dessus de sa moyenne a la meme heure (14 seances completes)
    V = X["V"]
    cum = np.concatenate([np.zeros((nd, 1)), np.cumsum(V, axis=1)], axis=1)
    v30 = np.full((nd, N), np.nan)
    for m in range(30, N, 30):
        v30[:, m] = cum[:, m + 1] - cum[:, m - 29]
    moy = glissant_complet(v30, ok, 14)
    with np.errstate(invalid="ignore"):
        fort = np.nan_to_num(v30 > moy, nan=0).astype(bool)
    perms["S2"] = (fort, fort)
    # S3 : tendance de fond (veille contre sa moyenne sur 50 seances completes)
    clot = np.full(nd, np.nan)
    clot[ok] = C[ok, N - 1]
    ma = np.full(nd, np.nan)
    ma[ok] = pd.Series(clot[ok]).rolling(50, min_periods=50).mean().shift(1).values
    with np.errstate(invalid="ignore"):
        hausse, baisse = veille > ma, veille < ma
    perms["S3"] = (np.repeat(hausse[:, None], N, axis=1), np.repeat(baisse[:, None], N, axis=1))
    # S5 : sortie aussi du range de la nuit
    onh, onl = S4.range_nuit("nasdaq100", J, X.get("contrat"))
    with np.errstate(invalid="ignore"):
        perms["S5"] = (C > onh[:, None], C < onl[:, None])
    return perms, vrai


def rebond(J, O, H, L, C, P, X, cout):
    """S4 : tournoi n°4, strategie 7 (achat de 9 h 30 a 16 h apres une seance dans les 10 % les plus basses)."""
    complete = S4.st.journees_completes(P)
    ok = complete & ~X["echeance"]
    prec = S4.K1.precedente(complete, X.get("contrat"))
    rv = S4.K1.de_la(C[:, N - 1] / O[:, 0] - 1, prec)
    f7 = np.nan_to_num(rv <= S4.quantile_valides(rv, 0.1), nan=0).astype(bool)
    rien = np.full(len(J), np.nan)
    base = S4.K1.entree_fixe(O, H, L, C, ok, cout, np.ones(len(J), np.int64), 0, rien, rien, N - 1)
    return np.where(f7, base, 0.0)


def main():
    J, O, H, L, C, P, X = charger("nasdaq100", fin=None)
    es = charger("sp500", fin=None)
    niv = Z.niveaux_propres(J, O, H, L, C, P, X)
    sigma, veille, vwap, ok = niv
    ok_j = ok & ~X["echeance"]
    an = pd.DatetimeIndex(J).year.values
    perms, vrai = permissions(J, O, H, L, C, P, X, niv, es)
    jouer = lambda pa, pv: zone_masque(C, O[:, 0], veille, vwap, sigma, ok, pa, pv)
    b1, a1 = jouer(vrai, vrai)
    bz, az = Z.zone(J, O, H, L, C, P, X)
    assert np.allclose(b1, bz) and np.array_equal(a1, az), "moteur masque different de V1"
    pts = {"V1": b1 - COUT * a1}
    for s in ("S1", "S2", "S3", "S5"):
        b, a = jouer(*perms[s])
        pts[s] = b - COUT * a
    pts["S4"] = pts["V1"] + rebond(J, O, H, L, C, P, X, COUT)
    r = {k: np.where(ok_j, v / O[:, 0], 0.0) for k, v in pts.items()}
    d = {k: np.where(ok_j, v * PT, 0.0) for k, v in pts.items()}
    t = lambda x, p: t_stat(x[ok_j & (an >= PERIODES[p][0]) & (an <= PERIODES[p][1])])
    sortie = []
    ecrire = lambda s="": (print(s, flush=True), sortie.append(s))
    ecrire("Zone corrigee V1 et nouvelles sources (NQ, 1 MNQ, frais reels). Controle : moteur sans filtre = V1 exactement.")
    noms = {"V1": "zone corrigee V1", "S1": "confirmation par l'ES", "S2": "confirmation par le volume", "S3": "tendance de fond",
            "S4": "+ rebond apres forte baisse", "S5": "sortie du range de la nuit"}
    for k in ("V1", "S1", "S2", "S3", "S4", "S5"):
        c = ok_j & (an >= 2023)
        ecrire(f"  {k} {noms[k]:28s} | " + " | ".join(f"{p} t {t(r[k], p):+.2f}" for p in PERIODES)
               + f" | 2023-2026 : {d[k][c].sum():+,.0f} $ ; trades/an {np.mean([(pts[k][ok_j & (an == y)] != 0).sum() for y in range(2023, 2027)]):.0f}")
    ecrire("\nTri (README.md) :")
    retenues = []
    for k in ("S1", "S2", "S3", "S4", "S5"):
        e1 = t(r[k], "2011-2016") > t(r["V1"], "2011-2016") and t(r[k], "2017-2022") > t(r["V1"], "2017-2022")
        c = ok_j & (an >= 2023)
        diff = t_stat((r[k] - r["V1"])[c])
        e2 = t(r[k], "2023-2026") > t(r["V1"], "2023-2026") and diff >= 2.33
        if e1 and e2:
            retenues.append(k)
        ecrire(f"  {k} : mieux que V1 sur 2011-2016 et 2017-2022 {'OUI' if e1 else 'non'} | 2023-2026 mieux, t de la difference"
               f" {diff:+.2f} (seuil 2,33) {'OUI' if e2 else 'non'} => {'RETENUE' if e1 and e2 else 'rejetee'}")
    ecrire(f"\nPistes retenues : {retenues or 'aucune'}")
    # par annee (information)
    for k in ("V1", "S1", "S2", "S3", "S4", "S5"):
        ecrire(f"  {k} par annee ($, 1 MNQ) : " + " ".join(f"{y}:{d[k][ok_j & (an == y)].sum():+,.0f}" for y in range(2017, 2027)))
    (ICI / "sources.txt").write_text("\n".join(sortie) + "\n")


if __name__ == "__main__":
    main()
