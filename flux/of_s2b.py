#!/usr/bin/env python3
"""Partie 6 (flux/README.md) : S2b avec un filtre d'order flow (FA a FE), choix sur avril - juillet, jugement sur
3 aout - 27 octobre 2026.

Lancer : KB=<copie de claude/keen-babbage-r686cl> FLUX_EXPORTS=flux/donnees python3 flux/of_s2b.py"""
from pathlib import Path

import numpy as np
import pandas as pd

import donnees as D
import systeme as Y

ICI = Path(__file__).resolve().parent
TICK = 0.25
SANS_VEILLE = pd.Timestamp("2026-10-19")
FIN_A, FIN_B = pd.Timestamp("2026-07-31"), pd.Timestamp("2026-10-27")
FILTRES = ["aucun", "FA", "FB", "FC", "FD", "FE"]


def signaux(m, X, d, filtre):
    h, l, c = m["h"][d], m["l"][d], m["c"][d]
    if d == 0:
        return []
    niveaux = [(m["h"][d - 1].max(), 1, 30), (m["l"][d - 1].min(), -1, 30), (h[:60].max(), 1, 60), (l[:60].min(), -1, 60)]
    out = []
    for L, haut, debut in niveaux:
        for b in range(debut, Y.FIN + 1):
            casse = (h[b] >= L + TICK and c[b - 1] <= L) if haut == 1 else (l[b] <= L - TICK and c[b - 1] >= L)
            if not casse:
                continue
            for f in range(b, min(b + 5, Y.FIN) + 1):
                if (c[f] <= L - TICK) if haut == 1 else (c[f] >= L + TICK):
                    ext = h[b:f + 1].max() if haut == 1 else l[b:f + 1].min()
                    sens = -haut
                    ok = True
                    if filtre == "FA":
                        ok = X["imb"][d, b] >= X["q75"][d] if haut == 1 else X["imb"][d, b] <= X["q25"][d]
                    elif filtre == "FB":
                        ok = X["delta"][d, f] * sens > 0
                    elif filtre == "FC":
                        ok = X["delta"][d, b:f + 1].sum() * haut > 0
                    elif filtre == "FD":
                        ok = X["d30"][d, f] * sens > 0
                    elif filtre == "FE":
                        ok = X["v"][d, b] >= 1.5 * np.median(X["v"][d, b - 30:b])
                    if ok:
                        out.append((f, sens, ext + TICK if haut == 1 else ext - TICK))
                    break
            break
    return [s for s in sorted(out) if s[0] <= 150]


def main():
    m, info, _ = D.seances()
    X = Y.mesures(m, info)
    Y.DUREE = 60
    jours = info["jour"]
    jou = X["jouable"] & (jours != SANS_VEILLE).to_numpy() & (jours <= FIN_B).to_numpy()
    A = np.flatnonzero(jou & (jours <= FIN_A).to_numpy())
    B = np.flatnonzero(jou & (jours > FIN_A).to_numpy())
    res = {}
    for f in FILTRES:
        tr = Y.jouer(m, info, X, lambda m_, X_, d, sans, f=f: signaux(m_, X_, d, f))
        tr = tr[tr["seance"].isin(np.r_[A, B])]
        res[f] = tr
    ref = pd.read_csv(ICI / "resultats" / "trades_S2b.csv")
    ref = ref[pd.to_datetime(ref["jour"]) <= FIN_B]
    assert len(res["aucun"]) == len(ref) and np.allclose(res["aucun"]["net"].to_numpy(), ref["net"].to_numpy()), "S2b non retrouvee"
    L = ["Partie 6 : S2b avec un filtre d'order flow. Points de NQ nets de frais par trade ; 1 point = 2 $ par MNQ.", "",
         f"{'filtre':<7} | {'A : trades, net moyen, t, total':<34} | {'B : trades, net moyen, t, total':<34}"]
    tA = {}
    for f, tr in res.items():
        a, b = tr[tr["seance"].isin(A)], tr[tr["seance"].isin(B)]
        ta, tb = Y.t_stat(Y.quotidien(a, A)), Y.t_stat(Y.quotidien(b, B))
        tA[f] = ta
        L.append(f"{f:<7} | {len(a):3d}, {a['net'].mean():+6.2f}, {ta:+5.2f}, {a['net'].sum():+7.1f}      | "
                 f"{len(b):3d}, {b['net'].mean():+6.2f}, {tb:+5.2f}, {b['net'].sum():+7.1f}")
    choix = max(tA, key=tA.get)
    b0, bc = res["aucun"][res["aucun"]["seance"].isin(B)], res[choix][res[choix]["seance"].isin(B)]
    t0, tc = Y.t_stat(Y.quotidien(b0, B)), Y.t_stat(Y.quotidien(bc, B))
    ok = choix != "aucun" and bc["net"].sum() > b0["net"].sum() and tc > t0 and len(bc) >= 20
    L += ["", f"Choisi sur avril - juillet : {choix} (t {tA[choix]:+.2f} ; S2b seule {tA['aucun']:+.2f})",
          f"Sur aout - 27 octobre : {bc['net'].sum():+.1f} pts, t {tc:+.2f}, {len(bc)} trades ; S2b seule {b0['net'].sum():+.1f} pts, t {t0:+.2f}",
          f"Decision fixee a l'avance : {'FILTRE CONSEILLE' if ok else 'aucun filtre conseille, S2b reste telle quelle'}"]
    texte = "\n".join(L)
    (ICI / "resultats" / "of_s2b.txt").write_text(texte + "\n")
    print(texte)


if __name__ == "__main__":
    main()
