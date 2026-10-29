#!/usr/bin/env python3
"""Partie 3 (flux/README.md) : exploration (tape : A ; G2b : 2012 - 2022), barriere des 8 bruits, finalistes ; coffre
unique pour toute la vague (tape : B ; G2b : 2023 - 2026) ; reglage glissant (G1 - G9).

  python3 flux/selection3.py explorer   -> resultats/partie3_exploration.txt, resultats/finalistes3.json (+ empreinte)
  python3 flux/selection3.py coffre     -> resultats/partie3_coffre.txt (une seule fois)
  python3 flux/selection3.py glissant   -> resultats/partie3_glissant.txt"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statistics import NormalDist

import quant as Q
import reglages as R

ICI = Path(__file__).resolve().parent
RES = ICI / "resultats"
FIN_A = pd.Timestamp("2026-07-31")
DEBUT_G2B, FIN_G2B = pd.Timestamp("2012-01-01"), pd.Timestamp("2022-12-31")
N_COFFRE = {"G4": 10, "G5": 10, "G9": 10, "G2b": 100}


def charger(nom):
    z = np.load(R.CALCUL / f"{nom}.npz")
    return z["P"].astype(np.float64), z["N"].astype(np.float64)


def t_lignes(P):
    n = P.shape[1]
    s = P.std(axis=1, ddof=1)
    return np.where(s > 0, P.mean(axis=1) / np.where(s > 0, s, 1) * np.sqrt(n), 0.0)


def score(P, N, cols, n_min):
    Pc, Nc = P[:, cols], N[:, cols]
    n = Nc.sum(axis=1)
    moy = np.where(n > 0, Pc.sum(axis=1) / np.where(n > 0, n, 1), 0.0)
    t = t_lignes(Pc)
    return t * np.minimum(1.0, n / n_min), t, n, moy


def decrire(c):
    sg = ", ".join(str(x) for x in c["signal"])
    duree = "jusqu'a 15 h 59" if c["duree"] == 0 else f"{c['duree']} min"
    stop = "aucun" if c["stop_u"] == 0 else f"{c['stop_u']:g} u"
    obj = "aucun" if c["objectif_u"] == 0 else f"{c['objectif_u']:g} u"
    return f"{c['famille']} ({sg}) | {duree}, stop {stop}, objectif {obj}, sens {'de base' if c['sens'] == 1 else 'inverse'}"


def colonnes():
    info = pd.read_pickle(R.CALCUL / "q_info.pkl")
    jou = np.load(R.CALCUL / "q_jouable.npy")
    A = np.flatnonzero(jou & (info["jour"] <= FIN_A).to_numpy())
    B = np.flatnonzero(jou & (info["jour"] > FIN_A).to_numpy())
    jb = pd.read_pickle(R.CALCUL / "q_jours_g2b.pkl")
    joub = np.load(R.CALCUL / "q_jouable_g2b.npy")
    Ab = np.flatnonzero(joub & ((jb >= DEBUT_G2B) & (jb <= FIN_G2B)).to_numpy())
    Bb = np.flatnonzero(joub & (jb > FIN_G2B).to_numpy())
    return info, jou, A, B, jb, Ab, Bb


def explorer():
    cf = pd.read_pickle(R.CALCUL / "q_configs.pkl")
    cb = pd.read_pickle(R.CALCUL / "q_configs_g2b.pkl")
    info, jou, A, B, jb, Ab, Bb = colonnes()
    L = [f"Partie 3, exploration. Tape : A = {len(A)} seances jouables ({info['jour'][A[0]].date()} - "
         f"{info['jour'][A[-1]].date()}), {len(cf)} configurations. G2b : {len(Ab)} seances (2012 - 2022), "
         f"{len(cb)} configurations. Score = t par seance x min(1, trades / n_min). 8 graines de bruit.", ""]
    finalistes = []
    for nom_jeu, table, cols, prefixe in (("tape", cf, A, "q_"), ("G2b", cb, Ab, "q_g2b_")):
        n_min = np.array([Q.N_MIN.get(f, 40) for f in table["famille"]], float)
        barr = {}
        for g in Q.GRAINES:
            P, N = charger(f"{prefixe}bruit{g}")
            sc, t, n, moy = score(P, N, cols, n_min)
            ok = (moy > 0) & (n >= n_min)
            for fam in table["famille"].unique():
                f = (table["famille"] == fam).to_numpy() & ok
                barr.setdefault(fam, []).append(sc[f].max() if f.any() else -np.inf)
        P, N = charger(f"{prefixe}reel")
        sc, t, n, moy = score(P, N, cols, n_min)
        ok = (moy > 0) & (n >= n_min)
        for fam in table["famille"].unique():
            f = (table["famille"] == fam).to_numpy()
            b = max(barr[fam])
            moyb = np.mean([x for x in barr[fam] if np.isfinite(x)]) if np.isfinite(barr[fam]).any() else float("nan")
            L.append(f"{fam} ({int(f.sum())} configurations) : eligibles reels {int((f & ok).sum())} ; meilleur score reel "
                     f"{sc[f & ok].max() if (f & ok).any() else float('nan'):.2f} ; bruit {', '.join(f'{x:.2f}' for x in barr[fam])}"
                     f" (moyenne {moyb:.2f}) -> barriere {b:.2f}")
            if (f & ok).any():
                i = int(np.flatnonzero(f & ok)[np.argmax(sc[f & ok])])
                L.append(f"    meilleure reelle : {decrire(table.iloc[i])}")
                L.append(f"    {int(n[i])} trades, net moyen {moy[i]:+.2f} pt, t par seance {t[i]:+.2f}, score {sc[i]:.2f} -> "
                         + ("FINALISTE" if sc[i] > b else "pas finaliste (le bruit fait aussi bien ou mieux)"))
                if sc[i] > b:
                    finalistes.append({"jeu": nom_jeu, "ligne": i, "description": decrire(table.iloc[i])})
        L.append("")
    L.append(f"Finalistes : {len(finalistes)}")
    texte = "\n".join(L)
    (RES / "partie3_exploration.txt").write_text(texte + "\n")
    contenu = json.dumps({"finalistes": finalistes}, ensure_ascii=False, indent=1) + "\n"
    (RES / "finalistes3.json").write_text(contenu)
    (RES / "finalistes3.sha256").write_text(hashlib.sha256(contenu.encode()).hexdigest() + "\n")
    print(texte)


def coffre():
    contenu = (RES / "finalistes3.json").read_text()
    if hashlib.sha256(contenu.encode()).hexdigest() != (RES / "finalistes3.sha256").read_text().strip():
        raise SystemExit("finalistes modifies : coffre refuse")
    if (RES / "partie3_coffre.txt").exists():
        raise SystemExit("coffre deja ouvert")
    fin = json.loads(contenu)["finalistes"]
    m = len(fin)
    L = [f"Partie 3, coffre (tape : 3 aout - 16 octobre 2026 ; G2b : 2023 - 28 octobre 2026), ouvert une fois ; m = {m}"]
    if m == 0:
        L.append("Aucune finaliste : rien a juger.")
    else:
        seuil = NormalDist().inv_cdf(1 - 0.05 / m)
        info, jou, A, B, jb, Ab, Bb = colonnes()
        X = {}
        for f in fin:
            table = pd.read_pickle(R.CALCUL / ("q_configs.pkl" if f["jeu"] == "tape" else "q_configs_g2b.pkl"))
            c = table.iloc[f["ligne"]]
            cols = B if f["jeu"] == "tape" else Bb
            if f["jeu"] == "tape" and c["famille"] == "G6":
                cols = cols[np.load(R.CALCUL / "q_gros.npy")[cols]]
            P, N = charger("q_reel" if f["jeu"] == "tape" else "q_g2b_reel")
            nB = N[f["ligne"], cols].sum()
            moy = P[f["ligne"], cols].sum() / nB if nB else 0.0
            tB = t_lignes(P[f["ligne"], cols][None, :])[0]
            if f["jeu"] not in X:
                X[f["jeu"]] = Q.tape()[0] if f["jeu"] == "tape" else Q.libre()[0]
            tr = Q.trades_config(X[f["jeu"]], c)
            tr = tr[tr["seance"].isin(cols)]
            pos = pd.Index(cols).get_indexer(tr["seance"])
            rng = np.random.default_rng(1)
            a, b = tr["net"].to_numpy(), tr["net_inverse"].to_numpy()
            pl = np.array([t_lignes(np.bincount(pos, weights=np.where(rng.random(len(a)) < 0.5, a, b),
                                                minlength=len(cols))[None, :])[0] for _ in range(2000)])
            bat = (pl < tB).mean()
            ok = tB >= seuil and moy > 0 and nB >= N_COFFRE.get(c["famille"], 15) and bat >= 0.95
            L += [f"  {f['description']}",
                  f"    coffre : {int(nB)} trades, net moyen {moy:+.2f} pt, t par seance {tB:+.2f} (seuil {seuil:.2f}), "
                  f"placebo battu {bat:.1%} -> {'RETENUE' if ok else 'non retenue'}"]
    texte = "\n".join(L)
    (RES / "partie3_coffre.txt").write_text(texte + "\n")
    print(texte)


def glissant():
    cf = pd.read_pickle(R.CALCUL / "q_configs.pkl")
    info, jou, A, B, jb, Ab, Bb = colonnes()
    jours = info["jour"]
    n_min_rel = np.array([0.25 if f in ("G4", "G5", "G9") else 0.5 for f in cf["famille"]])
    L = ["Partie 3, reglage glissant (G1 - G9 ensemble) : au debut de chaque mois, la configuration au meilleur score "
         "sur tout le passe est jouee le mois suivant. Hors echantillon : mai - 16 octobre 2026.", ""]
    res = {}
    for nom in ["reel"] + [f"bruit{g}" for g in Q.GRAINES]:
        P, N = charger(f"q_{nom}")
        hors, lignes = [], []
        for mo in pd.period_range("2026-05", "2026-10", freq="M"):
            passe = np.flatnonzero(jou & (jours < mo.start_time).to_numpy())
            joue = np.flatnonzero(jou & (jours.dt.to_period("M") == mo).to_numpy())
            sc, t, n, moy = score(P, N, passe, n_min_rel * len(passe))
            sc = np.where((moy > 0) & (n > 0), sc, -np.inf)
            i = int(np.argmax(sc))
            hors.append(P[i, joue])
            lignes.append(f"    {mo} : {decrire(cf.iloc[i])} (score passe {sc[i]:.2f}) -> {int(N[i, joue].sum())} trades, "
                          f"{P[i, joue].sum():+.0f} pt")
        h = np.concatenate(hors)
        tt = t_lignes(h[None, :])[0]
        res[nom] = (tt, h.sum())
        L.append(f"  {nom} : {len(h)} seances hors echantillon, total {h.sum():+.0f} pt ({2 * h.sum():+,.0f} $ par MNQ), "
                 f"t par seance {tt:+.2f}")
        if nom == "reel":
            L += lignes
    tr, gr = res["reel"]
    utile = tr >= 1.65 and gr > 0 and all(tr > res[k][0] for k in res if k != "reel")
    L += ["", f"Decision fixee a l'avance : reglage glissant {'UTILE' if utile else 'pas utile'} (t {tr:+.2f})"]
    texte = "\n".join(L)
    (RES / "partie3_glissant.txt").write_text(texte + "\n")
    print(texte)


if __name__ == "__main__":
    {"explorer": explorer, "coffre": coffre, "glissant": glissant}[sys.argv[1]]()
