"""Les 15 strategies du tournoi n°2 (regles dans README.md), sur les tableaux minute (seances x 390 minutes) de
intraday/strategies.py charger. Chaque fonction renvoie les points nets de frais par seance (0 sans trade) ;
la paire NQ / ES renvoie des rendements quotidiens nets (montant egal sur les deux jambes)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tournoi"))
import concurrents as K1  # noqa: E402  (cassure, entree_fixe, melanger du tournoi n°1)

st = K1.st
N = 390
NB = 78                      # barres de 5 minutes par seance
DERNIERE_ENTREE = 66         # barre de 15 h (9 h 30 + 66 x 5 min)
NAN = np.nan


# ---------------------------------------------------------------- A. indicateurs populaires (barres de 5 minutes)

def barres5(O, H, L, C):
    nd = O.shape[0]
    o5 = O[:, ::5]
    h5 = H.reshape(nd, NB, 5).max(axis=2)
    l5 = L.reshape(nd, NB, 5).min(axis=2)
    c5 = C[:, 4::5]
    return o5, h5, l5, c5


def ema(x, n):
    return pd.Series(x).ewm(span=n, adjust=False).mean().values


@njit(cache=True)
def _rma(x, n):
    """Moyenne de Wilder (alpha = 1/n), demarree sur la moyenne simple des n premieres valeurs."""
    out = np.full(len(x), np.nan)
    s = 0.0
    for i in range(n):
        s += x[i]
    out[n - 1] = s / n
    a = 1.0 / n
    for i in range(n, len(x)):
        out[i] = out[i - 1] + a * (x[i] - out[i - 1])
    return out


@njit(cache=True)
def supertrend(h, l, c, n, f):
    """Sens du Supertrend (+1 / -1), regles de TradingView (ta.supertrend) : ecart moyen vrai de Wilder sur n barres."""
    m = len(c)
    tr = np.empty(m)
    tr[0] = h[0] - l[0]
    for i in range(1, m):
        tr[i] = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
    atr = _rma(tr, n)
    sens = np.zeros(m, np.int64)
    bas_f, haut_f = np.nan, np.nan
    d = -1                                 # comme TradingView : la 1re ligne est la bande haute
    for i in range(n - 1, m):
        mid = (h[i] + l[i]) / 2
        bas, haut = mid - f * atr[i], mid + f * atr[i]
        if i > n - 1:
            if not (bas > bas_f or c[i - 1] < bas_f):
                bas = bas_f
            if not (haut < haut_f or c[i - 1] > haut_f):
                haut = haut_f
            if d < 0:                      # la ligne etait la bande haute
                d = 1 if c[i] > haut else -1
            else:
                d = -1 if c[i] < bas else 1
        bas_f, haut_f = bas, haut
        sens[i] = d
    return sens


def rsi(c, n):
    dc = np.diff(c, prepend=c[0])
    g, p = np.maximum(dc, 0.0), np.maximum(-dc, 0.0)
    mg, mp = _rma(g[1:], n), _rma(p[1:], n)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(mp == 0, 100.0, np.where(mg == 0, 0.0, 100 - 100 / (1 + mg / mp)))
    return np.r_[NAN, r]


@njit(cache=True)
def positions(ent_a, ent_v, sor_a, sor_v, ok):
    """Position tenue pendant chaque barre (seances x 78) : le signal a la cloture de la barre b s'execute a
    l'ouverture de b + 1 ; entrees seulement a l'ouverture des barres 1 a 66 (9 h 35 - 15 h), sorties a tout moment ;
    a plat a l'ouverture ; rien les jours exclus. Sur un meme signal : la sortie d'abord, puis l'entree."""
    nd, nb = ent_a.shape
    q = np.zeros((nd, nb), np.int64)
    for d in range(nd):
        if not ok[d]:
            continue
        pos = 0
        for b in range(nb - 1):
            if pos > 0 and sor_a[d, b]:
                pos = 0
            elif pos < 0 and sor_v[d, b]:
                pos = 0
            if pos == 0 and b + 1 <= DERNIERE_ENTREE:
                if ent_a[d, b]:
                    pos = 1
                elif ent_v[d, b]:
                    pos = -1
            q[d, b + 1] = pos
    return q


def points(q, o5, c_fin, cout):
    """Points nets par seance : somme des positions x variation d'ouverture a ouverture (la derniere barre finit a la
    cloture de 16 h), moins la moitie des frais d'un aller-retour a chaque unite de position changee."""
    suiv = np.concatenate([o5[:, 1:], c_fin[:, None]], axis=1)
    brut = (q * (suiv - o5)).sum(axis=1)
    chg = np.abs(np.diff(q, axis=1, prepend=0)).sum(axis=1) + np.abs(q[:, -1])
    return brut - chg * cout / 2


def signaux5(O, H, L, C):
    """Signaux (entree achat, entree vente, sortie achat, sortie vente) des 7 indicateurs, calcules en continu sur
    toutes les barres de 5 minutes des seances, a la cloture de chaque barre."""
    o5, h5, l5, c5 = barres5(O, H, L, C)
    nd = o5.shape[0]
    h, l, c = h5.ravel(), l5.ravel(), c5.ravel()
    forme = lambda x: np.asarray(x).reshape(nd, NB)
    sig = {}
    def toujours(s):                                     # toujours en position, du cote de s
        return (s > 0, s < 0, s < 0, s > 0)
    sig["Croisement de moyennes 9/21"] = toujours(np.sign(ema(c, 9) - ema(c, 21)))
    sig["Supertrend (10, 3)"] = toujours(supertrend(h, l, c, 10, 3.0))
    macd = ema(c, 12) - ema(c, 26)
    sig["MACD (12, 26, 9)"] = toujours(np.sign(macd - ema(macd, 9)))
    s = pd.Series(c)
    moy = s.rolling(20).mean().values
    ect = s.rolling(20).std(ddof=0).values
    haut, bas = moy + 2 * ect, moy - 2 * ect
    c_1, haut_1, bas_1 = np.r_[NAN, c[:-1]], np.r_[NAN, haut[:-1]], np.r_[NAN, bas[:-1]]
    passe_haut = (c > haut) & (c_1 <= haut_1)
    passe_bas = (c < bas) & (c_1 >= bas_1)
    sig["Bollinger (20, 2), cassure"] = (passe_haut, passe_bas, c < moy, c > moy)
    sig["Bollinger (20, 2), retour"] = (passe_bas, passe_haut, c > moy, c < moy)
    r = rsi(c, 2)
    sig["RSI(2) (Connors)"] = (r < 10, r > 90, r > 50, r < 50)
    hh20 = pd.Series(h).rolling(20).max().shift(1).values
    ll20 = pd.Series(l).rolling(20).min().shift(1).values
    hh10 = pd.Series(h).rolling(10).max().shift(1).values
    ll10 = pd.Series(l).rolling(10).min().shift(1).values
    sig["Canal de Donchian 20 / 10"] = (c > hh20, c < ll20, c < ll10, c > hh10)
    return o5, {k: tuple(forme(np.nan_to_num(x, nan=0).astype(bool)) for x in v) for k, v in sig.items()}


# ---------------------------------------------------------------- B. schemas etudies (minutes)

def schemas(J, O, H, L, C, X, ok, cout):
    nd = len(J)
    o0 = O[:, 0]
    rien = np.full(nd, NAN)
    jours = pd.DatetimeIndex(J)
    hj, lj = H.max(axis=1), L.min(axis=1)
    res = {}
    # 8. NR7 + range d'ouverture 30 min : amplitude de la veille = la plus faible des 7 dernieres seances completes
    amp = np.where(X["complete"], hj - lj, NAN)
    mini7 = pd.Series(amp).rolling(7, min_periods=7).min().values
    nr7 = np.r_[False, (amp[:-1] <= mini7[:-1]) & ~np.isnan(mini7[:-1])]
    hh, ll = H[:, :30].max(axis=1), L[:, :30].min(axis=1)
    res["NR7 + range d'ouverture 30 min"] = K1.cassure(O, H, L, C, ok & nr7, cout, hh, ll, ll, hh, 30)
    # 9. jour interieur (la veille comprise dans l'avant-veille, meme contrat, deux seances completes) : cassure de la veille
    h1, l1, h2, l2 = np.r_[NAN, hj[:-1]], np.r_[NAN, lj[:-1]], np.r_[NAN, NAN, hj[:-2]], np.r_[NAN, NAN, lj[:-2]]
    comp1 = np.r_[False, X["complete"][:-1]]
    comp2 = np.r_[False, False, X["complete"][:-2]]
    meme = ~X["echeance"] & ~np.r_[False, X["echeance"][:-1]]
    interieur = (h1 <= h2) & (l1 >= l2) & comp1 & comp2 & meme
    mil = (h1 + l1) / 2
    res["Jour interieur + cassure de la veille"] = K1.cassure(O, H, L, C, ok & interieur, cout, h1, l1, mil, mil, 0)
    # 10. range d'ouverture 5 min + volume relatif (Zarattini, Barbon, Aziz 2024)
    v5 = X["V"][:, :5].sum(axis=1)
    v5_moy = pd.Series(v5).rolling(14, min_periods=14).mean().shift(1).values
    amp14 = pd.Series(hj - lj).rolling(14, min_periods=14).mean().shift(1).values
    s10 = np.where(v5 > v5_moy, np.sign(C[:, 4] - o0), 0).astype(np.int64)
    e = O[:, 5]
    stop10 = e - s10 * 0.1 * amp14
    res["Range d'ouverture 5 min + volume relatif"] = K1.entree_fixe(O, H, L, C, ok, cout, s10, 5, stop10, rien, N - 1)
    # 12. lundi contre vendredi : le lundi, a l'inverse de la seance du vendredi (seance precedente = ce vendredi)
    jsem = jours.weekday.values
    veille_ven = np.r_[False, (jsem[:-1] == 4)] & np.r_[False, (J[1:] - J[:-1]) <= np.timedelta64(3, "D")]
    r_ven = np.r_[NAN, C[:-1, N - 1] - o0[:-1]]
    s12 = np.where((jsem == 0) & veille_ven, -np.sign(np.nan_to_num(r_ven)), 0).astype(np.int64)
    res["Lundi contre vendredi"] = K1.entree_fixe(O, H, L, C, ok, cout, s12, 0, rien, rien, N - 1)
    # 13. echeance mensuelle des options (3e vendredi) : a 12 h, a l'inverse de 9 h 30 - 12 h, jusqu'a 16 h
    jm = jours.day.values
    s13 = np.where((jsem == 4) & (jm >= 15) & (jm <= 21), -np.sign(C[:, 149] - o0), 0).astype(np.int64)
    res["Echeance mensuelle des options"] = K1.entree_fixe(O, H, L, C, ok, cout, s13, 150, rien, rien, N - 1)
    # 14. jour de l'emploi (1er vendredi) : a 10 h, dans le sens de 9 h 30 - 10 h, jusqu'a 16 h
    s14 = np.where((jsem == 4) & (jm <= 7), np.sign(C[:, 29] - o0), 0).astype(np.int64)
    res["Jour de l'emploi americain"] = K1.entree_fixe(O, H, L, C, ok, cout, s14, 30, rien, rien, N - 1)
    # 15. retournement de la mi-journee : a 12 h, a l'inverse de 10 h - 12 h, jusqu'a 13 h 30
    s15 = (-np.sign(C[:, 149] - C[:, 29])).astype(np.int64)
    res["Retournement de la mi-journee"] = K1.entree_fixe(O, H, L, C, ok, cout, s15, 150, rien, rien, 239)
    return res


def toutes(J, O, H, L, C, P, X, cout):
    """Points nets par seance des 14 strategies a un marche ; ok = seance complete et pas de changement d'echeance."""
    complete = st.journees_completes(P)
    ok = complete & ~X["echeance"]
    o5, sig = signaux5(O, H, L, C)
    res = {nom: points(positions(*s, ok), o5, C[:, N - 1], cout) for nom, s in sig.items()}
    res.update(schemas(J, O, H, L, C, {**X, "complete": complete}, ok, cout))
    return res, ok


# ---------------------------------------------------------------- 11. paire NQ / ES

@njit(cache=True)
def _paire(Oa, Ca, Ob, Cb, ok, seuil, cout_a, cout_b):
    """Rendement quotidien net, montant egal sur les deux jambes (a : NQ, b : ES). Ecart x = variation de a depuis
    9 h 30 - variation de b (en log). Entrees aux points de 10 h, 10 h 30, ..., 15 h (prix a l'heure pile, execution
    a l'ouverture de la minute suivante) ; sortie des que l'ecart repasse 0 (verifie a chaque minute), ou a 16 h."""
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
            x = np.log(Ca[d, m - 1] / Oa[d, 0]) - np.log(Cb[d, m - 1] / Ob[d, 0])     # a l'heure 9 h 30 + m
            if pos != 0 and x * pos <= 0:
                tot += 0.5 * (-pos * (Oa[d, m] / ea - 1) + pos * (Ob[d, m] / eb - 1))
                pos = 0
            if pos == 0 and m % 30 == 0 and m <= 330 and abs(x) > seuil[d]:
                pos = 1 if x > 0 else -1               # +1 : a plus fort, vente de a, achat de b
                ea, eb = Oa[d, m], Ob[d, m]
                tot -= 0.5 * (cout_a / ea + cout_b / eb)
        if pos != 0:
            tot += 0.5 * (-pos * (Ca[d, N - 1] / ea - 1) + pos * (Cb[d, N - 1] / eb - 1))
        out[d] = tot
    return out


def aligner(a, b):
    """Garde les seances presentes sur les deux marches. a, b : (J, O, H, L, C, P, X)."""
    J = a[0].intersection(b[0])
    def sel(m):
        i = m[0].get_indexer(J)
        X = {"V": m[6]["V"][i], "echeance": m[6]["echeance"][i], "contrat": None}
        return (J,) + tuple(x[i] for x in m[1:6]) + (X,)
    return sel(a), sel(b)


def paire(a, b, cout_a, cout_b):
    """a, b alignes (aligner). Seuil : 1,5 fois l'ecart-type (20 seances precedentes) de l'ecart de fin de seance."""
    Ja, Oa, _, _, Ca, Pa, Xa = a
    _, Ob, _, _, Cb, Pb, Xb = b
    ok = st.journees_completes(Pa) & st.journees_completes(Pb) & ~Xa["echeance"] & ~Xb["echeance"]
    fin = np.log(Ca[:, N - 1] / Oa[:, 0]) - np.log(Cb[:, N - 1] / Ob[:, 0])
    fin = np.where(st.journees_completes(Pa) & st.journees_completes(Pb), fin, NAN)
    seuil = 1.5 * pd.Series(fin).rolling(20, min_periods=20).std().shift(1).values
    return _paire(Oa, Ca, Ob, Cb, ok, seuil, cout_a, cout_b), ok


def melanger_perm(O, H, L, C, V, perm):
    """Comme tournoi/concurrents.melanger, avec un ordre des minutes impose (le meme pour les deux marches de la paire)."""
    ro = np.ones_like(O)
    ro[:, 1:] = O[:, 1:] / C[:, :-1]
    rh, rl, rc = H / O, L / O, C / O
    ro, rh, rl, rc, V2 = (np.take_along_axis(x, perm, axis=1) for x in (ro, rh, rl, rc, V))
    O2, H2, L2, C2 = (np.empty_like(O) for _ in range(4))
    prix = O[:, 0].copy()
    for m in range(O.shape[1]):
        om = prix * (ro[:, m] if m > 0 else 1.0)
        O2[:, m], H2[:, m], L2[:, m], C2[:, m] = om, om * rh[:, m], om * rl[:, m], om * rc[:, m]
        prix = C2[:, m]
    return O2, H2, L2, C2, V2


def ordre_hasard(nd, rng):
    return np.concatenate([np.zeros((nd, 1), int), 1 + np.argsort(rng.random((nd, N - 1)), axis=1)], axis=1)
