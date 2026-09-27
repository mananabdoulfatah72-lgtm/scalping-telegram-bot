#!/usr/bin/env python3
"""Trois strategies intraday publiees, testees sur les prix minute du S&P 500 et du Nasdaq 100
(seance americaine 9 h 30 - 16 h), avec les frais des micro-futures MES et MNQ.

1. Momentum de fin de seance (Gao, Han, Li, Zhou, JFE 2018) : le rendement entre la cloture
   de la veille et 10 h donne le sens ; position de 15 h 30 a 16 h.
2. Momentum de fin de seance (Baltussen, Da, Lammers, Martens, JFE 2021) : le rendement entre
   la cloture de la veille et 15 h 30 donne le sens ; position de 15 h 30 a 16 h.
3. OPR 5 minutes (Zarattini et Aziz, 2023) : sens de la premiere bougie de 5 minutes, entree
   a 9 h 35, stop de l'autre cote de la bougie, objectif 10 fois le risque, sortie a 16 h.
4. Zone de bruit (Zarattini, Aziz et Barbon, 2024) : entree toutes les 30 minutes si le prix
   sort de la zone de bruit (mouvement moyen des 14 derniers jours a la meme heure) ; stop
   suiveur = limite de la zone ou prix moyen de la journee ; sortie a 16 h.
   Limite : pas de volumes, le prix moyen de la journee remplace le VWAP.

Aucun parametre n'est ajuste aux donnees : ce sont ceux des articles.
"""
from pathlib import Path

import numpy as np
import pandas as pd

DONNEES = Path(__file__).parent / "donnees"
N = 390                                   # minutes de 9 h 30 a 15 h 59
CONTRATS = {  # $ par point, taille du tick, frais par ordre ($), date de publication
    "sp500": {"micro": "MES", "pt": 5.0, "tick": 0.25},
    "nasdaq100": {"micro": "MNQ", "pt": 2.0, "tick": 0.25},
}
FRAIS_ORDRE = 1.00                        # $ par contrat et par ordre (commission + bourse)


def charger(nom):
    """Renvoie (jours, O, H, L, C, P) : tableaux (jours x 390 minutes). P indique les minutes
    presentes dans les donnees ; les minutes absentes sont remplies avec le dernier prix connu."""
    d = pd.read_csv(DONNEES / f"{nom}_1min.csv.gz")
    t = pd.to_datetime(d["t"])
    jour = t.dt.normalize()
    minute = (t.dt.hour * 60 + t.dt.minute - 570).values
    jours = np.sort(jour.unique())
    ij = np.searchsorted(jours, jour.values)
    tab = {}
    for col in "ohlc":
        a = np.full((len(jours), N), np.nan)
        a[ij, minute] = d[col].values
        tab[col] = a
    presentes = ~np.isnan(tab["c"])
    # minutes manquantes : on recopie le dernier prix connu de la journee
    C = pd.DataFrame(tab["c"]).ffill(axis=1).values
    for col in "ohl":
        tab[col] = np.where(np.isnan(tab[col]), C, tab[col])
    return pd.DatetimeIndex(jours), tab["o"], tab["h"], tab["l"], C, presentes


def journees_completes(P):
    """Seances completes (pas de fermeture anticipee) avec assez de minutes presentes."""
    return P[:, 0] & P[:, N - 1] & (P.sum(axis=1) >= 370)


def cout_aller_retour(nom):
    c = CONTRATS[nom]
    return 2 * (FRAIS_ORDRE + c["tick"] * c["pt"]) / c["pt"]      # en points d'indice


def fin_de_seance(jours, O, H, L, C, P, signal_minute):
    """Momentum de fin de seance. signal_minute : 29 (10 h, Gao) ou 359 (15 h 30, Baltussen).
    Renvoie un DataFrame par jour : sens, gain brut en points."""
    ok = journees_completes(P)
    veille = np.r_[np.nan, C[:-1, N - 1]]
    ok &= np.r_[False, ok[:-1]]                    # la veille doit etre une seance complete
    signal = C[:, signal_minute] / veille - 1
    sens = np.sign(signal)
    gain = sens * (C[:, N - 1] - C[:, 359])
    # pire moment du trade (points, <= 0) : utile pour les limites verifiees en temps reel
    pire = np.minimum(0, np.where(sens > 0, L[:, 360:].min(axis=1) - C[:, 359], C[:, 359] - H[:, 360:].max(axis=1)))
    return pd.DataFrame({"sens": sens, "brut": gain, "risque": np.nan, "pire": pire}, index=jours)[ok & (sens != 0)]


def opr5(jours, O, H, L, C, P, objectif_r=10.0):
    """OPR 5 minutes (Zarattini et Aziz). Gain brut en points et risque R en points."""
    ok = journees_completes(P)
    o0, c4 = O[:, 0], C[:, 4]
    haut, bas = H[:, :5].max(axis=1), L[:, :5].min(axis=1)
    sens = np.sign(c4 - o0)
    entree = O[:, 5]
    stop = np.where(sens > 0, bas, haut)
    risque = np.abs(entree - stop)
    cible = entree + sens * objectif_r * risque
    gain = np.full(len(jours), np.nan)
    pire = np.full(len(jours), np.nan)
    for d in np.where(ok & (sens != 0) & (risque > 0))[0]:
        s = sens[d]
        sortie = C[d, N - 1]
        extreme = entree[d]
        for m in range(5, N):
            o = O[d, m]
            # le cours ouvre deja au-dela du stop (ou de l'objectif) : sortie a ce prix
            if (s > 0 and o <= stop[d]) or (s < 0 and o >= stop[d]):
                sortie = o
                break
            if (s > 0 and o >= cible[d]) or (s < 0 and o <= cible[d]):
                sortie = o
                break
            touche_stop = L[d, m] <= stop[d] if s > 0 else H[d, m] >= stop[d]
            touche_cible = H[d, m] >= cible[d] if s > 0 else L[d, m] <= cible[d]
            if touche_stop:                        # si les deux dans la meme minute : stop d'abord
                sortie = stop[d]
                break
            if touche_cible:
                sortie = cible[d]
                break
            extreme = min(extreme, L[d, m]) if s > 0 else max(extreme, H[d, m])
        gain[d] = s * (sortie - entree[d])
        pire[d] = min(0.0, s * (extreme - entree[d]), gain[d])
    garde = ~np.isnan(gain)
    return pd.DataFrame({"sens": sens, "brut": gain, "risque": risque, "pire": pire}, index=jours)[garde]


def zone_de_bruit(jours, O, H, L, C, P, jours_moyenne=14, pas=30):
    """Zone de bruit (Zarattini, Aziz, Barbon). Plusieurs trades possibles par jour : on renvoie
    le gain brut total du jour en points et le nombre d'allers-retours."""
    ok = journees_completes(P)
    ouverture = O[:, 0]
    veille = np.r_[np.nan, C[:-1, N - 1]]
    mouvement = np.abs(C / ouverture[:, None] - 1)
    sigma = pd.DataFrame(mouvement).rolling(jours_moyenne, min_periods=jours_moyenne).mean().shift(1).values
    prix_moyen = np.cumsum((H + L + C) / 3, axis=1) / np.arange(1, N + 1)
    haut_ref = np.fmax(ouverture, veille)
    bas_ref = np.fmin(ouverture, veille)
    gains, nb = np.full(len(jours), np.nan), np.zeros(len(jours))
    moments = list(range(pas, N, pas))            # 10 h, 10 h 30, ..., 15 h 30
    for d in np.where(ok & ~np.isnan(veille) & ~np.isnan(sigma[:, pas]))[0]:
        pos, entree, total, allers = 0, 0.0, 0.0, 0
        for m in moments:
            p = C[d, m]
            ub = haut_ref[d] * (1 + sigma[d, m])
            lb = bas_ref[d] * (1 - sigma[d, m])
            # sortie sur stop suiveur
            if pos > 0 and p <= max(ub, prix_moyen[d, m]):
                total += p - entree; pos = 0
            elif pos < 0 and p >= min(lb, prix_moyen[d, m]):
                total += entree - p; pos = 0
            # entree
            if pos == 0 and p > ub:
                pos, entree, allers = 1, p, allers + 1
            elif pos == 0 and p < lb:
                pos, entree, allers = -1, p, allers + 1
        if pos:
            total += pos * (C[d, N - 1] - entree)
        gains[d], nb[d] = total, allers
    garde = ~np.isnan(gains) & (nb > 0)
    return pd.DataFrame({"brut": gains, "allers": nb}, index=jours)[garde]
