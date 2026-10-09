#!/usr/bin/env python3
"""Vague 4, partie A (README.md) : sur Topstep et Tradeify Growth, la zone seule contre la zone + RSI(2) adapte (A1 MES entre
deux clotures, A2 de nuit seulement MNQ, A3 de nuit seulement MES) ; reference : RSI(2) entre deux clotures MNQ.
Argent net par achat en 12 mois, niveau d'aujourd'hui. Ecrit partie_a.txt et partie_a.json."""
import json
import sys

import numpy as np
import pandas as pd

import donnees4 as D4
import moteur4 as M4

K = D4.K
sys.path.insert(0, str(D4.R0 / "intraday50k"))
sys.path.insert(0, str(D4.R0 / "static50k"))
import comptes as CP  # noqa: E402
import financee as F  # noqa: E402
import static as S  # noqa: E402

COMPTES = ("Topstep", "Tradeify Growth")
BOTS = {"zone seule": 0, "zone + RSI(2) entre deux clotures MNQ (reference)": 1, "A1 : RSI(2) entre deux clotures MES": 3,
        "A2 : RSI(2) de nuit seulement MNQ": 2, "A3 : RSI(2) de nuit seulement MES": 4}
CANDIDATES = {"A1 : RSI(2) entre deux clotures MES": False, "A2 : RSI(2) de nuit seulement MNQ": True,
              "A3 : RSI(2) de nuit seulement MES": True}           # True : regle stricte (idee venue d'un resultat vu)
TIRAGES = 5


def jouer(D, b, dd, nc, rsi):
    e, f_ = CP.COMPTES[nc][:7], F.FINANCES[nc]["f"]
    prix, mensuel, activation = F.FINANCES[nc]["prix"]
    part = F.FINANCES[nc]["part"]
    rows = []
    for d in dd:
        fn, fe = D4.facteurs(D, d)
        ret = np.zeros(M4.UN_AN)
        r = M4.parcours4(d, rsi, 2.0 * fn, 5.0 * fe, ret, *b, *e, *f_)
        mois = np.ceil(r[1] / 21.0) if mensuel else 1.0
        cout = prix * mois + (activation if r[0] == 1 else 0.0)
        rows.append((r[0], r[1], r[2], r[3], r[4] * part, r[4] * part - cout, ret * part))
    return rows


def mesures(rows):
    iss = np.array([x[0] for x in rows])
    net = np.array([x[5] for x in rows])
    recu = np.array([x[4] for x in rows])
    perdu = np.array([x[2] for x in rows])
    return {"achats": len(rows), "reussi": float((iss == 1).mean()), "retrait": float((recu > 0).mean()),
            "recu": float(recu.mean()), "net": float(net.mean()), "net_median": float(np.median(net)),
            "finance_perdu": float(perdu[iss == 1].mean()) if (iss == 1).any() else 0.0}


def ligne(nom, x):
    return (f"{nom} | {x['achats']} | {x['reussi']:.0%} | {x['retrait']:.0%} | {x['recu']:,.0f} $ | {x['net']:+,.0f} $"
            f" (mediane {x['net_median']:+,.0f}) | {x['finance_perdu']:.0%}")


def main():
    D = D4.charger()
    j, nj = D["jours"], len(D["jours"])
    b0 = D4.base(D)
    dd = [d for d in range(260, nj) if D["ouvert"][d] == 0][::5]
    G = {"choix 2012-2021": [d for d in dd if pd.Timestamp("2012-01-01") <= j[d] <= pd.Timestamp("2021-12-31")],
         "verification 2023 - sept. 2025": [d for d in dd if j[d] >= pd.Timestamp("2023-01-01") and d + M4.UN_AN <= nj],
         "2025 (descriptif)": [d for d in dd if j[d].year == 2025 and d + M4.UN_AN <= nj]}
    L = ["Vague 4, partie A : Topstep et Tradeify Growth, niveau d'aujourd'hui, 12 mois apres l'achat (prix, abonnements et"
         " activation deduits)", "",
         "compte | bot | achats | challenge reussi | au moins un retrait | retraits moyens | argent net moyen | compte"
         " finance perdu"]
    res = {}
    for nc in COMPTES:
        for g, ds in G.items():
            L.append(f"--- {nc}, {g}")
            for nb, r in BOTS.items():
                x = mesures(jouer(D, b0, ds, nc, r))
                res[f"{nc} | {nb} | {g}"] = x
                L.append(ligne(nb, x))
            print("\n".join(L[-6:]), flush=True)
    # decision (regles fixees avant le calcul)
    L += ["", "=== Decision"]
    retenues = {}
    for nc in COMPTES:
        z1 = res[f"{nc} | zone seule | choix 2012-2021"]["net"]
        z2 = res[f"{nc} | zone seule | verification 2023 - sept. 2025"]["net"]
        ok = []
        for nb, strict in CANDIDATES.items():
            c1 = res[f"{nc} | {nb} | choix 2012-2021"]["net"]
            c2 = res[f"{nc} | {nb} | verification 2023 - sept. 2025"]["net"]
            passe = c1 >= z1 + 100 and (c2 >= z2 + 100 if strict else c2 >= z2)
            L.append(f"{nc} | {nb} : {c1:+,.0f} $ / {c2:+,.0f} $ contre zone seule {z1:+,.0f} $ / {z2:+,.0f} $"
                     f" -> {'PASSE' if passe else 'non'}{' (regle stricte)' if strict else ''}")
            if passe:
                ok.append((c1, nb))
        retenues[nc] = max(ok)[1] if ok else "zone seule"
        L.append(f"=> {nc} : {retenues[nc]}")
    res["decision"] = retenues
    # descriptif : filtre delta simule sur la zone, pour la zone seule et la retenue
    rho = S.rho_2026()
    L += ["", f"=== Filtre delta simule (descriptif, rho {rho:.2f}, {TIRAGES} tirages), verification 2023 - sept. 2025"]
    for nom, rr in (("aussi bon qu'en 2026", rho), ("inutile", 0.0)):
        gardes = S.gardes_simules(D, rr)[:TIRAGES]
        for nc in COMPTES:
            for nb in sorted({"zone seule", retenues[nc]}):
                rows = sum((jouer(D, D4.base(D, g), G["verification 2023 - sept. 2025"], nc, BOTS[nb]) for g in gardes), [])
                x = mesures(rows)
                x["achats"] = len(G["verification 2023 - sept. 2025"])
                L.append(ligne(f"{nc} | {nb} | filtre {nom}", x))
    (D4.ICI / "partie_a.txt").write_text("\n".join(L) + "\n")
    (D4.ICI / "partie_a.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("\n".join(L))


if __name__ == "__main__":
    main()
