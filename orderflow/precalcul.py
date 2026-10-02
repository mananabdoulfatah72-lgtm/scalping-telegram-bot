#!/usr/bin/env python3
"""Briques de la machine order flow (README.md, regles v2), calculees minute par minute avec les seules donnees connues a
la cloture de la minute : niveaux (veille, volume profile, VWAP, ouverture), mesures d'order flow sur W minutes."""
from pathlib import Path

import numpy as np
import pandas as pd

import outils as O

FENETRES = (1, 3, 5, 10, 15, 30, 60)
RATIOS = (2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0)
NIVEAUX = ["plus haut veille", "plus bas veille", "cloture veille", "POC veille", "VAH veille", "VAL veille",
           "HVN veille", "LVN veille", "VWAP", "VWAP +1 ecart", "VWAP -1 ecart", "VWAP +2 ecarts", "VWAP -2 ecarts",
           "plus haut 30 min", "plus bas 30 min", "POC du jour"]


def profil(prix, volume):
    """POC, VAH, VAL (70 %), HVN et LVN (maxima / minima locaux du profil lisse sur 5 ticks) d'un profil de volume."""
    ordre = np.argsort(prix)
    p, v = prix[ordre], volume[ordre]
    if len(p) == 0 or v.sum() <= 0:
        return np.nan, np.nan, np.nan, np.array([]), np.array([])
    grille = np.arange(p[0], p[-1] + O.TICK / 2, O.TICK)
    vg = np.zeros(len(grille))
    np.add.at(vg, np.round((p - p[0]) / O.TICK).astype(int), v)
    ip = int(np.argmax(vg))
    bas, haut, cumul = ip, ip, vg[ip]
    while cumul < 0.7 * vg.sum():
        gauche = vg[bas - 1] if bas > 0 else -1
        droite = vg[haut + 1] if haut < len(vg) - 1 else -1
        if droite >= gauche:
            haut += 1
            cumul += vg[haut]
        else:
            bas -= 1
            cumul += vg[bas]
    lisse = np.convolve(vg, np.ones(5) / 5, mode="same")
    interieur = np.arange(1, len(lisse) - 1)
    hvn = grille[interieur[(lisse[1:-1] > lisse[:-2]) & (lisse[1:-1] >= lisse[2:])]]
    lvn = grille[interieur[(lisse[1:-1] < lisse[:-2]) & (lisse[1:-1] <= lisse[2:])]]
    return grille[ip], grille[haut], grille[bas], hvn, lvn


def plus_proche(liste, x):
    return liste[np.argmin(np.abs(liste - x))] if len(liste) else np.nan


class Briques:
    """Tableaux (seance x 390 minutes) des niveaux et mesures, pour toutes les seances de S."""

    def __init__(self, S, footprint, gros):
        nj = len(S.jours)
        self.nj = nj
        M = 390
        shape = (nj, M)
        self.o, self.h, self.l, self.c = (np.full(shape, np.nan) for _ in range(4))
        self.achat, self.vente = np.zeros(shape), np.zeros(shape)
        self.niveaux = np.full((len(NIVEAUX), nj, M), np.nan)
        self.l1 = np.zeros(shape)
        self.gros_net = np.zeros(shape)
        self.empile = np.zeros((len(RATIOS), nj, M), np.int8)
        self.pic = np.full(shape, np.nan)
        fp = footprint.copy()
        t = pd.to_datetime(fp["m"])
        fp["jour"] = t.dt.normalize()
        fp["minute"] = ((t - fp["jour"]).dt.total_seconds() // 60 - 570).astype(int)
        fp = fp[(fp["minute"] >= 0) & (fp["minute"] < M)]
        par_jour = {j: g for j, g in fp.groupby("jour")}
        vol_minute = np.zeros(shape)
        prev = None
        for d in range(nj):
            m = S.minutes(d)
            self.o[d], self.h[d], self.l[d], self.c[d] = m["o"], m["h"], m["l"], m["c"]
            self.achat[d], self.vente[d] = m["achat"], m["vente"]
            vol_minute[d] = m["achat"] + m["vente"]
            # VWAP et ecart-type pondere par les volumes, a la cloture de chaque minute
            vol = S.achat[d] + S.vente[d]
            cv = np.cumsum(vol)
            moy = np.where(cv > 0, np.cumsum(S.prix[d] * vol) / np.where(cv > 0, cv, 1), S.prix[d])
            var = np.where(cv > 0, np.cumsum(S.prix[d] ** 2 * vol) / np.where(cv > 0, cv, 1) - moy ** 2, 0)
            sd = np.sqrt(np.maximum(var, 0))
            vw, s1 = moy.reshape(M, 60)[:, -1], sd.reshape(M, 60)[:, -1]
            for k, x in enumerate((vw, vw + s1, vw - s1, vw + 2 * s1, vw - 2 * s1)):
                self.niveaux[8 + k, d] = x
            orh = np.maximum.accumulate(m["h"].to_numpy())
            orl = np.minimum.accumulate(m["l"].to_numpy())
            self.niveaux[13, d, 29:], self.niveaux[14, d, 29:] = orh[29], orl[29]   # connus apres les 30 premieres minutes
            g = par_jour.get(S.jours[d])
            if g is not None and len(g):
                # POC du jour en cours (volume par prix cumule jusqu'a la minute)
                prix_u = np.sort(g["prix"].unique())
                idx = np.searchsorted(prix_u, g["prix"].to_numpy())
                cum = np.zeros(len(prix_u))
                gm = g["minute"].to_numpy()
                vv = (g["achat"] + g["vente"]).to_numpy(float)
                ordre = np.argsort(gm, kind="stable")
                gm, idx_o, vv_o = gm[ordre], idx[ordre], vv[ordre]
                bornes = np.searchsorted(gm, np.arange(M + 1))
                for i in range(M):
                    a, b = bornes[i], bornes[i + 1]
                    np.add.at(cum, idx_o[a:b], vv_o[a:b])
                    self.niveaux[15, d, i] = prix_u[np.argmax(cum)] if cum.sum() > 0 else np.nan
                # empilement de desequilibres dans le footprint de chaque minute
                ach, ven = g["achat"].to_numpy(float), g["vente"].to_numpy(float)
                for i in np.unique(gm):
                    sel = g["minute"].to_numpy() == i
                    pr, a_, v_ = g["prix"].to_numpy()[sel], ach[sel], ven[sel]
                    o_ = np.argsort(pr)
                    pr, a_, v_ = pr[o_], a_[o_], v_[o_]
                    cont = np.r_[False, np.isclose(np.diff(pr), O.TICK)]          # prix voisin juste en dessous present
                    for kr, r in enumerate(RATIOS):
                        ach_imb = np.r_[False, (a_[1:] >= r * v_[:-1]) & (a_[1:] >= 5)] & cont
                        ven_imb = np.r_[(v_[:-1] >= r * a_[1:]) & (v_[:-1] >= 5), False] & np.r_[cont[1:], False]
                        def suite(x):
                            best = run = 0
                            for y in x:
                                run = run + 1 if y else 0
                                best = max(best, run)
                            return best
                        sa, sv = suite(ach_imb), suite(ven_imb)
                        self.empile[kr, d, i] = 1 if sa >= 3 and sv < 3 else (-1 if sv >= 3 and sa < 3 else 0)
                # profil complet de la seance (servira de veille a la suivante)
                tot = g.groupby("prix")[["achat", "vente"]].sum().sum(axis=1)
                prof = profil(tot.index.to_numpy(float), tot.to_numpy(float))
            else:
                prof = (np.nan, np.nan, np.nan, np.array([]), np.array([]))
            if d > 0 and prev is not None:
                ph, pl = S.veille(d)
                pc = float(S.prix[d - 1, -1])
                poc, vah, val, hvn, lvn = prev
                ouverture = float(m["o"].iloc[0])
                for k, x in enumerate((ph, pl, pc, poc, vah, val, plus_proche(hvn, ouverture), plus_proche(lvn, ouverture))):
                    self.niveaux[k, d] = x
            prev = prof
            # carnet au 1er niveau : moyenne des 10 dernieres secondes de chaque minute
            bq, aq = S.bid_q[d].reshape(M, 60)[:, -10:], S.ask_q[d].reshape(M, 60)[:, -10:]
            tot_q = bq + aq
            self.l1[d] = np.where(tot_q > 0, (bq - aq) / np.where(tot_q > 0, tot_q, 1), 0).mean(axis=1)
        # gros ordres : volume net signe par minute
        if len(gros):
            gj = S.jours.get_indexer(gros["jour"])
            ok = gj >= 0
            np.add.at(self.gros_net, (gj[ok], (gros["seconde"].to_numpy()[ok] // 60)), (gros["sens"] * gros["taille"]).to_numpy()[ok])
        # pic de volume : volume de la minute / moyenne de la meme minute sur les 5 seances d'avant
        for d in range(5, nj):
            ref = vol_minute[d - 5:d].mean(axis=0)
            self.pic[d] = np.where(ref > 0, vol_minute[d] / np.where(ref > 0, ref, 1), np.nan)
        self.vol = vol_minute
        self.change = S.change.copy()
        # sommes glissantes sur W minutes (pour le desequilibre, la divergence et les gros ordres)
        self.cum_achat = np.cumsum(self.achat, axis=1)
        self.cum_vente = np.cumsum(self.vente, axis=1)
        self.cum_gros = np.cumsum(self.gros_net, axis=1)
        # ecart-type des gros ordres nets par minute sur les 5 seances d'avant (pour un z)
        self.gros_sd = np.full(nj, np.nan)
        for d in range(5, nj):
            self.gros_sd[d] = self.gros_net[d - 5:d].std()
        self.bid, self.ask = S.bid, S.ask
        self._extremes = {}

    def extremes(self, W):
        """Plus haut et plus bas des clotures des W minutes d'avant (la minute en cours exclue)."""
        if W not in self._extremes:
            mx, mn = np.full_like(self.c, np.nan), np.full_like(self.c, np.nan)
            if W < self.c.shape[1]:
                fen = np.lib.stride_tricks.sliding_window_view(self.c, W, axis=1)[:, :self.c.shape[1] - W]
                mx[:, W:], mn[:, W:] = fen.max(axis=2), fen.min(axis=2)
            self._extremes[W] = (mx, mn)
        return self._extremes[W]

    def somme(self, cum, W):
        z = np.zeros((cum.shape[0], 1))
        dec = np.concatenate([z.repeat(W, axis=1), cum[:, :-W]], axis=1) if W < cum.shape[1] else np.zeros_like(cum)
        return cum - dec
