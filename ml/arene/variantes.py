#!/usr/bin/env python3
"""Arene, etape 2 (ml/arene/VARIANTES.md et son addendum) : les variantes distinctes des trois bots, rejouees minute par
minute avec les regles du compte finance, tuees en direct si elles ratent un test ; puis l'usine en marche avant
(2017 - 2026) qui ne choisit chaque annee que sur le passe. Version corrigee apres la double relecture."""
import itertools
import json
import os
import sys
import time

import numpy as np
from scipy import stats

import bots as BT
from direct import Direct

DOSSIER = sys.argv[1]
DX = Direct(DOSSIER)
etat = json.load(open(os.path.join(DOSSIER, "etat.json")))
DX.e.update({k: etat[k] for k in ("journal", "jours", "pied")})
DX.e["lignes"] = [l for l in etat["lignes"] if l.get("statut") == "référence"]
rel = json.load(open(os.path.join(DOSSIER, "relief.json")))
for l in DX.e["lignes"]:
    l["courbe"] = rel["courbes"].get(l["id"], [])
DX.e["version"] = etat["version"] + 1; DX.e["version_relief"] = etat["version_relief"] + 1
DX.maj(relief=True, force=True, phase="Étape 2 : variantes (version corrigée)", detail="préparation", progression=0.0, fini=False)
DX.dire("Étape 2, version corrigée après la double relecture : je rejoue les variantes distinctes des trois bots.", "a")
B = BT.Base(os.environ["CACHE_DOSSIER"])
PAS = 5; n = len(B.test); aj = B.an[B.test]; tst = BT.tst


def variante(base, heures, calme, stop, pause):
    t = [r for r in base if (heures != "10h" or r[2] >= 30) and (heures != "15h" or r[2] <= 330)]
    if calme == "évité":
        t = [r for r in t if not (np.isfinite(B.rang[BT.bougie_avant(r[0], r[2])]) and B.rang[BT.bougie_avant(r[0], r[2])] < 0.33)]
    if stop:
        t = BT.appliquer_stop(B, t, 1.5)
    if pause and t:
        t = sorted(t, key=lambda r: (r[0], r[2]))
        pnl = [r[1] * (r[6] - r[5]) * 2 * 28500 / r[5] - 3 for r in t]
        t = [r for k, r in enumerate(t) if k < 20 or sum(pnl[k - 20:k]) >= 0]
    return t


def profil(r, d, ntr, r6):
    m = BT.mesures(B, r, d, ntr); m["t_frais6"] = tst(r6[B.test]); m["p"] = float(1 - stats.t.cdf(m["t"], n - 1))
    return dict(j=r[B.test], d=d[B.test], j6=r6[B.test], tr=ntr[B.test] > 0, m=m)


def jouer(tr, lim=400.0):
    r, d, ntr = BT.journees(B, tr, 1, lim); r6, _, _ = BT.journees(B, tr, 1, lim, 6.0)
    return profil(r, d, ntr, r6)


BOTS = [("st", "Supertrend", BT.supertrend), ("zone", "Bot 3 en 1", BT.zone), ("xgb", "XGBoost", BT.xgboost)]
HEURES = {"st": ("toutes", "10h", "15h"), "zone": ("toutes", "15h"), "xgb": ("toutes", "10h")}     # sans les reglages sans effet
base_tr, base_p = {}, {}
for ident, nom, f in BOTS:
    base_tr[ident] = f(B); base_p[ident] = jouer(base_tr[ident])
DX.dire("Les trois bots de base sont rejoués avec le moteur corrigé.", "c")

TOUS = [(ident, nom, lim, stop, h, calme, pause) for ident, nom, _ in BOTS for lim, stop, h, calme, pause in
        itertools.product((200.0, 300.0, 400.0), (False, True), HEURES[ident], ("tradé", "évité"), (False, True))]
TOUS += [("asm", f"{a} + {b}", x, y) for (x, a), (y, b) in itertools.combinations([("st", "Supertrend"), ("zone", "Bot 3 en 1"), ("xgb", "XGBoost")], 2)]
COUL = {"st": "#3cc8ff", "zone": "#b48cff", "xgb": "#ffa028", "asm": "#2fd16f"}
profils, noms, fam, empreintes = {}, {}, {}, {}


def code(v):
    if v[0] == "asm":
        return f"asm-{v[2]}-{v[3]}", f"{v[1]} (même compte, limite commune 400 $)"
    ident, nom, lim, stop, h, calme, pause = v
    c = f"{ident}-{int(lim)}-{int(stop)}-{h}-{calme}-{int(pause)}"
    est_base = lim == 400.0 and not stop and h == "toutes" and calme == "tradé" and not pause
    lib = f"{nom} · {int(lim)} $" + (" · stop 1,5 ATR" if stop else "") + ({"10h": " · pas avant 10 h", "15h": " · pas après 15 h"}.get(h, "")) \
        + (" · sans marché calme" if calme == "évité" else "") + (" · pause" if pause else "") + (" (base)" if est_base else "")
    return c, lib


def jugement(m, ref):
    if m["t"] < 2.0: return "t sur 2014 - 2026 sous 2"
    if m["t_avant"] <= 0 or m["t_apres"] <= 0: return "négative sur une des deux moitiés"
    if m["t_frais6"] < 1.5: return "ne tient pas avec 6 $ de frais"
    if m["annees_pos"] < 9: return f"seulement {m['annees_pos']} années positives sur 13"
    if m["survie_60"] < ref["survie_60"] - 1e-9: return f"survie à 60 séances {m['survie_60']:.0%}, moins que son bot ({ref['survie_60']:.0%})"
    if m["grilles_an"] > ref["grilles_an"] + 1e-9: return f"{m['grilles_an']:.2f} masters grillés par an, plus que son bot ({ref['grilles_an']:.2f})"
    if m["pire_baisse"] < 1.25 * ref["pire_baisse"]: return "pire baisse trop profonde"
    return None


debut = time.time(); doublons = 0
for k, v in enumerate(TOUS):
    c, lib = code(v)
    if v[0] == "asm":
        x, y = v[2], v[3]
        tr = base_tr[x] + base_tr[y]
        r, d, ntr = BT.journees_ensemble(B, tr, 400.0); r6, _, _ = BT.journees_ensemble(B, tr, 400.0, 6.0)
        P = profil(r, d, ntr, r6)
        ref = max((base_p[x]["m"], base_p[y]["m"]), key=lambda m: m["survie_60"]); f_ = "asm"
    else:
        tr = variante(base_tr[v[0]], v[4], v[5], v[3], v[6])
        emp = (v[2], hash(tuple(tr)))
        if emp in empreintes:
            doublons += 1
            DX.dire(f"doublon écarté : {lib} donne exactement les trades de {noms[empreintes[emp]]}.", "g")
            continue
        empreintes[emp] = c
        P = jouer(tr, v[2]); ref = base_p[v[0]]["m"]; f_ = v[0]
    profils[c] = P; noms[c] = lib; fam[c] = f_
    m = P["m"]; est_base = lib.endswith("(base)")
    raison = None if est_base else jugement(m, ref)
    L = DX.ligne(c, lib, "référence" if est_base else ("tué" if raison else "en cours"), COUL[f_])
    L["courbe"] = [round(float(x), 1) for x in np.cumsum(P["j"])[::PAS]]; L["stats"] = m; L["raison"] = raison or ""
    L["tri"] = (-1 if raison else 1) + m["survie_60"] - m["grilles_an"] + m["net_an"] / 1e5
    if raison:
        DX.dire(f"tuée : {lib} — {raison}.", "b")
    elif not est_base:
        DX.dire(f"en vie : {lib} — net {m['net_an']:,.0f} $ par an, {m['grilles_an']:.2f} masters grillés par an, compte neuf grillé dans l'année {m['grille_250']:.0%}.".replace(",", " "), "h")
    DX.maj(relief=True, phase=f"Étape 2 : réglage {k + 1} sur {len(TOUS)}", detail=lib, progression=(k + 1) / len(TOUS) * 0.7, curseur=len(L["courbe"]) - 1)
    time.sleep(0.05)

cs = list(profils); pv = np.array([profils[c]["m"]["p"] for c in cs]); o = np.argsort(pv)
ok = pv[o] <= 0.05 * np.arange(1, len(pv) + 1) / len(pv); kk = np.nonzero(ok)[0].max() + 1 if ok.any() else 0
bh = set(cs[i] for i in o[:kk])
for L in DX.e["lignes"]:
    if L["id"] in profils and L["statut"] == "en cours":
        if L["id"] not in bh:
            L["statut"] = "tué"; L["raison"] = "ne survit pas à la correction des tests multiples"; L["tri"] -= 2
            DX.dire(f"tuée par la correction des tests multiples : {L['nom']}.", "b")
        else:
            L["statut"] = "retenu"
vivantes = [L["id"] for L in DX.e["lignes"] if L["id"] in profils and L["statut"] == "retenu"]
DX.dire(f"{len(cs)} réglages distincts ({doublons} doublons écartés, 3 bases) : {len(vivantes)} passent tous les tests sur 2014 - 2026, "
        f"{sum(1 for L in DX.e['lignes'] if L['id'] in profils and L['statut'] == 'tué')} sont tués. Choisis en regardant l'historique : place au vrai test, l'usine en marche avant.", "a")
DX.maj(relief=True, force=True, phase="Étape 2 : l'usine en marche avant", detail="chaque année, choix sur le passé seulement", progression=0.72)


def prefixe(P, fin):
    j, d, j6, tr = P["j"][:fin], P["d"][:fin], P["j6"][:fin], P["tr"][:fin]
    t = tst(j); h = fin // 2
    ans = sorted(set(aj[:fin])); pos = sum(j[aj[:fin] == y].sum() > 0 for y in ans)
    g60 = BT.grilles_depuis(j, d, 60)
    v = BT.vie(np.vstack([j, j, j]), np.vstack([d, d, d]), tr)
    cum = np.cumsum(j)
    return dict(t=t, p=float(1 - stats.t.cdf(t, fin - 1)), ok2=tst(j[:h]) > 0 and tst(j[h:]) > 0, t6=tst(j6), pos=pos / len(ans),
                survie=float(1 - g60.mean()), grilles_an=v["grilles_an"], net_an=v["net_an"], dd=float((cum - np.maximum.accumulate(cum)).min()))


def vit(m, ref):
    return (m["t"] >= 2 and m["ok2"] and m["t6"] >= 1.5 and m["pos"] >= 9 / 13 and m["survie"] >= ref["survie"] - 1e-9
            and m["grilles_an"] <= ref["grilles_an"] + 1e-9 and m["dd"] >= 1.25 * ref["dd"])


NOMS_F = {"st": "Supertrend", "zone": "Bot 3 en 1", "xgb": "XGBoost", "toutes": "globale"}
usines = {f: dict(j=np.zeros(n), d=np.zeros(n), tr=np.zeros(n, bool), choix={}) for f in NOMS_F}
d17 = int(np.argmax(aj >= 2017))
for Y in range(2017, 2027):
    fin = int(np.argmax(aj >= Y)); sel = aj == Y
    refs = {i: prefixe(base_p[i], fin) for i in ("st", "zone", "xgb")}
    pm = {c: prefixe(profils[c], fin) for c in cs}
    pv = np.array([pm[c]["p"] for c in cs]); o = np.argsort(pv)
    okk = pv[o] <= 0.05 * np.arange(1, len(pv) + 1) / len(pv); kk = np.nonzero(okk)[0].max() + 1 if okk.any() else 0
    bhY = set(cs[i] for i in o[:kk])
    cand = {}
    for c in cs:
        r_ = refs[fam[c]] if fam[c] != "asm" else max((refs[c.split("-")[1]], refs[c.split("-")[2]]), key=lambda m: m["survie"])
        if c in bhY and vit(pm[c], r_):
            cand[c] = pm[c]
    for f in usines:
        pool = {c: m for c, m in cand.items() if f == "toutes" or fam[c] == f}
        if pool:
            choix = max(pool, key=lambda c: (pool[c]["net_an"], pool[c]["survie"])); P = profils[choix]; lib = noms[choix]
        else:
            b0 = f if f != "toutes" else "zone"; P = base_p[b0]; lib = f"{NOMS_F[b0]} (base, aucune variante ne passe)"
        usines[f]["j"][sel] = P["j"][sel]; usines[f]["d"][sel] = P["d"][sel]; usines[f]["tr"][sel] = P["tr"][sel]; usines[f]["choix"][Y] = lib
        DX.dire(f"{Y} — usine {NOMS_F[f]} : choisie sur 2014 - {Y - 1} seulement → {lib}.", "c")
    DX.maj(force=True, curseur=int(np.argmax(aj >= Y)) // PAS, progression=0.72 + 0.25 * (Y - 2016) / 10, detail=f"année {Y} jouée avec les choix faits sur 2014 - {Y - 1}")
    time.sleep(0.3)


def bilan17(j, d, tr):
    jj, dd = j[d17:], d[d17:]
    v = BT.vie(np.vstack([j, j, j]), np.vstack([d, d, d]), tr, debut=d17)
    g60 = BT.grilles_depuis(jj, dd, 60)
    return dict(par_seance=float(jj.mean()), t=tst(jj), survie_60=float(1 - g60.mean()), **v)


resultat = {}
for f, base in (("st", "st"), ("zone", "zone"), ("xgb", "xgb"), ("toutes", "zone")):
    u = bilan17(usines[f]["j"], usines[f]["d"], usines[f]["tr"])
    ref = bilan17(base_p[base]["j"], base_p[base]["d"], base_p[base]["tr"])
    ecart = tst(usines[f]["j"][d17:] - base_p[base]["j"][d17:])
    gagne = u["net_an"] >= 1.1 * ref["net_an"] and ref["net_an"] > 0 and u["grilles_an"] <= ref["grilles_an"] + 1e-9
    resultat[f] = dict(usine=u, base=ref, t_ecart=ecart, adoptee=bool(gagne), choix=usines[f]["choix"])
    L = DX.ligne(f"usine-{f}", f"Usine {NOMS_F[f]} (marche avant)", "retenu" if gagne else "tué", "#ffffff")
    L["courbe"] = [round(float(x), 1) for x in np.cumsum(np.r_[np.zeros(d17), usines[f]["j"][d17:]])[::PAS]]
    L["stats"] = dict(par_seance=u["par_seance"], t=u["t"], survie_60=u["survie_60"], net_an=u["net_an"], grilles_an=u["grilles_an"])
    L["raison"] = "" if gagne else "ne bat pas son bot de base hors échantillon avec la marge exigée"; L["tri"] = 3 if gagne else -3
    DX.dire(f"Usine {NOMS_F[f]}, hors échantillon 2017 - 2026 : net {u['net_an']:,.0f} $ par an, {u['grilles_an']:.2f} masters grillés par an "
            f"(référence {ref['net_an']:,.0f} $ et {ref['grilles_an']:.2f}) ; écart par séance t {ecart:.2f} → "
            f"{'ADOPTÉE' if gagne else 'pas mieux que la référence : les variantes ne sont qu ajustement au passé'}.".replace(",", " "), "h" if gagne else "b")
json.dump(dict(variantes={c: dict(nom=noms[c], **profils[c]["m"]) for c in cs}, vivantes=vivantes, doublons=doublons, usines=resultat,
               bases={i: base_p[i]["m"] for i in base_p}), open(os.path.join(DOSSIER, "etape2.json"), "w"), default=float)
DX.maj(relief=True, force=True, phase="Étape 2 terminée (version corrigée)", detail="variantes testées, usine en marche avant jouée", progression=1.0, fini=True)
DX.dire(f"Étape 2 terminée en {time.time() - debut:.0f} s.", "a")
