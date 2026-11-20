"""Pour information : W1 contre le Supertrend depuis le compte de l utilisateur (52 000 $, plancher 50 100 $). Memes variables que w1_usine.py."""
import os, sys, numpy as np
ML = os.environ["ML_DIR"]; sys.path.insert(0, ML + "/arene"); sys.path.insert(0, ML)
import bots as BT, w1 as W
B = BT.Base(os.environ["CACHE_DOSSIER"])
ST = sorted(BT.supertrend(B), key=lambda t: (t[0], t[2]))
X, y, an = W.variables_prod(B, ST); p = W.probas(X, y, an); W1p, garde = W.tri(ST, p, y, an)
res = {}
for nom, tr in (("W1", W1p), ("Supertrend", [t for t, g_ in zip(ST, np.ones(len(ST), bool))])):
    r, dp, ntr = BT.journees(B, tr, 1, 400.0)
    res[nom] = (r * 26675 / 28500, dp * 26675 / 28500, ntr > 0)        # au prix du 19 novembre
ok = B.ok; idx = np.where(ok)[0]; J = np.array(B.J)[idx]
def compte(g, p, j, d0, n, solde=52000.0, pl=50100.0, retrait=53600.0):
    sans = 0
    for q in range(n):
        d = d0 + q
        if solde + p[d] <= pl: return 1
        solde += g[d]; sans = 0 if j[d] else sans + 1
        if sans >= 5: return 2
        if solde >= retrait: return 0
    return 3
for debut in ("2017-01-01", "2023-01-01"):
    print("== departs depuis", debut[:4], "(solde 52 000, plancher 50 100)")
    d0s = [i for i in range(len(idx)) if J[i] >= debut]
    for nom, (g, p, j) in res.items():
        g2, p2, j2 = g[idx], p[idx], j[idx]
        out = []
        for n in (10, 22):
            rr = np.array([compte(g2, p2, j2, i, n) for i in d0s if i + n <= len(idx)])
            out.append(f"{n} seances : retrait {np.mean(rr == 0):.0%}, perdu {np.mean((rr == 1) | (rr == 2)):.0%}")
        x = g2[d0s]; cum = np.cumsum(x)
        print(f"  {nom:10s} | " + " | ".join(out) + f" | par seance {x.mean():+.1f} $ | seances tradees {np.mean(j2[d0s]):.0%} | pire baisse {np.min(cum - np.maximum.accumulate(cum)):+,.0f} $")
