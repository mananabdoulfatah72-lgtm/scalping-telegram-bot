#!/usr/bin/env python3
"""Vague 5, etape 2 (README.md) : 40 candidates (Topstep, DayTraders Static, DayTraders S2F) x leviers (taille du compte
finance, reserve, taille du challenge, bot). Mesure : gain net par mois d'un seul compte a la fois, filtre delta simule
aussi bon qu'en 2026. Choix 2012-2022, verification 2023 - sept. 2026. Ecrit vague5.txt et vague5.json."""
import itertools
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
R0 = ICI.parent
sys.path.insert(0, str(R0 / "vague4"))
sys.path.insert(0, str(R0 / "static50k"))
import donnees4 as D4  # noqa: E402
import moteur4 as M4  # noqa: E402
import vague4 as V  # noqa: E402
import donnees as DN  # noqa: E402
import moteur_static as MS  # noqa: E402
import outils as U  # noqa: E402

S, CP, F = V.S, V.CP, V.F
MOIS, H2, TIRAGES = 21, 504, 10
SEUIL, RESERVE = 4000.0, 1000.0
PRIX = {"Static": (30.0, 30.0), "S2F": (570.0, 342.0)}
ACTIVATION_PRO = 130.0
FEN = {"choix 2012-2022": ("2012-01-01", "2023-01-01", 10), "verification 2023 - sept. 2026": ("2023-01-01", None, 20)}
G = {}                                                           # donnees partagees avec les processus (fork)


def candidates():
    out = []
    for bot, ch, fi, re in itertools.product(("zone + A3", "zone seule"), (1, 2), (1, 2), (0, 1)):
        out.append(dict(compte="Topstep", bot=bot, ch=ch, fi=fi, re=re))
    for bot, ch, fi, re in itertools.product(("E0", "E4"), (1, 2), (1, 2), (0, 1)):
        out.append(dict(compte="Static", bot=bot, ch=ch, fi=fi, re=re))
    for bot, fi, re in itertools.product(("E0", "E4"), (1, 2), (0, 1)):
        out.append(dict(compte="S2F", bot=bot, ch=0, fi=fi, re=re))
    return out


def nom(c):
    ch = "" if c["compte"] == "S2F" else f", challenge {c['ch']}x"
    return f"{c['compte']} {c['bot']}{ch}, finance {c['fi']}x, R{1000 * c['re']}"


REFERENCES = {"Topstep": dict(compte="Topstep", bot="zone + A3", ch=1, fi=1, re=0),
              "Static": dict(compte="Static", bot="E0", ch=1, fi=1, re=0),
              "S2F": dict(compte="S2F", bot="E0", ch=0, fi=1, re=0)}


def lien(c, b, pessimiste=0):
    """Fonction (d, h, premier) -> (flux net par seance depuis l'achat, retraits par seance, seances jusqu'a la fin du
    compte)."""
    if c["compte"] == "Topstep":
        D = G["D4"]
        e, f_ = CP.COMPTES["Topstep"][:7], F.FINANCES["Topstep"]["f"]
        prix, _, activation = F.FINANCES["Topstep"]["prix"]
        part = F.FINANCES["Topstep"]["part"]
        rsi = 4 if c["bot"] == "zone + A3" else 0

        def f(d, h, premier):
            fn, fe = D4.facteurs(D, d)
            ret = np.zeros(h)
            r = M4.parcours4(d, rsi, 2.0 * fn, 5.0 * fe, ret, *b, *e, *f_, h, c["ch"], c["fi"], SEUIL,
                             RESERVE * c["re"])
            fl = ret * part
            for k in range(int(np.ceil(r[1] / MOIS))):
                fl[MOIS * k] -= prix
            if r[0] == 1:
                fl[r[1] - 1] -= activation
            return fl, ret * part, r[6]
        return f
    D = G["DS"]
    s2f = c["compte"] == "S2F"
    prix = PRIX[c["compte"]]
    lev = (1 if s2f else c["ch"], c["fi"], SEUIL, RESERVE * c["re"])

    def f(d, h, premier):
        ret = np.zeros(h)
        r = U.achat(D, b, d, c["bot"], plafond=500.0, pessimiste=pessimiste, h1=h, h2=h, retraits=ret, s2f=s2f,
                    leviers=lev)
        fl = ret.copy()
        fl[0] -= prix[0] if premier else prix[1]
        if not s2f and r[MS.ISSUE] == 1:
            fl[int(r[MS.FIN_EVAL]) - 1] -= ACTIVATION_PRO
        if r[MS.ISSUE] == -1:
            fin = int(r[MS.FIN_EVAL])
        elif r[MS.PRO_PERDU] == 1:
            fin = int(r[MS.FIN_PRO])
        else:
            fin = h
        return fl, ret, fin
    return f


def chaine(D, f, d, w1):
    """Un seul compte a la fois, de d a w1 (rachete a la premiere seance ou le RSI(2) est a plat apres la fin du compte).
    Renvoie les flux nets par seance, les retraits par seance et le nombre d'achats."""
    flux, recu, n = np.zeros(len(D["jours"])), np.zeros(len(D["jours"])), 0
    while True:
        while d < w1 and D["ouvert"][d] != 0:
            d += 1
        if d >= w1:
            return flux, recu, n
        h = min(H2, w1 - d)
        fl, ret, fin = f(d, h, n == 0)
        assert 1 <= fin <= h
        flux[d:d + h] += fl
        recu[d:d + h] += ret
        n += 1
        d += fin


def bases(c, scen):
    """Tableaux des moteurs pour chaque tirage du filtre du scenario."""
    gardes = G["gardes"][scen]
    if c["compte"] == "Topstep":
        return [D4.base(G["D4"], g) for g in gardes]
    return [U.base(G["DS"], g) for g in gardes]


def mesurer(args):
    """Une candidate, un scenario, une fenetre : gains nets par mois du calendrier de chaque chaine."""
    c, scen, fw, pessimiste = args
    D = G["D4"]
    j = D["jours"]
    a, z, ndep = FEN[fw]
    w0 = int(np.searchsorted(j, pd.Timestamp(a)))
    w1 = len(j) if z is None else int(np.searchsorted(j, pd.Timestamp(z)))
    mc = pd.PeriodIndex(j[w0:w1], freq="M")
    M_, R_, nb, pire12 = [], [], [], []
    for b in bases(c, scen):
        f = lien(c, b, pessimiste)
        for k in range(ndep):
            fl, rc, n = chaine(D, f, w0 + 5 * k, w1)
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


def texte(x):
    return (f"{x['moy']:+,.0f} $ | {x['mois_retrait']:.0%} | {x['achats_an']:.1f} | {x['min_dep']:+,.0f} a {x['max_dep']:+,.0f} $"
            f" | {x['pire12_med']:+,.0f} / {x['pire12_min']:+,.0f} $ | "
            + ", ".join(f"{y} {v:+,.0f}" for y, v in x["an"].items()))


def lancer(taches):
    with mp.get_context("fork").Pool(4) as p:
        return p.map(mesurer, taches, chunksize=1)


def main():
    t0 = time.time()
    G["D4"] = D4.charger()
    G["DS"] = DN.charger()
    j = G["D4"]["jours"]
    assert (G["DS"]["jours"] == j).all()
    assert (G["DS"]["ouvert"] == G["D4"]["ouvert"]).all()
    assert G["D4"]["Z"][["d", "me", "ms", "sens"]].equals(G["DS"]["Z"][["d", "me", "ms", "sens"]])
    rho = S.rho_2026()
    G["gardes"] = {"filtre aussi bon qu'en 2026 (simule)": S.gardes_simules(G["D4"], rho)[:TIRAGES],
                   "sans filtre": [None], "filtre inutile (simule)": S.gardes_simules(G["D4"], 0.0)[:TIRAGES]}
    BON = "filtre aussi bon qu'en 2026 (simule)"
    CC = candidates()
    assert len(CC) == 40 and all(r in CC for r in REFERENCES.values())
    entete = ("candidate | moyenne par mois | mois avec un retrait | achats par an | selon le depart (min - max) |"
              " pires 12 mois de suite (mediane / pire) | par annee : moyenne par mois")
    L = [f"Vague 5 : un seul compte a la fois, gains nets par mois du calendrier, niveau d'aujourd'hui ; filtre simule"
         f" rho {rho:.2f}, {TIRAGES} tirages ; coussin pour le 2x : {SEUIL:,.0f} $ ; reserve : chaque retrait"
         f" {RESERVE:,.0f} $ sous le plus grand permis."
         f" Donnees jusqu'au {j[-1].date()}.", ""]
    res = {}
    for fw in FEN:
        out = lancer([(c, BON, fw, 0) for c in CC])
        for c, x in zip(CC, out):
            res[(nom(c), BON, fw)] = x
        print(f"{fw} ({time.time() - t0:.0f} s)", flush=True)
    # classement et decision (regles fixees avant le calcul)
    fc, fv = list(FEN)
    classe = sorted(CC, key=lambda c: -res[(nom(c), BON, fc)]["moy"])
    for fw in FEN:
        L += [f"=== {fw} | {BON} (classement du choix)", entete]
        L += [f"{nom(c)} | " + texte(res[(nom(c), BON, fw)]) for c in classe]
        L.append("")
    L.append("=== Decision")
    retenue = None
    for c in classe:
        x, ref = res[(nom(c), BON, fv)], res[(nom(REFERENCES[c["compte"]]), BON, fv)]
        ok1 = x["moy"] >= ref["moy"]
        ok2 = all(v > 0 for v in x["an"].values())
        L.append(f"{nom(c)} : choix {res[(nom(c), BON, fc)]['moy']:+,.0f} $ ; verification {x['moy']:+,.0f} $ contre"
                 f" {ref['moy']:+,.0f} $ pour le systeme actuel ({'oui' if ok1 else 'non'}) ; chaque annee positive"
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
    meilleures = {k: next(c for c in classe if c["compte"] == k) for k in REFERENCES}
    L.append("Meilleure de chaque compte (choix) : " + " ; ".join(f"{k} : {nom(c)}" for k, c in meilleures.items()))
    # descriptif : autres scenarios, Static pessimiste
    garder = [retenue] if retenue else []
    garder += list(meilleures.values()) + list(REFERENCES.values())
    vus, liste = set(), []
    for c in garder:
        if nom(c) not in vus:
            vus.add(nom(c))
            liste.append(c)
    taches = [(c, sc, fw, 0) for c in liste for sc in ("sans filtre", "filtre inutile (simule)") for fw in FEN]
    taches += [(c, BON, fw, 1) for c in liste if c["compte"] == "Static" for fw in FEN]
    out = lancer(taches)
    L += ["", "=== Descriptif : sans filtre, filtre inutile, Static pessimiste (plancher du Pro qui remonte apres un"
              " retrait)", "candidate | scenario | fenetre | " + entete.split(" | ", 1)[1]]
    for (c, sc, fw, pe), x in zip(taches, out):
        k = (nom(c), sc + (" (Pro pessimiste)" if pe else ""), fw)
        res[k] = x
        L.append(f"{k[0]} | {k[1]} | {fw} | " + texte(x))
    print(f"descriptif ({time.time() - t0:.0f} s)", flush=True)
    (ICI / "vague5.txt").write_text("\n".join(L) + "\n")
    (ICI / "vague5.json").write_text(json.dumps({" | ".join(k): v for k, v in res.items()} |
                                                {"retenue": nom(retenue) if retenue else None}, indent=1,
                                                ensure_ascii=False))
    print("\n".join(L))


if __name__ == "__main__":
    main()
