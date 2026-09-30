#!/usr/bin/env python3
"""Evolution n°2 : ouverture du coffre 2023-2026, une seule fois (regles dans README.md).

1. Finalistes : parmi toutes les strategies evaluees sur les 5 graines reelles avec une fitness >= 0,5 et la porte
   passee, la meilleure de chaque espece par Sharpe de validation (7 ou 9 especes) ; le champion est la meilleure.
2. Comparaison avec le bruit : meilleur Sharpe de validation sur les 5 graines de bruit, meme filtre.
3. Coffre : chaque finaliste rejoue 2011-2026 ; on mesure 2023-2026 (t, Sharpe, resultat de chaque annee).
4. Le champion passe si t >= 2,7, positif en 2023, 2024, 2025 et 2026, et Sharpe de validation > meilleur du bruit.

Lancer depuis ce dossier, apres lancer2.py : python3 coffre2.py
"""
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

import donnees2 as D
import genetique2 as G
import moteur2 as M
from tournoi3 import lire_quotidien

ICI = Path(__file__).resolve().parent
DEBUT_COFFRE = np.datetime64("2023-01-01")
GENES = ["espece", "marche", "L", "Z", "sens", "stop", "objectif", "debut", "filtre"]


def tableau_runs(nature):
    return pd.concat([pd.read_csv(f).assign(fichier=Path(f).stem) for f in sorted(glob.glob(str(ICI / "runs" / f"{nature}_*.csv")))])


def main():
    reel, bruit = tableau_runs("reel"), tableau_runs("placebo")
    filtre = lambda d: d[(d["fitness"] >= 0.5) & d["porte"]]
    fr, fb = filtre(reel), filtre(bruit)
    finalistes = fr.sort_values("val_sharpe", ascending=False).groupby("espece").head(1).sort_values("val_sharpe", ascending=False)
    max_bruit = float(fb["val_sharpe"].max())
    Q = lire_quotidien()
    coffres = {m: D.charger(m, "coffre", Q) for m in G.MARCHES}
    sortie, resultats = [], []
    for rang, (_, f) in enumerate(finalistes.iterrows()):
        g = {k: (float(f[k]) if k in ("Z", "stop", "objectif") else int(f[k])) for k in GENES}
        d = coffres[G.MARCHES[g["marche"]]]
        rend, dol, ntr, _ = M.lancer(d, g)
        c = d["jours"] >= DEBUT_COFFRE
        r, dl, n = rend[c], dol[c], ntr[c]
        t = float(r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else 0.0
        ans = pd.Series(dl, index=pd.DatetimeIndex(d["jours"][c])).groupby(lambda x: x.year).sum()
        champion = rang == 0
        res = {"champion": champion, "g": g, "fichier": f["fichier"],
               "entrainement": {"sharpe": float(f["ent_sharpe"]), "trades": int(f["ent_trades"])},
               "validation": {"sharpe": float(f["val_sharpe"]), "trades": int(f["val_trades"])},
               "coffre": {"t": t, "sharpe": G.sharpe(r), "trades": int(n.sum()), "dollars": float(dl.sum()),
                          "annees": [{"annee": str(a), "dollars": float(v)} for a, v in ans.items()]}}
        resultats.append(res)
        print(f"{'CHAMPION ' if champion else 'finaliste'} {M.ESPECES[g['espece']]:20s} {G.MARCHES[g['marche']]} {g} | "
              f"Sharpe entrainement {f['ent_sharpe']:.2f} ({int(f['ent_trades'])} trades), validation {f['val_sharpe']:.2f} ({int(f['val_trades'])})"
              f" | COFFRE 2023-2026 : t {t:+.2f}, Sharpe {G.sharpe(r):+.2f}, {int(n.sum())} trades, {dl.sum():+,.0f} $ pour 1 micro | "
              + " ".join(f"{a}:{v:+,.0f}$" for a, v in ans.items()), flush=True)
    ch = resultats[0]
    crit = {"t >= 2,7 sur 2023-2026": ch["coffre"]["t"] >= 2.7,
            "positif en 2023, 2024, 2025 et 2026": all(a["dollars"] > 0 for a in ch["coffre"]["annees"]) and len(ch["coffre"]["annees"]) == 4,
            f"Sharpe de validation > meilleur du bruit ({max_bruit:.2f})": ch["validation"]["sharpe"] > max_bruit}
    passe = all(crit.values())
    print(f"\nStrategies evaluees : {len(reel)} reelles, {len(bruit)} sur bruit ; filtre des finalistes : {len(fr)} reelles, {len(fb)} bruit")
    print(f"Meilleur Sharpe de validation : reelles {fr['val_sharpe'].max():.2f}, bruit {max_bruit:.2f}")
    for k, v in crit.items():
        print(f"  {'OK   ' if v else 'ECHEC'} {k}")
    verdict = ("Le champion passe tous les critères." if passe else
               "Le champion est rejeté : " + ", ".join(k for k, v in crit.items() if not v) + ".")
    print("\n" + verdict)
    # page de suivi
    f_tab = ICI / "tableau" / "data.json"
    tab = json.loads(f_tab.read_text())
    tab["coffre"] = {"ouvert": True, "finalistes": resultats, "criteres": crit, "passe": passe, "verdict": verdict,
                     "max_bruit": max_bruit, "max_reel": float(fr["val_sharpe"].max()), "evaluees": {"reel": len(reel), "bruit": len(bruit)}}
    f_tab.write_text(json.dumps(tab, separators=(",", ":")))
    (ICI / "resultats_coffre.json").write_text(json.dumps(tab["coffre"], indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
