#!/usr/bin/env python3
"""Piste 5 (README.md) : le bot tel quel (1 MNQ par source) sur trois comptes DayTraders : Trail 50K puis Pro, S2L Core
50K (evaluation puis compte reel sans regle de regularite), S2F 50K (finance tout de suite, descriptif). Meme moteur que
protection.py / piste2.py. Ecrit piste5.txt et piste5.json. Lancer depuis ce dossier : python3 piste5.py"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

import piste2 as Q
import protection as P

ICI = Path(__file__).resolve().parent
UN_AN = P.MAX_SEANCES


@njit(cache=True)
def seance5(d, etat, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu,
            perte, mode, blocage, frais_zone, frais_rsi, plafond, dll_douce):
    """Comme piste2.seance (q = 1, pas de seuil), avec une limite du jour douce : a veille - dll_douce, le bot ferme tout et
    ne trade plus de la journee (le compte continue). etat : cash, zp, ze, rp, re, veut, bloque, rsi_ok, pic_rt, plancher,
    veille. Renvoie (perdu, valeur de fin de seance)."""
    cash, zp, ze, rp, re = etat[0], int(etat[1]), etat[2], int(etat[3]), etat[4]
    veut, bloque, pic_rt, plancher, veille = int(etat[5]), etat[6] > 0, etat[8], etat[9], etat[10]
    k = z_deb[d]
    actif = -1
    arret = False
    glisse = 0.25 * 2.0
    nmin = O.shape[1]
    for t in range(nmin):
        if t == dec[d]:
            veut = voulu[d]
            if bloque and veut == 0:
                bloque = False
            cible = veut if (not bloque and not arret) else 0
            if cible != rp:
                if rp == 1:
                    cash += (O[d, t] - re) * 2.0 - frais_rsi
                    rp = 0
                else:
                    cash -= frais_rsi
                    rp, re = 1, O[d, t]
        n = zp + rp
        a = cash - 2.0 * (zp * ze + rp * re)
        if n > 0:
            hautv, basv = a + 2.0 * n * H[d, t], a + 2.0 * n * L[d, t]
        elif n < 0:
            hautv, basv = a + 2.0 * n * L[d, t], a + 2.0 * n * H[d, t]
        else:
            hautv, basv = a, a
        if mode == 1:
            if hautv > pic_rt:
                pic_rt = hautv
            plancher = pic_rt - perte
            if plancher > blocage:
                plancher = blocage
        ouv = a + 2.0 * n * O[d, t]
        if plafond > 0.0 and n != 0 and hautv >= veille + plafond:          # plafond du jour
            x = veille + plafond if ouv < veille + plafond else ouv
            cash = x - (frais_zone if zp != 0 else 0.0) - (frais_rsi if rp != 0 else 0.0) - glisse * (abs(zp) + rp)
            zp, rp, arret = 0, 0, True
            if actif >= 0:
                actif = -2
            basv = cash
        if dll_douce > 0.0 and n != 0 and zp + rp != 0 and basv <= veille - dll_douce:   # limite du jour douce
            x = veille - dll_douce if ouv > veille - dll_douce else ouv
            cash = x - (frais_zone if zp != 0 else 0.0) - (frais_rsi if rp != 0 else 0.0) - glisse * (abs(zp) + rp)
            zp, rp, arret = 0, 0, True
            if actif >= 0:
                actif = -2
            basv = cash
        if basv <= plancher:
            return 1, basv
        if actif >= 0 and z_ms[actif] == t:
            cash += zp * (C[d, t] - ze) * 2.0 - frais_zone
            zp, actif = 0, -1
        while k < z_fin[d] and z_me[k] < t:
            k += 1
        if k < z_fin[d] and z_me[k] == t:
            if z_garde[k] == 1 and zp == 0 and not arret:
                zp, ze, actif = z_sens[k], C[d, t], k
            k += 1
    eod = cash + rp * (C[d, nmin - 1] - re) * 2.0
    etat[0], etat[1], etat[2], etat[3], etat[4] = cash, zp, ze, rp, re
    etat[5], etat[6], etat[8], etat[9] = veut, 1.0 if bloque else 0.0, pic_rt, plancher
    return 0, eod


@njit(cache=True)
def depart(ouvert, d, perte):
    etat = np.zeros(11)
    etat[5] = ouvert[d]
    etat[6] = 1.0 if ouvert[d] == 1 else 0.0       # pas d'entree au milieu d'un trade du RSI(2)
    etat[9] = -perte
    return etat


@njit(cache=True)
def evaluation(debut, nmax, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu, ouvert,
               objectif, perte, regul, jmin, plafond, frais_zone, frais_rsi):
    """Evaluation a limite suivie en temps reel, bloquee a 50 000 $. Renvoie (issue 1/-1/0, derniere seance)."""
    etat = depart(ouvert, debut, perte)
    meilleur, qualif = -1e18, 0
    fin = min(O.shape[0], debut + nmax)
    for d in range(debut, fin):
        perdu, eod = seance5(d, etat, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu,
                             perte, 1, 0.0, frais_zone, frais_rsi, plafond, 0.0)
        if perdu:
            return -1, d
        g = eod - etat[10]
        etat[10] = eod
        meilleur = max(meilleur, g)
        if g >= 200.0:
            qualif += 1
        if eod >= objectif and qualif >= jmin and meilleur <= regul * eod:
            return 1, d
    return 0, fin - 1


@njit(cache=True)
def reel_s2l(debut, nmax, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu, ouvert, frais_zone, frais_rsi):
    """Compte reel S2L : limite suivie en temps reel (2 000 $), bloquee a 50 000 $ ; a chaque cloture, si le solde depasse
    52 500 $, tout ce qui depasse 52 000 $ est retire (80 % pour le trader). Renvoie (perdu, retraits, recu, 1er retrait)."""
    etat = depart(ouvert, debut, 2000.0)
    nret, recu, premier = 0, 0.0, -1
    fin = min(O.shape[0], debut + nmax)
    for d in range(debut, fin):
        perdu, eod = seance5(d, etat, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu,
                             2000.0, 1, 0.0, frais_zone, frais_rsi, 0.0, 0.0)
        if perdu:
            return 1, nret, recu, premier
        etat[10] = eod
        if eod >= 2500.0:
            x = eod - 2000.0
            etat[0] -= x
            etat[10] -= x
            recu += 0.8 * x
            nret += 1
            if premier < 0:
                premier = d
    return 0, nret, recu, premier


@njit(cache=True)
def s2f(debut, nmax, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu, ouvert, plafond, frais_zone, frais_rsi):
    """S2F 50K (descriptif) : limite = plus haut solde de cloture - 2 500 $, bloquee a 50 000 $ ; limite du jour douce de
    1 250 $ ; retraits selon README.md. Renvoie (perdu, retraits, recu, 1er retrait)."""
    etat = depart(ouvert, debut, 2500.0)
    pic_eod, base, meilleur, qualif, nret, recu, premier = 0.0, 0.0, -1e18, 0, 0, 0.0, -1
    fin = min(O.shape[0], debut + nmax)
    for d in range(debut, fin):
        perdu, eod = seance5(d, etat, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu,
                             2500.0, 0, 0.0, frais_zone, frais_rsi, plafond, 1250.0)
        if perdu:
            return 1, nret, recu, premier
        g = eod - etat[10]
        etat[10] = eod
        meilleur = max(meilleur, g)
        if g >= 200.0:
            qualif += 1
        pic_eod = max(pic_eod, eod)
        etat[9] = min(pic_eod - 2500.0, 0.0)
        seuil = 3500.0 if nret == 0 else (3000.0 if nret == 1 else 2500.0)
        gain = eod - base
        if qualif >= 10 and gain >= seuil and meilleur <= 0.2 * gain and eod >= 1500.0:
            x = min(2000.0, eod - 1000.0)
            etat[0] -= x
            etat[10] -= x
            recu += x
            nret += 1
            if premier < 0:
                premier = d
            base, meilleur, qualif = etat[10], -1e18, 0
    return 0, nret, recu, premier


def main():
    jours, O, H, L, C, Z, dec, voulu, ouvert = P.donnees()
    nj = len(jours)
    dates = pd.DatetimeIndex(jours)
    base = (O, H, L, C, P.tableaux_zone(Z, nj, np.ones(len(Z), bool)), dec, voulu, ouvert)
    a = Q.zt_args(base)
    possibles = [d for d in range(260, nj) if ouvert[d] == 0]
    # controle : evaluation Trail de ce fichier = challenge Trail de piste2 (memes issues)
    dd = [d for d in possibles if dates[d].year >= 2023 and d + UN_AN <= nj][::2]
    ref = Q.jouer(dd, base, P.COMPTES["DayTraders Trail"], 0.0)
    mien = [evaluation(int(d), UN_AN, *a, 3000.0, 2500.0, 0.5, 2, 0.0, P.FRAIS_ZONE, P.FRAIS_RSI)[0] for d in dd]
    L_ = [f"Controle : evaluation Trail de piste5 contre piste2, {len(dd)} departs : issues identiques"
          f" {int(sum(int(x) == int(y) for x, y in zip(mien, ref['issue'])))}/{len(dd)}", ""]
    res = {}
    for titre, an in (("2023 - sept. 2025", lambda x: x.year >= 2023), ("2025", lambda x: x.year == 2025)):
        dd = [d for d in possibles if an(dates[d]) and d + UN_AN <= nj][::2]
        lignes = {}
        for d in dd:
            fin_an = d + UN_AN
            # 1. Trail 50K puis Pro (piste 2)
            i, f = evaluation(d, UN_AN, *a, 3000.0, 2500.0, 0.5, 2, 0.0, P.FRAIS_ZONE, P.FRAIS_RSI)
            r = (0, 0, 0.0, -1)
            if i == 1 and f + 1 < nj:
                x = Q.finance(f + 1, fin_an - f - 1, *a, 2500.0, P.FRAIS_ZONE, P.FRAIS_RSI)
                r = (x[0], x[2], x[3], (f + 1 + x[4] - 1) if x[4] > 0 else -1)
            lignes.setdefault("Trail 50K puis Pro", []).append((d, i, *r, 75.0))
            # 2. S2L Core 50K, evaluation sans plafond puis avec plafond 750 $
            for nom, plaf in (("S2L Core 50K", 0.0), ("S2L Core 50K, plafond 750 $ en evaluation", 750.0)):
                i, f = evaluation(d, UN_AN, *a, 3000.0, 2000.0, 0.25, 8, plaf, P.FRAIS_ZONE, P.FRAIS_RSI)
                r = (0, 0, 0.0, -1)
                if i == 1 and f + 1 < fin_an:
                    r = reel_s2l(f + 1, fin_an - f - 1, *a, P.FRAIS_ZONE, P.FRAIS_RSI)
                lignes.setdefault(nom, []).append((d, i, *r, 229.0))
            # 3. S2F 50K (descriptif), sans plafond et avec plafond 500 $
            for nom, plaf in (("S2F 50K (descriptif)", 0.0), ("S2F 50K, plafond 500 $ (descriptif)", 500.0)):
                r = s2f(d, UN_AN, *a, plaf, P.FRAIS_ZONE, P.FRAIS_RSI)
                lignes.setdefault(nom, []).append((d, 1, *r, 57.0))
        L_.append(f"=== Challenges de {titre} ({len(dd)} achats, 12 mois de suivi chacun) ===")
        L_.append("compte | reussi | au moins un retrait en 12 mois | recu moyen en 12 mois, prix deduit | 1er retrait (mediane, seances apres l'achat) | compte finance/reel perdu")
        for nom, l in lignes.items():
            F = pd.DataFrame(l, columns=["depart", "ok", "perdu", "nret", "recu", "premier", "prix"])
            ok = F["ok"] == 1
            delai = (F.loc[F["premier"] >= 0, "premier"] - F.loc[F["premier"] >= 0, "depart"]).median()
            net = (F["recu"] - F["prix"]).mean()
            perdu = F.loc[ok, "perdu"].mean() if ok.any() else float("nan")
            L_.append(f"{nom} | {ok.mean():.0%} | {(F['nret'] > 0).mean():.0%} | {net:+,.0f} $ | "
                      f"{'-' if np.isnan(delai) else f'{delai:.0f}'} | {perdu:.0%}")
            res[f"{titre} | {nom}"] = {"reussi": float(ok.mean()), "retrait_12_mois": float((F["nret"] > 0).mean()),
                                      "recu_net_12_mois": float(net), "premier_retrait_seances": None if np.isnan(delai) else float(delai),
                                      "perdu_ensuite": None if np.isnan(perdu) else float(perdu)}
        L_.append("")
    (ICI / "piste5.txt").write_text("\n".join(L_) + "\n")
    (ICI / "piste5.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("\n".join(L_))


if __name__ == "__main__":
    main()
