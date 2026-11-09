#!/usr/bin/env python3
"""Arene, vague 9 (ml/arene/VAGUE9.md, regles fixees avant calcul) :
A. la regle d'inactivite de Bulenox (au moins un trade tous les 5 jours de trading) : Z12F (Bot 3 en 1 sans VIX inverse ni
   jours de la Fed) qui, apres 4 seances de suite sans trade, prend aussi le 5e jour les signaux de W1 (production, hors
   echantillon) ou a defaut du Supertrend NQ (K1), ou seulement du Supertrend (K2) ; un contrat a la fois, Z12F prioritaire.
   Mesure 2017 - 2026.
B. la nuit (permise par le contrat de 18 h a 16 h 59) : achat a l'ouverture Globex de 18 h, vente a 9 h 30 (N1), seulement
   apres une seance 9 h 30 - 16 h en baisse (N2). Mesure 2011 - 2026.
En direct dans l'arene. MINUTES_NQ=... CACHE_DOSSIER=... python3 vague9.py <dossier>"""
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
import w1 as W
from direct import Direct

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import donnees as Dn  # noqa: E402

DOSSIER = sys.argv[1]
R_ = Path(__file__).resolve().parents[2]
B = BT.Base(os.environ["CACHE_DOSSIER"])
O, H, L, C = B.O, B.H, B.L, B.C
aj = B.an[B.test]; n = len(B.test); jours = [B.J[s] for s in B.test]; FEN = aj >= 2017; d17 = int(np.argmax(FEN)); PAS = 5
PREF = float(Dn.PREF)
DX = Direct(DOSSIER)
DX.maj(force=True, phase="Vague 9 : la règle d'inactivité de Bulenox, et la nuit", detail="préparation", progression=0.0, fini=False,
       jours=jours[::PAS], curseur=0, pied=[
           ("vague 9", "A : au moins un trade tous les 5 jours avec une vraie stratégie (K1 W1 puis Supertrend, K2 Supertrend) ; B : la dérive de nuit (N1, N2) (ml/arene/VAGUE9.md)"),
           ("A retenue si", "aucune série de 5 séances sans trade 2017 - 2026, survie 60 j ≥ 95 %, ≤ 20 % de comptes neufs grillés en 1 an, ≤ 0,15 master grillé par an, net ≥ 90 % de Z12F"),
           ("B retenue si", "t ≥ 2 et Benjamini-Hochberg, positive 2011 - 2022 et 2023 - 2026, t ≥ 1,5 à 6 $ de frais, ≥ 11 années positives sur 16"),
           ("période", f"A : 2017 → {jours[-1]} ; B : 2011 → {jours[-1]} (courbes depuis 2014)")])
DX.dire("Vague 9 : le contrat Master demande au moins un trade tous les 5 jours de trading. Je cherche à rester actif avec une vraie stratégie, et je teste la nuit.", "a")


def ligne(ident, nom, j, coul, m, statut, raison=""):
    Lg = DX.ligne(ident, nom, statut, coul)
    Lg["courbe"] = [round(float(v), 1) for v in np.cumsum(j)[::PAS]]; Lg["stats"] = m; Lg["raison"] = raison
    Lg["tri"] = (2 if statut == "retenu" else -2 if statut == "tué" else 0) + (m.get("survie_60") or 0) - (m.get("grilles_an") or 0)
    DX.maj(relief=True, curseur=len(Lg["courbe"]) - 1)


def series_vides(trade):
    """Longueurs des series de seances de suite sans aucun trade."""
    out, k = [], 0
    for x in trade:
        if x:
            if k: out.append(k)
            k = 0
        else:
            k += 1
    if k: out.append(k)
    return out


# ================================================================== A. rester actif (2017 - 2026)
FED = {l.strip() for l in open(Path(__file__).parent / "donnees/fomc.txt") if l.strip() and not l.startswith("#")}
INV = W.ecart_vix(B) >= 0
ZF = sorted([t for t in BT.zone(B) if not INV[t[0]] and B.J[t[0]] not in FED], key=lambda t: (t[0], t[2]))
ST = sorted(BT.supertrend(B), key=lambda t: (t[0], t[2]))
DX.maj(force=True, progression=0.03, phase="Vague 9 : W1 (production) appris année par année", detail="marche en avant 2017 - 2026, 10 graines")
DX.dire(f"W1 version de production : {len(ST):,} signaux du Supertrend, appris chaque année sur le passé seul (10 graines).".replace(",", " "), "c")
X, y, an = W.variables_prod(B, ST)
p = W.probas(X, y, an); W1, garde = W.tri(ST, p, y, an)
DX.dire(f"W1 garde {garde[an >= 2017].mean():.0%} des signaux de 2017 - 2026.", "c")


def par_s(tr):
    d = {}
    for t in tr:
        d.setdefault(t[0], []).append(t)
    return d


def un_contrat(z, autres):
    """Un contrat a la fois, Z12F prioritaire : un signal de secours n'entre pas pendant une position de Z12F ; si Z12F entre
    pendant une position de secours, celle-ci est fermee a la cloture de la minute d'entree de Z12F (comme P2, vague 5)."""
    out = list(z)
    for t in autres:
        s, sens, m_in, deb, fin, e, x = t; sortie_ = fin + 1 if fin < 389 else 389
        conflit = next((q for q in z if m_in <= q[4] and q[2] <= sortie_), None)
        if conflit is None:
            out.append(t)
        elif m_in <= conflit[2]:
            out.append((s, sens, m_in, deb, conflit[2], e, float(C[s, conflit[2]])))
    return sorted(out, key=lambda t: (t[0], t[3]))


def regle_5e_jour(secours):
    """K1 / K2 : sequentiel sur les seances 2017 - 2026 ; apres 4 seances de suite sans aucun trade, ce jour-la on ajoute les
    signaux du premier secours qui en a (W1, puis le Supertrend pour K1)."""
    zs = par_s(ZF); sec = [par_s(x) for x in secours]
    out = [t for t in ZF if B.an[t[0]] < 2017]                     # avant 2017 : Z12F seul (hors mesure)
    vide, forces, source = 0, [], {}
    for i, s in enumerate(B.test):
        if not FEN[i]:
            continue
        jour = list(zs.get(s, []))
        if vide >= 4:
            for k, d in enumerate(sec):
                if d.get(s):
                    jour = un_contrat(jour, d[s]); forces.append(int(s)); source[int(s)] = k
                    break
        out += jour
        vide = 0 if jour else vide + 1
    return sorted(out, key=lambda t: (t[0], t[3])), forces, source


def mesurer(tr):
    r, dp, ntr = BT.journees(B, tr, 1, 400.0); r6 = BT.journees(B, tr, 1, 400.0, 6.0)[0]
    j, dd = r[B.test], dp[B.test]
    jours_tr = {t[0] for t in tr}; tt = np.array([s in jours_tr for s in B.test])
    jw, dw = j[FEN], dd[FEN]; cum = np.cumsum(jw); a = aj[FEN]
    vie = BT.vie(np.vstack([j, j, j]), np.vstack([dd, dd, dd]), tt, debut=d17)
    sv = series_vides(tt[FEN])
    # variante prudente : les seances incompletes du fichier (demi-journees, jours feries courts) comptees comme sans trade
    tous = [s for s in range(len(B.J)) if B.an[s] >= 2017]; sv2 = series_vides([s in jours_tr for s in tous])
    m = dict(par_seance=float(jw.mean()), t=BT.tst(jw), t_avant=BT.tst(jw[a <= 2022]), t_apres=BT.tst(jw[a >= 2023]), t_frais6=BT.tst(r6[B.test][FEN]),
             annees_pos=int(sum(jw[a == yy].sum() > 0 for yy in range(2017, 2027))), seances_tradees=float(tt[FEN].mean()),
             pire_jour=float(jw.min()), pire_baisse=float((cum - np.maximum.accumulate(cum)).min()),
             survie_60=float(1 - BT.grilles_depuis(jw, dw, 60).mean()), grille_250=float(BT.grilles_depuis(jw, dw, 250).mean()),
             periode=float(j[np.array([x >= "2026-08-11" for x in jours])].sum()), net_an=vie["net_an"], grilles_an=vie["grilles_an"],
             series5=int(sum(k >= 5 for k in sv)), series5_an=float(sum(k >= 5 for k in sv) / (FEN.sum() / 252)), plus_longue=int(max(sv) if sv else 0),
             series5_prudent=int(sum(k >= 5 for k in sv2)), plus_longue_prudent=int(max(sv2) if sv2 else 0))
    return j * FEN, m, r


def resume(nom, m):
    return (f"{nom} (2017 - 2026) : {m['par_seance']:+.1f} $ par séance, t {m['t']:.2f} (depuis 2023 : {m['t_apres']:.2f}), {m['seances_tradees']:.0%} des séances ; "
            f"séries de 5 séances sans trade : {m['series5']} ({m['series5_an']:.1f} par an, la plus longue {m['plus_longue']}) ; compte : survie {m['survie_60']:.0%}, "
            f"grillé en 1 an {m['grille_250']:.0%}, {m['grilles_an']:.2f} masters grillés par an, net {m['net_an']:,.0f} $ par an").replace(",", " ")


jz, z, rz = mesurer(ZF)
ligne("Z12F", "Z12F · Bot 3 en 1 sans VIX inversé ni Fed (référence)", jz, "#5ad1c8", z, "référence"); DX.dire(resume("Z12F", z), "c")
RES = {}
for k, (ident, nom, secours, coul) in enumerate((("K1", "K1 · 5e jour : W1, sinon Supertrend", (W1, ST), "#f9c74f"),
                                                ("K2", "K2 · 5e jour : Supertrend", (ST,), "#3cc8ff"))):
    DX.maj(force=True, progression=0.35 + 0.15 * k, phase=f"Vague 9 : {nom}", detail="rejeu minute par minute, un contrat à la fois")
    tr, forces, source = regle_5e_jour(secours)
    j, m, r = mesurer(tr)
    fj = np.array(forces, int)
    m["jours_forces"] = len(forces); m["jours_forces_an"] = float(len(forces) / (FEN.sum() / 252))
    m["gain_jours_forces"] = float((r[fj] - rz[fj]).sum()) if len(fj) else 0.0
    m["par_jour_force"] = float((r[fj] - rz[fj]).mean()) if len(fj) else 0.0
    m["jours_forces_w1"] = int(sum(1 for v in source.values() if v == 0)) if ident == "K1" else 0
    raisons = []
    if m["series5"] > 0: raisons.append(f"{m['series5']} séries de 5 séances sans trade (la plus longue {m['plus_longue']})")
    if m["survie_60"] < 0.95: raisons.append(f"survie {m['survie_60']:.0%} sous 95 %")
    if m["grille_250"] > 0.20: raisons.append(f"{m['grille_250']:.0%} de comptes neufs grillés dans l'année (au plus 20 %)")
    if m["grilles_an"] > 0.15: raisons.append(f"{m['grilles_an']:.2f} masters grillés par an (au plus 0,15)")
    if m["net_an"] < 0.9 * z["net_an"]: raisons.append(f"net {m['net_an']:,.0f} $ par an, il faut au moins {0.9 * z['net_an']:,.0f} $".replace(",", " "))
    RES[ident] = dict(nom=nom, trades=len(tr), raisons=raisons, retenu=not raisons, **m)
    ligne(ident, nom, j, coul, m, "tué" if raisons else "retenu", "; ".join(raisons))
    DX.dire(resume(nom, m) + f" ; {len(forces)} jours de secours ({m['jours_forces_an']:.1f} par an), {m['par_jour_force']:+.0f} $ par jour de secours"
            + (f" → tué ({'; '.join(raisons)})." if raisons else " → retenu."), "b" if raisons else "h")
    time.sleep(0.2)

# ================================================================== B. la nuit (2011 - 2026)
DX.maj(force=True, progression=0.7, phase="Vague 9 : la dérive de nuit", detail="ouverture Globex de 18 h (Yahoo) → ouverture de 9 h 30 (minutes)")
yd = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(R_ / "radar/donnees/jour/yahoo/*.csv.gz")))])
Y = yd[yd.serie.isin(["NQ=F:o", "NQ=F:c"])].pivot_table(index="date", columns="serie", values="valeur").dropna()
dates_y = list(Y.index); prec_y = {d: dates_y[i - 1] for i, d in enumerate(dates_y) if i}
NB = len(B.J); nuit = np.full(NB, np.nan); jour_rth = np.full(NB, np.nan); baisse = np.zeros(NB, bool)
ecartes = dict(sans_yahoo=0, veille_incomplete=0, contrats_differents=0)
for s in np.nonzero(B.ok)[0]:
    if s < 1 or B.an[s] < 2011:
        continue
    j = B.J[s]
    if j not in Y.index or prec_y.get(j) != B.J[s - 1]:
        ecartes["sans_yahoo"] += 1; continue
    if not B.ok[s - 1]:
        ecartes["veille_incomplete"] += 1; continue
    if abs(Y.loc[B.J[s - 1], "NQ=F:c"] / C[s - 1, 389] - 1) > 0.006:
        ecartes["contrats_differents"] += 1; continue
    o18 = float(Y.loc[j, "NQ=F:o"])
    nuit[s] = (O[s, 0] - o18) * 2.0 * PREF / o18
    jour_rth[s] = (C[s, 389] - O[s, 0]) * 2.0 * PREF / O[s, 0]
    baisse[s] = C[s - 1, 389] < O[s - 1, 0]
EL = np.nonzero(np.isfinite(nuit))[0]; aE = B.an[EL]
DX.dire(f"Nuits : {len(EL):,} séances 2011 - 2026 avec les deux sources sur le même contrat ; écartées : {ecartes['contrats_differents']} (contrats différents), "
        f"{ecartes['veille_incomplete']} (veille incomplète), {ecartes['sans_yahoo']} (pas de barre Yahoo correspondante).".replace(",", " "), "c")


def mesure_nuit(brut, garder):
    """Resultats par seance eligible (0 les nuits non prises) ; frais de 3 $ et de 6 $."""
    r3 = np.where(garder, brut - 3.0, 0.0); r6 = np.where(garder, brut - 6.0, 0.0); pris = brut[garder]
    cum = np.cumsum(r3)
    m = dict(par_seance=float(r3.mean()), par_nuit=float((pris - 3.0).mean()), nuits=int(garder.sum()), t=BT.tst(r3), t_avant=BT.tst(r3[aE <= 2022]),
             t_apres=BT.tst(r3[aE >= 2023]), t_frais6=BT.tst(r6), annees_pos=int(sum(r3[aE == yy].sum() > 0 for yy in range(2011, 2027))),
             par_an=float(r3.sum() / (len(EL) / 252)), pire_nuit=float(pris.min() - 3.0), meilleure_nuit=float(pris.max() - 3.0),
             nuits_sous_1100=int((pris - 3.0 <= -1100).sum()), nuits_sous_2500=int((pris - 3.0 <= -2500).sum()),
             pire_baisse=float((cum - np.maximum.accumulate(cum)).min()),
             depuis_2023=float(r3[aE >= 2023].sum()), periode=float(r3[np.array([B.J[s] >= "2026-08-11" for s in EL])].sum()))
    return r3, m


def courbe_2014(r3):
    v = np.zeros(NB); v[EL] = r3
    return v[B.test]


def resume_nuit(nom, m):
    return (f"{nom} (2011 - 2026) : {m['nuits']:,} nuits, {m['par_nuit']:+.1f} $ par nuit, t {m['t']:.2f} (2011 - 2022 : {m['t_avant']:.2f}, depuis 2023 : {m['t_apres']:.2f}), "
            f"à 6 $ de frais t {m['t_frais6']:.2f}, {m['annees_pos']} années positives sur 16, {m['par_an']:,.0f} $ par an ; pire nuit {m['pire_nuit']:,.0f} $, "
            f"{m['nuits_sous_1100']} nuits sous −1 100 $ (la limite du jour de Bulenox), {m['nuits_sous_2500']} sous −2 500 $").replace(",", " ")


TESTS_B = (("N1", "N1 · achat 18 h → 9 h 30, chaque nuit", np.ones(len(EL), bool), "#b48cff"),
           ("N2", "N2 · la même chose après une séance en baisse", baisse[EL], "#ff7ab6"))
for k, (ident, nom, garder, coul) in enumerate(TESTS_B):
    DX.maj(force=True, progression=0.75 + 0.1 * k, phase=f"Vague 9 : {nom}", detail="2011 - 2026, 1 MNQ")
    r3, m = mesure_nuit(nuit[EL], garder)
    raisons = []
    if m["t"] < 2: raisons.append(f"t {m['t']:.2f} sous 2")
    if m["t_avant"] <= 0 or m["t_apres"] <= 0: raisons.append("négatif sur 2011-2022 ou sur 2023-2026")
    if m["t_frais6"] < 1.5: raisons.append(f"avec 6 $ de frais t {m['t_frais6']:.2f}")
    if m["annees_pos"] < 11: raisons.append(f"{m['annees_pos']} années positives sur 16")
    RES[ident] = dict(nom=nom, raisons=raisons, **m)
    ligne(ident, nom + " (courbe depuis 2014)", courbe_2014(r3), coul, m, "tué" if raisons else "en cours", "; ".join(raisons))
    DX.dire(resume_nuit(nom, m) + (f" → tué ({'; '.join(raisons)})." if raisons else " → passe ses règles, en attente de la correction des tests multiples."), "b" if raisons else "h")
    time.sleep(0.2)
# information (pas un test) : la journee 9 h 30 - 16 h sur les memes seances, pour comparer la nuit et le jour
rj, mj = mesure_nuit(jour_rth[EL], np.ones(len(EL), bool))
ligne("jour", "information · achat 9 h 30 → 16 h, les mêmes séances", courbe_2014(rj), "#8d8d95", mj, "référence")
DX.dire(resume_nuit("Pour comparer, la journée 9 h 30 → 16 h", mj).replace("nuits", "séances").replace("par nuit", "par séance").replace("pire nuit", "pire séance"), "c")

cles = ["N1", "N2"]; pv = np.array([1 - stats.norm.cdf(RES[c]["t"]) for c in cles]); o = np.argsort(pv)
okk = pv[o] <= 0.05 * np.arange(1, len(pv) + 1) / len(pv); kk = (np.nonzero(okk)[0].max() + 1) if okk.any() else 0
bh = {cles[i] for i in o[:kk]}
for c in cles:
    RES[c]["p"] = float(pv[cles.index(c)]); RES[c]["bh"] = c in bh
    if c not in bh: RES[c]["raisons"].append("ne survit pas à Benjamini-Hochberg")
    RES[c]["retenu"] = not RES[c]["raisons"]
    for Lg in DX.e["lignes"]:
        if Lg["id"] == c:
            Lg["statut"] = "retenu" if RES[c]["retenu"] else "tué"; Lg["raison"] = "; ".join(RES[c]["raisons"])
g_ = [c for c in RES if RES[c]["retenu"]]
DX.dire("Vague 9 : " + (", ".join(g_) + " retenu(s)." if g_ else "rien ne passe toutes ses règles."), "a")
json.dump(dict(reference=z, tests=RES, information_jour=mj, nuits_ecartees=ecartes, garde_w1=float(garde[an >= 2017].mean())),
          open(os.path.join(DOSSIER, "vague9.json"), "w"), default=float)
DX.maj(relief=True, force=True, progression=1.0, phase="Vague 9 terminée", detail="4 tests", fini=True)
DX.dire("Vague 9 terminée.", "a")
