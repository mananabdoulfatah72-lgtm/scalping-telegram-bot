#!/usr/bin/env python3
"""Assemble la page du terminal : terminal.tpl.html + donnees.json (prep.py) + donnees2.json (prep2.py) + donnees3.json (prep3.py).
python3 terminal/assembler.py <dossier des json> <sortie.html>"""
import sys
from pathlib import Path

T = Path(__file__).parent
dos, sortie = Path(sys.argv[1]), Path(sys.argv[2])
page = (T / "terminal.tpl.html").read_text()
for cle, f in (("__DONNEES3__", "donnees3.json"), ("__DONNEES2__", "donnees2.json"), ("__DONNEES__", "donnees.json")):
    assert page.count(cle) == 1, cle
    page = page.replace(cle, (dos / f).read_text().replace("</", "<\\/"))
sortie.write_text(page)
print(sortie, round(len(page) / 1e6, 2), "Mo")
