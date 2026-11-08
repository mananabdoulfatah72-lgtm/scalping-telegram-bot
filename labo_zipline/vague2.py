#!/usr/bin/env python3
"""Vague 2 du labo zipline (labo_zipline/VAGUE2.md, regles fixees avant calcul) : 12 effets publies, juges sur la periode
qui suit leur publication. Calcul principal avec pandas ; les tests retenus sur un fonds sont rejoues dans zipline.
MINUTES_NQ=... CACHE_DOSSIER=... python3 vague2.py <sortie.json>"""
import glob
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
SORTIE = Path(sys.argv[1])

# ------------------------------------------------------------------ donnees
d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(RACINE / "radar/donnees/jour/yahoo/*.csv.gz")))])
d[["sym", "champ"]] = d.serie.str.rsplit(":", n=1, expand=True)
RADAR = {s: g.pivot_table(index="date", columns="champ", values="valeur", aggfunc="last").sort_index()
         for s, g in d[d.sym.isin(["^VIX", "^VIX3M", "^IRX", "BTC-USD", "ETH-USD", "SPY", "QQQ"])].groupby("sym")}
for s in RADAR:
    RADAR[s].index = pd.to_datetime(RADAR[s].index)
AJ = ICI / "donnees/ajuste.csv.gz"
if AJ.exists():
    a = pd.read_csv(AJ, parse_dates=["date"])
    FONDS = {s: g.set_index("date")[["o", "h", "l", "c"]].sort_index() for s, g in a.groupby("sym")}
    SOURCE = "prix ajustés des dividendes (Yahoo, auto_adjust)"
else:
    FONDS = {s: RADAR[s][["o", "h", "l", "c"]] for s in ("SPY", "QQQ")}
    SOURCE = "prix bruts du radar (dividendes absents)"
IRX = RADAR["^IRX"]["c"].dropna()
VIX, VIX3M = RADAR["^VIX"]["c"].dropna(), RADAR["^VIX3M"]["c"].dropna()
K_FONDS, K_CRYPTO = 0.0002, 0.0031


def rf_jour(index, an):
    """Taux sans risque du jour (bons du Tresor a 3 mois, connu la veille)."""
    return (IRX.reindex(index.union(IRX.index)).ffill().shift(1).reindex(index).fillna(0.0) / 100.0 / an)


# ------------------------------------------------------------------ statistiques
def nw(y, X, lags=5):
    """MCO avec erreurs de Newey-West : coefficients et t."""
    X = np.column_stack([np.ones(len(y))] + ([X] if X is not None else []))
    XtX = np.linalg.inv(X.T @ X); b = XtX @ X.T @ y; u = y - X @ b
    S = (X * u[:, None]).T @ (X * u[:, None])
    for l in range(1, lags + 1):
        w = 1 - l / (lags + 1); G = (X[l:] * u[l:, None]).T @ (X[:-l] * u[:-l, None]); S += w * (G + G.T)
    V = XtX @ S @ XtX
    return b, b / np.sqrt(np.diag(V))


def sharpe(e, an):
    return float(e.mean() / e.std() * np.sqrt(an)) if e.std() > 0 else 0.0


def juger_timing(fab, debut, fin, an, k):
    """fab(k) -> (rendement total de la strategie, de l'achat-conservation, taux sans risque), series quotidiennes."""
    out = {}
    for nom, kk in (("base", k), ("double", 2 * k)):
        rs, rb, rf = fab(kk)
        sel = (rs.index >= debut) & (rs.index <= fin)
        rs, rb, rf = rs[sel], rb[sel], rf[sel]
        es, eb = (rs - rf).to_numpy(), (rb - rf).to_numpy()
        b, t = nw(es, eb)
        r = dict(alpha_an=float(b[0] * an), t_alpha=float(t[0]), beta=float(b[1]), sharpe=sharpe(es, an), sharpe_bh=sharpe(eb, an), jours=len(es))
        if nom == "base":
            m = len(es) // 2
            r["alpha_moitie1"] = float(nw(es[:m], eb[:m])[0][0] * an); r["alpha_moitie2"] = float(nw(es[m:], eb[m:])[0][0] * an)
            cs, cb = (1 + rs).cumprod(), (1 + rb).cumprod()
            r["rendement_an"] = float(cs.iloc[-1] ** (an / len(rs)) - 1); r["rendement_an_bh"] = float(cb.iloc[-1] ** (an / len(rb)) - 1)
            r["pire_baisse"] = float((cs / cs.cummax() - 1).min()); r["pire_baisse_bh"] = float((cb / cb.cummax() - 1).min())
            r["courbe"] = [[i.strftime("%Y-%m-%d"), round(float(x) * 10000), round(float(y) * 10000)] for i, x, y in zip(cs.index[::5], cs.values[::5], cb.values[::5])]
        out[nom] = r
    b = out["base"]
    raisons = []
    if b["t_alpha"] < 2: raisons.append(f"t de l'alpha {b['t_alpha']:.2f} sous 2")
    if b["sharpe"] <= b["sharpe_bh"]: raisons.append(f"Sharpe {b['sharpe']:.2f} pas mieux que l'achat-conservation ({b['sharpe_bh']:.2f})")
    if b["alpha_moitie1"] <= 0 or b["alpha_moitie2"] <= 0: raisons.append("alpha négatif sur une moitié")
    if out["double"]["t_alpha"] < 1.5: raisons.append(f"frais doublés : t {out['double']['t_alpha']:.2f}")
    return dict(**b, t_frais_doubles=out["double"]["t_alpha"], raisons=raisons, t_test=b["t_alpha"], n_test=b["jours"])


def rendement(px):
    return px["c"].pct_change()


# ------------------------------------------------------------------ Z1, Z2 tournant du mois
def tom(sym):
    px = FONDS[sym]; r = rendement(px); j = px.index; rf = rf_jour(j, 252)
    mois = j.to_period("M"); rang = pd.Series(1, index=j).groupby(mois).cumsum()            # 1er, 2e... jour du mois
    dernier = pd.Series(mois, index=j) != pd.Series(mois, index=j).shift(-1)                # dernier jour de bourse du mois
    w = ((rang <= 3) | dernier).astype(float)                                              # jours -1, +1, +2, +3

    def fab(k):
        cout = k * w.diff().abs().fillna(0)
        return w * r + (1 - w) * rf - cout, r, rf
    return fab


# ------------------------------------------------------------------ Z3 - Z5 exposition geree par la volatilite
def volgeree(px, an, k):
    r = px["c"].pct_change().dropna(); rf = rf_jour(r.index, an)
    mois = r.index.to_period("M")
    rv = r.groupby(mois).var(ddof=0)
    inv = 1.0 / rv
    c = 1.0 / inv.expanding(min_periods=12).mean()                                           # passe seul (mois inclus)
    poids = (c / rv).clip(upper=2.0).shift(1)                                               # poids du mois m+1 = c_m / RV_m
    w = pd.Series(poids.reindex(mois).to_numpy(), index=r.index).fillna(0.0)

    def fab(kk):
        cout = kk * w.diff().abs().fillna(0)
        return w * r + (1 - w) * rf - cout, r, rf
    return fab


# ------------------------------------------------------------------ Z6, Z7 structure du VIX
def vixfiltre(sym):
    px = FONDS[sym]; r = rendement(px); j = px.index; rf = rf_jour(j, 252)
    ecart = (VIX - VIX3M).reindex(j.union(VIX.index)).ffill()
    w = (ecart.shift(1).reindex(j) < 0).astype(float)                                       # clôture de J-1

    def fab(k):
        cout = k * w.diff().abs().fillna(0)
        return w * r + (1 - w) * rf - cout, r, rf
    return fab


# ------------------------------------------------------------------ Z9, Z10 elan des cryptos sur 4 semaines
def crypto_elan(sym):
    px = RADAR[sym][["c"]].dropna(); px.index = pd.to_datetime(px.index)
    px = px.asfreq("D").ffill(); r = px["c"].pct_change(); rf = rf_jour(px.index, 365)
    signal = (px["c"] / px["c"].shift(28) - 1 > 0)
    dim = px.index.weekday == 6
    s = pd.Series(np.where(dim, signal.astype(float), np.nan), index=px.index).ffill()
    w = s.shift(1).fillna(0.0)                                                              # decide dimanche, joue lundi - dimanche

    def fab(k):
        cout = k * w.diff().abs().fillna(0)
        return w * r + (1 - w) * rf - cout, r, rf
    return fab


# ------------------------------------------------------------------ Z11 la nuit
def nuit(sym):
    px = FONDS[sym]; j = px.index; rf = rf_jour(j, 252)
    rn = px["o"] / px["c"].shift(1) - 1; r = rendement(px)

    def fab(k):
        return rn - 2 * k + 0 * rf, r, rf                                                   # investi la nuit seulement
    return fab


# ------------------------------------------------------------------ Z8 tendance de chaque marche (22 fonds)
def tsmom(k):
    ret = pd.DataFrame({s: FONDS[s]["c"].pct_change() for s in FONDS}).sort_index()
    px = pd.DataFrame({s: FONDS[s]["c"] for s in FONDS}).sort_index()
    rf = rf_jour(ret.index, 252)
    fins = ret.index[pd.Series(ret.index.to_period("M")) != pd.Series(ret.index.to_period("M")).shift(-1)]
    pos = pd.DataFrame(np.nan, index=ret.index, columns=ret.columns)
    for f in fins:
        i = ret.index.get_loc(f)
        if i < 253:
            continue
        sig = np.sign(px.iloc[i] / px.iloc[i - 252] - 1)
        vol = ret.iloc[i - 62:i + 1].std() * np.sqrt(252)
        p = (sig * (0.10 / vol).clip(upper=2.0)).where(px.iloc[i - 252].notna() & vol.notna())
        pos.loc[f] = p
    pos = pos.ffill().shift(1)                                                             # fixe a la fin du mois, joue ensuite
    n = pos.notna().sum(axis=1).replace(0, np.nan)
    poids = pos.div(n, axis=0).fillna(0.0)
    ex = (poids * ret.sub(rf, axis=0).fillna(0.0)).sum(axis=1)
    cout = k * poids.diff().abs().sum(axis=1).fillna(0)
    return (ex - cout)[n.notna()], poids


# ------------------------------------------------------------------ lancer
TESTS, RES = {}, {}
plan = [("Z1", "Tournant du mois · QQQ", tom("QQQ"), "2009-01-01", 252, K_FONDS),
        ("Z2", "Tournant du mois · SPY", tom("SPY"), "2009-01-01", 252, K_FONDS),
        ("Z3", "Exposition gérée par la volatilité · SPY", volgeree(FONDS["SPY"], 252, K_FONDS), "2016-01-01", 252, K_FONDS),
        ("Z4", "Exposition gérée par la volatilité · QQQ", volgeree(FONDS["QQQ"], 252, K_FONDS), "2016-01-01", 252, K_FONDS),
        ("Z5", "Exposition gérée par la volatilité · BTC", volgeree(RADAR["BTC-USD"].asfreq("D").ffill(), 365, K_CRYPTO), "2016-01-01", 365, K_CRYPTO),
        ("Z6", "Structure du VIX · SPY", vixfiltre("SPY"), "2015-01-01", 252, K_FONDS),
        ("Z7", "Structure du VIX · QQQ", vixfiltre("QQQ"), "2015-01-01", 252, K_FONDS),
        ("Z9", "Élan sur 4 semaines · BTC", crypto_elan("BTC-USD"), "2019-01-01", 365, K_CRYPTO),
        ("Z10", "Élan sur 4 semaines · ETH", crypto_elan("ETH-USD"), "2019-01-01", 365, K_CRYPTO),
        ("Z11", "La nuit seulement · QQQ", nuit("QQQ"), "2014-01-01", 252, K_FONDS)]
for cle, nom, fab, debut, an, k in plan:
    r = juger_timing(fab, pd.Timestamp(debut), pd.Timestamp("2026-10-30"), an, k)
    RES[cle] = dict(nom=nom, debut=debut, **r); TESTS[cle] = (r["t_test"], r["n_test"])
    print(f"{cle:4s} {nom:45s} alpha {r['alpha_an']:+.1%}/an t {r['t_alpha']:5.2f} | Sharpe {r['sharpe']:.2f} contre {r['sharpe_bh']:.2f} | "
          f"moitiés {r['alpha_moitie1']:+.1%} {r['alpha_moitie2']:+.1%} | frais x2 t {r['t_frais_doubles']:.2f} | "
          f"{r['rendement_an']:+.1%}/an contre {r['rendement_an_bh']:+.1%}, baisse {r['pire_baisse']:.0%} contre {r['pire_baisse_bh']:.0%}", flush=True)

if len(FONDS) >= 22:
    e, poids = tsmom(K_FONDS); e2, _ = tsmom(2 * K_FONDS)
    sel = e.index >= "2012-01-01"; e, e2 = e[sel], e2[sel]
    b, t = nw(e.to_numpy(), None); t2 = nw(e2.to_numpy(), None)[1][0]; m = len(e) // 2
    cs = (1 + e).cumprod()
    r = dict(rendement_exces_an=float(e.mean() * 252), t=float(t[0]), sharpe=sharpe(e, 252), moitie1=float(e.iloc[:m].mean() * 252),
             moitie2=float(e.iloc[m:].mean() * 252), t_frais_doubles=float(t2), pire_baisse=float((cs / cs.cummax() - 1).min()), jours=len(e),
             courbe=[[i.strftime("%Y-%m-%d"), round(float(x) * 10000)] for i, x in zip(cs.index[::5], cs.values[::5])])
    raisons = []
    if r["t"] < 2: raisons.append(f"t {r['t']:.2f} sous 2")
    if r["moitie1"] <= 0 or r["moitie2"] <= 0: raisons.append("perd sur une moitié")
    if r["t_frais_doubles"] < 1.5: raisons.append(f"frais doublés : t {r['t_frais_doubles']:.2f}")
    RES["Z8"] = dict(nom="Tendance de chaque marché · 22 fonds", debut="2012-01-01", raisons=raisons, **r); TESTS["Z8"] = (r["t"], len(e))
    print(f"Z8   Tendance de chaque marché · 22 fonds  exces {r['rendement_exces_an']:+.1%}/an t {r['t']:.2f} Sharpe {r['sharpe']:.2f} | "
          f"moitiés {r['moitie1']:+.1%} {r['moitie2']:+.1%} | frais x2 t {r['t_frais_doubles']:.2f} | baisse {r['pire_baisse']:.0%}", flush=True)
else:
    print("Z8 : pas de prix ajustés pour les 22 fonds, test non fait")

# Z12 : le Bot 3 en 1 sans les jours de structure du VIX inversee (rejeu de l'arene)
sys.path.insert(0, str(RACINE / "ml/arene")); sys.path.insert(0, str(RACINE / "ml"))
import bots as BT  # noqa: E402
B = BT.Base(os.environ["CACHE_DOSSIER"])
zt = BT.zone(B)
jours = pd.to_datetime([B.J[s] for s in range(len(B.J))])
ecart = (VIX - VIX3M).reindex(jours.union(VIX.index)).ffill()
inverse = (ecart.shift(1).reindex(jours) >= 0).to_numpy()                                   # clôture de la veille
garde = [t for t in zt if not inverse[t[0]]]


def profil(tr):
    r, dp, ntr = BT.journees(B, tr, 1, 400.0); r6, _, _ = BT.journees(B, tr, 1, 400.0, 6.0)
    m = BT.mesures(B, r, dp, ntr); m["t_frais6"] = BT.tst(r6[B.test]); return m


mb, mf = profil(zt), profil(garde)
raisons = []
if mf["t"] < 2: raisons.append("t sous 2")
if mf["t_avant"] <= 0 or mf["t_apres"] <= 0: raisons.append("négatif sur une moitié")
if mf["t_frais6"] < 1.5: raisons.append("ne tient pas avec 6 $ de frais")
if mf["annees_pos"] < 9: raisons.append(f"{mf['annees_pos']} années positives sur 13")
if mf["survie_60"] < mb["survie_60"] - 1e-9: raisons.append(f"survie {mf['survie_60']:.0%} sous celle du Bot 3 en 1 ({mb['survie_60']:.0%})")
if mf["grilles_an"] > mb["grilles_an"] + 1e-9: raisons.append(f"{mf['grilles_an']:.2f} masters grillés par an, plus que le Bot 3 en 1 ({mb['grilles_an']:.2f})")
if mf["pire_baisse"] < 1.25 * mb["pire_baisse"]: raisons.append("pire baisse trop profonde")
ninv = int(inverse[B.test].sum())
RES["Z12"] = dict(nom="Bot 3 en 1 sans les jours de VIX inversé", debut="2014-01-01", raisons=raisons, seances_evitees=ninv,
                  trades_evites=len(zt) - len(garde), base={k: mb[k] for k in ("par_seance", "t", "net_an", "grilles_an", "survie_60", "grille_250", "pire_baisse")},
                  **{k: mf[k] for k in ("par_seance", "t", "t_avant", "t_apres", "net_an", "grilles_an", "survie_60", "grille_250", "pire_baisse", "annees_pos", "t_frais6")})
TESTS["Z12"] = (mf["t"], len(B.test))
print(f"Z12  Bot 3 en 1 sans VIX inversé ({ninv} séances évitées) : {mf['par_seance']:+.1f} $/séance t {mf['t']:.2f}, net {mf['net_an']:,.0f} $/an, "
      f"{mf['grilles_an']:.2f} grillés/an, survie {mf['survie_60']:.0%}, grillé 1 an {mf['grille_250']:.0%} | Bot 3 en 1 : {mb['par_seance']:+.1f} $ t {mb['t']:.2f}, "
      f"net {mb['net_an']:,.0f} $, {mb['grilles_an']:.2f}, survie {mb['survie_60']:.0%}, grillé 1 an {mb['grille_250']:.0%}", flush=True)

# ------------------------------------------------------------------ Benjamini-Hochberg sur les 12
cles = list(TESTS); p = np.array([1 - stats.norm.cdf(TESTS[c][0]) for c in cles]); o = np.argsort(p)
ok = p[o] <= 0.05 * np.arange(1, len(p) + 1) / len(p); kk = (np.nonzero(ok)[0].max() + 1) if ok.any() else 0
bh = {cles[i] for i in o[:kk]}
print(f"\nFamille de {len(cles)} tests, source des fonds : {SOURCE}")
for c in cles:
    RES[c]["p"] = float(p[cles.index(c)]); RES[c]["bh"] = c in bh
    if c not in bh: RES[c]["raisons"].append("ne survit pas à Benjamini-Hochberg")
    RES[c]["retenu"] = not RES[c]["raisons"]
    print(f"{c:4s} {RES[c]['nom']:45s} {'RETENU' if RES[c]['retenu'] else 'non'}" + ("" if RES[c]["retenu"] else " : " + " ; ".join(RES[c]["raisons"])))
json.dump(dict(source=SOURCE, resultats=RES), open(SORTIE, "w"), ensure_ascii=False, separators=(",", ":"), allow_nan=False)
