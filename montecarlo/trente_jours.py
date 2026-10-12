#!/usr/bin/env python3
"""Bulenox depuis le 17 aout 2026 : le challenge est un achat unique valable 30 jours calendaires (Legacy Qualification
et Momentum), un reset ne prolonge pas. Le Monte Carlo (README.md) supposait un temps illimite. Ici : probabilite de
valider en 30 jours avec le moteur exact (tables.py, moteur_jour.py), pour chaque jour d'achat possible de l'histoire
(vrai calendrier, pas de tirage), et les 21 tirages du filtre. Lancer depuis ce dossier : python3 trente_jours.py."""
import numpy as np

import moteur_jour as MJ

z = np.load("tables.npz")
G, P, D, dates = z["gain"], z["pire"], z["drap"], z["jours"].astype("datetime64[D]")
N = len(dates)
REGLES = {   # objectif, perte max fin de journee, blocage du plancher, coussin du frein
    "Legacy option 2 (2 500 $, limite du jour 1 100 $)": (3000.0, 2500.0, 100.0, 1750.0),
    "Momentum EOD (2 250 $, limite du jour 1 200 $*)": (3000.0, 2250.0, 100.0, 1500.0),
}
FILTRES = {"aussi bon qu'en 2026": range(0, 10), "deux fois plus faible": range(10, 20), "aucun": range(20, 21)}
PERIODES = {"2012 - aout 2026": ("2012-01-01", "2026-08-27"), "2023 - aout 2026": ("2023-01-01", "2026-08-27"),
            "2025": ("2025-01-01", "2026-01-01"), "2026 (jan - aout)": ("2026-01-01", "2026-08-27")}
ret = np.zeros(64)


def un(r0, t, regle):
    obj, perte, bloc, frein = regle
    fin = np.searchsorted(dates, dates[r0] + np.timedelta64(30, "D"))
    lig = np.arange(r0, fin, dtype=np.int64)
    r = MJ.parcours_jour(lig, G[t], P[t], D[t], 0, frein, obj, perte, bloc, 2500.0, 100.0, 10, .4, 1000.0, 1500.0,
                         52600.0 - 50000.0, 3, ret)
    return r[0], (r[1] if r[0] == 1 else None), len(lig)


def main():
    lignes = []
    for nom_r, regle in REGLES.items():
        lignes.append(f"\n## {nom_r}\n")
        lignes.append("| Achats de | Filtre | Validé en 30 jours | Perdu | Expiré sans valider | Séances pour valider (médiane) |")
        lignes.append("|---|---|---|---|---|---|")
        for nom_p, (a, b) in PERIODES.items():
            debuts = np.nonzero((dates >= np.datetime64(a)) & (dates < np.datetime64(b)))[0]
            for nom_f, ts in FILTRES.items():
                v = p = e = 0; jours = []
                for t in ts:
                    for r0 in debuts:
                        iss, n, _ = un(r0, t, regle)
                        if iss == 1: v += 1; jours.append(n)
                        elif iss == -1: p += 1
                        else: e += 1
                tot = v + p + e
                med = f"{np.median(jours):.0f}" if jours else "-"
                lignes.append(f"| {nom_p} | {nom_f} | {100*v/tot:.0f} % | {100*p/tot:.0f} % | {100*e/tot:.0f} % | {med} |")
    sessions = [un(r0, 0, REGLES[next(iter(REGLES))])[2] for r0 in range(N - 30)]
    lignes.append(f"\nSéances dans 30 jours calendaires : médiane {np.median(sessions):.0f} (de {min(sessions)} à {max(sessions)}).")
    lignes.append("* Les tables gardent la limite du jour du bot à 1 100 $ ; Momentum autorise 1 200 $ : un peu prudent.")
    txt = "\n".join(lignes)
    open("trente_jours.txt", "w").write(txt + "\n"); print(txt)


if __name__ == "__main__":
    main()
