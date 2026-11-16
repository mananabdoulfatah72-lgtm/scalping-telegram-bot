"""Minutes du NQ (seance de New York) de 2011 a la derniere seance, rangees par seance : usine/REGLES.md, partie Donnees.

Sources :
- KB_MINUTES : intraday/donnees/nasdaq100_1min.csv.gz de la branche claude/keen-babbage-r686cl (2011 -> sept. 2026) ;
- zone/robot/nq_1min.csv.gz de main (depuis le 24 septembre 2025, mis a jour chaque soir par le robot zone).
Le fichier de main remplace l'autre a partir du 24 septembre 2025 (les deux sont identiques sur leurs minutes communes).
Faux prix : regle de bilan_challenge/st_detail.py (branche claude/peaceful-cerf-8dowsi).
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
N = 390                                   # minutes de 9 h 30 a 15 h 59
CACHE = Path(os.getenv("USINE_CACHE", ICI / ".cache"))


def lire_minutes(kb=None, recent=None):
    """Toutes les minutes (t, o, h, l, c, v, contrat), faux prix corriges. Renvoie aussi la liste des corrections."""
    kb = Path(kb or os.environ.get("KB_MINUTES", ""))
    recent = Path(recent or RACINE / "zone/robot/nq_1min.csv.gz")
    cols = ["t", "o", "h", "l", "c", "v", "contrat"]
    a = pd.read_csv(kb, usecols=cols)
    b = pd.read_csv(recent, usecols=cols)
    d = pd.concat([a[a.t < "2025-09-24"], b[b.t >= "2025-09-24"]], ignore_index=True)
    d = d.sort_values("t", kind="stable").drop_duplicates("t", keep="last").reset_index(drop=True)
    corrections = []
    pc = d.c.shift(1)
    meme_jour = d.t.str[:10] == d.t.shift(1).str[:10]
    for col in ("o", "h", "l"):
        ecart = np.minimum((d[col] - pc).abs(), (d[col] - d.c).abs())
        faux = (ecart > 300) & (ecart > 0.01 * d.c) & meme_jour
        for i in d.index[faux]:
            corrections.append(f"{d.t[i]} {col}={d.at[i, col]} (cloture d'avant {pc[i]}, cloture {d.c[i]})")
            d.at[i, col] = pc[i] if col == "o" else np.nan
    d["o"] = d.o.fillna(pc)
    d["h"] = d.h.fillna(d[["o", "c"]].max(axis=1)); d["l"] = d.l.fillna(d[["o", "c"]].min(axis=1))
    d["h"] = d[["h", "o", "c"]].max(axis=1); d["l"] = d[["l", "o", "c"]].min(axis=1)
    return d, corrections


def seances(d):
    """Tableaux par seance : J (dates), O, H, L, C, V (seances x 390), complete, segment de contrat."""
    jour = d.t.str[:10].to_numpy()
    m = (d.t.str[11:13].astype(int) * 60 + d.t.str[14:16].astype(int) - 570).to_numpy()
    g = (m >= 0) & (m < N)
    d, jour, m = d[g], jour[g], m[g]
    J = np.array(sorted(set(jour)))
    s = np.searchsorted(J, jour)
    S = len(J)
    A = {k: np.full((S, N), np.nan) for k in "ohlcv"}
    for k in "ohlcv":
        A[k][s, m] = d[k].to_numpy(float)
    pres = ~np.isnan(A["c"])
    complete = pres[:, 0] & pres[:, N - 1] & (pres.sum(1) >= 370)
    C = pd.DataFrame(A["c"]).ffill(axis=1).bfill(axis=1).to_numpy()
    O, H, L = [np.where(np.isnan(A[k]), C, A[k]) for k in "ohl"]
    V = np.nan_to_num(A["v"])
    # contrat de la seance : celui de sa premiere minute ; segment = numero du contrat, +1 a chaque changement
    premier = pd.Series(d.contrat.to_numpy(), index=s).groupby(level=0).first().reindex(range(S)).ffill().bfill().to_numpy()
    seg = np.cumsum(np.r_[0, (premier[1:] != premier[:-1]).astype(int)]).astype(np.int64)
    return dict(J=J, O=O, H=H, L=L, C=C, V=V, complete=complete, seg=seg)


def charger(kb=None, recent=None, rafraichir=False):
    """Donnees de l'usine, gardees en cache (.npz) tant que les fichiers sources ne changent pas."""
    kb = Path(kb or os.environ.get("KB_MINUTES", ""))
    recent = Path(recent or RACINE / "zone/robot/nq_1min.csv.gz")
    cle = f"{kb.stat().st_size}_{int(kb.stat().st_mtime)}_{recent.stat().st_size}_{int(recent.stat().st_mtime)}"
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"seances_{cle}.npz"
    if f.exists() and not rafraichir:
        z = np.load(f, allow_pickle=False)
        D = {k: z[k] for k in z.files if k != "corrections"}
        D["corrections"] = list(z["corrections"])
        return D
    d, corr = lire_minutes(kb, recent)
    D = seances(d)
    np.savez(f, **D, corrections=np.array(corr, dtype=str))
    D["corrections"] = corr
    return D


if __name__ == "__main__":
    D = charger()
    print(f"{len(D['J'])} seances, {D['complete'].sum()} completes, du {D['J'][0]} au {D['J'][-1]}")
    for c in D["corrections"]:
        print("faux prix corrige :", c)
