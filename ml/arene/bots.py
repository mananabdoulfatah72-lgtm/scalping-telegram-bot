"""Trades des bots et rejeu jour par jour avec les regles du compte finance Bulenox (Master 50K, Option 2 : plancher suiveur
de 2 500 $ calcule en fin de journee et bloque a 50 100 $, limite de perte du jour de 1 100 $, constance 40 % au retrait).
Un trade = (seance, sens, premiere minute, derniere minute, prix d'entree, prix de sortie) ; le chemin minute par minute
(plus haut, plus bas) sert a la limite du jour du bot, a celle de la firme et au plancher."""
import os
import re
import sys
from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent))
import caracteristiques as K  # noqa: E402
import donnees as D  # noqa: E402

DEPART, PERTE_MAX, VERROU, DLL = 50000.0, 2500.0, 50100.0, 1100.0


class Base:
    """Minutes du NQ, seances, variables du bot XGBoost et ses probabilites hors echantillon (marche en avant purgee)."""
    def __init__(self, cache_p):
        self.X = K.construire()
        self.J = self.X["J"]; self.ok = self.X["ok"]; self.S = self.X["S"]
        _, self.O, self.H, self.L, self.C, _, _ = D.nq_minutes()
        self.an = np.array([int(j[:4]) for j in self.J])
        so = np.nonzero(self.ok)[0]
        self.test = so[self.an[so] >= 2014]                  # seances completes 2014 - 2026 (fenetre commune aux trois bots)
        self.p = np.load(cache_p)
        self.pos = {j: i for i, j in enumerate(self.J)}


def supertrend(B):
    st = pd.read_csv(ICI.parent / "st_trades.csv")
    out = []
    for r in st.itertuples():
        s = B.pos.get(r.jour)
        if s is None:
            continue
        fin = 384 if r.m_out >= 385 else r.m_out - 1          # sortie a la cloture de 15 h 54, sinon a l'ouverture de la minute
        out.append((s, int(r.sens), int(r.m_in), int(fin), float(r.entree), float(r.sortie)))
    return out


LIGNE = re.compile(r"^(\d{4}-\d{2}-\d{2}) (achat|vente|sortie|stop)\b(?: (\d+)h(\d+))?(?: (\d+)h(\d+))?.*? a ([0-9.]+)")


def zone(B):
    """Bot 3 en 1 (zone de bruit, filtres C2 + Q1) : journal de rejeu 2011 - 12 oct. 2026, puis vraies seances du 13 oct. au 2 nov."""
    out = []
    for f, de, a in ((ICI / "donnees/c2q1.txt", "2011-01-01", "2026-10-12"), (ICI / "donnees/zone.txt", "2026-10-13", "2026-11-02")):
        ouvert = None
        for l in f.read_text().splitlines():
            g = LIGNE.match(l)
            if not g or "ecarte" in l or "RSI" in l or not (de <= g.group(1) <= a):
                continue
            h, mi = int(g.group(5) or g.group(3)), int(g.group(6) or g.group(4))
            mm, px = h * 60 + mi - 570, float(g.group(7))
            if g.group(2) in ("achat", "vente"):
                ouvert = (g.group(1), 1 if g.group(2) == "achat" else -1, mm, px)
            elif ouvert:
                s = B.pos.get(ouvert[0])
                if s is not None:
                    out.append((s, ouvert[1], ouvert[2], min(389, max(ouvert[2], mm)), ouvert[3], px))
                ouvert = None
    return out


def xgboost(B, seuil=0.55, stop_atr=None, filtre=None, heures=None):
    """Bot XGBoost NQ : moyenne des 10 modeles, probabilites hors echantillon ; une position, 1 heure, entree a l'ouverture de
    la minute qui suit la bougie. Options des variantes : stop en ATR, filtre (fonction de la bougie), bougies autorisees."""
    X = B.X; F = X["F"]; sess, b, an = X["sess"], X["b"], X["an"]
    fut = np.r_[X["c"][4:], np.full(4, np.nan)]
    utile = B.ok[sess] & X["meme"] & np.isfinite(F[:, :21]).all(1) & np.isfinite(fut) & (an >= 2014)
    sig = np.where(B.p > seuil, 1, np.where(B.p < 1 - seuil, -1, 0)) * utile
    atr = X["I"]["atr"]
    out = []; libre = -1
    for i in np.nonzero(sig)[0]:
        if i <= libre:
            continue
        if heures is not None and b[i] not in heures:
            continue
        if filtre is not None and not filtre(i):
            continue
        s, bq, sens = sess[i], b[i], int(sig[i])
        m0, m1 = 15 * (bq + 1), 15 * (bq + 4) + 14
        e = B.O[s, m0]; x = B.C[s, m1]; fin = m1
        if stop_atr is not None:
            niv = e - sens * stop_atr * atr[i]
            for m in range(m0, m1 + 1):
                if m > m0 and (B.O[s, m] - niv) * sens <= 0:
                    x, fin = B.O[s, m], m; break
                if ((B.L[s, m] if sens > 0 else B.H[s, m]) - niv) * sens <= 0:
                    x, fin = niv - sens * 0.25, m; break
        out.append((s, sens, m0, fin, e, x))
        libre = i + 3 if fin == m1 else s * 26 + fin // 15
    return out


@nb.njit(cache=True)
def _journees(S, ts, tsens, tm0, tm1, te, tx, H, L, taille, limite, frais, pref):
    res = np.zeros(S); dip = np.zeros(S); ntr = np.zeros(S)
    k = 0; n = len(ts)
    while k < n:
        s = ts[k]; real = 0.0; creux = 0.0; arret = False
        while k < n and ts[k] == s:
            if not arret:
                sens = tsens[k]; e = te[k]; ech = 2.0 * pref / e * taille
                for m in range(tm0[k], tm1[k] + 1):
                    pire = L[s, m] if sens > 0 else H[s, m]
                    eq = real + sens * (pire - e) * ech
                    if eq < creux:
                        creux = eq
                    if eq <= -limite:
                        real = -limite - frais * taille; arret = True
                        break
                if not arret:
                    real += sens * (tx[k] - e) * ech - frais * taille
                    if real < creux:
                        creux = real
                ntr[s] += 1
            k += 1
        res[s] = real; dip[s] = creux
    return res, dip, ntr


def journees(B, trades, taille=1, limite=400.0, frais=D.FRAIS):
    """Resultat et pire moment de chaque seance (limite du bot et limite de la firme appliquees, trade en cours coupe)."""
    t = sorted(trades, key=lambda x: (x[0], x[2]))
    a = lambda k, ty: np.array([x[k] for x in t], dtype=ty)
    return _journees(B.S, a(0, np.int64), a(1, np.int64), a(2, np.int64), a(3, np.int64), a(4, np.float64), a(5, np.float64),
                     B.H, B.L, float(taille), float(min(limite, DLL)), float(frais), float(D.PREF))


@nb.njit(cache=True)
def _compte(res, dip, i0, horizon):
    """Compte finance neuf au jour i0 : (jour du plancher touche ou -1, profit final, meilleure journee)."""
    solde = 50000.0; haut = 50000.0; meilleur = 0.0
    fin = min(len(res), i0 + horizon)
    for i in range(i0, fin):
        plancher = min(haut - 2500.0, 50100.0)
        if solde + dip[i] <= plancher:
            return i - i0, solde - 50000.0, meilleur
        solde += res[i]
        if res[i] > meilleur:
            meilleur = res[i]
        if solde > haut:
            haut = solde                                   # le plancher ne bouge qu'en fin de journee
    return -1, solde - 50000.0, meilleur


@nb.njit(cache=True)
def _vie(res, dip, coussin, tous):
    """Vie reelle d'un compte finance, rejoue dans l'ordre : toutes les `tous` seances, si le solde depasse 50 000 + coussin et
    que la meilleure journee depuis le dernier retrait ne fait pas plus de 40 % du gain, on retire tout au-dessus de ce niveau.
    Un compte grille est remplace le lendemain par un compte neuf. Renvoie (retire, retraits, comptes grilles)."""
    solde = 50000.0; haut = 50000.0; base = 50000.0; meilleur = 0.0; depuis = 0
    retire = 0.0; nret = 0; grilles = 0
    for i in range(len(res)):
        plancher = min(haut - 2500.0, 50100.0)
        if solde + dip[i] <= plancher:
            grilles += 1; solde = 50000.0; haut = 50000.0; base = 50000.0; meilleur = 0.0; depuis = 0
            continue
        solde += res[i]; depuis += 1
        if res[i] > meilleur:
            meilleur = res[i]
        if solde > haut:
            haut = solde
        niveau = 50000.0 + coussin
        if depuis >= tous and solde > niveau and solde - base > 0 and meilleur <= 0.4 * (solde - base):
            retire += solde - niveau; nret += 1; solde = niveau; base = niveau; meilleur = 0.0; depuis = 0
    return retire, nret, grilles


def mesures(B, res, dip, horizon=60):
    j = res[B.test]; d = dip[B.test]; aj = B.an[B.test]; jours = [B.J[s] for s in B.test]
    t = lambda v: float(v.mean() / v.std(ddof=1) * np.sqrt(len(v))) if len(v) > 2 and v.std() > 0 else 0.0
    cum = np.cumsum(j)
    n = len(j); vivants = payes = 0; profits = []
    for i0 in range(0, n - horizon):
        g, pr, mb = _compte(j, d, i0, horizon)
        if g < 0:
            vivants += 1; profits.append(pr)
            if pr > 0 and mb <= 0.4 * pr:
                payes += 1
    m = n - horizon
    # vie reelle : retraits toutes les 20 seances au-dessus de 52 600 $ (plancher bloque a 50 100 $, 2 500 $ de marge gardee)
    retire, nret, grilles = _vie(j, d, 2600.0, 20)
    ans = len(j) / 252
    per = np.array([x >= "2026-08-11" for x in jours])
    return dict(par_seance=float(j.mean()), t=t(j), t_avant=t(j[aj <= 2022]), t_apres=t(j[aj >= 2023]), pire_baisse=float((cum - np.maximum.accumulate(cum)).min()),
                pire_jour=float(j.min()), survie_60=vivants / m, retrait_60=payes / m, profit_60=float(np.median(profits)) if profits else None,
                grilles=grilles, retraits=nret, retire_an=retire / ans, periode=float(j[per].sum()), seances_periode=int(per.sum()),
                jours_trades=int(np.count_nonzero(j)))
