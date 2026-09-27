#!/usr/bin/env python3
"""Dates des annonces des reunions programmees du FOMC (dernier jour de chaque reunion), lues dans
les pages du calendrier de la Fed telechargees par telecharger_fomc.sh. Les reunions non programmees
et les conferences telephoniques sont exclues (comme Lucca et Moench, 2015)."""
import gzip
import re
from pathlib import Path

import pandas as pd

D = Path(__file__).parent / "donnees" / "fomc"
MOIS = {m: i + 1 for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                         "September", "October", "November", "December"])}
ABR = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}


def _texte(f):
    html = gzip.open(f, "rt", encoding="utf-8", errors="ignore").read()
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "\n", html))


def historiques():
    dates = []
    # "March 17-18 Meeting - 2015", "January 31-February 1 Meeting - 2017" ou "Jan/Feb 31-1 Meeting - 2017"
    mois_re = "|".join(MOIS)
    abr_re = "|".join(ABR)
    motif = re.compile(r"(?:(%s)/(%s)|(%s)) (\d{1,2})(?:-(?:(%s) )?(\d{1,2}))? Meeting( \(unscheduled\))? - (\d{4})"
                       % (abr_re, abr_re, mois_re, mois_re))
    for f in sorted(D.glob("fomchistorical*.htm.gz")):
        for a1, a2, m1, j1, m2, j2, non_prog, a in motif.findall(_texte(f)):
            if non_prog:
                continue
            if a1:                                        # "Jan/Feb 31-1" : le 2e jour est dans le 2e mois
                mois = ABR[a2] if j2 and int(j2) < int(j1) else ABR[a1]
            else:
                mois = MOIS[m2] if m2 else MOIS[m1]
            dates.append(pd.Timestamp(int(a), mois, int(j2 or j1)))
    return dates


def recentes():
    lignes = [l.strip() for l in re.sub(r"<[^>]+>", "\n", gzip.open(D / "fomccalendars.htm.gz", "rt", encoding="utf-8",
                                                                     errors="ignore").read()).split("\n") if l.strip()]
    dates, annee = [], None
    for i, l in enumerate(lignes):
        m = re.fullmatch(r"(\d{4}) FOMC Meetings", l)
        if m:
            annee = int(m.group(1))
            continue
        if annee is None or not re.fullmatch(r"(%s)(/(%s))?" % ("|".join(MOIS) + "|" + "|".join(ABR), "|".join(ABR)), l):
            continue
        suite = lignes[i + 1] if i + 1 < len(lignes) else ""
        j = re.fullmatch(r"(\d{1,2})(?:-(\d{1,2}))?\*?", suite)
        if not j:
            continue
        voisin = " ".join(lignes[i + 2:i + 5]).lower()
        if "unscheduled" in voisin or "notation vote" in voisin:
            continue
        parts = l.split("/")
        m1 = MOIS.get(parts[0], ABR.get(parts[0]))
        m2 = ABR[parts[1]] if len(parts) == 2 else m1
        j1, j2 = int(j.group(1)), int(j.group(2) or j.group(1))
        mois = m2 if j.group(2) and j2 < j1 else m1
        dates.append(pd.Timestamp(annee, mois, j2))
    return dates


def annonces():
    d = pd.DatetimeIndex(sorted(set(historiques()) | set(recentes())))
    return d


if __name__ == "__main__":
    d = annonces()
    print(d.to_series().groupby(d.year).size().to_dict())
    print([x.date().isoformat() for x in d[d.year >= 2019]])
