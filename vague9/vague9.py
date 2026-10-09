#!/usr/bin/env python3
"""Vague 9 (README.md) : 8 178 regles de confluence sur la zone (ET de 1 a 3 conditions parmi 29, trades non retenus
pas pris ou pris en MES), jugees sur l'objectif du 50K (12 mois sans toucher le plancher de 2 000 $ bloque a +100 $, et
au moins +6 000 $). Choix 2012-2021, jumeau de bruit de toute la recherche (10 fois), verification 2023 - sept. 2025 avec
200 filtres tires au hasard. Ecrit vague9.txt et vague9.json."""
import itertools
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import socle9 as S9  # noqa: E402

G = {}
JUMEAUX, PLACEBOS = 10, 200
PERTE, BLOC, CIBLE = 2000.0, 100.0, 6000.0


def preparer():
    D, T, a3, gardes = S9.charger()
    C, cz, _ = S9.conditions(D, T, gardes)
    noms = list(C) + list(cz[0])
    jour_niv = [k for k in noms if k in list(C)[:16] or k in cz[0]]           # conditions par seance
    # matrice par tirage : 29 x trades
    M = [np.array([C[k] for k in C] + [cz[i][k] for k in cz[i]]) for i in range(len(gardes))]
    grp = {"choix": S9.debuts(D, "2012-01-01", "2021-12-31"), "verification": S9.debuts(D, "2023-01-01", "2025-09-25"),
           "2025": S9.debuts(D, "2025-01-01", "2025-09-25")}
    G.update(D=D, T=T, a3=a3, gardes=gardes, noms=noms, jour_niv=jour_niv, M=M, grp=grp, nj=len(D["jours"]))


def regles():
    n = len(G["noms"])
    combos = [c for k in (1, 2, 3) for c in itertools.combinations(range(n), k)]
    return [(c, m) for c in combos for m in (False, True)]


def mesurer_masques(choisis, mes):
    """choisis : un masque par tirage. Renvoie, par groupe, (objectif tenu, perdu, gain median) moyens sur les tirages."""
    T, a3, nj = G["T"], G["a3"], G["nj"]
    out = {k: np.zeros(3) for k in G["grp"]}
    for i, g in enumerate(G["gardes"]):
        jj = S9.journalier(nj, T, a3, choisis[i], mes, g)
        for k, dd in G["grp"].items():
            ok, pe, fin = S9.objectif(jj, dd, PERTE, BLOC, CIBLE, S9.UN_AN)
            out[k] += (ok.mean(), pe.mean(), np.median(fin))
    return {k: v / len(G["gardes"]) for k, v in out.items()}


def un_lot(args):
    """Toutes les regles d'un lot, avec la matrice de conditions M (reelle ou jumeau)."""
    lot, cle = args
    M = G[cle]
    res = []
    for c, mes in lot:
        ch = [np.logical_and.reduce(M[i][list(c)]) for i in range(len(G["gardes"]))]
        r = mesurer_masques(ch, mes)
        res.append((c, mes, float(np.mean([x.mean() for x in ch])), r))
    return res


def lancer(R, cle):
    lots = [(R[i::16], cle) for i in range(16)]
    with mp.get_context("fork").Pool(4) as p:
        out = p.map(un_lot, lots, chunksize=1)
    return [x for o in out for x in o]


def jumeau(graine):
    """Conditions melangees : par seance pour les conditions de seance (une valeur par jour de trade, jours melanges),
    par trade pour les autres ; memes frequences."""
    rng = np.random.default_rng(graine)
    T = G["T"]
    jours, inv = np.unique(T["d"], return_inverse=True)
    prem = np.r_[0, np.flatnonzero(np.diff(T["d"])) + 1]                    # premier trade de chaque jour
    perm_j = rng.permutation(len(jours))
    out = []
    for M in G["M"]:
        M2 = M.copy()
        for r, nom in enumerate(G["noms"]):
            if nom in G["jour_niv"]:
                M2[r] = M[r][prem][perm_j][inv]
            else:
                M2[r] = M[r][rng.permutation(M.shape[1])]
        out.append(M2)
    return out


def nom_regle(c, mes):
    return " ET ".join(G["noms"][i] for i in c) + (" ; autres trades en MES" if mes else " ; autres trades pas pris")


def main():
    t0 = time.time()
    preparer()
    R = regles()
    assert len(R) == 8178, len(R)
    base = mesurer_masques([np.ones(len(G["T"]["d"]), bool)] * len(G["gardes"]), False)
    reel = lancer(R, "M")
    print(f"reel ({time.time() - t0:.0f} s)", flush=True)
    reel.sort(key=lambda x: -x[3]["choix"][0])
    best = reel[0]
    # jumeaux de bruit
    meilleurs_j = []
    for s in range(JUMEAUX):
        G["MJ"] = jumeau(1000 + s)
        rj = lancer(R, "MJ")
        meilleurs_j.append(max(x[3]["choix"][0] for x in rj))
        print(f"jumeau {s + 1} : meilleur {meilleurs_j[-1]:.1%} ({time.time() - t0:.0f} s)", flush=True)
    battus = sum(best[3]["choix"][0] > m for m in meilleurs_j)
    # placebos sur la verification pour la meilleure regle
    c, mes, part, _ = best
    rng = np.random.default_rng(7)
    nt = len(G["T"]["d"])
    pl = []
    for _ in range(PLACEBOS):
        ch = []
        for i in range(len(G["gardes"])):
            k = int(np.logical_and.reduce(G["M"][i][list(c)]).sum())
            m = np.zeros(nt, bool)
            m[rng.choice(nt, k, replace=False)] = True
            ch.append(m)
        pl.append(mesurer_masques(ch, mes)["verification"][0])
    v = best[3]["verification"]
    pct = float(np.mean(np.array(pl) < v[0]))
    ok1 = battus >= 9
    ok2 = v[0] > base["verification"][0] and v[1] < base["verification"][1]
    ok3 = pct >= 0.90
    f = lambda r: f"objectif tenu {r[0]:.0%}, perdu {r[1]:.0%}, gain median {r[2]:+,.0f} $"     # noqa: E731
    L = [f"Vague 9 : {len(R)} regles de confluence ; objectif = 12 mois sans toucher le plancher (2 000 $ sous le plus haut"
         f" de fin de seance, bloque a +100 $) et au moins +{CIBLE:,.0f} $ ; filtre simule, {len(G['gardes'])} tirages ;"
         f" fin de seance seulement.", "",
         "Bot de depart : " + " | ".join(f"{k} : {f(r)}" for k, r in base.items()), "",
         "=== Les 20 meilleures regles sur le choix (departs 2012-2021)",
         "regle | part des trades gardes | choix | verification (2023 - sept. 2025) | 2025"]
    for c_, m_, p_, r_ in reel[:20]:
        L.append(f"{nom_regle(c_, m_)} | {p_:.0%} | {f(r_['choix'])} | {f(r_['verification'])} | {f(r_['2025'])}")
    L += ["", "=== Jugement",
          f"Meilleure regle : {nom_regle(c, mes)} (trades gardes {part:.0%})",
          f"1. Jumeau de bruit : meilleure regle reelle {best[3]['choix'][0]:.1%} sur le choix ; meilleures des 10 recherches"
          f" sur conditions melangees : {', '.join(f'{m:.1%}' for m in meilleurs_j)} -> battue(s) {battus}/10"
          f" ({'oui' if ok1 else 'non'}, il faut 9)",
          f"2. Verification : {f(v)} contre le bot de depart {f(base['verification'])} ({'oui' if ok2 else 'non'})",
          f"3. Filtres au hasard gardant la meme part des trades : la regle fait mieux que {pct:.0%} d'entre eux"
          f" ({'oui' if ok3 else 'non'}, il faut 90 %)",
          f"=> {'RETENUE : a recalculer avec le moteur exact' if ok1 and ok2 and ok3 else 'NON RETENUE'}"]
    # meilleure regle de chaque taille et chaque facon, pour information
    L += ["", "=== Pour information : la meilleure de chaque taille (1, 2, 3 conditions) et chaque facon"]
    for k in (1, 2, 3):
        for m_ in (False, True):
            x = next(r for r in reel if len(r[0]) == k and r[1] == m_)
            L.append(f"{nom_regle(x[0], x[1])} | {x[2]:.0%} | {f(x[3]['choix'])} | {f(x[3]['verification'])} |"
                     f" {f(x[3]['2025'])}")
    # combien de regles battent le bot sur le choix ET la verification
    nb = sum(r[3]["choix"][0] > base["choix"][0] and r[3]["verification"][0] > base["verification"][0] for r in reel)
    L.append(f"Regles qui font mieux que le bot de depart sur le choix et sur la verification : {nb} sur {len(R)}")
    print(f"fin ({time.time() - t0:.0f} s)", flush=True)
    (ICI / "vague9.txt").write_text("\n".join(L) + "\n")
    (ICI / "vague9.json").write_text(json.dumps({
        "base": {k: list(v) for k, v in base.items()}, "jumeaux": meilleurs_j, "placebos": pl,
        "regles": [{"regle": nom_regle(c_, m_), "conditions": list(c_), "mes": m_, "part": p_,
                    **{k: list(v_) for k, v_ in r_.items()}} for c_, m_, p_, r_ in reel]}, ensure_ascii=False))
    print("\n".join(L))


if __name__ == "__main__":
    main()
