#!/usr/bin/env python3
"""Partie 14 (flux/README.md) : week-end crypto (W1, W2), liquidite nette de la Fed (N1, N2), prime de variance du
Nasdaq (V1, V2), fixes le 30 octobre 2026 avant tout calcul. Trades de l'ouverture a la cloture du NQ.

Lancer : python3 flux/recherche14.py <minutes NQ 2011 - 2026 (t,o,h,l,c,v,contrat)>"""
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "scalping"))
import donnees as SD  # noqa: E402

DEBUT_0DTE = "2022-05-16"
FRAIS = 3.0


def serie(famille, nom):
    fs = sorted((ICI.parent / "radar/donnees/jour" / famille).glob("*.csv.gz"))
    t = pd.concat([pd.read_csv(f) for f in fs])
    s = t[t["serie"] == nom].assign(date=lambda x: pd.to_datetime(x["date"])).set_index("date")["valeur"]
    return s.astype(float).sort_index()


def au_plus_tard(s, jours, decalage_jours):
    """Derniere valeur datee au plus tard `decalage_jours` jours calendaires avant chaque seance."""
    s = s.dropna()
    i = s.index.searchsorted(jours - pd.Timedelta(days=decalage_jours), side="right") - 1
    return np.where(i >= 0, s.values[np.maximum(i, 0)], np.nan)


def main():
    d = SD.minutes("NQ", chemin=sys.argv[1], debut="2011-01-01")
    jours = pd.DatetimeIndex(d["jours"].astype("datetime64[D]"))
    O, C = d["o"], d["c"]
    ok = d["complete"] & ~d["ech"]
    seance = (C[:, 389] - O[:, 0]) * float(d["pref"]) / O[:, 0] * float(d["pt"])
    # W : bitcoin du vendredi (cloture UTC = 20 h New York) au dimanche (meme heure)
    btc = serie("yahoo", "BTC-USD:c")
    lundi = jours.dayofweek == 0
    ven = np.array([btc.get(j - pd.Timedelta(days=3), np.nan) for j in jours])
    dim = np.array([btc.get(j - pd.Timedelta(days=1), np.nan) for j in jours])
    w = np.where(lundi, dim / ven - 1, np.nan)
    # N : liquidite nette du mercredi = WALCL - WTREGEN - RRP (milliards), utilisable a partir du vendredi
    walcl, tga, rrp = serie("alt", "fred:WALCL"), serie("alt", "fred:WTREGEN"), serie("alt", "fred:RRPONTSYD")
    mer = walcl.index
    nl = walcl / 1000 - tga.reindex(mer).ffill() / 1000 - rrp.reindex(rrp.index.union(mer)).ffill().reindex(mer).fillna(0)
    dnl = (nl - nl.shift(4)).dropna()
    dn = au_plus_tard(dnl, jours, 2)
    # V : prime de variance = (VXN/100)^2 de la veille - variance realisee du NQ (21 seances d'avant, annualisee)
    vxn = serie("yahoo", "^VXN:c")
    lr = np.diff(np.log(C), axis=1)
    rv = pd.Series(np.where(d["complete"], (lr ** 2).sum(1), np.nan), index=jours)
    rv21 = rv.rolling(21, min_periods=15).mean().shift(1) * 252
    vrp = pd.Series(au_plus_tard(vxn, jours, 1) / 100, index=jours) ** 2 - rv21
    rang = vrp.rolling(253, min_periods=200).apply(lambda x: (x[:-1] < x[-1]).mean() if np.isfinite(x[-1]) else np.nan,
                                                   raw=True).values
    regles = {
        "W1 week-end bitcoin négatif : vente le lundi": np.where(w < 0, -1, 0),
        "W2 week-end bitcoin ≤ −2 % : vente le lundi": np.where(w <= -0.02, -1, 0),
        "N1 liquidité nette en hausse : achat": np.where(dn > 0, 1, 0),
        "N2 liquidité nette : achat si hausse, vente si baisse": np.where(dn > 0, 1, np.where(dn < 0, -1, 0)),
        "V1 prime de variance haute : achat": np.where(rang >= 2 / 3, 1, 0),
        "V2 prime de variance : achat si haute, vente si basse": np.where(rang >= 2 / 3, 1, np.where(rang <= 1 / 3, -1, 0)),
    }
    base = pd.Series(np.where(ok, seance - FRAIS, np.nan), index=jours)
    seuil = NormalDist().inv_cdf(1 - 0.05 / len(regles))
    L = ["# Partie 14 : week-end crypto, liquidité nette, prime de variance", "",
         f"Trades de 9 h 30 à 16 h sur le NQ, $ pour 1 MNQ au prix d'aujourd'hui. Barre sur l'ère 0DTE : t ≥ {seuil:.2f}, "
         "gain moyen positif, 3 années gagnantes sur 5 (et, pour N1 et V1, mieux qu'un achat à chaque séance).", "",
         f"Référence, achat à chaque séance (frais compris) : ère 0DTE {base[jours >= DEBUT_0DTE].mean():+.1f} $ par séance ; "
         f"avant {base[jours < DEBUT_0DTE].mean():+.1f} $.", "",
         "| Règle | Période | Trades | Total | Moyenne | Moyenne à 6 $ de frais | t | Années |", "|---|---|---|---|---|---|---|---|"]
    for nom, sens in regles.items():
        brut = pd.Series(np.where(ok & (sens != 0), sens * seance, np.nan), index=jours)
        for per, m in (("avant mai 2022", jours < DEBUT_0DTE), ("ère 0DTE", jours >= DEBUT_0DTE)):
            y = (brut[m] - FRAIS).dropna()
            if len(y) < 2:
                L.append(f"| {nom} | {per} | {len(y)} | — | — | — | — | |")
                continue
            t = y.mean() / y.std(ddof=1) * np.sqrt(len(y))
            ans = y.groupby(y.index.year).sum()
            verdict = ""
            if per == "ère 0DTE":
                bat = nom[:2] not in ("N1", "V1") or y.mean() > base[m].mean()
                verdict = " **PASSE**" if (t >= seuil and y.mean() > 0 and (ans > 0).sum() >= 3 and bat) else " échoue"
            txt = ", ".join(f"{k} {v:+,.0f}" for k, v in ans.items()) if per == "ère 0DTE" else ""
            L.append(f"| {nom} | {per}{verdict} | {len(y)} | {y.sum():+,.0f} $ | {y.mean():+,.1f} $ | {y.mean() - FRAIS:+,.1f} $ | "
                     f"{t:+.2f} | {txt} |")
    out = ICI / "resultats/partie14"
    out.mkdir(parents=True, exist_ok=True)
    (out / "recherche14.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
