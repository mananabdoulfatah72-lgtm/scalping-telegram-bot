#!/usr/bin/env python3
"""Demo du terminal live : la page du relais (bot3en1/Relais.Quantower/live.html), avec a la place du relais un lecteur qui
rejoue les vraies minutes du mercredi 28 octobre 2026 (jour de decision de la Fed, 14 h New York) :
- NQ : minutes de Rithmic (9 h 30 - 16 h) avec les vrais achats et ventes a l'agression ; la nuit et 16 h - 17 h : minutes
  Yahoo du radar (NQ=F), volumes remis a l'echelle de Rithmic ;
- ES, YM, RTY, CL, GC, ZN : minutes Yahoo du radar ; VIX, dollar, Bitcoin, megacaps : minutes Yahoo du radar ;
- filtre VIX du Bot 3 en 1 : clotures du 27 octobre ; calendrier et nouvelles : seulement ce dont on a une trace reelle
  (le communique de la Fed de 14 h, flux RSS officiel).
Rien n'est invente ; ce qui manque (gros ordres, nouvelles du jour) est dit dans la page.
python3 terminal/live/demo.py <dossier contenant depuis13/> <sortie.html>"""
import glob
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[2]
SCR, SORTIE = Path(sys.argv[1]), Path(sys.argv[2])
J, JP = pd.Timestamp("2026-10-28"), pd.Timestamp("2026-10-27")
G = 1380
NY = "America/New_York"


def globex(t):
    """(jour Globex, minute depuis 18 h) pour des heures de New York sans fuseau."""
    h, m = t.dt.hour, t.dt.minute
    jour = t.dt.normalize() + pd.to_timedelta((h >= 18).astype(int), unit="D")
    i = np.where(h >= 18, (h - 18) * 60 + m, np.where(h < 17, (h + 6) * 60 + m, -1))
    return jour, i


# ------------------------------------------------------------------ minutes du radar (heure de New York)
fichiers = [f for f in sorted(glob.glob(str(R / "radar/donnees/minutes/2026/*.csv.gz"))) if "2026-09-20" <= Path(f).name[:10] <= "2026-10-28"]
rad = pd.concat([pd.read_csv(f) for f in fichiers])
rad["t"] = pd.to_datetime(rad.t); rad["jour"], rad["i"] = globex(rad.t)
rad = rad[rad.i >= 0]


def par_jour(sym):
    x = rad[rad.symbole == sym]
    out = {}
    for j, g in x.groupby("jour"):
        B = [None] * G
        for r in g.itertuples():
            B[int(r.i)] = [float(r.o), float(r.h), float(r.l), float(r.c), float(r.v), 0.0, 0.0]
        out[j] = B
    return out


def stats_hist(jours, avant, echelle=1.0):
    """Cloture de la veille, volume moyen par minute et plage moyenne sur les 20 seances (au moins 600 minutes) avant `avant`."""
    passes = [j for j in sorted(jours) if j < avant]
    pleins = [j for j in passes if sum(b is not None for b in jours[j]) >= 600][-20:]
    clot = None
    if passes:
        der = [b for b in jours[passes[-1]] if b]
        clot = der[-1][3] if der else None
    vm = [round(float(np.mean([(jours[j][k][4] if jours[j][k] else 0.0) for j in pleins])) * echelle, 1) for k in range(G)] if pleins else None
    pl = float(np.mean([max(b[1] for b in jours[j] if b) - min(b[2] for b in jours[j] if b) for j in pleins])) if pleins else None
    return clot, vm, pl, len(pleins)


marches = []
# ------------------------------------------------------------------ NQ : Rithmic (seance US, vrais achats / ventes) + Yahoo (nuit)
mn = pd.read_csv(SCR / "depuis13/minutes.csv"); mn["t"] = pd.to_datetime(mn.t)
ag = pd.read_csv(SCR / "depuis13/agresseurs.csv")
nqy = par_jour("NQ=F")
aujY = nqy[J]
rth = mn[mn.t.dt.normalize() == J]
agj = ag[ag.jour == "2026-10-28"].set_index("minute")
vR = rth.v.sum(); vY = sum(aujY[930 + k][4] for k in range(390) if aujY[930 + k])
f = vR / vY if vY else 1.0                                              # volumes Yahoo remis a l'echelle de Rithmic
B = [None if b is None else [b[0], b[1], b[2], b[3], round(b[4] * f), 0.0, 0.0] for b in aujY]
for r in rth.itertuples():
    k = r.t.hour * 60 + r.t.minute - 570
    a = agj.loc[k] if k in agj.index else None
    B[930 + k] = [float(r.o), float(r.h), float(r.l), float(r.c), float(r.v), float(a.achats) if a is not None else 0.0, float(a.ventes) if a is not None else 0.0]
clot, vmY, pl, ns = stats_hist(nqy, J, f)
# volume habituel de la seance US : minutes de Rithmic des 20 seances precedentes
hist = mn[(mn.t.dt.normalize() < J) & (mn.t.dt.normalize() >= J - pd.Timedelta(days=40))]
hist = hist[hist.t.dt.normalize().isin(sorted(hist.t.dt.normalize().unique())[-20:])]
vm_rth = hist.assign(k=hist.t.dt.hour * 60 + hist.t.dt.minute - 570).groupby("k").v.mean()
vm = list(vmY) if vmY else [0.0] * G
for k, v in vm_rth.items():
    if 0 <= k < 390: vm[930 + k] = round(float(v), 1)
marches.append(dict(nom="NQ", symbole="NQZ6", barres=[[i] + b for i, b in enumerate(B) if b], cloturePrec=clot, plageMoyenne=pl, seances=ns, volMoyen=vm))
print(f"NQ : {sum(b is not None for b in B)} minutes, facteur de volume de nuit {f:.2f}, cloture de la veille {clot}, {ns} seances de reference, "
      f"{len(agj)} minutes avec achats et ventes")
# ------------------------------------------------------------------ autres contrats (Yahoo)
for nom, sym, code in (("ES", "ES=F", "ESZ6"), ("YM", "YM=F", "YMZ6"), ("RTY", "RTY=F", "RTYZ6"), ("CL", "CL=F", "CLZ6"), ("GC", "GC=F", "GCZ6"), ("ZN", "ZN=F", "ZNZ6")):
    d = par_jour(sym)
    if J not in d: continue
    clot, vm, pl, ns = stats_hist(d, J)
    marches.append(dict(nom=nom, symbole=code, barres=[[i] + b for i, b in enumerate(d[J]) if b], cloturePrec=clot, plageMoyenne=pl, seances=ns, volMoyen=vm))
    print(f"{nom} : {sum(b is not None for b in d[J])} minutes, cloture de la veille {clot}, {ns} seances")

# ------------------------------------------------------------------ cotations (minutes Yahoo) et clotures de la veille
jour = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(R / "radar/donnees/jour/yahoo/*.csv.gz")))])
jour = jour[jour.date == "2026-10-27"].set_index("serie").valeur
debut = pd.Timestamp("2026-10-27 18:00").tz_localize(NY); fin = pd.Timestamp("2026-10-28 17:00").tz_localize(NY)
cot = []
for sym in ("^VIX", "DX-Y.NYB", "BTC-USD", "NVDA", "MSFT", "AAPL", "AMZN", "GOOGL", "META", "AVGO", "TSLA"):
    x = rad[rad.symbole == sym].copy(); x["u"] = x.t.dt.tz_localize(NY)
    x = x[(x.u >= debut) & (x.u < fin)].sort_values("u")
    veille = jour.get(f"{sym}:c")
    if x.empty or veille is None: continue
    cot.append(dict(symbole=sym, nom=sym, veille=float(veille), pts=[[int(u.timestamp()), round(float(c), 4)] for u, c in zip(x.u, x.c)]))
vv, v3 = float(jour["^VIX:c"]), float(jour["^VIX3M:c"])
iso = lambda s: pd.Timestamp(s).tz_localize(NY).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")
DEMO = dict(jour="2026-10-28", jourPrec="2026-10-27", debutUtc=int(debut.timestamp() * 1000), depart=840, marches=marches, cotations=cot,
            vixVeille=dict(pour="2026-10-28", date="2026-10-27", vix=vv, vix3m=v3, inverse=vv >= v3),
            calendrier=[dict(titre="FOMC Statement (décision de taux de la Fed)", pays="USD", date=iso("2026-10-28 14:00"), impact="High", prevision="", precedent="", reel="")],
            nouvelles=[dict(titre="Federal Reserve issues FOMC statement", lien="", source="federalreserve.gov", resume="Communiqué de la Fed (flux RSS officiel de la Réserve fédérale).",
                            date=iso("2026-10-28 14:00"), vu=iso("2026-10-28 14:00"))])
print(f"cotations : {[c['symbole'] for c in cot]} ; VIX {vv} / VIX 3 mois {v3} a la cloture du 27 octobre")

# ------------------------------------------------------------------ la page
page = (R / "bot3en1/Relais.Quantower/live.html").read_text()
tete = re.search(r"<head>(.*)</head>", page, re.S).group(1); corps = re.search(r"<body>(.*)</body>", page, re.S).group(1)
tete = re.sub(r'<meta charset="utf-8">\s*<meta name="viewport"[^>]*>', "", tete).replace("<title>NQ Live</title>", '<title>NQ Live Démo</title>\n<meta name="claude:viewport-fit-sides" content="cover">')
tete = tete.replace("body { color: var(--blanc); font-family: var(--mono); font-size: 13px; line-height: 1.4; margin: 0; padding: 0 12px 24px; }",
                    "body { color: var(--blanc); background: var(--noir); font-family: var(--mono); font-size: 13px; line-height: 1.4; margin: 0; padding-block: 0 24px; "
                    "padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }\n"
                    "body::before { content: \"\"; position: fixed; inset: 0 0 auto; height: env(safe-area-inset-top, 0px); z-index: 10; background: var(--noir); }")
tete = tete.replace(".tete { position: sticky; top: 0;", ".tete { position: sticky; top: env(safe-area-inset-top, 0px);")
tete = tete.replace("</style>", (Path(__file__).parent / "demo.css").read_text() + "</style>")
corps = corps.replace('<nav class="nav"><a href="/">STATION</a> <a href="/live" aria-current="page">LIVE</a></nav>', '<span class="puce demo-puce"><span class="k">DÉMO</span>28 octobre 2026 rejoué</span>')
corps = corps.replace('<div class="bande" id="bande"></div>', '<div class="bande" id="bande"></div>\n' + (Path(__file__).parent / "demo_barre.html").read_text())
corps = corps.replace('<main class="grille">\n  <div class="col">', '<main class="grille">\n  <div class="col">\n' + (Path(__file__).parent / "demo_guide.html").read_text())
moteur = (Path(__file__).parent / "demo.js").read_text()
donnees = json.dumps(DEMO, separators=(",", ":")).replace("</", "<\\/")
corps = corps.replace('<script>\n"use strict";', f'<script type="application/json" id="demo-donnees">{donnees}</script>\n<script>\n{moteur}\n</script>\n<script>\n"use strict";', 1)
assert "demo-donnees" in corps and "demo-barre" in corps and "demo-guide" in corps
SORTIE.write_text(tete.strip() + "\n" + corps.strip() + "\n")
print(SORTIE, round(SORTIE.stat().st_size / 1e3), "ko")
