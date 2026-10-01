#!/usr/bin/env python3
"""Quand la zone de bruit corrigee (V1) marche-t-elle ? (README.md, partie 3). Descriptif, rien n'est decide.
Lancer depuis ce dossier : python3 conditions.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "zone_failles"))
sys.path.insert(0, str(R / "tournoi"))
sys.path.insert(0, str(R / "evolution2"))
sys.path.insert(0, str(R / "fonds"))
import journal as Z  # noqa: E402
from explorer import charger, t_stat  # noqa: E402
import tournoi3 as T3  # noqa: E402
import fomc  # noqa: E402

ICI = Path(__file__).resolve().parent
COUT, PT = 1.5, 2.0
PERIODES = {"2011-2022": (2011, 2022), "2023-2026": (2023, 2026)}


def mesure(t, ok_j, J, o0, a, b):
    """Trades t (sous-ensemble) sur la periode [a, b] : nombre, $ net par trade (1 MNQ), t des jours (jours sans ces
    trades = 0)."""
    jours = pd.DatetimeIndex(J)
    m = ok_j & (jours.year >= a) & (jours.year <= b)
    tt = t[(t["jour"].dt.year >= a) & (t["jour"].dt.year <= b)]
    r = pd.Series(0.0, index=jours[m])
    if len(tt):
        r = r.add(((tt["brut"] - COUT) / o0[tt["d"].values]).groupby(tt["jour"].values).sum(), fill_value=0.0).reindex(jours[m]).fillna(0)
    return len(tt), float(((tt["brut"] - COUT) * PT).mean()) if len(tt) else np.nan, t_stat(r.values)


def main():
    J, O, H, L, C, P, X = charger("nasdaq100", fin=None)
    sigma, veille, vwap, ok = Z.niveaux_propres(J, O, H, L, C, P, X)
    t = Z.journal(J, O, H, L, C, P, X, sigma=sigma, veille=veille, vwap=vwap, ok=ok)
    ok_j = ok & ~X["echeance"]
    t = t[ok_j[t["d"].values]].copy()
    o0 = O[:, 0]
    d = t["d"].values
    an = t["jour"].dt.year.values
    expl = an <= 2022
    Q = T3.lire_quotidien()
    tiers = lambda x: np.nanquantile(x[expl], [1 / 3, 2 / 3])
    vix = pd.read_csv(R / "evolution2" / "donnees" / "vix.csv")
    vix = pd.Series(vix["CLOSE"].astype(float).values, index=pd.to_datetime(vix["DATE"], format="mixed"))
    v_niv = T3.veille(J, vix)[d]
    v_str = T3.veille(J, Q["vix_ratio"])[d]
    g = T3.veille(J, Q["gex"])
    g_bas = (g < T3.quantile_252(g, 0.5))[d]
    g_def = np.isfinite(T3.quantile_252(g, 0.5))[d]
    gap = np.abs(o0 / veille - 1)[d]
    prec = np.r_[-1, np.maximum.accumulate(np.where(ok, np.arange(len(J)), -1))[:-1]]
    r_veille = np.where(prec >= 0, C[np.maximum(prec, 0), 389] / O[np.maximum(prec, 0), 0] - 1, np.nan)[d]
    fed = pd.DatetimeIndex(J).isin(fomc.annonces())[d]
    groupes = {
        "Heure du controle d'entree": {f"{(570 + m) // 60}h{(570 + m) % 60:02d}": t["m_entree"].values == m for m in range(30, 390, 30)},
        "Jour de la semaine": {j: t["jour"].dt.weekday.values == i for i, j in enumerate(("lundi", "mardi", "mercredi", "jeudi", "vendredi"))},
        "Volatilite du moment (mouvement moyen)": dict(zip(("calme", "moyenne", "agitee"),
                                                           (lambda q: (t["sigma"].values <= q[0], (t["sigma"].values > q[0]) & (t["sigma"].values <= q[1]), t["sigma"].values > q[1]))(tiers(t["sigma"].values)))),
        "Niveau du VIX (veille)": dict(zip(("bas", "moyen", "haut"), (lambda q: (v_niv <= q[0], (v_niv > q[0]) & (v_niv <= q[1]), v_niv > q[1]))(tiers(v_niv)))),
        "Structure du VIX (veille)": {"contango (< 1)": v_str < 1, "deport (>= 1)": v_str >= 1},
        "GEX de la veille": {"sous sa mediane": g_def & g_bas, "au-dessus": g_def & ~g_bas},
        "Ecart d'ouverture": dict(zip(("petit", "moyen", "grand"), (lambda q: (gap <= q[0], (gap > q[0]) & (gap <= q[1]), gap > q[1]))(tiers(gap)))),
        "Seance de la veille": {"en hausse": r_veille > 0, "en baisse": r_veille < 0},
        "Sens du trade par rapport a la veille": {"meme sens": np.sign(r_veille) == t["sens"].values, "sens contraire": np.sign(r_veille) == -t["sens"].values},
        "Sens du trade": {"achats": t["sens"].values > 0, "ventes": t["sens"].values < 0},
        "Rang du trade dans la journee": {"1er": t["rang"].values == 1, "2e": t["rang"].values == 2, "3e ou plus": t["rang"].values >= 3},
        "Jour d'annonce de la Fed": {"oui": fed, "non": ~fed},
    }
    sortie = []
    ecrire = lambda s="": (print(s, flush=True), sortie.append(s))
    ecrire("Zone corrigee V1, NQ, 1 MNQ, frais reels. Pour chaque condition : trades, $ net par trade, t des jours, sur 2011-2022 puis 2023-2026.")
    ecrire("STABLE + : gagnant dans les deux periodes (t >= 1 dans chacune) ; STABLE - : perdant dans les deux (t <= -1).")
    tout = {p: mesure(t, ok_j, J, o0, a, b) for p, (a, b) in PERIODES.items()}
    ecrire(f"\nToutes les entrees : " + " | ".join(f"{p} : {n} trades, {v:+.2f} $/trade, t {tt:+.2f}" for p, (n, v, tt) in tout.items()))
    for titre, cats in groupes.items():
        ecrire(f"\n{titre}")
        for c, msk in cats.items():
            res = {p: mesure(t[msk], ok_j, J, o0, a, b) for p, (a, b) in PERIODES.items()}
            ts = [res[p][2] for p in PERIODES]
            etiquette = "STABLE +" if min(ts) >= 1 else ("STABLE -" if max(ts) <= -1 else "")
            ecrire(f"  {c:18s} | " + " | ".join(f"{p} : {res[p][0]:4d} trades, {res[p][1]:+7.2f} $/trade, t {res[p][2]:+5.2f}" for p in PERIODES)
                   + (f" | {etiquette}" if etiquette else ""))
    (ICI / "conditions.txt").write_text("\n".join(sortie) + "\n")


if __name__ == "__main__":
    main()
