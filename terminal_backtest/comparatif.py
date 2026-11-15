#!/usr/bin/env python3
"""Tes strategies deja mesurees sur le NQ, a cote des strategies quotidiennes du terminal, dans la meme unite :
dollars par seance pour 1 MNQ au prix d'aujourd'hui (28 500 points, soit 57 000 $ de valeur), frais compris,
sur la meme periode (celle des passes du terminal).

Deux mesures de fiabilite :
- t : le gain moyen compare a ses variations (au-dessus de 2, peu de chances que ce soit le hasard) ;
- t hors marche : la meme chose une fois retiree la part du gain qui vient de la simple hausse du NQ
  (regression du gain du jour sur le rendement du NQ du meme jour). C'est elle qui dit si la strategie apporte
  quelque chose de plus que « etre achete ».

Usage : SCRATCH=<dossier de travail avec st_detail.py, lm/, zone_c2q1_15ans.txt, nq_15ans.csv.gz> python3 comparatif.py
"""
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
S = Path(os.environ["SCRATCH"])
sys.path.insert(0, str(ICI)); sys.path.insert(0, str(S)); sys.path.insert(0, str(S / "lm/chantier"))
import reference as R  # noqa: E402

VALEUR = 57000.0
out, sig, D = R.tout()
dates = D["dates"]; a0 = out["meta"]["long"]["a"]; T = len(dates)
DEBUT, FIN = dates[a0], dates[T - 1]
nq = D["marches"][0]
MARCHE = {dates[t]: nq["c"][t] / nq["c"][t - 1] - 1.0 for t in range(1, T)}     # rendement du NQ, seance par seance
SERIES = {}


def mesure(nom, famille, jours, dollars, bulenox, note=""):
    s = pd.Series(dollars, index=jours, dtype=float)
    s = s[(s.index >= DEBUT) & (s.index <= FIN)]
    SERIES[nom] = s
    x = s.to_numpy(); n = len(x); m = x.mean(); e = x.std(ddof=1)
    r = s[s.index >= "2023-01-01"].to_numpy()
    cum = np.cumsum(x); an = s.groupby(s.index.str[:4]).sum()
    commun = [j for j in s.index if j in MARCHE]
    alpha, beta, ta = R.hors_marche([float(s[j]) for j in commun], [MARCHE[j] * VALEUR for j in commun])
    repere = famille == "repere"          # le marche lui-meme : « hors marche » n'a pas de sens
    return {"nom": nom, "famille": famille, "seances": int(n), "par_seance": float(m), "par_an": float(m * 252),
            "t": float(m / e * math.sqrt(n)), "t_depuis_2023": float(r.mean() / r.std(ddof=1) * math.sqrt(len(r))),
            "hors_marche_par_an": None if repere else float(alpha * 252), "part_du_marche": float(beta),
            "t_hors_marche": None if repere else float(ta),
            "pire_baisse": float((cum - np.maximum.accumulate(cum)).min()), "pire_seance": float(x.min()),
            "annees_perdantes": [k for k, v in an.items() if v < 0], "bulenox": bulenox, "note": note}


L = []
# 1. les strategies quotidiennes du terminal, sur le NQ, frais reels d'un micro-contrat (0,3 pb par ordre)
NOMS = {"supertrend": "Supertrend 10-3 (quotidien)", "zscore": "Z-score 20 (quotidien)", "dualmom": "Dual momentum",
        "ema_stop": "EMA 20/50 + stop ATR", "keltner": "Cassure de Keltner", "stoch": "Stochastique 14-3", "rsi2": "RSI(2) (quotidien)"}
for s in R.STRATEGIES:
    _, rets = R.backtest(sig[s][0], nq["o"], nq["c"], nq["r"], a0, T, 0.3 / 1e4)
    L.append(mesure(NOMS[s], "terminal", dates[a0:T], [r * VALEUR for r in rets], "interdit : position gardée plusieurs jours"))
_, rets = R.backtest([1] * T, nq["o"], nq["c"], nq["r"], a0, T, 0.3 / 1e4)
L.append(mesure("Acheter et conserver le NQ", "repere", dates[a0:T], [r * VALEUR for r in rets], "interdit : position gardée plusieurs jours"))

# 2. tes bots intraday (minutes NQ 2011 - 13 novembre 2026, 3 $ de frais par aller-retour et par MNQ)
import st_detail as X  # noqa: E402
import rejeu_periode as RP  # noqa: E402
J = [str(j) for j in X.J]; ok = [d for d in range(X.nj) if X.complete[d]]
tr, _ = RP.trades_bot(S / "zone_c2q1_15ans.txt")
z = {}
for j, sens, _, _, e, x in tr:
    z[j] = z.get(j, 0.0) + sens * (x - e) * 2 * (28500.0 / e) - 3.0
L.append(mesure("Zone de bruit (Bot 3 en 1, réglages actuels)", "tes bots", [J[d] for d in ok], [z.get(J[d], 0.0) for d in ok],
                "permis : à plat chaque soir", "sans le filtre delta, qui n'existe pas avant 2026"))


def journee(dd, lim):
    jv, arret = 0.0, False
    for i in range(X.jd[dd], X.jf[dd]):
        if arret:
            break
        s, me, mx, e, sortie = int(X.T[i, 1]), int(X.T[i, 2]), int(X.T[i, 3]), X.T[i, 4], X.T[i, 5]
        k = 28500.0 / e
        for mm in range(me + 1, mx + 1):
            o, adv = X.O[dd, mm], (X.L[dd, mm] if s > 0 else X.H[dd, mm])
            if jv + (2 * s * (adv - e) * k - 3.0) <= -lim:
                niv = e + s * ((-lim - jv) + 3.0) / (2 * k)
                sortie = (min(o, niv) - 1.0) if s > 0 else (max(o, niv) + 1.0); arret = True
                break
        jv += 2 * s * (sortie - e) * k - 3.0
    return jv


L.append(mesure("Supertrend 10-3 en 5 minutes (limite 400 $)", "tes bots", [J[d] for d in ok], [journee(d, 400) for d in ok],
                "permis : à plat chaque soir"))
m = pd.read_csv(S / "nq_15ans.csv.gz", usecols=["t", "o", "c", "contrat"])
m["j"] = m.t.str[:10]; g = m.groupby("j")
q = pd.DataFrame({"o": g.o.first(), "c": g.c.last(), "k": g.contrat.last(), "k0": g.contrat.first(), "n": g.size()})
q = q[q.n >= 370]
gain = (q.o / q.c.shift(1) - 1.0) * VALEUR - 3.0            # nuit qui finit a l'ouverture de ce jour
nuit = gain[(q.k0 == q.k.shift(1))].dropna()
L.append(mesure("Nuit (achat à 16 h, vente à 9 h 30 le lendemain)", "tes bots", list(nuit.index), nuit.to_numpy(),
                "permis seulement de 18 h à 9 h 30", "hors nuits de changement de contrat ; la version permise chez Bulenox entre à 18 h"))

# 3. ce que ca dit, ecrit a partir des nombres (frais de 2 pb pour les cellules, comme la page)
moins = lambda t_: t_.replace("-", "−")
fr = lambda x, d=1: moins(f"{x:+,.{d}f}".replace(",", " ").replace(".", ","))
ent = lambda x: moins(f"{x:+,.0f}".replace(",", " "))
cel = out["cellules"]["demande"]
joue = {s: sum(c["trades"] > 0 for p in cel for c in p[i]) for i, s in enumerate(R.STRATEGIES)}
bat = {s: sum(c["trades"] > 0 and c["ret"] > c["bh"] for p in cel for c in p[i]) for i, s in enumerate(R.STRATEGIES)}
part = {s: bat[s] / joue[s] for s in R.STRATEGIES}
lg = out["long"]["demande"]
nb = {s: sum(x["t_alpha"] >= 2 for x in lg[i]) for i, s in enumerate(R.STRATEGIES)}
tient = [NOMS[s] for s in R.STRATEGIES if nb[s] >= 2]; un = [NOMS[s] for s in R.STRATEGIES if nb[s] == 1]
meilleur_t = max(x["t_alpha"] for ligne in lg for x in ligne)
par_nom = {x["nom"]: x for x in L}
zone = next(x for x in L if x["nom"].startswith("Zone")); st5 = next(x for x in L if "5 minutes" in x["nom"])
nuit_ = next(x for x in L if x["nom"].startswith("Nuit")); bh = par_nom["Acheter et conserver le NQ"]; dm = par_nom["Dual momentum"]
liste = lambda v: " et ".join([", ".join(v[:-1]), v[-1]]) if len(v) > 1 else (v[0] if v else "aucune")
res = {"periode": {"debut": DEBUT, "fin": FIN},
       "unite": "dollars pour 1 MNQ au prix d'aujourd'hui (57 000 $ de valeur), frais compris", "lignes": L}
res["conclusions"] = [
    f"Aucune des 7 stratégies quotidiennes ne bat « acheter et conserver » plus de {max(part.values()) * 100:.0f} fois sur 100 : "
    f"de {min(bat.values())} à {max(bat.values())} années-marchés gagnées, sur 54 à 60 jouées.",
    (f"Une fois retirée la part du gain qui vient de la simple hausse du marché, tiennent sur au moins 2 marchés : {liste(tient)}."
     if tient else
     f"Une fois retirée la part du gain qui vient de la simple hausse du marché, aucune des 7 ne tient : le meilleur « t hors marché » "
     f"des 28 tests est {fr(meilleur_t, 2)}, sous le seuil de 2." + (f" Sur un seul marché : {liste(un)}." if un else "")),
    f"Le dual momentum gagne {ent(dm['par_an'])} $ par an sur le NQ parce qu'il est acheté plus de la moitié du temps dans un marché qui "
    f"monte. Hors marché, il reste {ent(dm['hors_marche_par_an'])} $ par an (t {fr(dm['t_hors_marche'], 2)}) : ce n'est pas un avantage.",
    f"Acheter et conserver le NQ gagne {ent(bh['par_an'])} $ par an pour 1 MNQ, avec une pire baisse de {ent(bh['pire_baisse'])} $ : "
    f"bien plus que les 2 500 $ permis sur un compte Bulenox.",
    f"Parmi tes bots, la zone de bruit reste la plus solide : {ent(zone['par_an'])} $ par an, t {fr(zone['t'], 2)} "
    f"(hors marché {fr(zone['t_hors_marche'], 2)}), pire baisse {ent(zone['pire_baisse'])} $, {len(zone['annees_perdantes'])} année perdante.",
    f"Le Supertrend en 5 minutes gagne autant par an ({ent(st5['par_an'])} $), mais avec une pire baisse de {ent(st5['pire_baisse'])} $ "
    f"et un avantage qui n'est plus mesurable depuis 2023 (t {fr(st5['t_depuis_2023'], 2)}).",
    f"La nuit sur le NQ gagne {ent(nuit_['par_an'])} $ par an (t {fr(nuit_['t'], 2)}, hors marché {fr(nuit_['t_hors_marche'], 2)}). "
    f"Chez Bulenox, elle n'est permise que de 18 h à 9 h 30.",
]
(ICI / "comparatif.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
pd.DataFrame(SERIES).to_csv(ICI / "series_par_seance.csv")
print("\n".join(res["conclusions"]))
for x in L:
    if x["t_hors_marche"] is None:
        continue
    print(f"{x['nom'][:50]:50s} {x['par_an']:+8,.0f} $/an  t {x['t']:+.2f}  hors marche {x['hors_marche_par_an']:+8,.0f} $/an t {x['t_hors_marche']:+.2f} "
          f"(part du marche {x['part_du_marche']:+.2f})  t depuis 2023 {x['t_depuis_2023']:+.2f}  pire baisse {x['pire_baisse']:+9,.0f} $")
