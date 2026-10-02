#!/usr/bin/env python3
"""Outils d'order flow sur le NQ (README.md) : chargement des donnees agregees, barres d'une minute avec delta, CVD,
VWAP, niveaux de la veille, footprint, gros ordres, et simulateur d'execution au marche (achat au meilleur vendeur,
vente au meilleur acheteur, a la seconde qui suit le signal, + 1 $ par ordre MNQ = 0,5 point de NQ)."""
import os
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
D = Path(os.getenv("OF_DONNEES", ICI / "donnees"))     # OF_DONNEES : autre dossier (essais sur donnees fabriquees)
NS = 23400                       # secondes de 9 h 30 a 16 h
TICK, COMMISSION = 0.25, 0.5     # points de NQ ; 1 $ par ordre MNQ = 0,5 point


def lots():
    return sorted(int(p.stem.split("_")[-1].split(".")[0]) for p in D.glob("nq_secondes_*.csv.gz"))


class Seances:
    """Toutes les seances telechargees, en tableaux (seance x seconde) : prix, haut, bas, achat, vente, bid, ask."""

    def __init__(self, dossier=D):
        s = pd.concat([pd.read_csv(p) for p in sorted(Path(dossier).glob("nq_secondes_*.csv.gz"))], ignore_index=True)
        s = s.drop_duplicates("t").sort_values("t")
        t = pd.to_datetime(s["t"])
        jour = t.dt.normalize()
        sec = ((t - jour).dt.total_seconds() - 34200).astype(int).to_numpy()
        garde = (sec >= 0) & (sec < NS)
        s, jour, sec = s[garde], jour[garde], sec[garde]
        # jours feries americains (cloture anticipee a 13 h) : seances retirees (note du 2 octobre, README)
        fin = pd.Series(sec).groupby(jour.to_numpy()).max()
        garde = ~jour.isin(fin.index[fin < 12900]).to_numpy()
        s, jour, sec = s[garde], jour[garde], sec[garde]
        self.jours = pd.DatetimeIndex(np.sort(jour.unique()))
        ij = self.jours.get_indexer(jour)
        nj = len(self.jours)

        def grille(col, remplir):
            a = np.full((nj, NS), np.nan)
            a[ij, sec] = s[col].to_numpy(float)
            return pd.DataFrame(a).ffill(axis=1).bfill(axis=1).to_numpy().copy() if remplir else np.nan_to_num(a)
        self.prix, self.bid, self.ask = grille("prix", True), grille("bid", True), grille("ask", True)
        self.bid_q, self.ask_q = grille("bid_q", True), grille("ask_q", True)
        self.haut = np.where(np.isnan(g := self._brut(s, ij, sec, "haut", nj)), self.prix, g)
        self.bas = np.where(np.isnan(g := self._brut(s, ij, sec, "bas", nj)), self.prix, g)
        self.achat, self.vente = grille("achat", False), grille("vente", False)
        contrat = pd.Series(s["contrat"].to_numpy()).groupby(ij).agg(lambda x: x.mode().iloc[0])
        self.contrat = contrat.reindex(range(nj)).to_numpy()
        changement = np.r_[False, self.contrat[1:] != self.contrat[:-1]]     # premiere seance d'un nouveau contrat
        # seance mince (volume < 40 % de la mediane des 20 seances d'avant, ex. veille d'un changement de contrat ou le
        # symbole suit encore l'ancien contrat) : pas de trade, comme un jour de changement (note du 2 octobre, README)
        vol = self.achat.sum(axis=1) + self.vente.sum(axis=1)
        self.mince = np.array([d > 0 and vol[d] < 0.4 * np.median(vol[max(0, d - 20):d]) for d in range(nj)])
        self.change = changement | self.mince                                  # seances sans trade
        self.n_secondes = np.bincount(ij, minlength=nj)
        self.n_trades = np.bincount(ij, weights=s["n"].to_numpy(float), minlength=nj)

    def restreindre(self, n):
        """Ne garde que les n premieres seances (l'exploration ne voit pas le coffre)."""
        for a in ("prix", "bid", "ask", "bid_q", "ask_q", "haut", "bas", "achat", "vente"):
            setattr(self, a, getattr(self, a)[:n].copy())
        for a in ("contrat", "change", "mince", "n_secondes", "n_trades"):
            setattr(self, a, getattr(self, a)[:n])
        self.jours = self.jours[:n]
        return self

    @staticmethod
    def _brut(s, ij, sec, col, nj):
        a = np.full((nj, NS), np.nan)
        a[ij, sec] = s[col].to_numpy(float)
        return a

    # ------------------------------------------------------------------ barres d'une minute
    def minutes(self, d):
        """Barres d'une minute de la seance d : ouverture, haut, bas, cloture, achat, vente, delta, CVD, VWAP."""
        p = self.prix[d].reshape(390, 60)
        h, b = self.haut[d].reshape(390, 60).max(axis=1), self.bas[d].reshape(390, 60).min(axis=1)
        a, v = self.achat[d].reshape(390, 60).sum(axis=1), self.vente[d].reshape(390, 60).sum(axis=1)
        vol = self.achat[d] + self.vente[d]
        cumv = np.cumsum(vol)
        vwap_s = np.where(cumv > 0, np.cumsum(self.prix[d] * vol) / np.where(cumv > 0, cumv, 1), self.prix[d])
        return pd.DataFrame({"o": p[:, 0], "h": h, "l": b, "c": p[:, -1], "achat": a, "vente": v, "delta": a - v,
                             "cvd": np.cumsum(a - v), "vwap": vwap_s.reshape(390, 60)[:, -1]})

    def veille(self, d):
        """Plus haut et plus bas de la seance precedente (None pour la premiere seance)."""
        if d == 0:
            return None, None
        return float(self.haut[d - 1].max()), float(self.bas[d - 1].min())

    def vwap(self, d):
        vol = self.achat[d] + self.vente[d]
        cumv = np.cumsum(vol)
        return np.where(cumv > 0, np.cumsum(self.prix[d] * vol) / np.where(cumv > 0, cumv, 1), self.prix[d])


# ---------------------------------------------------------------------- execution
def executer(S, trades):
    """trades : DataFrame (seance, seconde du signal, sens +1/-1, duree en secondes). Entree a la seconde suivante au
    meilleur prix du cote paye, sortie apres `duree` secondes (au plus tard 15 h 59 59) au meilleur prix du cote recu.
    Renvoie les trades avec brut, ecart paye et net en points de NQ."""
    if len(trades) == 0:
        return trades.assign(brut=[], net=[], ecart=[])
    d = trades["seance"].to_numpy()
    e = np.minimum(trades["seconde"].to_numpy() + 1, NS - 2)
    x = np.minimum(e + trades["duree"].to_numpy(), NS - 1)
    sens = trades["sens"].to_numpy()
    entree = np.where(sens > 0, S.ask[d, e], S.bid[d, e])
    sortie = np.where(sens > 0, S.bid[d, x], S.ask[d, x])
    mid_e, mid_x = (S.ask[d, e] + S.bid[d, e]) / 2, (S.ask[d, x] + S.bid[d, x]) / 2
    brut = sens * (mid_x - mid_e)                      # mouvement du prix milieu
    net = sens * (sortie - entree) - 2 * COMMISSION
    return trades.assign(entree=entree, sortie=sortie, brut=brut, ecart=brut - (net + 2 * COMMISSION), net=net)


def t_stat(x):
    x = np.asarray(x, float)
    s = x.std(ddof=1) if len(x) > 1 else 0.0
    return float(x.mean() / s * np.sqrt(len(x))) if s > 0 else 0.0


def hasard(S, trades, n=1000, graine=0):
    """t du gain net de n versions ou chaque trade garde sa seance, son sens et sa duree, a une seconde tiree au hasard."""
    if len(trades) == 0:
        return np.zeros(n)
    rng = np.random.default_rng(graine)
    d, sens, duree = (trades[c].to_numpy().astype(np.int64) for c in ("seance", "sens", "duree"))
    ts = np.empty(n)
    for i in range(n):
        sec = rng.integers(0, NS - 2 - duree)
        e = sec + 1
        x = np.minimum(e + duree, NS - 1)
        ent = np.where(sens > 0, S.ask[d, e], S.bid[d, e])
        sor = np.where(sens > 0, S.bid[d, x], S.ask[d, x])
        ts[i] = t_stat(sens * (sor - ent) - 2 * COMMISSION)
    return ts


def lire_footprint(dossier=D, jusqu_au=None):
    f = pd.concat([pd.read_csv(p) for p in sorted(Path(dossier).glob("nq_footprint_*.csv.gz"))], ignore_index=True)
    if jusqu_au is not None:
        f = f[f["m"].str[:10] <= str(pd.Timestamp(jusqu_au).date())]
    return f
