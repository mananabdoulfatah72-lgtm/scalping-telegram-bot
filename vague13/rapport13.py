#!/usr/bin/env python3
"""Vague 13 : applique le jugement fixe a l'avance (README.md) a vague13.json et ecrit vague13.txt."""
import json
from pathlib import Path

ICI = Path(__file__).resolve().parent
R = json.loads((ICI / "vague13.json").read_text())
CH, VE, A25 = "choix 2012-2021", "verification 2023 - aout 2026", "2025"
ORDRE = "ABCFDE"
NOMS = {"A": "taille 4 (vague 12)", "B": "+ arret a l'objectif", "C": "+ arret + protection", "D": "+ arret + fin de course",
        "E": "+ arret + protection + fin de course", "F": "+ arret + prudence pres du but"}
pc = lambda x: "-" if x is None else f"{100 * x:.0f} %"                                     # noqa: E731
usd = lambda x: "-" if x is None else f"{x:+,.0f} $".replace(",", " ")                      # noqa: E731
L = []
for compte in ("legacy", "momentum"):
    L.append(f"\n## {compte}\n")
    L.append("| Candidate | Filtre | Achats | Validé | Perdu | Expiré | Séances pour valider | Net moyen 24 mois | Achats perdants |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for g in (CH, VE, A25):
        for fil in ("fort", "moitie", "aucun"):
            for l in ORDRE:
                r = R[f"{compte} | {l}"][fil][g]
                L.append(f"| {l} {NOMS[l]} | {fil} | {g} | {pc(r['valide'])} | {pc(r['perdu'])} | {pc(r['expire'])} | "
                         f"{'-' if r['seances_med'] is None else int(r['seances_med'])} | {usd(r['net_moy'])} | {pc(r['perdants'])} |")
L.append("\n## Jugement fixé à l'avance\n")
for compte in ("legacy", "momentum"):
    v = {l: R[f"{compte} | {l}"]["fort"][CH]["valide"] for l in ORDRE}
    best = max(v.values())
    ret = next(l for l in ORDRE if v[l] >= best - 0.01)
    a_ve, r_ve = R[f"{compte} | A"]["fort"][VE]["valide"], R[f"{compte} | {ret}"]["fort"][VE]["valide"]
    a_25, r_25 = R[f"{compte} | A"]["fort"][A25]["valide"], R[f"{compte} | {ret}"]["fort"][A25]["valide"]
    ok = ret != "A" and r_ve >= a_ve + 0.03 and r_25 >= a_25 - 0.01
    L.append(f"- **{compte}** : retenue {ret} ({NOMS[ret]}), validé en 30 jours sur 2012-2021 : {pc(v[ret])} "
             f"(A : {pc(v['A'])}).")
    L.append(f"  - vérification 2023 - août 2026 : {pc(r_ve)} contre {pc(a_ve)} pour A ; 2025 : {pc(r_25)} contre {pc(a_25)}"
             f" → **{'REMPLACE la version de la vague 12' if ok else 'on garde A (vague 12)'}**")
(ICI / "vague13.txt").write_text("\n".join(L) + "\n")
print("\n".join(L[-6:]))
