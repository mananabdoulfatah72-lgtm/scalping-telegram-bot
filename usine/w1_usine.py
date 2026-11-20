#!/usr/bin/env python3
"""W1 dans l'usine (usine/REGLES.md, fixe le 20 novembre 2026) : le tri du Supertrend par W1 bat-il un tri au hasard ?

Donnees et code de l'arene : ML_DIR = dossier ml/ de la branche claude/optimistic-ptolemy-xs24ra (git archive),
MINUTES_NQ = minutes du NQ 2011 -> 2026 (t, o, h, l, c, v, contrat), CACHE_DOSSIER = un fichier .npy quelconque (les
probabilites du bot XGBoost NQ ne servent pas a W1).
Usage : ML_DIR=... MINUTES_NQ=... CACHE_DOSSIER=... python3 usine/w1_usine.py
"""
import json
import os
import sys
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
ML = Path(os.environ["ML_DIR"])
sys.path.insert(0, str(ML / "arene")); sys.path.insert(0, str(ML))
import bots as BT  # noqa: E402
import donnees as Dn  # noqa: E402
import w1 as W  # noqa: E402

N_TIRAGES, GRAINE = 10_000, 20261120


def t_stat(x):
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else 0.0


def principal():
    B = BT.Base(os.environ["CACHE_DOSSIER"])
    ST = sorted(BT.supertrend(B), key=lambda t: (t[0], t[2]))
    X, y, an = W.variables_prod(B, ST)
    p = W.probas(X, y, an)
    W1p, garde = W.tri(ST, p, y, an)
    # controle : la mesure de l'arene (seances, limite du jour 400 $), comme w1_prod.py
    r, dp, ntr = BT.journees(B, W1p, 1, 400.0)
    aj = B.an[B.test]; FEN = aj >= 2017
    controle_t = t_stat(r[B.test][FEN])
    # gain net de chaque trade pour 1 MNQ (formule de l'arene)
    pnl = np.array([s * (x - e) * 2.0 * Dn.PREF / e - Dn.FRAIS for (_, s, _, _, _, e, x) in ST])
    oos = (an >= 2017) & np.isfinite(p)
    reel = float(pnl[oos & garde].sum())
    rng = np.random.default_rng(GRAINE)
    annees = sorted(set(an[oos]))
    idx = {Y: np.where(oos & (an == Y))[0] for Y in annees}
    nb = {Y: int((garde & (an == Y)).sum()) for Y in annees}

    def tirages(depuis):
        ys = [Y for Y in annees if Y >= depuis]
        out = np.empty(N_TIRAGES)
        for k in range(N_TIRAGES):
            out[k] = sum(pnl[rng.choice(idx[Y], nb[Y], replace=False)].sum() for Y in ys)
        return out
    t17 = tirages(2017); reel23 = float(pnl[oos & garde & (an >= 2023)].sum()); t23 = tirages(2023)
    nb_ans = (an[oos].max() - 2017) + 10 / 12                     # 2017 -> 2 novembre 2026
    R = dict(controle_t_seances_2017=round(controle_t, 2), part_gardee=round(float(garde[oos].mean()), 3),
             trades_2017=int(oos.sum()), gardes_2017=int((oos & garde).sum()),
             w1_net_2017=round(reel), w1_par_an=round(reel / nb_ans), supertrend_net_2017=round(float(pnl[oos].sum())),
             hasard_median_2017=round(float(np.median(t17))), p_WA=float(np.mean(t17 >= reel)),
             w1_net_2023=round(reel23), hasard_median_2023=round(float(np.median(t23))), p_2023=float(np.mean(t23 >= reel23)),
             supertrend_net_2023=round(float(pnl[oos & (an >= 2023)].sum())))
    R["WA"] = bool(R["p_WA"] < 0.01)
    R["WB"] = bool(R["w1_par_an"] >= 1000 and reel23 > 0)
    R["retenu"] = bool(R["WA"] and R["WB"])
    d = ICI / "resultats" / "2026-11-20"; d.mkdir(parents=True, exist_ok=True)
    (d / "w1.json").write_text(json.dumps(R, indent=1, ensure_ascii=False))
    print(json.dumps(R, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    principal()
