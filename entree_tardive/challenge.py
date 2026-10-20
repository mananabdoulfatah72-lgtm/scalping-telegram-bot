#!/usr/bin/env python3
"""Etude entree_tardive/README.md, mesure 3 : challenge Bulenox Legacy 50K option 2 depuis 0, 16 seances, avec les
trades de chaque variante (trades/<variante>_<periode>.csv, ecrits par etude.py), rejoues minute par minute par le
moteur de la vague 13 (vague13/moteur13.defi13 -> vague4/moteur4.seance4, sans changement) :
- objectif +3 000 $, arret a +3 050 $ dans la journee (arret_obj, marge 50), perte max 2 500 $ en fin de journee
  (plancher = plus haut de fin de journee - 2 500, bloque a +100 comme la vague 13), limite du jour du bot 1 000 $ ;
- 4 MNQ, 6 MNQ les 5 dernieres des 16 seances (fin de course de la version D), pas de zone les jours de la Fed ;
- sans le RSI(2) de nuit (rsi = 0), sans frein MES ; prix au niveau d'aujourd'hui (facteur par seance de la vague 4 :
  derniere cloture des donnees / cloture de la seance d'avant), 3 $ par MNQ et par aller-retour (1,5 point).
Chaque seance de 2012 a 2026 comme premier jour (les 16 seances doivent etre dans les donnees) ; P1 pour information.

0. Controle du branchement : V1 avec les reglages de la vague 13 (D, 30 jours, RSI(2) de nuit, Fed) redonne
   vague13.json, d'abord avec les tableaux de la vague 13, puis avec la zone lue dans trades/H1_15ans.csv ; puis on
   retire une chose a la fois jusqu'aux donnees et reglages de cette etude.

Ecrit resultats_challenge.txt et departs_challenge.csv. Lancer : python3 challenge.py (numba, scipy et pandas requis ;
variables KB (branche de recherche) et NUMBA_CACHE_DIR conseillee pour ne rien ecrire dans KB)."""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.dont_write_bytecode = True
os.environ.setdefault("NUMBA_CACHE_DIR", str(Path(tempfile.gettempdir()) / "numba_entree_tardive"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ICI = Path(__file__).resolve().parent
# branche de recherche extraite a cote du depot :
#   git worktree add ../recherche origin/claude/keen-babbage-r686cl   (ou variable KB)
KB = Path(os.getenv("KB", str(Path(__file__).resolve().parent.parent.parent / "recherche")))
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(KB / "vague13"))
sys.path.insert(0, str(KB / "fonds"))
import etude as ET  # noqa: E402  (barres et chemins de l'etude)
import moteur13 as M13  # noqa: E402
import fomc  # noqa: E402

RB, N = ET.RB, ET.MV.N
LIM = 16
# Bulenox Legacy 50K option 2 : objectif, perte max, mode fin de journee, blocage, limite du jour (bot), regularite, jours
COMPTE = (3000.0, 2500.0, 0, 100.0, 1000.0, 0.0, 1)
# vague 13, version D : (q_ch, c_mnq, arret_obj, marge, q_bas, seuil_bas, q_fin, n_fin, q_but, seuil_but)
LEVIERS_D = (4, 0.0, 1, 50.0, 0, 0.0, 6, 5, 0, 0.0)
SANS_DELTA = ["H1", "E1", "E2", "S1", "L1"]
AVEC_DELTA = ["H1", "E1", "E2", "S1", "L1", "R", "RL", "SANS"]


# ----------------------------------------------------------------------------- donnees de cette etude
def donnees():
    """Minutes du NQ (barres de l'etude : recherche + robot), comme protection.donnees / vague4 : tableaux de robot.py,
    minutes absentes comblees par la suivante, derniere minute, facteur du jour, jours de la Fed."""
    d = ET.barres_15ans()
    jours, O, H, L, C, Pr, V, ech = RB.tableaux(d)
    der = (N - 1 - np.argmax(Pr[:, ::-1], axis=1)).astype(np.int64)
    O, H, L, C = (pd.DataFrame(a).bfill(axis=1).to_numpy() for a in (O, H, L, C))
    nj = len(jours)
    cl = C[np.arange(nj), der]
    kN = 2.0 * cl[-1] / np.r_[cl[0], cl[:-1]]                       # $ par point pour 1 MNQ, au niveau d'aujourd'hui
    j = pd.DatetimeIndex(jours)
    fed = j.isin(fomc.annonces())
    return dict(jours=j, O=O, H=H, L=L, C=C, der=der, kN=kN, fed=fed, cl=cl)


def lire(var, per):
    tr = pd.read_csv(ICI / "trades" / f"{var}_{per}.csv", parse_dates=["jour"])
    return tr[tr["garde"]].copy()


def zone(D, tr):
    """Tableaux de zone du moteur (comme protection.tableaux_zone) : trades tenus, pas les jours de la Fed. Controle que
    les prix d'entree et de sortie du fichier sont ceux des minutes du moteur."""
    j = D["jours"]
    d = np.searchsorted(j, tr["jour"].to_numpy())
    assert (j[d] == tr["jour"].to_numpy()).all()
    me, ms, sens = (tr[c].to_numpy(np.int64) for c in ("minute_entree", "minute_sortie", "sens"))
    assert np.abs(D["C"][d, me] - tr["prix_entree"].to_numpy()).max() < 1e-9
    assert np.abs(D["C"][d, ms] - tr["prix_sortie"].to_numpy()).max() < 1e-9
    garde = ~D["fed"][d]
    o = np.lexsort((me, d))
    d, me, ms, sens, garde = d[o], me[o], ms[o], sens[o], garde[o]
    nj = len(j)
    z_deb = np.searchsorted(d, np.arange(nj)).astype(np.int64)
    z_fin = np.searchsorted(d, np.arange(nj), side="right").astype(np.int64)
    return z_deb, z_fin, me, ms, sens, garde.astype(np.int64), int(garde.sum())


def base(D, zt):
    """Arguments de defi13 apres (debut, lim, rsi, kN, kE) : RSI(2) et ES absents (rsi = 0, zone sur MNQ seulement)."""
    nj = len(D["jours"])
    O, H, L, C = D["O"], D["H"], D["L"], D["C"]
    dec, voulu = np.full(nj, -1, np.int64), np.zeros(nj, np.int64)
    nuit = np.full((nj, 1), np.nan)
    nn = np.zeros(nj, np.int64)
    return (O, H, L, C, D["der"], *zt[:6], dec, voulu, nuit, nuit, nuit, nn, O, H, L, C, nuit, nuit, nuit, nn,
            np.zeros(nj, np.int64))


# ----------------------------------------------------------------------------- challenge
def defis(debuts, lims, rsi, kN, kE, b, compte=COMPTE, leviers=LEVIERS_D):
    """Un challenge par debut : issue (1 valide, -1 perdu, 0 expire), seances jouees, seances ou la limite du jour a
    coupe le bot, et seances jouees en tout."""
    out = np.zeros((len(debuts), 3), np.int64)
    dll = compte[4]
    for i, (d, lim) in enumerate(zip(debuts, lims)):
        ts, tp, tt = np.zeros(lim + 1), np.zeros(lim + 1), np.zeros(lim + 1, np.int64)
        iss, n, _, _ = M13.defi13(int(d), int(lim), rsi, kN, kE, *b, *compte, *leviers, ts, tp, tt)
        g = np.diff(np.r_[0.0, ts[:n]])
        # limite touchee : la seance finit a -(limite + frais de sortie) ou plus bas ; sans elle, au-dessus de
        # -(limite + frais de la derniere sortie) (3 $ par MNQ ; la sortie de la limite coute 3,50 $ par MNQ)
        coupe = int((g <= -(dll + 3.25 * np.abs(tt[:n]))).sum()) if dll > 0 else 0
        out[i] = (iss, n, coupe)
    return out


def resume(x):
    iss, n, coupe = x[:, 0], x[:, 1], x[:, 2]
    v = iss == 1
    return dict(departs=int(len(x)), valides_pct=100 * float(v.mean()), perdus_pct=100 * float((iss == -1).mean()),
                expires_pct=100 * float((iss == 0).mean()),
                seances_valider=float(np.median(n[v])) if v.any() else float("nan"),
                seances_jouees=int(n.sum()), jours_limite=int(coupe.sum()),
                jours_limite_touchee_pct=100 * float(coupe.sum() / n.sum()))


def limite_hors_challenge(D, b, debuts, q=4):
    """Pour comparaison : part des seances (jouees une a une, compte sans plancher ni objectif, q MNQ) ou la limite du
    jour coupe le bot."""
    n = 0
    for d in debuts:
        r = M13.seance4(int(d), 0, 0, 0.0, 0.0, -1e18, 0, COMPTE[1], 1e9, COMPTE[4], *b, D["kN"][d], D["kN"][d], q, 0, 0.0)
        n += r[1] <= -(COMPTE[4] + 3.25 * q)
    return 100 * n / len(debuts)


def debuts_entre(j, a, z, nj_max):
    """Seances de a a z (inclus) dont les LIM seances tiennent dans les nj_max premieres seances."""
    idx = np.flatnonzero((j >= pd.Timestamp(a)) & (j <= pd.Timestamp(z)))
    return idx[idx + LIM <= nj_max].astype(np.int64)


# ----------------------------------------------------------------------------- controle du branchement
def controle():
    """V1 + vague 13 version D (30 jours, Legacy, filtre 'aucun') : redonner vague13.json, puis retirer une chose a la
    fois. Renvoie des lignes de texte et un dict."""
    import regles13 as R13
    K = R13.K
    P = K.MC.preparer()
    j = P["jours"]
    nj = len(j)
    d0, d1, lim30, groupes = K.achats(P)
    ref = json.loads((KB / "vague13" / "vague13.json").read_text())["legacy | D"]["aucun"]
    args = R13.args_defi("legacy", "D")
    compte13, leviers13 = args[:7], args[7:]
    gr = {"choix 2012-2021": groupes["choix 2012-2021"][:2], "verification 2023 - aout 2026":
          groupes["verification 2023 - aout 2026"][:2]}
    L = ["Controle du branchement : V1, Bulenox Legacy, version D de la vague 13 (arret a +3 050 $, 6 MNQ les 5 dernieres"
         " seances, limite de 30 jours calendaires, limite du jour 1 100 $), filtre 'aucun' (sans filtre delta),"
         " pas de zone les jours de la Fed.", ""]
    res = {}

    def ligne(nom, b, rsi, kN, kE, debuts_fn, lims_fn, compte, leviers):
        cells = []
        for g, (a, z) in gr.items():
            dd = debuts_fn(a, z)
            x = defis(dd, lims_fn(dd), rsi, kN, kE, b, compte, leviers)
            r = resume(x)
            cells.append(f"{g} : {r['departs']} departs, valide {r['valides_pct']:.2f} %, perdu {r['perdus_pct']:.2f} %,"
                         f" expire {r['expires_pct']:.2f} %")
            res[(nom, g)] = (r, x)
        L.append(f"- {nom}")
        L.extend(f"    {c}" for c in cells)

    dd13 = lambda a, z: np.arange(max(a, d0), min(z, d1), dtype=np.int64)                  # noqa: E731
    l13 = lambda dd: lim30[dd]                                                               # noqa: E731
    b13 = P["bases"]["aucun"][0]
    L.append("- vague13.json (publie) :")
    for g in gr:
        L.append(f"    {g} : {ref[g]['achats']} achats, valide {100 * ref[g]['valide']:.2f} %, perdu"
                 f" {100 * ref[g]['perdu']:.2f} %, expire {100 * ref[g]['expire']:.2f} %")
    ligne("a. moteur13.defi13, tableaux de la vague 13 (RSI(2) de nuit sur MES)", b13, 4, P["kN"], P["kE"], dd13, l13,
          compte13, leviers13)
    # b. meme chose, zone lue dans trades/H1_15ans.csv (V1 de cette etude), sur les jours de la vague 13
    D13 = P["D"]
    tr = lire("H1", "15ans")
    tr = tr[tr["jour"] <= j[-1]]
    d = np.searchsorted(j, tr["jour"].to_numpy())
    assert (j[d] == tr["jour"].to_numpy()).all()
    assert np.abs(D13["C"][d, tr["minute_entree"].to_numpy()] - tr["prix_entree"].to_numpy()).max() < 1e-9
    assert np.abs(D13["C"][d, tr["minute_sortie"].to_numpy()] - tr["prix_sortie"].to_numpy()).max() < 1e-9
    Zm = pd.DataFrame({"d": d, "me": tr["minute_entree"].to_numpy(), "ms": tr["minute_sortie"].to_numpy(),
                       "sens": tr["sens"].to_numpy()}).sort_values(["d", "me"]).reset_index(drop=True)
    Z13 = D13["Z"]
    memes = set(map(tuple, Zm.to_numpy())) == set(map(tuple, Z13[["d", "me", "ms", "sens"]].to_numpy()))
    pf = ~pd.DatetimeIndex(j).isin(fomc.annonces())
    bm = K.MC.D4.base(dict(D13, Z=Zm), pf[Zm["d"].to_numpy()])
    L.append(f"- zone V1 de la vague 13 = trades/H1_15ans.csv jusqu'au {j[-1].date()} : {memes}"
             f" ({len(Zm)} / {len(Z13)} trades)")
    ligne("b. idem, zone lue dans trades/H1_15ans.csv", bm, 4, P["kN"], P["kE"], dd13, l13, compte13, leviers13)
    ligne("c. b sans le RSI(2) de nuit", bm, 0, P["kN"], P["kE"], dd13, l13, compte13, leviers13)
    # d. donnees de cette etude (barres jusqu'au 19 octobre 2026, facteur sur la derniere cloture), meme reglages que c
    D = donnees()
    jd = D["jours"]
    zt = zone(D, lire("H1", "15ans"))
    bd = base(D, zt)
    lim30d = np.array([int(np.searchsorted(jd, jd[k] + pd.Timedelta(days=30))) - k for k in range(len(jd))])
    a0, a1 = int(np.searchsorted(jd, j[d0])), int(np.searchsorted(jd, j[d1]))
    conv = lambda x: int(np.searchsorted(jd, j[x])) if x < nj else len(jd)                  # noqa: E731
    ddd = lambda a, z: np.arange(max(conv(a), a0), min(conv(z), a1), dtype=np.int64)        # noqa: E731
    ld = lambda dd: lim30d[dd]                                                               # noqa: E731
    ligne("d. c avec les donnees de cette etude (barres jusqu'au 19/10/2026)", bd, 0, D["kN"], D["kN"], ddd, ld,
          compte13, leviers13)
    ligne("e. d avec la limite du jour du bot a 1 000 $ (au lieu de 1 100 $)", bd, 0, D["kN"], D["kN"], ddd, ld,
          COMPTE, leviers13)
    ligne("f. e avec 16 seances au lieu de 30 jours calendaires (reglages de la mesure 3)", bd, 0, D["kN"], D["kN"], ddd,
          lambda dd: np.full(len(dd), LIM), COMPTE, leviers13)
    return L, res


# ----------------------------------------------------------------------------- principal
def main():
    t0 = time.time()
    L0, ctrl = controle()
    print("\n".join(L0), flush=True)
    D = donnees()
    j = D["jours"]
    nj = len(j)
    kN = D["kN"]
    # 15 ans : departs 2012 -> 2026 (16 seances dans les donnees, jusqu'au 19 octobre 2026)
    dd = debuts_entre(j, "2012-01-01", "2026-12-31", nj)
    recent = j[dd] >= pd.Timestamp("2023-01-01")
    lignes, rows, res = [], [], []
    for var in SANS_DELTA:
        zt = zone(D, lire(var, "15ans"))
        bz = base(D, zt)
        x = defis(dd, np.full(len(dd), LIM), 0, kN, kN, bz)
        for nom, m in (("2012-2026", np.ones(len(dd), bool)), ("2023-2026", recent)):
            r = resume(x[m])
            seances = np.arange(dd[m][0], nj)
            res.append(dict(variante=var, periode_departs=nom, **r, trades=zt[6],
                            limite_hors_challenge_pct=limite_hors_challenge(D, bz, seances)))
        rows.append(pd.DataFrame({"variante": var, "donnees": "15 ans sans filtre", "debut": j[dd].date,
                                  "issue": x[:, 0], "seances": x[:, 1], "limite_touchee": x[:, 2]}))
        print(var, res[-2], res[-1], flush=True)
    # P1 (pour information) : vrai delta, trades P1 puis P2 (Rithmic) pour les seances apres le 1er octobre ; departs
    # du 1er avril tant que les 16 seances tiennent avant le 16 octobre (fin du delta Rithmic)
    fin_delta = int(np.searchsorted(j, pd.Timestamp(ET.P2[1]), side="right"))
    dp = debuts_entre(j, ET.P1[0], ET.P1[1], fin_delta)
    res_p1 = []
    for var in AVEC_DELTA:
        tr = pd.concat([lire(var, "P1"), lire(var, "P2")], ignore_index=True)
        zt = zone(D, tr)
        x = defis(dp, np.full(len(dp), LIM), 0, kN, kN, base(D, zt))
        r = resume(x)
        res_p1.append(dict(variante=var, periode_departs=f"P1 {j[dp[0]].date()} - {j[dp[-1]].date()}", **r,
                           trades=zt[6]))
        rows.append(pd.DataFrame({"variante": var, "donnees": "P1 vrai delta", "debut": j[dp].date, "issue": x[:, 0],
                                  "seances": x[:, 1], "limite_touchee": x[:, 2]}))
        print(var, res_p1[-1], flush=True)
    pd.concat(rows).to_csv(ICI / "departs_challenge.csv", index=False)
    ecrire(L0, res, res_p1, D, dd, dp)
    print(f"fini en {time.time() - t0:.0f} s")


def ecrire(L0, res, res_p1, D, dd, dp):
    j = D["jours"]
    r = {(x["variante"], x["periode_departs"]): x for x in res}
    L = ["Mesure 3 (README.md) : challenge Bulenox Legacy 50K option 2 depuis 0, 16 seances, moteur de la vague 13"
         " (moteur13.defi13 / moteur4.seance4, sans changement).",
         "Objectif +3 000 $ (arret a +3 050 $ dans la journee), perte max 2 500 $ en fin de journee (plus haut de fin de"
         " journee depart 50 000 $, plancher bloque a 50 100 $), limite du jour du bot 1 000 $, 4 MNQ puis 6 MNQ les 5"
         " dernieres seances, pas de zone les jours de la Fed, sans RSI(2) de nuit, 3 $ par MNQ et par aller-retour, prix"
         " au niveau d'aujourd'hui (facteur de la vague 4, derniere cloture du 19/10/2026).",
         f"Trades : trades/<variante>_15ans.csv (sans filtre delta). Departs : chaque seance du {j[dd[0]].date()} au"
         f" {j[dd[-1]].date()} (les 16 seances dans les donnees).",
         "Limite touchee : part des seances jouees (tous departs confondus) ou la limite du jour de 1 000 $ a coupe le bot.",
         ""]
    tete = (f"{'var':4s} | {'departs':>7s} {'valide':>7s} {'perdu':>7s} {'expire':>7s} {'seances':>7s} {'limite':>7s} |"
            f" {'departs':>7s} {'valide':>7s} {'perdu':>7s} {'expire':>7s} {'seances':>7s} {'limite':>7s}")
    L += [f"{'':4s} | {'departs 2012-2026':^49s} | {'departs 2023-2026':^49s}", tete, "-" * len(tete)]
    for var in SANS_DELTA:
        c = []
        for p in ("2012-2026", "2023-2026"):
            x = r[(var, p)]
            c.append(f"{x['departs']:7d} {x['valides_pct']:6.1f}% {x['perdus_pct']:6.1f}% {x['expires_pct']:6.1f}%"
                     f" {x['seances_valider']:7.0f} {x['jours_limite_touchee_pct']:6.1f}%")
        L.append(f"{var:4s} | {c[0]} | {c[1]}")
    L.append("(seances : mediane des seances pour valider ; limite : part des seances jouees ou la limite du jour a coupe)")
    L += ["", "Pour comparaison, chaque seance jouee seule en 4 MNQ (sans plancher ni objectif) : part des seances ou la"
          " limite du jour de 1 000 $ coupe le bot (seances du 1er janvier de la periode au 19/10/2026) :"]
    for var in SANS_DELTA:
        L.append(f"- {var} : {r[(var, '2012-2026')]['limite_hors_challenge_pct']:.1f} % (2012-2026),"
                 f" {r[(var, '2023-2026')]['limite_hors_challenge_pct']:.1f} % (2023-2026) ;"
                 f" {r[(var, '2012-2026')]['trades']} trades tenus hors jours de la Fed")
    L += ["", "Critere 2 du README (au moins 2 points de valides de plus que V1 sur 2012-2026, et pas moins que V1 sur"
          " 2023-2026) :"]
    v1a, v1b = r[("H1", "2012-2026")]["valides_pct"], r[("H1", "2023-2026")]["valides_pct"]
    for var in SANS_DELTA[1:]:
        a, b = r[(var, "2012-2026")]["valides_pct"], r[(var, "2023-2026")]["valides_pct"]
        ok = a >= v1a + 2.0 and b >= v1b
        L.append(f"- {var} : {a - v1a:+.1f} points sur 2012-2026, {b - v1b:+.1f} points sur 2023-2026 -> "
                 f"{'passe' if ok else 'ne passe pas'}")
    L += ["", f"Pour information : P1 avec le vrai delta (Databento jusqu'au 01/10/2026, puis Rithmic P2 jusqu'au"
          f" 16/10/2026 pour les seances qui suivent), departs du {j[dp[0]].date()} au {j[dp[-1]].date()} ({len(dp)}"
          " departs qui se chevauchent : tres peu de departs independants, aucune decision).",
          f"{'var':4s} | {'trades':>6s} {'departs':>7s} {'valide':>7s} {'perdu':>7s} {'expire':>7s} {'seances':>7s}"
          f" {'limite':>7s}", "-" * 66]
    for x in res_p1:
        L.append(f"{x['variante']:4s} | {x['trades']:6d} {x['departs']:7d} {x['valides_pct']:6.1f}% {x['perdus_pct']:6.1f}%"
                 f" {x['expires_pct']:6.1f}% {x['seances_valider']:7.0f} {x['jours_limite_touchee_pct']:6.1f}%")
    L.append("(trades : trades tenus hors jours de la Fed sur P1 + P2 ; SANS : la zone sans filtre, pour comparaison)")
    L += [""] + L0
    (ICI / "resultats_challenge.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
