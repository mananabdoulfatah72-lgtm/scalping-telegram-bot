#!/usr/bin/env python3
"""Telecharge le rapport COT de la CFTC « Traders in Financial Futures », futures seuls, de 2006 a aujourd'hui, et garde
les lignes du contrat E-mini Nasdaq-100 (flux/README.md, partie 7) dans flux/donnees/cot/cot_nq.csv. Lance par
.github/workflows/donnees-cot.yml (le site de la CFTC n'est pas joignable depuis l'environnement de Claude)."""
import datetime as dt
import io
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests

ICI = Path(__file__).resolve().parent
SORTIE = ICI / "donnees" / "cot" / "cot_nq.csv"
BASE = "https://www.cftc.gov/files/dea/history/"
GARDER = ["Market_and_Exchange_Names", "Report_Date_as_YYYY-MM-DD", "CFTC_Contract_Market_Code", "Open_Interest_All",
          "Dealer_Positions_Long_All", "Dealer_Positions_Short_All", "Dealer_Positions_Spread_All",
          "Asset_Mgr_Positions_Long_All", "Asset_Mgr_Positions_Short_All", "Asset_Mgr_Positions_Spread_All",
          "Lev_Money_Positions_Long_All", "Lev_Money_Positions_Short_All", "Lev_Money_Positions_Spread_All",
          "Other_Rept_Positions_Long_All", "Other_Rept_Positions_Short_All",
          "NonRept_Positions_Long_All", "NonRept_Positions_Short_All"]


def telecharger(noms):
    for nom in noms:
        r = requests.get(BASE + nom, timeout=120, headers={"User-Agent": "Mozilla/5.0 (recherche COT)"})
        if r.status_code == 200 and r.content[:2] == b"PK":
            print(f"{nom} : {len(r.content) / 1e6:.1f} Mo")
            return r.content
        print(f"{nom} : code {r.status_code}")
    return None


def lignes_nq(contenu):
    out = []
    with zipfile.ZipFile(io.BytesIO(contenu)) as z:
        for n in z.namelist():
            t = pd.read_csv(io.BytesIO(z.read(n)), low_memory=False)
            nom = t["Market_and_Exchange_Names"].astype(str).str.upper()
            t = t[nom.str.contains("NASDAQ") & nom.str.contains("MINI") & ~nom.str.contains("MICRO")]
            out.append(t[[c for c in GARDER if c in t.columns]])
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def main():
    parts = []
    hist = telecharger(["fin_fut_txt_2006_2016.zip", "fut_fin_txt_2006_2016.zip"])
    if hist is None:
        sys.exit("historique 2006 - 2016 introuvable")
    parts.append(lignes_nq(hist))
    for an in range(2017, dt.date.today().year + 1):
        c = telecharger([f"fut_fin_txt_{an}.zip"])
        if c is None:
            sys.exit(f"annee {an} introuvable")
        parts.append(lignes_nq(c))
    t = pd.concat(parts, ignore_index=True).drop_duplicates()
    t = t.sort_values(["Report_Date_as_YYYY-MM-DD", "Market_and_Exchange_Names"])
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(SORTIE, index=False)
    print(f"{len(t)} lignes NQ, {t['Report_Date_as_YYYY-MM-DD'].min()} - {t['Report_Date_as_YYYY-MM-DD'].max()} ; marches : "
          + " | ".join(sorted(t["Market_and_Exchange_Names"].unique())))


if __name__ == "__main__":
    main()
