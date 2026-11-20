#!/usr/bin/env python3
"""Verification sur de vrais prix de futures (asie/README.md, fixee le 20 novembre 2026 avant le calcul).

Donnees : YAHOO = dossier des fichiers cinq_<code>.csv.gz et heure_<code>.csv.gz, copies de donnees_libres/yahoo/cinq/
et donnees_libres/yahoo/heure/ (branche claude/affectionate-turing-tnz0mn) ; ASIE_DONNEES = cotations HistData (machine 7).
Usage : YAHOO=<dossier> ASIE_DONNEES=<dossier> python3 asie/vrais_futures.py
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import machine7 as M7  # noqa: E402

Y = Path(os.environ["YAHOO"])
FUTURES = {"MGC": ("Or (MGC)", "xauusd", 1), "GC": ("Or (GC)", "xauusd", 1), "MNQ": ("Nasdaq (MNQ)", "usatechidxusd", 1),
           "MES": ("S&P 500 (MES)", "usa500idxusd", 1), "6E": ("Euro (6E)", "eurusd", 1), "6J": ("Yen (6J)", "usdjpy", -1),
           "6A": ("Dollar australien (6A)", "audusd", 1), "6B": ("Livre (6B)", "gbpusd", 1)}


def lire(fichier):
    d = pd.read_csv(fichier)
    d.index = pd.to_datetime(d["t"])
    return d[~d.index.duplicated(keep="last")]


def soirs(index):
    j = pd.DatetimeIndex(sorted(set(index.normalize())))
    return j[j.dayofweek < 4]


def fenetre(d, jours, h_e, h_s, j_s=0):
    """Rendement de l'ouverture de la barre h_e a l'ouverture de la barre h_s (jour + j_s), par soir."""
    out = {}
    for j in jours:
        a = j + pd.Timedelta(hours=int(h_e[:2]), minutes=int(h_e[3:]))
        b = j + pd.Timedelta(days=j_s, hours=int(h_s[:2]), minutes=int(h_s[3:]))
        if a in d.index and b in d.index:
            out[j] = d.at[b, "o"] / d.at[a, "o"] - 1
    return pd.Series(out, dtype=float)


def t_stat(x):
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else 0.0


def principal():
    R = {"test1_5_minutes": {}, "information_18h_19h": {}}
    L = ["Verification sur de vrais prix de futures (Yahoo, CME), heure de New York", "",
         "Test 1 : achat a 18 h 00, vente a 18 h 05, lundi - jeudi soir, 12 aout -> 21 octobre 2026 (avant frais)",
         "marche | soirs | moyenne futures (pb) | % en hausse | t | soirs communs avec HistData | futures sur ces soirs (pb) | HistData sur ces soirs (pb) | % en hausse HistData"]
    hist = {}
    for code, (nom, hd, sens) in FUTURES.items():
        d = lire(Y / f"cinq_{code}.csv.gz"); J = soirs(d.index)
        r = fenetre(d, J, "18:00", "18:05")
        if hd not in hist:
            hist[hd] = M7.Marche(hd)
        M = hist[hd]; jj = pd.DatetimeIndex(r.index)
        ie = M.indice(M7.utc(jj, M7.NY, "18:00")); i5 = M.indice(M7.utc(jj, M7.NY, "18:05"))
        okh = (ie >= 0) & (i5 >= 0)
        rh = pd.Series(np.where(okh, M.O[np.clip(i5, 0, M.n - 1)] / M.O[np.clip(ie, 0, M.n - 1)] - 1, np.nan), index=r.index) * sens
        comm = rh.dropna().index
        R["test1_5_minutes"][code] = dict(soirs=int(len(r)), moyenne_pb=round(float(r.mean()) * 1e4, 2), hausse=round(float((r > 0).mean()), 2),
                                          t=round(t_stat(r), 2), soirs_communs=int(len(comm)),
                                          futures_communs_pb=round(float(r[comm].mean()) * 1e4, 2) if len(comm) else None,
                                          histdata_communs_pb=round(float(rh[comm].mean()) * 1e4, 2) if len(comm) else None,
                                          hausse_histdata=round(float((rh[comm] > 0).mean()), 2) if len(comm) else None)
        x = R["test1_5_minutes"][code]
        L.append(f"{nom} | {x['soirs']} | {x['moyenne_pb']:+.2f} | {x['hausse']:.0%} | {x['t']:+.2f} | {x['soirs_communs']} | "
                 f"{x['futures_communs_pb']:+.2f} | {x['histdata_communs_pb']:+.2f} | {x['hausse_histdata']:.0%}")
    # test 2 : l'or du soir, barres d'une heure
    d = lire(Y / "heure_MGC.csv.gz"); J = soirs(d.index)
    r = fenetre(d, J, "18:00", "23:00")
    prix = pd.Series({j: d.at[j + pd.Timedelta(hours=18), "o"] for j in r.index})
    net = r - 4.0 / (10 * prix)
    t_reel = t_stat(net)
    placebos = []
    for h in range(24):
        if min(abs(h - 18), 24 - abs(h - 18)) <= 2:
            continue
        hs = (h + 5) % 24; js = 1 if h + 5 >= 24 else 0
        x = fenetre(d, J, f"{h:02d}:00", f"{hs:02d}:00", js)
        if len(x) > 50:
            px = x * 0 + prix.reindex(x.index).fillna(prix.mean())
            placebos.append((h, t_stat(x - 4.0 / (10 * px)), float(x.mean()) * 1e4))
    p = float(np.mean([t >= t_reel for _, t, _ in placebos]))
    moit = len(net) // 2
    R["test2_or_18h_23h"] = dict(soirs=int(len(net)), periode=[str(net.index[0].date()), str(net.index[-1].date())],
                                  brut_moyen_pb=round(float(r.mean()) * 1e4, 2), net_moyen_pb=round(float(net.mean()) * 1e4, 2),
                                  t=round(t_reel, 2), hausse=round(float((net > 0).mean()), 2),
                                  moities_pb=[round(float(net.iloc[:moit].sum()) * 1e4, 1), round(float(net.iloc[moit:].sum()) * 1e4, 1)],
                                  dollars_1_MGC=round(float((net * 10 * prix).sum())), p_placebo=round(p, 3),
                                  placebos=[(h, round(t, 2), round(m, 2)) for h, t, m in placebos],
                                  confirme=bool(t_reel >= 1.64 and p < 0.05))
    x = R["test2_or_18h_23h"]
    L += ["", f"Test 2 : or (MGC) achete a 18 h, vendu a 23 h, {x['periode'][0]} -> {x['periode'][1]}, frais 4 $ par aller-retour",
          f"{x['soirs']} soirs ; brut {x['brut_moyen_pb']:+.2f} pb, net {x['net_moyen_pb']:+.2f} pb par soir ; t {x['t']:+.2f} ; "
          f"{x['hausse']:.0%} de soirs gagnants ; moities {x['moities_pb'][0]:+.1f} / {x['moities_pb'][1]:+.1f} pb ; {x['dollars_1_MGC']:+,} $ pour 1 MGC",
          f"placebo : {p:.1%} des fenetres de 5 h commencees a d'autres heures font aussi bien ; t de ces fenetres : "
          + ", ".join(f"{h}h {t:+.2f}" for h, t, _ in x["placebos"]),
          f"=> {'CONFIRME' if x['confirme'] else 'NON CONFIRME'} sur de vrais prix"]
    L += ["", "Pour information : 18 h -> 19 h (barres d'une heure, avant frais)"]
    for code in ("MNQ", "MES", "MGC"):
        d = lire(Y / f"heure_{code}.csv.gz"); r = fenetre(d, soirs(d.index), "18:00", "19:00")
        R["information_18h_19h"][code] = dict(soirs=int(len(r)), moyenne_pb=round(float(r.mean()) * 1e4, 2), t=round(t_stat(r), 2))
        L.append(f"{FUTURES[code][0]} : {len(r)} soirs, {r.mean() * 1e4:+.2f} pb, t {t_stat(r):+.2f}")
    (ICI / "vrais_futures.json").write_text(json.dumps(R, indent=1, ensure_ascii=False))
    (ICI / "vrais_futures.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    principal()
