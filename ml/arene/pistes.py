#!/usr/bin/env python3
"""Arene, etape 3 (ml/arene/PISTES.md, regles fixees avant calcul) : A gestion du capital, B consensus et regimes,
C nouvelles etudes, D Supertrend sur 7 marches. Tout est affiche en direct dans l'arene."""
import json
import os
import sys
import time

import numba as nb
import numpy as np
import pandas as pd
from scipy import stats

import bots as BT
import marches as MK
from direct import Direct

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import donnees as D  # noqa: E402

DOSSIER = sys.argv[1]
DX = Direct(DOSSIER)
etat = json.load(open(os.path.join(DOSSIER, "etat.json")))
DX.e.update({k: etat[k] for k in ("journal", "jours", "pied")})
DX.e["lignes"] = [l for l in etat["lignes"] if l.get("statut") == "référence" or l["id"].startswith("usine")]
rel = json.load(open(os.path.join(DOSSIER, "relief.json")))
for l in DX.e["lignes"]:
    l["courbe"] = rel["courbes"].get(l["id"], [])
DX.e["version"] = etat["version"] + 1; DX.e["version_relief"] = etat["version_relief"] + 1
DX.maj(relief=True, force=True, phase="Étape 3 : quatre nouvelles pistes", detail="préparation", progression=0.0, fini=False)
DX.dire("Étape 3 : je lance les quatre pistes choisies ensemble (règles : ml/arene/PISTES.md).", "a")
B = BT.Base(os.environ["CACHE_DOSSIER"])
X = B.X; F = X["F"]; aj = B.an[B.test]; n = len(B.test); PAS = 5
_, _, _, _, _, VOL, _ = D.nq_minutes()
tst = lambda v: float(v.mean() / v.std(ddof=1) * np.sqrt(len(v))) if len(v) > 2 and v.std() > 0 else 0.0
TESTS = {}                                                              # famille corrigee ensemble (BH)


def ligne(ident, nom, j, coul, stats_, statut="en cours", raison=""):
    L = DX.ligne(ident, nom, statut, coul)
    L["courbe"] = [round(float(x), 1) for x in np.cumsum(j)[::PAS]]; L["stats"] = stats_; L["raison"] = raison
    L["tri"] = (2 if statut == "retenu" else -2 if statut == "tué" else 0) + stats_.get("survie_60", 0)
    DX.maj(relief=True, curseur=len(L["courbe"]) - 1)
    return L


def journees(tr, lim=400.0, taille=1, frais=3.0):
    return BT.journees(B, tr, taille, lim, frais)


def profil(tr, lim=400.0):
    r, d, _ = journees(tr, lim); r6, _, _ = journees(tr, lim, 1, 6.0)
    m = BT.mesures(B, r, d); j = r[B.test]
    m.update(t_frais6=tst(r6[B.test]), annees_pos=int(sum(j[aj == y].sum() > 0 for y in range(2014, 2027))))
    return r, d, m


def regles(m, ref):
    if m["t"] < 2.0: return "t sous 2"
    if m["t_avant"] <= 0 or m["t_apres"] <= 0: return "négative sur une des deux moitiés"
    if m["t_frais6"] < 1.5: return "ne tient pas avec 6 $ de frais"
    if m["annees_pos"] < 9: return f"{m['annees_pos']} années positives sur 13"
    if ref is not None:
        if m["survie_60"] < ref["survie_60"] - 1e-9: return f"survie {m['survie_60']:.0%} sous celle de son bot ({ref['survie_60']:.0%})"
        if m["grilles"] > ref["grilles"]: return f"{m['grilles']} comptes grillés, plus que son bot ({ref['grilles']})"
        if m["pire_baisse"] < 1.25 * ref["pire_baisse"]: return "pire baisse trop profonde"
    return None


base_tr = {"zone": BT.zone(B), "xgb": BT.xgboost(B), "st": BT.supertrend(B), "xgbs": BT.xgboost(B, stop_atr=1.5)}
base = {k: profil(t) for k, t in base_tr.items()}
DX.dire("Les bots de base sont rejoués ; je commence par la piste B (consensus et régimes).", "c")

# ------------------------------------------------------------------ B. consensus et regimes
avant = lambda s, m0: s * 26 + m0 // 15 - 1
sensp = lambda g: 0 if not np.isfinite(B.p[g]) else (1 if B.p[g] > 0.5 else -1)
pistesB = {
    "B1": ("B1 · XGBoost seulement si le Supertrend est d'accord", BT.xgboost(B, filtre=lambda i: F[i, 18] == (1 if B.p[i] > 0.5 else -1)), "xgb"),
    "B2": ("B2 · Supertrend seulement si XGBoost est d'accord", [t for t in base_tr["st"] if sensp(avant(t[0], t[2])) == t[1]], "st"),
    "B3": ("B3 · Bot 3 en 1 seulement si XGBoost est d'accord", [t for t in base_tr["zone"] if sensp(avant(t[0], t[2])) == t[1]], "zone"),
}
resultats = {}
for k, (nom, tr, b0) in pistesB.items():
    r, d, m = profil(tr); raison = regles(m, base[b0][2])
    TESTS[k] = (m["t"], n); resultats[k] = dict(nom=nom, raison=raison, **m)
    ligne(k, nom, r[B.test], "#2fd16f", m, "tué" if raison else "en cours", raison or "")
    DX.dire(f"{nom} : {m['par_seance']:+.1f} $ par séance, t {m['t']:.2f}, {m['grilles']} comptes grillés, survie {m['survie_60']:.0%} → "
            + (f"tuée ({raison})" if raison else "passe ses règles, en attente de la correction des tests multiples"), "b" if raison else "h")

# B4 : choix du bot selon le regime (volatilite x tendance), appris chaque annee sur le passe
Cj = B.C[:, 389]; ret = np.r_[np.nan, Cj[1:] / Cj[:-1] - 1]
sr = pd.Series(ret); vol = sr.rolling(20).std().shift(1); tend = (sr.rolling(20).sum().shift(1)).abs() / (vol * np.sqrt(20))
rv = vol.rolling(252, min_periods=126).rank(pct=True).to_numpy(); rt = tend.rolling(252, min_periods=126).rank(pct=True).to_numpy()
cv_ = np.floor(np.nan_to_num(rv) * 3).clip(0, 2); ct_ = np.floor(np.nan_to_num(rt) * 3).clip(0, 2)
case = np.where(np.isfinite(rv) & np.isfinite(rt), cv_ * 3 + ct_, -1)[B.test].astype(int)
jb = {k: base[k][0][B.test] for k in ("zone", "xgb", "st")}; db = {k: base[k][1][B.test] for k in ("zone", "xgb", "st")}
j4 = np.zeros(n); d4 = np.zeros(n); choix4 = {}
for Y in range(2017, 2027):
    passe = aj < Y; sel = aj == Y
    for c in range(9):
        pas = passe & (case == c)
        meil, gain = None, 0.0
        if pas.sum() >= 30:
            for k in jb:
                g = jb[k][pas].mean()
                if g > gain:
                    meil, gain = k, g
        choix4[(Y, c)] = meil
        q = sel & (case == c)
        if meil:
            j4[q] = jb[meil][q]; d4[q] = db[meil][q]
DX.dire("B4 : chaque année de 2017 à 2026, pour chacun des 9 régimes, j'ai choisi le bot sur les années d'avant seulement.", "c")
d17 = int(np.argmax(aj >= 2017))


def bilan17(j, d):
    jj, dd = j[d17:], d[d17:]
    ret_, nr, gr = BT._vie(jj, dd, 2600.0, 20)
    g60 = np.array([BT._compte(jj, dd, i0, 60)[0] >= 0 for i0 in range(len(jj) - 60)])
    a = aj[d17:]
    return dict(par_seance=float(jj.mean()), t=tst(jj), t_avant=tst(jj[a <= 2022]), t_apres=tst(jj[a >= 2023]), retire_an=ret_ / (len(jj) / 252),
                grilles=int(gr), survie_60=float(1 - g60.mean()))


m4 = bilan17(j4, d4); refs4 = {k: bilan17(jb[k], db[k]) for k in jb}
meilleur = max(refs4, key=lambda k: (refs4[k]["survie_60"], refs4[k]["retire_an"]))
raison4 = None if (m4["t"] >= 2 and m4["t_avant"] > 0 and m4["t_apres"] > 0 and m4["survie_60"] >= refs4[meilleur]["survie_60"] and m4["grilles"] <= refs4[meilleur]["grilles"]) else \
    f"ne bat pas le meilleur bot seul ({ {'zone': 'Bot 3 en 1', 'xgb': 'XGBoost', 'st': 'Supertrend'}[meilleur] }) sur 2017 - 2026"
TESTS["B4"] = (m4["t"], n - d17); resultats["B4"] = dict(nom="B4 · bot choisi selon le régime", raison=raison4, **m4, reference=refs4[meilleur])
ligne("B4", "B4 · bot choisi selon le régime", np.r_[np.zeros(d17), j4[d17:]], "#2fd16f", m4, "tué" if raison4 else "en cours", raison4 or "")
DX.dire(f"B4 : {m4['retire_an']:,.0f} $ retirés par an, {m4['grilles']} comptes grillés, survie {m4['survie_60']:.0%} (meilleur bot seul : "
        f"{refs4[meilleur]['retire_an']:,.0f} $, {refs4[meilleur]['grilles']}, {refs4[meilleur]['survie_60']:.0%}) → {'tuée : ' + raison4 if raison4 else 'passe'}.".replace(",", " "), "b" if raison4 else "h")
DX.maj(force=True, progression=0.3, phase="Étape 3 : piste C (nouvelles études)")

# ------------------------------------------------------------------ C. nouvelles etudes
def vwap_tendance():
    out = []
    for s in B.test:
        O, Cc, H, L, V = B.O[s], B.C[s], B.H[s], B.L[s], VOL[s]
        ty = (H + L + Cc) / 3; cv = np.cumsum(V); vw = np.where(cv > 0, np.cumsum(ty * V) / np.maximum(cv, 1e-9), np.cumsum(ty) / np.arange(1, 391))
        sig = np.sign(Cc - vw)
        pos, m0, e = 0, -1, 0.0
        for m in range(0, 388):
            cible = int(sig[m]) if sig[m] != 0 else pos
            if cible != pos:
                if pos:
                    out.append((s, pos, m0, m, e, O[m + 1]))
                pos, m0, e = cible, m + 1, O[m + 1]
        if pos:
            out.append((s, pos, m0, 388, e, O[389]))
    return out


def fin_de_seance():
    out = []
    for s in B.test:
        if s == 0:
            continue
        r = B.C[s, 359] / B.C[s - 1, 389] - 1
        if r != 0:
            out.append((s, -int(np.sign(r)), 360, 388, B.O[s, 360], B.O[s, 389]))
    return out


for k, nom, f in (("C1", "C1 · la VWAP en tendance (Zarattini et Aziz)", vwap_tendance), ("C2", "C2 · retournement de fin de séance (époque 0DTE)", fin_de_seance)):
    tr = f(); r, d, m = profil(tr, 400.0)
    if k == "C2":
        j = r[B.test]; m["t_0dte"] = tst(j[aj >= 2022]); m["t_controle"] = tst(j[aj <= 2021])
        raison = None if m["t_0dte"] >= 2 else f"t {m['t_0dte']:.2f} sur 2022 - 2026 (contrôle 2014 - 2021 : {m['t_controle']:.2f})"
        TESTS[k] = (m["t_0dte"], int((aj >= 2022).sum()))
    else:
        raison = regles(m, None) or (None if m["grilles"] <= base["zone"][2]["grilles"] else f"{m['grilles']} comptes grillés, plus que le Bot 3 en 1")
        TESTS[k] = (m["t"], n)
    resultats[k] = dict(nom=nom, raison=raison, trades=len(tr), **m)
    ligne(k, nom, r[B.test], "#e6e05a", m, "tué" if raison else "en cours", raison or "")
    DX.dire(f"{nom} : {len(tr):,} trades, {m['par_seance']:+.1f} $ par séance, t {m['t']:.2f}".replace(",", " ")
            + (f" (2022 - 2026 : {m['t_0dte']:.2f}, 2014 - 2021 : {m['t_controle']:.2f})" if k == "C2" else "") + (f" → tuée ({raison})." if raison else " → passe ses règles."), "b" if raison else "h")
DX.maj(force=True, progression=0.45, phase="Étape 3 : piste D (autres marchés)")

# ------------------------------------------------------------------ D. le Supertrend sur 7 marches
jours_d, series = None, {}
for nom in ("NQ", "ES", "RTY", "YM", "GC", "CL", "6E"):
    DX.dire(f"D : je reconstruis le Supertrend sur {nom} (minutes 2016 - 2026) et je le rejoue.", "c")
    M = MK.seances(nom); tr = MK.trades(M); r, d = MK.journees(M, tr)
    sel = M["ok"] & (M["J"] >= "2016-01-01")
    series[nom] = pd.DataFrame(dict(r=r[sel], d=d[sel]), index=pd.to_datetime(M["J"][sel]))
    v = r[sel]; a = pd.to_datetime(M["J"][sel]).year
    m = dict(par_seance=float(v.mean()), t=tst(v), t_1619=tst(v[a <= 2019]), t_2022=tst(v[(a >= 2020) & (a <= 2022)]), t_2326=tst(v[a >= 2023]), trades=len(tr))
    TESTS[f"D-{nom}"] = (m["t"], len(v)); resultats[f"D-{nom}"] = dict(nom=f"D · Supertrend {nom}", **m)
    jr = series[nom]["r"].reindex(pd.to_datetime([B.J[x] for x in B.test])).fillna(0.0).to_numpy()
    ligne(f"D-{nom}", f"D · Supertrend {nom}", jr, "#ff8f5a", m, "en cours")
    DX.dire(f"D · Supertrend {nom} : {m['par_seance']:+.1f} $ par séance (1 micro), t {m['t']:.2f} (2016-19 {m['t_1619']:.2f}, 2020-22 {m['t_2022']:.2f}, 2023-26 {m['t_2326']:.2f}).",
            "h" if m["t"] > 2 else "g")
tab = pd.concat({k: v["r"] for k, v in series.items()}, axis=1)
ecart = tab.rolling(60, min_periods=40).std().shift(1)
norm = (tab / ecart).mean(axis=1, skipna=True).dropna()
nq = tab["NQ"].reindex(norm.index)
port = norm * nq.std()                                                   # ramene au risque du NQ seul
a = port.index.year
mD = dict(t=tst(port.to_numpy()), t_1619=tst(port[a <= 2019].to_numpy()), t_2022=tst(port[(a >= 2020) & (a <= 2022)].to_numpy()),
          t_2326=tst(port[a >= 2023].to_numpy()), sharpe=float(port.mean() / port.std() * np.sqrt(252)), sharpe_nq=float(nq.mean() / nq.std() * np.sqrt(252)))
raisonD = None if (mD["t"] >= 3 and mD["t_1619"] > 0 and mD["t_2022"] > 0 and mD["t_2326"] > 0 and mD["sharpe"] > mD["sharpe_nq"]) else "conditions du portefeuille non remplies"
TESTS["D"] = (mD["t"], len(port)); resultats["D"] = dict(nom="D · portefeuille Supertrend 7 marchés", raison=raisonD, **mD)
DX.dire(f"D · portefeuille des 7 Supertrend (même risque chacun) : t {mD['t']:.2f}, Sharpe {mD['sharpe']:.2f} contre {mD['sharpe_nq']:.2f} pour le NQ seul → "
        + ("passe ses règles." if not raisonD else f"tué ({raisonD})."), "h" if not raisonD else "b")
DX.maj(force=True, progression=0.6, phase="Étape 3 : correction des tests multiples")

# ------------------------------------------------------------------ correction des tests multiples (13 tests)
cles = list(TESTS); pv = np.array([1 - stats.t.cdf(t, max(2, nn) - 1) for t, nn in TESTS.values()]); o = np.argsort(pv)
ok = pv[o] <= 0.05 * np.arange(1, len(pv) + 1) / len(pv); kk = np.nonzero(ok)[0].max() + 1 if ok.any() else 0
bh = set(cles[i] for i in o[:kk])
for k in cles:
    rr = resultats.get(k)
    if rr is None:
        continue
    rr["p"] = float(pv[cles.index(k)]); rr["bh"] = k in bh
    if k.startswith("D-"):
        rr["retenu"] = False                                         # un marche seul n'est pas une piste ; le portefeuille l'est
    else:
        rr["retenu"] = bool(k in bh and not rr.get("raison"))
    for L in DX.e["lignes"]:
        if L["id"] == k:
            L["statut"] = "retenu" if rr["retenu"] else ("tué" if not k.startswith("D-") or not rr["bh"] else L["statut"])
            if not rr["retenu"] and not L["raison"]:
                L["raison"] = "ne survit pas à la correction des tests multiples" if not rr["bh"] else (rr.get("raison") or "")
DX.dire("Correction des tests multiples faite : " + ", ".join(k for k in cles if resultats.get(k, {}).get("retenu")) + " retenue(s)." if any(r.get("retenu") for r in resultats.values())
        else "Correction des tests multiples faite : aucune piste B, C ou D n'est retenue.", "a")
DX.maj(relief=True, force=True, progression=0.65, phase="Étape 3 : piste A (gestion du capital)")


# ------------------------------------------------------------------ A. gestion du capital
@nb.njit(cache=True)
def vie_echelle(R, Dp, s2, s3, coussin, tous, i0, i1):
    """R, Dp : (3, n) resultats et creux a 1, 2, 3 MNQ. Taille du jour selon la marge (solde - plancher) en debut de seance."""
    solde = 50000.0; haut = 50000.0; base_ = 50000.0; meilleur = 0.0; depuis = 0; retire = 0.0; grilles = 0
    for i in range(i0, i1):
        plancher = min(haut - 2500.0, 50100.0); marge = solde - plancher
        t = 0
        if marge >= s3:
            t = 2
        elif marge >= s2:
            t = 1
        if solde + Dp[t, i] <= plancher:
            grilles += 1; solde = 50000.0; haut = 50000.0; base_ = 50000.0; meilleur = 0.0; depuis = 0
            continue
        solde += R[t, i]; depuis += 1
        if R[t, i] > meilleur:
            meilleur = R[t, i]
        if solde > haut:
            haut = solde
        niveau = 50000.0 + coussin
        if depuis >= tous and solde > niveau and solde - base_ > 0 and meilleur <= 0.4 * (solde - base_):
            retire += solde - niveau; solde = niveau; base_ = niveau; meilleur = 0.0; depuis = 0
    return retire, grilles


ECH = {"fixe 1 MNQ": (1e12, 1e12), "E1 (2 MNQ dès 3 500 $, 3 dès 5 000 $)": (3500.0, 5000.0), "E2 (2 dès 4 000 $, 3 dès 6 000 $)": (4000.0, 6000.0), "E3 (2 dès 5 000 $, jamais plus)": (5000.0, 1e12)}
NOMS_BOT = {"zone": "Bot 3 en 1", "xgb": "XGBoost", "xgbs": "XGBoost stop 1,5 ATR", "st": "Supertrend"}
RD = {}
for b0, tr in base_tr.items():
    Rr = np.zeros((3, n)); Dd = np.zeros((3, n))
    for t in (1, 2, 3):
        r, d, _ = journees(tr, min(400.0 * t, 1100.0), t); Rr[t - 1] = r[B.test]; Dd[t - 1] = d[B.test]
    RD[b0] = (Rr, Dd)
pols = [(b0, e, k) for b0 in base_tr for e in ECH for k in (2600.0, 4000.0, 6000.0)]
tabA = {}
for b0, e, k in pols:
    ret_, gr = vie_echelle(RD[b0][0], RD[b0][1], ECH[e][0], ECH[e][1], k, 20, 0, n)
    tabA[(b0, e, k)] = dict(retire_an=ret_ / (n / 252), grilles=int(gr))
ref_cle = ("zone", "fixe 1 MNQ", 2600.0)
DX.dire(f"A : 48 politiques rejouées sur 2014 - 2026. Référence (Bot 3 en 1, 1 MNQ, coussin 2 600 $) : {tabA[ref_cle]['retire_an']:,.0f} $ par an, {tabA[ref_cle]['grilles']} comptes grillés.".replace(",", " "), "c")
# marche avant : chaque annee, la politique qui a le plus retire sans griller plus que la reference sur les annees d'avant
solde_choix = {}
jA = []                                                                    # politique choisie par annee
for Y in range(2017, 2027):
    fin = int(np.argmax(aj >= Y))
    rref, gref = vie_echelle(RD["zone"][0], RD["zone"][1], 1e12, 1e12, 2600.0, 20, 0, fin)
    meil, mret = ref_cle, -1.0
    for b0, e, k in pols:
        r_, g_ = vie_echelle(RD[b0][0], RD[b0][1], ECH[e][0], ECH[e][1], k, 20, 0, fin)
        if g_ <= gref and r_ > mret:
            meil, mret = (b0, e, k), r_
    jA.append((Y, meil))
    DX.dire(f"A · {Y} : choisie sur 2014 - {Y - 1} → {NOMS_BOT[meil[0]]}, {meil[1]}, coussin {meil[2]:,.0f} $.".replace(",", " "), "c")


@nb.njit(cache=True)
def vie_suite(R, Dp, s2, s3, coussin, etat):
    """Une annee de vie avec une politique ; etat = [solde, haut, base, meilleur, depuis, retire, grilles] (modifie)."""
    solde, haut, base_, meilleur, depuis, retire, grilles = etat[0], etat[1], etat[2], etat[3], etat[4], etat[5], etat[6]
    for i in range(R.shape[1]):
        plancher = min(haut - 2500.0, 50100.0); marge = solde - plancher
        t = 2 if marge >= s3 else (1 if marge >= s2 else 0)
        if solde + Dp[t, i] <= plancher:
            grilles += 1; solde = 50000.0; haut = 50000.0; base_ = 50000.0; meilleur = 0.0; depuis = 0
            continue
        solde += R[t, i]; depuis += 1
        if R[t, i] > meilleur:
            meilleur = R[t, i]
        if solde > haut:
            haut = solde
        niveau = 50000.0 + coussin
        if depuis >= 20 and solde > niveau and solde - base_ > 0 and meilleur <= 0.4 * (solde - base_):
            retire += solde - niveau; solde = niveau; base_ = niveau; meilleur = 0.0; depuis = 0
    etat[0], etat[1], etat[2], etat[3], etat[4], etat[5], etat[6] = solde, haut, base_, meilleur, depuis, retire, grilles


etatA = np.array([50000.0, 50000.0, 50000.0, 0.0, 0.0, 0.0, 0.0]); etatR = etatA.copy()
for Y, (b0, e, k) in jA:
    sel = np.nonzero(aj == Y)[0]
    vie_suite(RD[b0][0][:, sel], RD[b0][1][:, sel], ECH[e][0], ECH[e][1], k, etatA)
    vie_suite(RD["zone"][0][:, sel], RD["zone"][1][:, sel], 1e12, 1e12, 2600.0, etatR)
ans17 = (n - d17) / 252
mA = dict(retire_an=etatA[5] / ans17, grilles=int(etatA[6])); mR = dict(retire_an=etatR[5] / ans17, grilles=int(etatR[6]))
adopteA = mA["retire_an"] > mR["retire_an"] and mA["grilles"] <= mR["grilles"]
resultats["A"] = dict(nom="A · gestion du capital (marche avant)", choix={Y: f"{NOMS_BOT[c[0]]}, {c[1]}, coussin {c[2]:.0f} $" for Y, c in jA}, **mA, reference=mR,
                      adoptee=bool(adopteA), politiques={f"{NOMS_BOT[b]} | {e} | {k:.0f}": v for (b, e, k), v in tabA.items()})
L = DX.ligne("A", "A · gestion du capital (marche avant)", "retenu" if adopteA else "tué", "#ffffff")
L["stats"] = dict(retire_an=mA["retire_an"], grilles=mA["grilles"]); L["raison"] = "" if adopteA else "ne bat pas le Bot 3 en 1 en 1 MNQ hors échantillon"
L["tri"] = 3 if adopteA else -3
DX.dire(f"A · hors échantillon 2017 - 2026 : {mA['retire_an']:,.0f} $ retirés par an, {mA['grilles']} comptes grillés ; Bot 3 en 1 en 1 MNQ : {mR['retire_an']:,.0f} $ et {mR['grilles']} → "
        f"{'ADOPTÉE' if adopteA else 'pas mieux'}.".replace(",", " "), "h" if adopteA else "b")
json.dump(dict(resultats=resultats, tests={k: dict(t=v[0], n=v[1]) for k, v in TESTS.items()}), open(os.path.join(DOSSIER, "etape3.json"), "w"), default=str)
DX.maj(relief=True, force=True, progression=1.0, phase="Étape 3 terminée", detail="quatre pistes testées", fini=True)
DX.dire("Étape 3 terminée.", "a")
