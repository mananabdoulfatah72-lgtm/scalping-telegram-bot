#!/usr/bin/env python3
"""Zone de bruit sur 7 marches (regles fixees dans README.md) : resultat par marche, portefeuille a risque egal,
puis, si les criteres sont remplis, bot coussin de challenge 50K en contrats micro entiers.

Lancer depuis ce dossier : python3 analyse.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
R = ICI.parent
sys.path.insert(0, str(R / "challenge"))
FRAIS_ORDRE, JOURS_MOYENNE, PAS = 1.0, 14, 30
# nom : (fichier, $ par point, tick, debut et fin de seance en minutes depuis minuit, heure de New York)
MARCHES = {
    "NQ": (R / "intraday/donnees/nasdaq100_1min.csv.gz", 2.0, 0.25, 570, 960),
    "ES": (R / "intraday/donnees/sp500_1min.csv.gz", 5.0, 0.25, 570, 960),
    "RTY": (ICI / "donnees/russell_1min.csv.gz", 5.0, 0.10, 570, 960),
    "YM": (ICI / "donnees/dow_1min.csv.gz", 0.5, 1.0, 570, 960),
    "GC": (ICI / "donnees/or_1min.csv.gz", 10.0, 0.10, 500, 810),
    "CL": (ICI / "donnees/petrole_1min.csv.gz", 100.0, 0.01, 540, 870),
    "6E": (ICI / "donnees/euro_1min.csv.gz", 12500.0, 0.0001, 500, 900),
}
PERIODES_MARCHE = [("2011", "2016"), ("2016", "2020"), ("2020", "2027")]
PERIODES = [("2016", "2020"), ("2020", "2027")]      # portefeuille : periode commune (README, precision du 29 septembre)
DEBUT_COMMUN = "2016-01-01"


def charger(fichier, m0, m1):
    """Tableaux (seances x minutes de la seance), comme intraday/strategies.py charger."""
    n = m1 - m0
    d = pd.read_csv(fichier)
    t = pd.to_datetime(d["t"])
    minute = (t.dt.hour * 60 + t.dt.minute - m0).values
    garde = (minute >= 0) & (minute < n)
    d, t, minute = d[garde], t[garde], minute[garde]
    jour = t.dt.normalize()
    jours = np.sort(jour.unique())
    ij = np.searchsorted(jours, jour.values)
    tab = {}
    for col in "ohlc":
        a = np.full((len(jours), n), np.nan)
        a[ij, minute] = d[col].values
        tab[col] = a
    P = ~np.isnan(tab["c"])
    C = pd.DataFrame(tab["c"]).ffill(axis=1).values
    for col in "ohl":
        tab[col] = np.where(np.isnan(tab[col]), C, tab[col])
    V = np.zeros((len(jours), n))
    V[ij, minute] = d["v"].values
    contrat = d.groupby(ij)["contrat"].last().reindex(range(len(jours))).values
    ech = np.r_[False, contrat[1:] != contrat[:-1]]
    return pd.DatetimeIndex(jours), tab["o"], tab["h"], tab["l"], C, P, V, ech


def zone_de_bruit(jours, O, H, L, C, P, V, ech):
    """Copie de intraday/strategies.py zone_de_bruit (avec VWAP) pour une seance de n minutes."""
    n = O.shape[1]
    ok = P[:, 0] & P[:, n - 1] & (P.sum(axis=1) >= n - 20)
    ouverture = O[:, 0]
    veille = np.r_[np.nan, C[:-1, n - 1]]
    veille[ech] = np.nan
    sigma = pd.DataFrame(np.abs(C / ouverture[:, None] - 1)).rolling(JOURS_MOYENNE, min_periods=JOURS_MOYENNE).mean().shift(1).values
    typique = (H + L + C) / 3
    cumv = np.cumsum(V, axis=1)
    prix_moyen = np.where(cumv > 0, np.cumsum(typique * V, axis=1) / np.where(cumv > 0, cumv, 1),
                          np.cumsum(typique, axis=1) / np.arange(1, n + 1))
    haut_ref, bas_ref = np.fmax(ouverture, veille), np.fmin(ouverture, veille)
    gains, nb, pires = np.full(len(jours), np.nan), np.zeros(len(jours)), np.zeros(len(jours))
    for d in np.where(ok & ~np.isnan(veille) & ~np.isnan(sigma[:, PAS]))[0]:
        pos, entree, total, allers, pire, avant = 0, 0.0, 0.0, 0, 0.0, 0
        for m in range(PAS, n, PAS):
            if pos:
                creux = L[d, avant + 1:m + 1].min() - entree if pos > 0 else entree - H[d, avant + 1:m + 1].max()
                pire = min(pire, total + creux)
            avant = m
            p = C[d, m]
            ub, lb = haut_ref[d] * (1 + sigma[d, m]), bas_ref[d] * (1 - sigma[d, m])
            if pos > 0 and p <= max(ub, prix_moyen[d, m]):
                total += p - entree; pos = 0
            elif pos < 0 and p >= min(lb, prix_moyen[d, m]):
                total += entree - p; pos = 0
            if pos == 0 and p > ub:
                pos, entree, allers = 1, p, allers + 1
            elif pos == 0 and p < lb:
                pos, entree, allers = -1, p, allers + 1
        if pos:
            creux = L[d, avant + 1:].min() - entree if pos > 0 else entree - H[d, avant + 1:].max()
            pire = min(pire, total + creux)
            total += pos * (C[d, n - 1] - entree)
        gains[d], nb[d], pires[d] = total, allers, min(pire, total, 0.0)
    garde = ~np.isnan(gains) & (nb > 0)
    z = pd.DataFrame({"brut": gains, "allers": nb, "pire": pires}, index=jours)[garde]
    return z, pd.DatetimeIndex(jours[ok])


def marche(nom):
    fichier, pt, tick, m0, m1 = MARCHES[nom]
    jours, O, H, L, C, P, V, ech = charger(fichier, m0, m1)
    z, completes = zone_de_bruit(jours, O, H, L, C, P, V, ech)
    cout = 2 * (FRAIS_ORDRE + tick * pt) / pt                        # points par aller-retour
    dollars = (z["brut"] - cout * z["allers"]) * pt
    gain = dollars.reindex(completes).fillna(0)
    pire = (z["pire"] * pt).reindex(completes).fillna(0).clip(upper=0)
    pire = np.minimum(pire, np.minimum(gain, 0))
    return dollars, pd.DataFrame({"gain": gain, "pire": pire, "risque1": gain.rolling(60, min_periods=40).std().shift(1)})


def t_stat(x):
    x = x.dropna()
    return x.mean() / x.std() * np.sqrt(len(x))


# ----------------------------------------------------------------------------- challenge multi-marches
def une_tentative(G, Pi, R1, i0, regle, f, jmax=None):
    solde = haut = 50000.0
    meilleur = 0.0
    fin = min(len(G), i0 + (regle["jours"] or 10 ** 6))
    for k in range(i0, fin):
        plancher = haut - regle["perte"]
        if regle["blocage"]:
            plancher = min(plancher, regle["blocage"])
        budget = f * (solde - plancher)
        r = R1[k]
        actifs = np.isfinite(r) & (r > 0)
        if actifs.any():
            b = budget / np.sqrt(actifs.sum())
            n = np.where(actifs, np.clip(np.floor(b / np.where(actifs, r, 1)), 0, 50), 0)
        else:
            n = np.zeros(len(r))
        jour, creux = float(np.nansum(n * G[k])), float(np.nansum(n * Pi[k]))
        if regle["jour_max"] and creux <= -regle["jour_max"]:
            jour = max(jour, -regle["jour_max"])
        if solde + creux <= plancher or solde + jour <= plancher:
            return -1, k
        solde += jour
        meilleur = max(meilleur, jour)
        haut = max(haut, solde)
        profit = solde - 50000
        if profit >= regle["objectif"] and (not regle["regularite"] or meilleur <= regle["regularite"] * profit):
            return 1, k
    return 0, fin - 1


def sur_un_an(G, Pi, R1, regle, f):
    res = []
    for i0 in range(0, len(G) - 252, 5):
        k, n_tent, ok = i0, 0, False
        while k < i0 + 252:
            n_tent += 1
            r, fin = une_tentative(G, Pi, R1, k, regle, f)
            if r == 1 and fin < i0 + 252:
                ok = True
                break
            k = fin + 1
            if r == 0 and regle["jours"] is None:
                break
        res.append((ok, n_tent))
    return pd.DataFrame(res, columns=["reussi", "tentatives"])


def finance(G, Pi, R1, i0, f):
    """Compte finance Phidias (hypotheses de challenge/finance.py) sur 12 mois : montant recu (80 %)."""
    solde = haut = 50000.0
    recu, meilleur, gain_periode = 0.0, 0.0, 0.0
    for j, k in enumerate(range(i0, min(len(G), i0 + 252))):
        plancher = 50100.0 if haut >= 52600 else haut - 2500
        r = R1[k]
        actifs = np.isfinite(r) & (r > 0)
        b = f * (solde - plancher) / np.sqrt(max(actifs.sum(), 1))
        n = np.where(actifs, np.clip(np.floor(b / np.where(actifs, r, 1)), 0, 50), 0)
        jour, creux = float(np.nansum(n * G[k])), float(np.nansum(n * Pi[k]))
        if solde + creux <= plancher or solde + jour <= plancher:
            return recu
        solde += jour
        haut = max(haut, solde)
        meilleur, gain_periode = max(meilleur, jour), gain_periode + jour
        if (j + 1) % 21 == 0 and solde > 52600 and gain_periode > 0 and meilleur <= 0.3 * gain_periode:
            recu += 0.8 * (solde - 52600)
            solde = 52600.0
            meilleur, gain_periode = 0.0, 0.0
    return recu


def main():
    series, dollars = {}, {}
    print("1. Zone de bruit par marche (1 micro, frais compris) :")
    for nom in MARCHES:
        if not MARCHES[nom][0].exists():
            sys.exit(f"Donnees manquantes : {MARCHES[nom][0]}")
        dol, s = marche(nom)
        dollars[nom], series[nom] = dol, s
        u = s["gain"] / s["risque1"]
        print(f"  {nom:3s} : {len(dol)} jours avec trade | {dol.mean():+.2f} $ par jour de trade (t {t_stat(dol):+.2f})"
              f" | en unites de risque {u.mean():+.3f} (t {t_stat(u):+.2f}) | "
              + " | ".join(f"{a}-{int(z) - 1} t {t_stat(u[(u.index >= a) & (u.index < z)]):+.2f}" for a, z in PERIODES_MARCHE
                           if ((u.index >= a) & (u.index < z)).sum() > 50), flush=True)
    U = pd.DataFrame({k: s["gain"] / s["risque1"] for k, s in series.items()}).loc[DEBUT_COMMUN:]
    corr = U.corr().values[np.triu_indices(len(U.columns), 1)]
    print(f"  correlation moyenne entre marches : {np.nanmean(corr):+.2f}")
    port = U.mean(axis=1).dropna()
    nq = U["NQ"].dropna()
    sh = lambda x: x.mean() / x.std() * np.sqrt(252)
    print(f"\n2. Portefeuille a risque egal (7 marches) contre NQ seul, en unites de risque, {port.index[0].date()} -> {port.index[-1].date()} :")
    print(f"  portefeuille : Sharpe {sh(port):.2f}, t {t_stat(port):+.2f} | NQ seul : Sharpe {sh(nq):.2f}, t {t_stat(nq):+.2f}")
    ok = t_stat(port) >= 3 and sh(port) > sh(nq)
    for a, z in PERIODES:
        x = port[(port.index >= a) & (port.index < z)]
        print(f"     {a}-{int(z) - 1} : moyenne {x.mean():+.3f} (t {t_stat(x):+.2f}) | NQ seul {nq[(nq.index >= a) & (nq.index < z)].mean():+.3f}")
        ok &= x.mean() > 0
    print(f"\nCriteres (t >= 3, positif dans chaque sous-periode, Sharpe > NQ seul) : {'REMPLIS' if ok else 'NON REMPLIS'}\n")
    if not ok:
        return
    from bot_challenge import FRACTIONS, REGLES
    jours = U.index
    G = pd.DataFrame({k: s["gain"] for k, s in series.items()}).reindex(jours).values
    Pi = pd.DataFrame({k: s["pire"] for k, s in series.items()}).reindex(jours).values
    R1 = pd.DataFrame({k: s["risque1"] for k, s in series.items()}).reindex(jours).values
    actif = (G != 0) & np.isfinite(G)
    moy = np.array([G[actif[:, j], j].mean() for j in range(G.shape[1])])
    G0, P0 = np.where(actif, G - moy, G), np.where(actif, Pi - moy, Pi)          # sans avantage
    print("3. Challenge 50K, 7 marches en micros entiers (un depart par semaine, regles a verifier) :")
    for firme, regle in REGLES.items():
        for f in FRACTIONS:
            une = np.array([une_tentative(G, Pi, R1, i, regle, f)[0] for i in range(0, len(G) - 252, 5)])
            an, an0 = sur_un_an(G, Pi, R1, regle, f), sur_un_an(G0, P0, R1, regle, f)
            deux = (an["reussi"] & (an["tentatives"] <= 2)).mean()
            ligne = (f"  {firme:12s} f={f:.2f} | 1 tentative : reussie {np.mean(une == 1):4.0%}, perdue {np.mean(une == -1):5.1%}"
                     f" | en 12 mois : valide {an['reussi'].mean():4.0%} (2 comptes max {deux:4.0%} ; sans avantage {an0['reussi'].mean():4.0%})")
            if firme.startswith("Phidias"):
                recu = np.array([finance(G, Pi, R1, i, f) for i in range(0, len(G) - 252, 5)])
                ligne += f" | finance 12 mois : recu {recu.mean():,.0f} $ en moyenne, rien {np.mean(recu == 0):.0%}"
            print(ligne, flush=True)
        print()


if __name__ == "__main__":
    main()
