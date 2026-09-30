#!/usr/bin/env python3
"""Tournoi n°4, etape 4 (README.md) : coffre 2023-2026, ouvert une seule fois, pour les survivants de explorer4.py et
la paire en continuation (hypothese nee du tournoi n°2, jugee seulement ici). Bonferroni sur l'ensemble du lot ;
au moins 3 annees positives sur 4.

Lancer depuis ce dossier, apres explorer4.py : python3 coffre4.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

import strategies4 as S
from concurrents2 import aligner
from explorer import charger, t_stat
from explorer4 import MARCHES, NOMS

ICI = Path(__file__).resolve().parent


def main():
    surv = json.loads((ICI / "survivants4.json").read_text())
    m = len(surv) + 1                                  # + la paire en continuation
    seuil = float(norm.ppf(1 - 0.05 / m))
    Q = S.T3.lire_quotidien()
    lignes, sortie = [f"Coffre 2023-2026 : {len(surv)} survivant(s) + la paire en continuation ; seuil de Bonferroni t >= {seuil:.2f}"], []
    donnees = {}
    for marche, (fichier, pt) in MARCHES.items():
        donnees[marche] = charger(fichier, fin=None)
    for s in surv:
        fichier, pt = MARCHES[s["marche"]]
        J, O, H, L, C, P, X = donnees[s["marche"]]
        res, ok, _ = S.toutes(J, O, H, L, C, P, X, S.st.cout_aller_retour(fichier), Q, S.range_nuit(fichier, J, X.get("contrat")))
        j = pd.DatetimeIndex(J)
        c = ok & (j.year >= 2023)
        t = t_stat(res[s["code"]][c] / O[c, 0])
        ans = pd.Series(res[s["code"]][c] * pt, index=j[c]).groupby(j[c].year).sum()
        passe = t >= seuil and (ans > 0).sum() >= 3
        sortie.append({"code": s["code"], "marche": s["marche"], "t": t, "annees": {str(a): float(v) for a, v in ans.items()}, "passe": bool(passe)})
        lignes.append(f"  {s['code']} {NOMS[s['code']]} {s['marche']} : t {t:+.2f} | " + " ".join(f"{a}:{v:+,.0f}$" for a, v in ans.items())
                      + f" (1 micro) | {'PASSE' if passe else 'rejete'}")
    a, b = aligner(donnees["NQ"], donnees["ES"])
    r, okp = S.paire_suivre(a, b, S.st.cout_aller_retour("nasdaq100"), S.st.cout_aller_retour("sp500"))
    j = pd.DatetimeIndex(a[0])
    c = okp & (j.year >= 2023)
    t = t_stat(r[c])
    ans = pd.Series(r[c], index=j[c]).groupby(j[c].year).sum()
    passe = t >= seuil and (ans > 0).sum() >= 3
    sortie.append({"code": "paire en continuation", "marche": "NQ+ES", "t": t, "annees": {str(k): float(v) for k, v in ans.items()},
                   "trades": int((r[c] != 0).sum()), "passe": bool(passe)})
    lignes.append(f"  Paire NQ / ES en continuation : t {t:+.2f}, {int((r[c] != 0).sum())} jours de trade | "
                  + " ".join(f"{k}:{v:+.1%}" for k, v in ans.items()) + f" (rendement, montant egal) | {'PASSE' if passe else 'rejete'}")
    print("\n".join(lignes))
    (ICI / "coffre4.txt").write_text("\n".join(lignes) + "\n")
    (ICI / "coffre4.json").write_text(json.dumps(sortie, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
