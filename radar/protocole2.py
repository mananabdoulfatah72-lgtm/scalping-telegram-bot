#!/usr/bin/env python3
"""Radar, protocole 2 (radar/README.md, fixe le 30 octobre 2026) : le scan du protocole 1 elargi a 8 marches tradables
en micro chez Bulenox, une entree toutes les 15 minutes, de nouvelles variables de seance, et une regression logistique
par marche et par couple entree-duree. Coffre 2023 - 2026 seulement avec --coffre.

Lancer : KB=<copie de claude/keen-babbage-r686cl> ROBOT=<zone/robot/nq_1min.csv.gz de main> RADAR_CALCUL=<dossier>
         python3 radar/protocole2.py [--cibles NQ,ES,...] [--placebos 20] [--coffre]"""
import argparse
import json
import sys
import time
import warnings
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

import scan as SC
import variables as V

warnings.filterwarnings("ignore", category=RuntimeWarning)
K = V.K
SD = V.SD
ICI = Path(__file__).resolve().parent
RESULTATS = ICI / "resultats" / "protocole2"
CALCUL = V.CALCUL / "protocole2"
CIBLES = ["NQ", "ES", "RTY", "YM", "GC", "CL", "6E", "BTC"]
FICHIERS = {"NQ": None, "ES": "intraday/donnees/sp500_1min.csv.gz", "RTY": "zone_multi/donnees/russell_1min.csv.gz",
            "YM": "zone_multi/donnees/dow_1min.csv.gz", "GC": "zone_multi/donnees/or_1min.csv.gz",
            "CL": "zone_multi/donnees/petrole_1min.csv.gz", "6E": "zone_multi/donnees/euro_1min.csv.gz",
            "BTC": "tournoi5/donnees/bitcoin_1min.csv.gz"}
DUREES = [15, 30, 60, 120, 0]
OUVERTURES_DEJA = 1                       # regle du protocole 1 deja jugee au coffre


def periodes(nom, jours):
    j = pd.DatetimeIndex(jours)
    if nom in ("NQ", "ES"):
        e, c0 = "2018-12-31", "2019-01-01"
    else:
        e, c0 = "2019-12-31", "2020-01-01"
    return {"E": np.asarray(j <= e), "C": np.asarray((j >= c0) & (j <= "2022-12-31")), "T": np.asarray(j >= "2023-01-01")}


def charger(nom):
    if nom == "NQ":
        return V.nq()
    return SD.minutes(nom, debut="2011-01-01")


def entrees(n):
    return np.arange(15, n - 30 + 1, 15)


def gains(d, ent):
    O, C = d["o"], d["c"]
    n = O.shape[1]
    ok = d["complete"] & ~d["ech"]
    ech = float(d["pref"]) / O[:, 0] * float(d["pt"])
    G = {}
    for e in ent:
        for H in DUREES:
            if H and e + H > n - 1:
                continue
            sortie = O[:, e + H] if H else C[:, n - 1]
            G[(int(e), H)] = np.where(ok, (sortie - O[:, e]) * ech, np.nan)
    return G


def grille(nom, jours, m0, n):
    """Clotures d'un autre marche a la meme heure de New York sur la fenetre [m0, m0 + n) de la cible (prolongees a
    plat), et son dernier prix connu a l'ouverture de la fenetre."""
    src = V.CALCUL / "nq_fusion.csv.gz" if nom == "NQ" else V.KB / FICHIERS[nom]
    d = pd.read_csv(src, usecols=["t", "o", "c"], dtype={"t": str})
    t = pd.to_datetime(d["t"])
    jour = t.dt.normalize().values.astype("datetime64[D]")
    m = (t.dt.hour * 60 + t.dt.minute).values
    ij = pd.DatetimeIndex(jours).get_indexer(pd.DatetimeIndex(jour))
    g = ij >= 0
    S = len(jours)
    Cm = np.full((S, 1440), np.nan)
    Cm[ij[g], m[g]] = d["c"].values[g]
    Om = np.full((S, 1440), np.nan)
    Om[ij[g], m[g]] = d["o"].values[g]
    Cm = pd.DataFrame(Cm).ffill(axis=1).values
    p0 = np.where(np.isfinite(Cm[:, m0 - 1]), Cm[:, m0 - 1], Om[:, m0])
    gc = pd.Series(d["c"].values[g]).groupby(ij[g])
    rng = (gc.max() - gc.min()).reindex(range(S)).values
    return Cm[:, m0:m0 + n], p0, rng


def variables_seance(d, nom, ent):
    O, Hh, L, C, Vv = d["o"], d["h"], d["l"], d["c"], d["v"]
    S, n = O.shape
    m0 = int(d["m0"])
    pm = d["prec_meme"]
    rng = Hh.max(1) - L.min(1)
    A20 = V.moyenne_avant(rng, 20, d["complete"])
    A100 = V.moyenne_avant(rng, 100, d["complete"])
    a = np.where(A20 > 0, A20, np.nan)
    v_prec = pm >= 0
    q = np.maximum(pm, 0)
    prevC = np.where(v_prec, C[q, n - 1], np.nan)
    prevH = np.where(v_prec, Hh[q].max(1), np.nan)
    prevL = np.where(v_prec, L[q].min(1), np.nan)
    hj = pd.Series(np.where(d["complete"], Hh.max(1), np.nan))
    lj = pd.Series(np.where(d["complete"], L.min(1), np.nan))
    h20 = hj.shift(1).rolling(20, min_periods=10).max().values
    l20 = lj.shift(1).rolling(20, min_periods=10).min().values
    contrat = d["contrat"]
    meme20 = np.r_[False, contrat[1:] == contrat[:-1]]                  # niveaux de 20 jours : meme contrat que la veille
    h20, l20 = np.where(meme20, h20, np.nan), np.where(meme20, l20, np.nan)
    tp = (Hh + L + C) / 3
    cv = np.cumsum(Vv, 1)
    vwap = np.cumsum(tp * Vv, 1) / np.where(cv > 0, cv, np.nan)
    cv_moy = np.vstack([V.moyenne_avant(cv[:, j], 20, d["complete"]) for j in range(n)]).T
    cmax, cmin = np.maximum.accumulate(Hh, 1), np.minimum.accumulate(L, 1)
    dc = np.abs(np.diff(np.c_[O[:, :1], C], axis=1)).cumsum(1)
    h30, l30 = Hh[:, :30].max(1), L[:, :30].min(1)
    h60, l60 = Hh[:, :60].max(1), L[:, :60].min(1)
    rond = float(d["rond"])
    autres = {}
    for x in CIBLES:
        if x == nom:
            continue
        g, p0, rx = grille(x, d["jours"], m0, n)
        autres[x] = (g, p0, V.moyenne_avant(rx, 20, np.isfinite(rx)))
    nan = np.full(S, np.nan)
    out = {}
    for e in ent:
        j = int(e) - 1
        f = {"ouv": (C[:, j] - O[:, 0]) / a}
        for k in (5, 15, 30, 60, 120):
            f[f"r{k}"] = (C[:, j] - C[:, j - k]) / a if j - k >= 0 else nan
        f["place"] = (C[:, j] - cmin[:, j]) / np.where(cmax[:, j] > cmin[:, j], cmax[:, j] - cmin[:, j], np.nan)
        f["amp"] = (cmax[:, j] - cmin[:, j]) / a
        f["amp30"] = (Hh[:, max(0, j - 29):j + 1].max(1) - L[:, max(0, j - 29):j + 1].min(1)) / a if j >= 29 else nan
        f["vwap"] = (C[:, j] - vwap[:, j]) / a
        f["volc"] = cv[:, j] / cv_moy[:, j]
        f["vol15"] = (cv[:, j] - cv[:, j - 15]) / (cv_moy[:, j] - cv_moy[:, j - 15]) if j >= 15 else nan
        f["ecart"] = (O[:, 0] - prevC) / a
        f["d_hv"] = (C[:, j] - prevH) / a
        f["d_bv"] = (C[:, j] - prevL) / a
        f["d_cv"] = (C[:, j] - prevC) / a
        f["d_h20"] = (C[:, j] - h20) / a
        f["d_b20"] = (C[:, j] - l20) / a
        f["or30"] = (C[:, j] - (h30 + l30) / 2) / np.where(h30 > l30, h30 - l30, np.nan) if e > 30 else nan
        f["or60"] = (C[:, j] - (h60 + l60) / 2) / np.where(h60 > l60, h60 - l60, np.nan) if e > 60 else nan
        f["eff"] = np.abs(C[:, j] - O[:, 0]) / np.where(dc[:, j] > 0, dc[:, j], np.nan)
        f["rond_h"] = (np.ceil(C[:, j] / rond) * rond - C[:, j]) / a
        f["rond_b"] = (C[:, j] - np.floor(C[:, j] / rond) * rond) / a
        f["age_h"] = (j - np.argmax(Hh[:, :e], 1)) / e
        f["age_b"] = (j - np.argmin(L[:, :e], 1)) / e
        for x, (g, p0, ax) in autres.items():
            f[f"{x}_ouv"] = (g[:, j] - p0) / ax
            f[f"{x}_r30"] = (g[:, j] - g[:, j - 30]) / ax if j >= 30 else nan
        out[int(e)] = f
    return out, dict(A20=A20, A100=A100, rng=rng, ok=d["complete"] & ~d["ech"])


def grandes_intraday(g, jours, m0, e):
    t930 = m0 + e - 570                                   # minutes depuis 9 h 30 a la decision
    k = (t930 - 1) // 30 * 30
    if k < 30 or k > 390:
        return np.full(len(jours), np.nan)
    piv = g.pivot(index="jour", columns="valeur", values=f"c{k}")
    po = g.pivot(index="jour", columns="valeur", values="ouverture")
    return (piv > po).mean(axis=1).where(piv.notna().sum(axis=1) >= 8).reindex(pd.DatetimeIndex(jours)).values


def cube(nom):
    CALCUL.mkdir(parents=True, exist_ok=True)
    f = CALCUL / f"{nom}.npz"
    if f.exists():
        z = np.load(f, allow_pickle=False)
        d = {k: z[k] for k in z.files}
        d["jours"] = pd.DatetimeIndex(d["jours"].astype("datetime64[D]"))
        d["cles"] = [tuple(int(x) for x in c) for c in d["cles"]]
        return d
    d = charger(nom)
    n = d["o"].shape[1]
    ent = entrees(n)
    G = gains(d, ent)
    intra, aux = variables_seance(d, nom, ent)
    fj, b = V.variables_jour(d, aux)
    fe, g = V.variables_externes(d)
    fn = V.variables_nouvelles(d)
    for k in [k for k in fn if k.startswith("_cal_")]:
        b[k[1:]] = fn.pop(k)
    X = {}
    for e in ent:
        x = dict(intra[int(e)])
        x["g_intra"] = grandes_intraday(g, d["jours"], int(d["m0"]), int(e))
        x.update(fj)
        x.update(fe)
        x.update(fn)
        X[int(e)] = x
    noms = list(X[int(ent[0])])
    cub = np.stack([np.column_stack([np.asarray(X[int(e)][k], float) for k in noms]) for e in ent]).astype(np.float32)
    binaires = sorted(b)
    B = np.column_stack([np.asarray(b[k], bool) for k in binaires])
    cles = sorted(G)
    out = dict(cube=cub, noms=np.array(noms), B=B, binaires=np.array(binaires), gains=np.stack([G[k] for k in cles]),
               cles=np.array(cles), ok=aux["ok"], jours=d["jours"].astype("datetime64[D]"), entrees=ent,
               frais=np.float64(d["frais"]), m0=np.int64(d["m0"]))
    np.savez_compressed(f, **out)
    return cube(nom)


# ------------------------------------------------------------------ etapes (comme scan.py, par marche)
def etape1(d, X3, B, P, frais):
    ok = d["ok"].astype(bool)
    out, pre = [], {}
    for ie, e in enumerate(d["entrees"]):
        I, var, desc = SC.conditions(X3[ie], B, P["E"])
        I[~ok] = 0.0
        Kc = I.shape[1]
        meme = var[:, None] == var[None, :]
        interdit = meme & ~np.eye(Kc, dtype=bool) | np.tril(np.ones((Kc, Kc), bool), -1)
        meilleur = np.full((Kc, Kc), -np.inf)
        choix = np.zeros((Kc, Kc, 2), np.int16)
        for ih, (ee, H) in enumerate(d["cles"]):
            if ee != e:
                continue
            gg = np.nan_to_num(d["gains"][ih])
            N, S1, S2 = SC.stats(I, gg, P["E"] & ok)
            for sens in (1, -1):
                with np.errstate(invalid="ignore", divide="ignore"):
                    moy = sens * S1 / N - frais
                    t = moy / np.sqrt((S2 - S1 * S1 / N) / (N - 1)) * np.sqrt(N)
                t = np.where((N >= SC.MIN_E) & ~interdit & np.isfinite(t), t, -np.inf)
                mieux = t > meilleur
                meilleur = np.where(mieux, t, meilleur)
                choix[mieux] = (ih, sens)
        k1, k2 = np.nonzero(meilleur >= SC.T_E)
        for a_, b_ in zip(k1, k2):
            out.append((int(e), int(var[a_]), int(var[b_]), int(a_), int(b_), int(choix[a_, b_, 0]),
                        int(choix[a_, b_, 1]), float(meilleur[a_, b_])))
        pre[int(e)] = (I, var, desc)
    t = pd.DataFrame(out, columns=["e", "va", "vb", "ka", "kb", "ih", "sens", "t_E"])
    if len(t):
        t = t.loc[t.groupby(["e", "va", "vb"])["t_E"].idxmax()].sort_values("t_E", ascending=False).head(SC.GARDER)
    return t.reset_index(drop=True), pre


def rejouer(d, pre, r, lignes, frais):
    I, _, _ = pre[int(r["e"])]
    g = d["gains"][int(r["ih"])]
    pris = (I[:, int(r["ka"])] > 0) & (I[:, int(r["kb"])] > 0) & d["ok"].astype(bool) & lignes & np.isfinite(g)
    return np.where(pris, r["sens"] * g - frais, np.nan)


def etape2(d, sel, pre, P, frais):
    sel = sel.copy()
    res = [SC.t_serie(rejouer(d, pre, r, P["C"], frais)) for _, r in sel.iterrows()]
    sel["n_C"], sel["moy_C"], sel["t_C"] = zip(*res) if res else ([], [], [])
    return sel


def libelle(d, pre, r, nom):
    noms = list(d["noms"]) + list(d["binaires"])
    _, _, desc = pre[int(r["e"])]
    parts = []
    for k in sorted({int(r["ka"]), int(r["kb"])}):
        f, b, _ = desc[k]
        parts.append(noms[f] if b < 0 else f"{noms[f]} {SC.NOMS_BINS[b]}")
    e, H = d["cles"][int(r["ih"])]
    h, m = divmod(int(d["m0"]) + e, 60)
    return (f"{nom} : {'achat' if r['sens'] > 0 else 'vente'} a {h} h {m:02d}, "
            f"{'jusqu a la cloture' if H == 0 else f'{H} min'} si " + " et ".join(parts))


def scanner(nom, n_placebos):
    d = cube(nom)
    P = periodes(nom, d["jours"])
    frais = float(d["frais"])
    t0 = time.time()
    sel, pre = etape1(d, d["cube"], d["B"], P, frais)
    sel = etape2(d, sel, pre, P, frais)
    fpl = RESULTATS / f"placebos_{nom}.json"
    pls = json.loads(fpl.read_text()) if fpl.exists() else []
    rng = np.random.default_rng(SC.GRAINE + CIBLES.index(nom))
    S = len(d["jours"])
    dec = rng.integers(250, S - 250, size=max(n_placebos, 1))
    while len(pls) < n_placebos:
        k = int(dec[len(pls)])
        X3, B = np.roll(d["cube"], k, axis=1), np.roll(d["B"], k, axis=0)
        s, p = etape1(d, X3, B, P, frais)
        s = etape2(d, s, p, P, frais)
        jug = s[(s["n_C"] >= SC.MIN_C) & (s["moy_C"] > 0)]
        pls.append({"decalage": k, "familles": int(len(s)), "t_C_max": float(jug["t_C"].max()) if len(jug) else 0.0})
        fpl.write_text(json.dumps(pls, indent=1) + "\n")
    maxs = np.array([p["t_C_max"] for p in pls[:n_placebos]])
    barre = max(SC.PLANCHER_C, float(np.quantile(maxs, 0.95))) if len(maxs) else SC.PLANCHER_C
    sel["regle"] = [libelle(d, pre, r, nom) for _, r in sel.iterrows()]
    surv = sel[(sel["t_C"] >= barre) & (sel["n_C"] >= SC.MIN_C) & (sel["moy_C"] > 0)].sort_values("t_C", ascending=False)
    garde, series = [], {}
    for i, r in surv.iterrows():
        x0 = np.nan_to_num(rejouer(d, pre, r, P["E"] | P["C"], frais))
        if any(np.corrcoef(x0, series[j])[0, 1] > 0.7 for j in garde):
            continue
        garde.append(i)
        series[i] = x0
    surv = surv.loc[garde].copy()
    surv["cible"] = nom
    L = [f"Protocole 2, {nom} : {len(d['jours'])} seances ({d['jours'][0].date()} - {d['jours'][-1].date()}), "
         f"{len(d['noms'])} variables continues, {len(d['binaires'])} du calendrier, {len(d['entrees'])} heures "
         f"d'entree, {len(d['cles'])} couples entree-duree ; frais {frais:.2f} $",
         f"Etape 1 : {len(sel)} familles (t_E >= 3) ; placebos : " + ", ".join(f"{x:.2f}" for x in sorted(maxs)),
         f"Barre de confirmation {barre:.2f} ; survivantes (sans doublons) : {len(surv)} ; calcul {time.time() - t0:.0f} s",
         ""]
    for _, r in sel.sort_values("t_C", ascending=False).head(10).iterrows():
        L.append(f"  t_E {r['t_E']:5.2f}  t_C {r['t_C']:5.2f}  n_C {int(r['n_C']):4d}  moy_C {r['moy_C']:+8.2f} $  "
                 f"{r['regle']}")
    (RESULTATS / f"scan_{nom}.txt").write_text("\n".join(L) + "\n")
    sel.to_csv(RESULTATS / f"familles_{nom}.csv.gz", index=False, float_format="%.4f")
    print("\n".join(L), flush=True)
    return surv, d, pre


def logistique(nom):
    """Regression logistique par couple entree-duree, reentrainee chaque annee (des 500 seances d'entrainement)."""
    from sklearn.linear_model import LogisticRegression
    d = cube(nom)
    frais = float(d["frais"])
    an = np.asarray(d["jours"].year)
    ok = d["ok"].astype(bool)
    lignes = []
    preds = {}
    for ih, (e, H) in enumerate(d["cles"]):
        ie = list(d["entrees"]).index(e)
        X = np.column_stack([d["cube"][ie].astype(float), d["B"].astype(float)])
        g = d["gains"][ih]
        p = np.full(len(g), np.nan)
        dl = np.full(len(g), np.nan)
        for Y in range(int(an.min()) + 1, 2027):
            tr = ok & (an < Y) & np.isfinite(g)
            te = ok & (an == Y)
            if tr.sum() < 500 or te.sum() == 0:
                continue
            Xtr, Xte = X[tr], X[te]
            fin = np.isfinite(Xtr)
            gk = (fin.sum(0) >= 100) & (np.nanstd(np.where(fin, Xtr, np.nan), 0) > 0)
            Xtr, Xte = Xtr[:, gk], Xte[:, gk]
            mu, sd = np.nanmean(Xtr, 0), np.nanstd(Xtr, 0)
            sd = np.where(sd > 0, sd, 1.0)
            Xtr = np.clip(np.nan_to_num((Xtr - mu) / sd), -5, 5)
            Xte = np.clip(np.nan_to_num((Xte - mu) / sd), -5, 5)
            mod = LogisticRegression(max_iter=2000).fit(Xtr, g[tr] > 0)
            ptr = mod.predict_proba(Xtr)[:, 1]
            p[te] = mod.predict_proba(Xte)[:, 1]
            dl[te] = np.quantile(np.abs(ptr - 0.5), 0.7)
        sens = np.where(p > 0.5 + dl, 1.0, np.where(p < 0.5 - dl, -1.0, 0.0))
        net = np.where((sens != 0) & np.isfinite(g) & ok, sens * g - frais, np.nan)
        preds[ih] = net
        oos = an <= 2022
        n_, m_, t_ = SC.t_serie(net[oos])
        lignes.append(dict(cible=nom, e=e, H=H, ih=ih, n_oos=n_, moy_oos=m_, t_oos=t_))
    return pd.DataFrame(lignes), preds, d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cibles", default=",".join(CIBLES))
    ap.add_argument("--placebos", type=int, default=20)
    ap.add_argument("--coffre", action="store_true")
    ap.add_argument("--sans-ia", action="store_true")
    a = ap.parse_args()
    RESULTATS.mkdir(parents=True, exist_ok=True)
    cibles = a.cibles.split(",")
    tout, ctx = [], {}
    for nom in cibles:
        surv, d, pre = scanner(nom, a.placebos)
        tout.append(surv)
        ctx[nom] = (d, pre)
    surv = pd.concat(tout, ignore_index=True) if tout else pd.DataFrame()
    ia_t, ia_ctx = [], {}
    if not a.sans_ia:
        for nom in cibles:
            t, preds, d = logistique(nom)
            ia_t.append(t)
            ia_ctx[nom] = (preds, d)
        T = pd.concat(ia_t, ignore_index=True)
        seuil_ia = NormalDist().inv_cdf(1 - 0.05 / len(T))
        ia_ret = T[T["t_oos"] >= seuil_ia]
        T.sort_values("t_oos", ascending=False).to_csv(RESULTATS / "logistique.csv", index=False, float_format="%.4f")
    else:
        T, ia_ret, seuil_ia = pd.DataFrame(), pd.DataFrame(), float("nan")
    L = ["Radar, protocole 2 (radar/README.md, fixe le 30 octobre 2026)", "",
         f"Survivantes de la confirmation (tous marches) : {len(surv)}",
         f"Regressions logistiques : {len(T)} modeles, barre t >= {seuil_ia:.2f} hors echantillon avant 2023, retenus "
         f"{len(ia_ret)}", ""]
    for _, r in surv.iterrows():
        L.append(f"  t_E {r['t_E']:5.2f}  t_C {r['t_C']:5.2f}  n_C {int(r['n_C']):4d}  moy_C {r['moy_C']:+8.2f} $  "
                 f"{r['regle']}")
    if len(T):
        L += ["", "Meilleures regressions hors echantillon :"]
        for _, r in T.sort_values("t_oos", ascending=False).head(10).iterrows():
            L.append(f"  {r['cible']:<4} e {int(r['e']):3d} H {int(r['H']):3d}  n {int(r['n_oos']):4d}  "
                     f"moy {r['moy_oos']:+8.2f} $  t {r['t_oos']:5.2f}")
    surv.to_csv(RESULTATS / "survivantes.csv", index=False, float_format="%.4f")
    if a.coffre:
        m = len(surv) + len(ia_ret) + OUVERTURES_DEJA
        seuil = NormalDist().inv_cdf(1 - 0.05 / m)
        L += ["", f"COFFRE 2023 - 2026 (ouvert une fois) : seuil t >= {seuil:.2f} (Bonferroni pour {m}, dont "
                  f"{OUVERTURES_DEJA} du protocole 1), 3 annees gagnantes sur 4", ""]
        res = []
        for _, r in surv.iterrows():
            d, pre = ctx[r["cible"]]
            P = periodes(r["cible"], d["jours"])
            x = rejouer(d, pre, r, P["T"], float(d["frais"]))
            res.append((r["regle"], x, d))
        for _, r in ia_ret.iterrows():
            preds, d = ia_ctx[r["cible"]]
            x = np.where(np.asarray(d["jours"].year) >= 2023, preds[int(r["ih"])], np.nan)
            res.append((f"{r['cible']} : regression logistique e {int(r['e'])} H {int(r['H'])}", x, d))
        lignes = []
        for regle, x, d in res:
            n_, m_, t_ = SC.t_serie(x)
            ans = pd.Series(x, index=d["jours"]).dropna().groupby(lambda j: j.year).sum()
            passe = bool(m_ > 0 and t_ >= seuil and (ans > 0).sum() >= 3)
            lignes.append(dict(regle=regle, n=n_, moy=m_, t=t_, passe=passe))
            L.append(f"  {'PASSE' if passe else 'echoue'}  n {n_}  moy {m_:+.2f} $  t {t_:.2f}  annees " +
                     ", ".join(f"{y} {v:+.0f}" for y, v in ans.items()) + f"  | {regle}")
        pd.DataFrame(lignes).to_csv(RESULTATS / "coffre.csv", index=False, float_format="%.4f")
    (RESULTATS / ("resume_coffre.txt" if a.coffre else "resume.txt")).write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    sys.exit(main())
