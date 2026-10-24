#!/usr/bin/env python3
"""Minutes des 7 marches en tableaux seance x minute (README.md). Ecrit cache/recherche_<m>.npz (seances jusqu'au
31 decembre 2022, seules lues par l'exploration) et cache/complet_<m>.npz (toutes les seances, lues seulement par
coffre.py). Lancer : KB=<branche de recherche extraite> python3 scalping/donnees.py"""
import sys

import numpy as np
import pandas as pd

import commun as K


def minutes(nom):
    fichier, pt, tick, m0, m1, frais, pref, rond = K.MARCHES[nom]
    n = m1 - m0
    d = pd.read_csv(K.KB / fichier)
    t = pd.to_datetime(d["t"])
    garde = t >= pd.Timestamp(K.DEBUT_DONNEES)
    d, t = d[garde], t[garde]
    minute = (t.dt.hour * 60 + t.dt.minute - m0).values
    garde = (minute >= 0) & (minute < n)
    d, t, minute = d[garde], t[garde], minute[garde]
    jour = t.dt.normalize()
    jours = np.sort(jour.unique())
    ij = np.searchsorted(jours, jour.values)
    tab = {}
    for col in "ohlcv":
        a = np.full((len(jours), n), np.nan if col != "v" else 0.0)
        a[ij, minute] = d[col].values.astype(float)
        tab[col] = a
    present = ~np.isnan(tab["c"])
    C = pd.DataFrame(tab["c"]).ffill(axis=1).values
    for col in "ohl":
        tab[col] = np.where(np.isnan(tab[col]), C, tab[col])      # minute manquante : recopiee a plat, volume 0
    contrat = d.groupby(ij)["contrat"].last().reindex(range(len(jours))).values
    complete = present[:, 0] & present[:, n - 1] & (present.sum(axis=1) >= n - 20)
    ech = np.r_[False, contrat[1:] != contrat[:-1]]                # changement de contrat : pas de trade ce jour-la
    # seance complete precedente, du meme contrat (niveaux de la veille), et quel que soit le contrat (ecart d'ouverture)
    prec_meme = np.full(len(jours), -1, np.int64)
    prec_tout = np.full(len(jours), -1, np.int64)
    der, der_c = -1, {}
    for i in range(len(jours)):
        prec_tout[i] = der
        prec_meme[i] = der_c.get(contrat[i], -1)
        if complete[i]:
            der = i
            der_c[contrat[i]] = i
    return dict(jours=jours.astype("datetime64[D]"), o=tab["o"], h=tab["h"], l=tab["l"], c=C, v=tab["v"],
                complete=complete, ech=ech, contrat=contrat.astype(np.int64), prec_meme=prec_meme, prec_tout=prec_tout,
                pt=np.float64(pt), tick=np.float64(tick), m0=np.int64(m0), n=np.int64(n), frais=np.float64(frais),
                pref=np.float64(pref), rond=np.float64(rond))


def aligner_autre(d, a):
    """Clotures de l'autre indice a la meme seance et a la meme minute (NaN si sa seance n'est pas complete)."""
    x = np.full(d["c"].shape, np.nan)
    ia = pd.DatetimeIndex(a["jours"]).get_indexer(pd.DatetimeIndex(d["jours"]))
    for i, k in enumerate(ia):
        if k >= 0 and a["complete"][k] and not a["ech"][k]:
            x[i] = a["c"][k]
    return x


def couper(d, fin):
    r = d["jours"] <= fin
    return {k: (v[r] if isinstance(v, np.ndarray) and v.ndim >= 1 and len(v) == len(r) else v) for k, v in d.items()}


def main():
    K.CACHE.mkdir(exist_ok=True)
    tout = {nom: minutes(nom) for nom in K.MARCHES}
    for nom, autre in K.AUTRE_INDICE.items():
        tout[nom]["autre_c"] = aligner_autre(tout[nom], tout[autre])
    for nom, d in tout.items():
        r = couper(d, K.FIN_RECHERCHE)
        assert r["jours"].max() <= K.FIN_RECHERCHE
        assert (r["prec_meme"] < np.arange(len(r["jours"]))).all() and (r["prec_tout"] < np.arange(len(r["jours"]))).all()
        np.savez_compressed(K.CACHE / f"recherche_{nom}.npz", **r)
        np.savez_compressed(K.CACHE / f"complet_{nom}.npz", **d)
        jouable = d["complete"] & ~d["ech"]
        print(f"{nom} : {len(d['jours'])} seances du {d['jours'][0]} au {d['jours'][-1]} ({len(r['jours'])} pour la "
              f"recherche), completes {int(d['complete'].sum())}, jouables {int(jouable.sum())}, {d['n']} minutes",
              flush=True)


if __name__ == "__main__":
    sys.exit(main())
