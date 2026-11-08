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
DX.e["lignes"] = [l for l in etat["lignes"] if l.get("statut") == "référence" and "-" not in l["id"] or l["id"].startswith("usine")]
rel = json.load(open(os.path.join(DOSSIER, "relief.json")))
for l in DX.e["lignes"]:
    l["courbe"] = rel["courbes"].get(l["id"], [])
DX.e["version"] = etat["version"] + 1; DX.e["version_relief"] = etat["version_relief"] + 1
DX.maj(relief=True, force=True, phase="Étape 3 : quatre nouvelles pistes", detail="préparation", progression=0.0, fini=False)
DX.dire("Étape 3 : je lance les quatre pistes choisies ensemble (règles : ml/arene/PISTES.md).", "a")
B = BT.Base(os.environ["CACHE_DOSSIER"])
X = B.X; F = X["F"]; aj = B.an[B.test]; n = len(B.test); PAS = 5
VOL = B.V
tst = BT.tst
TESTS = {}                                                              # famille corrigee ensemble (BH)


def ligne(ident, nom, j, coul, stats_, statut="en cours", raison=""):
    L = DX.ligne(ident, nom, statut, coul)
    L["courbe"] = [round(float(x), 1) for x in np.cumsum(j)[::PAS]]; L["stats"] = stats_; L["raison"] = raison
    L["tri"] = (2 if statut == "retenu" else -2 if statut == "tué" else 0) + (stats_.get("survie_60") or 0) - (stats_.get("grilles_an") or 0)
    DX.maj(relief=True, curseur=len(L["courbe"]) - 1)
    return L


def journees(tr, lim=400.0, taille=1, frais=3.0):
    return BT.journees(B, tr, taille, lim, frais)


def profil(tr, lim=400.0):
    r, d, ntr = journees(tr, lim); r6, _, _ = journees(tr, lim, 1, 6.0)
    m = BT.mesures(B, r, d, ntr); m["t_frais6"] = tst(r6[B.test])
    return r, d, m, ntr


def regles(m, ref):
    if m["t"] < 2.0: return "t sous 2"
    if m["t_avant"] <= 0 or m["t_apres"] <= 0: return "négative sur une des deux moitiés"
    if m["t_frais6"] < 1.5: return "ne tient pas avec 6 $ de frais"
    if m["annees_pos"] < 9: return f"{m['annees_pos']} années positives sur 13"
    if ref is not None:
        if m["survie_60"] < ref["survie_60"] - 1e-9: return f"survie {m['survie_60']:.0%} sous celle de son bot ({ref['survie_60']:.0%})"
        if m["grilles_an"] > ref["grilles_an"] + 1e-9: return f"{m['grilles_an']:.2f} masters grillés par an, plus que son bot ({ref['grilles_an']:.2f})"
        if m["pire_baisse"] < 1.25 * ref["pire_baisse"]: return "pire baisse trop profonde"
    return None


base_tr = {"zone": BT.zone(B), "xgb": BT.xgboost(B), "st": BT.supertrend(B)}
base_tr["xgbs"] = BT.appliquer_stop(B, base_tr["xgb"], 1.5)
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
    r, d, m, _ = profil(tr); raison = regles(m, base[b0][2])
    TESTS[k] = (m["t"], n); resultats[k] = dict(nom=nom, raison=raison, **m)
    ligne(k, nom, r[B.test], "#2fd16f", m, "tué" if raison else "en cours", raison or "")
    DX.dire(f"{nom} : {m['par_seance']:+.1f} $ par séance, t {m['t']:.2f}, net {m['net_an']:,.0f} $ par an, {m['grilles_an']:.2f} masters grillés par an, survie {m['survie_60']:.0%} → ".replace(",", " ")
            + (f"tuée ({raison})" if raison else "passe ses règles, en attente de la correction des tests multiples"), "b" if raison else "h")

# B4 : choix du bot selon le regime (volatilite x tendance), appris chaque annee sur le passe
Cj = B.C[:, 389]; ret = np.r_[np.nan, Cj[1:] / Cj[:-1] - 1]
sr = pd.Series(ret); vol = sr.rolling(20).std().shift(1); tend = (sr.rolling(20).sum().shift(1)).abs() / (vol * np.sqrt(20))
rv = vol.rolling(252, min_periods=126).rank(pct=True).to_numpy(); rt = tend.rolling(252, min_periods=126).rank(pct=True).to_numpy()
cv_ = np.floor(np.nan_to_num(rv) * 3).clip(0, 2); ct_ = np.floor(np.nan_to_num(rt) * 3).clip(0, 2)
case = np.where(np.isfinite(rv) & np.isfinite(rt), cv_ * 3 + ct_, -1)[B.test].astype(int)
jb = {k: base[k][0][B.test] for k in ("zone", "xgb", "st")}; db = {k: base[k][1][B.test] for k in ("zone", "xgb", "st")}
tb = {k: base[k][3][B.test] > 0 for k in ("zone", "xgb", "st")}
j4 = np.zeros(n); d4 = np.zeros(n); t4 = np.zeros(n, bool); choix4 = {}
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
            j4[q] = jb[meil][q]; d4[q] = db[meil][q]; t4[q] = tb[meil][q]
DX.dire("B4 : chaque année de 2017 à 2026, pour chacun des 9 régimes, j'ai choisi le bot sur les années d'avant seulement.", "c")
d17 = int(np.argmax(aj >= 2017))


def bilan17(j, d, tr):
    jj, dd = j[d17:], d[d17:]
    v = BT.vie(np.vstack([j, j, j]), np.vstack([d, d, d]), tr, debut=d17)
    g60 = BT.grilles_depuis(jj, dd, 60)
    a = aj[d17:]
    return dict(par_seance=float(jj.mean()), t=tst(jj), t_avant=tst(jj[a <= 2022]), t_apres=tst(jj[a >= 2023]), survie_60=float(1 - g60.mean()), **v)


m4 = bilan17(j4, d4, t4); refs4 = {k: bilan17(jb[k], db[k], tb[k]) for k in jb}
meilleur = max(refs4, key=lambda k: (refs4[k]["survie_60"], refs4[k]["net_an"]))
raison4 = None if (m4["t"] >= 2 and m4["t_avant"] > 0 and m4["t_apres"] > 0 and m4["survie_60"] >= refs4[meilleur]["survie_60"] and m4["grilles_an"] <= refs4[meilleur]["grilles_an"] + 1e-9) else \
    f"ne bat pas le meilleur bot seul ({ {'zone': 'Bot 3 en 1', 'xgb': 'XGBoost', 'st': 'Supertrend'}[meilleur] }) sur 2017 - 2026"
TESTS["B4"] = (m4["t"], n - d17); resultats["B4"] = dict(nom="B4 · bot choisi selon le régime", raison=raison4, **m4, reference=refs4[meilleur])
ligne("B4", "B4 · bot choisi selon le régime", np.r_[np.zeros(d17), j4[d17:]], "#2fd16f", m4, "tué" if raison4 else "en cours", raison4 or "")
DX.dire(f"B4 : net {m4['net_an']:,.0f} $ par an, {m4['grilles_an']:.2f} masters grillés par an, survie {m4['survie_60']:.0%} (meilleur bot seul : "
        f"{refs4[meilleur]['net_an']:,.0f} $, {refs4[meilleur]['grilles_an']:.2f}, {refs4[meilleur]['survie_60']:.0%}) → {'tuée : ' + raison4 if raison4 else 'passe'}.".replace(",", " "), "b" if raison4 else "h")
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
                    out.append((s, pos, m0, m0, m, e, O[m + 1]))
                pos, m0, e = cible, m + 1, O[m + 1]
        if pos:
            out.append((s, pos, m0, m0, 388, e, O[389]))
    return out


def fin_de_seance():
    out = []
    for s in B.test:
        if s == 0:
            continue
        r = B.C[s, 359] / B.C[s - 1, 389] - 1
        if r != 0:
            out.append((s, -int(np.sign(r)), 360, 360, 388, B.O[s, 360], B.O[s, 389]))
    return out


for k, nom, f in (("C1", "C1 · la VWAP en tendance (Zarattini et Aziz)", vwap_tendance), ("C2", "C2 · retournement de fin de séance (époque 0DTE)", fin_de_seance)):
    tr = f(); r, d, m, _ = profil(tr, 400.0)
    if k == "C2":
        j = r[B.test]; m["t_0dte"] = tst(j[aj >= 2022]); m["t_controle"] = tst(j[aj <= 2021])
        raison = None if m["t_0dte"] >= 2 else f"t {m['t_0dte']:.2f} sur 2022 - 2026 (contrôle 2014 - 2021 : {m['t_controle']:.2f})"
        TESTS[k] = (m["t_0dte"], int((aj >= 2022).sum()))
    else:
        raison = regles(m, None) or (None if m["grilles_an"] <= base["zone"][2]["grilles_an"] + 1e-9 else f"{m['grilles_an']:.2f} masters grillés par an, plus que le Bot 3 en 1")
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
ECH = {"fixe 1 MNQ": (1e12, 1e12), "E1 (2 MNQ dès 3 500 $ de marge, 3 dès 5 000 $)": (3500.0, 5000.0),
       "E2 (2 dès 4 000 $, 3 dès 6 000 $)": (4000.0, 6000.0), "E3 (2 dès 5 000 $, jamais plus)": (5000.0, 1e12)}
NOMS_BOT = {"zone": "Bot 3 en 1", "xgb": "XGBoost", "xgbs": "XGBoost stop 1,5 ATR", "st": "Supertrend"}
ORDRE = list(base_tr)
RD = np.zeros((len(ORDRE), 3, n)); DD = np.zeros((len(ORDRE), 3, n)); TR = np.zeros((len(ORDRE), n), np.bool_)
for bi, b0 in enumerate(ORDRE):
    for t in (1, 2, 3):
        r, d, ntr = journees(base_tr[b0], min(400.0 * t, 1100.0), t); RD[bi, t - 1] = r[B.test]; DD[bi, t - 1] = d[B.test]
        if t == 1:
            TR[bi] = ntr[B.test] > 0
pols = [(b0, e, k) for b0 in ORDRE for e in ECH for k in (2600.0, 4000.0, 6000.0)]


def vie_pol(b0, e, k, debut=0, fin=None):
    bi = ORDRE.index(b0)
    return BT.vie(RD[bi], DD[bi], TR[bi], debut, fin, ECH[e][0], ECH[e][1], k)


tabA = {p_: vie_pol(*p_) for p_ in pols}
ref_cle = ("zone", "fixe 1 MNQ", 2600.0)
DX.dire(f"A : {len(pols)} politiques rejouées sur 2014 - 2026 (vie réelle moyennée). Référence (Bot 3 en 1, 1 MNQ) : net {tabA[ref_cle]['net_an']:,.0f} $ par an, "
        f"{tabA[ref_cle]['grilles_an']:.2f} masters grillés par an.".replace(",", " "), "c")


@nb.njit(cache=True)
def _vie_pol(RDa, DDa, TRa, bot_i, s2_i, s3_i, garde_i, i0, i1, frais_mois, activation):
    """Vie reelle ou la politique (bot, echelle, coussin) change chaque annee selon le choix fait sur le passe."""
    phase = 1; solde = 50000.0; haut = 50000.0; base_ = 50000.0; meilleur = 0.0; jours = 0; nret = 0
    retire = 0.0; frais = 0.0; grilles = 0; duree_q = 0
    for i in range(i0, i1):
        b = bot_i[i]; plancher = min(haut - 2500.0, 50100.0); t = 0
        if phase == 1:
            marge = solde - plancher
            if marge >= s3_i[i]:
                t = 2
            elif marge >= s2_i[i]:
                t = 1
        else:
            if duree_q % 20 == 0:
                frais += frais_mois
            duree_q += 1
        if solde + DDa[b, t, i] <= plancher:
            if phase == 1:
                grilles += 1
            phase = 0; duree_q = 0; solde = 50000.0; haut = 50000.0; base_ = 50000.0; meilleur = 0.0; jours = 0
            continue
        solde += RDa[b, t, i]
        if solde > haut:
            haut = solde
        if phase == 0:
            if solde >= 53000.0:
                frais += activation; phase = 1; solde = 50000.0; haut = 50000.0; base_ = 50000.0; meilleur = 0.0; jours = 0; nret = 0
            continue
        if TRa[b, i]:
            jours += 1
        if RDa[b, t, i] > meilleur:
            meilleur = RDa[b, t, i]
        dispo = solde - (50000.0 + garde_i[i])
        if nret < 3 and dispo > 1500.0:
            dispo = 1500.0
        if jours >= 10 and dispo >= 1000.0 and solde - base_ > 0 and meilleur <= 0.4 * (solde - base_):
            retire += dispo; solde -= dispo; base_ = solde; meilleur = 0.0; jours = 0; nret += 1
    return retire, frais, grilles


bot_i = np.zeros(n, np.int64); s2_i = np.full(n, 1e12); s3_i = np.full(n, 1e12); garde_i = np.full(n, 2600.0); jA = []
for Y in range(2017, 2027):
    fin = int(np.argmax(aj >= Y)); sel = aj == Y
    ref = vie_pol(*ref_cle, 0, fin)
    meil, mnet = ref_cle, -1e18
    for p_ in pols:
        v = vie_pol(*p_, 0, fin)
        if v["grilles_an"] <= ref["grilles_an"] + 1e-9 and v["net_an"] > mnet:
            meil, mnet = p_, v["net_an"]
    jA.append((Y, meil))
    bot_i[sel] = ORDRE.index(meil[0]); s2_i[sel] = ECH[meil[1]][0]; s3_i[sel] = ECH[meil[1]][1]; garde_i[sel] = meil[2]
    DX.dire(f"A · {Y} : choisie sur 2014 - {Y - 1} → {NOMS_BOT[meil[0]]}, {meil[1]}, coussin {meil[2]:,.0f} $.".replace(",", " "), "c")
acc = np.zeros(3); accR = np.zeros(3); ans_ = 0.0
bi_ref = ORDRE.index("zone")
for i0 in range(d17, n - 252, 20):
    acc += np.array(_vie_pol(RD, DD, TR, bot_i, s2_i, s3_i, garde_i, i0, n, 100.0, 148.0))
    accR += np.array(_vie_pol(RD, DD, TR, np.full(n, bi_ref, np.int64), np.full(n, 1e12), np.full(n, 1e12), np.full(n, 2600.0), i0, n, 100.0, 148.0))
    ans_ += (n - i0) / 252
mA = dict(net_an=(acc[0] - acc[1]) / ans_, grilles_an=acc[2] / ans_); mR = dict(net_an=(accR[0] - accR[1]) / ans_, grilles_an=accR[2] / ans_)
adopteA = mA["net_an"] >= 1.1 * mR["net_an"] and mA["grilles_an"] <= mR["grilles_an"] + 1e-9
resultats["A"] = dict(nom="A · gestion du capital (marche avant)", choix={Y: f"{NOMS_BOT[c[0]]}, {c[1]}, coussin {c[2]:.0f} $" for Y, c in jA}, **mA, reference=mR,
                      adoptee=bool(adopteA), politiques={f"{NOMS_BOT[b]} | {e} | {k:.0f}": v for (b, e, k), v in tabA.items()})
L = DX.ligne("A", "A · gestion du capital (marche avant)", "retenu" if adopteA else "tué", "#ffffff")
L["stats"] = dict(net_an=mA["net_an"], grilles_an=mA["grilles_an"]); L["raison"] = "" if adopteA else "ne bat pas le Bot 3 en 1 en 1 MNQ hors échantillon"
L["tri"] = 3 if adopteA else -3
DX.dire(f"A · hors échantillon 2017 - 2026 : net {mA['net_an']:,.0f} $ par an, {mA['grilles_an']:.2f} masters grillés par an ; Bot 3 en 1 en 1 MNQ : "
        f"{mR['net_an']:,.0f} $ et {mR['grilles_an']:.2f} → {'ADOPTÉE' if adopteA else 'pas mieux'}.".replace(",", " "), "h" if adopteA else "b")
json.dump(dict(resultats=resultats, tests={k: dict(t=v[0], n=v[1]) for k, v in TESTS.items()}), open(os.path.join(DOSSIER, "etape3.json"), "w"), default=str)
DX.maj(relief=True, force=True, progression=1.0, phase="Étape 3 terminée", detail="quatre pistes testées", fini=True)
DX.dire("Étape 3 terminée.", "a")
