#!/usr/bin/env python3
"""Verifications de la zone de bruit (seul resultat positif) : achats contre ventes, en % du prix,
sans les meilleurs jours, et challenges Apex/Topstep sur 2020-2026 seulement.

Lancer depuis ce dossier : python3 verif_zone.py
"""
import numpy as np
import pandas as pd

import strategies as st
from challenge import REGLES, simuler


def zone_detail(J, O, H, L, C, P, X, jours_moyenne=14, pas=30):
    """Meme strategie que strategies.zone_de_bruit, mais chaque trade separement (sens, gain en points, prix)."""
    ok = st.journees_completes(P)
    ouverture = O[:, 0]
    veille = st.cloture_veille(C, X)
    sigma = pd.DataFrame(np.abs(C / ouverture[:, None] - 1)).rolling(jours_moyenne).mean().shift(1).values
    typique, V = (H + L + C) / 3, X["V"]
    cumv = np.cumsum(V, axis=1)
    vwap = np.cumsum(typique * V, axis=1) / np.where(cumv > 0, cumv, 1)
    haut_ref, bas_ref = np.fmax(ouverture, veille), np.fmin(ouverture, veille)
    trades = []
    for d in np.where(ok & ~np.isnan(veille) & ~np.isnan(sigma[:, pas]))[0]:
        pos, entree = 0, 0.0
        for m in range(pas, st.N, pas):
            p = C[d, m]
            ub, lb = haut_ref[d] * (1 + sigma[d, m]), bas_ref[d] * (1 - sigma[d, m])
            if pos > 0 and p <= max(ub, vwap[d, m]) or pos < 0 and p >= min(lb, vwap[d, m]):
                trades.append((J[d], pos, pos * (p - entree), entree)); pos = 0
            if pos == 0 and p > ub:
                pos, entree = 1, p
            elif pos == 0 and p < lb:
                pos, entree = -1, p
        if pos:
            trades.append((J[d], pos, pos * (C[d, st.N - 1] - entree), entree))
    return pd.DataFrame(trades, columns=["jour", "sens", "brut", "prix"])


def main():
    for nom in ["nasdaq100", "sp500"]:
        J, O, H, L, C, P, X = st.charger(nom)
        cout = st.cout_aller_retour(nom)
        t = zone_detail(J, O, H, L, C, P, X)
        t["net"] = t["brut"] - cout
        t["brut_pb"] = t["brut"] / t["prix"] * 1e4
        t["cout_pb"] = cout / t["prix"] * 1e4
        t["net_pb"] = t["net"] / t["prix"] * 1e4
        print(f"\n=== {nom.upper()} : {len(t)} trades")
        for lab, a, z in [("2011-2014", "2011", "2015"), ("2015-2019", "2015", "2020"), ("2020-2026", "2020", "2027"),
                          ("depuis mai 2024", "2024-05-01", "2027")]:
            x = t[(t.jour >= a) & (t.jour < z)]
            print(f"  {lab:16s} brut {x.brut_pb.mean():+5.1f} pb | frais {x.cout_pb.mean():4.1f} pb | net {x.net_pb.mean():+5.1f} pb"
                  f" (t {x.net_pb.mean() / x.net_pb.std() * np.sqrt(len(x)):+.2f}) | achats {x[x.sens > 0].net_pb.mean():+5.1f} pb"
                  f" ({(x.sens > 0).sum()}) | ventes {x[x.sens < 0].net_pb.mean():+5.1f} pb ({(x.sens < 0).sum()})")
        par_jour = t.groupby("jour")["net"].sum()
        top = par_jour.nlargest(int(len(par_jour) * 0.01)).index
        print(f"  sans le 1 % des meilleurs jours : {par_jour.drop(top).mean():+.2f} pt par jour de trade "
              f"(au lieu de {par_jour.mean():+.2f})")
    # challenges sur 2020-2026 seulement (periode favorable, a prendre comme un plafond)
    from analyse import calculer
    for nom in ["nasdaq100"]:
        jours, res, _ = calculer(nom)
        df = res["Zone de bruit"]
        jours = jours[jours >= "2020-01-01"]
        df = df[df.index >= "2020-01-01"]
        net = df["net"].reindex(jours).fillna(0).values
        pire = np.minimum(df["pire"].reindex(jours).fillna(0).values, np.minimum(net, 0))
        print(f"\n  Challenges 2020-2026 seulement, zone de bruit {st.CONTRATS[nom]['micro']} :")
        for regle in REGLES:
            for n in [2, 3, 5, 10]:
                k = n * st.CONTRATS[nom]["pt"]
                ok, dur = simuler(net * k, pire * k, regle)
                sans = net - df["net"].mean() * (net != 0)
                ok0, _ = simuler(sans * k, pire * k, regle)
                print(f"    {regle:12s} {n:2d} MNQ : reussi {np.mean(ok == 1):4.0%} | perdu {np.mean(ok == -1):4.0%} | pas fini {np.mean(ok == 0):4.0%}"
                      f" | duree mediane {np.nanmedian(dur) if (ok == 1).any() else float('nan'):3.0f} seances || sans avantage : reussi {np.mean(ok0 == 1):4.0%}")


if __name__ == "__main__":
    main()
