#!/usr/bin/env python3
"""Murs d'options (README.md, precision sur les murs), par GitHub Actions :
- chaque semaine, l'interet ouvert (statistics, stat_type 9) des options trimestrielles ES et NQ (CME, Databento),
  publie entre le samedi 0 h et le lundi 6 h UTC (chiffres du vendredi, avant la seance du lundi) ;
- call wall et put wall : strike au plus fort interet ouvert en calls (en puts) sur l'echeance trimestrielle la plus
  proche ; zero gamma : prix ou le gamma total (teneurs acheteurs des calls, vendeurs des puts, Black-76, volatilite =
  VIX de la date de l'interet ouvert) change de signe, le plus proche du prix du jour ;
- sorties : donnees/murs_ES.csv et murs_NQ.csv (date = jour de l'interet ouvert), donnees/couts_murs.txt.
Le cout total est verifie avant : au-dela de 25 $, rien n'est telecharge.
Aussi : relevé de equity-lab.com (llms.txt, sitemap.xml, pages du plan) -> donnees/equity_lab_com.txt.
Cle : DATABENTO_API_KEY (secret)."""
import math
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).parent
SORTIE = ICI / "donnees"
PLAFOND = 25.0
MOIS = {"H": 3, "M": 6, "U": 9, "Z": 12}
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def equity_lab():
    lignes = []
    def lire(url):
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
            return r.read().decode("utf-8", "replace")
    pages = []
    for chemin in ("/llms.txt", "/llms-full.txt", "/sitemap.xml"):
        try:
            t = lire("https://equity-lab.com" + chemin)
            lignes.append(f"=== {chemin}\n{t[:8000]}\n")
            pages += re.findall(r"<loc>([^<]+)</loc>", t)
        except Exception as e:                      # noqa: BLE001
            lignes.append(f"=== {chemin} : ECHEC {e}\n")
    for url in pages[:25]:
        try:
            t = lire(url)
            t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", t)
            titre = re.search(r"(?is)<title[^>]*>(.*?)</title>", t)
            desc = re.search(r'(?is)<meta[^>]+name="description"[^>]+content="([^"]*)"', t)
            txt = re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", t)).strip()
            lignes.append(f"=== {url}\nTitre : {titre.group(1).strip() if titre else ''}\nDescription : {desc.group(1) if desc else ''}\n{txt[:1500]}\n")
        except Exception as e:                      # noqa: BLE001
            lignes.append(f"=== {url} : ECHEC {e}\n")
    (SORTIE / "equity_lab_com.txt").write_text("\n".join(lignes))
    print("equity-lab.com : " + ", ".join(l.splitlines()[0] for l in lignes), flush=True)


def troisieme_vendredi(annee, mois):
    d = pd.Timestamp(annee, mois, 15)
    return d + pd.Timedelta(days=(4 - d.weekday()) % 7)


def lire_symbole(sym, annee_ref):
    """'ESZ6 C6500' -> (echeance, 'C', 6500.0) ; None si ce n'est pas une option trimestrielle simple."""
    m = re.fullmatch(r"(ES|NQ)([HMUZ])(\d) ([CP])(\d+(?:\.\d+)?)", str(sym).strip())
    if not m:
        return None
    chiffre = int(m.group(3))
    annee = annee_ref - 1
    while annee % 10 != chiffre:
        annee += 1
    return troisieme_vendredi(annee, MOIS[m.group(2)]), m.group(4), float(m.group(5))


def gamma76(F, K, T, s):
    d1 = (np.log(F / K) + 0.5 * s * s * T) / (s * np.sqrt(T))
    return np.exp(-0.5 * d1 * d1) / np.sqrt(2 * np.pi) / (F * s * np.sqrt(T))


def niveaux(oi, jour, vix, prix):
    """oi : DataFrame (echeance, type, strike, quantite) d'une semaine. Renvoie call wall, put wall, zero gamma."""
    oi = oi[oi["echeance"] > jour]
    if oi.empty:
        return np.nan, np.nan, np.nan
    proche = oi[oi["echeance"] == oi["echeance"].min()]
    c, p = proche[proche["type"] == "C"], proche[proche["type"] == "P"]
    cw = float(c.loc[c["quantite"].idxmax(), "strike"]) if len(c) else np.nan
    pw = float(p.loc[p["quantite"].idxmax(), "strike"]) if len(p) else np.nan
    zg = np.nan
    if not np.isnan(vix) and not np.isnan(prix):
        T = ((oi["echeance"] - jour).dt.days.values / 365.0).clip(1 / 365, None)
        signe = np.where(oi["type"].values == "C", 1.0, -1.0)
        grille = prix * np.linspace(0.8, 1.2, 401)
        g = np.array([(signe * oi["quantite"].values * gamma76(F, oi["strike"].values, T, vix / 100)).sum() * F for F in grille])
        chg = np.where(np.sign(g[1:]) != np.sign(g[:-1]))[0]
        if len(chg):
            i = chg[np.argmin(np.abs(grille[chg] - prix))]
            zg = float(grille[i] - g[i] * (grille[i + 1] - grille[i]) / (g[i + 1] - g[i]))
    return cw, pw, zg


def main():
    SORTIE.mkdir(exist_ok=True)
    equity_lab()
    import databento as db
    client = db.Historical()
    lundis = pd.date_range("2011-01-03", "2026-09-28", freq="W-MON")
    fenetres = [(l - pd.Timedelta(hours=48), l + pd.Timedelta(hours=6)) for l in lundis]     # samedi 0 h - lundi 6 h UTC
    rng = np.random.default_rng(0)
    echant = rng.choice(len(fenetres), 24, replace=False)
    lignes = []
    total = 0.0
    for parent in ("ES.OPT", "NQ.OPT"):
        c = [client.metadata.get_cost(dataset="GLBX.MDP3", symbols=[parent], stype_in="parent", schema="statistics",
                                      start=fenetres[i][0].isoformat(), end=fenetres[i][1].isoformat()) for i in echant]
        estim = float(np.mean(c)) * len(fenetres)
        total += estim
        lignes.append(f"{parent} : {len(fenetres)} semaines, cout estime {estim:.2f} $ (moyenne de 24 semaines tirees au hasard)")
        print(lignes[-1], flush=True)
    lignes.append(f"Total estime : {total:.2f} $ (plafond {PLAFOND} $)")
    print(lignes[-1], flush=True)
    if total > PLAFOND:
        (SORTIE / "couts_murs.txt").write_text("\n".join(lignes + ["Trop cher : rien n'est telecharge"]) + "\n")
        sys.exit(0)
    vix = pd.read_csv(SORTIE / "vix.csv")
    vix = pd.Series(vix["CLOSE"].astype(float).values, index=pd.to_datetime(vix["DATE"], format="mixed"))
    for parent, fichier in (("ES.OPT", "sp500"), ("NQ.OPT", "nasdaq100")):
        marche = parent[:2]
        px = pd.read_csv(ICI.parent / "intraday" / "donnees" / f"{fichier}_1min.csv.gz", usecols=["t", "c"])
        px["j"] = pd.to_datetime(px["t"].str[:10])
        cloture = px.groupby("j")["c"].last()

        def semaine(f):
            try:
                df = client.timeseries.get_range(dataset="GLBX.MDP3", symbols=[parent], stype_in="parent", schema="statistics",
                                                 start=f[0].isoformat(), end=f[1].isoformat()).to_df()
            except Exception as e:                  # noqa: BLE001
                return f, None, str(e)
            if df.empty:
                return f, None, "vide"
            df = df[df["stat_type"] == 9]
            return f, df[["ts_ref", "symbol", "quantity"]].copy(), ""

        with ThreadPoolExecutor(4) as ex:
            resultats = list(ex.map(semaine, fenetres))
        out, vides = [], 0
        for f, df, err in resultats:
            if df is None or df.empty:
                vides += 1
                continue
            ref = pd.to_datetime(df["ts_ref"]).dt.tz_localize(None).dt.normalize() if pd.to_datetime(df["ts_ref"]).dt.tz is not None \
                else pd.to_datetime(df["ts_ref"]).dt.normalize()
            jour = ref.max()
            df = df[ref == jour]
            lus = [lire_symbole(s, jour.year) for s in df["symbol"]]
            garde = [x is not None for x in lus]
            oi = pd.DataFrame([x for x in lus if x is not None], columns=["echeance", "type", "strike"])
            oi["quantite"] = df["quantity"].values[garde].astype(float)
            oi = oi[oi["quantite"] > 0]
            v = vix[:jour].iloc[-1] if len(vix[:jour]) else np.nan
            p = cloture[:jour].iloc[-1] if len(cloture[:jour]) else np.nan
            cw, pw, zg = niveaux(oi, jour, v, p)
            out.append({"date": jour.date(), "call": cw, "put": pw, "zero": zg, "prix": p, "options": len(oi),
                        "oi_total": float(oi["quantite"].sum())})
        m = pd.DataFrame(out).drop_duplicates("date", keep="last").sort_values("date")
        m.to_csv(SORTIE / f"murs_{marche}.csv", index=False)
        lignes.append(f"{marche} : {len(m)} semaines avec murs, {vides} fenetres vides ou en echec ; "
                      f"du {m['date'].iloc[0]} au {m['date'].iloc[-1]}")
        print(lignes[-1], flush=True)
    (SORTIE / "couts_murs.txt").write_text("\n".join(lignes) + "\n")


if __name__ == "__main__":
    main()
