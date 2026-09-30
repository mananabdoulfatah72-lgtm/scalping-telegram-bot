"""Zone de bruit (intraday/strategies.py zone_de_bruit) rejouee trade par trade, pour l'autopsie. Memes regles :
limites = max(ouverture, cloture de la veille) x (1 + sigma) et min(...) x (1 - sigma), sigma = mouvement moyen
|C / ouverture - 1| des 14 seances precedentes a la meme minute ; controles toutes les 30 min de 10 h a 15 h 30 ;
entree si le prix sort de la zone ; stop suiveur = limite ou VWAP ; tout ferme a 16 h."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "intraday"))
import strategies as st  # noqa: E402

N = 390


def niveaux(J, O, H, L, C, P, X, jours_moyenne=14):
    """sigma, veille, VWAP, ok : exactement comme st.zone_de_bruit."""
    ok = st.journees_completes(P)
    ouverture = O[:, 0]
    veille = st.cloture_veille(C, X)
    sigma = pd.DataFrame(np.abs(C / ouverture[:, None] - 1)).rolling(jours_moyenne, min_periods=jours_moyenne).mean().shift(1).values
    typique = (H + L + C) / 3
    V = X["V"]
    cumv = np.cumsum(V, axis=1)
    vwap = np.where(cumv > 0, np.cumsum(typique * V, axis=1) / np.where(cumv > 0, cumv, 1), np.cumsum(typique, axis=1) / np.arange(1, N + 1))
    return sigma, veille, vwap, ok


def journal(J, O, H, L, C, P, X, sigma=None, veille=None, vwap=None, ok=None, pas=30):
    """Un trade par ligne : jour, rang du trade dans la journee, sens, minute et prix d'entree et de sortie, raison
    (stop ou cloture), gain brut en points, et au moment de l'entree : sigma, distance a la limite."""
    s0, v0, w0, k0 = niveaux(J, O, H, L, C, P, X)
    sigma = s0 if sigma is None else sigma
    veille = v0 if veille is None else veille
    vwap = w0 if vwap is None else vwap
    ok = k0 if ok is None else ok
    ouverture = O[:, 0]
    haut_ref, bas_ref = np.fmax(ouverture, veille), np.fmin(ouverture, veille)
    lignes = []
    for d in np.where(ok & ~np.isnan(veille) & ~np.isnan(sigma[:, pas]))[0]:
        pos, entree, m_e, rang = 0, 0.0, 0, 0
        for m in range(pas, N, pas):
            p = C[d, m]
            ub, lb = haut_ref[d] * (1 + sigma[d, m]), bas_ref[d] * (1 - sigma[d, m])
            if pos > 0 and p <= max(ub, vwap[d, m]):
                lignes.append((d, rang, 1, m_e, entree, m, p, "stop", p - entree))
                pos = 0
            elif pos < 0 and p >= min(lb, vwap[d, m]):
                lignes.append((d, rang, -1, m_e, entree, m, p, "stop", entree - p))
                pos = 0
            if pos == 0 and p > ub:
                pos, entree, m_e, rang = 1, p, m, rang + 1
            elif pos == 0 and p < lb:
                pos, entree, m_e, rang = -1, p, m, rang + 1
        if pos:
            lignes.append((d, rang, pos, m_e, entree, N - 1, C[d, N - 1], "cloture", pos * (C[d, N - 1] - entree)))
    t = pd.DataFrame(lignes, columns=["d", "rang", "sens", "m_entree", "px_entree", "m_sortie", "px_sortie", "raison", "brut"])
    t["jour"] = pd.DatetimeIndex(J)[t["d"].values]
    t["sigma"] = sigma[t["d"].values, t["m_entree"].values]
    return t


def niveaux_propres(J, O, H, L, C, P, X, jours_moyenne=14):
    """V1 : sigma sur les 14 dernieres seances COMPLETES (a chaque minute), veille = cloture de la derniere seance
    complete du meme contrat. Les seances incompletes (feries CME, fermetures anticipees) ne servent plus."""
    sigma0, _, vwap, ok = niveaux(J, O, H, L, C, P, X, jours_moyenne)
    comp = ok
    mv = np.abs(C / O[:, :1] - 1)
    sigma = np.full_like(mv, np.nan)
    sigma[comp] = pd.DataFrame(mv[comp]).rolling(jours_moyenne, min_periods=jours_moyenne).mean().shift(1).values
    contrat = X.get("contrat")
    idx = np.where(comp, np.arange(len(J)), -1)
    prec = np.r_[-1, np.maximum.accumulate(idx)[:-1]]
    if contrat is not None:
        prec = np.where((prec >= 0) & (contrat[np.maximum(prec, 0)] == contrat), prec, -1)
    veille = np.where(prec >= 0, C[np.maximum(prec, 0), N - 1], np.nan)
    return sigma, veille, vwap, ok


def zone(J, O, H, L, C, P, X, propre=True, max_trades=99, jours=None, achats_seuls=False, stop="limite_vwap", pas=30):
    """Gain brut en points et nombre d'allers-retours par seance, selon la variante (README.md, partie 2).
    jours : masque des seances ou l'on peut entrer (filtre GEX) ; stop : "limite_vwap" (regle d'origine) ou "vwap"."""
    sigma, veille, vwap, ok = niveaux_propres(J, O, H, L, C, P, X) if propre else niveaux(J, O, H, L, C, P, X)
    ouverture = O[:, 0]
    haut_ref, bas_ref = np.fmax(ouverture, veille), np.fmin(ouverture, veille)
    nd = len(J)
    brut, allers = np.zeros(nd), np.zeros(nd)
    permis = np.ones(nd, bool) if jours is None else jours
    for d in np.where(ok & permis & ~np.isnan(veille) & ~np.isnan(sigma[:, pas]))[0]:
        pos, entree, n, tot = 0, 0.0, 0, 0.0
        for m in range(pas, N, pas):
            p = C[d, m]
            ub, lb = haut_ref[d] * (1 + sigma[d, m]), bas_ref[d] * (1 - sigma[d, m])
            lim_l = max(ub, vwap[d, m]) if stop == "limite_vwap" else vwap[d, m]
            lim_c = min(lb, vwap[d, m]) if stop == "limite_vwap" else vwap[d, m]
            if pos > 0 and p <= lim_l:
                tot += p - entree
                pos = 0
            elif pos < 0 and p >= lim_c:
                tot += entree - p
                pos = 0
            if pos == 0 and n < max_trades:
                if p > ub:
                    pos, entree, n = 1, p, n + 1
                elif p < lb and not achats_seuls:
                    pos, entree, n = -1, p, n + 1
        if pos:
            tot += pos * (C[d, N - 1] - entree)
        brut[d], allers[d] = tot, n
    return brut, allers
