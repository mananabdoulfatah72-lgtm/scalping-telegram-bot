#!/usr/bin/env python3
"""Fige l'arene (page + etat + relief) en une seule page publiable : les donnees sont integrees, la page les relit comme en direct."""
import re
import sys
from pathlib import Path

ici = Path(__file__).resolve().parent
dossier, sortie = Path(sys.argv[1]), Path(sys.argv[2])
html = (ici / "index.html").read_text()
tete = re.search(r"<head>(.*)</head>", html, re.S).group(1)
corps = re.search(r"<body>(.*)</body>", html, re.S).group(1)
tete = re.sub(r'<meta charset="utf-8">\s*<meta name="viewport"[^>]*>', '<meta name="claude:viewport-fit-sides" content="cover">', tete)
tete = tete.replace("max(12px, env(safe-area-inset-right, 0px))", "max(16px, env(safe-area-inset-right, 0px))").replace("max(12px, env(safe-area-inset-left, 0px))", "max(16px, env(safe-area-inset-left, 0px))")
tete = tete.replace("padding: env(safe-area-inset-top, 0px) max(16px", "padding: 0 max(16px")
fige = lambda n: (dossier / n).read_text().replace("</", "<\\/")
injecte = (f'<script type="application/json" id="etat-fige">{fige("etat.json")}</script>\n'
           f'<script type="application/json" id="relief-fige">{fige("relief.json")}</script>\n'
           '<script>const _F = { "etat.json": document.getElementById("etat-fige").textContent, "relief.json": document.getElementById("relief-fige").textContent };\n'
           'window.fetch = async u => { const k = String(u).split("?")[0]; return { ok: k in _F, json: async () => JSON.parse(_F[k]) }; };</script>\n')
corps = corps.replace('<script src="https://cdnjs.cloudflare.com', injecte + '<script src="https://cdnjs.cloudflare.com', 1)
sortie.write_text(tete.strip() + "\n" + corps.strip() + "\n")
print(sortie, sortie.stat().st_size // 1024, "Ko")
