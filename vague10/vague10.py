#!/usr/bin/env python3
"""Vague 10 (README.md) : 72 candidates = 3 comptes 50K x 2 coussins gardes x 12 freins (MES sous un coussin, pause du bot,
stop du jour, mix), tous sans zone les jours de la Fed. Mesure : un seul achat, sans rachat. Ecrit vague10.txt et
vague10.json."""
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "vague9"))
sys.path.insert(0, str(ICI.parent / "vague8"))
import socle9 as S9  # noqa: E402
import vague8 as V8  # noqa: E402

W, D4, M4 = V8.W, V8.D4, V8.M4
G = {}
FREINS = {"aucun": dict(),
          **{f"MES sous {c:,} $ de coussin": dict(c_mnq=float(c)) for c in (1750, 1500, 1250, 1000)},
          **{f"pause {n} seances sous {c:,} $": dict(c_pause=float(c), n_pause=n) for c in (1500, 1000) for n in (10, 20)},
          **{f"stop du jour {s} $": dict(dll=float(s)) for s in (300, 500)},
          "MES sous 1,500 $ + stop du jour 500 $": dict(c_mnq=1500.0, dll=500.0)}
COMPTES = ("LucidFlex 50K", "Topstep 50K", "FundedNext Legacy 50K")


def candidates():
    return [dict(compte=c, k=k, frein=f) for c in COMPTES for k in (1, 2) for f in FREINS]


def nom(c):
    return f"{c['compte']}, garder {2000 * c['k']:,} $, frein : {c['frein']}"


def achats(args):
    """Un seul achat (comme vague8.achats, sans rachat), avec le frein."""
    c, g = args
    D = G["D"]
    kN, kE = D4.facteurs_jour(D)
    cap = V8.fin_groupe(D, g)
    e, f_, part, (prix, mensuel, activation), _, pc = V8.reglages(dict(compte=c["compte"], zone="zone MNQ", k=c["k"]))
    fr = FREINS[c["frein"]]
    if "dll" in fr:
        e = e[:4] + (min(e[4], fr["dll"]) if e[4] > 0 else fr["dll"],) + e[5:]
        f_ = f_[:2] + (min(f_[2], fr["dll"]) if f_[2] > 0 else fr["dll"],) + f_[3:]
    iss, nch, perdu12, recu, vie, net = [], [], [], 0.0, 0.0, []
    for b in G["bases"]:
        for d in G["groupes"][g]:
            sv = min(V8.H_SUIVI, cap - d)
            ret = np.zeros(sv)
            r = M4.parcours4(d, 4, 2.0 * kN, 5.0 * kE, ret, *b, *e, *f_, sv, 1, 1, 1e18, 0.0, pc,
                             fr.get("c_mnq", 0.0), fr.get("c_pause", 0.0), fr.get("n_pause", 0))
            iss.append(r[0])
            nch.append(r[1])
            m24 = min(r[1], V8.H)
            cout = prix * (np.ceil(m24 / V8.MOIS) if mensuel else 1) + (activation if r[0] == 1 and r[1] <= V8.H else 0.0)
            if r[0] != 1:
                net.append(-cout)
                continue
            fin = r[6] if r[2] else sv
            if sv - r[1] >= 252:
                perdu12.append(bool(r[2]) and fin - r[1] <= 252)
            recu += ret[:fin].sum() * part
            vie += (fin - r[1]) / V8.MOIS
            net.append(ret[:min(fin, V8.H)].sum() * part - cout)
    iss, nch, net = np.array(iss), np.array(nch), np.array(net)
    ok = iss == 1
    fini = (iss != 0).sum()
    return {"reussi": float(ok.mean()), "perdu": float((iss == -1).sum() / fini) if fini else float("nan"),
            "pas_fini": float((iss == 0).mean()),
            "valide_mois": float(np.median(nch[ok]) / V8.MOIS) if ok.any() else float("nan"),
            "valide_q3": float(np.percentile(nch[ok], 75) / V8.MOIS) if ok.any() else float("nan"),
            "finance_perdu12": float(np.mean(perdu12)) if perdu12 else float("nan"), "n12": len(perdu12),
            "retraits_mois_vie": recu / vie if vie else 0.0, "net_achat": float(net.mean()),
            "net_median": float(np.median(net)), "achats_perdants": float(np.mean(net < 0))}


def texte(x):
    return (f"challenge reussi {x['reussi']:.0%} / perdu {x['perdu']:.0%} (pas fini {x['pas_fini']:.0%}), valide en"
            f" {x['valide_mois']:.1f} mois (3 sur 4 en {x['valide_q3']:.1f}) | finance perdu dans les 12 mois"
            f" {x['finance_perdu12']:.0%} (sur {x['n12']}) | retraits par mois en vie {x['retraits_mois_vie']:,.0f} $ |"
            f" net de l'achat sur 24 mois : moyenne {x['net_achat']:+,.0f} $, mediane {x['net_median']:+,.0f} $ |"
            f" achats qui perdent de l'argent {x['achats_perdants']:.0%}")


def main():
    t0 = time.time()
    W.regler("regles")
    D, T, a3, gardes = S9.charger()
    C, _, _ = S9.conditions(D, T, gardes)
    fed = C["pas un jour de la Fed"]
    W.G["D4"] = D
    G.update(D=D, bases=[D4.base(D, g & fed) for g in gardes], groupes=V8.groupes(D))
    CC = candidates()
    assert len(CC) == 72
    GA = list(G["groupes"])
    taches = [(c, g) for c in CC for g in GA]
    with mp.get_context("fork").Pool(4) as p:
        out = p.map(achats, taches, chunksize=1)
    res = {(nom(c), g): x for (c, g), x in zip(taches, out)}
    print(f"calcul ({time.time() - t0:.0f} s)", flush=True)
    gc, gv, g25 = GA
    classe = sorted(CC, key=lambda c: -res[(nom(c), gc)]["net_achat"])
    L = ["Vague 10 : un seul achat de 50K, sans rachat ; bot zone 1 MNQ + RSI(2) de nuit sur 1 MES, pas de zone les jours"
         " de la Fed ; filtre simule aussi bon qu'en 2026 (10 tirages) ; suivi 36 mois au plus.", ""]
    for g in GA:
        L += [f"=== {g} (classement : net par achat sur 2012-2021)"] + [f"{nom(c)} | " + texte(res[(nom(c), g)])
                                                                         for c in classe] + [""]
    L.append("=== Jugement")
    sure = lambda x, s: x["perdu"] <= s and x["finance_perdu12"] <= s                    # noqa: E731
    sures = [c for c in classe if sure(res[(nom(c), gc)], 0.20)]
    L.append(f"Sures sur les achats 2012-2021 : {len(sures)} sur {len(CC)}")
    retenue = None
    for c in sures:
        xv, x5 = res[(nom(c), gv)], res[(nom(c), g25)]
        ok1 = sure(xv, 0.25) and xv["net_achat"] > 0
        ok2 = x5["perdu"] <= 0.25
        L.append(f"{nom(c)} : net {res[(nom(c), gc)]['net_achat']:+,.0f} $ (2012-2021) ; 2023-2026 : challenge perdu"
                 f" {xv['perdu']:.0%}, finance perdu {xv['finance_perdu12']:.0%}, net {xv['net_achat']:+,.0f} $"
                 f" ({'oui' if ok1 else 'non'}) ; achats 2025 : challenge perdu {x5['perdu']:.0%}"
                 f" ({'oui' if ok2 else 'non'}) -> {'VALIDEE' if ok1 and ok2 else 'non validee'}")
        if ok1 and ok2:
            retenue = c
            break
    L.append(f"=> {'retenue : ' + nom(retenue) if retenue else 'aucune candidate sure et validee'}")
    L += ["", "=== Pour voir ce que fait chaque frein : LucidFlex, Topstep, FundedNext, garder 4 000 $ ; challenge perdu"
          " (2012-21 / 2023-26 / 2025) ; finance perdu en 12 mois (2012-21 / 2023-26) ; net par achat (2012-21 / 2023-26 /"
          " 2025)"]
    for f in FREINS:
        for k in COMPTES:
            c = dict(compte=k, k=2, frein=f)
            a, v, z = (res[(nom(c), g)] for g in GA)
            L.append(f"{f} | {k} | {a['perdu']:.0%} / {v['perdu']:.0%} / {z['perdu']:.0%} | {a['finance_perdu12']:.0%} /"
                     f" {v['finance_perdu12']:.0%} | {a['net_achat']:+,.0f} / {v['net_achat']:+,.0f} /"
                     f" {z['net_achat']:+,.0f} $")
    (ICI / "vague10.txt").write_text("\n".join(L) + "\n")
    (ICI / "vague10.json").write_text(json.dumps({" | ".join(k): v for k, v in res.items()} |
                                                 {"retenue": nom(retenue) if retenue else None}, indent=1,
                                                 ensure_ascii=False))
    print(f"fin ({time.time() - t0:.0f} s)", flush=True)
    print("\n".join(L[-40:]))


if __name__ == "__main__":
    main()
