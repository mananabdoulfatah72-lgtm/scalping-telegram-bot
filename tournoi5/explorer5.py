#!/usr/bin/env python3
"""Tournoi n°5, etapes 1 et 2 (README.md). Chaque famille tourne des que ses donnees sont la.
Lancer depuis ce dossier : python3 explorer5.py [B C A D E]
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

import strategies5 as S
from explorer import t_stat      # tournoi/explorer.py

ICI = Path(__file__).resolve().parent
N_BRUIT, N_JOURS = 20, 200
FIN = pd.Timestamp("2022-12-31")


def mesure(r, ok, J, debut):
    j = pd.DatetimeIndex(J)
    m = ok & (j >= pd.Timestamp(debut)) & (j <= FIN)
    x = r[m]
    moit = j[m].year <= (j[m].year.min() + j[m].year.max()) // 2
    return m, {"t": t_stat(x), "jours": int(m.sum()), "jours_trade": int((x != 0).sum()),
               "t_1re_moitie": t_stat(x[moit]), "t_2e_moitie": t_stat(x[~moit]), "rendement_moyen_bp": float(x[x != 0].mean() * 1e4) if (x != 0).any() else 0.0}


def famille_minutes(code, marche, fonction, debut):
    J, O, H, L, C, P, V, ech, complete, contrat = S.charger_minutes(marche)
    g = pd.DatetimeIndex(J) <= FIN                                 # le coffre n'entre pas dans l'exploration
    J, O, H, L, C, ech, complete, contrat = J[g], O[g], H[g], L[g], C[g], ech[g], complete[g], contrat[g]
    cout = S.cout_micro(marche)
    pts, ok = fonction(J, O, H, L, C, complete, ech, contrat, cout)
    m, res = mesure(pts / O[:, 0], ok, J, debut)
    rng = np.random.default_rng(2032)
    bruit = []
    for k in range(N_BRUIT):
        O2, H2, L2, C2 = S.melanger_sans_volume(O, H, L, C, rng, S.MINUTES[marche][2])
        p2, ok2 = fonction(J, O2, H2, L2, C2, complete, ech, contrat, cout)
        bruit.append(mesure(p2 / O2[:, 0], ok2, J, debut)[1]["t"])
    b = max(bruit)
    return {"code": code, "marche": marche, **res, "controle": f"bruit max {b:+.2f}", "passe": res["t"] >= 2 and res["t"] > b}


def main():
    familles = sys.argv[1:] or ["B", "C", "A", "D", "E"]
    lignes = []
    t0 = time.time()
    if "B" in familles:
        for i, marche in enumerate(("RTY", "YM", "GC", "CL", "6E")):
            f = lambda J, O, H, L, C, comp, ech, con, cout: S.fin_de_seance(O, H, L, C, comp, ech, con, cout)
            lignes.append(famille_minutes(f"B{i + 1}", marche, f, "2016-01-01"))
            print(f"  B {marche} ({time.time() - t0:.0f} s)", flush=True)
    if "C" in familles:
        f = lambda J, O, H, L, C, comp, ech, con, cout: S.rapport_eia(J, O, H, L, C, comp, ech, cout)
        lignes.append(famille_minutes("C1", "CL", f, "2016-01-01"))
    if "D" in familles and (S.DONNEES / "bitcoin_1min.csv.gz").exists():
        f = lambda J, O, H, L, C, comp, ech, con, cout: S.bitcoin(O, H, L, C, comp, ech, cout)
        lignes.append(famille_minutes("D1", "BTC", f, "2018-01-01"))
    if "A" in familles and all((S.DONNEES / f"{d}_1h.csv.gz").exists() for d in S.DEVISES):
        heures = {d: S.lire_heures(d) for d in S.DEVISES}
        J = S.jours_ouvres(heures)
        J = J[J <= FIN]
        fix = S.heure_fixing(J)
        for code, decal, sens in (("A1", -1, -1), ("A2", 0, 1)):
            r, ok = S.trade_heure(heures, J, fix + decal, sens)
            m, res = mesure(r, ok, J, "2011-01-01")
            autres = []
            for hh in range(3, 16):
                if hh == (10 if decal == -1 else 11):
                    continue
                r2, ok2 = S.trade_heure(heures, J, np.full(len(J), hh), sens)
                autres.append((hh, mesure(r2, ok2, J, "2011-01-01")[1]["t"]))
            b = max(t for _, t in autres)
            lignes.append({"code": code, "marche": "panier de 6 devises", **res,
                           "controle": f"autres heures : max {b:+.2f} (" + " ".join(f"{h}h:{t:+.1f}" for h, t in autres) + ")",
                           "passe": res["t"] >= 2 and res["t"] > b})
    if "E" in familles and (S.DONNEES / "ZN_1h.csv.gz").exists() and (S.DONNEES / "adjudications.csv").exists():
        h = S.lire_heures("ZN")
        J = S.jours_ouvres({"ZN": h})
        J = J[J <= FIN]
        adj = pd.DatetimeIndex(J).isin(S.adjudications())
        rng = np.random.default_rng(2033)
        for code, h0, h1, sens in (("E1", 9, 13, -1), ("E2", 13, 15, 1)):
            r_tous, ok = S.zn_trade(h, J, h0, h1, sens)
            r = np.where(adj, r_tous, 0.0)
            m, res = mesure(r, ok, J, "2011-01-01")
            pool = np.where(ok & ~adj & (pd.DatetimeIndex(J) >= pd.Timestamp("2011-01-01")))[0]
            n = int((adj & m).sum())
            ts = []
            for _ in range(N_JOURS):
                msk = np.zeros(len(J), bool)
                msk[rng.choice(pool, n, replace=False)] = True
                ts.append(mesure(np.where(msk, r_tous, 0.0), ok, J, "2011-01-01")[1]["t"])
            p95 = float(np.quantile(ts, 0.95))
            lignes.append({"code": code, "marche": "ZN", **res, "controle": f"jours sans adjudication p95 {p95:+.2f} ({n} adjudications)",
                           "passe": res["t"] >= 2 and res["t"] > p95})
    df = pd.DataFrame(lignes)
    nom = "exploration5_" + "".join(familles) + ".csv"
    df.to_csv(ICI / nom, index=False)
    print("\nTournoi n°5 - exploration jusqu'a 2022 (t sur les rendements quotidiens nets) :")
    for _, x in df.sort_values("t", ascending=False).iterrows():
        print(f"  {x['code']} {x['marche']:20s} | t {x['t']:+.2f} (1re moitie {x['t_1re_moitie']:+.2f}, 2e {x['t_2e_moitie']:+.2f})"
              f" | {x['jours_trade']:4d} jours de trade, {x['rendement_moyen_bp']:+.1f} pb net par jour de trade | {x['controle']}"
              f" | {'SURVIT' if x['passe'] else 'elimine'}", flush=True)
    surv = df[df["passe"]]
    print(f"\nSurvivants : {len(surv)}" + "".join(f"\n  - {a} {b}" for a, b in zip(surv["code"], surv["marche"])))
    f = ICI / "survivants5.json"
    anciens = json.loads(f.read_text()) if f.exists() else []
    anciens = [a for a in anciens if a["code"] not in set(df["code"])] + [{"code": a, "marche": b} for a, b in zip(surv["code"], surv["marche"])]
    f.write_text(json.dumps(anciens, indent=1))


if __name__ == "__main__":
    main()
