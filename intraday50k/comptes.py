#!/usr/bin/env python3
"""Partie 2 (README.md) : le bot (zone seule, ou zone + RSI(2) entre deux clotures) sur les comptes 50K intraday.
Ecrit comptes.txt et comptes.json. Lancer depuis ce dossier : python3 comptes.py"""
import json

import numpy as np
import pandas as pd
from scipy.stats import norm

import commun as K
import moteur as M

# objectif, perte max, mode (1 suivi en direct, 0 fin de journee), blocage du plancher (au-dessus du depart),
# limite du jour douce (0 : aucune), regularite (0 : aucune), jours mini, seances au plus
COMPTES = {
    "Bulenox option 1 (suivi en direct)": (3000.0, 2500.0, 1, 100.0, 0.0, 0.0, 1, 252),
    "Bulenox option 2 (fin de journee)": (3000.0, 2500.0, 0, 100.0, 1100.0, 0.0, 1, 252),
    "Tradeify Growth": (3000.0, 2000.0, 0, 100.0, 1250.0, 0.0, 1, 252),
    "Tradeify Select": (3000.0, 2000.0, 0, 100.0, 0.0, 0.40, 3, 252),
    "Lucid Flex": (3000.0, 2000.0, 0, 100.0, 0.0, 0.50, 1, 252),
    "Topstep": (3000.0, 2000.0, 0, 0.0, 1000.0, 0.50, 1, 252),
    "Apex EOD (descriptif)": (3000.0, 2000.0, 0, 100.0, 0.0, 0.0, 1, 21),
}
BOTS = {"Z": 0, "Z+R": 1}
TIRAGES = 20


def lancer(departs, base, compte, avec_rsi):
    obj, perte, mode, bloc, dll, regul, jmin, nmax = compte
    out = [M.challenge(int(d), nmax, avec_rsi, *base, obj, perte, mode, bloc, dll, regul, jmin, K.P.FRAIS_ZONE,
                       K.P.FRAIS_RSI) for d in departs]
    return pd.DataFrame(out, columns=["issue", "seances", "marge", "valeur"], index=list(departs))


def bilan(r):
    ok, ko = (r["issue"] == 1).mean(), (r["issue"] == -1).mean()
    med = r.loc[r["issue"] == 1, "seances"].median()
    return {"departs": len(r), "reussis": round(100 * ok, 1), "perdus": round(100 * ko, 1),
            "pas_finis": round(100 * (1 - ok - ko), 1), "score": round(100 * (ok - ko), 1),
            "seances_mediane": None if np.isnan(med) else int(med)}


def gardes_simules(D, nj):
    """Comme filtre_h1/scenario.py : signal correle au resultat de chaque trade de zone (rho mesure en 2026), 20 % ecartes."""
    z26 = pd.read_csv(K.R0 / "orderflow" / "zone_avril_septembre_2026.csv")
    g = z26["garde"].astype(bool)
    ecart = (z26["points"][g].mean() - z26["points"][~g].mean()) / z26["points"].std()
    part = float((~g).mean())
    q = norm.ppf(part)
    rho = ecart / (norm.pdf(q) / part + norm.pdf(q) / (1 - part))
    Z, C = D["Z"], D["C"]
    d, me, ms, s = (Z[k].to_numpy() for k in ("d", "me", "ms", "sens"))
    pts = s * (C[d, ms] - C[d, me]) - K.RB.COUT
    zr = pts / pd.Series(pts).groupby(D["jours"][d].year).transform("std").to_numpy()
    rng = np.random.default_rng(7)
    return rho, [(rho * zr + np.sqrt(1 - rho ** 2) * rng.standard_normal(len(zr))) > q for _ in range(TIRAGES)]


def main():
    D = K.charger()
    j = D["jours"]
    nj = len(j)
    def base(garde):
        return (D["O"], D["H"], D["L"], D["C"], D["derniere"], *K.P.tableaux_zone(D["Z"], nj, garde), D["dec"],
                D["voulu"], D["NO"], D["NH"], D["NL"], D["nn"])
    b0 = base(np.ones(len(D["Z"]), bool))
    possibles = [d for d in range(260, nj) if D["ouvert"][d] == 0]
    departs = possibles[::K.P.PAS_DEPART]
    groupes = {"2011-2022": [d for d in departs if j[d] <= pd.Timestamp("2022-12-31")],
               "2023-2026": [d for d in departs if j[d] >= pd.Timestamp("2023-01-01")],
               "2025": [d for d in departs if j[d].year == 2025]}
    L = [f"Comptes 50K intraday, bot a 1 MNQ par source ; {nj} seances du {j[0].date()} au {j[-1].date()} ;"
         f" departs : 1 seance sur {K.P.PAS_DEPART}, RSI(2) a plat", ""]
    # gain du bot sans compte
    for nom, r in BOTS.items():
        g = M.gains_jour(r, D["O"], D["C"], D["derniere"], *b0[5:11], D["dec"], D["voulu"], D["NO"], D["nn"],
                         K.P.FRAIS_ZONE, K.P.FRAIS_RSI)
        s = pd.Series(g, index=j)
        L.append(f"bot {nom} sans compte : {s[j >= '2012-01-01'].mean():+.1f} $ par seance (2012-2026),"
                 f" {s[j >= '2023-01-01'].mean():+.1f} $ (2023-2026) ; pire seance {s.min():+,.0f} $ ;"
                 f" mois positifs {(s[j >= '2012-01-01'].resample('ME').sum() > 0).mean():.0%}")
    res = {}
    L += ["", "compte | bot | 2011-2022 : reussis / perdus / pas finis / seances (mediane) | 2023-2026 : idem |"
          " departs 2025 : reussis / perdus"]
    for nc, compte in COMPTES.items():
        res[nc] = {}
        for nb, r in BOTS.items():
            x = {k: bilan(lancer(v, b0, compte, r)) for k, v in groupes.items()}
            res[nc][nb] = x
            a, b, c = x["2011-2022"], x["2023-2026"], x["2025"]
            L.append(f"{nc} | {nb} | {a['reussis']:.1f} / {a['perdus']:.1f} / {a['pas_finis']:.1f} / {a['seances_mediane']}"
                     f" | {b['reussis']:.1f} / {b['perdus']:.1f} / {b['pas_finis']:.1f} / {b['seances_mediane']}"
                     f" | {c['reussis']:.1f} / {c['perdus']:.1f}")
    # descriptif : filtre delta simule (2023-2026 et 2025)
    rho, gardes = gardes_simules(D, nj)
    L += ["", f"Descriptif : zone filtree par un delta simule (rho = {rho:.2f}, {TIRAGES} tirages, 20 % ecartes) ;"
          " reussis / perdus en moyenne", "compte | bot | 2023-2026 | departs 2025"]
    bases = [base(gd) for gd in gardes]
    for nc, compte in COMPTES.items():
        for nb, r in BOTS.items():
            xs = [{k: bilan(lancer(groupes[k], bb, compte, r)) for k in ("2023-2026", "2025")} for bb in bases]
            m = {k: (np.mean([x[k]["reussis"] for x in xs]), np.mean([x[k]["perdus"] for x in xs])) for k in xs[0]}
            res[nc][nb]["filtre_simule"] = m
            L.append(f"{nc} | {nb} | {m['2023-2026'][0]:.1f} / {m['2023-2026'][1]:.1f} | {m['2025'][0]:.1f} / {m['2025'][1]:.1f}")
    # descriptif : avril - 25 septembre 2026 avec le vrai delta, un depart par seance
    filtre = pd.read_csv(K.R0 / "orderflow/zone_avril_septembre_2026.csv")
    gv = {(x.jour, int(x.minute), int(x.sens)): bool(x.garde) for x in filtre.itertuples()}
    garde_vrai = np.array([gv.get(c, True) for c in zip(D["Z"]["jour"], D["Z"]["me"], D["Z"]["sens"])])
    bv = base(garde_vrai)
    d0 = int(np.searchsorted(j, pd.Timestamp("2026-04-01")))
    tous = [d for d in range(d0, nj) if D["ouvert"][d] == 0]
    L += ["", f"Descriptif : avril - 25 septembre 2026, vrai delta, un depart par seance ({len(tous)} departs) ;"
          " reussis / perdus / pas finis (jusqu'au 25 septembre)", "compte | bot | resultat"]
    for nc, compte in COMPTES.items():
        for nb, r in BOTS.items():
            cc = compte[:7] + (nj,) if compte[7] > 21 else compte
            x = bilan(lancer(tous, bv, cc, r))
            res[nc][nb]["2026_vrai_delta"] = x
            L.append(f"{nc} | {nb} | {x['reussis']:.1f} / {x['perdus']:.1f} / {x['pas_finis']:.1f}")
    (K.ICI / "comptes.txt").write_text("\n".join(L) + "\n")
    (K.ICI / "comptes.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("\n".join(L))


if __name__ == "__main__":
    main()
