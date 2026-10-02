#!/usr/bin/env python3
"""Tournoi 8, etape 3 (README.md) : la zone de bruit et le RSI(2) sur NQ ensemble.

- correlation quotidienne et Sharpe du melange au meme risque (ecarts-types mesures sur 2011-2022, appliques a 2023-2026) ;
- challenge Phidias 50K (regles et gestion du robot : simulateur de zone_retrait/, verifie egal a une_journee) avec
  la zone seule, puis avec les deux : chaque source recoit f x coussin / racine(2), au moins 1 micro ; le pire moment
  du jour est la somme des pires moments (prudent).

Le RSI(2) gagne ou perd de 15 h 50 la veille a 15 h 50 le jour meme : ce resultat est compte le jour meme. Son pire
moment : le plus bas entre l'ouverture de 9 h 30 et 15 h 49, ou le prix de 15 h 50 (la nuit n'est pas dans nos minutes,
le vrai pire moment peut etre un peu plus bas). Taille du RSI(2) : risque d'un MNQ = ecart-type de ses gains les jours
en position, sur les 252 seances d'avant (au moins 20 jours, sinon celui de 2011-2022).

Lancer depuis ce dossier : ROBOT_ZONE=/chemin/zone/robot.py python3 combinaison8.py"""
import importlib.util
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

import tournoi8 as T

ICI = Path(__file__).resolve().parent
R = ICI.parent
AN = 252
PRIX_CHALLENGE = 164.0


@njit(cache=True)
def carriere2(g1, p1, s1, g2, p2, s2, deux, i0, n_jours, f, jours_qualif, gain_qualif, capital=50000.0, objectif=4000.0,
              perte=2500.0, blocage=50100.0, seuil=52600.0, part=0.8, rmin=500.0, rmax=2000.0, regul=0.3, mini=1, maxi=50):
    """Comme carriere() de zone_retrait/retrait.py (meme gestion, f identique partout), avec une deuxieme source si `deux`.
    Renvoie (recu, challenges commences, comptes perdus, challenges reussis, retraits)."""
    finance = False
    solde = haut = capital
    meilleur = gain_p = 0.0
    qualif = 0
    recu, challenges, perdus, reussis, retraits = 0.0, 1, 0, 0, 0
    k_src = np.sqrt(2.0) if deux else 1.0
    for k in range(i0, min(len(g1), i0 + n_jours)):
        plancher = (blocage if haut >= seuil else haut - perte) if finance else haut - perte
        coussin = solde - plancher
        n1 = mini
        if s1[k] > 0:
            n1 = int(min(max(np.floor(f * coussin / k_src / s1[k]), mini), maxi))
        jour, creux = n1 * g1[k], n1 * p1[k]
        if deux:
            n2 = mini
            if s2[k] > 0:
                n2 = int(min(max(np.floor(f * coussin / k_src / s2[k]), mini), maxi))
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
            r = min(rmax, solde - seuil)
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


def serie_rsi2():
    """$ pour 1 MNQ chaque seance (2011 - septembre 2026), pire moment, position tenue a l'arrivee du jour."""
    s = T.charger("NQ", jusqu_au="2026-12-31")
    pos = T.positions(s, 0)
    rend, dol, *_ = T.journal(s, pos)
    avant = np.r_[0, pos[:-1]]
    P, L = s["P"].to_numpy(), s["L"].to_numpy()
    pt = s.attrs["pt"]
    pire = np.where(avant == 1, (np.minimum(L, P) - np.r_[P[0], P[:-1]]) * pt - s.attrs["cote"] * pt * np.abs(pos - avant), 0.0)
    pire = np.minimum(pire, np.minimum(dol, 0.0))
    return pd.DataFrame({"gain": dol, "pire": pire, "tenu": avant}, index=pd.DatetimeIndex(s["date"]).normalize())


def main():
    robot = charger_robot()
    z = robot.serie_du_bot(pd.read_csv(R / "intraday/donnees/nasdaq100_1min.csv.gz"))[0]
    z.index = pd.DatetimeIndex(z.index).normalize()
    r = serie_rsi2()
    jours = z.index.intersection(r.index)
    z, r = z.loc[jours], r.loc[jours]
    g1, p1, s1 = (z[c].to_numpy(float) for c in ("gain", "pire", "risque1"))
    g2, p2 = r["gain"].to_numpy(float), r["pire"].to_numpy(float)
    # risque d'un MNQ pour le RSI(2) : ecart-type des jours en position sur les 252 seances d'avant
    tenu = r["tenu"].to_numpy() == 1
    ref = r["gain"][(r.index <= "2022-12-31") & tenu].std()
    s2 = np.full(len(r), ref)
    for k in range(len(r)):
        x = g2[max(0, k - 252):k][tenu[max(0, k - 252):k]]
        if len(x) >= 20:
            s2[k] = x.std()
    lignes = [f"Zone de bruit (robot, 1 MNQ) et RSI(2) NQ (1 MNQ) : {len(jours)} seances communes, {jours[0].date()} -> {jours[-1].date()}", ""]
    for nom, (a, b) in {"2011-2022": ("2011-01-01", "2022-12-31"), "2023-2026 (coffre)": ("2023-01-01", "2026-12-31")}.items():
        k = (jours >= a) & (jours <= b)
        c = np.corrcoef(g1[k], g2[k])[0, 1]
        lignes.append(f"Correlation quotidienne {nom} : {c:+.2f}")
    k0, k1 = jours <= "2022-12-31", jours >= "2023-01-01"
    e1, e2 = g1[k0].std(), g2[k0].std()
    sh = lambda x: x.mean() / x.std() * np.sqrt(AN)
    melange = g1 / e1 + g2 / e2
    lignes += ["", "Sharpe 2023-2026 (ecarts-types de 2011-2022 pour le meme risque) :",
               f"  zone seule {sh(g1[k1]):.2f} | RSI(2) seul {sh(g2[k1]):.2f} | melange au meme risque {sh(melange[k1]):.2f}",
               f"  (pour comparaison, 2011-2022 : zone {sh(g1[k0]):.2f} | RSI(2) {sh(g2[k0]):.2f} | melange {sh(melange[k0]):.2f})"]
    # challenge : departs tous les 5 jours, 2023-2024 sur 24 mois et 2023-2025 sur 12 mois
    f = robot.F_CHALLENGE
    jq, gq = robot.JOURS_QUALIF, robot.GAIN_QUALIF

    def mesure(idx, deux, n_jours):
        res = np.array([carriere2(g1, p1, s1, g2, p2, s2, deux, i, n_jours, f, jq, gq) for i in idx])
        ans = n_jours / AN
        net = (res[:, 0] - PRIX_CHALLENGE * res[:, 1]) / ans
        return (f"net {net.mean():+7,.0f} $/an | recu {res[:, 0].mean() / ans:6,.0f} $/an | challenges {res[:, 1].mean() / ans:.2f}/an"
                f" | reussis {res[:, 3].mean():.2f} | retraits {res[:, 4].mean() / ans:.2f}/an | rien recu {(res[:, 0] == 0).mean():4.0%}")
    # controle d'egalite avec le simulateur de zone_retrait (zone seule)
    sys.path.insert(0, str(R / "zone_retrait"))
    import retrait as RT
    for i0 in (0, 500, 1500, len(jours) - 2 * AN):
        a = RT.carriere(g1, p1, s1, i0, 2 * AN, f, f, f, 0.0, jq, gq)
        b = carriere2(g1, p1, s1, g2, p2, s2, False, i0, 2 * AN, f, jq, gq)
        assert np.isclose(a[0], b[0]) and a[1:] == b[1:], (i0, a, b)
    lignes += ["", "Controle : zone seule = simulateur de zone_retrait/ (lui-meme verifie egal au robot) : OK", ""]
    for titre, debut, fin, n_j in (("departs 2023-2024, 24 mois", "2023-01-01", None, 2 * AN),
                                   ("departs 2023-2025, 12 mois", "2023-01-01", None, AN),
                                   ("information, en echantillon : departs 2011-2020, 24 mois", "2011-01-01", "2020-12-31", 2 * AN)):
        idx = [i for i in range(0, len(jours), 5) if jours[i] >= pd.Timestamp(debut) and i + n_j <= len(jours)
               and (fin is None or jours[i] <= pd.Timestamp(fin))]
        lignes += [f"Challenge Phidias 50K, {titre} ({len(idx)} departs) :",
                   f"  zone seule      : {mesure(idx, False, n_j)}", f"  zone + RSI(2)   : {mesure(idx, True, n_j)}", ""]
    (ICI / "combinaison8.txt").write_text("\n".join(lignes) + "\n")
    print("\n".join(lignes))


if __name__ == "__main__":
    main()
