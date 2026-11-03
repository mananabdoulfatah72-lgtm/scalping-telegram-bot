#!/usr/bin/env python3
"""Donnees du terminal NQ (toutes reelles) : minutes 2011 -> 12 oct. 2026 (Databento) + export Rithmic 13 oct. -> 2 nov. 2026."""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

S = Path("/tmp/claude-0/-home-user-scalping-telegram-bot/73d2fc28-0760-5668-987b-2a927564efe7/scratchpad")
sys.path.insert(0, "/home/user/scalping-telegram-bot/audit/machine6")
import pyramide as P  # noqa: E402

N = 390
PREF = 28500.0
J, O, H, L, C, ok = P.jours(str(S / "depuis13/minutes.csv"))
NJ = len(J)
an = np.array([int(j[:4]) for j in J])
dates = pd.to_datetime(J)
print("seances", NJ, J[0], J[-1])

# ------------------------------------------------------------------ Supertrend continu (ligne et sens par barre de 5 min)
h5 = H.reshape(NJ, 78, 5).max(2).ravel(); l5 = L.reshape(NJ, 78, 5).min(2).ravel(); c5 = C[:, 4::5].ravel(); o5 = O[:, 0::5].ravel()
n5 = len(c5)
st = np.zeros(n5); ligne = np.full(n5, np.nan); atrs = np.zeros(n5)
atr, hb, lb, d = 0.0, np.nan, np.nan, 1.0
for i in range(1, n5):
    tr = max(h5[i] - l5[i], abs(h5[i] - c5[i - 1]), abs(l5[i] - c5[i - 1]))
    atr = tr if i == 1 else (atr * 9 + tr) / 10
    mid = (h5[i] + l5[i]) / 2
    hb2, lb2 = mid + 3 * atr, mid - 3 * atr
    if i > 1:
        hb2 = hb2 if (hb2 < hb or c5[i - 1] > hb) else hb
        lb2 = lb2 if (lb2 > lb or c5[i - 1] < lb) else lb
        if d > 0 and c5[i] < lb2:
            d = -1.0
        elif d < 0 and c5[i] > hb2:
            d = 1.0
    hb, lb = hb2, lb2
    st[i] = d if i >= 10 else 0.0
    ligne[i] = lb if d > 0 else hb
    atrs[i] = atr

# trades du Supertrend (regle H12, identique au moteur C#)
st_trades = []
for s in range(NJ):
    if not ok[s]:
        continue
    pos, m_in, e = 0, -1, 0.0
    for b in range(76):
        i = s * 78 + b
        cible = pos if st[i] == 0 else int(st[i])
        m = 5 * b + 5
        if cible != pos and pos != 0:
            st_trades.append((s, pos, m_in, m, e, O[s, m])); pos = 0
        if cible != 0 and pos == 0 and m <= 360:
            pos, m_in, e = cible, m, O[s, m]
    if pos != 0:
        st_trades.append((s, pos, m_in, 385, e, C[s, 384]))
stt = pd.DataFrame(st_trades, columns=["s", "sens", "m_in", "m_out", "e", "x"])
stt["pts"] = stt.sens * (stt.x - stt.e)
stt["usd"] = 2 * stt.pts * PREF / O[stt.s, 0] - 3
st_jour = np.zeros(NJ); np.add.at(st_jour, stt.s.to_numpy(), stt.usd.to_numpy())
# controle : trades du 13 oct. au 2 nov. identiques au rejeu C#
cs = pd.read_csv(S / "depuis13/st_trades.csv"); cs = cs[cs.jour >= "2026-10-13"]
py = stt[stt.s >= np.searchsorted(J, "2026-10-13")]
assert len(cs) == len(py) and np.allclose(cs.entree.values, py.e.values) and np.allclose(cs.sortie.values, py.x.values), "Supertrend different du moteur C#"

# ------------------------------------------------------------------ zone (bot 3 en 1, C2 + Q1) : trades par seance
LIGNE = re.compile(r"^(\d{4}-\d{2}-\d{2}) (achat|vente|sortie|stop)\b(?: (\d+)h(\d+))?(?: (\d+)h(\d+))?.*? a ([0-9.]+)")
def zone_trades(fichier, de, a, filtre):
    out, ouvert = [], None
    for l in Path(fichier).read_text().splitlines():
        g = LIGNE.match(l)
        if not g or "ecarte" in l or "RSI" in l:
            continue
        j = g.group(1)
        if not (de <= j <= a):
            continue
        h, mi = int(g.group(5) or g.group(3)), int(g.group(6) or g.group(4))
        mm, px = h * 60 + mi - 570, float(g.group(7))
        if g.group(2) in ("achat", "vente"):
            dl = re.search(r"delta 30 min ([+-]?\d+)", l)
            ouvert = (j, 1 if g.group(2) == "achat" else -1, mm, px, int(dl.group(1)) if dl and filtre else None)
        elif ouvert:
            out.append(dict(jour=ouvert[0], sens=ouvert[1], m_in=ouvert[2], e=ouvert[3], delta=ouvert[4], m_out=mm, x=px)); ouvert = None
    return out
zt = zone_trades(S / "audit/c2q1.txt", "2011-01-01", "2026-10-12", False) + zone_trades(S / "depuis13/zone.txt", "2026-10-13", "2026-11-02", True)
zt = pd.DataFrame(zt)
pos_j = {j: i for i, j in enumerate(J)}
zt = zt[zt.jour.isin(pos_j)].copy()
zt["s"] = zt.jour.map(pos_j)
zt["pts"] = zt.sens * (zt.x - zt.e)
zt["usd"] = 2 * zt.pts * PREF / O[zt.s, 0] - 3
zone_jour = np.zeros(NJ); np.add.at(zone_jour, zt.s.to_numpy(), zt.usd.to_numpy())

# ------------------------------------------------------------------ seances : quotidien, VWAP, zone de bruit
dO, dH, dL, dC = O[:, 0], H.max(1), L.min(1), C[:, N - 1]
prevC = np.r_[np.nan, dC[:-1]]
typ = (H + L + C) / 3
vol_src = pd.read_csv(S / "depuis13/minutes.csv", usecols=["t", "v"])
vol_src["j"] = vol_src.t.str[:10]; vol_src["m"] = vol_src.t.str[11:13].astype(int) * 60 + vol_src.t.str[14:16].astype(int) - 570
vol_src = vol_src[(vol_src.m >= 0) & (vol_src.m < N)]
V = np.zeros((NJ, N)); V[pd.Index(J).get_indexer(vol_src.j), vol_src.m.to_numpy()] = vol_src.v.to_numpy(float)
cumv = np.cumsum(V, 1); vwap = np.where(cumv > 0, np.cumsum(typ * V, 1) / np.maximum(cumv, 1), np.cumsum(typ, 1) / np.arange(1, N + 1))
# sigma de la zone (14 seances completes precedentes), bandes par controle
mv = np.abs(C[:, 30::30][:, :12] / dO[:, None] - 1)
sig = np.full((NJ, 12), np.nan)
comp = np.where(ok)[0]
for s in range(NJ):
    p = comp[comp < s]
    if len(p) >= 14:
        sig[s] = mv[p[-14:]].mean(0)
veille = np.full(NJ, np.nan)
for s in range(1, NJ):
    p = comp[comp < s]
    if len(p):
        veille[s] = dC[p[-1]]
# prochaine seance (3 novembre) : ecart de la zone par controle, au prix de cloture du 2 novembre
s_next_sig = mv[comp[-14:]].mean(0)

# ------------------------------------------------------------------ 1. MARCHE
D = {}
k = NJ - 1
rv = pd.Series(np.log(dC / prevC)).rolling(20).std() * np.sqrt(252) * 100
D["marche"] = dict(
    date=J[k], dernier=float(dC[k]), veille=float(dC[k - 1]), haut=float(dH[k]), bas=float(dL[k]), ouverture=float(dO[k]),
    atr5=float(atrs[(k + 1) * 78 - 1]), st_sens=int(st[(k + 1) * 78 - 1]), st_ligne=float(ligne[(k + 1) * 78 - 1]),
    vol20=float(rv.iloc[k]), vol20_med=float(rv.iloc[-252:].median()),
    zone_ecart=[round(float(x) * dC[k], 1) for x in s_next_sig], zone_pct=[round(float(x) * 100, 3) for x in s_next_sig],
    range_moy20=float((dH - dL)[-20:].mean()),
    quotidien=[[J[i], float(dO[i]), float(dH[i]), float(dL[i]), float(dC[i])] for i in range(NJ - 260, NJ)],
)

# ------------------------------------------------------------------ 2. GRAPHIQUE : 60 dernieres seances, barres de 5 min
seances = []
for s in range(NJ - 60, NJ):
    b0 = s * 78
    bars = [[round(float(o5[b0 + b]), 2), round(float(h5[b0 + b]), 2), round(float(l5[b0 + b]), 2), round(float(c5[b0 + b]), 2)] for b in range(78)]
    vw = [round(float(vwap[s, 5 * b + 4]), 2) for b in range(78)]
    li = [round(float(ligne[b0 + b]), 2) for b in range(78)]
    sn = [int(st[b0 + b]) for b in range(78)]
    ref_h, ref_b = max(dO[s], veille[s]), min(dO[s], veille[s])
    bandes = [[(k_ + 1) * 30, round(float(ref_h * (1 + sig[s, k_])), 2), round(float(ref_b * (1 - sig[s, k_])), 2)] for k_ in range(12)] if not np.isnan(sig[s, 0]) else []
    sti = stt[stt.s == s]; zti = zt[zt.s == s]
    seances.append(dict(
        jour=J[s], complete=bool(ok[s]), veille=float(veille[s]), barres=bars, vwap=vw, ligne=li, sens=sn, bandes=bandes,
        st=[[int(r.sens), int(r.m_in), int(r.m_out), float(r.e), float(r.x), round(float(r.pts), 2)] for r in sti.itertuples()],
        zone=[[int(r.sens), int(r.m_in), int(r.m_out), float(r.e), float(r.x), round(float(r.pts), 2), r.delta] for r in zti.itertuples()],
        st_usd=round(float(st_jour[s]), 1), zone_usd=round(float(zone_jour[s]), 1), delta_reel=J[s] >= "2026-10-13"))
D["seances"] = seances

# ------------------------------------------------------------------ 3. AGENTS
def stats(x):
    x = np.asarray(x, float)
    return dict(n=int(len(x)), moy=float(x.mean()), t=float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))))
okj = ok & (np.arange(NJ) > 30)
def courbe(jour):
    sr = pd.Series(jour[okj], index=dates[okj]).resample("W-FRI").sum().cumsum()
    return [[d.strftime("%Y-%m-%d"), round(float(v), 1)] for d, v in sr.items()]
def bilan(tr, jour):
    w = tr.usd.to_numpy()
    cum = np.cumsum(jour[okj])
    an_ = pd.Series(jour[okj], index=an[okj]).groupby(level=0).sum()
    return dict(trades=int(len(w)), par_trade=float(w.mean()), gagnants=float((w > 0).mean() * 100),
                pf=float(w[w > 0].sum() / -w[w < 0].sum()), pire_baisse=float((cum - np.maximum.accumulate(cum)).min()),
                seance=stats(jour[okj]), depuis2023=stats(jour[okj & (an >= 2023)]), avant2023=stats(jour[okj & (an < 2023)]),
                trades_par_seance=float(len(w) / okj.sum()), annees={int(a_): round(float(v)) for a_, v in an_.items()},
                courbe=courbe(jour))
D["agents"] = dict(zone=bilan(zt, zone_jour), st=bilan(stt, st_jour),
                   correlation=float(np.corrcoef(zone_jour[okj], st_jour[okj])[0, 1]))
rec = [s for s in range(NJ) if J[s] >= "2026-10-13"]
D["agents"]["recent"] = [[J[s], round(float(st_jour[s])), round(float(zone_jour[s])), int((stt.s == s).sum()), int((zt.s == s).sum())] for s in rec]

# ------------------------------------------------------------------ 5. LABO : variables connues avant la decision, et ce qui suit
def pct(a, b):
    return (a / b - 1) * 100
gap = pct(dO, prevC)
r30 = pct(C[:, 29], dO)
prev_ret = np.r_[np.nan, pct(dC[1:], dC[:-1])]
rvq = rv.shift(1).to_numpy()
regime = np.full(NJ, np.nan)
for s in range(260, NJ):
    w = rvq[s - 250:s]; w = w[~np.isnan(w)]
    if len(w) and not np.isnan(rvq[s]):
        regime[s] = (w < rvq[s]).mean() * 100
lab = dict(
    jour=list(J), dow=[int(x) for x in dates.dayofweek], an=[int(x) for x in an], complete=[bool(x) for x in ok],
    gap=np.round(gap, 3).tolist(), veille=np.round(prev_ret, 3).tolist(), r30=np.round(r30, 3).tolist(), regime=np.round(regime, 1).tolist(),
    oc=np.round(pct(dC, dO), 3).tolist(), r10c=np.round(pct(dC, C[:, 29]), 3).tolist(), derniere_h=np.round(pct(dC, C[:, 329]), 3).tolist(),
    premiere_h=np.round(pct(C[:, 59], dO), 3).tolist(), st=np.round(st_jour, 1).tolist(), zone=np.round(zone_jour, 1).tolist())
for kk in ("gap", "veille", "r30", "regime", "oc", "r10c", "derniere_h", "premiere_h"):
    lab[kk] = [None if (v is None or (isinstance(v, float) and np.isnan(v))) else v for v in lab[kk]]
D["labo"] = lab

# relief : |rendement| moyen par demi-heure et par annee (points de base)
rel = []
for a_ in range(2011, 2027):
    sel = ok & (an == a_)
    row = []
    for h in range(13):
        m0, m1 = h * 30, min(h * 30 + 29, N - 1)
        row.append(round(float(np.nanmean(np.abs(C[sel, m1] / O[sel, m0] - 1)) * 1e4), 2))
    rel.append(row)
D["relief"] = dict(annees=list(range(2011, 2027)), valeurs=rel)

# ------------------------------------------------------------------ 6. CALENDRIER
D["calendrier"] = [
    ["2026-11-12", "Dernier jour du challenge (reglage du bot)", "challenge"],
    ["2026-11-26", "Thanksgiving : Bourse fermee, seance courte du NQ (pas de trade)", "court"],
    ["2026-11-27", "Lendemain de Thanksgiving : seance courte (pas de trade)", "court"],
    ["2026-12-09", "Annonce de la Fed (pas de zone ce jour-la)", "fed"],
    ["2026-12-16", "Changement de contrat : NQZ6 -> NQH7, MNQZ6 -> MNQH7", "contrat"],
    ["2026-12-24", "Veille de Noel : seance courte (pas de trade)", "court"],
    ["2026-12-25", "Noel : marche ferme", "ferme"],
    ["2027-01-01", "Jour de l'an : marche ferme", "ferme"],
]
# ------------------------------------------------------------------ 4. RISQUE : challenge Bulenox, plancher suivi en temps reel (simulateur audit/machine6)
import sim  # noqa: E402
def grille(tr, entree_ouverture):
    tr = tr.sort_values(["s", "m_in"])
    td = tr.s.to_numpy().astype(np.int64)
    jd = np.searchsorted(td, np.arange(NJ), "left").astype(np.int64); jf = np.searchsorted(td, np.arange(NJ), "right").astype(np.int64)
    me = tr.m_in.to_numpy() - (1 if entree_ouverture else 0)
    mx = np.where(tr.m_out.to_numpy() >= 385, 384, tr.m_out.to_numpy() - (1 if entree_ouverture else 0))
    args = (O, H, L, C, jd, jf, tr.sens.to_numpy().astype(np.int64), me.astype(np.int64), mx.astype(np.int64),
            tr.e.to_numpy(float), tr.x.to_numpy(float), np.ones(len(tr)), tr.e.to_numpy(float))
    pris = np.ones(len(tr), np.bool_)
    return args, pris
GR = {}
debut_ok = np.where(ok & (np.arange(NJ) > 120))[0]
for nom, tr, eo, tailles in (("zone", zt, False, (1, 2, 3, 4, 5, 6)), ("st", stt, True, (1, 2, 3, 4))):
    args, pris = grille(tr, eo)
    for compte, (s0, h0, ns) in {"actuel": (50000.0, 51500.0, 8), "nouveau": (50000.0, 50000.0, 22)}.items():
        for T in tailles:
            for lim in (300, 400, 500, 600, 800, 1000, 0):
                for per, deb in (("15ans", debut_ok), ("2024", debut_ok[an[debut_ok] >= 2024])):
                    deb = deb[deb + ns <= NJ].astype(np.int64)
                    prm = np.array([T, lim or 1e9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0, PREF, 0], float)
                    r, _ = sim.lot(deb, ns, prm, s0, h0, *args, pris, 53000.0, 2500.0, 50100.0)
                    r = r[r != 9]
                    GR[f"{nom}|{compte}|{T}|{lim}|{per}"] = [round((r == 1).mean() * 100, 1), round((r == -1).mean() * 100, 1)]
D["risque"] = GR
print("grille", len(GR), "; zone actuel 4/1000", GR["zone|actuel|4|1000|15ans"], "; st actuel 1/400", GR["st|actuel|1|400|15ans"])

def propre(o, chemin="D"):
    if isinstance(o, dict):
        return {k: propre(v, f"{chemin}.{k}") for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [propre(v, chemin) for v in o]
    if isinstance(o, (float, np.floating)):
        if not np.isfinite(o):
            vides.add(chemin)
            return None
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o
vides = set()
D = propre(D)
print("valeurs absentes remplacees par null dans :", sorted(vides))
json.dump(D, open(S / "terminal/donnees.json", "w"), separators=(",", ":"), allow_nan=False)
print("ok", (S / "terminal/donnees.json").stat().st_size // 1024, "Ko ;",
      "zone", D["agents"]["zone"]["seance"], "st", D["agents"]["st"]["seance"], "corr", round(D["agents"]["correlation"], 2))
