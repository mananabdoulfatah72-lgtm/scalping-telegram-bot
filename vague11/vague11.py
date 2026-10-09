#!/usr/bin/env python3
"""Vague 11 (README.md) : plafond de gain du jour sur le compte Master Bulenox 50K. Un seul achat. Ecrit vague11.txt."""
import sys
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "vague10"))
import budget30 as B  # noqa: E402

V8, S9, W, D4, M4 = B.V8, B.S9, B.W, B.D4, B.M4
PLAFONDS = (0.0, 400.0, 500.0, 600.0, 750.0, 1000.0)


def mesurer(D, bases, kN, kE, dd, cap, cap_f, suivi24):
    iss, nch, r1, r2, r3, p12, net, ecart = [], [], [], [], [], [], [], []
    for b in bases:
        for d in dd:
            sv = min(V8.H_SUIVI, cap - d)
            if suivi24 and sv < V8.H:
                continue
            ret = np.zeros(sv)
            r = M4.parcours4(d, 4, 2.0 * kN, 5.0 * kE, ret, *b, *B.E, *B.F, sv, 1, 1, 1e18, 0.0, 0, 1750.0, 0.0, 0, cap_f)
            iss.append(r[0])
            if r[0] != 1:
                if sv >= V8.H:
                    net.append(-B.PRIX)
                continue
            nch.append(r[1])
            fin = r[6] if r[2] else sv
            idx = np.flatnonzero(ret > 0)
            for k, lst in enumerate((r1, r2, r3)):
                lst.append(idx[k] + 1 if len(idx) > k else np.nan)
            ecart += list(np.diff(idx))
            if sv - r[1] >= 252:
                p12.append(bool(r[2]) and fin - r[1] <= 252)
            if sv >= V8.H:
                net.append(ret[:min(fin, V8.H)].sum() - B.PRIX - B.ACTIVATION)
    iss = np.array(iss)
    fini = (iss != 0).sum()
    m = lambda x: np.nanmedian(x) / V8.MOIS if len(x) else np.nan                          # noqa: E731
    return {"perdu": (iss == -1).sum() / fini if fini else np.nan, "valide": m(nch), "r1": m(r1), "r2": m(r2),
            "r3": m(r3), "r3_part": float(np.mean(~np.isnan(np.array(r3, float)))) if r3 else np.nan,
            "ecart": m(ecart), "p12": float(np.mean(p12)) if p12 else np.nan,
            "net": float(np.median(net)) if net else np.nan, "perdants": float(np.mean(np.array(net) < 0)) if net else np.nan}


def texte(x):
    return (f"challenge perdu {x['perdu']:.0%}, valide au mois {x['valide']:.1f} | retraits aux mois {x['r1']:.1f} /"
            f" {x['r2']:.1f} / {x['r3']:.1f} (3e atteint {x['r3_part']:.0%}), un tous les {x['ecart']:.1f} mois |"
            f" Master perdu en 12 mois {x['p12']:.0%} | net sur 24 mois (mediane) {x['net']:+,.0f} $, achats perdants"
            f" {x['perdants']:.0%}")


def main():
    W.regler("regles")
    D, T, a3, gardes = S9.charger()
    C, _, _ = S9.conditions(D, T, gardes)
    bases = [D4.base(D, g & C["pas un jour de la Fed"]) for g in gardes]
    kN, kE = D4.facteurs_jour(D)
    G = V8.groupes(D)
    res = {}
    L = ["Vague 11 : Bulenox 50K, plafond de gain du jour sur le compte Master ; un seul achat ; filtre simule (10 tirages)", ""]
    for g in G:
        cap = V8.fin_groupe(D, g)
        L.append(f"=== {g}" + (" (achats suivis 24 mois)" if g != "achats 2025 - mars 2026" else " (challenge seulement)"))
        for pl in PLAFONDS:
            x = mesurer(D, bases, kN, kE, G[g], cap, pl, g != "achats 2025 - mars 2026")
            res[(g, pl)] = x
            L.append(f"plafond {'aucun' if pl == 0 else f'{pl:,.0f} $'} | " + texte(x))
            print(L[-1], flush=True)
        L.append("")
    gc, gv = "achats 2012-2021", "achats 2023 - mars 2026"
    ref_c, ref_v = res[(gc, 0.0)], res[(gv, 0.0)]
    ok = [pl for pl in PLAFONDS if res[(gc, pl)]["p12"] <= ref_c["p12"] + 0.03]
    choix = max(ok, key=lambda pl: res[(gc, pl)]["net"])
    v = res[(gv, choix)]
    valide = v["net"] >= ref_v["net"] and v["p12"] <= ref_v["p12"] + 0.03
    L += ["=== Jugement",
          f"Choix (2012-2021) : plafond {'aucun' if choix == 0 else f'{choix:,.0f} $'} ; net {res[(gc, choix)]['net']:+,.0f} $"
          f" contre {ref_c['net']:+,.0f} $ sans plafond",
          f"Verification (2023 - sept. 2024) : net {v['net']:+,.0f} $ contre {ref_v['net']:+,.0f} $ ; Master perdu"
          f" {v['p12']:.0%} contre {ref_v['p12']:.0%} -> {'VALIDE' if valide else 'NON VALIDE'}"]
    (ICI / "vague11.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L[-3:]))


if __name__ == "__main__":
    main()
