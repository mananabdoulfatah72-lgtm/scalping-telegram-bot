#!/usr/bin/env python3
"""LucidFlex 50K avec le systeme retenu (zone + A3, challenge 3x, finance 2x), descriptif (demande de l'utilisateur du
9 octobre 2026) : temps pour valider, risque de perdre le challenge et le compte finance, quand arrivent les retraits.
Achats une seance sur cinq, suivis 24 mois, chaque trade au niveau d'aujourd'hui de son jour d'entree, filtre simule aussi
bon qu'en 2026 (10 tirages) et sans filtre. Ecrit lucidflex.txt."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "vague6"))
import vague6 as V6  # noqa: E402

W, D4, M4 = V6.W, V6.D4, V6.M4
H = 504                                                   # 24 mois
MOIS = 21


def achats(D, b, dd):
    e, f_, part, _ = V6.INTRADAY["LucidFlex"]
    kN, kE = D4.facteurs_jour(D)
    out = []
    for d in dd:
        ret = np.zeros(H)
        r = M4.parcours4(d, 4, 2.0 * kN, 5.0 * kE, ret, *b, *e, *f_, H, 3, 2, V6.SEUIL, 0.0, 1)
        out.append((r, ret * part, min(H, len(D["jours"]) - d)))
    return out


def resume(rows):
    iss = np.array([r[0][0] for r in rows])
    nch = np.array([r[0][1] for r in rows])
    suivi = np.array([r[2] for r in rows])
    ok, ko = iss == 1, iss == -1
    m = lambda s: f"{s / MOIS:.1f} mois"                       # noqa: E731
    L = [f"  challenge : reussi {ok.mean():.0%}, seuil de perte touche {ko.mean():.0%}, pas fini {1 - ok.mean() - ko.mean():.0%}",
         f"  temps pour valider (reussis) : 1 sur 4 en {m(np.percentile(nch[ok], 25))}, la moitie en"
         f" {m(np.median(nch[ok]))}, 3 sur 4 en {m(np.percentile(nch[ok], 75))} ; seuil touche au bout de"
         f" {m(np.median(nch[ko]))} en mediane"]
    prem, ecarts, montants, vies, perdu12, perdu24, en_vie_mois, recu = [], [], [], [], [], [], 0.0, 0.0
    for (r, ret, sv), o in zip(rows, ok):
        if not o:
            continue
        debut_fin = r[1]
        fin = r[6] if r[2] else sv                          # fin du compte finance (perdu) ou du suivi
        vie = fin - debut_fin
        vies.append((vie, r[2]))
        idx = np.flatnonzero(ret[:fin] > 0)
        if len(idx):
            prem.append(idx[0] + 1 - debut_fin)
            ecarts += list(np.diff(idx))
            montants += list(ret[idx])
        if sv - debut_fin >= 252:                           # suivi d'au moins 12 mois apres le debut du compte finance
            perdu12.append(r[2] and vie <= 252)
        if sv - debut_fin >= H - 21:
            perdu24.append(r[2])
        en_vie_mois += vie / MOIS
        recu += ret[:fin].sum()
    L += [f"  compte finance : premier retrait {m(np.median(prem))} apres la reussite en mediane (1 sur 4 :"
          f" {m(np.percentile(prem, 25))}, 3 sur 4 : {m(np.percentile(prem, 75))}) ; puis un retrait tous les"
          f" {m(np.median(ecarts))} en mediane ; retrait moyen {np.mean(montants):,.0f} $ (90 % compris)",
          f"  compte finance perdu dans les 12 mois : {np.mean(perdu12):.0%} ; dans les 24 mois : {np.mean(perdu24):.0%}"
          f" ; retraits par mois d'un compte finance en vie : {recu / en_vie_mois:,.0f} $"]
    return L


def main():
    W.regler("regles")
    D = D4.charger()
    W.G["D4"] = D
    j, nj = D["jours"], len(D["jours"])
    rho = V6.S.rho_2026()
    dd = [d for d in range(260, nj) if D["ouvert"][d] == 0][::5]
    G = {"achats 2012-2021": [d for d in dd if pd.Timestamp("2012-01-01") <= j[d] <= pd.Timestamp("2021-12-31")],
         "achats 2023 - sept. 2024 (suivis 24 mois)": [d for d in dd if j[d] >= pd.Timestamp("2023-01-01") and d + H <= nj],
         "achats 2025 - mars 2026 (suivis jusqu'au 25 sept. 2026)": [d for d in dd if pd.Timestamp("2025-01-01") <= j[d]
                                                                     <= pd.Timestamp("2026-03-31")]}
    scen = {"filtre aussi bon qu'en 2026 (simule)": V6.S.gardes_simules(D, rho)[:V6.TIRAGES], "sans filtre": [None]}
    L = ["LucidFlex 50K, zone + A3, challenge 3x (3 MNQ + 3 MES), compte finance 2x des 4 000 $ de coussin ; chaque trade"
         " au niveau d'aujourd'hui de son jour d'entree (descriptif)", ""]
    for sc, gardes in scen.items():
        for g, ds in G.items():
            rows = sum((achats(D, D4.base(D, gg), ds) for gg in gardes), [])
            L += [f"=== {sc} | {g} ({len(ds)} achats)"] + resume(rows)
            print("\n".join(L[-5:]), flush=True)
    (ICI / "lucidflex.txt").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
