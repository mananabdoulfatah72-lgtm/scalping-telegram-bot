#!/usr/bin/env python3
"""Machine 12 (asie/README.md) : l'elan de fin de seance a l'heure de reglement propre a 7 marches jamais testes a ces
heures (cuivre, platine, essence, gaz naturel, obligations a 30, 10 et 5 ans), mesure sur leurs ETF (Alpaca, 5 minutes,
2016 - 2026), tous les jours et seulement les jours de grand mouvement, aux frais d'aujourd'hui des futures CME.
Usage : ETF_DONNEES=<dossier des fichiers <ETF>.csv.gz> python3 asie/machine12.py
"""
import json
import os
import sys
from pathlib import Path

import holidays
import numpy as np
import pandas as pd
from scipy.stats import norm

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import machine7 as M7  # noqa: E402

D = Path(os.environ["ETF_DONNEES"])
DEBUT, FIN_EXPLO, DEBUT_COFFRE, FIN = "2016-01-01", "2022-12-31", "2023-01-01", "2026-10-02"
SOUS = [(2016, 2018), (2019, 2020), (2021, 2022)]
FOIS, FENETRE, N_SIGNES, GRAINE = 1.5, 60, 1000, 12
# ETF : (future, heure de reglement a New York, $ d'un aller-retour = 2 ticks + commissions, nominal du future le 21 oct. 2026)
MARCHES = {
    "CPER": ("Cuivre (HG)", "13:00", 30.0, 25000 * 6.5700),
    "PPLT": ("Platine (PL)", "13:05", 15.0, 50 * 1633.9),
    "UGA": ("Essence (RB)", "14:30", 13.4, 42000 * 3.0514),
    "UNG": ("Gaz naturel (NG)", "14:30", 25.0, 10000 * 2.776),
    "TLT": ("Obligation 30 ans (ZB)", "15:00", 67.5, 100000 * 1.058125),
    "IEF": ("Obligation 10 ans (ZN)", "15:00", 36.25, 100000 * 1.05265625),
    "IEI": ("Obligation 5 ans (ZF)", "15:00", 20.6, 100000 * 1.039140625),
}


def seances(etf):
    d = pd.read_csv(D / f"{etf}.csv.gz", usecols=["t", "c"]); t = pd.to_datetime(d["t"])
    m = (t.dt.hour * 60 + t.dt.minute - 570) // 5
    ok = (m >= 0) & (m < 78)
    P = pd.DataFrame({"jour": t.dt.normalize()[ok], "k": m[ok], "c": d["c"][ok]}).pivot_table(index="jour", columns="k", values="c", aggfunc="last")
    P = P.reindex(columns=range(78)).ffill(axis=1)                    # dernier prix connu dans la seance
    fer = holidays.NYSE(years=range(2015, 2027))
    P = P[[(j.dayofweek < 5) and (j.date() not in fer) for j in P.index]]
    return P


def prix_a(P, hhmm):
    h, m = map(int, hhmm.split(":")); k = (h * 60 + m - 570) // 5 - 1   # cloture de la barre qui finit a cette heure
    return P[k].to_numpy()


def trades(etf, grand):
    nom, reg, dollars, nominal = MARCHES[etf]; P = seances(etf)
    h, m = map(int, reg.split(":")); avant = f"{(h * 60 + m - 30) // 60:02d}:{(h * 60 + m - 30) % 60:02d}"
    e, x = prix_a(P, avant), prix_a(P, reg)
    veille = np.r_[np.nan, x[:-1]]
    R = e / veille - 1
    brut = np.sign(R) * (x / e - 1)
    d = pd.DataFrame({"jour": P.index, "R": R, "brut": brut}).dropna().reset_index(drop=True)
    d = d[d["R"] != 0].reset_index(drop=True)
    if grand:
        a = d["R"].abs(); moy = a.shift(1).rolling(FENETRE, min_periods=40).mean()
        d = d[(a >= FOIS * moy).fillna(False)].reset_index(drop=True)
    frais = dollars / nominal
    d["r"] = d["brut"] - frais
    return d, frais, nominal


def mesure(d, debut, fin, nominal, sous=SOUS):
    x = d[(d["jour"] >= pd.Timestamp(debut)) & (d["jour"] <= pd.Timestamp(fin))]
    an = x["jour"].dt.year
    return x, {"t": round(M7.t_stat(x["r"].to_numpy()), 2), "t_brut": round(M7.t_stat(x["brut"].to_numpy()), 2), "jours": int(len(x)),
               "brut_moyen_pb": round(float(x["brut"].mean()) * 1e4, 2), "net_moyen_pb": round(float(x["r"].mean()) * 1e4, 2),
               "sous_periodes": [round(float(x["r"][(an >= a) & (an <= b)].sum()) * 1e4, 1) for a, b in sous],
               "dollars_1_contrat": round(float(x["r"].sum()) * nominal)}


def principal():
    res = []
    for etf in MARCHES:
        for grand in (False, True):
            d, frais, nominal = trades(etf, grand)
            x, b = mesure(d, DEBUT, FIN_EXPLO, nominal)
            rng = np.random.default_rng(GRAINE); br = x["brut"].to_numpy()
            ts = np.array([M7.t_stat(rng.choice([-1.0, 1.0], len(br)) * br - frais) for _ in range(N_SIGNES)])
            b.update(nom=f"{MARCHES[etf][0]} via {etf}, {'grands jours' if grand else 'tous les jours'}, reglement {MARCHES[etf][1]}",
                     etf=etf, grand=grand, frais_pb=round(frais * 1e4, 2), p=float((ts >= b["t"]).mean()))
            res.append(b)
            print(f"{b['nom']} : frais {b['frais_pb']} pb, brut {b['brut_moyen_pb']:+.2f} pb (t {b['t_brut']:+.2f}), net {b['net_moyen_pb']:+.2f} pb "
                  f"(t {b['t']:+.2f}), p {b['p']:.3f}, {b['jours']} jours, {b['sous_periodes']}", flush=True)
    bh = M7.benjamini_hochberg([r["p"] for r in res])
    for r, g in zip(res, bh):
        r["bh"] = bool(g)
        r["survivante"] = bool(r["t"] >= 2 and r["p"] <= 0.05 and sum(v > 0 for v in r["sous_periodes"]) >= 2 and g and r["jours"] >= 200)
    surv = [r for r in res if r["survivante"]]
    print(f"\nMachine 12, exploration 2016 - 2022 : {len(res)} regles ; survivantes : {len(surv)}")
    if surv:
        seuil = float(norm.ppf(1 - 0.05 / len(surv)))
        print(f"Coffre 2023 -> {FIN}, ouvert une seule fois : seuil de Bonferroni t >= {seuil:.2f}, 3 annees positives sur 4")
        for r in surv:
            d, frais, nominal = trades(r["etf"], r["grand"])
            x, b = mesure(d, DEBUT_COFFRE, FIN, nominal, sous=[(2023, 2023), (2024, 2024), (2025, 2025), (2026, 2026)])
            r["coffre"] = b; r["passe"] = bool(b["t"] >= seuil and sum(v > 0 for v in b["sous_periodes"]) >= 3)
            print(f"{r['nom']} | t {b['t']:+.2f} | brut {b['brut_moyen_pb']:+.2f} pb, net {b['net_moyen_pb']:+.2f} pb | annees {b['sous_periodes']} | "
                  f"{b['dollars_1_contrat']:+,} $ | {'PASSE' if r['passe'] else 'echoue'}")
    (ICI / "machine12.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    principal()
