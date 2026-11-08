#!/usr/bin/env python3
"""Arene, etape 2 (ml/arene/VARIANTES.md, regles fixees avant calcul) : 219 variantes des trois bots, chacune rejouee minute
par minute avec les regles du compte finance, tuee en direct si elle rate un test ; puis l'usine en marche avant
(2017 - 2026) qui ne choisit chaque annee que sur le passe."""
import itertools
import json
import os
import sys
import time

import numba as nb
import numpy as np
from scipy import stats

import bots as BT
from direct import Direct

DOSSIER = sys.argv[1]
DX = Direct(DOSSIER)
etat = json.load(open(os.path.join(DOSSIER, "etat.json")))
DX.e.update({k: etat[k] for k in ("lignes", "journal", "jours", "pied")})
DX.e["version"] = etat["version"] + 1; DX.e["version_relief"] = etat["version_relief"] + 1
DX.maj(force=True, phase="Étape 2 : préparation des variantes", detail="lecture des minutes et des trades des trois bots", progression=0.0, fini=False)
DX.dire("Étape 2 : je prépare 219 variantes des trois bots (règles écrites avant le calcul : ml/arene/VARIANTES.md).", "a")
B = BT.Base(os.environ["CACHE_DOSSIER"])
X = B.X; ATR = X["I"]["atr"]; RANG = X["F"][:, 7]
PAS = 5; n = len(B.test); aj = B.an[B.test]


@nb.njit(cache=True)
def stop_trades(ts, tsens, tm0, tm1, te, tx, O, H, L, niv_atr):
    m1 = tm1.copy(); x = tx.copy()
    for k in range(len(ts)):
        s, sens, e = ts[k], tsens[k], te[k]
        niv = e - sens * niv_atr[k]
        for m in range(tm0[k], tm1[k] + 1):
            if m > tm0[k] and (O[s, m] - niv) * sens <= 0:
                x[k] = O[s, m]; m1[k] = m; break
            pire = L[s, m] if sens > 0 else H[s, m]
            if (pire - niv) * sens <= 0:
                x[k] = niv - sens * 0.25; m1[k] = m; break
    return m1, x


def bougie_avant(s, m0):
    return s * 26 + m0 // 15 - 1                      # derniere bougie de 15 min terminee avant l'entree


def variante(base, heures, calme, stop, pause):
    t = [r for r in base if (heures != "10h" or r[2] >= 30) and (heures != "15h" or r[2] <= 330)]
    if calme == "évité":
        t = [r for r in t if not (np.isfinite(RANG[bougie_avant(r[0], r[2])]) and RANG[bougie_avant(r[0], r[2])] < 0.33)]
    if stop and t:
        a = lambda k, ty: np.array([r[k] for r in t], dtype=ty)
        niv = np.array([1.5 * ATR[bougie_avant(r[0], r[2])] for r in t]); niv = np.where(np.isfinite(niv), niv, 1e9)
        m1, x = stop_trades(a(0, np.int64), a(1, np.int64), a(2, np.int64), a(3, np.int64), a(4, np.float64), a(5, np.float64), B.O, B.H, B.L, niv)
        t = [(r[0], r[1], r[2], int(m1[k]), r[4], float(x[k])) for k, r in enumerate(t)]
    if pause and t:
        t = sorted(t, key=lambda r: (r[0], r[2]))
        pnl = [r[1] * (r[5] - r[4]) * 2 * 28500 / r[4] - 3 for r in t]
        garde = []
        for k, r in enumerate(t):
            if k < 20 or sum(pnl[k - 20:k]) >= 0:
                garde.append(r)
        t = garde
    return t


def tst(v):
    return float(v.mean() / v.std(ddof=1) * np.sqrt(len(v))) if len(v) > 2 and v.std() > 0 else 0.0


_compte = BT._compte


@nb.njit(cache=True)
def grilles60(res, dip, horizon):
    n = len(res); out = np.zeros(max(0, n - horizon), np.bool_)
    for i0 in range(n - horizon):
        g, pr, mb = _compte(res, dip, i0, horizon)
        out[i0] = g >= 0
    return out


def profil(res, dip, res6):
    j, d, j6 = res[B.test], dip[B.test], res6[B.test]
    cum = np.cumsum(j)
    gr60 = grilles60(j, d, 60)
    retire, nret, grilles = BT._vie(j, d, 2600.0, 20)
    ans = [y for y in range(2014, 2027)]
    pos = sum(j[aj == y].sum() > 0 for y in ans)
    t = tst(j)
    per = np.array([B.J[s] >= "2026-08-11" for s in B.test])
    return dict(j=j, d=d, j6=j6, gr60=gr60, m=dict(par_seance=float(j.mean()), t=t, p=float(1 - stats.t.cdf(t, n - 1)), t_avant=tst(j[aj <= 2022]), t_apres=tst(j[aj >= 2023]),
                t_frais6=tst(j6), annees_pos=int(pos), survie_60=float(1 - gr60.mean()), retire_an=retire / (n / 252), grilles=int(grilles), retraits=int(nret),
                pire_baisse=float((cum - np.maximum.accumulate(cum)).min()), periode=float(j[per].sum())))


# ------------------------------------------------------------------ les bots de base
BOTS = [("st", "Supertrend", BT.supertrend), ("zone", "Bot 3 en 1", BT.zone), ("xgb", "XGBoost", BT.xgboost)]
base_tr, base_p = {}, {}
for ident, nom, f in BOTS:
    base_tr[ident] = f(B)
    r, d, _ = BT.journees(B, base_tr[ident], 1, 400.0); r6, _, _ = BT.journees(B, base_tr[ident], 1, 400.0, 6.0)
    base_p[ident] = profil(r, d, r6)
DX.dire("Les trois bots de base sont prêts ; chaque variante sera comparée à son bot.", "c")

GRILLE = list(itertools.product((200.0, 300.0, 400.0), (False, True), ("toutes", "10h", "15h"), ("tradé", "évité"), (False, True)))
TOUS = [(ident, nom) + g for ident, nom, _ in BOTS for g in GRILLE] + [("asm", a + " + " + b, x, y) for (x, a), (y, b) in
        itertools.combinations([("st", "Supertrend"), ("zone", "Bot 3 en 1"), ("xgb", "XGBoost")], 2)]
COUL = {"st": "#3cc8ff", "zone": "#b48cff", "xgb": "#ffa028", "asm": "#2fd16f"}
profils, noms = {}, {}


def code(v):
    if v[0] == "asm":
        return f"asm-{v[2]}-{v[3]}", f"{v[1]} (même compte)"
    ident, nom, lim, stop, heures, calme, pause = v
    c = f"{ident}-{int(lim)}-{int(stop)}-{heures}-{calme}-{int(pause)}"
    lib = f"{nom} · {int(lim)} $" + (" · stop 1,5 ATR" if stop else "") + ({"10h": " · après 10 h", "15h": " · avant 15 h"}.get(heures, "")) + (" · sans marché calme" if calme == "évité" else "") + (" · pause" if pause else "")
    return c, lib


def jugement(m, ref):
    """Regles 2 a 6 (la regle 1 avec la correction de Benjamini-Hochberg est appliquee quand toutes sont calculees)."""
    if m["t"] < 2.0: return "t sur 2014 - 2026 sous 2"
    if m["t_avant"] <= 0 or m["t_apres"] <= 0: return "négative sur une des deux moitiés"
    if m["t_frais6"] < 1.5: return "ne tient pas avec 6 $ de frais"
    if m["annees_pos"] < 9: return f"seulement {m['annees_pos']} années positives sur 13"
    if m["survie_60"] < ref["survie_60"] - 1e-9: return f"survie à 60 séances {m['survie_60']:.0%}, moins que son bot ({ref['survie_60']:.0%})"
    if m["grilles"] > ref["grilles"]: return f"{m['grilles']} comptes grillés, plus que son bot ({ref['grilles']})"
    if m["pire_baisse"] < 1.25 * ref["pire_baisse"]: return "pire baisse trop profonde"
    return None


debut = time.time()
for k, v in enumerate(TOUS):
    c, lib = code(v)
    if v[0] == "asm":
        x, y = v[2], v[3]
        rx, dx_, _ = BT.journees(B, base_tr[x], 1, 200.0); ry, dy, _ = BT.journees(B, base_tr[y], 1, 200.0)
        rx6, _, _ = BT.journees(B, base_tr[x], 1, 200.0, 6.0); ry6, _, _ = BT.journees(B, base_tr[y], 1, 200.0, 6.0)
        P = profil(rx + ry, dx_ + dy, rx6 + ry6)
        ref = max((base_p[x]["m"], base_p[y]["m"]), key=lambda m: m["survie_60"])
    else:
        ident, nom, lim, stop, heures, calme, pause = v
        t = variante(base_tr[ident], heures, calme, stop, pause)
        r, d, _ = BT.journees(B, t, 1, lim); r6, _, _ = BT.journees(B, t, 1, lim, 6.0)
        P = profil(r, d, r6); ref = base_p[ident]["m"]
    profils[c] = P; noms[c] = lib
    m = P["m"]; raison = jugement(m, ref)
    L = DX.ligne(c, lib, "tué" if raison else "en cours", COUL[v[0]])
    L["courbe"] = [round(float(x), 1) for x in np.cumsum(P["j"])[::PAS]]; L["stats"] = m; L["raison"] = raison or ""
    L["tri"] = (-1 if raison else 1) + m["survie_60"] - m["grilles"] / 100 + m["retire_an"] / 1e6
    if raison:
        DX.dire(f"tuée : {lib} — {raison}.", "b")
    else:
        DX.dire(f"en vie : {lib} — {m['retire_an']:,.0f} $ retirés par an, {m['grilles']} comptes grillés, survie 60 j {m['survie_60']:.0%}.".replace(",", " "), "h")
    DX.maj(relief=True, phase=f"Étape 2 : variante {k + 1} sur {len(TOUS)}", detail=lib, progression=(k + 1) / len(TOUS) * 0.7, curseur=len(L["courbe"]) - 1)

# ------------------------------------------------------------------ regle 1 : t >= 2 et Benjamini-Hochberg sur les 219
cs = list(profils); pv = np.array([profils[c]["m"]["p"] for c in cs]); o = np.argsort(pv)
ok = pv[o] <= 0.05 * np.arange(1, len(pv) + 1) / len(pv); kk = np.nonzero(ok)[0].max() + 1 if ok.any() else 0
bh = set(cs[i] for i in o[:kk])
for L in DX.e["lignes"]:
    if L["id"] in profils and L["statut"] != "tué" and L["id"] not in bh:
        L["statut"] = "tué"; L["raison"] = "ne survit pas à la correction des tests multiples"; L["tri"] -= 2
        DX.dire(f"tuée par la correction des tests multiples : {L['nom']}.", "b")
vivantes = [L for L in DX.e["lignes"] if L["id"] in profils and L["statut"] != "tué"]
for L in vivantes:
    L["statut"] = "retenu"
DX.dire(f"Sur 219 variantes, {len(vivantes)} passent tous les tests sur 2014 - 2026. Mais elles ont été choisies en regardant l'historique : "
        "je fais maintenant le vrai test, l'usine en marche avant.", "a")
DX.maj(relief=True, force=True, phase="Étape 2 : l'usine en marche avant", detail="chaque année, choix sur le passé seulement", progression=0.72)


# ------------------------------------------------------------------ l'usine en marche avant : 2017 - 2026
def prefixe(P, fin, refm):
    """Regles 1 a 6 et retire par an, sur les seances [0, fin) seulement."""
    j, d, j6, g60 = P["j"][:fin], P["d"][:fin], P["j6"][:fin], P["gr60"]
    t = tst(j); h = fin // 2
    ans = sorted(set(aj[:fin])); pos = sum(j[aj[:fin] == y].sum() > 0 for y in ans)
    sv = 1 - g60[:max(1, fin - 60)].mean()
    retire, nret, gr = BT._vie(j, d, 2600.0, 20)
    cum = np.cumsum(j); dd = (cum - np.maximum.accumulate(cum)).min()
    m = dict(t=t, p=float(1 - stats.t.cdf(t, fin - 1)), ok2=tst(j[:h]) > 0 and tst(j[h:]) > 0, t6=tst(j6), pos=pos / len(ans), survie=sv, grilles=gr,
             retire=retire / (fin / 252), dd=dd)
    if refm is None:
        return m, True
    vit = t >= 2 and m["ok2"] and m["t6"] >= 1.5 and m["pos"] >= 9 / 13 and sv >= refm["survie"] - 1e-9 and gr <= refm["grilles"] and dd >= 1.25 * refm["dd"]
    return m, vit


usines = {f: dict(j=np.zeros(n), d=np.zeros(n), choix={}) for f in ("st", "zone", "xgb", "toutes")}
debut17 = int(np.argmax(aj >= 2017))
for Y in range(2017, 2027):
    fin = int(np.argmax(aj >= Y)); sel = (aj == Y)
    refs = {i: prefixe(base_p[i], fin, None)[0] for i in ("st", "zone", "xgb")}
    cand = {}
    for c in cs:
        fam = c.split("-")[0] if not c.startswith("asm") else "asm"
        refm = refs[fam] if fam != "asm" else max((refs[c.split("-")[1]], refs[c.split("-")[2]]), key=lambda m: m["survie"])
        m, vit = prefixe(profils[c], fin, refm)
        if vit:
            cand[c] = (fam, m)
    # Benjamini-Hochberg sur le passe
    if cand:
        cc = list(cand); pv = np.array([cand[c][1]["p"] for c in cc]); o = np.argsort(pv)
        okk = pv[o] <= 0.05 * np.arange(1, len(pv) + 1) / len(cs); kk = np.nonzero(okk)[0].max() + 1 if okk.any() else 0
        cand = {cc[i]: cand[cc[i]] for i in o[:kk]}
    for f in usines:
        pool = {c: v for c, v in cand.items() if f == "toutes" or v[0] == f}
        if pool:
            choix = max(pool, key=lambda c: (pool[c][1]["retire"], pool[c][1]["survie"]))
        else:
            choix = f if f != "toutes" else max(("st", "zone", "xgb"), key=lambda i: refs[i]["retire"])
        P = profils.get(choix) or base_p[choix]
        usines[f]["j"][sel] = P["j"][sel]; usines[f]["d"][sel] = P["d"][sel]; usines[f]["choix"][Y] = noms.get(choix, {"st": "Supertrend (base)", "zone": "Bot 3 en 1 (base)", "xgb": "XGBoost (base)"}.get(choix, choix))
        DX.dire(f"{Y} — usine {({'st': 'Supertrend', 'zone': 'Bot 3 en 1', 'xgb': 'XGBoost', 'toutes': 'globale'})[f]} : choisie sur 2014 - {Y - 1} seulement → {usines[f]['choix'][Y]}.", "c")
    DX.maj(force=True, curseur=int(np.argmax(aj >= Y)) // PAS, progression=0.72 + 0.25 * (Y - 2016) / 10, detail=f"année {Y} jouée avec les choix faits sur 2014 - {Y - 1}")
    time.sleep(0.3)

# comparaison 2017 - 2026 : usines contre bots de base, sur la meme fenetre
def bilan17(j, d):
    jj, dd = j[debut17:], d[debut17:]
    retire, nret, gr = BT._vie(jj, dd, 2600.0, 20)
    g60 = grilles60(jj, dd, 60)
    return dict(par_seance=float(jj.mean()), t=tst(jj), retire_an=retire / (len(jj) / 252), grilles=int(gr), survie_60=float(1 - g60.mean()))


resultat = {}
for f, nomf, base in (("st", "Supertrend", "st"), ("zone", "Bot 3 en 1", "zone"), ("xgb", "XGBoost", "xgb"), ("toutes", "globale", None)):
    u = bilan17(usines[f]["j"], usines[f]["d"])
    refs = {i: bilan17(base_p[i]["j"], base_p[i]["d"]) for i in ("st", "zone", "xgb")}
    ref = refs[base] if base else max(refs.values(), key=lambda m: m["retire_an"] - 1000 * m["grilles"])
    gagne = u["retire_an"] > ref["retire_an"] and u["grilles"] <= ref["grilles"]
    resultat[f] = dict(usine=u, base=ref, adoptee=bool(gagne), choix=usines[f]["choix"])
    L = DX.ligne(f"usine-{f}", f"Usine {nomf} (marche avant)", "retenu" if gagne else "tué", "#ffffff")
    cum = np.cumsum(np.r_[np.zeros(debut17), usines[f]["j"][debut17:]])
    L["courbe"] = [round(float(x), 1) for x in cum[::PAS]]; L["stats"] = dict(par_seance=u["par_seance"], t=u["t"], survie_60=u["survie_60"], retire_an=u["retire_an"], grilles=u["grilles"])
    L["raison"] = "" if gagne else "ne bat pas le bot de base hors échantillon"; L["tri"] = 3 if gagne else -3
    DX.dire(f"Usine {nomf}, hors échantillon 2017 - 2026 : {u['retire_an']:,.0f} $ retirés par an, {u['grilles']} comptes grillés (bot de base : "
            f"{ref['retire_an']:,.0f} $ et {ref['grilles']}) → {'ADOPTÉE' if gagne else 'pas mieux que le bot de base : variantes = ajustement au passé'}.".replace(",", " "), "h" if gagne else "b")
json.dump(dict(variantes={c: dict(nom=noms[c], **profils[c]["m"]) for c in cs}, vivantes=[L["id"] for L in vivantes], usines=resultat,
               bases={i: base_p[i]["m"] for i in base_p}), open(os.path.join(DOSSIER, "etape2.json"), "w"), default=float)
DX.maj(relief=True, force=True, phase="Étape 2 terminée", detail="variantes testées, usine en marche avant jouée", progression=1.0, fini=True)
DX.dire(f"Étape 2 terminée en {time.time() - debut:.0f} s.", "a")
