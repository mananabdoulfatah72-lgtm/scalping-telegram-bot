#!/usr/bin/env python3
"""Ouverture du coffre 2023 - septembre 2026 de la machine n°3, une seule fois (README.md, regles v2 et v2.1).

1. Barriere du bruit, par marche : meilleur Sharpe de validation parmi les strategies des 8 graines de bruit avec une
   fitness >= 0,5 et la porte passee.
2. Finalistes : pour chaque marche, parmi les strategies des 8 graines reelles avec une fitness >= 0,5 et la porte
   passee, celle au meilleur Sharpe de validation ; gardee seulement si elle bat la barriere du bruit de son marche.
3. Coffre : chaque finaliste gardé rejoue 2016-2026 ; il passe si t >= 2,6 sur 2023-2026 et au moins 3 annees
   positives sur 4.
4. Mesures descriptives sur chaque periode (ne servent pas a choisir) : Sharpe, perte maximale, jours gagnants, gain
   moyen et perte moyenne par trade.

Ecrit resultats_coffre3.txt et resultats_coffre3.json. Lancer depuis ce dossier, apres lancer3.py : python3 coffre3.py
"""
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

import genetique3 as G
import moteur3 as M

ICI = Path(__file__).resolve().parent
GENES = ["famille", "inverse", "marche", "L", "Z", "sens", "stop", "objectif", "debut", "duree", "filtre"]
PERIODES = {"entrainement 2016-2019": ("2016-01-01", "2019-12-31"), "validation 2020-2022": ("2020-01-01", "2022-12-31"),
            "coffre 2023-2026": ("2023-01-01", "2026-12-31")}
T_MIN, ANNEES_MIN, CAPITAL = 2.6, 3, 50_000.0
SENS = ["achat et vente", "achat seul", "vente seule"]
FILTRES = ["tous les jours", "jours agites", "jours calmes"]


def runs(nature):
    return pd.concat([pd.read_csv(f).assign(fichier=Path(f).name.split(".")[0])
                      for f in sorted(glob.glob(str(ICI / "runs" / f"{nature}_*.csv.gz")))], ignore_index=True)


def retenues(d):
    return d[(d["fitness"] >= 0.5) & d["porte"]]


def genes(ligne):
    return {k: (float(ligne[k]) if k in ("Z", "stop", "objectif") else int(ligne[k])) for k in GENES}


def decrire(g):
    m = G.MARCHES[g["marche"]]
    return (f"{m} · {M.FAMILLES[g['famille']]} ({'contrer' if g['inverse'] else 'suivre'}), L {g['L']}, Z {g['Z']:.2f},"
            f" {SENS[g['sens']]}, stop {g['stop']:.2%}, objectif {g['objectif']:.2%}, entree des la barre {g['debut']},"
            f" sortie apres {g['duree']} barres, {FILTRES[g['filtre']]}")


def mesures(rend, dol, ntr, pnl):
    """rend, dol, ntr : par seance jouable de la periode ; pnl : $ de chaque trade de la periode (1 micro)."""
    n = len(rend)
    s = rend.std()
    cum = np.cumsum(dol)
    pic = np.maximum.accumulate(np.r_[0.0, cum])[1:]
    gains, pertes = pnl[pnl > 0], pnl[pnl <= 0]
    return {"seances": n, "trades": int(ntr.sum()), "sharpe": round(G.sharpe(rend), 3),
            "t": round(float(rend.mean() / s * np.sqrt(n)) if s > 0 else 0.0, 3), "dollars_1_micro": round(float(dol.sum()), 2),
            "perte_max_1_micro": round(float((cum - pic).min()) if n else 0.0, 2),
            "perte_max_pct_50k": round(float((cum - pic).min()) / CAPITAL * 100 if n else 0.0, 3),
            "jours_gagnants": round(float((dol[ntr > 0] > 0).mean()) if (ntr > 0).any() else 0.0, 3),
            "trades_gagnants": round(float(len(gains) / len(pnl)) if len(pnl) else 0.0, 3),
            "gain_moyen": round(float(gains.mean()) if len(gains) else 0.0, 2),
            "perte_moyenne": round(float(pertes.mean()) if len(pertes) else 0.0, 2)}


def main():
    reel, bruit = runs("reel"), runs("bruit")
    rr, rb = retenues(reel), retenues(bruit)
    lignes = [f"Machine evolutive n°3 (regles v2.1) : {len(reel)} strategies evaluees sur vraies donnees, {len(bruit)} sur bruit"
              f" ({reel['fichier'].nunique()} + {bruit['fichier'].nunique()} evolutions).",
              f"Fitness >= 0,5 et porte passee : {len(rr)} sur vraies donnees, {len(rb)} sur bruit.", ""]
    barriere = {}
    lignes.append("Barriere du bruit par marche (meilleur Sharpe de validation sur bruit, meme filtre) :")
    for i, m in enumerate(G.MARCHES):
        b = rb[rb["marche"] == i]
        barriere[i] = float(b["sharpe_val"].max()) if len(b) else G.SHARPE_PORTE
        lignes.append(f"  {m:4s} {barriere[i]:5.2f}  ({len(b)} strategies de bruit retenues)")
    lignes.append("")
    finalistes = rr.sort_values("sharpe_val", ascending=False).groupby("marche").head(1).sort_values("sharpe_val", ascending=False)
    donnees = {m: M.preparer(M.charger(ICI / "cache" / f"complet_{m}.npz")) for m in G.MARCHES}
    sortie = []
    lignes.append(f"Finalistes (un par marche au plus) : {len(finalistes)}")
    for _, f in finalistes.iterrows():
        g = genes(f)
        m = G.MARCHES[g["marche"]]
        bat = float(f["sharpe_val"]) > barriere[g["marche"]]
        res = {"strategie": decrire(g), "genes": g, "fitness": round(float(f["fitness"]), 3), "sharpe_validation": round(float(f["sharpe_val"]), 3),
               "barriere_bruit": round(barriere[g["marche"]], 3), "bat_le_bruit": bat, "trouvee_par": f["fichier"]}
        lignes += ["", f"- {res['strategie']}", f"  fitness {res['fitness']:.2f}, Sharpe de validation {res['sharpe_validation']:.2f}"
                   f" contre {res['barriere_bruit']:.2f} sur bruit : {'bat le bruit' if bat else 'NE BAT PAS le bruit, elimine sans ouvrir le coffre'}"]
        if bat:
            d = donnees[m]
            rend, dol, ntr, pnl = M.lancer_journal(d, g)
            jouable = ~d["interdit"]
            jour_du_trade = np.repeat(d["jours"], int(d["nb"]))
            res["periodes"] = {}
            for nom, (a, b) in PERIODES.items():
                k = jouable & (d["jours"] >= np.datetime64(a)) & (d["jours"] <= np.datetime64(b))
                kt = (jour_du_trade >= np.datetime64(a)) & (jour_du_trade <= np.datetime64(b)) & np.isfinite(pnl)
                res["periodes"][nom] = mesures(rend[k], dol[k], ntr[k], pnl[kt])
            co = jouable & (d["jours"] >= np.datetime64("2023-01-01"))
            annees = pd.Series(dol[co], index=pd.DatetimeIndex(d["jours"][co]).year).groupby(level=0).sum()
            res["annees_coffre"] = {int(a): round(float(v), 2) for a, v in annees.items()}
            t = res["periodes"]["coffre 2023-2026"]["t"]
            positives = int((annees > 0).sum())
            res["passe"] = bool(t >= T_MIN and positives >= ANNEES_MIN)
            for nom, x in res["periodes"].items():
                lignes.append(f"  {nom:22s} Sharpe {x['sharpe']:5.2f}  t {x['t']:5.2f}  {x['trades']:5d} trades  {x['dollars_1_micro']:+10.0f} $"
                              f"  perte max {x['perte_max_1_micro']:+8.0f} $ ({x['perte_max_pct_50k']:+.2f} % de 50 000 $)"
                              f"  jours gagnants {x['jours_gagnants']:.0%}  gain moyen {x['gain_moyen']:+.0f} $ / perte moyenne {x['perte_moyenne']:+.0f} $")
            lignes.append("  annees du coffre : " + ", ".join(f"{a} {v:+.0f} $" for a, v in res["annees_coffre"].items()))
            lignes.append(f"  VERDICT : {'PASSE' if res['passe'] else 'ELIMINE'} (t {t:.2f} contre {T_MIN} exige ; {positives} annees positives sur"
                          f" {len(annees)}, {ANNEES_MIN} exigees)")
        sortie.append(res)
    survivants = [r for r in sortie if r.get("passe")]
    lignes += ["", f"Survivants : {len(survivants)}"] + [f"  {r['strategie']}" for r in survivants]
    (ICI / "resultats_coffre3.txt").write_text("\n".join(lignes) + "\n")
    (ICI / "resultats_coffre3.json").write_text(json.dumps({"barriere_bruit": {G.MARCHES[i]: v for i, v in barriere.items()},
                                                            "finalistes": sortie, "evaluees_reel": len(reel), "evaluees_bruit": len(bruit),
                                                            "retenues_reel": len(rr), "retenues_bruit": len(rb)}, indent=1, ensure_ascii=False))
    print("\n".join(lignes))


if __name__ == "__main__":
    main()
