#!/usr/bin/env python3
"""Arene, vague 8 (ml/arene/VAGUE8.md, regles fixees avant calcul) : A. retour a la moyenne sur les journees sans Z12 (R1 bandes
de la VWAP, R2 RSI 2, R3 fausse cassure de l'ouverture), seules puis avec Z12 sur le meme compte (un contrat a la fois, Z12
prioritaire) ; B. filtres de journee pour Z12 (F1 Fed, F2 gros ecart d'ouverture, F3 pause apres une seance perdante, F4 limite
250 $). 2014 - 2026, en direct dans l'arene. MINUTES_NQ=... CACHE_DOSSIER=... python3 vague8.py <dossier>"""
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats

import bots as BT
import w1 as W
from direct import Direct

DOSSIER = sys.argv[1]
B = BT.Base(os.environ["CACHE_DOSSIER"])
O, H, L, C, V, ATR = B.O, B.H, B.L, B.C, B.V, B.atr
OK = np.nonzero(B.ok)[0]
jours = [B.J[s] for s in B.test]; n = len(B.test); PAS = 5
DX = Direct(DOSSIER)
DX.maj(force=True, phase="Vague 8 : les journées sans Z12, des filtres pour Z12", detail="préparation", progression=0.0, fini=False,
       jours=jours[::PAS], curseur=0, pied=[
           ("vague 8", "A : retour à la moyenne (VWAP, RSI 2, fausse cassure) avec Z12 ; B : Z12 sans Fed, sans gros écart, pause après une perte, limite 250 $ (ml/arene/VAGUE8.md)"),
           ("A retenue si", "avec Z12 : survie 60 j ≥ 95 %, ≤ 20 % de comptes neufs grillés en 1 an, ≤ 0,15 master grillé par an, net ≥ 1,3 × Z12, ≥ 50 % des séances"),
           ("B retenu si", "moins de comptes neufs grillés que Z12, pas plus de masters grillés, net au moins égal"),
           ("période", f"{jours[0]} → {jours[-1]} ({n} séances)")])
DX.dire("Vague 8 : je cherche des gains sur les journées où Z12 ne fait rien, et des filtres de journée qui rendent Z12 plus sûr.", "a")


def sortie(s, sens, m0, e, stop, cible, fin_max=384):
    """Premier contact du stop ou de l'objectif a partir de la minute m0 (stop compte en premier dans une meme minute)."""
    for m in range(m0, fin_max + 1):
        if sens > 0:
            if m > m0 and O[s, m] <= stop: return m - 1, float(O[s, m])
            if L[s, m] <= stop: return m - 1, float(stop)
            if cible is not None and m > m0 and O[s, m] >= cible: return m - 1, float(O[s, m])
            if cible is not None and H[s, m] >= cible: return m - 1, float(cible)
        else:
            if m > m0 and O[s, m] >= stop: return m - 1, float(O[s, m])
            if H[s, m] >= stop: return m - 1, float(stop)
            if cible is not None and m > m0 and O[s, m] <= cible: return m - 1, float(O[s, m])
            if cible is not None and L[s, m] <= cible: return m - 1, float(cible)
    return fin_max, float(C[s, fin_max])


def r1_vwap():
    out = []
    for s in OK:
        tp = (H[s] + L[s] + C[s]) / 3; v = V[s]; cv = np.cumsum(v); ctv = np.cumsum(tp * v); ctv2 = np.cumsum(tp * tp * v)
        ct = np.cumsum(tp); ct2 = np.cumsum(tp * tp); nb = 0; m = 29
        while m + 1 <= 360 and nb < 2:
            k = m + 1
            if cv[m] > 0:
                vw = ctv[m] / cv[m]; var = ctv2[m] / cv[m] - vw * vw
            else:
                vw = ct[m] / k; var = ct2[m] / k - vw * vw
            sd = np.sqrt(max(var, 0.0)); c = C[s, m]; sens = 0
            if sd > 0 and c > vw + 2 * sd: sens = -1
            elif sd > 0 and c < vw - 2 * sd: sens = 1
            if sens == 0:
                m += 5; continue
            e = O[s, m + 1]; risque = (vw - e) * sens
            if risque <= 0:
                m += 5; continue
            fin, x = sortie(s, sens, m + 1, e, e - sens * risque, vw)
            out.append((int(s), sens, m + 1, m + 1, int(fin), float(e), x)); nb += 1
            m = ((fin + 1) // 5) * 5 + 4
    return out


def r2_rsi():
    out = []
    for s in OK:
        c5 = C[s, 4::5][:78]; rsi = np.full(78, np.nan); ag = al = 0.0
        for b in range(1, 78):
            d = c5[b] - c5[b - 1]; g, l_ = max(d, 0.0), max(-d, 0.0)
            if b <= 2:
                ag += g / 2; al += l_ / 2
            else:
                ag = (ag + g) / 2; al = (al + l_) / 2
            if b >= 2:
                rsi[b] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
        nb = 0; b = 5
        while nb < 2 and 5 * b + 5 <= 360:
            r = rsi[b]
            sens = 1 if r < 5 else -1 if r > 95 else 0
            if sens == 0 or np.isnan(r):
                b += 1; continue
            m0 = 5 * b + 5; e = O[s, m0]; a = ATR[BT.bougie_avant(s, m0)]
            if not np.isfinite(a) or a <= 0:
                b += 1; continue
            stop = e - sens * 1.5 * a; fin, x = 384, float(C[s, 384])
            for m in range(m0, 385):
                if sens > 0 and ((m > m0 and O[s, m] <= stop) or L[s, m] <= stop):
                    fin, x = m - 1, float(O[s, m] if (m > m0 and O[s, m] <= stop) else stop); break
                if sens < 0 and ((m > m0 and O[s, m] >= stop) or H[s, m] >= stop):
                    fin, x = m - 1, float(O[s, m] if (m > m0 and O[s, m] >= stop) else stop); break
                if m % 5 == 4 and m < 384:
                    rb = rsi[m // 5]
                    if (sens > 0 and rb > 50) or (sens < 0 and rb < 50):
                        fin, x = m, float(O[s, m + 1]); break
            out.append((int(s), sens, m0, m0, int(fin), float(e), x)); nb += 1
            b = (fin + 1) // 5 + 1 if fin < 384 else 99
    return out


def r3_fausse_cassure():
    out = []
    for s in OK:
        orh, orl = H[s, :30].max(), L[s, :30].min()
        b = 6; casse, debut = 0, -1
        while 5 * b + 5 <= 360 and b < 78:
            c = C[s, 5 * b + 4]
            if casse == 0:
                if c > orh: casse, debut = 1, b
                elif c < orl: casse, debut = -1, b
            elif b - debut > 3:
                break
            elif (casse > 0 and c < orh) or (casse < 0 and c > orl):
                sens = -casse; m0 = 5 * b + 5; e = O[s, m0]
                stop = H[s, 5 * debut:m0].max() if sens < 0 else L[s, 5 * debut:m0].min()
                cible = orl if sens < 0 else orh
                if (stop - e) * (-sens) > 0 and (cible - e) * sens > 0:
                    fin, x = sortie(s, sens, m0, e, stop, cible)
                    out.append((int(s), sens, m0, m0, int(fin), float(e), x))
                break
            b += 1
    return out


def un_contrat(z12, autres):
    par_s = {}
    for t in z12:
        par_s.setdefault(t[0], []).append(t)
    out = list(z12)
    for t in autres:
        s, sens, m_in, deb, fin, e, x = t; sortie_ = fin + 1 if fin < 389 else 389
        conflit = next((z for z in par_s.get(s, []) if m_in <= z[4] and z[2] <= sortie_), None)
        if conflit is None:
            out.append(t)
        elif m_in <= conflit[2]:
            out.append((s, sens, m_in, deb, conflit[2], e, float(C[s, conflit[2]])))
    return sorted(out, key=lambda t: (t[0], t[3]))


def mesurer(tr, limite=400.0):
    r, dp, ntr = BT.journees(B, tr, 1, limite); r6 = BT.journees(B, tr, 1, limite, 6.0)[0]
    m = BT.mesures(B, r, dp, ntr); m["t_frais6"] = BT.tst(r6[B.test]); m["seances_tradees"] = float((ntr[B.test] > 0).mean())
    return r[B.test], m


def resume(nom, m):
    return (f"{nom} : {m['par_seance']:+.1f} $ par séance, t {m['t']:.2f} (depuis 2023 : {m['t_apres']:.2f}), {m['seances_tradees']:.0%} des séances ; compte : "
            f"survie {m['survie_60']:.0%}, grillé en 1 an {m['grille_250']:.0%}, {m['grilles_an']:.2f} masters grillés par an, net {m['net_an']:,.0f} $ par an").replace(",", " ")


def ligne(ident, nom, j, coul, m, statut, raison=""):
    Lg = DX.ligne(ident, nom, statut, coul)
    Lg["courbe"] = [round(float(v), 1) for v in np.cumsum(j)[::PAS]]; Lg["stats"] = m; Lg["raison"] = raison
    Lg["tri"] = (2 if statut == "retenu" else -2 if statut == "tué" else 0) + (m.get("survie_60") or 0) - (m.get("grilles_an") or 0)
    DX.maj(relief=True, curseur=len(Lg["courbe"]) - 1)


def regles_edge(m):
    r = []
    if m["t"] < 2: r.append(f"t {m['t']:.2f} sous 2")
    if m["t_avant"] <= 0 or m["t_apres"] <= 0: r.append("négatif sur 2014-2022 ou sur 2023-2026")
    if m["t_frais6"] < 1.5: r.append(f"avec 6 $ de frais t {m['t_frais6']:.2f}")
    if m["annees_pos"] < 9: r.append(f"{m['annees_pos']} années positives sur 13")
    return r


INV = W.ecart_vix(B) >= 0
Z12 = sorted([t for t in BT.zone(B) if not INV[t[0]]], key=lambda t: (t[0], t[2]))
jz, z = mesurer(Z12)
ligne("Z12", "Z12 · Bot 3 en 1 sans VIX inversé (référence)", jz, "#5ad1c8", z, "référence"); DX.dire(resume("Z12", z), "c")
RES = {}
for k, (ident, nom, fab, coul) in enumerate((("R1", "R1 · bandes de la VWAP", r1_vwap, "#b5e48c"), ("R2", "R2 · RSI 2 (Connors)", r2_rsi, "#99d98c"),
                                            ("R3", "R3 · fausse cassure de l'ouverture", r3_fausse_cassure, "#76c893"))):
    DX.maj(force=True, progression=0.05 + 0.15 * k, phase=f"Vague 8 : {nom}", detail="seule, puis avec Z12 sur le même compte")
    tr = fab(); j, m = mesurer(tr)
    raisons = regles_edge(m)
    jc, mc = mesurer(un_contrat(Z12, tr))
    if mc["survie_60"] < 0.95: raisons.append(f"avec Z12 : survie {mc['survie_60']:.0%} sous 95 %")
    if mc["grille_250"] > 0.20: raisons.append(f"avec Z12 : {mc['grille_250']:.0%} de comptes neufs grillés dans l'année (au plus 20 %)")
    if mc["grilles_an"] > 0.15: raisons.append(f"avec Z12 : {mc['grilles_an']:.2f} masters grillés par an (au plus 0,15)")
    if mc["net_an"] < 1.3 * z["net_an"]: raisons.append(f"avec Z12 : net {mc['net_an']:,.0f} $ par an, il faut {1.3 * z['net_an']:,.0f} $".replace(",", " "))
    if mc["seances_tradees"] < 0.5: raisons.append(f"avec Z12 : {mc['seances_tradees']:.0%} des séances (au moins 50 %)")
    RES[ident] = dict(nom=nom, trades=len(tr), raisons=raisons, avec_z12=mc, **m)
    ligne(ident, nom + " (seule)", j, coul, m, "tué" if raisons else "en cours", "; ".join(raisons))
    ligne(f"Z12+{ident}", f"Z12 + {nom}", jc, "#ffffff", mc, "tué" if raisons else "en cours", "; ".join(raisons))
    DX.dire(resume(nom + " seule", m), "c")
    DX.dire(resume(f"Z12 + {ident} (un contrat à la fois)", mc) + (f" → tué ({'; '.join(raisons)})." if raisons else " → passe ses règles, en attente de la correction des tests multiples."), "b" if raisons else "h")

FED = {l.strip() for l in open(Path(__file__).parent / "donnees/fomc.txt") if l.strip() and not l.startswith("#")}
gap = np.full(len(B.J), np.nan)
for s in OK:
    if s > 0 and B.ok[s - 1]:
        gap[s] = O[s, 0] / C[s - 1, 389] - 1
r_z = BT.journees(B, Z12, 1, 400.0)[0]
pause, perdu = set(), False                                        # F3 : pause d'une seance apres une seance perdante
for s in OK:
    if perdu:
        pause.add(int(s)); perdu = False
    else:
        perdu = r_z[s] < 0
FILTRES = (("F1", "F1 · Z12 sans les jours de la Fed", [t for t in Z12 if B.J[t[0]] not in FED], 400.0),
           ("F2", "F2 · Z12 sans gros écart d'ouverture (1 %)", [t for t in Z12 if not (abs(gap[t[0]]) >= 0.01)], 400.0),
           ("F3", "F3 · Z12 avec une pause après une séance perdante", [t for t in Z12 if t[0] not in pause], 400.0),
           ("F4", "F4 · Z12 avec une limite du jour de 250 $", Z12, 250.0))
for k, (ident, nom, tr, lim) in enumerate(FILTRES):
    DX.maj(force=True, progression=0.55 + 0.1 * k, phase=f"Vague 8 : {nom}", detail="rejeu minute par minute")
    j, m = mesurer(tr, lim); raisons = regles_edge(m)
    if m["grille_250"] >= z["grille_250"] - 1e-9: raisons.append(f"{m['grille_250']:.0%} de comptes neufs grillés dans l'année, pas moins que Z12 ({z['grille_250']:.0%})")
    if m["grilles_an"] > z["grilles_an"] + 1e-9: raisons.append(f"{m['grilles_an']:.2f} masters grillés par an, plus que Z12")
    if m["net_an"] < z["net_an"]: raisons.append(f"net {m['net_an']:,.0f} $ par an, moins que Z12 ({z['net_an']:,.0f} $)".replace(",", " "))
    RES[ident] = dict(nom=nom, trades=len(tr), raisons=raisons, **m)
    ligne(ident, nom, j, "#90e0ef", m, "tué" if raisons else "en cours", "; ".join(raisons))
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
        if Lg["id"] in (c, f"Z12+{c}"):
            Lg["statut"] = "retenu" if RES[c]["retenu"] else "tué"; Lg["raison"] = "; ".join(RES[c]["raisons"])
g_ = [c for c in cles if RES[c]["retenu"]]
DX.dire("Vague 8 : " + (", ".join(g_) + " retenu(s)." if g_ else "rien ne passe toutes ses règles."), "a")
json.dump(dict(reference=z, tests=RES), open(os.path.join(DOSSIER, "vague8.json"), "w"), default=float)
DX.maj(relief=True, force=True, progression=1.0, phase="Vague 8 terminée", detail="7 tests", fini=True)
DX.dire("Vague 8 terminée.", "a")
