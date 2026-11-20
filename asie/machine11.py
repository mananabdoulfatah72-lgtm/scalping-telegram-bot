#!/usr/bin/env python3
"""Machine 11 (asie/README.md) : les effets vus avant frais par les machines 9 et 10, joues seulement les jours de grand
mouvement (|signal| >= 1,5 fois sa moyenne des 60 jours precedents), aux frais d'aujourd'hui.
Usage : ASIE_DONNEES=<dossier HistData 5 min UTC> python3 asie/machine11.py exploration | coffre
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import machine7 as M7  # noqa: E402
import machine9 as M9  # noqa: E402
import machine10 as M10  # noqa: E402

DEBUT_HIST, FIN_EXPLO, DEBUT_COFFRE, FIN = "2011-12-01", M7.FIN_EXPLO, M7.DEBUT_COFFRE, M9.FIN
FOIS, FENETRE = 1.5, 60
M10.CONTRATS["jpxjpy"] = ("Nikkei 225 (MNK)", 7.0, lambda p: 0.5 * p)     # 2 ticks de 2,50 $ + 2 $ de commission supposes


def bases():
    fin_osaka = dict(entree=("TSE", -15), sortie=("TSE", 15))
    B = {s["marche"]: s for s in M10.strategies() if s["famille"] == "B"}
    T = {s["marche"]: s for s in M10.strategies() if s["famille"] == "T"}
    return [
        ("jpxjpy", dict(nom="N2 grand : Nikkei, ouverture de Tokyo contre un grand mouvement du S&P 500", famille="N2", marche="jpxjpy",
                        entree="09:00", sortie="09:30", signal_sp=True, sens="retour"), M9.jouer),
        ("jpxjpy", dict(nom="N1 grand : Nikkei, fin de seance d'Osaka dans le sens d'une grande journee", famille="N1", marche="jpxjpy",
                        **fin_osaka, signal=(("veille", ("TSE", 15)), ("TSE", -15)), sens="continuation"), M9.jouer),
        ("usatechidxusd", dict(T["usatechidxusd"], nom="T grand : MNQ, ouverture de Tokyo contre un grand mouvement du S&P 500"), M10.jouer),
        ("usa500idxusd", dict(T["usa500idxusd"], nom="T grand : MES, ouverture de Tokyo contre un grand mouvement du S&P 500"), M10.jouer),
        ("xagusd", dict(B["xagusd"], nom="B grand : argent (SIL), fin de seance dans le sens d'une grande journee"), M10.jouer),
        ("bcousd", dict(B["bcousd"], nom="B grand : petrole (CL), fin de seance dans le sens d'une grande journee"), M10.jouer),
        ("xauusd", dict(B["xauusd"], nom="B grand : or (MGC), fin de seance dans le sens d'une grande journee"), M10.jouer),
        ("eurusd", dict(B["eurusd"], nom="B grand : euro (6E), fin de seance dans le sens d'une grande journee"), M10.jouer),
    ]


def trades(code, s, jouer):
    M = M10.marche(code)
    d = jouer(s, M, DEBUT_HIST, FIN).reset_index(drop=True)
    a = d["signal"].abs()
    moy = a.shift(1).rolling(FENETRE, min_periods=40).mean()
    return M, d[(a >= FOIS * moy).fillna(False)].reset_index(drop=True)


def periode(d, debut, fin):
    return d[(d["jour"] >= pd.Timestamp(debut)) & (d["jour"] <= pd.Timestamp(fin))].reset_index(drop=True)


def exploration():
    res = []
    for code, s, jouer in bases():
        M, d = trades(code, s, jouer); dx = periode(d, M7.DEBUT, FIN_EXPLO)
        b = M10.bilan(dx, M); b.update(nom=s["nom"], part_des_jours=None)
        b["testable"] = b["jours"] >= 200
        b["p"] = M10.placebo(dx) if b["testable"] else None
        res.append(b)
        print(f"{s['nom']} : frais {b['frais_pb']} pb, brut {b['brut_moyen_pb']:+.2f} pb (t {b['t_brut']:+.2f}), net {b['net_moyen_pb']:+.2f} pb "
              f"(t {b['t']:+.2f}), p {b['p']}, {b['jours']} jours, sous-periodes {b['sous_periodes']}, {b['dollars_1_contrat']:+,.0f} $", flush=True)
    jug = [r for r in res if r["testable"]]
    bh = M7.benjamini_hochberg([r["p"] for r in jug])
    for r in res:
        r["bh"] = r["survivante"] = False
    for r, g in zip(jug, bh):
        r["bh"] = bool(g)
        r["survivante"] = bool(r["t"] >= 2 and r["p"] <= 0.05 and sum(x > 0 for x in r["sous_periodes"]) >= 2 and g)
    surv = [r["nom"] for r in res if r["survivante"]]
    (ICI / "exploration11.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    (ICI / "survivantes11.json").write_text(json.dumps(surv, indent=1, ensure_ascii=False))
    L = [f"Machine 11, exploration 2012 - 2022 : {len(res)} regles ; survivantes : {len(surv)}", "",
         "regle | frais (pb) | brut moyen (pb, t) | net moyen (pb) | t net | p | BH | sous-periodes (pb) | jours | $ pour 1 contrat | survivante"]
    for r in sorted(res, key=lambda x: -x["t"]):
        L.append(f"{r['nom']} | {r['frais_pb']} | {r['brut_moyen_pb']:+.2f} ({r['t_brut']:+.2f}) | {r['net_moyen_pb']:+.2f} | {r['t']:+.2f} | "
                 + (f"{r['p']:.3f}" if r["testable"] else "-") + f" | {'oui' if r['bh'] else 'non'} | "
                 + " / ".join(f"{x:+.1f}" for x in r["sous_periodes"]) + f" | {r['jours']} | {r['dollars_1_contrat']:+,.0f} | {'OUI' if r['survivante'] else ''}")
    (ICI / "exploration11.txt").write_text("\n".join(L) + "\n"); print("\n".join(L))


def coffre():
    surv = json.loads((ICI / "survivantes11.json").read_text())
    if not surv:
        print("Aucune survivante : le coffre 2023 - 2026 reste ferme."); return
    m = len(surv); seuil = float(norm.ppf(1 - 0.05 / m)); res = []
    L = [f"Machine 11, coffre 2023 -> {FIN} : {m} survivantes, seuil de Bonferroni t >= {seuil:.2f}, 3 annees positives sur 4", ""]
    for code, s, jouer in bases():
        if s["nom"] not in surv:
            continue
        M, d = trades(code, s, jouer); dv = periode(d, DEBUT_COFFRE, FIN); jj = M9.par_jour(dv)
        an = pd.DatetimeIndex(jj.index).year
        par_an = {y: round(float(jj["r"][an == y].sum()) * 1e4, 1) for y in (2023, 2024, 2025, 2026)}
        t = M7.t_stat(jj["r"].to_numpy()); passe = bool(t >= seuil and sum(v > 0 for v in par_an.values()) >= 3)
        b = M10.bilan(dv, M)
        res.append(dict(nom=s["nom"], t=round(t, 2), par_an=par_an, jours=len(jj), brut_moyen_pb=b["brut_moyen_pb"], net_moyen_pb=b["net_moyen_pb"],
                        dollars_1_contrat=b["dollars_1_contrat"], passe=passe))
        L.append(f"{s['nom']} | t {t:+.2f} | brut {b['brut_moyen_pb']:+.2f} pb, net {b['net_moyen_pb']:+.2f} pb | "
                 + " / ".join(f"{y} {v:+.1f}" for y, v in par_an.items()) + f" | {b['dollars_1_contrat']:+,.0f} $ | {'PASSE' if passe else 'echoue'}")
    (ICI / "coffre11.txt").write_text("\n".join(L) + "\n"); (ICI / "coffre11.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("\n".join(L))


if __name__ == "__main__":
    {"exploration": exploration, "coffre": coffre}[sys.argv[1]]()
