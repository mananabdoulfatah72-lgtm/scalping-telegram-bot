"""Zone de bruit (Bot 3 en 1, reglages actuels C2 + Q1, sans le filtre delta) contre Supertrend 10-3, dans le meme
simulateur (machine v6) depuis le Master de l'utilisateur : 51 000 $, plancher 49 200 $, 1er retrait a 53 600 $.
En plus : la regle d'inactivite de Bulenox (5 jours de trading sans trade = Master perdu)."""
import numpy as np

import st_detail as X

sim = X.sim
D = sim.charger(str(X.S / "nq_15ans.csv.gz"), str(X.S / "zone_c2q1_15ans.txt"), cache=None)
J = D["jours"]; nj = len(J); td = D["t_jour"]
jd = np.searchsorted(td, np.arange(nj), "left").astype(np.int64); jf = np.searchsorted(td, np.arange(nj), "right").astype(np.int64)
ZARGS = (D["O"], D["H"], D["L"], D["C"], jd, jf, D["t_sens"], D["t_me"], D["t_mx"], D["t_e"], D["t_x"], D["t_w"], D["t_niv"])
assert list(J) == list(X.J), "les deux jeux de seances different"
print(f"zone : {len(td)} trades sur {nj} seances ; seances sans trade : {(jf == jd).mean() * 100:.0f} % "
      f"(Supertrend : {(X.jf == X.jd).mean() * 100:.0f} %)")


def inactif(vide, i, ns):
    """Premiere seance (0, 1, ...) de la fenetre ou 5 seances de suite sans trade sont atteintes, sinon None."""
    n = 0
    for q in range(ns):
        n = n + 1 if vide[i + q] else 0
        if n >= 5:
            return q
    return None


for nom, args, vide, prm in (("Zone (Bot 3 en 1) 1 MNQ, limite 1 000 $", ZARGS, jf == jd, X.prm(1, 1000)),
                             ("Supertrend 1 MNQ, limite 400 $", X.ARGS, X.jf == X.jd, X.prm(1, 400))):
    pris = np.ones(len(args[6]), np.bool_)
    for eod, regle in ((0, "temps reel"), (1, "fin de journee")):
        p = prm.copy(); p[12] = eod
        for a0 in ("2011", "2023"):
            for ns in (66, 250):
                deb = [i for i in range(nj) if J[i] >= a0 and D["complete"][i] and i + ns <= nj]
                c = {"retrait": 0, "plancher": 0, "inactivite": 0, "ni": 0}
                for i in deb:
                    r = sim.fenetre(i, ns, p, 51000.0, 51700.0, *args, pris, 53550.0, 2500.0, 50100.0, 0)
                    qi = inactif(vide, i, ns)
                    if qi is not None and (r[0] == 0 or qi < r[2]):
                        c["inactivite"] += 1
                    else:
                        c[{1: "retrait", -1: "plancher", 0: "ni"}[r[0]]] += 1
                n = len(deb)
                print(f"  {nom:40s} | plancher {regle:14s} | departs {a0}+ | {ns:3d} seances : 53 600 $ atteint {c['retrait'] / n * 100:3.0f} %, "
                      f"perdu par le plancher {c['plancher'] / n * 100:3.0f} %, perdu par l'inactivite {c['inactivite'] / n * 100:3.0f} %, "
                      f"ni l'un ni l'autre {c['ni'] / n * 100:3.0f} %")
