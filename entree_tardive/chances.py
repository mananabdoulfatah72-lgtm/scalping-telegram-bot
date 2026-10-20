#!/usr/bin/env python3
"""D'ou viennent les 55 % de la vague 13, et que deviennent-ils dans la situation de l'utilisateur (20 octobre 2026 :
challenge Bulenox revenu a 0 de gain, 16 seances restantes, RSI(2) de nuit decoche, limite du jour du bot a 1 000 $) ?
Moteur et tirages du filtre de la vague 13 sans changement (montecarlo.preparer : 10 tirages du filtre aussi bon qu'en
2026, 10 deux fois plus faibles, un sans filtre). On part du reglage publie et on change une chose a la fois.
Ecrit chances.txt. Meme lancement que challenge.py (variable KB)."""
import os
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
os.environ.setdefault("NUMBA_CACHE_DIR", str(Path(tempfile.gettempdir()) / "numba_entree_tardive"))

import json  # noqa: E402

import numpy as np  # noqa: E402

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import challenge as CH  # noqa: E402  (KB, defis, COMPTE)

import regles13 as R13  # noqa: E402

FILTRES = {"fort": "filtre aussi bon qu'en 2026", "moitie": "filtre deux fois plus faible", "aucun": "sans filtre"}
GROUPES = ["choix 2012-2021", "verification 2023 - aout 2026", "2025"]


def defi_pic():
    """moteur13.defi13 avec un plus haut de fin de journee deja atteint (pic0, en $ au-dessus du depart) : seules les
    valeurs de depart du plus haut et du plancher changent ; pic0 = 0 redonne defi13."""
    import inspect
    from numba import njit
    src = inspect.getsource(R13.M13.defi13.py_func).replace("@njit(cache=True)\n", "")
    for x, y in [("t_solde, t_plancher, t_taille):", "t_solde, t_plancher, t_taille, pic0):"),
                 ("cash, veut, pic_rt, pic_eod, veille = 0.0, 0, 0.0, 0.0, 0.0\n    plancher = -e_perte",
                  "cash, veut, pic_rt, pic_eod, veille = 0.0, 0, pic0, pic0, 0.0\n    plancher = min(pic0 - e_perte, e_bloc)"),
                 ("def defi13(", "def defi_pic(")]:
        assert src.count(x) == 1, x
        src = src.replace(x, y)
    ns = dict(R13.M13.__dict__)
    exec(src, ns)
    return njit(ns["defi_pic"])


def main():
    K = R13.K
    P = K.MC.preparer()
    d0, d1, lim30, groupes = K.achats(P)
    publie = json.loads((CH.KB / "vague13" / "vague13.json").read_text())["legacy | D"]
    args = R13.args_defi("legacy", "D")
    compte13, leviers13 = args[:7], args[7:]
    compte1000 = (*compte13[:4], 1000.0, *compte13[5:])
    etapes = [("1. vague 13 publiee : D, 30 jours calendaires, RSI(2) de nuit, limite du jour 1 100 $", 4, compte13, None),
              ("2. sans le RSI(2) de nuit (decoche : Bulenox interdit la nuit)", 0, compte13, None),
              ("3. limite du jour du bot a 1 000 $", 0, compte1000, None),
              ("4. depuis 0 avec 16 seances (situation du 20 octobre 2026)", 0, compte1000, 16)]
    L = ["Chances de valider le challenge Bulenox Legacy 50K (version D : arret a +3 050 $, 6 MNQ les 5 dernieres seances),",
         "moteur et tirages du filtre de la vague 13, une chose changee a la fois. Valide / perdu / expire, en % des departs.", ""]
    for fil, nom in FILTRES.items():
        L.append(f"== {nom}")
        for titre, rsi, compte, lim in etapes:
            L.append(titre)
            for g in GROUPES:
                a, z = groupes[g][:2]
                dd = np.arange(max(a, d0), min(z, d1), dtype=np.int64)
                lims = lim30[dd] if lim is None else np.full(len(dd), lim)
                x = np.concatenate([CH.defis(dd, lims, rsi, P["kN"], P["kE"], b, compte, leviers13) for b in P["bases"][fil]])
                iss = x[:, 0]
                v, p, e = (100 * float((iss == k).mean()) for k in (1, -1, 0))
                ref = ""
                if lim is None and rsi == 4:
                    r = publie[fil][g]
                    ref = f"   (publie : {100 * r['valide']:.1f} / {100 * r['perdu']:.1f} / {100 * r['expire']:.1f})"
                L.append(f"    {g:<31} {len(x):6d} departs  valide {v:5.1f}  perdu {p:5.1f}  expire {e:5.1f}{ref}")
        L.append("")
    # 5. plus haut de fin de journee deja au-dessus de 50 000 $ (gains rendus avant le 20 octobre) : plancher plus haut
    defi = defi_pic()
    L += ["5. comme 4, avec un plus haut de fin de journee deja atteint (plancher = plus haut - 2 500 $, bloque a 50 100 $),"
          " solde revenu a 50 000 $", "   (pic0 = 0 redonne exactement l'etape 4 : controle ci-dessous)"]
    for fil in ("fort", "aucun"):
        L.append(f"== {FILTRES[fil]}")
        for pic0 in (0.0, 500.0, 1000.0, 1500.0, 2000.0):
            cells = []
            for g in GROUPES[:2]:
                a, z = groupes[g][:2]
                dd = np.arange(max(a, d0), min(z, d1), dtype=np.int64)
                iss = []
                for b in P["bases"][fil]:
                    for d in dd:
                        ts, tp, tt = np.zeros(17), np.zeros(17), np.zeros(17, np.int64)
                        iss.append(defi(int(d), 16, 0, P["kN"], P["kE"], *b, *compte1000, *leviers13, ts, tp, tt, pic0)[0])
                iss = np.array(iss)
                cells.append(f"{g} : valide {100 * (iss == 1).mean():5.1f}  perdu {100 * (iss == -1).mean():5.1f}"
                             f"  expire {100 * (iss == 0).mean():5.1f}")
            L.append(f"    plus haut {50000 + pic0:,.0f} $ (plancher {min(50000 + pic0 - 2500, 50100):,.0f} $) : " + " | ".join(cells))
        L.append("")
    (ICI / "chances.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
