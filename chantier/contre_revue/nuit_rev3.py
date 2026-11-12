import sys; sys.path.insert(0, '.')
import numpy as np, pandas as pd
import charge as Ch
from nuit_rev import tstat, gain
N = pd.read_pickle("nuits_rev.pkl").set_index("jour", drop=False); S = pd.read_pickle("seances_rev.pkl")
B = pd.read_pickle("base_nuit.pkl")
g0, _ = gain(N, 0.0); N["g0"] = g0
dn = B.dn.reindex(N.index)
X = N[dn.isna().to_numpy()].copy()
T = S[S.ok].copy(); T["ct_prec"] = T.contrat.shift(1); T["j_prec"] = T.index.to_series().shift(1)
X["roll"] = (T.contrat != T.ct_prec).reindex(X.index)
X["j_prec"] = T.j_prec.reindex(X.index)
print(len(X), "nuits exclues ; roll:", int(X.roll.sum()), " gain moyen roll:", X[X.roll].g0.mean().round(1), " non-roll:", X[~X.roll].g0.mean().round(1), "n", int((~X.roll).sum()))
print(X[["g0", "roll", "j_prec", "nb"]].sort_values("g0").head(12).to_string())
print(X[["g0", "roll", "j_prec", "nb"]].sort_values("g0").tail(25).to_string())
print(X.groupby(X.index.str[:4]).g0.agg(["size", "mean", "sum"]).round(0).to_string())
