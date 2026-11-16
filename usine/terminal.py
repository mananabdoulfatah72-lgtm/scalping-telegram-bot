"""Terminal Kronos NQ : la page publiee (usine/terminal/page.html), faite des resultats de kronos_nq.py.

Usage : KB_MINUTES=<nasdaq100_1min.csv.gz> python3 usine/terminal.py
Pour les 5 dernieres seances calculees : bougies de 5 minutes, les 100 trajectoires de chaque decision, ce qui s'est passe ;
plus le verdict du test (resultats/<date>/kronos.json).
"""
import json
import sys
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import donnees as Dn  # noqa: E402
import kronos_nq as K  # noqa: E402


def principal():
    D = Dn.charger(); J = D["J"]; pos = {str(j): i for i, j in enumerate(J)}
    dec = [json.loads(l) for l in K.FICHIER.read_text().splitlines() if l.strip()]
    avec = [d for d in dec if d["decisions"][0].get("chemins")][-5:]
    seances = []
    for d in avec:
        s = pos[d["jour"]]
        b = [[round(float(D["O"][s, 5 * k]), 2), round(float(D["H"][s, 5 * k:5 * k + 5].max()), 2),
              round(float(D["L"][s, 5 * k:5 * k + 5].min()), 2), round(float(D["C"][s, 5 * k + 4]), 2)] for k in range(78)]
        seances.append(dict(jour=d["jour"], bougies=b,
                            decisions=[dict(bloc=x["bloc"], f=x["f"], derniere=x["derniere"], chemins=x["chemins"]) for x in d["decisions"]]))
    res = sorted((ICI / "resultats").glob("*/kronos.json"))
    verdict = json.loads(res[-1].read_text()) if res else None
    donnees = json.dumps(dict(seances=seances, verdict=verdict), ensure_ascii=False, separators=(",", ":"))
    page = (ICI / "terminal" / "modele.html").read_text(encoding="utf-8").replace("/*DONNEES*/null", donnees)
    (ICI / "terminal" / "page.html").write_text(page, encoding="utf-8")
    print(f"page ecrite : {len(seances)} seances, {len(page) / 1e3:.0f} ko")


if __name__ == "__main__":
    principal()
