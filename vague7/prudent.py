#!/usr/bin/env python3
"""Reglages prudents (demande de l'utilisateur du 9 octobre 2026 : perdre le moins possible, quitte a valider plus
lentement), descriptif. Pour chaque compte et chaque bot a la plus petite taille (1x partout) : chance de reussir le
challenge du premier coup, temps pour valider, chance de perdre le compte finance dans les 12 mois, retraits par mois
d'un compte finance en vie. Chaque trade au niveau d'aujourd'hui de son jour d'entree, filtre simule aussi bon qu'en 2026
(10 tirages) et sans filtre. Ecrit prudent.txt."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "vague6"))
import vague6 as V6  # noqa: E402

W, D4, M4, U, MS = V6.W, V6.D4, V6.M4, V6.U, V6.MS
H, MOIS = 504, 21
SYSTEMES = [("LucidFlex", 4, "zone + RSI(2) de nuit sur MES"), ("LucidFlex", 0, "zone seule"),
            ("Topstep", 4, "zone + RSI(2) de nuit sur MES"), ("Topstep", 0, "zone seule"),
            ("FundedNext Legacy", 4, "zone + RSI(2) de nuit sur MES"),
            ("Static", None, "zone + RSI(2) sur MES (E4)"), ("Static", "E1", "zone seule (E1)")]


def un_achat(D, DS, b, d, compte, bot):
    """(issue, seances du challenge, finance perdu, fin du compte finance, retraits par seance x part, suivi)."""
    sv = min(H, len(D["jours"]) - d)
    if compte in V6.INTRADAY:
        e, f_, part, _ = V6.INTRADAY[compte]
        kN, kE = D4.facteurs_jour(D)
        ret = np.zeros(H)
        r = M4.parcours4(d, bot, 2.0 * kN, 5.0 * kE, ret, *b, *e, *f_, H, 1, 1, V6.SEUIL, 0.0,
                         1 if compte == "LucidFlex" else 0)
        return r[0], r[1], r[2], (r[6] if r[2] else sv), ret * part, sv
    ret = np.zeros(H)
    r = U.achat(DS, b, d, bot or "E4", plafond=500.0, h1=H, h2=H, retraits=ret, niveau="jour", activite=1)
    issue = int(r[MS.ISSUE])
    nch = int(r[MS.FIN_EVAL]) if issue != 0 else sv
    return issue, nch, bool(r[MS.PRO_PERDU] == 1), (int(r[MS.FIN_PRO]) if r[MS.PRO_PERDU] == 1 else sv), ret, sv


def resume(rows):
    iss = np.array([x[0] for x in rows])
    nch = np.array([x[1] for x in rows])
    ok, ko = iss == 1, iss == -1
    perdu12, recu, vie = [], 0.0, 0.0
    for (i, n, perdu, fin, ret, sv) in rows:
        if i != 1:
            continue
        if sv - n >= 252:
            perdu12.append(perdu and fin - n <= 252)
        recu += ret[:fin].sum()
        vie += (fin - n) / MOIS
    t = f"{np.median(nch[ok]) / MOIS:.1f} mois" if ok.any() else "-"
    q = f"{np.percentile(nch[ok], 75) / MOIS:.1f}" if ok.any() else "-"
    return (f"reussi {ok.mean():.0%} | perdu {ko.mean():.0%} | pas fini en 24 mois {1 - ok.mean() - ko.mean():.0%} |"
            f" valide en {t} (3 sur 4 en {q} mois) | finance perdu dans les 12 mois"
            f" {np.mean(perdu12):.0%} | retraits par mois en vie {recu / vie if vie else 0:,.0f} $")


def main():
    W.regler("regles")
    D = D4.charger()
    DS = W.DN.charger()
    j, nj = D["jours"], len(D["jours"])
    rho = V6.S.rho_2026()
    dd = [d for d in range(260, nj) if D["ouvert"][d] == 0][::5]
    G = {"achats 2012-2021": [d for d in dd if pd.Timestamp("2012-01-01") <= j[d] <= pd.Timestamp("2021-12-31")],
         "achats 2023 - sept. 2024": [d for d in dd if j[d] >= pd.Timestamp("2023-01-01") and d + H <= nj],
         "achats 2025 - mars 2026": [d for d in dd if pd.Timestamp("2025-01-01") <= j[d] <= pd.Timestamp("2026-03-31")]}
    scen = {"filtre aussi bon qu'en 2026 (simule)": V6.S.gardes_simules(D, rho)[:V6.TIRAGES], "sans filtre": [None]}
    L = ["Reglages prudents (taille 1x partout), chaque trade au niveau d'aujourd'hui de son jour d'entree (descriptif)",
         "compte | bot | scenario | achats | reussi | perdu | pas fini | temps pour valider | compte finance perdu dans"
         " les 12 mois | retraits par mois d'un compte finance en vie", ""]
    for compte, bot, nb in SYSTEMES:
        for sc, gardes in scen.items():
            for g, ds in G.items():
                rows = []
                for gg in gardes:
                    b = D4.base(D, gg) if compte in V6.INTRADAY else U.base(DS, gg)
                    rows += [un_achat(D, DS, b, d, compte, bot) for d in ds]
                L.append(f"{compte} | {nb} | {sc} | {g} | " + resume(rows))
                print(L[-1], flush=True)
    (ICI / "prudent.txt").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
