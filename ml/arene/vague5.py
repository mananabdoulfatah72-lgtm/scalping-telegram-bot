#!/usr/bin/env python3
"""Arene, vague 5 (ml/arene/VAGUE5.md, regles fixees avant calcul) : Z12 + W1 sur le meme compte (limite commune ; un contrat
a la fois) et W1 sans la variable VIX. Mesure 2017 - 2026, en direct dans l'arene.
MINUTES_NQ=... CACHE_DOSSIER=... python3 vague5.py <dossier de l'arene>"""
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
C = B.C
aj = B.an[B.test]; n = len(B.test); jours = [B.J[s] for s in B.test]; FEN = aj >= 2017; d17 = int(np.argmax(FEN)); PAS = 5

DX = Direct(DOSSIER)
DX.maj(force=True, phase="Vague 5 : l'activité de W1 avec la sécurité de Z12", detail="préparation", progression=0.0, fini=False,
       jours=jours[::PAS], curseur=0, pied=[
           ("vague 5", "Z12 + W1 sur le même compte (limite commune ; un contrat à la fois) et W1 sans VIX (ml/arene/VAGUE5.md)"),
           ("but", "trader au moins 75 % des séances avec survie à 60 séances ≥ 90 %, au plus 30 % de comptes grillés dans l'année, net au moins celui de Z12"),
           ("W1", "signaux du Supertrend NQ triés par un modèle réappris chaque année sur le passé seul (moyenne de 10 graines)"),
           ("période", f"mesure 2017 - 2026 ({int(FEN.sum())} séances)")])
DX.dire("Vague 5 : je mets Z12 et W1 sur le même compte pour avoir l'activité de W1 et la sécurité de Z12.", "a")

ECART = W.ecart_vix(B); INV = ECART >= 0
ST = sorted(BT.supertrend(B), key=lambda t: (t[0], t[2]))
Z12 = [t for t in BT.zone(B) if not INV[t[0]]]
X, y, an = W.variables(B, ST, ECART)
DX.dire(f"W1 : {len(ST):,} trades du Supertrend, j'apprends année par année (2017 → 2026) avec 10 graines.".replace(",", " "), "c")
DX.maj(force=True, progression=0.05, phase="Vague 5 : apprentissage de W1 (10 graines)", detail="marche en avant 2017 - 2026")
p = W.probas(X, y, an); W1, garde = W.tri(ST, p, y, an)
DX.maj(force=True, progression=0.35, phase="Vague 5 : apprentissage de W1 sans VIX", detail="marche en avant 2017 - 2026")
cols = [i for i in range(X.shape[1]) if i != W.I_VIX]
p_sv = W.probas(X, y, an, colonnes=cols); W1sv, _ = W.tri(ST, p_sv, y, an)
DX.dire(f"W1 garde {garde[an >= 2017].mean():.0%} des signaux de 2017 - 2026 ; la version sans VIX en garde {np.mean([t in set(W1sv) for t in ST if B.J[t[0]][:4] >= '2017']):.0%}.", "c")


def un_contrat(z12, w1):
    """P2 : jamais plus de 1 MNQ. W1 n'entre pas pendant une position de Z12 ; si Z12 entre pendant une position de W1,
    W1 est ferme a ce moment-la (cloture de la minute d'entree de Z12)."""
    par_s = {}
    for t in z12:
        par_s.setdefault(t[0], []).append(t)
    out = list(z12)
    for t in w1:
        s, sens, m_in, deb, fin, e, x = t; sortie = fin + 1 if fin < 389 else 389
        conflit = next((z for z in par_s.get(s, []) if m_in <= z[4] and z[2] <= sortie), None)
        if conflit is None:
            out.append(t)
        elif m_in <= conflit[2]:                                     # W1 deja en position quand Z12 entre : W1 ferme
            out.append((s, sens, m_in, deb, conflit[2], e, float(C[s, conflit[2]])))
    return sorted(out, key=lambda t: (t[0], t[3]))


def mesurer(tr, ensemble=False):
    if ensemble:
        r, dp, ntr = BT.journees_ensemble(B, tr, 400.0); r6 = BT.journees_ensemble(B, tr, 400.0, 6.0)[0]
    else:
        r, dp, ntr = BT.journees(B, tr, 1, 400.0); r6 = BT.journees(B, tr, 1, 400.0, 6.0)[0]
    j, dd, tt = r[B.test], dp[B.test], ntr[B.test] > 0
    jw, dw = j[FEN], dd[FEN]; cum = np.cumsum(jw); a = aj[FEN]
    vie = BT.vie(np.vstack([j, j, j]), np.vstack([dd, dd, dd]), tt, debut=d17)
    idx = pd.to_datetime(np.array(jours)[FEN]); sj = pd.Series(jw, index=idx)
    sem = sj.groupby([idx.isocalendar().year.values, idx.isocalendar().week.values]).sum(); mo = sj.groupby(idx.to_period("M")).sum()
    m = dict(par_seance=float(jw.mean()), t=BT.tst(jw), t_avant=BT.tst(jw[a <= 2022]), t_apres=BT.tst(jw[a >= 2023]), t_frais6=BT.tst(r6[B.test][FEN]),
             annees_pos=int(sum(jw[a == yy].sum() > 0 for yy in range(2017, 2027))), seances_tradees=float(tt[FEN].mean()),
             jours_positifs=float((jw[tt[FEN]] > 0).mean()), semaines_positives=float((sem > 0).mean()), mois_positifs=float((mo > 0).mean()),
             pire_semaine=float(sem.min()), pire_jour=float(jw.min()), pire_baisse=float((cum - np.maximum.accumulate(cum)).min()),
             survie_60=float(1 - BT.grilles_depuis(jw, dw, 60).mean()), grille_250=float(BT.grilles_depuis(jw, dw, 250).mean()),
             periode=float(j[np.array([x >= "2026-08-11" for x in jours])].sum()), net_an=vie["net_an"], grilles_an=vie["grilles_an"])
    return j, m


def resume(nom, m):
    return (f"{nom} (2017 - 2026) : {m['par_seance']:+.1f} $ par séance, t {m['t']:.2f} (depuis 2023 : {m['t_apres']:.2f}), {m['seances_tradees']:.0%} des séances, "
            f"{m['semaines_positives']:.0%} de semaines et {m['mois_positifs']:.0%} de mois positifs ; compte : survie {m['survie_60']:.0%}, grillé en 1 an {m['grille_250']:.0%}, "
            f"{m['grilles_an']:.2f} masters grillés par an, net {m['net_an']:,.0f} $ par an").replace(",", " ")


def ligne(ident, nom, j, coul, m, statut, raison=""):
    Lg = DX.ligne(ident, nom, statut, coul)
    Lg["courbe"] = [round(float(v), 1) for v in np.cumsum(j)[::PAS]]; Lg["stats"] = m; Lg["raison"] = raison
    Lg["tri"] = (2 if statut == "retenu" else -2 if statut == "tué" else 0) + (m.get("survie_60") or 0) - (m.get("grilles_an") or 0)
    DX.maj(relief=True, curseur=len(Lg["courbe"]) - 1)


REF = {}
for ident, nom, tr, coul in (("st", "Supertrend NQ", ST, "#3cc8ff"), ("Z12", "Z12 · Bot 3 en 1 sans VIX inversé", Z12, "#5ad1c8"),
                             ("W1", "W1 · Supertrend trié (10 graines)", W1, "#f9c74f")):
    j, m = mesurer(tr); REF[ident] = m
    ligne(ident, nom + " (référence)", j, coul, m, "référence"); DX.dire(resume(nom, m), "c"); time.sleep(0.2)

RES = {}
TESTS = (("P1", "P1 · Z12 + W1, limite commune", Z12 + W1, True, "#ffffff"),
         ("P2", "P2 · Z12 + W1, un contrat à la fois", un_contrat(Z12, W1), False, "#e9c46a"),
         ("P3", "P3 · W1 sans la variable VIX", W1sv, False, "#f4a261"))
for k, (ident, nom, tr, ens, coul) in enumerate(TESTS):
    DX.maj(force=True, progression=0.6 + 0.12 * k, phase=f"Vague 5 : {nom}", detail="rejeu minute par minute")
    j, m = mesurer(tr, ens); z, st = REF["Z12"], REF["st"]; raisons = []
    if m["t"] < 2: raisons.append(f"t {m['t']:.2f} sous 2")
    if m["t_avant"] <= 0 or m["t_apres"] <= 0: raisons.append("négatif sur 2017-2022 ou sur 2023-2026")
    if m["t_frais6"] < 1.5: raisons.append(f"avec 6 $ de frais t {m['t_frais6']:.2f}")
    if m["annees_pos"] < 7: raisons.append(f"{m['annees_pos']} années positives sur 10")
    if m["seances_tradees"] < 0.75: raisons.append(f"trade seulement {m['seances_tradees']:.0%} des séances")
    if ident in ("P1", "P2"):
        if m["survie_60"] < 0.90: raisons.append(f"survie {m['survie_60']:.0%} sous 90 %")
        if m["grille_250"] > 0.30: raisons.append(f"{m['grille_250']:.0%} de comptes neufs grillés dans l'année (au plus 30 %)")
        if m["grilles_an"] > 0.30: raisons.append(f"{m['grilles_an']:.2f} masters grillés par an (au plus 0,30)")
        if m["net_an"] < z["net_an"]: raisons.append(f"net {m['net_an']:,.0f} $ par an, moins que Z12 ({z['net_an']:,.0f} $)".replace(",", " "))
    else:
        if m["survie_60"] < st["survie_60"] + 0.10 - 1e-9: raisons.append(f"survie {m['survie_60']:.0%} (il faut {st['survie_60'] + 0.10:.0%})")
        if m["grilles_an"] > 0.8 * st["grilles_an"] + 1e-9: raisons.append(f"{m['grilles_an']:.2f} masters grillés par an (au plus {0.8 * st['grilles_an']:.2f})")
        if m["pire_baisse"] < 1.25 * st["pire_baisse"]: raisons.append("pire baisse trop profonde")
        if m["net_an"] < st["net_an"]: raisons.append("net plus bas que le Supertrend")
    RES[ident] = dict(nom=nom, trades=len(tr), raisons=raisons, **m)
    ligne(ident, nom, j, coul, m, "tué" if raisons else "en cours", "; ".join(raisons))
    DX.dire(resume(nom, m) + (f" → tué ({'; '.join(raisons)})." if raisons else " → passe ses règles, en attente de la correction des tests multiples."), "b" if raisons else "h")

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
DX.dire("Correction des tests multiples faite : " + (", ".join(g_) + " retenu(s)." if g_ else "aucun test ne passe toutes ses règles."), "a")
json.dump(dict(references=REF, tests=RES, garde_w1=float(garde[an >= 2017].mean())), open(os.path.join(DOSSIER, "vague5.json"), "w"), default=float)
DX.maj(relief=True, force=True, progression=1.0, phase="Vague 5 terminée", detail="3 tests", fini=True)
DX.dire("Vague 5 terminée.", "a")
