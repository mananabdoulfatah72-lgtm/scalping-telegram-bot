#!/usr/bin/env python3
"""Zone + RSI(2) sur un meme compte : quelle taille ? (README.md). Grille de 128 gestions, choix sur 2011-2020,
controle sur 2023-2024. Lancer depuis ce dossier : ROBOT_ZONE=/chemin/zone/robot.py python3 taille2.py"""
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

ICI = Path(__file__).resolve().parent
R = ICI.parent
sys.path[:0] = [str(R / "tournoi8"), str(R / "zone_retrait")]
import combinaison8 as C  # noqa: E402
import retrait as RT  # noqa: E402

AN, PRIX = 252, 164.0
FS, MARGES = (0.15, 0.25, 0.35, 0.50), (0.0, 1000.0)


@njit(cache=True)
def carriere(g1, p1, s1, g2, p2, s2, deux, i0, n_jours, f_ch, f_av, f_ap, marge, jours_qualif, gain_qualif,
             capital=50000.0, objectif=4000.0, perte=2500.0, blocage=50100.0, seuil=52600.0, part=0.8,
             rmin=500.0, rmax=2000.0, regul=0.3, mini=1, maxi=50):
    """carriere() de zone_retrait/retrait.py avec une deuxieme source (si `deux`) : chacune f x coussin / racine(2).
    Renvoie (recu, challenges commences, comptes perdus, challenges reussis, retraits)."""
    finance = False
    solde = haut = capital
    meilleur = gain_p = 0.0
    qualif = 0
    recu, challenges, perdus, reussis, retraits = 0.0, 1, 0, 0, 0
    ks = np.sqrt(2.0) if deux else 1.0
    for k in range(i0, min(len(g1), i0 + n_jours)):
        if finance:
            plancher = blocage if haut >= seuil else haut - perte
            f = f_ap if haut >= seuil else f_av
        else:
            plancher = haut - perte
            f = f_ch
        coussin = solde - plancher
        n1 = mini
        if s1[k] > 0:
            n1 = int(min(max(np.floor(f * coussin / ks / s1[k]), mini), maxi))
        jour, creux = n1 * g1[k], n1 * p1[k]
        if deux:
            n2 = mini
            if s2[k] > 0:
                n2 = int(min(max(np.floor(f * coussin / ks / s2[k]), mini), maxi))
            jour += n2 * g2[k]
            creux += n2 * p2[k]
        if solde + creux <= plancher or solde + jour <= plancher:
            perdus += 1
            challenges += 1
            finance = False
            solde = haut = capital
            meilleur = gain_p = 0.0
            qualif = 0
            continue
        solde += jour
        haut = max(haut, solde)
        if not finance and solde - capital >= objectif:
            reussis += 1
            finance = True
            solde = haut = capital
            meilleur = gain_p = 0.0
            qualif = 0
        elif finance:
            meilleur = max(meilleur, jour)
            gain_p += jour
            if jour >= gain_qualif:
                qualif += 1
            r = min(rmax, solde - seuil - marge)
            if qualif >= jours_qualif and r >= rmin and gain_p > 0 and meilleur <= regul * gain_p:
                recu += part * r
                solde -= r
                retraits += 1
                meilleur = gain_p = 0.0
                qualif = 0
    return recu, challenges, perdus, reussis, retraits


def series():
    robot = C.charger_robot()
    z = robot.serie_du_bot(pd.read_csv(R / "intraday/donnees/nasdaq100_1min.csv.gz"))[0]
    z.index = pd.DatetimeIndex(z.index).normalize()
    r = C.serie_rsi2()
    j = z.index.intersection(r.index)
    z, r = z.loc[j], r.loc[j]
    g2, tenu = r["gain"].to_numpy(float), r["tenu"].to_numpy() == 1
    ref = r["gain"][(r.index <= "2022-12-31") & tenu].std()
    s2 = np.array([g2[max(0, k - AN):k][tenu[max(0, k - AN):k]].std() if tenu[max(0, k - AN):k].sum() >= 20 else ref
                   for k in range(len(r))])
    return robot, j, (z["gain"].to_numpy(float), z["pire"].to_numpy(float), z["risque1"].to_numpy(float),
                      g2, r["pire"].to_numpy(float), s2)


def main():
    robot, j, (g1, p1, s1, g2, p2, s2) = series()
    jq, gq = robot.JOURS_QUALIF, robot.GAIN_QUALIF
    sortie = []
    ecrire = lambda s="": (print(s, flush=True), sortie.append(s))
    # controle : sans deuxieme source, identique au simulateur de zone_retrait (lui-meme egal au robot)
    rng = np.random.default_rng(2)
    for _ in range(12):
        reg = (rng.choice(FS), rng.choice(FS), rng.choice(FS), rng.choice(MARGES))
        i0 = int(rng.integers(0, len(j) - 2 * AN))
        a = RT.carriere(g1, p1, s1, i0, 2 * AN, *reg, jq, gq)
        b = carriere(g1, p1, s1, g2, p2, s2, False, i0, 2 * AN, *reg, jq, gq)
        assert np.isclose(a[0], b[0]) and a[1:] == b[1:], (reg, i0, a, b)
    ecrire("Controle : sans RSI(2), ce simulateur = celui de zone_retrait/ (12 carrieres au hasard) : OK")
    ecrire(f"Zone de bruit + RSI(2) NQ, chacune f x coussin / racine(2), au moins 1 MNQ. Seances {j[0].date()} -> {j[-1].date()}")
    choix = [i for i in range(0, len(j), 5) if j[i].year <= 2020 and i + 2 * AN <= len(j) and j[min(i + 2 * AN, len(j) - 1)].year <= 2022]
    ctrl = [i for i in range(0, len(j), 5) if j[i] >= pd.Timestamp("2023-01-01") and i + 2 * AN <= len(j)]
    ctrl12 = [i for i in range(0, len(j), 5) if j[i] >= pd.Timestamp("2023-01-01") and i + AN <= len(j)]

    def mesure(idx, reg, n_jours, deux=True):
        x = np.array([carriere(g1, p1, s1, g2, p2, s2, deux, i, n_jours, *reg, jq, gq) for i in idx])
        ans = n_jours / AN
        return {"net_an": (x[:, 0] - PRIX * x[:, 1]).mean() / ans, "recu_an": x[:, 0].mean() / ans, "challenges_an": x[:, 1].mean() / ans,
                "perdus_an": x[:, 2].mean() / ans, "retraits_an": x[:, 4].mean() / ans, "rien": (x[:, 0] == 0).mean()}
    fmt = lambda r: (f"net {r['net_an']:+6,.0f} $/an | recu {r['recu_an']:6,.0f} $/an | challenges {r['challenges_an']:.2f}/an"
                     f" | comptes perdus {r['perdus_an']:.2f}/an | retraits {r['retraits_an']:.2f}/an | rien recu {r['rien']:4.0%}")
    grille = list(itertools.product(FS, FS, FS, MARGES))
    res = pd.DataFrame([{"f_ch": a, "f_av": b, "f_ap": c, "marge": m, **mesure(choix, (a, b, c, m), 2 * AN)} for a, b, c, m in grille])
    res = res.sort_values("net_an", ascending=False).reset_index(drop=True)
    actuel = (0.15, 0.15, 0.15, 0.0)
    act = res[(res.f_ch == 0.15) & (res.f_av == 0.15) & (res.f_ap == 0.15) & (res.marge == 0)].iloc[0]
    b = res.iloc[0]
    cle = (b.f_ch, b.f_av, b.f_ap, b.marge)
    ecrire(f"\n=== Choix : departs 2011-2020 ({len(choix)} departs, 24 mois)")
    ecrire(f"  actuelle (0,15 partout, marge 0), rang {int(act.name) + 1} sur 128 : {fmt(act)}")
    ecrire("  10 meilleures :")
    for i, r in res.head(10).iterrows():
        ecrire(f"   {i + 1:3d}. f challenge {r.f_ch:.2f} | avant blocage {r.f_av:.2f} | apres {r.f_ap:.2f} | marge {r.marge:4.0f} $ : {fmt(r)}")
    ecrire(f"  mediane des 128 : net {res.net_an.median():+,.0f} $/an")
    ecrire("  voisins de la gestion choisie (un reglage change) :")
    for nom in ("f_ch", "f_av", "f_ap", "marge"):
        vals = FS if nom != "marge" else MARGES
        morceaux = []
        for v in vals:
            q = dict(zip(("f_ch", "f_av", "f_ap", "marge"), cle))
            q[nom] = v
            rr = res[(res.f_ch == q["f_ch"]) & (res.f_av == q["f_av"]) & (res.f_ap == q["f_ap"]) & (res.marge == q["marge"])].iloc[0]
            morceaux.append(f"{v:g}:{rr.net_an:+,.0f}")
        ecrire(f"     {nom:6s} " + "  ".join(morceaux))
    ecrire(f"\n=== Controle : departs 2023-01 a {j[ctrl[-1]].date()} ({len(ctrl)} departs, 24 mois)")
    c_act, c_choix = mesure(ctrl, actuel, 2 * AN), mesure(ctrl, cle, 2 * AN)
    ecrire(f"  actuelle {actuel} : {fmt(c_act)}")
    ecrire(f"  choisie  {cle} : {fmt(c_choix)}")
    ecrire(f"  (zone seule, gestion actuelle : {fmt(mesure(ctrl, actuel, 2 * AN, deux=False))})")
    ecrire(f"\n=== Information : departs 2023-2025 suivis 12 mois ({len(ctrl12)} departs)")
    for nom, reg in (("actuelle", actuel), ("choisie", cle)):
        ecrire(f"  {nom:8s} : {fmt(mesure(ctrl12, reg, AN))}")
    adopte = c_choix["net_an"] > c_act["net_an"]
    ecrire(f"\nAdoption (README) : choisie {c_choix['net_an']:+,.0f} $/an contre {c_act['net_an']:+,.0f} $/an pour l'actuelle sur le controle"
           f" => {'ADOPTEE' if adopte else 'non adoptee : on garde 0,15 partout'}")
    res.to_csv(ICI / "grille2.csv", index=False, float_format="%.4g")
    (ICI / "taille2.txt").write_text("\n".join(sortie) + "\n")


if __name__ == "__main__":
    main()
