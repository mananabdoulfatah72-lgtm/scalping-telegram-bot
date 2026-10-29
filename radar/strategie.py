#!/usr/bin/env python3
"""Radar, constitution de la strategie (radar/README.md, protocole du 29 octobre 2026) : joue ensemble, 1 MNQ chacune,
les regles du scan et les modeles qui ont passe le coffre, les mesure sur les trois periodes et sur des challenges
Bulenox 50K simules (objectif + 3 000 $, perte maximale suivie en fin de journee 2 500 $, limite du jour 1 100 $), de
1 a 4 MNQ, avec un depart a chaque seance du coffre. Ecrit radar/resultats/STRATEGIE.md et strategie.json (regles
figees pour le suivi en direct). Si rien n'a passe le coffre, l'ecrit aussi.

Lancer : RADAR_CALCUL=<dossier> python3 radar/strategie.py"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import scan as SC

ICI = Path(__file__).resolve().parent
RESULTATS = ICI / "resultats"
DEPART, OBJECTIF, PERTE_MAX, LIMITE_JOUR = 50_000.0, 3_000.0, 2_500.0, 1_100.0


def regles_scan(d):
    f = RESULTATS / "scan_survivantes_coffre.csv"
    if not f.exists():
        return []
    t = pd.read_csv(f)
    t = t[t["passe"].astype(str).str.lower() == "true"]
    out = []
    for _, r in t.iterrows():
        ie = list(d["entrees"]).index(int(r["e"]))
        I, var, desc = SC.conditions(d["cube"][ie], d["B"], SC.periodes(d["jours"])["E"])
        pris = (I[:, int(r["ka"])] > 0) & (I[:, int(r["kb"])] > 0)
        noms = list(d["noms"]) + list(d["binaires"])
        conds = []
        for k in sorted({int(r["ka"]), int(r["kb"])}):
            fvar, b, q = desc[k]
            conds.append({"variable": noms[fvar], "tranche": int(b),
                          "seuils": None if q is None else [float(x) for x in q]})
        out.append({"source": "scan", "regle": r["regle"], "e": int(r["e"]), "ih": int(r["ih"]),
                    "sens": np.where(pris, float(r["sens"]), 0.0), "conditions": conds})
    return out


def modeles_ia(d):
    f = RESULTATS / "ia_coffre.txt"
    if not f.exists():
        return []
    passes = [l for l in f.read_text().splitlines() if l.strip().startswith("PASSE")]
    if not passes:
        return []
    z = np.load(SC.CALCUL / "ia_predictions.npz")
    T = pd.read_csv(RESULTATS / "ia_modeles.csv")
    out = []
    for l in passes:
        _, modele, e, _, H = l.split()[:5]
        r = T[(T["modele"] == modele) & (T["e"] == int(e)) & (T["H"] == int(H))].iloc[0]
        p, dl = z["P"][int(r["im"]), int(r["ih"])], z["D"][int(r["im"]), int(r["ih"])]
        sens = np.where(p > 0.5 + dl, 1.0, np.where(p < 0.5 - dl, -1.0, 0.0))
        out.append({"source": "ia", "regle": f"{modele} {e} min {H}", "e": int(e), "ih": int(r["ih"]),
                    "sens": np.nan_to_num(sens), "conditions": []})
    return out


def pires(d, regle):
    """Gain net de la seance et pire moment du trade (au plus bas des minutes), en $ par MNQ."""
    e, H = d["cles"][regle["ih"]]
    g = d["gains"][regle["ih"]]
    s = regle["sens"]
    net = np.where((s != 0) & np.isfinite(g), s * g - SC.FRAIS, 0.0)
    return net


def challenge(jours_pnl, n_mnq):
    """Pour chaque depart : 1 valide, -1 perdu, 0 pas fini a la fin des donnees ; et nombre de seances."""
    x = np.asarray(jours_pnl) * n_mnq
    x = np.maximum(x, -LIMITE_JOUR)
    res, duree = [], []
    for s0 in range(len(x)):
        solde, haut, r = DEPART, DEPART, 0
        for k in range(s0, len(x)):
            solde += x[k]
            haut = max(haut, solde)
            plancher = min(haut - PERTE_MAX, DEPART + 100)
            if solde >= DEPART + OBJECTIF:
                r = 1
                break
            if solde <= plancher:
                r = -1
                break
        res.append(r)
        duree.append(k - s0 + 1)
    return np.array(res), np.array(duree)


def main():
    d = SC.charger()
    P = SC.periodes(d["jours"])
    regles = regles_scan(d) + modeles_ia(d)
    RESULTATS.mkdir(parents=True, exist_ok=True)
    L = ["# Stratégie du radar", ""]
    if not regles:
        L += ["**Aucune règle ni aucun modèle n'a passé le coffre.** Le protocole fixé d'avance ne permet pas de "
              "constituer une stratégie. Les meilleures survivantes de la confirmation sont suivies en direct (sans "
              "argent) par `flux/veille.py`."]
        (RESULTATS / "STRATEGIE.md").write_text("\n".join(L) + "\n")
        (RESULTATS / "strategie.json").write_text(json.dumps({"regles": []}, indent=1) + "\n")
        print("\n".join(L))
        return
    pnl = np.zeros(len(d["jours"]))
    for r in regles:
        pnl += pires(d, r)
    ok = d["ok"].astype(bool)
    L += [f"{len(regles)} règle(s), 1 MNQ chacune :", ""] + [f"- {r['regle']}" for r in regles] + [""]
    L += ["| Période | Séances | Séances jouées | Total | Moyenne par séance jouée | t |", "|---|---|---|---|---|---|"]
    for nom, m in (("Exploration 2011-2018", P["E"]), ("Confirmation 2019-2022", P["C"]), ("Coffre 2023-2026", P["T"])):
        x = pnl[m & ok]
        jouees = x[x != 0]
        n, moy, t = SC.t_serie(jouees)
        L.append(f"| {nom} | {len(x)} | {n} | {x.sum():+,.0f} $ | {moy:+,.1f} $ | {t:.2f} |")
    L += ["", "Challenges Bulenox 50K simulés, un départ à chaque séance du coffre :", "",
          "| MNQ par règle | Validés | Perdus | Pas finis | Séances pour valider (médiane) |", "|---|---|---|---|---|"]
    x = pnl[P["T"] & ok]
    for n in (1, 2, 3, 4):
        r, du = challenge(x, n)
        L.append(f"| {n} | {np.mean(r == 1):.0%} | {np.mean(r == -1):.0%} | {np.mean(r == 0):.0%} | "
                 f"{np.median(du[r == 1]) if (r == 1).any() else float('nan'):.0f} |")
    (RESULTATS / "STRATEGIE.md").write_text("\n".join(L) + "\n")
    (RESULTATS / "strategie.json").write_text(json.dumps(
        {"regles": [{k: v for k, v in r.items() if k != "sens"} for r in regles]}, indent=1, default=str) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
