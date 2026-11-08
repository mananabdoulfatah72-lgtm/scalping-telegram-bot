"""Bundles zipline du labo : `crypto` (calendrier 24h/24, 7j/7) et `etf` (Bourse de New York). Les CSV viennent de
extraire.py, dans le dossier donne par la variable LABO_CSV."""
import os

import pandas as pd
from zipline.data.bundles import register
from zipline.data.bundles.csvdir import csvdir_equities

CSV = os.environ["LABO_CSV"]                 # zipline execute ce fichier sans __file__
FIN = pd.Timestamp("2026-10-30")
register("crypto", csvdir_equities(["daily"], os.path.join(CSV, "crypto")), calendar_name="24/7",
         start_session=pd.Timestamp("2014-12-31"), end_session=FIN - pd.Timedelta(days=1))   # dates decalees, voir extraire.py
register("etf", csvdir_equities(["daily"], os.path.join(CSV, "etf")), calendar_name="XNYS",
         start_session=pd.Timestamp("2015-01-02"), end_session=FIN)
