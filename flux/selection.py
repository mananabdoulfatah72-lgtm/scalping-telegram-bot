#!/usr/bin/env python3
"""Partie 2 (flux/README.md) : selection sur A seulement, barriere du bruit, finalistes ; puis coffre B (une seule fois)
et reglage glissant. Lit les calculs de reglages.py (FLUX_CALCUL).

  python3 flux/selection.py explorer   -> resultats/partie2_exploration.txt, resultats/finalistes.json (+ empreinte)
  python3 flux/selection.py coffre     -> resultats/partie2_coffre.txt (refuse si les finalistes ont change ou si deja ouvert)
  python3 flux/selection.py glissant   -> resultats/partie2_glissant.txt"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import reglages as G

ICI = Path(__file__).resolve().parent
RES = ICI / "resultats"
FIN_A = pd.Timestamp("2026-07-31")
BONF = {1: 1.645, 2: 1.96, 3: 2.13}


def charger(nom):
    z = np.load(G.CALCUL / f"{nom}.npz")
    return z["P"].astype(np.float64), z["N"].astype(np.float64)


def t_lignes(P):
    """t par seance de chaque ligne (seances en colonnes)."""
    n = P.shape[1]
    s = P.std(axis=1, ddof=1)
    return np.where(s > 0, P.mean(axis=1) / np.where(s > 0, s, 1) * np.sqrt(n), 0.0)


def score(P, N, cols, n_min):
    Pc, Nc = P[:, cols], N[:, cols]
    n = Nc.sum(axis=1)
    moyen = np.where(n > 0, Pc.sum(axis=1) / np.where(n > 0, n, 1), 0.0)
    t = t_lignes(Pc)
    sc = t * np.minimum(1.0, n / n_min)
    eligible = moyen > 0
    return sc, t, n, moyen, eligible


def decrire(c):
    if c["famille"] == "F1":
        W, vw, k, qa, vm, cp = c["signal"]
        s = (f"F1 repli absorbe : delta {W} min, VWAP {'exige' if vw else 'libre'}, repli {k} min, desequilibre au-dela du "
             f"quantile {qa}, volume >= {vm} x mediane 30 min, cloture favorable {'exigee' if cp else 'libre'}")
    elif c["famille"] == "F2":
        niv, qa, fw = c["signal"]
        s = f"F2 cassure ratee : niveaux {niv}, agression {'aucune' if qa == 0 else 'quantile ' + str(qa)}, echec en {fw} min"
    else:
        E, qf, rj = c["signal"]
        s = f"F3 volume d'arret : extreme {'de la seance' if E == 0 else str(E) + ' min'}, footprint quantile {qf}, rejet {rj} pt"
    obj = "aucun" if c["objectif"] == 0 else f"{c['objectif']:g} R"
    return (f"{s} | objectif {obj}, {c['duree']} min, stop min {c['stop_min']:g} pt, signaux jusqu'a "
            f"{'15 h' if c['t_max'] == 330 else '12 h'}, sens {'du setup' if c['sens'] == 1 else 'inverse'}")


def explorer():
    cf = pd.read_pickle(G.CALCUL / "configs.pkl")
    info = pd.read_pickle(G.CALCUL / "info.pkl")
    jou = np.load(G.CALCUL / "jouable.npy")
    A = np.flatnonzero(jou & (info["jour"] <= FIN_A).to_numpy())
    L = [f"Partie 2, exploration sur A seulement : {len(A)} seances jouables du {info['jour'][A[0]].date()} au "
         f"{info['jour'][A[-1]].date()} ; {len(cf)} configurations ; score = t par seance x min(1, trades / 40)", ""]
    barr = {}
    for nom in [f"bruit{g}" for g in G.GRAINES]:
        P, N = charger(nom)
        sc, t, n, moy, el = score(P, N, A, 40)
        ok = el & (n >= 40)
        for fam in ("F1", "F2", "F3"):
            f = (cf["famille"] == fam).to_numpy() & ok
            barr.setdefault(fam, []).append(sc[f].max() if f.any() else -np.inf)
    P, N = charger("reel")
    sc, t, n, moy, el = score(P, N, A, 40)
    ok = el & (n >= 40)
    L.append("Nombre de configurations eligibles (>= 40 trades, gain net moyen > 0) et meilleur score, reel contre bruit :")
    finalistes = []
    for fam in ("F1", "F2", "F3"):
        f = (cf["famille"] == fam).to_numpy()
        b = max(barr[fam])
        L.append(f"  {fam} : reel {int((f & ok).sum())} eligibles, meilleur score {sc[f & ok].max() if (f & ok).any() else float('nan'):.2f} "
                 f"| bruit, meilleur score par graine : {', '.join(f'{x:.2f}' for x in barr[fam])} -> barriere {b:.2f}")
        for seuil in (2.0, 2.5, 3.0, 3.5):
            L.append(f"      score >= {seuil} : reel {int((f & ok & (sc >= seuil)).sum())}")
        if (f & ok).any():
            i = int(np.flatnonzero(f & ok)[np.argmax(sc[f & ok])])
            c = cf.iloc[i]
            L.append(f"      meilleure reelle : {decrire(c)}")
            L.append(f"      sur A : {int(n[i])} trades, net moyen {moy[i]:+.2f} pt, t par seance {t[i]:+.2f}, score {sc[i]:.2f}")
            if sc[i] > b:
                finalistes.append(i)
                L.append("      -> FINALISTE (au-dessus de la barriere du bruit)")
            else:
                L.append("      -> pas finaliste (le bruit fait aussi bien ou mieux)")
    L.append("")
    L.append(f"Finalistes : {len(finalistes)}")
    texte = "\n".join(L)
    (RES / "partie2_exploration.txt").write_text(texte + "\n")
    contenu = json.dumps({"finalistes": [int(i) for i in finalistes],
                          "descriptions": [decrire(cf.iloc[i]) for i in finalistes]}, ensure_ascii=False, indent=1)
    (RES / "finalistes.json").write_text(contenu + "\n")
    (RES / "finalistes.sha256").write_text(hashlib.sha256((contenu + "\n").encode()).hexdigest() + "\n")
    print(texte)


def placebo_b(X, cfg, B, n=2000, graine=1):
    tr = G.trades_config(X, cfg)
    tr = tr[tr["seance"].isin(B)]
    pos = pd.Index(B).get_indexer(tr["seance"])
    a, b = tr["net"].to_numpy(), tr["net_inverse"].to_numpy()
    rng = np.random.default_rng(graine)
    ts = np.empty(n)
    for k in range(n):
        q = np.bincount(pos, weights=np.where(rng.random(len(a)) < 0.5, a, b), minlength=len(B))
        ts[k] = t_lignes(q[None, :])[0]
    return ts


def coffre():
    contenu = (RES / "finalistes.json").read_text()
    if hashlib.sha256(contenu.encode()).hexdigest() != (RES / "finalistes.sha256").read_text().strip():
        raise SystemExit("les finalistes ont change depuis l'exploration : coffre refuse")
    if (RES / "partie2_coffre.txt").exists():
        raise SystemExit("le coffre a deja ete ouvert")
    fin = json.loads(contenu)["finalistes"]
    cf = pd.read_pickle(G.CALCUL / "configs.pkl")
    info = pd.read_pickle(G.CALCUL / "info.pkl")
    jou = np.load(G.CALCUL / "jouable.npy")
    fp = np.load(G.CALCUL / "fp_ok.npy")
    L = [f"Partie 2, coffre B (3 aout - 16 octobre 2026), ouvert une fois ; m = {len(fin)} finaliste(s)"]
    if not fin:
        L.append("Aucune finaliste : rien a juger.")
    else:
        import donnees as D
        m, info2, _ = D.seances()
        X = G.tableaux(m, info2)
        P, N = charger("reel")
        seuil = BONF[len(fin)]
        for i in fin:
            c = cf.iloc[i]
            B = np.flatnonzero(jou & (info["jour"] > FIN_A).to_numpy() & (fp if c["famille"] == "F3" else True))
            nB = N[i, B].sum()
            moy = P[i, B].sum() / nB if nB else 0.0
            tB = t_lignes(P[i, B][None, :])[0]
            pl = placebo_b(X, c, B)
            bat = (pl < tB).mean()
            ok = tB >= seuil and moy > 0 and nB >= 20 and bat >= 0.95
            L += [f"  {decrire(c)}",
                  f"    B : {int(nB)} trades, net moyen {moy:+.2f} pt, t par seance {tB:+.2f} (seuil {seuil}), placebo battu "
                  f"{bat:.1%} -> {'RETENUE' if ok else 'non retenue'}"]
    texte = "\n".join(L)
    (RES / "partie2_coffre.txt").write_text(texte + "\n")
    print(texte)


def glissant():
    cf = pd.read_pickle(G.CALCUL / "configs.pkl")
    info = pd.read_pickle(G.CALCUL / "info.pkl")
    jou = np.load(G.CALCUL / "jouable.npy")
    jours = info["jour"]
    mois = pd.period_range("2026-05", "2026-10", freq="M")
    L = ["Partie 2, reglage glissant : au debut de chaque mois, la configuration au meilleur score sur tout le passe "
         "(depuis avril) est jouee le mois suivant. Hors echantillon : mai - 16 octobre 2026.", ""]
    resultats = {}
    for nom in ["reel"] + [f"bruit{g}" for g in G.GRAINES]:
        P, N = charger(nom)
        hors, lignes = [], []
        for mo in mois:
            passe = np.flatnonzero(jou & (jours < mo.start_time).to_numpy())
            joue = np.flatnonzero(jou & (jours.dt.to_period("M") == mo).to_numpy())
            if len(joue) == 0:
                continue
            sc, t, n, moy, el = score(P, N, passe, 0.5 * len(passe))
            sc = np.where(el & (n > 0), sc, -np.inf)
            i = int(np.argmax(sc))
            g = P[i, joue]
            hors.append(g)
            lignes.append(f"    {mo} : choisie {cf['famille'][i]} (score passe {sc[i]:.2f}, t passe {t[i]:+.2f}) -> "
                          f"{int(N[i, joue].sum())} trades, {g.sum():+.0f} pt")
            if nom == "reel":
                lignes.append(f"        {decrire(cf.iloc[i])}")
        h = np.concatenate(hors)
        tt = t_lignes(h[None, :])[0]
        resultats[nom] = (tt, h.sum())
        L.append(f"  {nom} : hors echantillon {len(h)} seances, total {h.sum():+.0f} pt ({h.sum() * 2:+,.0f} $ par MNQ), "
                 f"t par seance {tt:+.2f}")
        L += lignes
    tr, gr = resultats["reel"]
    utile = tr >= 1.65 and gr > 0 and all(tr > resultats[k][0] for k in resultats if k != "reel")
    L += ["", f"Decision fixee a l'avance : reglage glissant {'UTILE' if utile else 'pas utile'} "
              f"(t {tr:+.2f}, seuil 1,65, et mieux que les 4 bruits)"]
    # configuration du jour : meilleure sur tout l'historique (descriptif, c'est ce que le bot recevrait)
    P, N = charger("reel")
    tout = np.flatnonzero(jou)
    sc, t, n, moy, el = score(P, N, tout, 0.5 * len(tout))
    sc = np.where(el & (n > 0), sc, -np.inf)
    i = int(np.argmax(sc))
    L += ["", "Meilleure configuration sur tout l'historique (avril - 16 octobre ; descriptif, chiffres optimistes car "
              "choisie sur ces memes seances) :",
          f"  {decrire(cf.iloc[i])}",
          f"  {int(n[i])} trades, net moyen {moy[i]:+.2f} pt, t par seance {t[i]:+.2f}, configuration n. {i}"]
    texte = "\n".join(L)
    (RES / "partie2_glissant.txt").write_text(texte + "\n")
    (RES / "configuration_du_jour.json").write_text(json.dumps({"configuration": i, "description": decrire(cf.iloc[i]),
                                                                "famille": cf["famille"][i],
                                                                "signal": list(cf["signal"][i]),
                                                                **{k: (float(cf[k][i]) if k in ("objectif", "stop_min")
                                                                       else int(cf[k][i]))
                                                                   for k in ("objectif", "duree", "stop_min", "t_max",
                                                                             "sens")}},
                                                               ensure_ascii=False, indent=1) + "\n")
    print(texte)


if __name__ == "__main__":
    {"explorer": explorer, "coffre": coffre, "glissant": glissant}[sys.argv[1]]()
