#!/usr/bin/env python3
"""etude_large/pistes/README.md, piste 1 (regles fixees le 22 octobre 2026, commit a6e791f, avant tout calcul) :
sortie VWAP de la zone. Dans le cas vise (acheteur avec ub < C <= VWAP au controle, vente : VWAP <= C < lb), V1 vend puis
rachete au meme prix. Trois facons de traiter ce cas :
- ZL (tenir, reference) : on ne fait rien ; sortie seulement si C <= ub (achat) ou C >= lb (vente), ou a 15 h 59 ;
- ZW (le bot quand le delta est contre) : sortie a C ; plus d'entree dans le meme sens tant qu'un controle n'a pas vu
  C <= ub (achat) ou C >= lb (vente) ; l'autre sens suit la regle normale ;
- ZW+ : sortie a C sans rachat ; a un controle suivant, une nouvelle entree dans le meme sens demande C > max(ub, VWAP)
  (C < min(lb, VWAP) pour une vente).
2 tests bilateraux : series quotidiennes ZW - ZL et ZW+ - ZL, points nets, 0 les jours sans cas.
Exploration 2011-2022, coffre 2023 -> 20 octobre 2026. Pas de zone les jours de la Fed ni les jours courts. 1 MNQ,
1,5 point par aller-retour. Moteur : delta_mesures/etude.py (preparer, trades_zone), challenges : delta_mesures challenge()
(Bulenox, 16 seances depuis 0) et etude_large/partie_d.py (Lucid Flex, 1 MNQ).

Lancer : KB=<branche de recherche extraite> python3 etude_large/pistes/sortie_vwap/etude.py. Ecrit resultats.txt."""
import os
import sys
import tempfile
from collections import defaultdict
from math import erf, sqrt
from pathlib import Path

sys.dont_write_bytecode = True
os.environ.setdefault("NUMBA_CACHE_DIR", str(Path(tempfile.gettempdir()) / "numba_delta_mesures"))

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent.parent
sys.path = [p for p in sys.path if Path(p or ".").resolve() != ICI]       # ce fichier s'appelle aussi etude.py
sys.path.insert(0, str(RACINE / "delta_mesures"))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import etude as DM  # noqa: E402
sys.path.insert(0, str(RACINE / "etude_large"))
import partie_d as PD  # noqa: E402
import partie_a as PA  # noqa: E402
sys.path.insert(0, str(DM.KB / "fonds"))
import fomc  # noqa: E402

N, PAS, COUT = DM.N, DM.PAS, DM.COUT
COUT_ES = 0.9
CONTROLES = list(range(PAS, DM.DERNIERE_ENTREE + 1, PAS))     # 10 h 00 ... 15 h 30
EXPLO = ("2011-01-01", "2022-12-31")
COFFRE = ("2023-01-01", DM.FIN)
JUGE = ("2011-01-01", "2026-09-25")                          # recomptage du juge (scratchpad/check/reentree.py)
PLACEBOS, GRAINE = 200, 20261022
ES = DM.KB / "intraday" / "donnees" / "sp500_1min.csv.gz"
LUCID = "Lucid Flex 50K"
BULENOX = [("4 puis 6 MNQ (reglage actuel)", 4, 6, 5)]
TESTS = [("ZW - ZL", "ZW"), ("ZW+ - ZL", "ZW+")]


def heure(m):
    return DM.heure(m)


def virgule(x, f="{:+.2f}"):
    return f.format(x).replace(".", ",")


# ----------------------------------------------------------------------------- une seance
def seance(z, i, regle, cout, forcees=frozenset(), blocage=None):
    """Une seance de la zone, controles de 10 h 00 a 15 h 30, a plat a 15 h 59.
    regle : 'V1', 'ZL', 'ZW', 'ZW+' ; 'PLA' = placebo : ZL, plus une sortie aux controles de forcees (tenus avec C au-dela
    du VWAP), suivie du blocage de la regle testee (blocage = 'ZW' ou 'ZW+').
    Renvoie dict(trades [(me, sens, pe, ms, ps, net)], cas [(m, sens)] : cas vise rencontre en position, eff : sorties
    forcees effectives, tenus [(m, sens)] : controles tenus avec C au-dela de max(ub, VWAP) (min(lb, VWAP)), ambig :
    entrees ZW+ qu'une lecture 'condition pour toute la seance' aurait refusees, net)."""
    C, sg, vw, hr, br = z["C"][i], z["sigma"][i], z["vwap"][i], z["href"][i], z["bref"][i]
    blq = regle if regle in ("ZW", "ZW+") else blocage
    pos, pe, me = 0, 0.0, -1
    bloc = {1: False, -1: False}            # ZW : entree interdite dans ce sens
    plus = {1: False, -1: False}            # ZW+ : entree dans ce sens seulement au-dela du VWAP
    deja = {1: False, -1: False}            # un cas ZW+ a deja eu lieu dans ce sens aujourd'hui (compteur d'ambiguite)
    trades, cas, eff, tenus, ambig = [], [], [], [], 0

    def sortir(m, p):
        nonlocal pos
        trades.append((me, pos, pe, m, p, pos * (p - pe) - cout))
        pos = 0

    for m in CONTROLES:
        p = C[m]
        ub, lb, v = hr * (1 + sg[m]), br * (1 - sg[m]), vw[m]
        ici = 0                                 # ZW+ : sens sans rachat a ce controle
        if pos:
            s = pos
            limite = (p <= ub) if s > 0 else (p >= lb)
            entre_vwap = (p <= v) if s > 0 else (p >= v)          # au-dela de la limite, pas du VWAP : cas vise
            if limite:
                sortir(m, p)
            elif entre_vwap:
                cas.append((m, s))
                if regle == "V1":
                    sortir(m, p)                                  # rachat ci-dessous, au meme prix
                elif regle in ("ZW", "ZW+"):
                    sortir(m, p)
                    if regle == "ZW":
                        bloc[s] = True
                    else:
                        plus[s] = deja[s] = True
                        ici = s
                # ZL et PLA : on tient
            elif regle == "PLA" and m in forcees:
                sortir(m, p)
                eff.append(m)
                if blq == "ZW":
                    bloc[s] = True
                else:
                    plus[s] = True
                    ici = s
            else:
                tenus.append((m, s))
        if bloc[1] and p <= ub:
            bloc[1] = False
        if bloc[-1] and p >= lb:
            bloc[-1] = False
        if pos == 0:
            for s, signal, vwap_ok in ((1, p > ub, p > v), (-1, p < lb, p < v)):
                if not signal or bloc[s] or s == ici or (plus[s] and not vwap_ok):
                    continue
                if regle == "ZW+" and deja[s] and not plus[s] and not vwap_ok:
                    ambig += 1
                pos, pe, me = s, p, m
                plus[s] = False
                break
    if pos:
        sortir(N - 1, C[N - 1])
    return dict(trades=trades, cas=cas, eff=eff, tenus=tenus, ambig=ambig, net=sum(t[5] for t in trades))


def jouer(z, jours_idx, regle, cout):
    return {i: seance(z, i, regle, cout) for i in jours_idx}


def trades_df(z, res):
    lignes = []
    for i, r in res.items():
        for me, s, pe, ms, ps, net in r["trades"]:
            lignes.append(dict(jour=z["jours"][i], minute_entree=me, sens=s, prix_entree=pe, minute_sortie=ms,
                               prix_sortie=ps, points=net))
    df = pd.DataFrame(lignes, columns=["jour", "minute_entree", "sens", "prix_entree", "minute_sortie", "prix_sortie",
                                       "points"])
    return df.sort_values(["jour", "minute_entree"]).reset_index(drop=True)


# ----------------------------------------------------------------------------- statistiques
def t_stat(x):
    return PA.t_stat(x)


def p_bilateral(t):
    return 1 - erf(abs(t) / sqrt(2))


def serie(res, idx):
    return np.array([res[i]["net"] for i in idx])


# ----------------------------------------------------------------------------- placebo
def placebo(z, idx, regle, res_zl, k_an, rng):
    """Un placebo : par annee, k_an[y] sorties forcees effectives, tirees au hasard parmi les controles tenus de ZL ou
    C > max(ub, VWAP) (vente : C < min(lb, VWAP)), suivies du blocage de la regle testee. Renvoie la somme de PLA - ZL."""
    total = 0.0
    annees = defaultdict(list)
    for i in idx:
        for m, s in res_zl[i]["tenus"]:
            annees[z["jours"][i].year].append((i, m))
    for y, cands in annees.items():
        k = k_an.get(y, 0)
        if k == 0:
            continue
        choisis, eff_j, net_j, n = defaultdict(frozenset), {}, {}, 0
        for c in rng.permutation(len(cands)):
            if n == k:
                break
            i, m = cands[c]
            nouveau = choisis[i] | {m}
            r = seance(z, i, "PLA", COUT, forcees=nouveau, blocage=regle)
            e = len(r["eff"])
            if n - eff_j.get(i, 0) + e != n + 1:
                continue
            choisis[i], n, eff_j[i], net_j[i] = nouveau, n + 1, e, r["net"]
        total += sum(net_j[i] - res_zl[i]["net"] for i in net_j)
    return total


# ----------------------------------------------------------------------------- challenges
def chemins(z, Hm, Lm, tr):
    """Recopie de partie_d.chemins_zone avec une liste de trades donnee (jours de la Fed deja retires de tr)."""
    jours = pd.DatetimeIndex([z["jours"][i] for i in z["jouables"]])
    jours = jours[(jours >= PD.DEBUT) & (jours <= DM.FIN)]
    idx = {j: i for i, j in enumerate(z["jours"])}
    ref = float(z["C"][idx[pd.Timestamp(DM.FIN)], N - 1])
    ch, bas, haut = (np.zeros((len(jours), N)) for _ in range(3))
    pos = {j: k for k, j in enumerate(jours)}
    for j, g in tr.groupby("jour"):
        if j not in pos:
            continue
        i = idx[j]
        C, H, L = z["C"][i], Hm[i], Lm[i]
        f = ref / C[0]
        c, contre, pour = np.zeros(N), np.zeros(N), np.zeros(N)
        for _, t in g.iterrows():
            me, ms, s, pe = int(t["minute_entree"]), int(t["minute_sortie"]), int(t["sens"]), float(t["prix_entree"])
            c[me:ms] += s * (C[me:ms] - pe) * f
            c[ms:] += s * (float(t["prix_sortie"]) - pe) * f
            c[me:] -= DM.COUT
            w = slice(me + 1, ms + 1)
            contre[w] += ((C[w] - L[w]) if s > 0 else (H[w] - C[w])) * f
            pour[w] += ((H[w] - C[w]) if s > 0 else (C[w] - L[w])) * f
        k = pos[j]
        ch[k], bas[k], haut[k] = c * DM.RB.PT, (c - contre) * DM.RB.PT, (c + pour) * DM.RB.PT
    return jours, ch, bas, haut


def lucid(z, Hm, Lm, tr):
    obj, dd, bloc, dll, nmax, part, *_ = PD.FIRMES[LUCID]
    jours, clo, bas, haut = chemins(z, Hm, Lm, tr)
    verif = np.where(jours >= PD.DEBUT_VERIF)[0]
    lim = PD.limites_depart(jours, verif, nmax)
    ok = verif + lim < len(jours)
    iss, nb = PD.tous_les_departs(clo, bas, haut, verif[ok], lim[ok], 1.0, 1.0, 0, float(obj), float(dd), float(bloc),
                                  float(dll), part, True)
    return dict(n=int(ok.sum()), valide=(iss == 1).mean() * 100, perdu=(iss == -1).mean() * 100,
                expire=(iss == 0).mean() * 100)


def bulenox(bars, z, tr):
    r = [x for x in DM.challenge(bars, z, tr, 0.0, 0.0, BULENOX) if x["departs"] == "2023-2026"][0]
    return r


# ----------------------------------------------------------------------------- controles
def regard_futur(z, idx, rng, n=300):
    """Chaque decision au controle m ne doit dependre que des minutes <= m : on remplace tout ce qui suit m (prix, VWAP,
    sigma) par du bruit et on verifie que les actions jusqu'a m sont les memes. Sigma et VWAP recalcules a la main."""
    def avant(tr, m):
        return [(me, s, pe, ms if ms <= m else None, ps if ms <= m else None) for me, s, pe, ms, ps, _ in tr if me <= m]

    erreurs, changees = 0, 0
    for i in rng.choice(idx, size=min(n, len(idx)), replace=False):
        for regle in ("ZL", "ZW", "ZW+"):
            ref = seance(z, i, regle, COUT)
            for m in CONTROLES:
                zz = {"href": z["href"], "bref": z["bref"]}
                for k in ("C", "vwap", "sigma"):
                    a = z[k][i].copy()
                    a[m + 1:] = a[m + 1:] * (1 + rng.normal(0, 0.05, N - m - 1))
                    zz[k] = {i: a}
                r = seance(zz, i, regle, COUT)
                erreurs += avant(r["trades"], m) != avant(ref["trades"], m)
                changees += r["trades"] != ref["trades"]
    return erreurs, changees


def verif_sigma_vwap(bars, z, rng, n=200):
    jours, O, H, L, C, P, V, ech = DM.RB.tableaux(bars)
    ok = DM.RB.seances_completes(P)
    comp = np.where(ok)[0]
    err_s, err_v = 0.0, 0.0
    for i in rng.choice(z["jouables"], size=n, replace=False):
        prev = comp[comp < i][-DM.JM:]
        m = int(rng.choice(CONTROLES))
        s = np.mean(np.abs(C[prev, m] / O[prev, 0] - 1))
        err_s = max(err_s, abs(s - z["sigma"][i, m]))
        typ = (H[i, :m + 1] + L[i, :m + 1] + C[i, :m + 1]) / 3
        v = (typ * V[i, :m + 1]).sum() / V[i, :m + 1].sum()
        err_v = max(err_v, abs(v - z["vwap"][i, m]))
    return err_s, err_v


def relances(tr):
    """Trades qui rachetent dans le meme sens a la minute ou le trade precedent du jour vient de sortir."""
    tr = tr.sort_values(["jour", "minute_entree"]).reset_index(drop=True)
    prev = tr.groupby("jour").shift(1)
    return tr[(prev["minute_sortie"] == tr["minute_entree"]) & (prev["sens"] == tr["sens"])]


# ----------------------------------------------------------------------------- principal
def main():
    L = []
    rng = np.random.default_rng(GRAINE)
    fed = set(pd.DatetimeIndex(fomc.annonces()))
    rech = pd.read_csv(DM.RECHERCHE)
    robot = pd.read_csv(DM.ROBOT)
    robot = robot[robot["t"] <= DM.FIN + " 23:59"]
    bars = pd.concat([rech, robot[robot["t"] > rech["t"].iloc[-1]]], ignore_index=True)

    L.append("Piste 1 : sortie VWAP de la zone, tenir (ZL) ou sortir pour de bon (ZW, ZW+)")
    L.append("Regles : etude_large/pistes/README.md (commit a6e791f, fixees avant tout calcul). NQ minute, 1 MNQ, 1,5 point")
    L.append("par aller-retour, pas de zone les jours de la Fed ni les jours courts. Exploration 2011-2022, coffre 2023 -> 20 oct. 2026.")
    L.append("")

    # ------------------------------------------------------------- controle a) : base du juge
    L.append("CONTROLE a) recomptage du juge (minutes de la recherche seules, 2011 -> 25 sept. 2026, tous les jours)")
    z0 = DM.preparer(rech)
    v1_dm = DM.trades_zone(z0, *JUGE)
    idx0 = [i for i in z0["jouables"] if pd.Timestamp(JUGE[0]) <= z0["jours"][i] <= pd.Timestamp(JUGE[1])]
    r_v1 = jouer(z0, idx0, "V1", COUT)
    r_zl = jouer(z0, idx0, "ZL", COUT)
    v1_ici = trades_df(z0, r_v1)
    a = v1_dm.sort_values(["jour", "minute_entree"]).reset_index(drop=True)
    meme = (len(a) == len(v1_ici) and (a["jour"].values == v1_ici["jour"].values).all()
            and all(np.array_equal(a[c].to_numpy(), v1_ici[c].to_numpy()) for c in ("minute_entree", "sens",
                                                                                      "minute_sortie"))
            and np.abs(a["points"].to_numpy() - v1_ici["points"].to_numpy()).max() < 1e-9)
    rel = relances(a)
    ncas = sum(len(r["cas"]) for r in r_v1.values())
    ans = rel["jour"].dt.year.value_counts().sort_index()
    tot_v1, tot_zl = a["points"].sum(), sum(r["net"] for r in r_zl.values())
    exact = abs(tot_zl - tot_v1 - COUT * ncas) < 1e-6
    meme_pos = all(abs(r_zl[i]["net"] - r_v1[i]["net"] - COUT * len(r_v1[i]["cas"])) < 1e-9 for i in idx0)
    ctl_a = meme and len(a) == 3562 and len(rel) == 382 and ncas == 382 and rel["jour"].nunique() == 210 and exact \
        and ans.min() == 10 and ans.max() == 43
    L.append(f"  V1 recalculee ici = delta_mesures trades_zone trade par trade : {'oui' if meme else 'NON'} ({len(a)} trades ; juge 3 562)")
    L.append(f"  rachats dans le meme sens au meme controle : {len(rel)} (juge 382) ; cas vises vus par la seance : {ncas} ;"
             f" {rel['jour'].nunique()} seances (juge 210) ; de {ans.min()} a {ans.max()} par an (juge 10 a 43)")
    L.append(f"  V1 {virgule(tot_v1)} pt ; ZL {virgule(tot_zl)} pt ; ZL - V1 = {virgule(tot_zl - tot_v1)} = 1,5 x {ncas}"
             f" ({virgule(COUT * ncas)}) : {'exact' if exact else 'ECART'} ; seance par seance (ZL = V1 + 1,5 x cas du jour) :"
             f" {'exact' if meme_pos else 'ECART'}")
    L.append(f"  -> controle a) {'PASSE' if ctl_a else 'ECHEC'}")
    L.append("")

    # ------------------------------------------------------------- base de la piste
    z = DM.preparer(bars)
    _, _, Hm, Lm, _, _, _, _ = DM.RB.tableaux(bars)
    univers = [i for i in z["jouables"] if z["jours"][i] not in fed and not DM.RB.jour_court(z["jours"][i])
               and z["jours"][i] <= pd.Timestamp(DM.FIN)]
    per = {"exploration": [i for i in univers if pd.Timestamp(EXPLO[0]) <= z["jours"][i] <= pd.Timestamp(EXPLO[1])],
           "coffre": [i for i in univers if pd.Timestamp(COFFRE[0]) <= z["jours"][i] <= pd.Timestamp(COFFRE[1])]}
    exclus_fed = sum(1 for i in z["jouables"] if z["jours"][i] in fed and z["jours"][i] <= pd.Timestamp(DM.FIN))
    exclus_court = sum(1 for i in z["jouables"] if DM.RB.jour_court(z["jours"][i]))
    tous = per["exploration"] + per["coffre"]
    R = {r: jouer(z, tous, r, COUT) for r in ("V1", "ZL", "ZW", "ZW+")}
    v1_full = trades_df(z, R["V1"])
    dm_full = DM.trades_zone(z, EXPLO[0], DM.FIN)
    dm_full = dm_full[dm_full["jour"].isin([z["jours"][i] for i in tous])].sort_values(["jour", "minute_entree"])
    meme_full = len(dm_full) == len(v1_full) and np.abs(dm_full["points"].to_numpy() - v1_full["points"].to_numpy()).max() < 1e-9
    L.append(f"BASE : minutes de la recherche + robot jusqu'au {DM.FIN} ; {len(univers)} seances de zone ({exclus_fed} jours de"
             f" la Fed retires, {exclus_court} jour court parmi les seances completes) : exploration {len(per['exploration'])},"
             f" coffre {len(per['coffre'])}")
    L.append(f"  V1 ici = delta_mesures trades_zone sur ces seances : {'oui' if meme_full else 'NON'} ({len(v1_full)} trades)")

    # regard vers le futur
    e_fut, e_chg = regard_futur(z, np.array(tous), rng)
    e_s, e_v = verif_sigma_vwap(bars, z, rng)
    fut_ok = e_fut == 0 and e_s < 1e-12 and e_v < 1e-6
    L.append(f"  regard vers le futur : 300 seances x 12 controles x 3 regles, tout ce qui suit le controle brouille ->"
             f" {e_fut} decision changee jusqu'au controle (la suite change dans {e_chg} cas sur 10 800, le brouillage agit) ;")
    L.append(f"  sigma recalcule a la main (14 seances completes AVANT le jour) ecart max {e_s:.1e} ; VWAP recalcule (minutes"
             f" <= controle) ecart max {e_v:.1e} -> {'aucun regard vers le futur' if fut_ok else 'PROBLEME'}")
    # recopie de partie_d.chemins_zone : doit redonner l'original avec les trades de V1
    jc, c0, b0, h0 = PD.chemins_zone()
    tv1 = trades_df(z, R["V1"])
    jm, c1_, b1_, h1_ = chemins(z, Hm, Lm, tv1)
    ch_ok = (jc.equals(jm) and np.abs(c0 - c1_).max() < 1e-9 and np.abs(b0 - b1_).max() < 1e-9
             and np.abs(h0 - h1_).max() < 1e-9)
    L.append(f"  chemins des challenges (recopie de partie_d.chemins_zone) avec les trades de V1 = original : {'oui' if ch_ok else 'NON'}")
    L.append("")
    L.append("Cas vises (V1 / ZL : ub < C <= VWAP en position ; ZW et ZW+ : sorties VWAP effectives sur leur propre chemin)")
    for p, idx in per.items():
        L.append(f"  {p:11} : V1 {sum(len(R['V1'][i]['cas']) for i in idx)} cas ({sum(1 for i in idx if R['V1'][i]['cas'])} seances),"
                 f" ZW {sum(len(R['ZW'][i]['cas']) for i in idx)}, ZW+ {sum(len(R['ZW+'][i]['cas']) for i in idx)}")
    L.append("")
    L.append("Totaux (points nets, 1 MNQ)            trades   points   t seances   Sharpe")
    for p, idx in per.items():
        for r in ("V1", "ZL", "ZW", "ZW+"):
            x = serie(R[r], idx)
            nt = sum(len(R[r][i]["trades"]) for i in idx)
            L.append(f"  {p:11} {r:4}                        {nt:6d} {x.sum():+9.2f}   {t_stat(x):+6.2f}   {PA.sharpe(x):+6.2f}")
    L.append("")

    # ------------------------------------------------------------- les 2 tests
    sortie, CH = [], {}
    for nom, regle in TESTS:
        L.append(f"=== TEST {nom} (bilateral) ===")
        d = {p: serie(R[regle], idx) - serie(R["ZL"], idx) for p, idx in per.items()}
        te, tc = t_stat(d["exploration"]), t_stat(d["coffre"])
        gagnant, perdant = (regle, "ZL") if d["exploration"].sum() > 0 else ("ZL", regle)
        for p, idx in per.items():
            nc = sum(len(R[regle][i]["cas"]) for i in idx)
            L.append(f"  {p:11} : delta {d[p].sum():+9.2f} pt sur {len(idx)} seances, {nc} cas ({d[p].sum() / max(nc, 1):+.2f} pt"
                     f" par cas), seances touchees {int((d[p] != 0).sum())}, t {t_stat(d[p]):+.2f}"
                     f" (p bilateral {p_bilateral(t_stat(d[p])):.3f})")
        c1 = abs(te) >= 2
        c2 = np.sign(tc) == np.sign(te) and abs(tc) >= 1.5
        L.append(f"  1) exploration |t| >= 2 : t {te:+.2f} -> {'oui' if c1 else 'non'} (Benjamini-Hochberg : calcule sur les 17 tests)")
        L.append(f"  2) coffre meme signe et |t| >= 1,5 : t {tc:+.2f} -> {'oui' if c2 else 'non'}")
        sh = {p: (PA.sharpe(serie(R[gagnant], idx)), PA.sharpe(serie(R[perdant], idx))) for p, idx in per.items()}
        c3 = all(g > q for g, q in sh.values())
        L.append(f"  3) Sharpe du gagnant ({gagnant}, sens de l'exploration) > perdant ({perdant}) sur les deux periodes : "
                 + " ; ".join(f"{p} {g:+.3f} contre {q:+.3f}" for p, (g, q) in sh.items()) + f" -> {'oui' if c3 else 'non'}")
        # placebo (exploration)
        idx = per["exploration"]
        k_an = defaultdict(int)
        for i in idx:
            k_an[z["jours"][i].year] += len(R[regle][i]["cas"])
        pl = np.array([placebo(z, idx, regle, R["ZL"], k_an, rng) for _ in range(PLACEBOS)])
        reel = d["exploration"].sum()
        part = (pl < reel).mean() if gagnant == regle else (pl > reel).mean()
        c4 = part >= 0.95
        L.append(f"  4) placebo (exploration, {PLACEBOS} tirages, {sum(k_an.values())} sorties forcees par tirage, meme nombre par an,"
                 f" blocage de {regle}) : placebos moyenne {pl.mean():+.1f} pt, 5e-95e centile {np.percentile(pl, 5):+.1f} /"
                 f" {np.percentile(pl, 95):+.1f} ; reel {reel:+.1f} plus extreme du cote gagnant que {part * 100:.1f} % -> {'oui' if c4 else 'non'}")
        # challenges
        for r in (gagnant, perdant):
            if r not in CH:
                tr_ = trades_df(z, R[r])
                CH[r] = (bulenox(bars, z, tr_), lucid(z, Hm, Lm, tr_))
        (bg, lg), (bp, lp) = CH[gagnant], CH[perdant]
        c5b = bg["valide"] >= bp["valide"] - 1.0
        c5l = lg["valide"] >= lp["valide"] - 1.0
        c5 = c5b and c5l
        L.append(f"  5) challenges, departs 2023-2026, le gagnant valide au plus 1 point de moins que le perdant :")
        L.append(f"     Bulenox (delta_mesures challenge, 16 seances depuis 0, {BULENOX[0][0]}, {bg['n']} departs) :"
                 f" {gagnant} valide {bg['valide']:.1f} % (perdu {bg['perdu']:.1f} %), {perdant} {bp['valide']:.1f} %"
                 f" (perdu {bp['perdu']:.1f} %) -> {'oui' if c5b else 'non'}")
        L.append(f"     Lucid Flex 50K (partie D, 1 MNQ, {lg['n']} departs) : {gagnant} valide {lg['valide']:.1f} % (perdu"
                 f" {lg['perdu']:.1f} %), {perdant} {lp['valide']:.1f} % (perdu {lp['perdu']:.1f} %) -> {'oui' if c5l else 'non'}")
        ok = c1 and c2 and c3 and c4 and c5
        L.append(f"  -> criteres propres (hors Benjamini-Hochberg) : {'TOUS PASSES' if ok else 'ECHEC'}"
                 f" (1 {'oui' if c1 else 'non'}, 2 {'oui' if c2 else 'non'}, 3 {'oui' if c3 else 'non'},"
                 f" 4 {'oui' if c4 else 'non'}, 5 {'oui' if c5 else 'non'})")
        if regle == "ZW+":
            amb = sum(R["ZW+"][i]["ambig"] for i in tous)
            L.append(f"  lecture de ZW+ : la condition 'au-dela du VWAP' vaut pour la prochaine entree dans le meme sens ;"
                     f" entrees qu'une condition valable toute la seance aurait refusees : {amb}")
        L.append("")
        sortie.append(dict(nom=nom, t_explo=te, t_coffre=tc, gagnant=gagnant, c=(c1, c2, c3, c4, c5), sh=sh, part=part,
                           bul=(bg["valide"], bp["valide"]), luc=(lg["valide"], lp["valide"]), ok=ok))

    # ------------------------------------------------------------- controle c)
    L.append("CONTROLE c) achats et ventes, heure du cas (chaque seance est rangee selon son premier cas)")
    for nom, regle in TESTS:
        L.append(f"  {nom}")
        for p, idx in per.items():
            dd = {i: R[regle][i]["net"] - R["ZL"][i]["net"] for i in idx if R[regle][i]["cas"]}
            prem = {i: R[regle][i]["cas"][0] for i in dd}
            plus_un = sum(1 for i in dd if len(R[regle][i]["cas"]) > 1)
            for s, lab in ((1, "achats"), (-1, "ventes")):
                x = np.array([dd[i] for i in dd if prem[i][1] == s])
                L.append(f"    {p:11} {lab} : {len(x):3d} seances, {x.sum():+8.2f} pt, {x.mean() if len(x) else 0:+6.2f} par seance")
            ligne = []
            for m in CONTROLES:
                x = [dd[i] for i in dd if prem[i][0] == m]
                if x:
                    ligne.append(f"{heure(m)} {len(x)} / {sum(x):+.0f}")
            L.append(f"    {p:11} par heure (seances / points) : " + ", ".join(ligne))
            L.append(f"    {p:11} seances avec plus d'un cas : {plus_un}")
    L.append("")

    # ------------------------------------------------------------- controle d) ES
    L.append("CONTROLE d) ES minute en replication (information, 0,9 point par aller-retour, donnees jusqu'au 25 sept. 2026)")
    es = pd.read_csv(ES)
    ze = DM.preparer(es)
    ue = [i for i in ze["jouables"] if ze["jours"][i] not in fed and not DM.RB.jour_court(ze["jours"][i])]
    pe_ = {"exploration": [i for i in ue if pd.Timestamp(EXPLO[0]) <= ze["jours"][i] <= pd.Timestamp(EXPLO[1])],
           "coffre": [i for i in ue if pd.Timestamp(COFFRE[0]) <= ze["jours"][i] <= pd.Timestamp(COFFRE[1])]}
    RE = {r: jouer(ze, pe_["exploration"] + pe_["coffre"], r, COUT_ES) for r in ("ZL", "ZW", "ZW+")}
    ctl_d = []
    for (nom, regle), s in zip(TESTS, sortie):
        parts = []
        for p, idx in pe_.items():
            x = serie(RE[regle], idx) - serie(RE["ZL"], idx)
            parts.append(f"{p} {x.sum():+.2f} pt ES, {sum(len(RE[regle][i]['cas']) for i in idx)} cas, t {t_stat(x):+.2f}")
        xe = serie(RE[regle], pe_["exploration"]) - serie(RE["ZL"], pe_["exploration"])
        meme_signe = np.sign(t_stat(xe)) == np.sign(s["t_explo"])
        ctl_d.append(meme_signe)
        L.append(f"  {nom} : " + " ; ".join(parts) + f" -> meme signe que le NQ en exploration : {'oui' if meme_signe else 'non'}")
    L.append("")

    # ------------------------------------------------------------- controles b) et e) : P1, P2, vrai delta
    L.append("CONTROLES b) et e) : P1 (Databento, avril - 1er oct. 2026) et P2 (Rithmic, 2 - 16 oct. 2026), vrai delta")
    t = pd.read_csv(RACINE / "delta_mesures" / "trades.csv", parse_dates=["jour"])
    zr = DM.preparer(robot)
    ctl_b = True
    for nomp, (a_, b_) in (("P1", DM.P1), ("P2", DM.P2)):
        x = t[t["periode"] == nomp].sort_values(["jour", "minute_entree"]).reset_index(drop=True)
        y = DM.trades_zone(zr, a_, b_).sort_values(["jour", "minute_entree"]).reset_index(drop=True)
        meme = len(x) == len(y) and np.abs(x["points"].to_numpy() - y["points"].to_numpy()).max() < 1e-3 and \
            (x["minute_entree"].to_numpy() == y["minute_entree"].to_numpy()).all()
        rl = relances(x)
        ecartes = int((~rl["B"]).sum())
        L.append(f"  {nomp} : trades.csv = zone recalculee sur les barres du robot : {'oui' if meme else 'NON'} ({len(x)} trades) ;"
                 f" rachats du cas vise : {len(rl)}, ecartes par le filtre B : {ecartes} ({ecartes / max(len(rl), 1) * 100:.0f} %),"
                 f" points de ces rachats (sans filtre) {rl['points'].sum():+.2f}")
        for r in rl.itertuples():
            L.append(f"     {r.jour.date()} {heure(r.minute_entree)} {'achat' if r.sens > 0 else 'vente'} {r.points:+8.2f} pt,"
                     f" delta des 30 minutes {r.D30:+.0f} -> {'garde' if r.B else 'ecarte'}")
        if nomp == "P2" and len(rl) == 0:
            L.append("  P2 : aucun rachat de ce type sur les 7 trades : la part ecartee n'est pas mesurable sur P2.")
        if nomp == "P1":
            h1 = x[x["B"]]
            okh = len(h1) == 79 and abs(h1["points"].sum() - 1776.75) < 1e-6
            ok11 = len(rl) == 11 and ecartes == 11
            ctl_b = meme and okh and ok11
            L.append(f"  P1 : H1 (filtre B, relance decochee) {len(h1)} trades {h1['points'].sum():+.2f} pt (attendu 79, +1 776,75) ;"
                     f" 11 rachats tous ecartes : {'oui' if ok11 else 'non'} -> controle b) {'PASSE' if ctl_b else 'ECHEC'}")
    L.append("")

    # ------------------------------------------------------------- decision
    L.append("RESUME DES 2 TESTS (t d'exploration et de coffre ; critere 1 sans Benjamini-Hochberg, calcule ensuite sur 17 tests)")
    for s in sortie:
        L.append(f"  {s['nom']:9} t explo {s['t_explo']:+.2f} (bilateral, p {p_bilateral(s['t_explo']):.3f}), t coffre {s['t_coffre']:+.2f},"
                 f" gagnant de l'exploration {s['gagnant']} ; criteres 1-5 : "
                 + " ".join(f"{k + 1}:{'oui' if v else 'non'}" for k, v in enumerate(s["c"]))
                 + f" -> {'passe ses criteres' if s['ok'] else 'echoue'}")
    L.append("Controles : a) " + ("passe" if ctl_a else "ECHEC") + " ; b) " + ("passe" if ctl_b else "ECHEC")
             + " ; c) publie ; d) ES meme signe : " + ", ".join("oui" if c else "non" for c in ctl_d)
             + " ; e) publie ; regard vers le futur : " + ("aucun" if fut_ok else "PROBLEME"))
    gagne = [s for s in sortie if s["ok"]]
    if not gagne:
        L.append("DECISION fixee d'avance : aucun vainqueur net -> ZL passe dans le robot virtuel (frais economises, environ"
                 " 1,5 point par cas) et l'ecart entre backtest et bot est publie.")
    else:
        for s in gagne:
            L.append(f"DECISION fixee d'avance (sous reserve de Benjamini-Hochberg et de la contre-verification) : {s['nom']},"
                     f" gagnant {s['gagnant']}.")
    L.append("")
    L.append("LECTURES DES REGLES (choisies avant les chiffres, au plus pres du README) :")
    L.append("- series quotidiennes sur les seances ou la zone joue (jours de la Fed retires, aucun jour court parmi les seances")
    L.append("  completes), 0 les seances sans cas ; Sharpe = moyenne / ecart-type x racine(252) de ces series (partie_a.sharpe).")
    L.append("- ZW+ : la condition 'C au-dela du VWAP' porte sur la prochaine entree dans le meme sens apres la sortie VWAP")
    L.append("  (elle n'est pas levee par un retour dans la zone) ; la lecture 'toute la seance' n'aurait change que"
             f" {sum(R['ZW+'][i]['ambig'] for i in tous)} entrees.")
    L.append("- placebo : en exploration (periode du test) ; les controles candidats sont ceux ou ZL tient avec C au-dela de")
    L.append("  max(ub, VWAP) (vente : min(lb, VWAP)) ; nombre de sorties forcees effectives par an = nombre de sorties VWAP de la")
    L.append("  regle testee ; 'meme blocage' = celui de la regle testee (ZW : pas de rachat dans le meme sens avant C <= ub ;")
    L.append("  ZW+ : pas de rachat a ce controle, puis rachat seulement au-dela du VWAP). Ecart compare : somme des points nets.")
    L.append("- Bulenox : delta_mesures challenge() depuis un compte neuf (0 $), 16 seances, a la taille de l'appel 'depuis 0' de")
    L.append("  ce code, qui est le reglage actuel du bot (4 MNQ puis 6) ; Lucid Flex : partie D a 1 MNQ comme le README.")
    L.append("- P1 et P2 : delta reel lu dans delta_mesures/trades.csv (filtre B), apres verification que ses trades sont ceux de")
    L.append("  la zone recalculee sur les barres du robot.")
    texte = "\n".join(L)
    print(texte)
    (ICI / "resultats.txt").write_text(texte + "\n")


if __name__ == "__main__":
    main()
