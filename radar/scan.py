#!/usr/bin/env python3
"""Radar, scan des regles (radar/README.md, protocole du 29 octobre 2026) : toutes les regles a une ou deux conditions
x 49 couples entree-duree x 2 sens, sur le NQ. Etape 1 (exploration 2011 - 2018), etape 2 (confirmation 2019 - 2022)
avec la barre des placebos, puis, seulement avec --coffre, etape 3 (2023 - 2026).

Les sommes de toutes les paires de conditions se font d'un coup : pour une heure d'entree, I (seances x conditions)
donne N = I'I (trades), S1 = I'(I.g) et S2 = I'(I.g^2) (somme et somme des carres des gains bruts).

Lancer : RADAR_CALCUL=<dossier de variables.npz> python3 radar/scan.py [--placebos 20] [--coffre]"""
import argparse
import json
import os
import time
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
CALCUL = Path(os.getenv("RADAR_CALCUL", str(ICI / "calcul")))
RESULTATS = ICI / "resultats"
FRAIS = 3.0
FIN_EXPLO, DEBUT_CONF, FIN_CONF, DEBUT_COFFRE = "2018-12-31", "2019-01-01", "2022-12-31", "2023-01-01"
MIN_E, MIN_C, T_E, GARDER = 120, 40, 3.0, 5000
QUANTILES = (0.1, 0.2, 0.4, 0.6, 0.8, 0.9)
NOMS_BINS = ["10 % bas", "Q1", "Q2", "Q3", "Q4", "Q5", "10 % haut"]
PLANCHER_C = 3.0
GRAINE = 20261029


def charger():
    z = np.load(CALCUL / "variables.npz", allow_pickle=False)
    d = {k: z[k] for k in z.files}
    d["jours"] = pd.DatetimeIndex(d["jours"].astype("datetime64[D]"))
    d["cles"] = [tuple(int(x) for x in c) for c in d["cles"]]
    return d


def periodes(jours):
    return {"E": np.asarray(jours <= FIN_EXPLO), "C": np.asarray((jours >= DEBUT_CONF) & (jours <= FIN_CONF)),
            "T": np.asarray(jours >= DEBUT_COFFRE)}


def conditions(X, B, explo):
    """Conditions d'une heure d'entree : 7 tranches par variable continue (seuils de l'exploration), 1 par variable du
    calendrier. Renvoie I (seances x K, 0/1), la variable de chaque condition et sa description."""
    cols, var, desc = [], [], []
    for f in range(X.shape[1]):
        x = X[:, f]
        xe = x[explo & np.isfinite(x)]
        if len(xe) < 200:
            continue
        q = np.quantile(xe, QUANTILES)
        fin = np.isfinite(x)
        xx = np.where(fin, x, np.nan)
        with np.errstate(invalid="ignore"):
            tranches = [xx <= q[0], xx <= q[1], (xx > q[1]) & (xx <= q[2]), (xx > q[2]) & (xx <= q[3]),
                        (xx > q[3]) & (xx <= q[4]), xx > q[4], xx > q[5]]
        for k, c in enumerate(tranches):
            cols.append(c & fin)
            var.append(f)
            desc.append((f, k, q))
    for b in range(B.shape[1]):
        cols.append(B[:, b])
        var.append(X.shape[1] + b)
        desc.append((X.shape[1] + b, -1, None))
    return np.column_stack(cols).astype(np.float64), np.array(var), desc


def stats(I, g, lignes):
    """N, S1, S2 de toutes les paires de conditions sur les seances `lignes` (g : gain brut d'un achat)."""
    Ip = I[lignes]
    gp = g[lignes]
    N = Ip.T @ Ip
    A = Ip * gp[:, None]
    S1 = Ip.T @ A
    S2 = Ip.T @ (A * gp[:, None])
    return N, S1, S2


def t_net(N, S1, S2, sens):
    with np.errstate(invalid="ignore", divide="ignore"):
        moy = sens * S1 / N - FRAIS
        var = (S2 - S1 * S1 / N) / (N - 1)
        t = moy / np.sqrt(var) * np.sqrt(N)
    return moy, t


def etape1(d, X3, B, P):
    """Meilleure regle d'exploration de chaque famille (variables, heure d'entree). Renvoie un DataFrame."""
    lignes_ok = d["ok"].astype(bool)
    out = []
    pre = {}
    for ie, e in enumerate(d["entrees"]):
        I, var, desc = conditions(X3[ie], B, P["E"])
        I[~lignes_ok] = 0.0
        K = I.shape[1]
        meme = var[:, None] == var[None, :]
        interdit = meme & ~np.eye(K, dtype=bool) | np.tril(np.ones((K, K), bool), -1)
        meilleur = np.full((K, K), -np.inf)
        choix = np.zeros((K, K, 2), np.int16)
        for ih, (ee, H) in enumerate(d["cles"]):
            if ee != e:
                continue
            g = np.nan_to_num(d["gains"][ih])
            N, S1, S2 = stats(I, g, P["E"] & lignes_ok)
            for sens in (1, -1):
                _, t = t_net(N, S1, S2, sens)
                t = np.where((N >= MIN_E) & ~interdit & np.isfinite(t), t, -np.inf)
                mieux = t > meilleur
                meilleur = np.where(mieux, t, meilleur)
                choix[mieux] = (ih, sens)
        k1, k2 = np.nonzero(meilleur >= T_E)
        for a, b in zip(k1, k2):
            out.append((int(e), int(var[a]), int(var[b]), int(a), int(b), int(choix[a, b, 0]), int(choix[a, b, 1]),
                        float(meilleur[a, b])))
        pre[int(e)] = (I, var, desc)
    t = pd.DataFrame(out, columns=["e", "va", "vb", "ka", "kb", "ih", "sens", "t_E"])
    if len(t):
        t = t.loc[t.groupby(["e", "va", "vb"])["t_E"].idxmax()].sort_values("t_E", ascending=False).head(GARDER)
    return t.reset_index(drop=True), pre


def rejouer(d, pre, r, lignes):
    """Gains nets par seance d'une regle (NaN hors trade) sur les seances `lignes`."""
    I, _, _ = pre[int(r["e"])]
    g = d["gains"][int(r["ih"])]
    pris = (I[:, int(r["ka"])] > 0) & (I[:, int(r["kb"])] > 0) & d["ok"].astype(bool) & lignes & np.isfinite(g)
    return np.where(pris, r["sens"] * g - FRAIS, np.nan)


def t_serie(x):
    x = x[np.isfinite(x)]
    if len(x) < 2 or x.std(ddof=1) == 0:
        return len(x), np.nan, np.nan
    return len(x), x.mean(), x.mean() / x.std(ddof=1) * np.sqrt(len(x))


def etape2(d, sel, pre, P):
    rows = []
    for _, r in sel.iterrows():
        n, m, t = t_serie(rejouer(d, pre, r, P["C"]))
        rows.append((n, m, t))
    sel = sel.copy()
    sel["n_C"], sel["moy_C"], sel["t_C"] = zip(*rows) if rows else ([], [], [])
    return sel


def decaler(d, k):
    X3 = np.roll(d["cube"], k, axis=1)
    B = np.roll(d["B"], k, axis=0)
    return X3, B


def libelle(d, pre, r):
    noms = list(d["noms"]) + list(d["binaires"])
    _, _, desc = pre[int(r["e"])]
    parts = []
    for k in sorted({int(r["ka"]), int(r["kb"])}):
        f, b, q = desc[k]
        parts.append(noms[f] if b < 0 else f"{noms[f]} {NOMS_BINS[b]}")
    e, H = d["cles"][int(r["ih"])]
    h, m = divmod(570 + e, 60)
    return (f"{'achat' if r['sens'] > 0 else 'vente'} a {h} h {m:02d}, "
            f"{'jusqu a 16 h' if H == 0 else f'{H} min'} si " + " et ".join(parts))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--placebos", type=int, default=20)
    ap.add_argument("--coffre", action="store_true")
    a = ap.parse_args()
    d = charger()
    P = periodes(d["jours"])
    RESULTATS.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    sel, pre = etape1(d, d["cube"], d["B"], P)
    sel = etape2(d, sel, pre, P)
    print(f"etape 1 : {len(sel)} familles envoyees (t_E de {sel['t_E'].min():.2f} a {sel['t_E'].max():.2f}) "
          f"en {time.time() - t0:.0f} s ; meilleur t_C {sel['t_C'].max():.2f}", flush=True)
    rng = np.random.default_rng(GRAINE)
    S = len(d["jours"])
    fichier_pl = RESULTATS / "scan_placebos.json"
    placebos = json.loads(fichier_pl.read_text()) if fichier_pl.exists() else []
    decalages = rng.integers(250, S - 250, size=max(a.placebos, 1))
    while len(placebos) < a.placebos:
        k = int(decalages[len(placebos)])
        X3, B = decaler(d, k)
        s_pl, pre_pl = etape1(d, X3, B, P)
        s_pl = etape2(d, s_pl, pre_pl, P)
        placebos.append({"decalage": k, "familles": int(len(s_pl)), "t_E_max": float(s_pl["t_E"].max()),
                         "t_C_max": float(np.nanmax(s_pl["t_C"])) if len(s_pl) else float("nan"),
                         "nb_t_C_3": int((s_pl["t_C"] >= 3).sum())})
        print(f"placebo {len(placebos)} (decalage {k}) : {len(s_pl)} familles, meilleur t_E {s_pl['t_E'].max():.2f}, "
              f"meilleur t_C {placebos[-1]['t_C_max']:.2f}", flush=True)
        fichier_pl.write_text(json.dumps(placebos, indent=1) + "\n")
    maxs = np.array([p["t_C_max"] for p in placebos[:a.placebos]])
    barre = max(PLANCHER_C, float(np.quantile(maxs, 0.95))) if len(maxs) else PLANCHER_C
    surv = sel[(sel["t_C"] >= barre) & (sel["n_C"] >= MIN_C) & (sel["moy_C"] > 0)].copy()
    # doublons : correlation des gains par seance sur exploration + confirmation
    garde = []
    series = {}
    for i, r in surv.sort_values("t_C", ascending=False).iterrows():
        x = rejouer(d, pre, r, P["E"] | P["C"])
        x0 = np.nan_to_num(x)
        if any(np.corrcoef(x0, series[j])[0, 1] > 0.7 for j in garde):
            continue
        garde.append(i)
        series[i] = x0
    surv = surv.loc[garde]
    sel["regle"] = [libelle(d, pre, r) for _, r in sel.iterrows()]
    surv["regle"] = [libelle(d, pre, r) for _, r in surv.iterrows()]
    L = ["Radar, scan des regles (radar/README.md, protocole du 29 octobre 2026)", "",
         f"{len(d['jours'])} seances du NQ ({d['jours'][0].date()} - {d['jours'][-1].date()}), {len(d['noms'])} variables "
         f"continues, {len(d['binaires'])} du calendrier, 11 heures d'entree, 49 couples entree-duree.",
         f"Etape 1 : {len(sel)} familles envoyees en confirmation (t_E >= {T_E}, au plus {GARDER}).",
         f"Placebos ({len(maxs)}) : meilleur t de confirmation " + ", ".join(f"{x:.2f}" for x in sorted(maxs)),
         f"Barre de confirmation : {barre:.2f}", f"Survivantes de l'etape 2 (sans doublons) : {len(surv)}", ""]
    L += ["Les 30 meilleures familles en confirmation (toutes, survivantes ou non) :", ""]
    for _, r in sel.sort_values("t_C", ascending=False).head(30).iterrows():
        L.append(f"  t_E {r['t_E']:5.2f}  t_C {r['t_C']:5.2f}  n_C {int(r['n_C']):4d}  moy_C {r['moy_C']:+7.2f} $  "
                 f"{r['regle']}")
    if len(surv):
        L += ["", "Survivantes :", ""]
        for _, r in surv.iterrows():
            L.append(f"  t_E {r['t_E']:5.2f}  t_C {r['t_C']:5.2f}  n_C {int(r['n_C']):4d}  moy_C {r['moy_C']:+7.2f} $  "
                     f"{r['regle']}")
    if a.coffre and len(surv):
        m = len(surv)
        seuil = NormalDist().inv_cdf(1 - 0.05 / m)
        L += ["", f"COFFRE 2023 - 2026 (ouvert une fois) : seuil t >= {seuil:.2f} (Bonferroni pour {m}), 3 annees sur 4", ""]
        for i, r in surv.iterrows():
            x = rejouer(d, pre, r, P["T"])
            n, moy, t = t_serie(x)
            ans = pd.Series(x, index=d["jours"]).dropna().groupby(lambda j: j.year).sum()
            passe = (moy > 0) and (t >= seuil) and ((ans > 0).sum() >= 3)
            surv.loc[i, ["n_T", "moy_T", "t_T", "passe"]] = [n, moy, t, passe]
            L.append(f"  {'PASSE' if passe else 'echoue'}  n {n}  moy {moy:+.2f} $  t {t:.2f}  annees " +
                     ", ".join(f"{y} {v:+.0f}" for y, v in ans.items()) + f"  | {r['regle']}")
    (RESULTATS / ("scan_coffre.txt" if a.coffre else "scan.txt")).write_text("\n".join(L) + "\n")
    sel.to_csv(RESULTATS / "scan_familles.csv.gz", index=False, float_format="%.4f")
    surv.to_csv(RESULTATS / ("scan_survivantes_coffre.csv" if a.coffre else "scan_survivantes.csv"), index=False,
                float_format="%.4f")
    print("\n".join(L))


if __name__ == "__main__":
    main()
