#!/usr/bin/env python3
"""Assemble le labo : page_v3.html + donnees du Monte Carlo (montecarlo/donnees_v2.json, moteur_jour.js) + robustesse.json
-> labo_bulenox.html."""
import json
from pathlib import Path

ICI = Path(__file__).resolve().parent
MC = ICI.parent / "montecarlo"


def main():
    sur = lambda t: t.replace("</", "<\\/")                                          # noqa: E731
    mc = json.loads((MC / "donnees_v2.json").read_text())
    moteur = (MC / "moteur_jour.js").read_text().replace("if (typeof module", "if (false && typeof module")
    page = (ICI / "page_v3.html").read_text()
    page = page.replace("/*MOTEUR*/", moteur).replace("/*DONNEES*/", sur(json.dumps(mc, separators=(",", ":"), ensure_ascii=False)))
    page = page.replace("/*ROBUSTESSE*/", sur((ICI / "robustesse.json").read_text()))
    (ICI / "labo_bulenox.html").write_text(page)
    print(f"labo_bulenox.html : {len(page) / 1e6:.2f} Mo")


if __name__ == "__main__":
    main()
