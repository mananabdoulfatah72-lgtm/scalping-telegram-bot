"""Ou se loge la derive CFD - future dans la journee ? Rendement moyen par barre de 5 min selon l'heure (horodatages corriges)."""
import sys; sys.path.insert(0, '.')
import numpy as np, pandas as pd
import charge as Ch
from nuit_corr import cfd_corrige
c = cfd_corrige(); off = Ch.decalage_ny(c.utc); ny = c.utc + pd.to_timedelta(off, unit="h")
c = c.assign(ny=ny, mn=(ny.dt.hour * 60 + ny.dt.minute).to_numpy())
K = 2 * 28500
c["r_in"] = (c.c / c.o - 1) * K                    # dans la barre
c["r_gap"] = (c.o / c.c.shift(1) - 1) * K          # entre la cloture d'avant et l'ouverture
c["ecart_min"] = c.utc.diff().dt.total_seconds() / 60
for a, b in (("2012", "2019"), ("2019", "2023"), ("2024", "2027")):
    x = c[(c.utc >= a) & (c.utc < b)]
    g = x.groupby("mn").r_in.agg(["mean", "std", "size"]); g["t"] = g["mean"] / (g["std"] / np.sqrt(g["size"]))
    print(f"== {a}-{b} : barres ou le rendement moyen dans la barre est le plus loin de 0")
    print(g[g["size"] > 300].sort_values("t", key=abs).tail(6).round(2).to_string())
    y = x[x.ecart_min == 5]
    g = y.groupby("mn").r_gap.agg(["mean", "std", "size"]); g["t"] = g["mean"] / (g["std"] / np.sqrt(g["size"]))
    print("   saut cloture -> ouverture entre deux barres qui se suivent")
    print(g[g["size"] > 300].sort_values("t", key=abs).tail(5).round(2).to_string())
    z = x[(x.ecart_min >= 45) & (x.ecart_min <= 130)]
    print(f"   saut pendant la pause du soir : moy {z.r_gap.mean():.2f} $, mediane {z.r_gap.median():.2f}, n {len(z)}, t {z.r_gap.mean() / (z.r_gap.std() / np.sqrt(len(z))):.2f}")
print("== somme des sauts moyens cloture -> ouverture (barres qui se suivent) sur la fenetre de nuit 18 h 05 -> 9 h 30, par periode")
for a, b in (("2012", "2019"), ("2019", "2023"), ("2023", "2024"), ("2024", "2027")):
    x = c[(c.utc >= a) & (c.utc < b) & (c.ecart_min == 5)]
    g = x.groupby("mn").r_gap.mean()
    nuit = g[(g.index > 1080) | (g.index <= 570)]
    jour = g[(g.index > 570) & (g.index <= 960)]
    print(f"  {a}-{b}: nuit {nuit.sum():+.2f} $ ; jour {jour.sum():+.2f} $")
