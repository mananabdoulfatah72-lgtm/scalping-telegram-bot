#!/usr/bin/env python3
"""Vague 8 (README.md) : la bonne taille. 60 candidates = 5 comptes (LucidFlex 50K/100K/150K, Topstep 50K, FundedNext
Legacy 50K) x 4 regles pour la zone (MNQ toujours, MES toujours, MES sous 1,5x ou 2x la perte permise de coussin) x 3
coussins gardes apres un retrait (0, 1x, 2x la perte permise). Bot zone + RSI(2) de nuit sur 1 MES, taille 1x partout.
Mesures : sur les achats (challenge perdu, compte finance perdu dans les 12 mois) et gain net par mois d'un seul compte a
la fois. Jugement : securite d'abord. Ecrit vague8.txt et vague8.json. `python3 vague8.py rapide` : 2 tirages (essai)."""
import itertools
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "vague6"))
import vague6 as V6  # noqa: E402

W, D4, M4, S = V6.W, V6.D4, V6.M4, V6.S
MOIS, FEN, BON = V6.MOIS, V6.FEN, V6.BON
H = 504                                                         # gain net d'un achat : sur ses 24 premiers mois
H_SUIVI = 756                                                   # suivi d'un achat (revue) : 36 mois au plus
TIRAGES = 10
SANS = "sans filtre"


def _f(perte, jours_seuil, plafond):
    """Compte finance LucidFlex : perte, blocage +100 $, pas de limite du jour, 5 jours a +seuil par cycle, pas de
    regularite, 500 $ au moins, plafond par retrait, 50 % du gain du cycle, solde garde 0, pas de nombre maximal."""
    return (perte, 100.0, 0.0, 5, jours_seuil, 0.0, 500.0, np.array([plafond]), 0.5, 0.0, 0)


# compte : (challenge, finance, part du trader, (prix, mensuel, activation), perte permise, part_cycle)
COMPTES = {
    "LucidFlex 50K": ((3000.0, 2000.0, 0, 100.0, 0.0, 0.50, 1), _f(2000.0, 150.0, 2000.0), 0.9, (146.0, False, 0.0),
                      2000.0, 1),
    "LucidFlex 100K": ((6000.0, 3000.0, 0, 100.0, 0.0, 0.50, 1), _f(3000.0, 200.0, 2500.0), 0.9, (293.0, False, 0.0),
                       3000.0, 1),
    "LucidFlex 150K": ((9000.0, 4500.0, 0, 100.0, 0.0, 0.50, 1), _f(4500.0, 250.0, 3000.0), 0.9, (407.0, False, 0.0),
                       4500.0, 1),
    "Topstep 50K": V6.INTRADAY["Topstep"] + (2000.0, 0),
    "FundedNext Legacy 50K": V6.INTRADAY["FundedNext Legacy"] + (2000.0, 0),
}
ZONES = {"zone MNQ": 0.0, "zone MES": 1e18, "zone MES sous 1,5x": 1.5, "zone MES sous 2x": 2.0}
COUSSINS = (0, 1, 2)                                            # coussin garde apres un retrait, en pertes permises


def candidates():
    return [dict(compte=c, zone=z, k=k) for c, z, k in itertools.product(COMPTES, ZONES, COUSSINS)]


def nom(c):
    return f"{c['compte']}, {c['zone']}, coussin garde {c['k']}x"


def reglages(c):
    """(challenge, finance avec le coussin garde, part, prix, c_mnq, part_cycle)."""
    e, f_, part, prix, perte, pc = COMPTES[c["compte"]]
    f_ = list(f_)
    if c["k"] > 0:
        f_[9] = f_[1] + c["k"] * perte                          # solde garde = plancher bloque + K (K = 0 : comme avant)
    z = ZONES[c["zone"]]
    c_mnq = z if z in (0.0, 1e18) else z * perte
    return e, tuple(f_), part, prix, c_mnq, pc


def un_achat(D, b, d, c, h, ret):
    e, f_, _, _, c_mnq, pc = reglages(c)
    kN, kE = D4.facteurs_jour(D)
    return M4.parcours4(d, 4, 2.0 * kN, 5.0 * kE, ret, *b, *e, *f_, h, 1, 1, 1e18, 0.0, pc, c_mnq)


def lien(c, b):
    """Comme vague6.lien : (d, h, premier) -> (flux net par seance, retraits recus par seance, seances jusqu'a la fin)."""
    D = W.G["D4"]
    _, _, part, (prix, mensuel, activation), _, _ = reglages(c)

    def f(d, h, premier):
        ret = np.zeros(h)
        r = un_achat(D, b, d, c, h, ret)
        fl = ret * part
        for k in range(int(np.ceil(r[1] / MOIS)) if mensuel else 1):
            fl[MOIS * k] -= prix
        if r[0] == 1:
            fl[r[1] - 1] -= activation
        return fl, ret * part, r[6]
    return f


def groupes(D):
    j, nj = D["jours"], len(D["jours"])
    dd = [d for d in range(260, nj) if D["ouvert"][d] == 0][::5]
    t = pd.Timestamp
    return {"achats 2012-2021": [d for d in dd if t("2012-01-01") <= j[d] <= t("2021-12-31")],
            "achats 2023 - mars 2026": [d for d in dd if t("2023-01-01") <= j[d] <= t("2026-03-31")],
            "achats 2025 - mars 2026": [d for d in dd if t("2025-01-01") <= j[d] <= t("2026-03-31")]}


def fin_groupe(D, g):
    """Revue : les achats de la fenetre de choix ne sont pas suivis au-dela du 31 decembre 2022 (rien de la verification)."""
    j = D["jours"]
    return int(np.searchsorted(j, pd.Timestamp("2023-01-01"))) if g == "achats 2012-2021" else len(j)


def achats(args):
    """Une candidate, un scenario, un groupe d'achats : challenge reussi / perdu, temps pour valider, compte finance
    perdu dans les 12 mois, retraits par mois d'un compte finance en vie (x part), gain net par achat sur ses 24 premiers
    mois. Suivi de 36 mois au plus, arrete a la fin du groupe (revue)."""
    c, scen, g = args
    D = W.G["D4"]
    cap = fin_groupe(D, g)
    _, _, part, (prix, mensuel, activation), _, _ = reglages(c)
    iss, nch, perdu12, recu, vie, net = [], [], [], 0.0, 0.0, []
    for b in W.G["bases"][scen]:
        for d in W.G["groupes"][g]:
            sv = min(H_SUIVI, cap - d)
            ret = np.zeros(sv)
            r = un_achat(D, b, d, c, sv, ret)
            iss.append(r[0])
            nch.append(r[1])
            m24 = min(r[1], H)                                  # mois de challenge payes dans les 24 premiers mois
            cout = prix * (np.ceil(m24 / MOIS) if mensuel else 1) + (activation if r[0] == 1 and r[1] <= H else 0.0)
            if r[0] != 1:
                net.append(-cout)
                continue
            fin = r[6] if r[2] else sv
            if sv - r[1] >= 252:
                perdu12.append(bool(r[2]) and fin - r[1] <= 252)
            recu += ret[:fin].sum() * part
            vie += (fin - r[1]) / MOIS
            net.append(ret[:min(fin, H)].sum() * part - cout)
    iss, nch = np.array(iss), np.array(nch)
    ok = iss == 1
    fini = (iss != 0).sum()
    return {"reussi": float(ok.mean()), "perdu": float((iss == -1).sum() / fini) if fini else float("nan"),
            "pas_fini": float((iss == 0).mean()),
            "valide_mois": float(np.median(nch[ok]) / MOIS) if ok.any() else float("nan"),
            "valide_q3": float(np.percentile(nch[ok], 75) / MOIS) if ok.any() else float("nan"),
            "finance_perdu12": float(np.mean(perdu12)) if perdu12 else float("nan"), "n12": len(perdu12),
            "retraits_mois_vie": recu / vie if vie else 0.0, "net_achat": float(np.mean(net)),
            "achats_perdants": float(np.mean(np.array(net) < 0))}


def chaine(args):
    """Comme vague7.mesurer : gain net par mois du calendrier d'un seul compte a la fois."""
    c, scen, fw = args
    D = W.G["D4"]
    j = D["jours"]
    a, z, ndep = FEN[fw]
    w0 = int(np.searchsorted(j, pd.Timestamp(a)))
    w1 = len(j) if z is None else int(np.searchsorted(j, pd.Timestamp(z)))
    mc = pd.PeriodIndex(j[w0:w1], freq="M")
    M_, R_, nb, pire12 = [], [], [], []
    for b in W.G["bases"][scen]:
        f = lien(c, b)
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


def lancer(f, taches):
    with mp.get_context("fork").Pool(4) as p:
        return p.map(f, taches, chunksize=1)


def t_achats(x):
    return (f"challenge reussi {x['reussi']:.0%}, pas fini {x['pas_fini']:.0%}, perdu parmi les termines"
            f" {x['perdu']:.0%}, valide en {x['valide_mois']:.1f} mois"
            f" (3 sur 4 en {x['valide_q3']:.1f}) | finance perdu dans les 12 mois {x['finance_perdu12']:.0%}"
            f" (sur {x['n12']}) | retraits par mois en vie {x['retraits_mois_vie']:,.0f} $ | net par achat (24 premiers mois au"
            f" plus)"
            f" {x['net_achat']:+,.0f} $ | achats qui perdent de l'argent {x['achats_perdants']:.0%}")


def sure(x, seuil):
    return x["perdu"] <= seuil and x["finance_perdu12"] <= seuil


def main(rapide=False):
    t0 = time.time()
    W.regler("regles")
    D = D4.charger()
    W.G["D4"] = D
    nt = 2 if rapide else TIRAGES
    rho = S.rho_2026()
    gardes = {BON: S.gardes_simules(D, rho)[:nt], SANS: [None]}
    W.G["bases"] = {k: [D4.base(D, g) for g in v] for k, v in gardes.items()}
    W.G["groupes"] = groupes(D)
    GA = list(W.G["groupes"])
    CC = candidates()
    assert len(CC) == 60
    res = {}
    t1 = [(c, BON, g) for c in CC for g in GA]
    for (c, sc, g), x in zip(t1, lancer(achats, t1)):
        res[(nom(c), sc, g)] = x
    print(f"achats ({time.time() - t0:.0f} s)", flush=True)
    t2 = [(c, BON, fw) for c in CC for fw in FEN]
    for (c, sc, fw), x in zip(t2, lancer(chaine, t2)):
        res[(nom(c), sc, fw)] = x
    print(f"chaines ({time.time() - t0:.0f} s)", flush=True)
    fc, fv = list(FEN)
    gc, gv, g25 = GA
    L = [f"Vague 8 : la bonne taille. Bot zone + RSI(2) de nuit sur 1 MES, taille 1x ; filtre simule rho {rho:.2f}, {nt}"
         f" tirages ; achats une seance sur cinq, suivis 36 mois au plus (achats 2012-2021 : pas apres 2022) ; chaque trade au niveau d'aujourd'hui de son jour"
         f" d'entree. Donnees jusqu'au {D['jours'][-1].date()}.", ""]
    classe = sorted(CC, key=lambda c: -res[(nom(c), BON, fc)]["moy"])
    for g in GA:
        L += [f"=== {BON} | {g}"] + [f"{nom(c)} | " + t_achats(res[(nom(c), BON, g)]) for c in classe] + [""]
    for fw in FEN:
        L += [f"=== {BON} | un seul compte a la fois | {fw}",
              "candidate | moyenne par mois | mois avec un retrait | achats par an | selon le depart (min - max) | pires"
              " 12 mois de suite (mediane / pire) | par annee : moyenne par mois"]
        L += [f"{nom(c)} | " + W.texte(res[(nom(c), BON, fw)]) for c in classe] + [""]
    # jugement
    L.append("=== Jugement (securite d'abord)")
    sures = [c for c in classe if sure(res[(nom(c), BON, gc)], 0.20)]
    L.append(f"Sures sur les achats 2012-2021 (challenge perdu <= 20 % et finance perdu dans les 12 mois <= 20 %) :"
             f" {len(sures)} sur {len(CC)}")
    retenue = None
    for c in sures:
        xa, xc = res[(nom(c), BON, gv)], res[(nom(c), BON, fv)]
        ok1 = sure(xa, 0.25)
        ok2 = all(v > 0 for v in xc["an"].values())
        L.append(f"{nom(c)} : choix {res[(nom(c), BON, fc)]['moy']:+,.0f} $ par mois ; verification : challenge perdu"
                 f" {xa['perdu']:.0%}, finance perdu dans les 12 mois {xa['finance_perdu12']:.0%} (<= 25 % :"
                 f" {'oui' if ok1 else 'non'}) ; {xc['moy']:+,.0f} $ par mois ; chaque annee positive"
                 f" ({'oui' if ok2 else 'non'}) -> {'VALIDEE' if ok1 and ok2 else 'non validee'}")
        if ok1 and ok2:
            retenue = c
            break
    if retenue is None:
        L.append("=> aucune candidate sure et validee")
    else:
        v = res[(nom(retenue), BON, fv)]["moy"]
        L.append(f"=> retenue : {nom(retenue)} ; verification {v:+,.0f} $ par mois -> objectif de 500 $"
                 f" {'ATTEINT' if v >= 500 else 'PAS ATTEINT'}")
    # descriptif : la meilleure sure de chaque compte, et la retenue, sans filtre
    meill = {}
    for k in COMPTES:
        s_k = [c for c in sures if c["compte"] == k]
        meill[k] = s_k[0] if s_k else min((c for c in CC if c["compte"] == k),
                                          key=lambda c: max(np.nan_to_num(res[(nom(c), BON, gc)]["perdu"], nan=1.0),
                                                            np.nan_to_num(res[(nom(c), BON, gc)]["finance_perdu12"],
                                                                          nan=1.0)))
    L += ["", "=== Meilleure sure de chaque compte (ou la plus sure s'il n'y en a pas)"]
    L += [f"{k} : {nom(c)}" for k, c in meill.items()]
    liste = list({nom(c): c for c in ([retenue] if retenue else []) + list(meill.values())}.values())
    t3 = [(c, SANS, g) for c in liste for g in GA]
    t4 = [(c, SANS, fw) for c in liste for fw in FEN]
    o3, o4 = lancer(achats, t3), lancer(chaine, t4)
    L += ["", f"=== Descriptif : {SANS}"]
    for (c, sc, g), x in zip(t3, o3):
        res[(nom(c), sc, g)] = x
        L.append(f"{nom(c)} | {sc} | {g} | " + t_achats(x))
    for (c, sc, fw), x in zip(t4, o4):
        res[(nom(c), sc, fw)] = x
        L.append(f"{nom(c)} | {sc} | {fw} | " + W.texte(x))
    print(f"fin ({time.time() - t0:.0f} s)", flush=True)
    suf = "_rapide" if rapide else ""
    (ICI / f"vague8{suf}.txt").write_text("\n".join(L) + "\n")
    (ICI / f"vague8{suf}.json").write_text(json.dumps({" | ".join(k): v for k, v in res.items()} |
                                                    {"retenue": nom(retenue) if retenue else None,
                                                     "meilleures": {k: nom(c) for k, c in meill.items()}},
                                                    indent=1, ensure_ascii=False))
    print("\n".join(L))


if __name__ == "__main__":
    main(rapide=len(sys.argv) > 1 and sys.argv[1] == "rapide")
