#!/usr/bin/env python3
"""Radar (radar/README.md, protocole du 29 octobre 2026) : variables du NQ a chaque heure de decision, calculees avec ce
qui est connu a ce moment-la, et gains des trades. Ecrit <RADAR_CALCUL>/variables.npz.

Lancer : KB=<copie de claude/keen-babbage-r686cl> ROBOT=<zone/robot/nq_1min.csv.gz de main> RADAR_CALCUL=<dossier>
         python3 radar/variables.py"""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "scalping"))
import commun as K  # noqa: E402
import donnees as SD  # noqa: E402

KB = K.KB
DONNEES = ICI / "donnees"
CALCUL = Path(os.getenv("RADAR_CALCUL", str(ICI / "calcul")))
ENTREES = np.array([5, 15, 30, 60, 90, 120, 180, 240, 300, 330, 360])     # minutes apres 9 h 30
DUREES = [15, 30, 60, 120, 0]                                                # 0 : clôture de 16 h
FRAIS = 3.0                                                                  # $ par aller-retour et par MNQ
DEBUT = "2011-01-01"
AUTRES = {"ES": "intraday/donnees/sp500_1min.csv.gz", "RTY": "zone_multi/donnees/russell_1min.csv.gz",
          "YM": "zone_multi/donnees/dow_1min.csv.gz", "GC": "zone_multi/donnees/or_1min.csv.gz",
          "CL": "zone_multi/donnees/petrole_1min.csv.gz", "EU": "zone_multi/donnees/euro_1min.csv.gz",
          "BTC": "tournoi5/donnees/bitcoin_1min.csv.gz"}


# ------------------------------------------------------------------ prix du NQ
def nq():
    """Minutes du NQ 2011 - 2026 : donnees de la recherche, puis fichier du robot de la zone pour les jours suivants."""
    CALCUL.mkdir(parents=True, exist_ok=True)
    fusion = CALCUL / "nq_fusion.csv.gz"
    if not fusion.exists():
        a = pd.read_csv(KB / "intraday/donnees/nasdaq100_1min.csv.gz", dtype={"t": str})
        b = pd.read_csv(os.environ["ROBOT"], dtype={"t": str})
        fin_a = a["t"].str[:10].max()
        b = b[b["t"].str[:10] > fin_a]
        pd.concat([a, b], ignore_index=True).to_csv(fusion, index=False)
    return SD.minutes("NQ", chemin=fusion, debut=DEBUT)


def grille_autre(nom, jours):
    """Clotures d'un autre marche sur la grille seance x minute du NQ (9 h 30 - 15 h 59), a la meme heure de New York,
    prolongees a plat apres sa derniere minute du jour ; prix de 9 h 30 (derniere cloture connue avant 9 h 30 si le
    marche ouvre plus tot, sinon ouverture de 9 h 30) ; range de sa seance et cloture de sa seance."""
    d = pd.read_csv(KB / AUTRES[nom], usecols=["t", "o", "h", "l", "c"], dtype={"t": str})
    t = pd.to_datetime(d["t"])
    jour = t.dt.normalize().values.astype("datetime64[D]")
    m = (t.dt.hour * 60 + t.dt.minute).values
    ij = pd.DatetimeIndex(jours).get_indexer(pd.DatetimeIndex(jour))
    garde = ij >= 0
    S = len(jours)
    C = np.full((S, 960), np.nan)
    C[ij[garde], np.clip(m[garde], 0, 959)] = d["c"].values[garde]
    C = pd.DataFrame(C).ffill(axis=1).values
    O = np.full((S, 960), np.nan)
    O[ij[garde], np.clip(m[garde], 0, 959)] = d["o"].values[garde]
    p930 = np.where(np.isfinite(C[:, 569]), C[:, 569], O[:, 570])
    grille = C[:, 570:960]
    hi = pd.Series(d["h"].values[garde]).groupby(ij[garde]).max().reindex(range(S)).values
    lo = pd.Series(d["l"].values[garde]).groupby(ij[garde]).min().reindex(range(S)).values
    clo = pd.Series(d["c"].values[garde]).groupby(ij[garde]).last().reindex(range(S)).values
    return grille, p930, hi - lo, clo


def moyenne_avant(x, n, ok):
    """Moyenne des n dernieres valeurs (seances ok) strictement avant chaque seance."""
    s = pd.Series(np.where(ok, x, np.nan))
    return s.shift(1).rolling(n, min_periods=max(5, n // 2)).mean().values


# ------------------------------------------------------------------ gains
def gains(d):
    """g[e, H] : gain brut d'un achat par seance en $ par MNQ au prix d'aujourd'hui (vente = −g) ; NaN si non jouable."""
    O, C = d["o"], d["c"]
    ok = d["complete"] & ~d["ech"]
    ech = float(d["pref"]) / O[:, 0] * float(d["pt"])
    G = {}
    for e in ENTREES:
        for H in DUREES:
            x = e + H if H else None
            if H and x > 389:
                continue
            sortie = O[:, x] if H else C[:, 389]
            g = (sortie - O[:, e]) * ech
            G[(int(e), H)] = np.where(ok, g, np.nan)
    return G


# ------------------------------------------------------------------ variables
def variables_nq(d):
    O, Hh, L, C, V = d["o"], d["h"], d["l"], d["c"], d["v"]
    S = len(O)
    ok = d["complete"] & ~d["ech"]
    pm = d["prec_meme"]
    rng = Hh.max(1) - L.min(1)
    A20 = moyenne_avant(rng, 20, d["complete"])
    A100 = moyenne_avant(rng, 100, d["complete"])
    a = np.where(A20 > 0, A20, np.nan)
    prevC = np.where(pm >= 0, C[np.maximum(pm, 0), 389], np.nan)
    prevH = np.where(pm >= 0, Hh[np.maximum(pm, 0)].max(1), np.nan)
    prevL = np.where(pm >= 0, L[np.maximum(pm, 0)].min(1), np.nan)
    tp = (Hh + L + C) / 3
    cv = np.cumsum(V, 1)
    vwap = np.cumsum(tp * V, 1) / np.where(cv > 0, cv, np.nan)
    cv_moy = np.vstack([moyenne_avant(cv[:, j], 20, d["complete"]) for j in range(390)]).T
    cmax, cmin = np.maximum.accumulate(Hh, 1), np.minimum.accumulate(L, 1)
    dc = np.abs(np.diff(np.c_[O[:, :1], C], axis=1)).cumsum(1)
    h30, l30 = Hh[:, :30].max(1), L[:, :30].min(1)
    autres = {n: grille_autre(n, d["jours"]) for n in AUTRES}
    A20_aut = {n: moyenne_avant(g[2], 20, np.isfinite(g[2])) for n, g in autres.items()}
    out = {}
    for e in ENTREES:
        j = e - 1
        f = {}
        f["ouv"] = (C[:, j] - O[:, 0]) / a
        for k in (15, 30, 60):
            f[f"r{k}"] = (C[:, j] - C[:, j - k]) / a if j - k >= 0 else np.full(S, np.nan)
        f["place"] = (C[:, j] - cmin[:, j]) / np.where(cmax[:, j] > cmin[:, j], cmax[:, j] - cmin[:, j], np.nan)
        f["amp"] = (cmax[:, j] - cmin[:, j]) / a
        f["vwap"] = (C[:, j] - vwap[:, j]) / a
        f["volc"] = cv[:, j] / cv_moy[:, j]
        v15 = cv[:, j] - (cv[:, j - 15] if j >= 15 else 0)
        v15m = cv_moy[:, j] - (cv_moy[:, j - 15] if j >= 15 else 0)
        f["vol15"] = v15 / v15m if j >= 15 else np.full(S, np.nan)
        f["ecart"] = (O[:, 0] - prevC) / a
        f["d_hv"] = (C[:, j] - prevH) / a
        f["d_bv"] = (C[:, j] - prevL) / a
        f["or30"] = (C[:, j] - (h30 + l30) / 2) / (h30 - l30) if e > 30 else np.full(S, np.nan)
        f["eff"] = np.abs(C[:, j] - O[:, 0]) / np.where(dc[:, j] > 0, dc[:, j], np.nan)
        f["rond_h"] = (np.ceil(C[:, j] / 100) * 100 - C[:, j]) / a
        f["rond_b"] = (C[:, j] - np.floor(C[:, j] / 100) * 100) / a
        f["age_h"] = (j - np.argmax(Hh[:, :e], 1)) / e
        f["age_b"] = (j - np.argmin(L[:, :e], 1)) / e
        for n, (g, p930, _, _) in autres.items():
            an = A20_aut[n]
            f[f"{n}_ouv"] = (g[:, j] - p930) / an
            f[f"{n}_r30"] = (g[:, j] - g[:, j - 30]) / an if j >= 30 else np.full(S, np.nan)
        f["nq_es"] = f["ouv"] - f["ES_ouv"]
        f["nq_es30"] = f["r30"] - f["ES_r30"] if j >= 30 else np.full(S, np.nan)
        out[int(e)] = f
    return out, dict(A20=A20, A100=A100, prevC=prevC, rng=rng, ok=ok)


def serie_jour(d):
    """Cours de cloture ajuste des changements de contrat (log), RTH."""
    C, O = d["c"][:, 389], d["o"][:, 0]
    pm = d["prec_meme"]
    r = np.where(pm >= 0, np.log(C / np.where(pm >= 0, d["c"][np.maximum(pm, 0), 389], np.nan)), np.log(C / O))
    r = np.where(d["complete"], r, 0.0)
    return np.cumsum(np.nan_to_num(r)), r


def variables_jour(d, aux):
    """Variables connues avant l'ouverture (identiques a toutes les heures de decision)."""
    S = len(d["o"])
    jours = pd.DatetimeIndex(d["jours"])
    O, Hh, L, C = d["o"], d["h"], d["l"], d["c"]
    pt = d["prec_tout"]
    a = aux["A20"]
    f = {}
    p = np.maximum(pt, 0)
    v = pt >= 0
    f["j_ret"] = np.where(v, (C[p, 389] - O[p, 0]) / a, np.nan)
    f["j_place"] = np.where(v, (C[p, 389] - L[p].min(1)) / np.maximum(Hh[p].max(1) - L[p].min(1), 1e-9), np.nan)
    f["j_amp"] = np.where(v, aux["rng"][p] / a, np.nan)
    lp, r = serie_jour(d)
    sig = pd.Series(np.where(d["complete"], r, np.nan)).rolling(20, min_periods=10).std().values
    lpv = np.where(v, lp[p], np.nan)
    sgv = np.where(v, sig[p], np.nan)

    def recul(k):
        q = p.copy()
        for _ in range(k):
            q = np.where(q >= 0, pt[np.maximum(q, 0)], -1)
        return np.where(q >= 0, lp[np.maximum(q, 0)], np.nan)

    f["j_r5"] = (lpv - recul(5)) / (sgv * np.sqrt(5))
    f["j_r20"] = (lpv - recul(20)) / (sgv * np.sqrt(20))
    s = pd.Series(lp)
    for n in (50, 200):
        ma = s.rolling(n, min_periods=n // 2).mean().values
        f[f"j_ma{n}"] = np.where(v, (lp[p] - ma[p]) / sig[p], np.nan)
    hausse = np.where(r > 0, r, 0.0)
    baisse = np.where(r < 0, -r, 0.0)
    mh = pd.Series(hausse).ewm(alpha=0.5, adjust=False).mean().values
    mb = pd.Series(baisse).ewm(alpha=0.5, adjust=False).mean().values
    rsi = 100 * mh / np.maximum(mh + mb, 1e-12)
    f["j_rsi2"] = np.where(v, rsi[p], np.nan)
    serie = np.zeros(S)
    for i in range(1, S):
        serie[i] = (max(serie[i - 1], 0) + 1 if r[i] > 0 else min(serie[i - 1], 0) - 1 if r[i] < 0 else 0)
    f["j_serie"] = np.where(v, np.clip(serie[p], -5, 5), np.nan)
    f["j_volreg"] = aux["A20"] / aux["A100"]
    # calendrier (connu d'avance)
    b = {}
    for k, nom in enumerate(["lundi", "mardi", "mercredi", "jeudi", "vendredi"]):
        b[f"cal_{nom}"] = jours.dayofweek == k
    mois = jours.to_period("M")
    rang = pd.Series(1, index=range(S)).groupby(mois).cumsum().values
    reste = pd.Series(1, index=range(S))[::-1].groupby(mois[::-1]).cumsum()[::-1].values
    b["cal_debut_mois"] = rang <= 2
    b["cal_fin_mois"] = reste <= 2
    b["cal_mi_mois"] = (jours.day >= 14) & (jours.day <= 16)
    trois = set(pd.date_range(jours[0], jours[-1] + pd.Timedelta(days=40), freq="WOM-3FRI").normalize())
    opex = np.array([x in trois for x in jours])
    b["cal_opex"] = opex
    semaine = jours.to_period("W-FRI")
    sem_opex = set(semaine[opex])
    b["cal_semaine_opex"] = np.array([w in sem_opex for w in semaine])
    b["cal_lendemain_opex"] = np.r_[False, opex[:-1]]
    vixexp = {x - pd.Timedelta(days=30) for x in trois}          # mercredi, 30 jours avant l'echeance du mois suivant
    b["cal_echeance_vix"] = np.array([x in vixexp for x in jours])
    sys.path.insert(0, str(KB / "fonds"))
    import fomc as FO
    fed = pd.DatetimeIndex(sorted(set(FO.annonces()))).normalize()
    fed_set = set(fed)
    ifed = np.array([x in fed_set for x in jours])
    b["cal_fed"] = ifed
    b["cal_veille_fed"] = np.r_[ifed[1:], False]
    b["cal_lendemain_fed"] = np.r_[False, ifed[:-1]]
    b["cal_emploi"] = (jours.dayofweek == 4) & (jours.day <= 7)
    trim = jours.month.isin([3, 6, 9, 12])
    b["cal_fin_trimestre"] = np.asarray(trim) & (reste <= 3)
    suivant = np.r_[jours[1:], jours[-1:] + pd.Timedelta(days=1)]
    precedent = np.r_[jours[:1] - pd.Timedelta(days=1), jours[:-1]]
    b["cal_veille_ferie"] = np.array([(n - x).days > (3 if x.dayofweek == 4 else 1) for x, n in zip(jours, suivant)])
    b["cal_lendemain_ferie"] = np.array([(x - q).days > (3 if x.dayofweek == 0 else 1) for x, q in zip(jours, precedent)])
    return f, b


def lire_vix(nom):
    t = pd.read_csv(KB / f"evolution2/donnees/{nom}.csv")
    t.columns = [c.strip().lower() for c in t.columns]
    dcol = [c for c in t.columns if "date" in c][0]
    ccol = [c for c in t.columns if "close" in c][0]
    return pd.Series(t[ccol].values, index=pd.to_datetime(t[dcol])).sort_index()


def veille(serie, jours, decalage_jours=1, age_max=14):
    """Derniere valeur publiee au plus tard `decalage_jours` jours ouvres avant chaque seance (NaN si elle date de plus
    de `age_max` jours : source arretee ou en retard)."""
    s = serie.dropna().sort_index()
    s = s[~s.index.duplicated(keep="last")]
    limite = pd.DatetimeIndex(jours) - pd.offsets.BDay(decalage_jours)
    i = s.index.searchsorted(limite, side="right") - 1
    v = np.where(i >= 0, s.values[np.maximum(i, 0)], np.nan)
    age = (limite - s.index[np.maximum(i, 0)]).days
    return np.where(np.asarray(age) <= age_max, v, np.nan)


def zscore_avant(s, n=60):
    s = s.astype(float)
    m = s.rolling(n, min_periods=n // 2).mean().shift(1)
    e = s.rolling(n, min_periods=n // 2).std().shift(1)
    return (s - m) / e


def rang_avant(s, n=252):
    return s.rolling(n, min_periods=n // 2).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True)


def variables_externes(d):
    jours = pd.DatetimeIndex(d["jours"])
    f = {}
    vix, v3, v9 = lire_vix("vix"), lire_vix("vix3m"), lire_vix("vix9d")
    f["vix_rang"] = veille(rang_avant(vix), jours)
    f["vix_var"] = veille(np.log(vix).diff(), jours)
    f["vix_terme"] = veille(vix / v3, jours)
    f["vix_9j"] = veille(v9 / vix, jours)
    f["vix_ma20"] = veille(vix / vix.rolling(20).mean(), jours)
    sq = pd.read_csv(KB / "evolution2/donnees/dix_gex.csv", parse_dates=["date"]).set_index("date")
    f["dix"] = veille(sq["dix"], jours)
    f["dix_var5"] = veille(sq["dix"].diff(5), jours)
    f["gex"] = veille(zscore_avant(sq["gex"], 252), jours)
    cot = pd.read_csv(ICI.parent / "flux/donnees/cot/cot_nq.csv")
    cot["date"] = pd.to_datetime(cot["Report_Date_as_YYYY-MM-DD"], format="mixed")
    cot = cot.groupby("date").sum(numeric_only=True)
    oi = cot["Open_Interest_All"]
    for nom, cle in (("cot_levier", "Lev_Money"), ("cot_gerants", "Asset_Mgr"), ("cot_banques", "Dealer")):
        net = (cot[f"{cle}_Positions_Long_All"] - cot[f"{cle}_Positions_Short_All"]) / oi
        z = (net - net.rolling(52, min_periods=26).mean()) / net.rolling(52, min_periods=26).std()
        z.index = z.index + pd.Timedelta(days=6)              # mardi -> lundi suivant (publie le vendredi)
        f[nom] = veille(z, jours, 0)
    # 10 grandes valeurs (cotes de 30 en 30 minutes, 2016 - 2026)
    g = pd.read_csv(KB / "vague4/donnees/grandes.csv.gz", parse_dates=["jour"])
    piv_o = g.pivot(index="jour", columns="valeur", values="ouverture")
    piv_c = g.pivot(index="jour", columns="valeur", values="c390")
    ret = piv_c / piv_o - 1
    f["g_largeur"] = veille((ret > 0).mean(axis=1).where(ret.notna().sum(axis=1) >= 8), jours)
    f["g_dispersion"] = veille(ret.std(axis=1), jours)
    gap = (piv_o / piv_c.shift(1) - 1).reindex(jours)
    ouvnq = (d["o"][:, 0] - np.where(d["prec_meme"] >= 0, d["c"][np.maximum(d["prec_meme"], 0), 389], np.nan)) / \
        d["o"][:, 0]
    f["g_ecart_rel"] = gap.mean(axis=1).values - ouvnq
    f["g_ecart_disp"] = gap.std(axis=1).values
    return f, g


def grandes_intraday(g, jours, e):
    """Part des 10 grandes au-dessus de leur ouverture au dernier relevé de 30 minutes connu a la decision."""
    k = (e - 1) // 30 * 30
    if k < 30:
        return np.full(len(jours), np.nan)
    piv = g.pivot(index="jour", columns="valeur", values=f"c{k}")
    po = g.pivot(index="jour", columns="valeur", values="ouverture")
    x = (piv > po).mean(axis=1).where(piv.notna().sum(axis=1) >= 8)
    return x.reindex(pd.DatetimeIndex(jours)).values


# ------------------------------------------------------------------ sources nouvelles (radar/donnees, collecte.py)
def lire_long(famille):
    fs = sorted((DONNEES / "jour" / famille).glob("*.csv.gz"))
    if not fs:
        return None
    t = pd.concat([pd.read_csv(f, dtype={"date": str, "serie": str}) for f in fs], ignore_index=True)
    t["date"] = pd.to_datetime(t["date"])
    t["valeur"] = pd.to_numeric(t["valeur"], errors="coerce")
    return t.pivot_table(index="date", columns="serie", values="valeur", aggfunc="last").sort_index()


def variables_nouvelles(d):
    """Variables des sources du radar. Celles dont la source manque sont simplement absentes."""
    jours = pd.DatetimeIndex(d["jours"])
    f = {}
    fin = lire_long("finra")
    if fin is not None:
        def part(syms):
            cs = [f"{s}:court" for s in syms if f"{s}:court" in fin]
            ts = [f"{s}:total" for s in syms if f"{s}:total" in fin]
            return fin[cs].sum(axis=1, min_count=1) / fin[ts].sum(axis=1, min_count=1)
        import collecte as CO
        ndx = [s for s in CO.FINRA if s not in ("QQQ", "TQQQ", "SQQQ", "QLD", "SPY", "SSO", "UPRO", "SPXU", "IWM",
                                                "DIA", "SMH", "SOXL", "SOXS", "XLK", "TLT", "HYG", "GLD", "VXX",
                                                "UVXY", "SVXY", "ARKK", "JPM", "GS", "MSTR", "COIN", "PLTR", "ARM",
                                                "SMCI")]
        for nom, syms in (("qqq", ["QQQ"]), ("levier", ["TQQQ", "SQQQ", "QLD"]), ("ndx", ndx)):
            p = part(syms)
            f[f"finra_{nom}"] = veille(p, jours)
            f[f"finra_{nom}_z"] = veille(zscore_avant(p, 60), jours)
    alt = lire_long("alt")
    if alt is not None:
        groupes = {"peur": ["Stock_market_crash", "Recession", "Bear_market", "Margin_call", "Black_Monday_(1987)",
                            "Stagflation", "Bank_run"],
                   "marche": ["Stock_market", "Nasdaq", "NASDAQ-100", "Day_trading", "Options_(finance)"],
                   "ia": ["Nvidia", "Artificial_intelligence", "ChatGPT"],
                   "macro": ["Inflation", "Interest_rate", "Federal_Reserve", "Quantitative_easing", "Unemployment",
                             "Layoff", "Yield_curve"],
                   "crypto": ["Bitcoin"]}
        for nom, arts in groupes.items():
            cols = [f"wiki:{x}" for x in arts if f"wiki:{x}" in alt]
            if not cols:
                continue
            lv = np.log(alt[cols].clip(lower=1))
            z = ((lv - lv.rolling(30, min_periods=15).mean().shift(1)) /
                 lv.rolling(30, min_periods=15).std().shift(1)).mean(axis=1)
            f[f"wiki_{nom}"] = veille(z, jours)
        series = {"fred_hy5": ("fred:BAMLH0A0HYM2", "diff5", 2), "fred_courbe": ("fred:T10Y2Y", "niveau", 2),
                  "fred_reel": ("fred:DFII10", "diff5", 2), "fred_rrp": ("fred:RRPONTSYD", "diff5", 2),
                  "fred_tresor": ("fred:WTREGEN", "diff1", 7), "fred_reserves": ("fred:WRESBAL", "diff1", 7),
                  "fred_stress": ("fred:STLFSI4", "niveau", 7), "fred_nfci": ("fred:NFCI", "niveau", 7),
                  "fred_incertitude": ("fred:USEPUINDXD", "z", 2), "fred_chomage_ins": ("fred:ICSA", "z", 7),
                  "aaii_ecart": (None, None, 1), "sq_dix_raw": (None, None, 1)}
        for nom, (col, mode, lag) in series.items():
            if col is None or col not in alt:
                continue
            s = alt[col].dropna()
            x = s.diff(5) if mode == "diff5" else s.diff(1) if mode == "diff1" else \
                zscore_avant(s, 60) if mode == "z" else s
            f[nom] = veille(x, jours, lag)
        if "aaii:bullish" in alt and "aaii:bearish" in alt:
            f["aaii_ecart"] = veille((alt["aaii:bullish"] - alt["aaii:bearish"]).dropna(), jours, 1)
        if "cnn:fear_and_greed_historical" in alt:
            f["cnn_peur"] = veille(alt["cnn:fear_and_greed_historical"].dropna(), jours, 1)
    ya = lire_long("yahoo")
    if ya is not None:
        def c(s):
            return ya.get(f"{s}:c")

        def o(s):
            return ya.get(f"{s}:o")

        def ret(s):
            x = c(s)
            return None if x is None else np.log(x.dropna()).diff()
        for nom, s in (("skew", "^SKEW"), ("vvix", "^VVIX"), ("move", "^MOVE"), ("ovx", "^OVX"), ("vxn", "^VXN")):
            if c(s) is not None:
                f[f"y_{nom}"] = veille(rang_avant(c(s).dropna()), jours)
        for nom, s in (("dollar", "DX-Y.NYB"), ("tlt", "TLT"), ("hyg", "HYG"), ("btc", "BTC-USD"), ("taux10", "^TNX"),
                       ("petrole", "CL=F"), ("or", "GC=F"), ("cuivre", "HG=F"), ("yen", "6J=F")):
            r = ret(s)
            if r is not None:
                f[f"y_{nom}"] = veille(r, jours)
        if c("XLK") is not None and c("SPY") is not None:
            f["y_tech_rel"] = veille((np.log(c("XLK")) - np.log(c("SPY"))).diff(), jours)
        if c("SMH") is not None and c("QQQ") is not None:
            f["y_semi_rel"] = veille((np.log(c("SMH")) - np.log(c("QQQ"))).diff(), jours)
        if c("RSP") is not None and c("SPY") is not None:
            f["y_egal_rel"] = veille((np.log(c("RSP")) - np.log(c("SPY"))).diff(5), jours)
        for nom, s in (("nikkei", "^N225"), ("hangseng", "^HSI")):
            r = ret(s)
            if r is not None:
                f[f"y_{nom}_jour"] = veille(r, jours, 0)        # fermes avant 9 h 30 a New York
        if o("^GDAXI") is not None:
            gap = (np.log(o("^GDAXI")) - np.log(c("^GDAXI")).shift(1)).dropna()
            f["y_dax_ouv"] = veille(gap, jours, 0)              # ouverture de Francfort (3 h a New York)
        for nom, s in (("tqqq", "TQQQ"), ("vxx", "VXX")):
            v = ya.get(f"{s}:v")
            if v is not None:
                f[f"y_vol_{nom}"] = veille(zscore_avant(np.log(v.clip(lower=1)), 60), jours)
    res = DONNEES / "evenements" / "resultats.csv"
    if res.exists():
        r = pd.read_csv(res)
        r = r[r["symbole"].isin(["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "TSLA", "NFLX", "COST"])]
        t = pd.to_datetime(r["t"])
        # publie apres la cloture -> seance suivante ; avant l'ouverture -> meme seance
        cible = np.where(t.dt.hour >= 16, (t.dt.normalize() + pd.offsets.BDay(1)), t.dt.normalize())
        cnt = pd.Series(1, index=pd.DatetimeIndex(cible)).groupby(level=0).sum()
        f["_cal_resultats"] = cnt.reindex(jours).fillna(0).values > 0
    return f


def tout():
    d = nq()
    G = gains(d)
    intra, aux = variables_nq(d)
    fj, b = variables_jour(d, aux)
    fe, g = variables_externes(d)
    sys.path.insert(0, str(ICI))
    fn = variables_nouvelles(d)
    for k in [k for k in fn if k.startswith("_cal_")]:
        b[k[1:]] = fn.pop(k)
    jours = d["jours"]
    noms_j = list(fj) + list(fe) + list(fn)
    X = {}
    for e in ENTREES:
        f = dict(intra[int(e)])
        f["g_intra"] = grandes_intraday(g, jours, int(e))
        f.update(fj)
        f.update(fe)
        f.update(fn)
        X[int(e)] = f
    noms = list(X[int(ENTREES[0])])
    cube = np.stack([np.column_stack([np.asarray(X[int(e)][n], float) for n in noms]) for e in ENTREES])
    binaires = sorted(b)
    B = np.column_stack([np.asarray(b[n], bool) for n in binaires])
    gk = sorted(G)
    gains_arr = np.stack([G[k] for k in gk])
    ok = aux["ok"]
    CALCUL.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CALCUL / "variables.npz", cube=cube.astype(np.float32), noms=np.array(noms),
                        B=B, binaires=np.array(binaires), gains=gains_arr, cles=np.array(gk), ok=ok,
                        jours=jours.astype("datetime64[D]"), entrees=ENTREES, noms_jour=np.array(noms_j))
    print(f"{len(jours)} seances ({jours[0]} - {jours[-1]}), jouables {ok.sum()} ; {len(noms)} variables continues "
          f"({len(noms_j)} d'avant l'ouverture), {len(binaires)} du calendrier ; {len(gk)} couples entree-duree")
    for i, n in enumerate(noms):
        x = cube[:, :, i]
        print(f"  {n:<18} presente {np.isfinite(x).mean():6.1%}  1re seance {jours[np.argmax(np.isfinite(x).any(0))]}")


if __name__ == "__main__":
    tout()
