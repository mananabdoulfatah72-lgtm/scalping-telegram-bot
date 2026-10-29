#!/usr/bin/env python3
"""Challenge Bulenox 50K sans limite de temps (descriptif, question de l'utilisateur) : chances de valider selon la taille
de la zone (fixe), avec ou sans ajout, depuis la situation de l'utilisateur et depuis un compte neuf. Memes chemins que
challenge_ajouts.py ; horizon de 252 seances (un an) au lieu de 30 jours.
Lancer : KB=<branche de recherche> python3 scalping/sans_limite_bulenox.py"""
import numpy as np

import challenge_ajouts as CA
import commun as K
import partie_e as E
import partie_g as G
import partie_h as H
import situation_bulenox as SB
from numba import njit


@njit(cache=True)
def _duree(Zc, Zw, fed, departs, n, z, solde, haut0):
    """Nombre de seances jusqu'a la validation (-1 sinon), zone seule a taille fixe."""
    S, N = Zc.shape
    out = np.full(len(departs), -1, np.int64)
    for k in range(len(departs)):
        d0 = departs[k]
        bal, haut = solde, haut0
        plancher = 50100.0 if haut >= 52600.0 else haut - 2500.0
        for s in range(d0, min(d0 + n, S)):
            zz = 0.0 if fed[s] else z
            jour, fini = 0.0, 0
            for m in range(N):
                if bal + zz * Zw[s, m] <= plancher:
                    fini = -1
                    break
                if zz * Zw[s, m] <= -1000.0:
                    jour = -1000.0
                    break
                if bal + zz * Zc[s, m] >= 53050.0:
                    fini = 1
                    break
                jour = zz * Zc[s, m]
            if fini == 1:
                out[k] = s - d0 + 1
                break
            if fini == -1:
                break
            bal += jour
            haut = max(haut, bal)
            plancher = 50100.0 if haut >= 52600.0 else haut - 2500.0
            if bal <= plancher:
                break
    return out


def main():
    d = E.jour_nq()
    S = d["c"].shape[0]
    ok = d["complete"] & ~d["ech"]
    Zc, Zw = CA.chemins(d, CA.trades_zone(d, G.calcul(d)[4]))
    aj = {"ORB 5 min": CA.chemins(d, CA.trades_seances(d, ok, "H1")),
          "cassure de la veille": CA.chemins(d, CA.trades_seances(d, ok, "H5"))}
    fed = np.isin(d["jours"], E.fomc())
    n = 252
    dep = np.flatnonzero((d["jours"] >= np.datetime64("2012-01-01")) & (np.arange(S) <= S - n))
    zero = np.zeros_like(Zc)
    L = [f"Bulenox 50K sans limite de temps (horizon {n} seances), zone sans filtre a taille fixe, pas de zone les jours de "
         f"la Fed ; departs 2012 - {str(d['jours'][dep[-1]])[:4]} ({len(dep)})", ""]
    for nom, solde, haut in (("depuis ta situation (50 600 $, plancher 48 672 $)", 50600.0, 51172.0),
                             ("depuis un compte neuf (50 000 $, plancher 47 500 $)", 50000.0, 50000.0)):
        L += [nom, f"  {'reglage':<40} valide   perdu   pas fini   seances pour valider (mediane)"]
        for z in (1, 2, 3, 4, 6):
            for anom, a, (Ac, Aw) in [("", 0.0, (zero, zero))] + ([(f" + {k} 1 MNQ", 1.0, v) for k, v in aj.items()]
                                                                  if z == 2 else []):
                r = SB._depuis(Zc, Zw, Ac, Aw, fed, dep, n, float(z), float(z), a, solde, haut)
                du = ""
                if not a:
                    x = _duree(Zc, Zw, fed, dep, n, float(z), solde, haut)
                    x = x[x > 0]
                    du = f"{np.median(x):5.0f} (un quart apres plus de {np.percentile(x, 75):.0f})" if len(x) else ""
                L.append(f"  {('zone ' + str(z) + ' MNQ' + anom):<40} {(r == 1).mean():6.1%} {(r == -1).mean():7.1%} "
                         f"{(r == 0).mean():8.1%}   {du}")
        L.append("")
    out = K.ICI / "resultats" / "i" / "sans_limite_bulenox.txt"
    out.write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
