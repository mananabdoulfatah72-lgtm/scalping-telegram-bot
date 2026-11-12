"""Robustesse de la nuit : effet de la premiere barre (prix acheteur a la reouverture), derive CFD / future."""
import sys; sys.path.insert(0, '.')
import numpy as np, pandas as pd
import charge as Ch
from nuit_rev import tstat, gain
N = pd.read_pickle("nuits_rev.pkl"); S = pd.read_pickle("seances_rev.pkl")
ex = (N.jour <= "2022-12-31").to_numpy()
K = 2 * 28500
# 1. rendement des premieres barres de la nuit (ouverture k -> ouverture k+1), en $ au prix d'aujourd'hui
print("== rendement moyen par barre au debut de la nuit ($ pour 1 MNQ au prix d'aujourd'hui)")
for k in range(0, 8):
    r = np.array([(x.o[k + 1] / x.o[k] - 1) * K for x in N.itertuples()])
    print(f"  barre {k} -> {k+1}: moy {r.mean():6.2f} $  t {tstat(r):5.2f}   expl {r[ex].mean():6.2f} (t {tstat(r[ex]):.2f})  ctrl {r[~ex].mean():6.2f} (t {tstat(r[~ex]):.2f})  mediane {np.median(r):.2f}")
# rendement dans la premiere barre : ouverture -> cloture ? (on n'a pas c dans N) -> via o[k+1]
# 2. entree retardee
print("== entree retardee de k barres (sans stop / stop 0,75 %)")
for k in (0, 1, 2, 3, 6, 12, 24):
    N2 = N.copy()
    N2["entree"] = [x.o[k] for x in N.itertuples()]
    N2["o"] = [x.o[k:] for x in N.itertuples()]; N2["l"] = [x.l[k:] for x in N.itertuples()]
    g0, _ = gain(N2, 0.0); g75, s75 = gain(N2, 0.0075)
    print(f"  +{5*k:3d} min : sans stop t {tstat(g0):.2f} ({tstat(g0[ex]):.2f}/{tstat(g0[~ex]):.2f}) moy {g0.mean():.1f} | stop 0,75 t {tstat(g75):.2f} ({tstat(g75[ex]):.2f}/{tstat(g75[~ex]):.2f}) moy {g75.mean():.1f} stops {int(s75.sum())}")
# 3. derive CFD/future appliquee aux nuits de l'etude
B = pd.read_pickle("base_nuit.pkl")
N = N.set_index("jour", drop=False)
dn = B.dn.reindex(N.index)
print("nuits avec derive mesurable (meme contrat):", int(dn.notna().sum()), "sur", len(N))
g0, _ = gain(N, 0.0); g75, _ = gain(N, 0.0075)
ok = dn.notna().to_numpy(); exo = ex[ok]
for nom, g in (("sans stop", g0), ("stop 0,75 %", g75)):
    a = g[ok]; b = a - dn[ok].to_numpy()
    print(f"  {nom}: CFD t {tstat(a):.2f} ({tstat(a[exo]):.2f}/{tstat(a[~exo]):.2f}) moy {a.mean():.1f} ({a[exo].mean():.1f}/{a[~exo].mean():.1f})"
          f" | moins la derive mesuree nuit par nuit: t {tstat(b):.2f} ({tstat(b[exo]):.2f}/{tstat(b[~exo]):.2f}) moy {b.mean():.1f} ({b[exo].mean():.1f}/{b[~exo].mean():.1f})")
# derive moyenne par annee, appliquee en moyenne (moins bruitee)
an = N.jour.str[:4]
m_an = dn.groupby(an).mean()
print("derive moyenne par annee ($/nuit):", m_an.round(2).to_dict())
for nom, g in (("sans stop", g0), ("stop 0,75 %", g75)):
    b = g - an.map(m_an).to_numpy()
    print(f"  {nom} moins la derive moyenne de l'annee: t {tstat(b):.2f} ({tstat(b[ex]):.2f}/{tstat(b[~ex]):.2f}) moy {b.mean():.1f} ({b[ex].mean():.1f}/{b[~ex].mean():.1f})")
# 4. le future lui-meme : cloture 15 h 59 -> ouverture 9 h 30 (meme contrat), 1 MNQ, frais 3 $
T = S[S.ok].copy(); T["c_prec"] = T.c1559.shift(1); T["ct_prec"] = T.contrat.shift(1); T["j_prec"] = T.index.to_series().shift(1)
T = T[(T.contrat == T.ct_prec)]
T["g"] = (T.o930 / T.c_prec - 1) * K - 3
T["dow"] = pd.to_datetime(T.index).dayofweek
for nom, sel in (("toutes (2011 ->)", T.index >= "2011"), ("depuis 2012-01-04, jusqu'au 2026-10-02", (T.index >= "2012-01-04") & (T.index <= "2026-10-02")),
                 ("memes dates que les nuits de l'etude", T.index.isin(N.index))):
    x = T[sel]; e = (x.index <= "2022-12-31")
    print(f"  future cloture->ouverture, {nom}: n {len(x)} t {tstat(x.g):.2f} ({tstat(x.g[e]):.2f}/{tstat(x.g[~e]):.2f}) moy {x.g.mean():.1f} ({x.g[e].mean():.1f}/{x.g[~e].mean():.1f})")
x = T[T.index.isin(N.index)]
print("  par annee future c->o:", x.groupby(x.index.str[:4]).g.mean().round(1).to_dict())
print("  par annee CFD 18h->9h30:", pd.Series(g0, index=N.index).groupby(an).mean().round(1).to_dict())
