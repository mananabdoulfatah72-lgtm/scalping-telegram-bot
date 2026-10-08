#!/usr/bin/env python3
"""Gains par mois du systeme Static retenu (E0 P500, au niveau d'aujourd'hui), descriptif, demande de l'utilisateur du
8 octobre 2026 : « oublie les frais d'activation, combien par mois ». Trois lectures :
1. un Static achete : retraits moyens au mois 1, 2, ... 24 apres l'achat ;
2. un compte Pro en vie : retraits moyens par mois ;
3. un programme « un Static achete chaque mois » : retraits recus chaque mois du calendrier, une fois le programme
   lance depuis 24 mois (chaque compte est suivi 24 mois au plus, puis oublie : prudent).
Sans filtre (historique), et avec le filtre delta simule (aussi bon qu'en 2026 / inutile, 10 tirages). Les frais
d'activation sont ignores ; le prix du Static (30 $ par mois) est montre a part. Ecrit par_mois.txt."""
import numpy as np
import pandas as pd

import donnees as DN
import moteur_static as M
import outils as U
import static as S

H2 = S.H2
TIRAGES = 10


def achats_mensuels(D):
    """Premier depart possible (RSI(2) a plat) de chaque mois."""
    j = D["jours"]
    poss = U.departs(D, 1)
    vus, out = set(), []
    for d in poss:
        m = (j[d].year, j[d].month)
        if m not in vus and j[d] >= pd.Timestamp("2012-01-01"):
            vus.add(m)
            out.append(d)
    return out


def jouer(D, b, achats):
    """Pour chaque achat : resultat du moteur et retraits seance par seance (24 mois)."""
    R, P = [], []
    for d in achats:
        ret = np.zeros(H2)
        R.append(U.achat(D, b, d, "E0", plafond=500.0, h2=H2, retraits=ret))
        P.append(ret)
    return np.array(R), np.array(P)


def lectures(D, achats, R, P):
    j = D["jours"]
    nj = len(j)
    mois_cal = pd.PeriodIndex(j, freq="M")
    out = {}
    # 1. par achat : retraits au mois k apres l'achat (achats avec 24 mois de suivi)
    complets = [i for i, d in enumerate(achats) if d + H2 <= nj]
    par_mois = np.zeros((len(achats), 24))
    for i, d in enumerate(achats):
        m0 = mois_cal[d]
        for s in np.flatnonzero(P[i]):
            k = (mois_cal[d + s] - m0).n
            if k < 24:
                par_mois[i, k] += P[i][s]
    out["par_achat"] = par_mois
    out["complets"] = complets
    # 2. compte Pro en vie : retraits / mois de vie du compte Pro
    vie, recu = 0.0, 0.0
    for i, d in enumerate(achats):
        r = R[i]
        if r[M.ISSUE] != 1:
            continue
        debut = int(r[M.FIN_EVAL])
        fin = int(r[M.FIN_PRO]) if r[M.PRO_PERDU] == 1 else min(H2, nj - d)
        vie += max(0, fin - debut) / 21.0
        recu += P[i].sum()
    out["pro_par_mois"] = recu / vie if vie else 0.0
    out["pro_mois_de_vie"] = vie
    # 3. programme : un achat par mois ; revenu de chaque mois du calendrier
    tous = pd.period_range(mois_cal[achats[0]], mois_cal[nj - 1], freq="M")
    revenu = pd.Series(0.0, index=tous)
    pro_vivants = pd.Series(0, index=tous)
    for i, d in enumerate(achats):
        for s in np.flatnonzero(P[i]):
            revenu[mois_cal[d + s]] += P[i][s]
        r = R[i]
        if r[M.ISSUE] == 1:
            a = d + int(r[M.FIN_EVAL])
            b = d + (int(r[M.FIN_PRO]) if r[M.PRO_PERDU] == 1 else min(H2, nj - d)) - 1
            for m in pd.period_range(mois_cal[min(a, nj - 1)], mois_cal[min(b, nj - 1)], freq="M"):
                pro_vivants[m] += 1
    regime = tous[tous >= mois_cal[achats[0]] + 24]           # programme lance depuis 24 mois
    out["revenu"] = revenu[regime]
    out["pro_vivants"] = pro_vivants[regime]
    return out


def texte_programme(nom, x):
    rv, pv = x["revenu"], x["pro_vivants"]
    L = [f"--- {nom} : programme « 1 Static achete chaque mois » (30 $ par mois), revenu par mois du calendrier"
         f" ({rv.index[0]} - {rv.index[-1]}, {len(rv)} mois)",
         f"tous les mois : moyenne {rv.mean():,.0f} $ ; mediane {rv.median():,.0f} $ ; mois a 0 $ : {(rv == 0).mean():.0%} ;"
         f" meilleur {rv.max():,.0f} $ ; comptes Pro en vie : {pv.mean():.1f} en moyenne, {pv.max()} au plus",
         "annee | revenu moyen par mois | mediane | mois a 0 $ | meilleur mois | revenu de l'annee | moins 360 $ d'achats"]
    for a, g in rv.groupby(rv.index.year):
        L.append(f"{a} | {g.mean():,.0f} $ | {g.median():,.0f} $ | {(g == 0).mean():.0%} | {g.max():,.0f} $ |"
                 f" {g.sum():,.0f} $ ({len(g)} mois) | {g.sum() - 30 * len(g):+,.0f} $")
    return L


def main():
    D = DN.charger()
    j = D["jours"]
    achats = achats_mensuels(D)
    L = ["Gains par mois du systeme Static (bot + plafond du jour de 500 $ sur le compte Pro), au niveau d'aujourd'hui,"
         " frais d'activation ignores (descriptif, ecrit apres les resultats)", ""]
    scen = {"sans filtre (historique)": [U.base(D)]}
    rho = S.rho_2026()
    scen["filtre aussi bon qu'en 2026 (simule)"] = [U.base(D, g) for g in S.gardes_simules(D, rho)[:TIRAGES]]
    scen["filtre inutile (simule)"] = [U.base(D, g) for g in S.gardes_simules(D, 0.0)[:TIRAGES]]
    for nom, bases in scen.items():
        xs = [lectures(D, achats, *jouer(D, b, achats)) for b in bases]
        # 1. par achat
        pm = np.mean([x["par_achat"] for x in xs], axis=0)
        c = xs[0]["complets"]
        anc = [i for i in c if j[achats[i]] <= pd.Timestamp("2021-12-31")]
        rec = [i for i in c if j[achats[i]] >= pd.Timestamp("2023-01-01")]
        L.append(f"=== {nom}")
        for lab, idx in (("achats 2012-2021", anc), ("achats 2023 - sept. 2024", rec)):
            m = pm[idx].mean(axis=0)
            L.append(f"un Static achete ({lab}, {len(idx)} achats) : retraits moyens par mois apres l'achat :"
                     f" mois 1-3 {m[:3].mean():,.0f} $ ; 4-6 {m[3:6].mean():,.0f} $ ; 7-12 {m[6:12].mean():,.0f} $ ;"
                     f" 13-24 {m[12:24].mean():,.0f} $ ; total 12 mois {m[:12].sum():,.0f} $, 24 mois {m.sum():,.0f} $")
        L.append(f"un compte Pro en vie : {np.mean([x['pro_par_mois'] for x in xs]):,.0f} $ de retraits par mois en moyenne"
                 f" ({np.mean([x['pro_mois_de_vie'] for x in xs]):,.0f} mois de vie de comptes Pro observes)")
        if len(xs) == 1:
            L += texte_programme(nom, xs[0])
        else:
            rv = pd.concat([x["revenu"] for x in xs], axis=1).mean(axis=1)
            L += texte_programme(nom + f", moyenne de {len(xs)} tirages", {"revenu": rv, "pro_vivants": xs[0]["pro_vivants"]})
        L.append("")
        print("\n".join(L[-30:]), flush=True)
    (DN.ICI / "par_mois.txt").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
