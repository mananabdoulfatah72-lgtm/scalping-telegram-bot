#!/usr/bin/env python3
"""Piste 2 (README.md) : variante Z (« zone d'abord », le RSI(2) n'ouvre qu'une fois le compte a +2 500 $) et phase
financee DayTraders (compte Pro) apres un challenge Trail 50K reussi. Meme moteur que protection.py.
Ecrit piste2.txt et piste2.json. Lancer depuis ce dossier : python3 piste2.py"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

import protection as P

ICI = Path(__file__).resolve().parent
SEUIL_Z = 2500.0


@njit(cache=True)
def seance(d, etat, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu,
           perte, mode, blocage, dll, seuil, frais_zone, frais_rsi, q, plafond):
    """Joue la seance d sans protection, q MNQ par source. etat (tableau de 10) : cash, zp, ze, rp, re, veut, bloque, rsi_ok, pic_rt,
    plancher. Renvoie (perdu, valeur de fin de seance, marge mini du jour)."""
    v = 2.0 * q
    frais_zone, frais_rsi = frais_zone * q, frais_rsi * q
    cash, zp, ze, rp, re = etat[0], int(etat[1]), etat[2], int(etat[3]), etat[4]
    veut, bloque, rsi_ok, pic_rt, plancher = int(etat[5]), etat[6] > 0, etat[7] > 0, etat[8], etat[9]
    veille = etat[10]
    k = z_deb[d]
    actif = -1
    marge = 1e18
    nmin = O.shape[1]
    arret = False
    glisse = 0.25 * v
    for t in range(nmin):
        if t == dec[d]:
            veut = voulu[d]
            if bloque and veut == 0:
                bloque = False
            if not rsi_ok and cash + rp * (O[d, t] - re) * v >= seuil:
                rsi_ok = True
                if veut == 1 and rp == 0:
                    bloque = True              # pas d'entree au milieu d'un trade du RSI(2) : on attend un nouveau signal
            cible = veut if (rsi_ok and not bloque and not arret) else 0
            if cible != rp:
                if rp == 1:
                    cash += (O[d, t] - re) * v - frais_rsi
                    rp = 0
                else:
                    cash -= frais_rsi
                    rp, re = 1, O[d, t]
        n = zp + rp
        a = cash - v * (zp * ze + rp * re)
        if n > 0:
            hautv, basv = a + v * n * H[d, t], a + v * n * L[d, t]
        elif n < 0:
            hautv, basv = a + v * n * L[d, t], a + v * n * H[d, t]
        else:
            hautv, basv = a, a
        if mode == 1:
            if hautv > pic_rt:
                pic_rt = hautv
            plancher = pic_rt - perte
            if blocage == blocage and plancher > blocage:
                plancher = blocage
        dur = plancher
        if dll > 0.0 and veille - dll > dur:
            dur = veille - dll
        if plafond > 0.0 and n != 0 and hautv >= veille + plafond:      # plafond du jour (piste 4)
            ouv = a + v * n * O[d, t]
            x = veille + plafond if ouv < veille + plafond else ouv
            cash = x - (frais_zone if zp != 0 else 0.0) - (frais_rsi if rp != 0 else 0.0) - glisse * (abs(zp) + rp)
            zp, rp, arret = 0, 0, True
            if actif >= 0:
                actif = -2
            basv = cash
        if basv - dur < marge:
            marge = basv - dur
        if basv <= dur:
            return 1, basv, marge
        if actif >= 0 and z_ms[actif] == t:
            cash += zp * (C[d, t] - ze) * v - frais_zone
            zp, actif = 0, -1
        while k < z_fin[d] and z_me[k] < t:
            k += 1
        if k < z_fin[d] and z_me[k] == t:
            if z_garde[k] == 1 and zp == 0 and not arret:
                zp, ze, actif = z_sens[k], C[d, t], k
            k += 1
    eod = cash + rp * (C[d, nmin - 1] - re) * v
    etat[0], etat[1], etat[2], etat[3], etat[4] = cash, zp, ze, rp, re
    etat[5], etat[6], etat[7], etat[8], etat[9] = veut, 1.0 if bloque else 0.0, 1.0 if rsi_ok else 0.0, pic_rt, plancher
    return 0, eod, marge


@njit(cache=True)
def challenge(debut, nmax, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu, ouvert,
              objectif, perte, mode, blocage, dll, regul, jmin, seuil, frais_zone, frais_rsi):
    """Challenge sans protection, avec le seuil du RSI(2) (0 : RSI(2) des le depart). Renvoie (issue, seance de fin,
    seances jouees, marge mini)."""
    etat = np.zeros(11)
    etat[5] = ouvert[debut]
    etat[6] = 1.0 if ouvert[debut] == 1 else 0.0
    etat[7] = 1.0 if seuil <= 0.0 else 0.0
    etat[9] = -perte
    pic_eod, meilleur, qualif, marge = 0.0, -1e18, 0, 1e18
    fin = min(O.shape[0], debut + nmax)
    for d in range(debut, fin):
        perdu, eod, m = seance(d, etat, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu,
                               perte, mode, blocage, dll, seuil, frais_zone, frais_rsi, 1.0, 0.0)
        if m < marge:
            marge = m
        if perdu:
            return -1, d, d - debut + 1, marge
        g = eod - etat[10]
        etat[10] = eod
        if g > meilleur:
            meilleur = g
        if g >= 200.0:
            qualif += 1
        if mode == 0:
            if eod > pic_eod:
                pic_eod = eod
            etat[9] = pic_eod - perte
            if blocage == blocage and etat[9] > blocage:
                etat[9] = blocage
        if eod >= objectif and qualif >= jmin and (regul == 0.0 or meilleur <= regul * eod):
            return 1, d, d - debut + 1, marge
    return 0, fin - 1, fin - debut, marge


@njit(cache=True)
def finance(debut, nmax, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu, ouvert,
            perte, frais_zone, frais_rsi, taille_bloque=1.0, tous_qualifiants=False, plafond=0.0):
    """Compte Pro DayTraders 50K (README.md). Renvoie (perdu, seances jouees, retraits, total recu, seance du 1er retrait
    depuis le debut du compte, -1 si aucun)."""
    etat = np.zeros(11)
    etat[5] = ouvert[debut]
    etat[6] = 1.0 if ouvert[debut] == 1 else 0.0
    etat[7] = 1.0
    etat[9] = -perte
    base, meilleur, qualif, nret, recu, premier = 0.0, -1e18, 0, 0, 0.0, -1
    q = 1.0
    fin = min(O.shape[0], debut + nmax)
    for d in range(debut, fin):
        if q == 1.0 and taille_bloque != 1.0 and etat[9] >= 0.0 and etat[3] == 0:
            q = taille_bloque                  # limite bloquee et RSI(2) a plat : nouvelle taille pour les trades suivants
        perdu, eod, m = seance(d, etat, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu,
                               perte, 1, 0.0, 0.0, 0.0, frais_zone, frais_rsi, q, plafond)
        if perdu:
            return 1, d - debut + 1, nret, recu, premier
        g = eod - etat[10]
        etat[10] = eod
        if g > meilleur:
            meilleur = g
        if g >= 200.0 or tous_qualifiants:
            qualif += 1
        gain = eod - base
        if qualif >= 8 and gain > 0.0 and meilleur <= 0.3 * gain and eod >= 1500.0:
            x = min(2000.0, eod - 1000.0)
            etat[0] -= x                       # le retrait sort du solde (la limite reste bloquee au plus a 50 000 $)
            etat[10] -= x
            recu += x
            nret += 1
            if premier < 0:
                premier = d - debut + 1
            base, meilleur, qualif = etat[10], -1e18, 0
    return 0, fin - debut, nret, recu, premier


def zt_args(base):
    O, H, L, C, zt, dec, voulu, ouvert = base
    return (O, H, L, C) + tuple(zt) + (dec, voulu, ouvert)


def jouer(departs, base, compte, seuil, nmax=P.MAX_SEANCES):
    obj, perte, mode, blocage, dll, regul, jmin = compte
    a = zt_args(base)
    out = [challenge(int(d), nmax, *a, obj, perte, mode, np.nan if blocage is None else blocage, dll, regul, jmin,
                     seuil, P.FRAIS_ZONE, P.FRAIS_RSI) for d in departs]
    return pd.DataFrame(out, columns=["issue", "fin", "seances", "marge"], index=departs)


def main():
    jours, O, H, L, C, Z, dec, voulu, ouvert = P.donnees()
    nj = len(jours)
    dates = pd.DatetimeIndex(jours)
    base = (O, H, L, C, P.tableaux_zone(Z, nj, np.ones(len(Z), bool)), dec, voulu, ouvert)
    # controle : seuil 0 = protection A du moteur valide (memes issues sur les memes departs)
    possibles = [d for d in range(260, nj) if ouvert[d] == 0]
    departs = possibles[::P.PAS_DEPART]
    a_ref = P.lancer(departs, base, P.COMPTES["DayTraders Trail"], P.PROTECTIONS["A"])
    a_new = jouer(departs, base, P.COMPTES["DayTraders Trail"], 0.0)
    L_ = [f"Controle : seuil 0 contre protection A de protection.py, DayTraders Trail, {len(departs)} departs :"
          f" issues identiques {int((a_ref['issue'].to_numpy() == a_new['issue'].to_numpy()).sum())}/{len(departs)}", ""]
    expl = [d for d in departs if dates[d] <= pd.Timestamp("2022-12-31")]
    coffre = [d for d in departs if dates[d] >= pd.Timestamp("2023-01-01")]
    complets_2025 = [d for d in possibles if dates[d].year == 2025 and d + P.MAX_SEANCES <= nj]
    res = {}
    for nom in ("Phidias Premium", "DayTraders Trail", "DayTraders EOD"):
        c = P.COMPTES[nom]
        L_ += [f"=== {nom} === version | 2011-2022 : reussis / perdus / score | 2023-2026 : reussis / perdus / score |"
               " departs 2025 suivis 252 seances : reussis / perdus"]
        res[nom] = {}
        for v, seuil in (("A", 0.0), ("Z", SEUIL_Z)):
            b1, b2 = P.bilan(jouer(expl, base, c, seuil)), P.bilan(jouer(coffre, base, c, seuil))
            b3 = P.bilan(jouer(complets_2025, base, c, seuil))
            res[nom][v] = {"2011-2022": b1, "2023-2026": b2, "2025": b3}
            L_.append(f"{v} | {b1['reussis']} / {b1['perdus']} / {b1['score']:+.1f} | {b2['reussis']} / {b2['perdus']} /"
                      f" {b2['score']:+.1f} | {b3['reussis']} / {b3['perdus']} ({b3['departs']} departs)")
        a, z = res[nom]["A"], res[nom]["Z"]
        choix = "Z" if z["2011-2022"]["score"] >= a["2011-2022"]["score"] + 3 else "A"
        verif = choix == "A" or z["2023-2026"]["score"] >= a["2023-2026"]["score"]
        res[nom]["retenu"] = choix if verif else "A"
        L_.append(f"-> choix sur 2011-2022 : {choix} ; verification 2023-2026 : {'oui' if verif else 'non'} ;"
                  f" RETENU : {res[nom]['retenu']}")
        L_.append("")
    # phase financee DayTraders apres un Trail 50K reussi (bot tel quel), departs 2023 - 2025 suivis completement
    L_.append("=== Phase financee DayTraders (Pro 50K), bot tel quel ===")
    a = zt_args(base)
    for titre, periode in (("departs 2023 - septembre 2025", lambda x: x.year >= 2023), ("departs 2025", lambda x: x.year == 2025)):
        dd = [d for d in possibles if periode(dates[d]) and d + P.MAX_SEANCES <= nj]     # suivi complet de 12 mois
        ch = jouer(dd[::2], base, P.COMPTES["DayTraders Trail"], 0.0)
        lignes = []
        for d, x in ch.iterrows():
            un_an = d + P.MAX_SEANCES                  # 12 mois apres l'achat du challenge
            if x["issue"] == 1 and int(x["fin"]) + 1 < nj:
                f = finance(int(x["fin"]) + 1, P.MAX_SEANCES, *a, 2500.0, P.FRAIS_ZONE, P.FRAIS_RSI)
                f12 = finance(int(x["fin"]) + 1, max(0, un_an - int(x["fin"]) - 1), *a, 2500.0, P.FRAIS_ZONE, P.FRAIS_RSI)
                lignes.append((d, 1, *f, f12[3], f12[2]))
            else:
                lignes.append((d, int(x["issue"]), 0, 0, 0, 0.0, -1, 0.0, 0))
        F = pd.DataFrame(lignes, columns=["depart", "challenge", "perdu_pro", "seances_pro", "retraits", "recu",
                                          "premier", "recu_12_mois", "retraits_12_mois"])
        ok = F[F["challenge"] == 1]
        L_ += [f"{titre} ({len(F)} challenges) : challenge reussi {len(ok) / len(F):.0%} ;",
               f"  apres la reussite (252 seances de compte Pro au plus) : au moins un retrait {(ok['retraits'] > 0).mean():.0%},"
               f" compte Pro perdu {ok['perdu_pro'].mean():.0%}, recu moyen {ok['recu'].mean():,.0f} $ (mediane {ok['recu'].median():,.0f} $),"
               f" premier retrait apres {ok.loc[ok['premier'] > 0, 'premier'].median():.0f} seances (mediane)",
               f"  sur les 12 mois qui suivent l'achat du challenge : recu moyen {F['recu_12_mois'].mean():,.0f} $ par challenge achete,"
               f" au moins un retrait {(F['retraits_12_mois'] > 0).mean():.0%} des challenges", ""]
        res[f"finance {titre}"] = {"challenges": len(F), "reussis": float(len(ok) / len(F)),
                                   "au_moins_un_retrait": float((ok["retraits"] > 0).mean()), "perdu_pro": float(ok["perdu_pro"].mean()),
                                   "recu_moyen": float(ok["recu"].mean()), "recu_12_mois_par_challenge": float(F["recu_12_mois"].mean()),
                                   "retrait_12_mois": float((F["retraits_12_mois"] > 0).mean())}
    (ICI / "piste2.txt").write_text("\n".join(L_) + "\n")
    (ICI / "piste2.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("\n".join(L_))




def piste3():
    """Piste 3 (README.md) : compte Pro a 2 MNQ par source une fois la limite bloquee ; descriptif : tout jour qualifie."""
    jours, O, H, L, C, Z, dec, voulu, ouvert = P.donnees()
    nj = len(jours)
    dates = pd.DatetimeIndex(jours)
    base = (O, H, L, C, P.tableaux_zone(Z, nj, np.ones(len(Z), bool)), dec, voulu, ouvert)
    a = zt_args(base)
    possibles = [d for d in range(260, nj) if ouvert[d] == 0]
    L_ = ["Piste 3 : compte Pro DayTraders, challenges Trail 50K de 2023 - septembre 2025 (un depart sur deux, 12 mois de suivi)"]
    res = {}
    for titre, an in (("2023 - sept. 2025", lambda x: x.year >= 2023), ("2025", lambda x: x.year == 2025)):
        dd = [d for d in possibles if an(dates[d]) and d + P.MAX_SEANCES <= nj][::2]
        ch = jouer(dd, base, P.COMPTES["DayTraders Trail"], 0.0)
        for nom, taille, tous in (("1 MNQ (piste 2)", 1.0, False), ("2 MNQ apres blocage", 2.0, False),
                                  ("1 MNQ, tout jour qualifie (descriptif)", 1.0, True), ("2 MNQ, tout jour qualifie (descriptif)", 2.0, True)):
            lignes = []
            for d, x in ch.iterrows():
                if x["issue"] == 1 and int(x["fin"]) + 1 < nj:
                    f = finance(int(x["fin"]) + 1, P.MAX_SEANCES, *a, 2500.0, P.FRAIS_ZONE, P.FRAIS_RSI, taille, tous)
                    f12 = finance(int(x["fin"]) + 1, max(0, d + P.MAX_SEANCES - int(x["fin"]) - 1), *a, 2500.0,
                                  P.FRAIS_ZONE, P.FRAIS_RSI, taille, tous)
                    lignes.append((1, f[0], f[2], f[3], f12[3], f12[2]))
                else:
                    lignes.append((0, 0, 0, 0.0, 0.0, 0))
            F = pd.DataFrame(lignes, columns=["ok", "perdu", "nret", "recu", "recu12", "nret12"])
            ok = F[F["ok"] == 1]
            L_.append(f"{titre} | {nom} : challenges {len(F)}, reussis {len(ok) / len(F):.0%} ; compte Pro sur 252 seances :"
                      f" perdu {ok['perdu'].mean():.0%}, au moins un retrait {(ok['nret'] > 0).mean():.0%}, recu moyen {ok['recu'].mean():,.0f} $"
                      f" ; 12 mois apres l'achat : recu moyen {F['recu12'].mean():,.0f} $ par challenge, au moins un retrait {(F['nret12'] > 0).mean():.0%}")
            res[f"{titre} | {nom}"] = {"reussis": float(len(ok) / len(F)), "perdu_pro": float(ok["perdu"].mean()),
                                       "retrait": float((ok["nret"] > 0).mean()), "recu_moyen": float(ok["recu"].mean()),
                                       "recu_12_mois": float(F["recu12"].mean()), "retrait_12_mois": float((F["nret12"] > 0).mean())}
    r1, r2 = res["2023 - sept. 2025 | 1 MNQ (piste 2)"], res["2023 - sept. 2025 | 2 MNQ apres blocage"]
    ok = r2["recu_12_mois"] > r1["recu_12_mois"] and r2["perdu_pro"] <= 0.40
    L_.append(f"-> 2 MNQ apres blocage : {'RETENU' if ok else 'PAS RETENU'} (recu sur 12 mois {r1['recu_12_mois']:,.0f} -> {r2['recu_12_mois']:,.0f} $,"
              f" comptes Pro perdus {r2['perdu_pro']:.0%}, seuil 40 %)")
    (ICI / "piste3.txt").write_text("\n".join(L_) + "\n")
    (ICI / "piste3.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("\n".join(L_))



def piste4():
    """Piste 4 (README.md) : compte Pro avec un plafond du jour a 500 $ ; challenge inchange."""
    jours, O, H, L, C, Z, dec, voulu, ouvert = P.donnees()
    nj = len(jours)
    dates = pd.DatetimeIndex(jours)
    base = (O, H, L, C, P.tableaux_zone(Z, nj, np.ones(len(Z), bool)), dec, voulu, ouvert)
    a = zt_args(base)
    possibles = [d for d in range(260, nj) if ouvert[d] == 0]
    L_ = ["Piste 4 : compte Pro DayTraders avec plafond du jour a 500 $, challenges Trail 50K (un depart sur deux, 12 mois de suivi)"]
    res = {}
    for titre, an in (("2023 - sept. 2025", lambda x: x.year >= 2023), ("2025", lambda x: x.year == 2025)):
        dd = [d for d in possibles if an(dates[d]) and d + P.MAX_SEANCES <= nj][::2]
        ch = jouer(dd, base, P.COMPTES["DayTraders Trail"], 0.0)
        for nom, plaf in (("sans plafond (piste 2)", 0.0), ("plafond 500 $", 500.0)):
            lignes = []
            for d, x in ch.iterrows():
                if x["issue"] == 1 and int(x["fin"]) + 1 < nj:
                    f = finance(int(x["fin"]) + 1, P.MAX_SEANCES, *a, 2500.0, P.FRAIS_ZONE, P.FRAIS_RSI, 1.0, False, plaf)
                    f12 = finance(int(x["fin"]) + 1, max(0, d + P.MAX_SEANCES - int(x["fin"]) - 1), *a, 2500.0,
                                  P.FRAIS_ZONE, P.FRAIS_RSI, 1.0, False, plaf)
                    lignes.append((1, f[0], f[2], f[3], f[4], f12[3], f12[2]))
                else:
                    lignes.append((0, 0, 0, 0.0, -1, 0.0, 0))
            F = pd.DataFrame(lignes, columns=["ok", "perdu", "nret", "recu", "premier", "recu12", "nret12"])
            ok = F[F["ok"] == 1]
            prem = ok.loc[ok["premier"] > 0, "premier"]
            L_.append(f"{titre} | {nom} : challenges {len(F)}, reussis {len(ok) / len(F):.0%} ; compte Pro sur 252 seances :"
                      f" perdu {ok['perdu'].mean():.0%}, au moins un retrait {(ok['nret'] > 0).mean():.0%}, recu moyen {ok['recu'].mean():,.0f} $,"
                      f" 1er retrait apres {prem.median() if len(prem) else float('nan'):.0f} seances ; 12 mois apres l'achat :"
                      f" recu moyen {F['recu12'].mean():,.0f} $ par challenge, au moins un retrait {(F['nret12'] > 0).mean():.0%}")
            res[f"{titre} | {nom}"] = {"reussis": float(len(ok) / len(F)), "perdu_pro": float(ok["perdu"].mean()),
                                       "retrait": float((ok["nret"] > 0).mean()), "recu_moyen": float(ok["recu"].mean()),
                                       "premier_retrait_seances": None if not len(prem) else float(prem.median()),
                                       "recu_12_mois": float(F["recu12"].mean()), "retrait_12_mois": float((F["nret12"] > 0).mean())}
    r1, r2 = res["2023 - sept. 2025 | sans plafond (piste 2)"], res["2023 - sept. 2025 | plafond 500 $"]
    ok = r2["recu_12_mois"] > r1["recu_12_mois"] and r2["perdu_pro"] <= 0.40
    L_.append(f"-> plafond 500 $ : {'RETENU' if ok else 'PAS RETENU'} (recu sur 12 mois {r1['recu_12_mois']:,.0f} -> {r2['recu_12_mois']:,.0f} $,"
              f" comptes Pro perdus {r2['perdu_pro']:.0%}, seuil 40 %)")
    (ICI / "piste4.txt").write_text("\n".join(L_) + "\n")
    (ICI / "piste4.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("\n".join(L_))


if __name__ == "__main__":
    import sys as _s
    piste4() if "piste4" in _s.argv else (piste3() if "piste3" in _s.argv else main())
