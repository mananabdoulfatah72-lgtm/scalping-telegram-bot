#!/usr/bin/env python3
"""Vague 7 (README.md) : le rebond ajoute au meilleur systeme de chaque compte (vague 6), puis le meilleur challenge 50K.
Methode de la vague 6 : un seul compte a la fois, chaque trade au niveau d'aujourd'hui de son jour d'entree, compte garde
tant qu'il vit, regle d'activite de DayTraders, filtre delta simule aussi bon qu'en 2026. Ecrit vague7.txt et vague7.json."""
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "vague6"))
sys.path.insert(0, str(ICI))
import rebond as RB  # noqa: E402
import vague6 as V6  # noqa: E402

W, D4, U = V6.W, V6.D4, V6.U
FEN, BON, TIRAGES = V6.FEN, V6.BON, V6.TIRAGES
REFERENCE = 410.0                                      # meilleur valide jusqu'ici (S2L, vague 6, suite)
SYSTEMES = [dict(compte="Topstep", ch=3, fi=2, re=0), dict(compte="LucidFlex", ch=3, fi=2, re=0),
            dict(compte="FundedNext Legacy", ch=3, fi=2, re=0), dict(compte="Static", ch=3, fi=2, re=0),
            dict(compte="S2L", ch=1, fi=2, re=6000)]
PRIX = {"Topstep": "49 $ par mois + 149 $ a la reussite", "LucidFlex": "140 $ une fois",
        "FundedNext Legacy": "200 $ une fois", "Static": "30 $ + 130 $ a la reussite", "S2L": "229 $"}


def nom(c, reb):
    return V6.nom(c) + (" + rebond" if reb else "")


def bases(c, scen, reb):
    s = RB.pour(W.G["D4"]) if reb else None
    gardes = W.G["gardes"][scen]
    if c["compte"] in V6.INTRADAY:
        return [D4.base(W.G["D4"], g, rebond=s) for g in gardes]
    return [U.base(W.G["DS"], g, rebond=s) for g in gardes]


def mesurer(args):
    """Comme vague6.mesurer, avec ou sans le rebond."""
    c, reb, scen, fw = args
    D = W.G["D4"]
    j = D["jours"]
    a, z, ndep = FEN[fw]
    w0 = int(np.searchsorted(j, pd.Timestamp(a)))
    w1 = len(j) if z is None else int(np.searchsorted(j, pd.Timestamp(z)))
    mc = pd.PeriodIndex(j[w0:w1], freq="M")
    M_, R_, nb, pire12 = [], [], [], []
    for b in bases(c, scen, reb):
        f = V6.lien(c, b)
        for k in range(ndep):
            fl, rc, n = W.chaine(D, f, w0 + 5 * k, w1)
            m_ = pd.Series(fl[w0:w1]).groupby(mc).sum()
            r_ = pd.Series(rc[w0:w1]).groupby(mc).sum()
            m_[m_.index < mc[5 * k]] = np.nan
            r_[r_.index < mc[5 * k]] = np.nan
            M_.append(m_)
            R_.append(r_)
            nb.append(n / ((w1 - w0 - 5 * k) / 252))
            pire12.append(m_.dropna().rolling(12).sum().min())
    tous = pd.concat(M_, axis=1)
    moy = tous.mean(axis=1)
    an = moy.groupby(moy.index.year).mean()
    rv = pd.concat(R_, axis=1).stack()
    return {"moy": float(moy.mean()), "mois_retrait": float((rv > 0).mean()), "achats_an": float(np.mean(nb)),
            "min_dep": float(tous.mean().min()), "max_dep": float(tous.mean().max()),
            "pire12_med": float(np.nanmedian(pire12)), "pire12_min": float(np.nanmin(pire12)),
            "an": {int(y): float(x) for y, x in an.items()}}


def lancer(taches):
    with mp.get_context("fork").Pool(4) as p:
        return p.map(mesurer, taches, chunksize=1)


def rebond_seul(D):
    """Gain du rebond seul (1 MNQ, au niveau d'aujourd'hui du jour, 3 $ de frais), par annee."""
    s = RB.pour(D).astype(bool)
    kN, _ = D4.facteurs_jour(D)
    der = D["derniere"]
    idx = np.flatnonzero(s)
    g = (D["C"][idx, der[idx]] - D["O"][idx, 0]) * 2.0 * kN[idx] - 3.0
    return pd.Series(g, index=pd.DatetimeIndex(D["jours"][idx])).groupby(lambda t: t.year).agg(["count", "sum"])


def main():
    t0 = time.time()
    W.regler("regles")
    W.G["D4"] = D4.charger()
    W.G["DS"] = W.DN.charger()
    j = W.G["D4"]["jours"]
    rho = V6.S.rho_2026()
    W.G["gardes"] = {BON: V6.S.gardes_simules(W.G["D4"], rho)[:TIRAGES], "sans filtre": [None],
                     "filtre inutile (simule)": V6.S.gardes_simules(W.G["D4"], 0.0)[:TIRAGES]}
    RB.pour(W.G["D4"])
    entete = ("candidate | moyenne par mois | mois avec un retrait | achats par an | selon le depart (min - max) |"
              " pires 12 mois de suite (mediane / pire) | par annee : moyenne par mois")
    L = [f"Vague 7 : le rebond ajoute au meilleur systeme de chaque compte ; un seul compte a la fois, gains nets par mois"
         f" du calendrier, niveau d'aujourd'hui du jour, comptes gardes tant qu'ils vivent ; filtre simule rho {rho:.2f},"
         f" {TIRAGES} tirages. Donnees jusqu'au {j[-1].date()}.", ""]
    taches = [(c, reb, BON, fw) for c in SYSTEMES for reb in (False, True) for fw in FEN]
    out = lancer(taches)
    res = {(nom(c, reb), scen, fw): x for (c, reb, scen, fw), x in zip(taches, out)}
    print(f"calcul ({time.time() - t0:.0f} s)", flush=True)
    fc, fv = list(FEN)
    L += [f"=== {BON}", "candidate | fenetre | " + entete.split(" | ", 1)[1]]
    for c in SYSTEMES:
        for reb in (False, True):
            for fw in FEN:
                L.append(f"{nom(c, reb)} | {fw} | " + W.texte(res[(nom(c, reb), BON, fw)]))
    # 1. le rebond reste-t-il sur chaque compte ?
    L += ["", "=== 1. Le rebond reste sur un compte s'il fait mieux sur le choix ET sur la verification"]
    finaux = []
    for c in SYSTEMES:
        a1, a2 = (res[(nom(c, False), BON, fw)]["moy"] for fw in FEN)
        b1, b2 = (res[(nom(c, True), BON, fw)]["moy"] for fw in FEN)
        garde = b1 > a1 and b2 > a2
        finaux.append((c, garde))
        L.append(f"{c['compte']} : sans rebond {a1:+,.0f} / {a2:+,.0f} $ ; avec {b1:+,.0f} / {b2:+,.0f} $ -> rebond"
                 f" {'GARDE' if garde else 'non'}")
    # 2. le meilleur challenge
    L += ["", "=== 2. Le meilleur challenge (systeme final de chaque compte, classe sur le choix)"]
    classe = sorted(finaux, key=lambda x: -res[(nom(*x), BON, fc)]["moy"])
    retenu = None
    for c, reb in classe:
        x = res[(nom(c, reb), BON, fv)]
        ok1, ok2 = x["moy"] >= REFERENCE, all(v > 0 for v in x["an"].values())
        L.append(f"{nom(c, reb)} ({PRIX[c['compte']]}) : choix {res[(nom(c, reb), BON, fc)]['moy']:+,.0f} $ ;"
                 f" verification {x['moy']:+,.0f} $ contre {REFERENCE:+,.0f} $ ({'oui' if ok1 else 'non'}) ; chaque annee"
                 f" positive ({'oui' if ok2 else 'non'}) -> {'VALIDE' if ok1 and ok2 else 'non valide'}")
        if ok1 and ok2 and retenu is None:
            retenu = (c, reb)
    if retenu is None:
        L.append("=> aucun systeme valide")
    else:
        v = res[(nom(*retenu), BON, fv)]["moy"]
        L.append(f"=> meilleur challenge : {nom(*retenu)} ({PRIX[retenu[0]['compte']]}) ; verification {v:+,.0f} $ par"
                 f" mois -> objectif de 500 $ {'ATTEINT' if v >= 500 else 'PAS ATTEINT'}")
    # descriptif
    t2 = [(c, reb, sc, fw) for c, reb in finaux for sc in ("sans filtre", "filtre inutile (simule)") for fw in FEN]
    out2 = lancer(t2)
    L += ["", "=== Descriptif : sans filtre, filtre inutile (systemes finaux)",
          "candidate | scenario | fenetre | " + entete.split(" | ", 1)[1]]
    for (c, reb, sc, fw), x in zip(t2, out2):
        res[(nom(c, reb), sc, fw)] = x
        L.append(f"{nom(c, reb)} | {sc} | {fw} | " + W.texte(x))
    rs = rebond_seul(W.G["D4"])
    L += ["", "=== Le rebond seul (1 MNQ, niveau d'aujourd'hui du jour, frais compris) : annee | trades | gain",
          " ; ".join(f"{y} : {int(r['count'])} / {r['sum']:+,.0f} $" for y, r in rs.iterrows())]
    print(f"fin ({time.time() - t0:.0f} s)", flush=True)
    (ICI / "vague7.txt").write_text("\n".join(L) + "\n")
    (ICI / "vague7.json").write_text(json.dumps({" | ".join(k): v for k, v in res.items()} |
                                                {"retenu": nom(*retenu) if retenu else None}, indent=1,
                                                ensure_ascii=False))
    print("\n".join(L))


if __name__ == "__main__":
    main()
