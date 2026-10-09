#!/usr/bin/env python3
"""Deux comptes en meme temps, un Static (E4, challenge 2x) et un Topstep (zone + A3, challenge 2x, finance 2x), chacun
rachete des qu'il est perdu : gains nets mois par mois, 2023 - sept. 2026 (descriptif, demande de l'utilisateur du
9 octobre 2026). Les deux comptes jouent le meme tirage du filtre simule et partent le meme jour. Ecrit deux_comptes.txt.
`python3 deux_comptes.py jour` : methode corrigee (README.md), avec la retenue de vague5_jour.txt pour le Static (financee
2x) ; ecrit deux_comptes_jour.txt."""
import multiprocessing as mp
import sys

import numpy as np
import pandas as pd

import vague5 as W

STATIC = dict(compte="Static", bot="E4", ch=2, fi=1, re=0)
TOPSTEP = dict(compte="Topstep", bot="zone + A3", ch=2, fi=2, re=0)
DEPARTS = 20


def un_tirage(args):
    """Pour un tirage du filtre : flux mensuels (net, retraits) de chaque compte, pour chaque date de depart."""
    scen, i = args
    D = W.G["D4"]
    j = D["jours"]
    w0 = int(np.searchsorted(j, pd.Timestamp("2023-01-01")))
    w1 = len(j)
    mc = pd.PeriodIndex(j[w0:w1], freq="M")
    out = []
    for c in (STATIC, TOPSTEP):
        g = W.G["gardes"][scen][i]
        b = W.D4.base(D, g) if c["compte"] == "Topstep" else W.U.base(W.G["DS"], g)
        f = W.lien(c, b)
        par_dep = []
        for k in range(DEPARTS):
            fl, rc, _ = W.chaine(D, f, w0 + 5 * k, w1)
            net = pd.Series(fl[w0:w1]).groupby(mc).sum()
            ret = pd.Series(rc[w0:w1]).groupby(mc).sum()
            net[net.index < mc[5 * k]] = np.nan
            ret[ret.index < mc[5 * k]] = np.nan
            par_dep.append((net, ret))
        out.append(par_dep)
    return out


def main():
    global STATIC
    W.regler(sys.argv[1] if len(sys.argv) > 1 else "achat")
    if W.NIVEAU == "jour":
        STATIC = dict(compte="Static", bot="E4", ch=2, fi=2, re=0)
    W.G["D4"] = W.D4.charger()
    W.G["DS"] = W.DN.charger()
    rho = W.S.rho_2026()
    W.G["gardes"] = {"filtre aussi bon qu'en 2026 (simule)": W.S.gardes_simules(W.G["D4"], rho)[:W.TIRAGES],
                     "sans filtre": [None]}
    mode = ("chaque trade au niveau d'aujourd'hui de son jour d'entree, comptes gardes tant qu'ils vivent"
            if W.NIVEAU == "jour" else "niveau fixe a l'achat, compte rachete apres 24 mois")
    L = [f"Deux comptes en meme temps (descriptif, {mode}) : {W.nom(STATIC)} + {W.nom(TOPSTEP)}, chacun rachete des"
         f" qu'il est perdu ; gains nets par mois du calendrier (retraits - prix - activation), niveau d'aujourd'hui ; {DEPARTS}"
         f" dates de depart (une seance sur cinq a partir du 3 janvier 2023) x tirages du filtre simule (rho {rho:.2f})."
         f" Septembre 2026 s'arrete au 25.", ""]
    for scen in W.G["gardes"]:
        n = len(W.G["gardes"][scen])
        with mp.get_context("fork").Pool(4) as p:
            res = p.map(un_tirage, [(scen, i) for i in range(n)])
        NS, NT, RS, RT = [], [], [], []
        for st, tp in res:
            for (ns, rs), (nt, rt) in zip(st, tp):
                NS.append(ns)
                NT.append(nt)
                RS.append(rs)
                RT.append(rt)
        NS, NT, RS, RT = (pd.concat(x, axis=1) for x in (NS, NT, RS, RT))
        tot = NS + NT
        ok = tot.notna()
        moy = lambda x: x.mean(axis=1).mean()          # noqa: E731  (comme vague5 : moyenne des chemins, puis des mois)
        L += [f"=== {scen} ({tot.shape[1]} chemins)",
              f"moyenne par mois : Static {moy(NS):+,.0f} $ + Topstep {moy(NT):+,.0f} $ = {moy(tot):+,.0f} $ ; mois"
              f" median {tot.stack().median():+,.0f} $",
              f"mois a 500 $ ou plus : {(tot[ok] >= 500).stack().mean():.0%} ; mois avec un retrait : Static"
              f" {(RS > 0)[ok].stack().mean():.0%}, Topstep {(RT > 0)[ok].stack().mean():.0%}, au moins un des deux"
              f" {((RS > 0) | (RT > 0))[ok].stack().mean():.0%}, les deux le meme mois {((RS > 0) & (RT > 0))[ok].stack().mean():.0%}",
              "", "annee | Static par mois | Topstep par mois | les deux par mois | mois a 500 $ ou plus | mois sans aucun"
              " retrait | gain de l'annee : moyenne (1 chemin sur 10 sous / au-dessus)"]
        an = tot.index.year
        for y in sorted(set(an)):
            s = an == y
            ty = tot[s]
            anneeh = ty.sum(min_count=1)
            sans = ~((RS[s] > 0) | (RT[s] > 0))
            L.append(f"{y} | {moy(NS[s]):+,.0f} $ | {moy(NT[s]):+,.0f} $ | {moy(ty):+,.0f} $ |"
                     f" {(ty >= 500)[ty.notna()].stack().mean():.0%} | {sans[ty.notna()].stack().mean():.0%} |"
                     f" {anneeh.mean():+,.0f} $ ({anneeh.quantile(0.1):+,.0f} / {anneeh.quantile(0.9):+,.0f} $)"
                     f"{' (9 mois)' if y == 2026 else ''}")
        L += ["", "mois | les deux : moyenne | 1 chemin sur 4 sous / au-dessus | chemins avec un retrait Static / Topstep"]
        for m in tot.index:
            v = tot.loc[m].dropna()
            L.append(f"{m} | {v.mean():+,.0f} $ | {v.quantile(0.25):+,.0f} / {v.quantile(0.75):+,.0f} $ |"
                     f" {(RS.loc[m].dropna() > 0).mean():.0%} / {(RT.loc[m].dropna() > 0).mean():.0%}")
        # un chemin reel : premier tirage, depart le 3 janvier 2023
        L += ["", "Un chemin reel (premier tirage, depart le 3 janvier 2023) : mois | Static | Topstep | les deux"]
        cum = 0.0
        for m in tot.index:
            x = tot.iloc[:, 0].loc[m]
            cum += x
            L.append(f"{m} | {NS.iloc[:, 0].loc[m]:+,.0f} | {NT.iloc[:, 0].loc[m]:+,.0f} | {x:+,.0f} (cumul {cum:+,.0f})")
        L.append("")
        print("\n".join(L[-60:]), flush=True)
    (W.ICI / f"deux_comptes{W.SUFFIXE}.txt").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
