#!/usr/bin/env python3
"""Etape 7 de la recette : ouvrir les resultats de zipline avec pandas, imprimer rendements, pire baisse et chaque
transaction, comparer a l'achat-conservation et rendre le verdict ecrit d'avance (REGLES.md). Ecrit aussi les donnees de
l'ecran Lightweight Charts. python3 lire.py <dossier de travail> <sortie.json>"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

TRAV = Path(sys.argv[1]); SORTIE = Path(sys.argv[2])
ECH = json.load(open(TRAV / "csv/echelles.json"))
ACTIFS = [("BTC", "crypto"), ("ETH", "crypto"), ("SOL", "crypto")] + [(s, "etf") for s in ("QQQ", "SPY", "IWM", "GLD", "TLT", "SMH")]
FRAIS_BH = {"crypto": 2 * (0.0026 + 0.0005), "etf": 2 * 0.0005}             # un aller-retour pour l'achat-conservation


def baisse(eq):
    return float((eq / eq.cummax() - 1).min())


def mesures(r, eq, an):
    r = r.fillna(0.0); n = len(r); moit = n // 2
    t = float(r.mean() / r.std(ddof=1) * np.sqrt(n)) if r.std() > 0 else 0.0
    ans = n / an
    return dict(rendement=float(eq.iloc[-1] / eq.iloc[0] - 1), par_an=float((eq.iloc[-1] / eq.iloc[0]) ** (1 / ans) - 1),
                pire_baisse=baisse(eq), sharpe=float(r.mean() / r.std() * np.sqrt(an)) if r.std() > 0 else 0.0, t=t,
                moitie1=float((1 + r.iloc[:moit]).prod() - 1), moitie2=float((1 + r.iloc[moit:]).prod() - 1), jours=n)


def lire(actif, fam, nom):
    p = pd.read_pickle(TRAV / "resultats" / f"{actif}_{nom}.pickle")
    k = ECH.get(actif, 1.0) if fam == "crypto" else 1.0
    jours = pd.to_datetime(p.period_open).dt.tz_localize(None).dt.normalize()   # date de la seance (calendrier 24/7 compris)
    p.index = jours
    an = 365 if fam == "crypto" else 252
    eq = p.portfolio_value
    prix = p.prix * k
    bh_r = prix.pct_change().fillna(0.0); bh_r.iloc[0] -= FRAIS_BH[fam] / 2; bh_r.iloc[-1] -= FRAIS_BH[fam] / 2
    bh_eq = 10000 * (1 + bh_r).cumprod()
    # transactions (prix reels) et motif de chaque sortie (decide a la cloture d'avant, execute a la cloture suivante)
    tx, motifs = [], p.motif.where(p.motif != "")
    com = {o["id"]: (o["commission"] or 0.0) for liste in p.orders for o in liste}   # zipline range les frais dans les ordres
    vus = set()
    for d, liste in p.transactions.items():
        for t in liste:
            frais = com.get(t["order_id"], 0.0) if t["order_id"] not in vus else 0.0; vus.add(t["order_id"])
            sens = "achat" if t["amount"] > 0 else "vente"
            avant = motifs[:d - pd.Timedelta(days=1)].dropna()
            sortie = avant.iloc[-1] if len(avant) else ""
            if sens == "vente" and sortie in ("entrée", ""):
                sortie = "fin des données"          # zipline ferme la position quand l'actif n'a plus de bougies
            tx.append(dict(date=d.strftime("%Y-%m-%d"), sens=sens, quantite=float(abs(t["amount"]) / k), prix=float(t["price"] * k),
                           frais=float(frais), motif="entrée" if sens == "achat" else sortie))
    # allers-retours
    rt, ouvert = [], None
    for t in tx:
        if t["sens"] == "achat":
            ouvert = t
        elif ouvert:
            rt.append(dict(entree=ouvert["date"], sortie=t["date"], prix_entree=ouvert["prix"], prix_sortie=t["prix"], motif=t["motif"],
                           resultat=float(t["prix"] / ouvert["prix"] - 1))); ouvert = None
    m = mesures(p.returns, eq, an); b = mesures(bh_r, bh_eq, an)
    m.update(trades=len(rt), gagnants=float(np.mean([x["resultat"] > 0 for x in rt])) if rt else None,
             en_marche=float((p.long_value > 0).mean()), frais=float(sum(t["frais"] for t in tx)),
             sorties={mo: sum(1 for x in rt if x["motif"] == mo) for mo in ("stop", "objectif", "fin de tendance")})
    return p, k, eq, bh_eq, prix, tx, rt, m, b


def csv_reel(actif, fam):
    c = pd.read_csv(TRAV / "csv" / fam / "daily" / f"{actif}.csv", parse_dates=["date"]).set_index("date")
    k = ECH.get(actif, 1.0) if fam == "crypto" else 1.0
    if fam == "crypto":
        c.index = c.index + pd.Timedelta(days=1)                             # dates reelles (voir extraire.py)
    return c[["open", "high", "low", "close"]] * k


tout, pv = {}, {}
for actif, fam in ACTIFS:
    tout[actif] = {"famille": fam}
    for nom in ("fenetre", "complet"):
        p, k, eq, bh_eq, prix, tx, rt, m, b = lire(actif, fam, nom)
        print(f"\n===== {actif} · {'1er janv. 2024 → 31 déc. 2025' if nom == 'fenetre' else 'historique complet'} "
              f"({p.index[0].date()} → {p.index[-1].date()}) =====")
        print(f"stratégie : {m['rendement']:+.1%} ({m['par_an']:+.1%} par an), pire baisse {m['pire_baisse']:.1%}, Sharpe {m['sharpe']:.2f}, "
              f"t {m['t']:.2f}, {m['trades']} trades, {m['en_marche']:.0%} du temps investi, frais {m['frais']:,.0f} $")
        print(f"achat-conservation : {b['rendement']:+.1%} ({b['par_an']:+.1%} par an), pire baisse {b['pire_baisse']:.1%}, Sharpe {b['sharpe']:.2f}")
        if nom == "fenetre":
            print("transactions :")
            for t in tx:
                print(f"  {t['date']}  {t['sens']:5s} {t['quantite']:12.4f} à {t['prix']:12,.2f} $  frais {t['frais']:7.2f} $  {t['motif']}")
        c = csv_reel(actif, fam).loc[p.index[0]:p.index[-1]]
        rec = lambda s: [None if not np.isfinite(v) else round(float(v), 6) for v in s]
        tout[actif][nom] = dict(
            mesures=m, achat_conservation=b, transactions=tx, allers_retours=rt,
            bougies=[[d.strftime("%Y-%m-%d"), *[round(float(v), 6) for v in row]] for d, row in zip(c.index, c.values)],
            jours=[d.strftime("%Y-%m-%d") for d in p.index], capital=rec(eq), capital_bh=rec(bh_eq),
            ema20=rec(p.ema20 * k), ema50=rec(p.ema50 * k), stop=rec(p.stop * k), objectif=rec(p.objectif * k))
        if nom == "complet":
            pv[actif] = 1 - stats.t.cdf(m["t"], m["jours"] - 1)

# verdict ecrit d'avance (sur l'historique complet) + Benjamini-Hochberg sur les 9
cles = list(pv); p_ = np.array([pv[c] for c in cles]); o = np.argsort(p_)
ok = p_[o] <= 0.05 * np.arange(1, len(p_) + 1) / len(p_); kk = (np.nonzero(ok)[0].max() + 1) if ok.any() else 0
bh = {cles[i] for i in o[:kk]}
print("\n===== verdict (historique complet, règles fixées d'avance) =====")
for a in cles:
    m, b = tout[a]["complet"]["mesures"], tout[a]["complet"]["achat_conservation"]
    raisons = []
    if m["t"] < 2: raisons.append(f"t {m['t']:.2f} sous 2")
    if m["moitie1"] <= 0 or m["moitie2"] <= 0: raisons.append("perd sur une moitié")
    if m["sharpe"] <= b["sharpe"]: raisons.append(f"Sharpe {m['sharpe']:.2f} pas mieux que l'achat-conservation ({b['sharpe']:.2f})")
    if m["pire_baisse"] <= b["pire_baisse"]: raisons.append("baisse pas moins profonde que l'achat-conservation")
    if a not in bh: raisons.append("ne survit pas à Benjamini-Hochberg")
    tout[a]["verdict"] = dict(atout=not raisons, raisons=raisons, p=float(pv[a]), bh=a in bh)
    print(f"{a:4s} : {'ATOUT' if not raisons else 'pas d atout'}" + ("" if not raisons else " (" + " ; ".join(raisons) + ")"))
json.dump(tout, open(SORTIE, "w"), separators=(",", ":"), allow_nan=False)
print("\n", SORTIE, round(SORTIE.stat().st_size / 1e6, 2), "Mo")
