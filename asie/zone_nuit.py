#!/usr/bin/env python3
"""Machine 8 (asie/README.md) : la zone de bruit pendant la session asiatique, 18 h 00 -> 3 h 00 (New York).
Usage : ASIE_DONNEES=<dossier HistData> python3 asie/zone_nuit.py exploration | coffre"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import machine7 as M7  # noqa: E402

MARCHES = ["usatechidxusd", "usa500idxusd", "xauusd"]
LARGEURS = [1.0, 1.4]
JOURS, NC = 14, 17                       # 14 nuits de moyenne ; 17 controles (18 h 30 -> 2 h 30)
FIN_NUIT = 108                           # 3 h 00 = 18 h 00 + 108 barres de 5 minutes


def nuits(M, debut, fin):
    """Pour chaque soir (lundi - jeudi) : indice de la barre de 18 h 00, O, C americaine, prix aux controles, prix moyen."""
    j = M7.soirs(pd.Timestamp(debut) - pd.Timedelta(days=40), fin)
    i0 = M.indice(M7.utc(j, M7.NY, "18:00"))
    i16 = M.indice(M7.utc(j, M7.NY, "16:00"))
    out = []
    for jour, a, b in zip(j, i0, i16):
        if a < 0 or a + FIN_NUIT >= M.n or not np.isfinite(M.O[a]):
            continue
        ctrl = np.array([M.C[a + 6 * k - 1] for k in range(1, NC + 1)])
        if not np.isfinite(ctrl).all() or not np.isfinite(M.O[a + FIN_NUIT]):
            continue
        c_us = np.nan
        if b >= 0:
            fen = M.C[b:min(b + 12, a)]
            fen = fen[np.isfinite(fen)]
            c_us = fen[-1] if len(fen) else np.nan
        cl = M.C[a:a + 6 * NC]
        moy = np.array([np.nanmean(cl[:6 * k]) for k in range(1, NC + 1)])
        out.append(dict(jour=jour, O=M.O[a], C=c_us, ctrl=ctrl, moy=moy, sortie=M.O[a + FIN_NUIT]))
    return out


def jouer(M, debut, fin, largeur):
    N = nuits(M, debut, fin)
    trades = []
    for n in range(JOURS, len(N)):
        x = N[n]
        if x["jour"] < pd.Timestamp(debut):
            continue
        bruit = np.mean([np.abs(N[q]["ctrl"] / N[q]["O"] - 1) for q in range(n - JOURS, n)], axis=0)
        ref_h = max(x["O"], x["C"]) if np.isfinite(x["C"]) else x["O"]
        ref_b = min(x["O"], x["C"]) if np.isfinite(x["C"]) else x["O"]
        haut, bas = ref_h * (1 + largeur * bruit), ref_b * (1 - largeur * bruit)
        pos, e = 0, 0.0
        for k in range(NC):
            p = x["ctrl"][k]
            if pos > 0 and p <= max(haut[k], x["moy"][k]):
                trades.append((x["jour"], p / e - 1, e)); pos = 0
            elif pos < 0 and p >= min(bas[k], x["moy"][k]):
                trades.append((x["jour"], e / p - 1 if False else -(p / e - 1), e)); pos = 0
            if pos == 0 and k < NC - 1:
                if p > haut[k]:
                    pos, e = 1, p
                elif p < bas[k]:
                    pos, e = -1, p
        if pos != 0:
            trades.append((x["jour"], pos * (x["sortie"] / e - 1), e))
    d = pd.DataFrame(trades, columns=["jour", "brut", "e"])
    if len(d):
        d["r"] = d["brut"] - np.array([M.cout(v) for v in d["e"]])
    else:
        d["r"] = []
    return d


def par_nuit(d):
    return d.groupby("jour")[["brut", "r"]].sum() if len(d) else pd.DataFrame(columns=["brut", "r"])


def exploration():
    res = []
    for c in MARCHES:
        M = M7.Marche(c)
        for lg in LARGEURS:
            d = jouer(M, M7.DEBUT, M7.FIN_EXPLO, lg); j = par_nuit(d)
            t = M7.t_stat(j["r"]); an = pd.DatetimeIndex(j.index).year
            rng = np.random.default_rng(M7.GRAINE); brut = d["brut"].to_numpy(); cout = brut - d["r"].to_numpy()
            nuits_id = pd.factorize(d["jour"])[0]
            ts = [M7.t_stat(np.bincount(nuits_id, rng.choice([-1.0, 1.0], len(brut)) * brut - cout)) for _ in range(M7.N_SIGNES)]
            p = float(np.mean(np.array(ts) >= t))
            sous = [round(float(j["r"][(an >= a) & (an <= b)].sum()) * 1e4, 1) for a, b in M7.SOUS]
            dol = float((d["r"] * np.array([M.notionnel(v) for v in d["e"]])).sum())
            r = dict(nom=f"zone de nuit {c} largeur {lg}", marche=c, largeur=lg, t=round(t, 2), p=p, trades=int(len(d)),
                     nuits=int(len(j)), brut_moyen_pb=round(float(j["brut"].mean()) * 1e4, 2), net_moyen_pb=round(float(j["r"].mean()) * 1e4, 2),
                     sous_periodes=sous, dollars_1_contrat=round(dol))
            res.append(r); print(r, flush=True)
    bh = M7.benjamini_hochberg([r["p"] for r in res])
    for r, g in zip(res, bh):
        r["bh"] = bool(g)
        r["survivante"] = bool(r["t"] >= 2 and r["p"] <= 0.05 and sum(x > 0 for x in r["sous_periodes"]) >= 2 and g)
    L = ["Machine 8, exploration 2012 - 2022 : la zone de bruit de 18 h a 3 h (New York)", "",
         "strategie | t | brut moyen par nuit (pb) | net moyen (pb) | p placebo | BH | sous-periodes (pb) | nuits avec trade | trades | $ pour 1 contrat | survivante"]
    for r in res:
        L.append(f"{r['nom']} | {r['t']:+.2f} | {r['brut_moyen_pb']:+.2f} | {r['net_moyen_pb']:+.2f} | {r['p']:.3f} | {'oui' if r['bh'] else 'non'} | "
                 + " / ".join(f"{x:+.1f}" for x in r["sous_periodes"]) + f" | {r['nuits']} | {r['trades']} | {r['dollars_1_contrat']:+,} | {'OUI' if r['survivante'] else ''}")
    (ICI / "zone_nuit_exploration.txt").write_text("\n".join(L) + "\n")
    (ICI / "zone_nuit_exploration.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("\n".join(L))


def coffre():
    res = json.loads((ICI / "zone_nuit_exploration.json").read_text())
    surv = [r for r in res if r["survivante"]]
    if not surv:
        print("Aucune survivante : le coffre 2023 - 2026 reste ferme."); return
    seuil = float(norm.ppf(1 - 0.05 / len(surv))); L = [f"Machine 8, coffre 2023 -> {M7.FIN} : seuil t {seuil:.2f}"]
    for r in surv:
        M = M7.Marche(r["marche"]); j = par_nuit(jouer(M, M7.DEBUT_COFFRE, M7.FIN, r["largeur"]))
        an = pd.DatetimeIndex(j.index).year; par_an = {y: round(float(j["r"][an == y].sum()) * 1e4, 1) for y in (2023, 2024, 2025, 2026)}
        t = M7.t_stat(j["r"]); ok = t >= seuil and sum(v > 0 for v in par_an.values()) >= 3
        L.append(f"{r['nom']} | t {t:+.2f} | {par_an} | {'PASSE' if ok else 'echoue'}")
    (ICI / "zone_nuit_coffre.txt").write_text("\n".join(L) + "\n"); print("\n".join(L))


if __name__ == "__main__":
    {"exploration": exploration, "coffre": coffre}[sys.argv[1]]()
