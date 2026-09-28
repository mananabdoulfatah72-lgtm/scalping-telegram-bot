#!/usr/bin/env python3
"""Version 7 adaptee a un challenge 50K futures avec cloture le jour meme (regles fixees dans README.md) :
MNQ achete a l'ouverture, stop 0,5 % sous l'ouverture, vente a 15 h 59 ; filtre momentum mensuel du
Nasdaq (A) ou sans filtre (B). Verifie l'avantage, puis rejoue le bot coussin sur les regles des firmes.

Lancer depuis ce dossier : python3 version7_futures.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "intraday"))
sys.path.insert(0, str(ICI))
import strategies as st  # noqa: E402
from bot_challenge import FRACTIONS, REGLES, sans_avantage, sur_un_an, une_tentative  # noqa: E402

NOM = "nasdaq100"
STOP = 0.005
M6, SAUT = 126, 21


def journees():
    J, O, H, L, C, P, X = st.charger(NOM)
    c = st.CONTRATS[NOM]
    pt, tick, cout = c["pt"], c["tick"], st.cout_aller_retour(NOM)
    ech = X["echeance"]
    ouv, clo = O[:, 0], C[:, -1]
    # niveau du Nasdaq sans le saut de changement d'echeance (ce jour-la, seulement la seance)
    r = np.r_[0.0, clo[1:] / clo[:-1] - 1]
    r[ech] = (clo / ouv - 1)[ech]
    niveau = np.cumprod(1 + r)
    # signal mensuel, comme la version 7 : a la derniere seance du mois, rendement de t - 126 a t - 21
    mois = J.to_period("M")
    fins = [i for i in range(len(J)) if i + 1 == len(J) or mois[i + 1] != mois[i]]
    signal = np.full(len(J), np.nan)
    for e, suivante in zip(fins[:-1], fins[1:]):
        if e >= M6:
            signal[e + 1:suivante + 1] = float(niveau[e - SAUT] / niveau[e - M6] - 1 > 0)
    ok = st.journees_completes(P) & ~ech
    lignes = []
    for i in range(1, len(J)):
        if np.isnan(signal[i]):
            continue
        entree = ouv[i]
        seuil = entree * (1 - STOP)
        touche = np.flatnonzero(L[i] <= seuil)
        if touche.size:
            k = touche[0]
            sortie = min(seuil, O[i, k]) - tick           # stop touche (ou saute) : sortie au stop moins 1 tick
            bas = sortie
        else:
            sortie, bas = clo[i], L[i].min()
        lignes.append({
            "jour": J[i], "signal": signal[i], "ok": ok[i], "stop": bool(touche.size),
            "gain": (sortie - entree - cout) * pt,                         # $ pour 1 MNQ, frais compris
            "pire": (min(bas, sortie) - entree - cout) * pt,               # pire moment de la journee, $ pour 1 MNQ
            "risque1": (clo[i - 1] * STOP + tick + cout) * pt,             # perte au stop, connue avant l'ouverture
            "jour_nq": clo[i] / ouv[i] - 1, "nuit_nq": np.nan if ech[i] else ouv[i] / clo[i - 1] - 1,
        })
    return pd.DataFrame(lignes).set_index("jour")


def pour_le_bot(j, avec_filtre):
    trade = j["ok"] & ((j["signal"] == 1) if avec_filtre else True)
    d = pd.DataFrame({"gain": j["gain"].where(trade, 0.0), "pire": j["pire"].where(trade, 0.0).clip(upper=0),
                      "risque1": j["risque1"], "melange": 0.0, "stop": j["stop"] & trade})
    return d, trade


def avantage(nom, d, trade):
    """En dollars pour 1 MNQ, et en unites de risque (gain / perte au stop) : c'est ce que le bot trade,
    et le Nasdaq passe de 2 300 a 31 000 points, donc les dollars sont domines par les dernieres annees."""
    g = d.loc[trade, "gain"]
    u = g / d.loc[trade, "risque1"]
    tt = lambda x: x.mean() / x.std() * np.sqrt(len(x))
    print(f"  {nom} : {len(g)} trades | {g.mean():+.2f} $ par trade et par MNQ (t {tt(g):+.2f}) | en unites de risque "
          f"{u.mean():+.3f} (t {tt(u):+.2f}) | gagnants {(g > 0).mean():.0%} | stop touche {d.loc[trade, 'stop'].mean():.0%}")
    for a, z in [("2011", "2015"), ("2015", "2020"), ("2020", "2027")]:
        sel = (g.index >= a) & (g.index < z)
        print(f"     {a}-{int(z) - 1} : {g[sel].mean():+.2f} $ (t {tt(g[sel]):+.2f}) | unites de risque {u[sel].mean():+.3f}"
              f" (t {tt(u[sel]):+.2f}) | {sel.sum()} trades")


def placebo_filtre(j, n=500, graine=0):
    """Le filtre choisit-il de meilleurs mois que le hasard ? Meme suite de mois achetes / a plat, decalee au hasard."""
    rng = np.random.default_rng(graine)
    m = j["signal"].groupby(j.index.to_period("M")).first()
    g = (j["gain"] / j["risque1"]).where(j["ok"])           # en unites de risque
    mg = g.groupby(j.index.to_period("M")).agg(["sum", "count"])
    vrai = (mg["sum"] * m).sum() / (mg["count"] * m).sum()
    ps = []
    for _ in range(n):
        s = np.roll(m.values, rng.integers(12, len(m) - 12))
        ps.append((mg["sum"] * s).sum() / (mg["count"] * s).sum())
    return float(np.mean(np.array(ps) < vrai))


def main():
    j = journees()
    print(f"NQ minute {j.index[0].date()} -> {j.index[-1].date()} ({len(j)} seances avec signal)\n")
    nuit, jour = np.log1p(j["nuit_nq"].dropna()).sum(), np.log1p(j["jour_nq"]).sum()
    print(f"Information : sur la periode, le Nasdaq a fait {np.expm1(nuit):+.0%} la nuit (cloture -> ouverture) et "
          f"{np.expm1(jour):+.0%} en seance (ouverture -> cloture).\n")
    print("1. Avantage (1 MNQ, frais compris, stop 0,5 %) :")
    res = {}
    for nom, filtre in [("A avec filtre momentum", True), ("B sans filtre", False)]:
        d, trade = pour_le_bot(j, filtre)
        avantage(nom, d, trade)
        res[nom] = d
    print(f"  filtre A : placebo battu {placebo_filtre(j):.0%} (mois achetes tires au hasard, en unites de risque)\n")
    print("2. Challenge 50K (bot coussin, un depart par semaine, regles a verifier chez chaque firme) :")
    for nom, d in res.items():
        d0 = sans_avantage(d)
        for firme, regle in REGLES.items():
            for f in FRACTIONS:
                une = np.array([une_tentative(d, i, regle, f, False)[0] for i in range(0, len(d) - 252, 5)])
                an, an0 = sur_un_an(d, regle, f, False), sur_un_an(d0, regle, f, False)
                deux = (an["reussi"] & (an["tentatives"] <= 2)).mean()
                recent = sur_un_an(d[d.index >= "2020"], regle, f, False)
                recent0 = sur_un_an(sans_avantage(d[d.index >= "2020"]), regle, f, False)
                print(f"  {nom[:1]} {firme:12s} f={f:.2f} | 1 tentative : reussie {np.mean(une == 1):4.0%}, perdue {np.mean(une == -1):5.1%}"
                      f" | en 12 mois : valide {an['reussi'].mean():4.0%} (avec 2 comptes max {deux:4.0%} ;"
                      f" sans avantage {an0['reussi'].mean():4.0%} ; depuis 2020 {recent['reussi'].mean():4.0%},"
                      f" sans avantage {recent0['reussi'].mean():4.0%})"
                      f" | tentatives {an['tentatives'].mean():.1f} (max {an['tentatives'].max()})", flush=True)
        print()


if __name__ == "__main__":
    main()
