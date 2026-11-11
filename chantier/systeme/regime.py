"""Detecteur de regime du marche (partie A du chantier). L'etat d'une seance est connu la veille a 16 h 15.

Entrees : les clotures quotidiennes du NQ (seances completes, dans l'ordre) et, pour les memes seances, le VIX et le
VIX3M de la veille. Sortie : un etat par seance parmi CHUTE, VOLATIL, TENDANCE, CALME (ou None s'il manque du passe).
"""
import numpy as np

ETATS = ("CHUTE", "VOLATIL", "TENDANCE", "CALME")


def etats(clotures, vix_veille, vix3m_veille):
    """clotures[i] = cloture de la seance i. L'etat de la seance i n'utilise que les clotures 0..i-1."""
    c = np.asarray(clotures, float); n = len(c)
    r = np.diff(np.log(c))                                   # r[k] = rendement de la seance k+1
    vol = np.full(n, np.nan); tend = np.full(n, np.nan); r5 = np.full(n, np.nan)
    for p in range(20, n):                                   # valeurs connues a la cloture de la seance p
        x = r[p - 20:p]; s = x.std(ddof=1)
        vol[p] = s; tend[p] = abs(x.sum()) / (s * np.sqrt(20)) if s > 0 else 0.0; r5[p] = r[p - 5:p].sum()
    out = [None] * n
    for i in range(273, n):                                  # 20 seances de mesure + 252 valeurs d'avant
        p = i - 1
        passe_vol = vol[p - 252:p]; passe_r5 = r5[p - 252:p]
        if not (np.isfinite(passe_vol).all() and np.isfinite(passe_r5).all()):
            continue
        inverse = np.isfinite(vix_veille[i]) and np.isfinite(vix3m_veille[i]) and vix_veille[i] >= vix3m_veille[i]
        chute = r5[p] <= np.percentile(passe_r5, 10)
        if inverse or chute:
            out[i] = "CHUTE"
        elif vol[p] > np.percentile(passe_vol, 200 / 3):
            out[i] = "VOLATIL"
        elif tend[p] >= 1:
            out[i] = "TENDANCE"
        else:
            out[i] = "CALME"
    return out
