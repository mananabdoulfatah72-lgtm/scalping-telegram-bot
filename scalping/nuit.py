#!/usr/bin/env python3
"""Partie D (README.md, regles v2) : seances de nuit (18 h - 9 h 25, New York) en barres de 5 minutes, depuis les
fichiers HistData de la recherche (UTC). Ecrit cache/recherche_nuit_<m>.npz (seances jusqu'au 31 decembre 2022) et
cache/complet_nuit_<m>.npz. Lancer : KB=<branche de recherche extraite> python3 scalping/nuit.py"""
import numpy as np
import pandas as pd

import commun as K

# marche : (fichier HistData, $ par point du micro, tick, frais par aller-retour, pas des niveaux ronds, grille des
# prix des donnees : cotations du comptant et des CFD, plus fines que le tick des futures)
MARCHES_NUIT = {
    "NQ": ("usatechidxusd", 2.0, 0.25, 3.00, 100.0, 0.001),
    "ES": ("usa500idxusd", 5.0, 0.25, 4.50, 25.0, 0.001),
    "GC": ("xauusd", 10.0, 0.10, 4.00, 10.0, 0.001),
    "6E": ("eurusd", 12500.0, 0.0001, 4.50, 0.005, 0.00001),
    "6B": ("gbpusd", 6250.0, 0.0001, 3.25, 0.005, 0.00001),
    "6A": ("audusd", 10000.0, 0.0001, 4.00, 0.005, 0.00001),
}
N_NUIT = 184                       # 18 h 00 -> 9 h 20 (derniere barre, finit a 9 h 25)
DEBUT_NUIT = np.datetime64("2012-01-01")
DEBUT_ENTRAINEMENT_NUIT = np.datetime64("2013-01-01")
DEBUT_VALIDATION_NUIT = np.datetime64("2019-01-01")
# minutes d'evenement de F9, en barres depuis 18 h : decalages fixes de F9 (1, 5, 15, 30, 31) et 19 h, 20 h, 21 h,
# 2 h, 3 h, 4 h, 7 h, 8 h, 8 h 30, 9 h
EVENEMENTS_NUIT = np.array([1, 5, 12, 15, 24, 30, 31, 36, 96, 108, 120, 156, 168, 174, 180], np.int64)


def seances(nom):
    fichier, pt, tick, frais, rond, pas = MARCHES_NUIT[nom]
    morceaux = sorted((K.KB / "sessions24" / "annees").glob(f"{fichier}_*_5m.csv.gz"))
    d = pd.concat([pd.read_csv(f) for f in morceaux], ignore_index=True)
    t = pd.to_datetime(d["t"]).dt.tz_localize("UTC").dt.tz_convert("America/New_York").dt.tz_localize(None)
    d = d.assign(t=t).drop_duplicates("t").sort_values("t")
    t = d["t"]
    minute = t.dt.hour * 60 + t.dt.minute
    apres = minute >= 18 * 60                                   # 18 h - minuit : seance du lendemain
    avant = minute <= 9 * 60 + 20                               # minuit - 9 h 20
    garde = apres | avant
    d, t, minute, apres = d[garde], t[garde], minute[garde], apres[garde]
    jour = (t.dt.normalize() + pd.to_timedelta(apres.astype(int), unit="D"))
    pos = np.where(apres, (minute - 18 * 60) // 5, (minute + 6 * 60) // 5).astype(int)
    garde = (pos >= 0) & (pos < N_NUIT) & (jour >= pd.Timestamp(DEBUT_NUIT))
    d, jour, pos = d[garde], jour[garde], pos[garde]
    # le lundi s'ouvre le dimanche soir ; une seance datee d'un samedi ou d'un dimanche n'existe pas
    garde = jour.dt.day_of_week < 5
    d, jour, pos = d[garde], jour[garde], pos[garde]
    jours = np.sort(jour.unique())
    ij = np.searchsorted(jours, jour.values)
    tab = {}
    for col in "ohlc":
        a = np.full((len(jours), N_NUIT), np.nan)
        a[ij, pos] = d[col].values.astype(float)
        tab[col] = a
    present = ~np.isnan(tab["c"])
    C = pd.DataFrame(tab["c"]).ffill(axis=1).values
    for col in "ohl":
        tab[col] = np.where(np.isnan(tab[col]), C, tab[col])
    complete = present[:, 0] & present[:, N_NUIT - 1] & (present.sum(axis=1) >= N_NUIT - 18)
    prec = np.full(len(jours), -1, np.int64)
    der = -1
    for i in range(len(jours)):
        prec[i] = der
        if complete[i]:
            der = i
    pref = float(d["c"].values[-1])
    return dict(jours=jours.astype("datetime64[D]"), o=tab["o"], h=tab["h"], l=tab["l"], c=C,
                v=np.ones_like(C), complete=complete, ech=np.zeros(len(jours), bool),
                contrat=np.zeros(len(jours), np.int64), prec_meme=prec, prec_tout=prec.copy(), pt=np.float64(pt),
                tick=np.float64(tick), m0=np.int64(18 * 60), n=np.int64(N_NUIT), frais=np.float64(frais),
                pref=np.float64(pref), rond=np.float64(rond), pas=np.float64(pas), evenements=EVENEMENTS_NUIT)


def main():
    K.CACHE.mkdir(exist_ok=True)
    for nom in MARCHES_NUIT:
        d = seances(nom)
        r = d["jours"] <= K.FIN_RECHERCHE
        rr = {k: (v[r] if isinstance(v, np.ndarray) and v.ndim >= 1 and len(v) == len(r) else v) for k, v in d.items()}
        np.savez_compressed(K.CACHE / f"recherche_nuit_{nom}.npz", **rr)
        np.savez_compressed(K.CACHE / f"complet_nuit_{nom}.npz", **d)
        print(f"nuit {nom} : {len(d['jours'])} seances du {d['jours'][0]} au {d['jours'][-1]} ({int(r.sum())} pour la "
              f"recherche), completes {int(d['complete'].sum())}, prix de reference {d['pref']}", flush=True)


if __name__ == "__main__":
    main()
