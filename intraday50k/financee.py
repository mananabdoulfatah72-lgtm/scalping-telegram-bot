#!/usr/bin/env python3
"""Phase financee des trois comptes en tete (README.md) : challenge puis compte finance, 12 mois apres l'achat.
Ecrit financee.txt et financee.json. Lancer depuis ce dossier : python3 financee.py"""
import json

import numpy as np
import pandas as pd
from numba import njit

import commun as K
import comptes as CP
import moteur as M

PT, GLISSE = M.PT, M.GLISSE
UN_AN = 252


@njit(cache=True)
def seance(d, avec_rsi, veut, cash, pic_rt, plancher, mode, perte, blocage, dll, O, H, L, C, der, z_deb, z_fin, z_me,
           z_ms, z_sens, z_garde, dec, voulu, NO, NH, NL, nn, frais_zone, frais_rsi):
    """Une seance (nuit + journee), meme logique que moteur.challenge. Renvoie (perdu, cash fin de seance, veut,
    pic_rt, plancher, au moins un trade)."""
    arret = False
    depart_jour = cash
    trade = False
    zp, ze, rp, re = 0, 0.0, 0, 0.0
    if avec_rsi == 1 and veut == 1:
        trade = True
        if nn[d] > 0:
            re = NO[d, 0]
            cash -= frais_rsi
            rp = 1
            for k in range(nn[d]):
                a = cash - PT * re
                hautv, basv = a + PT * NH[d, k], a + PT * NL[d, k]
                ouv = a + PT * NO[d, k]
                if mode == 1:
                    if hautv > pic_rt:
                        pic_rt = hautv
                    plancher = min(pic_rt - perte, blocage)
                if dll > 0.0 and basv <= depart_jour - dll:
                    x = depart_jour - dll if ouv > depart_jour - dll else ouv
                    cash = x - frais_rsi - GLISSE
                    rp = 0
                    arret = True
                    basv = cash
                if basv <= plancher:
                    return True, basv, veut, pic_rt, plancher, trade
                if arret:
                    break
        else:
            re = O[d, 0]
            cash -= frais_rsi
            rp = 1
    k = z_deb[d]
    actif = -1
    dmin = der[d]
    for t in range(dmin + 1):
        if t == dec[d]:
            if rp == 1 and voulu[d] == 0:
                cash += (O[d, t] - re) * PT - frais_rsi
                rp = 0
            veut = voulu[d]
        n = zp + rp
        a = cash - PT * (zp * ze + rp * re)
        ouv = a + PT * n * O[d, t]
        if n > 0:
            hautv, basv = a + PT * n * H[d, t], a + PT * n * L[d, t]
        elif n < 0:
            hautv, basv = a + PT * n * L[d, t], a + PT * n * H[d, t]
        else:
            hautv, basv = a, a
        if mode == 1:
            if hautv > pic_rt:
                pic_rt = hautv
            plancher = min(pic_rt - perte, blocage)
        if dll > 0.0 and n != 0 and basv <= depart_jour - dll:
            x = depart_jour - dll if ouv > depart_jour - dll else ouv
            cash = x - (frais_zone if zp != 0 else 0.0) - (frais_rsi if rp != 0 else 0.0) - GLISSE * (abs(zp) + rp)
            zp, rp, arret = 0, 0, True
            if actif >= 0:
                actif = -2
            basv = cash
        if basv <= plancher:
            return True, basv, veut, pic_rt, plancher, trade
        if actif >= 0 and z_ms[actif] == t:
            cash += zp * (C[d, t] - ze) * PT - frais_zone
            zp, actif = 0, -1
        while k < z_fin[d] and z_me[k] < t:
            k += 1
        if k < z_fin[d] and z_me[k] == t:
            if not arret and z_garde[k] == 1 and zp == 0:
                zp, ze, actif = z_sens[k], C[d, t], k
                trade = True
            k += 1
    if rp == 1:
        cash += (C[d, dmin] - re) * PT - frais_rsi
    if zp != 0:
        cash += zp * (C[d, dmin] - ze) * PT - frais_zone
    return False, cash, veut, pic_rt, plancher, trade


@njit(cache=True)
def parcours(debut, avec_rsi, O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu, NO, NH, NL, nn,
             e_obj, e_perte, e_mode, e_bloc, e_dll, e_regul, e_jmin, f_perte, f_bloc, f_dll, f_jours, f_seuil, f_regul,
             f_min, plafonds, f_part, f_reserve, f_max, frais_zone, frais_rsi):
    """Challenge puis compte finance, sur UN_AN seances apres l'achat. Renvoie (issue du challenge, seances du
    challenge, compte finance perdu, nombre de retraits, recu brut, seance du 1er retrait depuis l'achat (-1))."""
    nj = O.shape[0]
    fin = min(nj, debut + UN_AN)
    cash, veut, pic_rt, pic_eod, veille = 0.0, 0, 0.0, 0.0, 0.0
    plancher = -e_perte
    meilleur, jours = -1e18, 0
    issue, n_ch = 0, 0
    d = debut
    while d < fin:
        perdu, cash, veut, pic_rt, plancher, tr = seance(d, avec_rsi, veut, cash, pic_rt, plancher, e_mode, e_perte,
                                                          e_bloc, e_dll, O, H, L, C, der, z_deb, z_fin, z_me, z_ms,
                                                          z_sens, z_garde, dec, voulu, NO, NH, NL, nn, frais_zone, frais_rsi)
        if perdu:
            return -1, d - debut + 1, False, 0, 0.0, -1
        g = cash - veille
        veille = cash
        jours += 1
        if g > meilleur:
            meilleur = g
        if e_mode == 0:
            if cash > pic_eod:
                pic_eod = cash
            plancher = min(pic_eod - e_perte, e_bloc)
        d += 1
        if cash >= e_obj and jours >= e_jmin and (e_regul == 0.0 or meilleur <= e_regul * cash):
            issue, n_ch = 1, d - debut
            break
    if issue != 1:
        return 0, fin - debut, False, 0, 0.0, -1
    # compte finance : nouveau compte a 50 000 $ (0), le bot continue
    cash, pic_eod, veille, base = 0.0, 0.0, 0.0, 0.0
    plancher = -f_perte
    meilleur, qual, n, recu, premier = -1e18, 0, 0, 0.0, -1
    while d < fin:
        perdu, cash, veut, pic_rt, plancher, tr = seance(d, avec_rsi, veut, cash, 0.0, plancher, 0, f_perte, f_bloc,
                                                          f_dll, O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens,
                                                          z_garde, dec, voulu, NO, NH, NL, nn, frais_zone, frais_rsi)
        if perdu:
            return 1, n_ch, True, n, recu, premier
        g = cash - veille
        veille = cash
        if (f_seuil > 0.0 and g >= f_seuil) or (f_seuil == 0.0 and tr):
            qual += 1
        if g > meilleur:
            meilleur = g
        if cash > pic_eod:
            pic_eod = cash
        plancher = min(pic_eod - f_perte, f_bloc)
        d += 1
        gain = cash - base
        if qual >= f_jours and gain > 0.0 and (f_regul == 0.0 or meilleur <= f_regul * gain):
            plaf = plafonds[min(n, len(plafonds) - 1)]
            x = min(plaf, cash - f_reserve)
            if f_part > 0.0:
                x = min(x, f_part * cash)
            if x >= f_min:
                cash -= x
                veille = cash
                recu += x
                n += 1
                if premier < 0:
                    premier = d - debut
                base, meilleur, qual = cash, -1e18, 0
                if f_max > 0 and n >= f_max:
                    return 1, n_ch, False, n, recu, premier
    return 1, n_ch, False, n, recu, premier


# reglages de la phase financee (README.md) : perte, blocage, limite du jour, jours par cycle, seuil d'un jour (0 : un
# trade suffit), regularite, minimum, plafonds, part du gain du compte (0 : aucune), solde garde, retraits max,
# part du trader, cout (prix du challenge, mensuel ?, activation)
FINANCES = {
    "Bulenox option 2 (fin de journee)": dict(f=(2500.0, 100.0, 1100.0, 10, 0.0, 0.40, 1000.0,
                                               np.array([1500.0, 1500.0, 1500.0, 1e9]), 0.0, 2600.0, 3),
                                          part=1.0, prix=(175.0, True, 148.0)),
    "Topstep": dict(f=(2000.0, 0.0, 1000.0, 5, 150.0, 0.0, 125.0, np.array([2000.0]), 0.5, 0.0, 0),
                    part=0.9, prix=(49.0, True, 149.0)),
    "Tradeify Growth": dict(f=(2000.0, 100.0, 1250.0, 5, 150.0, 0.35, 500.0,
                               np.array([1500.0, 2000.0, 2500.0, 3000.0]), 0.0, 3000.0, 0),
                            part=0.9, prix=(145.0, False, 0.0)),
}


def main():
    D = K.charger()
    j = D["jours"]
    nj = len(j)
    def base(garde):
        return (D["O"], D["H"], D["L"], D["C"], D["derniere"], *K.P.tableaux_zone(D["Z"], nj, garde), D["dec"],
                D["voulu"], D["NO"], D["NH"], D["NL"], D["nn"])
    b0 = base(np.ones(len(D["Z"]), bool))
    possibles = [d for d in range(260, nj) if D["ouvert"][d] == 0]
    groupes = {"2023 - sept. 2025": [d for d in possibles if j[d].year >= 2023 and d + UN_AN <= nj][::2],
               "2025": [d for d in possibles if j[d].year == 2025 and d + UN_AN <= nj][::2],
               "2011-2022": [d for d in possibles if j[d].year <= 2022][::5]}
    # controle : l'issue du challenge de parcours() = moteur.challenge (memes departs)
    e = CP.COMPTES["Bulenox option 2 (fin de journee)"]
    f = FINANCES["Bulenox option 2 (fin de journee)"]["f"]
    dd = groupes["2023 - sept. 2025"]
    a = [parcours(d, 1, *b0, *e[:7], *f, K.P.FRAIS_ZONE, K.P.FRAIS_RSI)[0] for d in dd]
    bb = [M.challenge(d, UN_AN, 1, *b0, *e[:7], K.P.FRAIS_ZONE, K.P.FRAIS_RSI)[0] for d in dd]
    L = [f"Controle : issues du challenge de financee.py = moteur.py sur {len(dd)} departs : "
         f"{sum(int(x) == int(y) for x, y in zip(a, bb))}/{len(dd)}", ""]
    rho, gardes = CP.gardes_simules(D, nj)
    bases = {"sans filtre": [b0], "filtre simule (descriptif)": [base(g) for g in gardes]}
    res = {}
    L.append("compte | bot | zone | achats | challenge reussi | au moins un retrait en 12 mois | recu moyen en 12 mois"
             " (part du trader) | 1er retrait (mediane, seances apres l'achat) | compte finance perdu | cout moyen")
    for nc, fin_ in FINANCES.items():
        e = CP.COMPTES[nc]
        prix, mensuel, activation = fin_["prix"]
        for nb, r in CP.BOTS.items():
            for nz, bl in bases.items():
                for ng, dd in groupes.items():
                    if nz != "sans filtre" and ng == "2011-2022":
                        continue
                    R = pd.DataFrame([parcours(d, r, *bb, *e[:7], *fin_["f"], K.P.FRAIS_ZONE, K.P.FRAIS_RSI)
                                      for bb in bl for d in dd],
                                     columns=["issue", "seances", "perdu_f", "n", "recu", "premier"])
                    ok = R["issue"] == 1
                    mois = np.ceil(R["seances"] / 21.0) if mensuel else 1.0
                    cout = (prix * mois + np.where(ok, activation, 0.0)).mean()
                    x = {"achats": len(dd), "reussi": float(ok.mean()), "retrait": float((R["n"] > 0).mean()),
                         "recu": float((R["recu"] * fin_["part"]).mean()),
                         "premier": None if (R["premier"] >= 0).sum() == 0 else float(R.loc[R["premier"] >= 0, "premier"].median()),
                         "perdu_f": None if ok.sum() == 0 else float(R.loc[ok, "perdu_f"].mean()), "cout": float(cout)}
                    res[f"{nc} | {nb} | {nz} | {ng}"] = x
                    prem = "-" if x["premier"] is None else f"{x['premier']:.0f}"
                    pf = "-" if x["perdu_f"] is None else f"{x['perdu_f']:.0%}"
                    L.append(f"{nc} | {nb} | {nz} | {ng} | {x['reussi']:.0%} | {x['retrait']:.0%} | {x['recu']:+,.0f} $ |"
                             f" {prem} | {pf} | {x['cout']:,.0f} $")
    (K.ICI / "financee.txt").write_text("\n".join(L) + "\n")
    (K.ICI / "financee.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("\n".join(L))


if __name__ == "__main__":
    main()
