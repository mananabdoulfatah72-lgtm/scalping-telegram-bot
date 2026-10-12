#!/usr/bin/env python3
"""Vague 12 : applique le jugement fixe a l'avance (README.md) a vague12.json et ecrit vague12.txt."""
import json
from pathlib import Path

ICI = Path(__file__).resolve().parent
R = json.loads((ICI / "vague12.json").read_text())
CH, VE, A25 = "choix 2012-2021", "verification 2023 - aout 2026", "2025"
pc = lambda x: "-" if x is None else f"{100 * x:.0f} %"                                     # noqa: E731
usd = lambda x: "-" if x is None else f"{x:+,.0f} $".replace(",", " ")                      # noqa: E731
L = []


def ligne(nom, fil, g):
    r = R[nom][fil][g]
    return (f"| {nom} | {pc(r['valide'])} | {pc(r['perdu'])} | {pc(r['expire'])} | "
            f"{'-' if r['seances_med'] is None else int(r['seances_med'])} | {pc(r['retrait24'])} | {usd(r['net_moy'])} | "
            f"{usd(r['net_med'])} | {pc(r['perdants'])} | {pc(r['master_perdu12'])} |")


ENTETE = ("| Candidate | Validé | Perdu | Expiré / pas fini | Séances pour valider | Au moins un retrait en 24 mois | "
          "Net moyen 24 mois | Net médian | Achats perdants | Master perdu en 12 mois |\n|---|---|---|---|---|---|---|---|---|---|")
for fil, titre in (("fort", "filtre aussi bon qu'en 2026"), ("moitie", "filtre deux fois plus faible"), ("aucun", "sans filtre")):
    for g in (CH, VE, A25):
        L += [f"\n### {g} | {titre}\n", ENTETE] + [ligne(n, fil, g) for n in R]
retenues = {}
L.append("\n## Jugement fixé à l'avance\n")
for c in ("legacy", "momentum"):
    noms = [n for n in R if n.startswith(c + " |")]
    best = max(R[n]["fort"][CH]["valide"] for n in noms)
    ex = [n for n in noms if R[n]["fort"][CH]["valide"] >= best - 0.01]
    ret = min(ex, key=lambda n: int(n.split("taille ")[1][0]))
    base = f"{c} | taille 1 | frein"
    v_r, v_b = R[ret]["fort"][VE]["valide"], R[base]["fort"][VE]["valide"]
    net = R[ret]["fort"][VE]["net_moy"]
    ok = v_r >= 2 * v_b and net is not None and net > 0
    retenues[c] = ret
    L.append(f"- **{c}** : retenue « {ret} » (validé en 30 jours sur 2012-2021 : {pc(R[ret]['fort'][CH]['valide'])}, "
             f"le meilleur étant {pc(best)}).")
    L.append(f"  - vérification 2023 - août 2026 : validé {pc(v_r)} contre {pc(v_b)} pour le bot tel quel "
             f"({'au moins 2 fois' if v_r >= 2 * v_b else 'moins de 2 fois'}) ; net moyen 24 mois {usd(net)} "
             f"→ **{'VALIDÉE' if ok else 'NON VALIDÉE'}**")
L.append("\n## Comparaison finale (net moyen d'un achat sur 24 mois, prix et activation compris)\n")
L.append("| Compte | Prix payé avant de savoir | Choix 2012-2021 (fort / moitié) | Vérif. 2023 - sept. 2024 (fort / moitié) | Validé, vérif. fort | Achats perdants, vérif. fort |")
L.append("|---|---|---|---|---|---|")
prix = {"legacy": "19,25 $ (+148 $ à la réussite)", "momentum": "143 $ (85,80 $ avec -40 %)", "goat": "34,50 $",
        "flex": "69,99 $"}
comp = [retenues["legacy"], retenues["momentum"], "legacy | taille 1 | frein", "goat | taille 1 | frein",
        "goat | taille 1 | sans frein", "flex | taille 1 | zone toujours sur MES", "flex | taille 1 | zone MNQ, frein"]
for n in comp:
    c = n.split(" |")[0]
    f = lambda fil, g: usd(R[n][fil][g]["net_moy"])                                          # noqa: E731
    L.append(f"| {n} | {prix[c]} | {f('fort', CH)} / {f('moitie', CH)} | {f('fort', VE)} / {f('moitie', VE)} | "
             f"{pc(R[n]['fort'][VE]['valide'])} | {pc(R[n]['fort'][VE]['perdants'])} |")
dans_budget = [retenues["legacy"], "legacy | taille 1 | frein"]
pos = [n for n in dans_budget if (R[n]["moitie"][VE]["net_moy"] or -1) > 0 and (R[n]["moitie"][CH]["net_moy"] or -1) > 0]
L.append(f"\nRègle 4 (dans le budget, net moyen positif avec le filtre deux fois plus faible, sur les deux périodes) : "
         f"{', '.join(pos) if pos else 'aucun compte'}. Goat : compte financé non simulé, comparé sur le challenge seulement.")
(ICI / "vague12.txt").write_text("\n".join(L) + "\n")
print("\n".join(L[-22:]))
