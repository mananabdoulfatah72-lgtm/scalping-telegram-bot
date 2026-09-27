#!/usr/bin/env python3
"""Les sources de gain candidates du fonds.

Chaque source se construit en renvoyant (rendements journaliers nets de frais, placebo) :
- les rendements sont a une echelle libre : le moteur ramene chaque source au meme risque ;
- placebo(rng) renvoie les rendements nets d'une version ou le choix (quand / quoi acheter) est
  tire au hasard, ou None pour une prime de risque pure.
Les regles de chaque source sont celles des etudes citees ; aucun parametre n'est ajuste ici.
"""
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from scipy.stats import rankdata

ICI = Path(__file__).parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI.parent / "tendance"))
sys.path.insert(0, str(ICI.parent / "intraday"))
import fomc  # noqa: E402
import strategies as ST  # noqa: E402
import systeme as S  # noqa: E402

JOURS_AN = 252
ACTIONS = ["S&P 500", "Nasdaq 100", "Russell 2000"]
FAMILLE = {m.nom: m.famille for m in S.MARCHES}
COUT = pd.Series({m.nom: m.cout_pb / 1e4 for m in S.MARCHES})
FAMILLES_CROISEES = ("actions", "obligations", "devises", "metaux", "energie")   # sans crypto, comme l'etude


@dataclass(frozen=True)
class Source:
    cle: str
    nom: str
    principe: str
    reference: str
    publication: str                 # date de publication de l'etude (debut de la periode "apres")
    construire: Callable


@lru_cache(None)
def rendements():
    close, adj = S.charger()
    return S.rendements_futures(close, adj)


@lru_cache(None)
def intraday(nom):
    return ST.charger(nom)


# ----------------------------------------------------------------------------- primes deja testees
def tendance():
    r = rendements()
    net, pos, _ = S.backtest(r)
    R, Q, c = r.fillna(0).values, pos.values, COUT[r.columns].values

    def placebo(rng):   # positions de chaque marche decalees au hasard dans le temps
        Z = np.column_stack([np.roll(Q[:, j], rng.integers(252, len(R) - 252)) for j in range(Q.shape[1])])
        brut = (Z[:-1] * R[1:]).sum(axis=1)
        frais = (np.abs(np.diff(Z, axis=0)) * c).sum(axis=1)
        return pd.Series(np.r_[0.0, brut - frais], index=r.index)
    return net, placebo


def achat():
    return S.backtest(rendements(), toujours_acheteur=True)[0], None


def zone_de_bruit():
    from analyse import calculer
    jours, res, cout = calculer("nasdaq100")
    J, O, *_ = intraday("nasdaq100")
    df = res["Zone de bruit"]
    ouverture = pd.Series(O[:, 0], index=J).reindex(df.index)
    net = (df["net"] / ouverture)
    frais = (cout * df["allers"] / ouverture).values
    brut = net.values + frais
    cal = rendements().index
    serie = net.reindex(cal).fillna(0)[cal >= df.index[0]]

    def placebo(rng):   # sens de chaque journee tire au hasard (memes mouvements, memes frais)
        s = pd.Series(rng.choice([-1.0, 1.0], len(brut)) * brut - frais, index=df.index)
        return s.reindex(cal).fillna(0)[cal >= df.index[0]]
    return serie, placebo


# ----------------------------------------------------------------------------- choix entre marches
class Croise:
    """Portefeuille 'croise' (Asness, Moskowitz, Pedersen 2013) : chaque fin de mois, dans chaque
    famille, poids = rang du signal - rang moyen (achat des meilleurs, vente des moins bons), risque
    egal par famille (10 % prevu avec la covariance des 126 derniers jours), familles a poids egal."""

    def __init__(self, fenetre=126):
        r = rendements()
        self.r = r
        jours = r.index
        self.fins = pd.DatetimeIndex(pd.Series(jours, index=jours).groupby(jours.to_period("M")).last().values)
        idx = jours.get_indexer(self.fins)
        R, dispo = r.fillna(0).values, r.notna().values
        vol = S.volatilite(r).values[idx]
        n = r.shape[1]
        self.ok = np.zeros((len(idx), n), bool)
        self.cov = np.full((len(idx), n, n), np.nan)
        for t, i in enumerate(idx):
            if i >= fenetre:
                self.ok[t] = dispo[i - fenetre + 1:i + 1].all(axis=0) & ~np.isnan(vol[t])
                self.cov[t] = np.cov(R[i - fenetre + 1:i + 1].T) * JOURS_AN
        self.vol = vol
        self.groupes = [np.array([j for j, c in enumerate(r.columns) if FAMILLE[c] == f]) for f in FAMILLES_CROISEES]
        indice = (1 + r.fillna(0)).cumprod().where(r.notna())
        self.prix_mois = indice.reindex(self.fins)             # niveau en fin de mois

    def positions(self, signal):
        pos = np.zeros(signal.shape)
        for t in range(len(self.fins)):
            parts = []
            for g in self.groupes:
                sel = g[self.ok[t, g] & ~np.isnan(signal[t, g])]
                if len(sel) < 2:
                    continue
                rang = rankdata(signal[t, sel])
                w = rang - rang.mean()
                if not np.abs(w).sum():
                    continue
                w = w / np.abs(w).sum() * 2 / self.vol[t, sel]
                var = w @ self.cov[t][np.ix_(sel, sel)] @ w
                if var > 0:
                    parts.append((sel, w * 0.10 / np.sqrt(var)))
            for sel, w in parts:
                pos[t, sel] = w / len(parts)
        return pd.DataFrame(pos, index=self.fins, columns=self.r.columns)

    def rendement(self, pos):
        r = self.r
        P = pos.reindex(r.index).ffill().fillna(0)
        brut = (P.shift(1) * r.fillna(0)).sum(axis=1)
        frais = (pos.diff().abs().fillna(pos.abs()) * COUT[pos.columns]).sum(axis=1)
        frais = frais.reindex(r.index).fillna(0).shift(1).fillna(0)
        net = brut - frais
        return net[net.index >= pos.index[(pos.abs().sum(axis=1) > 0).values.argmax()]]

    def source(self, signal):
        s = signal.values

        def placebo(rng):   # signal decale au hasard dans le temps (garde sa structure, casse le lien)
            k = rng.integers(12, len(s) - 12)
            return self.rendement(self.positions(np.roll(s, k, axis=0)))
        return self.rendement(self.positions(s)), placebo


@lru_cache(None)
def croise():
    return Croise()


def momentum_croise():
    c = croise()
    m = c.prix_mois
    signal = m.shift(1) / m.shift(12) - 1          # rendement sur 12 mois, sans le dernier mois
    return c.source(signal)


def valeur():
    c = croise()
    m = c.prix_mois
    signal = np.log(m.rolling(13).mean().shift(54) / m)   # prix moyen d'il y a 4,5 a 5,5 ans / prix actuel
    return c.source(signal)


# ----------------------------------------------------------------------------- actions
def _indice_actions():
    eq = rendements()[ACTIONS].mean(axis=1)
    return eq[eq.index >= eq.first_valid_index()].fillna(0)


def vol_geree():
    """Moreira et Muir (2017) : exposition du mois = 1 / variance realisee du mois precedent."""
    eq = _indice_actions()
    mois = eq.index.to_period("M")
    rv = eq.pow(2).groupby(mois).sum()
    w = (1 / rv).shift(1)
    w = (w / w.expanding(12).median()).clip(upper=2.5).dropna()
    cout = COUT[ACTIONS].mean()

    def serie(wm):
        wd = pd.Series(wm.reindex(mois).values, index=eq.index)
        frais = (wm.diff().abs() * cout).reindex(mois).values
        premier = ~pd.Series(mois).duplicated().values
        net = wd * eq - np.where(premier, np.nan_to_num(frais), 0)
        return net.dropna()

    def placebo(rng):   # memes expositions, attribuees aux mois au hasard
        return serie(pd.Series(rng.permutation(w.values), index=w.index))
    return serie(w), placebo


def tournant_du_mois():
    """McConnell et Xu (2008) : acheter les actions du dernier jour du mois au 3e jour du mois suivant."""
    eq = _indice_actions()
    mois = eq.index.to_period("M")
    g = pd.Series(1, index=eq.index).groupby(mois)
    debut, fin = g.cumcount().values, g.cumcount(ascending=False).values
    cout = COUT[ACTIONS].mean()
    taille = pd.Series(mois).groupby(mois).transform("size").values

    def serie(dedans):
        entree = dedans & ~np.r_[False, dedans[:-1]]
        sortie = dedans & ~np.r_[dedans[1:], False]
        return pd.Series(eq.values * dedans - cout * (entree.astype(float) + sortie), index=eq.index)

    def placebo(rng):   # 4 jours de suite places au hasard dans chaque mois
        depart = {p: rng.integers(0, max(1, n - 3)) for p, n in zip(mois, taille)}
        d0 = np.array([depart[p] for p in mois])
        return serie((debut >= d0) & (debut < d0 + 4))
    return serie((fin == 0) | (debut <= 2)), placebo


def veille_fomc():
    """Lucca et Moench (2015) : acheter le S&P de 14 h la veille d'une annonce programmee du FOMC
    jusqu'a juste avant l'annonce (13 h 55 ; 12 h en 2011-2012, annonces parfois a 12 h 30)."""
    J, O, H, L, C, P, X = intraday("sp500")
    cout = ST.cout_aller_retour("sp500")
    fin = np.where(J.year <= 2012, 150, 265)
    p0 = np.r_[np.nan, C[:-1, 270]]
    p1 = C[np.arange(len(J)), fin]
    assez = P.sum(axis=1) >= 300
    valide = np.r_[False, assez[:-1]] & assez & ~X["echeance"]
    valide &= np.r_[False, (J[1:] - J[:-1]).days <= 4]
    fenetre = np.where(valide, (p1 - p0 - cout) / p0, np.nan)
    annonces = J.isin(fomc.annonces())
    cal = rendements().index

    def serie(jours_choisis):
        s = pd.Series(np.where(jours_choisis & valide, fenetre, 0.0), index=J)
        return s.reindex(cal).fillna(0)[cal >= J[0]]

    candidats = np.where(valide & ~annonces & ~np.r_[annonces[1:], False])[0]
    par_an = pd.Series(annonces & valide, index=J).groupby(J.year).sum()

    def placebo(rng):   # autant de jours tires au hasard, chaque annee
        choix = np.zeros(len(J), bool)
        for a, n in par_an.items():
            pool = candidats[J[candidats].year == a]
            choix[rng.choice(pool, size=min(int(n), len(pool)), replace=False)] = True
        return serie(choix)
    return serie(annonces), placebo


SOURCES = [
    Source("achat", "Acheter tout, tout le temps", "prime de risque : chaque marche au meme risque, jamais vendeur",
           "Asness, Frazzini, Pedersen (2012), parite des risques", "2012-01-01", achat),
    Source("tendance", "Suivi de tendance", "acheter ce qui monte, vendre ce qui baisse, sur 19 marches",
           "Moskowitz, Ooi, Pedersen (2012), momentum de serie", "2012-05-01", tendance),
    Source("zone", "Zone de bruit Nasdaq", "suivre le Nasdaq quand il sort de son agitation normale du jour",
           "Zarattini, Aziz, Barbon (2024)", "2024-05-01", zone_de_bruit),
    Source("momentum", "Momentum croise", "dans chaque famille, acheter les marches qui ont le plus monte sur 12 mois, vendre les autres",
           "Asness, Moskowitz, Pedersen (2013), Value and Momentum Everywhere", "2013-06-01", momentum_croise),
    Source("valeur", "Valeur (retour sur 5 ans)", "dans chaque famille, acheter les marches les plus baisses sur 5 ans, vendre les autres",
           "Asness, Moskowitz, Pedersen (2013), Value and Momentum Everywhere", "2013-06-01", valeur),
    Source("volgeree", "Actions pilotees par la volatilite", "moins d'actions apres un mois agite, plus apres un mois calme",
           "Moreira, Muir (2017), Volatility-Managed Portfolios", "2017-08-01", vol_geree),
    Source("tom", "Tournant du mois", "acheter les actions du dernier jour du mois au 3e jour du suivant",
           "McConnell, Xu (2008), Equity Returns at the Turn of the Month", "2008-01-01", tournant_du_mois),
    Source("fomc", "Veille de la Fed", "acheter le S&P les 24 h avant une annonce programmee de la Fed",
           "Lucca, Moench (2015), The Pre-FOMC Announcement Drift", "2015-02-01", veille_fomc),
]
