#!/usr/bin/env python3
"""static50k (README.md) : 14 variantes du bot sur DayTraders Static 50K puis Pro Static, au niveau d'aujourd'hui ; choix
sur les departs de 2012-2021, verification sur 2023 - sept. 2025 ; descriptifs (2022, 2025, prix de l'epoque, compte Pro
pessimiste, 24 mois, filtre delta simule, vrai delta d'avril - septembre 2026). Ecrit static.txt et static.json.
Lancer depuis ce dossier : python3 static.py"""
import json
import sys
import time

import numpy as np
import pandas as pd
from scipy.stats import norm

import donnees as DN
import moteur_static as M
import outils as U

ICI = DN.ICI
PRIX, ACTIVATION, EUROS_500 = 30.0, 130.0, 580.0
H1, H2 = 252, 504
VAR = list(M.VARIANTES)
CAPS = {"P0": 0.0, "P500": 500.0}
CANDIDATES = [(v, c) for v in VAR for c in CAPS]
TIRAGES = 20


def lancer(D, b, departs, v, cap, niveau=True, pessimiste=0, h2=H2):
    return np.array([U.achat(D, b, d, v, plafond=CAPS[cap], pessimiste=pessimiste, niveau=niveau, h2=h2)
                     for d in departs])


def mesures(R, h=H1):
    """Mesures d'un groupe d'achats (R : resultats du moteur), horizon h seances."""
    iss, fe = R[:, M.ISSUE], R[:, M.FIN_EVAL]
    ok = (iss == 1) & (fe <= h)
    ko = (iss == -1) & (fe <= h)
    recu = R[:, M.RECU1] if h == H1 else R[:, M.RECU2]
    net = recu - PRIX - ACTIVATION * ok
    pro = ok & (R[:, M.PRO_PERDU] == 1) & (R[:, M.FIN_PRO] <= h)
    prem = R[:, M.PREMIER]
    prem = prem[(prem > 0) & (prem <= h)]
    return {"achats": len(R), "net": float(net.mean()), "net_median": float(np.median(net)),
            "reussi": float(ok.mean()), "perdu": float(ko.mean()),
            "seances_reussite": float(np.median(fe[ok])) if ok.any() else None,
            "retrait": float((recu > 0).mean()), "net_580": float((net >= EUROS_500).mean()),
            "recu": float(recu.mean()), "pro_perdu": float(pro.mean()),
            "premier_retrait": float(np.median(prem)) if len(prem) else None,
            "inactif": float((ok & (R[:, M.INACTIF] == 1)).mean())}


def ligne(nom, x):
    s = "-" if x["seances_reussite"] is None else f"{x['seances_reussite']:.0f}"
    p = "-" if x["premier_retrait"] is None else f"{x['premier_retrait']:.0f}"
    return (f"{nom} | {x['achats']} | {x['net']:+,.0f} $ (mediane {x['net_median']:+,.0f}) | {x['reussi']:.0%} / "
            f"{x['perdu']:.0%} | {s} | {x['retrait']:.0%} | {x['net_580']:.0%} | {x['recu']:,.0f} $ | "
            f"{x['pro_perdu']:.0%} | {p}")


ENTETE = ("variante | achats | argent net moyen par achat | evaluation reussie / perdue | seances pour reussir (mediane) |"
          " au moins un retrait | net >= 580 $ (500 EUR) | retraits moyens | compte Pro perdu | 1er retrait (mediane,"
          " seances apres l'achat)")


def gardes_simules(D, rho, graine=7):
    """Comme filtre_h1/scenario.py : signal correle au resultat de chaque trade de zone, 20 % ecartes, TIRAGES tirages."""
    z26 = pd.read_csv(DN.R0 / "orderflow" / "zone_avril_septembre_2026.csv")
    g = z26["garde"].astype(bool)
    part = float((~g).mean())
    q = norm.ppf(part)
    Z, C = D["Z"], D["C"]
    d, me, ms, s = (Z[k].to_numpy() for k in ("d", "me", "ms", "sens"))
    pts = s * (C[d, ms] - C[d, me]) - DN.RB.COUT
    zr = pts / pd.Series(pts).groupby(D["jours"][d].year).transform("std").to_numpy()
    rng = np.random.default_rng(graine)
    return [(rho * zr + np.sqrt(1 - rho ** 2) * rng.standard_normal(len(zr))) > q for _ in range(TIRAGES)]


def rho_2026():
    z26 = pd.read_csv(DN.R0 / "orderflow" / "zone_avril_septembre_2026.csv")
    g = z26["garde"].astype(bool)
    ecart = (z26["points"][g].mean() - z26["points"][~g].mean()) / z26["points"].std()
    part = float((~g).mean())
    q = norm.ppf(part)
    return ecart / (norm.pdf(q) / part + norm.pdf(q) / (1 - part))


def garde_vrai(D):
    f = pd.read_csv(DN.R0 / "orderflow/zone_avril_septembre_2026.csv")
    g = {(r.jour, int(r.minute), int(r.sens)): bool(r.garde) for r in f.itertuples()}
    Z = D["Z"]
    return np.array([g.get(c, True) for c in zip(Z["jour"], Z["me"], Z["sens"])])


def main():
    t0 = time.time()
    D = DN.charger()
    j, nj = D["jours"], len(D["jours"])
    b0 = U.base(D)
    possibles = U.departs(D, 1)
    departs = U.departs(D)
    G = {"choix 2012-2021": [d for d in departs if pd.Timestamp("2012-01-01") <= j[d] <= pd.Timestamp("2021-12-31")],
         "verification 2023 - sept. 2025": [d for d in departs if j[d] >= pd.Timestamp("2023-01-01") and d + H1 <= nj],
         "2022 (descriptif)": [d for d in departs if j[d].year == 2022],
         "2025 (descriptif)": [d for d in departs if j[d].year == 2025 and d + H1 <= nj]}
    tous = sorted(set(sum(G.values(), [])))
    cn, ce = U.clotures(D)
    L = [f"DayTraders Static 50K puis Pro Static ; {nj} seances du {j[0].date()} au {j[-1].date()} ; departs : 1 seance"
         f" sur 5, RSI(2) a plat ; prix {PRIX:.0f} $, activation {ACTIVATION:.0f} $ ; NQ au depart ramene a "
         f"{cn[-1]:,.0f} points, ES a {ce[-1]:,.0f}",
         "Groupes : " + " ; ".join(f"{k} : {len(v)} achats" for k, v in G.items()), ""]
    res = {}
    # ------------------------------------------------------------------ 14 candidates, niveau d'aujourd'hui
    R = {}
    for v, c in CANDIDATES:
        out = lancer(D, b0, tous, v, c)
        R[(v, c)] = dict(zip(tous, out))
        print(f"{v} {c} ({time.time() - t0:.0f} s)", flush=True)
    def groupe(vc, g, h=H1):
        dd = G[g] if h == H1 else [d for d in G[g] if d + H2 <= nj]
        return mesures(np.array([R[vc][d] for d in dd]), h)
    for g in G:
        L += [f"=== {g}, au niveau d'aujourd'hui, 12 mois apres l'achat", ENTETE]
        for vc in CANDIDATES:
            x = groupe(vc, g)
            res[f"{vc[0]} {vc[1]} | {g} | 12 mois"] = x
            L.append(ligne(f"{vc[0]} {vc[1]}", x))
        L.append("")
    # ------------------------------------------------------------------ choix et verification
    gc, gv = "choix 2012-2021", "verification 2023 - sept. 2025"
    net_c = {vc: res[f"{vc[0]} {vc[1]} | {gc} | 12 mois"]["net"] for vc in CANDIDATES}
    net_v = {vc: res[f"{vc[0]} {vc[1]} | {gv} | 12 mois"]["net"] for vc in CANDIDATES}
    choisie = max(CANDIDATES, key=lambda vc: net_c[vc])
    valide = net_v[choisie] > 0 and net_v[choisie] >= net_v[("E0", "P0")]
    meilleure_r = max([vc for vc in CANDIDATES if vc[0] != "E1"], key=lambda vc: net_c[vc])
    sans = ("E1", meilleure_r[1])
    rsi_reste = net_c[meilleure_r] > net_c[sans] and net_v[meilleure_r] > net_v[sans]
    L += ["=== Decision (regles fixees avant le calcul)",
          f"choisie sur 2012-2021 : {choisie[0]} {choisie[1]} ({net_c[choisie]:+,.0f} $ par achat) ; verification 2023 -"
          f" sept. 2025 : {net_v[choisie]:+,.0f} $ contre {net_v[('E0', 'P0')]:+,.0f} $ pour E0 P0 -> "
          f"{'VALIDEE' if valide else 'NON VALIDEE'}",
          f"RSI(2) : meilleure variante avec RSI(2) sur 2012-2021 = {meilleure_r[0]} {meilleure_r[1]} "
          f"({net_c[meilleure_r]:+,.0f} $ / verification {net_v[meilleure_r]:+,.0f} $) contre {sans[0]} {sans[1]} "
          f"({net_c[sans]:+,.0f} $ / {net_v[sans]:+,.0f} $) -> le RSI(2) {'RESTE' if rsi_reste else 'SORT'}", ""]
    res["decision"] = {"choisie": " ".join(choisie), "validee": bool(valide), "meilleure_avec_rsi": " ".join(meilleure_r),
                       "rsi_reste": bool(rsi_reste)}
    suivies = sorted({choisie, ("E0", "P0"), ("E0", "P500"), meilleure_r, sans})
    # ------------------------------------------------------------------ descriptifs
    L += ["=== 24 mois apres l'achat (descriptif, achats avec 24 mois de suivi)", ENTETE]
    for g in (gc, gv):
        for vc in suivies:
            x = groupe(vc, g, H2)
            res[f"{vc[0]} {vc[1]} | {g} | 24 mois"] = x
            L.append(ligne(f"{vc[0]} {vc[1]} | {g}", x))
    L += ["", "=== Prix de l'epoque (descriptif), 12 mois", ENTETE]
    for vc in suivies:
        for g in (gc, gv):
            out = lancer(D, b0, G[g], vc[0], vc[1], niveau=False, h2=H1)
            x = mesures(out)
            res[f"{vc[0]} {vc[1]} | {g} | prix de l'epoque"] = x
            L.append(ligne(f"{vc[0]} {vc[1]} | {g}", x))
    L += ["", "=== Compte Pro pessimiste : plancher remonte a 1 000 $ sous le solde apres chaque retrait (descriptif)", ENTETE]
    for vc in suivies:
        for g in (gc, gv):
            out = lancer(D, b0, G[g], vc[0], vc[1], pessimiste=1, h2=H1)
            x = mesures(out)
            res[f"{vc[0]} {vc[1]} | {g} | pessimiste"] = x
            L.append(ligne(f"{vc[0]} {vc[1]} | {g}", x))
    L += ["", "Regle d'activite (descriptif) : part des achats dont le compte Pro passe 21 seances sans un jour a +200 $"
              " dans les 12 mois"]
    for vc in suivies:
        L.append(f"{vc[0]} {vc[1]} : " + " ; ".join(f"{g} {res[f'{vc[0]} {vc[1]} | {g} | 12 mois']['inactif']:.0%}"
                                                    for g in (gc, gv)))
    # ------------------------------------------------------------------ filtre delta simule (descriptif)
    rho = rho_2026()
    L += ["", f"=== Filtre delta simule (descriptif, comme filtre_h1/scenario.py ; rho mesure en 2026 = {rho:.2f}, "
              f"{TIRAGES} tirages par achat), 12 mois", ENTETE]
    for nom, r in (("aussi bon qu'en 2026", rho), ("deux fois moins bon", rho / 2), ("inutile", 0.0)):
        bases = [U.base(D, g) for g in gardes_simules(D, r)]
        for vc in sorted({choisie, ("E0", "P0")}):
            for g in (gc, gv):
                out = np.vstack([lancer(D, bb, G[g], vc[0], vc[1], h2=H1) for bb in bases])
                x = mesures(out)
                x["achats"] = len(G[g])                 # achats distincts (chacun joue TIRAGES fois)
                res[f"{vc[0]} {vc[1]} | {g} | filtre {nom}"] = x
                L.append(ligne(f"{vc[0]} {vc[1]} | {g} | filtre {nom}", x))
                print(f"filtre {nom} {vc} {g} ({time.time() - t0:.0f} s)", flush=True)
    # ------------------------------------------------------------------ vrai delta, avril - septembre 2026
    bv = U.base(D, garde_vrai(D))
    d26 = [d for d in possibles if j[d] >= pd.Timestamp("2026-04-01")]
    L += ["", "=== Avril - 25 septembre 2026 avec le vrai delta (descriptif) : un achat a chaque seance ou le RSI(2) est"
              " a plat, suivi jusqu'au 25 septembre", "variante | achats | evaluation reussie / perdue / en cours au 25"
              " sept. | au moins un retrait | retraits moyens"]
    for vc in sorted({choisie, ("E0", "P0"), ("E1", choisie[1])}):
        out = lancer(D, bv, d26, vc[0], vc[1], h2=H2)
        ok, ko = out[:, M.ISSUE] == 1, out[:, M.ISSUE] == -1
        L.append(f"{vc[0]} {vc[1]} | {len(d26)} | {ok.mean():.0%} / {ko.mean():.0%} / {1 - ok.mean() - ko.mean():.0%} |"
                 f" {(out[:, M.RECU2] > 0).mean():.0%} | {out[:, M.RECU2].mean():,.0f} $")
    (ICI / "static.txt").write_text("\n".join(L) + "\n")
    (ICI / "static.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("\n".join(L))
    print(f"({time.time() - t0:.0f} s)", file=sys.stderr)


if __name__ == "__main__":
    main()
