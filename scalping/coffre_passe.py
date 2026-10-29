#!/usr/bin/env python3
"""Coffre du passe (README.md) : les 2 candidates NQ de la version 5 sur 2011 - 2016, jamais vues ; placebos et toutes les
admises reelles du NQ pour comparaison. Ecrit resultats/v5/coffre_passe.txt.
Lancer : KB=<branche de recherche extraite> python3 scalping/coffre_passe.py"""
import json

import numpy as np

import commun as K
import moteur as M
import partie_e as E
import selection5 as SEL

d = E.jour_nq()
j = json.loads((K.ICI / "resultats" / "v5" / "candidats.json").read_text())
cst = j["candidates"][0]["constantes"]
for k in ("pt", "tick", "pas", "frais", "pref", "rond"):
    d[k] = np.float64(cst[k])
f = M.indicateurs(d)
s0 = int(np.searchsorted(d["jours"], np.datetime64("2011-01-01")))
s1 = int(np.searchsorted(d["jours"], np.datetime64("2016-12-31"), "right"))
an = d["jours"][s0:s1].astype("datetime64[Y]").astype(int) + 1970


def jouer(g):
    gain, n, w, brut, _ = M.jouer(np.asarray(g, float), f, s0, s1)
    x = gain[np.isfinite(gain)]
    x = x[x != 0]
    t = K.t_stat(x) if len(x) > 2 and x.std() > 0 else float("nan")
    par = " ".join(f"{a}:{np.nansum(gain[an == a]):+.0f}" for a in range(2011, 2017))
    return n, x.sum(), t, w / max(n, 1), par


L = [f"Coffre du passe : NQ du {d['jours'][s0]} au {d['jours'][s1 - 1]} ({s1 - s0} seances, {int(f['jouable'][s0:s1].sum())} "
     "jouables), jamais vu par les versions 4 et 5. 1 MNQ au prix d'aujourd'hui, frais d'aujourd'hui.", ""]
for x in j["candidates"]:
    if x["marche"] != "NQ":
        continue
    n, tot, t, w, par = jouer(x["genome"])
    v = "CONFIRMEE dans le passe" if (n >= 100 and t >= 1.96 and tot > 0) else ("ECARTEE" if t <= 0 else "pas de conclusion")
    L.append(f"candidate (t controle {x['t_c']:.2f}) : {n} trades, {tot:+,.0f} $, t {t:+.2f}, gagnants {w:.0%} -> {v}")
    L.append(f"    {par}")
    L.append(f"    {x['description']}")
for x in j["placebos"]:
    if x["marche"] == "NQ" and x["type"] == "placebo" and x.get("suivi"):
        n, tot, t, w, par = jouer(x["genome"])
        L.append(f"placebo ({x['sorte']}) : {n} trades, {tot:+,.0f} $, t {t:+.2f}")
runs = SEL.lire("B", "NQ", "reel")
adm = SEL.admises(runs, dedoublonner=True)
ts = []
for a in adm:
    n, tot, t, w, par = jouer(a["genome"])
    if n >= 30:
        ts.append(t)
ts = np.array(ts)
L += ["", f"Toutes les admises reelles du NQ (v5, {len(ts)} avec au moins 30 trades) sur 2011 - 2016 : t median {np.nanmedian(ts):+.2f}, "
      f"part > 0 {np.nanmean(ts > 0):.0%}, part >= 1,96 {np.nanmean(ts >= 1.96):.1%}"]
txt = "\n".join(L)
(K.ICI / "resultats" / "v5" / "coffre_passe.txt").write_text(txt + "\n")
print(txt)
