"""Moteur deterministe de l'usine (usine/REGLES.md) : positions par minute de chaque idee, rendements nets par minute,
dollars par seance, permutations. Compile avec numba : meme reponse a chaque fois.

Conventions : seances x 390 minutes (minute 0 = 9 h 30, New York). Pour chaque minute m, deux positions :
- pg[s, m] tient l'ecart d'ouverture de la minute (ouverture(m) / cloture(m - 1)) ;
- pi[s, m] tient la minute elle-meme (cloture(m) / ouverture(m)).
Une entree a la cloture de la minute m0 donne pg = pi = sens a partir de m0 + 1. Une entree a l'ouverture de m0 (Supertrend)
donne pi[m0] = sens, pg[m0] = position d'avant.
"""
import numpy as np
from numba import njit

N = 390
COUT = 1.5 / 57000.0      # frais par cote, en rendement : 3 $ l'aller-retour pour 1 MNQ a 28 500 points
DOLLAR = 57000.0          # 1 MNQ au prix d'aujourd'hui : 2 $ x 28 500 points
CONTROLES = 12            # zone : controles aux minutes 30, 60, ..., 360


# ---------------------------------------------------------------------------------------------------- donnees derivees
def deriver(D, O=None, H=None, L=None, C=None, V=None):
    """Tout ce dont les strategies ont besoin, calcule une fois par jeu de minutes (vrai ou permute)."""
    O = D["O"] if O is None else O; H = D["H"] if H is None else H; L = D["L"] if L is None else L
    C = D["C"] if C is None else C; V = D["V"] if V is None else V
    ok, seg = D["complete"], D["seg"]
    S = C.shape[0]
    lg = np.zeros_like(C); lg[:, 1:] = np.log(O[:, 1:] / C[:, :-1])
    lb = np.log(C / O)
    typ = (H + L + C) / 3; cv = np.cumsum(V, axis=1)
    vwap = np.where(cv > 0, np.cumsum(typ * V, axis=1) / np.where(cv > 0, cv, 1), np.cumsum(typ, axis=1) / np.arange(1, N + 1))
    # derniere seance complete avant chaque seance, et seulement si le contrat n'a pas change entre les deux
    idx = np.where(ok, np.arange(S), -1)
    prec = np.r_[-1, np.maximum.accumulate(idx)[:-1]]
    prec = np.where((prec >= 0) & (seg[np.maximum(prec, 0)] == seg), prec, -1)
    pm = np.maximum(prec, 0)
    veille = np.where(prec >= 0, C[pm, N - 1], np.nan)
    ph = np.where(prec >= 0, H[pm].max(axis=1), np.nan)
    pl = np.where(prec >= 0, L[pm].min(axis=1), np.nan)
    # zone : |cloture(m) / ouverture - 1| aux controles, sommes cumulees sur les seances completes
    mv = np.abs(C[:, 30:361:30] / O[:, :1] - 1)
    comp = np.where(ok)[0]
    mvc = np.vstack([np.zeros((1, CONTROLES)), np.cumsum(mv[comp], axis=0)])
    cpos = np.searchsorted(comp, np.arange(S)).astype(np.int64)
    return dict(O=O, H=H, L=L, C=C, V=V, ok=ok, lg=lg, lb=lb, vwap=vwap, veille=veille, ph=ph, pl=pl, mvc=mvc, cpos=cpos)


# ---------------------------------------------------------------------------------------------------- les strategies
@njit(cache=True)
def k_zone(C, O, vwap, ok, veille, mvc, cpos, k, jours):
    S = C.shape[0]; pos = np.zeros((S, N), np.int8)
    for s in range(S):
        if not ok[s] or np.isnan(veille[s]) or cpos[s] < jours:
            continue
        c = cpos[s]
        hr = max(O[s, 0], veille[s]); br = min(O[s, 0], veille[s])
        p_ = 0; m0 = 0
        for j in range(CONTROLES):
            m = 30 * (j + 1)
            sig = (mvc[c, j] - mvc[c - jours, j]) / jours
            p = C[s, m]; ub = hr * (1 + k * sig); lb = br * (1 - k * sig)
            if p_ > 0 and p <= max(ub, vwap[s, m]):
                for q in range(m0 + 1, m + 1):
                    pos[s, q] = 1
                p_ = 0
            elif p_ < 0 and p >= min(lb, vwap[s, m]):
                for q in range(m0 + 1, m + 1):
                    pos[s, q] = -1
                p_ = 0
            if p_ == 0:
                if p > ub:
                    p_ = 1; m0 = m
                elif p < lb:
                    p_ = -1; m0 = m
        if p_ != 0:
            for q in range(m0 + 1, N):
                pos[s, q] = p_
    return pos


@njit(cache=True)
def k_supertrend(O, H, L, C, ok, per, mult):
    S = C.shape[0]; nb = S * 78
    h5 = np.empty(nb); l5 = np.empty(nb); c5 = np.empty(nb)
    for s in range(S):
        for b in range(78):
            hh = H[s, 5 * b]; ll = L[s, 5 * b]
            for q in range(1, 5):
                hh = max(hh, H[s, 5 * b + q]); ll = min(ll, L[s, 5 * b + q])
            h5[s * 78 + b] = hh; l5[s * 78 + b] = ll; c5[s * 78 + b] = C[s, 5 * b + 4]
    st = np.zeros(nb); atr = 0.0; hb = np.nan; lb = np.nan; dr = 1.0
    for i in range(1, nb):
        tr = max(h5[i] - l5[i], abs(h5[i] - c5[i - 1]), abs(l5[i] - c5[i - 1]))
        atr = tr if i == 1 else (atr * (per - 1) + tr) / per
        mid = (h5[i] + l5[i]) / 2; hb2 = mid + mult * atr; lb2 = mid - mult * atr
        if i > 1:
            hb2 = hb2 if (hb2 < hb or c5[i - 1] > hb) else hb
            lb2 = lb2 if (lb2 > lb or c5[i - 1] < lb) else lb
            if dr > 0 and c5[i] < lb2:
                dr = -1.0
            elif dr < 0 and c5[i] > hb2:
                dr = 1.0
        hb = hb2; lb = lb2
        st[i] = dr if i >= per else 0.0
    pg = np.zeros((S, N), np.int8); pi = np.zeros((S, N), np.int8)
    for s in range(S):
        if not ok[s]:
            continue
        pos = 0; m_in = -1
        for bb in range(76):
            v = st[s * 78 + bb]
            cible = pos if v == 0 else int(v)
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


@njit(cache=True)
def k_orb(H, L, C, ok, dur, emax):
    S = C.shape[0]; pos = np.zeros((S, N), np.int8)
    for s in range(S):
        if not ok[s]:
            continue
        hi = H[s, 0]; lo = L[s, 0]
        for q in range(1, dur):
            hi = max(hi, H[s, q]); lo = min(lo, L[s, q])
        sens = 0; m0 = -1
        for m in range(dur, emax):
            if C[s, m] > hi:
                sens = 1; m0 = m; break
            if C[s, m] < lo:
                sens = -1; m0 = m; break
        if sens == 0:
            continue
        fin = N - 1
        for m in range(m0 + 1, N):
            if (sens > 0 and C[s, m] < lo) or (sens < 0 and C[s, m] > hi):
                fin = m; break
        for q in range(m0 + 1, fin + 1):
            pos[s, q] = sens
    return pos


@njit(cache=True)
def k_momentum(O, C, ok, veille, t1, ref, t2):
    S = C.shape[0]; pos = np.zeros((S, N), np.int8)
    for s in range(S):
        if not ok[s]:
            continue
        r0 = veille[s] if ref == 0 else O[s, 0]
        if np.isnan(r0):
            continue
        sig = C[s, t1 - 1] / r0 - 1
        if sig == 0:
            continue
        sens = 1 if sig > 0 else -1
        for q in range(t2, N):
            pos[s, q] = sens
    return pos


@njit(cache=True)
def k_veille(C, ok, ph, pl, marge, emax, sortie):
    S = C.shape[0]; pos = np.zeros((S, N), np.int8)
    for s in range(S):
        if not ok[s] or np.isnan(ph[s]):
            continue
        up = ph[s] * (1 + marge); dn = pl[s] * (1 - marge)
        sens = 0; m0 = -1
        for m in range(0, emax):
            if C[s, m] > up:
                sens = 1; m0 = m; break
            if C[s, m] < dn:
                sens = -1; m0 = m; break
        if sens == 0:
            continue
        fin = N - 1
        if sortie == 0:
            for m in range(m0 + 1, N):
                if (sens > 0 and C[s, m] < ph[s]) or (sens < 0 and C[s, m] > pl[s]):
                    fin = m; break
        for q in range(m0 + 1, fin + 1):
            pos[s, q] = sens
    return pos


@njit(cache=True)
def k_gap(O, C, ok, veille, seuil, hmax):
    S = C.shape[0]; pos = np.zeros((S, N), np.int8)
    for s in range(S):
        if not ok[s] or np.isnan(veille[s]):
            continue
        g = O[s, 0] / veille[s] - 1
        if abs(g) < seuil:
            continue
        sens = -1 if g > 0 else 1
        fin = min(hmax, N - 1)
        for m in range(1, fin + 1):
            if (sens > 0 and C[s, m] >= veille[s]) or (sens < 0 and C[s, m] <= veille[s]):
                fin = m; break
        for q in range(1, fin + 1):
            pos[s, q] = sens
    return pos


@njit(cache=True)
def k_fin(C, ok, veille, t, seuil):
    S = C.shape[0]; pos = np.zeros((S, N), np.int8)
    for s in range(S):
        if not ok[s] or np.isnan(veille[s]):
            continue
        r = C[s, t - 1] / veille[s] - 1
        if r == 0 or abs(r) < seuil:
            continue
        sens = 1 if r > 0 else -1
        for q in range(t, N):
            pos[s, q] = sens
    return pos


def _deux(pos):
    return pos, pos


STRATEGIES = {
    "zone": dict(titre="Zone de bruit (Bot 3 en 1 sans filtres)", avantage="Quand le prix sort de sa bande de bruit habituelle, le mouvement continue plus souvent qu'il ne revient.", contrepartie="Ceux qui vendent la cassure, et les teneurs de marché qui couvrent leur gamma en suivant le mouvement.", reglages=[("k", [0.6, 0.8, 1.0, 1.2, 1.4]), ("jours", [7, 10, 14, 20, 30])],
                 bot={"k": 1.0, "jours": 14}, limite=1000.0,
                 f=lambda P, k, jours: _deux(k_zone(P["C"], P["O"], P["vwap"], P["ok"], P["veille"], P["mvc"], P["cpos"], k, jours))),
    "supertrend": dict(titre="Supertrend NQ, bougies de 5 minutes", avantage="Un jour de tendance, le mouvement court terme se prolonge.", contrepartie="Les apporteurs de liquidité qui vendent la hausse un jour de tendance.", reglages=[("atr", [7, 10, 14, 20, 30]), ("multiple", [2.0, 2.5, 3.0, 3.5, 4.0])],
                       bot={"atr": 10, "multiple": 3.0}, limite=400.0,
                       f=lambda P, atr, multiple: k_supertrend(P["O"], P["H"], P["L"], P["C"], P["ok"], atr, multiple)),
    "orb": dict(titre="Cassure du range d'ouverture (ORB)", avantage="Le déséquilibre des ordres de l'ouverture se prolonge dans la journée.", contrepartie="Ceux qui vendent la cassure du range d'ouverture.", reglages=[("duree", [5, 10, 15, 30, 45, 60]), ("derniere_entree", [90, 150, 240, 330])],
                limite=1000.0, f=lambda P, duree, derniere_entree: _deux(k_orb(P["H"], P["L"], P["C"], P["ok"], duree, derniere_entree))),
    "momentum": dict(titre="Momentum de la première demi-heure", avantage="Le sens du début de séance prédit celui de la fin de séance (Gao, Han, Li, Zhou 2018).", contrepartie="Les fonds et ETF à levier qui rééquilibrent en fin de séance quel que soit le prix.", reglages=[("fin_signal", [30, 60, 90]), ("reference", [0, 1]), ("debut_position", [330, 360, 375])],
                     limite=1000.0, f=lambda P, fin_signal, reference, debut_position: _deux(k_momentum(P["O"], P["C"], P["ok"], P["veille"], fin_signal, reference, debut_position))),
    "veille": dict(titre="Cassure du plus haut ou du plus bas de la veille", avantage="Le plus haut et le plus bas de la veille concentrent des stops dont le déclenchement prolonge le mouvement.", contrepartie="Les porteurs de ces stops.", reglages=[("marge", [0.0, 0.001, 0.002, 0.003]), ("derniere_entree", [150, 330]), ("sortie", [0, 1])],
                   limite=1000.0, f=lambda P, marge, derniere_entree, sortie: _deux(k_veille(P["C"], P["ok"], P["ph"], P["pl"], marge, derniere_entree, sortie))),
    "gap": dict(titre="Fade du gap d'ouverture", avantage="Un écart de nuit en partie excessif se referme en début de séance.", contrepartie="Ceux qui achètent ou vendent à l'ouverture sur les nouvelles de la nuit.", reglages=[("seuil", [0.003, 0.005, 0.008, 0.010]), ("duree_max", [30, 60, 120])],
                limite=1000.0, f=lambda P, seuil, duree_max: _deux(k_gap(P["O"], P["C"], P["ok"], P["veille"], seuil, duree_max))),
    "fin": dict(titre="Mouvement de fin de séance", avantage="Les ETF à levier et les vendeurs d'options achètent la hausse (vendent la baisse) du jour en fin de séance.", contrepartie="Eux, qui paient l'impact de ces ordres forcés.", reglages=[("debut", [300, 330, 360]), ("seuil", [0.0, 0.0025, 0.005, 0.010])],
                limite=1000.0, f=lambda P, debut, seuil: _deux(k_fin(P["C"], P["ok"], P["veille"], debut, seuil))),
}


# ---------------------------------------------------------------------------------------------------- mesures
@njit(cache=True)
def k_stats(lg, lb, pg, pi, ok):
    """Par seance : somme des minutes gagnantes, des minutes perdantes (positive), rendement net total, a-t-elle trade."""
    S = lg.shape[0]
    sp = np.zeros(S); sn = np.zeros(S); tot = np.zeros(S); joue = np.zeros(S, np.bool_)
    for s in range(S):
        if not ok[s]:
            continue
        prev = 0
        for m in range(N):
            a = pg[s, m]; b = pi[s, m]
            r = 0.0
            if m > 0:
                r += a * lg[s, m] - COUT * abs(a - prev)
            r += b * lb[s, m] - COUT * abs(b - a)
            if m == N - 1:
                r -= COUT * abs(b)
            if r > 0:
                sp[s] += r
            elif r < 0:
                sn[s] -= r
            tot[s] += r
            if a != 0 or b != 0:
                joue[s] = True
            prev = b
    return sp, sn, tot, joue


@njit(cache=True)
def k_dollars(lg, lb, O, H, L, pg, pi, ok, lim):
    """Par seance, 1 MNQ au prix d'aujourd'hui : gain, pire moment (realise + latent, au plus bas / plus haut de chaque
    minute), a-t-elle trade. Limite du jour : tout est ferme a -lim (1 point de glissement + frais), plus rien ensuite."""
    S = lg.shape[0]
    gain = np.zeros(S); pire = np.zeros(S); joue = np.zeros(S, np.bool_)
    for s in range(S):
        if not ok[s]:
            continue
        v = 0.0; w = 0.0; prev = 0; stop = False
        for m in range(N):
            a = pg[s, m]; b = pi[s, m]
            if a != 0 or b != 0:
                joue[s] = True
            if m > 0:
                v += DOLLAR * (a * lg[s, m] - COUT * abs(a - prev))
                if a != 0 and v <= -lim:
                    v -= 2.0 + DOLLAR * COUT
                    w = min(w, v); stop = True
                    break
            v -= DOLLAR * COUT * abs(b - a)
            if b != 0:
                ext = L[s, m] if b > 0 else H[s, m]
                adv = v + DOLLAR * b * np.log(ext / O[s, m])
                if adv <= -lim:
                    v = -lim - 2.0 - DOLLAR * COUT
                    w = min(w, v); stop = True
                    break
                w = min(w, adv)
            v += DOLLAR * b * lb[s, m]
            w = min(w, v)
            prev = b
        if not stop and prev != 0:
            v -= DOLLAR * COUT * abs(prev)
            w = min(w, v)
        gain[s] = v; pire[s] = w
    return gain, pire, joue


# ---------------------------------------------------------------------------------------------------- permutation
@njit(cache=True)
def k_permuter(O, H, L, C, V, masque, graine):
    """REGLES.md : dans chaque seance du masque, les ecarts d'ouverture des minutes 1 a 389 sont melanges entre eux, et
    separement les formes des minutes (plus haut, plus bas, cloture par rapport a l'ouverture, volume). La minute 0, la
    cloture de la seance et l'ecart de la nuit ne bougent pas."""
    np.random.seed(graine)
    S = O.shape[0]; n = N - 1
    O2 = O.copy(); H2 = H.copy(); L2 = L.copy(); C2 = C.copy(); V2 = V.copy()
    gap = np.empty(n); dh = np.empty(n); dl = np.empty(n); dc = np.empty(n); vv = np.empty(n)
    for s in range(S):
        if not masque[s]:
            continue
        for m in range(1, N):
            gap[m - 1] = np.log(O[s, m] / C[s, m - 1])
            dh[m - 1] = np.log(H[s, m] / O[s, m]); dl[m - 1] = np.log(L[s, m] / O[s, m])
            dc[m - 1] = np.log(C[s, m] / O[s, m]); vv[m - 1] = V[s, m]
        p1 = np.random.permutation(n); p2 = np.random.permutation(n)
        prevc = C[s, 0]
        for m in range(1, N):
            o = prevc * np.exp(gap[p1[m - 1]]); j = p2[m - 1]
            O2[s, m] = o; H2[s, m] = o * np.exp(dh[j]); L2[s, m] = o * np.exp(dl[j])
            C2[s, m] = o * np.exp(dc[j]); V2[s, m] = vv[j]
            prevc = C2[s, m]
    return O2, H2, L2, C2, V2


def combinaisons(strat):
    """Les reglages de la grille, dans l'ordre (le dernier reglage varie le plus vite), et la forme de la grille."""
    noms = [n for n, _ in strat["reglages"]]; valeurs = [v for _, v in strat["reglages"]]
    forme = tuple(len(v) for v in valeurs)
    out = [dict(zip(noms, [valeurs[i][j] for i, j in enumerate(ix)])) for ix in np.ndindex(*forme)]
    return out, forme


def grille_stats(strat, P):
    """Stats par seance de chaque reglage : tableaux (reglages x seances)."""
    combos, _ = combinaisons(strat)
    S = P["C"].shape[0]
    SP = np.zeros((len(combos), S)); SN = np.zeros_like(SP); TOT = np.zeros_like(SP); JOUE = np.zeros((len(combos), S), bool)
    for i, c in enumerate(combos):
        pg, pi = strat["f"](P, **c)
        SP[i], SN[i], TOT[i], JOUE[i] = k_stats(P["lg"], P["lb"], pg, pi, P["ok"])
    return SP, SN, TOT, JOUE
