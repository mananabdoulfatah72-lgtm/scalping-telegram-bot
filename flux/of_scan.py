#!/usr/bin/env python3
"""Partie 10 (flux/README.md) : scan order flow facon radar, fixe le 30 octobre 2026 avant tout calcul. Regles a une ou
deux conditions sur des variables d'order flow (delta, intensite, carnet, gros lots, footprint, prix), decisions toutes
les 15 minutes regroupees en 3 fenetres, exploration avril - mi-juillet 2026, confirmation mi-juillet - octobre 2026
avec 20 placebos, puis suivi sur les seances de FluxNQ (l'avenir).

Lancer : python3 flux/of_scan.py scan <dossier des fichiers nq_secondes_*, nq_footprint_*, nq_gros_*>
         [ROBOT=<zone/robot/nq_1min.csv.gz>] python3 flux/of_scan.py fluxnq [<dossiers d'avant>] <dossier a juger>"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import of_fige as OF

ICI = Path(__file__).resolve().parent
RESULTATS = ICI / "resultats" / "partie10"
ENTREES = np.arange(15, 361, 15)
FENETRES = {"matin": range(15, 121, 15), "mi-journee": range(135, 241, 15), "apres-midi": range(255, 361, 15)}
DUREES = [15, 30, 60]
FRAIS, PT, GROS = 3.0, 2.0, 20
FIN_EXPLO, FIN_CONF = "2026-07-15", "2026-10-01"
MIN_E, MIN_C, T_E, GARDER, N_PLACEBOS, PLANCHER = 60, 30, 3.0, 2000, 20, 3.0
QUANTILES = (0.1, 0.2, 0.4, 0.6, 0.8, 0.9)
TRANCHES = ["10 % bas", "Q1", "Q2", "Q3", "Q4", "Q5", "10 % haut"]
GRAINE = 20261030


# ------------------------------------------------------------------ minutes d'une seance
def minutes(x, fp, gros):
    """x : secondes (of_fige) ; fp : DataFrame (minute, prix, achat, vente) ; gros : DataFrame (minute, sens, taille)."""
    c = x["c"].reshape(390, 60)
    O = np.r_[x["c"][0], x["c"][59::60][:-1]]
    H, L, C = x["h"].reshape(390, 60).max(1), x["l"].reshape(390, 60).min(1), c[:, -1]
    buy, sell, n = (x[k].reshape(390, 60).sum(1) for k in ("buy", "sell", "n"))
    with np.errstate(invalid="ignore", divide="ignore"):
        ob = ((x["bq"] - x["aq"]) / (x["bq"] + x["aq"])).reshape(390, 60)
    ob = np.nanmean(np.where(np.isfinite(ob), ob, np.nan), 1) if np.isfinite(ob).any() else np.full(390, np.nan)
    pile_a, pile_v = np.zeros(390), np.zeros(390)
    profil = {}
    poc = np.full(390, np.nan)
    if fp is not None and len(fp):
        fpm = {m: g for m, g in fp.groupby("minute")}
        for m in range(390):
            g = fpm.get(m)
            if g is not None:
                g = g.sort_values("prix")
                ra = (g["achat"].values >= 3 * g["vente"].values) & (g["achat"].values > 0)
                rv = (g["vente"].values >= 3 * g["achat"].values) & (g["vente"].values > 0)
                pile_a[m] = float(np.convolve(ra, np.ones(3), "valid").max(initial=0) >= 3)
                pile_v[m] = float(np.convolve(rv, np.ones(3), "valid").max(initial=0) >= 3)
                for p, v in zip(g["prix"].values, g["achat"].values + g["vente"].values):
                    profil[p] = profil.get(p, 0.0) + v
            if profil:
                poc[m] = max(profil, key=profil.get)            # POC a la fin de la minute m
    gs, gn = np.zeros(390), np.zeros(390)
    if gros is not None and len(gros):
        g = gros[gros["taille"] >= GROS]
        np.add.at(gs, g["minute"].values, (g["sens"] * g["taille"]).values)
        np.add.at(gn, g["minute"].values, 1.0)
    return dict(O=O, H=H, L=L, C=C, buy=buy, sell=sell, n=n, ob=ob, pile_a=pile_a, pile_v=pile_v, poc=poc, gs=gs, gn=gn)


def variables(m, prevC):
    """Variables a chaque minute de decision (donnees jusqu'a la minute e - 1)."""
    O, H, L, C = m["O"], m["H"], m["L"], m["C"]
    vol = m["buy"] + m["sell"]
    dl = m["buy"] - m["sell"]
    cv, cd, cn = np.cumsum(vol), np.cumsum(dl), np.cumsum(m["n"])
    tp = (H + L + C) / 3
    vw = np.cumsum(tp * vol) / np.where(cv > 0, cv, np.nan)
    rng = np.cumsum(H - L) / np.arange(1, 391)
    cmax, cmin = np.maximum.accumulate(H), np.minimum.accumulate(L)
    cgn = np.cumsum(m["gn"])
    out = {}
    for e in ENTREES:
        j = e - 1
        a = max(rng[j], 1.0)
        f = {}
        f["ouv"] = (C[j] - O[0]) / a
        for k in (5, 15, 30, 60):
            f[f"r{k}"] = (C[j] - C[j - k]) / a if j - k >= 0 else np.nan
        f["place"] = (C[j] - cmin[j]) / (cmax[j] - cmin[j]) if cmax[j] > cmin[j] else np.nan
        f["amp"] = (cmax[j] - cmin[j]) / a
        f["vwap"] = (C[j] - vw[j]) / a
        f["poc"] = (C[j] - m["poc"][j]) / a
        f["ecart"] = (O[0] - prevC) / a if np.isfinite(prevC) else np.nan

        def dsum(k):
            lo = max(0, j - k + 1)
            v = vol[lo:j + 1].sum()
            return dl[lo:j + 1].sum() / v if v > 0 else np.nan
        for k in (5, 15, 30, 60):
            f[f"d{k}"] = dsum(k)
        f["dcum"] = cd[j] / cv[j] if cv[j] > 0 else np.nan
        f["absorption"] = f["r15"] * np.sign(f["d15"]) / (abs(f["d15"]) + 0.05) if np.isfinite(f["d15"]) else np.nan
        f["intens_n"] = m["n"][j - 4:j + 1].sum() / (cn[j] / (j + 1) * 5) if cn[j] > 0 else np.nan
        f["intens_v"] = vol[j - 4:j + 1].sum() / (cv[j] / (j + 1) * 5) if cv[j] > 0 else np.nan
        f["carnet5"] = np.nanmean(m["ob"][j - 4:j + 1]) if np.isfinite(m["ob"][j - 4:j + 1]).any() else np.nan
        f["carnet15"] = np.nanmean(m["ob"][max(0, j - 14):j + 1]) if np.isfinite(m["ob"][max(0, j - 14):j + 1]).any() else np.nan
        v15 = vol[max(0, j - 14):j + 1].sum()
        f["gros15"] = m["gs"][max(0, j - 14):j + 1].sum() / v15 if v15 > 0 else np.nan
        f["gros30"] = m["gn"][max(0, j - 29):j + 1].sum() / (cgn[j] / (j + 1) * 30) if cgn[j] > 0 else np.nan
        f["pile15"] = m["pile_a"][max(0, j - 14):j + 1].sum() - m["pile_v"][max(0, j - 14):j + 1].sum()
        out[int(e)] = f
    return out


def gains(m):
    O = m["O"]
    return {(int(e), H): (O[min(e + H, 389)] - O[e]) * PT for e in ENTREES for H in DUREES}


# ------------------------------------------------------------------ historique de Databento
def charger_historique(dossier):
    d = Path(dossier)
    sec = OF.secondes_databento(sorted(d.glob("nq_secondes_*.csv.gz")))
    fp = pd.concat([pd.read_csv(f) for f in sorted(d.glob("nq_footprint_*.csv.gz"))], ignore_index=True)
    t = pd.to_datetime(fp["m"])
    fp["jour"] = t.dt.strftime("%Y-%m-%d")
    fp["minute"] = (t.dt.hour * 60 + t.dt.minute - 570).values
    gr = pd.concat([pd.read_csv(f) for f in sorted(d.glob("nq_gros_*.csv.gz"))], ignore_index=True)
    tg = pd.to_datetime(gr["t"])
    gr["jour"] = tg.dt.strftime("%Y-%m-%d")
    gr["minute"] = (tg.dt.hour * 60 + tg.dt.minute - 570).values
    gr = gr[(gr["minute"] >= 0) & (gr["minute"] < 390)]
    fp = fp[(fp["minute"] >= 0) & (fp["minute"] < 390)]
    fpj, grj = dict(tuple(fp.groupby("jour"))), dict(tuple(gr.groupby("jour")))
    return [(j, minutes(x, fpj.get(j), grj.get(j))) for j, x in sec.items()]


def cube(seances):
    jours = [j for j, _ in seances]
    prevC = np.r_[np.nan, [m["C"][-1] for _, m in seances[:-1]]]
    V = [variables(m, p) for (_, m), p in zip(seances, prevC)]
    noms = list(V[0][int(ENTREES[0])])
    X = np.stack([np.array([[v[int(e)][k] for k in noms] for v in V], float) for e in ENTREES])
    G = [gains(m) for _, m in seances]
    g = {(int(e), H): np.array([x[(int(e), H)] for x in G]) for e in ENTREES for H in DUREES}
    dow = pd.DatetimeIndex(jours).dayofweek
    B = np.column_stack([dow == k for k in range(5)])
    return dict(jours=pd.DatetimeIndex(jours), X=X, noms=noms, g=g, B=B,
                binaires=["lundi", "mardi", "mercredi", "jeudi", "vendredi"])


# ------------------------------------------------------------------ scan
def seuils(X, E):
    """Seuils des 7 tranches de chaque variable a chaque heure (exploration seulement)."""
    out = np.full((X.shape[0], X.shape[2], len(QUANTILES)), np.nan)
    for ie in range(X.shape[0]):
        for f in range(X.shape[2]):
            x = X[ie, E, f]
            x = x[np.isfinite(x)]
            if len(x) >= 50:
                out[ie, f] = np.quantile(x, QUANTILES)
    return out


def indicatrices(X, B, Q):
    """I[ie] : seances x conditions (7 par variable continue, puis le calendrier), indices identiques a chaque heure."""
    nE, S, F = X.shape
    Kc = F * 7 + B.shape[1]
    I = np.zeros((nE, S, Kc))
    for ie in range(nE):
        for f in range(F):
            q = Q[ie, f]
            if not np.isfinite(q).all():
                continue
            x = X[ie, :, f]
            fin = np.isfinite(x)
            xx = np.where(fin, x, np.nan)
            with np.errstate(invalid="ignore"):
                tr = [xx <= q[0], xx <= q[1], (xx > q[1]) & (xx <= q[2]), (xx > q[2]) & (xx <= q[3]),
                      (xx > q[3]) & (xx <= q[4]), xx > q[4], xx > q[5]]
            for k, cnd in enumerate(tr):
                I[ie, :, f * 7 + k] = cnd & fin
        I[ie, :, F * 7:] = B
    var = np.r_[np.repeat(np.arange(F), 7), F + np.arange(B.shape[1])]
    return I, var


def sommes(I, d, lignes, fen, H):
    K = I.shape[2]
    N, S1, S2 = np.zeros((K, K)), np.zeros((K, K)), np.zeros((K, K))
    for e in fen:
        ie = list(ENTREES).index(e)
        Ip = I[ie][lignes]
        g = d["g"][(e, H)][lignes]
        A = Ip * g[:, None]
        N += Ip.T @ Ip
        S1 += Ip.T @ A
        S2 += Ip.T @ (A * g[:, None])
    return N, S1, S2


def etape1(d, I, var, E):
    K = I.shape[2]
    interdit = (var[:, None] == var[None, :]) & ~np.eye(K, dtype=bool) | np.tril(np.ones((K, K), bool), -1)
    out = []
    for nf, fen in FENETRES.items():
        best = np.full((K, K), -np.inf)
        choix = np.zeros((K, K, 2), np.int64)
        for H in DUREES:
            N, S1, S2 = sommes(I, d, E, fen, H)
            for sens in (1, -1):
                with np.errstate(invalid="ignore", divide="ignore"):
                    moy = sens * S1 / N - FRAIS
                    t = moy / np.sqrt((S2 - S1 * S1 / N) / (N - 1)) * np.sqrt(N)
                t = np.where((N >= MIN_E) & ~interdit & np.isfinite(t), t, -np.inf)
                mieux = t > best
                best = np.where(mieux, t, best)
                choix[mieux] = (H, sens)
        for a, b in zip(*np.nonzero(best >= T_E)):
            out.append((nf, int(var[a]), int(var[b]), int(a), int(b), int(choix[a, b, 0]), int(choix[a, b, 1]),
                        float(best[a, b])))
    t = pd.DataFrame(out, columns=["fenetre", "va", "vb", "ka", "kb", "H", "sens", "t_E"])
    if len(t):
        t = t.loc[t.groupby(["fenetre", "va", "vb"])["t_E"].idxmax()].sort_values("t_E", ascending=False).head(GARDER)
    return t.reset_index(drop=True)


def rejouer(d, I, r, lignes):
    """Gains nets de chaque trade de la regle sur les seances `lignes` : (seance, gain)."""
    out = []
    for e in FENETRES[r["fenetre"]]:
        ie = list(ENTREES).index(e)
        pris = (I[ie][:, int(r["ka"])] > 0) & (I[ie][:, int(r["kb"])] > 0) & lignes
        g = d["g"][(e, int(r["H"]))]
        for s in np.nonzero(pris)[0]:
            out.append((s, r["sens"] * g[s] - FRAIS))
    return out


def t_trades(tr):
    x = np.array([g for _, g in tr])
    if len(x) < 2 or x.std(ddof=1) == 0:
        return len(x), np.nan, np.nan
    return len(x), x.mean(), x.mean() / x.std(ddof=1) * np.sqrt(len(x))


def etape2(d, I, sel, C):
    res = [t_trades(rejouer(d, I, r, C)) for _, r in sel.iterrows()]
    sel = sel.copy()
    sel["n_C"], sel["moy_C"], sel["t_C"] = zip(*res) if res else ([], [], [])
    return sel


def libelle(d, r):
    noms = d["noms"] + d["binaires"]
    F = len(d["noms"])
    parts = []
    for k in sorted({int(r["ka"]), int(r["kb"])}):
        parts.append(noms[k // 7] + " " + TRANCHES[k % 7] if k < F * 7 else noms[F + k - F * 7])
    return (f"{'achat' if r['sens'] > 0 else 'vente'} ({r['fenetre']}, {int(r['H'])} min) si " + " et ".join(parts))


def scan(dossier):
    RESULTATS.mkdir(parents=True, exist_ok=True)
    d = cube(charger_historique(dossier))
    j = d["jours"]
    E, C = np.asarray(j <= FIN_EXPLO), np.asarray((j > FIN_EXPLO) & (j <= FIN_CONF))
    Q = seuils(d["X"], E)
    I, var = indicatrices(d["X"], d["B"], Q)
    sel = etape2(d, I, etape1(d, I, var, E), C)
    S = len(j)
    rng = np.random.default_rng(GRAINE)
    decal = rng.choice(np.arange(15, S - 15), size=N_PLACEBOS, replace=False)
    maxs = []
    for k in decal:
        Xp, Bp = np.roll(d["X"], int(k), axis=1), np.roll(d["B"], int(k), axis=0)
        Ip, vp = indicatrices(Xp, Bp, seuils(Xp, E))
        s = etape2(d, Ip, etape1(d, Ip, vp, E), C)
        jug = s[(s["n_C"] >= MIN_C) & (s["moy_C"] > 0)]
        maxs.append(float(jug["t_C"].max()) if len(jug) else 0.0)
    barre = max(PLANCHER, float(np.quantile(maxs, 0.95)))
    sel["regle"] = [libelle(d, r) for _, r in sel.iterrows()]
    surv = sel[(sel["n_C"] >= MIN_C) & (sel["moy_C"] > 0) & (sel["t_C"] >= barre)].sort_values("t_C", ascending=False)
    garde, series = [], {}
    for i, r in surv.iterrows():
        x = np.zeros(S)
        for s, g in rejouer(d, I, r, E | C):
            x[s] += g
        if any(np.corrcoef(x, series[k])[0, 1] > 0.7 for k in garde):
            continue
        garde.append(i)
        series[i] = x
    surv = surv.loc[garde]
    if len(surv):
        figees, quoi = surv, "survivantes"
    else:
        figees, quoi = sel[(sel["n_C"] >= MIN_C) & (sel["moy_C"] > 0) & (sel["t_C"] >= 2)].sort_values(
            "t_C", ascending=False).head(5), "5 meilleures de confirmation a t >= 2 (aucune survivante)"
    regles = []
    for _, r in figees.iterrows():
        conds = []
        for k in sorted({int(r["ka"]), int(r["kb"])}):
            if k < len(d["noms"]) * 7:
                f, b = k // 7, k % 7
                conds.append({"variable": d["noms"][f], "tranche": b,
                              "seuils": {int(e): [float(v) for v in Q[ie, f]] for ie, e in enumerate(ENTREES)}})
            else:
                conds.append({"variable": d["binaires"][k - len(d["noms"]) * 7], "tranche": -1})
        regles.append({"regle": r["regle"], "fenetre": r["fenetre"], "H": int(r["H"]), "sens": int(r["sens"]),
                       "t_E": float(r["t_E"]), "t_C": float(r["t_C"]), "n_C": int(r["n_C"]), "conditions": conds})
    (RESULTATS / "regles_figees.json").write_text(json.dumps({"quoi": quoi, "regles": regles}, indent=1,
                                                             ensure_ascii=False) + "\n")
    L = [f"# Partie 10 : scan order flow sur {S} séances ({j[0].date()} - {j[-1].date()})", "",
         f"{len(d['noms'])} variables d'order flow et de prix, 5 jours de la semaine, 3 fenêtres, 3 durées, 2 sens.",
         f"Exploration jusqu'au {FIN_EXPLO} ({E.sum()} séances), confirmation ensuite ({C.sum()} séances).", "",
         f"Étape 1 : {len(sel)} familles à t ≥ {T_E}.",
         "Placebos : meilleur t de confirmation " + ", ".join(f"{x:.2f}" for x in sorted(maxs)) + f" ; barre {barre:.2f}.",
         f"Survivantes : {len(surv)}.", f"Figées pour les séances de FluxNQ : {quoi}.", "",
         "Les 15 meilleures familles en confirmation :", ""]
    for _, r in sel.sort_values("t_C", ascending=False).head(15).iterrows():
        L.append(f"- t_E {r['t_E']:.2f}, t_C {r['t_C']:.2f}, {int(r['n_C'])} trades, {r['moy_C']:+.1f} $ : {r['regle']}")
    (RESULTATS / "scan.md").write_text("\n".join(L) + "\n")
    sel.to_csv(RESULTATS / "familles.csv.gz", index=False, float_format="%.4f")
    print("\n".join(L))


# ------------------------------------------------------------------ seances de FluxNQ
def seance_fluxnq(dossier):
    j, paq = OF.secondes_fluxnq(dossier)
    if j is None:
        return None, None
    x, _ = paq
    tape = OF.lire(dossier, "tape.csv")
    tu = pd.to_datetime(tape["t_utc"]).dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    mi = (tu.dt.hour * 60 + tu.dt.minute).values - 570
    tape = tape.assign(minute=mi)
    tape = tape[(tape["minute"] >= 0) & (tape["minute"] < 390)]
    fp = tape.assign(achat=np.where(tape["cote"] > 0, tape["taille"], 0.0),
                     vente=np.where(tape["cote"] < 0, tape["taille"], 0.0)).groupby(["minute", "prix"], as_index=False)[
        ["achat", "vente"]].sum()
    gr = tape[tape["taille"] >= GROS].assign(sens=lambda t: t["cote"])[["minute", "sens", "taille"]]
    return j, minutes(x, fp, gr)


def jouer_fluxnq(dossiers):
    fig = json.loads((RESULTATS / "regles_figees.json").read_text())
    seances = [s for s in (seance_fluxnq(d) for d in dossiers) if s[0] is not None]
    j, m = seances[-1]
    prevC = seances[-2][1]["C"][-1] if len(seances) > 1 else np.nan
    if not np.isfinite(prevC) and os.getenv("ROBOT"):                # cloture de la veille : minutes du robot (main)
        rb = pd.read_csv(os.environ["ROBOT"], dtype={"t": str})
        rb = rb[(rb["t"].str[:10] < j) & (rb["t"].str[11:16] == "15:59")]
        prevC = float(rb["c"].iloc[-1]) if len(rb) else np.nan
    V = variables(m, prevC)
    g = gains(m)
    dow = pd.Timestamp(j).dayofweek
    lignes = []
    for r in fig["regles"]:
        for e in FENETRES[r["fenetre"]]:
            ok = True
            for c in r["conditions"]:
                if c["tranche"] < 0:
                    ok &= ["lundi", "mardi", "mercredi", "jeudi", "vendredi"].index(c["variable"]) == dow
                    continue
                x, q, b = V[e][c["variable"]], c["seuils"][str(e)], c["tranche"]
                bas, haut = [(-np.inf, q[0]), (-np.inf, q[1]), (q[1], q[2]), (q[2], q[3]), (q[3], q[4]), (q[4], np.inf),
                             (q[5], np.inf)][b]                  # meme tranche qu'a l'exploration : bas < x <= haut
                ok &= bool(np.isfinite(x) and bas < x <= haut)
            if ok:
                net = r["sens"] * g[(e, r["H"])] - FRAIS
                lignes.append((r["regle"], e, net))
    L = [f"# Partie 10 : règles figées jouées sur la séance du {j} (FluxNQ)", "", f"Règles : {fig['quoi']}.", ""]
    if not lignes:
        L.append("Aucune règle ne s'est déclenchée.")
    for regle, e, net in lignes:
        h, mn = divmod(570 + e, 60)
        L.append(f"- {h} h {mn:02d} : {regle} : {net:+.1f} $")
    (RESULTATS / f"fluxnq_{j}.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    if sys.argv[1] == "scan":
        scan(sys.argv[2])
    else:
        jouer_fluxnq(sys.argv[2:])
