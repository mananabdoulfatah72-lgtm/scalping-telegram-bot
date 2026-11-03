#!/usr/bin/env python3
"""Partie V (ml/REGLES.md) : teneur de marche LMSR de Hanson. Prix = softmax, perte maximale b ln(n), et 2 000 traders
simules avec une information privee bruitee : le prix converge-t-il vers la vraie probabilite ? Simulation seulement."""
import json

import numpy as np

import donnees as D


class LMSR:
    def __init__(self, n, b):
        self.q = np.zeros(n); self.b = b

    def cout(self, q=None):
        q = self.q if q is None else q
        m = q.max() / self.b
        return self.b * (m + np.log(np.exp(q / self.b - m).sum()))      # b ln(somme e^(q/b)), sans debordement

    def prix(self):
        z = np.exp((self.q - self.q.max()) / self.b); return z / z.sum()   # = softmax(q / b)

    def acheter(self, i, x):
        avant = self.cout(); self.q[i] += x; return self.cout() - avant


out = {}
txt = ["# Partie V : marché de prédiction LMSR (simulation)\n"]
# 1. identites : softmax, somme a 1, perte maximale b ln(n)
m = LMSR(3, 100.0)
for i, x in [(0, 50), (1, 120), (0, -30), (2, 400)]:
    m.acheter(i, x)
q = m.q / m.b; sm = np.exp(q - q.max()) / np.exp(q - q.max()).sum()
pire = []
for gagnant in range(3):
    mm = LMSR(3, 100.0); paye = 0.0
    for _ in range(2000):                                  # un trader qui sait : il achete le gagnant jusqu'a un prix de 0,999
        if mm.prix()[gagnant] > 0.999:
            break
        paye += mm.acheter(gagnant, 5.0)
    pire.append(mm.q[gagnant] - paye)                    # perte du teneur = ce qu'il doit payer - ce qu'il a encaisse
out["identites"] = dict(prix=m.prix().tolist(), softmax=sm.tolist(), somme=float(m.prix().sum()), perte_max_theorique=float(100 * np.log(3)), perte_max_observee=float(max(pire)))
txt.append(f"- Prix LMSR après 4 achats : {np.round(m.prix(), 4).tolist()} ; softmax(q / b) : {np.round(sm, 4).tolist()} ; somme {m.prix().sum():.6f}.")
txt.append(f"- Perte maximale du teneur, b ln(n) = {100 * np.log(3):.2f} $ ; un trader qui connaît le résultat lui prend au plus {max(pire):.2f} $.")

# 2. convergence : 2 000 traders, information privee bruitee, achats de taille limitee
rng = np.random.default_rng(1)
vraie = 0.62; b = 200.0; traj = {}
for bruit in (0.10, 0.25):
    mk = LMSR(2, b); chemin = []
    for t in range(2000):
        croyance = np.clip(vraie + rng.normal(0, bruit), 0.01, 0.99)    # estimation privee
        p = mk.prix()[0]
        if abs(croyance - p) > 0.01:                                     # achete le cote sous-evalue, 10 parts au plus
            i = 0 if croyance > p else 1
            mk.acheter(i, min(10.0, abs(croyance - p) * b))
        chemin.append(mk.prix()[0])
    traj[str(bruit)] = chemin[::10]
    txt.append(f"- Vraie probabilité {vraie:.0%}, bruit privé ±{bruit:.0%} : prix après 200 traders {chemin[199]:.1%}, "
               f"après 2 000 {chemin[-1]:.1%} (moyenne des 500 derniers {np.mean(chemin[-500:]):.1%}).")
out["convergence"] = dict(vraie=vraie, b=b, chemins=traj)

# 3. coherence entre marches lies : P(A) <= P(B) quand A implique B
txt.append("- Marchés liés : si « A » implique « B », un prix P(A) > P(B) est un arbitrage sans risque "
           "(vendre A, acheter B) ; c'est ce que les robots traquent entre contrats corrélés.")
txt.append("\nNB : Polymarket est bloqué en France par l'Autorité nationale des jeux depuis novembre 2024 ; tout ceci reste une simulation.")
json.dump(out, open(D.SORTIE / "n5.json", "w"))
D.ecrire("n5.md", "\n".join(txt) + "\n")
