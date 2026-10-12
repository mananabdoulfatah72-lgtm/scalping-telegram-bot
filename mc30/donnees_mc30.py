#!/usr/bin/env python3
"""Monte Carlo 30 jours (README.md) : l'univers complet des achats de la version D (vague 13), pour la page.
Chaque seance du 3 janvier 2012 au 26 aout 2026 comme jour d'achat, chacun des 21 tirages du filtre simule (10 fort,
10 moitie, 1 sans filtre) ; chaque achat est rejoue avec le moteur exact (vague13/moteur13 : defi13 puis master13, qui
appellent vague4/moteur4.seance4 seance par seance), Bulenox Legacy 50K option 2 :
- challenge de 30 jours : 4 MNQ par source, pas de frein, tout ferme a 53 050 $, 6 MNQ les 5 dernieres seances ;
- Master : 1 MNQ, frein 750 $, plafond du jour 500 $, suivi pendant H + 22 seances apres l'achat (24 mois apres la
  validation au moins, ou jusqu'a la fin des donnees), et jusqu'au 3e retrait (Bulenox passe alors le compte en reel).
Pour chaque achat : issue, solde a la fin de chaque seance du challenge, et au Master la perte eventuelle et les retraits
(seance et montant). Ecrit univers_mc30.json (en-tete) et univers_mc30.bin.gz (tableaux binaires, voir ecrire()).
Usage : python3 donnees_mc30.py"""
import gzip
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
R0 = ICI.parent
sys.path.insert(0, str(R0 / "vague13"))
sys.path.insert(0, str(R0 / "vague12"))
import regles13 as R13  # noqa: E402
import vague12 as V  # noqa: E402

K, M13 = R13.K, R13.M13
P, LIM = V.P, V.LIM
A = K.COMPTES["legacy"]
LETTRE = "D"
TIRAGES = [("fort", t) for t in range(10)] + [("moitie", t) for t in range(10)] + [("aucun", 0)]
JOURS = np.arange(V.D0, V.D1, dtype=np.int64)            # toutes les seances, 2022 comprise (la page n'est pas un choix)
SANS_PERTE = 65535
SUIVI = K.H + 22                                         # 24 mois de Master apres la validation, meme a 22 seances


def achat(b, d):
    sv = min(SUIVI, V.NJ - d)
    lim = int(LIM[d])
    ts, tp, tt = np.zeros(lim + 1), np.zeros(lim + 1), np.zeros(lim + 1, np.int64)
    iss, nch, veut, d2 = M13.defi13(d, lim, 4, P["kN"], P["kE"], *b, *R13.args_defi("legacy", LETTRE), ts, tp, tt)
    sol = np.round(ts[:nch]).astype(np.int64)
    if iss != 1:
        return iss, nch, sol, None
    ret = np.zeros(max(sv, 1))
    F = A["F"]
    perdu, n, recu, prem, fin = M13.master13(d, d2, veut, min(V.NJ, d + sv), 4, P["kN"], P["kE"], ret, *b, *F[:9],
                                             F[9], F[10], A["cycle"], A["frein"], A["cap"])
    msv = min(V.NJ, d + sv) - d - nch                     # seances de Master suivies apres la validation
    perte = (fin - nch) if perdu else SANS_PERTE           # seance (apres la validation) ou le Master est perdu
    idx = np.flatnonzero(ret > 0)
    pay = [(int(i + 1 - nch), int(round(ret[i]))) for i in idx]
    return iss, nch, sol, (perte, msv, pay)


def tache(k):
    fil, t = TIRAGES[k]
    b = P["bases"][fil][t]
    return k, [achat(b, int(d)) for d in JOURS]


def ecrire(R):
    """Tableaux dans l'ordre des chemins (tirage k, puis jour) : issue int8, seances uint8, soldes int16 (ecart au depart,
    code en differences seance par seance), puis pour les valides : perte uint16 (65535 = pas perdu), suivi uint16,
    nombre de retraits uint8 ; retraits : seance uint16, montant uint16."""
    iss, nch, sol, perte, msv, npay, pt, pm = [], [], [], [], [], [], [], []
    for k in range(len(TIRAGES)):
        for i, n, s, m in R[k]:
            iss.append(i)
            nch.append(n)
            sol.extend(np.diff(np.concatenate([[0], s])).tolist())
            if i == 1:
                perte.append(m[0])
                msv.append(m[1])
                npay.append(len(m[2]))
                pt.extend(x[0] for x in m[2])
                pm.extend(x[1] for x in m[2])
    parts = [("iss", np.array(iss, np.int8)), ("nch", np.array(nch, np.uint8)), ("sol", np.array(sol, np.int16)),
             ("perte", np.array(perte, np.uint16)), ("msv", np.array(msv, np.uint16)), ("npay", np.array(npay, np.uint8)),
             ("pt", np.array(pt, np.uint16)), ("pm", np.array(pm, np.uint16))]
    assert max(abs(min(sol)), max(sol)) < 32000 and max(pm) < 65535 and max(nch) < 255
    off, blob, sections = 0, b"", {}
    for nom, a in parts:
        by = a.astype(a.dtype.newbyteorder("<")).tobytes()
        sections[nom] = [off, len(a)]
        blob += by
        off += len(by)
    (ICI / "univers_mc30.bin.gz").write_bytes(gzip.compress(blob, 9, mtime=0))
    return sections, len(blob)


def references(R):
    """Taux de validation calcules ici, pour controler la page (et la vague 13) : par periode et par filtre."""
    j = P["jours"]
    i = lambda x: int(np.searchsorted(j, pd.Timestamp(x)))                              # noqa: E731
    groupes = {"2012-2021": (i("2012-01-01"), i("2022-01-01")), "2023-2026": (i("2023-01-01"), V.D1),
               "2025": (i("2025-01-01"), i("2026-01-01")), "tout": (V.D0, V.D1)}
    out = {}
    for g, (a, z) in groupes.items():
        m = (JOURS >= a) & (JOURS < z)
        for fil in ("fort", "moitie", "aucun"):
            ks = [k for k, (f, _) in enumerate(TIRAGES) if f == fil]
            x = np.concatenate([np.array([r[0] for r in R[k]])[m] for k in ks])
            out[f"{g}|{fil}"] = dict(achats=int(len(x)), valide=float(np.mean(x == 1)), perdu=float(np.mean(x == -1)),
                                     expire=float(np.mean(x == 0)))
    return out


def comparaison():
    """Versions comparees (filtre fort) : bot tel quel (Labo 30 jours) et candidates de la vague 13."""
    v13 = json.loads((R0 / "vague13" / "vague13.json").read_text())
    l30 = json.loads((R0 / "labo30" / "donnees30.json").read_text())["stats"]
    per = {"2012-2021": "choix 2012-2021", "2023-2026": "verification 2023 - aout 2026", "2025": "2025"}
    lignes = [("Bot tel quel (1 MNQ, frein 750)", {g: l30[f"t1|fort|{g}"]["valide"] for g in per})]
    for lettre, nom in (("A", "4 MNQ, sans frein (vague 12)"), ("B", "4 MNQ + arrêt à l'objectif"),
                        ("D", "4 MNQ + arrêt à l'objectif + 6 MNQ en fin de course (retenue)")):
        lignes.append((nom, {g: v13[f"legacy | {lettre}"]["fort"][p]["valide"] for g, p in per.items()}))
    lignes.append(("Retenue, sans le filtre delta", {g: v13["legacy | D"]["aucun"][p]["valide"] for g, p in per.items()}))
    return [dict(nom=n, **v) for n, v in lignes]


def main():
    t0 = time.time()
    with mp.Pool(min(len(TIRAGES), mp.cpu_count())) as pool:
        R = {}
        for k, r in pool.imap_unordered(tache, range(len(TIRAGES))):
            R[k] = r
            print(f"tirage {len(R)}/{len(TIRAGES)} ({time.time() - t0:.0f} s)", flush=True)
    sections, taille = ecrire(R)
    ref = references(R)
    j = P["jours"]
    tete = dict(
        version="D", jours=[str(j[d].date()) for d in JOURS], lim=[int(LIM[d]) for d in JOURS],
        dates_suite=[str(j[d].date()) for d in range(V.D1, V.NJ)],
        tirages=[f"{f}{t}" for f, t in TIRAGES], sections=sections, taille_brute=taille, H=K.H,
        prix=A["prix"], activation=A["activation"], objectif=3000.0, perte_max=2500.0, blocage=100.0, marge=R13.MARGE,
        n_fin=5, taille_ch=4, taille_fin=6, sans_perte=SANS_PERTE, references=ref, comparaison=comparaison(),
        fin_donnees=str(j[V.NJ - 1].date()))
    (ICI / "univers_mc30.json").write_text(json.dumps(tete, ensure_ascii=False))
    gz = (ICI / "univers_mc30.bin.gz").stat().st_size
    print(f"fini en {time.time() - t0:.0f} s ; {len(JOURS)} jours x {len(TIRAGES)} tirages ; "
          f"binaire {taille / 1e6:.2f} Mo, compresse {gz / 1e6:.2f} Mo")
    for g in ("2012-2021", "2023-2026", "2025", "tout"):
        print(g, " ".join(f"{fil} {ref[f'{g}|{fil}']['valide']:.4f}" for fil in ("fort", "moitie", "aucun")))


if __name__ == "__main__":
    main()
