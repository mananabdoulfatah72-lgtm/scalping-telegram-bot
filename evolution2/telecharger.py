#!/usr/bin/env python3
"""Donnees des nouvelles pistes (README.md), telechargees par GitHub Actions :
1. GEX et DIX du S&P 500 (SqueezeMetrics, gratuit, quotidien depuis 2011) -> donnees/dix_gex.csv
2. VIX, VIX 3 mois et VIX 9 jours (CBOE, gratuit)                        -> donnees/vix*.csv
3. Pages publiques d'EquityLab (page d'accueil, robots.txt) pour savoir ce qu'on peut en tirer
                                                                          -> donnees/equitylab.txt
4. Options sur futures ES et NQ (Databento, CME) : cout demande avant tout, et un seul jour d'echantillon
   (definitions et statistiques : strikes, echeances, interet ouvert) pour preparer le calcul des murs
                                                                          -> donnees/couts_options.txt, echantillon_*.csv.gz
Cle Databento : DATABENTO_API_KEY (secret), jamais ecrite ailleurs.
"""
import os
import re
import urllib.request
from pathlib import Path

SORTIE = Path(__file__).parent / "donnees"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def lire(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.status, r.read()


def gratuit():
    for nom, url in (("dix_gex.csv", "https://squeezemetrics.com/monitor/static/DIX.csv"),
                     ("vix.csv", "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"),
                     ("vix3m.csv", "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX3M_History.csv"),
                     ("vix9d.csv", "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX9D_History.csv")):
        try:
            code, contenu = lire(url)
            (SORTIE / nom).write_bytes(contenu)
            lignes = contenu.decode("utf-8", "replace").splitlines()
            print(f"{nom} : {code}, {len(lignes)} lignes, {lignes[0]} ... {lignes[-1]}", flush=True)
        except Exception as e:                       # noqa: BLE001
            print(f"{nom} : ECHEC {e}", flush=True)


def texte_visible(html):
    html = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    titre = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    liens = sorted(set(re.findall(r'href="([^"#]+)"', html)))[:80]
    txt = re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", html)).strip()
    return (titre.group(1).strip() if titre else ""), txt, liens


def equitylab():
    rapport = []
    for dom in ("equitylab.fr", "www.equitylab.fr", "equitylab.com", "www.equitylab.com", "equitylab.ai", "equitylab.io",
                "equitylab.app", "equity-lab.com", "equity-lab.fr", "app.equitylab.fr"):
        for chemin in ("/", "/robots.txt"):
            url = f"https://{dom}{chemin}"
            try:
                code, contenu = lire(url, timeout=20)
                s = contenu.decode("utf-8", "replace")
                if chemin == "/":
                    titre, txt, liens = texte_visible(s)
                    rapport.append(f"=== {url} : {code}\nTitre : {titre}\nTexte : {txt[:4000]}\nLiens : {' '.join(liens)}\n")
                else:
                    rapport.append(f"=== {url} : {code}\n{s[:3000]}\n")
            except Exception as e:                   # noqa: BLE001
                rapport.append(f"=== {url} : ECHEC {e}\n")
    (SORTIE / "equitylab.txt").write_text("\n".join(rapport))
    print("\n".join(r.splitlines()[0] for r in rapport), flush=True)


def options():
    if not os.getenv("DATABENTO_API_KEY"):
        print("Pas de cle Databento : couts des options non demandes")
        return
    import databento as db
    import pandas as pd
    client = db.Historical()
    fin = pd.Timestamp(client.metadata.get_dataset_range(dataset="GLBX.MDP3")["end"]).normalize()
    lignes = [f"Fin des donnees GLBX.MDP3 : {fin.date()}"]
    for parent in ("ES.OPT", "NQ.OPT"):
        for schema in ("statistics", "definition"):
            for debut in ("2011-01-01", "2017-01-01", "2023-01-01"):
                try:
                    c = client.metadata.get_cost(dataset="GLBX.MDP3", symbols=[parent], stype_in="parent", schema=schema,
                                                 start=debut, end=fin.isoformat())
                    lignes.append(f"{parent} {schema} depuis {debut} : {c:.2f} $")
                except Exception as e:           # noqa: BLE001
                    lignes.append(f"{parent} {schema} depuis {debut} : ECHEC {e}")
                print(lignes[-1], flush=True)
    # un jour d'echantillon (quelques centimes) pour connaitre le format exact
    jour = (fin - pd.tseries.offsets.BDay(3)).normalize()
    for schema in ("definition", "statistics"):
        try:
            c = client.metadata.get_cost(dataset="GLBX.MDP3", symbols=["ES.OPT"], stype_in="parent", schema=schema,
                                         start=jour.isoformat(), end=(jour + pd.Timedelta(days=1)).isoformat())
            lignes.append(f"Echantillon ES.OPT {schema} {jour.date()} : {c:.4f} $")
            if c <= 1.0:
                df = client.timeseries.get_range(dataset="GLBX.MDP3", symbols=["ES.OPT"], stype_in="parent", schema=schema,
                                                 start=jour.isoformat(), end=(jour + pd.Timedelta(days=1)).isoformat()).to_df()
                df.to_csv(SORTIE / f"echantillon_es_opt_{schema}.csv.gz")
                lignes.append(f"  {len(df)} lignes, colonnes : {', '.join(map(str, df.columns))}")
        except Exception as e:                       # noqa: BLE001
            lignes.append(f"Echantillon {schema} : ECHEC {e}")
        print(lignes[-1], flush=True)
    (SORTIE / "couts_options.txt").write_text("\n".join(lignes) + "\n")


def main():
    SORTIE.mkdir(exist_ok=True)
    gratuit()
    equitylab()
    options()


if __name__ == "__main__":
    main()
