"""Pour information (asie/README.md) : la bougie de minuit (18 h 00 -> 18 h 05, New York) sur les 7 marches. Usage : ASIE_DONNEES=<dossier> python3 asie/cinq_minutes.py"""
import sys, numpy as np, pandas as pd
from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parent))
import machine7 as M7
print("Pour information : la bougie de minuit (18 h 00 -> 18 h 05, New York), achat, lundi - jeudi soir")
print("marche | periode | brut moyen (pb) | % positifs | frais (pb) | net moyen (pb) | t net | apres derniere heure US en baisse : brut | en hausse : brut")
for c in M7.MARCHES:
    M = M7.Marche(c)
    for nom, (a, b) in (("2012-2022", (M7.DEBUT, M7.FIN_EXPLO)), ("2023-2026", (M7.DEBUT_COFFRE, M7.FIN))):
        J = M7.soirs(a, b)
        ie = M.indice(M7.utc(J, M7.NY, "18:00")); i5 = M.indice(M7.utc(J, M7.NY, "18:05"))
        i15 = M.indice(M7.utc(J, M7.NY, "15:00")); i16 = M.indice(M7.utc(J, M7.NY, "16:00"))
        ok = (ie >= 0) & (i5 > ie) & (i15 >= 0) & (i16 >= 0)
        e, x = M.O[ie[ok]], M.O[i5[ok]]
        mv = M.O[i16[ok]] / M.O[i15[ok]] - 1
        g = np.isfinite(e) & np.isfinite(x)
        r = x[g] / e[g] - 1; mv = mv[g]
        cout = np.array([M.cout(v) for v in e[g]])
        net = r - cout
        bas, haut = r[mv < 0], r[mv > 0]
        print(f"{M.nom} | {nom} | {r.mean() * 1e4:+.2f} | {np.mean(r > 0):.0%} | {cout.mean() * 1e4:.2f} | {net.mean() * 1e4:+.2f} | {M7.t_stat(net):+.2f} | "
              f"{bas.mean() * 1e4:+.2f} | {haut.mean() * 1e4:+.2f}")
