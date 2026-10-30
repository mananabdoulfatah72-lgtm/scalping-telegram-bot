#!/usr/bin/env python3
"""Partie 16 (flux/README.md) : grille order flow d'environ 200 000 reglages, fixee le 30 octobre 2026 avant la seance
de FluxNQ et avant tout calcul. Signaux G1 a G6 a chaque seconde, sorties stop / objectif / duree en multiples de A,
3 fenetres d'entree. Historique (tape et premier niveau) : exploration, confirmation et 10 placebos. Seances de FluxNQ :
regles figees jouees a l'aveugle, et classement des reglages du DOM avec 10 placebos sur la meme seance.

Lancer : python3 flux/of_grille.py historique <dossier nq_secondes_*, nq_gros_*>
         python3 flux/of_grille.py fluxnq <dossier d'une seance de FluxNQ>"""
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

import of_fige as OF

ICI = Path(__file__).resolve().parent
RESULTATS = ICI / "resultats" / "partie16"
N, TICK, PT, COMMISSION, MAX_JOUR, FIN = OF.N, 0.25, 2.0, 2.0, 4, 23100
STOPS = np.array([0.5, 1, 1.5, 2, 3, 4])
CIBLES = np.array([0.5, 1, 1.5, 2, 3, 4])
DUREES = np.array([120, 300, 900, 1800, 3600])
FENETRES = {"10 h - 15 h 30": (1800, 21600), "10 h - 12 h": (1800, 9000), "13 h - 15 h 30": (12600, 21600)}
FIN_EXPLO, FIN_CONF = "2026-07-15", "2026-10-01"
MIN_E, MIN_C, T_E, GARDER, N_PLACEBOS, PLANCHER = 60, 30, 3.0, 5000, 10, 3.0
GROS = 20
SORTIES = list(itertools.product(range(len(STOPS)), range(len(CIBLES)), range(len(DUREES))))
COMBOS = [(f, s) for f in range(len(FENETRES)) for s in range(len(SORTIES))]


# ------------------------------------------------------------------ signaux
def roulant(x, w):
    c = np.cumsum(np.r_[0.0, x])
    out = np.zeros(len(x))
    out[w - 1:] = c[w:] - c[:-w]
    out[:w - 1] = c[1:w]
    return out


@njit(cache=True)
def persiste(cond, p):
    """Vrai quand cond est vraie depuis au moins p secondes de suite."""
    out = np.zeros(len(cond), np.bool_)
    k = 0
    for i in range(len(cond)):
        k = k + 1 if cond[i] else 0
        out[i] = k >= p
    return out


def definitions(dom):
    """Liste des signaux : (nom, famille, reglages). dom : inclure ceux qui demandent plusieurs niveaux."""
    out = []
    for w, th, m, sens in itertools.product((5, 10, 30, 60, 120), (0.5, 0.6, 0.7, 0.8), (1, 2, 4), (1, -1)):
        out.append((f"G1 delta {w} s, ≥ {th}, volume ≥ {m}x, {'suivre' if sens > 0 else 'contrer'}", "G1", (w, th, m, sens)))
    niveaux = (1, 3, 5, 10) if dom else (1,)
    for k, th, p, sens in itertools.product(niveaux, (0.2, 0.3, 0.4, 0.5, 0.6), (5, 15, 30, 60), (1, -1)):
        out.append((f"G2 carnet {k} niveau(x), ≥ {th} pendant {p} s, {'suivre' if sens > 0 else 'contrer'}", "G2", (k, th, p, sens)))
    for w, a, quoi in itertools.product((30, 60, 300), (0.5, 1.0), ("delta", "prix")):
        out.append((f"G3 divergence {w} s, mouvement ≥ {a} A, suivre le {quoi}", "G3", (w, a, quoi)))
    for r, part, m, sens in itertools.product((1, 2, 3), (0.7, 0.8, 0.9), (3, 5, 10), (1, -1)):
        out.append((f"G4 balayage ≥ {r} pt, {int(part * 100)} % d'un côté, volume ≥ {m}x, {'suivre' if sens > 0 else 'contrer'}",
                    "G4", (r, part, m, sens)))
    if dom:
        for pct, w, sens in itertools.product((0.3, 0.4, 0.5), (3, 5, 10), (1, -1)):
            out.append((f"G5 retrait −{int(pct * 100)} % en {w} s, {'côté qui tient' if sens > 0 else 'inverse'}", "G5", (pct, w, sens)))
    for w, q, sens in itertools.product((30, 60, 300), (50, 100, 200), (1, -1)):
        out.append((f"G6 gros lots {w} s, ≥ {q} contrats, {'suivre' if sens > 0 else 'contrer'}", "G6", (w, q, sens)))
    return [o for o in out if dom or not (o[1] == "G2" and o[2][0] > 1) and o[1] != "G5"]


def signal(x, A, fam, p):
    c, h, l, buy, sell = x["c"], x["h"], x["l"], x["buy"], x["sell"]
    vol = buy + sell
    moy = np.r_[0.0, np.cumsum(vol)[:-1]] / np.maximum(np.arange(N), 1)
    z = np.zeros(N, np.int64)
    if fam == "G1":
        w, th, m, sens = p
        D, V = roulant(buy - sell, w), roulant(vol, w)
        ok = (np.abs(D) >= th * np.maximum(V, 1e-9)) & (V >= m * moy * w) & (V > 0)
        return np.where(ok, sens * np.sign(D), 0).astype(np.int64)
    if fam == "G2":
        k, th, per, sens = p
        if k == 1:
            b, a = x["bq"], x["aq"]
        else:
            b, a = x[f"sb{k}"], x[f"sa{k}"]
        if not (np.isfinite(b).any() and np.isfinite(a).any()):
            return z
        with np.errstate(invalid="ignore", divide="ignore"):
            imb = (b - a) / (b + a)
        haut, bas = persiste(np.nan_to_num(imb) >= th, per), persiste(np.nan_to_num(imb) <= -th, per)
        return (sens * (haut.astype(np.int64) - bas.astype(np.int64))).astype(np.int64)
    if fam == "G3":
        w, a, quoi = p
        mv = np.r_[np.zeros(w), c[w:] - c[:-w]]
        D = roulant(buy - sell, w)
        ok = (np.abs(mv) >= a * A) & (np.sign(D) * np.sign(mv) < 0)
        return np.where(ok, np.sign(D) if quoi == "delta" else np.sign(mv), 0).astype(np.int64)
    if fam == "G4":
        r, part, m, sens = p
        ok = (h - l >= r) & (np.maximum(buy, sell) >= part * np.maximum(vol, 1e-9)) & (vol >= np.maximum(m * moy, 10))
        return np.where(ok, sens * np.sign(buy - sell), 0).astype(np.int64)
    if fam == "G5":
        pct, w, sens = p
        b, a = x.get("sb5"), x.get("sa5")
        if b is None:
            return z
        rb = np.r_[np.full(w + 60, np.nan), (roulant(b, 60) / 60)[59:-(w + 1)]][:N]
        ra = np.r_[np.full(w + 60, np.nan), (roulant(a, 60) / 60)[59:-(w + 1)]][:N]
        with np.errstate(invalid="ignore"):
            achat = (a <= (1 - pct) * ra) & (b >= 0.9 * rb)
            vente = (b <= (1 - pct) * rb) & (a >= 0.9 * ra)
        return (sens * (achat.astype(np.int64) - vente.astype(np.int64))).astype(np.int64)
    if fam == "G6":
        w, q, sens = p
        S = roulant(x["gros"], w)
        return np.where(np.abs(S) >= q, sens * np.sign(S), 0).astype(np.int64)
    raise ValueError(fam)


# ------------------------------------------------------------------ simulation de tous les reglages d'un signal
@njit(cache=True)
def tous_reglages(c, h, l, A, es, ed, stops, cibles, durees, fdeb, ffin, n_out, s_out, q_out):
    nS, nC, nD = len(stops), len(cibles), len(durees)
    k = 0
    for iw in range(len(fdeb)):
        for i1 in range(nS):
            for i2 in range(nC):
                for i3 in range(nD):
                    pos = np.searchsorted(es, fdeb[iw])
                    nt = 0
                    while pos < len(es) and es[pos] <= ffin[iw] and nt < 4:
                        s = es[pos]
                        d = ed[pos]
                        e = c[s] + d * 0.25
                        sd, od = stops[i1] * A[s], cibles[i2] * A[s]
                        if d > 0:
                            st = np.floor((e - sd) / 0.25) * 0.25
                            ob = np.ceil((e + od) / 0.25) * 0.25
                        else:
                            st = np.ceil((e + sd) / 0.25) * 0.25
                            ob = np.floor((e - od) / 0.25) * 0.25
                        der = min(s + durees[i3], 23100)
                        sortie, x = c[der] - d * 0.25, der
                        for t in range(s + 1, der + 1):
                            if d > 0:
                                if l[t] <= st:
                                    sortie, x = st - 0.25, t
                                    break
                                if h[t] >= ob + 0.25:
                                    sortie, x = ob, t
                                    break
                            else:
                                if h[t] >= st:
                                    sortie, x = st + 0.25, t
                                    break
                                if l[t] <= ob - 0.25:
                                    sortie, x = ob, t
                                    break
                        g = d * (sortie - e) * 2.0 - 2.0
                        n_out[k] += 1
                        s_out[k] += g
                        q_out[k] += g * g
                        nt += 1
                        pos = np.searchsorted(es, x + 1)
                    k += 1


FDEB = np.array([v[0] for v in FENETRES.values()])
FFIN = np.array([v[1] for v in FENETRES.values()])


def entrees(sig):
    es = np.nonzero(sig)[0]
    es = es[(es >= FDEB.min()) & (es <= FFIN.max())]
    return es.astype(np.int64), sig[es].astype(np.int64)


def preparer(x):
    A = OF.echelle_A(x["h"], x["l"])
    return A


# ------------------------------------------------------------------ historique
def charger_historique(dossier):
    d = Path(dossier)
    sec = OF.secondes_databento(sorted(d.glob("nq_secondes_*.csv.gz")))
    gr = pd.concat([pd.read_csv(f) for f in sorted(d.glob("nq_gros_*.csv.gz"))], ignore_index=True)
    t = pd.to_datetime(gr["t"])
    gr["jour"] = t.dt.strftime("%Y-%m-%d")
    gr["s"] = (t.dt.hour * 3600 + t.dt.minute * 60 + t.dt.second).values - 34200
    gr = gr[(gr["taille"] >= GROS) & (gr["s"] >= 0) & (gr["s"] < N)]
    for j, g in gr.groupby("jour"):
        if j in sec:
            a = np.zeros(N)
            np.add.at(a, g["s"].values, (g["sens"] * g["taille"]).values)
            sec[j]["gros"] = a
    for j in sec:
        sec[j].setdefault("gros", np.zeros(N))
    return sec


def accumuler(jours, sec, defs, decalage=0):
    """Sommes par (signal, reglage) sur l'exploration et la confirmation ; decalage : signaux pris k seances plus tot."""
    S, K = len(defs), len(COMBOS)
    acc = {p: [np.zeros((S, K)) for _ in range(3)] for p in ("E", "C")}
    A = {j: preparer(sec[j]) for j in jours}
    for i, j in enumerate(jours):
        per = "E" if j <= FIN_EXPLO else "C"
        src = jours[(i - decalage) % len(jours)]
        x, xs = sec[j], sec[src]
        n, s_, q = acc[per]
        for k, (_, fam, p) in enumerate(defs):
            es, ed = entrees(signal(xs, A[src], fam, p))
            if not len(es):
                continue
            tous_reglages(x["c"], x["h"], x["l"], A[j], es, ed, STOPS, CIBLES, DUREES, FDEB, FFIN, n[k], s_[k], q[k])
    return acc


def stat(n, s, q):
    with np.errstate(invalid="ignore", divide="ignore"):
        m = s / n
        sd = np.sqrt((q - s * s / n) / (n - 1))
        return m, m / sd * np.sqrt(n)


def selection(acc, defs):
    nE, sE, qE = acc["E"]
    nC, sC, qC = acc["C"]
    mE, tE = stat(nE, sE, qE)
    mC, tC = stat(nC, sC, qC)
    tE = np.where((nE >= MIN_E) & np.isfinite(tE), tE, -np.inf)
    rows = []
    nS = len(SORTIES)
    for k in range(len(defs)):
        for iw in range(len(FENETRES)):
            blk = slice(iw * nS, (iw + 1) * nS)
            j = int(np.argmax(tE[k, blk]))
            if tE[k, blk][j] >= T_E:
                c = iw * nS + j
                rows.append((k, iw, j, float(tE[k, c]), float(mE[k, c]), int(nE[k, c]), float(tC[k, c]),
                             float(mC[k, c]), int(nC[k, c])))
    t = pd.DataFrame(rows, columns=["sig", "fen", "sortie", "t_E", "moy_E", "n_E", "t_C", "moy_C", "n_C"])
    return t.sort_values("t_E", ascending=False).head(GARDER).reset_index(drop=True)


def libelle(defs, r):
    i1, i2, i3 = SORTIES[int(r["sortie"])]
    return (f"{defs[int(r['sig'])][0]} ; {list(FENETRES)[int(r['fen'])]} ; stop {STOPS[i1]} A, objectif {CIBLES[i2]} A, "
            f"{DUREES[i3] // 60} min au plus")


def historique(dossier):
    RESULTATS.mkdir(parents=True, exist_ok=True)
    sec = charger_historique(dossier)
    jours = sorted(sec)
    defs = definitions(dom=False)
    t0 = time.time()
    acc = accumuler(jours, sec, defs)
    sel = selection(acc, defs)
    print(f"reel : {len(defs)} signaux x {len(COMBOS)} reglages, {len(sel)} familles a t_E >= 3, "
          f"{time.time() - t0:.0f} s", flush=True)
    rng = np.random.default_rng(20261030)
    decal = rng.choice(np.arange(10, len(jours) - 10), size=N_PLACEBOS, replace=False)
    fpl = RESULTATS / "placebos.json"
    pls = json.loads(fpl.read_text()) if fpl.exists() else []
    while len(pls) < N_PLACEBOS:
        k = int(decal[len(pls)])
        s = selection(accumuler(jours, sec, defs, k), defs)
        jug = s[(s["n_C"] >= MIN_C) & (s["moy_C"] > 0)]
        pls.append({"decalage": k, "familles": int(len(s)), "t_C_max": float(jug["t_C"].max()) if len(jug) else 0.0})
        fpl.write_text(json.dumps(pls, indent=1) + "\n")
        print(f"placebo {len(pls)} : {pls[-1]}", flush=True)
    maxs = np.array([p["t_C_max"] for p in pls])
    barre = max(PLANCHER, float(np.quantile(maxs, 0.95)))
    sel["regle"] = [libelle(defs, r) for _, r in sel.iterrows()]
    surv = sel[(sel["n_C"] >= MIN_C) & (sel["moy_C"] > 0) & (sel["t_C"] >= barre)].sort_values("t_C", ascending=False)
    if len(surv):
        fig, quoi = surv, "survivantes"
    else:
        fig = sel[(sel["n_C"] >= MIN_C) & (sel["moy_C"] > 0) & (sel["t_C"] >= 2)].sort_values("t_C", ascending=False).head(5)
        quoi = "5 meilleures de confirmation a t >= 2 (aucune survivante)" if len(fig) else "aucune (rien a t >= 2)"
    regles = []
    for _, r in fig.iterrows():
        nom, fam, p = defs[int(r["sig"])]
        regles.append({"regle": r["regle"], "famille": fam, "reglages": list(p), "fenetre": int(r["fen"]),
                       "sortie": list(SORTIES[int(r["sortie"])]), "t_E": r["t_E"], "t_C": r["t_C"], "n_C": int(r["n_C"])})
    (RESULTATS / "regles_figees.json").write_text(json.dumps({"quoi": quoi, "regles": regles}, indent=1,
                                                             ensure_ascii=False, default=float) + "\n")
    nb = len(defs) * len(COMBOS)
    L = [f"# Partie 16 : grille order flow sur {len(jours)} séances ({jours[0]} - {jours[-1]})", "",
         f"{len(defs)} signaux du tape et du premier niveau × {len(SORTIES)} sorties × {len(FENETRES)} fenêtres = "
         f"{nb:,} réglages (les {len(definitions(True)) - len(defs)} signaux du DOM attendent les séances de FluxNQ).",
         f"Étape 1 : {len(sel)} familles à t ≥ {T_E} en exploration.",
         "Placebos : meilleur t de confirmation " + ", ".join(f"{x:.2f}" for x in sorted(maxs)) + f" ; barre {barre:.2f}.",
         f"Survivantes : {len(surv)}. Figées pour les séances de FluxNQ : {quoi}.", "",
         "Les 15 meilleures familles en confirmation :", ""]
    for _, r in sel.sort_values("t_C", ascending=False).head(15).iterrows():
        L.append(f"- t_E {r['t_E']:.2f}, t_C {r['t_C']:.2f}, {int(r['n_C'])} trades, {r['moy_C']:+.1f} $ : {r['regle']}")
    (RESULTATS / "historique.md").write_text("\n".join(L) + "\n")
    sel.to_csv(RESULTATS / "familles.csv.gz", index=False, float_format="%.4f")
    print("\n".join(L))


# ------------------------------------------------------------------ seance de FluxNQ
def seance_fluxnq(dossier):
    j, paq = OF.secondes_fluxnq(dossier)
    x, niv = paq
    tape = OF.lire(dossier, "tape.csv")
    tu = pd.to_datetime(tape["t_utc"]).dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    s = (tu.dt.hour * 3600 + tu.dt.minute * 60 + tu.dt.second).values - 34200
    g = (s >= 0) & (s < N) & (tape["taille"].values >= GROS)
    x["gros"] = np.zeros(N)
    np.add.at(x["gros"], s[g], (tape["cote"].values * tape["taille"].values)[g])
    if niv is not None:
        for k in (3, 5, 10):
            x[f"sb{k}"] = np.nansum(niv["qa"][:, :k], 1)
            x[f"sa{k}"] = np.nansum(niv["qv"][:, :k], 1)
    return j, x


def fluxnq(dossier):
    RESULTATS.mkdir(parents=True, exist_ok=True)
    j, x = seance_fluxnq(dossier)
    A = preparer(x)
    L = [f"# Partie 16 : séance du {j} enregistrée par FluxNQ", ""]
    fig = json.loads((RESULTATS / "regles_figees.json").read_text())
    L += [f"## Règles figées avant la séance ({fig['quoi']})", ""]
    for r in fig["regles"]:
        sig = signal(x, A, r["famille"], tuple(r["reglages"]))
        es, ed = entrees(sig)
        i1, i2, i3 = r["sortie"]
        iw = r["fenetre"]
        n, s_, q = np.zeros(1), np.zeros(1), np.zeros(1)
        tous_reglages(x["c"], x["h"], x["l"], A, es, ed, STOPS[[i1]], CIBLES[[i2]], DUREES[[i3]], FDEB[[iw]], FFIN[[iw]],
                      n, s_, q)
        L.append(f"- {r['regle']} : {int(n[0])} trade(s), {s_[0]:+.1f} $")
    defs = [d for d in definitions(dom=True) if d[1] in ("G2", "G5") and (d[1] == "G5" or d[2][0] > 1)]

    def classement(sigs_de):
        n = np.zeros((len(defs), len(COMBOS)))
        s_, q = np.zeros_like(n), np.zeros_like(n)
        for k, (_, fam, p) in enumerate(defs):
            es, ed = entrees(sigs_de(fam, p))
            if len(es):
                tous_reglages(x["c"], x["h"], x["l"], A, es, ed, STOPS, CIBLES, DUREES, FDEB, FFIN, n[k], s_[k], q[k])
        return n, s_
    n, s_ = classement(lambda fam, p: signal(x, A, fam, p))
    rng = np.random.default_rng(20261030)
    meilleurs = []
    for k in range(N_PLACEBOS):
        dec = int(rng.integers(1800, N - 1800))
        _, sp = classement(lambda fam, p: np.roll(signal(x, A, fam, p), dec))
        meilleurs.append(float(sp.max()))
    L += ["", f"## Réglages du DOM ({len(defs) * len(COMBOS):,}) : classement de cette seance (pas un résultat)", "",
          "Meilleur gain d'un réglage avec les signaux décalés au hasard dans la séance (10 placebos) : "
          + ", ".join(f"{v:+.0f} $" for v in sorted(meilleurs)), ""]
    ordre = np.argsort(s_, axis=None)[::-1][:10]
    for idx in ordre:
        k, c = np.unravel_index(idx, s_.shape)
        iw, isort = COMBOS[c]
        i1, i2, i3 = SORTIES[isort]
        L.append(f"- {s_[k, c]:+.0f} $ ({int(n[k, c])} trades) : {defs[k][0]} ; {list(FENETRES)[iw]} ; stop {STOPS[i1]} A, "
                 f"objectif {CIBLES[i2]} A, {DUREES[i3] // 60} min")
    (RESULTATS / f"fluxnq_{j}.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    (historique if sys.argv[1] == "historique" else fluxnq)(sys.argv[2])
