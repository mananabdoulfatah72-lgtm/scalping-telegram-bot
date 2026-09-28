#!/usr/bin/env python3
"""Les sources de gain candidates du fonds.

Chaque source se construit en renvoyant (rendements journaliers nets de frais, placebo) :
- les rendements sont a une echelle libre : le moteur ramene chaque source au meme risque ;
- placebo(rng) renvoie les rendements nets d'une version ou le choix (quand / quoi acheter) est
  tire au hasard, ou None pour une prime de risque pure.
Les regles de chaque source sont celles des etudes citees ; aucun parametre n'est ajuste ici.
"""
import json
import re
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

    def __init__(self, r, famille, cout, familles, fenetre=126):
        self.r, self.cout = r, cout
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
                self.ok[t] = dispo[i - fenetre + 1:i + 1].mean(axis=0) >= 0.9
                self.ok[t] &= ~np.isnan(vol[t])
                self.cov[t] = np.cov(R[i - fenetre + 1:i + 1].T) * JOURS_AN
        self.vol = vol
        self.groupes = [np.array([j for j, c in enumerate(r.columns) if famille[c] == f]) for f in familles]
        self.groupes = [g for g in self.groupes if len(g)]
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

    def brut(self, pos):
        P = pos.reindex(self.r.index).ffill().fillna(0)
        return (P.shift(1) * self.r.fillna(0)).sum(axis=1)

    def frais(self, pos):
        f = (pos.diff().abs().fillna(pos.abs()) * self.cout[pos.columns]).sum(axis=1)
        return f.reindex(self.r.index).fillna(0).shift(1).fillna(0)

    def rendement(self, pos):
        net = self.brut(pos) - self.frais(pos)
        return net[net.index >= pos.index[(pos.abs().sum(axis=1) > 0).values.argmax()]]

    def source(self, signal):
        """Placebo v1 (phase 2) : signal decale au hasard dans le temps."""
        s = signal.values

        def placebo(rng):
            k = rng.integers(12, len(s) - 12)
            return self.rendement(self.positions(np.roll(s, k, axis=0)))
        return self.rendement(self.positions(s)), placebo

    def source_v2(self, signal):
        """Placebo v2 : memes positions, sens tire au hasard pour chaque marche chaque mois, memes frais."""
        pos = self.positions(signal.values)
        net = self.rendement(pos)
        frais = self.frais(pos)

        def placebo(rng):
            signes = pos * rng.choice([-1.0, 1.0], size=pos.shape)
            return (self.brut(signes) - frais).reindex(net.index)
        return net, placebo


@lru_cache(None)
def croise():
    return Croise(rendements(), FAMILLE, COUT, FAMILLES_CROISEES)


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


# ----------------------------------------------------------------------------- 40 futures CME (phase 3)
# famille, taille du tick, $ par point de prix (pour les frais : 1 tick + 2,50 $ par contrat et par ordre)
SPEC = {
    "ES": ("actions", 0.25, 50), "NQ": ("actions", 0.25, 20), "RTY": ("actions", 0.1, 50), "YM": ("actions", 1, 5),
    "NKD": ("actions", 5, 5),
    "ZT": ("obligations", 1 / 256, 2000), "ZF": ("obligations", 1 / 128, 1000), "ZN": ("obligations", 1 / 64, 1000),
    "TN": ("obligations", 1 / 64, 1000), "ZB": ("obligations", 1 / 32, 1000), "UB": ("obligations", 1 / 32, 1000),
    "6E": ("devises", 0.00005, 125000), "6J": ("devises", 0.0000005, 12500000), "6B": ("devises", 0.0001, 62500),
    "6A": ("devises", 0.00005, 100000), "6C": ("devises", 0.00005, 100000), "6S": ("devises", 0.00005, 125000),
    "6N": ("devises", 0.00005, 100000), "6M": ("devises", 0.00001, 500000),
    "CL": ("energie", 0.01, 1000), "BZ": ("energie", 0.01, 1000), "HO": ("energie", 0.0001, 42000),
    "RB": ("energie", 0.0001, 42000), "NG": ("energie", 0.001, 10000),
    "GC": ("metaux", 0.1, 100), "SI": ("metaux", 0.005, 5000), "HG": ("metaux", 0.0005, 25000),
    "PL": ("metaux", 0.1, 50), "PA": ("metaux", 0.5, 100),
    "ZC": ("agricoles", 0.25, 50), "ZW": ("agricoles", 0.25, 50), "ZS": ("agricoles", 0.25, 50),
    "ZM": ("agricoles", 0.1, 100), "ZL": ("agricoles", 0.01, 600), "KE": ("agricoles", 0.25, 50),
    "LE": ("betail", 0.025, 400), "HE": ("betail", 0.025, 400), "GF": ("betail", 0.025, 500),
    "BTC": ("crypto", 5, 5), "ETH": ("crypto", 0.25, 50),
}
FAMILLES_40 = ("actions", "obligations", "devises", "energie", "metaux", "agricoles", "betail")   # croise : sans crypto
MOIS_CODE = {c: i + 1 for i, c in enumerate("FGHJKMNQUVXZ")}


@lru_cache(None)
def _barres():
    d = pd.read_csv(ICI / "donnees" / "futures_1d.csv.gz", parse_dates=["date"])
    d["racine"] = d["symbole"].str.split(".").str[0]
    d["rang"] = d["symbole"].str[-1].astype(int)
    tab = {}
    for k in (0, 1):
        x = d[d["rang"] == k]
        tab[f"c{k}"] = x.pivot_table(index="date", columns="racine", values="c", aggfunc="last")
        tab[f"id{k}"] = x.pivot_table(index="date", columns="racine", values="contrat", aggfunc="last")
    cols = [r for r in SPEC if r in tab["c0"].columns]
    jours = tab["c0"].index
    return {k: v.reindex(index=jours, columns=cols) for k, v in tab.items()}


@lru_cache(None)
def futures40():
    """Rendements journaliers continus du contrat le plus echange : le jour ou il change, rendement du
    nouveau contrat depuis la veille (il etait alors le 2e). Renvoie (rendements, liste de Marche)."""
    b = _barres()
    colonnes = {}
    for n in b["c0"].columns:                        # chaque marche compare a SA seance precedente
        ok = b["c0"][n].notna()
        c0, c1, i0, i1 = (b[k][n][ok] for k in ("c0", "c1", "id0", "id1"))
        meme = i0.eq(i0.shift(1)).values
        roule = i0.eq(i1.shift(1)).values & ~meme
        rr = np.where(meme, c0 / c0.shift(1) - 1, np.where(roule, c0 / c1.shift(1) - 1, np.nan))
        positif = (c0 > 0) & (c0.shift(1) > 0) & (np.where(roule, c1.shift(1), 1) > 0)
        colonnes[n] = pd.Series(np.where(positif, rr, np.nan), index=c0.index)
    r = pd.DataFrame(colonnes).reindex(b["c0"].index)
    aberrant = r.abs() > 0.5
    if aberrant.values.any():
        print(f"  (donnees : {int(aberrant.values.sum())} rendements journaliers de plus de 50 % retires)")
    r = r.mask(aberrant)
    # jour sans cotation (jour ferie propre a ce marche, donnee manquante) : rendement nul, sinon le
    # moteur de systeme.py retirerait le marche du portefeuille pendant un an (il exige 256 jours pleins)
    for n in r.columns:
        a, z = r[n].first_valid_index(), r[n].last_valid_index()
        r.loc[a:z, n] = r.loc[a:z, n].fillna(0.0)
    prix = b["c0"].median()
    marches = [S.Marche(n, SPEC[n][0], n, None, "", SPEC[n][2],
                        float((SPEC[n][1] + 2.5 / SPEC[n][2]) / prix[n] * 1e4)) for n in r.columns]
    return r, marches


@lru_cache(None)
def croise40():
    r, M = futures40()
    return Croise(r, {m.nom: m.famille for m in M}, pd.Series({m.nom: m.cout_pb / 1e4 for m in M}), FAMILLES_40)


def _maturites():
    """Echeance (en annees decimales) de chaque contrat, d'apres son symbole (ex. CLZ5 = decembre 2025)."""
    noms = json.loads((ICI / "donnees" / "contrats.json").read_text())
    b = _barres()
    premier = {}
    for k in (0, 1):
        pile = b[f"id{k}"].stack().dropna()
        for (date, racine), i in pile.items():
            premier.setdefault((int(i), racine), date)
    mat = {}
    for (i, racine), date in premier.items():
        t = date.year + (date.month - 1) / 12
        options = []
        for brut in noms.get(str(i), []):            # un numero de contrat peut avoir servi plusieurs fois
            m = re.fullmatch(re.escape(racine) + r"([FGHJKMNQUVXZ])(\d{1,2})", brut)
            if m:
                y = int(m.group(2))
                annee = date.year + (y - date.year % 10) % 10 if len(m.group(2)) == 1 else 2000 + y
                options.append(annee + (MOIS_CODE[m.group(1)] - 1) / 12)
        options = [o for o in options if o >= t - 1 / 12]
        if options:
            mat[i] = min(options)                    # l'echeance la plus proche apres la date ou on le voit
    return mat


def carry40():
    """Carry croise (Koijen, Moskowitz, Pedersen, Vrugt 2018) : (ln F proche - ln F suivant) / ecart d'echeance."""
    b = _barres()
    mat = _maturites()
    m0 = b["id0"].apply(lambda col: col.map(lambda i: mat.get(int(i), np.nan) if pd.notna(i) else np.nan))
    m1 = b["id1"].apply(lambda col: col.map(lambda i: mat.get(int(i), np.nan) if pd.notna(i) else np.nan))
    ecart = (m1 - m0).where(lambda e: e.abs() > 0.01)
    carry = (np.log(b["c0"]) - np.log(b["c1"])) / ecart
    c = croise40()
    return c.source_v2(carry.reindex(c.fins))


def tendance40():
    r, M = futures40()
    net, pos, couts = S.backtest(r, marches=M)
    frais = couts.shift(1).fillna(0).values
    R, Q = r.fillna(0).values, pos.values
    _, semaine = np.unique(r.index.to_period("W-FRI").asi8, return_inverse=True)

    def placebo(rng):   # v2 : sens tire au hasard pour chaque marche chaque semaine, memes frais
        Z = Q * rng.choice([-1.0, 1.0], size=(semaine.max() + 1, Q.shape[1]))[semaine]
        brut = np.r_[0.0, (Z[:-1] * R[1:]).sum(axis=1)]
        return pd.Series(brut - frais, index=r.index)
    return net, placebo


def achat40():
    r, M = futures40()
    return S.backtest(r, marches=M, toujours_acheteur=True)[0], None


def momentum40():
    c = croise40()
    m = c.prix_mois
    return c.source_v2(m.shift(1) / m.shift(12) - 1)


def valeur40():
    c = croise40()
    m = c.prix_mois
    return c.source_v2(np.log(m.rolling(13).mean().shift(54) / m))


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
    annonces = J.isin(fomc.annonces())
    f = ICI / "donnees" / "es_v1_fomc.csv.gz"
    if f.exists():   # jour de changement d'echeance : prix de la veille pris sur le nouveau contrat (alors 2e)
        v1 = pd.read_csv(f).drop_duplicates("t", keep="last").set_index("t")
        for i in np.where(annonces & X["echeance"] & assez & np.r_[False, assez[:-1]])[0]:
            cle = f"{J[i - 1].date()} 14:00"
            if cle in v1.index and int(v1.at[cle, "contrat"]) == int(X["contrat"][i]):
                p0[i], valide[i] = v1.at[cle, "c"], True
    fenetre = np.where(valide, (p1 - p0 - cout) / p0, np.nan)
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


SOURCES_PHASE2 = [
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


SOURCES = [
    Source("achat40", "Acheter tout, tout le temps (40 futures)", "prime de risque : chaque marche au meme risque, jamais vendeur",
           "Asness, Frazzini, Pedersen (2012), parite des risques", "2012-01-01", achat40),
    Source("tendance40", "Suivi de tendance (40 futures)", "acheter ce qui monte, vendre ce qui baisse",
           "Moskowitz, Ooi, Pedersen (2012), momentum de serie", "2012-05-01", tendance40),
    Source("carry40", "Carry croise (40 futures)", "dans chaque famille, acheter les marches dont le contrat proche vaut plus que le suivant",
           "Koijen, Moskowitz, Pedersen, Vrugt (2018), Carry", "2018-05-01", carry40),
    Source("momentum40", "Momentum croise (40 futures)", "dans chaque famille, acheter les marches qui ont le plus monte sur 12 mois",
           "Asness, Moskowitz, Pedersen (2013), Value and Momentum Everywhere", "2013-06-01", momentum40),
    Source("valeur40", "Valeur, retour sur 5 ans (40 futures)", "dans chaque famille, acheter les marches les plus baisses sur 5 ans",
           "Asness, Moskowitz, Pedersen (2013), Value and Momentum Everywhere", "2013-06-01", valeur40),
    Source("zone", "Zone de bruit Nasdaq", "suivre le Nasdaq quand il sort de son agitation normale du jour",
           "Zarattini, Aziz, Barbon (2024)", "2024-05-01", zone_de_bruit),
    Source("volgeree", "Actions pilotees par la volatilite", "moins d'actions apres un mois agite, plus apres un mois calme",
           "Moreira, Muir (2017), Volatility-Managed Portfolios", "2017-08-01", vol_geree),
    Source("tom", "Tournant du mois", "acheter les actions du dernier jour du mois au 3e jour du suivant",
           "McConnell, Xu (2008), Equity Returns at the Turn of the Month", "2008-01-01", tournant_du_mois),
    Source("fomc", "Veille de la Fed", "acheter le S&P les 24 h avant une annonce programmee de la Fed",
           "Lucca, Moench (2015), The Pre-FOMC Announcement Drift", "2015-02-01", veille_fomc),
]
