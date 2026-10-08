#!/usr/bin/env bash
# Essai court : la source HistData (prix minute gratuits) repond-elle depuis GitHub ? (resultats en annotations)
set -u
pip install histdata pandas >/dev/null 2>&1
python3 - <<'PY'
import glob, os, traceback, zipfile
from histdata import download_hist_data as dl
from histdata.api import Platform as P, TimeFrame as TF
for paire, an, mois in (("eurusd", "2013", None), ("nsxusd", "2013", None), ("wtiusd", "2013", None), ("eurusd", "2026", "9")):
    try:
        f = dl(year=an, month=mois, pair=paire, platform=P.GENERIC_ASCII, time_frame=TF.ONE_MINUTE)
        z = zipfile.ZipFile(f)
        noms = z.namelist()
        tete = z.read([n for n in noms if n.endswith(".csv")][0])[:200].decode(errors="replace").replace("\n", " | ")
        print(f"::warning::{paire} {an} {mois} OK : {f} {os.path.getsize(f)} octets {noms} -- {tete}")
    except Exception as e:
        print(f"::warning::{paire} {an} {mois} ECHEC : {type(e).__name__} {str(e)[:300]}")
PY
