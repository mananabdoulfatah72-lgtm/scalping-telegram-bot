#!/usr/bin/env python3
"""Arene, vague 6 (ml/arene/VAGUE6.md, regles fixees avant calcul) : A. tri par apprentissage d'autres signaux (cassure des
5 premieres minutes, XGBoost NQ, Z12) ; B. demarrage prudent du compte (Z12 seul tant que la marge est faible, Z12 + W1
au-dessus). Mesure 2017 - 2026, en direct dans l'arene. MINUTES_NQ=... CACHE_DOSSIER=... python3 vague6.py <dossier>"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy import stats

import bots as BT
import w1 as W
from direct import Direct

DOSSIER = sys.argv[1]
B = BT.Base(os.environ["CACHE_DOSSIER"])
O, H, L, C = B.O, B.H, B.L, B.C
OK = np.nonzero(B.ok)[0]
aj = B.an[B.test]; n = len(B.test); jours = [B.J[s] for s in B.test]; FEN = aj >= 2017; d17 = int(np.argmax(FEN)); PAS = 5
PER = np.array([x >= "2026-08-11" for x in jours])

DX = Direct(DOSSIER)
DX.maj(force=True, phase="Vague 6 : de meilleurs résultats pour le compte financé", detail="préparation", progression=0.0, fini=False,
       jours=jours[::PAS], curseur=0, pied=[
           ("vague 6", "A : tri par apprentissage de la cassure d'ouverture, de XGBoost NQ et de Z12 ; B : Z12 seul au début, Z12 + W1 quand la marge le permet (ml/arene/VAGUE6.md)"),
           ("B retenue si", "survie 60 j ≥ 95 %, ≤ 20 % de comptes neufs grillés en 1 an, ≤ 0,15 master grillé par an, net ≥ 1,3 × Z12, ≥ 50 % des séances tradées"),
           ("compte", "Master 50K Option 2, 1 MNQ par bot, limite 400 $, 3 $ de frais, vie réelle (retraits, constance 40 %, requalification payée)"),
           ("période", f"mesure 2017 - 2026 ({int(FEN.sum())} séances)")])
DX.dire("Vague 6 : je cherche mieux pour le compte financé (trier d'autres signaux ; démarrer prudemment, puis accélérer quand le coussin existe).", "a")


def orb(nm=5):
    out = []
    for s in OK:
        o, c = O[s, 0], C[s, nm - 1]
        if not np.isfinite(o + c) or c == o:
            continue
        sens = 1 if c > o else -1
        e = O[s, nm]; stop = L[s, :nm].min() if sens > 0 else H[s, :nm].max(); risque = (e - stop) * sens
        if risque <= 0:
            continue
        cible = e + sens * 10 * risque; x, fin = C[s, 389], 389
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


def trier(tr, nom):
    tr = sorted(tr, key=lambda t: (t[0], t[2]))
    X, y, an = W.variables_prod(B, tr)
    DX.dire(f"{nom} : {len(tr):,} signaux, j'apprends année par année (2017 → 2026) avec 10 graines.".replace(",", " "), "c")
    p = W.probas(X, y, an); garde, g = W.tri(tr, p, y, an)
    DX.dire(f"{nom} : le modèle garde {g[an >= 2017].mean():.0%} des signaux de 2017 - 2026.", "c")
    return garde


def un_contrat(z12, w1):
    par_s = {}
    for t in z12:
        par_s.setdefault(t[0], []).append(t)
    out = list(z12)
    for t in w1:
        s, sens, m_in, deb, fin, e, x = t; sortie = fin + 1 if fin < 389 else 389
        conflit = next((z for z in par_s.get(s, []) if m_in <= z[4] and z[2] <= sortie), None)
        if conflit is None:
            out.append(t)
        elif m_in <= conflit[2]:
            out.append((s, sens, m_in, deb, conflit[2], e, float(C[s, conflit[2]])))
    return sorted(out, key=lambda t: (t[0], t[3]))


def jours_de(tr, ensemble=False, frais=3.0):
    r, dp, ntr = BT.journees_ensemble(B, tr, 400.0, frais) if ensemble else BT.journees(B, tr, 1, 400.0, frais)
    return r[B.test], dp[B.test], ntr[B.test] > 0


def mesurer(tr, ensemble=False):
    j, dd, tt = jours_de(tr, ensemble); r6 = jours_de(tr, ensemble, 6.0)[0]
    jw, dw = j[FEN], dd[FEN]; cum = np.cumsum(jw); a = aj[FEN]
    vie = BT.vie(np.vstack([j, j, j]), np.vstack([dd, dd, dd]), tt, debut=d17)
    return j, dict(par_seance=float(jw.mean()), t=BT.tst(jw), t_avant=BT.tst(jw[a <= 2022]), t_apres=BT.tst(jw[a >= 2023]), t_frais6=BT.tst(r6[FEN]),
                   annees_pos=int(sum(jw[a == yy].sum() > 0 for yy in range(2017, 2027))), seances_tradees=float(tt[FEN].mean()),
                   pire_baisse=float((cum - np.maximum.accumulate(cum)).min()), survie_60=float(1 - BT.grilles_depuis(jw, dw, 60).mean()),
                   grille_250=float(BT.grilles_depuis(jw, dw, 250).mean()), periode=float(j[PER].sum()), net_an=vie["net_an"], grilles_an=vie["grilles_an"])


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


def resume(nom, m):
    return (f"{nom} (2017 - 2026) : {m['seances_tradees']:.0%} des séances ; compte : survie {m['survie_60']:.0%}, grillé en 1 an {m['grille_250']:.0%}, "
            f"{m['grilles_an']:.2f} masters grillés par an, net {m['net_an']:,.0f} $ par an").replace(",", " ") + (
            f", t {m['t']:.2f} (depuis 2023 : {m['t_apres']:.2f})" if "t" in m else f", 1re année {m['net_1an']:,.0f} $".replace(",", " "))


def ligne(ident, nom, j, coul, m, statut, raison=""):
    Lg = DX.ligne(ident, nom, statut, coul)
    Lg["courbe"] = [round(float(v), 1) for v in np.cumsum(j)[::PAS]]; Lg["stats"] = m; Lg["raison"] = raison
    Lg["tri"] = (2 if statut == "retenu" else -2 if statut == "tué" else 0) + (m.get("survie_60") or 0) - (m.get("grilles_an") or 0)
    DX.maj(relief=True, curseur=len(Lg["courbe"]) - 1)


ECART = W.ecart_vix(B); INV = ECART >= 0
ST = sorted(BT.supertrend(B), key=lambda t: (t[0], t[2]))
Z12 = sorted([t for t in BT.zone(B) if not INV[t[0]]], key=lambda t: (t[0], t[2]))
DX.maj(force=True, progression=0.05, phase="Vague 6 : W1 de production (hors échantillon)", detail="10 graines, 2017 - 2026")
W1p = trier(ST, "W1 (production)")
REF = {}
for ident, nom, tr, coul in (("Z12", "Z12 · Bot 3 en 1 sans VIX inversé", Z12, "#5ad1c8"), ("W1", "W1 · Supertrend trié (production)", W1p, "#f9c74f")):
    j, m = mesurer(tr); REF[ident] = m
    ligne(ident, nom + " (référence)", j, coul, m, "référence"); DX.dire(resume(nom, m), "c")

RES = {}
BASES = (("M1", "M1 · cassure des 5 premières minutes, triée", orb(5), "#ffd166"),
         ("M2", "M2 · XGBoost NQ, trié", BT.xgboost(B), "#ffa028"),
         ("M3", "M3 · Z12, trié", Z12, "#90e0ef"))
for k, (ident, nom, tr, coul) in enumerate(BASES):
    DX.maj(force=True, progression=0.2 + 0.15 * k, phase=f"Vague 6 : {nom}", detail="tri par apprentissage en marche avant")
    garde = trier(tr, nom)
    j, m = mesurer(garde); z = REF["Z12"]; raisons = []
    if m["t"] < 2: raisons.append(f"t {m['t']:.2f} sous 2")
    if m["t_avant"] <= 0 or m["t_apres"] <= 0: raisons.append("négatif sur 2017-2022 ou sur 2023-2026")
    if m["t_frais6"] < 1.5: raisons.append(f"avec 6 $ de frais t {m['t_frais6']:.2f}")
    if m["annees_pos"] < 7: raisons.append(f"{m['annees_pos']} années positives sur 10")
    if ident in ("M1", "M2"):
        if m["seances_tradees"] < 0.5: raisons.append(f"trade seulement {m['seances_tradees']:.0%} des séances")
        if m["survie_60"] < 0.90: raisons.append(f"survie {m['survie_60']:.0%} sous 90 %")
        if m["grille_250"] > 0.30: raisons.append(f"{m['grille_250']:.0%} de comptes neufs grillés dans l'année (au plus 30 %)")
        if m["grilles_an"] > 0.30: raisons.append(f"{m['grilles_an']:.2f} masters grillés par an (au plus 0,30)")
    else:
        if m["grilles_an"] > z["grilles_an"] + 1e-9: raisons.append(f"{m['grilles_an']:.2f} masters grillés par an, plus que Z12 ({z['grilles_an']:.2f})")
        if m["net_an"] < z["net_an"]: raisons.append(f"net {m['net_an']:,.0f} $ par an, moins que Z12 ({z['net_an']:,.0f} $)".replace(",", " "))
    RES[ident] = dict(nom=nom, trades=len(garde), raisons=raisons, **m)
    ligne(ident, nom, j, coul, m, "tué" if raisons else "en cours", "; ".join(raisons))
    DX.dire(resume(nom, m) + (f" → tué ({'; '.join(raisons)})." if raisons else " → passe ses règles, en attente de la correction des tests multiples."), "b" if raisons else "h")

# Benjamini-Hochberg : famille de 7 (les 4 politiques n'ont pas de p : comptees comme p = 1, ce qui rend la correction plus severe)
cles = list(RES); pv = np.array([1 - stats.norm.cdf(RES[c]["t"]) for c in cles] + [1.0] * 4); o = np.argsort(pv)
okk = pv[o] <= 0.05 * np.arange(1, len(pv) + 1) / len(pv); kk = (np.nonzero(okk)[0].max() + 1) if okk.any() else 0
bh = {int(i) for i in o[:kk]}
for i, c in enumerate(cles):
    RES[c]["p"] = float(pv[i]); RES[c]["bh"] = i in bh
    if i not in bh: RES[c]["raisons"].append("ne survit pas à Benjamini-Hochberg")
    RES[c]["retenu"] = not RES[c]["raisons"]
    for Lg in DX.e["lignes"]:
        if Lg["id"] == c:
            Lg["statut"] = "retenu" if RES[c]["retenu"] else "tué"; Lg["raison"] = "; ".join(RES[c]["raisons"])

# B. politiques du compte
DX.maj(force=True, progression=0.7, phase="Vague 6 : démarrage prudent du compte", detail="Z12 seul, puis Z12 + W1 quand la marge le permet")
Zj = jours_de(Z12); P1j = jours_de(Z12 + W1p, ensemble=True); P2j = jours_de(un_contrat(Z12, W1p))
_, ref = politique(Zj, Zj, 1e12, 2600.0)
DX.dire(f"Z12 seul, même simulateur (référence de B) : net {ref['net_an']:,.0f} $ par an, survie {ref['survie_60']:.0%}, grillé en 1 an {ref['grille_250']:.0%}, "
        f"{ref['grilles_an']:.2f} masters grillés par an, {ref['seances_tradees']:.0%} des séances.".replace(",", " "), "c")
POL = {}
for ident, nom, M, seuil, garde, coul in (("L1", "L1 · Z12, puis Z12 + W1 dès 3 500 $ de marge (limite commune)", P1j, 3500.0, 4000.0, "#ffffff"),
                                          ("L2", "L2 · Z12, puis Z12 + W1 dès 5 000 $ de marge (limite commune)", P1j, 5000.0, 6000.0, "#e0e0e0"),
                                          ("L3", "L3 · Z12, puis Z12 + W1 dès 3 500 $ (un contrat à la fois)", P2j, 3500.0, 4000.0, "#e9c46a"),
                                          ("L4", "L4 · Z12, puis Z12 + W1 dès 5 000 $ (un contrat à la fois)", P2j, 5000.0, 6000.0, "#d4a373")):
    j, m = politique(Zj, M, seuil, garde); raisons = []
    if m["survie_60"] < 0.95: raisons.append(f"survie {m['survie_60']:.0%} sous 95 %")
    if m["grille_250"] > 0.20: raisons.append(f"{m['grille_250']:.0%} de comptes neufs grillés dans l'année (au plus 20 %)")
    if m["grilles_an"] > 0.15: raisons.append(f"{m['grilles_an']:.2f} masters grillés par an (au plus 0,15)")
    if m["net_an"] < 1.3 * ref["net_an"]: raisons.append(f"net {m['net_an']:,.0f} $ par an, il faut {1.3 * ref['net_an']:,.0f} $".replace(",", " "))
    if m["seances_tradees"] < 0.5: raisons.append(f"trade {m['seances_tradees']:.0%} des séances (au moins 50 %)")
    POL[ident] = dict(nom=nom, raisons=raisons, retenu=not raisons, **m)
    ligne(ident, nom, j, coul, m, "retenu" if not raisons else "tué", "; ".join(raisons))
    DX.dire(resume(nom, m) + (" → RETENUE." if not raisons else f" → tuée ({'; '.join(raisons)})."), "h" if not raisons else "b"); time.sleep(0.2)

g_ = [c for c in cles if RES[c]["retenu"]] + [c for c in POL if POL[c]["retenu"]]
DX.dire("Vague 6 : " + (", ".join(g_) + " retenu(s)." if g_ else "rien ne passe toutes ses règles."), "a")
json.dump(dict(references=REF, reference_politique=ref, tri=RES, politiques=POL), open(os.path.join(DOSSIER, "vague6.json"), "w"), default=float)
DX.maj(relief=True, force=True, progression=1.0, phase="Vague 6 terminée", detail="3 tris et 4 politiques", fini=True)
DX.dire("Vague 6 terminée.", "a")
