#!/usr/bin/env python3
"""Moteur de la machine scalping (README.md, regles du 24 octobre 2026) : indicateurs connus a la cloture de chaque
minute, familles F0 a F9 (partie B) et regles A1 a A5b (partie A), execution au marche ou a cours limite, stops et
objectifs verifies dans la minute dans l'ordre le plus defavorable, gains au prix d'aujourd'hui."""
import numpy as np
from numba import njit

import commun as K

# --- genome (tableau float64 de longueur NG) ---------------------------------------------------------------------
FAM, INV, COTES, DEBUT, FIN, REGIME, TEND, ENTREE, FENETRE, STOP, OBJ, DUREE, PAUSE, PK, PZ, PX, PY, PW = range(18)
NG = 18
DEBUTS = np.array([1, 15, 30, 60, 120, 180], np.int64)
FINS = np.array([60, 120, 210, 300, -5], np.int64)            # -5 : 5 minutes avant la fin
LIMITES = np.array([0.0, 0.1, 0.25, 0.5])                       # 0 : au marche
FENETRES = np.array([1, 3, 5], np.int64)
DUREES = np.array([1, 2, 3, 5, 10, 15, 20, 30], np.int64)
PAUSES = np.array([0, 5, 15], np.int64)
K_F1 = np.array([2, 3, 5, 10, 15, 30], np.int64)
K_F3 = np.array([5, 10, 15, 20, 30], np.int64)
K_F7 = np.array([1, 2, 3, 5], np.int64)
K_F8 = np.array([5, 10, 15, 30], np.int64)
TAILLE_F8 = np.array([1, 3, 5], np.int64)
K_F9 = np.array([1, 5, 15, 30], np.int64)
EVENEMENTS = np.array([1, 5, 15, 30, 31, 60, 90, 150, 210, 270, 300, 330, 360, 375, 380], np.int64)
NIVEAUX = 12          # F5 : 0 plus haut veille, 1 plus bas veille, 2 cloture veille, 3-8 range d'ouverture 5/15/30 (haut, bas),
                      # 9 plus haut du jour, 10 plus bas du jour, 11 niveau rond
SQ15 = np.sqrt(15.0)
SQ30 = np.sqrt(30.0)


# --- indicateurs ---------------------------------------------------------------------------------------------------
def indicateurs(d):
    """d : dictionnaire de donnees (donnees.py ou bruit.py). Renvoie le dictionnaire des tableaux utilises par le moteur."""
    O, H, L, C, V = d["o"], d["h"], d["l"], d["c"], d["v"]
    S, N = C.shape
    lr = np.empty_like(C)
    lr[:, 0] = np.log(C[:, 0] / O[:, 0])
    lr[:, 1:] = np.log(C[:, 1:] / C[:, :-1])
    complete = d["complete"]
    prec_tout, prec_meme = d["prec_tout"], d["prec_meme"]
    var_jour = (lr ** 2).mean(axis=1)
    init = np.where(prec_tout >= 0, var_jour[np.maximum(prec_tout, 0)], np.nan)
    sig, sigp = _ewma(lr, init)
    typ = (H + L + C) / 3
    cv = np.cumsum(V, axis=1)
    vwap = np.where(cv > 0, np.cumsum(typ * V, axis=1) / np.where(cv > 0, cv, 1.0),
                    np.cumsum(typ, axis=1) / np.arange(1, N + 1))
    hh = np.maximum.accumulate(H, axis=1)
    ll = np.minimum.accumulate(L, axis=1)
    ph = np.where(prec_meme >= 0, H.max(axis=1)[np.maximum(prec_meme, 0)], np.nan)
    pl = np.where(prec_meme >= 0, L.min(axis=1)[np.maximum(prec_meme, 0)], np.nan)
    pc = np.where(prec_meme >= 0, C[np.maximum(prec_meme, 0), N - 1], np.nan)
    idx_c = np.flatnonzero(complete)
    vm = np.full(C.shape, np.nan)
    medsig = np.full(C.shape, np.nan)
    # partie A : seuils connus avant la seance (seances completes precedentes seulement)
    a1 = np.abs(np.log(C[:, 14] / O[:, 0]))
    a3 = np.abs(lr[:, 30]) if N > 31 else np.zeros(S)
    thr1 = np.full(S, np.nan)
    thr3 = np.full(S, np.nan)
    q999 = np.full(S, np.nan)
    sd10 = np.full(S, np.nan)
    nb10 = N // 10
    r10 = np.empty((S, nb10))
    r10[:, 0] = np.log(C[:, 9] / O[:, 0])
    r10[:, 1:] = np.log(C[:, 19::10][:, :nb10 - 1] / C[:, 9::10][:, :nb10 - 1])
    for s in range(S):
        k = np.searchsorted(idx_c, s)              # nombre de seances completes strictement avant s
        if k >= 10:
            vm[s] = np.median(V[idx_c[k - 10:k]], axis=0)
        if k >= 20:
            p = idx_c[k - 20:k]
            medsig[s] = np.median(sig[p], axis=0)          # regime : sigma a la meme minute des 20 seances d'avant
            q999[s] = np.quantile(np.abs(lr[p, 1:]).ravel(), 0.999)
            sd10[s] = r10[p].std(ddof=1)
        if k >= 252:
            p = idx_c[k - 252:k]
            thr1[s] = np.quantile(a1[p], 0.90)
            thr3[s] = np.quantile(a3[p], 0.90)
    rg = sig / medsig
    jouable = complete & ~d["ech"] & np.isfinite(init) & np.isfinite(medsig[:, 0]) & np.isfinite(vm[:, 0])
    f = dict(O=O, H=H, L=L, C=C, V=V, lr=lr, sig=sig, sigp=sigp, vwap=vwap, hh=hh, ll=ll, ph=ph, pl=pl, pc=pc, vm=vm,
             rg=rg, jouable=jouable, echelle=d["pref"] / O[:, 0], thr1=thr1, thr3=thr3, q999=q999, sd10=sd10,
             pt=float(d["pt"]), tick=float(d["tick"]), frais=float(d["frais"]), rond=float(d["rond"]),
             pas=float(d["pas"]) if "pas" in d else float(d["tick"]),
             evts=np.asarray(d["evenements"], np.int64) if "evenements" in d else EVENEMENTS, jours=d["jours"])
    if "autre_c" in d:
        X = d["autre_c"]
        lx = np.zeros_like(X)
        lx[:, 1:] = np.log(X[:, 1:] / X[:, :-1])
        vx = np.where(np.isfinite(X).all(axis=1), (lx ** 2).mean(axis=1), np.nan)   # seance absente : NaN
        initx = np.where(prec_tout >= 0, vx[np.maximum(prec_tout, 0)], np.nan)
        _, sxp = _ewma(np.nan_to_num(lx), initx)
        f["X"] = X
        f["sxp"] = np.where(np.isfinite(X), sxp, np.nan)
    else:
        f["X"] = np.full((1, 1), np.nan)
        f["sxp"] = np.full((1, 1), np.nan)
    return f


@njit(cache=True)
def _ewma(lr, init):
    lam = 0.5 ** (1.0 / 30.0)
    S, N = lr.shape
    sig = np.empty_like(lr)
    sigp = np.empty_like(lr)
    for s in range(S):
        v = init[s]
        for t in range(N):
            sigp[s, t] = np.sqrt(v)
            v = lam * v + (1.0 - lam) * lr[s, t] ** 2
            sig[s, t] = np.sqrt(v)
    return sig, sigp


# --- signaux --------------------------------------------------------------------------------------------------------
@njit(cache=True)
def _cond(g, s, t, O, H, L, C, V, sigp, vwap, hh, ll, ph, pl, pc, vm, X, sxp, rond, evts, h):
    """Direction du signal brut de la famille a la cloture de la minute t (0 : rien), avant le gene 'sens'."""
    fam = int(g[FAM])
    sp = sigp[s, t]
    if not (sp > 0):
        return 0
    if fam == 0:
        r = np.log(C[s, t] / (C[s, t - 1] if t > 0 else O[s, 0]))
        if abs(r) >= g[PZ] * sp:
            return 1 if r > 0 else -1
        return 0
    if fam == 1:
        k = K_F1[int(g[PK])]
        if t < k:
            return 0
        r = np.log(C[s, t] / C[s, t - k])
        if abs(r) >= g[PZ] * sp * np.sqrt(k):
            return 1 if r > 0 else -1
        return 0
    if fam == 2:
        n = int(g[PK])
        if t < n:
            return 0
        up = True
        dn = True
        for j in range(t - n + 1, t + 1):
            if not (C[s, j] > C[s, j - 1]):
                up = False
            if not (C[s, j] < C[s, j - 1]):
                dn = False
        if not (up or dn):
            return 0
        r = np.log(C[s, t] / C[s, t - n])
        if abs(r) < g[PZ] * sp * np.sqrt(n):
            return 0
        return 1 if up else -1
    if fam == 3:
        k = K_F3[int(g[PK])]
        if t < k:
            return 0
        hi = H[s, t - k]
        lo = L[s, t - k]
        for j in range(t - k + 1, t):
            if H[s, j] > hi:
                hi = H[s, j]
            if L[s, j] < lo:
                lo = L[s, j]
        if (hi - lo) / C[s, t - 1] >= g[PY] * sp * np.sqrt(k):
            return 0
        if C[s, t] > hi:
            return 1
        if C[s, t] < lo:
            return -1
        return 0
    if fam == 4:
        e = (C[s, t] - vwap[s, t]) / C[s, t]
        if abs(e) >= g[PZ] * sp * SQ30:
            return 1 if e > 0 else -1
        return 0
    if fam == 5:
        if t < 1:
            return 0
        typ = int(g[PX])
        conf = int(g[PW])
        marge = g[PZ] * sp * C[s, t]
        if typ == 11:
            r0 = np.floor(C[s, t - 1] / rond + 1e-9)
            if conf == 0:
                r1 = np.floor(C[s, t] / rond + 1e-9)
                if r1 > r0 and C[s, t] - r1 * rond >= marge:
                    return 1
                if r1 < r0 and (r1 + 1.0) * rond - C[s, t] >= marge:
                    return -1
                return 0
            nv = (r0 + 1) * rond                 # rejet du niveau rond au-dessus ou au-dessous (a une demi-maille pres)
            if H[s, t] > nv + h and C[s, t] < nv - h:
                return -1
            nv = r0 * rond
            if L[s, t] < nv - h and C[s, t] > nv + h and C[s, t - 1] > nv + h:
                return 1
            return 0
        if typ == 9 or typ == 10:
            if t < 1:
                return 0
            if typ == 9:
                lv = hh[s, t - 1]
                if conf == 0:
                    return 1 if C[s, t] > lv + marge else 0
                return -1 if (H[s, t] > lv and C[s, t] < lv) else 0
            lv = ll[s, t - 1]
            if conf == 0:
                return -1 if C[s, t] < lv - marge else 0
            return 1 if (L[s, t] < lv and C[s, t] > lv) else 0
        if typ <= 2:
            lv = ph[s] if typ == 0 else (pl[s] if typ == 1 else pc[s])
        else:
            m = 5 if typ <= 4 else (15 if typ <= 6 else 30)
            if t < m:                            # le range d'ouverture n'est connu qu'apres sa derniere minute
                return 0
            lv = hh[s, m - 1] if (typ % 2 == 1) else ll[s, m - 1]
        if not np.isfinite(lv):
            return 0
        a, b = C[s, t - 1], C[s, t]
        if conf == 0:
            if a <= lv and b >= lv + marge and b > lv:
                return 1
            if a >= lv and b <= lv - marge and b < lv:
                return -1
            return 0
        if a < lv and H[s, t] > lv and b < lv:
            return -1
        if a > lv and L[s, t] < lv and b > lv:
            return 1
        return 0
    if fam == 6:
        m = vm[s, t]
        if m > 0 and V[s, t] >= g[PY] * m and C[s, t] != O[s, t]:
            return 1 if C[s, t] > O[s, t] else -1
        return 0
    if fam == 7:
        k = K_F7[int(g[PK])]
        if t < k or X.shape[0] == 1:
            return 0
        x0 = X[s, t - k]
        x1 = X[s, t]
        sx = sxp[s, t]
        if not (np.isfinite(x0) and np.isfinite(x1) and sx > 0):
            return 0
        rk = np.sqrt(k)
        zx = np.log(x1 / x0) / (sx * rk)
        zs = np.log(C[s, t] / C[s, t - k]) / (sp * rk)
        if zx >= g[PZ] and zx - zs >= g[PY]:
            return 1
        if zx <= -g[PZ] and zs - zx >= g[PY]:
            return -1
        return 0
    if fam == 8:
        m = TAILLE_F8[int(g[PW])]
        if (t + 1) % m != 0 or t + 1 < 2 * m:
            return 0
        a0 = t - m + 1
        o = O[s, a0]
        c = C[s, t]
        hi = H[s, a0]
        lo = L[s, a0]
        for j in range(a0 + 1, t + 1):
            if H[s, j] > hi:
                hi = H[s, j]
            if L[s, j] < lo:
                lo = L[s, j]
        rng = hi - lo
        if rng <= 0:
            return 0
        motif = 0
        if int(g[PX]) == 0:                       # meche
            if min(o, c) - lo >= g[PY] * rng and c >= lo + 2.0 * rng / 3.0:
                motif = 1
            elif hi - max(o, c) >= g[PY] * rng and c <= lo + rng / 3.0:
                motif = -1
        else:                                     # avalement
            po = O[s, a0 - m]
            pcl = C[s, a0 - 1]
            if c > o and pcl < po and c >= po and o <= pcl:
                motif = 1
            elif c < o and pcl > po and c <= po and o >= pcl:
                motif = -1
        if motif == 0:
            return 0
        k = K_F8[int(g[PK])]
        if a0 - 1 - k < 0:
            return 0
        r = np.log(C[s, a0 - 1] / C[s, a0 - 1 - k])
        z = r / (sp * np.sqrt(k))
        if motif == 1 and z <= -g[PZ]:
            return 1
        if motif == -1 and z >= g[PZ]:
            return -1
        return 0
    if fam == 9:
        e = evts[int(g[PX])]
        if t != e - 1:
            return 0
        k = K_F9[int(g[PK])]
        base = C[s, t - k] if t - k >= 0 else O[s, 0]
        r = np.log(C[s, t] / base)
        if r == 0.0 or abs(r) < g[PZ] * sp * np.sqrt(k):
            return 0
        return 1 if r > 0 else -1
    return 0


# --- execution -------------------------------------------------------------------------------------------------------
@njit(cache=True)
def _vers_perte(x, sens, pas):
    """Prix sur la grille, arrondi du cote defavorable pour une position de sens `sens` (stop, limite d'achat ou de
    vente : plus bas pour un achat, plus haut pour une vente)."""
    if sens == 1:
        return np.floor(x / pas + 1e-6) * pas
    return np.ceil(x / pas - 1e-6) * pas


@njit(cache=True)
def _vers_loin(x, sens, pas):
    """Objectif sur la grille, arrondi en s'eloignant du prix d'entree (prudent)."""
    if sens == 1:
        return np.ceil(x / pas - 1e-6) * pas
    return np.floor(x / pas + 1e-6) * pas

@njit(cache=True)
def evaluer(g, s0, s1, O, H, L, C, V, lr, sig, sigp, vwap, hh, ll, ph, pl, pc, vm, rg, jouable, echelle, thr1, thr3,
            q999, sd10, X, sxp, pt, tick, frais, rond, evts, pas, journal):
    """Joue le genome g sur les seances [s0, s1). Renvoie (gain $ par seance, NaN si la seance n'est pas jouable ;
    nombre de trades ; trades gagnants ; somme des gains avant frais). journal (n, 6) : si n > 1, les n premiers trades
    (seance, minute d'entree, minute de sortie, sens, prix d'entree, prix de sortie)."""
    S, N = C.shape
    fam = int(g[FAM])
    gain = np.zeros(s1 - s0)
    ntr = 0
    nwin = 0
    brut = 0.0
    nj = 0
    debut = DEBUTS[int(g[DEBUT])]
    fin = FINS[int(g[FIN])]
    if fin < 0:
        fin = N + fin
    croisement = fam == 1 or fam == 4 or fam == 7
    h = 0.5 * pas                 # demi-maille de la grille des prix : comparaisons sans erreur d'arrondi
    pause = PAUSES[int(g[PAUSE])] if fam < 10 else 0
    for s in range(s0, s1):
        if not jouable[s]:
            gain[s - s0] = np.nan
            continue
        pos = 0
        attente = 0          # 0 rien ; 1 ordre au marche (ouverture suivante) ; 2 ordre a cours limite
        a_dir = 0
        a_lim = 0.0
        a_exp = 0
        a_ds = 0.0
        a_dt = 0.0
        a_tr = 0.0
        a_stop_abs = 0.0
        ent = 0.0
        stp = np.nan
        tgt = np.nan
        e = 0
        hmax = 1
        lim_fill = False
        prochain = 0
        touche = np.zeros(401 if fam == 14 else 1, np.bool_)
        base_rond = np.floor(O[s, 0] / rond + 1e-9) - 200.0
        for t in range(N):
            # 1) ordre en attente, execute pendant la minute t
            if attente != 0 and pos == 0 and t > N - 3:
                attente = 0                              # pas de remplissage dans les 2 dernieres minutes
            if attente != 0 and pos == 0:
                rempli = False
                if attente == 1:
                    ent = O[s, t]
                    rempli = True
                    lim_fill = False
                elif a_dir == 1:
                    if O[s, t] < a_lim - h:                  # ouverture strictement au-dela de la limite
                        ent = O[s, t]
                        rempli = True
                        lim_fill = True
                    elif L[s, t] <= a_lim - tick + h:        # limite traversee d'au moins un tick
                        ent = a_lim
                        rempli = True
                        lim_fill = True
                else:
                    if O[s, t] > a_lim + h:
                        ent = O[s, t]
                        rempli = True
                        lim_fill = True
                    elif H[s, t] >= a_lim + tick - h:
                        ent = a_lim
                        rempli = True
                        lim_fill = True
                if rempli:
                    pos = a_dir
                    e = t
                    attente = 0
                    if a_stop_abs != 0.0:
                        stp = a_stop_abs
                    elif a_ds > 0.0:
                        stp = _vers_perte(ent - pos * a_ds, pos, tick)
                    else:
                        stp = np.nan
                    if a_tr > 0.0:
                        tgt = _vers_loin(ent * (1.0 + pos * a_tr), pos, tick)
                    elif a_dt > 0.0:
                        tgt = _vers_loin(ent + pos * a_dt, pos, tick)
                    else:
                        tgt = np.nan
                elif attente == 2 and t >= a_exp:
                    attente = 0
                    prochain = t
            # 1b) A5a : premier contact d'un niveau rond, ordre limite pose sur le niveau
            if fam == 14 and t >= 1:
                bas_ = min(L[s, t], C[s, t - 1])            # un niveau saute par un ecart compte comme touche
                haut_ = max(H[s, t], C[s, t - 1])
                lo_k = max(int(np.floor(bas_ / rond - 1e-9) - base_rond), 0)
                hi_k = min(int(np.floor(haut_ / rond + 1e-9) - base_rond) + 1, 401)
                choix = -1
                dist = 1e18
                for kk in range(lo_k, hi_k):
                    nv = (kk + base_rond) * rond
                    if nv < bas_ - h or nv > haut_ + h or touche[kk]:
                        continue
                    touche[kk] = True
                    dd = abs(nv - C[s, t - 1])
                    if dd < dist:
                        dist = dd
                        choix = kk
                if choix >= 0 and pos == 0 and attente == 0 and t >= 30 and t <= 360 and t <= N - 3:
                    nv = (choix + base_rond) * rond
                    if C[s, t - 1] < nv - h and L[s, t] <= nv + h and H[s, t] >= nv + tick - h:
                        pos = -1
                    elif C[s, t - 1] > nv + h and H[s, t] >= nv - h and L[s, t] <= nv - tick + h:
                        pos = 1
                    if pos != 0:
                        ent = nv
                        e = t
                        lim_fill = True
                        stp = _vers_perte(ent * (1.0 - pos * 0.0015), pos, tick)
                        tgt = _vers_loin(ent * (1.0 + pos * 0.003), pos, tick)
                        hmax = 30
            elif fam == 14:
                lo_k = max(int(np.floor(L[s, 0] / rond - 1e-9) - base_rond), 0)
                hi_k = min(int(np.floor(H[s, 0] / rond + 1e-9) - base_rond) + 1, 401)
                for kk in range(lo_k, hi_k):
                    nv = (kk + base_rond) * rond
                    if L[s, 0] - h <= nv <= H[s, 0] + h:
                        touche[kk] = True
            # 2) gestion de la position pendant la minute t (ordre le plus defavorable)
            if pos != 0 and t >= e:
                sortie = np.nan
                if t == e and np.isfinite(stp) and pos * (ent - stp) <= h:
                    sortie = ent                         # entree deja au-dela du stop : sortie immediate
                elif pos == 1:
                    if t > e and np.isfinite(stp) and O[s, t] <= stp + h:
                        sortie = O[s, t]
                    elif np.isfinite(stp) and L[s, t] <= stp + h:
                        sortie = stp
                    elif (not (lim_fill and t == e)) and np.isfinite(tgt) and H[s, t] >= tgt + tick - h:
                        sortie = tgt
                else:
                    if t > e and np.isfinite(stp) and O[s, t] >= stp - h:
                        sortie = O[s, t]
                    elif np.isfinite(stp) and H[s, t] >= stp - h:
                        sortie = stp
                    elif (not (lim_fill and t == e)) and np.isfinite(tgt) and L[s, t] <= tgt - tick + h:
                        sortie = tgt
                if not np.isfinite(sortie) and (t >= e + hmax - 1 or t == N - 1):
                    sortie = C[s, t]
                if np.isfinite(sortie):
                    pts = pos * (sortie - ent)
                    g_ = pts * pt * echelle[s] - frais
                    gain[s - s0] += g_
                    brut += pts * pt * echelle[s]
                    ntr += 1
                    if g_ > 0:
                        nwin += 1
                    if journal.shape[0] > 1 and nj < journal.shape[0]:
                        journal[nj, 0] = s
                        journal[nj, 1] = e
                        journal[nj, 2] = t
                        journal[nj, 3] = pos
                        journal[nj, 4] = ent
                        journal[nj, 5] = sortie
                        nj += 1
                    pos = 0
                    prochain = t + pause
            # 3) signal a la cloture de la minute t
            if fam < 10:
                if pos != 0 or attente != 0 or t < prochain or t + 1 < debut or t + 1 >= fin or t + 1 > N - 3:
                    continue
                reg = int(g[REGIME])
                if (reg == 1 and not (rg[s, t] > 1.2)) or (reg == 2 and not (rg[s, t] < 0.8)):
                    continue
                d = _cond(g, s, t, O, H, L, C, V, sigp, vwap, hh, ll, ph, pl, pc, vm, X, sxp, rond, evts, h)
                if d == 0:
                    continue
                if croisement and t >= 1:
                    if _cond(g, s, t - 1, O, H, L, C, V, sigp, vwap, hh, ll, ph, pl, pc, vm, X, sxp, rond, evts, h) == d:
                        continue
                if g[INV] > 0.5:
                    d = -d
                cot = int(g[COTES])
                if (cot == 1 and d < 0) or (cot == 2 and d > 0):
                    continue
                td = int(g[TEND])
                sgn = 1 if C[s, t] > O[s, 0] else (-1 if C[s, t] < O[s, 0] else 0)
                if (td == 1 and sgn != d) or (td == 2 and sgn != -d):
                    continue
                u = sig[s, t] * SQ15 * C[s, t]
                a_ds = max(g[STOP] * u, 2.0 * tick) if g[STOP] > 0 else 0.0
                a_dt = max(g[OBJ] * u, 2.0 * tick) if g[OBJ] > 0 else 0.0
                a_tr = 0.0
                a_stop_abs = 0.0
                a_dir = d
                hmax = DUREES[int(g[DUREE])]
                j = LIMITES[int(g[ENTREE])]
                if j == 0.0:
                    attente = 1
                else:
                    attente = 2
                    a_lim = C[s, t] - d * j * u
                    a_lim = _vers_perte(a_lim, d, tick)    # limite au tick du micro, en s'eloignant du marche
                    a_exp = t + FENETRES[int(g[FENETRE])]
            elif fam != 14:
                if pos != 0 or attente != 0 or t + 1 > N - 3:
                    continue
                d = 0
                a_ds = 0.0
                a_dt = 0.0
                a_tr = 0.0
                a_stop_abs = 0.0
                if fam == 10:                      # A1 : Grant, Wolf, Yu
                    if t == 14 and np.isfinite(thr1[s]):
                        r = np.log(C[s, 14] / O[s, 0])
                        if abs(r) >= thr1[s] and r != 0.0:
                            d = -1 if r > 0 else 1
                            hmax = N
                elif fam == 11:                    # A2 : minute extreme
                    if t >= 1 and np.isfinite(q999[s]) and abs(lr[s, t]) >= q999[s] and lr[s, t] != 0.0:
                        d = -1 if lr[s, t] > 0 else 1
                        hmax = 1
                elif fam == 12:                    # A3 : saut de 10 h 00
                    if t == 30 and np.isfinite(thr3[s]) and abs(lr[s, 30]) >= thr3[s] and lr[s, 30] != 0.0:
                        d = 1 if lr[s, 30] > 0 else -1
                        hmax = 1
                elif fam == 13:                    # A4 : mouvement de 10 minutes extreme
                    if (t + 1) % 10 == 0 and np.isfinite(sd10[s]) and sd10[s] > 0:
                        r = np.log(C[s, t] / (C[s, t - 10] if t >= 10 else O[s, 0]))
                        if abs(r) >= 2.0 * sd10[s] and r != 0.0:
                            d = -1 if r > 0 else 1
                            hmax = 10
                elif fam == 15:                    # A5b : cassure d'un niveau rond
                    if t >= 1 and t + 1 >= 30 and t + 1 <= 360:
                        r0 = np.floor(C[s, t - 1] / rond + 1e-9)
                        r1 = np.floor(C[s, t] / rond + 1e-9)
                        if r1 > r0 and C[s, t] >= r1 * rond * 1.0005:
                            d = 1
                            a_stop_abs = r1 * rond
                        elif r1 < r0 and C[s, t] <= (r1 + 1.0) * rond * 0.9995:
                            d = -1
                            a_stop_abs = (r1 + 1.0) * rond
                        if d != 0:
                            hmax = 30
                            a_tr = 0.003
                if d != 0:
                    a_dir = d
                    attente = 1
    return gain, ntr, nwin, brut


def arguments(f):
    return (f["O"], f["H"], f["L"], f["C"], f["V"], f["lr"], f["sig"], f["sigp"], f["vwap"], f["hh"], f["ll"], f["ph"],
            f["pl"], f["pc"], f["vm"], f["rg"], f["jouable"], f["echelle"], f["thr1"], f["thr3"], f["q999"], f["sd10"],
            f["X"], f["sxp"], f["pt"], f["tick"], f["frais"], f["rond"], f["evts"], f["pas"])


def jouer(g, f, s0, s1, journal=0):
    jr = np.zeros((max(journal, 1), 6))
    gain, ntr, nwin, brut = evaluer(np.asarray(g, np.float64), int(s0), int(s1), *arguments(f), jr)
    return gain, ntr, nwin, brut, (jr[:min(journal, ntr)] if journal else None)
