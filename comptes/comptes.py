#!/usr/bin/env python3
"""Plusieurs comptes Phidias, et frein contre les comptes perdus (README.md).
Lancer depuis ce dossier : ROBOT_ZONE=/chemin/zone/robot.py python3 comptes.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
R = ICI.parent
sys.path[:0] = [str(R / "zone_deux")]
import taille2 as T2  # noqa: E402

AN, PRIX, ECART = 252, 164.0, 63
REGLES = [None, (750.0, "rsi2"), (750.0, "zone"), (1250.0, "rsi2"), (1250.0, "zone")]


def parcours(S, i0, n_jours, regle=None, jq=10, gq=150.0, f=0.15, capital=50000.0, objectif=4000.0, perte=2500.0,
             blocage=50100.0, seuil=52600.0, part=0.8, rmin=500.0, rmax=2000.0, regul=0.3):
    """Un compte (relance apres chaque perte) de la seance i0 pendant n_jours. Meme gestion que carriere() de
    zone_deux/taille2.py (f identique partout, marge 0) ; `regle` = (T, source) : sous un coussin T, une seule source a
    1 MNQ. Renvoie recu, challenges, perdus, finance (par seance), premier retrait (indice de seance ou None)."""
    g1, p1, s1, g2, p2, s2 = S
    finance = False
    solde = haut = capital
    meilleur = gain_p = 0.0
    qualif = 0
    recu, challenges, perdus = 0.0, 1, 0
    en_finance = np.zeros(n_jours, bool)
    premier = None
    ks = np.sqrt(2.0)
    for t, k in enumerate(range(i0, min(len(g1), i0 + n_jours))):
        plancher = (blocage if haut >= seuil else haut - perte) if finance else haut - perte
        coussin = solde - plancher
        if regle is not None and coussin < regle[0]:
            n1, n2 = (0, 1) if regle[1] == "rsi2" else (1, 0)
        else:
            n1 = int(min(max(np.floor(f * coussin / ks / s1[k]), 1), 50)) if s1[k] > 0 else 1
            n2 = int(min(max(np.floor(f * coussin / ks / s2[k]), 1), 50)) if s2[k] > 0 else 1
        jour, creux = n1 * g1[k] + n2 * g2[k], n1 * p1[k] + n2 * p2[k]
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
            finance = True
            solde = haut = capital
            meilleur = gain_p = 0.0
            qualif = 0
        elif finance:
            meilleur = max(meilleur, jour)
            gain_p += jour
            qualif += jour >= gq
            r = min(rmax, solde - seuil)
            if qualif >= jq and r >= rmin and gain_p > 0 and meilleur <= regul * gain_p:
                recu += part * r
                solde -= r
                meilleur = gain_p = 0.0
                qualif = 0
                premier = t if premier is None else premier
        en_finance[t] = finance
    return recu, challenges, perdus, en_finance, premier


def main():
    robot, j, S = T2.series()
    sortie = []
    ecrire = lambda s="": (print(s, flush=True), sortie.append(s))
    # controle : sans frein, ce simulateur = carriere() de zone_deux (gestion actuelle)
    for i0 in (0, 700, 1600, len(j) - 2 * AN):
        a = parcours(S, i0, 2 * AN)
        b = T2.carriere(*S[:3], *S[3:], True, i0, 2 * AN, 0.15, 0.15, 0.15, 0.0, robot.JOURS_QUALIF, robot.GAIN_QUALIF)
        assert np.isclose(a[0], b[0]) and (a[1], a[2]) == (b[1], b[2]), (i0, a[:3], b)
    ecrire("Controle : ce simulateur sans frein = celui de zone_deux/ (lui-meme verifie egal au robot) : OK")
    ecrire(f"Zone de bruit + RSI(2), gestion actuelle. Seances {j[0].date()} -> {j[-1].date()}. Challenge 164 $.")
    ctrl = [i for i in range(0, len(j), 5) if j[i] >= pd.Timestamp("2023-01-01") and i + 2 * AN <= len(j)]
    choix = [i for i in range(0, len(j), 5) if j[i].year <= 2020 and i + 2 * AN <= len(j) and j[min(i + 2 * AN, len(j) - 1)].year <= 2022]

    # ---------------------------------------------------------------- A. plusieurs comptes
    def comptes(idx, n_comptes, ecart, regle=None):
        res = []
        for i in idx:
            recu = frais = 0.0
            fin_tout = np.zeros(2 * AN, bool)
            premiers = []
            for k in range(n_comptes):
                d = k * ecart
                r = parcours(S, i + d, 2 * AN - d, regle)
                recu += r[0]
                frais += PRIX * r[1]
                fin_tout[d:] |= r[3]
                if r[4] is not None:
                    premiers.append(d + r[4])
            res.append({"net": recu - frais, "recu": recu, "frais": frais, "temps_finance": fin_tout.mean(),
                        "premier": min(premiers) if premiers else None})
        return pd.DataFrame(res)

    def resume(df):
        p = df["premier"].dropna()
        return (f"net en 24 mois : moyenne {df.net.mean():+7,.0f} $, mediane {df.net.median():+7,.0f} $, pire {df.net.min():+7,.0f} $,"
                f" perte d'argent dans {(df.net < 0).mean():4.0%} des cas | challenges payes {df.frais.mean():5,.0f} $ | au moins un compte"
                f" finance {df.temps_finance.mean():4.0%} du temps | premier retrait {'apres ' + format(p.median() / 21, '.1f') + ' mois (mediane)' if len(p) else 'jamais'},"
                f" dans {df['premier'].notna().mean():4.0%} des cas")
    for titre, idx in (("Departs 2023-2024", ctrl), ("Information, en echantillon : departs 2011-2020", choix)):
        ecrire(f"\n=== A. {titre} ({len(idx)} departs, horizon 24 mois apres l'ouverture du premier compte)")
        un = comptes(idx, 1, 0)
        for n in (1, 2, 3, 5):
            meme = comptes(idx[:12], n, 0) if n > 1 else None
            if meme is not None:
                assert np.allclose(meme.net.values, n * un.net.values[:12])      # n comptes le meme jour = n fois un compte
            df = un.assign(net=n * un.net, recu=n * un.recu, frais=n * un.frais)
            ecrire(f"  {n} compte(s) ouvert(s) le meme jour : {resume(df)}")
        for n in (2, 3):
            ecrire(f"  {n} comptes echelonnes (un tous les 3 mois) : {resume(comptes(idx, n, ECART))}")

    # ---------------------------------------------------------------- B. frein
    def mesure(idx, regle):
        x = [parcours(S, i, 2 * AN, regle) for i in idx]
        recu = np.array([r[0] for r in x]); ch = np.array([r[1] for r in x]); pe = np.array([r[2] for r in x])
        return {"net_an": float((recu - PRIX * ch).mean() / 2), "recu_an": float(recu.mean() / 2), "perdus_an": float(pe.mean() / 2),
                "rien": float((recu == 0).mean())}
    nom = lambda r: "base (gestion actuelle)" if r is None else f"frein : sous {r[0]:,.0f} $ de coussin, {'RSI(2)' if r[1] == 'rsi2' else 'zone'} seul"
    fmt = lambda m: f"net {m['net_an']:+6,.0f} $/an | recu {m['recu_an']:5,.0f} $/an | comptes perdus {m['perdus_an']:.2f}/an | rien recu {m['rien']:4.0%}"
    ecrire(f"\n=== B. Frein contre les comptes perdus : choix sur les departs 2011-2020 ({len(choix)} departs, 24 mois)")
    m_choix = {r: mesure(choix, r) for r in REGLES}
    for r in REGLES:
        ecrire(f"  {nom(r):45s} {fmt(m_choix[r])}")
    meilleure = max(REGLES, key=lambda r: m_choix[r]["net_an"])
    ecrire(f"  choisie : {nom(meilleure)}")
    ecrire(f"\n  Controle, departs 2023-2024 ({len(ctrl)} departs, 24 mois) :")
    m_ctrl = {r: mesure(ctrl, r) for r in REGLES}
    for r in REGLES:
        ecrire(f"  {nom(r):45s} {fmt(m_ctrl[r])}")
    base, ch = m_ctrl[None], m_ctrl[meilleure]
    adopte = meilleure is not None and ch["net_an"] > base["net_an"] and ch["perdus_an"] <= base["perdus_an"]
    ecrire(f"\nAdoption (README) : {nom(meilleure)} -> " + ("la base elle-meme : rien a changer" if meilleure is None else
           (f"ADOPTEE ({ch['net_an']:+,.0f} $/an contre {base['net_an']:+,.0f} ; comptes perdus {ch['perdus_an']:.2f} contre {base['perdus_an']:.2f})" if adopte
            else f"non adoptee ({ch['net_an']:+,.0f} $/an contre {base['net_an']:+,.0f} ; comptes perdus {ch['perdus_an']:.2f} contre {base['perdus_an']:.2f})")))
    (ICI / "comptes.txt").write_text("\n".join(sortie) + "\n")


if __name__ == "__main__":
    main()
