#!/usr/bin/env python3
"""Suivi du bot FluxNQ en direct (flux/README.md, « La barre pour passer en reel ») : lit les carnets virtuels, les ordres
passifs et les ordres reels enregistres par le bot, et dit pour chaque regle si elle a franchi la barre fixee d'avance
(au moins 40 trades en direct, gain net moyen > 0, t >= 2,24).

Lancer : python3 flux/suivi_direct.py <dossier flux copie du PC (C:\\Bot3en1\\flux)>"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

N_MIN, SEUIL_T = 40, 2.24


def t_stat(x):
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 1 and x.std(ddof=1) > 0 else 0.0


def main(dossier):
    d = Path(dossier)
    lire = lambda nom: pd.concat([pd.read_csv(f) for f in sorted(d.glob(f"*/{nom}"))], ignore_index=True) \
        if list(d.glob(f"*/{nom}")) else pd.DataFrame()
    v, p, r = lire("virtuel.csv"), lire("passif.csv"), lire("reel.csv")
    seances = sorted(x.name for x in d.iterdir() if x.is_dir() and (x / "minutes.csv").exists())
    print(f"Seances enregistrees : {len(seances)} ({seances[0] if seances else '-'} - {seances[-1] if seances else '-'})")
    print(f"Barre pour le reel : au moins {N_MIN} trades virtuels en direct, gain net moyen > 0, t >= {SEUIL_T}\n")
    for regle in ("S1", "S2", "S2b", "C1"):
        x = v[v["regle"] == regle]["net"] if len(v) else pd.Series(dtype=float)
        n, moy, t = len(x), (x.mean() if len(x) else 0.0), t_stat(x)
        ok = n >= N_MIN and moy > 0 and t >= SEUIL_T
        etat = "FRANCHIE" if ok else (f"pas encore ({N_MIN - n} trades manquent)" if n < N_MIN else "non franchie")
        ligne = f"{regle:<4} {n:3d} trades, net moyen {moy:+6.2f} pt ({2 * moy:+.0f} $ par MNQ), t {t:+.2f} -> {etat}"
        if len(p) and len(v):
            pp = p[p["regle"] == regle]
            if len(pp):
                ligne += f" ; ordres passifs remplis {pp['rempli'].mean():.0%}"
        print(ligne)
    if len(r):
        print(f"\nOrdres reels : {len(r)} trade(s), {r['gain_estime_dollars'].sum():+.0f} $ estimes")


if __name__ == "__main__":
    main(sys.argv[1])
