#!/usr/bin/env python3
"""Machine v6 (audit/machine6/REGLES.md) : donnees et simulateur de challenge Bulenox minute par minute.

Deux regles de compte :
- "option1" : plancher = min(plus haut latent - 2 500, 50 100), suivi minute par minute (gains ouverts compris) ;
- "fin_de_jour" : plus haut = solde de cloture (regle supposee dans l'audit), sert a verifier le simulateur.
"""
import re
from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

N = 390
PAS = 30
FRAIS = 3.0
GLISSE_LIMITE = 1.0
TICK = 0.25
LIGNE = re.compile(r"^(\d{4}-\d{2}-\d{2}) (achat|vente|sortie|stop)\b(?: (\d+)h(\d+))?(?: (\d+)h(\d+))?.*? a ([0-9.]+)")
DEP = re.compile(r"\[depassement ([0-9.]+)\]")


def charger(minutes_csv, trades_txt, cache=None):
    if cache and Path(cache).exists():
        return dict(np.load(cache, allow_pickle=True))
    d = pd.read_csv(minutes_csv, usecols=["t", "o", "h", "l", "c"])
    jour = d["t"].str[:10]
    m = d["t"].str[11:13].astype(int) * 60 + d["t"].str[14:16].astype(int) - 570
    garde = (m >= 0) & (m < N)
    d, jour, m = d[garde], jour[garde], m[garde]
    jours = np.array(sorted(jour.unique()))
    idx = pd.Index(jours).get_indexer(jour)
    nj = len(jours)
    A = {}
    for col in "ohlc":
        a = np.full((nj, N), np.nan)
        a[idx, m.to_numpy()] = d[col].to_numpy(float)
        A[col] = a
    present = ~np.isnan(A["c"])
    C = pd.DataFrame(A["c"]).ffill(axis=1).bfill(axis=1).to_numpy()
    O, H, L = [np.where(np.isnan(A[k]), C, A[k]) for k in "ohl"]
    complete = present[:, 0] & present[:, N - 1] & (present.sum(1) >= 370)
    o0 = O[:, 0]
    veille = np.full(nj, np.nan)
    mv = np.abs(C[:, PAS::PAS][:, :12] / o0[:, None] - 1)
    sigma = np.full((nj, 12), np.nan)
    comp = np.where(complete)[0]
    for i in range(nj):
        prec = comp[comp < i]
        if len(prec):
            veille[i] = C[prec[-1], N - 1]
        if len(prec) >= 14:
            sigma[i] = mv[prec[-14:]].mean(0)
    sig_jour = np.nanmean(sigma, 1)
    med = pd.Series(sig_jour).rolling(250, min_periods=120).median().shift(1).to_numpy()
    ref_h = np.fmax(o0, veille)
    gap = np.abs(o0 - veille) / (ref_h * sigma[:, 0])
    # trades du bot (rejeu)
    T = []
    ouvert = None
    pos_jour = {j: i for i, j in enumerate(jours)}
    for l in Path(trades_txt).read_text().splitlines():
        g = LIGNE.match(l)
        if not g or "ecarte" in l:
            continue
        j, quoi = g.group(1), g.group(2)
        h, mi = int(g.group(5) or g.group(3)), int(g.group(6) or g.group(4))
        mm, prix = h * 60 + mi - 570, float(g.group(7))
        if quoi in ("achat", "vente"):
            dp = DEP.search(l)
            ouvert = (j, 1 if quoi == "achat" else -1, mm, prix, float(dp.group(1)) if dp else 0.0)
        elif ouvert:
            jj, s, me, e, dep = ouvert
            di = pos_jour[jj]
            k = me // PAS - 1
            ref = ref_h[di] if s > 0 else np.fmin(o0[di], veille[di])
            w = ref * sigma[di, k]
            T.append((di, s, me, mm, e, prix, dep, w, ref + s * w, k))
            ouvert = None
    T = np.array(T, float)
    out = dict(jours=jours, O=O, H=H, L=L, C=C, complete=complete, sigma=sigma, sig_jour=sig_jour, med=med, gap=gap,
               t_jour=T[:, 0].astype(np.int64), t_sens=T[:, 1].astype(np.int64), t_me=T[:, 2].astype(np.int64),
               t_mx=T[:, 3].astype(np.int64), t_e=T[:, 4], t_x=T[:, 5], t_dep=T[:, 6], t_w=T[:, 7], t_niv=T[:, 8],
               t_k=T[:, 9].astype(np.int64))
    if cache:
        np.savez(cache, **out)
    return out


# parametres de gestion (vecteur float) : indices
P_T, P_L, P_G, P_S, P_P, P_B, P_R, P_N, P_J, P_O, P_PESS, P_GLISSE, P_EOD, P_PREF = range(14)


@nb.njit(cache=True)
def fenetre(debut, nseances, prm, solde0, haut0, O, H, L, C, jt_debut, jt_fin, t_sens, t_me, t_mx, t_e, t_x, t_w, t_niv,
            pris, objectif, perte_max, blocage, jour_depuis):
    """Un challenge de nseances depuis la seance `debut`. Renvoie (issue, solde final, seance de fin) ;
    issue : 1 reussi, -1 echoue, 0 ni l'un ni l'autre, 9 pas assez de seances."""
    T = prm[P_T]; Lim = prm[P_L]; G = prm[P_G]; S = prm[P_S]; Pt = prm[P_P]; B = prm[P_B]; R = prm[P_R]
    NMAX = prm[P_N]; J = prm[P_J]; Oj = prm[P_O]; pess = prm[P_PESS] > 0; gl = prm[P_GLISSE]; eod = prm[P_EOD] > 0
    pref = prm[P_PREF]
    solde = solde0
    haut = haut0
    nj = O.shape[0]
    for q in range(nseances):
        d = debut + q
        if d >= nj:
            return 9, solde, q
        plancher = min(haut - perte_max, depart_bloque(blocage))
        lim = Lim
        if G > 0:
            lim = min(lim, solde - plancher - G)
            if lim < 50:
                if eod:
                    haut = max(haut, solde)
                continue
        jour_val = 0.0
        arret = False
        ntr = 0
        for i in range(jt_debut[d], jt_fin[d]):
            if arret:
                break
            if not pris[i]:
                continue
            if NMAX > 0 and ntr >= NMAX:
                break
            ntr += 1
            s = t_sens[i]; e = t_e[i]; w = t_w[i]; k = pref / e
            stop = -1e18 if s > 0 else 1e18
            if S > 0:
                stop = t_niv[i] - s * S * w
            cible = 1e18 if s > 0 else -1e18
            if Pt > 0:
                cible = e + s * Pt * w
            gmax = 0.0
            be = False
            sortie = t_x[i]
            fin_mx = t_mx[i]
            sorti = False
            for m in range(t_me[i] + 1, t_mx[i] + 1):
                o = O[d, m]; hh = H[d, m]; ll = L[d, m]; cc = C[d, m]
                fav = hh if s > 0 else ll
                adv = ll if s > 0 else hh
                if pess and not eod:
                    v_fav = solde + jour_val + T * (2 * s * (fav - e) * k - FRAIS)
                    if v_fav > haut:
                        haut = v_fav
                        plancher = min(haut - perte_max, depart_bloque(blocage))
                # stops du trade (cote defavorable d'abord)
                st = stop
                if be and ((s > 0 and e > st) or (s < 0 and e < st)):
                    st = e
                if (s > 0 and adv <= st) or (s < 0 and adv >= st):
                    sortie = (min(o, st) - TICK - gl) if s > 0 else (max(o, st) + TICK + gl)
                    sorti = True
                # plancher et limite du jour sur le pire prix de la minute
                pire = adv if not sorti else sortie
                v_adv = solde + jour_val + T * (2 * s * (pire - e) * k - FRAIS)
                if v_adv <= plancher:
                    return -1, v_adv, q
                if jour_val + T * (2 * s * (pire - e) * k - FRAIS) <= -lim:
                    niveau = e + s * ((-lim - jour_val) / T + FRAIS) / (2 * k)
                    sortie = (min(o, niveau) - GLISSE_LIMITE - gl) if s > 0 else (max(o, niveau) + GLISSE_LIMITE + gl)
                    sorti = True
                    arret = True
                if sorti:
                    break
                # objectif du trade (cote favorable)
                if (s > 0 and fav >= cible) or (s < 0 and fav <= cible):
                    sortie = max(o, cible) if s > 0 else min(o, cible)
                    sorti = True
                g_lat = s * (fav - e)
                if g_lat > gmax:
                    gmax = g_lat
                if not pess and not eod:
                    v_fav = solde + jour_val + T * (2 * s * ((sortie if sorti else fav) - e) * k - FRAIS)
                    if v_fav > haut:
                        haut = v_fav
                        plancher = min(haut - perte_max, depart_bloque(blocage))
                if sorti:
                    break
                v_cl = jour_val + T * (2 * s * (cc - e) * k - FRAIS)
                # objectif du challenge (a la cloture de la minute, comme le bot)
                if not eod and solde + v_cl >= objectif + 50:
                    return 1, solde + v_cl, q
                if Oj > 0 and v_cl >= Oj:
                    sortie = cc - s * gl
                    sorti = True
                    arret = True
                    break
                if B > 0 and gmax >= B * w:
                    be = True
                if R > 0 and gmax >= R * w and s * (cc - e) <= 0.5 * gmax:
                    sortie = cc - s * gl
                    sorti = True
                    break
            if not sorti:
                sortie = sortie - s * gl
            r = T * (2 * s * (sortie - e) * k - FRAIS)
            jour_val += r
            if not eod and solde + jour_val >= objectif + 50:
                return 1, solde + jour_val, q
            if J > 0 and r > 0:
                arret = True
            if Oj > 0 and jour_val >= Oj:
                arret = True
        solde += jour_val
        if eod:
            if solde >= objectif:
                return 1, solde, q
            haut = max(haut, solde)
    return 0, solde, nseances


@nb.njit(cache=True)
def depart_bloque(blocage):
    return blocage


@nb.njit(cache=True)
def lot(debuts, nseances, prm, solde0, haut0, O, H, L, C, jt_debut, jt_fin, t_sens, t_me, t_mx, t_e, t_x, t_w, t_niv,
        pris, objectif, perte_max, blocage):
    res = np.zeros(len(debuts), np.int64)
    for z in range(len(debuts)):
        res[z] = fenetre(debuts[z], nseances, prm, solde0, haut0, O, H, L, C, jt_debut, jt_fin, t_sens, t_me, t_mx, t_e,
                         t_x, t_w, t_niv, pris, objectif, perte_max, blocage, 0)[0]
    return res


@nb.njit(cache=True)
def journees(prm, O, H, L, C, jt_debut, jt_fin, t_sens, t_me, t_mx, t_e, t_x, t_w, t_niv, pris, nj):
    """Resultat de chaque seance (sans compte : pas de plancher ni d'objectif), pour le t des journees (controle 4)."""
    out = np.zeros(nj)
    big = 1e12
    for d in range(nj):
        # une fenetre d'une seance, solde enorme : seuls la gestion et la limite du jour jouent
        prm2 = prm.copy()
        r = fenetre(d, 1, prm2, big, big, O, H, L, C, jt_debut, jt_fin, t_sens, t_me, t_mx, t_e, t_x, t_w, t_niv, pris,
                    1e18, 1e15, -1e18, 0)
        out[d] = r[1] - big
    return out
