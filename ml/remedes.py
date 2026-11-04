#!/usr/bin/env python3
"""Remedes contre les pertes du bot XGBoost NQ (ml/REMEDES.md, fixes avant calcul) : stop a 1 ou 1,5 ATR, pas de trade en
marche calme, les deux ; puis limite du jour. Memes signaux que le dossier (moyenne des 10 modeles, marche en avant purgee),
trades rejoues minute par minute."""
import json
import os

import numpy as np
import pandas as pd

import caracteristiques as K
import donnees as D

X = K.construire()
F, c, fut, sess, b, an, ok, J = (X[k] for k in ("F", "c", "fut", "sess", "b", "an", "ok", "J"))
ATR = X["I"]["atr"]
F = F[:, :21]
_, O, H, L, C, V, _ = D.nq_minutes()
an_j = np.array([int(j[:4]) for j in J])
utile = ok[sess] & X["meme"] & np.isfinite(F).all(1) & np.isfinite(fut)
p = np.load(os.environ.get("CACHE_DOSSIER", "dossier_p.npy"))
ev = utile & (an >= 2014)
sig0 = np.where(p > 0.55, 1, np.where(p < 0.45, -1, 0)) * ev
sess_ok = np.nonzero(ok)[0]; test_s = sess_ok[an_j[sess_ok] >= 2014]


def jouer(stop_atr=None, calme=False):
    """Trades : (seance, bougie du signal, sens, $, [(pire, meilleur) par quart d'heure])."""
    out = []; libre = -1
    for i in np.nonzero(sig0)[0]:
        if i <= libre:
            continue
        if calme and F[i, 7] < 0.33:
            continue
        s, bq, sens = sess[i], b[i], int(sig0[i])
        m0, m1 = 15 * (bq + 1), 15 * (bq + 4) + 14
        e = O[s, m0]; ech = 2 * D.PREF / e
        stop = None if stop_atr is None else e - sens * stop_atr * ATR[i]
        sortie, ms, ext = C[s, m1], m1, []
        pire = meil = 0.0
        for m in range(m0, m1 + 1):
            lo, hi = (L[s, m], H[s, m]) if sens > 0 else (H[s, m], L[s, m])
            if stop is not None:
                if m > m0 and (O[s, m] - stop) * sens <= 0:
                    sortie, ms = O[s, m], m; pire = min(pire, (sortie - e) * sens * ech); break
                if (lo - stop) * sens <= 0:
                    sortie, ms = stop - sens * 0.25, m; pire = min(pire, (sortie - e) * sens * ech); break
            pire = min(pire, (lo - e) * sens * ech); meil = max(meil, (hi - e) * sens * ech)
            if m % 15 == 14:
                ext.append((pire, meil)); pire = meil = 0.0
        ext.append((pire, meil))
        out.append((s, i, sens, sens * (sortie - e) * ech - D.FRAIS, ext))
        libre = (i + 3) if ms == m1 else s * 26 + ms // 15        # apres un stop : le signal suivant peut rouvrir
    return out


def tstat(v):
    return float(v.mean() / v.std(ddof=1) * np.sqrt(len(v)))


def mesures(T):
    usd = np.zeros(X["S"])
    for s, i, sens, u, ext in T:
        usd[s] += u
    j = usd[test_s]; aj = an_j[test_s]
    cum = np.cumsum(j); dd = cum - np.maximum.accumulate(cum)
    mois = pd.Series(j, index=pd.to_datetime([J[s] for s in test_s])).resample("ME").sum()
    serie = "".join("1" if x > 0 else "0" for x in j)
    u = np.array([t[3] for t in T])
    return dict(trades=len(T), par_seance=float(j.mean()), t=tstat(j), t_avant=tstat(j[aj <= 2022]), t_apres=tstat(j[aj >= 2023]),
                ecart=float(j.std(ddof=1)), pire_baisse=float(dd.min()), pire_mois=float(mois.min()), pire_seance=float(j.min()),
                pertes_suite=max(len(x) for x in serie.split("1")), taux=float((u > 0).mean()), sans_2020=tstat(j[aj != 2020]),
                facteur=float(u[u > 0].sum() / -u[u <= 0].sum()))


def challenge(T, debut, solde, haut, cible, limite, fin_de_journee=False):
    par = {}
    for t in T:
        par.setdefault(t[0], []).append(t)
    for n, s in enumerate([s for s in range(len(J)) if ok[s] and s >= debut]):
        jour = 0.0
        for _, _, _, res, ext in par.get(s, []):
            if jour <= -limite:
                break
            for pire, meil in ext:
                if not fin_de_journee:
                    haut = max(haut, solde + meil)
                if solde + pire <= min(haut - 2500, 50100):
                    return "echec", n + 1
            solde += res; jour += res
            if not fin_de_journee:
                haut = max(haut, solde)
            if solde >= cible:
                return "reussite", n + 1
        if fin_de_journee:
            haut = max(haut, solde)
    return "en cours", 0


departs = [s for s in range(len(J)) if ok[s] and "2023-01-01" <= J[s] <= "2026-06-30"]


def comptes(T, limite=400.0):
    r = {}
    for nom, args in (("actuel", (50000.0, 51500.0, 53050.0, limite, False)), ("neuf", (50000.0, 50000.0, 53000.0, limite, False)),
                      ("neuf, plancher fin de journée", (50000.0, 50000.0, 53000.0, limite, True))):
        iss = [challenge(T, d, *args)[0] for d in departs]
        r[nom] = dict(reussite=iss.count("reussite") / len(iss), echec=iss.count("echec") / len(iss))
    return r


CAND = {"R0 tel quel": dict(), "R1 stop 1 ATR": dict(stop_atr=1.0), "R2 stop 1,5 ATR": dict(stop_atr=1.5),
        "R3 pas de trade en marché calme": dict(calme=True), "R4 stop 1,5 ATR + pas de marché calme": dict(stop_atr=1.5, calme=True)}
res, trades = {}, {}
for nom, kw in CAND.items():
    T = jouer(**kw); trades[nom] = T
    res[nom] = dict(**mesures(T), comptes=comptes(T))
    print(nom, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in res[nom].items() if k != "comptes"}, res[nom]["comptes"], flush=True)
base = res["R0 tel quel"]
for nom, r in res.items():
    if nom == "R0 tel quel":
        r["adopte"] = None; continue
    r["conditions"] = dict(baisse_et_ecart=r["pire_baisse"] > base["pire_baisse"] and r["ecart"] < base["ecart"], t_3=r["t"] >= 3.0,
                           deux_moities=r["t_avant"] > 0 and r["t_apres"] > 0, challenge_neuf=r["comptes"]["neuf"]["reussite"] > base["comptes"]["neuf"]["reussite"])
    r["adopte"] = all(r["conditions"].values())
gagnants = [n for n, r in res.items() if r.get("adopte")]
choisi = max(gagnants, key=lambda n: res[n]["pire_baisse"]) if gagnants else "R0 tel quel"
limites = {str(int(lim)): comptes(trades[choisi], lim) for lim in (200.0, 300.0, 400.0, 800.0)}
json.dump(dict(candidats=res, choisi=choisi, limites=limites), open(D.SORTIE / "remedes.json", "w"))
txt = ["# Remèdes contre les pertes (règles fixées avant calcul : ml/REMEDES.md)\n",
       "| remède | trades | $ par séance | t | t 2014-22 | t 2023-26 | t sans 2020 | écart type | pire baisse | pire mois | pire séance | pertes d'affilée | compte actuel | compte neuf | neuf, fin de journée | adopté |",
       "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for nom, r in res.items():
    cpt = r["comptes"]
    txt.append(f"| {nom} | {r['trades']} | {r['par_seance']:+.1f} | {r['t']:.2f} | {r['t_avant']:+.2f} | {r['t_apres']:+.2f} | {r['sans_2020']:+.2f} | {r['ecart']:.0f} | "
               f"{r['pire_baisse']:+,.0f} | {r['pire_mois']:+,.0f} | {r['pire_seance']:+,.0f} | {r['pertes_suite']} | "
               f"{cpt['actuel']['reussite']:.0%} | {cpt['neuf']['reussite']:.0%} | {cpt['neuf, plancher fin de journée']['reussite']:.0%} | "
               f"{'—' if r['adopte'] is None else ('OUI' if r['adopte'] else 'non')} |")
txt.append(f"\nRetenu : **{choisi}**.\n\n## Limite du jour (avec {choisi})\n\n| limite | compte actuel | compte neuf | neuf, fin de journée |\n|---|---|---|---|")
for lim, r in limites.items():
    txt.append(f"| {lim} $ | {r['actuel']['reussite']:.0%} | {r['neuf']['reussite']:.0%} | {r['neuf, plancher fin de journée']['reussite']:.0%} |")
D.ecrire("remedes.md", "\n".join(txt) + "\n")
