#!/usr/bin/env python3
"""Arene, vague 9, information ecrite APRES le calcul de la vague (pas une regle fixee d avance) : K1 avec un compteur sur toutes les seances du fichier (demi-journees comprises, sans trade
possible dans le rejeu), declenche apres 4 ou apres 3 jours sans trade.
MINUTES_NQ=... CACHE_DOSSIER=... python3 vague9_info.py <sortie.json>"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pathlib import Path
import bots as BT
import w1 as W
B = BT.Base(os.environ["CACHE_DOSSIER"]); C = B.C
FED = {l.strip() for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "donnees/fomc.txt")) if l.strip() and not l.startswith("#")}
INV = W.ecart_vix(B) >= 0
ZF = sorted([t for t in BT.zone(B) if not INV[t[0]] and B.J[t[0]] not in FED], key=lambda t: (t[0], t[2]))
ST = sorted(BT.supertrend(B), key=lambda t: (t[0], t[2]))
X, y, an = W.variables_prod(B, ST); p = W.probas(X, y, an); W1, garde = W.tri(ST, p, y, an)
aj = B.an[B.test]; FEN = aj >= 2017; d17 = int(np.argmax(FEN))
def par_s(tr):
    d = {}
    for t in tr: d.setdefault(t[0], []).append(t)
    return d
def un_contrat(z, autres):
    out = list(z)
    for t in autres:
        s, sens, m_in, deb, fin, e, x = t; so = fin + 1 if fin < 389 else 389
        c = next((q for q in z if m_in <= q[4] and q[2] <= so), None)
        if c is None: out.append(t)
        elif m_in <= c[2]: out.append((s, sens, m_in, deb, c[2], e, float(C[s, c[2]])))
    return out
def regle(seuil):
    zs = par_s(ZF); sec = [par_s(W1), par_s(ST)]; out = [t for t in ZF if B.an[t[0]] < 2017]; vide = 0
    for s in range(len(B.J)):
        if B.an[s] < 2017: continue
        jour = list(zs.get(s, [])) if B.ok[s] else []
        if B.ok[s] and vide >= seuil:
            for d in sec:
                if d.get(s): jour = un_contrat(jour, d[s]); break
        out += jour; vide = 0 if jour else vide + 1
    return sorted(out, key=lambda t: (t[0], t[3]))
def series(trade):
    o, k = [], 0
    for x in trade:
        if x:
            if k: o.append(k)
            k = 0
        else: k += 1
    if k: o.append(k)
    return o
res = {}
for nom, seuil in (("K1 compteur calendrier, apres 4", 4), ("K1 compteur calendrier, apres 3", 3)):
    tr = regle(seuil); r, dp, ntr = BT.journees(B, tr, 1, 400.0)
    j, dd = r[B.test], dp[B.test]; jt = {t[0] for t in tr}; tt = np.array([s in jt for s in B.test])
    v = BT.vie(np.vstack([j] * 3), np.vstack([dd] * 3), tt, debut=d17); jw, dw = j[FEN], dd[FEN]
    sv = series([s in jt for s in range(len(B.J)) if B.an[s] >= 2017])
    m = dict(series5=sum(k >= 5 for k in sv), plus_longue=max(sv), t=BT.tst(jw), par_seance=float(jw.mean()), survie_60=float(1 - BT.grilles_depuis(jw, dw, 60).mean()),
             grille_250=float(BT.grilles_depuis(jw, dw, 250).mean()), grilles_an=v["grilles_an"], net_an=v["net_an"], seances=float(tt[FEN].mean()))
    res[nom] = m; print(nom, {k: round(x, 3) if isinstance(x, float) else x for k, x in m.items()}, flush=True)
json.dump(res, open(sys.argv[1], "w"), default=float)
