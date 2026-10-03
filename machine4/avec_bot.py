#!/usr/bin/env python3
"""Machine 4, etape 5 du tri (README.md) : les strategies du palier retenue ou interessante ajoutees au bot (zone + RSI(2),
1 MNQ), meme code que protection/piste6.py (gain de la strategie ajoute en fin de seance). Ecrit avec_bot.txt."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "protection"))
import machine4 as M  # noqa: E402
import piste6 as P6  # noqa: E402
import protection as P  # noqa: E402

res = json.loads((ICI / "coffre4.json").read_text())["candidates"]
choisies = [x for x in res if x["palier"] in ("retenue", "interessante")]
D = M.charger("2100-01-01")
I = M.indicateurs(D)
PP, COTE = M.dollars(D)
jours, O, H, L, C, Z, dec, voulu, ouvert = P.donnees()
nj = len(jours)
dates = pd.DatetimeIndex(jours)
zt = P.tableaux_zone(Z, nj, np.ones(len(Z), bool))
a = (O, H, L, C) + tuple(zt) + (dec, voulu, ouvert)
fz, fr = P.FRAIS_ZONE, P.FRAIS_RSI
cands = {"bot seul": np.zeros(nj)}
for x in choisies:
    row = np.array(x["row"], np.int64)
    g = M.gains(M.pos_de(row, I, D), int(row[1]), D["r"], PP, COTE, D["chg"])
    cands["+ " + x["desc"]] = pd.Series(g, index=D["jours"]).reindex(dates).fillna(0.0).to_numpy()
bot = P6.gains_du_bot(*a, fz, fr)
possibles = [d for d in range(260, nj) if ouvert[d] == 0]
departs = possibles[::P.PAS_DEPART]
expl = [d for d in departs if dates[d] <= pd.Timestamp("2022-12-31")]
coffre = [d for d in departs if dates[d] >= pd.Timestamp("2023-01-01")]
complets = [d for d in possibles if dates[d] >= pd.Timestamp("2023-01-01") and d + P.MAX_SEANCES <= nj][::2]
Lg = ["Machine 4 : strategies du palier interessante ajoutees au bot (zone + RSI(2), 1 MNQ)", "",
      "source | gain par an | corr. quotidienne avec le bot (2023-2026) | Trail 2011-2022 : reussis / perdus / score |"
      " Trail 2023-2026 : idem | S2F + plafond 500 $ : recu en 12 mois / au moins un retrait"]
base = None
for nom, x in cands.items():
    c23 = dates >= pd.Timestamp("2023-01-01")
    corr = float(np.corrcoef(x[c23], bot[c23])[0, 1]) if x[c23].std() > 0 else float("nan")
    par_an = x[260:].sum() / ((dates[-1] - dates[260]).days / 365.25)

    def bil(ds):
        r = np.array([P6.trail(int(d), P.MAX_SEANCES, *a, x, fz, fr)[0] for d in ds])
        return 100 * (r == 1).mean(), 100 * (r == -1).mean(), 100 * ((r == 1).mean() - (r == -1).mean())
    b1, b2 = bil(expl), bil(coffre)
    s = [P6.s2f(int(d), P.MAX_SEANCES, *a, x, fz, fr) for d in complets]
    recu, ret = np.mean([q[2] - 57.0 for q in s]), np.mean([q[1] > 0 for q in s])
    Lg.append(f"{nom} | {par_an:+,.0f} $ | {corr:+.2f} | {b1[0]:.1f} / {b1[1]:.1f} / {b1[2]:+.1f} |"
              f" {b2[0]:.1f} / {b2[1]:.1f} / {b2[2]:+.1f} | {recu:+,.0f} $ / {ret:.0%}")
    if base is None:
        base = (b1[2], b2[2])
    else:
        Lg.append(f"  -> score Trail {b1[2]:+.1f} contre {base[0]:+.1f} (2011-2022), {b2[2]:+.1f} contre {base[1]:+.1f} (2023-2026)")
(ICI / "avec_bot.txt").write_text("\n".join(Lg) + "\n")
print("\n".join(Lg))
