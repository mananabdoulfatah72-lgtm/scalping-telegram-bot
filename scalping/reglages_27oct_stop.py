#!/usr/bin/env python3
"""Demande de l'utilisateur du 27 octobre 2026 (descriptif) : configuration installee sans sortie aux controles
(reglages_27oct_sans_sortie.py) + un vrai stop a D points au-dela du niveau casse (achat : niveau - D ; vente : niveau + D),
touche a n'importe quel moment, rempli un tick au-dela ou a l'ouverture si elle est deja au-dela ; sinon 16 h ; limite du jour
1 000 $. D = 70 points (choix de l'utilisateur), 50 et 100 pour la sensibilite. Les D points sont ramenes au prix de chaque jour
(D x ouverture / 30 900) pour que le passe soit comparable ; le mode « points fixes » sert de reference au rejeu C# (STOP=70).
Ecrit resultats/j/reglages_27oct_stop.txt et _trades.csv.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/reglages_27oct_stop.py"""
import os

import numpy as np
import pandas as pd
from numba import njit

import challenge_ajouts as CA
import donnees as D
import partie_e as E
import partie_g as G
import partie_j as J
import reglages_27oct_sans_sortie as SS
import situation_bulenox as SB


@njit(cache=True)
def _avec_stop(O, H, L, C, tr, niveaux, dist, tick):
    """Memes entrees que tr (sortie a 16 h) ; stop a dist[s] points au-dela du niveau casse."""
    out = tr.copy()
    N = C.shape[1]
    for i in range(len(tr)):
        s, me, e = int(tr[i, 0]), int(tr[i, 1]), tr[i, 2]
        st = niveaux[i] - e * dist[s]
        for m in range(me + 1, N):
            if (e > 0 and L[s, m] <= st) or (e < 0 and H[s, m] >= st):
                out[i, 4] = m
                out[i, 5] = (min(O[s, m], st) - tick) if e > 0 else (max(O[s, m], st) + tick)
                out[i, 6] = 2
                break
    return out


def main():
    d = D.minutes("NQ", chemin=os.environ["MINUTES"], debut="2011-01-01")
    S = d["c"].shape[0]
    sigma, vwap, href, bref, jouable = G.zone_tableaux(d)
    fed = np.isin(d["jours"], E.fomc())
    an = d["jours"].astype("datetime64[Y]").astype(int) + 1970
    jo = jouable & ~fed
    jours = pd.to_datetime(d["jours"])
    tick = float(d["tick"])
    dep = np.flatnonzero(d["jours"] >= np.datetime64("2012-01-01"))
    dep13 = dep[dep <= S - 13]
    dep25 = dep13[d["jours"][dep13] >= np.datetime64("2025-01-01")]
    zero = np.zeros_like(d["c"])
    base = SS._zone_ss(d["c"], d["v"], sigma, href, bref, jouable, 1.0, 5)
    s_, me = base[:, 0].astype(int), base[:, 1].astype(int)
    ctl = (me // 30) * 30
    niv = np.where(base[:, 2] > 0, href[s_] * (1 + sigma[s_, ctl]), bref[s_] * (1 - sigma[s_, ctl]))
    ouv = d["o"][:, 0]
    jeux = {"sans stop (installee)": base}
    for D_ in (50.0, 70.0, 100.0):
        jeux[f"stop {D_:.0f} points" + (" (CHOIX)" if D_ == 70 else "")] = _avec_stop(d["o"], d["h"], d["l"], d["c"], base, niv,
                                                                                       D_ * ouv / float(d["pref"]), tick)
    fixe = _avec_stop(d["o"], d["h"], d["l"], d["c"], base, niv, np.full(S, 70.0), tick)
    L = [f"Minutes du NQ : {d['jours'][0]} - {d['jours'][-1]}. Entrees identiques dans tous les cas.", ""]
    for nom, t in jeux.items():
        pts = t[:, 2] * (t[:, 5] - t[:, 3]) - float(d["frais"]) / float(d["pt"])
        Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in t])
        g = Zc[:, -1]
        ts = [g[jo & (an >= a0) & (an <= a1)] for a0, a1 in ((2011, 2022), (2023, 2026))]
        ts = [x.mean() / x.std(ddof=1) * np.sqrt(len(x)) for x in ts]
        r = SB._depuis(Zc, Zw, zero, zero, fed, dep13, 13, 4.0, 6.0, 0.0, 49500.0, 51000.0, 1000.0)
        r25 = SB._depuis(Zc, Zw, zero, zero, fed, dep25, 13, 4.0, 6.0, 0.0, 49500.0, 51000.0, 1000.0)
        x = pd.Series(np.where(jo, np.where((4 * Zw <= -1000).any(axis=1), -1000.0, 4 * Zc[:, -1]), 0.0), index=jours)
        tr = x[(x != 0) & (x.index >= "2023-01-01")]
        a26 = x[x.index >= "2026-04-01"]
        L += [f"{nom} : stoppes {(t[:, 6] == 2).mean():.0%}, t {ts[0]:+.2f} / {ts[1]:+.2f}, journees a -1 000 $ (15 ans) "
              f"{int((Zw[jo].min(axis=1) <= -250).sum())}",
              f"  2023-2026 : jours gagnants {(tr > 0).mean():.0%}, gain moyen {tr[tr > 0].mean():+,.0f} $, perte moyenne {tr[tr < 0].mean():+,.0f} $, "
              f"pire jour {tr.min():+,.0f} $, jours a -1 000 $ {(tr <= -1000).mean():.0%}",
              "  par an (4 MNQ) : " + " ".join(f"{y}:{x[x.index.year == y].sum():+,.0f}" for y in range(2018, 2027))
              + f" | total 2011-2026 {x.sum():+,.0f} $, depuis 2023 {x[x.index >= '2023-01-01'].sum():+,.0f} $",
              f"  avril - 23 oct. 2026 : {a26.sum():+,.0f} $, jours a -1 000 $ {(a26 <= -1000).sum()} sur {(a26 != 0).sum()}",
              f"  challenge marge 1 000 $ : valide {(r == 1).mean():.1%} perdu {(r == -1).mean():.1%} expire {(r == 0).mean():.1%} ; "
              f"departs depuis 2025 : valide {(r25 == 1).mean():.1%} perdu {(r25 == -1).mean():.1%}",
              "  octobre 2026 : " + " ".join(f"{i.day}:{v:+,.0f}" for i, v in x[(x.index >= '2026-10-01') & (x != 0)].items())
              + f"   total {x[x.index >= '2026-10-01'].sum():+,.0f} $", ""]
    pd.DataFrame({"jour": d["jours"][fixe[:, 0].astype(int)].astype(str), "minute_entree": fixe[:, 1].astype(int),
                  "sens": fixe[:, 2].astype(int), "prix_entree": fixe[:, 3], "minute_sortie": fixe[:, 4].astype(int),
                  "prix_sortie": fixe[:, 5]}).to_csv(J.SORTIE / "reglages_27oct_stop70_fixe_trades.csv", index=False)
    (J.SORTIE / "reglages_27oct_stop.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
