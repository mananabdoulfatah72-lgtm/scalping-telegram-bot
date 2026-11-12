"""Les 16 variantes de la partie N, filtres recodes independamment ; donnees de l'etude puis horodatages corriges."""
import sys; sys.path.insert(0, '.')
import numpy as np, pandas as pd
from math import erf, sqrt
import charge as Ch
from nuit_rev import tstat, gain

def filtres(S):
    """S : seances (index = date). Renvoie F1 (pas inverse), F2 (baisse), F3 (cher), connus avant la nuit qui precede chaque seance."""
    V = Ch.vol_brut()
    def veille(nom):
        s, r = V[nom]
        s = pd.concat([s, r[~r.index.isin(s.index)]]).sort_index(); s = s[~s.index.duplicated()].dropna()
        dates = s.index.to_numpy(); vals = s.to_numpy()
        k = np.searchsorted(dates, S.index.to_numpy(), "left") - 1          # derniere date strictement avant la seance
        return pd.Series(np.where(k >= 0, vals[np.maximum(k, 0)], np.nan), index=S.index), pd.Series(np.where(k >= 0, dates[np.maximum(k, 0)], ""), index=S.index)
    vix, dvix = veille("VIX"); v3, _ = veille("VIX3M"); vxn, dvxn = veille("VXN")
    C = S[S.ok]
    lr = np.log(C.c1559).diff()                                  # rendement cloture a cloture de chaque seance complete
    rv = lr.rolling(20).std(ddof=1) * np.sqrt(252) * 100         # connu a la cloture de la seance
    rv_prec = rv.shift(1)                                        # seance complete d'avant
    baisse = (C.c1559 < C.o930).shift(1).fillna(False).astype(bool)
    ratio = vxn.reindex(C.index) / rv_prec
    med = ratio.rolling(252, min_periods=252).median().shift(1)
    cher = (ratio > med)
    F = pd.DataFrame(index=S.index)
    F["inverse"] = (vix >= v3)
    F["baisse"] = baisse.reindex(S.index).fillna(False); F["cher"] = cher.reindex(S.index).fillna(False)
    F["d_vix"] = dvix; F["vix"] = vix; F["vix3m"] = v3
    return F

def p_uni(t):
    return 0.5 * (1 - erf(t / sqrt(2)))

def bh(p, q=0.05):
    p = np.asarray(p); n = len(p); o = np.argsort(p); ok = p[o] <= q * np.arange(1, n + 1) / n
    k = np.nonzero(ok)[0].max() + 1 if ok.any() else 0
    out = np.zeros(n, bool); out[o[:k]] = True; return out

def table(N, F, nom):
    print("==", nom)
    ex = (N.jour <= "2022-12-31").to_numpy(); an = N.jour.str[:4].to_numpy(); res = []
    f = F.reindex(N.jour)
    masques = {"F0": np.ones(len(N), bool), "F1": ~f.inverse.to_numpy(bool), "F2": f.baisse.to_numpy(bool), "F3": f.cher.to_numpy(bool)}
    for stop in (0.0, 0.005, 0.0075, 0.01):
        g, stp = gain(N, stop); g6, _ = gain(N, stop, 6.0)
        for k, m in masques.items():
            v = np.where(m, g, 0.0); v6 = np.where(m, g6, 0.0)
            pos = sum(v[an == a].sum() > 0 for a in np.unique(an))
            res.append(dict(stop=stop, f=k, n=int(m.sum()), t=tstat(v), t_ex=tstat(v[ex]), t_ct=tstat(v[~ex]), t6=tstat(v6), moy=g[m].mean(), moy_ex=v[ex].mean(), moy_ct=v[~ex].mean(),
                            pire=g[m].min(), pos=pos, stops=int((stp & m).sum())))
    R = pd.DataFrame(res); R["bh"] = bh([p_uni(t) for t in R.t])
    R["retenue"] = (R.t >= 2) & R.bh & (R.moy_ex > 0) & (R.moy_ct > 0) & (R.t6 >= 1.5) & (R.pos >= 10) & (R.pire > -1100)
    print(R.round(2).to_string())
    return R

if __name__ == "__main__":
    S = pd.read_pickle("seances_rev.pkl")
    F = filtres(S); F.to_pickle("filtres_rev.pkl")
    # controle anti-regard vers le futur : la date du VIX utilise est strictement avant la seance
    print("date VIX >= date de la seance :", int((F.d_vix >= F.index).sum()))
    N0 = pd.read_pickle("nuits_rev.pkl"); Nc = pd.read_pickle("nuits_corr.pkl")
    R0 = table(N0, F, "donnees de l'etude (horodatages bruts)")
    Rc = table(Nc, F, "horodatages corriges")
