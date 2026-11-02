#!/usr/bin/env python3
"""Partie R (README.md) : Iwanaga-Sakemoto (R1, R1b), cycle de la Fed (R2), veille de jour ferie (R3), sur NQ et ES.
Lancer : NQ_CSV=<minutes NQ t,o,h,l,c,v,contrat> ES_CSV=<minutes ES> KB=<branche de recherche extraite> python3 scalping/partie_r.py"""
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from dateutil.easter import easter
from scipy.stats import norm

ICI = Path(__file__).parent
SORTIE = ICI / "resultats" / "r"
N = 390
MARCHES = {"NQ": dict(csv=os.environ["NQ_CSV"], pt=2.0, tick=0.25, pref=30900.0),
           "ES": dict(csv=os.environ["ES_CSV"], pt=5.0, tick=0.25, pref=7805.0)}
REGLES = ["R1", "R1b", "R2", "R3"]
PUBLICATION = {"R1": "2025-11-01", "R1b": "2025-11-01", "R2": "2019-01-01", "R3": "1990-01-01"}
SEUIL = float(norm.ppf(1 - 0.05 / 8))
TIRAGES = 200


def seances(csv):
    d = pd.read_csv(csv, usecols=["t", "o", "h", "l", "c", "contrat"])
    j = d["t"].str[:10]
    m = d["t"].str[11:13].astype(int) * 60 + d["t"].str[14:16].astype(int) - 570
    g = (m >= 0) & (m < N)
    d, j, m = d[g], j[g], m[g].to_numpy()
    jours = np.array(sorted(j.unique()))
    i = pd.Index(jours).get_indexer(j)
    A = {}
    for k in "oc":
        a = np.full((len(jours), N), np.nan)
        a[i, m] = d[k].to_numpy(float)
        A[k] = a
    pres = ~np.isnan(A["c"])
    C = pd.DataFrame(A["c"]).ffill(axis=1).to_numpy()
    O = np.where(np.isnan(A["o"]), C, A["o"])
    complete = pres[:, 0] & pres[:, N - 1] & (pres.sum(1) >= 370)
    contrat = d.groupby(j)["contrat"].agg(lambda s: s.mode().iloc[0]).reindex(jours).to_numpy()
    # cloture de la veille du meme contrat (seance complete juste avant)
    prec = np.full(len(jours), np.nan)
    for k in range(1, len(jours)):
        if complete[k - 1] and contrat[k - 1] == contrat[k]:
            prec[k] = C[k - 1, N - 1]
    return dict(jours=pd.to_datetime(jours).values.astype("datetime64[D]"), O=O, C=C, complete=complete, prec=prec)


def feries(a0, a1):
    """Jours de fermeture de la Bourse de New York (regles NYSE + fermetures exceptionnelles)."""
    out = set()
    def obs(d):                       # samedi -> vendredi, dimanche -> lundi
        return d - timedelta(1) if d.weekday() == 5 else d + timedelta(1) if d.weekday() == 6 else d
    def nieme(a, mo, wd, n):
        d = date(a, mo, 1)
        d += timedelta((wd - d.weekday()) % 7)
        return d + timedelta(7 * (n - 1))
    def dernier(a, mo, wd):
        d = date(a, mo + 1, 1) - timedelta(1) if mo < 12 else date(a, 12, 31)
        return d - timedelta((d.weekday() - wd) % 7)
    for a in range(a0, a1 + 1):
        ny = date(a, 1, 1)
        if ny.weekday() != 5:          # le 1er janvier un samedi n'est pas rattrape le vendredi
            out.add(obs(ny))
        out |= {nieme(a, 1, 0, 3), nieme(a, 2, 0, 3), easter(a) - timedelta(2), dernier(a, 5, 0), obs(date(a, 7, 4)),
                nieme(a, 9, 0, 1), nieme(a, 11, 3, 4), obs(date(a, 12, 25))}
        if a >= 2022:
            out.add(obs(date(a, 6, 19)))
    out |= {date(2012, 10, 29), date(2012, 10, 30), date(2018, 12, 5), date(2025, 1, 9)}
    return np.array(sorted(out), dtype="datetime64[D]")


def fomc():
    sys.path.insert(0, str(Path(os.environ["KB"]) / "fonds"))
    import fomc as F  # noqa: E402
    return np.array(F.annonces().values.astype("datetime64[D]"))


def signaux(S):
    """Position par seance (+1, -1, 0) pour chaque regle, et fenetre (entree, sortie) en minutes."""
    J, O, C, ok, prec = S["jours"], S["O"], S["C"], S["complete"], S["prec"]
    n = len(J)
    r = O[:, 0] / prec - 1
    pos = {}
    p1 = np.where(ok & ~np.isnan(r) & (r != 0), -np.sign(np.nan_to_num(r)), 0.0)
    pos["R1"] = p1
    ab = np.abs(r)
    seuil = np.full(n, np.nan)
    hist = []
    for k in range(n):
        if len(hist) >= 252:
            seuil[k] = np.percentile(hist[-252:], 70)
        if ok[k] and not np.isnan(ab[k]):
            hist.append(ab[k])
    pos["R1b"] = np.where(~np.isnan(seuil) & (ab >= seuil), p1, 0.0)
    # cycle de la Fed (en seances de la Bourse, completes ou non)
    F = fomc()
    idx = {d: k for k, d in enumerate(J)}
    tF = np.array([idx[d] for d in F if d in idx])
    sem = np.full(n, -99)
    for k in range(n):
        nxt = tF[tF >= k]
        if len(nxt) and nxt[0] - k <= 1:
            sem[k] = 0
            continue
        prv = tF[tF < k]
        if len(prv):
            sem[k] = (k - prv[-1] + 1) // 5
    pos["R2"] = np.where(ok & (sem >= 0) & (sem <= 6) & (sem % 2 == 0), 1.0, 0.0)
    fer = feries(int(str(J[0])[:4]), int(str(J[-1])[:4]) + 1)
    veille = np.zeros(n, bool)
    for f in fer:
        k = np.searchsorted(J, f) - 1           # derniere seance avant le jour ferie
        if 0 <= k < n and J[k] < f and (f - J[k]).astype(int) <= 4:
            veille[k] = True
    pos["R3"] = np.where(ok & veille, 1.0, 0.0)
    fen = {"R1": (1, 29), "R1b": (1, 29), "R2": (1, N - 1), "R3": (1, N - 1)}
    return pos, fen, dict(semaines=sem, veilles=veille)


def gains(S, p, fen, m):
    e, x = fen
    brut = p * (S["C"][:, x] - S["O"][:, e]) * m["pt"] * (m["pref"] / S["O"][:, 0])
    frais = 2 * (1 + m["tick"] * m["pt"])
    return np.where(p != 0, brut - frais, np.nan)


def tstat(g):
    g = g[~np.isnan(g)]
    return (g.mean() / g.std(ddof=1) * np.sqrt(len(g)), g.mean(), len(g)) if len(g) > 2 else (np.nan, np.nan, len(g))


def main():
    SORTIE.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(2026)
    lignes = [f"Partie R : seuil de retenue t >= {SEUIL:.2f} ; placebo {TIRAGES} tirages", "",
              "| Marche | Regle | Trades | t | Net par trade | 2011-2022 | 2023-fin | Depuis publication | Bat le placebo | Verdict |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    res = {}
    for nom, m in MARCHES.items():
        S = seances(m["csv"])
        pos, fen, info = signaux(S)
        J = S["jours"]
        a1, a2 = J <= np.datetime64("2022-12-31"), J >= np.datetime64("2023-01-01")
        for R in REGLES:
            g = gains(S, pos[R], fen[R], m)
            t, moy, n = tstat(g)
            t1, m1, _ = tstat(np.where(a1, g, np.nan))
            t2, m2, _ = tstat(np.where(a2, g, np.nan))
            tp, mp, npub = tstat(np.where(J >= np.datetime64(PUBLICATION[R]), g, np.nan))
            plac = []
            eligibles = np.where(S["complete"] & (~np.isnan(S["prec"]) if R.startswith("R1") else S["complete"]))[0]
            for _ in range(TIRAGES):
                q = np.zeros(len(J))
                if R.startswith("R1"):
                    act = np.where(pos[R] != 0)[0]
                    q[rng.choice(eligibles, len(act), replace=False)] = rng.permutation(pos[R][act])
                else:
                    q[rng.choice(eligibles, int((pos[R] != 0).sum()), replace=False)] = 1.0
                plac.append(tstat(gains(S, q, fen[R], m))[0])
            pc = float(np.mean(np.array(plac) < t) * 100)
            deux = m1 > 0 and m2 > 0
            verdict = "RETENUE" if t >= SEUIL and deux and pc >= 95 else "interessante" if t >= 1.65 and deux and pc >= 90 else "rejetee"
            res[f"{nom} {R}"] = dict(trades=n, t=t, moyenne=moy, t_2011_2022=t1, t_2023=t2, t_publication=tp, n_publication=npub,
                                     placebo_pct=pc, verdict=verdict)
            lignes.append(f"| {nom} | {R} | {n} | {t:+.2f} | {moy:+.1f} $ | {t1:+.2f} ({m1:+.1f} $) | {t2:+.2f} ({m2:+.1f} $) | "
                          f"{tp:+.2f} ({npub}) | {pc:.0f} % | {verdict} |")
        lignes.append(f"\n{nom} : {int(S['complete'].sum())} seances completes, {int(info['veilles'].sum())} veilles de jour ferie, "
                      f"{int(((info['semaines'] >= 0) & (info['semaines'] <= 6)).sum())} seances dans les semaines 0 a 6 du cycle de la Fed\n")
    (SORTIE / "partie_r.txt").write_text("\n".join(lignes) + "\n")
    json.dump(res, open(SORTIE / "partie_r.json", "w"), indent=1, default=float)
    print("\n".join(lignes))


if __name__ == "__main__":
    main()
