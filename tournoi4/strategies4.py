"""Strategies du tournoi n°4 (README.md) sur les tableaux minute (seances x 390) de intraday/strategies.py charger.
Chaque fonction renvoie les points nets de frais par seance (0 sans trade) ; la paire renvoie des rendements."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

ICI = Path(__file__).resolve().parent
R = ICI.parent
sys.path.insert(0, str(R / "tournoi"))
sys.path.insert(0, str(R / "tournoi2"))
sys.path.insert(0, str(R / "evolution2"))
import concurrents as K1  # noqa: E402
import tournoi3 as T3  # noqa: E402  (rejet, veille, quantile_252, lire_quotidien)

st = K1.st
N = 390
NAN = np.nan


# ---------------------------------------------------------------- range de la nuit

def range_nuit(fichier, J, contrat):
    """Plus haut et plus bas de la nuit (barres d'une heure de 18 h la veille a 8 h, meme contrat que la seance)."""
    h = pd.read_csv(R / "nuit" / "donnees" / f"{fichier}_1h.csv.gz")
    t = pd.to_datetime(h["t"])
    heure = t.dt.hour
    garde = (heure >= 18) | (heure < 9)
    h, t = h[garde], t[garde]
    seance = (t.dt.normalize() + pd.to_timedelta((t.dt.hour >= 18).astype(int), unit="D")).values
    g = pd.DataFrame({"seance": seance, "contrat": h["contrat"].values, "h": h["h"].values, "l": h["l"].values})
    g = g.groupby(["seance", "contrat"]).agg(h=("h", "max"), l=("l", "min"), n=("h", "size"))
    cle = pd.MultiIndex.from_arrays([pd.DatetimeIndex(J), contrat if contrat is not None else np.zeros(len(J), int)])
    g = g.reindex(cle)
    ok = g["n"].values >= 8                              # au moins 8 heures de nuit
    return np.where(ok, g["h"].values, NAN), np.where(ok, g["l"].values, NAN)


# ---------------------------------------------------------------- briques

def quantile_valides(x, q):
    """Quantile q des 252 valeurs existantes precedentes (les seances sans valeur, par exemple un changement
    d'echeance, sont sautees au lieu d'annuler toute la fenetre)."""
    v = np.isfinite(x)
    out = np.full(len(x), NAN)
    out[v] = pd.Series(x[v]).rolling(252, min_periods=252).quantile(q).shift(1).values
    return out


def meme_demi_heure(O, C, ok, cout, complete, tranches):
    """Heston-Korajczyk-Sadka : pour chaque demi-heure k de tranches, dans le sens de la moyenne de cette demi-heure sur
    les 20 seances completes precedentes ; entree a l'ouverture de la demi-heure, sortie a sa derniere cloture."""
    nd = len(O)
    rien = np.full(nd, NAN)
    out = np.zeros(nd)
    for k in tranches:
        a, b = 30 * k, 30 * k + 29
        r = C[:, b] / O[:, a] - 1
        moy = K1.glissant_complet(r, complete, 20)
        s = np.sign(np.nan_to_num(moy)).astype(np.int64)
        out += K1.entree_fixe(O, C, C, C, ok, cout, s, a, rien, rien, b)       # ni stop ni objectif : H et L inutiles
    return out


def mois_en_cours(J, C, complete, contrat):
    """Mouvement du mois en cours a l'ouverture de chaque seance (cloture de la derniere seance du mois precedent ->
    cloture de la veille), en chainant les rendements de cloture a cloture sans jamais melanger deux contrats."""
    nd = len(J)
    prec = K1.precedente(complete, contrat)
    r = np.where(prec >= 0, C[:, N - 1] / K1.de_la(C[:, N - 1], prec) - 1, 0.0)    # rendement de la seance d (meme contrat)
    r = np.where(complete, np.nan_to_num(r), 0.0)
    mois = pd.DatetimeIndex(J).to_period("M")
    cum = np.zeros(nd)
    acc, m_cour = 0.0, None
    for d in range(nd):
        if mois[d] != m_cour:
            m_cour, acc = mois[d], 0.0                  # nouvelle seance d'un nouveau mois : rien de cumule avant elle
        cum[d] = acc                                    # connu a l'ouverture de d : seances du mois avant d
        acc = (1 + acc) * (1 + r[d]) - 1
    return cum


def derniers_jours(J, complete, n=4):
    """Vrai pour les n dernieres seances completes de chaque mois."""
    nd = len(J)
    ic = np.where(complete)[0]
    mois = pd.DatetimeIndex(J)[ic].to_period("M")
    depuis_fin = pd.Series(np.arange(len(ic))[::-1]).groupby(mois[::-1]).cumcount().values[::-1]
    out = np.zeros(nd, bool)
    out[ic] = depuis_fin < n
    return out


def logistique(X, y, lam=1.0, iterations=25):
    """Regression logistique (Newton), penalite L2 lam sur les coefficients (pas sur la constante)."""
    Xb = np.c_[np.ones(len(X)), X]
    w = np.zeros(Xb.shape[1])
    P = lam * np.eye(Xb.shape[1])
    P[0, 0] = 0.0
    for _ in range(iterations):
        p = 1 / (1 + np.exp(-Xb @ w))
        g = Xb.T @ (p - y) + P @ w
        Hs = Xb.T @ (Xb * (p * (1 - p))[:, None]) + P
        w -= np.linalg.solve(Hs, g)
    return w


def variables(J, O, H, L, C, X, complete, Q):
    """Les 8 variables connues a 10 h (README.md, strategie 8) et la cible (10 h -> 16 h en hausse)."""
    prec = K1.precedente(complete, X.get("contrat"))
    pc = K1.de_la(C[:, N - 1], prec)
    v30 = X["V"][:, :30].sum(axis=1)
    amp = H.max(axis=1) - L.min(axis=1)
    F = np.c_[O[:, 0] / pc - 1,
              C[:, 29] / O[:, 0] - 1,
              np.log(np.maximum(v30, 1) / K1.glissant_complet(np.maximum(v30, 1), complete, 20)),
              K1.de_la(C[:, N - 1] / O[:, 0] - 1, prec),
              K1.de_la(amp, prec) / K1.glissant_complet(amp, complete, 20),
              T3.veille(J, Q["vix_ratio"]), T3.veille(J, Q["gex"]), T3.veille(J, Q["dix"])]
    y = (C[:, N - 1] > O[:, 30]).astype(float)
    return F, y


def modele_appris(J, O, H, L, C, X, ok, complete, Q, apprendre=None):
    """Sens a 10 h (+1, -1, 0) donne par la regression logistique reentrainee chaque 1er janvier sur les annees passees.
    apprendre : (F, y) d'autres donnees pour l'apprentissage (par defaut, les memes seances)."""
    nd = len(J)
    F, y = variables(J, O, H, L, C, X, complete, Q)
    Fa, ya = apprendre if apprendre is not None else (F, y)
    utilisable = ok & np.all(np.isfinite(F), axis=1)
    util_a = ok & np.all(np.isfinite(Fa), axis=1)
    annee = pd.DatetimeIndex(J).year.values
    sens = np.zeros(nd, np.int64)
    for a in range(2013, annee.max() + 1):
        app = util_a & (annee < a)
        jeu = utilisable & (annee == a)
        if app.sum() < 200 or not jeu.any():
            continue
        mu, sd = Fa[app].mean(axis=0), Fa[app].std(axis=0)
        sd[sd == 0] = 1
        w = logistique((Fa[app] - mu) / sd, ya[app])
        p = 1 / (1 + np.exp(-(w[0] + ((F[jeu] - mu) / sd) @ w[1:])))
        sens[jeu] = np.where(p > 0.55, 1, np.where(p < 0.45, -1, 0))
    return sens


def toutes(J, O, H, L, C, P, X, cout, Q, nuit):
    """Points nets par seance des 8 strategies, ok, et pour les strategies 3 et 7 leur base et leur filtre."""
    complete = st.journees_completes(P)
    ok = complete & ~X["echeance"]
    nd = len(J)
    o0 = O[:, 0]
    rien = np.full(nd, NAN)
    prec = K1.precedente(complete, X.get("contrat"))
    res = {}
    res["1"] = meme_demi_heure(O, C, ok, cout, complete, (0, 12))
    res["2"] = meme_demi_heure(O, C, ok, cout, complete, range(13))
    mtd = mois_en_cours(J, C, complete, X.get("contrat"))
    grand = np.abs(mtd) >= T3.quantile_252(np.abs(mtd), 2 / 3)
    f3 = derniers_jours(J, complete) & np.nan_to_num(grand, nan=0).astype(bool) & (mtd != 0)
    base3 = K1.entree_fixe(O, H, L, C, ok, cout, (-np.sign(mtd)).astype(np.int64), 0, rien, rien, N - 1)
    res["3"] = np.where(f3, base3, 0.0)
    r = C[:, 359] / o0 - 1
    grand4 = np.abs(r) >= T3.quantile_252(np.abs(r), 0.8)
    s4 = np.where(np.nan_to_num(grand4, nan=0).astype(bool), np.sign(r), 0).astype(np.int64)
    res["4"] = K1.entree_fixe(O, H, L, C, ok, cout, s4, 360, rien, rien, N - 1)
    onh, onl = nuit
    mil = (onh + onl) / 2
    res["5"] = K1.cassure(O, H, L, C, ok, cout, onh, onl, mil, mil, 0)
    dedans = (o0 >= onl) & (o0 <= onh)
    q = (onh - onl) / 4
    res["6"] = T3.rejet(O, H, L, C, ok & dedans, cout, np.where(dedans, onh, NAN), np.where(dedans, onl, NAN), onh + q, onl - q, mil, mil)
    rv = K1.de_la(C[:, N - 1] / o0 - 1, prec)
    q7 = quantile_valides(rv, 0.1)
    f7 = np.nan_to_num(rv <= q7, nan=0).astype(bool)
    base7 = K1.entree_fixe(O, H, L, C, ok, cout, np.ones(nd, np.int64), 0, rien, rien, N - 1)
    res["7"] = np.where(f7, base7, 0.0)
    s8 = modele_appris(J, O, H, L, C, X, ok, complete, Q)
    res["8"] = K1.entree_fixe(O, H, L, C, ok, cout, s8, 30, rien, rien, N - 1)
    # tirages au hasard (etape 3) : parmi les seances ou le signal existe, meme sens que la strategie
    jours = {"3": (base3, f3, np.isfinite(T3.quantile_252(np.abs(mtd), 2 / 3)) & (mtd != 0)),
             "7": (base7, f7, np.isfinite(q7) & np.isfinite(rv))}
    return res, ok, jours


# ---------------------------------------------------------------- paire en continuation (hypothese jugee sur le coffre)

@njit(cache=True)
def _paire_suivre(Oa, Ca, Ob, Cb, ok, seuil, cout_a, cout_b):
    """Comme la paire du tournoi n°2 (memes points de controle, meme seuil, sortie quand l'ecart repasse 0 ou a 16 h),
    mais achat du plus fort et vente du plus faible."""
    nd = Oa.shape[0]
    out = np.zeros(nd)
    for d in range(nd):
        if not ok[d] or np.isnan(seuil[d]):
            continue
        pos = 0
        ea = 0.0
        eb = 0.0
        tot = 0.0
        for m in range(30, N):
            x = np.log(Ca[d, m - 1] / Oa[d, 0]) - np.log(Cb[d, m - 1] / Ob[d, 0])
            if pos != 0 and x * pos <= 0:
                tot += 0.5 * (pos * (Oa[d, m] / ea - 1) - pos * (Ob[d, m] / eb - 1))
                pos = 0
            if pos == 0 and m % 30 == 0 and m <= 330 and abs(x) > seuil[d]:
                pos = 1 if x > 0 else -1               # +1 : a plus fort, achat de a, vente de b
                ea, eb = Oa[d, m], Ob[d, m]
                tot -= 0.5 * (cout_a / ea + cout_b / eb)
        if pos != 0:
            tot += 0.5 * (pos * (Ca[d, N - 1] / ea - 1) - pos * (Cb[d, N - 1] / eb - 1))
        out[d] = tot
    return out


def paire_suivre(a, b, cout_a, cout_b):
    Ja, Oa, _, _, Ca, Pa, Xa = a
    _, Ob, _, _, Cb, Pb, Xb = b
    complete = st.journees_completes(Pa) & st.journees_completes(Pb)
    ok = complete & ~Xa["echeance"] & ~Xb["echeance"]
    fin = np.log(Ca[:, N - 1] / Oa[:, 0]) - np.log(Cb[:, N - 1] / Ob[:, 0])
    seuil = 1.5 * K1.glissant_complet(fin, complete, 20, "std")
    return _paire_suivre(Oa, Ca, Ob, Cb, ok, seuil, cout_a, cout_b), ok
