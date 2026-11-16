"""Test R de usine/REGLES.md (ajouts du 16 novembre 2026) : sous le frein, faut-il aussi passer le secours sur 1 MES ?

Usage : KB_MINUTES=<nasdaq100_1min.csv.gz> ES_MINUTES=<sp500_1min.csv.gz> python3 usine/pupitre.py
Les deux fichiers viennent de intraday/donnees/ (branche claude/keen-babbage-r686cl).
Ecrit usine/resultats/<date>/pupitre.json et imprime le resume.

Politiques (compte de la porte 5, Supertrend en secours la seance qui suit 2 seances sans trade) :
- P0 : sans frein (controle : sur les donnees de l'usine, elle doit redonner la porte 5 du reglage du bot) ;
- P1 : regle actuelle, zone sur 1 MES sous le frein, secours toujours sur 1 MNQ ;
- P2 : zone et secours sur 1 MES sous le frein.
Le frein est celui du bot (bot3en1/Bot3en1.Core/RegleCompte.cs, branche claude/optimistic-ptolemy-xs24ra) : coussin
(solde - plancher) sous 2 500 - 750 = 1 750 $, avec le plancher de la porte 5.
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import donnees as Dn  # noqa: E402
import moteur as Mo  # noqa: E402
import portes as Po  # noqa: E402

N = Mo.N
DEBUT, FIN_ES = "2015-01-01", "2026-09-25"
PRIX_MNQ = 28500.0                 # niveau du NQ retenu par l'usine (moteur.DOLLAR = 2 $ x 28 500)
FRAIS_MES = 4.50                   # $ l'aller-retour pour 1 MES : 1 $ par ordre et 1 tick (1,25 $) par ordre
GLISSEMENT_MNQ, GLISSEMENT_MES = 2.0, 5.0   # 1 point a la limite du jour : 2 $ sur MNQ (comme moteur.k_dollars), 5 $ sur MES
PERTE_MAX, FREIN = 2500.0, 750.0
ZONE, SUPERTREND = {"k": 1.0, "jours": 14}, {"atr": 10, "multiple": 3.0}


@njit(cache=True)
def k_dollars_p(lg, lb, O, H, L, pg, pi, ok, lim, dollar, cout, gliss):
    """moteur.k_dollars, avec la valeur du contrat, les frais par cote et le glissement de la limite en parametres."""
    S = lg.shape[0]
    gain = np.zeros(S); pire = np.zeros(S); joue = np.zeros(S, np.bool_)
    for s in range(S):
        if not ok[s]:
            continue
        v = 0.0; w = 0.0; prev = 0; stop = False
        for m in range(N):
            a = pg[s, m]; b = pi[s, m]
            if a != 0 or b != 0:
                joue[s] = True
            if m > 0:
                v += dollar * (a * lg[s, m] - cout * abs(a - prev))
                if a != 0 and v <= -lim:
                    v -= gliss + dollar * cout
                    w = min(w, v); stop = True
                    break
            v -= dollar * cout * abs(b - a)
            if b != 0:
                ext = L[s, m] if b > 0 else H[s, m]
                adv = v + dollar * b * np.log(ext / O[s, m])
                if adv <= -lim:
                    v = -lim - gliss - dollar * cout
                    w = min(w, v); stop = True
                    break
                w = min(w, adv)
            v += dollar * b * lb[s, m]
            w = min(w, v)
            prev = b
        if not stop and prev != 0:
            v -= dollar * cout * abs(prev)
            w = min(w, v)
        gain[s] = v; pire[s] = w
    return gain, pire, joue


def compte(jeux, depart, n, solde0, haut0, avec_frein):
    """Master Bulenox Option 2 (porte 5) avec le frein du bot. jeux = (zone, secours, zone sous le frein, secours sous le
    frein), chacun (gain, pire, joue). Renvoie l'issue (0 retrait, 1 plancher, 2 inactivite, 3 ni l'un ni l'autre), le
    gain, et le nombre de seances jouees sous le frein."""
    zone, sec, zone_f, sec_f = jeux
    solde, haut, sans, freinees = solde0, haut0, 0, 0
    for q in range(n):
        d = depart + q
        pl = min(haut - PERTE_MAX, 50000.0)
        frein = avec_frein and (solde - pl < PERTE_MAX - FREIN)
        freinees += int(frein)
        g, p, j = (sec_f if frein else sec) if sans >= 2 else (zone_f if frein else zone)
        if solde + p[d] <= pl:
            return 1, pl - solde0, freinees
        solde += g[d]
        sans = 0 if j[d] else sans + 1
        if sans >= 5:
            return 2, solde - solde0, freinees
        if solde >= 53600.0:
            return 0, solde - solde0, freinees
        haut = max(haut, solde)
    return 3, solde - solde0, freinees


def mesurer(jeux, departs, avec_frein):
    out = {}
    for scen, s0, h0 in (("neuf", 50000.0, 50000.0), ("marge_700", 49900.0, 51700.0)):
        for n in (22, 250):
            r = [compte(jeux, i, n, s0, h0, avec_frein) for i in departs(n)]
            iss = np.array([a for a, _, _ in r]); gg = np.array([b for _, b, _ in r]); ff = np.array([c for _, _, c in r])
            out[f"{scen}_{n}"] = dict(retrait=float(np.mean(iss == 0)), plancher=float(np.mean(iss == 1)),
                                      inactivite=float(np.mean(iss == 2)), ni=float(np.mean(iss == 3)),
                                      perdus=float(np.mean((iss == 1) | (iss == 2))), gain_moyen=float(gg.mean()),
                                      seances_freinees=float(ff.mean()), comptes=len(r))
    return out


def es_aligne(J, kb_es):
    """Minutes du S&P rangees sur les seances du NQ (meme indice de seance), et leurs seances completes."""
    d = pd.read_csv(kb_es, usecols=["t", "o", "h", "l", "c", "v", "contrat"])
    E = Dn.seances(d)
    pos = {j: i for i, j in enumerate(E["J"])}
    S = len(J)
    O = np.ones((S, N)); H = np.ones((S, N)); L = np.ones((S, N)); C = np.ones((S, N)); ok = np.zeros(S, bool)
    for s, j in enumerate(J):
        i = pos.get(j)
        if i is not None:
            O[s], H[s], L[s], C[s], ok[s] = E["O"][i], E["H"][i], E["L"][i], E["C"][i], E["complete"][i]
    lg = np.zeros_like(C); lg[:, 1:] = np.log(O[:, 1:] / C[:, :-1])
    return dict(O=O, H=H, L=L, C=C, ok=ok, lg=lg, lb=np.log(C / O))


def principal():
    D = Dn.charger(); P = Mo.deriver(D); J = D["J"]; ok = D["complete"]; S = len(J)
    dossier = ICI / "resultats" / dt.date.today().isoformat(); dossier.mkdir(parents=True, exist_ok=True)
    zs, ss = Mo.STRATEGIES["zone"], Mo.STRATEGIES["supertrend"]
    zpg, zpi = zs["f"](P, **ZONE); spg, spi = ss["f"](P, **SUPERTREND)
    zone = Mo.k_dollars(P["lg"], P["lb"], P["O"], P["H"], P["L"], zpg, zpi, ok, zs["limite"])
    sec = Mo.k_dollars(P["lg"], P["lb"], P["O"], P["H"], P["L"], spg, spi, ok, ss["limite"])
    # controle 1 : la copie parametree de k_dollars redonne k_dollars sur le NQ
    z2 = k_dollars_p(P["lg"], P["lb"], P["O"], P["H"], P["L"], zpg, zpi, ok, zs["limite"], Mo.DOLLAR, Mo.COUT, GLISSEMENT_MNQ)
    controle_copie = bool(all(np.array_equal(a, b) for a, b in zip(zone, z2)))
    # controle 2 : P0 sur les donnees de l'usine redonne la porte 5 du reglage du bot
    debut = int(np.searchsorted(J, Po.WF_DEBUT))
    dep_usine = lambda n: [i for i in range(debut, S - n + 1) if ok[i]]  # noqa: E731
    p0_usine = mesurer((zone, sec, zone, sec), dep_usine, False)
    ref = Po.porte5(D, P, zs, ZONE, J)["variantes"]["avec le Supertrend en secours"]
    controle_p5 = bool(all(abs(p0_usine[k][x] - ref[k][x]) < 1e-12 for k in ref for x in ("retrait", "plancher", "inactivite", "gain_moyen")))
    # le S&P, aligne sur les seances du NQ ; on garde les seances completes dans les deux fichiers, de 2015 au 25 sept. 2026
    E = es_aligne(J, os.environ["ES_MINUTES"])
    i_fin = int(np.searchsorted(J, FIN_ES))
    prix_es = PRIX_MNQ * E["C"][i_fin, N - 1] / D["C"][i_fin, N - 1]
    dollar_mes = 5.0 * prix_es; cout_mes = FRAIS_MES / 2 / dollar_mes
    ok2 = ok & E["ok"]
    zone_m = k_dollars_p(E["lg"], E["lb"], E["O"], E["H"], E["L"], zpg, zpi, ok2, zs["limite"], dollar_mes, cout_mes, GLISSEMENT_MES)
    sec_m = k_dollars_p(E["lg"], E["lb"], E["O"], E["H"], E["L"], spg, spi, ok2, ss["limite"], dollar_mes, cout_mes, GLISSEMENT_MES)
    garde = np.where(ok2 & (J >= DEBUT) & (J <= FIN_ES))[0]
    serre = lambda x: tuple(a[garde] for a in x)  # noqa: E731
    Z, SC, ZM, SM = serre(zone), serre(sec), serre(zone_m), serre(sec_m)
    dep = lambda n: list(range(0, len(garde) - n + 1))  # noqa: E731
    R = dict(controle_copie_k_dollars=controle_copie, controle_porte5=controle_p5, porte5_usine_P0=p0_usine,
             seances=int(len(garde)), premiere=str(J[garde[0]]), derniere=str(J[garde[-1]]), prix_es_estime=float(prix_es),
             dollar_mes=float(dollar_mes), politiques={})
    for nom, jeux, frein in (("P0", (Z, SC, Z, SC), False), ("P1", (Z, SC, ZM, SC), True), ("P2", (Z, SC, ZM, SM), True)):
        R["politiques"][nom] = mesurer(jeux, dep, frein)
    # par seance, pour information : gain moyen et pire seance de chaque strategie sur MNQ et sur MES
    R["par_seance"] = {nom: dict(gain_moyen=float(g[j].mean()), pire_seance=float(g.min()), pire_moment=float(p.min()),
                                 part_tradee=float(j.mean()))
                       for nom, (g, p, j) in (("zone_MNQ", Z), ("zone_MES", ZM), ("supertrend_MNQ", SC), ("supertrend_MES", SM))}
    P1, P2 = R["politiques"]["P1"], R["politiques"]["P2"]
    R["recommande_P2"] = bool(P2["marge_700_22"]["perdus"] < P1["marge_700_22"]["perdus"]
                              and P2["marge_700_250"]["perdus"] < P1["marge_700_250"]["perdus"]
                              and P2["neuf_250"]["retrait"] >= P1["neuf_250"]["retrait"] - 0.02)
    (dossier / "pupitre.json").write_text(json.dumps(R, ensure_ascii=False, default=float))
    print(f"Controles : copie de k_dollars {controle_copie} ; P0 = porte 5 du reglage du bot {controle_p5}")
    print(f"Seances communes completes : {len(garde)} ({R['premiere']} -> {R['derniere']}) ; S&P estime a {prix_es:,.0f} ; "
          f"1 MES = {dollar_mes:,.0f} $ de notionnel")
    for nom, v in R["par_seance"].items():
        print(f"  {nom:15s} gain moyen les jours trades {v['gain_moyen']:+7.1f} $ ; pire seance {v['pire_seance']:+8.0f} $ ; "
              f"pire moment {v['pire_moment']:+8.0f} $ ; trade {v['part_tradee']:.0%} des seances")
    for nom, v in R["politiques"].items():
        print(nom, " | ".join(f"{k} : retrait {x['retrait']:.1%}, perdus {x['perdus']:.1%} (plancher {x['plancher']:.1%}, "
                                  f"inactivite {x['inactivite']:.1%}), gain moyen {x['gain_moyen']:+,.0f} $"
                                  for k, x in v.items()))
    print("P2 recommandee :", R["recommande_P2"])


if __name__ == "__main__":
    principal()
