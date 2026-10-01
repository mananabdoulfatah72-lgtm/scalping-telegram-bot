#!/usr/bin/env python3
"""Variantes de la zone de bruit (README.md, partie 2) : tri sur 2011-2022, controle ES, puis 2023-2026 ouvert une fois.
Lancer depuis ce dossier : python3 variantes.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import journal as Z

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tournoi"))
sys.path.insert(0, str(R / "evolution2"))
from explorer import charger, t_stat  # noqa: E402
import tournoi3 as T3  # noqa: E402

ICI = Path(__file__).resolve().parent
MARCHES = {"NQ": ("nasdaq100", 2.0), "ES": ("sp500", 5.0)}
PERIODES = {"2011-2016": (2011, 2016), "2017-2022": (2017, 2022), "2011-2022": (2011, 2022), "2023-2026": (2023, 2026)}


def variantes(J, O, H, L, C, P, X, Q):
    g = T3.veille(J, Q["gex"])
    gex_bas = np.nan_to_num(g < T3.quantile_252(g, 0.5), nan=0).astype(bool)
    return {"V0": dict(propre=False), "V1": dict(), "V2": dict(max_trades=1), "V3": dict(jours=gex_bas),
            "V4": dict(achats_seuls=True), "V5": dict(stop="vwap")}


def main():
    Q = T3.lire_quotidien()
    sortie = []
    ecrire = lambda s="": (print(s, flush=True), sortie.append(s))
    res = {}
    for marche, (fichier, pt) in MARCHES.items():
        J, O, H, L, C, P, X = charger(fichier, fin=None)
        cout = Z.st.cout_aller_retour(fichier)
        cout_auj = cout / C[-1, -1]                                # frais d'aujourd'hui en fraction du prix
        ok = Z.st.journees_completes(P) & ~X["echeance"]
        an = pd.DatetimeIndex(J).year.values
        o0 = O[:, 0]
        vs = variantes(J, O, H, L, C, P, X, Q)
        ecrire(f"=== {marche} ===")
        for nom, kw in vs.items():
            brut, allers = Z.zone(J, O, H, L, C, P, X, **kw)
            r = np.where(ok, (brut - cout * allers) / o0, 0.0)
            r_auj = np.where(ok, brut / o0 - cout_auj * allers, 0.0)
            res[(marche, nom)] = (r, ok, an, brut * pt - cout * allers * pt)
            ts = {p: t_stat(r[ok & (an >= a) & (an <= b)]) for p, (a, b) in PERIODES.items()}
            ecrire(f"  {nom} | " + " | ".join(f"{p} t {v:+.2f}" for p, v in ts.items())
                   + f" | aux frais d'aujourd'hui 2011-2022 t {t_stat(r_auj[ok & (an <= 2022)]):+.2f}"
                   + f" | {int(allers[ok & (an <= 2022)].sum())} trades 2011-2022")
    ecrire("\nTri (README.md) :")
    t = lambda m, n, p: t_stat(res[(m, n)][0][res[(m, n)][1] & (res[(m, n)][2] >= PERIODES[p][0]) & (res[(m, n)][2] <= PERIODES[p][1])])
    retenues = []
    for n in ("V2", "V3", "V4", "V5"):
        e1 = t("NQ", n, "2011-2016") > t("NQ", "V1", "2011-2016") and t("NQ", n, "2017-2022") > t("NQ", "V1", "2017-2022")
        e2 = t("ES", n, "2011-2022") >= t("ES", "V1", "2011-2022")
        r, ok, an, _ = res[("NQ", n)]
        r1 = res[("NQ", "V1")][0]
        c = ok & (an >= 2023)
        diff = t_stat((r - r1)[c])
        e3 = t("NQ", n, "2023-2026") > t("NQ", "V1", "2023-2026") and diff >= 1.65
        passe = e1 and e2 and e3
        if passe:
            retenues.append(n)
        ecrire(f"  {n} : mieux que V1 sur NQ 2011-2016 et 2017-2022 {'OUI' if e1 else 'non'} | pas pire sur ES {'OUI' if e2 else 'non'}"
               f" | 2023-2026 mieux que V1, t de la difference {diff:+.2f} {'OUI' if e3 else 'non'} => {'RETENUE' if passe else 'rejetee'}")
    ecrire(f"\nVariantes retenues : {retenues or 'aucune'}")
    if retenues:
        J, O, H, L, C, P, X = charger("nasdaq100", fin=None)
        kw = {}
        vs = variantes(J, O, H, L, C, P, X, Q)
        for n in retenues:
            kw.update(vs[n])
        brut, allers = Z.zone(J, O, H, L, C, P, X, **kw)
        ok = Z.st.journees_completes(P) & ~X["echeance"]
        an = pd.DatetimeIndex(J).year.values
        r = np.where(ok, (brut - Z.st.cout_aller_retour("nasdaq100") * allers) / O[:, 0], 0.0)
        c = ok & (an >= 2023)
        ans = pd.Series(np.where(ok, brut - 1.5 * allers, 0.0)[c] * 2.0, index=pd.DatetimeIndex(J)[c]).groupby(an[c]).sum()
        passe = t_stat(r[c]) >= 2 and (ans > 0).sum() >= 3
        ecrire(f"Version finale ({' + '.join(['V1'] + retenues)}) sur 2023-2026 : t {t_stat(r[c]):+.2f} | "
               + " ".join(f"{a}:{v:+,.0f}$" for a, v in ans.items()) + f" (1 micro) | {'PASSE' if passe else 'rejetee'}")
    # par annee pour V0 et V1 (information)
    for n in ("V0", "V1"):
        r, ok, an, dol = res[("NQ", n)]
        ecrire(f"NQ {n} par annee (1 micro, $) : " + " ".join(f"{a}:{dol[ok & (an == a)].sum():+,.0f}" for a in range(2011, 2027)))
    (ICI / "variantes.txt").write_text("\n".join(sortie) + "\n")


if __name__ == "__main__":
    main()
