#!/usr/bin/env python3
"""Filtre H1, version Rithmic (README.md) : transactions du NQ exportees de Quantower (strategie « Export transactions
NQ »), fichiers transactions_*.csv dans filtre_h1/donnees_rithmic/. Valide la source contre Databento (orderflow/) sur
les seances communes, puis teste le filtre sur les trades de zone hors du 1er avril - 2 octobre 2026. Decision unique a
150 trades mesures ; avant, point d'etape descriptif. Ecrit resultat_rithmic.txt. Lancer depuis ce dossier."""
import glob
import io
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
R0 = ICI.parent
sys.path.insert(0, str(R0 / "protection"))
import os  # noqa: E402
os.environ.setdefault("ROBOT_DEBUT_RSI2", "2000-01-01")
os.environ.setdefault("ROBOT_DOSSIER", str(R0 / "protection" / "_robot"))
import robot_main as RB  # noqa: E402

EXCLU = ("2026-04-01", "2026-10-02")
SEUIL_TRADES, T_MIN, SANS_COTE_MAX, ACCORD_MIN = 150, 2.0, 0.10, 0.95


def minutes_nq():
    """Barres d'une minute du backtest (recherche) completees par celles du robot (main) apres leur fin."""
    d = pd.read_csv(R0 / "intraday/donnees/nasdaq100_1min.csv.gz")
    try:
        brut = subprocess.run(["git", "-C", str(R0), "show", "origin/main:zone/robot/nq_1min.csv.gz"], capture_output=True, check=True).stdout
        r = pd.read_csv(io.BytesIO(brut), compression="gzip")
        d = pd.concat([d, r[r["t"] > d["t"].iloc[-1]]], ignore_index=True)
    except Exception as e:
        print(f"(barres du robot indisponibles : {e} ; seulement les barres de la recherche)")
    return d


def trades_zone(d):
    jours, O, H, L, C, P, V, ech = RB.tableaux(d)
    _, trades, _ = RB.zone_de_bruit(jours, O, H, L, C, P, V, ech)
    out = []
    for j, liste in trades.items():
        for texte in liste:
            x = RB.MOTIF_ZONE.match(texte)
            if x:
                m = int(x.group(2)) * 60 + int(x.group(3)) - 570
                sens = 1 if x.group(1) == "achat" else -1
                e, s = float(x.group(4).replace(",", "")), float(x.group(7).replace(",", ""))
                out.append((str(pd.Timestamp(j).date()), m, sens, sens * (s - e) - RB.COUT))
    return pd.DataFrame(out, columns=["jour", "minute", "sens", "points"])


def welch(a, b):
    return float((a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))) if len(a) > 1 and len(b) > 1 else float("nan")


def main():
    fichiers = sorted(glob.glob(str(ICI / "donnees_rithmic" / "transactions_*.csv")))
    if not fichiers:
        raise SystemExit("aucun fichier dans filtre_h1/donnees_rithmic/ (exporter depuis Quantower, voir README.md)")
    x = pd.concat([pd.read_csv(f) for f in fichiers], ignore_index=True)
    x = x.groupby(["jour", "minute"], as_index=False)[["achats", "ventes", "sans_cote"]].sum()
    par_jour = {j: g.set_index("minute") for j, g in x.groupby("jour")}
    z = trades_zone(minutes_nq())
    z = z[z["jour"].isin(par_jour)].reset_index(drop=True)
    delta, sans = [], []
    for r in z.itertuples():
        g = par_jour[r.jour]
        w = g.loc[(g.index >= r.minute - 29) & (g.index <= r.minute)]
        tot = w[["achats", "ventes", "sans_cote"]].to_numpy().sum()
        delta.append(float(w["achats"].sum() - w["ventes"].sum()))
        sans.append(float(w["sans_cote"].sum() / tot) if tot > 0 else 1.0)
    z["delta"], z["sans_cote"] = delta, sans
    L = [f"Filtre H1, version Rithmic : {len(fichiers)} fichier(s), {len(par_jour)} seances exportees"
         f" ({min(par_jour)} - {max(par_jour)}), {len(z)} trades de zone sur ces seances", ""]
    # 1. validation contre Databento sur les seances communes
    of = pd.read_csv(R0 / "orderflow" / "zone_avril_septembre_2026.csv")
    v = z.merge(of[["jour", "minute", "sens", "delta30"]], on=["jour", "minute", "sens"])
    v = v[(v["delta"] != 0) & (v["delta30"] != 0)]
    if len(v):
        accord = float((np.sign(v["delta"]) == np.sign(v["delta30"])).mean())
        source_ok = accord >= ACCORD_MIN
        L.append(f"Validation contre Databento : meme signe du delta 30 min sur {accord:.1%} de {len(v)} trades communs"
                 f" (seuil {ACCORD_MIN:.0%}) -> source {'ACCEPTEE' if source_ok else 'REFUSEE : test descriptif seulement'}")
    else:
        source_ok = None
        L.append("Validation contre Databento : aucune seance commune exportee (exporter aussi juin - septembre 2026,"
                 " contrats NQU6 ou NQM6). Tant qu'elle manque, le test reste descriptif.")
    # 2. test hors de la periode deja utilisee
    t = z[(z["jour"] < EXCLU[0]) | (z["jour"] > EXCLU[1])]
    t = t[t["sans_cote"] <= SANS_COTE_MAX]
    garde = np.sign(t["delta"]) == t["sens"]
    a, b = t["points"][garde], t["points"][~garde]
    tw = welch(a, b)
    L += ["", f"Test hors du {EXCLU[0]} - {EXCLU[1]} : {len(t)} trades mesures"
          f" ({int((z['sans_cote'] > SANS_COTE_MAX).sum())} fenetres exclues, plus de 10 % sans cote)"]
    if len(t):
        L += [f"- gardes : {len(a)} trades, {a.mean() if len(a) else float('nan'):+.2f} pt ; ecartes : {len(b)},"
              f" {b.mean() if len(b) else float('nan'):+.2f} pt ; t {tw:+.2f}",
              f"- zone seule {t['points'].sum():+,.0f} pt ({2 * t['points'].sum():+,.0f} $ pour 1 MNQ) ;"
              f" zone filtree {a.sum():+,.0f} pt ({2 * a.sum():+,.0f} $)"]
    if len(t) >= SEUIL_TRADES and source_ok:
        ok = tw >= T_MIN and a.sum() > t["points"].sum()
        L.append(f"-> DECISION ({len(t)} trades >= {SEUIL_TRADES}) : filtre {'CONFIRME' if ok else 'NON CONFIRME'}")
    else:
        L.append(f"-> point d'etape, pas de decision ({len(t)} trades sur {SEUIL_TRADES} ;"
                 f" source {'acceptee' if source_ok else 'pas encore validee' if source_ok is None else 'refusee'})")
    (ICI / "resultat_rithmic.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
