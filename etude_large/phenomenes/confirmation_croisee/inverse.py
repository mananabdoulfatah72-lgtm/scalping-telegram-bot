#!/usr/bin/env python3
"""etude_large/phenomenes/README.md, « hypothese ajoutee apres l'exploration de B, avant l'ouverture de son coffre »
(commit 9a8ae2b) : les entrees de la zone que l'AUD/JPY residuel ne confirme pas (ecartees par B2) gagnent-elles plus
que les entrees confirmees ? Test I1 au coffre (3 janvier 2023 -> 2 octobre 2026) : Welch unilateral sur le gain par
trade en $ (serie de decision), t >= 2,0. Scores, seuils et decisions exactement ceux de B2 (etude.py, importe sans
changement). Regle R2x (taille doublee sur les entrees non confirmees) seulement si I1 est confirme. Pour
information : B1 et B3, sous-periodes.

Lancer : KB=<branche de recherche extraite> python3 etude_large/phenomenes/confirmation_croisee/inverse.py.
Ecrit resultats_inverse.txt."""
import importlib.util
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ICI = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("piste_b", ICI / "etude.py")
B = importlib.util.module_from_spec(_s)
_s.loader.exec_module(B)
DM, RB, PD, PA = B.DM, B.RB, B.PD, B.PA

COFFRE = (pd.Timestamp("2023-01-03"), pd.Timestamp("2026-10-02"))
EXPLO = (pd.Timestamp("2012-01-01"), pd.Timestamp("2022-12-30"))


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float((a.mean() - b.mean()) / se)


def main():
    fed = set(pd.DatetimeIndex(B.fomc.annonces()))
    rech = pd.read_csv(DM.RECHERCHE)
    robot = pd.read_csv(DM.ROBOT)
    bars = pd.concat([rech, robot[robot["t"] > rech["t"].iloc[-1]]], ignore_index=True)
    z = DM.preparer(bars)
    jours, O, Hm, Lm, C, Pm, V, ech = RB.tableaux(bars)
    complete = RB.seances_completes(Pm)
    tous = DM.trades_zone(z, "2000-01-01", DM.FIN)
    tr = tous[~tous["jour"].isin(fed)].sort_values(["jour", "minute_entree"]).reset_index(drop=True)
    ent = B.entrees(z, tr, complete)
    brut = {"VXX": B.lire_etf("VXX"), "UUP": B.lire_etf("UUP"), "TLT": B.lire_etf("TLT"), "IEF": B.lire_etf("IEF"),
            "AUD": B.lire_histdata("audusd"), "JPY": B.lire_histdata("usdjpy"), "TECH": B.lire_histdata("usatechidxusd"),
            "EUR": B.lire_histdata("eurusd"), "BTC": B.lire_btc()}
    g = {nom: B.grille(b, jours) for nom, b in brut.items()}
    D = B.pipeline(jours, complete, O[:, 0], C, g, ent)["D"]
    jr = ent["jour"]
    usd = ent["usd"]
    L = ["Hypothese inversee de B2 (commit 9a8ae2b, fixee apres l'exploration de B, avant l'ouverture de son coffre)", ""]
    res = {}
    for nom in ("B2", "B1", "B3"):
        d = D[nom]
        note = ~np.isnan(d["sc"])
        nc, cf = note & d["ecarte"], note & ~d["ecarte"]
        lig = []
        for lab, (a, b) in (("exploration 2012 - 2022", EXPLO), ("coffre 2023 - 2 oct. 2026", COFFRE),
                            ("coffre 2023 - 2024", (COFFRE[0], pd.Timestamp("2024-12-31"))),
                            ("coffre 2025 - 2 oct. 2026", (pd.Timestamp("2025-01-01"), COFFRE[1]))):
            m = np.asarray((jr >= a) & (jr <= b))
            t = welch(usd[nc & m], usd[cf & m])
            lig.append(f"{lab} : non confirmees {int((nc & m).sum())} trades {usd[nc & m].mean():+.1f} $, confirmees "
                       f"{int((cf & m).sum())} trades {usd[cf & m].mean():+.1f} $, t de Welch {t:+.2f}")
            if lab.startswith("coffre 2023 - 2 oct"):
                res[nom] = t
        L.append(f"{nom}{' (test I1, principal)' if nom == 'B2' else ' (information)'} :")
        L += ["  " + x for x in lig]
    ok = res["B2"] >= 2.0
    L += ["", f"DECISION I1 : t de Welch au coffre {res['B2']:+.2f} -> {'CONFIRMEE' if ok else 'NON CONFIRMEE (t < 2,0)'}"]
    if not ok:
        L.append("La regle R2x n'est pas testee (fixe d'avance : seulement si I1 est confirme).")
    else:
        L.append("I1 confirmee : R2x a tester selon le README (non fait automatiquement ici).")
    (ICI / "resultats_inverse.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
