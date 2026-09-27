#!/usr/bin/env python3
"""Systeme de tendance multi-marches sur Phidias Premium 50K : version realiste.

- Univers limite aux contrats micro dont UN contrat ne peut pas perdre plus de ~1 500 $ sur une
  journee de krach (on retire MES, MNQ, MGC, SIL, MBT) ; l'or passe par le contrat 1 once (1OZ)
  si Phidias l'autorise (variante).
- Contrats entiers optimises (systeme.contrats_optimises), valeur des contrats d'aujourd'hui.
- Coussin : la taille baisse avec la marge restante ; une journee a 5 ecarts-types du portefeuille
  reel et le pire krach d'un seul marche doivent tenir dans la marge.
- Un challenge demarre chaque semaine depuis 2008, suivi 2 ans maximum.
"""
import numpy as np
import pandas as pd

import systeme as S

CAPITAL = 50_000
FRAIS = 3.25
KRACH = {"actions": .10, "obligations": .04, "devises": .04, "metaux": .08, "energie": .20, "crypto": .30}
ECHELLES = np.round(np.arange(0.1, 1.01, 0.1), 2)


def univers(avec_or_1oz=False):
    exclus = {"S&P 500", "Nasdaq 100", "Argent", "Bitcoin", "Or"}
    ms = [m for m in S.MARCHES if m.nom not in exclus]
    if avec_or_1oz:
        ms.append(S.Marche("Or", "metaux", "GLD", "GC=F", "1OZ", 1, 2.0))
    return ms


def preparer(marches, vol_visee):
    close, adj = S.charger()
    r = S.rendements_futures(close, adj, marches)
    _, pos, _ = S.backtest(r, marches=marches)
    cv = S.valeur_contrat(close, marches).iloc[-1]
    periode = r.index.to_period("W-FRI").asi8
    jours = np.where(np.r_[periode[:-1] != periode[1:], True])[0]
    grille = S.contrats_optimises(r, pos, cv, CAPITAL, vol_visee, ECHELLES, jours)
    N = np.stack([grille[e].values for e in ECHELLES])            # (echelles, semaines, marches)
    R = r.fillna(0).values
    cvv = cv[r.columns].values
    kr = np.array([KRACH[m.famille] for m in marches])
    sig = np.zeros(N.shape[:2]); pire = np.zeros(N.shape[:2])
    for j, t in enumerate(jours):
        if t < 260:
            continue
        cov = np.cov(R[t - 252:t + 1].T) * np.outer(cvv, cvv)
        for e in range(len(ECHELLES)):
            n = N[e, j]
            sig[e, j] = np.sqrt(max(n @ cov @ n, 0))
            pire[e, j] = np.max(np.abs(n) * cvv * kr) if n.any() else 0
    semaine = np.searchsorted(jours, np.arange(len(r)), side="left")   # semaine du jour t (re-equilibrage)
    return r, R, cvv, jours, N, sig, pire


def simuler(R, cvv, jours, N, sig, pire, debuts, horizon, finance=False, seuil=52_600, reserve=250.0):
    est_reeq = np.zeros(len(R), bool); est_reeq[jours] = True
    idx_sem = np.full(len(R), -1); idx_sem[jours] = np.arange(len(jours))
    nd = len(debuts)
    bal = np.full(nd, float(CAPITAL)); haut = bal.copy(); n = np.zeros((nd, R.shape[1]))
    etat = np.zeros(nd, int); jour = np.full(nd, np.nan)
    verse = np.zeros(nd); depart = bal.copy(); meilleur = np.zeros(nd); nb_ret = np.zeros(nd)
    g2 = 0.0; ng = 0
    for k in range(horizon):
        t = np.minimum(debuts + k, len(R) - 2)
        actif = (etat == 0) & (debuts + k < len(R) - 1)
        plancher = np.minimum(haut - 2500, CAPITAL + 100) if finance else haut - 2500
        marge = bal - plancher - reserve
        a_reeq = actif & est_reeq[t]
        if a_reeq.any():
            j = idx_sem[t]
            c = np.clip(marge / (2500 - reserve), 0, 1)
            # plus grande echelle permise par le coussin, le risque reel (5 sigma/jour) et le pire krach
            ok = (ECHELLES[:, None] <= c[None, :] + 1e-9) \
                & (5 * sig[:, j] / np.sqrt(S.JOURS_AN) <= marge[None, :]) & (pire[:, j] <= marge[None, :])
            e = np.where(ok.any(axis=0), len(ECHELLES) - 1 - np.argmax(ok[::-1], axis=0), -1)
            cible = np.where((e >= 0)[:, None], N[np.maximum(e, 0), j], 0)
            chg = np.abs(cible - n).sum(axis=1)
            n = np.where(a_reeq[:, None], cible, n)
            bal -= np.where(a_reeq, chg * FRAIS, 0)
        g = np.where(actif, (n * cvv * R[t + 1]).sum(axis=1), 0.0)
        bal += g; meilleur = np.maximum(meilleur, g)
        g2 += float((g[actif] ** 2).sum()); ng += int(actif.sum())
        plancher = np.minimum(haut - 2500, CAPITAL + 100) if finance else haut - 2500
        perdu = actif & (bal <= plancher)
        etat[perdu] = -1; actif &= ~perdu
        haut = np.where(actif, np.maximum(haut, bal), haut)
        if not finance:
            ok = actif & (bal >= CAPITAL + 4000)
            etat[ok] = 1; jour[ok] = k + 1
        elif k % 21 == 20:
            gain = bal - depart
            peut = actif & (bal > seuil) & (gain > 0) & (meilleur <= 0.30 * gain)
            w = np.where(peut, bal - seuil, 0.0)
            part = np.select([nb_ret < 1, nb_ret < 2, nb_ret < 3, nb_ret < 4], [.75, .80, .85, .90], 1.0)
            verse += part * w; bal -= w; nb_ret += peut
            depart = np.where(peut, bal, depart); meilleur = np.where(peut, 0.0, meilleur)
        n[etat != 0] = 0
    simuler.risque = np.sqrt(g2 / max(ng, 1)) * np.sqrt(S.JOURS_AN)
    return etat, jour, verse


def main():
    for avec_or in [False, True]:
        ms = univers(avec_or)
        for vv in [0.12, 0.16, 0.24]:
            r, R, cvv, jours, N, sig, pire = preparer(ms, vv)
            idx = r.index
            debuts = jours[(idx[jours] >= pd.Timestamp("2008-01-01"))] + 1
            debuts = debuts[debuts < len(idx) - 21]
            etat, jour, _ = simuler(R, cvv, jours, N, sig, pire, debuts, 504)
            complet = debuts + 504 <= len(idx)
            m = jour / 21
            titre = f"{len(ms)} marches{' + or 1OZ' if avec_or else ''}, vol visee {vv:.0%}"
            print(f"{titre}: evaluation reussie {np.mean(etat == 1):4.0%} (6 mois {np.mean((etat == 1) & (m <= 6)):4.0%},"
                  f" 12 mois {np.mean((etat == 1) & (m <= 12)):4.0%}) | perdue {np.mean(etat == -1):4.0%}"
                  f" | pas finie {np.mean(etat == 0):4.0%} (trop recentes {np.mean((etat == 0) & ~complet):4.0%})"
                  f" | mediane {np.nanmedian(m):4.1f} mois | risque reel {simuler.risque:,.0f} $/an")
            for a, b in [("2008", "2014"), ("2014", "2020"), ("2020", "2027")]:
                sel = (idx[debuts] >= pd.Timestamp(a)) & (idx[debuts] < pd.Timestamp(b))
                print(f"    departs {a}-{int(b) - 1}: reussie {np.mean(etat[sel] == 1):4.0%}, perdue {np.mean(etat[sel] == -1):4.0%}")
            df = debuts[debuts + 252 <= len(idx)]
            for seuil in [52_600, 55_000]:
                ef, _, verse = simuler(R, cvv, jours, N, sig, pire, df, 252, finance=True, seuil=seuil)
                print(f"    finance (retrait > {seuil:,} $): perdu en 1 an {np.mean(ef == -1):4.0%}, verse {verse.mean():6,.0f} $/an"
                      f" (mediane {np.median(verse):5,.0f} $, 1 compte sur 4 > {np.percentile(verse, 75):5,.0f} $)")
        print()


if __name__ == "__main__":
    main()
