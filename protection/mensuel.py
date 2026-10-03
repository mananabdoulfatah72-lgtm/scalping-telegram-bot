#!/usr/bin/env python3
"""Descriptif : gain mensuel de chaque partie du bot 3 en 1 (1 MNQ) - zone de bruit seule, RSI(2) seul, les deux, et le
filtre delta reel (connu d'avril a septembre 2026 seulement, orderflow/zone_avril_septembre_2026.csv). Meme moteur que
piste6.gains_du_bot (frais compris, sans regles de compte). Ecrit mensuel.txt. Lancer depuis ce dossier."""
import numpy as np
import pandas as pd

import piste6 as P6
import protection as P

jours, O, H, L, C, Z, dec, voulu, ouvert = P.donnees()
nj = len(jours)
dates = pd.DatetimeIndex(jours)
fz, fr = P.FRAIS_ZONE, P.FRAIS_RSI
of = pd.read_csv(P.ICI.parent / "orderflow" / "zone_avril_septembre_2026.csv", parse_dates=["jour"])
cle = pd.MultiIndex.from_arrays([pd.DatetimeIndex(dates[Z["d"].to_numpy()]), Z["me"], Z["sens"]])
filtre = pd.Series(of["garde"].astype(bool).to_numpy(), index=pd.MultiIndex.from_arrays([of["jour"], of["minute"], of["sens"]]))
garde_reel = filtre.reindex(cle).fillna(True).to_numpy(bool)            # avant avril 2026 : pas de delta, trade garde
connu = filtre.reindex(cle).notna().to_numpy()
tout, rien = np.ones(len(Z), bool), np.zeros(len(Z), bool)
zero = np.zeros(nj, np.int64)


def gains(garde, rsi=True):
    zt = P.tableaux_zone(Z, nj, garde)
    return P6.gains_du_bot(O, H, L, C, *zt, dec, voulu if rsi else zero, ouvert if rsi else zero, fz, fr)


g = pd.DataFrame({"zone": gains(tout, False), "rsi2": gains(rien, True), "bot": gains(tout, True),
                  "bot_filtre": gains(garde_reel, True)}, index=dates).iloc[260:]
m = g.groupby(g.index.to_period("M")).sum()
m["apport_filtre"] = m["bot_filtre"] - m["bot"]
L = [f"Gain mensuel du bot 3 en 1, 1 MNQ, frais compris (sans regles de compte) ; {g.index[0].date()} - {g.index[-1].date()}",
     f"Filtre delta reel connu sur {connu.sum()} trades de zone (avril - septembre 2026) ; avant, le bot garde tous les trades", "",
     "periode | zone seule $/mois | RSI(2) seul $/mois | zone + RSI(2) $/mois | mois positifs | pire mois | meilleur mois"]
for nom, a, b in (("2012-2022", "2012-01", "2022-12"), ("2023-2025", "2023-01", "2025-12"), ("2026 (janv. - sept.)", "2026-01", "2026-09"),
                  ("2012-2026", "2012-01", "2026-09")):
    x = m.loc[a:b]
    L.append(f"{nom} | {x['zone'].mean():+,.0f} | {x['rsi2'].mean():+,.0f} | {x['bot'].mean():+,.0f} | "
             f"{(x['bot'] > 0).mean():.0%} | {x['bot'].min():+,.0f} | {x['bot'].max():+,.0f}")
L += ["", "par annee | zone | RSI(2) | zone + RSI(2) | mois positifs"]
for a, x in m.groupby(m.index.year):
    L.append(f"{a} | {x['zone'].sum():+,.0f} | {x['rsi2'].sum():+,.0f} | {x['bot'].sum():+,.0f} | {(x['bot'] > 0).sum()}/{len(x)}")
L += ["", "2026 mois par mois | zone | RSI(2) | zone + RSI(2) | avec le filtre delta reel | apport du filtre"]
for p, x in m.loc["2026-01":].iterrows():
    L.append(f"{p} | {x['zone']:+,.0f} | {x['rsi2']:+,.0f} | {x['bot']:+,.0f} | {x['bot_filtre']:+,.0f} | {x['apport_filtre']:+,.0f}")
x = m.loc["2026-04":"2026-09"]
L.append(f"avril - septembre 2026 | {x['zone'].sum():+,.0f} | {x['rsi2'].sum():+,.0f} | {x['bot'].sum():+,.0f} | "
         f"{x['bot_filtre'].sum():+,.0f} | {x['apport_filtre'].sum():+,.0f}")
c = np.corrcoef(g["zone"], g["rsi2"])[0, 1]
cm = np.corrcoef(m["zone"], m["rsi2"])[0, 1]
L += ["", f"Correlation zone / RSI(2) : {c:+.2f} par jour, {cm:+.2f} par mois",
      f"Mois ou les deux perdent : {((m['zone'] < 0) & (m['rsi2'] < 0)).mean():.0%} ; zone perd mais RSI(2) gagne : "
      f"{((m['zone'] < 0) & (m['rsi2'] > 0)).mean():.0%} ; l'inverse : {((m['zone'] > 0) & (m['rsi2'] < 0)).mean():.0%}"]
(P.ICI / "mensuel.txt").write_text("\n".join(L) + "\n")
print("\n".join(L))
