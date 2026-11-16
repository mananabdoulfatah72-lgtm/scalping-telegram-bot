"""Les 4 portes de l'article, plus la porte 5 (le compte Bulenox), pour chaque idee de usine/REGLES.md.

Usage : KB_MINUTES=<nasdaq100_1min.csv.gz de keen-babbage> python3 usine/portes.py [idee ...] [--nouvelles]
Variables : NPERM_IS (1 000), NPERM_WF (200), PROCESSUS (nombre de coeurs).
Ecrit usine/resultats/<date du calcul>/<idee>.json, ajoute des lignes a usine/registre.csv et imprime un resume.
"""
import csv
import datetime as dt
import json
import math
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import donnees as Dn  # noqa: E402
import moteur as Mo  # noqa: E402

DEV = ("2011-01-03", "2014-12-31")
WF_DEBUT = "2015-01-01"
PAS_JOURS, ANS_TRAIN = 30, 4
NPERM_IS = int(os.getenv("NPERM_IS", "1000"))
NPERM_WF = int(os.getenv("NPERM_WF", "200"))
PROCESSUS = int(os.getenv("PROCESSUS", str(os.cpu_count() or 1)))
INFO = ("zone", "supertrend")          # deja sur le compte : toutes les portes, pour information
SEUIL_P_IS, SEUIL_P_WF, GAIN_AN_MIN = 0.01, 0.01, 1000.0


# ------------------------------------------------------------------------------------------------------------ outils
def pf_de(sp, sn):
    sp, sn = np.asarray(sp, float), np.asarray(sn, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(sn > 0, sp / np.where(sn > 0, sn, 1), np.where(sp > 0, np.inf, np.nan))
    return r


def voisins(i, forme):
    ix = np.unravel_index(i, forme); out = []
    for d in range(len(forme)):
        for pas in (-1, 1):
            j = list(ix); j[d] += pas
            if 0 <= j[d] < forme[d]:
                out.append(int(np.ravel_multi_index(tuple(j), forme)))
    return out


def t_stat(x):
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * math.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else 0.0


def pas_marche(J):
    """Bornes (debut d'entrainement, debut du test, fin du test) en indices de seance, tous les 30 jours depuis 2015."""
    dates = pd.to_datetime(J)
    t = pd.Timestamp(WF_DEBUT); fin = dates[-1]; out = []
    while t <= fin:
        a = int(dates.searchsorted(t - pd.DateOffset(years=ANS_TRAIN)))
        b = int(dates.searchsorted(t)); c = int(dates.searchsorted(t + pd.Timedelta(days=PAS_JOURS)))
        if c > b:
            out.append((a, b, c))
        t += pd.Timedelta(days=PAS_JOURS)
    return out


def marche_en_avant(SP, SN, TOT, PAS):
    """Choisit a chaque pas le reglage au meilleur profit factor sur les 4 ans d'avant ; renvoie les sommes hors echantillon,
    le reglage choisi a chaque pas et le rendement net de chaque seance hors echantillon."""
    CSP = np.concatenate([np.zeros((SP.shape[0], 1)), np.cumsum(SP, axis=1)], axis=1)
    CSN = np.concatenate([np.zeros((SN.shape[0], 1)), np.cumsum(SN, axis=1)], axis=1)
    sp = sn = 0.0; choix = []; serie = np.zeros(SP.shape[1]); dans = np.zeros(SP.shape[1], bool)
    for a, b, c in PAS:
        pf = pf_de(CSP[:, b] - CSP[:, a], CSN[:, b] - CSN[:, a])
        pf = np.where(np.isfinite(pf), pf, np.where(np.isinf(pf), 1e9, 0.0))
        k = int(np.argmax(pf)); choix.append(k)
        sp += CSP[k, c] - CSP[k, b]; sn += CSN[k, c] - CSN[k, b]
        serie[b:c] = TOT[k, b:c]; dans[b:c] = True
    return sp, sn, choix, serie, dans


# ------------------------------------------------------------------------------------------------- travail en parallele
_CTX = {}


def _perm_is(graine):
    c = _CTX; Dd = c["Ddev"]
    O2, H2, L2, C2, V2 = Mo.k_permuter(Dd["O"], Dd["H"], Dd["L"], Dd["C"], Dd["V"], c["masque_dev"], graine)
    P = Mo.deriver(Dd, O2, H2, L2, C2, V2)
    SP, SN, _, _ = Mo.grille_stats(c["strat"], P)
    pf = pf_de(SP[:, c["sel_dev"]].sum(1), SN[:, c["sel_dev"]].sum(1))
    return float(np.nanmax(np.where(np.isinf(pf), 1e9, pf)))


def _perm_wf(graine):
    c = _CTX; D = c["D"]
    O2, H2, L2, C2, V2 = Mo.k_permuter(D["O"], D["H"], D["L"], D["C"], D["V"], c["masque_wf"], graine)
    P = Mo.deriver(D, O2, H2, L2, C2, V2)
    SP, SN, TOT, _ = Mo.grille_stats(c["strat"], P)
    sp, sn, _, _, _ = marche_en_avant(SP, SN, TOT, c["PAS"])
    return float(pf_de(sp, sn))


def parallele(fonction, graines):
    if PROCESSUS <= 1:
        return [fonction(g) for g in graines]
    with mp.get_context("fork").Pool(PROCESSUS) as pool:
        return pool.map(fonction, graines, chunksize=max(1, len(graines) // (PROCESSUS * 8)))


# ------------------------------------------------------------------------------------------------------------- porte 5
def compte(gain, pire, joue, depart, n, solde0, haut0, secours=None):
    """Master Bulenox Option 2 depuis une seance : 0 premier retrait (53 600 $), 1 plancher, 2 inactivite, 3 ni l'un ni
    l'autre ; et le gain (un compte perdu par le plancher compte plancher - depart)."""
    solde, haut, sans = solde0, haut0, 0
    for q in range(n):
        d = depart + q
        pl = min(haut - 2500.0, 50000.0)
        g, p, j = (secours if (secours is not None and sans >= 2) else (gain, pire, joue))
        if solde + p[d] <= pl:
            return 1, pl - solde0
        solde += g[d]
        sans = 0 if j[d] else sans + 1
        if sans >= 5:
            return 2, solde - solde0
        if solde >= 53600.0:
            return 0, solde - solde0
        haut = max(haut, solde)
    return 3, solde - solde0


def porte5(D, P, strat, reglage, J):
    pg, pi = strat["f"](P, **reglage)
    g, p, j = Mo.k_dollars(P["lg"], P["lb"], P["O"], P["H"], P["L"], pg, pi, P["ok"], strat["limite"])
    st = Mo.STRATEGIES["supertrend"]
    sg, sp_, sj = Mo.k_dollars(P["lg"], P["lb"], P["O"], P["H"], P["L"], *st["f"](P, 10, 3.0), P["ok"], 400.0)
    ok = D["complete"]
    debut = int(np.searchsorted(J, WF_DEBUT))
    part = float(j[debut:][ok[debut:]].mean())
    variantes = [("seule", None)] + ([("avec le Supertrend en secours", (sg, sp_, sj))] if part < 0.8 else [])
    S = len(J); res = {"part_seances_tradees": part, "variantes": {}}
    x = g[debut:][ok[debut:]]; r23 = g[J >= "2023-01-01"][ok[J >= "2023-01-01"]]
    cum = np.cumsum(x)
    res["dollars"] = dict(gain_par_an=float(x.mean() * 252), t=t_stat(x), t_depuis_2023=t_stat(r23),
                          pire_baisse=float((cum - np.maximum.accumulate(cum)).min()), pire_seance=float(x.min()))
    for nom, sec in variantes:
        v = {}
        for scen, s0, h0 in (("neuf", 50000.0, 50000.0), ("marge_700", 49900.0, 51700.0)):
            for n in (22, 250):
                deps = [i for i in range(debut, S - n + 1) if ok[i]]
                r = [compte(g, p, j, i, n, s0, h0, sec) for i in deps]
                iss = np.array([a for a, _ in r]); gg = np.array([b for _, b in r])
                v[f"{scen}_{n}"] = dict(retrait=float(np.mean(iss == 0)), plancher=float(np.mean(iss == 1)),
                                        inactivite=float(np.mean(iss == 2)), ni=float(np.mean(iss == 3)),
                                        gain_moyen=float(gg.mean()), gain_median=float(np.median(gg)), comptes=len(deps))
        res["variantes"][nom] = v
    jouee = "avec le Supertrend en secours" if part < 0.8 else "seule"
    vv = res["variantes"][jouee]["neuf_250"]
    res["jouee"] = jouee
    res["passe"] = bool(vv["retrait"] > vv["plancher"] + vv["inactivite"])
    return res


# ------------------------------------------------------------------------------------------------------------- portes
def evaluer(nom, D, P, PAS, J):
    strat = Mo.STRATEGIES[nom]
    combos, forme = Mo.combinaisons(strat)
    t0 = time.time()
    R = {"idee": nom, "titre": strat["titre"], "reglages": strat["reglages"], "forme": forme, "portes": {}}
    SP, SN, TOT, JOUE = Mo.grille_stats(strat, P)
    ok = D["complete"]
    sel_dev = ok & (J >= DEV[0]) & (J <= DEV[1])
    # porte 1
    pf = pf_de(SP[:, sel_dev].sum(1), SN[:, sel_dev].sum(1))
    pfz = np.where(np.isfinite(pf), pf, 0.0)
    best = int(np.argmax(pfz)); nb = voisins(best, forme); pnb = pfz[nb]
    tb = t_stat(TOT[best, sel_dev])
    plateau = bool(np.mean(pnb > 1.0) >= 2 / 3 and np.median(pnb) > 1 + (pfz[best] - 1) / 2)
    centre = int(np.argmax([np.median(pfz[[i] + voisins(i, forme)]) for i in range(len(combos))]))
    p1 = dict(pf=pfz.tolist(), meilleur=best, reglage_meilleur=combos[best], pf_meilleur=float(pfz[best]), t_meilleur=tb,
              voisins_pf=pnb.tolist(), plateau=plateau, trop_parfait=bool(pfz[best] >= 3), centre=centre,
              reglage_centre=combos[centre], pf_centre=float(pfz[centre]),
              t_grille=[t_stat(TOT[i, sel_dev]) for i in range(len(combos))])
    p1["passe"] = bool(pfz[best] > 1.0 and tb > 1.0 and plateau and not p1["trop_parfait"])
    if "bot" in strat:
        ib = combos.index(strat["bot"]); p1["reglage_bot"] = strat["bot"]; p1["pf_bot"] = float(pfz[ib])
    R["portes"]["1"] = p1
    info = nom in INFO
    verdict = None if p1["passe"] else "rejetee a la porte 1"
    # porte 2
    if p1["passe"] or info:
        fin_dev = int(np.searchsorted(J, DEV[1], side="right"))
        Ddev = {k: (v[:fin_dev] if isinstance(v, np.ndarray) and v.shape[:1] == (len(J),) else v) for k, v in D.items()}
        _CTX.clear(); _CTX.update(strat=strat, Ddev=Ddev, masque_dev=sel_dev[:fin_dev], sel_dev=sel_dev[:fin_dev])
        dist = np.array(parallele(_perm_is, list(range(1, NPERM_IS + 1))))
        pval = float(np.mean(dist >= pfz[best]))
        R["portes"]["2"] = dict(p=pval, permutations=NPERM_IS, pf_reel=float(pfz[best]), distribution=dist.tolist(),
                                passe=bool(pval < SEUIL_P_IS))
        if verdict is None and not R["portes"]["2"]["passe"]:
            verdict = "rejetee a la porte 2"
    # porte 3
    if verdict is None or info:
        sp, sn, choix, serie, dans = marche_en_avant(SP, SN, TOT, PAS)
        pf_oos = float(pf_de(sp, sn)); x = serie[dans & ok]
        gain_an = float(x.mean() * 252 * Mo.DOLLAR)
        jj = pd.Series(serie[dans] * Mo.DOLLAR, index=pd.to_datetime(J[dans]))
        mois = jj.groupby(jj.index.to_period("M")).sum()
        R["portes"]["3"] = dict(pf=pf_oos, gain_par_an=gain_an, t=t_stat(x), seances=int(len(x)),
                                choix=[combos[k] for k in choix], debuts=[str(J[b]) for _, b, _ in PAS],
                                mois=[[str(k), float(v)] for k, v in mois.items()],
                                passe=bool(pf_oos > 1.0 and gain_an >= GAIN_AN_MIN))
        if verdict is None and not R["portes"]["3"]["passe"]:
            verdict = "rejetee a la porte 3"
    # porte 4
    if verdict is None or info:
        masque_wf = ok & (J >= WF_DEBUT)
        _CTX.clear(); _CTX.update(strat=strat, D=D, masque_wf=masque_wf, PAS=PAS)
        dist = np.array(parallele(_perm_wf, list(range(100001, 100001 + NPERM_WF))))
        reel = R["portes"]["3"]["pf"]
        pval = float(np.mean(dist >= reel))
        R["portes"]["4"] = dict(p=pval, permutations=NPERM_WF, pf_reel=reel, distribution=dist.tolist(), passe=bool(pval < SEUIL_P_WF))
        if verdict is None and not R["portes"]["4"]["passe"]:
            verdict = "rejetee a la porte 4"
    # porte 5
    if verdict is None or info:
        R["portes"]["5"] = porte5(D, P, strat, combos[centre], J)
        if "bot" in strat:
            R["portes"]["5"]["reglage_du_bot"] = porte5(D, P, strat, strat["bot"], J)
        if verdict is None and not R["portes"]["5"]["passe"]:
            verdict = "rejetee a la porte 5"
    R["verdict"] = verdict or "passe les 5 portes"
    R["secondes"] = round(time.time() - t0, 1)
    return R


def ligne(R):
    p = R["portes"]; f = lambda k, x: (f"{p[k][x]:.3f}" if k in p else "")  # noqa: E731
    return dict(date=dt.date.today().isoformat(), idee=R["idee"], titre=R["titre"],
                pf_dev=f"{p['1']['pf_meilleur']:.3f}", reglage_dev=json.dumps(p["1"]["reglage_meilleur"]),
                plateau=p["1"]["plateau"], centre=json.dumps(p["1"]["reglage_centre"]),
                p_porte2=f("2", "p"), pf_hors_echantillon=f("3", "pf"),
                gain_an_hors_echantillon=(f"{p['3']['gain_par_an']:.0f}" if "3" in p else ""), p_porte4=f("4", "p"),
                porte5=(json.dumps(p["5"]["variantes"][p["5"]["jouee"]]["neuf_250"]) if "5" in p else ""),
                verdict=R["verdict"])


def principal():
    D = Dn.charger(); P = Mo.deriver(D); J = D["J"]; PAS = pas_marche(J)
    idees = [a for a in sys.argv[1:] if not a.startswith("--")] or list(Mo.STRATEGIES)
    if "--nouvelles" in sys.argv:                       # la nuit : seulement les idees jamais passees par les portes
        reg = ICI / "registre.csv"
        deja = set(pd.read_csv(reg).idee) if reg.exists() else set()
        idees = [k for k in Mo.STRATEGIES if k not in deja]
        if not idees:
            print("Aucune idee nouvelle : rien a calculer ce soir.")
            return
    dossier = ICI / "resultats" / dt.date.today().isoformat(); dossier.mkdir(parents=True, exist_ok=True)
    print(f"Donnees : {len(J)} seances ({D['J'][0]} -> {D['J'][-1]}) ; marche en avant : {len(PAS)} pas de {PAS_JOURS} jours ; "
          f"{NPERM_IS} et {NPERM_WF} permutations ; {PROCESSUS} processus", flush=True)
    for nom in idees:
        R = evaluer(nom, D, P, PAS, J)
        (dossier / f"{nom}.json").write_text(json.dumps(R, ensure_ascii=False, default=float))
        reg = ICI / "registre.csv"; neuf = not reg.exists()
        with open(reg, "a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(ligne(R)))
            if neuf:
                w.writeheader()
            w.writerow(ligne(R))
        p = R["portes"]
        txt = f"{nom:11s} porte 1 : PF {p['1']['pf_meilleur']:.3f} (t {p['1']['t_meilleur']:.2f}, plateau {p['1']['plateau']}) {p['1']['reglage_meilleur']}"
        if "2" in p:
            txt += f" | porte 2 : p {p['2']['p']:.3f}"
        if "3" in p:
            txt += f" | porte 3 : PF {p['3']['pf']:.3f}, {p['3']['gain_par_an']:+,.0f} $/an"
        if "4" in p:
            txt += f" | porte 4 : p {p['4']['p']:.3f}"
        if "5" in p:
            v = p["5"]["variantes"][p["5"]["jouee"]]["neuf_250"]
            txt += f" | porte 5 ({p['5']['jouee']}) : retrait {v['retrait']:.0%}, perdu {v['plancher'] + v['inactivite']:.0%}"
        print(txt + f" => {R['verdict']} ({R['secondes']} s)", flush=True)


if __name__ == "__main__":
    principal()
