#!/usr/bin/env python3
"""Retirer plus du compte finance (README.md) : grille de 128 gestions, choix sur 2011-2020, controle sur 2023-2024.
Le simulateur rapide reprend exactement une_journee du robot (zone/robot.py sur main, chemin dans ROBOT_ZONE) ; le
controle d'egalite est fait au debut. Lancer depuis ce dossier : ROBOT_ZONE=/chemin/zone/robot.py python3 retrait.py"""
import importlib.util
import itertools
import os
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

ICI = Path(__file__).resolve().parent
R = ICI.parent
AN = 252
FS = (0.15, 0.25, 0.35, 0.50)
MARGES = (0.0, 1000.0)


@njit(cache=True)
def carriere(g, p, s1, i0, n_jours, f_ch, f_av, f_ap, marge, jours_qualif, gain_qualif,
             capital=50000.0, objectif=4000.0, perte=2500.0, blocage=50100.0, seuil=52600.0, part=0.8,
             rmin=500.0, rmax=2000.0, regul=0.3, mini=1, maxi=50):
    """Une carriere : challenge, compte finance, retraits ; un compte perdu relance un challenge.
    Renvoie (recu, challenges commences, comptes perdus, challenges reussis, retraits)."""
    finance = False
    solde = haut = capital
    meilleur = gain_p = 0.0
    qualif = 0
    recu, challenges, perdus, reussis, retraits = 0.0, 1, 0, 0, 0
    for k in range(i0, min(len(g), i0 + n_jours)):
        if finance:
            plancher = blocage if haut >= seuil else haut - perte
            f = f_ap if haut >= seuil else f_av
        else:
            plancher = haut - perte
            f = f_ch
        coussin = solde - plancher
        n = mini
        if s1[k] > 0:
            n = int(min(max(np.floor(f * coussin / s1[k]), mini), maxi))
        jour, creux = n * g[k], n * p[k]
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


def charger_robot():
    spec = importlib.util.spec_from_file_location("robot", os.environ["ROBOT_ZONE"])
    robot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(robot)
    return robot


def regler(robot, f_ch, f_av, f_ap, marge):
    robot.F_CHALLENGE, robot.F_AVANT, robot.F_APRES, robot.MARGE_RETRAIT = f_ch, f_av, f_ap, marge


def carriere_robot(robot, d, i0, n_jours):
    etat = {"debut": None, "derniere_date": None, "tentatives": [], "recu_total": 0.0, "gain_1_mnq": 0.0}
    robot.nouveau_challenge(etat, None)
    lignes = [robot.une_journee(etat, x, str(t.date())) for t, x in d.iloc[i0:i0 + n_jours].iterrows()]
    ev = pd.Series([l["evenement"] for l in lignes])
    return (etat["recu_total"], len(etat["tentatives"]), int(ev.str.startswith("COMPTE PERDU").sum()),
            int(ev.str.startswith("CHALLENGE REUSSI").sum()), int((pd.Series([l["retrait"] for l in lignes]) > 0).sum()))


def main():
    robot = charger_robot()
    d = robot.serie_du_bot(pd.read_csv(R / "intraday/donnees/nasdaq100_1min.csv.gz"))[0]
    g, p, s1 = (d[c].values.astype(float) for c in ("gain", "pire", "risque1"))
    sortie = []
    ecrire = lambda s="": (print(s, flush=True), sortie.append(s))
    # controle : le simulateur rapide = le robot
    rng = np.random.default_rng(7)
    for essai in range(12):
        reg = (rng.choice(FS), rng.choice(FS), rng.choice(FS), rng.choice(MARGES))
        i0 = int(rng.integers(0, len(d) - 2 * AN))
        regler(robot, *reg)
        a = carriere_robot(robot, d, i0, 2 * AN)
        b = carriere(g, p, s1, i0, 2 * AN, *reg, robot.JOURS_QUALIF, robot.GAIN_QUALIF)
        assert np.isclose(a[0], b[0]) and a[1:] == b[1:], (reg, i0, a, b)
    regler(robot, 0.15, 0.15, 0.15, 0.0)
    ecrire("Controle : simulateur rapide = une_journee du robot (12 carrieres tirees au hasard) : OK")
    ecrire(f"Zone V1 seule, 1 MNQ minimum, regles Phidias 50K Fundamental publiques (README.md), challenge 164 $. {d.index[0].date()} -> {d.index[-1].date()}")
    an = d.index
    choix_idx = [i for i in range(0, len(d), 5) if an[i].year <= 2020 and i + 2 * AN <= len(d) and an[min(i + 2 * AN, len(d) - 1)].year <= 2022]
    ctrl_idx = [i for i in range(0, len(d), 5) if an[i] >= pd.Timestamp("2023-01-01") and i + 2 * AN <= len(d)]
    ctrl12 = [i for i in range(0, len(d), 5) if an[i] >= pd.Timestamp("2023-01-01") and i + AN <= len(d)]

    def mesure(idx, reg, n_jours, jq=10, gq=150.0):
        r = np.array([carriere(g, p, s1, i, n_jours, *reg, jq, gq) for i in idx])
        ans = n_jours / AN
        net = (r[:, 0] - 164.0 * r[:, 1]) / ans
        return {"net_an": net.mean(), "recu_an": r[:, 0].mean() / ans, "challenges_an": r[:, 1].mean() / ans,
                "perdus_an": r[:, 2].mean() / ans, "reussis": r[:, 3].mean(), "retraits_an": r[:, 4].mean() / ans,
                "rien": (r[:, 0] == 0).mean(), "mediane_recu_an": np.median(r[:, 0]) / ans}

    grille = list(itertools.product(FS, FS, FS, MARGES))
    res = pd.DataFrame([{"f_ch": a, "f_av": b, "f_ap": c, "marge": m, **mesure(choix_idx, (a, b, c, m), 2 * AN)} for a, b, c, m in grille])
    res = res.sort_values("net_an", ascending=False).reset_index(drop=True)
    actuel = (0.15, 0.15, 0.15, 0.0)
    act = res[(res.f_ch == 0.15) & (res.f_av == 0.15) & (res.f_ap == 0.15) & (res.marge == 0)].iloc[0]
    best = res.iloc[0]
    cle = (best.f_ch, best.f_av, best.f_ap, best.marge)
    fmt = lambda r: (f"net {r['net_an']:+6,.0f} $/an | recu {r['recu_an']:6,.0f} $/an (mediane {r['mediane_recu_an']:5,.0f}) | challenges {r['challenges_an']:.2f}/an"
                     f" | comptes perdus {r['perdus_an']:.2f}/an | retraits {r['retraits_an']:.2f}/an | rien en 24 mois {r['rien']:4.0%}")
    ecrire(f"\n=== Choix : departs 2011-2020 ({len(choix_idx)} departs, 24 mois chacun)")
    ecrire(f"  actuelle (0,15 / 0,15 / 0,15 / 0 $), rang {int(act.name) + 1} sur 128 : {fmt(act)}")
    ecrire("  10 meilleures :")
    for i, r in res.head(10).iterrows():
        ecrire(f"   {i + 1:3d}. f challenge {r.f_ch:.2f} | avant blocage {r.f_av:.2f} | apres {r.f_ap:.2f} | marge {r.marge:4.0f} $ : {fmt(r)}")
    ecrire(f"  mediane des 128 : net {res.net_an.median():+,.0f} $/an")
    # voisins de la gestion choisie
    ecrire("  voisins de la gestion choisie (un reglage change) :")
    for j, nom in enumerate(("f_ch", "f_av", "f_ap", "marge")):
        vals = FS if nom != "marge" else MARGES
        ligne = []
        for v in vals:
            q = dict(zip(("f_ch", "f_av", "f_ap", "marge"), cle)); q[nom] = v
            rr = res[(res.f_ch == q["f_ch"]) & (res.f_av == q["f_av"]) & (res.f_ap == q["f_ap"]) & (res.marge == q["marge"])].iloc[0]
            ligne.append(f"{v:g}:{rr.net_an:+,.0f}")
        ecrire(f"     {nom:6s} " + "  ".join(ligne))
    ecrire(f"\n=== Controle : departs 2023-01 a {an[ctrl_idx[-1]].date()} ({len(ctrl_idx)} departs, 24 mois) ; une seule periode de marche")
    for nom, reg in (("actuelle", actuel), ("choisie", cle)):
        ecrire(f"  {nom:8s} {reg} : {fmt(mesure(ctrl_idx, reg, 2 * AN))}")
    ecrire(f"\n=== Controle sur 12 mois : departs 2023-2025 ({len(ctrl12)} departs)")
    for nom, reg in (("actuelle", actuel), ("choisie", cle)):
        m = mesure(ctrl12, reg, AN)
        ecrire(f"  {nom:8s} : " + fmt(m).replace("rien en 24 mois", "rien en 12 mois"))
    ecrire("\n=== Variante (information) : 10 jours de trading au lieu de 10 jours qualifiants (>= 150 $)")
    for nom, reg in (("actuelle", actuel), ("choisie", cle)):
        ecrire(f"  {nom:8s} 2011-2020 : {fmt(mesure(choix_idx, reg, 2 * AN, gq=-1e18))}")
        ecrire(f"  {nom:8s} 2023-2024 : {fmt(mesure(ctrl_idx, reg, 2 * AN, gq=-1e18))}")
    c_act, c_best = mesure(ctrl_idx, actuel, 2 * AN)["net_an"], mesure(ctrl_idx, cle, 2 * AN)["net_an"]
    ecrire(f"\nAdoption (README) : score de la choisie sur le controle {c_best:+,.0f} $/an contre {c_act:+,.0f} $/an pour l'actuelle"
           f" => {'ADOPTEE' if c_best > c_act else 'non adoptee (seules les regles corrigees sont portees)'}")
    res.to_csv(ICI / "grille.csv", index=False, float_format="%.4g")
    (ICI / "retrait.txt").write_text("\n".join(sortie) + "\n")


if __name__ == "__main__":
    main()
