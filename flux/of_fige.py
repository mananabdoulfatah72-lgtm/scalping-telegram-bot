#!/usr/bin/env python3
"""Partie 9 (flux/README.md) : vague order flow figee le 30 octobre 2026 avant tout calcul. 7 regles sur le tape et le
premier niveau du carnet (T1-T7), jugees sur les 127 seances de la seconde de Databento, et 4 regles sur le DOM a 10
niveaux (D1-D4), jouees sur les seances enregistrees par FluxNQ (tape.csv, dom.csv, eventuellement en .gz).

Lancer : python3 flux/of_fige.py historique <nq_secondes_1.csv.gz> [<...>]
         python3 flux/of_fige.py fluxnq [<dossiers de seances d'avant>] <dossier de la seance a juger>"""
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd
from numba import njit

ICI = Path(__file__).resolve().parent
RESULTATS = ICI / "resultats" / "partie9"
N = 23400                              # secondes de 9 h 30 a 16 h
DEBUT, FIN_ENTREE, FIN = 1800, 21600, 23100      # entrees de 10 h a 15 h 30, sortie au plus tard a 15 h 55
TICK, PT, COMMISSION, MAX_JOUR = 0.25, 2.0, 2.0, 4
PLACE_R1 = 0.8591989517211914
REGLES_TAPE = ["T1", "T2", "T3", "T4", "T5", "T6", "T7"]
REGLES_DOM = ["D1", "D2", "D3", "D4"]
NOMS = {"T1": "balayage", "T2": "epuisement", "T3": "iceberg", "T4": "VPIN", "T5": "rafale", "T6": "absorption",
        "T7": "apres-midi + flux", "D1": "desequilibre du carnet", "D2": "retrait de liquidite", "D3": "rebond sur un mur",
        "D4": "mur casse"}


# ------------------------------------------------------------------ secondes
def completer(t):
    """DataFrame indexe par la seconde (0..N-1) -> tableaux complets (prix prolonges, volumes nuls si pas de transaction)."""
    t = t[(t.index >= 0) & (t.index < N)]
    t = t[~t.index.duplicated(keep="last")].reindex(range(N))
    c = t["c"].ffill().bfill().values
    out = {"c": c, "h": t["h"].fillna(pd.Series(c)).values, "l": t["l"].fillna(pd.Series(c)).values}
    for k in ("buy", "sell", "n"):
        out[k] = t[k].fillna(0.0).values
    for k in ("bid", "ask", "bq", "aq"):
        out[k] = t[k].ffill().bfill().values if k in t else np.full(N, np.nan)
    return out


def secondes_databento(fichiers):
    jours = {}
    for f in fichiers:
        d = pd.read_csv(f)
        t = pd.to_datetime(d["t"])
        d["jour"] = t.dt.strftime("%Y-%m-%d")
        d["s"] = ((t.dt.hour * 3600 + t.dt.minute * 60 + t.dt.second) - 9 * 3600 - 1800).values
        d = d.rename(columns={"prix": "c", "haut": "h", "bas": "l", "achat": "buy", "vente": "sell",
                              "bid_q": "bq", "ask_q": "aq"})
        for j, x in d.groupby("jour"):
            jours[j] = completer(x.set_index("s"))
    return dict(sorted(jours.items()))


def lire(dossier, nom):
    for f in (Path(dossier) / nom, Path(dossier) / (nom + ".gz")):
        if f.exists():
            return pd.read_csv(f)
    return None


def secondes_fluxnq(dossier):
    """Une seance de FluxNQ : secondes du tape et photos du carnet (meilleurs prix et 10 niveaux)."""
    tape = lire(dossier, "tape.csv")
    if tape is None or not len(tape):
        return None, None
    tu = pd.to_datetime(tape["t_utc"]).dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    jour = tu.dt.strftime("%Y-%m-%d").mode().iloc[0]
    s = (tu.dt.hour * 3600 + tu.dt.minute * 60 + tu.dt.second).values - 9 * 3600 - 1800
    tape = tape.assign(s=s, buy=np.where(tape["cote"] > 0, tape["taille"], 0.0),
                       sell=np.where(tape["cote"] < 0, tape["taille"], 0.0))
    g = tape.groupby("s")
    t = pd.DataFrame({"c": g["prix"].last(), "h": g["prix"].max(), "l": g["prix"].min(), "buy": g["buy"].sum(),
                      "sell": g["sell"].sum(), "n": g["prix"].size()})
    dom = lire(dossier, "dom.csv")
    niveaux = None
    if dom is not None and len(dom):
        du = pd.to_datetime(dom["t_utc"]).dt.tz_localize("UTC").dt.tz_convert("America/New_York")
        ds = (du.dt.hour * 3600 + du.dt.minute * 60 + du.dt.second).values - 9 * 3600 - 1800
        dom = dom.assign(s=ds).groupby("s").last()
        t = t.join(dom[["pa1", "qa1", "pv1", "qv1"]].rename(columns={"pa1": "bid", "qa1": "bq", "pv1": "ask",
                                                                       "qv1": "aq"}), how="outer")
        idx = pd.RangeIndex(N)
        niveaux = {k: dom[[f"{k}{i}" for i in range(1, 11)]].reindex(idx).ffill().values
                   for k in ("pa", "qa", "pv", "qv")}
    return jour, (completer(t), niveaux)


# ------------------------------------------------------------------ outils
def echelle_A(h, l):
    """A a chaque seconde : moyenne des ranges des 30 dernieres minutes terminees, plancher 2 points."""
    mh = h.reshape(-1, 60).max(1)
    ml = l.reshape(-1, 60).min(1)
    r = pd.Series(mh - ml).rolling(30, min_periods=30).mean().shift(1).values
    return np.maximum(np.repeat(r, 60), 2.0)


def roulant(x, w):
    c = np.cumsum(np.r_[0.0, x])
    out = np.full(len(x), np.nan)
    out[w - 1:] = c[w:] - c[:-w]
    return out


@njit(cache=True)
def simuler(c, h, l, sens, stop_d, obj_d, duree, debut, fin_entree, fin, tick, pt, commission, max_jour):
    """Trades d'une regle sur une seance : (seconde d'entree, sens, entree, seconde de sortie, sortie, motif, gain $)."""
    out = []
    s = debut
    n = 0
    while s <= fin_entree and n < max_jour:
        d = sens[s]
        if d == 0:
            s += 1
            continue
        e = c[s] + d * tick
        if d > 0:                                       # stop et objectif sur la grille des ticks, du cote prudent
            st = np.floor((e - stop_d[s]) / tick) * tick
            ob = np.ceil((e + obj_d[s]) / tick) * tick
        else:
            st = np.ceil((e + stop_d[s]) / tick) * tick
            ob = np.floor((e - obj_d[s]) / tick) * tick
        dernier = min(s + duree[s], fin)
        sortie, x, motif = 0.0, dernier, 0
        for k in range(s + 1, dernier + 1):
            if d > 0:
                if l[k] <= st:
                    sortie, x, motif = st - tick, k, 1
                    break
                if h[k] >= ob + tick:
                    sortie, x, motif = ob, k, 2
                    break
            else:
                if h[k] >= st:
                    sortie, x, motif = st + tick, k, 1
                    break
                if l[k] <= ob - tick:
                    sortie, x, motif = ob, k, 2
                    break
        if motif == 0:
            sortie = c[dernier] - d * tick
        out.append((s, d, e, x, sortie, motif, d * (sortie - e) * pt - commission))
        n += 1
        s = x + 1
    return out


@njit(cache=True)
def t2_signaux(c, h, l, balayage, sens_bal, A, tick):
    S = len(c)
    sens = np.zeros(S, np.int64)
    stop = np.zeros(S)
    for s0 in range(1, S):
        d = sens_bal[s0]
        if not balayage[s0]:
            continue
        a = max(0, s0 - 3600)
        if d > 0 and h[s0] <= h[a:s0].max():
            continue
        if d < 0 and l[s0] >= l[a:s0].min():
            continue
        avant = c[s0 - 1]
        for s in range(s0 + 1, min(s0 + 31, S)):
            if (d > 0 and c[s] < avant) or (d < 0 and c[s] > avant):
                e = c[s] - d * tick                     # entree contre le balayage
                if d > 0:
                    st = h[s0:s + 1].max() + tick
                    stop[s] = st - e
                else:
                    st = l[s0:s + 1].min() - tick
                    stop[s] = e - st
                sens[s] = -d
                break
    return sens, stop


@njit(cache=True)
def t3_signaux(c, h, l, bid, ask, bq, aq, buy, sell, A, w):
    S = len(c)
    sens = np.zeros(S, np.int64)
    stop = np.zeros(S)
    for s in range(w - 1, S):
        a = s - w + 1
        b0 = bid[a]
        ok_b = True
        vs, mq, lo = 0.0, 0.0, 1e18
        for k in range(a, s + 1):
            if bid[k] != b0:
                ok_b = False
                break
            vs += sell[k]
            mq += bq[k]
            lo = min(lo, l[k])
        if ok_b and lo >= b0 and vs >= 100 and vs >= 4 * mq / w:
            sens[s] = 1
            stop[s] = (c[s] + 0.25) - (b0 - max(1.0, 0.5 * A[s]))
            continue
        a0 = ask[a]
        ok_a = True
        vb, mq, hi = 0.0, 0.0, -1e18
        for k in range(a, s + 1):
            if ask[k] != a0:
                ok_a = False
                break
            vb += buy[k]
            mq += aq[k]
            hi = max(hi, h[k])
        if ok_a and hi <= a0 and vb >= 100 and vb >= 4 * mq / w:
            sens[s] = -1
            stop[s] = (a0 + max(1.0, 0.5 * A[s])) - (c[s] - 0.25)
    return sens, stop


# ------------------------------------------------------------------ regles
def regles_tape(x, etat):
    """Signaux (sens, stop, objectif, duree) des regles T1-T7 sur une seance ; etat : historique du VPIN (T4)."""
    c, h, l, buy, sell, n = x["c"], x["h"], x["l"], x["buy"], x["sell"], x["n"]
    A = echelle_A(h, l)
    vol = buy + sell
    moy_prec = np.r_[0.0, np.cumsum(vol)[:-1]] / np.maximum(np.arange(N), 1)
    sgn = np.sign(buy - sell).astype(np.int64)
    dc = np.r_[0.0, np.diff(c)]
    bal = (h - l >= 2.0) & (np.maximum(buy, sell) >= 0.8 * np.maximum(vol, 1e-9)) & \
          (vol >= np.maximum(50.0, 5 * moy_prec)) & (dc * sgn >= 1.0)
    out = {}
    out["T1"] = (np.where(bal, sgn, 0), 1.5 * A, 3.0 * A, np.full(N, 900))
    s2, st2 = t2_signaux(c, h, l, bal, sgn, A, TICK)
    out["T2"] = (s2, st2, 2.0 * st2, np.full(N, 1800))
    if np.isfinite(x["bid"]).all() and np.isfinite(x["bq"]).all():
        s3, st3 = t3_signaux(c, h, l, x["bid"], x["ask"], x["bq"], x["aq"], buy, sell, A, 30)
        out["T3"] = (s3, st3, 2.0 * st3, np.full(N, 1200))
    # T4 : VPIN (paquets de volume de 1/50 du volume moyen des 5 seances d'avant ; signaux des la 6e seance)
    s4 = np.zeros(N, np.int64)
    prec = etat["volumes"][-5:]
    vb = (np.mean(prec) if prec else vol.sum()) / 50
    anciens = np.concatenate(etat["vpin_jours"][-5:]) if len(etat["vpin_jours"]) >= 5 else np.array([])
    seuil = np.quantile(anciens, 0.9) if len(anciens) else np.inf
    paq = etat["paquets"]
    cb = cs = 0.0
    vp = []
    for s in range(N):
        cb += buy[s]
        cs += sell[s]
        if cb + cs >= vb:
            paq.append((abs(cb - cs) / (cb + cs), cb - cs))
            cb = cs = 0.0
            if len(paq) >= 50:
                v = np.mean([q[0] for q in paq[-50:]])
                vp.append(v)
                if v > seuil:
                    s4[s] = int(np.sign(sum(q[1] for q in paq[-10:])))
    del paq[:-60]
    etat["vpin_jours"].append(np.array(vp))
    etat["volumes"].append(vol.sum())
    out["T4"] = (s4, 2.0 * A, 4.0 * A, np.full(N, 1800))
    n10 = roulant(n, 10)
    moy10 = roulant(n, 600)
    moy10 = np.r_[np.full(10, np.nan), moy10[:-10]] / 60.0
    v10 = roulant(vol, 10)
    d10 = roulant(buy - sell, 10)
    dir5 = np.sign(np.nan_to_num(d10)).astype(np.int64)
    mv10 = np.r_[np.full(10, np.nan), c[10:] - c[:-10]]
    c5 = (n10 >= 4 * moy10) & (moy10 > 0) & (np.abs(d10) >= 0.6 * v10) & (mv10 * dir5 >= 0.5 * A)
    out["T5"] = (np.where(c5, dir5, 0), 1.5 * A, 3.0 * A, np.full(N, 900))
    d300 = roulant(buy - sell, 300)
    ad = np.abs(d300)
    moy_abs = pd.Series(ad).expanding(min_periods=60).mean().shift(1).values
    mv300 = np.r_[np.full(300, np.nan), c[300:] - c[:-300]]
    sg = np.sign(np.nan_to_num(d300))
    c6 = (ad >= 2 * moy_abs) & (mv300 * sg <= 0.25 * A) & (sg != 0)
    out["T6"] = (np.where(c6, -sg, 0).astype(np.int64), 1.5 * A, 3.0 * A, np.full(N, 1800))
    s7 = np.zeros(N, np.int64)
    k = 4 * 3600 - 1
    hi, lo = h[:k + 1].max(), l[:k + 1].min()
    if hi > lo and (c[k] - lo) / (hi - lo) > PLACE_R1 and (buy[:k + 1] - sell[:k + 1]).sum() > 0:
        s7[k] = 1
    out["T7"] = (s7, np.full(N, 1e9), np.full(N, 1e9), np.full(N, 7200))
    return out, A


def regles_dom(x, niv, A):
    c, h, l, buy, sell = x["c"], x["h"], x["l"], x["buy"], x["sell"]
    qa, qv, pa, pv = niv["qa"], niv["qv"], niv["pa"], niv["pv"]
    sb, sa = np.nansum(qa, 1), np.nansum(qv, 1)
    imb = (sb - sa) / np.where(sb + sa > 0, sb + sa, np.nan)
    d30 = roulant(buy - sell, 30)
    out = {}
    s1 = np.zeros(N, np.int64)
    run_h = run_b = 0
    for s in range(N):
        run_h = run_h + 1 if imb[s] >= 0.30 else 0
        run_b = run_b + 1 if imb[s] <= -0.30 else 0
        if run_h >= 30 and d30[s] >= 0:
            s1[s] = 1
        elif run_b >= 30 and d30[s] <= 0:
            s1[s] = -1
    out["D1"] = (s1, 1.5 * A, 3.0 * A, np.full(N, 900))
    ref_a = np.r_[np.full(6, np.nan), (roulant(sa, 60) / 60)[:-6]]      # moyenne des 60 s finissant 5 s plus tot
    ref_b = np.r_[np.full(6, np.nan), (roulant(sb, 60) / 60)[:-6]]
    s2 = np.where((sa <= 0.6 * ref_a) & (sb >= 0.9 * ref_b), 1, np.where((sb <= 0.6 * ref_b) & (sa >= 0.9 * ref_a), -1, 0))
    out["D2"] = (s2.astype(np.int64), 1.0 * A, 2.0 * A, np.full(N, 600))
    s3, st3 = np.zeros(N, np.int64), np.zeros(N)
    s4, st4 = np.zeros(N, np.int64), np.zeros(N)
    age_b, age_a = {}, {}
    for s in range(N):
        tailles = np.r_[qa[s], qv[s]]
        if not np.isfinite(tailles).any():
            continue
        med = np.nanmedian(tailles)
        murs_b = {pa[s, i] for i in range(10) if np.isfinite(qa[s, i]) and qa[s, i] >= 5 * med}
        murs_a = {pv[s, i] for i in range(10) if np.isfinite(qv[s, i]) and qv[s, i] >= 5 * med}
        anc_b, anc_a = age_b, age_a
        age_b = {p: anc_b.get(p, 0) + 1 for p in murs_b}
        age_a = {p: anc_a.get(p, 0) + 1 for p in murs_a}
        e_l = c[s] + TICK
        e_c = c[s] - TICK
        for p, ag in anc_a.items():                     # mur de ventes traverse : achat
            if ag >= 30 and h[s] >= p + TICK and s3[s] == 0 and s4[s] == 0:
                s4[s], st4[s] = 1, e_l - (p - 0.5 * A[s])
        for p, ag in anc_b.items():                     # mur d'achats traverse : vente
            if ag >= 30 and l[s] <= p - TICK and s4[s] == 0:
                s4[s], st4[s] = -1, (p + 0.5 * A[s]) - e_c
        for p, ag in age_b.items():
            if ag >= 30 and np.isfinite(pa[s, 0]) and 0 <= pa[s, 0] - p <= 2 * TICK and s3[s] == 0:
                s3[s], st3[s] = 1, e_l - (p - 2 * TICK)
        for p, ag in age_a.items():
            if ag >= 30 and np.isfinite(pv[s, 0]) and 0 <= p - pv[s, 0] <= 2 * TICK and s3[s] == 0:
                s3[s], st3[s] = -1, (p + 2 * TICK) - e_c
    out["D3"] = (s3, st3, 2.0 * st3, np.full(N, 600))
    out["D4"] = (s4, st4, 2.0 * st4, np.full(N, 900))
    return out


def jouer(x, regles):
    lignes = []
    for nom, (sens, st, ob, du) in regles.items():
        sens = np.asarray(sens, np.int64)
        st = np.where(np.isfinite(st) & (st > 0), st, 0.0)
        sens = np.where(st > 0, sens, 0)
        for tr in simuler(x["c"], x["h"], x["l"], sens, st.astype(float), np.asarray(ob, float),
                          np.asarray(du, np.int64), DEBUT if nom != "T7" else 0, FIN_ENTREE, FIN, TICK, PT, COMMISSION,
                          MAX_JOUR):
            lignes.append((nom,) + tuple(tr))
    return lignes


def heure(s):
    s = int(s) + 9 * 3600 + 1800
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def tableau(t, regles, barre=None):
    L = ["| Règle | Trades | Gagnants | Total | Moyenne | t | Verdict |", "|---|---|---|---|---|---|---|"]
    for r in regles:
        x = t.loc[t["regle"] == r, "gain"].values
        n = len(x)
        m = x.mean() if n else 0.0
        tt = m / x.std(ddof=1) * np.sqrt(n) if n > 1 and x.std(ddof=1) > 0 else 0.0
        v = "" if barre is None else ("PASSE" if n >= 30 and tt >= barre else "échoue")
        L.append(f"| {r} {NOMS[r]} | {n} | {(x > 0).sum()} | {x.sum():+,.0f} $ | {m:+,.1f} $ | {tt:+.2f} | {v} |")
    return L


def main():
    RESULTATS.mkdir(parents=True, exist_ok=True)
    mode = sys.argv[1]
    if mode == "historique":
        jours = secondes_databento(sys.argv[2:])
        etat = {"volumes": [], "vpin_jours": [], "paquets": []}
        lignes = []
        for j, x in jours.items():
            regles, _ = regles_tape(x, etat)
            lignes += [(j,) + tr for tr in jouer(x, regles)]
        t = pd.DataFrame(lignes, columns=["jour", "regle", "s_entree", "sens", "entree", "s_sortie", "sortie", "motif",
                                          "gain"])
        t.to_csv(RESULTATS / "historique_trades.csv", index=False, float_format="%.2f")
        barre = NormalDist().inv_cdf(1 - 0.05 / 7)
        L = [f"# Partie 9 : les 7 règles du tape sur {len(jours)} séances ({min(jours)} - {max(jours)})", "",
             f"Seconde de Databento, 1 MNQ, frais et glissement compris. Barre : t ≥ {barre:.2f} avec au moins 30 trades.",
             ""] + tableau(t, REGLES_TAPE, barre)
        L += ["", "Par mois ($) :", ""]
        t["mois"] = t["jour"].str[:7]
        piv = t.pivot_table(index="regle", columns="mois", values="gain", aggfunc="sum").fillna(0).round(0)
        L += ["| Règle | " + " | ".join(piv.columns) + " |", "|---|" + "---|" * len(piv.columns)]
        L += [f"| {r} | " + " | ".join(f"{v:+,.0f}" for v in piv.loc[r]) + " |" for r in piv.index]
        (RESULTATS / "historique.md").write_text("\n".join(L) + "\n")
        print("\n".join(L))
    else:
        dossiers = sys.argv[2:]                                 # dans l'ordre des jours ; la derniere est jugee
        etat = {"volumes": [], "vpin_jours": [], "paquets": []}
        lignes, jours = [], []
        for k, dos in enumerate(dossiers):
            j, paq = secondes_fluxnq(dos)
            if j is None:
                continue
            x, niv = paq
            regles, A = regles_tape(x, etat)
            if k < len(dossiers) - 1:
                continue
            if niv is not None:
                regles.update(regles_dom(x, niv, A))
            jours.append(j)
            lignes += [(j,) + tr for tr in jouer(x, regles)]
        t = pd.DataFrame(lignes, columns=["jour", "regle", "s_entree", "sens", "entree", "s_sortie", "sortie", "motif",
                                          "gain"])
        j = jours[-1]
        t.to_csv(RESULTATS / f"fluxnq_{j}.csv", index=False, float_format="%.2f")
        L = [f"# Partie 9 : séance du {j} enregistrée par FluxNQ (règles figées le 30 octobre 2026 à 9 h 42, New York)",
             "", "Une séance ne prouve rien : ces trades s'ajoutent au suivi (barre : 40 trades et t ≥ 2,64).", ""]
        L += tableau(t, REGLES_TAPE + REGLES_DOM)
        L += ["", "Trades :", ""]
        motifs = {0: "heure", 1: "stop", 2: "objectif"}
        for _, r in t.sort_values("s_entree").iterrows():
            L.append(f"- {r['regle']} {NOMS[r['regle']]} : {'achat' if r['sens'] > 0 else 'vente'} à {heure(r['s_entree'])} "
                     f"({r['entree']:.2f}), sortie à {heure(r['s_sortie'])} ({r['sortie']:.2f}, {motifs[int(r['motif'])]}) : "
                     f"{r['gain']:+.1f} $")
        (RESULTATS / f"fluxnq_{j}.md").write_text("\n".join(L) + "\n")
        print("\n".join(L))


if __name__ == "__main__":
    main()
