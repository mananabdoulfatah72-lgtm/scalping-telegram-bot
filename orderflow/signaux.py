#!/usr/bin/env python3
"""Les cinq hypotheses du README, codees telles qu'ecrites. Chaque detecteur renvoie un DataFrame de trades
(seance, seconde du signal, sens, duree en secondes), avec une seule position a la fois par hypothese, sans signal les
jours de changement de contrat, et en n'utilisant que les donnees connues a la seconde du signal."""
import re

import numpy as np
import pandas as pd

from outils import NS, TICK

QUINZE, TRENTE = 900, 1800


def _sans_chevauchement(liste):
    """Garde les signaux d'une seance qui arrivent apres la fin du trade precedent."""
    out, fin = [], {}
    for d, s, sens, duree in sorted(liste):
        if s > fin.get(d, -1):
            out.append((d, s, sens, duree))
            fin[d] = s + 1 + duree
    return pd.DataFrame(out, columns=["seance", "seconde", "sens", "duree"])


def h2_absorption(S, seances):
    """Absorption sur le plus haut ou le plus bas de la veille, ou sur le VWAP du jour, puis retournement (15 minutes)."""
    liste = []
    for d in seances:
        if d < 5 or S.change[d]:
            continue
        # seuil : 90e centile des volumes agressifs d'un cote par minute, sur les 5 seances d'avant
        vols = np.concatenate([np.r_[S.achat[k].reshape(390, 60).sum(1), S.vente[k].reshape(390, 60).sum(1)] for k in range(d - 5, d)])
        q = np.quantile(vols, 0.90)
        m = S.minutes(d)
        ph, pl = S.veille(d)
        vwap_debut = np.r_[m["o"].iloc[0], m["vwap"].to_numpy()[:-1]]       # VWAP connu au debut de la minute
        for i in range(1, 390):
            o, h, l, c = m.loc[i, ["o", "h", "l", "c"]]
            achat, vente = m.loc[i, "achat"], m.loc[i, "vente"]
            sig = 0
            for niveau in (ph, pl, vwap_debut[i]):
                if niveau is None:
                    continue
                if o < niveau and h >= niveau - 2 * TICK and c <= niveau - 2 * TICK and achat >= q:
                    sig = -1                    # poussee acheteuse absorbee sous une resistance : vente
                elif o > niveau and l <= niveau + 2 * TICK and c >= niveau + 2 * TICK and vente >= q:
                    sig = 1                     # poussee vendeuse absorbee sur un support : achat
                if sig:
                    break
            if sig:
                liste.append((d, (i + 1) * 60 - 1, sig, QUINZE))
    return _sans_chevauchement(liste)


def seuil_gros(S, gros, d):
    """Plus petite taille k >= 10 telle que la part des transactions de taille >= k, sur les 5 seances d'avant, soit au
    plus 0,1 % (le fichier des gros ordres contient toutes les transactions d'au moins 10 contrats)."""
    jours = S.jours[d - 5:d]
    g = gros[gros["jour"].isin(jours)]["taille"].to_numpy()
    total = 0
    for k in range(d - 5, d):
        total += S.n_trades[k]
    k = 10
    while (g >= k).sum() > 0.001 * total:
        k += 1
    return k


def h3_gros_ordres(S, gros, seances):
    """Suivre le sens d'une transaction au moins egale au 99,9e centile des tailles des 5 seances d'avant (15 minutes)."""
    liste = []
    for d in seances:
        if d < 5 or S.change[d]:
            continue
        k = seuil_gros(S, gros, d)
        g = gros[(gros["jour"] == S.jours[d]) & (gros["taille"] >= k) & (gros["sens"] != 0)]
        for s, sens in zip(g["seconde"].to_numpy(), g["sens"].to_numpy()):
            if 0 <= s < NS - 2:
                liste.append((d, int(s), int(sens), QUINZE))
    return _sans_chevauchement(liste)


def h4_divergence(S, seances):
    """Nouveau plus haut de la seance (apres 10 h) avec un delta des 30 dernieres minutes negatif : vente ;
    nouveau plus bas avec un delta positif : achat (15 minutes)."""
    liste = []
    for d in seances:
        if S.change[d]:
            continue
        hh = np.maximum.accumulate(S.haut[d])
        ll = np.minimum.accumulate(S.bas[d])
        nouveau_h = np.r_[False, S.haut[d][1:] > hh[:-1]]
        nouveau_b = np.r_[False, S.bas[d][1:] < ll[:-1]]
        delta = np.cumsum(S.achat[d] - S.vente[d])
        d30 = delta - np.r_[np.zeros(TRENTE), delta[:-TRENTE]]
        for s in np.flatnonzero((nouveau_h | nouveau_b) & (np.arange(NS) >= TRENTE)):
            if nouveau_h[s] and d30[s] < 0:
                liste.append((d, int(s), -1, QUINZE))
            elif nouveau_b[s] and d30[s] > 0:
                liste.append((d, int(s), 1, QUINZE))
    return _sans_chevauchement(liste)


def h5_delta15(S, seances):
    """Toutes les 15 minutes de 9 h 45 a 15 h 30 : desequilibre des 15 dernieres minutes au-dela de 0,15 -> on le suit
    30 minutes."""
    liste = []
    for d in seances:
        if S.change[d]:
            continue
        for fin in range(QUINZE, 21601, QUINZE):
            a, v = S.achat[d, fin - QUINZE:fin].sum(), S.vente[d, fin - QUINZE:fin].sum()
            if a + v > 0 and abs(a - v) / (a + v) > 0.15:
                liste.append((d, fin - 1, 1 if a > v else -1, TRENTE))
    return _sans_chevauchement(liste)


def lire_gros(S, dossier):
    from pathlib import Path
    g = pd.concat([pd.read_csv(p) for p in sorted(Path(dossier).glob("nq_gros_*.csv.gz"))], ignore_index=True)
    t = pd.to_datetime(g["t"])
    g["jour"] = t.dt.normalize()
    g["seconde"] = ((t - g["jour"]).dt.total_seconds() - 34200).astype(int)
    return g[(g["seconde"] >= 0) & (g["seconde"] < NS)].reset_index(drop=True)


# ---------------------------------------------------------------------- H1 : filtre de la zone de bruit
MOTIF = re.compile(r"(achat|vente) (\d+)h(\d+) a ([\d,.]+) -> sortie (\d+)h(\d+) a ([\d,.]+)")


def trades_zone(robot, minutes_robot, jours):
    """Trades de la zone de bruit (code du robot, sur ses barres d'une minute) pour les seances `jours` : seance, minute
    de decision, sens, gain en points de NQ apres les frais du robot (1,5 point par aller-retour)."""
    jj, O, H, L, C, P, V, ech = robot.tableaux(minutes_robot)
    _, trades, _ = robot.zone_de_bruit(jj, O, H, L, C, P, V, ech)
    out = []
    for j, liste in trades.items():
        j = pd.Timestamp(j)
        if j not in jours:
            continue
        for texte in liste:
            x = MOTIF.search(texte)
            if not x:
                continue
            sens = 1 if x.group(1) == "achat" else -1
            m = int(x.group(2)) * 60 + int(x.group(3)) - 570
            entree, sortie = float(x.group(4).replace(",", "")), float(x.group(7).replace(",", ""))
            out.append({"jour": j, "minute": m, "sens": sens, "points": sens * (sortie - entree) - robot.COUT})
    return pd.DataFrame(out)


def h1_filtre(S, zone):
    """Pour chaque trade de zone : delta des 30 minutes qui finissent a la cloture de la minute de decision ; garde si
    son signe va dans le sens du trade."""
    if zone.empty:
        return zone.assign(seance=[], delta30=[], garde=[])
    d = S.jours.get_indexer(zone["jour"])
    fin = (zone["minute"].to_numpy() + 1) * 60
    deb = np.maximum(fin - TRENTE, 0)
    delta = np.array([S.achat[k, a:b].sum() - S.vente[k, a:b].sum() for k, a, b in zip(d, deb, fin)])
    vol = np.array([S.achat[k, a:b].sum() + S.vente[k, a:b].sum() for k, a, b in zip(d, deb, fin)])
    x = np.where(vol > 0, delta / np.where(vol > 0, vol, 1), 0.0)
    return zone.assign(seance=d, delta30=x, garde=np.sign(x) == zone["sens"].to_numpy())
