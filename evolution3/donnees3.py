#!/usr/bin/env python3
"""Barres de 5 minutes des 5 marches (README.md) depuis les minutes de zone_multi/. Ecrit cache/recherche_<m>.npz
(seances jusqu'au 31 decembre 2022, seules lues par l'evolution) et cache/complet_<m>.npz (toutes les seances, lues
seulement par coffre3.py). Lancer depuis ce dossier : python3 donnees3.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
R = ICI.parent
sys.path.insert(0, str(R / "tournoi"))
import concurrents as K1  # noqa: E402

FRAIS_ORDRE = 1.0
# marche : (fichier, $ par point du micro, tick, debut et fin de seance en minutes, New York)
MARCHES = {
    "RTY": (R / "zone_multi/donnees/russell_1min.csv.gz", 5.0, 0.10, 570, 960),
    "YM": (R / "zone_multi/donnees/dow_1min.csv.gz", 0.5, 1.0, 570, 960),
    "GC": (R / "zone_multi/donnees/or_1min.csv.gz", 10.0, 0.10, 500, 810),
    "CL": (R / "zone_multi/donnees/petrole_1min.csv.gz", 100.0, 0.01, 540, 870),
    "6E": (R / "zone_multi/donnees/euro_1min.csv.gz", 12500.0, 0.0001, 500, 900),
}
FIN_RECHERCHE = np.datetime64("2022-12-31")


def minutes(fichier, m0, m1):
    n = m1 - m0
    d = pd.read_csv(fichier)
    t = pd.to_datetime(d["t"])
    minute = (t.dt.hour * 60 + t.dt.minute - m0).values
    garde = (minute >= 0) & (minute < n)
    d, t, minute = d[garde], t[garde], minute[garde]
    jour = t.dt.normalize()
    jours = np.sort(jour.unique())
    ij = np.searchsorted(jours, jour.values)
    tab = {}
    for col in "ohlcv":
        a = np.full((len(jours), n), np.nan if col != "v" else 0.0)
        a[ij, minute] = d[col].values
        tab[col] = a
    P = ~np.isnan(tab["c"])
    C = pd.DataFrame(tab["c"]).ffill(axis=1).values
    for col in "ohl":
        tab[col] = np.where(np.isnan(tab[col]), C, tab[col])
    contrat = d.groupby(ij)["contrat"].last().reindex(range(len(jours))).values
    ech = np.r_[False, contrat[1:] != contrat[:-1]]
    return pd.DatetimeIndex(jours), tab["o"], tab["h"], tab["l"], C, tab["v"], P, ech, contrat


def construire(nom):
    fichier, pt, tick, m0, m1 = MARCHES[nom]
    J, O, H, L, C, V, P, ech, contrat = minutes(fichier, m0, m1)
    n = m1 - m0
    nb = n // 5
    complete = P[:, 0] & P[:, n - 1] & (P.sum(axis=1) >= n - 20)
    # VWAP de la seance a chaque minute, puis a la cloture de chaque barre de 5 minutes
    typ = (H + L + C) / 3
    cv = np.cumsum(V, axis=1)
    vw = np.where(cv > 0, np.cumsum(typ * V, axis=1) / np.where(cv > 0, cv, 1), np.cumsum(typ, axis=1) / np.arange(1, n + 1))
    f = lambda x: x.reshape(len(J), nb, 5)
    o5, h5, l5, c5, vw5 = f(O)[:, :, 0], f(H).max(axis=2), f(L).min(axis=2), f(C)[:, :, 4], f(vw)[:, :, 4]
    # seance precedente (derniere seance complete du meme contrat) : cloture, plus haut, plus bas
    prec = K1.precedente(complete, contrat)
    pc, ph, pl = K1.de_la(C[:, n - 1], prec), K1.de_la(H.max(axis=1), prec), K1.de_la(L.min(axis=1), prec)
    gap = np.abs(O[:, 0] / pc - 1)
    gap_moy = K1.glissant_complet(gap, complete, 20)
    amp = (H.max(axis=1) - L.min(axis=1)) / O[:, 0]
    amp_v = K1.de_la(amp, prec)
    med = K1.glissant_complet(amp, complete, 20, "median")      # 20 seances completes avant ce jour
    med_v = K1.de_la(med, prec)                                   # ... avant la veille
    regime = np.where(amp_v > med_v, 1, np.where(amp_v <= med_v, 2, 0)).astype(np.int8)
    interdit = ~complete | ech | np.isnan(pc)
    cout = 2 * (FRAIS_ORDRE + tick * pt) / pt
    out = {"jours": J.values.astype("datetime64[D]"), "o": o5, "h": h5, "l": l5, "c": c5, "vwap": vw5, "v": f(V).sum(axis=2),
           "pc": pc, "ph": ph, "pl": pl, "prec": prec.astype(np.int64), "gap_moy": gap_moy, "regime": regime, "interdit": interdit,
           "cout": np.float64(cout), "pt": np.float64(pt), "tick": np.float64(tick), "nb": np.int64(nb)}
    return out


def main():
    for nom in MARCHES:
        d = construire(nom)
        r = d["jours"] <= FIN_RECHERCHE
        assert (d["prec"] < np.arange(len(r))).all()          # la veille est toujours avant : couper ne la change pas
        np.savez_compressed(ICI / "cache" / f"recherche_{nom}.npz",
                            **{k: (v[r] if isinstance(v, np.ndarray) and v.ndim >= 1 and len(v) == len(r) else v) for k, v in d.items()})
        np.savez_compressed(ICI / "cache" / f"complet_{nom}.npz", **d)
        print(f"{nom} : {len(d['jours'])} seances ({int(r.sum())} pour la recherche, jusqu'au {d['jours'][r].max()}),"
              f" {d['nb']} barres, jouables {int((~d['interdit']).sum())}, frais {d['cout']:.5g} points", flush=True)


if __name__ == "__main__":
    main()
