#!/usr/bin/env python3
"""Monte Carlo du bot sur Bulenox 50K (README.md). Chaque achat simule suit 24 mois (504 seances) faits de vraies
seances du bot tirees au hasard par blocs de 21 seances consecutives (un mois), dans un regime choisi, avec le filtre
delta a une force choisie. Le moteur est celui du bot (moteur_mc.parcours_mc = vague4/moteur4 sans changement de
seance) avec les reglages Bulenox du bot (README de bot3en1). Ecrit mc.json (donnees de la page) et montecarlo.txt."""
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
R0 = ICI.parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(R0 / "vague10"))
sys.path.insert(0, str(R0 / "vague9"))
import moteur_mc as MM  # noqa: E402
import budget30 as B  # noqa: E402
import socle9 as S9  # noqa: E402

M4, D4, W = B.M4, B.D4, B.W
S = S9.S
H, BLOC, MOIS = 504, 21, 21
N, N_TRACE = 4000, 150
FREIN, PLAFOND = 1750.0, 500.0                     # frein : zone sur MES sous 1 750 $ de coussin (750 sous le maximum)
REGIMES = {"tout": ("Toute l'histoire", "2012-01-03", "2026-09-25"),
           "recent": ("Regime recent", "2023-01-03", "2026-09-25"),
           "2025": ("Annee 2025", "2025-01-02", "2025-12-31")}
FILTRES = {"fort": "aussi bon qu'en 2026", "moitie": "deux fois plus faible", "aucun": "aucun filtre"}
P = {}


def preparer():
    W.regler("regles")
    D, T, a3, gardes = S9.charger()
    C, _, _ = S9.conditions(D, T, gardes)
    pf = C["pas un jour de la Fed"]
    moitie = S.gardes_simules(D, S.rho_2026() / 2)[:len(gardes)]
    tous = np.ones(len(T["d"]), bool)
    bases = {"fort": [D4.base(D, g & pf) for g in gardes], "moitie": [D4.base(D, g & pf) for g in moitie],
             "aucun": [D4.base(D, tous & pf)]}
    kN, kE = D4.facteurs_jour(D)
    j = pd.DatetimeIndex(D["jours"])
    pools = {}
    for k, (_, a, z) in REGIMES.items():
        dedans = (j >= pd.Timestamp(a)) & (j <= pd.Timestamp(z))
        ok = np.array([dedans[i:i + BLOC].all() and i + BLOC <= len(j) for i in range(len(j))])
        pools[k] = np.flatnonzero(ok).astype(np.int64)
    P.update(D=D, T=T, a3=a3, gardes=gardes, moitie=moitie, pf=pf, bases=bases, kN=2.0 * kN, kE=5.0 * kE, pools=pools,
             jours=j)
    return P


def tirer_chemin(rng, pool):
    nb = -(-H // BLOC)
    return (rng.choice(pool, nb)[:, None] + np.arange(BLOC)[None, :]).reshape(-1)[:H].astype(np.int64)


def un_chemin(idx, b, Q=None):
    Q = Q or P
    ret, so, pl, ph = np.zeros(H), np.zeros(H), np.zeros(H), np.zeros(H, np.int64)
    r = MM.parcours_mc(np.asarray(idx, np.int64), 4, Q["kN"], Q["kE"], ret, so, pl, ph, *b, *B.E, *B.F, FREIN, PLAFOND)
    return {"r": r, "ret": ret, "solde": so, "plancher": pl, "phase": ph}


def poche(t):
    """Argent pour toi a la fin de chaque seance : -prix a l'achat, -activation a la reussite, + retraits."""
    r = t["r"]
    flux = t["ret"].copy()
    flux[0] -= B.PRIX
    if r[0] == 1:
        flux[int(r[1]) - 1] -= B.ACTIVATION
    return np.cumsum(flux)


def lot(args):
    reg, fil, i0, i1 = args
    rng = np.random.default_rng([list(REGIMES).index(reg), list(FILTRES).index(fil), i0])
    bases = P["bases"][fil]
    out = []
    for i in range(i0, i1):
        idx = tirer_chemin(rng, P["pools"][reg])
        t = un_chemin(idx, bases[i % len(bases)])
        r = t["r"]
        rs = np.flatnonzero(t["ret"] > 0)
        x = {"r": [float(v) for v in r], "retraits": [[int(s) + 1, float(t["ret"][s])] for s in rs],
             "poche": poche(t).astype(np.float32)}
        if i < N_TRACE:
            fin = int(r[6]) if r[0] != 0 else H
            x["trace"] = np.round(t["solde"][:fin] / 10).astype(int).tolist()
            x["debut_annee"] = int(P["jours"][idx[0]].year)
        out.append(x)
    return out


def resumer(res):
    """Mesures d'un scenario sur ses N achats."""
    n = len(res)
    r = np.array([x["r"] for x in res])
    issue, nch, mp_, nret, fin = r[:, 0], r[:, 1], r[:, 2].astype(bool), r[:, 3].astype(int), r[:, 6]
    pc = np.array([x["poche"] for x in res])
    s = np.arange(1, H + 1)
    valide = issue == 1
    ch_perdu = issue == -1
    # jalons : part des achats ayant atteint l'etape a la fin de chaque seance
    jal = {"valide": [(valide & (nch <= k)).mean() for k in s],
           "ch_perdu": [(ch_perdu & (nch <= k)).mean() for k in s],
           "m_perdu": [(mp_ & (fin <= k)).mean() for k in s]}
    for q in (1, 2, 3):
        sq = np.array([x["retraits"][q - 1][0] if len(x["retraits"]) >= q else 10 ** 9 for x in res])
        jal[f"r{q}"] = [(sq <= k).mean() for k in s]
    jal = {k: [round(float(v), 4) for v in vs] for k, vs in jal.items()}
    pcts = {str(p): np.round(np.percentile(pc, p, axis=0)).astype(int).tolist() for p in (5, 25, 50, 75, 95)}
    moy = np.round(pc.mean(axis=0)).astype(int).tolist()
    net = pc[:, -1]
    # issue a 24 mois
    cat = []
    for x, i_, m_, k_ in zip(res, issue, mp_, nret):
        if i_ == -1:
            cat.append("ch_perdu")
        elif i_ == 0:
            cat.append("ch_en_cours")
        elif k_ >= 3:
            cat.append("reel")
        elif m_:
            cat.append(f"m_perdu_{k_}")
        else:
            cat.append(f"m_vivant_{k_}")
    cats = pd.Series(cat).value_counts().to_dict()
    mois_val = np.ceil(nch[valide] / MOIS).astype(int)
    hist_val = np.bincount(np.minimum(mois_val, 25), minlength=26)[1:].tolist()
    q = lambda v: float(np.median(v)) / MOIS if len(v) else None                          # noqa: E731
    sr = {f"r{k}": [x["retraits"][k - 1][0] for x in res if len(x["retraits"]) >= k] for k in (1, 2, 3)}
    montants = [m for x in res for _, m in x["retraits"]]
    nets_par_k = {str(k): float(np.median(net[(nret == k) & valide])) if ((nret == k) & valide).any() else None
                  for k in range(4)}
    return {
        "n": n, "jalons": jal, "poche": pcts, "poche_moy": moy, "issues": {k: int(v) for k, v in cats.items()},
        "hist_validation": hist_val,
        "valide": float(valide.mean()), "ch_perdu": float(ch_perdu.mean()), "ch_en_cours": float((issue == 0).mean()),
        "m_perdu": float(mp_.mean()), "m_perdu_sur_valides": float(mp_[valide].mean()) if valide.any() else None,
        "reel": float((nret >= 3).mean()), "au_moins_1": float((nret >= 1).mean()),
        "mois_validation": q(nch[valide]), "mois_validation_q": [float(np.percentile(nch[valide], p)) / MOIS
                                                                 for p in (25, 75)] if valide.any() else None,
        "mois_r": {k: q(v) for k, v in sr.items()},
        "montant_moyen": float(np.mean(montants)) if montants else None,
        "net_mediane": float(np.median(net)), "net_moyenne": float(net.mean()),
        "net_q": [float(np.percentile(net, p)) for p in (5, 25, 75, 95)],
        "perdants": float((net < 0).mean()), "net_par_retraits": nets_par_k,
        "hist_net": np.histogram(net, bins=np.arange(-500, 4751, 250))[0].tolist(),
        "traces": [{"t": x["trace"], "r": [int(v) if abs(v) < 1e8 else v for v in x["r"][:7]],
                    "ret": x["retraits"], "an": x["debut_annee"]} for x in res if "trace" in x],
    }


def historique():
    """Le bot sans les regles du compte : gain de chaque mois (1 MNQ zone + 1 MES RSI(2) de nuit, pas de zone les jours
    de la Fed), filtre aussi bon qu'en 2026 (moyenne des 10 tirages) et sans filtre ; statistiques des jours de zone."""
    D, T, a3, j = P["D"], P["T"], P["a3"], P["jours"]
    nj, pf = len(j), P["pf"]
    per = j.to_period("M")
    out = {}
    for nom, gg in (("fort", P["gardes"]), ("aucun", [np.ones(len(T["d"]), bool)])):
        tot, zon = [], []
        for g in gg:
            p = g & pf
            z = np.bincount(T["d"][p], weights=T["mnq"][p], minlength=nj)
            tot.append(pd.Series(z + a3, index=j).groupby(per).sum())
            zon.append(pd.Series(z, index=j).groupby(per).sum())
        out[nom] = {"total": pd.concat(tot, axis=1).mean(axis=1), "zone": pd.concat(zon, axis=1).mean(axis=1)}
    rsi = pd.Series(a3, index=j).groupby(per).sum()
    m = out["fort"]["total"].loc["2012-01":"2026-09"]
    jours = []
    for nom, a, z in (("2012-2021", "2012-01-01", "2021-12-31"), ("2023-2026", "2023-01-01", "2026-09-30")):
        sel = (j >= pd.Timestamp(a)) & (j <= pd.Timestamp(z))
        g = P["gardes"][0] & pf
        zj = np.bincount(T["d"][g], weights=T["mnq"][g], minlength=nj)[sel]
        act = zj[zj != 0]
        jours.append({"periode": nom, "seances": int(sel.sum()), "jours_zone": int(len(act)),
                      "gagnants": float((act > 0).mean()), "gain_moyen": float(act[act > 0].mean()),
                      "perte_moyenne": float(act[act < 0].mean())})
    return {"mois": [str(p) for p in m.index],
            "fort": np.round(m.values).astype(int).tolist(),
            "aucun": np.round(out["aucun"]["total"].loc["2012-01":"2026-09"].values).astype(int).tolist(),
            "zone_fort": np.round(out["fort"]["zone"].loc["2012-01":"2026-09"].values).astype(int).tolist(),
            "rsi": np.round(rsi.loc["2012-01":"2026-09"].values).astype(int).tolist(), "jours": jours}


def main():
    t0 = time.time()
    preparer()
    sc = {}
    L = [f"Monte Carlo Bulenox 50K : {N} achats par scenario, 24 mois chacun, blocs de {BLOC} seances ; frein MES sous"
         f" {FREIN:,.0f} $ de coussin, plafond {PLAFOND:,.0f} $/jour sur le Master, pas de zone les jours de la Fed.", ""]
    for reg in REGIMES:
        for fil in FILTRES:
            lots = [(reg, fil, i, min(i + 250, N)) for i in range(0, N, 250)]
            with mp.get_context("fork").Pool(4) as pool:
                res = [x for o in pool.map(lot, lots, chunksize=1) for x in o]
            x = resumer(res)
            sc[f"{reg}|{fil}"] = x
            L.append(f"{REGIMES[reg][0]} / filtre {FILTRES[fil]} : valide {x['valide']:.0%} (mois {x['mois_validation']:.1f}),"
                     f" challenge perdu {x['ch_perdu']:.0%}, Master perdu {x['m_perdu']:.0%}, 1 retrait ou plus"
                     f" {x['au_moins_1']:.0%}, 3 retraits {x['reel']:.0%}, net median {x['net_mediane']:+,.0f} $,"
                     f" moyen {x['net_moyenne']:+,.0f} $, achats perdants {x['perdants']:.0%}")
            print(L[-1], f"({time.time() - t0:.0f} s)", flush=True)
    hist = historique()
    reglages = {"PRIX": B.PRIX, "ACTIVATION": B.ACTIVATION, "E": [float(v) for v in B.E], "FREIN": FREIN,
                "PLAFOND": PLAFOND, "N": N, "H": H, "BLOC": BLOC,
                "F": [float(v) if np.ndim(v) == 0 else [float(u) for u in v] for v in B.F],
                "regimes": {k: list(v) for k, v in REGIMES.items()}, "filtres": FILTRES,
                "pools": {k: int(len(v)) for k, v in P["pools"].items()}}
    (ICI / "mc.json").write_text(json.dumps({"reglages": reglages, "scenarios": sc, "historique": hist},
                                            separators=(",", ":"), ensure_ascii=False))
    (ICI / "montecarlo.txt").write_text("\n".join(L) + "\n")
    print(f"fin ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
