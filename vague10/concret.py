#!/usr/bin/env python3
"""Vague 10, descriptif : le reglage conseille en chiffres concrets pour un seul achat (FundedNext Legacy 50K, zone 1 MNQ
+ RSI(2) de nuit sur 1 MES, frein MES sous 1 500 $ de coussin, pas de zone les jours de la Fed, garder 4 000 $ apres
chaque retrait ; filtre simule aussi bon qu'en 2026, 10 tirages). Temps pour valider, premier retrait, rythme et montant
des retraits, compte finance perdu, argent net de l'achat. Ecrit concret.txt."""
import sys
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import vague10 as V10  # noqa: E402

V8, S9, W, D4, M4 = V10.V8, V10.S9, V10.W, V10.D4, V10.M4


def main():
    W.regler("regles")
    D, T, a3, gardes = S9.charger()
    C, _, _ = S9.conditions(D, T, gardes)
    bases = [D4.base(D, g & C["pas un jour de la Fed"]) for g in gardes]
    kN, kE = D4.facteurs_jour(D)
    e, f_, part, (prix, _, _), _, pc = V8.reglages(dict(compte="FundedNext Legacy 50K", zone="zone MNQ", k=2))
    G = V8.groupes(D)
    m = lambda x: f"{x / V8.MOIS:.1f} mois"                                                  # noqa: E731
    L = ["FundedNext Legacy 50K (200 $ une fois, 80 % des retraits pour le trader), zone 1 MNQ + RSI(2) de nuit sur 1 MES,"
         " frein MES sous 1 500 $ de coussin, pas de zone les jours de la Fed, garder 4 000 $ apres chaque retrait.", ""]
    for g in G:
        cap = V8.fin_groupe(D, g)
        nch, iss, prem, ecarts, montants, p12, p24, net, an1, an2 = [], [], [], [], [], [], [], [], [], []
        for b in bases:
            for d in G[g]:
                sv = min(V8.H_SUIVI, cap - d)
                ret = np.zeros(sv)
                r = M4.parcours4(d, 4, 2.0 * kN, 5.0 * kE, ret, *b, *e, *f_, sv, 1, 1, 1e18, 0.0, pc, 1500.0)
                iss.append(r[0])
                if r[0] != 1:
                    if sv >= V8.H:                                  # seulement les achats suivis 24 mois
                        net.append(-prix)
                    continue
                nch.append(r[1])
                fin = r[6] if r[2] else sv
                idx = np.flatnonzero(ret[:fin] > 0)
                if len(idx):
                    prem.append(idx[0] + 1 - r[1])
                    ecarts += list(np.diff(idx))
                    montants += list(ret[idx] * part)
                if sv - r[1] >= 252:
                    p12.append(bool(r[2]) and fin - r[1] <= 252)
                    an1.append(ret[r[1]:r[1] + 252].sum() * part)
                if sv - r[1] >= 504:
                    p24.append(bool(r[2]) and fin - r[1] <= 504)
                    an2.append(ret[r[1] + 252:r[1] + 504].sum() * part)
                if sv >= V8.H:
                    net.append(ret[:min(fin, V8.H)].sum() * part - prix)
        iss, nch, net = np.array(iss), np.array(nch), np.array(net)
        q = lambda x, p: np.percentile(x, p) if len(x) else float("nan")                    # noqa: E731
        L += [f"=== {g} ({len(G[g])} achats x {len(bases)} tirages)",
              f"challenge : reussi {np.mean(iss == 1):.0%}, perdu {np.mean(iss == -1):.0%}, pas fini a la fin des donnees"
              f" {np.mean(iss == 0):.0%}",
              f"temps pour valider : 1 sur 4 en {m(q(nch, 25))}, la moitie en {m(q(nch, 50))}, 3 sur 4 en {m(q(nch, 75))}",
              f"premier retrait apres la validation : la moitie en {m(q(prem, 50))} (3 sur 4 en {m(q(prem, 75))}) ; puis un"
              f" retrait tous les {m(q(ecarts, 50))} en mediane ; montant pour toi (80 %) : moyenne {np.mean(montants):,.0f} $"
              f" (la moitie au-dessus de {q(montants, 50):,.0f} $)" if prem else "pas encore de retrait",
              f"retraits recus pour toi pendant la 1re annee financee : moyenne {np.mean(an1):,.0f} $, mediane"
              f" {q(an1, 50):,.0f} $, 1 sur 4 sous {q(an1, 25):,.0f} $ ({len(an1)} comptes suivis 12 mois)" if an1 else
              "1re annee financee : pas encore assez de recul",
              f"retraits recus pour toi pendant la 2e annee financee : moyenne {np.mean(an2):,.0f} $, mediane"
              f" {q(an2, 50):,.0f} $ ({len(an2)} comptes suivis 24 mois)" if an2 else "2e annee financee : pas encore de recul",
              f"compte finance perdu : dans les 12 mois {np.mean(p12):.0%} ({len(p12)} comptes), dans les 24 mois"
              f" {np.mean(p24):.0%} ({len(p24)} comptes)" if p12 else "compte finance perdu : pas encore assez de recul",
              f"argent net de l'achat sur 24 mois (achats suivis 24 mois) : 1 sur 10 sous {q(net, 10):+,.0f} $, 1 sur 4 sous"
              f" {q(net, 25):+,.0f} $, mediane {q(net, 50):+,.0f} $, 3 sur 4 sous {q(net, 75):+,.0f} $ ; perte d'argent"
              f" {np.mean(net < 0):.0%}" if len(net) else "argent net sur 24 mois : pas encore assez de recul", ""]
        print("\n".join(L[-9:]), flush=True)
    (ICI / "concret.txt").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
