#!/usr/bin/env python3
"""Etape 8 de la recette : l'ecran Lightweight Charts. Compacte labo.json (lire.py) et l'insere dans ecran.tpl.html.
python3 ecran.py <labo.json> <sortie.html>"""
import json
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
L = json.load(open(sys.argv[1]))


def px(v):
    return None if v is None else (round(v, 2) if abs(v) >= 10 else round(v, 4))


def cap(v):
    return None if v is None else round(v)


out = {}
for a, d in L.items():
    e = {"famille": d["famille"], "verdict": d["verdict"]}
    for nom in ("fenetre", "complet"):
        r = d[nom]
        x = dict(mesures=r["mesures"], achat_conservation=r["achat_conservation"], allers_retours=r["allers_retours"],
                 transactions=[[t["date"], t["sens"][0], px(t["prix"]), round(t["quantite"], 4), round(t["frais"], 2), t["motif"]] for t in r["transactions"]],
                 jours=r["jours"], capital=[cap(v) for v in r["capital"]], capital_bh=[cap(v) for v in r["capital_bh"]],
                 stop=[px(v) for v in r["stop"]], objectif=[px(v) for v in r["objectif"]])
        if nom == "complet":
            x["bougies"] = [[b[0], *[px(v) for v in b[1:]]] for b in r["bougies"]]
            x["ema20"] = [px(v) for v in r["ema20"]]; x["ema50"] = [px(v) for v in r["ema50"]]
        e[nom] = x
    out[a] = e
page = (ICI / "ecran.tpl.html").read_text()
assert page.count("__DONNEES__") == 1
Path(sys.argv[2]).write_text(page.replace("__DONNEES__", json.dumps(out, separators=(",", ":"), allow_nan=False).replace("</", "<\\/")))
print(sys.argv[2], round(Path(sys.argv[2]).stat().st_size / 1e6, 2), "Mo")
