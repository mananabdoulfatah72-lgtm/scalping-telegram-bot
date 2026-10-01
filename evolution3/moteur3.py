"""Moteur de backtest de la machine n°3 (README.md, regles v2) : barres de 5 minutes, 16 familles d'hypotheses, numba.
Signal a la cloture de la barre j, entree a l'ouverture de la barre j + 1 (meme seance), une position a la fois,
stop avant objectif, sortie forcee apres `duree` barres et a la fin de la seance, frais par aller-retour."""
import numpy as np
from numba import njit

FAMILLES = ["ecart a la moyenne", "cassure de canal", "range d'ouverture", "ecart au VWAP", "mouvement depuis l'ouverture",
            "gap", "niveaux de la veille", "RSI", "MACD", "Bollinger squeeze", "balayage de liquidite", "balayage de la veille",
            "fair value gap", "order flow estime", "pic de volume", "marche leader"]
(MOYENNE, CANAL, OUVERTURE, VWAP, DEPUIS, GAP, VEILLE, RSI, MACD, SQUEEZE, BALAYAGE, BALAYAGE_VEILLE, FVG, FLUX, VOLUME,
 LEADER) = range(16)


@njit(cache=True)
def moy_ecart(c, L):
    """Moyenne et ecart-type glissants de c sur L barres (barre courante comprise), calcul exact par fenetre."""
    n = c.shape[0]
    moy = np.full(n, np.nan)
    ect = np.full(n, np.nan)
    s = 0.0
    s2 = 0.0
    ref = c[0]
    for i in range(n):
        if i % 2048 == 0 and i >= L:
            ref = c[i]
            s = 0.0
            s2 = 0.0
            for k in range(i - L + 1, i + 1):
                x = c[k] - ref
                s += x
                s2 += x * x
        else:
            x = c[i] - ref
            s += x
            s2 += x * x
            if i >= L:
                y = c[i - L] - ref
                s -= y
                s2 -= y * y
        if i >= L - 1:
            m = s / L
            v = s2 / L - m * m
            moy[i] = m + ref
            ect[i] = np.sqrt(v) if v > 0 else 0.0
    return moy, ect


@njit(cache=True)
def ecart_variations(c, n=20):
    """Ecart-type des variations de prix sur les n dernieres barres (barre courante comprise)."""
    N = c.shape[0]
    dc = np.zeros(N)
    for i in range(1, N):
        dc[i] = c[i] - c[i - 1]
    _, e = moy_ecart(dc, n)
    return e


@njit(cache=True)
def ema(x, span):
    a = 2.0 / (span + 1.0)
    out = np.empty(x.shape[0])
    m = x[0]
    for i in range(x.shape[0]):
        m = a * x[i] + (1.0 - a) * m
        out[i] = m
    return out


@njit(cache=True)
def signaux(famille, o, h, l, c, v, vref, lc, ph, pl, sig, ect, nb, L, Z):
    """Signal (+1, -1 ou 0) des familles 7 a 15 a la cloture de chaque barre j, calcule avec les barres <= j seulement."""
    n = c.shape[0]
    s = np.zeros(n, np.int8)
    if famille == RSI:
        haut = 50.0 + 15.0 * Z
        bas = 50.0 - 15.0 * Z
        g = 0.0
        p = 0.0
        for i in range(1, n):
            x = c[i] - c[i - 1]
            if i <= L:
                g += max(x, 0.0) / L
                p += max(-x, 0.0) / L
            else:
                g = (g * (L - 1) + max(x, 0.0)) / L
                p = (p * (L - 1) + max(-x, 0.0)) / L
            if i >= L:
                r = 100.0 if p == 0.0 else 100.0 - 100.0 / (1.0 + g / p)
                if r > haut:
                    s[i] = 1
                elif r < bas:
                    s[i] = -1
    elif famille == MACD:
        lent = max(L + 1, int(round(L * 26.0 / 12.0)))
        m = ema(c, L) - ema(c, lent)
        hist = m - ema(m, max(2, int(round(L * 9.0 / 12.0))))
        k = Z * 0.1 * np.sqrt(L)
        for i in range(3 * lent, n):
            if hist[i] > k * sig[i]:
                s[i] = 1
            elif hist[i] < -k * sig[i]:
                s[i] = -1
    elif famille == SQUEEZE:
        e0 = np.where(np.isnan(ect), 0.0, ect)
        m100, _ = moy_ecart(e0, 100)
        moy, _ = moy_ecart(c, L)
        for i in range(L + 102, n):
            if ect[i - 1] < 0.8 * m100[i - 2] and ect[i] > 0:
                if c[i] > moy[i] + Z * ect[i]:
                    s[i] = 1
                elif c[i] < moy[i] - Z * ect[i]:
                    s[i] = -1
    elif famille == BALAYAGE or famille == BALAYAGE_VEILLE:
        for i in range(L if famille == BALAYAGE else 1, n):
            if np.isnan(sig[i]):
                continue
            marge = (Z - 0.25) * 0.5 * sig[i]
            if famille == BALAYAGE:
                hh = h[i - L]
                ll = l[i - L]
                for k in range(i - L + 1, i):
                    if h[k] > hh:
                        hh = h[k]
                    if l[k] < ll:
                        ll = l[k]
            else:
                d = i // nb
                hh = ph[d]
                ll = pl[d]
                if np.isnan(hh):
                    continue
            achat = l[i] < ll - marge and c[i] > ll
            vente = h[i] > hh + marge and c[i] < hh
            if achat and not vente:
                s[i] = 1
            elif vente and not achat:
                s[i] = -1
    elif famille == FVG:
        # dernier FVG haussier et dernier baissier : bas, haut, barre de formation ; consomme au premier retour (au plus un trade)
        hb = -1
        hbas = 0.0
        hhaut = 0.0
        bk = -1
        bbas = 0.0
        bhaut = 0.0
        for i in range(n):
            achat = hb >= 0 and i - hb <= L and l[i] <= hhaut and c[i] >= hbas
            vente = bk >= 0 and i - bk <= L and h[i] >= bbas and c[i] <= bhaut
            if achat:
                hb = -1
            if vente:
                bk = -1
            if achat and not vente:
                s[i] = 1
            elif vente and not achat:
                s[i] = -1
            if hb >= 0 and c[i] < hbas:
                hb = -1
            if bk >= 0 and c[i] > bhaut:
                bk = -1
            if i % nb >= 2 and not np.isnan(sig[i]):
                if l[i] - h[i - 2] >= Z * 0.5 * sig[i] and l[i] > h[i - 2]:
                    hb = i
                    hbas = h[i - 2]
                    hhaut = l[i]
                if l[i - 2] - h[i] >= Z * 0.5 * sig[i] and l[i - 2] > h[i]:
                    bk = i
                    bbas = h[i]
                    bhaut = l[i - 2]
    elif famille == FLUX:
        k = Z * 0.5 / np.sqrt(L)
        sd = 0.0
        sv = 0.0
        dl = np.zeros(n)
        for i in range(n):
            if h[i] > l[i]:
                dl[i] = v[i] * (2.0 * c[i] - h[i] - l[i]) / (h[i] - l[i])
            sd += dl[i]
            sv += v[i]
            if i >= L:
                sd -= dl[i - L]
                sv -= v[i - L]
            if i >= L - 1 and sv > 0:
                x = sd / sv
                if x > k:
                    s[i] = 1
                elif x < -k:
                    s[i] = -1
    elif famille == VOLUME:
        for i in range(n):
            if not np.isnan(vref[i]) and vref[i] > 0 and v[i] > (1.0 + Z) * vref[i]:
                if c[i] > o[i]:
                    s[i] = 1
                elif c[i] < o[i]:
                    s[i] = -1
    elif famille == LEADER:
        lo = np.log(c)
        lq = np.log(lc)
        ro = np.zeros(n)
        rl = np.full(n, np.nan)
        for i in range(1, n):
            ro[i] = lo[i] - lo[i - 1]
            rl[i] = lq[i] - lq[i - 1]
        ql = ql2 = qo = qo2 = 0.0
        nl = 0
        for i in range(1, n):
            if i % 1024 == 0 or i <= 20:
                # sommes exactes sur la fenetre i-19..i (recalculees regulierement pour eviter la derive)
                ql = ql2 = qo = qo2 = 0.0
                nl = 0
                for k in range(max(1, i - 19), i + 1):
                    qo += ro[k]
                    qo2 += ro[k] * ro[k]
                    if not np.isnan(rl[k]):
                        ql += rl[k]
                        ql2 += rl[k] * rl[k]
                        nl += 1
            else:
                qo += ro[i] - ro[i - 20]
                qo2 += ro[i] * ro[i] - ro[i - 20] * ro[i - 20]
                if not np.isnan(rl[i]):
                    ql += rl[i]
                    ql2 += rl[i] * rl[i]
                    nl += 1
                if not np.isnan(rl[i - 20]):
                    ql -= rl[i - 20]
                    ql2 -= rl[i - 20] * rl[i - 20]
                    nl -= 1
            if i < L + 20 or nl < 15 or np.isnan(lq[i]) or np.isnan(lq[i - L]):
                continue
            vl = ql2 / nl - (ql / nl) ** 2
            vo = qo2 / 20 - (qo / 20) ** 2
            if vl <= 1e-12 or vo <= 1e-12:     # fenetre sans mouvement (seance incomplete remplie) : pas de signal
                continue
            zl = (lq[i] - lq[i - L]) / np.sqrt(vl * L)
            zo = (lo[i] - lo[i - L]) / np.sqrt(vo * L)
            if zl - zo > Z:
                s[i] = 1
            elif zl - zo < -Z:
                s[i] = -1
    return s


@njit(cache=True)
def simuler(o, h, l, c, vwap, v, vref, lc, pc, ph, pl, gap_moy, interdit, regime, nb, famille, inverse, L, Z, sens, stop,
            objectif, debut, duree, filtre, cout, pt):
    """Renvoie (rendement net par seance, $ net par seance pour 1 micro, trades par seance).
    sens : 0 les deux, 1 achat seul, 2 vente seule ; filtre : 0 aucun, 1 jours agites, 2 jours calmes."""
    n = c.shape[0]
    nj = n // nb
    rend = np.zeros(nj)
    dollars = np.zeros(nj)
    ntr = np.zeros(nj, np.int32)
    moy, ect = moy_ecart(c, L)
    sig = ecart_variations(c, 20)
    sx = signaux(famille, o, h, l, c, v, vref, lc, ph, pl, sig, ect, nb, L, Z) if famille >= RSI else np.zeros(1, np.int8)
    derniere = nb - 6
    pos = 0
    entree = 0.0
    px_stop = 0.0
    px_obj = 0.0
    i_entree = 0
    orb_h = 0.0
    orb_l = 0.0
    o_jour = 0.0
    deja_gap = False
    for i in range(n):
        b = i % nb
        d = i // nb
        if b == 0:
            orb_h = h[i]
            orb_l = l[i]
            o_jour = o[i]
            deja_gap = False
        elif b < L:
            if h[i] > orb_h:
                orb_h = h[i]
            if l[i] < orb_l:
                orb_l = l[i]
        entre_ici = False
        if pos == 0 and b >= 1 and b >= debut and b <= derniere and not interdit[d]:
            j = i - 1
            bj = j % nb
            s = 0
            permis = (filtre == 0 or regime[d] == filtre) and not np.isnan(sig[j]) and sig[j] > 0
            if permis:
                if famille == MOYENNE:
                    if j >= L - 1 and ect[j] > 0:
                        z = (c[j] - moy[j]) / ect[j]
                        if z > Z:
                            s = 1
                        elif z < -Z:
                            s = -1
                elif famille == CANAL:
                    if j >= L:
                        hh = h[j - L]
                        ll = l[j - L]
                        for m in range(j - L + 1, j):
                            if h[m] > hh:
                                hh = h[m]
                            if l[m] < ll:
                                ll = l[m]
                        if c[j] > hh + Z * sig[j]:
                            s = 1
                        elif c[j] < ll - Z * sig[j]:
                            s = -1
                elif famille == OUVERTURE:
                    if bj >= L - 1:
                        if c[j] > orb_h + Z * sig[j]:
                            s = 1
                        elif c[j] < orb_l - Z * sig[j]:
                            s = -1
                elif famille == VWAP:
                    dv = c[j] - vwap[j]
                    if dv > Z * sig[j]:
                        s = 1
                    elif dv < -Z * sig[j]:
                        s = -1
                elif famille == DEPUIS:
                    mv = c[j] - o_jour
                    if mv > Z * sig[j]:
                        s = 1
                    elif mv < -Z * sig[j]:
                        s = -1
                elif famille == GAP:
                    if not deja_gap and not np.isnan(pc[d]) and not np.isnan(gap_moy[d]) and gap_moy[d] > 0:
                        g = o_jour / pc[d] - 1.0
                        if g > Z * gap_moy[d]:
                            s = 1
                        elif g < -Z * gap_moy[d]:
                            s = -1
                elif famille == VEILLE:
                    if not np.isnan(ph[d]):
                        if c[j] > ph[d] + Z * sig[j]:
                            s = 1
                        elif c[j] < pl[d] - Z * sig[j]:
                            s = -1
                else:
                    s = int(sx[j])
            if inverse == 1:
                s = -s
            if (sens == 1 and s < 0) or (sens == 2 and s > 0):
                s = 0
            if s != 0:
                pos = s
                entree = o[i]
                px_stop = entree * (1.0 - s * stop)
                px_obj = entree * (1.0 + s * objectif)
                i_entree = i
                entre_ici = True
                if famille == GAP:
                    deja_gap = True
        if pos != 0:
            sortie = np.nan
            if pos > 0:
                if (not entre_ici) and o[i] <= px_stop:
                    sortie = o[i]
                elif l[i] <= px_stop:
                    sortie = px_stop
                elif h[i] >= px_obj:
                    sortie = px_obj
            else:
                if (not entre_ici) and o[i] >= px_stop:
                    sortie = o[i]
                elif h[i] >= px_stop:
                    sortie = px_stop
                elif l[i] <= px_obj:
                    sortie = px_obj
            if np.isnan(sortie) and (b == nb - 1 or i - i_entree + 1 >= duree):
                sortie = c[i]
            if not np.isnan(sortie):
                points = pos * (sortie - entree) - cout
                rend[d] += points / entree
                dollars[d] += points * pt
                ntr[d] += 1
                pos = 0
    return rend, dollars, ntr


def volume_reference(v, interdit, n=20):
    """Volume moyen de chaque barre sur les n seances jouables d'avant (la seance elle-meme exclue), NaN avant."""
    ref = np.full(v.shape, np.nan)
    pile = []
    for dj in range(v.shape[0]):
        if len(pile) == n:
            ref[dj] = np.mean(pile, axis=0)
        if not interdit[dj]:
            pile.append(v[dj])
            if len(pile) > n:
                pile.pop(0)
    return ref


def preparer(d):
    """Ajoute le volume de reference (famille 14), recalcule a chaque chargement (et sur le bruit)."""
    return {**d, "vref": volume_reference(d["v"], d["interdit"])}


def lancer(d, g):
    """g : dict de genes decodes ; d : dict du marche passe par preparer() (tableaux seances x barres, aplatis ici)."""
    return simuler(d["o"].ravel(), d["h"].ravel(), d["l"].ravel(), d["c"].ravel(), d["vwap"].ravel(), d["v"].ravel(),
                   d["vref"].ravel(), d["lc"].ravel(), d["pc"], d["ph"], d["pl"], d["gap_moy"], d["interdit"], d["regime"], int(d["nb"]), int(g["famille"]), int(g["inverse"]),
                   int(g["L"]), float(g["Z"]), int(g["sens"]), float(g["stop"]), float(g["objectif"]), int(g["debut"]),
                   int(g["duree"]), int(g["filtre"]), float(d["cout"]), float(d["pt"]))


def charger(chemin):
    z = np.load(chemin)
    return {k: z[k] for k in z.files}
