#!/usr/bin/env python3
"""Arene, vague 4 (ml/arene/VAGUE4.md, regles fixees avant calcul) : le meme Supertrend NQ, en mieux. W1 tri des signaux par
apprentissage en marche avant, W2 taille selon l'agitation, W3 les deux. Mesure 2017 - 2026, en direct dans l'arene.
MINUTES_NQ=... CACHE_DOSSIER=... python3 vague4.py <dossier de l'arene>"""
import glob
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from scipy import stats

import bots as BT
from direct import Direct

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import donnees as Dn  # noqa: E402

R = Path(__file__).resolve().parents[2]
DOSSIER = sys.argv[1]
B = BT.Base(os.environ["CACHE_DOSSIER"])
O, H, L, C, V = B.O, B.H, B.L, B.C, B.V
F = B.X["F"]; ATR = B.atr
aj = B.an[B.test]; n = len(B.test); jours = [B.J[s] for s in B.test]; W = aj >= 2017; d17 = int(np.argmax(W))
PAS = 5

d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(R / "radar/donnees/jour/yahoo/*.csv.gz")))])
v = d[d.serie.isin(["^VIX:c", "^VIX3M:c"])].pivot_table(index="date", columns="serie", values="valeur"); v.index = pd.to_datetime(v.index)
tous = pd.to_datetime([B.J[s] for s in range(len(B.J))])
veille = v.reindex(tous.union(v.index)).ffill().shift(1).reindex(tous)
ECART_VIX = (veille["^VIX:c"] - veille["^VIX3M:c"]).to_numpy()

ST = sorted(BT.supertrend(B), key=lambda t: (t[0], t[2]))
DX = Direct(DOSSIER)
DX.maj(force=True, phase="Vague 4 : le même Supertrend, en mieux", detail="préparation", progression=0.0, fini=False, jours=jours[::PAS], curseur=0, pied=[
    ("vague 4", "signaux du Supertrend NQ inchangés : tri par apprentissage (marche en avant), taille selon l'agitation (ml/arene/VAGUE4.md)"),
    ("mieux que le Supertrend", "sur 2017 - 2026 : t ≥ 2 et Benjamini-Hochberg, deux moitiés positives, frais doublés, 7 années sur 10, 80 % des séances, survie +10 points, 20 % de grillés en moins, net au moins égal"),
    ("compte", "Master 50K Option 2, limite du bot 400 $ par MNQ, 3 $ de frais par MNQ"),
    ("période", f"{jours[0]} → {jours[-1]}, mesure 2017 - 2026")])
DX.dire("Vague 4 : je garde les signaux du Supertrend NQ et je change ce qu'on en fait (trier les signaux, régler la taille).", "a")

# ------------------------------------------------------------------ W1 : variables connues avant chaque entree, etiquettes
X, y, an_t = [], [], []
for k, (s, sens, m, _, fin, e, x) in enumerate(ST):
    if k == 0 or ST[k - 1][0] != s:
        nb_avant, res_avant = 0, 0.0
    g = BT.bougie_avant(s, m)
    tp = (H[s, :m] + L[s, :m] + C[s, :m]) / 3; vv = V[s, :m]
    vw = (tp * vv).sum() / vv.sum() if vv.sum() > 0 else tp.mean()
    atr = ATR[g] if g >= 0 and np.isfinite(ATR[g]) and ATR[g] > 0 else np.nan
    gap = O[s, 0] / C[s - 1, 389] - 1 if s > 0 and B.ok[s - 1] else np.nan
    X.append(np.r_[F[g] if g >= 0 else np.full(F.shape[1], np.nan),
                   sens, m, sens * (O[s, m] - vw) / atr, sens * (O[s, m] / O[s, 0] - 1), sens * gap, ECART_VIX[s], nb_avant, res_avant])
    pnl = sens * (x - e) * 2.0 * Dn.PREF / e - Dn.FRAIS
    y.append(int(pnl > 0)); an_t.append(int(B.J[s][:4]))
    nb_avant += 1; res_avant += pnl
X, y, an_t = np.array(X, float), np.array(y), np.array(an_t)
garde = np.ones(len(ST), bool); proba = np.full(len(ST), np.nan)
for Y in range(2017, 2027):
    app, test = an_t < Y, an_t == Y
    if not test.any():
        continue
    mdl = xgb.XGBClassifier(n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                            min_child_weight=20, random_state=0, n_jobs=4, eval_metric="logloss")
    mdl.fit(X[app], y[app]); p = mdl.predict_proba(X[test])[:, 1]; seuil = y[app].mean()
    proba[test] = p; garde[test] = p > seuil
    DX.dire(f"W1 · {Y} : appris sur {app.sum():,} trades de 2011 à {Y - 1} (gagnants {seuil:.0%}) ; garde {garde[test].mean():.0%} des {test.sum()} trades de {Y}.".replace(",", " "), "c")
    DX.maj(force=True, progression=0.05 + 0.4 * (Y - 2016) / 10, phase="Vague 4 : W1 tri des signaux (marche en avant)", detail=f"année {Y}")
W1 = [t for t, g_ in zip(ST, garde) if g_]

# ------------------------------------------------------------------ W2 : taille selon l'agitation (connue la veille)
OKs = np.nonzero(B.ok)[0]
cl = pd.Series(C[OKs, 389], index=OKs)
rv = cl.pct_change().rolling(20).std().shift(1)
rang = rv.rolling(252, min_periods=126).rank(pct=True)
TAILLE = np.ones(len(B.J), int)
TAILLE[OKs] = np.where(rang.to_numpy() < 0.5, 2, 1)


def journees_taille(tr, frais=3.0, taille_var=False):
    r1, d1, n1 = BT.journees(B, tr, 1, 400.0, frais)
    if not taille_var:
        return r1, d1, n1
    r2, d2, _ = BT.journees(B, tr, 2, 800.0, frais)
    return np.where(TAILLE == 2, r2, r1), np.where(TAILLE == 2, d2, d1), n1


def mesures(tr, taille_var=False):
    r, dp, ntr = journees_taille(tr, 3.0, taille_var); r6 = journees_taille(tr, 6.0, taille_var)[0]
    j, dd, tt = r[B.test], dp[B.test], ntr[B.test] > 0
    jw, dw = j[W], dd[W]; cum = np.cumsum(jw); a = aj[W]
    vie = BT.vie(np.vstack([j, j, j]), np.vstack([dd, dd, dd]), tt, debut=d17)
    idx = pd.to_datetime(np.array(jours)[W]); sj = pd.Series(jw, index=idx)
    sem = sj.groupby([idx.isocalendar().year.values, idx.isocalendar().week.values]).sum(); mo = sj.groupby(idx.to_period("M")).sum()
    m = dict(par_seance=float(jw.mean()), t=BT.tst(jw), t_avant=BT.tst(jw[a <= 2022]), t_apres=BT.tst(jw[a >= 2023]), t_frais6=BT.tst(r6[B.test][W]),
             annees_pos=int(sum(jw[a == yy].sum() > 0 for yy in range(2017, 2027))), seances_tradees=float(tt[W].mean()),
             jours_positifs=float((jw[tt[W]] > 0).mean()), semaines_positives=float((sem > 0).mean()), mois_positifs=float((mo > 0).mean()),
             pire_semaine=float(sem.min()), pire_jour=float(jw.min()), pire_baisse=float((cum - np.maximum.accumulate(cum)).min()),
             survie_60=float(1 - BT.grilles_depuis(jw, dw, 60).mean()), grille_250=float(BT.grilles_depuis(jw, dw, 250).mean()),
             periode=float(j[np.array([x >= "2026-08-11" for x in jours])].sum()), net_an=vie["net_an"], grilles_an=vie["grilles_an"])
    return j, m


def resume(nom, m):
    return (f"{nom} (2017 - 2026) : {m['par_seance']:+.1f} $ par séance, t {m['t']:.2f} (depuis 2023 : {m['t_apres']:.2f}), {m['seances_tradees']:.0%} des séances, "
            f"{m['semaines_positives']:.0%} de semaines positives ; compte : survie {m['survie_60']:.0%}, grillé en 1 an {m['grille_250']:.0%}, "
            f"{m['grilles_an']:.2f} masters grillés par an, net {m['net_an']:,.0f} $ par an").replace(",", " ")


def ligne(ident, nom, j, coul, m, statut, raison=""):
    Lg = DX.ligne(ident, nom, statut, coul)
    Lg["courbe"] = [round(float(x), 1) for x in np.cumsum(j)[::PAS]]; Lg["stats"] = m; Lg["raison"] = raison
    Lg["tri"] = (2 if statut == "retenu" else -2 if statut == "tué" else 0) + (m.get("survie_60") or 0) - (m.get("grilles_an") or 0)
    DX.maj(relief=True, curseur=len(Lg["courbe"]) - 1)


j_st, ref = mesures(ST)
ligne("st", "Supertrend NQ (référence)", j_st, "#3cc8ff", ref, "référence"); DX.dire(resume("Supertrend NQ", ref), "c")
V6 = [t for t in ST if (lambda s, sens, m: sens * (O[s, m] - ((((H[s, :m] + L[s, :m] + C[s, :m]) / 3) * V[s, :m]).sum() / V[s, :m].sum()
                                                         if V[s, :m].sum() > 0 else ((H[s, :m] + L[s, :m] + C[s, :m]) / 3).mean())) > 0)(t[0], t[1], t[2])]
j_v6, m_v6 = mesures(V6)
ligne("V6", "V6 · Supertrend avec la VWAP (vague 3, en observation)", j_v6, "#48cae4", m_v6, "référence"); DX.dire(resume("V6 (pour comparer)", m_v6), "c")

RES = {}
for k, (ident, nom, tr, tv, coul) in enumerate((("W1", "W1 · Supertrend trié par apprentissage", W1, False, "#ffd166"),
                                                 ("W2", "W2 · Supertrend, taille selon l'agitation", ST, True, "#f4a261"),
                                                 ("W3", "W3 · trié + taille selon l'agitation", W1, True, "#e76f51"))):
    DX.maj(force=True, progression=0.5 + 0.15 * k, phase=f"Vague 4 : {nom}", detail="rejeu minute par minute")
    j, m = mesures(tr, tv)
    raisons = []
    if m["t"] < 2: raisons.append(f"t {m['t']:.2f} sous 2")
    if m["t_avant"] <= 0 or m["t_apres"] <= 0: raisons.append("négatif sur 2017-2022 ou sur 2023-2026")
    if m["t_frais6"] < 1.5: raisons.append(f"avec 6 $ de frais t {m['t_frais6']:.2f}")
    if m["annees_pos"] < 7: raisons.append(f"{m['annees_pos']} années positives sur 10")
    if m["seances_tradees"] < 0.8: raisons.append(f"trade seulement {m['seances_tradees']:.0%} des séances")
    if m["survie_60"] < ref["survie_60"] + 0.10 - 1e-9: raisons.append(f"survie {m['survie_60']:.0%} (il faut {ref['survie_60'] + 0.10:.0%})")
    if m["grilles_an"] > 0.8 * ref["grilles_an"] + 1e-9: raisons.append(f"{m['grilles_an']:.2f} masters grillés par an (il faut au plus {0.8 * ref['grilles_an']:.2f})")
    if m["pire_baisse"] < 1.25 * ref["pire_baisse"]: raisons.append("pire baisse trop profonde")
    if m["net_an"] < ref["net_an"]: raisons.append(f"net {m['net_an']:,.0f} $ par an, moins que le Supertrend ({ref['net_an']:,.0f} $)".replace(",", " "))
    RES[ident] = dict(nom=nom, trades=len(tr), raisons=raisons, **m)
    ligne(ident, nom, j, coul, m, "tué" if raisons else "en cours", "; ".join(raisons))
    DX.dire(resume(nom, m) + (f" → tué ({'; '.join(raisons)})." if raisons else " → passe ses règles, en attente de la correction des tests multiples."), "b" if raisons else "h")
    time.sleep(0.3)

cles = list(RES); p = np.array([1 - stats.norm.cdf(RES[c]["t"]) for c in cles]); o = np.argsort(p)
okk = p[o] <= 0.05 * np.arange(1, len(p) + 1) / len(p); kk = (np.nonzero(okk)[0].max() + 1) if okk.any() else 0
bh = {cles[i] for i in o[:kk]}
for c in cles:
    RES[c]["p"] = float(p[cles.index(c)]); RES[c]["bh"] = c in bh
    if c not in bh: RES[c]["raisons"].append("ne survit pas à Benjamini-Hochberg")
    RES[c]["retenu"] = not RES[c]["raisons"]
    for Lg in DX.e["lignes"]:
        if Lg["id"] == c:
            Lg["statut"] = "retenu" if RES[c]["retenu"] else "tué"; Lg["raison"] = "; ".join(RES[c]["raisons"])
g_ = [c for c in cles if RES[c]["retenu"]]
DX.dire("Correction des tests multiples faite : " + (", ".join(g_) + " retenu(s)." if g_ else "aucun ne fait nettement mieux que le Supertrend NQ."), "a")
json.dump(dict(reference=ref, v6=m_v6, candidats=RES, garde_par_an={str(Y): float(garde[an_t == Y].mean()) for Y in range(2017, 2027)}),
          open(os.path.join(DOSSIER, "vague4.json"), "w"), default=float)
DX.maj(relief=True, force=True, progression=1.0, phase="Vague 4 terminée", detail="3 candidats testés", fini=True)
DX.dire("Vague 4 terminée.", "a")
