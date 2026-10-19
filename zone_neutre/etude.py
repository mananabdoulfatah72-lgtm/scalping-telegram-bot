#!/usr/bin/env python3
"""Variante « zone neutre » du filtre delta (README.md) : garde aussi les trades dont le delta des 30 minutes est presque
nul (|delta| < seuil x volume). Donnees : Databento (avril - 2 octobre 2026) et export Rithmic (apres le 2 octobre).
Ecrit resultats.txt. Lancer depuis la racine du depot."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

R0 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R0 / "filtre_h1"))
import test_rithmic as TR  # noqa: E402

SEUIL, AUTRES = 0.01, (0.005, 0.02, 0.03)
FIN_DATABENTO = "2026-10-02"


def trades_databento():
    z = pd.read_csv(R0 / "orderflow" / "zone_avril_septembre_2026.csv")
    return z.rename(columns={"delta30": "frac"})[["jour", "minute", "sens", "points", "frac"]].assign(periode="databento")


def trades_rithmic():
    x = pd.read_csv(R0 / "filtre_h1" / "donnees_rithmic" / "transactions_NQZ6_rithmic.csv")
    x = x[x["jour"] > FIN_DATABENTO]
    pj = {j: g.set_index("minute") for j, g in x.groupby("jour")}
    z = TR.trades_zone(TR.minutes_nq())
    z = z[z["jour"].isin(pj)].reset_index(drop=True)
    frac = []
    for r in z.itertuples():
        w = pj[r.jour].loc[lambda g: (g.index >= r.minute - 29) & (g.index <= r.minute)]
        a, v = w["achats"].sum(), w["ventes"].sum()
        frac.append((a - v) / (a + v) if a + v > 0 else 0.0)
    return z.assign(frac=frac, periode="rithmic")[["jour", "minute", "sens", "points", "frac", "periode"]]


def garde(z, seuil):
    h1 = np.sign(z["frac"]) == z["sens"]
    return h1 if seuil is None else h1 | (z["frac"].abs() < seuil)


def ligne(z, seuil, nom):
    g = garde(z, seuil)
    a, b = z["points"][g], z["points"][~g]
    return (f"  {nom:<22} gardes {len(a):3d} ({a.mean() if len(a) else float('nan'):+7.2f} pt)  ecartes {len(b):3d}"
            f" ({b.mean() if len(b) else float('nan'):+7.2f} pt)  t {TR.welch(a, b):+5.2f}  total {a.sum():+8.1f} pt")


def main():
    z = pd.concat([trades_databento(), trades_rithmic()], ignore_index=True)
    L = [f"Zone neutre (seuil {SEUIL:.0%}) : {len(z)} trades de zone mesures"
         f" ({(z.periode == 'databento').sum()} Databento avril - {FIN_DATABENTO}, {(z.periode == 'rithmic').sum()} Rithmic apres)", ""]
    for per, zz in [("databento", z[z.periode == "databento"]), ("rithmic", z[z.periode == "rithmic"]), ("tout", z)]:
        L.append(f"{per} : zone sans filtre {zz['points'].sum():+.1f} pt sur {len(zz)} trades")
        L.append(ligne(zz, None, "filtre H1"))
        L.append(ligne(zz, SEUIL, f"variante N1 ({SEUIL:.1%})"))
        for s in AUTRES:
            L.append(ligne(zz, s, f"descriptif ({s:.1%})"))
        L.append("")
    rep = z[(np.sign(z["frac"]) != z["sens"]) & (z["frac"].abs() < SEUIL)]
    L.append(f"Trades repeches par N1 (ecartes par H1, |delta| < {SEUIL:.0%}) : {len(rep)}")
    for r in rep.itertuples():
        L.append(f"  {r.jour} minute {r.minute:3d} {'achat' if r.sens > 0 else 'vente'} delta {r.frac:+.3%} -> {r.points:+.2f} pt ({r.periode})")
    ec = z[np.sign(z["frac"]) != z["sens"]]
    fort, faible = ec[ec["frac"].abs() >= SEUIL], ec[ec["frac"].abs() < SEUIL]
    L += ["", f"Ecartes par H1 : {len(ec)} ; delta fort (>= {SEUIL:.0%}) {len(fort)} trades, {fort['points'].mean():+.2f} pt en moyenne ;"
          f" delta faible {len(faible)} trades, {faible['points'].mean() if len(faible) else float('nan'):+.2f} pt"]
    # decision fixee a l'avance
    n1d = garde(z[z.periode == "databento"], SEUIL); h1d = garde(z[z.periode == "databento"], None)
    n1r = garde(z[z.periode == "rithmic"], SEUIL); h1r = garde(z[z.periode == "rithmic"], None)
    zd, zr = z[z.periode == "databento"]["points"], z[z.periode == "rithmic"]["points"]
    ok3 = zd[n1d].sum() >= zd[h1d].sum() and zr[n1r].sum() >= zr[h1r].sum()
    if len(rep) < 10:
        L.append(f"-> PAS DE DECISION : {len(rep)} trades repeches sur 10 necessaires ; le bot garde le filtre H1")
    else:
        ok = rep["points"].mean() > 0 and ok3
        L.append(f"-> DECISION : variante N1 {'ADOPTEE' if ok else 'REJETEE'} (moyenne des repeches {rep['points'].mean():+.2f} pt,"
                 f" N1 >= H1 sur les deux periodes : {'oui' if ok3 else 'non'})")
    (Path(__file__).resolve().parent / "resultats.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
