"""Piste D (ml/arene/PISTES.md) : le Supertrend 10-3 (barres de 5 min) sur 7 marches micro, fenetres et frais de
scalping/commun.py, memes regles qu'au NQ (verifiees contre le bot C#) ramenees a la longueur de chaque fenetre."""
import os
import sys

import numba as nb
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scalping"))
from commun import MARCHES  # noqa: E402

KB = os.environ.get("KB_DONNEES")


def seances(nom):
    f, ppt, tick, deb, fin, frais, ref, _ = MARCHES[nom]
    d = pd.read_csv(os.path.join(KB, f), usecols=[0, 1, 2, 3, 4])
    d.columns = ["t", "o", "h", "l", "c"]
    m = d.t.str[11:13].astype(int) * 60 + d.t.str[14:16].astype(int) - deb
    Lm = fin - deb
    g = (m >= 0) & (m < Lm)
    d, m = d[g], m[g].to_numpy()
    j = d.t.str[:10]
    J = np.array(sorted(j.unique()))
    i = pd.Index(J).get_indexer(j)
    A = {}
    for k in "ohlc":
        a = np.full((len(J), Lm), np.nan); a[i, m] = d[k].to_numpy(float); A[k] = a
    pres = ~np.isnan(A["c"])
    C = pd.DataFrame(A["c"]).ffill(axis=1).bfill(axis=1).to_numpy()
    O, H, L = [np.where(np.isnan(A[k]), C, A[k]) for k in "ohl"]
    ok = pres[:, 0] & pres[:, Lm - 1] & (pres.sum(1) >= Lm - 20)
    return dict(J=J, O=O, H=H, L=L, C=C, ok=ok, Lm=Lm, ppt=ppt, frais=frais, ref=ref, tick=tick)


@nb.njit(cache=True)
def supertrend(H, L, C, nb5):
    S = C.shape[0]; n = S * nb5
    h5, l5, c5 = np.empty(n), np.empty(n), np.empty(n)
    for s in range(S):
        for b in range(nb5):
            i = s * nb5 + b
            h5[i] = H[s, 5 * b:5 * b + 5].max(); l5[i] = L[s, 5 * b:5 * b + 5].min(); c5[i] = C[s, 5 * b + 4]
    st = np.zeros(n)
    atr, hb, lb, d = 0.0, np.nan, np.nan, 1.0
    for i in range(1, n):
        tr = max(h5[i] - l5[i], abs(h5[i] - c5[i - 1]), abs(l5[i] - c5[i - 1]))
        atr = tr if i == 1 else (atr * 9 + tr) / 10
        mid = (h5[i] + l5[i]) / 2
        hb2, lb2 = mid + 3 * atr, mid - 3 * atr
        if i > 1:
            hb2 = hb2 if (hb2 < hb or c5[i - 1] > hb) else hb
            lb2 = lb2 if (lb2 > lb or c5[i - 1] < lb) else lb
            if d > 0 and c5[i] < lb2:
                d = -1.0
            elif d < 0 and c5[i] > hb2:
                d = 1.0
        hb, lb = hb2, lb2
        st[i] = d if i >= 10 else 0.0
    return st


def trades(M):
    """Comme le bot NQ : decision a la cloture de la barre de 5 min, ordre a l'ouverture de la minute suivante, entrees
    jusqu'a 30 min avant la fin de la fenetre, a plat a la cloture de la minute Lm - 6 (5 min avant la fin)."""
    Lm = M["Lm"]; nb5 = Lm // 5
    st = supertrend(M["H"][:, :nb5 * 5], M["L"][:, :nb5 * 5], M["C"][:, :nb5 * 5], nb5)
    O, C = M["O"], M["C"]
    derniere, aplat = Lm - 30, Lm - 6
    out = []
    for s in np.nonzero(M["ok"])[0]:
        pos, m_in, e = 0, -1, 0.0
        for b in range(nb5 - 2):
            m = 5 * b + 5
            if m > aplat:
                break
            sens = st[s * nb5 + b]
            cible = pos if sens == 0 else int(sens)
            if cible != pos and pos != 0:
                out.append((s, pos, m_in, m - 1, e, O[s, m])); pos = 0
            if cible != 0 and pos == 0 and m <= derniere:
                pos, m_in, e = cible, m, O[s, m]
        if pos != 0:
            out.append((s, pos, m_in, aplat, e, C[s, aplat]))
    return out


def journees(M, tr, taille=1, limite=1e9):
    """Resultat et pire moment de chaque seance, en $ au prix d'aujourd'hui pour 1 micro, frais compris."""
    S = len(M["J"]); res = np.zeros(S); dip = np.zeros(S)
    t = sorted(tr, key=lambda x: (x[0], x[2]))
    k = 0
    while k < len(t):
        s = t[k][0]; real = 0.0; creux = 0.0; arret = False
        while k < len(t) and t[k][0] == s:
            _, sens, m0, m1, e, x = t[k]
            if not arret:
                ech = M["ppt"] * M["ref"] / e * taille
                pire = (M["L"][s, m0:m1 + 1] if sens > 0 else M["H"][s, m0:m1 + 1])
                eq = real + sens * (pire - e) * ech
                creux = min(creux, eq.min())
                if eq.min() <= -limite:
                    real = -limite - M["frais"] * taille; arret = True
                else:
                    real += sens * (x - e) * ech - M["frais"] * taille
            k += 1
        res[s] = real; dip[s] = creux
    return res, dip
