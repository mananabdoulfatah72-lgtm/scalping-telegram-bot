#!/usr/bin/env python3
"""Etapes 1 et 2 du tournoi n°2 (README.md) : exploration 2011-2022 et controle sur 20 versions melangees.
Les annees 2023-2026 ne sont pas utilisees ici (coupees au chargement).

Lancer depuis ce dossier : python3 explorer2.py
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import concurrents2 as K
from explorer import charger, explorer_marche, ligne, publier, t_stat      # tournoi/explorer.py (meme chaine que le tournoi n°1)

ICI = Path(__file__).resolve().parent
MARCHES = {"NQ": ("nasdaq100", 2.0), "ES": ("sp500", 5.0)}      # fichier, $ par point pour 1 micro
N_BRUIT = 20
PAIRE = "Paire NQ / ES en retour a la moyenne"


def mesurer_paire(r, ok, J):
    x = r[ok]
    j = pd.DatetimeIndex(J[ok])
    trades = x != 0
    moit = j.year <= 2016
    return {"t": t_stat(x), "jours": int(ok.sum()), "jours_trade": int(trades.sum()),
            "dollars_par_jour_trade": float(x[trades].mean() * 50_000) if trades.any() else 0.0,      # pour 50 000 $ engages
            "dollars_total": float(x.sum() * 50_000), "t_2011_2016": t_stat(x[moit]), "t_2017_2022": t_stat(x[~moit]),
            "jours_gagnants": float((x[trades] > 0).mean()) if trades.any() else 0.0}


def main():
    t0 = time.time()
    lignes, zones, donnees = [], {}, {}
    for marche, (fichier, pt) in MARCHES.items():
        donnees[marche] = charger(fichier)
        assert donnees[marche][0].max() <= pd.Timestamp("2022-12-31")
        l, zones[marche] = explorer_marche(K.toutes, marche, donnees[marche], fichier, pt, t0)
        lignes += l
    # 11. la paire : un seul essai pour les deux marches ; le meme melange pour NQ et ES
    a, b = K.aligner(donnees["NQ"], donnees["ES"])
    ca, cb = K.st.cout_aller_retour("nasdaq100"), K.st.cout_aller_retour("sp500")
    r, okp = K.paire(a, b, ca, cb)
    rng = np.random.default_rng(2027)
    bp = []
    for k in range(N_BRUIT):
        perm = K.ordre_hasard(len(a[0]), rng)
        a2 = (a[0],) + K.melanger_perm(*a[1:5], a[6]["V"], perm)[:4] + (a[5], a[6])
        b2 = (b[0],) + K.melanger_perm(*b[1:5], b[6]["V"], perm)[:4] + (b[5], b[6])
        r2, ok2 = K.paire(a2, b2, ca, cb)
        bp.append(t_stat(r2[ok2]))
        print(f"  paire bruit {k + 1}/{N_BRUIT} ({time.time() - t0:.0f} s)", flush=True)
    rp = pd.Series(r[okp], index=pd.DatetimeIndex(a[0][okp]))
    zq = zones["NQ"].reindex(rp.index).fillna(0)
    lignes.append(ligne(PAIRE, "NQ+ES", mesurer_paire(r, okp, a[0]), bp, float(np.corrcoef(rp.values, zq.values)[0, 1])))
    df = pd.DataFrame(lignes)
    assert len(df) == 29
    publier(df, ICI)


if __name__ == "__main__":
    main()
