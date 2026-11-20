"""Tournoi des indicateurs TradingView (usine/REGLES.md, idees 9 a 15) : etat de chaque indicateur a la cloture de chaque
bougie de 5 minutes du NQ, puis positions par minute avec le cadre du Supertrend (moteur.k_supertrend). Importer ce module
ajoute les 7 idees a moteur.STRATEGIES."""
import math

import numpy as np
from numba import njit

import moteur as Mo

N, B = Mo.N, 78                                    # minutes et bougies de 5 minutes par seance


# ------------------------------------------------------------------ outils (conventions de Pine)
@njit(cache=True)
def barres5(O, H, L, C):
    S = C.shape[0]; nb = S * B
    o5 = np.empty(nb); h5 = np.empty(nb); l5 = np.empty(nb); c5 = np.empty(nb)
    for s in range(S):
        for b in range(B):
            hh = H[s, 5 * b]; ll = L[s, 5 * b]
            for q in range(1, 5):
                hh = max(hh, H[s, 5 * b + q]); ll = min(ll, L[s, 5 * b + q])
            o5[s * B + b] = O[s, 5 * b]; h5[s * B + b] = hh; l5[s * B + b] = ll; c5[s * B + b] = C[s, 5 * b + 4]
    return o5, h5, l5, c5


@njit(cache=True)
def sma(x, n):
    """Moyenne simple ; manquante tant qu'une valeur de la fenetre manque (comme Pine)."""
    out = np.full(x.shape[0], np.nan); s = 0.0; nn = 0
    for i in range(x.shape[0]):
        if np.isnan(x[i]):
            nn += 1
        else:
            s += x[i]
        if i >= n:
            if np.isnan(x[i - n]):
                nn -= 1
            else:
                s -= x[i - n]
        if i >= n - 1 and nn == 0:
            out[i] = s / n
    return out


@njit(cache=True)
def ema(x, n):
    a = 2.0 / (n + 1); out = np.full(x.shape[0], np.nan); prev = np.nan
    for i in range(x.shape[0]):
        if np.isnan(x[i]):
            continue
        prev = x[i] if np.isnan(prev) else a * x[i] + (1 - a) * prev
        out[i] = prev
    return out


@njit(cache=True)
def rma(x, n):
    out = np.full(x.shape[0], np.nan); s = 0.0
    for i in range(x.shape[0]):
        if i < n:
            s += x[i]
            if i == n - 1:
                out[i] = s / n
        else:
            out[i] = (out[i - 1] * (n - 1) + x[i]) / n
    return out


@njit(cache=True)
def vrai_range(h, l, c):
    tr = np.empty(c.shape[0]); tr[0] = h[0] - l[0]
    for i in range(1, c.shape[0]):
        tr[i] = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
    return tr


@njit(cache=True)
def stdev(x, n):
    out = np.full(x.shape[0], np.nan)
    for i in range(n - 1, x.shape[0]):
        m = 0.0
        for k in range(i - n + 1, i + 1):
            m += x[k]
        m /= n; v = 0.0
        for k in range(i - n + 1, i + 1):
            v += (x[k] - m) ** 2
        out[i] = math.sqrt(v / n)
    return out


@njit(cache=True)
def plus_haut(x, n):
    out = np.full(x.shape[0], np.nan)
    for i in range(n - 1, x.shape[0]):
        m = x[i - n + 1]
        for k in range(i - n + 2, i + 1):
            m = max(m, x[k])
        out[i] = m
    return out


@njit(cache=True)
def plus_bas(x, n):
    out = np.full(x.shape[0], np.nan)
    for i in range(n - 1, x.shape[0]):
        m = x[i - n + 1]
        for k in range(i - n + 2, i + 1):
            m = min(m, x[k])
        out[i] = m
    return out


@njit(cache=True)
def wma(x, n):
    out = np.full(x.shape[0], np.nan); den = n * (n + 1) / 2.0
    for i in range(n - 1, x.shape[0]):
        s = 0.0; ok = True
        for k in range(n):
            v = x[i - k]
            if np.isnan(v):
                ok = False; break
            s += v * (n - k)
        if ok:
            out[i] = s / den
    return out


@njit(cache=True)
def linreg(x, n):
    """Valeur, a la derniere bougie, de la droite des moindres carres sur les n dernieres (linreg(x, n, 0) de Pine)."""
    out = np.full(x.shape[0], np.nan)
    sx = n * (n - 1) / 2.0; sxx = (n - 1) * n * (2 * n - 1) / 6.0
    for i in range(n - 1, x.shape[0]):
        sy = 0.0; sxy = 0.0; ok = True
        for k in range(n):
            v = x[i - n + 1 + k]
            if np.isnan(v):
                ok = False; break
            sy += v; sxy += k * v
        if ok:
            pente = (n * sxy - sx * sy) / (n * sxx - sx * sx)
            out[i] = (sy - pente * sx) / n + pente * (n - 1)
    return out


# ------------------------------------------------------------------ etats des 7 indicateurs
@njit(cache=True)
def etat_squeeze(h, l, c, n, mkc):
    tr = vrai_range(h, l, c); base = sma(c, n); sd = stdev(c, n); rg = sma(tr, n)
    hh = plus_haut(h, n); ll = plus_bas(l, n)
    x = c - ((hh + ll) / 2.0 + base) / 2.0
    val = linreg(x, n)
    st = np.zeros(c.shape[0]); pos = 0.0; arme = False
    for i in range(c.shape[0]):
        if np.isnan(sd[i]) or np.isnan(rg[i]) or np.isnan(val[i]):
            continue
        up_bb = base[i] + mkc * sd[i]; lo_bb = base[i] - mkc * sd[i]
        up_kc = base[i] + mkc * rg[i]; lo_kc = base[i] - mkc * rg[i]
        sqz_on = lo_bb > lo_kc and up_bb < up_kc
        sqz_off = lo_bb < lo_kc and up_bb > up_kc
        if pos != 0 and np.sign(val[i]) == -pos:
            pos = 0.0
        if pos == 0 and sqz_off and arme and val[i] != 0:
            pos = np.sign(val[i])
        if sqz_off:
            arme = False
        if sqz_on:
            arme = True
        st[i] = pos
    return st


@njit(cache=True)
def etat_utbot(h, l, c, a, n):
    atr = rma(vrai_range(h, l, c), n)
    st = np.zeros(c.shape[0]); stop = 0.0; pos = 0.0
    for i in range(1, c.shape[0]):
        if np.isnan(atr[i]):
            continue
        perte = a * atr[i]; prev = stop
        if c[i] > prev and c[i - 1] > prev:
            stop = max(prev, c[i] - perte)
        elif c[i] < prev and c[i - 1] < prev:
            stop = min(prev, c[i] + perte)
        elif c[i] > prev:
            stop = c[i] - perte
        else:
            stop = c[i] + perte
        if c[i - 1] < prev and c[i] > prev:
            pos = 1.0
        elif c[i - 1] > prev and c[i] < prev:
            pos = -1.0
        st[i] = pos
    return st


@njit(cache=True)
def etat_ssl(h, l, c, n):
    mh = sma(h, n); ml = sma(l, n)
    st = np.zeros(c.shape[0]); hlv = 0.0
    for i in range(c.shape[0]):
        if np.isnan(mh[i]):
            continue
        if c[i] > mh[i]:
            hlv = 1.0
        elif c[i] < ml[i]:
            hlv = -1.0
        st[i] = hlv
    return st


@njit(cache=True)
def etat_rangefilter(c, p, m):
    d = np.zeros(c.shape[0])
    for i in range(1, c.shape[0]):
        d[i] = abs(c[i] - c[i - 1])
    rng = ema(ema(d, p), 2 * p - 1) * m
    st = np.zeros(c.shape[0]); filt = 0.0; up = 0.0; dn = 0.0; cond = 0.0
    for i in range(1, c.shape[0]):
        r = rng[i]; prev = filt
        if c[i] > prev:
            filt = prev if c[i] - r < prev else c[i] - r
        else:
            filt = prev if c[i] + r > prev else c[i] + r
        if filt > prev:
            up += 1; dn = 0
        elif filt < prev:
            dn += 1; up = 0
        if i < 2 * (2 * p - 1):
            continue
        long_c = c[i] > filt and c[i] != c[i - 1] and up > 0
        short_c = c[i] < filt and c[i] != c[i - 1] and dn > 0
        if long_c:
            cond = 1.0
        elif short_c:
            cond = -1.0
        st[i] = cond
    return st


@njit(cache=True)
def etat_wavetrend(h, l, c, n1, n2):
    ap = (h + l + c) / 3.0
    esa = ema(ap, n1); d = ema(np.abs(ap - esa), n1)
    ci = (ap - esa) / (0.015 * d)
    wt1 = ema(ci, n2); wt2 = sma(wt1, 4)
    st = np.zeros(c.shape[0]); pos = 0.0
    for i in range(1, c.shape[0]):
        if np.isnan(wt2[i]) or np.isnan(wt2[i - 1]):
            continue
        if wt1[i] > wt2[i] and wt1[i - 1] <= wt2[i - 1] and wt1[i] < -53:
            pos = 1.0
        elif wt1[i] < wt2[i] and wt1[i - 1] >= wt2[i - 1] and wt1[i] > 53:
            pos = -1.0
        st[i] = pos
    return st


@njit(cache=True)
def etat_hull(c, n):
    hma = wma(2.0 * wma(c, n // 2) - wma(c, n), int(round(math.sqrt(n))))
    st = np.zeros(c.shape[0])
    for i in range(2, c.shape[0]):
        if np.isnan(hma[i]) or np.isnan(hma[i - 2]):
            continue
        st[i] = 1.0 if hma[i] > hma[i - 2] else -1.0
    return st


@njit(cache=True)
def etat_chandelier(h, l, c, n, mult):
    atr = rma(vrai_range(h, l, c), n) * mult
    hc = plus_haut(c, n); lc = plus_bas(c, n)
    st = np.zeros(c.shape[0]); ls_prev = np.nan; ss_prev = np.nan; d = 1.0
    for i in range(1, c.shape[0]):
        if np.isnan(atr[i]) or np.isnan(hc[i]):
            continue
        ls = hc[i] - atr[i]; ss = lc[i] + atr[i]
        lsp = ls if np.isnan(ls_prev) else ls_prev
        ssp = ss if np.isnan(ss_prev) else ss_prev
        if c[i - 1] > lsp:
            ls = max(ls, lsp)
        if c[i - 1] < ssp:
            ss = min(ss, ssp)
        if c[i] > ssp:
            d = 1.0
        elif c[i] < lsp:
            d = -1.0
        ls_prev = ls; ss_prev = ss
        st[i] = d
    return st


# ------------------------------------------------------------------ positions (cadre du Supertrend)
@njit(cache=True)
def k_positions(st, ok):
    """Comme moteur.k_supertrend : etat lu a la cloture de la bougie b, position a l'ouverture de la minute 5b + 5 ;
    0 = a plat ; pas d'entree apres 15 h 30 ; a plat a 15 h 55."""
    S = ok.shape[0]
    pg = np.zeros((S, N), np.int8); pi = np.zeros((S, N), np.int8)
    for s in range(S):
        if not ok[s]:
            continue
        pos = 0; m_in = -1
        for bb in range(76):
            cible = int(st[s * B + bb])
            mm = 5 * bb + 5
            if cible != pos and pos != 0:
                for q in range(m_in + 1, mm):
                    pg[s, q] = pos; pi[s, q] = pos
                pg[s, mm] = pos
                pos = 0
            if cible != 0 and pos == 0 and mm <= 360:
                pos = cible; m_in = mm; pi[s, mm] = pos
        if pos != 0:
            for q in range(m_in + 1, 385):
                pg[s, q] = pos; pi[s, q] = pos
    return pg, pi


def _cinq(P):
    return barres5(P["O"], P["H"], P["L"], P["C"])


def _f(fonction):
    return lambda P, **r: k_positions(fonction(_cinq(P), **r), P["ok"])


IDEES = {
    "tv_squeeze": ("Squeeze Momentum (LazyBear)", [("n", [10, 15, 20, 30, 40]), ("mkc", [1.0, 1.25, 1.5, 2.0, 2.5])], {"n": 20, "mkc": 1.5},
                   lambda b, n, mkc: etat_squeeze(b[1], b[2], b[3], n, mkc)),
    "tv_utbot": ("UT Bot Alerts (QuantNomad)", [("a", [0.5, 1.0, 1.5, 2.0, 3.0]), ("c", [5, 10, 14, 20, 30])], {"a": 1.0, "c": 10},
                 lambda b, a, c: etat_utbot(b[1], b[2], b[3], a, c)),
    "tv_ssl": ("SSL Channel (ErwinBeckers)", [("n", [5, 7, 10, 14, 20, 30])], {"n": 10},
               lambda b, n: etat_ssl(b[1], b[2], b[3], n)),
    "tv_rangefilter": ("Range Filter Buy and Sell (DonovanWall, guikroth)", [("p", [20, 50, 100, 150, 200]), ("m", [1.5, 2.0, 3.0, 4.0, 5.0])], {"p": 100, "m": 3.0},
                       lambda b, p, m: etat_rangefilter(b[3], p, m)),
    "tv_wavetrend": ("WaveTrend (LazyBear)", [("n1", [6, 8, 10, 14, 20]), ("n2", [11, 15, 21, 28, 35])], {"n1": 10, "n2": 21},
                     lambda b, n1, n2: etat_wavetrend(b[1], b[2], b[3], n1, n2)),
    "tv_hull": ("Hull Suite (InSilico)", [("n", [20, 34, 55, 89, 144])], {"n": 55},
                lambda b, n: etat_hull(b[3], n)),
    "tv_chandelier": ("Chandelier Exit (everget)", [("n", [10, 14, 22, 30, 44]), ("mult", [1.5, 2.0, 3.0, 4.0, 5.0])], {"n": 22, "mult": 3.0},
                      lambda b, n, mult: etat_chandelier(b[1], b[2], b[3], n, mult)),
}

for _cle, (_titre, _grille, _defaut, _etat) in IDEES.items():
    Mo.STRATEGIES[_cle] = dict(titre=_titre, avantage="Indicateur populaire de TradingView, a code ouvert (usine/REGLES.md, tournoi).",
                               contrepartie="Celle du suivi de tendance ou du retour a la moyenne, selon l'indicateur.",
                               reglages=_grille, bot=_defaut, limite=400.0, f=_f(_etat))
