"""Le CFD (prix acheteur, type indice comptant ?) contre le future NQ : derive de la base."""
import sys; sys.path.insert(0, '.')
import numpy as np, pandas as pd
import charge as Ch
S = pd.read_pickle("seances_rev.pkl")
c = Ch.cfd_brut(); off = Ch.decalage_ny(c.utc); ny = c.utc + pd.to_timedelta(off, unit="h")
c = c.assign(ny=ny, mn=(ny.dt.hour * 60 + ny.dt.minute).to_numpy(), date=ny.dt.strftime("%Y-%m-%d"))
o930 = c[c.mn == 570].set_index("date").o; o1600 = c[c.mn == 960].set_index("date").o; c1555 = c[c.mn == 955].set_index("date").c
T = S[S.ok].copy()
T["cfd930"] = o930.reindex(T.index); T["cfd16"] = o1600.reindex(T.index); T["cfd1555c"] = c1555.reindex(T.index)
T["base930"] = T.cfd930 - T.o930; T["base16"] = T.cfd1555c - T.c1559
print(T[["o930", "cfd930", "base930", "c1559", "cfd1555c", "base16", "contrat"]].iloc[[300, 301, 302, 1500, 1501, 2990, 2991, 3200, 3201, 3600, 3601, 3602]])
# base en % du prix, par trimestre : dents de scie ?
T["bp"] = T.base930 / T.o930 * 1e4
print(T.groupby(T.index.str[:7]).bp.mean().iloc[-40:].round(1).to_string())
# derive de nuit : (CFD 16h -> 9h30) - (future 15h59 cloture -> 9h30), sans changement de contrat
T["j_prec"] = T.index.to_series().shift(1); T["c_prec"] = T.c1559.shift(1); T["cfd_prec"] = T.cfd1555c.shift(1); T["ct_prec"] = T.contrat.shift(1)
g = T[(T.contrat == T.ct_prec) & T.cfd930.notna() & T.cfd_prec.notna()].copy()
g["nuit_fut"] = np.log(g.o930 / g.c_prec); g["nuit_cfd"] = np.log(g.cfd930 / g.cfd_prec)
g["jour_fut"] = np.log(g.c1559 / g.o930); g["jour_cfd"] = np.log(g.cfd1555c / g.cfd930)
g["dn"] = (g.nuit_cfd - g.nuit_fut) * 2 * 28500; g["dj"] = (g.jour_cfd - g.jour_fut) * 2 * 28500
g["cal"] = (pd.to_datetime(g.index) - pd.to_datetime(g.j_prec)).dt.days
an = g.index.str[:4]
r = g.groupby(an).agg(n=("dn", "size"), derive_nuit_moy=("dn", "mean"), derive_nuit_med=("dn", "median"), derive_jour_moy=("dj", "mean"), total_nuit=("dn", "sum"), jours_cal=("cal", "sum"))
r["pct_an"] = r.total_nuit / (2 * 28500) / r.jours_cal * 365 * 100
print(r.round(2).to_string())
print("derive moyenne par nuit en $ (1 MNQ au prix d'aujourd'hui):", g.dn.mean().round(2), " mediane", g.dn.median().round(2), "t", (g.dn.mean() / (g.dn.std() / np.sqrt(len(g)))).round(1))
print("par jour de semaine de la seance (0=lundi):", g.groupby(pd.to_datetime(g.index).dayofweek).dn.agg(["mean", "median", "size"]).round(2).to_string())
g.to_pickle("base_nuit.pkl")
