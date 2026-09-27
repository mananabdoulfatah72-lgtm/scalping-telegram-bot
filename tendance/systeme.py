#!/usr/bin/env python3
"""Systeme de suivi de tendance multi-marches (methode des fonds "CTA").

Principe, avec des reglages classiques fixes a l'avance (non optimises sur les donnees) :
- signal : croisements de moyennes mobiles exponentielles 16/64, 32/128 et 64/256 jours,
  normalises par la volatilite (methode EWMAC de Robert Carver), plafonnes a +/-20 ;
- taille : chaque marche vise le meme risque, les 6 familles de marches pesent autant ;
- re-equilibrage chaque semaine (cours du vendredi), avec une marge de 10 % pour eviter
  les petits ajustements ;
- rendements "futures" : rendement de l'ETF moins le taux court (le contrat futures ne
  rapporte pas d'interets), et rendement au comptant moins 7 %/an de cout de portage pour
  BTC et ETH.
"""
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

DONNEES = Path(__file__).parent / "donnees" / "prix.csv.gz"
JOURS_AN = 252


@dataclass(frozen=True)
class Marche:
    nom: str
    famille: str
    source: str        # serie utilisee pour les rendements
    futures: str       # futures en continu (Yahoo) pour la taille du contrat, ou None
    micro: str         # contrat micro CME
    multiplicateur: float  # $ par point du futures ; si futures est None : valeur fixe du contrat en $
    cout_pb: float     # cout d'un aller simple, en points de base du montant echange


MARCHES = [
    Marche("S&P 500", "actions", "SPY", "ES=F", "MES", 5, 1.5),
    Marche("Nasdaq 100", "actions", "QQQ", "NQ=F", "MNQ", 2, 1.5),
    Marche("Russell 2000", "actions", "IWM", "RTY=F", "M2K", 5, 2.0),
    Marche("Taux 2 ans", "obligations", "SHY", None, "2YY", 52_000, 2.0),
    Marche("Taux 10 ans", "obligations", "IEF", None, "10Y", 13_300, 2.0),
    Marche("Taux 30 ans", "obligations", "TLT", None, "30Y", 5_900, 2.0),
    Marche("Euro", "devises", "FXE", "6E=F", "M6E", 12_500, 1.5),
    Marche("Dollar australien", "devises", "FXA", "6A=F", "M6A", 10_000, 2.0),
    Marche("Livre sterling", "devises", "FXB", "6B=F", "M6B", 6_250, 2.0),
    Marche("Yen", "devises", "FXY", "6J=F", "MJY", 1_250_000, 2.0),
    Marche("Dollar canadien", "devises", "FXC", "6C=F", "MCD", 10_000, 2.0),
    Marche("Franc suisse", "devises", "FXF", "6S=F", "MSF", 12_500, 2.0),
    Marche("Or", "metaux", "GLD", "GC=F", "MGC", 10, 2.0),
    Marche("Argent", "metaux", "SLV", "SI=F", "SIL", 1_000, 4.0),
    Marche("Cuivre", "metaux", "CPER", "HG=F", "MHG", 2_500, 4.0),
    Marche("Petrole", "energie", "USO", "CL=F", "MCL", 100, 4.0),
    Marche("Gaz naturel", "energie", "UNG", "NG=F", "MNG", 1_000, 8.0),
    Marche("Bitcoin", "crypto", "BTC-USD", "BTC=F", "MBT", 0.1, 6.0),
    Marche("Ether", "crypto", "ETH-USD", "ETH=F", "MET", 0.1, 30.0),
]
PORTAGE_CRYPTO = 0.07   # cout annuel des futures BTC/ETH par rapport au comptant


def charger():
    d = pd.read_csv(DONNEES, parse_dates=["date"])
    close = d.pivot(index="date", columns="ticker", values="close")
    adj = d.pivot(index="date", columns="ticker", values="adjclose")
    return close, adj


def rendements_futures(close, adj, marches=MARCHES):
    """Rendements journaliers 'excedentaires' (comme un futures), calendrier de la bourse US."""
    jours = adj["SPY"].dropna().index
    taux = (close["^IRX"].reindex(jours).ffill() / 100 / JOURS_AN).fillna(0)
    r = {}
    for m in marches:
        prix = adj[m.source].dropna()
        if m.famille == "crypto":
            prix = prix.reindex(jours, method="ffill")
            rr = prix.pct_change() - PORTAGE_CRYPTO / JOURS_AN
        else:
            prix = prix.reindex(jours)
            rr = prix.pct_change() - taux
        premier = adj[m.source].first_valid_index()
        rr[rr.index <= premier] = np.nan
        r[m.nom] = rr
    return pd.DataFrame(r)


def valeur_contrat(close, marches=MARCHES):
    """Valeur en $ d'un contrat micro, jour par jour."""
    jours = close["SPY"].dropna().index
    v = {}
    for m in marches:
        if m.futures is None:
            v[m.nom] = pd.Series(float(m.multiplicateur), index=jours)
        else:
            v[m.nom] = close[m.futures].reindex(jours).ffill() * m.multiplicateur
    return pd.DataFrame(v)


def prevision(r, vitesses=(16, 32, 64)):
    """Force de la tendance, entre -20 et +20 (10 = tendance moyenne)."""
    echelle = {2: 12.1, 4: 8.53, 8: 5.95, 16: 4.10, 32: 2.79, 64: 1.91}
    prix = (1 + r.fillna(0)).cumprod().where(r.notna())
    vol_prix = prix * r.ewm(span=36, min_periods=20).std()
    f = []
    for v in vitesses:
        brut = (prix.ewm(span=v, min_periods=v).mean() - prix.ewm(span=4 * v, min_periods=4 * v).mean()) / vol_prix
        f.append((brut * echelle[v]).clip(-20, 20))
    fdm = {1: 1.0, 2: 1.1, 3: 1.15}.get(len(vitesses), 1.2)
    return (sum(f) / len(f) * fdm).clip(-20, 20)


def volatilite(r):
    """Volatilite annuelle prevue : 70 % recente + 30 % moyenne longue."""
    court = r.ewm(span=36, min_periods=20).std()
    long_ = court.rolling(2520, min_periods=252).mean()
    return (0.7 * court + 0.3 * long_.fillna(court)) * np.sqrt(JOURS_AN)


def poids(r, marches=MARCHES, exclure=()):
    """Poids par marche : familles egales, marches egaux dans chaque famille (marches disponibles)."""
    dispo = r.notna().rolling(256).sum() >= 256
    fam = pd.Series({m.nom: m.famille for m in marches})
    w = pd.DataFrame(0.0, index=r.index, columns=r.columns)
    actifs = dispo.copy()
    for c in exclure:
        actifs[fam.index[fam == c]] = False
    nb_fam = actifs.T.groupby(fam).any().T.sum(axis=1)
    for c in fam.unique():
        cols = fam.index[fam == c]
        n = actifs[cols].sum(axis=1)
        part = (1 / nb_fam.replace(0, np.nan)) / n.replace(0, np.nan)
        w[cols] = actifs[cols].mul(part, axis=0)
    return w.fillna(0)


def multiplicateur_diversification(r, w):
    """IDM = 1 / sqrt(w' C w), correlations des rendements hebdo sur 2 ans (negatives -> 0), max 2,5."""
    hebdo = (1 + r.fillna(0)).resample("W-FRI").prod() - 1
    hebdo = hebdo.where(r.notna().resample("W-FRI").last())
    idm = pd.Series(np.nan, index=hebdo.index)
    for i in range(104, len(hebdo), 4):
        bloc = hebdo.iloc[i - 104:i]
        c = bloc.corr(min_periods=52).clip(lower=0).fillna(0).values.copy()
        np.fill_diagonal(c, 1.0)
        ww = w.reindex([hebdo.index[i]], method="ffill").values[0]
        if ww.sum() == 0:
            continue
        idm.iloc[i] = min(2.5, 1 / np.sqrt(ww @ c @ ww))
    return idm.ffill().reindex(r.index, method="ffill").fillna(1.0)


def backtest(r, cible=0.20, vitesses=(16, 32, 64), marches=MARCHES, exclure=(), multi_couts=1.0,
             frequence="W-FRI", marge=0.10, toujours_acheteur=False):
    """Renvoie (rendement quotidien du portefeuille, positions en fraction du capital, couts).
    toujours_acheteur=True : portefeuille qui achete tout, tout le temps (prevision fixe +10)."""
    if toujours_acheteur:
        f = pd.DataFrame(10.0, index=r.index, columns=r.columns).where(r.notna())
    else:
        f = prevision(r, vitesses)
    vol = volatilite(r)
    w = poids(r, marches, exclure)
    idm = multiplicateur_diversification(r, w)
    moyenne = w.mul(idm, axis=0) * cible / vol           # position pour une prevision de 10
    cible_pos = (f / 10 * moyenne).fillna(0)
    periode = cible_pos.index.to_period(frequence).asi8
    reeq = np.r_[periode[:-1] != periode[1:], True]       # dernier jour de bourse de chaque periode
    pos = np.zeros(cible_pos.shape[1])
    positions = np.zeros(cible_pos.shape)
    couts = np.zeros(len(cible_pos))
    cout_pb = np.array([m.cout_pb for m in marches]) / 1e4 * multi_couts
    moy = moyenne.fillna(0).values
    tgt = cible_pos.values
    for t in range(len(cible_pos)):
        if reeq[t]:
            ecart = tgt[t] - pos
            bouge = np.abs(ecart) > marge * np.abs(moy[t])
            nouveau = np.where(bouge, tgt[t], pos)
            couts[t] = np.sum(np.abs(nouveau - pos) * cout_pb)
            pos = nouveau
        positions[t] = pos
    positions = pd.DataFrame(positions, index=cible_pos.index, columns=cible_pos.columns)
    brut = (positions.shift(1) * r.fillna(0)).sum(axis=1)
    net = brut - pd.Series(couts, index=r.index).shift(1).fillna(0)
    return net, positions, pd.Series(couts, index=r.index)


# Melange 50/50 : autant de risque dans la tendance et dans l'achat permanent. Les deux etant presque
# independants (correlation 0,035 sur 2007-2026), le melange est moins risque que chacun : on le
# remultiplie par 1 / racine((1 + 0,035) / 2) = 1,39 pour revenir au risque vise.
MULT_MELANGE = 1.39


def positions_melange(r, **kw):
    """Positions (fraction du capital, pour 20 % de risque) du melange 50/50 tendance + achat permanent."""
    _, tendance, _ = backtest(r, **kw)
    _, achat, _ = backtest(r, toujours_acheteur=True, **kw)
    return (tendance + achat) / 2 * MULT_MELANGE, tendance


def stats(x, nom=""):
    x = x.dropna()
    x = x[x.index >= x.ne(0).idxmax()]
    an = x.mean() * JOURS_AN
    vol = x.std() * np.sqrt(JOURS_AN)
    cumul = (1 + x).cumprod()
    baisse = (cumul / cumul.cummax() - 1).min()
    annees = x.groupby(x.index.year).apply(lambda y: (1 + y).prod() - 1)
    return {
        "nom": nom, "debut": x.index[0].date(), "sharpe": an / vol if vol else np.nan,
        "rendement_an": an, "vol_an": vol, "pire_baisse": baisse,
        "annees_positives": (annees > 0).mean(), "pire_annee": annees.min(),
        "pire_jour": x.min(), "annees": annees,
    }


def contrats_optimises(r, positions, cv, capital, vol_visee, echelles=(1.0,), jours=None):
    """Petits comptes : a chaque re-equilibrage, cherche les contrats entiers dont le portefeuille est
    le plus proche du portefeuille ideal (ecart de risque minimal, covariance des 12 derniers mois).
    Methode 'gloutonne' : on ajoute ou retire 1 contrat a la fois tant que l'ecart diminue.
    Renvoie {echelle: DataFrame de contrats} aux jours de re-equilibrage."""
    R = r.fillna(0).values
    cvv = cv[r.columns].values
    ideal = (positions * capital * vol_visee / 0.20).values
    if jours is None:
        periode = r.index.to_period("W-FRI").asi8
        jours = np.where(np.r_[periode[:-1] != periode[1:], True])[0]
    res = {e: np.zeros((len(jours), R.shape[1])) for e in echelles}
    for j, t in enumerate(jours):
        if t < 260:
            continue
        cov = np.cov(R[t - 252:t + 1].T) + np.eye(R.shape[1]) * 1e-10
        cov_c = cov * np.outer(cvv, cvv)                  # covariance en $ par contrat
        for e in echelles:
            d = ideal[t] * e / cvv                        # contrats ideaux (fractionnaires)
            n = np.zeros_like(d)
            ecart = n - d
            g = cov_c @ ecart
            for _ in range(200):
                gain_plus = 2 * g + np.diag(cov_c)        # variation de l'ecart si +1 contrat
                gain_moins = -2 * g + np.diag(cov_c)      # si -1 contrat
                i_p, i_m = np.argmin(gain_plus), np.argmin(gain_moins)
                if min(gain_plus[i_p], gain_moins[i_m]) >= -1e-12:
                    break
                if gain_plus[i_p] <= gain_moins[i_m]:
                    n[i_p] += 1; g += cov_c[:, i_p]
                else:
                    n[i_m] -= 1; g -= cov_c[:, i_m]
            res[e][j] = n
    return {e: pd.DataFrame(v, index=r.index[jours], columns=r.columns) for e, v in res.items()}
