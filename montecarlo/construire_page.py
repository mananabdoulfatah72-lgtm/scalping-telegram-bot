#!/usr/bin/env python3
"""Assemble la page Monte Carlo : page_modele.html + mc.json -> monte_carlo_bulenox.html."""
from pathlib import Path

ICI = Path(__file__).resolve().parent
donnees = (ICI / "mc.json").read_text().replace("</", "<\\/")
page = (ICI / "page_modele.html").read_text().replace("/*DONNEES*/", donnees)
(ICI / "monte_carlo_bulenox.html").write_text(page)
print(f"monte_carlo_bulenox.html : {len(page) / 1e6:.2f} Mo")
