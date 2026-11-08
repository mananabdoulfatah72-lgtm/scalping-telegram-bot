#!/usr/bin/env python3
"""Labo zipline de bout en bout, comme dans la recette : CSV -> bundles (zipline ingest) -> backtests (zipline run) ->
pickles. python3 lancer.py <dossier de travail> (a lancer avec le python de l'environnement ou zipline est installe)."""
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

ICI = Path(__file__).resolve().parent
TRAV = Path(sys.argv[1]).resolve()
ZL = str(Path(sys.executable).parent / "zipline")
env = dict(os.environ, ZIPLINE_ROOT=str(TRAV / "zipline_root"), LABO_CSV=str(TRAV / "csv"))
subprocess.run([sys.executable, str(ICI / "extraire.py"), str(TRAV / "csv")], check=True)
for b in ("crypto", "etf") if "--sans-ingest" not in sys.argv else ():
    subprocess.run([ZL, "-e", str(ICI / "extension.py"), "ingest", "-b", b], check=True, env=env)
ACTIFS = [("BTC", "crypto"), ("ETH", "crypto"), ("SOL", "crypto")] + [(s, "etf") for s in ("QQQ", "SPY", "IWM", "GLD", "TLT", "SMH")]
(TRAV / "resultats").mkdir(exist_ok=True)
for actif, fam in ACTIFS:
    debut_donnees = pd.read_csv(TRAV / "csv" / fam / "daily" / f"{actif}.csv", nrows=1).date.iloc[0]
    debut = max(pd.Timestamp("2016-01-01"), pd.Timestamp(debut_donnees) + pd.Timedelta(days=200))   # 120 seances d'historique
    fin = "2026-10-30" if fam == "etf" else "2026-10-29"         # crypto : la seance du 29 oct. voit encore... voir sonde.py
    for nom, (s, e) in {"fenetre": ("2024-01-01", "2025-12-31"), "complet": (debut.strftime("%Y-%m-%d"), fin)}.items():
        if fam == "etf":                                                     # premiere et derniere seances ouvertes
            import exchange_calendars as xc
            cal = xc.get_calendar("XNYS"); ses = cal.sessions_in_range(s, e); s, e = ses[0].strftime("%Y-%m-%d"), ses[-1].strftime("%Y-%m-%d")
        sortie = TRAV / "resultats" / f"{actif}_{nom}.pickle"
        cmd = [ZL, "-e", str(ICI / "extension.py"), "run", "-f", str(ICI / "strategie.py"), "-b", fam, "--start", s, "--end", e,
               "--capital-base", "10000", "--no-benchmark", "--trading-calendar", "24/7" if fam == "crypto" else "XNYS",
               "-o", str(sortie)]
        r = subprocess.run(cmd, env=dict(env, ACTIF=actif, FAMILLE=fam), capture_output=True, text=True)
        print(actif, nom, s, "->", e, "ok" if r.returncode == 0 else "ERREUR\n" + r.stderr[-2000:], flush=True)
