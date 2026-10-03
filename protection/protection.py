#!/usr/bin/env python3
"""Protections du bot 3 en 1 (README.md) : zone de bruit (filtree par le vrai delta quand il existe) + RSI(2), 1 MNQ
chacun, rejoues minute par minute avec les regles de Phidias Premium 50K et de DayTraders 50K (Trail, EOD).
Ecrit resultats.txt et resultats.json. Lancer depuis ce dossier : python3 protection.py"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

ICI = Path(__file__).resolve().parent
R0 = ICI.parent
os.environ.setdefault("ROBOT_DEBUT_RSI2", "2000-01-01")          # RSI(2) actif sur tout l'historique
os.environ.setdefault("ROBOT_DOSSIER", str(ICI / "_robot"))      # rien n'est ecrit : le robot n'est pas lance
sys.path.insert(0, str(ICI))
import robot_main as RB                                          # noqa: E402

N = RB.N
PT = RB.PT
FRAIS_ZONE = RB.COUT * PT                     # $ par aller-retour de zone (1 MNQ)
FRAIS_RSI = (1.0 / PT + 0.25) * PT            # $ par ordre du RSI(2)
GLISSE = 0.25 * PT                            # 1 tick de plus pour une sortie de protection
FIN_DONNEES = "2026-09-25"
MAX_SEANCES, PAS_DEPART = 252, 5
COMPTES = {   # objectif, perte, mode (0 cloture, 1 temps reel), blocage (None : aucun), limite du jour, regularite, jours
    "Phidias Premium": (4000.0, 2500.0, 0, None, 0.0, 0.0, 0),
    "DayTraders Trail": (3000.0, 2500.0, 1, 0.0, 0.0, 0.5, 2),
    "DayTraders EOD": (3000.0, 2000.0, 0, None, 1250.0, 0.5, 2),
    "DayTraders EOD (bloquee a 50 000, descriptif)": (3000.0, 2000.0, 0, 0.0, 1250.0, 0.5, 2),
}
PROTECTIONS = {"A": (0, 0, 0), "B": (1, 0, 0), "C": (0, 1, 0), "B+C": (1, 1, 0), "D": (0, 0, 1), "B+C+D": (1, 1, 1)}
COUPE, STOP_RSI, PLAFOND = 300.0, 600.0, 1400.0


def donnees():
    d = pd.read_csv(R0 / "intraday/donnees/nasdaq100_1min.csv.gz")
    d = d[d["t"].str[:10] <= FIN_DONNEES]
    jours, O, H, L, C, P, V, ech = RB.tableaux(d)
    z, trades, _ = RB.zone_de_bruit(jours, O, H, L, C, P, V, ech)
    r, _ = RB.rsi2(jours, O, H, L, C, P, ech)
    # pour le moteur seulement : minutes avant la premiere transaction d'une seance = premiere minute connue
    O, H, L, C = (pd.DataFrame(a).bfill(axis=1).to_numpy() for a in (O, H, L, C))
    # zone : un trade par ligne (seance, minute d'entree, minute de sortie, sens)
    lignes = []
    for j, liste in trades.items():
        d_ = int(np.searchsorted(jours, j))
        for texte in liste:
            x = RB.MOTIF_ZONE.match(texte)
            if not x:
                continue
            me = int(x.group(2)) * 60 + int(x.group(3)) - 570
            ms = min(int(x.group(5)) * 60 + int(x.group(6)) - 570, N - 1)
            sens = 1 if x.group(1) == "achat" else -1
            e, s = float(x.group(4).replace(",", "")), float(x.group(7).replace(",", ""))
            assert abs(e - C[d_, me]) < 1e-6 and abs(s - C[d_, ms]) < 1e-6, (j, texte)
            lignes.append((d_, me, ms, sens, str(pd.Timestamp(j).date())))
    Z = pd.DataFrame(lignes, columns=["d", "me", "ms", "sens", "jour"]).sort_values(["d", "me"]).reset_index(drop=True)
    # RSI(2) : minute de decision, position voulue apres la decision, prix d'execution
    derniere = N - 1 - np.argmax(P[:, ::-1], axis=1)
    dec = np.full(len(jours), -1, np.int64)
    voulu = np.zeros(len(jours), np.int64)
    idx = np.searchsorted(jours, r.index)
    dec[idx] = derniere[idx] - 9
    voulu[idx] = r["pos_rsi2"].to_numpy()
    assert np.allclose(O[idx, dec[idx]], r["prix_rsi2"].to_numpy())
    # position voulue a l'ouverture de chaque seance (pour choisir les departs : RSI(2) a plat)
    tenu, ouvert = 0, np.zeros(len(jours), np.int64)
    for d_ in range(len(jours)):
        ouvert[d_] = tenu
        if dec[d_] >= 0:
            tenu = voulu[d_]
    return jours, O, H, L, C, Z, dec, voulu, ouvert


@njit(cache=True)
def jouer(debut, nmax, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu, ouvert,
          objectif, perte, mode, blocage, dll, regul, jmin, prot_b, prot_c, prot_d,
          coupe, stop_rsi, plafond, frais_zone, frais_rsi, glisse):
    """Un challenge qui commence a la seance `debut`. Renvoie (issue, derniere seance, seances jouees, marge mini,
    valeur du compte a la fin) ; issue : 1 reussi, -1 perdu, 0 pas fini."""
    nj = O.shape[0]
    cash, zp, ze, rp, re = 0.0, 0, 0.0, 0, 0.0
    veut, bloque = ouvert[debut], False
    if veut == 1:
        bloque = True                     # trade du RSI(2) deja en cours avant le depart : on ne le prend pas
    pic_rt, pic_eod, veille = 0.0, 0.0, 0.0
    plancher = -perte
    meilleur, qualif, marge = -1e18, 0, 1e18
    fin = min(nj, debut + nmax)
    for d in range(debut, fin):
        arret = False
        k = z_deb[d]
        actif = -1                        # indice du trade de zone en cours
        for t in range(O.shape[1]):
            # 1. decision du RSI(2) a l'ouverture de la minute
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
            # 2. valeur du compte dans la minute
            n = zp + rp
            a = cash - 2.0 * (zp * ze + rp * re)
            ouv = a + 2.0 * n * O[d, t]
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
                if blocage == blocage and plancher > blocage:      # blocage defini (pas NaN)
                    plancher = blocage
            dur = plancher
            if dll > 0.0 and veille - dll > dur:
                dur = veille - dll
            # 3. plafond du jour (le plus haut avant le plus bas)
            if prot_d == 1 and n != 0 and hautv >= veille + plafond:
                x = veille + plafond if ouv < veille + plafond else ouv
                cash = x - (frais_zone if zp != 0 else 0.0) - (frais_rsi if rp != 0 else 0.0) - glisse * abs(zp) - glisse * rp
                zp, rp, arret = 0, 0, True
                if actif >= 0:
                    actif = -2
                n, a, basv = 0, cash, cash
            # 4. stop du RSI(2)
            if prot_c == 1 and rp == 1 and L[d, t] <= re - stop_rsi / 2.0:
                px = re - stop_rsi / 2.0 if O[d, t] > re - stop_rsi / 2.0 else O[d, t]
                cash += (px - re) * 2.0 - frais_rsi - glisse
                rp, bloque = 0, True
                n = zp
                a = cash - 2.0 * zp * ze
                ouv = a + 2.0 * n * O[d, t]
                if n > 0:
                    basv = a + 2.0 * n * L[d, t]
                elif n < 0:
                    basv = a + 2.0 * n * H[d, t]
                else:
                    basv = a
            # 5. coupe-circuit, puis limite du compte
            if prot_b == 1 and n != 0 and basv <= dur + coupe:
                x = dur + coupe if ouv > dur + coupe else ouv
                cash = x - (frais_zone if zp != 0 else 0.0) - (frais_rsi if rp != 0 else 0.0) - glisse * abs(zp) - glisse * rp
                zp, rp, arret = 0, 0, True
                if actif >= 0:
                    actif = -2
                basv = cash
            if basv - dur < marge:
                marge = basv - dur
            if basv <= dur:
                return -1, d, d - debut + 1, marge, basv
            # 6. zone a la cloture de la minute : sortie puis entree
            if actif >= 0 and z_ms[actif] == t:
                cash += zp * (C[d, t] - ze) * 2.0 - frais_zone
                zp, actif = 0, -1
            while k < z_fin[d] and z_me[k] < t:
                k += 1
            if k < z_fin[d] and z_me[k] == t:
                if not arret and z_garde[k] == 1 and zp == 0:
                    zp, ze, actif = z_sens[k], C[d, t], k
                k += 1
        # fin de seance
        eod = cash + rp * (C[d, O.shape[1] - 1] - re) * 2.0
        g = eod - veille
        veille = eod
        if g > meilleur:
            meilleur = g
        if g >= 200.0:
            qualif += 1
        if mode == 0:
            if eod > pic_eod:
                pic_eod = eod
            plancher = pic_eod - perte
            if blocage == blocage and plancher > blocage:
                plancher = blocage
        if eod >= objectif and qualif >= jmin and (regul == 0.0 or meilleur <= regul * eod):
            return 1, d, d - debut + 1, marge, eod
    return 0, fin - 1, fin - debut, marge, veille


def tableaux_zone(Z, nj, garde):
    z_deb = np.searchsorted(Z["d"].to_numpy(), np.arange(nj)).astype(np.int64)
    z_fin = np.searchsorted(Z["d"].to_numpy(), np.arange(nj), side="right").astype(np.int64)
    return (z_deb, z_fin, Z["me"].to_numpy(np.int64), Z["ms"].to_numpy(np.int64), Z["sens"].to_numpy(np.int64),
            garde.astype(np.int64))


def lancer(departs, base, compte, prot, nmax=MAX_SEANCES):
    O, H, L, C, zt, dec, voulu, ouvert = base
    obj, perte, mode, blocage, dll, regul, jmin = compte
    pb, pc, pd_ = prot
    out = []
    for d in departs:
        out.append(jouer(int(d), nmax, O, H, L, C, *zt, dec, voulu, ouvert, obj, perte, mode,
                         np.nan if blocage is None else blocage, dll, regul, jmin, pb, pc, pd_,
                         COUPE, STOP_RSI, PLAFOND, FRAIS_ZONE, FRAIS_RSI, GLISSE))
    return pd.DataFrame(out, columns=["issue", "fin", "seances", "marge", "valeur"], index=departs)


def bilan(res):
    n = len(res)
    reussi, perdu = (res["issue"] == 1).mean(), (res["issue"] == -1).mean()
    med = res.loc[res["issue"] == 1, "seances"].median()
    return {"departs": n, "reussis": round(100 * reussi, 1), "perdus": round(100 * perdu, 1),
            "pas_finis": round(100 * (1 - reussi - perdu), 1), "score": round(100 * (reussi - perdu), 1),
            "seances_mediane": None if np.isnan(med) else int(med)}


def main():
    jours, O, H, L, C, Z, dec, voulu, ouvert = donnees()
    nj = len(jours)
    filtre = pd.read_csv(R0 / "orderflow/zone_avril_septembre_2026.csv")
    g = {(r.jour, int(r.minute), int(r.sens)): bool(r.garde) for r in filtre.itertuples()}
    cle = list(zip(Z["jour"], Z["me"], Z["sens"]))
    garde_vrai = np.array([g.get(c, True) for c in cle])
    manque = [c for c in cle if "2026-04-01" <= c[0] <= FIN_DONNEES and c not in g]
    base_long = (O, H, L, C, tableaux_zone(Z, nj, np.ones(len(Z), bool)), dec, voulu, ouvert)
    base_2026 = (O, H, L, C, tableaux_zone(Z, nj, garde_vrai), dec, voulu, ouvert)
    dates = pd.DatetimeIndex(jours)
    L_ = [f"Protections du bot 3 en 1, minute par minute ; {nj} seances du {dates[0].date()} au {dates[-1].date()} ;"
          f" trades de zone 2026 sans decision du filtre : {len(manque)}", ""]
    # controle : sans compte (perte infinie), avril - 25 septembre 2026, filtre vrai -> total du rejeu journalier
    d0 = int(np.searchsorted(dates, pd.Timestamp("2026-04-01")))
    sans = (1e12, 1e12, 0, None, 0.0, 0.0, 0)
    ctrl = lancer([d0], base_2026, sans, PROTECTIONS["A"], nmax=nj)
    L_.append(f"controle : avril - 25 septembre 2026, vrai delta, sans protection : {ctrl['valeur'].iloc[0]:+,.1f} $"
              f" (rejeu journalier : +4 366 $)")
    ctrl_long = lancer([int(np.searchsorted(dates, pd.Timestamp("2023-01-03")))], base_long, sans, PROTECTIONS["A"], nmax=nj)
    L_.append(f"controle : 2023 - 25 septembre 2026, zone non filtree + RSI(2) : {ctrl_long['valeur'].iloc[0]:+,.1f} $")
    res_json = {}
    # departs : une seance sur cinq, RSI(2) a plat a l'ouverture, apres 260 seances d'historique
    possibles = [d for d in range(260, nj) if ouvert[d] == 0]
    departs = possibles[::PAS_DEPART]
    expl = [d for d in departs if dates[d] <= pd.Timestamp("2022-12-31")]
    coffre = [d for d in departs if dates[d] >= pd.Timestamp("2023-01-01")]
    for nom, compte in COMPTES.items():
        L_ += ["", f"=== {nom} ===", "protection | 2011-2022 : reussis / perdus / pas finis / score / seances mediane |"
               " 2023-2026 : idem"]
        res_json[nom] = {}
        prots = [p for p in PROTECTIONS if "D" not in p or nom.startswith("DayTraders")]
        for p in prots:
            a, b = bilan(lancer(expl, base_long, compte, PROTECTIONS[p])), bilan(lancer(coffre, base_long, compte, PROTECTIONS[p]))
            res_json[nom][p] = {"2011-2022": a, "2023-2026": b}
            L_.append(f"{p:6s} | {a['reussis']:5.1f} / {a['perdus']:5.1f} / {a['pas_finis']:5.1f} / {a['score']:+6.1f} /"
                      f" {a['seances_mediane']} | {b['reussis']:5.1f} / {b['perdus']:5.1f} / {b['pas_finis']:5.1f} /"
                      f" {b['score']:+6.1f} / {b['seances_mediane']}")
        if "descriptif" in nom:
            continue
        sA = res_json[nom]["A"]["2011-2022"]["score"]
        cand = [(res_json[nom][p]["2011-2022"]["score"], p) for p in prots if p != "A"
                and res_json[nom][p]["2011-2022"]["score"] >= sA + 3]
        choix = max(cand)[1] if cand else "A"
        verif = choix == "A" or res_json[nom][choix]["2023-2026"]["score"] >= res_json[nom]["A"]["2023-2026"]["score"]
        retenu = choix if verif else "A"
        res_json[nom]["retenu"] = retenu
        L_.append(f"-> choix sur 2011-2022 : {choix} ; verification 2023-2026 : {'oui' if verif else 'non'} ; RETENU : {retenu}")
    # descriptif : avril - septembre 2026 avec le vrai delta
    L_ += ["", "=== Avril - 25 septembre 2026, vrai delta (descriptif) ==="]
    debuts_mois = [next(d for d in range(nj) if dates[d].month == m and dates[d].year == 2026 and ouvert[d] == 0)
                   for m in range(4, 10)]
    tous = [d for d in range(d0, nj) if ouvert[d] == 0]
    res_json["2026"] = {}
    for nom, compte in COMPTES.items():
        if "descriptif" in nom:
            continue
        prots = [p for p in PROTECTIONS if "D" not in p or nom.startswith("DayTraders")]
        for p in prots:
            r1 = lancer(debuts_mois, base_2026, compte, PROTECTIONS[p], nmax=nj)
            r2 = bilan(lancer(tous, base_2026, compte, PROTECTIONS[p], nmax=nj))
            txt = " ; ".join(f"{dates[d].strftime('%d/%m')} {'reussi' if x.issue == 1 else ('PERDU' if x.issue == -1 else 'en cours')}"
                             f" {dates[int(x.fin)].strftime('%d/%m')}" for d, x in r1.iterrows())
            L_.append(f"{nom} {p} | 1er du mois : {txt} | chaque seance ({r2['departs']}) : reussis {r2['reussis']} %,"
                      f" perdus {r2['perdus']} %")
            res_json["2026"][f"{nom} {p}"] = {"premiers": {str(dates[d].date()): [int(x.issue), str(dates[int(x.fin)].date())]
                                                        for d, x in r1.iterrows()}, "chaque_seance": r2}
    (ICI / "resultats.txt").write_text("\n".join(L_) + "\n")
    (ICI / "resultats.json").write_text(json.dumps(res_json, indent=1, ensure_ascii=False))
    print("\n".join(L_))


if __name__ == "__main__":
    main()
