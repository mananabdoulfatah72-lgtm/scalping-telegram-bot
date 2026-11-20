#!/usr/bin/env python3
"""Filtres de regime et portefeuille pour reduire les baisses du Supertrend + renfort + bougie folle (usine/REGLES.md,
fixe le 20 novembre 2026). Usage : KB_MINUTES=<nasdaq100_1min.csv.gz> NQ_RECENT=<nq_1min.csv.gz> python3 usine/filtres_st.py"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import donnees as Dn  # noqa: E402
import moteur as Mo  # noqa: E402
import pupitre as Pu  # noqa: E402
import agents_st as A  # noqa: E402
import renfort_st as R  # noqa: E402
import indicateurs as I  # noqa: E402
import familles_tendance as FT  # noqa: E402


def mesures(g, p, j, jours, idx_ok):
    s = pd.Series(g, index=jours); mois = s.resample("ME").sum()
    out = {}
    for nom, (a, b) in (("2015-2022", ("2015-01-01", "2022-12-31")), ("2023-2026", ("2023-01-01", "2026-11-19"))):
        x = s[a:b]; cum = x.cumsum()
        out[nom] = dict(par_an=round(float(x.mean()) * 252), pire_baisse=round(float((cum - cum.cummax()).min())))
    rr = np.array([A.compte(g, p, j, i, 22) for i in range(len(g) - 22)])
    r23 = rr[(jours >= "2023-01-01")[:len(rr)]]
    out.update(retrait_22_2023=round(float(np.mean(r23 == 0)), 3), perdu_22_2023=round(float(np.mean((r23 == 1) | (r23 == 2))), 3),
               pire_mois=round(float(mois.min())), mois_positifs=round(float(np.mean(mois[mois.index < "2026-11-01"] > 0)), 3),
               juillet_septembre_2026=round(float(s["2026-07-01":"2026-09-30"].sum())), mois_en_cours=round(float(s["2026-10-13":"2026-11-19"].sum())))
    return out


def principal():
    D = Dn.charger(recent=os.environ.get("NQ_RECENT") or None)
    P = Mo.deriver(D); J = D["J"]; ok = D["complete"].copy()
    ok[np.where(J == "2026-11-19")[0][0]] = True
    P["ok"] = ok
    O, H, L, C = P["O"], P["H"], P["L"], P["C"]; S = len(J)
    pg, pi = R.k_st_renfort(O, H, L, C, ok, 10, 3.0, True, True)
    idx = np.where(ok & (J >= "2015-01-01"))[0]; jours = pd.to_datetime(J[idx].astype(str))
    def dollars(pg_, pi_, lim=300.0):
        g, p, j = Pu.k_dollars_p(P["lg"], P["lb"], O, H, L, pg_, pi_, ok, lim, A.DOL, A.COUT, 2.0)
        return np.nan_to_num(g), np.nan_to_num(p), j
    g0, p0, j0 = dollars(pg, pi)
    # donnees du jour, seances completes seulement (sinon NaN), connues a la cloture
    cl = np.where(ok, C[:, -1], np.nan); op = np.where(ok, O[:, 0], np.nan)
    hi = np.where(ok, H.max(axis=1), np.nan); lo = np.where(ok, L.min(axis=1), np.nan)
    d = pd.DataFrame({"cl": cl, "op": op, "hi": hi, "lo": lo})
    sma20 = d["cl"].rolling(20, min_periods=20).mean()
    sens_fond = np.sign(d["cl"] - sma20).shift(1).to_numpy()                        # F1 : connu la veille
    eff = ((d["cl"] - d["op"]).abs() / (d["hi"] - d["lo"])).rolling(10, min_periods=8).mean()
    f4 = (eff > eff.rolling(250, min_periods=200).median().shift(1)).shift(1).fillna(False).to_numpy()
    amp = (d["hi"] - d["lo"]) / d["cl"]
    f5 = (amp > amp.rolling(100, min_periods=80).median().shift(1)).shift(1).fillna(False).to_numpy()
    gs = pd.Series(g0).where(ok)
    f3 = (gs.rolling(20, min_periods=20).sum().shift(1) > 0).fillna(False).to_numpy()   # seances non tradees : ignorees
    V = {}
    # F1 : positions du mauvais sens mises a zero
    m1 = np.nan_to_num(sens_fond)[:, None]
    V["F1 tendance du jour (moyenne 20 jours)"] = (np.where(np.sign(pg) == m1, pg, 0).astype(np.int8), np.where(np.sign(pi) == m1, pi, 0).astype(np.int8))
    # F2 : accord avec le Supertrend 15 minutes (etat de la derniere bougie de 5 minutes finie)
    o5, h5, l5, c5 = I.barres5(O, H, L, C)
    st15 = FT.supertrend_15(h5, l5, c5, 10, 3.0).reshape(S, 78)
    q = np.arange(Mo.N); b = np.clip(q // 5 - 1, 0, 77)
    autor = st15[:, b]
    V["F2 accord avec le Supertrend 15 minutes"] = (np.where(np.sign(pg) == np.sign(autor), pg, 0).astype(np.int8),
                                                   np.where(np.sign(pi) == np.sign(autor), pi, 0).astype(np.int8))
    for nom, masque in (("F3 courbe de gains (20 seances)", f3), ("F4 marche directionnel", f4), ("F5 marche agite", f5)):
        V[nom] = (np.where(masque[:, None], pg, 0).astype(np.int8), np.where(masque[:, None], pi, 0).astype(np.int8))
    res = {"Base : Supertrend + renfort + bougie folle, limite 300 $": mesures(g0[idx], p0[idx], j0[idx], jours, idx)}
    for nom, (a, b_) in V.items():
        g, p, j = dollars(a, b_)
        res[nom] = mesures(g[idx], p[idx], j[idx], jours, idx)
    Z = Mo.STRATEGIES["zone"]; zpg, zpi = Z["f"](P, **Z["bot"])
    gz, pz, jz = dollars(zpg, zpi, Z["limite"])
    res["P base + zone de bruit"] = mesures(g0[idx] + gz[idx], p0[idx] + pz[idx], j0[idx] | jz[idx], jours, idx)
    res["(pour info) zone de bruit seule"] = mesures(gz[idx], pz[idx], jz[idx], jours, idx)
    base = res["Base : Supertrend + renfort + bougie folle, limite 300 $"]
    for nom, v in res.items():
        if nom.startswith("Base") or nom.startswith("(pour"):
            continue
        v["retenue"] = bool(all(v[k]["pire_baisse"] >= 0.8 * base[k]["pire_baisse"] and v[k]["par_an"] >= 0.8 * base[k]["par_an"] for k in ("2015-2022", "2023-2026"))
                            and v["perdu_22_2023"] < base["perdu_22_2023"])
    (ICI / "resultats" / "2026-11-20" / "filtres_st.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(f"{'variante':52s} | $/an 15-22 | baisse 15-22 | $/an 23-26 | baisse 23-26 | pire mois | mois + | juil-sept 26 | mois en cours | compte : retrait / perdu")
    for nom, v in res.items():
        a, b_ = v["2015-2022"], v["2023-2026"]
        print(f"{nom[:52]:52s} | {a['par_an']:+7,} | {a['pire_baisse']:+8,} | {b_['par_an']:+7,} | {b_['pire_baisse']:+8,} | {v['pire_mois']:+7,} | {v['mois_positifs']:.0%} | "
              f"{v['juillet_septembre_2026']:+7,} | {v['mois_en_cours']:+7,} | {v['retrait_22_2023']:.0%} / {v['perdu_22_2023']:.0%} {'RETENUE' if v.get('retenue') else ''}")


if __name__ == "__main__":
    principal()
