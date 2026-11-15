#!/usr/bin/env python3
"""Assemble terminal.html : gabarit + style + donnees (data.json, comparatif.json) + moteur + interface, tout en ligne.
Usage : python3 build.py"""
import json
from pathlib import Path

ICI = Path(__file__).resolve().parent
SRC = ICI / "src"


def json_en_ligne(chemin):
    """JSON compact, sur une ligne, sans « </ » (qui fermerait la balise <script>)."""
    texte = json.dumps(json.loads(chemin.read_text(encoding="utf-8")), ensure_ascii=False, separators=(",", ":"))
    return texte.replace("</", "<\\/")


def script_en_ligne(chemin):
    texte = chemin.read_text(encoding="utf-8")
    assert "</script" not in texte.lower(), chemin
    return texte


def main():
    page = (SRC / "template.html").read_text(encoding="utf-8")
    morceaux = {
        "/*STYLE*/": (SRC / "style.css").read_text(encoding="utf-8"),
        "/*DATA*/": json_en_ligne(ICI / "data.json"),
        "/*COMPARATIF*/": json_en_ligne(ICI / "comparatif.json"),
        "/*ENGINE*/": script_en_ligne(SRC / "engine.js"),
        "/*UI*/": script_en_ligne(SRC / "ui.js"),
    }
    for cle, valeur in morceaux.items():
        assert page.count(cle) == 1, cle
        page = page.replace(cle, valeur)
    assert page.startswith("<title>Terminal Backtest Futures</title>")
    sortie = ICI / "terminal.html"
    sortie.write_text(page, encoding="utf-8")
    print(f"terminal.html : {sortie.stat().st_size / 1e6:.2f} Mo")


if __name__ == "__main__":
    main()
