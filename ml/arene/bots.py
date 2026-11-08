"""Trades des bots et rejeu jour par jour avec les regles du compte finance Bulenox (Master 50K, Option 2 : plancher suiveur
de 2 500 $ calcule en fin de journee et bloque a 50 100 $, limite de perte du jour de la firme 1 100 $, constance 40 % au
retrait). Version corrigee apres la double relecture (#ultrareview, ml/arene/VARIANTES.md, addendum).

Un trade = (seance, sens, minute d'entree, premiere minute du chemin, derniere minute du chemin, prix d'entree, prix de
sortie). Le chemin (plus haut, plus bas de chaque minute) ne contient que des prix posterieurs a l'entree et anterieurs a la
sortie : le Bot 3 en 1 entre a la cloture de sa minute (chemin des la minute suivante), le Supertrend et XGBoost a
l'ouverture ; un trade sorti a l'ouverture d'une minute ou par un stop s'arrete a la minute d'avant."""
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

DLL = 1100.0
GLISSEMENT = 1.0                                  # point de NQ perdu a une sortie forcee par la limite du jour


class Base:
    """Minutes du NQ, seances, variables du bot XGBoost et ses probabilites hors echantillon (marche en avant purgee)."""
    def __init__(self, cache_p):
        self.X = K.construire()
        self.J = self.X["J"]; self.ok = self.X["ok"]; self.S = self.X["S"]
        _, self.O, self.H, self.L, self.C, self.V, _ = D.nq_minutes()
        self.an = np.array([int(j[:4]) for j in self.J])
        so = np.nonzero(self.ok)[0]
        self.test = so[self.an[so] >= 2014]                  # seances completes 2014 - 2026 (fenetre commune aux trois bots)
        self.p = np.load(cache_p)
        self.pos = {j: i for i, j in enumerate(self.J)}
        self.atr = self.X["I"]["atr"]; self.rang = self.X["F"][:, 7]


def bougie_avant(s, m_entree):
    return s * 26 + m_entree // 15 - 1                  # derniere bougie de 15 min terminee avant l'entree


def supertrend(B):
    st = pd.read_csv(ICI.parent / "st_trades.csv")
    out = []
    for r in st.itertuples():
        s = B.pos.get(r.jour)
        if s is None:
            continue
        fin = 384 if r.m_out >= 385 else r.m_out - 1          # sortie a la cloture de 15 h 54, sinon a l'ouverture de m_out
        out.append((s, int(r.sens), int(r.m_in), int(r.m_in), int(fin), float(r.entree), float(r.sortie)))
    return out


LIGNE = re.compile(r"^(\d{4}-\d{2}-\d{2}) (achat|vente|sortie|stop)\b(?: (\d+)h(\d+))?(?: (\d+)h(\d+))?.*? a ([0-9.]+)")


def zone(B):
    """Bot 3 en 1 (zone de bruit, filtres C2 + Q1, sans le filtre delta) : une seule regle sur toute la periode
    (journal de rejeu jusqu'au 27 oct. 2026, puis la seance du 2 nov.). Entree a la cloture de la minute du controle."""
    out = []
    for f, de, a in ((ICI / "donnees/c2q1.txt", "2011-01-01", "2026-10-27"), (ICI / "donnees/zone.txt", "2026-10-28", "2026-11-02")):
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
                    out.append((s, ouvert[1], ouvert[2], ouvert[2] + 1, min(389, max(ouvert[2], mm)), ouvert[3], px))
                ouvert = None
    return out


def xgboost(B, seuil=0.55, filtre=None):
    """Bot XGBoost NQ : moyenne des 10 modeles, probabilites hors echantillon ; une position, 1 heure, entree a l'ouverture
    de la minute qui suit la bougie, sortie a la cloture de la 4e bougie. `filtre(i)` : condition sur la bougie du signal."""
    X = B.X; F = X["F"]; sess, b, an = X["sess"], X["b"], X["an"]
    fut = np.r_[X["c"][4:], np.full(4, np.nan)]
    utile = B.ok[sess] & X["meme"] & np.isfinite(F[:, :21]).all(1) & np.isfinite(fut) & (an >= 2014)
    sig = np.where(B.p > seuil, 1, np.where(B.p < 1 - seuil, -1, 0)) * utile
    out = []; libre = -1
    for i in np.nonzero(sig)[0]:
        if i <= libre or (filtre is not None and not filtre(i)):
            continue
        s, bq, sens = sess[i], b[i], int(sig[i])
        m0, m1 = 15 * (bq + 1), 15 * (bq + 4) + 14
        out.append((s, sens, m0, m0, m1, B.O[s, m0], B.C[s, m1]))
        libre = i + 3
    return out


@nb.njit(cache=True)
def _stop(ts, tsens, tdeb, tfin, te, tx, O, H, L, niv_atr):
    fin = tfin.copy(); x = tx.copy()
    for k in range(len(ts)):
        s, sens, e = ts[k], tsens[k], te[k]
        niv = e - sens * niv_atr[k]
        for m in range(tdeb[k], tfin[k] + 1):
            if m > tdeb[k] and (O[s, m] - niv) * sens <= 0:
                x[k] = O[s, m]; fin[k] = m - 1; break             # ouverture deja au-dela du stop
            pire = L[s, m] if sens > 0 else H[s, m]
            if (pire - niv) * sens <= 0:
                x[k] = niv - sens * 0.25; fin[k] = m - 1; break     # stop touche dans la minute : sortie au stop - 1 tick
    return fin, x


def appliquer_stop(B, tr, k_atr):
    """Stop a k_atr x ATR 14 (bougies de 15 min, derniere terminee avant l'entree). Le bot attend ensuite son trade suivant."""
    if not tr:
        return tr
    a = lambda i, ty: np.array([r[i] for r in tr], dtype=ty)
    niv = np.array([k_atr * B.atr[bougie_avant(r[0], r[2])] for r in tr]); niv = np.where(np.isfinite(niv), niv, 1e9)
    fin, x = _stop(a(0, np.int64), a(1, np.int64), a(3, np.int64), a(4, np.int64), a(5, np.float64), a(6, np.float64), B.O, B.H, B.L, niv)
    return [(r[0], r[1], r[2], r[3], int(fin[k]), r[5], float(x[k])) for k, r in enumerate(tr)]


@nb.njit(cache=True)
def _journees(S, ts, tsens, tdeb, tfin, te, tx, H, L, taille, limite, frais, pref, glisse):
    """Une seule position a la fois (un bot). Limite du jour sur realise + latent : le trade en cours est coupe a la limite
    (moins le glissement), plus aucun trade ensuite. Renvoie resultat, creux et nombre de trades par seance."""
    res = np.zeros(S); dip = np.zeros(S); ntr = np.zeros(S)
    k = 0; n = len(ts)
    while k < n:
        s = ts[k]; real = 0.0; creux = 0.0; arret = False
        while k < n and ts[k] == s:
            if not arret:
                sens = tsens[k]; e = te[k]; ech = 2.0 * pref / e * taille
                for m in range(tdeb[k], tfin[k] + 1):
                    eq = real + sens * ((L[s, m] if sens > 0 else H[s, m]) - e) * ech
                    if eq < creux:
                        creux = eq
                    if eq <= -limite:
                        real = -limite - glisse * ech - frais * taille; arret = True
                        break
                if not arret:
                    real += sens * (tx[k] - e) * ech - frais * taille
                    if real <= -limite:
                        arret = True
                if real < creux:
                    creux = real
                ntr[s] += 1
            k += 1
        res[s] = real; dip[s] = creux
    return res, dip, ntr


def tableaux(tr):
    t = sorted(tr, key=lambda x: (x[0], x[3]))
    a = lambda k, ty: np.array([x[k] for x in t], dtype=ty)
    return a(0, np.int64), a(1, np.int64), a(3, np.int64), a(4, np.int64), a(5, np.float64), a(6, np.float64)


def journees(B, trades, taille=1, limite=400.0, frais=D.FRAIS):
    ts, tsens, tdeb, tfin, te, tx = tableaux(trades)
    return _journees(B.S, ts, tsens, tdeb, tfin, te, tx, B.H, B.L, float(taille), float(min(limite, DLL)), float(frais), float(D.PREF), GLISSEMENT)


@nb.njit(cache=True)
def _journees_ensemble(S, ts, tsens, tdeb, tfin, te, tx, H, L, limite, frais, pref, glisse):
    """Plusieurs bots sur le meme compte, positions simultanees : equite minute par minute (pire prix de chaque position a
    la meme minute, donc prudent), tout est coupe a la limite commune, plus rien ensuite."""
    res = np.zeros(S); dip = np.zeros(S)
    k = 0; n = len(ts)
    lat = np.zeros(392); clos = np.zeros(392)
    while k < n:
        s = ts[k]; k0 = k
        while k < n and ts[k] == s:
            k += 1
        lat[:] = 0.0; clos[:] = 0.0
        for q in range(k0, k):
            ech = 2.0 * pref / te[q]
            for m in range(tdeb[q], tfin[q] + 1):
                lat[m] += tsens[q] * ((L[s, m] if tsens[q] > 0 else H[s, m]) - te[q]) * ech
            clos[tfin[q] + 1] += tsens[q] * (tx[q] - te[q]) * ech - frais
        real = 0.0; creux = 0.0; coupe = False
        for m in range(391):
            real += clos[m]
            eq = real + lat[m]
            if eq < creux:
                creux = eq
            if eq <= -limite:
                ouverts = 0
                for q in range(k0, k):
                    if tdeb[q] <= m <= tfin[q]:
                        ouverts += 1
                real = -limite - ouverts * (glisse * 2.0 * pref / te[k0] + frais); coupe = True
                break
        if real < creux:
            creux = real
        res[s] = real; dip[s] = creux
    return res, dip


def journees_ensemble(B, trades, limite=400.0, frais=D.FRAIS):
    ts, tsens, tdeb, tfin, te, tx = tableaux(trades)
    r, d = _journees_ensemble(B.S, ts, tsens, tdeb, tfin, te, tx, B.H, B.L, float(min(limite, DLL)), float(frais), float(D.PREF), GLISSEMENT)
    ntr = np.zeros(B.S); np.add.at(ntr, ts, 1)
    return r, d, ntr


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
def grilles_depuis(res, dip, horizon):
    n = len(res); out = np.zeros(max(0, n - horizon), np.bool_)
    for i0 in range(n - horizon):
        g, pr, mb = _compte(res, dip, i0, horizon)
        out[i0] = g >= 0
    return out


@nb.njit(cache=True)
def _vie_reelle(R, Dp, trade, i0, i1, s2, s3, garde, frais_mois, activation):
    """Vie reelle d'un compte Master (regles de retrait documentees dans audit/README.md, a verifier chez Bulenox) :
    10 jours de trading par retrait, au moins 1 000 $, les trois premiers plafonnes a 1 500 $, meilleure journee au plus 40 %
    du gain depuis le dernier retrait, `garde` $ gardes au-dessus de 50 000 $ (au moins 2 600). Taille du jour selon la
    marge (solde - plancher) : 2 MNQ des s2, 3 des s3 (R, Dp : resultats et creux a 1, 2, 3 MNQ). Un Master grille oblige a
    repasser une qualification avec le meme bot en 1 MNQ (objectif 53 000 $, plancher suiveur 2 500 $ en fin de journee),
    payee frais_mois toutes les 20 seances, plus l'activation a la reussite.
    Renvoie (retire, frais, masters grilles, qualifications ratees, retraits)."""
    phase = 1
    solde = 50000.0; haut = 50000.0; base_ = 50000.0; meilleur = 0.0; jours = 0; nret = 0
    retire = 0.0; frais = 0.0; grilles = 0; rates = 0; duree_q = 0
    for i in range(i0, i1):
        plancher = min(haut - 2500.0, 50100.0)
        t = 0
        if phase == 1:
            marge = solde - plancher
            if marge >= s3:
                t = 2
            elif marge >= s2:
                t = 1
        else:
            if duree_q % 20 == 0:
                frais += frais_mois
            duree_q += 1
        if solde + Dp[t, i] <= plancher:
            if phase == 1:
                grilles += 1
            else:
                rates += 1
            phase = 0; duree_q = 0; solde = 50000.0; haut = 50000.0; base_ = 50000.0; meilleur = 0.0; jours = 0
            continue
        solde += R[t, i]
        if solde > haut:
            haut = solde
        if phase == 0:
            if solde >= 53000.0:
                frais += activation; phase = 1; solde = 50000.0; haut = 50000.0; base_ = 50000.0; meilleur = 0.0; jours = 0; nret = 0
            continue
        if trade[i]:
            jours += 1
        if R[t, i] > meilleur:
            meilleur = R[t, i]
        dispo = solde - (50000.0 + garde)
        if nret < 3 and dispo > 1500.0:
            dispo = 1500.0
        if jours >= 10 and dispo >= 1000.0 and solde - base_ > 0 and meilleur <= 0.4 * (solde - base_):
            retire += dispo; solde -= dispo; base_ = solde; meilleur = 0.0; jours = 0; nret += 1
    return retire, frais, grilles, rates, nret


def vie(R, Dp, trade, debut=0, fin=None, s2=1e12, s3=1e12, garde=2600.0, pas=20, frais_mois=100.0, activation=148.0):
    """Vie reelle moyennee sur des departs tous les `pas` seances (le resultat d'un seul parcours est trop instable) :
    chaque depart joue jusqu'a `fin`. Renvoie le net par an (retire - frais), les masters grilles par an, etc."""
    fin = R.shape[1] if fin is None else fin
    acc = np.zeros(5); ans = 0.0
    for i0 in range(debut, max(debut + 1, fin - 252), pas):
        r = _vie_reelle(R, Dp, trade, i0, fin, s2, s3, garde, frais_mois, activation)
        acc += np.array(r); ans += (fin - i0) / 252
    return dict(net_an=float((acc[0] - acc[1]) / ans), retire_an=float(acc[0] / ans), frais_an=float(acc[1] / ans),
                grilles_an=float(acc[2] / ans), qualifs_ratees_an=float(acc[3] / ans))


def tst(v):
    return float(v.mean() / v.std(ddof=1) * np.sqrt(len(v))) if len(v) > 2 and v.std() > 0 else 0.0


def mesures(B, res, dip, ntr):
    """Mesures 2014 - 2026 d'un bot (1 MNQ) : t, deux moities, compte neuf (survie a 60 seances, grille dans l'annee) et vie
    reelle moyennee (net par an, masters grilles par an)."""
    j = res[B.test]; d = dip[B.test]; tr = ntr[B.test] > 0; aj = B.an[B.test]; jours = [B.J[s] for s in B.test]
    cum = np.cumsum(j)
    g60 = grilles_depuis(j, d, 60); g250 = grilles_depuis(j, d, 250)
    R = np.vstack([j, j, j]); Dp = np.vstack([d, d, d])
    v = vie(R, Dp, tr)
    per = np.array([x >= "2026-08-11" for x in jours])
    return dict(par_seance=float(j.mean()), t=tst(j), t_avant=tst(j[aj <= 2022]), t_apres=tst(j[aj >= 2023]), pire_baisse=float((cum - np.maximum.accumulate(cum)).min()),
                pire_jour=float(j.min()), survie_60=float(1 - g60.mean()), grille_250=float(g250.mean()), periode=float(j[per].sum()),
                annees_pos=int(sum(j[aj == y].sum() > 0 for y in range(2014, 2027))), jours_trades=int(tr.sum()), **v)
