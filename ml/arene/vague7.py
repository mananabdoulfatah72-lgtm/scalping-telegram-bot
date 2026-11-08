#!/usr/bin/env python3
"""Arene, vague 7 (ml/arene/VAGUE7.md, regles fixees avant calcul) : le modele de tri sert a regler la taille de Z12.
S1 Z12 + 1 MNQ de plus sur les trades gardes ; S2 M3 en 2 MNQ ; S3 M3 en 1 MNQ puis 2 MNQ des 3 500 $ de marge.
MINUTES_NQ=... CACHE_DOSSIER=... python3 vague7.py <dossier de l'arene>"""
import json
import os
import sys
import time

import numpy as np
from scipy import stats

import bots as BT
import w1 as W
from direct import Direct

DOSSIER = sys.argv[1]
B = BT.Base(os.environ["CACHE_DOSSIER"])
aj = B.an[B.test]; n = len(B.test); jours = [B.J[s] for s in B.test]; FEN = aj >= 2017; d17 = int(np.argmax(FEN)); PAS = 5
PER = np.array([x >= "2026-08-11" for x in jours])
DX = Direct(DOSSIER)
DX.maj(force=True, phase="Vague 7 : le modèle règle la taille de Z12", detail="préparation", progression=0.0, fini=False, jours=jours[::PAS], curseur=0, pied=[
    ("vague 7", "S1 Z12 + 1 MNQ sur les trades jugés bons ; S2 ces trades seuls en 2 MNQ ; S3 en 1 MNQ puis 2 MNQ dès 3 500 $ de marge (ml/arene/VAGUE7.md)"),
    ("retenu si", "survie 60 j ≥ 95 %, ≤ 20 % de comptes neufs grillés en 1 an, ≤ 0,15 master grillé par an, net ≥ 1,3 × Z12, 1re année ≥ Z12"),
    ("compte", "Master 50K Option 2, limite du bot 400 $ par MNQ, 3 $ de frais par MNQ, vie réelle"),
    ("période", f"mesure 2017 - 2026 ({int(FEN.sum())} séances)")])
DX.dire("Vague 7 : au lieu de jeter les trades de Z12 que le modèle juge moins bons, je les garde en 1 MNQ et je double les bons.", "a")


def jours_de(tr, taille=1, ensemble=False, frais=3.0):
    lim = 400.0 * taille if not ensemble else 800.0
    r, dp, ntr = BT.journees_ensemble(B, tr, lim, frais) if ensemble else BT.journees(B, tr, taille, lim, frais)
    return r[B.test], dp[B.test], ntr[B.test] > 0


def edge(j, j6):
    jw = j[FEN]; a = aj[FEN]
    return dict(t=BT.tst(jw), t_avant=BT.tst(jw[a <= 2022]), t_apres=BT.tst(jw[a >= 2023]), t_frais6=BT.tst(j6[FEN]),
                annees_pos=int(sum(jw[a == yy].sum() > 0 for yy in range(2017, 2027))), par_seance=float(jw.mean()))


def trier(tr, nom):
    tr = sorted(tr, key=lambda t: (t[0], t[2]))
    X, y, an = W.variables_prod(B, tr)
    DX.dire(f"{nom} : {len(tr):,} signaux, j'apprends année par année (2017 → 2026) avec 10 graines.".replace(",", " "), "c")
    p = W.probas(X, y, an); garde, g = W.tri(tr, p, y, an)
    DX.dire(f"{nom} : le modèle garde {g[an >= 2017].mean():.0%} des signaux de 2017 - 2026.", "c")
    return garde


def parcours(R0, D0, T0, R1, D1, T1, seuil, garde, i0, i1):
    """Un compte Master neuf en i0, joue jusqu'a i1 : Z12 seul (0) ou Z12 + W1 (1) selon la marge de la veille ; requalification
    en Z12 seul. Renvoie retire, frais, masters grilles, 1re seance grillee, 1er retrait, seances tradees, journal du resultat."""
    phase = 1; solde = haut = base_ = 50000.0; meil = 0.0; jr = 0; nret = 0; ret = fr = 0.0; g = 0; dq = 0
    prem_g = prem_r = -1; actives = 0; journal = np.zeros(i1 - i0)
    for i in range(i0, i1):
        pl = min(haut - 2500, 50100); mode = 1 if (phase == 1 and solde - pl >= seuil) else 0
        R, Dp, T = (R1, D1, T1) if mode else (R0, D0, T0)
        if phase == 0:
            if dq % 20 == 0: fr += 100
            dq += 1
        actives += T[i]
        if solde + Dp[i] <= pl:
            if phase == 1:
                g += 1
                if prem_g < 0: prem_g = i - i0
            journal[i - i0] = pl - solde
            phase = 0; dq = 0; solde = haut = base_ = 50000.0; meil = 0.0; jr = 0; continue
        solde += R[i]; haut = max(haut, solde); journal[i - i0] = R[i]
        if phase == 0:
            if solde >= 53000: fr += 148; phase = 1; solde = haut = base_ = 50000.0; meil = 0.0; jr = 0; nret = 0
            continue
        jr += T[i]; meil = max(meil, R[i]); dispo = solde - (50000 + garde)
        if nret < 3: dispo = min(dispo, 1500)
        if jr >= 10 and dispo >= 1000 and solde - base_ > 0 and meil <= 0.4 * (solde - base_):
            ret += dispo; solde -= dispo; base_ = solde; meil = 0.0; jr = 0; nret += 1
            if prem_r < 0: prem_r = i - i0
    return ret, fr, g, prem_g, prem_r, actives, journal


def politique(Z, M, seuil, garde):
    starts = range(d17, n - 252, 20); acc = np.zeros(3); ans = 0.0; act = 0; tot = 0; g60 = []; g250 = []; prem = []; net1 = []
    for i0 in starts:
        r, f, g, pg, pr, a, _ = parcours(*Z, *M, seuil, garde, i0, n)
        acc += (r, f, g); ans += (n - i0) / 252; act += a; tot += n - i0
        g60.append(0 <= pg < 60); g250.append(0 <= pg < 250)
        if pr >= 0: prem.append(pr)
        r1, f1, *_ = parcours(*Z, *M, seuil, garde, i0, min(n, i0 + 250)); net1.append(r1 - f1)
    j = parcours(*Z, *M, seuil, garde, d17, n)[6]
    return np.r_[np.zeros(d17), j], dict(net_an=float((acc[0] - acc[1]) / ans), grilles_an=float(acc[2] / ans), survie_60=float(1 - np.mean(g60)),
                                         grille_250=float(np.mean(g250)), seances_tradees=float(act / tot), net_1an=float(np.mean(net1)),
                                         premier_retrait=float(np.median(prem)) if prem else None,
                                         periode=float(parcours(*Z, *M, seuil, garde, int(np.argmax(PER)), n)[6].sum()))




def ligne(ident, nom, j, coul, m, statut, raison=""):
    Lg = DX.ligne(ident, nom, statut, coul)
    Lg["courbe"] = [round(float(v), 1) for v in np.cumsum(j)[::PAS]]; Lg["stats"] = m; Lg["raison"] = raison
    Lg["tri"] = (2 if statut == "retenu" else -2 if statut == "tué" else 0) + (m.get("survie_60") or 0) - (m.get("grilles_an") or 0)
    DX.maj(relief=True, curseur=len(Lg["courbe"]) - 1)


def resume(nom, m):
    return (f"{nom} (2017 - 2026) : t {m['t']:.2f} (depuis 2023 : {m['t_apres']:.2f}), {m['seances_tradees']:.0%} des séances ; compte : survie {m['survie_60']:.0%}, "
            f"grillé en 1 an {m['grille_250']:.0%}, {m['grilles_an']:.2f} masters grillés par an, net {m['net_an']:,.0f} $ par an, "
            f"1re année {m['net_1an']:,.0f} $, 1er retrait après {m['premier_retrait'] or 0:.0f} séances (médiane)").replace(",", " ")


INV = W.ecart_vix(B) >= 0
Z12 = sorted([t for t in BT.zone(B) if not INV[t[0]]], key=lambda t: (t[0], t[2]))
DX.maj(force=True, progression=0.05, phase="Vague 7 : tri des trades de Z12 (marche en avant)", detail="10 graines, 2017 - 2026")
M3 = trier(Z12, "Z12")
Zj = jours_de(Z12)
cj, ref = politique(Zj, Zj, 1e12, 2600.0); ref.update(edge(Zj[0], jours_de(Z12, frais=6.0)[0]))
ligne("Z12", "Z12 · Bot 3 en 1 sans VIX inversé, 1 MNQ (référence)", Zj[0], "#5ad1c8", ref, "référence"); DX.dire(resume("Z12 (1 MNQ)", ref), "c")
M3_1, M3_2 = jours_de(M3, 1), jours_de(M3, 2)
TESTS = (("S1", "S1 · Z12, 2 MNQ sur les trades jugés bons", jours_de(Z12 + M3, ensemble=True), None, 1e12, jours_de(Z12 + M3, ensemble=True, frais=6.0)[0], "#ffffff"),
         ("S2", "S2 · trades jugés bons seulement, en 2 MNQ", M3_2, None, 1e12, jours_de(M3, 2, frais=6.0)[0], "#f9c74f"),
         ("S3", "S3 · trades jugés bons, 1 puis 2 MNQ dès 3 500 $ de marge", M3_1, M3_2, 3500.0, None, "#90e0ef"))
RES = {}
for k, (ident, nom, Za, Ma, seuil, j6, coul) in enumerate(TESTS):
    DX.maj(force=True, progression=0.4 + 0.18 * k, phase=f"Vague 7 : {nom}", detail="vie réelle du compte")
    j, m = politique(Za, Ma or Za, seuil, 2600.0)
    if j6 is None:                                    # S3 : chemin du compte avec 6 $ de frais par MNQ
        j6 = politique(jours_de(M3, 1, frais=6.0), jours_de(M3, 2, frais=6.0), seuil, 2600.0)[0]
    m.update(edge(Za[0] if Ma is None else j, j6))
    raisons = []
    if m["t"] < 2: raisons.append(f"t {m['t']:.2f} sous 2")
    if m["t_avant"] <= 0 or m["t_apres"] <= 0: raisons.append("négatif sur 2017-2022 ou sur 2023-2026")
    if m["t_frais6"] < 1.5: raisons.append(f"avec 6 $ de frais t {m['t_frais6']:.2f}")
    if m["annees_pos"] < 7: raisons.append(f"{m['annees_pos']} années positives sur 10")
    if m["survie_60"] < 0.95: raisons.append(f"survie {m['survie_60']:.0%} sous 95 %")
    if m["grille_250"] > 0.20: raisons.append(f"{m['grille_250']:.0%} de comptes neufs grillés dans l'année (au plus 20 %)")
    if m["grilles_an"] > 0.15: raisons.append(f"{m['grilles_an']:.2f} masters grillés par an (au plus 0,15)")
    if m["net_an"] < 1.3 * ref["net_an"]: raisons.append(f"net {m['net_an']:,.0f} $ par an, il faut {1.3 * ref['net_an']:,.0f} $".replace(",", " "))
    if m["net_1an"] < ref["net_1an"]: raisons.append(f"1re année {m['net_1an']:,.0f} $, moins que Z12 ({ref['net_1an']:,.0f} $)".replace(",", " "))
    RES[ident] = dict(nom=nom, raisons=raisons, **m)
    ligne(ident, nom, j[-n:] if len(j) >= n else j, coul, m, "tué" if raisons else "en cours", "; ".join(raisons))
    DX.dire(resume(nom, m) + (f" → tué ({'; '.join(raisons)})." if raisons else " → passe ses règles, en attente de la correction des tests multiples."), "b" if raisons else "h")
    time.sleep(0.2)
cles = list(RES); pv = np.array([1 - stats.norm.cdf(RES[c]["t"]) for c in cles]); o = np.argsort(pv)
okk = pv[o] <= 0.05 * np.arange(1, len(pv) + 1) / len(pv); kk = (np.nonzero(okk)[0].max() + 1) if okk.any() else 0
bh = {cles[i] for i in o[:kk]}
for c in cles:
    RES[c]["p"] = float(pv[cles.index(c)]); RES[c]["bh"] = c in bh
    if c not in bh: RES[c]["raisons"].append("ne survit pas à Benjamini-Hochberg")
    RES[c]["retenu"] = not RES[c]["raisons"]
    for Lg in DX.e["lignes"]:
        if Lg["id"] == c:
            Lg["statut"] = "retenu" if RES[c]["retenu"] else "tué"; Lg["raison"] = "; ".join(RES[c]["raisons"])
g_ = [c for c in cles if RES[c]["retenu"]]
DX.dire("Vague 7 : " + (", ".join(g_) + " retenu(s)." if g_ else "rien ne passe toutes ses règles."), "a")
json.dump(dict(reference=ref, tests=RES), open(os.path.join(DOSSIER, "vague7.json"), "w"), default=float)
DX.maj(relief=True, force=True, progression=1.0, phase="Vague 7 terminée", detail="3 tests", fini=True)
DX.dire("Vague 7 terminée.", "a")
