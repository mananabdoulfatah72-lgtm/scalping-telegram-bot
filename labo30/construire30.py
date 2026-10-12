#!/usr/bin/env python3
"""Labo 30 jours : insere donnees30.json dans page30.html et ecrit labo_30_jours.html."""
from pathlib import Path

ICI = Path(__file__).resolve().parent
page = (ICI / "page30.html").read_text()
donnees = (ICI / "donnees30.json").read_text().replace("</", "<\\/")
assert "/*DONNEES*/" in page
(ICI / "labo_30_jours.html").write_text(page.replace("/*DONNEES*/", donnees))
print(f"labo_30_jours.html : {len(page) + len(donnees):,} octets")
