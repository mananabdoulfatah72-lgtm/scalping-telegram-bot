"""Contre-revue de la partie N : recalcul independant depuis les fichiers bruts."""
import sys, datetime as dt
sys.path.insert(0, '.')
import numpy as np, pandas as pd
import charge as Ch

PREF = 28500.0; TICK = 0.25

def tstat(v):
    v = np.asarray(v, float); return v.mean() / (v.std(ddof=1) / np.sqrt(len(v)))

def seances():
    d = Ch.nq_brut()
    g = d.groupby("jour")
    nb = g.size()
    prem = d[d.m == 0].set_index("jour"); dern = d[d.m == 389].set_index("jour")
    S = pd.DataFrame({"nb": nb})
    S["o930"] = prem.o.reindex(S.index); S["c1559"] = dern.c.reindex(S.index)
    S["ok"] = S.o930.notna() & S.c1559.notna() & (S.nb >= 370)
    S["contrat"] = g.contrat.first()
    return S

def nuits():
    S = seances()
    c = Ch.cfd_brut()
    off = Ch.decalage_ny(c.utc)
    ny = c.utc + pd.to_timedelta(off, unit="h")
    c = c.assign(ny=ny, mn=(ny.dt.hour * 60 + ny.dt.minute).to_numpy(), date=ny.dt.strftime("%Y-%m-%d"))
    # jour de trading : barres >= 18 h -> lendemain (calendrier) ; barres < 9 h 30 -> meme jour
    lendemain = (ny + pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d")
    c["tj"] = np.where(c.mn >= 1080, lendemain, np.where(c.mn < 570, c.date, ""))
    b930 = c[c.mn == 570].set_index("date")
    grp = {k: v for k, v in c[c.tj != ""].groupby("tj")}
    lignes = []
    for jour, r in S.iterrows():
        if not r.ok or jour not in grp:
            continue
        g = grp[jour]
        if len(g) < 150:
            continue
        k0 = g.iloc[0]
        veille = (pd.Timestamp(jour) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        if not (k0.mn >= 1080 and k0.mn < 1110 and k0.date == veille):
            continue
        if jour not in b930.index:
            continue
        lignes.append(dict(jour=jour, entree=k0.o, t_entree=k0.ny, sortie=b930.o[jour], nb=len(g), o=g.o.to_numpy(), l=g.l.to_numpy(),
                           h=g.h.to_numpy(), mn=g.mn.to_numpy(), dow_entree=k0.ny.dayofweek))
    return S, pd.DataFrame(lignes)

def gain(N, stop, frais=3.0, tick_apres_ouverture=True):
    out = np.zeros(len(N)); stp = np.zeros(len(N), bool)
    for i, r in enumerate(N.itertuples()):
        e = r.entree; px = r.sortie
        if stop > 0:
            niv = e * (1 - stop)
            k = np.nonzero(r.l <= niv)[0]
            if len(k):
                k = k[0]; stp[i] = True
                if k > 0 and r.o[k] < niv:
                    px = r.o[k] - (TICK * e / PREF if tick_apres_ouverture else 0.0)   # ouverture sous le niveau
                else:
                    px = niv - TICK * e / PREF          # niveau moins 1 tick (tick a l'echelle du prix d'aujourd'hui)
        out[i] = (px - e) * 2 * PREF / e - frais
    return out, stp

if __name__ == "__main__":
    S, N = nuits()
    N.to_pickle("nuits_rev.pkl"); S.to_pickle("seances_rev.pkl")
    print("seances:", len(S), "completes:", int(S.ok.sum()))
    print("nuits jouables:", len(N), N.jour.iloc[0], N.jour.iloc[-1])
    print("jour de semaine de l'entree (0=lundi ... 6=dimanche):", N.dow_entree.value_counts().sort_index().to_dict())
    print("minute d'entree:", pd.Series([x for x in N.t_entree.dt.hour * 60 + N.t_entree.dt.minute]).value_counts().to_dict())
    ex = (N.jour <= "2022-12-31").to_numpy()
    for stop in (0.0, 0.005, 0.0075, 0.01):
        g, stp = gain(N, stop)
        g6, _ = gain(N, stop, 6.0)
        an = N.jour.str[:4].to_numpy(); pos = sum(g[an == a].sum() > 0 for a in np.unique(an))
        print(f"stop {stop*100:.2f}% : n {len(g)} t {tstat(g):.2f} (expl {tstat(g[ex]):.2f} / ctrl {tstat(g[~ex]):.2f}) t6 {tstat(g6):.2f} moy {g.mean():.1f} "
              f"(expl {g[ex].mean():.1f}, ctrl {g[~ex].mean():.1f}) pire {g.min():.0f} stops {int(stp.sum())} annees+ {pos}/{len(np.unique(an))} total {g.sum():.0f}")
