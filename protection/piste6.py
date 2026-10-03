#!/usr/bin/env python3
"""Piste 6 (README.md) : une 4e source ajoutee au bot (zone non filtree + RSI(2), 1 MNQ chacun) : tendance seule (T100,
T30, robot de tendance en contrats micro entiers) ou veille de la Fed (F, 1 MES). Leur gain du jour entre au solde a la
cloture. Jugement sur le challenge DayTraders Trail 50K ; descriptif : S2F 50K + plafond 500 $ et Trail puis Pro.
Ecrit piste6.txt et piste6.json. Lancer depuis ce dossier : python3 piste6.py"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

import protection as P

ICI = Path(__file__).resolve().parent
R0 = ICI.parent
sys.path.insert(0, str(R0 / "tendance"))
sys.path.insert(0, str(R0 / "fonds"))


# ----------------------------------------------------------------------------- les candidates, en $ par seance
def tendance(jours, echelle):
    """Gain du jour du robot de tendance (tendance/systeme.py, contrats entiers pour 50 000 $, 12 %/an) a l'echelle
    donnee de sa grille, recu le jour t+1 pour les positions fixees le vendredi."""
    import challenge_phidias as CP
    import systeme as S
    r, R, cvv, semaines, N, _, _ = CP.preparer(S.MARCHES, 0.12)
    e = int(np.argmin(np.abs(CP.ECHELLES - echelle)))
    idx = {t: j for j, t in enumerate(semaines)}
    n = np.zeros(R.shape[1])
    gain = np.zeros(len(R))
    for t in range(len(R) - 1):
        if t in idx and t >= 260:
            cible = N[e, idx[t]]
            gain[t + 1] -= np.abs(cible - n).sum() * CP.FRAIS
            n = cible
        gain[t + 1] += float((n * cvv * R[t + 1]).sum())
    s = pd.Series(gain, index=pd.DatetimeIndex(r.index).normalize())
    s = s.groupby(level=0).sum()
    return s.reindex(pd.DatetimeIndex(jours)).fillna(0.0).to_numpy()   # jour sans seance NQ : pas de gain compte


def veille_fed(jours):
    """1 MES de 14 h la veille d'une annonce programmee a 13 h 55 le jour de l'annonce (12 h en 2011-2012)."""
    import fomc
    d = pd.read_csv(R0 / "intraday/donnees/sp500_1min.csv.gz")
    d = d[d["t"].str[:10] <= P.FIN_DONNEES]
    J, O, H, L, C, Pp, V, ech = P.RB.tableaux(d)
    J = pd.DatetimeIndex(J)
    contrat = d.groupby(pd.to_datetime(d["t"].str[:10]))["contrat"].last().reindex(J).to_numpy()
    annonces = set(pd.DatetimeIndex(fomc.annonces()).normalize())
    gain = pd.Series(0.0, index=J)
    pt, frais = 5.0, 0.9
    for i in range(1, len(J)):
        if J[i] not in annonces:
            continue
        a, b = i - 1, i
        fin = 150 if J[b].year <= 2012 else 265
        if (J[b] - J[a]).days > 4 or Pp[a].sum() < 300 or Pp[b].sum() < 300 or contrat[a] != contrat[b]:
            continue
        p0, c0, p1 = C[a, 270], C[a, P.N - 1], C[b, fin]
        gain[J[a]] += (c0 - p0) * pt
        gain[J[b]] += (p1 - c0 - frais) * pt
    return gain.reindex(pd.DatetimeIndex(jours)).fillna(0.0).to_numpy()


# ----------------------------------------------------------------------------- moteur (piste5.seance5 + gain externe)
@njit(cache=True)
def seance6(d, etat, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu,
            perte, mode, blocage, frais_zone, frais_rsi, plafond, dll_douce, extra):
    cash, zp, ze, rp, re = etat[0], int(etat[1]), etat[2], int(etat[3]), etat[4]
    veut, bloque, pic_rt, plancher, veille = int(etat[5]), etat[6] > 0, etat[8], etat[9], etat[10]
    k = z_deb[d]
    actif = -1
    arret = False
    glisse = 0.5
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
        if plafond > 0.0 and n != 0 and hautv >= veille + plafond:
            x = veille + plafond if ouv < veille + plafond else ouv
            cash = x - (frais_zone if zp != 0 else 0.0) - (frais_rsi if rp != 0 else 0.0) - glisse * (abs(zp) + rp)
            zp, rp, arret = 0, 0, True
            if actif >= 0:
                actif = -2
            basv = cash
        if dll_douce > 0.0 and n != 0 and basv <= veille - dll_douce:
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
    cash += extra                                         # 4e source : gain du jour a la cloture
    eod = cash + rp * (C[d, nmin - 1] - re) * 2.0
    if mode == 1 and eod > pic_rt:
        pic_rt = eod
    if eod <= plancher:
        return 1, eod
    etat[0], etat[1], etat[2], etat[3], etat[4] = cash, zp, ze, rp, re
    etat[5], etat[6], etat[8], etat[9] = veut, 1.0 if bloque else 0.0, pic_rt, plancher
    return 0, eod


@njit(cache=True)
def nouvel_etat(ouvert, d, perte):
    etat = np.zeros(11)
    etat[5] = ouvert[d]
    etat[6] = 1.0 if ouvert[d] == 1 else 0.0
    etat[9] = -perte
    return etat


@njit(cache=True)
def trail(debut, nmax, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu, ouvert, extra, fz, fr):
    """Challenge DayTraders Trail 50K. Renvoie (issue, derniere seance)."""
    etat = nouvel_etat(ouvert, debut, 2500.0)
    meilleur, qualif = -1e18, 0
    fin = min(O.shape[0], debut + nmax)
    for d in range(debut, fin):
        perdu, eod = seance6(d, etat, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu,
                             2500.0, 1, 0.0, fz, fr, 0.0, 0.0, extra[d])
        if perdu:
            return -1, d
        g = eod - etat[10]
        etat[10] = eod
        meilleur = max(meilleur, g)
        if g >= 200.0:
            qualif += 1
        if eod >= 3000.0 and qualif >= 2 and meilleur <= 0.5 * eod:
            return 1, d
    return 0, fin - 1


@njit(cache=True)
def pro(debut, nmax, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu, ouvert, extra, fz, fr):
    """Compte Pro DayTraders (piste 2). Renvoie (perdu, retraits, recu)."""
    etat = nouvel_etat(ouvert, debut, 2500.0)
    base, meilleur, qualif, nret, recu = 0.0, -1e18, 0, 0, 0.0
    fin = min(O.shape[0], debut + nmax)
    for d in range(debut, fin):
        perdu, eod = seance6(d, etat, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu,
                             2500.0, 1, 0.0, fz, fr, 0.0, 0.0, extra[d])
        if perdu:
            return 1, nret, recu
        g = eod - etat[10]
        etat[10] = eod
        meilleur = max(meilleur, g)
        if g >= 200.0:
            qualif += 1
        gain = eod - base
        if qualif >= 8 and gain > 0.0 and meilleur <= 0.3 * gain and eod >= 1500.0:
            x = min(2000.0, eod - 1000.0)
            etat[0] -= x
            etat[10] -= x
            recu += x
            nret += 1
            base, meilleur, qualif = etat[10], -1e18, 0
    return 0, nret, recu


@njit(cache=True)
def s2f(debut, nmax, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu, ouvert, extra, fz, fr):
    """S2F 50K avec plafond 500 $ (piste 5, descriptif). Renvoie (perdu, retraits, recu)."""
    etat = nouvel_etat(ouvert, debut, 2500.0)
    pic_eod, base, meilleur, qualif, nret, recu = 0.0, 0.0, -1e18, 0, 0, 0.0
    fin = min(O.shape[0], debut + nmax)
    for d in range(debut, fin):
        perdu, eod = seance6(d, etat, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu,
                             2500.0, 0, 0.0, fz, fr, 500.0, 1250.0, extra[d])
        if perdu:
            return 1, nret, recu
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
            base, meilleur, qualif = etat[10], -1e18, 0
    return 0, nret, recu


@njit(cache=True)
def gains_du_bot(O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu, ouvert, fz, fr):
    """Gain de chaque seance du bot seul, sans compte (pour les correlations)."""
    etat = nouvel_etat(ouvert, 260, 1e12)
    out = np.zeros(O.shape[0])
    for d in range(260, O.shape[0]):
        _, eod = seance6(d, etat, O, H, L, C, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu,
                         1e12, 0, 0.0, fz, fr, 0.0, 0.0, 0.0)
        out[d] = eod - etat[10]
        etat[10] = eod
    return out


def main():
    jours, O, H, L, C, Z, dec, voulu, ouvert = P.donnees()
    nj = len(jours)
    dates = pd.DatetimeIndex(jours)
    zt = P.tableaux_zone(Z, nj, np.ones(len(Z), bool))
    a = (O, H, L, C) + tuple(zt) + (dec, voulu, ouvert)
    fz, fr = P.FRAIS_ZONE, P.FRAIS_RSI
    cands = {"bot seul": np.zeros(nj), "+ T100 (tendance du robot)": tendance(jours, 1.0),
             "+ T30 (tendance a 0,3)": tendance(jours, 0.3), "+ F (veille de la Fed, 1 MES)": veille_fed(jours)}
    bot = gains_du_bot(*a, fz, fr)
    possibles = [d for d in range(260, nj) if ouvert[d] == 0]
    departs = possibles[::P.PAS_DEPART]
    expl = [d for d in departs if dates[d] <= pd.Timestamp("2022-12-31")]
    coffre = [d for d in departs if dates[d] >= pd.Timestamp("2023-01-01")]
    complets = [d for d in possibles if dates[d] >= pd.Timestamp("2023-01-01") and d + P.MAX_SEANCES <= nj][::2]
    L_ = [f"Piste 6 : 4e source ajoutee au bot ; {nj} seances du {dates[0].date()} au {dates[-1].date()}", "",
          "source | gain par an (1 unite) | correlation quotidienne avec le bot | Trail 2011-2022 : reussis / perdus / score |"
          " Trail 2023-2026 : idem | S2F + plafond 500 $ : recu en 12 mois / au moins un retrait | Trail puis Pro : recu en 12 mois"]
    res = {}
    for nom, x in cands.items():
        ans = (dates[-1] - dates[260]).days / 365.25
        par_an = x[260:].sum() / ans
        actifs = (x != 0) & (np.arange(nj) >= 260)
        corr = float(np.corrcoef(x[260:], bot[260:])[0, 1]) if x[260:].std() > 0 else float("nan")
        def bil(ds):
            r = np.array([trail(int(d), P.MAX_SEANCES, *a, x, fz, fr)[0] for d in ds])
            return round(100 * (r == 1).mean(), 1), round(100 * (r == -1).mean(), 1), round(100 * ((r == 1).mean() - (r == -1).mean()), 1)
        b1, b2 = bil(expl), bil(coffre)
        recu_s2f, ret_s2f, recu_pro = [], [], []
        for d in complets:
            p, nr, rc = s2f(int(d), P.MAX_SEANCES, *a, x, fz, fr)
            recu_s2f.append(rc - 57.0); ret_s2f.append(nr > 0)
            i, f = trail(int(d), P.MAX_SEANCES, *a, x, fz, fr)
            rp = pro(f + 1, d + P.MAX_SEANCES - f - 1, *a, x, fz, fr)[2] if i == 1 and f + 1 < d + P.MAX_SEANCES else 0.0
            recu_pro.append(rp - 75.0)
        res[nom] = {"par_an": par_an, "jours_actifs": int(actifs.sum()), "corr": corr, "trail_2011_2022": b1, "trail_2023_2026": b2,
                    "s2f_recu_12_mois": float(np.mean(recu_s2f)), "s2f_retrait": float(np.mean(ret_s2f)), "pro_recu_12_mois": float(np.mean(recu_pro))}
        L_.append(f"{nom} | {par_an:+,.0f} $ | {corr:+.2f} | {b1[0]} / {b1[1]} / {b1[2]:+.1f} | {b2[0]} / {b2[1]} / {b2[2]:+.1f} |"
                  f" {np.mean(recu_s2f):+,.0f} $ / {np.mean(ret_s2f):.0%} | {np.mean(recu_pro):+,.0f} $")
    base1, base2 = res["bot seul"]["trail_2011_2022"][2], res["bot seul"]["trail_2023_2026"][2]
    L_.append("")
    for nom in list(cands)[1:]:
        s1, s2 = res[nom]["trail_2011_2022"][2], res[nom]["trail_2023_2026"][2]
        ok = s1 >= base1 + 3 and s2 >= base2
        res[nom]["retenue"] = bool(ok)
        L_.append(f"-> {nom} : score 2011-2022 {s1:+.1f} contre {base1:+.1f}, 2023-2026 {s2:+.1f} contre {base2:+.1f} :"
                  f" {'RETENUE' if ok else 'PAS RETENUE'}")
    (ICI / "piste6.txt").write_text("\n".join(L_) + "\n")
    (ICI / "piste6.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("\n".join(L_))


if __name__ == "__main__":
    main()
