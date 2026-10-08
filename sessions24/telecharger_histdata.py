#!/usr/bin/env python3
"""Telecharge les prix minute gratuits de HistData (2012 - 2026), les passe en UTC et ecrit des barres de 5 minutes par annee :
sessions24/annees/<code>_<annee>_5m.csv.gz (memes codes que la machine 5). Lance par donnees-sessions.yml.
Attention : malgre la documentation de HistData (« EST sans changement d'heure »), les horodatages suivent l'heure de
New York avec l'heure d'ete (verifie, README.md).
Dukascopy refuse les telechargements depuis GitHub depuis octobre 2026 (reponse 202)."""
import io
import zipfile
from pathlib import Path

import pandas as pd
from histdata import download_hist_data as dl
from histdata.api import Platform as P, TimeFrame as TF

ICI = Path(__file__).resolve().parent
ANNEES = ICI / "annees"
CODES = {"usatechidxusd": "nsxusd", "usa500idxusd": "spxusd", "eurusd": "eurusd", "gbpusd": "gbpusd",
         "usdjpy": "usdjpy", "audusd": "audusd", "xauusd": "xauusd", "lightcmdusd": "wtiusd"}


def lire(f):
    z = zipfile.ZipFile(f)
    nom = [n for n in z.namelist() if n.endswith(".csv")][0]
    d = pd.read_csv(io.BytesIO(z.read(nom)), sep=";", header=None, names=["t", "o", "h", "l", "c", "v"],
                    dtype={"t": str})
    t = pd.to_datetime(d["t"], format="%Y%m%d %H%M%S").dt.tz_localize(            # HistData : heure de New York
        "America/New_York", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC").dt.tz_localize(None)  # avec l'heure d'ete
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
    ANNEES.mkdir(parents=True, exist_ok=True)
    for code, paire in CODES.items():
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
                        except Exception as e:
                            print(f"{code} {an}-{m:02d} : pas de fichier ({type(e).__name__})")
                            break
                    x = pd.concat(morceaux)
                out = cinq(x)
                out.to_csv(ANNEES / f"{code}_{an}_5m.csv.gz", index=False, compression="gzip")
                h = pd.to_datetime(out["t"]).dt.hour.value_counts().sort_index()
                print(f"{code} ({paire}) {an} : {len(out)} barres de 5 min ({out['t'].iloc[0]} -> {out['t'].iloc[-1]} UTC) ;"
                      f" heures UTC couvertes : {len(h)}/24")
            except Exception as e:
                print(f"::warning::{code} ({paire}) {an} : ECHEC {type(e).__name__} {str(e)[:200]}")
    for f in Path(".").glob("DAT_ASCII_*.zip"):
        f.unlink()


if __name__ == "__main__":
    main()
