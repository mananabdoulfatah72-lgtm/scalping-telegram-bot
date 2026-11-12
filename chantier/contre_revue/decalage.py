"""Les horodatages du CFD sont-ils bien en UTC toute l'annee ? Correlation des rendements 5 min CFD / future NQ a plusieurs decalages."""
import sys; sys.path.insert(0, '.')
import numpy as np, pandas as pd
import charge as Ch
d = Ch.nq_brut()
c = Ch.cfd_brut(); off = Ch.decalage_ny(c.utc); ny = c.utc + pd.to_timedelta(off, unit="h")
c = c.assign(ny=ny)
# future : cloture toutes les 5 minutes
d["ts"] = pd.to_datetime(d.t, format="%Y-%m-%d %H:%M")
f5 = d.set_index("ts").c.resample("5min", label="left", closed="left").last().dropna()   # cloture de la barre de 5 min commencant a ts
rf = np.log(f5).diff()
rf = rf[(rf.index.hour * 60 + rf.index.minute) > 570]         # pas le rendement de nuit
cc = c.set_index("ny").c
rc = np.log(cc).diff()
def corr_jour(jour, lags=(-60, -30, 0, 30, 60)):
    a = rf[jour]
    out = {}
    for lg in lags:
        b = rc.reindex(a.index + pd.Timedelta(minutes=lg))
        ok = np.isfinite(b.values) & np.isfinite(a.values)
        out[lg] = np.corrcoef(a.values[ok], b.values[ok])[0, 1] if ok.sum() > 20 else np.nan
    return out
jours = sorted(set(rf.index.strftime("%Y-%m-%d")))
res = []
for j in jours:
    if j < "2012-01-04" or j > "2026-10-02":
        continue
    try:
        o = corr_jour(j)
    except KeyError:
        continue
    o["jour"] = j; res.append(o)
R = pd.DataFrame(res).set_index("jour")
R = R.dropna(how="all", subset=[-60, -30, 0, 30, 60]); R["meilleur"] = R[[-60, -30, 0, 30, 60]].fillna(-9).idxmax(axis=1)
print(R.meilleur.value_counts())
bad = R[R.meilleur != 0]
print(bad.round(2).to_string())
R.to_pickle("decalage.pkl")
