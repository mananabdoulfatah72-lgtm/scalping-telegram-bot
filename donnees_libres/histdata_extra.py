#!/usr/bin/env python3
"""Prix minute gratuits de HistData (2012 - 2026) pour les marches absents de sessions24/ (branche de recherche) :
argent (SI), Brent (BZ), Nikkei (NKD), indice du dollar (DX), dollar canadien (6C), franc suisse (6S), dollar
neo-zelandais (6N). Meme traitement que sessions24/telecharger_histdata.py : heure de New York avec l'heure d'ete
(verifie dans sessions24/README.md), passee en UTC, barres de 5 minutes 24 h sur 24 (prix acheteur).
Ecrit donnees_libres/histdata_5min/<code>_<annee>_5m.csv.gz (t UTC, o, h, l, c) et resume.txt.
Lance par .github/workflows/donnees-libres.yml."""
import io
import zipfile
from pathlib import Path

import pandas as pd
from histdata import download_hist_data as dl
from histdata.api import Platform as P, TimeFrame as TF

ICI = Path(__file__).resolve().parent
SORTIE = ICI / "histdata_5min"
# code -> (paire HistData, future CME suivi)
CODES = {"xagusd": ("xagusd", "SI"), "bcousd": ("bcousd", "BZ"), "jpxjpy": ("jpxjpy", "NKD"),
         "udxusd": ("udxusd", "DX"), "usdcad": ("usdcad", "6C"), "usdchf": ("usdchf", "6S"),
         "nzdusd": ("nzdusd", "6N")}


def lire(f):
    z = zipfile.ZipFile(f)
    nom = [n for n in z.namelist() if n.endswith(".csv")][0]
    d = pd.read_csv(io.BytesIO(z.read(nom)), sep=";", header=None, names=["t", "o", "h", "l", "c", "v"],
                    dtype={"t": str})
    t = pd.to_datetime(d["t"], format="%Y%m%d %H%M%S").dt.tz_localize(
        "America/New_York", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC").dt.tz_localize(None)
    d, t = d[t.notna()], t[t.notna()]
    return pd.DataFrame({"o": d["o"].to_numpy(), "h": d["h"].to_numpy(), "l": d["l"].to_numpy(),
                         "c": d["c"].to_numpy()}, index=pd.DatetimeIndex(t))


def cinq(x):
    x = x[~x.index.duplicated(keep="last")].sort_index()
    b = x.resample("5min", label="left", closed="left").agg({"o": "first", "h": "max", "l": "min", "c": "last"}).dropna()
    nd = 5 if b["c"].median() < 50 else 3
    return pd.DataFrame({"t": b.index.strftime("%Y-%m-%d %H:%M").to_numpy(), "o": b["o"].round(nd).to_numpy(),
                         "h": b["h"].round(nd).to_numpy(), "l": b["l"].round(nd).to_numpy(), "c": b["c"].round(nd).to_numpy()})


def main():
    SORTIE.mkdir(parents=True, exist_ok=True)
    resume = []
    for code, (paire, fut) in CODES.items():
        for an in range(2012, 2027):
            try:
                if an < 2026:
                    x = lire(dl(year=str(an), month=None, pair=paire, platform=P.GENERIC_ASCII, time_frame=TF.ONE_MINUTE))
                else:
                    morceaux = []
                    for m in range(1, 13):
                        try:
                            morceaux.append(lire(dl(year=str(an), month=str(m), pair=paire, platform=P.GENERIC_ASCII,
                                                    time_frame=TF.ONE_MINUTE)))
                        except Exception:
                            break
                    x = pd.concat(morceaux)
                out = cinq(x)
                out.to_csv(SORTIE / f"{code}_{an}_5m.csv.gz", index=False, compression="gzip")
                ligne = f"{code} ({fut}) {an} : {len(out)} barres ({out['t'].iloc[0]} -> {out['t'].iloc[-1]} UTC)"
            except Exception as e:
                ligne = f"{code} ({fut}) {an} : ECHEC {type(e).__name__} {str(e)[:150]}"
                print(f"::warning::{ligne}")
            print(ligne, flush=True)
            resume.append(ligne)
    for f in Path(".").glob("DAT_ASCII_*.zip"):
        f.unlink()
    (SORTIE / "resume.txt").write_text("\n".join(resume) + "\n")


if __name__ == "__main__":
    main()
