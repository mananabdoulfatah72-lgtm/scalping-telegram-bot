#!/usr/bin/env python3
"""Arene, vague 10 (ml/arene/VAGUE10.md, regles fixees avant calcul) : le Bot 3 en 1 tel qu'il est regle (Z12F, limite du
jour 1 000 $, frein, plafond 0 ou 500 $) face au vrai contrat Master Bulenox (Option 2) : plancher qui s'arrete a 50 000 $,
retraits (10 jours, 1 000 - 1 500 $, 2 600 $ gardes, 40 %, 90 %), fin du Master au 3e retrait puis funded (plancher de
2 000 $, hypotheses), inactivite (5 jours de trading sans trade, comptes de facon prudente) = compte perdu.
MINUTES_NQ=... CACHE_DOSSIER=... python3 vague10.py <dossier de l'arene>"""
import json
import os
import sys
import time
from pathlib import Path

import numba as nb
import numpy as np

import bots as BT
import w1 as W
from direct import Direct

DOSSIER = sys.argv[1]
ICI = Path(__file__).resolve().parent
B = BT.Base(os.environ["CACHE_DOSSIER"])
C = B.C
aj = B.an[B.test]; n = len(B.test); jours = [B.J[s] for s in B.test]; FEN = aj >= 2017; d17 = int(np.argmax(FEN)); PAS = 5
DX = Direct(DOSSIER)
DX.maj(force=True, phase="Vague 10 : ton bot tel qu'il est réglé, face au vrai contrat", detail="préparation", progression=0.0, fini=False,
       jours=jours[::PAS], curseur=0, pied=[
           ("vague 10", "Z12F, limite 1 000 $, frein, plafond 0 ou 500 $ ; secours du même bot après 3 jours sans trade (ml/arene/VAGUE10.md)"),
           ("contrat", "plancher arrêté à 50 000 $, retraits 1 000 - 1 500 $, 40 %, 90 %, fin du Master au 3e retrait puis funded à 2 000 $, 5 jours sans trade = compte perdu"),
           ("choix", "conforme = aucun compte perdu par inactivité ; puis le moins de Masters perdus avant le 3e retrait (écart d'au moins 5 points et 3 épisodes)"),
           ("période", f"un Master neuf toutes les 20 séances, 2017 → {jours[-1]}")])
DX.dire("Vague 10 : je rejoue ton bot avec ses vrais réglages et le vrai contrat Master, sans rien d'optimiste.", "a")


# ------------------------------------------------------------------ trades
def zone_fichier(f, de="2011-01-01", a="2026-12-31"):
    """Trades d'un journal de rejeu de la zone (meme lecture que bots.zone)."""
    out, ouvert = [], None
    for l in Path(f).read_text().splitlines():
        g = BT.LIGNE.match(l)
        if not g or "ecarte" in l or "RSI" in l or not (de <= g.group(1) <= a):
            continue
        h, mi = int(g.group(5) or g.group(3)), int(g.group(6) or g.group(4))
        mm, px = h * 60 + mi - 570, float(g.group(7))
        if g.group(2) in ("achat", "vente"):
            ouvert = (g.group(1), 1 if g.group(2) == "achat" else -1, mm, px)
        elif ouvert:
            s = B.pos.get(ouvert[0])
            if s is not None:
                out.append((s, ouvert[1], ouvert[2], ouvert[2] + 1, min(389, max(ouvert[2], mm)), ouvert[3], px))
            ouvert = None
    return out


FED = {l.strip() for l in open(ICI / "donnees/fomc.txt") if l.strip() and not l.startswith("#")}
INV = W.ecart_vix(B) >= 0
ZONE = sorted(BT.zone(B), key=lambda t: (t[0], t[2]))
ZF = [t for t in ZONE if not INV[t[0]] and B.J[t[0]] not in FED]
C2 = sorted(zone_fichier(ICI / "donnees/c2.txt", a="2026-10-27") + [t for t in ZONE if B.J[t[0]] >= "2026-10-28"], key=lambda t: (t[0], t[2]))
GAP = np.zeros(n, int); GAP[1:] = np.diff(B.test) - 1                      # jours du fichier sans seance complete entre deux seances


def par_s(tr):
    d = {}
    for t in tr:
        d.setdefault(t[0], []).append(t)
    return d


def un_contrat(z, autres):
    out = list(z)
    for t in autres:
        s, sens, m_in, deb, fin, e, x = t; so = fin + 1 if fin < 389 else 389
        c = next((q for q in z if m_in <= q[4] and q[2] <= so), None)
        if c is None:
            out.append(t)
        elif m_in <= c[2]:
            out.append((s, sens, m_in, deb, c[2], e, float(C[s, c[2]])))
    return out


def secours(base, sources, seuil=3, combiner=False):
    """Apres `seuil` jours de trading de suite sans trade (jours du fichier compris), ce jour-la on prend les trades de la
    premiere source qui en a. combiner=False (T2) : la zone sans filtres remplace la zone du jour ; True (K1c) : un contrat
    a la fois avec la zone prioritaire."""
    zs = par_s(base); src = [par_s(x) for x in sources]
    out, vide, forces = [], 0, 0
    for k, s in enumerate(B.test):
        vide += GAP[k]
        jour = list(zs.get(s, []))
        if vide >= seuil:
            for d in src:
                if d.get(s):
                    jour = un_contrat(jour, d[s]) if combiner else list(d[s]); forces += 1
                    break
        out += jour
        vide = 0 if jour else vide + 1
    return sorted(out, key=lambda t: (t[0], t[3])), forces


# ------------------------------------------------------------------ resultats du jour (limite, plafond, exposition)
@nb.njit(cache=True)
def _journees_cap(S, ts, tsens, tdeb, tfin, te, tx, H, L, taille, limite, cap, frais, pref, glisse):
    """Comme bots._journees, plus le plafond du jour : des que le gain du jour (realise + latent au meilleur prix de la
    minute) atteint `cap`, tout est ferme a ce niveau et plus rien ensuite. Dans une meme minute la perte compte d'abord."""
    res = np.zeros(S); dip = np.zeros(S)
    k = 0; n = len(ts)
    while k < n:
        s = ts[k]; real = 0.0; creux = 0.0; arret = False
        while k < n and ts[k] == s:
            if not arret:
                sens = tsens[k]; e = te[k]; ech = 2.0 * pref / e * taille
                for m in range(tdeb[k], tfin[k] + 1):
                    eq = real + sens * ((L[s, m] if sens > 0 else H[s, m]) - e) * ech
                    if eq < creux:
                        creux = eq
                    if eq <= -limite:
                        real = -limite - glisse * ech - frais * taille; arret = True
                        break
                    if cap > 0:
                        haut = real + sens * ((H[s, m] if sens > 0 else L[s, m]) - e) * ech
                        if haut >= cap:
                            real = cap - frais * taille; arret = True
                            break
                if not arret:
                    real += sens * (tx[k] - e) * ech - frais * taille
                    if real <= -limite or (cap > 0 and real >= cap):
                        arret = True
                if real < creux:
                    creux = real
            k += 1
        res[s] = real; dip[s] = creux
    return res, dip


def jours_de(tr, limite, cap, taille):
    ts, tsens, tdeb, tfin, te, tx = BT.tableaux(tr)
    r, d = _journees_cap(B.S, ts, tsens, tdeb, tfin, te, tx, B.H, B.L, float(taille), float(min(limite, BT.DLL)), float(cap), 3.0, 28500.0, BT.GLISSEMENT)
    return r[B.test], d[B.test]


# ------------------------------------------------------------------ le compte selon le contrat
def vie_contrat(R0, D0, R1, D1, T, i0, frein=750.0):
    """Un Master neuf au jour i0 puis, au 3e retrait, un funded (hypotheses de VAGUE10.md). Renvoie un dict."""
    o = dict(issue="en cours", fin=None, j1=None, j3=None, touche_m=-148.0, funded=None)
    solde = haut = base = 50000.0; meil = 0.0; jrs = 0; nret = 0; vide = 0; perte = 2500.0; phase = "M"; i_f = None; touche_f = 0.0
    for i in range(i0, n):
        if i > i0:
            vide += GAP[i]
        if vide >= 5:
            return fin(o, phase, "inactivité", i, i_f, touche_f)
        plancher = min(haut - perte, 50000.0)
        t = 1 if frein > 0 and solde - plancher < perte - frein else 0
        R, Dp = (R1, D1) if t else (R0, D0)
        if solde + Dp[i] <= plancher:
            return fin(o, phase, "plancher", i, i_f, touche_f)
        solde += R[i]; haut = max(haut, solde)
        if T[i]:
            jrs += 1; vide = 0
        else:
            vide += 1
            if vide >= 5:
                return fin(o, phase, "inactivité", i, i_f, touche_f)
        meil = max(meil, R[i])
        dispo = solde - 52600.0
        if phase == "M" and nret < 3:
            dispo = min(dispo, 1500.0)
        if jrs >= 10 and dispo >= 1000.0 and solde - base > 0 and meil <= 0.4 * (solde - base):
            solde -= dispo; base = solde; meil = 0.0; jrs = 0; nret += 1
            if phase == "M":
                o["touche_m"] += 0.9 * dispo
                if nret == 1: o["j1"] = i - i0
                if nret == 3:                                        # passage en funded (hypotheses)
                    o["j3"] = i - i0; o["issue"] = "3 retraits"
                    phase = "F"; i_f = i; solde = haut = base = 50000.0; meil = 0.0; jrs = 0; nret = 0; perte = 2000.0; vide = 0
            else:
                if i - i_f <= 252: touche_f += 0.9 * dispo
        if phase == "F" and i - i_f >= 252:
            o["funded"] = dict(issue="en vie après 1 an", touche=touche_f); return o
    if phase == "F":
        o["funded"] = dict(issue="données finies", touche=touche_f)
    return o


def fin(o, phase, cause, i, i_f, touche_f):
    if phase == "M":
        o["issue"] = cause; o["fin"] = i
    else:
        o["funded"] = dict(issue=cause, touche=touche_f, fin=i, jours=i - i_f)
    return o


def series(T):
    """Series de jours sans trade, jours du fichier compris (2017 - 2026)."""
    out, vide = [], 0
    for i in range(d17, n):
        vide += GAP[i] if i > d17 else 0
        if T[i]:
            if vide: out.append(vide)
            vide = 0
        else:
            vide += 1
    if vide: out.append(vide)
    return out


def mesurer(tr, limite=1000.0, cap=0.0, frein=750.0):
    R0, D0 = jours_de(tr, limite, cap, 1.0); R1, D1 = jours_de(tr, limite, cap, 0.5)
    js = {t[0] for t in tr}; T = np.array([s in js for s in B.test])
    departs = list(range(d17, n, 20)); vs = [vie_contrat(R0, D0, R1, D1, T, i0, frein) for i0 in departs]
    N = len(vs); cpt = lambda c: sum(v["issue"] == c for v in vs) / N
    j1 = [v["j1"] for v in vs if v["j1"] is not None]; j3 = [v["j3"] for v in vs if v["j3"] is not None]
    fd = [v["funded"] for v in vs if v["funded"] and v["funded"]["issue"] != "données finies"]
    pertes = sorted({v["fin"] for v in vs if v["issue"] in ("plancher", "inactivité")})
    sv = series(T); jw = R0[FEN]
    m = dict(departs=N, trois=cpt("3 retraits"), plancher=cpt("plancher"), inactivite=cpt("inactivité"), en_cours=cpt("en cours"),
             perdus=cpt("plancher") + cpt("inactivité"), episodes=len(pertes), dates_pertes=[jours[i] for i in pertes],
             med_j1=float(np.median(j1)) if j1 else None, med_j3=float(np.median(j3)) if j3 else None,
             touche_master=float(np.mean([v["touche_m"] for v in vs])),
             funded_n=len(fd), funded_perdu=float(np.mean([f["issue"] in ("plancher", "inactivité") for f in fd])) if fd else None,
             funded_touche=float(np.mean([f["touche"] for f in fd])) if fd else None,
             series5=int(sum(k >= 5 for k in sv)), plus_longue=int(max(sv) if sv else 0),
             par_seance=float(jw.mean()), t=BT.tst(jw), seances_tradees=float(T[FEN].mean()),
             survie_60=None, net_an=None, grilles_an=None)
    return R0 * FEN, m


def resume(nom, m):
    f = lambda x: "—" if x is None else f"{x:.0f}"
    return (f"{nom} : {m['trois']:.0%} des Masters atteignent le 3e retrait, {m['perdus']:.0%} perdus avant ({m['plancher']:.0%} par le plancher, "
            f"{m['inactivite']:.0%} par l'inactivité ; {m['episodes']} jours de perte distincts), {m['en_cours']:.0%} en cours à la fin ; "
            f"1er retrait en {f(m['med_j1'])} séances, 3e en {f(m['med_j3'])} (médianes) ; tu touches {m['touche_master']:,.0f} $ par Master en moyenne ; "
            f"funded : {'—' if m['funded_perdu'] is None else format(m['funded_perdu'], '.0%')} perdus dans l'année, "
            f"{'—' if m['funded_touche'] is None else format(m['funded_touche'], ',.0f')} $ touchés dans l'année ; "
            f"séries de 5 jours sans trade : {m['series5']} (la plus longue {m['plus_longue']})").replace(",", " ")


def ligne(ident, nom, j, coul, m, statut, raison=""):
    Lg = DX.ligne(ident, nom, statut, coul)
    Lg["courbe"] = [round(float(v), 1) for v in np.cumsum(j)[::PAS]]; Lg["stats"] = m; Lg["raison"] = raison
    Lg["tri"] = (2 if statut == "retenu" else -2 if statut == "tué" else 0) + m["trois"] - m["perdus"]
    DX.maj(relief=True, curseur=len(Lg["courbe"]) - 1)


T2, f2 = secours(ZF, (C2,))
DX.dire(f"Secours du même bot (T2) : {f2} jours où la zone tourne sans filtres après 3 jours sans trade, sur 2014 - 2026.", "c")
CANDIDATS = (("T0", "T0 · ton bot tel qu'il est réglé (limite 1 000 $, frein, sans plafond)", ZF, 1000.0, 0.0, 750.0, "#5ad1c8"),
             ("T1", "T1 · T0 avec un plafond du jour de 500 $", ZF, 1000.0, 500.0, 750.0, "#90e0ef"),
             ("T2", "T2 · T0 + secours du même bot après 3 jours sans trade", T2, 1000.0, 0.0, 750.0, "#f9c74f"),
             ("T3", "T3 · T2 avec un plafond du jour de 500 $", T2, 1000.0, 500.0, 750.0, "#f4a261"))
RES = {}
for k, (ident, nom, tr, lim, cap, fr_, coul) in enumerate(CANDIDATS):
    DX.maj(force=True, progression=0.05 + 0.15 * k, phase=f"Vague 10 : {nom}", detail="un Master neuf toutes les 20 séances, puis le funded")
    j, m = mesurer(tr, lim, cap, fr_); RES[ident] = dict(nom=nom, **m)
    ligne(ident, nom, j, coul, m, "en cours"); DX.dire(resume(nom, m), "c"); time.sleep(0.2)

INFO = {}
DX.maj(force=True, progression=0.65, phase="Vague 10 : pour information", detail="limite 400 $, sans frein, W1 en secours")
for ident, nom, tr, lim, cap, fr_ in (("I400", "T0 avec une limite du jour de 400 $", ZF, 400.0, 0.0, 750.0),
                                      ("Isf", "T0 sans frein", ZF, 1000.0, 0.0, 0.0)):
    j, m = mesurer(tr, lim, cap, fr_); INFO[ident] = dict(nom=nom, **m)
    ligne(ident, "information · " + nom, j, "#8d8d95", m, "référence"); DX.dire("Pour information, " + resume(nom, m), "c")
ST = sorted(BT.supertrend(B), key=lambda t: (t[0], t[2]))
X, y, an = W.variables_prod(B, ST); p = W.probas(X, y, an); W1, _ = W.tri(ST, p, y, an)
K1c, fk = secours(ZF, (W1, ST), 3, True)
j, m = mesurer(K1c, 1000.0, 0.0, 750.0); INFO["K1c"] = dict(nom="K1c · W1 après 3 jours sans trade (limite 1 000 $)", **m)
ligne("K1c", "information · K1c, W1 en secours après 3 jours", j, "#b48cff", m, "référence"); DX.dire("Pour information, " + resume("K1c (W1 en secours)", m), "c")

# ------------------------------------------------------------------ regle de choix (VAGUE10.md)
conf = [c for c in ("T0", "T1", "T2", "T3") if RES[c]["series5"] == 0 and RES[c]["inactivite"] == 0]
for c in RES:
    RES[c]["conforme"] = c in conf
    if c not in conf:
        RES[c]["raisons"] = [f"{RES[c]['series5']} séries de 5 jours de trading sans trade (la plus longue {RES[c]['plus_longue']}) : "
                             f"{RES[c]['inactivite']:.0%} des Masters perdus par l'inactivité"]
    else:
        RES[c]["raisons"] = []
choix = None
if conf:
    choix = conf[0]
    for c in conf[1:]:
        a, b = RES[choix], RES[c]
        if a["perdus"] - b["perdus"] >= 0.05 and max(a["episodes"], b["episodes"]) >= 3:     # l'ecart doit reposer sur au moins 3 jours de perte distincts
            choix = c
    base = {"T1": "T0", "T3": "T2"}.get(choix)
    if base in conf:                                                  # le plafond doit raccourcir d'au moins 15 % sans couter plus de 2 points
        a, b = RES[base], RES[choix]
        if not (a["med_j3"] and b["med_j3"] and b["med_j3"] <= 0.85 * a["med_j3"] and b["perdus"] <= a["perdus"] + 0.02):
            choix = base
    sans = {"T0": "T1", "T2": "T3"}.get(choix)                        # le plafond gagne-t-il contre la meme version sans plafond ?
    if sans in conf:
        a, b = RES[choix], RES[sans]
        if a["med_j3"] and b["med_j3"] and b["med_j3"] <= 0.85 * a["med_j3"] and b["perdus"] <= a["perdus"] + 0.02:
            choix = sans
for c in RES:
    RES[c]["retenu"] = c == choix
    for Lg in DX.e["lignes"]:
        if Lg["id"] == c:
            Lg["statut"] = "retenu" if c == choix else ("tué" if not RES[c]["conforme"] else "en cours"); Lg["raison"] = "; ".join(RES[c]["raisons"])
DX.dire("Vague 10 : " + (f"{choix} retenu ({RES[choix]['nom']})." if choix else "aucun réglage du bot seul ne tient la règle d'inactivité du contrat : "
                         "il lui faut une seconde stratégie, à faire accepter par Bulenox."), "a")
json.dump(dict(tests=RES, information=INFO, choix=choix, jours_secours_T2=f2, jours_secours_K1c=fk), open(os.path.join(DOSSIER, "vague10.json"), "w"), default=float,
          ensure_ascii=False)
DX.maj(relief=True, force=True, progression=1.0, phase="Vague 10 terminée", detail="4 candidats, 3 informations", fini=True)
DX.dire("Vague 10 terminée.", "a")
