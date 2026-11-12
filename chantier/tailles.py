"""Parties J et K (REGLES.md) : la nuit sur le MES ; gagner plus avec la taille selon la marge, la nuit et le retrait.

Usage : python3 tailles.py j | k     (ecrit resultats/partie_j.txt et partie_k.txt)
"""
import sys

import numpy as np

import compte as Cp
import divers as Dv
import donnees as D
import nuit as Nn
import variantes as V

n0 = V.n0
TAILLES = (0.5, 1.0, 2.0, 3.0, 4.0)
ECHELLES = {"E0": ((0, 1.0),), "E1": ((0, 1.0), (2600, 2.0)), "E2": ((0, 1.0), (2600, 2.0), (3600, 3.0)),
            "E3": ((0, 1.0), (2000, 2.0), (3000, 3.0), (4000, 4.0)), "F2": ((0, 2.0),), "F4": ((0, 4.0),)}
NOMS_E = {"E0": "1 MNQ", "E1": "2 MNQ dès 2 600 $ de marge", "E2": "2 MNQ dès 2 600 $, 3 dès 3 600 $", "E3": "2 MNQ dès 2 000 $, 3 dès 3 000 $, 4 dès 4 000 $",
          "F2": "2 MNQ tout le temps", "F4": "4 MNQ tout le temps"}
FRAIS_MES = 4.5


def nuit_mes():
    """La nuit sur le S&P 24 h, pour 1 MES au prix d'aujourd'hui (5 $ par point x dernier prix du fichier)."""
    X = Nn.construire("usa500idxusd")
    _, _, C, ok = Dv.fenetre("intraday/donnees/sp500_1min.csv.gz")
    pref = float(C[np.nonzero(ok)[0][-1], -1])
    X["E"] = 5.0 * pref; X["tick"] = 0.25 / pref
    return X, pref


class Tables:
    """Resultat et creux de chaque journee, pour chaque taille du bot et chaque nuit : aucune, 1 MNQ, 1/2 MNQ, 1 MES."""

    def __init__(self, B, stop=0.005):
        self.B = B
        Xq = Nn.construire(); gq, cq, _ = Nn.gains(Xq, stop); jq = np.isfinite(Xq["entree"])
        Xe, self.pref_es = nuit_mes(); ge, ce, _ = Nn.gains(Xe, stop, FRAIS_MES); je = np.isfinite(Xe["entree"])
        gh, ch, _ = V.gains_fenetre(Xe, V.barres("usa500idxusd"), "E", 0.0, FRAIS_MES); jh = np.isfinite(gh) & je    # 1 MES de 8 h a 9 h (Paris)
        self.heure = gh[jh]
        z = lambda a, ok: np.where(ok, a, 0.0)
        nuits = {"": (None, None), "nq": (z(gq, jq), z(cq, jq)), "nqd": (z(gq, jq) * 0.5, z(cq, jq) * 0.5), "es": (z(ge, je), z(ce, je)), "ee": (z(gh, jh), z(ch, jh))}
        self.R = {}; self.D = {}
        for b in TAILLES:
            for nom, (g, c) in nuits.items():
                self.R[(b, nom)], self.D[(b, nom)] = B.journees(B.zf, b, 1000.0, None if g is None else g / b, None if c is None else c / b)
        js = {t[0] for t in B.zf}; self.Tbot = np.array([s in js for s in B.test])
        self.jq = jq[B.test]; self.je = je[B.test]; self.jh = jh[B.test]


def politique(echelle="E0", nuit_seuil=None, retrait_min=1000.0, nuit="nq", k=2, demi=False, secours="nuit"):
    return dict(echelle=ECHELLES[echelle], nuit_seuil=nuit_seuil, retrait_min=retrait_min, nuit=nuit, k=k, demi=demi, secours=secours)


def vie2(Tb, pol, i0, prise=None, apres=None, solde0=50000.0, haut0=50000.0, horizon=None):
    """Un Master (puis un funded) comme compte.Banc.vie, avec plusieurs tailles. prise / apres : calendrier de secours
    global de H2 (controle) ; sinon le compteur d'inactivite est tenu pour ce compte."""
    B = Tb.B; R = Tb.R; Dd = Tb.D
    o = dict(issue="en cours", fin=None, j1=None, j3=None, touche_m=-148.0, funded=None, i0=i0)
    solde, haut, base = solde0, haut0, 50000.0; meil = 0.0; jrs = 0; nret = 0; vide = 0; perte = 2500.0; phase = "M"; i_f = None; touche_f = 0.0
    k = pol["k"]; ech = pol["echelle"]; b0 = ech[0][1]; seuil_n = pol["nuit_seuil"]; rmin = pol["retrait_min"]
    fin_i = B.n if horizon is None else min(B.n, i0 + horizon)

    def fin(cause, i):
        if phase == "M":
            o["issue"] = cause; o["fin"] = i
        else:
            o["funded"] = dict(issue=cause, touche=touche_f, fin=i, jours=i - i_f)
        return o
    for i in range(i0, fin_i):
        if i > i0:
            if prise is not None:
                vide = apres[i] if apres[i] >= 0 else vide + B.gap[i]
            else:
                for _ in range(B.gap[i]):                      # jours sans donnees : un secours a 0 $ y est pris si besoin
                    vide = 0 if vide >= k else vide + 1
        if vide >= 5:
            return fin("inactivité", i)
        plancher = min(haut - perte, 50000.0); marge = solde - plancher
        frein = marge < perte - 750.0
        if frein:
            b = b0 / 2
        else:
            b = b0
            for seuil, t in ech:
                if marge >= seuil:
                    b = t
        secours = bool(prise[B.test[i]]) if prise is not None else vide >= k
        nuit = ""
        if seuil_n is not None and marge >= seuil_n and not frein and Tb.jq[i]:
            nuit = "nq"                                        # la nuit comme module de gain : 1 MNQ
        if secours and nuit == "":
            if pol["secours"] == "heure":
                nuit = "ee" if Tb.jh[i] else ""                # 1 MES de 8 h a 9 h (Paris)
            elif frein and pol["demi"]:
                nuit = "nqd" if Tb.jq[i] else ""
            elif frein or pol["nuit"] == "es":
                nuit = "es" if Tb.je[i] else ""
            else:
                nuit = "nq" if Tb.jq[i] else ""
        trade_nuit = nuit != "" or secours                     # un secours dans un trou compte comme un trade a 0 $
        r = R[(b, nuit)][i]
        if solde + Dd[(b, nuit)][i] <= plancher:
            return fin("plancher", i)
        solde += r; haut = max(haut, solde)
        if Tb.Tbot[i] or trade_nuit:
            jrs += 1; vide = 0
        else:
            vide += 1
            if vide >= 5:
                return fin("inactivité", i)
        meil = max(meil, r)
        dispo = solde - 52600.0
        if phase == "M" and nret < 3:
            dispo = min(dispo, 1500.0)
        if jrs >= 10 and dispo >= (rmin if phase == "M" else 1000.0) and solde - base > 0 and meil <= 0.4 * (solde - base):
            solde -= dispo; base = solde; meil = 0.0; jrs = 0; nret += 1
            if phase == "M":
                o["touche_m"] += 0.9 * dispo
                if nret == 1:
                    o["j1"] = i - i0
                if nret == 3:
                    o["j3"] = i - i0; o["issue"] = "3 retraits"
                    phase = "F"; i_f = i; solde = haut = base = 50000.0; meil = 0.0; jrs = 0; nret = 0; perte = 2000.0; vide = 0
            elif i - i_f <= 252:
                touche_f += 0.9 * dispo
        if phase == "F" and i - i_f >= 252:
            o["funded"] = dict(issue="en vie après 1 an", touche=touche_f); return o
    if phase == "F":
        o["funded"] = dict(issue="données finies", touche=touche_f)
    return o


def lancer(Tb, pol, depart=0, prise=None, apres=None):
    B = Tb.B
    return [vie2(Tb, pol, i0, prise, apres) for i0 in range(B.d17 + depart, B.n, 20)]


def bilan(B, vs):
    N = len(vs); part = lambda c: sum(v["issue"] == c for v in vs) / N
    duree = np.array([v["j3"] if v["issue"] == "3 retraits" else (v["fin"] - v["i0"] + 1 if v["fin"] is not None else B.n - v["i0"]) for v in vs], float)
    touche = np.array([v["touche_m"] for v in vs]); j1 = [v["j1"] for v in vs if v["j1"] is not None]; j3 = [v["j3"] for v in vs if v["j3"] is not None]
    avant = np.array([B.jours[v["i0"]] < "2022-01-01" for v in vs])
    taux = lambda g: float(touche[g].sum() / (duree[g].sum() / 21)) if g.any() else float("nan")
    fd = [v["funded"] for v in vs if v["funded"] and v["funded"]["issue"] != "données finies"]
    return dict(departs=N, trois=part("3 retraits"), plancher=part("plancher"), inactivite=part("inactivité"), en_cours=part("en cours"),
                med_j1=float(np.median(j1)) if j1 else None, med_j3=float(np.median(j3)) if j3 else None, touche=float(touche.mean()),
                par_mois=taux(np.ones(N, bool)), par_mois_avant=taux(avant), par_mois_depuis=taux(~avant),
                episodes=len({v["fin"] for v in vs if v["issue"] == "plancher"}),
                funded_n=len(fd), funded_perdu=float(np.mean([f["issue"] in ("plancher", "inactivité") for f in fd])) if fd else None,
                funded_touche=float(np.mean([f["touche"] for f in fd])) if fd else None)


# ====================================================================== partie J : la nuit sur le MES
def partie_j():
    X, pref = nuit_mes(); jou = np.isfinite(X["entree"]); J = X["J"]
    Xq = Nn.construire(); jq = np.isfinite(Xq["entree"])
    L = [f"Partie J : la nuit sur le MES (S&P 500 24 h), achat 18 h, vente 9 h 30 ; 1 MES au prix d'aujourd'hui ({n0(pref)} points, 5 $ par point), frais 4,50 $.",
         f"Nuits jouables : {int(jou.sum())} du {J[jou][0]} au {J[jou][-1]} (Nasdaq : {int(jq.sum())}).", "",
         f"{'variante':<14}{'nuits':>6}{'t':>7}{'t expl':>8}{'t ctrl':>8}{'t a 9$':>8}{'$/nuit':>8}{'$/an':>8}{'pire':>8}{'annees+':>8}{'stops':>6}  verdict"]
    res = {}; ps = []
    for stop in (0.0, 0.005):
        g, creux, stp = Nn.gains(X, stop, FRAIS_MES); g9, _, _ = Nn.gains(X, stop, 2 * FRAIS_MES)
        m = Nn.mesure(X, g, jou); m["t6"] = Nn.mesure(X, g9, jou)["t"]; m["stoppees"] = int(stp.sum()); res[f"stop_{stop}"] = m; ps.append(D.p_unilateral(m["t"]))
    passe = D.bh(ps)
    for k, (cle, m) in enumerate(res.items()):
        cond = [m["t"] >= 2 and passe[k], m["moy_ex"] > 0 and m["moy_ct"] > 0, m["t6"] >= 1.5, m["annees_pos"] >= 10, m["pire"] > -1100]
        m["retenue"] = bool(all(cond))
        raison = "RETENUE" if all(cond) else "échoue : " + ", ".join(x for x, c in zip(("t/BH", "deux périodes", "frais doublés", "années", "pire nuit"), cond) if not c)
        nom = "sans stop" if cle.endswith("0.0") else "stop 0,50 %"
        L.append(f"{nom:<14}{m['n']:>6}{m['t']:>7.2f}{m['t_ex']:>8.2f}{m['t_ct']:>8.2f}{m['t6']:>8.2f}{m['moy']:>8.1f}{m['par_an']:>8.0f}{m['pire']:>8.0f}{m['annees_pos']:>5}/{m['annees']:<2}{m['stoppees']:>6}  {raison}")
    ge, _, _ = Nn.gains(X, 0.0, FRAIS_MES); gq, _, _ = Nn.gains(Xq, 0.0); c = jou & jq
    L += ["", f"Lien avec la nuit du Nasdaq (sans stop, {int(c.sum())} nuits communes) : corrélation {np.corrcoef(ge[c], gq[c])[0, 1]:.2f}.", ""]
    B = Cp.Banc("2026-10-02"); Tb = Tables(B)
    L.append("Dans le compte Master (2017 → 2 octobre 2026, un Master neuf toutes les 20 séances, compteur d'inactivité tenu compte par compte) :")
    for cle, nom, pol in (("mnq", "secours après 2 jours sur 1 MNQ (1 MES sous le frein)", politique()), ("mes", "secours après 2 jours, toujours sur 1 MES", politique(nuit="es"))):
        b = bilan(B, lancer(Tb, pol)); dec = [bilan(B, lancer(Tb, pol, d)) for d in (5, 10, 15)]
        ok = b["inactivite"] == 0 and b["plancher"] <= 0.20 and b["touche"] > 0
        res[cle] = dict(**b, adoptee=bool(ok), plancher_decales=[x["plancher"] for x in dec], trois_decales=[x["trois"] for x in dec])
        L.append(f"  {nom} : {b['trois']:.0%} au 3e retrait, {b['plancher']:.0%} perdus par le plancher, {b['inactivite']:.0%} par l'inactivité ; touché {n0(b['touche'])} $ par Master, "
                 f"{b['par_mois']:.0f} $ par mois de vie ; 1er retrait en {b['med_j1']:.0f} séances, 3e en {b['med_j3']:.0f} ; départs décalés : 3e retrait "
                 f"{min(res[cle]['trois_decales']):.0%} à {max(res[cle]['trois_decales']):.0%}, plancher {min(res[cle]['plancher_decales']):.0%} à {max(res[cle]['plancher_decales']):.0%} "
                 f"→ {'ADOPTÉE' if ok else 'non adoptée'}")
    V.ecrire("partie_j", L, res)


# ====================================================================== partie K : gagner plus
def partie_k(sec="nuit", solde0=50700.0, haut0=51800.0):
    B = Cp.Banc("2026-10-02"); Tb = Tables(B); res = {}; nom_fichier = "partie_k" if sec == "nuit" else "partie_k2"
    # controle : E0, N0, R1 avec le calendrier global de H2 et la demi-taille de MNQ sous le frein
    prise, apres, _ = V.secours_tp(B, 2)
    c = bilan(B, lancer(Tb, politique(demi=True), 0, prise, apres))
    h = Tb.heure
    L = [f"Partie {'K' if sec == 'nuit' else 'K2'} : gagner plus avec la taille selon la marge, la nuit et le retrait (Master Bulenox 50K, 2017 → 2 octobre 2026).",
         f"Contrôle du simulateur : H2 publiait 70 % au 3e retrait, 2 % perdus par le plancher, 2 675 $ touchés ; ici {c['trois']:.1%}, {c['plancher']:.1%}, {n0(c['touche'])} $.", "",
         ("Secours de nuit après 2 jours sans trade dans tous les cas (stop 0,50 %, 1 MNQ, 1 MES sous le frein)." if sec == "nuit" else
          f"Secours après 2 jours sans trade : 1 MES de 8 h à 9 h (Paris), sans stop ({len(h)} nuits : {h.mean():+.1f} $ en moyenne, écart type {h.std(ddof=1):.0f} $, pire {h.min():.0f} $, t {D.tstat(h):.2f}).")
         + " N1 : en plus, la nuit entière sur 1 MNQ (stop 0,50 %) chaque soir dès 2 600 $ de marge.",
         "R1 : retrait dès 1 000 $ disponibles ; R2 : retrait à 1 500 $.", "",
         f"{'politique':<12}{'3e retrait':>11}{'plancher':>10}{'(décalés)':>12}{'inact.':>8}{'1er ret.':>9}{'3e ret.':>8}{'touché':>9}{'$ / mois':>9}{'avant 2022':>11}{'depuis':>8}  verdict"]
    res["controle"] = c; fiches = {}
    for e in ECHELLES:
        for nn, seuil in (("N0", None), ("N1", 2600.0)):
            for rr, rmin in (("R1", 1000.0), ("R2", 1500.0)):
                pol = politique(e, seuil, rmin, secours=sec); cle = f"{e}-{nn}-{rr}"
                b = bilan(B, lancer(Tb, pol)); dec = [bilan(B, lancer(Tb, pol, d)) for d in (5, 10, 15)]
                b["plancher_series"] = [b["plancher"]] + [x["plancher"] for x in dec]; b["par_mois_series"] = [b["par_mois"]] + [x["par_mois"] for x in dec]
                fiches[cle] = (pol, b)
    ref = fiches["E0-N0-R1"][1]
    for cle, (pol, b) in fiches.items():
        ok = (b["inactivite"] == 0 and max(b["plancher_series"]) <= 0.30 and b["par_mois"] >= 1.25 * ref["par_mois"]
              and b["par_mois_avant"] > ref["par_mois_avant"] and b["par_mois_depuis"] > ref["par_mois_depuis"])
        b["adoptee"] = bool(ok) and cle != "E0-N0-R1"; res[cle] = b
        f = lambda x: "—" if x is None else f"{x:.0f}"
        L.append(f"{cle:<12}{b['trois']:>10.0%} {b['plancher']:>9.0%} {f'{min(b['plancher_series']):.0%}-{max(b['plancher_series']):.0%}':>11} {b['inactivite']:>7.0%} {f(b['med_j1']):>8} {f(b['med_j3']):>7} "
                 f"{n0(b['touche']):>8} {b['par_mois']:>8.0f} {b['par_mois_avant']:>10.0f} {b['par_mois_depuis']:>7.0f}  "
                 f"{'référence' if cle == 'E0-N0-R1' else ('ADOPTÉE' if ok else 'non')}")
    adopt = sorted(((b["par_mois"], cle) for cle, (pol, b) in fiches.items() if res[cle]["adoptee"]), reverse=True)
    res["recommandee"] = adopt[0][1] if adopt else None
    L += ["", "Échelles : " + " ; ".join(f"{k} = {v}" for k, v in NOMS_E.items()) + ". Sous 1 750 $ de marge : demi-taille du premier échelon.",
          f"Adoptées : {', '.join(c for _, c in adopt) if adopt else 'aucune'}. Recommandée : {res['recommandee'] or 'aucune'}.", "",
          f"Descriptif : depuis l'état actuel du compte (solde {n0(solde0)} $, plus haut {n0(haut0)} $, marge {n0(solde0 - min(haut0 - 2500, 50000))} $), 250 séances au plus, depuis chaque séance de 2017 à 2025.",
          f"{'politique':<12}{'perdu (plancher)':>17}{'au moins 1 retrait':>20}{'3 retraits':>12}{'1er retrait (séances)':>23}{'touché en 250 séances':>23}"]
    for cle, (pol, b) in fiches.items():
        vs = [vie2(Tb, pol, i0, None, None, solde0, haut0, 250) for i0 in range(B.d17, B.n - 250, 10)]
        j1 = [v["j1"] for v in vs if v["j1"] is not None]
        d = dict(perdu=float(np.mean([v["issue"] == "plancher" for v in vs])), un_retrait=len(j1) / len(vs), trois=float(np.mean([v["issue"] == "3 retraits" for v in vs])),
                 med_j1=float(np.median(j1)) if j1 else None, touche=float(np.mean([v["touche_m"] + 148.0 for v in vs])), inactivite=float(np.mean([v["issue"] == "inactivité" for v in vs])))
        res[cle]["depuis_etat_actuel"] = d
        L.append(f"{cle:<12}{d['perdu']:>16.0%} {d['un_retrait']:>19.0%} {d['trois']:>11.0%} {('—' if d['med_j1'] is None else format(d['med_j1'], '.0f')):>22} {n0(d['touche']):>22}")
    V.ecrire(nom_fichier, L, res)


if __name__ == "__main__":
    for q in sys.argv[1:] or ["j", "k"]:
        {"j": partie_j, "k": partie_k, "k2": lambda: partie_k("heure")}[q]()
        print()
