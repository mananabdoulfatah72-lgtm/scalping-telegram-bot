"""Pour information (asie/README.md) : robustesse du test de l or sur le coffre. Usage : ASIE_DONNEES=<dossier> python3 asie/or_robustesse.py"""
import sys, numpy as np, pandas as pd
from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parent))
import machine7 as M7
M = M7.Marche("xauusd"); A, B = M7.DEBUT_COFFRE, M7.FIN
base = dict(nom="or", famille="R1", marche="xauusd", sens=1, sortie="23:30")
d = M7.jouer(base, M, A, B); t_reel = M7.t_stat(d["r"])
# 1. la meme fenetre de 5 h 30 a toutes les autres heures (2023 - 2026)
ts = []
for k in range(-144, 145):
    if abs(k) * 5 <= 120: continue
    x = M7.jouer(base, M, A, B, decalage=k)
    ts.append((M7.t_stat(x["r"]), float(x["brut"].mean()) * 1e4, k))
ts.sort(reverse=True)
print(f"1. placebo 2023-2026 : t reel {t_reel:.2f} ; part des fenetres decalees qui font aussi bien : {np.mean([t >= t_reel for t, _, _ in ts]):.3f} sur {len(ts)}")
print("   meilleures fenetres decalees (t, brut pb, decalage en min) :", [(round(t, 2), round(b, 2), k * 5) for t, b, k in ts[:4]])
print(f"   gain moyen brut d'une fenetre de 5 h 30 au hasard dans la journee : {np.mean([b for _, b, _ in ts]):+.2f} pb contre {d['brut'].mean() * 1e4:+.2f} pb a 18 h")
# 2. entree un peu plus tard, frais doubles
J = M7.soirs(A, B)
for hh in ("18:05", "18:15", "18:30"):
    ie = M.indice(M7.utc(J, M7.NY, hh)); i_s = M.indice(M7.utc(J, M7.NY, "23:30"))
    ok = (ie >= 0) & (i_s > ie); e = M.O[ie[ok]]; x = M.O[i_s[ok]]; g = np.isfinite(e) & np.isfinite(x)
    r = x[g] / e[g] - 1 - 2e-4
    print(f"2. entree {hh} : net moyen {r.mean() * 1e4:+.2f} pb, t {M7.t_stat(r):.2f} ; frais doubles (4 pb) depuis 18 h 00 : t {M7.t_stat(d['brut'] - 4e-4):.2f}")
# 3. ou se fait la hausse de l'or : rendement moyen de chaque heure (New York), 2023 - 2026, jours lundi-vendredi
t = pd.date_range(pd.Timestamp(A, tz="UTC"), pd.Timestamp(B, tz="UTC"), freq="5min")
i = M.indice(t); o = M.O[i]; c = M.C[i]
df = pd.DataFrame({"h": t.tz_convert(M7.NY).hour, "r": np.log(c / o)}).dropna()
heure = df.groupby("h")["r"].sum() * 1e4
tot = heure.sum()
print("3. part de la hausse totale de l'or 2023 - 2026 faite a chaque heure (New York) :")
print("   " + " | ".join(f"{h}h {v / tot:+.0%}" for h, v in heure.items()))
# 4. en dollars pour 1 MGC au prix du 2 octobre 2026
p = float(d["e"].iloc[-1]); usd = (d["brut"] - 4.0 / (10 * d["e"])) * 10 * p
cum = usd.cumsum(); dd = (cum - cum.cummax()).min()
ie = M.indice(M7.utc(pd.DatetimeIndex(d["jour"]), M7.NY, "18:00")); fin = M.indice(M7.utc(pd.DatetimeIndex(d["jour"]), M7.NY, "23:30"))
pire = [float((np.nanmin(M.L[a:b]) / M.O[a] - 1) * 10 * p) for a, b in zip(ie, fin)]
print(f"4. 1 MGC a {p:.0f} $ : {usd.mean():+.0f} $ par soir, ecart-type {usd.std():.0f} $, soirs gagnants {np.mean(usd > 0):.0%}, pire soir {usd.min():+.0f} $, "
      f"pire moment d'un soir {min(pire):+.0f} $, pire baisse {dd:+.0f} $, total {cum.iloc[-1]:+.0f} $ sur {len(usd)} soirs")
