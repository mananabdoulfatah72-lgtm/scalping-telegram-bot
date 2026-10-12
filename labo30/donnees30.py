#!/usr/bin/env python3
"""Labo 30 jours (README.md) : donnees de la page, toutes calculees avec le moteur exact du bot (vague13/moteur13 =
vague4/moteur4 seance par seance), Bulenox Legacy 50K, challenge de 30 jours puis Master en taille 1.
1. Statistiques exactes sur tous les achats (chaque seance, 21 tirages du filtre), par version, filtre et periode.
2. Echantillon de challenges rejoues seance par seance (solde chaque soir, retraits du Master) pour l'animation.
3. Exemples reels : quatre fenetres de 30 jours, trade par trade.
4. Gains et pertes d'une seance en taille 1 et 4, courbes du bot sans regles de compte.
Usage : python3 donnees30.py [lettre de la vague 13 retenue, A par defaut]. Ecrit donnees30.json."""
import json
import multiprocessing as mp
import pickle
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
M4 = M13.M4
P, LIM = V.P, V.LIM
A = K.COMPTES["legacy"]
RETENUE = sys.argv[1] if len(sys.argv) > 1 else "A"
VERSIONS = {"t1": ("Bot tel quel (1 MNQ, frein)", 1, A["frein"], "A"), "t2": ("2 MNQ", 2, 0.0, "A"),
            "t3": ("3 MNQ", 3, 0.0, "A"), "t4": ("4 MNQ (version 30 jours, vague 12)", 4, 0.0, "A")}
NOMS13 = {"B": "arrêt à l'objectif", "C": "arrêt à l'objectif + protection", "D": "arrêt à l'objectif + fin de course",
          "E": "arrêt + protection + fin de course", "F": "arrêt à l'objectif + prudence près du but"}
if RETENUE != "A":
    VERSIONS["v13"] = (f"4 MNQ + {NOMS13[RETENUE]} (vague 13)", 4, 0.0, RETENUE)
if RETENUE not in ("A", "B"):
    VERSIONS["v13b"] = (f"4 MNQ + {NOMS13['B']} seul (vague 13)", 4, 0.0, "B")
FILTRES = {"fort": 10, "moitie": 10, "aucun": 1}
GROUPES = {"2012-2021": (V.D0, V.CHOIX_FIN), "2023-2026": (V.VERIF_DEB, V.D1), "2025": V.GROUPES["2025"][:2]}
N_ECH = 300


def achat(b, d, q, c_ch, lettre, traces=False):
    sv = min(K.H, (V.CHOIX_SUIVI if d < V.CHOIX_FIN else V.NJ) - d)
    lim = int(LIM[d])
    a = R13.args_defi("legacy", lettre)
    args = a[:7] + (q, c_ch) + a[9:]
    ts, tp, tt = np.zeros(lim + 1), np.zeros(lim + 1), np.zeros(lim + 1, np.int64)
    iss, nch, veut, d2 = M13.defi13(d, lim, 4, P["kN"], P["kE"], *b, *args, ts, tp, tt)
    ret = np.zeros(max(sv, 1))
    perdu, n, fin = False, 0, nch
    if iss == 1:
        F = A["F"]
        perdu, n, recu, prem, fin = M13.master13(d, d2, veut, min(V.NJ, d + sv), 4, P["kN"], P["kE"], ret, *b, *F[:9],
                                                 F[9], F[10], A["cycle"], A["frein"], A["cap"])
    idx = np.flatnonzero(ret[:K.H] > 0)
    t_ret = [int(i + 1 - nch) for i in idx]
    net = ret[:K.H].sum() - A["prix"] - (A["activation"] if iss == 1 else 0.0) if sv >= K.H else np.nan
    ligne = (d, iss, nch, float(perdu), len(idx), *(t_ret + [np.nan] * 3)[:3], ret[:K.H].sum(), net,
             (fin - nch) if (iss == 1 and perdu) else np.nan, sv)
    if traces:
        return ligne, ts[:nch].copy(), [float(x) for x in ret[idx]]
    return ligne


def tache(args):
    v, fil, t = args
    _, q, c_ch, lettre = VERSIONS[v]
    b = P["bases"][fil][t]
    dd = [d for d in V.jours_achat("legacy")]
    return v, fil, t, np.array([achat(b, int(d), q, c_ch, lettre) for d in dd])


def resume(x):
    iss = x[:, 1]
    val = iss == 1
    full = ~np.isnan(x[:, 9])
    y = x[val]
    pct = lambda a, p: float(np.nanpercentile(a, p)) if np.isfinite(a).any() else None          # noqa: E731
    suivi = y[:, 11] - y[:, 2] >= 252                       # Masters suivis au moins 12 mois apres la validation
    return dict(
        achats=int(len(x)), valide=float(val.mean()), perdu=float((iss == -1).mean()), expire=float((iss == 0).mean()),
        hist_valide=np.bincount(x[val, 2].astype(int), minlength=24)[:24].tolist(),
        hist_perdu=np.bincount(x[iss == -1, 2].astype(int), minlength=24)[:24].tolist(),
        seances_med=pct(y[:, 2], 50),
        m_un_retrait=float(np.mean(y[suivi, 4] >= 1)) if suivi.any() else None,
        m_trois=float(np.mean(y[suivi, 4] >= 3)) if suivi.any() else None,
        m_perdu_sans=float(np.mean((y[suivi, 3] == 1) & (y[suivi, 4] == 0))) if suivi.any() else None,
        r1=[pct(y[:, 5], p) for p in (25, 50, 75)], r2=pct(y[:, 6], 50), r3=pct(y[:, 7], 50),
        net_moy=float(np.nanmean(x[full, 9])) if full.any() else None,
        net_med=float(np.nanmedian(x[full, 9])) if full.any() else None,
        perdants=float(np.mean(x[full, 9] < 0)) if full.any() else None,
        hist_net=np.histogram(x[full, 9], bins=np.arange(-500, 5001, 250))[0].tolist() if full.any() else None)


def echantillon(args):
    v, fil, g, graine = args
    _, q, c_ch, lettre = VERSIONS[v]
    rng = np.random.default_rng(graine)
    a, z = GROUPES[g]
    dd = np.array([d for d in V.jours_achat("legacy") if a <= d < z])
    out = []
    for _ in range(N_ECH):
        t = int(rng.integers(FILTRES[fil]))
        d = int(rng.choice(dd))
        ligne, sol, rets = achat(P["bases"][fil][t], d, q, c_ch, lettre, traces=True)
        out.append(dict(j=str(P["jours"][d].date()), i=int(ligne[1]), n=int(ligne[2]), s=[int(round(x)) for x in sol],
                        r=[None if np.isnan(x) else int(x) for x in ligne[5:8]], m=[int(x) for x in rets],
                        p=None if np.isnan(ligne[10]) else int(ligne[10])))
    return v, fil, g, out


def heure(t):
    m = 9 * 60 + 30 + int(t)
    return f"{m // 60}h{m % 60:02d}"


def exemple(d, q, c_ch, lettre, t=0):
    """Rejoue une fenetre de 30 jours seance par seance avec seance4 (comme defi13) et decrit chaque trade."""
    b = P["bases"]["fort"][t]
    O, H, L, C, der, z_deb, z_fin, z_me, z_ms, z_sens, z_garde, dec, voulu, NO, NH, NL, nn, EO, EH, EL, EC, ENO, ENH, \
        ENL, enn, reb = b
    a = R13.args_defi("legacy", lettre)
    e_obj, e_perte, e_mode, e_bloc, e_dll = a[0], a[1], a[2], a[3], a[4]
    arret, marge, q_bas, seuil_bas, q_fin, n_fin, q_but, seuil_but = a[9:]
    lim = int(LIM[d])
    Z = P["D"]["Z"]
    pf = V.P["pf"]
    cash, veut, pic, pic_eod, plancher = 0.0, 0, 0.0, 0.0, -e_perte
    jours = []
    for s in range(lim):
        j = d + s
        qc = q
        if seuil_but > 0 and e_obj - cash < seuil_but:
            qc = q_but
        if n_fin > 0 and lim - s <= n_fin:
            qc = q_fin
        if seuil_bas > 0 and cash - plancher < seuil_bas:
            qc = q_bas
        zi = 1 if c_ch > 0 and cash - plancher < c_ch else 0
        cap = max(0.0, e_obj + marge - cash) if arret == 1 else 0.0
        veut_in, avant = veut, cash
        perdu, cash, veut, pic, plancher, tr = M4.seance4(j, 4, veut, cash, pic, plancher, e_mode, e_perte, e_bloc, e_dll,
                                                          *b, P["kN"][j], P["kE"][j], qc, zi, cap)
        trades = []
        if veut_in == 1 and enn[j] > 0:
            pts = EO[j, 0] - ENO[j, 0]
            trades.append(dict(type="nuit", sens="achat", entree="18h00 (veille)", sortie="9h30", contrats=f"{qc} MES",
                               points=round(float(pts), 2), usd=round(float(qc * (pts * P["kE"][j] - 2.25)))))
        for k in range(z_deb[j], z_fin[j]):
            me, ms, se = int(z_me[k]), int(z_ms[k]), int(z_sens[k])
            if z_garde[k] != 1:
                raison = "jour de la Fed" if not pf[k] else "écarté par le filtre delta"
                trades.append(dict(type="ecarte", sens="achat" if se > 0 else "vente", entree=heure(me), raison=raison))
                continue
            if zi == 0:
                pts = C[j, ms] - C[j, me]
                usd = qc * (se * pts * P["kN"][j] - 3.0)
                ctr = f"{qc} MNQ"
            else:
                pts = EC[j, ms] - EC[j, me]
                usd = qc * (se * pts * P["kE"][j] - 4.5)
                ctr = f"{qc} MES"
            trades.append(dict(type="zone", sens="achat" if se > 0 else "vente", entree=heure(me), sortie=heure(ms),
                               contrats=ctr, points=round(float(se * pts), 2), usd=round(float(usd))))
        g = cash - avant
        nominal = sum(x.get("usd", 0) for x in trades)
        if not perdu and e_mode == 0:
            pic_eod = max(pic_eod, cash)
            plancher = min(pic_eod - e_perte, e_bloc)
        jours.append(dict(date=str(P["jours"][j].date()), taille=int(qc), gain=round(g), solde=round(cash),
                          plancher=round(plancher), trades=trades,
                          anticipe=bool(abs(nominal - g) > 15 and any(x["type"] != "ecarte" for x in trades)),
                          perdu=bool(perdu)))
        if perdu:
            return dict(issue="perdu", seances=s + 1, jours=jours)
        if cash >= e_obj:
            return dict(issue="validé", seances=s + 1, jours=jours)
    return dict(issue="expiré", seances=lim, jours=jours)


def gains_seance():
    """Gain de chaque seance 2012-2026, sans regles de compte (limite du jour 1 100 $), tailles 1 et 4, 10 tirages."""
    s0 = int(np.searchsorted(P["jours"], pd.Timestamp("2012-01-03")))
    res = {}
    for q in (1, 4):
        tous, courbes = [], []
        for t in range(10):
            b = P["bases"]["fort"][t]
            veut, g = 0, np.zeros(V.NJ - s0)
            for j in range(s0, V.NJ):
                perdu, cash, veut, _, _, tr = M4.seance4(j, 4, veut, 0.0, 0.0, -1e12, 0, 1e12, 0.0, 1100.0, *b,
                                                         P["kN"][j], P["kE"][j], q, 0, 0.0)
                g[j - s0] = cash
            tous.append(g)
        G = np.vstack(tous)
        tot = G.sum(axis=1)
        med = int(np.argsort(tot)[len(tot) // 2])
        x = G[G != 0]
        cum = np.cumsum(G[med])
        dd = cum - np.maximum.accumulate(cum)
        res[str(q)] = dict(
            jours_trade=float(np.mean(G != 0)), gagnants=float(np.mean(x > 0)), gain_moy=float(x[x > 0].mean()),
            perte_moy=float(x[x < 0].mean()), meilleur=float(x.max()), pire=float(x.min()),
            p5=float(np.percentile(x, 5)), p95=float(np.percentile(x, 95)),
            limite_jour=float(np.mean(x <= -1050)),
            hist=np.histogram(np.clip(x, -1300, 2999), bins=np.arange(-1300, 3001, 100))[0].tolist(),
            courbe=[round(float(v)) for v in cum[::3]], dates=[str(P["jours"][s0 + i].date()) for i in range(0, len(cum), 3)],
            pire_baisse=float(dd.min()), par_an=float(G[med].sum() / (len(cum) / 252)))
    return res


def main():
    t0 = time.time()
    cache = ICI / f"cache30_{RETENUE}.pkl"
    if cache.exists():
        stats, par_an, ech = pickle.loads(cache.read_bytes())
    else:
        stats, par_an, ech = calculer(t0)
        cache.write_bytes(pickle.dumps((stats, par_an, ech)))
    finir(t0, stats, par_an, ech)


def calculer(t0):
    taches = [(v, fil, t) for v in VERSIONS for fil, n in FILTRES.items() for t in range(n)]
    X = {}
    with mp.get_context("fork").Pool(4) as pool:
        for k, (v, fil, t, out) in enumerate(pool.imap_unordered(tache, taches)):
            X.setdefault((v, fil), []).append(out)
            if k % 20 == 0:
                print(f"achats : {k + 1}/{len(taches)} ({time.time() - t0:.0f} s)", flush=True)
        stats, par_an = {}, {}
        for (v, fil), outs in X.items():
            x = np.vstack(outs)
            for g, (a, z) in GROUPES.items():
                stats[f"{v}|{fil}|{g}"] = resume(x[(x[:, 0] >= a) & (x[:, 0] < z)])
            ans = pd.DatetimeIndex(P["jours"][x[:, 0].astype(int)]).year
            par_an[f"{v}|{fil}"] = {int(y): float(np.mean(x[ans == y, 1] == 1)) for y in sorted(set(ans))}
        ech = {}
        args = [(v, fil, g, 1000 + i) for i, (v, fil, g) in enumerate((v, f, g) for v in VERSIONS for f in FILTRES
                                                                     for g in GROUPES)]
        for v, fil, g, out in pool.imap_unordered(echantillon, args):
            ech[f"{v}|{fil}|{g}"] = out
    print(f"echantillons ({time.time() - t0:.0f} s)", flush=True)
    return stats, par_an, ech


def finir(t0, stats, par_an, ech):
    vr = "v13" if "v13" in VERSIONS else "t4"
    _, q, c_ch, lettre = VERSIONS[vr]
    b0 = P["bases"]["fort"][0]
    cand = [(d, achat(b0, int(d), q, c_ch, lettre)) for d in V.jours_achat("legacy") if d >= V.VERIF_DEB]
    val = [(d, l) for d, l in cand if l[1] == 1]
    rapide = min(val, key=lambda x: (x[1][2], -x[0]))[0]
    meds = sorted(val, key=lambda x: x[1][2])
    med_n = meds[len(meds) // 2][1][2]
    typ = [d for d, l in val if l[2] == med_n and l[4] >= 1] or [d for d, l in val if l[2] == med_n]
    typique = typ[-1]
    perdu = [d for d, l in cand if l[1] == -1][-1]
    expire = [d for d, l in cand if l[1] == 0][-1]
    exemples = {k: exemple(int(d), q, c_ch, lettre) for k, d in (("rapide", rapide), ("typique", typique),
                                                                   ("perdu", perdu), ("expire", expire))}
    print(f"exemples ({time.time() - t0:.0f} s)", flush=True)
    gs = gains_seance()
    sortie = dict(versions={v: x[0] for v, x in VERSIONS.items()}, retenue=vr, lettre13=RETENUE, stats=stats, par_an=par_an,
                  echantillons=ech, exemples=exemples, gains=gs,
                  vague12=json.loads((R0 / "vague12" / "vague12.json").read_text()),
                  vague13=json.loads((R0 / "vague13" / "vague13.json").read_text()))
    (ICI / "donnees30.json").write_text(json.dumps(sortie, ensure_ascii=False, separators=(",", ":")))
    print(f"fini en {time.time() - t0:.0f} s ; {len(json.dumps(sortie)) / 1e6:.2f} Mo", flush=True)


if __name__ == "__main__":
    main()
