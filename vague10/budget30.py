#!/usr/bin/env python3
"""Vague 10, descriptif (demande de l'utilisateur : budget de 30 EUR au plus) : Bulenox 50K Qualification (option 2,
perte 2 500 $ en fin de journee, limite du jour douce 1 100 $), ~19 $ avec un code a -89 % (paiement unique depuis le
17 aout 2026 selon les sites d'avis) + 148 $ d'activation du compte Master a la reussite. Compte Master comme
intraday50k/financee.py : 10 jours de trading par cycle, meilleur jour <= 40 % du gain du cycle, retraits <= 1 500 $ pour
les 3 premiers (100 % pour le trader), solde garde >= 52 600 $, passage en compte reel apres 3 retraits (la simulation
s'arrete la). Bot de la vague 10 (pas de zone les jours de la Fed), avec et sans frein MES. Un seul achat. Ecrit
budget30.txt."""
import sys
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import vague10 as V10  # noqa: E402

V8, S9, W, D4, M4 = V10.V8, V10.S9, V10.W, V10.D4, V10.M4
E = (3000.0, 2500.0, 0, 100.0, 1100.0, 0.0, 1)
F = (2500.0, 100.0, 1100.0, 10, 0.0, 0.40, 1000.0, np.array([1500.0, 1500.0, 1500.0, 1e9]), 0.0, 2600.0, 3)
PRIX, ACTIVATION = 19.25, 148.0


def main():
    W.regler("regles")
    D, T, a3, gardes = S9.charger()
    C, _, _ = S9.conditions(D, T, gardes)
    bases = [D4.base(D, g & C["pas un jour de la Fed"]) for g in gardes]
    kN, kE = D4.facteurs_jour(D)
    G = V8.groupes(D)
    m = lambda x: f"{x / V8.MOIS:.1f} mois"                                                  # noqa: E731
    L = [f"Bulenox 50K Qualification option 2 ({PRIX} $ avec code + {ACTIVATION} $ d'activation a la reussite), bot zone"
         " 1 MNQ + RSI(2) de nuit sur 1 MES, pas de zone les jours de la Fed ; filtre simule aussi bon qu'en 2026 (10"
         " tirages) ; un seul achat. Le Master passe en compte reel apres 3 retraits (non simule au-dela).", ""]
    for frein, c_mnq in (("sans frein", 0.0), ("frein MES des 500 $ sous le plus haut", 2000.0),
                         ("frein MES des 750 $ sous le plus haut", 1750.0)):
        for g in G:
            cap = V8.fin_groupe(D, g)
            iss, nch, prem, montants, n3, p12, net = [], [], [], [], [], [], []
            for b in bases:
                for d in G[g]:
                    sv = min(V8.H_SUIVI, cap - d)
                    ret = np.zeros(sv)
                    r = M4.parcours4(d, 4, 2.0 * kN, 5.0 * kE, ret, *b, *E, *F, sv, 1, 1, 1e18, 0.0, 0, c_mnq)
                    iss.append(r[0])
                    if r[0] != 1:
                        if sv >= V8.H:
                            net.append(-PRIX)
                        continue
                    nch.append(r[1])
                    fin = r[6] if r[2] else sv
                    idx = np.flatnonzero(ret[:fin] > 0)
                    if len(idx):
                        prem.append(idx[0] + 1 - r[1])
                        montants += list(ret[idx])
                    n3.append(r[3] >= 3)
                    if sv - r[1] >= 252:
                        p12.append(bool(r[2]) and fin - r[1] <= 252)
                    if sv >= V8.H:
                        net.append(ret[:min(fin, V8.H)].sum() - PRIX - ACTIVATION)
            iss, nch = np.array(iss), np.array(nch)
            q = lambda x, p: np.percentile(x, p) if len(x) else float("nan")                # noqa: E731
            L += [f"=== {frein} | {g}",
                  f"challenge : reussi {np.mean(iss == 1):.0%}, perdu {np.mean(iss == -1):.0%}, pas fini"
                  f" {np.mean(iss == 0):.0%} ; valide : la moitie en {m(q(nch, 50))}, 3 sur 4 en {m(q(nch, 75))}",
                  (f"premier retrait apres la validation : la moitie en {m(q(prem, 50))} ; retrait moyen"
                   f" {np.mean(montants):,.0f} $ ; comptes arrives au compte reel (3 retraits) : {np.mean(n3):.0%}"
                   if prem else "pas encore de retrait"),
                  (f"Master perdu dans les 12 mois : {np.mean(p12):.0%} ({len(p12)} comptes)" if p12 else
                   "Master perdu : pas encore de recul"),
                  (f"argent net sur 24 mois (prix et activation compris) : mediane {q(net, 50):+,.0f} $, 1 sur 4 sous"
                   f" {q(net, 25):+,.0f} $ ; achats qui perdent de l'argent {np.mean(np.array(net) < 0):.0%}"
                   if net else "argent net sur 24 mois : pas encore de recul"), ""]
            print("\n".join(L[-6:]), flush=True)
    (ICI / "budget30.txt").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
