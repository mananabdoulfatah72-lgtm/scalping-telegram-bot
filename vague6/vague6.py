#!/usr/bin/env python3
"""Vague 6 (README.md) : 42 candidates sur 5 comptes (Topstep, LucidFlex, FundedNext Legacy, DayTraders Static, DayTraders
S2L) x taille du challenge (1x, 2x, 3x) x taille du compte finance (1x, 2x) x reserve (S2L seulement). Methode finale de
la vague 5 : chaque trade au niveau d'aujourd'hui de son jour d'entree, compte garde tant qu'il vit, regle d'activite de
DayTraders. Mesure : gain net par mois d'un seul compte a la fois, filtre delta simule aussi bon qu'en 2026. Choix
2012-2022, verification 2023 - sept. 2026. Ecrit vague6.txt et vague6.json."""
import itertools
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "vague5"))
import vague5 as W  # noqa: E402

D4, M4, U, MS, CP, F, S = W.D4, W.M4, W.U, W.MS, W.CP, W.F, W.S
MOIS, TIRAGES, SEUIL = W.MOIS, W.TIRAGES, W.SEUIL
FEN = W.FEN
BON = "filtre aussi bon qu'en 2026 (simule)"
REFERENCE_V5 = 388.0                         # retenue de la vague 5 (Topstep zone + A3, challenge 2x, finance 2x)

# comptes qui ferment chaque soir (moteur de Topstep) : (challenge, finance, part du trader, (prix, mensuel, activation))
# challenge : objectif, perte, mode (0 fin de journee), blocage, limite du jour, regularite, jours mini
# finance : perte, blocage, limite du jour, jours par cycle, seuil d'un jour, regularite, minimum, plafonds, part du
# gain, solde garde, retraits max
INTRADAY = {
    "Topstep": (CP.COMPTES["Topstep"][:7], F.FINANCES["Topstep"]["f"], F.FINANCES["Topstep"]["part"],
                F.FINANCES["Topstep"]["prix"]),
    "LucidFlex": ((3000.0, 2000.0, 0, 100.0, 0.0, 0.50, 1),
                  (2000.0, 100.0, 0.0, 5, 150.0, 0.0, 500.0, np.array([2000.0]), 0.5, 0.0, 0), 0.9, (140.0, False, 0.0)),
    "FundedNext Legacy": ((3000.0, 2000.0, 0, 0.0, 0.0, 0.40, 1),
                          (2000.0, 0.0, 0.0, 5, 200.0, 0.0, 250.0, np.array([6000.0]), 0.5, 0.0, 0), 0.8,
                          (200.0, False, 0.0)),
}
PRIX_STATIC, ACTIVATION_PRO, PRIX_S2L, PART_S2L = 30.0, 130.0, 229.0, 0.8


def candidates():
    out = []
    for compte in ("Topstep", "LucidFlex", "FundedNext Legacy", "Static"):
        for ch, fi in itertools.product((1, 2, 3), (1, 2)):
            out.append(dict(compte=compte, ch=ch, fi=fi, re=0))
    for ch, fi, re in itertools.product((1, 2, 3), (1, 2), (0, 1000, 2000)):
        out.append(dict(compte="S2L", ch=ch, fi=fi, re=re))
    return out


def nom(c):
    bot = "zone + A3" if c["compte"] in INTRADAY else "E4"
    r = f", reserve {c['re']:,} $" if c["compte"] == "S2L" else ""
    return f"{c['compte']} {bot}, challenge {c['ch']}x, finance {c['fi']}x{r}"


def lien(c, b, dll_ferme=False):
    """Fonction (d, h, premier) -> (flux net par seance depuis l'achat, retraits recus par seance, seances jusqu'a la fin
    du compte). dll_ferme : S2L avec une limite du jour definitive (descriptif)."""
    if c["compte"] in INTRADAY:
        D = W.G["D4"]
        e, f_, part, (prix, mensuel, activation) = INTRADAY[c["compte"]]
        kN, kE = D4.facteurs_jour(D)

        def f(d, h, premier):
            ret = np.zeros(h)
            r = M4.parcours4(d, 4, 2.0 * kN, 5.0 * kE, ret, *b, *e, *f_, h, c["ch"], c["fi"], SEUIL, 0.0)
            fl = ret * part
            for k in range(int(np.ceil(r[1] / MOIS)) if mensuel else 1):
                fl[MOIS * k] -= prix
            if r[0] == 1:
                fl[r[1] - 1] -= activation
            return fl, ret * part, r[6]
        return f
    D = W.G["DS"]
    s2l = c["compte"] == "S2L"

    def f(d, h, premier):
        ret = np.zeros(h)
        r = U.achat(D, b, d, "E4", plafond=0.0 if s2l else 500.0, h1=h, h2=h, retraits=ret, niveau="jour",
                    leviers=(c["ch"], c["fi"], SEUIL, float(c["re"])), activite=1, s2l=s2l and not dll_ferme,
                    s2l_ferme=s2l and dll_ferme)
        part = PART_S2L if s2l else 1.0
        fl = ret * part
        fl[0] -= PRIX_S2L if s2l else PRIX_STATIC
        if not s2l and r[MS.ISSUE] == 1:
            fl[int(r[MS.FIN_EVAL]) - 1] -= ACTIVATION_PRO
        if r[MS.ISSUE] == -1:
            fin = int(r[MS.FIN_EVAL])
        elif r[MS.PRO_PERDU] == 1:
            fin = int(r[MS.FIN_PRO])
        else:
            fin = h
        return fl, ret * part, fin
    return f


def bases(c, scen):
    gardes = W.G["gardes"][scen]
    if c["compte"] in INTRADAY:
        return [D4.base(W.G["D4"], g) for g in gardes]
    return [U.base(W.G["DS"], g) for g in gardes]


def mesurer(args):
    """Une candidate, un scenario, une fenetre : gains nets par mois du calendrier de chaque chaine."""
    c, scen, fw, dll_ferme = args
    D = W.G["D4"]
    j = D["jours"]
    a, z, ndep = FEN[fw]
    w0 = int(np.searchsorted(j, pd.Timestamp(a)))
    w1 = len(j) if z is None else int(np.searchsorted(j, pd.Timestamp(z)))
    mc = pd.PeriodIndex(j[w0:w1], freq="M")
    M_, R_, nb, pire12 = [], [], [], []
    for b in bases(c, scen):
        f = lien(c, b, dll_ferme)
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


def main():
    t0 = time.time()
    W.regler("regles")
    W.G["D4"] = D4.charger()
    W.G["DS"] = W.DN.charger()
    j = W.G["D4"]["jours"]
    assert (W.G["DS"]["ouvert"] == W.G["D4"]["ouvert"]).all()
    rho = S.rho_2026()
    W.G["gardes"] = {BON: S.gardes_simules(W.G["D4"], rho)[:TIRAGES], "sans filtre": [None],
                     "filtre inutile (simule)": S.gardes_simules(W.G["D4"], 0.0)[:TIRAGES]}
    CC = candidates()
    assert len(CC) == 42
    entete = ("candidate | moyenne par mois | mois avec un retrait | achats par an | selon le depart (min - max) |"
              " pires 12 mois de suite (mediane / pire) | par annee : moyenne par mois")
    L = [f"Vague 6 : un seul compte a la fois, gains nets par mois du calendrier (retraits x part du trader - prix),"
         f" chaque trade au niveau d'aujourd'hui de son jour d'entree, comptes gardes tant qu'ils vivent, regle d'activite"
         f" de DayTraders ; filtre simule rho {rho:.2f}, {TIRAGES} tirages ; 2x des {SEUIL:,.0f} $ de coussin. Donnees"
         f" jusqu'au {j[-1].date()}.", ""]
    res = {}
    for fw in FEN:
        out = lancer([(c, BON, fw, False) for c in CC])
        for c, x in zip(CC, out):
            res[(nom(c), BON, fw)] = x
        print(f"{fw} ({time.time() - t0:.0f} s)", flush=True)
    fc, fv = list(FEN)
    classe = sorted(CC, key=lambda c: -res[(nom(c), BON, fc)]["moy"])
    for fw in FEN:
        L += [f"=== {fw} | {BON} (classement du choix)", entete]
        L += [f"{nom(c)} | " + W.texte(res[(nom(c), BON, fw)]) for c in classe]
        L.append("")
    L.append("=== Decision")
    retenue = None
    for c in classe:
        x = res[(nom(c), BON, fv)]
        ok1 = x["moy"] >= REFERENCE_V5
        ok2 = all(v > 0 for v in x["an"].values())
        L.append(f"{nom(c)} : choix {res[(nom(c), BON, fc)]['moy']:+,.0f} $ ; verification {x['moy']:+,.0f} $ contre"
                 f" {REFERENCE_V5:+,.0f} $ (vague 5) ({'oui' if ok1 else 'non'}) ; chaque annee positive"
                 f" ({'oui' if ok2 else 'non'}) -> {'VALIDEE' if ok1 and ok2 else 'non validee'}")
        if ok1 and ok2:
            retenue = c
            break
    if retenue is None:
        L.append("=> aucune candidate validee")
    else:
        v = res[(nom(retenue), BON, fv)]["moy"]
        L.append(f"=> retenue : {nom(retenue)} ; verification {v:+,.0f} $ par mois -> objectif de 500 $"
                 f" {'ATTEINT' if v >= 500 else 'PAS ATTEINT'}")
    comptes = ("Topstep", "LucidFlex", "FundedNext Legacy", "Static", "S2L")
    meilleures = {k: next(c for c in classe if c["compte"] == k) for k in comptes}
    L.append("Meilleure de chaque compte (choix) : " + " ; ".join(nom(c) for c in meilleures.values()))
    # descriptif : sans filtre, filtre inutile, pour la retenue et la meilleure de chaque compte
    liste = list({nom(c): c for c in ([retenue] if retenue else []) + list(meilleures.values())}.values())
    taches = [(c, sc, fw, False) for c in liste for sc in ("sans filtre", "filtre inutile (simule)") for fw in FEN]
    taches += [(meilleures["S2L"], BON, fw, True) for fw in FEN]
    out = lancer(taches)
    L += ["", "=== Descriptif : sans filtre, filtre inutile ; S2L avec une limite du jour definitive",
          "candidate | scenario | fenetre | " + entete.split(" | ", 1)[1]]
    for (c, sc, fw, df), x in zip(taches, out):
        sc2 = sc + (" (S2L, limite du jour definitive)" if df else "")
        res[(nom(c), sc2, fw)] = x
        L.append(f"{nom(c)} | {sc2} | {fw} | " + W.texte(x))
    print(f"descriptif ({time.time() - t0:.0f} s)", flush=True)
    (ICI / "vague6.txt").write_text("\n".join(L) + "\n")
    (ICI / "vague6.json").write_text(json.dumps({" | ".join(k): v for k, v in res.items()} |
                                                {"retenue": nom(retenue) if retenue else None,
                                                 "meilleures": meilleures}, indent=1, ensure_ascii=False))
    print("\n".join(L))


if __name__ == "__main__":
    main()
