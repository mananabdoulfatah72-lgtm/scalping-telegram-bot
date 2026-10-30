#!/usr/bin/env python3
"""Radar, collecte (radar/README.md) : chaque soir de semaine, recupere les donnees gratuites de plus de 150 series
(futures, indices, volatilite, taux, devises, matieres premieres, crypto, ETF, grandes valeurs du Nasdaq 100, ventes a
decouvert FINRA, gamma et DIX, pages Wikipedia, FRED, peur et avidite de CNN, sentiment AAII, dates de resultats,
options du Nasdaq 100 chez le CBOE, ton des nouvelles GDELT) et les garde dans radar/donnees/. Lance par
.github/workflows/radar.yml (ces sites ne sont pas joignables depuis l'environnement de Claude).

Stockage (jamais reecrit une fois le mois passe, pour que le depot grossisse peu) :
  donnees/jour/<famille>/<AAAA>.csv.gz avant 2026, <AAAA-MM>.csv.gz ensuite : colonnes date, serie, valeur
  donnees/heure/<AAAA ou AAAA-MM>.csv.gz : barres d'une heure (t a New York, symbole, o, h, l, c, v)
  donnees/minutes/<AAAA>/<AAAA-MM-JJ>.csv.gz : barres d'une minute de la journee, tous les symboles
  donnees/options/<AAAA>/<AAAA-MM-JJ>_<sous-jacent>.csv.gz : gamma par prix d'exercice (photo du soir)
  donnees/evenements/resultats.csv : dates de publication des resultats des grandes valeurs
  donnees/etat.json : ce que chaque source a donne au dernier passage"""
import concurrent.futures as cf
import datetime as dt
import io
import json
import os
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ICI = Path(__file__).resolve().parent
DONNEES = ICI / "donnees"
NY = "America/New_York"
AN_MOIS = 2026                       # a partir de cette annee : un fichier par mois au lieu d'un par an
NAVIGATEUR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/126.0 Safari/537.36"}
RECHERCHE = {"User-Agent": "radar-recherche/1.0 (github.com/mananabdoulfatah72-lgtm/scalping-telegram-bot)"}

FUTURES = ["NQ=F", "ES=F", "YM=F", "RTY=F", "CL=F", "BZ=F", "NG=F", "RB=F", "HO=F", "GC=F", "SI=F", "HG=F", "PL=F",
           "PA=F", "ZN=F", "ZB=F", "ZF=F", "ZT=F", "6E=F", "6J=F", "6B=F", "6A=F", "6C=F", "6S=F", "ZC=F", "ZW=F",
           "ZS=F", "ZL=F", "KC=F", "SB=F", "CC=F", "CT=F", "LE=F", "HE=F", "BTC=F"]
INDICES = ["^NDX", "^GSPC", "^DJI", "^RUT", "^SOX", "^NYA", "^VIX", "^VXN", "^VIX9D", "^VIX3M", "^VIX6M", "^VVIX",
           "^SKEW", "^OVX", "^GVZ", "^MOVE", "^TNX", "^IRX", "^FVX", "^TYX", "DX-Y.NYB", "^N225", "^HSI", "^GDAXI",
           "^FTSE", "^STOXX50E", "^FCHI", "000001.SS", "^KS11", "^AXJO", "^BSESN", "^TWII", "^BVSP", "^MXX"]
ETF = ["QQQ", "TQQQ", "SQQQ", "QLD", "SPY", "SSO", "UPRO", "SPXU", "IWM", "DIA", "TLT", "IEF", "SHY", "TIP", "HYG",
       "LQD", "JNK", "GLD", "SLV", "USO", "UNG", "UUP", "FXE", "FXY", "EEM", "EFA", "FXI", "EWJ", "EWG", "EWZ", "XLK",
       "XLF", "XLE", "XLV", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE", "XLC", "SMH", "SOXX", "SOXL", "ARKK", "KRE",
       "XBI", "IBB", "VNQ", "XHB", "ITB", "IYT", "MTUM", "QUAL", "USMV", "VLUE", "RSP", "QQEW", "VXX", "SVXY", "BITO",
       "IBIT"]
GRANDES = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "AVGO", "TSLA", "COST", "NFLX", "AMD", "ADBE",
           "PEP", "CSCO", "TMUS", "INTC", "QCOM", "TXN", "AMAT", "INTU", "ISRG", "BKNG", "MU", "LRCX", "PANW", "ASML",
           "PLTR", "ARM", "MSTR", "COIN", "SMCI", "JPM", "GS", "BRK-B"]
CRYPTO = ["BTC-USD", "ETH-USD", "SOL-USD"]
UNIVERS_JOUR = FUTURES + INDICES + ETF + GRANDES + CRYPTO
UNIVERS_HEURE = ["NQ=F", "ES=F", "YM=F", "RTY=F", "CL=F", "GC=F", "SI=F", "HG=F", "NG=F", "ZN=F", "ZB=F", "6E=F",
                 "6J=F", "6B=F", "^VIX", "^VXN", "DX-Y.NYB", "^N225", "^GDAXI", "^FTSE", "^HSI", "QQQ", "TQQQ", "SPY",
                 "TLT", "HYG", "SMH", "NVDA", "AAPL", "MSFT", "AMZN", "META", "GOOGL", "AVGO", "TSLA", "BTC-USD",
                 "ETH-USD"]
UNIVERS_MINUTE = ["NQ=F", "ES=F", "YM=F", "RTY=F", "CL=F", "GC=F", "SI=F", "HG=F", "NG=F", "ZN=F", "ZB=F", "6E=F",
                  "6J=F", "^VIX", "DX-Y.NYB", "QQQ", "TQQQ", "SPY", "SMH", "NVDA", "AAPL", "MSFT", "AMZN", "META",
                  "GOOGL", "AVGO", "TSLA", "BTC-USD"]
FINRA = ["QQQ", "TQQQ", "SQQQ", "QLD", "SPY", "SSO", "UPRO", "SPXU", "IWM", "DIA", "SMH", "SOXL", "SOXS", "XLK", "TLT",
         "HYG", "GLD", "VXX", "UVXY", "SVXY", "ARKK"] + [g for g in GRANDES if g not in ("GOOG", "BRK-B")] + [
         "ABNB", "ADI", "ADP", "AEP", "ALGN", "AMGN", "ANSS", "AZN", "BIIB", "BKR", "CDNS", "CEG", "CHTR", "CMCSA",
         "CPRT", "CRWD", "CSGP", "CSX", "CTAS", "CTSH", "DDOG", "DLTR", "DXCM", "EA", "EXC", "FANG", "FAST", "FTNT",
         "GEHC", "GFS", "GILD", "HON", "IDXX", "ILMN", "KDP", "KHC", "KLAC", "LULU", "MAR", "MCHP", "MDB", "MDLZ",
         "MELI", "MNST", "MRVL", "NXPI", "ODFL", "ON", "ORLY", "PAYX", "PCAR", "PDD", "PYPL", "REGN", "ROP", "ROST",
         "SBUX", "SNPS", "TEAM", "TTD", "TTWO", "VRSK", "VRTX", "WBD", "WDAY", "XEL", "ZS"]
WIKI = ["Stock_market_crash", "Recession", "Inflation", "Stock_market", "Bear_market", "Nasdaq", "NASDAQ-100",
        "Federal_Reserve", "Interest_rate", "Unemployment", "Layoff", "Bank_run", "Short_(finance)", "Margin_call",
        "Bitcoin", "Nvidia", "Artificial_intelligence", "ChatGPT", "Tariff", "United_States_debt_ceiling",
        "Quantitative_easing", "Stagflation", "Dot-com_bubble", "Black_Monday_(1987)", "Volatility_(finance)",
        "Options_(finance)", "Day_trading", "GameStop", "Gold_as_an_investment", "Yield_curve"]
FRED_ESSENTIELLES = ["BAMLH0A0HYM2", "T10Y2Y", "DFII10", "RRPONTSYD", "WTREGEN", "WRESBAL", "STLFSI4", "NFCI",
                     "USEPUINDXD", "ICSA"]
FRED = ["DGS10", "DGS2", "DGS3MO", "T10Y2Y", "T10Y3M", "T10YIE", "DFII10", "BAMLH0A0HYM2", "BAMLC0A0CM", "DTWEXBGS",
        "DEXJPUS", "DEXUSEU", "VIXCLS", "VXNCLS", "RRPONTSYD", "WALCL", "WTREGEN", "WRESBAL", "NFCI", "ANFCI",
        "STLFSI4", "ICSA", "CCSA", "SOFR", "EFFR", "DCOILWTICO", "DHHNGSP", "USEPUINDXD", "WLEMUINDXD", "SP500",
        "NASDAQCOM", "NASDAQ100", "MORTGAGE30US", "UMCSENT", "CPIAUCSL", "PAYEMS", "UNRATE", "INDPRO", "M2SL"]
GDELT = {"marche": '"stock market"', "fed": '"Federal Reserve"', "recession": "recession", "inflation": "inflation",
         "nvidia": "Nvidia", "droits": "tariffs", "ia": '"artificial intelligence"', "krach": "crash stocks"}
OPTIONS = {"NDX": "_NDX", "QQQ": "QQQ", "SPX": "_SPX"}

ETAT = {}


def noter(source, **info):
    ETAT[source] = {"heure_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M"), **info}
    print(f"{source} : " + ", ".join(f"{k} {v}" for k, v in info.items()), flush=True)


def get(url, essais=3, attente=5, entetes=None, **kw):
    for k in range(essais):
        try:
            r = requests.get(url, timeout=60, headers=entetes or NAVIGATEUR, **kw)
            if r.status_code == 200:
                return r
            if r.status_code in (400, 403, 404):
                return r
        except requests.RequestException:
            pass
        time.sleep(attente * (k + 1))
    return None


# ------------------------------------------------------------------ stockage
def cle_fichier(jour):
    j = pd.Timestamp(jour)
    return f"{j.year}" if j.year < AN_MOIS else f"{j.year}-{j.month:02d}"


def ranger(t, dossier, colonne_date, cles):
    """Ajoute les lignes de t (DataFrame) dans dossier/<annee ou mois>.csv.gz. Un fichier deja ecrit d'un mois (ou d'une
    annee) termine depuis plus de 40 jours ne recoit que les lignes qui lui manquent, sans que ses valeurs changent."""
    if t is None or len(t) == 0:
        return 0
    dossier.mkdir(parents=True, exist_ok=True)
    t = t.copy()
    jours = pd.to_datetime(t[colonne_date].astype(str).str[:10])
    t["_f"] = [cle_fichier(j) for j in jours]
    limite = pd.Timestamp.today().normalize() - pd.Timedelta(days=40)
    n = 0
    for f, part in t.groupby("_f"):
        part = part.drop(columns="_f")
        chemin = dossier / f"{f}.csv.gz"
        fin_periode = (pd.Timestamp(f"{f}-12-31") if len(f) == 4 else pd.Period(f).end_time.normalize())
        if chemin.exists():
            ancien = pd.read_csv(chemin, dtype=str)
            part = part.astype(str)
            if fin_periode < limite:
                cle_anc = set(map(tuple, ancien[cles].values))
                part = part[[tuple(x) not in cle_anc for x in part[cles].values]]
                if len(part) == 0:
                    continue
            tout = pd.concat([ancien, part], ignore_index=True).drop_duplicates(cles, keep="last")
        else:
            tout = part.astype(str)
        tout = tout.sort_values(cles).reset_index(drop=True)
        if chemin.exists():
            avant = pd.read_csv(chemin, dtype=str)
            if len(avant) == len(tout) and avant.equals(tout[avant.columns]):
                continue
        tout.to_csv(chemin, index=False, compression={"method": "gzip", "mtime": 0})
        n += 1
    return n


def long(df, prefixe):
    """DataFrame date x colonnes -> lignes (date, serie, valeur) sans les vides."""
    df = df.copy()
    df.index = pd.to_datetime(df.index).strftime("%Y-%m-%d")
    df.index.name = "date"
    t = df.stack().rename("valeur").reset_index()
    t.columns = ["date", "serie", "valeur"]
    t["serie"] = prefixe + t["serie"].astype(str)
    t = t[pd.to_numeric(t["valeur"], errors="coerce").notna()]
    t["valeur"] = pd.to_numeric(t["valeur"]).map(lambda v: f"{v:.10g}")
    return t


# ------------------------------------------------------------------ Yahoo
def yahoo_telecharger(symboles, **kw):
    import yfinance as yf
    out = {}
    for i in range(0, len(symboles), 20):
        lot = symboles[i:i + 20]
        for essai in range(3):
            try:
                d = yf.download(lot, group_by="ticker", auto_adjust=False, threads=True, progress=False, **kw)
                break
            except Exception as e:
                print(f"Yahoo {lot[0]}... : {type(e).__name__}, nouvel essai")
                time.sleep(20 * (essai + 1))
                d = None
        if d is None or len(d) == 0:
            continue
        for s in lot:
            try:
                x = d[s] if isinstance(d.columns, pd.MultiIndex) else d
            except KeyError:
                continue
            x = x.dropna(how="all")
            if len(x):
                out[s] = x
        time.sleep(2)
    return out


def yahoo_jour():
    d = yahoo_telecharger(UNIVERS_JOUR, period="max", interval="1d")
    parts = []
    for s, x in d.items():
        x = x.rename(columns={"Open": "o", "High": "h", "Low": "l", "Close": "c", "Volume": "v"})
        parts.append(long(x[[c for c in "ohlcv" if c in x.columns]], f"{s}:"))
    t = pd.concat(parts, ignore_index=True) if parts else None
    n = ranger(t, DONNEES / "jour" / "yahoo", "date", ["date", "serie"])
    noter("yahoo_jour", symboles=len(d), manquants=sorted(set(UNIVERS_JOUR) - set(d)), fichiers_ecrits=n)


def barres(x, s):
    x = x.rename(columns={"Open": "o", "High": "h", "Low": "l", "Close": "c", "Volume": "v"})
    idx = pd.DatetimeIndex(x.index)
    idx = idx.tz_localize("UTC") if idx.tz is None else idx
    t = pd.DataFrame({"t": idx.tz_convert(NY).strftime("%Y-%m-%d %H:%M"), "symbole": s})
    for c in "ohlcv":
        t[c] = x[c].map(lambda v: f"{v:.10g}").values if c in x.columns else ""
    return t[t["c"] != "nan"]


def yahoo_heure():
    d = yahoo_telecharger(UNIVERS_HEURE, period="730d", interval="1h")
    t = pd.concat([barres(x, s) for s, x in d.items()], ignore_index=True) if d else None
    n = ranger(t, DONNEES / "heure", "t", ["t", "symbole"])
    noter("yahoo_heure", symboles=len(d), fichiers_ecrits=n)


def yahoo_minute():
    """Les 29 derniers jours (limite de Yahoo pour la minute) : un fichier par journee de New York terminee."""
    fin = pd.Timestamp.now(tz=NY).normalize()
    parts = []
    for k in range(4):
        a = fin - pd.Timedelta(days=28 - 7 * k)
        b = a + pd.Timedelta(days=7) if k < 3 else fin + pd.Timedelta(days=1)
        d = yahoo_telecharger(UNIVERS_MINUTE, start=a.strftime("%Y-%m-%d"), end=b.strftime("%Y-%m-%d"), interval="1m")
        parts += [barres(x, s) for s, x in d.items()]
    if not parts:
        noter("yahoo_minute", jours_ecrits=0)
        return
    t = pd.concat(parts, ignore_index=True).drop_duplicates(["t", "symbole"], keep="last")
    t["jour"] = t["t"].str[:10]
    aujourdhui = fin.strftime("%Y-%m-%d")
    ecrits = 0
    for j, part in t.groupby("jour"):
        if j >= aujourdhui and pd.Timestamp.now(tz=NY).hour < 18:
            continue                                    # journee pas finie : ecrite au passage suivant
        chemin = DONNEES / "minutes" / j[:4] / f"{j}.csv.gz"
        part = part.drop(columns="jour").sort_values(["symbole", "t"])
        if chemin.exists():
            ancien = pd.read_csv(chemin, dtype=str)
            if set(part["symbole"]) <= set(ancien["symbole"]):
                continue
            part = pd.concat([ancien, part[~part["symbole"].isin(set(ancien["symbole"]))]]).sort_values(["symbole", "t"])
        chemin.parent.mkdir(parents=True, exist_ok=True)
        part.to_csv(chemin, index=False, compression={"method": "gzip", "mtime": 0})
        ecrits += 1
    noter("yahoo_minute", symboles=t["symbole"].nunique(), jours_ecrits=ecrits)


def resultats():
    import yfinance as yf
    lignes = []
    for s in GRANDES:
        try:
            e = yf.Ticker(s).get_earnings_dates(limit=100)
        except Exception:
            e = None
        if e is None or len(e) == 0:
            continue
        idx = pd.DatetimeIndex(e.index)
        idx = idx.tz_convert(NY) if idx.tz is not None else idx.tz_localize(NY)
        for i, (ts, r) in enumerate(e.iterrows()):
            lignes.append({"symbole": s, "t": idx[i].strftime("%Y-%m-%d %H:%M"),
                           "bpa_attendu": r.get("EPS Estimate"), "bpa_publie": r.get("Reported EPS"),
                           "surprise_pct": r.get("Surprise(%)")})
        time.sleep(1)
    if not lignes:
        noter("resultats", lignes=0)
        return
    t = pd.DataFrame(lignes)
    chemin = DONNEES / "evenements" / "resultats.csv"
    chemin.parent.mkdir(parents=True, exist_ok=True)
    if chemin.exists():
        t = pd.concat([pd.read_csv(chemin), t]).drop_duplicates(["symbole", "t"], keep="last")
    t.sort_values(["symbole", "t"]).to_csv(chemin, index=False)
    noter("resultats", symboles=t["symbole"].nunique(), lignes=len(t))


# ------------------------------------------------------------------ autres sources
def finra():
    """Volumes vendus a decouvert declares a la FINRA (tous les marches americains, fichier CNMS), depuis aout 2009."""
    dossier = DONNEES / "jour" / "finra"
    deja = set()
    if dossier.exists():
        for f in dossier.glob("*.csv.gz"):
            deja |= set(pd.read_csv(f, usecols=["date"], dtype=str)["date"])
    jours = [j for j in pd.bdate_range("2009-08-03", pd.Timestamp.today().normalize() - pd.Timedelta(days=1))
             if j.strftime("%Y-%m-%d") not in deja]
    n_max = int(os.getenv("RADAR_FINRA_MAX", "2500"))               # l'historique se complete en plusieurs passages
    jours = jours[:n_max] if os.getenv("RADAR_FINRA_ANCIENS") else jours[-n_max:]
    garder = set(FINRA)

    def fichier(prefixe, j):
        r = get(f"https://cdn.finra.org/equity/regsho/daily/{prefixe}shvol{j:%Y%m%d}.txt", essais=2, attente=3)
        if r is None or r.status_code != 200 or b"|" not in r.content[:200]:
            return None
        t = pd.read_csv(io.BytesIO(r.content), sep="|", dtype=str)
        return t[t["Symbol"].isin(garder)]

    def un(j):
        """Fichier consolide (CNMS, depuis 2018) ; avant, somme des places de declaration (Nasdaq, NYSE, ADF)."""
        t = fichier("CNMS", j)
        if t is None:
            parts = [x for x in (fichier(p, j) for p in ("FNSQ", "FNYX", "FNRA", "FNQC")) if x is not None and len(x)]
            if not parts:
                return None
            t = pd.concat(parts)
            for c in ("ShortVolume", "ShortExemptVolume", "TotalVolume"):
                t[c] = pd.to_numeric(t[c], errors="coerce") if c in t else 0.0     # colonne absente des vieux fichiers
            t = t.groupby("Symbol", as_index=False)[["ShortVolume", "ShortExemptVolume", "TotalVolume"]].sum()
        if not len(t):
            return None
        out = []
        for col, nom in (("ShortVolume", "court"), ("ShortExemptVolume", "exempte"), ("TotalVolume", "total")):
            if col in t.columns:
                out.append(pd.DataFrame({"date": j.strftime("%Y-%m-%d"), "serie": t["Symbol"] + ":" + nom,
                                         "valeur": t[col]}))
        return pd.concat(out)

    parts = []
    with cf.ThreadPoolExecutor(12) as ex:
        for x in ex.map(un, jours):
            if x is not None:
                parts.append(x)
    t = pd.concat(parts, ignore_index=True) if parts else None
    n = ranger(t, dossier, "date", ["date", "serie"])
    noter("finra", jours_demandes=len(jours), jours_recus=len(parts), fichiers_ecrits=n)


def dix_gex():
    r = get("https://squeezemetrics.com/monitor/static/DIX.csv")
    if r is None or r.status_code != 200:
        noter("dix_gex", erreur=getattr(r, "status_code", "pas de reponse"))
        return
    t = pd.read_csv(io.BytesIO(r.content)).set_index("date")[["dix", "gex", "price"]]
    n = ranger(long(t, "squeeze:"), DONNEES / "jour" / "alt", "date", ["date", "serie"])
    noter("dix_gex", lignes=len(t), derniere=str(t.index[-1]), fichiers_ecrits=n)


def wiki():
    fin = (pd.Timestamp.today() - pd.Timedelta(days=1)).strftime("%Y%m%d")
    cols = {}
    for a in WIKI:
        r = get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/"
                f"{requests.utils.quote(a, safe='')}/daily/20150701/{fin}", entetes=RECHERCHE)
        if r is None or r.status_code != 200:
            continue
        it = r.json().get("items", [])
        cols[a] = pd.Series({pd.Timestamp(x["timestamp"][:8]): x["views"] for x in it})
        time.sleep(0.3)
    t = long(pd.DataFrame(cols), "wiki:") if cols else None
    n = ranger(t, DONNEES / "jour" / "alt", "date", ["date", "serie"])
    noter("wikipedia", articles=len(cols), fichiers_ecrits=n)


def fred():
    """Series de la FRED (le site repond parfois tres lentement : 20 s par serie, 6 min en tout, arret apres 4 echecs
    de suite)."""
    cols = {}
    debut, echecs = time.time(), 0
    for s in FRED_ESSENTIELLES + [x for x in FRED if x not in FRED_ESSENTIELLES]:
        if time.time() - debut > 600 or echecs >= 4:
            break
        try:
            r = requests.get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}", timeout=60, headers=RECHERCHE)
        except requests.RequestException:
            r = None
        if r is None or r.status_code != 200 or not r.content[:200].strip():
            echecs += 1
            continue
        echecs = 0
        t = pd.read_csv(io.BytesIO(r.content))
        t = t.set_index(t.columns[0])
        cols[s] = pd.to_numeric(t.iloc[:, 0], errors="coerce")
        time.sleep(0.5)
    t = long(pd.DataFrame(cols), "fred:") if cols else None
    n = ranger(t, DONNEES / "jour" / "alt", "date", ["date", "serie"])
    noter("fred", series=len(cols), manquantes=sorted(set(FRED) - set(cols)), fichiers_ecrits=n)


def incertitude():
    """Indice quotidien d'incertitude des politiques economiques (Baker, Bloom et Davis), tire des journaux americains."""
    r = get("https://www.policyuncertainty.com/media/All_Daily_Policy_Data.csv")
    if r is None or r.status_code != 200:
        noter("incertitude", erreur=getattr(r, "status_code", "pas de reponse"))
        return
    t = pd.read_csv(io.BytesIO(r.content))
    t.columns = [c.strip().lower() for c in t.columns]
    t["date"] = pd.to_datetime(dict(year=t["year"], month=t["month"], day=t["day"]))
    col = [c for c in t.columns if "daily" in c or "policy" in c][0]
    s = t.set_index("date")[[col]].rename(columns={col: "epu"})
    n = ranger(long(s, "incertitude:"), DONNEES / "jour" / "alt", "date", ["date", "serie"])
    noter("incertitude", lignes=len(s), derniere=str(s.index[-1].date()), fichiers_ecrits=n)


def cnn():
    r = get("https://production.dataviz.cnn.io/index/fearandgreed/graphdata/2010-01-01",
            entetes={**NAVIGATEUR, "Referer": "https://www.cnn.com/", "Origin": "https://www.cnn.com"})
    if r is None or r.status_code != 200:
        noter("cnn_peur_avidite", erreur=getattr(r, "status_code", "pas de reponse"))
        return
    j = r.json()
    cols = {}
    for cle, v in j.items():
        if isinstance(v, dict) and isinstance(v.get("data"), list):
            cols[cle] = pd.Series({pd.Timestamp(x["x"], unit="ms").normalize(): x["y"] for x in v["data"]})
    t = long(pd.DataFrame(cols), "cnn:") if cols else None
    n = ranger(t, DONNEES / "jour" / "alt", "date", ["date", "serie"])
    noter("cnn_peur_avidite", series=len(cols), fichiers_ecrits=n)


def aaii():
    r = get("https://www.aaii.com/files/surveys/sentiment.xls")
    if r is None or r.status_code != 200 or len(r.content) < 10000:
        noter("aaii", erreur=getattr(r, "status_code", "pas de reponse"))
        return
    try:
        x = pd.read_excel(io.BytesIO(r.content), skiprows=3)
        x = x.rename(columns={x.columns[0]: "date"})
        x["date"] = pd.to_datetime(x["date"], errors="coerce")
        x = x.dropna(subset=["date"]).set_index("date")
        x = x[[c for c in x.columns if str(c).strip().lower() in ("bullish", "neutral", "bearish")]]
        x.columns = [str(c).strip().lower() for c in x.columns]
        n = ranger(long(x, "aaii:"), DONNEES / "jour" / "alt", "date", ["date", "serie"])
        noter("aaii", lignes=len(x), fichiers_ecrits=n)
    except Exception as e:
        noter("aaii", erreur=type(e).__name__)


def gdelt():
    """Volume et ton des articles du monde entier (GDELT), par jour, sur les 3 derniers mois (limite de l'outil)."""
    cols = {}
    for nom, q in GDELT.items():
        for mode in ("timelinevol", "timelinetone"):
            r = get(f"https://api.gdeltproject.org/api/v2/doc/doc?query={requests.utils.quote(q)}%20sourcelang:english"
                    f"&mode={mode}&format=json&timespan=3months&timelinesmooth=0", essais=2, attente=10)
            time.sleep(6)
            if r is None or r.status_code != 200:
                continue
            try:
                serie = r.json()["timeline"][0]["data"]
            except (ValueError, KeyError, IndexError):
                continue
            s = pd.Series({pd.Timestamp(x["date"][:8]): x["value"] for x in serie})
            cols[f"{nom}:{'volume' if mode.endswith('vol') else 'ton'}"] = s.groupby(level=0).mean()
    t = long(pd.DataFrame(cols), "gdelt:") if cols else None
    n = ranger(t, DONNEES / "jour" / "alt", "date", ["date", "serie"])
    noter("gdelt", series=len(cols), fichiers_ecrits=n)


def options_cboe():
    """Photo du soir des options (CBOE, cotations differees) : exposition gamma des teneurs de marche par prix d'exercice,
    avec l'hypothese habituelle (ils ont vendu les puts et achete les calls des clients : gamma des calls +, puts -)."""
    jour = pd.Timestamp.now(tz=NY)
    if jour.dayofweek >= 5:
        noter("options_cboe", info="week-end")
        return
    lignes = []
    for nom, code in OPTIONS.items():
        r = get(f"https://cdn.cboe.com/api/global/delayed_quotes/options/{code}.json")
        if r is None or r.status_code != 200:
            continue
        d = r.json().get("data", {})
        spot = float(d.get("current_price") or d.get("close") or np.nan)
        o = pd.DataFrame(d.get("options", []))
        if not len(o) or not np.isfinite(spot):
            continue
        sym = o["option"].str.extract(r"^(?P<r>[A-Z_]+?)(?P<e>\d{6})(?P<cp>[CP])(?P<k>\d{8})$")
        o["echeance"] = pd.to_datetime(sym["e"], format="%y%m%d", errors="coerce")
        o["type"], o["k"] = sym["cp"], pd.to_numeric(sym["k"], errors="coerce") / 1000
        for c in ("gamma", "open_interest", "volume", "iv", "delta"):
            o[c] = pd.to_numeric(o.get(c), errors="coerce").fillna(0.0)
        signe = np.where(o["type"] == "C", 1.0, -1.0)
        o["gex"] = signe * o["gamma"] * o["open_interest"] * 100 * spot * spot * 0.01
        o["jours"] = (o["echeance"] - pd.Timestamp(jour.date())).dt.days
        o["oi_call"] = np.where(o["type"] == "C", o["open_interest"], 0.0)
        o["oi_put"] = np.where(o["type"] == "P", o["open_interest"], 0.0)
        par_k = o.groupby("k")[["gex", "oi_call", "oi_put", "volume"]].sum().reset_index()
        proche = o[o["jours"] <= 1]
        cum = par_k.sort_values("k")["gex"].cumsum().values
        ks = par_k.sort_values("k")["k"].values
        bascule = float(ks[np.argmin(np.abs(cum))]) if len(ks) else np.nan
        calls, puts = o[o["type"] == "C"], o[o["type"] == "P"]
        mur_call = float(calls.groupby("k")["gex"].sum().idxmax()) if len(calls) else np.nan
        mur_put = float(puts.groupby("k")["gex"].sum().idxmin()) if len(puts) else np.nan
        resume = {"spot": spot, "gex_total": float(o["gex"].sum()), "gex_0dte": float(proche["gex"].sum()),
                  "bascule": bascule, "mur_call": mur_call, "mur_put": mur_put,
                  "pc_oi": float(puts["open_interest"].sum() / max(1.0, calls["open_interest"].sum())),
                  "pc_volume": float(puts["volume"].sum() / max(1.0, calls["volume"].sum()))}
        for k, v in resume.items():
            lignes.append({"date": jour.strftime("%Y-%m-%d"), "serie": f"cboe:{nom}:{k}", "valeur": f"{v:.10g}"})
        chemin = DONNEES / "options" / jour.strftime("%Y") / f"{jour:%Y-%m-%d}_{nom}.csv.gz"
        chemin.parent.mkdir(parents=True, exist_ok=True)
        par_k.to_csv(chemin, index=False, float_format="%.6g", compression={"method": "gzip", "mtime": 0})
    t = pd.DataFrame(lignes) if lignes else None
    n = ranger(t, DONNEES / "jour" / "alt", "date", ["date", "serie"])
    noter("options_cboe", sous_jacents=len({l["serie"].split(":")[1] for l in lignes}), fichiers_ecrits=n)


SOURCES = [yahoo_jour, yahoo_heure, yahoo_minute, finra, dix_gex, wiki, fred, incertitude, cnn, aaii, gdelt,
           options_cboe, resultats]


def main():
    seules = os.getenv("RADAR_SOURCES", "")
    for f in SOURCES:
        if seules and f.__name__ not in seules.split(","):
            continue
        t0 = time.time()
        try:
            f()
        except Exception:
            noter(f.__name__, erreur=traceback.format_exc(limit=3).strip().splitlines()[-1])
        print(f"  ({time.time() - t0:.0f} s)", flush=True)
    chemin = DONNEES / "etat.json"
    ancien = json.loads(chemin.read_text()) if chemin.exists() else {}
    ancien.update(ETAT)
    chemin.write_text(json.dumps(ancien, indent=1, ensure_ascii=False, default=str) + "\n")


if __name__ == "__main__":
    main()
