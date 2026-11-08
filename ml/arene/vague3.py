#!/usr/bin/env python3
"""Arene, vague 3 (ml/arene/VAGUE3.md, regles fixees avant calcul) : un Supertrend en mieux. Sept candidats qui suivent la
tendance du jour et tradent presque chaque seance, rejoues minute par minute et affiches en direct dans l'arene.
MINUTES_NQ=... CACHE_DOSSIER=... python3 vague3.py <dossier de l'arene> [--verif]"""
import glob
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import bots as BT
from direct import Direct

ICI = Path(__file__).resolve().parent; R = ICI.parents[1]
DOSSIER = sys.argv[1]
B = BT.Base(os.environ["CACHE_DOSSIER"])
O, H, L, C, V = B.O, B.H, B.L, B.C, B.V
OK = np.nonzero(B.ok)[0]
aj = B.an[B.test]; n = len(B.test); jours = [B.J[s] for s in B.test]


# ------------------------------------------------------------------ candidats
def orb(nm):
    """Cassure des nm premieres minutes : sens de la plage, entree a l'ouverture de la minute nm, stop a l'autre bout de la
    plage, objectif 10 fois le risque, sinon sortie a 16 h."""
    out = []
    for s in OK:
        o, c = O[s, 0], C[s, nm - 1]
        if not np.isfinite(o + c) or c == o:
            continue
        sens = 1 if c > o else -1
        e = O[s, nm]; stop = L[s, :nm].min() if sens > 0 else H[s, :nm].max()
        risque = (e - stop) * sens
        if risque <= 0:
            continue                                         # ouverture deja au-dela du stop : pas de trade
        cible = e + sens * 10 * risque
        x, fin = C[s, 389], 389
        for m in range(nm, 390):
            if sens > 0:
                if m > nm and O[s, m] <= stop: x, fin = O[s, m], m - 1; break
                if L[s, m] <= stop: x, fin = stop, m - 1; break
                if m > nm and O[s, m] >= cible: x, fin = O[s, m], m - 1; break
                if H[s, m] >= cible: x, fin = cible, m - 1; break
            else:
                if m > nm and O[s, m] >= stop: x, fin = O[s, m], m - 1; break
                if H[s, m] >= stop: x, fin = stop, m - 1; break
                if m > nm and O[s, m] <= cible: x, fin = O[s, m], m - 1; break
                if L[s, m] <= cible: x, fin = cible, m - 1; break
        out.append((int(s), sens, nm, nm, int(fin), float(e), float(x)))
    return out


def gao():
    """Elan de la derniere demi-heure : signe du rendement de la cloture de la veille a 10 h, joue de 15 h 30 a 16 h."""
    out = []
    for s in OK:
        if s == 0 or not B.ok[s - 1]:
            continue
        r1 = C[s, 29] / C[s - 1, 389] - 1
        if not np.isfinite(r1) or r1 == 0:
            continue
        out.append((int(s), 1 if r1 > 0 else -1, 360, 360, 389, float(O[s, 360]), float(C[s, 389])))
    return out


def supertrend_k(k):
    """Le Supertrend NQ (10, 3) sur bougies de k minutes, calcule en continu sur les seances completes ; decision a la cloture
    de la bougie, ordre a l'ouverture de la minute suivante, pas d'entree apres 15 h, a plat a la cloture de 15 h 54."""
    nb = 390 // k; S = len(OK); N = S * nb
    h, l, c = np.empty(N), np.empty(N), np.empty(N)
    for i, s in enumerate(OK):
        for b in range(nb):
            j = i * nb + b
            h[j] = H[s, k * b:k * b + k].max(); l[j] = L[s, k * b:k * b + k].min(); c[j] = C[s, k * b + k - 1]
    st = np.zeros(N); atr, hb, lb, d = 0.0, np.nan, np.nan, 1.0
    for j in range(1, N):
        tr = max(h[j] - l[j], abs(h[j] - c[j - 1]), abs(l[j] - c[j - 1]))
        atr = tr if j == 1 else (atr * 9 + tr) / 10
        mid = (h[j] + l[j]) / 2; hb2, lb2 = mid + 3 * atr, mid - 3 * atr
        if j > 1:
            hb2 = hb2 if (hb2 < hb or c[j - 1] > hb) else hb
            lb2 = lb2 if (lb2 > lb or c[j - 1] < lb) else lb
            if d > 0 and c[j] < lb2: d = -1.0
            elif d < 0 and c[j] > hb2: d = 1.0
        hb, lb = hb2, lb2
        st[j] = d if j >= 10 else 0.0
    out, derniere, aplat = [], 360, 384
    for i, s in enumerate(OK):
        pos, m_in, e = 0, -1, 0.0
        for b in range(nb - 2):
            m = k * b + k
            if m > aplat:
                break
            sens = st[i * nb + b]; cible = pos if sens == 0 else int(sens)
            if cible != pos and pos != 0:
                out.append((int(s), pos, m_in, m_in, m - 1, float(e), float(O[s, m]))); pos = 0
            if cible != 0 and pos == 0 and m <= derniere:
                pos, m_in, e = cible, m, O[s, m]
        if pos != 0:
            out.append((int(s), pos, m_in, m_in, aplat, float(e), float(C[s, aplat])))
    return out


def avec_vwap(tr):
    garde = []
    for t in tr:
        s, sens, m = t[0], t[1], t[2]
        tp = (H[s, :m] + L[s, :m] + C[s, :m]) / 3; v = V[s, :m]
        vw = (tp * v).sum() / v.sum() if v.sum() > 0 else tp.mean()
        if sens * (O[s, m] - vw) > 0:
            garde.append(t)
    return garde


d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(R / "radar/donnees/jour/yahoo/*.csv.gz")))])
v = d[d.serie.isin(["^VIX:c", "^VIX3M:c"])].pivot_table(index="date", columns="serie", values="valeur"); v.index = pd.to_datetime(v.index)
tous = pd.to_datetime([B.J[s] for s in range(len(B.J))])
veille = v.reindex(tous.union(v.index)).ffill().shift(1).reindex(tous)
INV = (veille["^VIX:c"] >= veille["^VIX3M:c"]).to_numpy()

ST = BT.supertrend(B)
if "--verif" in sys.argv:                                     # le Supertrend generique a 5 min doit retrouver l'officiel
    a = sorted((t[0], t[1], t[2], round(t[5], 2)) for t in supertrend_k(5)); b = sorted((t[0], t[1], t[2], round(t[5], 2)) for t in ST)
    commun = len(set(a) & set(b)); print(f"Supertrend générique 5 min : {len(a)} trades, officiel {len(b)}, communs {commun} ({commun / len(b):.1%})")
    sys.exit()


# ------------------------------------------------------------------ mesures
def profil(tr, ensemble=False):
    f = BT.journees_ensemble if ensemble else BT.journees
    r, dp, ntr = f(B, tr, 400.0) if ensemble else f(B, tr, 1, 400.0)
    r6 = (BT.journees_ensemble(B, tr, 400.0, 6.0) if ensemble else BT.journees(B, tr, 1, 400.0, 6.0))[0]
    m = BT.mesures(B, r, dp, ntr); j = r[B.test]; tt = ntr[B.test] > 0
    m["t_frais6"] = BT.tst(r6[B.test]); m["seances_tradees"] = float(tt.mean())
    m["jours_positifs"] = float((j[tt] > 0).mean()) if tt.any() else 0.0
    idx = pd.to_datetime(jours); sj = pd.Series(j, index=idx)
    sem = sj.groupby([idx.isocalendar().year.values, idx.isocalendar().week.values]).sum(); mo = sj.groupby(idx.to_period("M")).sum()
    m["semaines_positives"] = float((sem > 0).mean()); m["mois_positifs"] = float((mo > 0).mean()); m["pire_semaine"] = float(sem.min())
    m["apres_2023_06"] = float(j[np.array([x >= "2023-06-01" for x in jours])].mean())
    return r, dp, ntr, m


DX = Direct(DOSSIER)
PAS = 5
DX.maj(force=True, phase="Vague 3 : un Supertrend en mieux", detail="préparation", progression=0.0, fini=False, jours=jours[::PAS], curseur=0, pied=[
    ("vague 3", "7 candidats qui suivent la tendance du jour, règles fixées avant calcul (ml/arene/VAGUE3.md)"),
    ("mieux que le Supertrend", "t ≥ 2 et Benjamini-Hochberg, positif 2014-22 et 2023-26, frais doublés, 9 années sur 13, 80 % des séances tradées, survie 60 j ≥ 56 %, ≤ 0,97 master grillé par an"),
    ("compte", "Master 50K Option 2, 1 MNQ, limite du bot 400 $, 3 $ de frais"),
    ("période", f"{jours[0]} → {jours[-1]} ({n} séances)")])
DX.dire("Vague 3 : je cherche un Supertrend en mieux, qui trade presque tous les jours et grille moins de comptes.", "a")


def ligne(ident, nom, j, coul, m, statut, raison=""):
    Lg = DX.ligne(ident, nom, statut, coul)
    Lg["courbe"] = [round(float(x), 1) for x in np.cumsum(j)[::PAS]]; Lg["stats"] = m; Lg["raison"] = raison
    Lg["tri"] = (2 if statut == "retenu" else -2 if statut == "tué" else 0) + (m.get("survie_60") or 0) - (m.get("grilles_an") or 0)
    DX.maj(relief=True, curseur=len(Lg["courbe"]) - 1)
    return Lg


def resume(nom, m):
    return (f"{nom} : {m['par_seance']:+.1f} $ par séance, t {m['t']:.2f} (depuis 2023 : {m['t_apres']:.2f}), {m['seances_tradees']:.0%} des séances tradées, "
            f"{m['jours_positifs']:.0%} de journées positives, {m['semaines_positives']:.0%} de semaines positives ; compte : survie {m['survie_60']:.0%}, "
            f"grillé en 1 an {m['grille_250']:.0%}, {m['grilles_an']:.2f} masters grillés par an, net {m['net_an']:,.0f} $ par an").replace(",", " ")


Z12 = [t for t in BT.zone(B) if not INV[t[0]]]
REF = {}
for ident, nom, tr, coul in (("st", "Supertrend NQ (référence)", ST, "#3cc8ff"), ("Z12", "Z12 · Bot 3 en 1 sans VIX inversé (référence)", Z12, "#5ad1c8")):
    r, dp, ntr, m = profil(tr); REF[ident] = (tr, m)
    ligne(ident, nom, r[B.test], coul, m, "référence"); DX.dire(resume(nom, m), "c"); time.sleep(0.3)

CAND = [("V1", "V1 · cassure des 5 premières minutes", lambda: orb(5), "#ffd166"),
        ("V2", "V2 · cassure des 15 premières minutes", lambda: orb(15), "#f4a261"),
        ("V3", "V3 · cassure des 30 premières minutes", lambda: orb(30), "#e76f51"),
        ("V4", "V4 · élan de la dernière demi-heure", gao, "#b5e48c"),
        ("V5", "V5 · Supertrend sur bougies de 15 min", lambda: supertrend_k(15), "#90e0ef"),
        ("V6", "V6 · Supertrend avec la VWAP", lambda: avec_vwap(ST), "#48cae4"),
        ("V7", "V7 · Supertrend sans les jours de VIX inversé", lambda: [t for t in ST if not INV[t[0]]], "#00b4d8")]
RES, TR = {}, {}
for k, (ident, nom, fab, coul) in enumerate(CAND):
    DX.maj(force=True, progression=(k + 0.5) / (len(CAND) + 2), phase=f"Vague 3 : {nom}", detail="reconstruction des trades et rejeu minute par minute")
    tr = fab(); TR[ident] = tr
    r, dp, ntr, m = profil(tr)
    st = REF["st"][1]; raisons = []
    if m["t"] < 2: raisons.append(f"t {m['t']:.2f} sous 2")
    if m["t_avant"] <= 0 or m["t_apres"] <= 0: raisons.append("négatif sur 2014-2022 ou sur 2023-2026")
    if m["t_frais6"] < 1.5: raisons.append(f"avec 6 $ de frais t {m['t_frais6']:.2f}")
    if m["annees_pos"] < 9: raisons.append(f"{m['annees_pos']} années positives sur 13")
    if m["seances_tradees"] < 0.8: raisons.append(f"trade seulement {m['seances_tradees']:.0%} des séances")
    if m["survie_60"] < 0.56: raisons.append(f"survie {m['survie_60']:.0%} sous 56 %")
    if m["grilles_an"] > 0.97: raisons.append(f"{m['grilles_an']:.2f} masters grillés par an (plus de 0,97)")
    if m["pire_baisse"] < 1.25 * st["pire_baisse"]: raisons.append("pire baisse trop profonde")
    if ident in ("V1", "V2", "V3") and m["apres_2023_06"] <= 0: raisons.append("négatif depuis la publication (juin 2023)")
    RES[ident] = dict(nom=nom, trades=len(tr), raisons=raisons, **m)
    ligne(ident, nom, r[B.test], coul, m, "tué" if raisons else "en cours", "; ".join(raisons))
    DX.dire(resume(nom, m) + (f" → tué ({'; '.join(raisons)})." if raisons else " → passe ses règles, en attente de la correction des tests multiples."), "b" if raisons else "h")

# Benjamini-Hochberg sur les 7
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
gardes = [c for c in cles if RES[c]["retenu"]]
DX.dire("Correction des tests multiples faite : " + (", ".join(gardes) + " retenu(s)." if gardes else "aucun candidat ne fait mieux que le Supertrend NQ."), "a")
DX.maj(relief=True, force=True, progression=(len(CAND) + 0.5) / (len(CAND) + 2), phase="Vague 3 : Z12 + candidat sur le même compte")

# Z12 + candidat retenu, meme compte, limite commune
ENS = {}
z = REF["Z12"][1]
for c in gardes:
    r, dp, ntr, m = profil(Z12 + TR[c], ensemble=True)
    raisons = []
    if m["survie_60"] < z["survie_60"] - 1e-9: raisons.append(f"survie {m['survie_60']:.0%} sous celle de Z12 ({z['survie_60']:.0%})")
    if m["grilles_an"] > z["grilles_an"] + 1e-9: raisons.append(f"{m['grilles_an']:.2f} masters grillés par an, plus que Z12 ({z['grilles_an']:.2f})")
    if m["seances_tradees"] <= z["seances_tradees"]: raisons.append("ne trade pas plus de séances")
    ENS[c] = dict(nom=f"Z12 + {c}", raisons=raisons, garde=not raisons, **m)
    ligne(f"Z12+{c}", f"Z12 + {RES[c]['nom']}", r[B.test], "#ffffff", m, "retenu" if not raisons else "tué", "; ".join(raisons))
    DX.dire(resume(f"Z12 + {c} (même compte)", m) + (" → gardé." if not raisons else f" → pas mieux que Z12 seul ({'; '.join(raisons)})."), "h" if not raisons else "b")
json.dump(dict(references={k: v[1] for k, v in REF.items()}, candidats=RES, ensembles=ENS), open(os.path.join(DOSSIER, "vague3.json"), "w"), default=float)
DX.maj(relief=True, force=True, progression=1.0, phase="Vague 3 terminée", detail="7 candidats testés", fini=True)
DX.dire("Vague 3 terminée.", "a")
