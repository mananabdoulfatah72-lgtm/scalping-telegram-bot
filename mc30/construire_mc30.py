#!/usr/bin/env python3
"""Assemble la page du Monte Carlo 30 jours : page_mc30.html + univers_mc30.json (en-tete) + univers_mc30.bin.gz
(en base 64) -> monte_carlo_30_jours.html. Usage : python3 construire_mc30.py"""
import base64
from pathlib import Path

ICI = Path(__file__).resolve().parent
page = (ICI / "page_mc30.html").read_text()
tete = (ICI / "univers_mc30.json").read_text().replace("</", "<\\/")
b64 = base64.b64encode((ICI / "univers_mc30.bin.gz").read_bytes()).decode()
assert page.count("/*TETE*/") == 1 and page.count("/*BIN*/") == 1
sortie = ICI / "monte_carlo_30_jours.html"
sortie.write_text(page.replace("/*TETE*/", tete).replace("/*BIN*/", b64))
print(f"{sortie.name} : {sortie.stat().st_size / 1e6:.2f} Mo")
