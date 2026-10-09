#!/usr/bin/env python3
"""Vague 10, descriptif : FundedNext Futures Flex 50K avec les regles donnees par l'utilisateur le 9 octobre 2026.
Challenge : objectif 2 500 $, perte max 1 500 $ en fin de journee (supposee bloquee au solde de depart, comme le Legacy),
pas de limite du jour, regularite 40 %, paiement unique. Compte finance : meme perte max (supposee), 5 jours a +200 $,
gain du cycle >= 500 $ (retrait >= 250 $), retrait <= 50 % des profits et <= 1 500 $, 95 % pour le trader, revue apres
5 retraits (la simulation s'arrete la). Deux lectures de « 50 % des profits » (du cycle ou du total). Bot de la vague 10
(zone 1 MNQ + RSI(2) de nuit sur 1 MES, pas de zone les jours de la Fed), avec ou sans frein MES, coussin garde. Un seul
achat. Ecrit flex50k.txt."""
import sys
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import vague10 as V10  # noqa: E402

V8, S9, W, D4, M4 = V10.V8, V10.S9, V10.W, V10.D4, V10.M4
E = (2500.0, 1500.0, 0, 0.0, 0.0, 0.40, 1)
PRIX, PART = 49.0, 0.95


def f_tuple(k):
    return (1500.0, 0.0, 0.0, 5, 200.0, 0.0, 250.0, np.array([1500.0]), 0.5, 1500.0 * k, 5)


def main():
    W.regler("regles")
    D, T, a3, gardes = S9.charger()
    C, _, _ = S9.conditions(D, T, gardes)
    bases = [D4.base(D, g & C["pas un jour de la Fed"]) for g in gardes]
    kN, kE = D4.facteurs_jour(D)
    G = V8.groupes(D)
    m = lambda x: x / V8.MOIS                                                               # noqa: E731
    L = [f"FundedNext Futures Flex 50K (regles de l'utilisateur ; prix suppose {PRIX} $), bot de la vague 10, un seul achat,"
         " filtre simule aussi bon qu'en 2026 (10 tirages). Colonnes : challenge perdu | valide (moitie / 3 sur 4) |"
         " finance perdu en 12 mois | 1er retrait (mois apres l'achat) | retraits recus la 1re et la 2e annee financee"
         " (medianes) | arrives a 5 retraits", ""]
    for pc, lecture in ((1, "50 % du gain du cycle"), (0, "50 % du gain total")):
        for k in (0, 1, 2):
            for frein, c_mnq in (("sans frein", 0.0), ("frein MES des 500 $ sous le plus haut", 1000.0),
                                 ("frein MES des 375 $ sous le plus haut", 1125.0), ("zone toujours sur MES", 1e18)):
                L.append(f"=== {lecture} | garder {1500 * k:,} $ | {frein}")
                for g in G:
                    cap = V8.fin_groupe(D, g)
                    iss, nch, p12, r1, an1, an2, n5 = [], [], [], [], [], [], []
                    for b in bases:
                        for d in G[g]:
                            sv = min(V8.H_SUIVI, cap - d)
                            ret = np.zeros(sv)
                            r = M4.parcours4(d, 4, 2.0 * kN, 5.0 * kE, ret, *b, *E, *f_tuple(k), sv, 1, 1, 1e18, 0.0, pc,
                                             c_mnq)
                            iss.append(r[0])
                            if r[0] != 1:
                                continue
                            nch.append(r[1])
                            fin = r[6] if r[2] else sv
                            idx = np.flatnonzero(ret > 0)
                            if len(idx):
                                r1.append(idx[0] + 1)
                            n5.append(r[3] >= 5)
                            if sv - r[1] >= 252:
                                p12.append(bool(r[2]) and fin - r[1] <= 252)
                                an1.append(ret[r[1]:r[1] + 252].sum() * PART)
                            if sv - r[1] >= 504:
                                an2.append(ret[r[1] + 252:r[1] + 504].sum() * PART)
                    iss = np.array(iss)
                    fini = (iss != 0).sum()
                    q = lambda x, p: np.percentile(x, p) if len(x) else float("nan")       # noqa: E731
                    L.append(f"  {g} : challenge perdu {(iss == -1).sum() / fini:.0%} | valide {m(q(nch, 50)):.1f} /"
                             f" {m(q(nch, 75)):.1f} mois | finance perdu en 12 mois "
                             + (f"{np.mean(p12):.0%}" if p12 else "-") + f" | 1er retrait au mois {m(q(r1, 50)):.1f} |"
                             f" 1re annee {q(an1, 50):,.0f} $, 2e annee {q(an2, 50):,.0f} $ | 5 retraits "
                             + (f"{np.mean(n5):.0%}" if n5 else "-"))
                print("\n".join(L[-4:]), flush=True)
    (ICI / "flex50k.txt").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
