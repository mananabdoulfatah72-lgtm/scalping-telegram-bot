#!/usr/bin/env python3
"""Gain de chaque seance du bot seul (zone de bruit + RSI(2), 1 MNQ, sans filtre delta qui n'existe pas avant 2026),
calcule par protection/piste6.py gains_du_bot. Ecrit bot_quotidien.csv (date, gain en $). Lancer depuis ce dossier."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "protection"))
import protection as P  # noqa: E402
import piste6  # noqa: E402

jours, O, H, L, C, Z, dec, voulu, ouvert = P.donnees()
zt = P.tableaux_zone(Z, len(jours), np.ones(len(Z), bool))
gain = piste6.gains_du_bot(O, H, L, C, *zt, dec, voulu, ouvert, P.FRAIS_ZONE, P.FRAIS_RSI)
d = pd.DataFrame({"date": pd.DatetimeIndex(jours).strftime("%Y-%m-%d"), "gain": np.round(gain, 2)})
d.iloc[260:].to_csv(ICI / "bot_quotidien.csv", index=False)
print(f"{len(d) - 260} seances, du {d['date'].iloc[260]} au {d['date'].iloc[-1]}, total {d['gain'].iloc[260:].sum():+,.0f} $")
