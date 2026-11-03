#!/usr/bin/env python3
"""Assemble station-direct.html (page servie par le relais Quantower) a partir du terminal et du moteur direct."""
import re
import sys
from pathlib import Path

T = Path(__file__).parent
tpl = (T / "terminal.tpl.html").read_text()
direct = (T / "direct_js.txt").read_text()
modele = (T / "modele_ml.json").read_text().strip()
sortie = Path(sys.argv[1]) if len(sys.argv) > 1 else T.parent / "bot3en1/Relais.Quantower/station-direct.html"


def entre(txt, a, b):
    i = txt.index(a) + len(a)
    return txt[i:txt.index(b, i)]


def fonction(nom):
    """Texte d'une fonction de premier niveau du terminal (accolades equilibrees)."""
    i = tpl.index(f"\nfunction {nom}(") + 1
    j = tpl.index("{", i); n = 0
    for k in range(j, len(tpl)):
        n += {"{": 1, "}": -1}.get(tpl[k], 0)
        if n == 0:
            return tpl[i:k + 1]
    raise ValueError(nom)


def ligne(debut):
    i = tpl.index("\n" + debut) + 1
    return tpl[i:tpl.index("\n", i)]


def patch(txt, a, b):
    assert txt.count(a) == 1, a
    return txt.replace(a, b)


css = entre(tpl, "<style>", "</style>")
css += """
/* page en direct */
.direct.vert { color: var(--hausse); border-color: var(--hausse); } .direct.vert i { background: var(--hausse); }
.direct.ambre { color: var(--ambre); border-color: var(--ambre); } .direct.ambre i { background: var(--ambre); animation: none; }
.direct.rouge { color: var(--baisse); border-color: var(--baisse); } .direct.rouge i { background: var(--baisse); animation: none; }
.reglage { color: var(--gris); font-family: var(--cond); display: inline-flex; gap: 4px; align-items: center; white-space: nowrap; }
.reglage input { width: 10ch; background: var(--panneau2); border: 1px solid var(--trait); color: var(--blanc); padding: 2px 6px; }
#d-etat { font-family: var(--cond); font-size: 12px; flex: 1 1 260px; min-width: 0; }
.flux b { font-weight: 600; }
"""

station = entre(tpl, '<section class="vue" id="v-station" hidden>', "</section>")
station = station[station.index('<div class="defileur"'):]
for a, b in [
    ("NQZ6 · 15 minutes <span>rubans EMA 8-89, Bollinger 20-2, RSI, MACD, signal ML</span>",
     "15 minutes en direct <span>EMA 8-89, Bollinger, RSI, MACD, ML recalculés à chaque transaction</span>"),
    ("Ruban EMA lumineux <span>s'élève avec le prix</span>", "Ruban EMA lumineux <span>boule = dernier prix</span>"),
    ("Volume par prix <span>60 séances</span>", "Volume par prix <span>30 séances</span>"),
    ("Agents <span>1 MNQ</span>", "Compte et agents <span>journaux en direct</span>"),
    ("Risque <span>à l'heure du replay</span>", "Risque <span>compte réel</span>"),
    ("Ordres · papier <span>remplis à la barre suivante</span>", "Ordres · papier <span>rien n'est envoyé</span>"),
    ("Structure de la volatilité <span>amplitude des 15 min</span>", "Structure de la volatilité <span>amplitude des 15 min</span>"),
]:
    station = patch(station, a, b)

aides = entre(tpl, 'const D = JSON.parse(document.getElementById("donnees").textContent);\n', "\n\n// ----")

f = {n: fonction(n) for n in ["alertes", "scene3", "surface", "rampe3", "majFil", "evenementsSeance", "ajusterStation",
                              "chartStation", "sparkline", "jauge", "positionSt", "tape"]}
f["alertes"] = patch(f["alertes"], "if (i < 0 || i > 77) return;", "if (i < 0 || i > 77 || i >= s.barres.length) return;")
f["alertes"] = patch(f["alertes"], "`Supertrend NQ : ${sens > 0", "`règle Supertrend (calcul) : ${sens > 0")
f["evenementsSeance"] = patch(f["evenementsSeance"], "for (let b = 0; b < 26; b++) {", "for (let b = 0; b < 26 && k0 * 26 + b < NQ2.barres.length; b++) {")
f["chartStation"] = patch(f["chartStation"], "bougie(k, ...B[k].slice(0, 4));", "bougie(k, ...B[k].slice(0, 4), k === K_EN_COURS);")
f["tape"] = patch(f["tape"], '[["NQZ6", ', '[[esc(LIVE.symboles.nq || "NQ"), ')
f["tape"] = patch(f["tape"], "s.vwap[Math.max(0, Math.floor(ST.m / 5) - 1)]", "s.vwap[s.vwap.length - 1]")
f["tape"] = patch(f["tape"], "s.sens[Math.max(0, Math.floor(ST.m / 5) - 1)] > 0", "s.sens[s.sens.length - 1] > 0")
f["positionSt"] = patch(f["positionSt"], 'const fini = ST.m >= 385; ["st-achat", "st-vente", "st-plat"].forEach(id => $(id).disabled = fini || ST.m < 5);',
                        'const fini = !LIVE.ouverte || ST.m >= 385; ["st-achat", "st-vente", "st-plat"].forEach(id => $(id).disabled = fini);')

js = "\n".join(['"use strict";', aides, ligne("const EMAS = "), ligne("const coulEma = ")] + list(f.values()) + [direct])

page = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Station NQ en direct</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600;700&display=swap">
<style>{css}</style>
</head>
<body>
<div class="tete">
  <div class="barre">
    <span class="logo">NQ DIRECT</span>
    <span class="direct rouge" id="d-badge"><i></i><span>CONNEXION</span></span>
    <span class="st-horloge" id="st-horloge">—</span>
    <span class="g">symbole <b class="a" id="d-symbole">—</b></span>
    <label class="reglage" for="d-limite">limite du jour <input type="number" id="d-limite" min="50" step="50"> $</label>
    <label class="reglage" for="d-plancher">plancher <input type="number" id="d-plancher" step="100"> $</label>
    <span id="d-etat" class="g">chargement…</span>
  </div>
</div>
<section class="vue" id="v-station">
  {station}
</section>
<script type="application/json" id="modele">{modele}</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
{js}
</script>
</body>
</html>
"""
sortie.write_text(page)
print(sortie, len(page) // 1024, "Ko")
