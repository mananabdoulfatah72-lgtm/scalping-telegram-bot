"""La nuit recalculee avec les horodatages du CFD corriges (+60 min pendant les semaines ou les Etats-Unis et l'Europe
ne sont pas a la meme heure d'ete, 2019 ->)."""
import sys, datetime as dt; sys.path.insert(0, '.')
import numpy as np, pandas as pd
import charge as Ch
from nuit_rev import tstat, gain, seances

def dernier_dimanche(a, mois):
    j = dt.date(a, mois + 1, 1) - dt.timedelta(days=1)
    return j - dt.timedelta(days=(j.weekday() + 1) % 7)

def fenetres(a):
    us_deb = Ch._nieme_dimanche(a, 3, 2); eu_deb = dernier_dimanche(a, 3)
    eu_fin = dernier_dimanche(a, 10); us_fin = Ch._nieme_dimanche(a, 11, 1)
    return (us_deb, eu_deb), (eu_fin, us_fin)

def cfd_corrige():
    c = Ch.cfd_brut().copy()
    utc = c.utc.copy(); dec = np.zeros(len(c), bool)
    for a in range(2019, 2027):
        for d, f in fenetres(a):
            g = (c.utc >= pd.Timestamp(d)) & (c.utc < pd.Timestamp(f))
            dec |= g.to_numpy()
    c["decale"] = dec
    c.loc[dec, "utc"] = c.utc[dec] + pd.Timedelta(minutes=60)
    return c

def nuits(c, S):
    off = Ch.decalage_ny(c.utc)
    ny = c.utc + pd.to_timedelta(off, unit="h")
    c = c.assign(ny=ny, mn=(ny.dt.hour * 60 + ny.dt.minute).to_numpy(), date=ny.dt.strftime("%Y-%m-%d"))
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
                           h=g.h.to_numpy(), mn=g.mn.to_numpy(), dow_entree=k0.ny.dayofweek, decale=bool(g.decale.any()) if "decale" in g else False))
    return pd.DataFrame(lignes)

def resume(N, nom):
    ex = (N.jour <= "2022-12-31").to_numpy(); out = {}
    for stop in (0.0, 0.005, 0.0075, 0.01):
        g, stp = gain(N, stop); g6, _ = gain(N, stop, 6.0)
        an = N.jour.str[:4].to_numpy(); pos = sum(g[an == a].sum() > 0 for a in np.unique(an))
        print(f"{nom} stop {stop*100:.2f}% : n {len(g)} t {tstat(g):.2f} (expl {tstat(g[ex]):.2f} / ctrl {tstat(g[~ex]):.2f}) t6 {tstat(g6):.2f} moy {g.mean():.1f} "
              f"(expl {g[ex].mean():.1f}, ctrl {g[~ex].mean():.1f}) pire {g.min():.0f} ({N.jour.iloc[int(g.argmin())]}) <=-1100: {int((g<=-1100).sum())} stops {int(stp.sum())} annees+ {pos}/{len(np.unique(an))} total {g.sum():.0f}")
        out[stop] = g
    return out

if __name__ == "__main__":
    S = seances()
    c = cfd_corrige()
    print("barres decalees:", int(c.decale.sum()))
    # controle : premiere barre apres le week-end dans les fenetres
    Nc = nuits(c, S); Nc.to_pickle("nuits_corr.pkl")
    N0 = pd.read_pickle("nuits_rev.pkl")
    print("nuits jouables (corrige):", len(Nc), " (etude:", len(N0), ") ; nuits dans les semaines decalees:", int(Nc.decale.sum()))
    print("minute d'entree (corrige):", pd.Series(Nc.t_entree.dt.hour * 60 + Nc.t_entree.dt.minute).value_counts().to_dict())
    g0 = resume(N0, "ETUDE  ")
    gc = resume(Nc, "CORRIGE")
    # les nuits des semaines decalees : etude contre corrige
    a = N0.set_index("jour"); a["g"] = g0[0.0]; b = Nc.set_index("jour"); b["g"] = gc[0.0]
    dj = b.index[b.decale]
    com = [j for j in dj if j in a.index]
    print(f"semaines decalees : {len(dj)} nuits corrigees, {len(com)} communes ; gain moyen etude {a.g.reindex(com).mean():.1f} $ (total {a.g.reindex(com).sum():.0f}) ; "
          f"corrige {b.g.reindex(com).mean():.1f} $ (total {b.g.reindex(com).sum():.0f})")
    hors = [j for j in a.index if j not in set(dj)]
    print(f"hors semaines decalees : etude {a.g.reindex(hors).mean():.1f} $ sur {len(hors)} nuits, t {tstat(a.g.reindex(hors)):.2f}")
    print("nuits de l'etude absentes du corrige:", [j for j in a.index if j not in b.index][:30])
    print("nuits du corrige absentes de l'etude:", [j for j in b.index if j not in a.index][:30])
