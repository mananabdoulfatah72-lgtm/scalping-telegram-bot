#!/usr/bin/env python3
"""Signaux d'order flow 1 a 6 sur les transactions du ES (regles dans README.md).

Lancer depuis ce dossier : python3 analyse.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

D = Path(__file__).parent / "donnees"
TICK = 0.25
COUT = 2.6                     # ticks par aller-retour (ecart traverse 2 fois + 1 $ par ordre sur MES)
S_JOUR = 23400                 # secondes de 9 h 30 a 16 h
DEBUT_DEC, FIN_DEC = 1, 384    # decisions a la fin des minutes 9 h 30 ... 15 h 53 (sortie avant 16 h)


def charger():
    s = pd.read_csv(D / "es_secondes.csv.gz", parse_dates=["t"]).set_index("t")
    # seances anormales (jour ferie, jour ou le contrat suivi n'est plus le plus echange) : volume < 50 % de la mediane
    vol = (s["achat"] + s["vente"]).groupby(s.index.normalize()).sum()
    exclus = vol[vol < 0.5 * vol.median()]
    if len(exclus):
        print("Seances ecartees (volume anormal) : " + ", ".join(f"{d.date()} ({v:,.0f} contrats)" for d, v in exclus.items()))
    jours = sorted(vol.index.difference(exclus.index))
    grilles = []
    for j in jours:
        idx = pd.date_range(j + pd.Timedelta(hours=9, minutes=30), periods=S_JOUR, freq="s")
        g = s.reindex(idx)
        g[["achat", "vente", "n"]] = g[["achat", "vente", "n"]].fillna(0)
        g[["prix", "bid", "ask", "bid_q", "ask_q"]] = g[["prix", "bid", "ask", "bid_q", "ask_q"]].ffill().bfill()
        grilles.append(g)
    f = pd.read_csv(D / "es_footprint.csv.gz", parse_dates=["m"])
    return jours, grilles, f


def signaux_jour(g, fp):
    """Signaux et mouvements futurs a la fin de chaque minute d'une journee."""
    mid = ((g["bid"] + g["ask"]) / 2).values
    achat, vente = g["achat"].values.reshape(390, 60).sum(1), g["vente"].values.reshape(390, 60).sum(1)
    b, a, bq, aq = g["bid"].values, g["ask"].values, g["bid_q"].values, g["ask_q"].values
    e = np.zeros(S_JOUR)
    e[1:] = ((b[1:] >= b[:-1]) * bq[1:] - (b[1:] <= b[:-1]) * bq[:-1]
             - (a[1:] <= a[:-1]) * aq[1:] + (a[1:] >= a[:-1]) * aq[:-1])
    ofi = e.reshape(390, 60).sum(1)
    fin = np.arange(390) * 60 + 59                         # derniere seconde de chaque minute
    tot = achat + vente
    delta1 = np.where(tot > 0, (achat - vente) / np.maximum(tot, 1), 0)
    a15 = pd.Series(achat).rolling(15, min_periods=15).sum().values
    v15 = pd.Series(vente).rolling(15, min_periods=15).sum().values
    cvd15 = (a15 - v15) / np.maximum(a15 + v15, 1)
    q = (bq[fin] - aq[fin]) / np.maximum(bq[fin] + aq[fin], 1)
    ofi_z = ofi / pd.Series(ofi).rolling(60, min_periods=30).std().shift(1).values
    haut15 = pd.Series(mid).rolling(900, min_periods=900).max().values[fin]
    bas15 = pd.Series(mid).rolling(900, min_periods=900).min().values[fin]
    absorption = np.where((mid[fin] >= haut15) & (a15 - v15 < 0), -1, np.where((mid[fin] <= bas15) & (a15 - v15 > 0), 1, 0))
    # footprint : desequilibres empiles (300 %, 3 niveaux, au moins 20 contrats)
    empile = np.zeros(390)
    minutes = g.index[fin].floor("min")
    for k, m in enumerate(minutes):
        x = fp.get(m)
        if x is None or len(x) < 3:
            continue
        px = np.round(x["prix"].values / TICK).astype(int)
        acht = dict(zip(px, x["achat"].values))
        vnt = dict(zip(px, x["vente"].values))
        prix = sorted(px)
        acheteur = [acht.get(p, 0) >= 20 and acht.get(p, 0) >= 3 * vnt.get(p - 1, 0) for p in prix]
        vendeur = [vnt.get(p, 0) >= 20 and vnt.get(p, 0) >= 3 * acht.get(p + 1, 0) for p in prix]

        def pile(bools):
            meilleur = cour = 0
            for i, v in enumerate(bools):
                cour = cour + 1 if v and (i == 0 or prix[i] == prix[i - 1] + 1) else (1 if v else 0)
                meilleur = max(meilleur, cour)
            return meilleur
        ach, ven = pile(acheteur) >= 3, pile(vendeur) >= 3
        empile[k] = 1 if ach and not ven else (-1 if ven and not ach else 0)
    futur = {h: np.full(390, np.nan) for h in (1, 5)}
    for h in (1, 5):
        ok = fin + 60 * h < S_JOUR
        futur[h][ok] = (mid[fin[ok] + 60 * h] - mid[fin[ok]]) / TICK
    return pd.DataFrame({"delta1": delta1, "cvd15": cvd15, "carnet": q, "ofi": ofi_z, "empile": empile,
                         "absorption": absorption, "f1": futur[1], "f5": futur[5]})


REGLES = {  # signal -> fonction qui donne le sens (-1, 0, +1)
    "1 Delta 1 minute": lambda d: np.where(np.abs(d["delta1"]) >= 0.3, np.sign(d["delta1"]), 0),
    "2 CVD 15 minutes": lambda d: np.where(np.abs(d["cvd15"]) >= 0.15, np.sign(d["cvd15"]), 0),
    "3 Desequilibre du carnet": lambda d: np.where(np.abs(d["carnet"]) >= 0.5, np.sign(d["carnet"]), 0),
    "4 OFI (Cont et al.)": lambda d: np.where(np.abs(d["ofi"]) >= 2, np.sign(d["ofi"]), 0),
    "5 Footprint empile": lambda d: d["empile"].values,
    "6 Absorption": lambda d: d["absorption"].values,
}


def simuler(jours_df, sens_f, h):
    """Trades sans chevauchement : entree a la fin de la minute du signal, sortie h minutes apres."""
    gains = []
    for d in jours_df:
        sens = np.nan_to_num(np.asarray(sens_f(d), float))
        fut = d[f"f{h}"].values
        k = DEBUT_DEC
        while k <= FIN_DEC:
            if sens[k] != 0 and not np.isnan(fut[k]):
                gains.append(sens[k] * fut[k])
                k += h
            else:
                k += 1
    return np.array(gains)


def main():
    jours, grilles, f = charger()
    fp = {m: x for m, x in f.groupby("m")}
    jd = [signaux_jour(g, fp) for g in grilles]
    tout = pd.concat(jd, ignore_index=True)
    print(f"{len(jours)} seances ES, du {jours[0].date()} au {jours[-1].date()} ; frais {COUT} ticks par aller-retour\n")
    print("Borne haute : mouvement moyen (ticks) du decile le plus favorable, et correlation de rang")
    sortie = {"seances": len(jours), "debut": str(jours[0].date()), "fin": str(jours[-1].date()), "deciles": {}, "signaux": {}}
    for s in ["delta1", "cvd15", "carnet", "ofi"]:
        x = tout[[s, "f1", "f5"]].dropna()
        dec = pd.qcut(x[s].rank(method="first"), 10, labels=False)
        lig = {}
        for h in (1, 5):
            m = x.groupby(dec)[f"f{h}"].mean()
            ic = spearmanr(x[s], x[f"f{h}"]).correlation
            meilleur = max(m.iloc[-1], -m.iloc[0])
            lig[h] = {"haut": float(m.iloc[-1]), "bas": float(m.iloc[0]), "meilleur": float(meilleur), "ic": float(ic)}
            print(f"  {s:7s} {h} min : decile haut {m.iloc[-1]:+.2f} | decile bas {m.iloc[0]:+.2f} | meilleur {meilleur:.2f} tick"
                  f" (frais {COUT}) | correlation {ic:+.3f}")
        sortie["deciles"][s] = lig
    print("\nStrategies (regles fixees), trades sans chevauchement :")
    rng = np.random.default_rng(0)
    for nom, regle in REGLES.items():
        for h in (1, 5):
            g = simuler(jd, regle, h)
            if len(g) < 30:
                print(f"  {nom:26s} {h} min : {len(g)} trades, trop peu")
                continue
            net = g - COUT
            t = net.mean() / net.std() * np.sqrt(len(net))
            plac = np.array([(rng.choice([-1.0, 1.0], len(g)) * g).mean() - COUT for _ in range(2000)])
            cent = float(np.mean(plac < net.mean()))
            dollars = net.mean() * TICK * 5 * len(g) / len(jours)          # $ par jour, 1 MES
            ok = net.mean() > 0 and t >= 2 and cent >= 0.95
            print(f"  {nom:26s} {h} min : {len(g):5d} trades | brut {g.mean():+.2f} | net {net.mean():+.2f} ticks (t {t:+.2f})"
                  f" | {dollars:+.0f} $/jour par MES | placebo battu {cent:.0%} | {'EXPLOITABLE' if ok else 'non'}")
            sortie["signaux"][f"{nom} {h} min"] = {"trades": int(len(g)), "brut": float(g.mean()), "net": float(net.mean()),
                                                   "t": float(t), "dollars_jour": float(dollars), "placebo": cent,
                                                   "exploitable": bool(ok)}
    Path(__file__).with_name("resultats.json").write_text(json.dumps(sortie, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
