#!/usr/bin/env python3
"""Machine 7 (asie/README.md) : la reouverture de 18 h a New York (minuit a Paris). 173 strategies sur 7 marches,
barres de 5 minutes HistData en UTC. Exploration 2012-2022 avec placebos, coffre 2023 -> 2 octobre 2026 une seule fois.

Donnees : ASIE_DONNEES = dossier des fichiers sessions24/annees/<code>_<annee>_5m.csv.gz de la branche
claude/keen-babbage-r686cl (git show), par exemple :
    for f in $(git ls-tree -r --name-only origin/claude/keen-babbage-r686cl sessions24/annees); do
        git show origin/claude/keen-babbage-r686cl:$f > donnees/$(basename $f); done
Usage : ASIE_DONNEES=<dossier> python3 asie/machine7.py exploration | coffre | info
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit
from scipy.stats import norm

ICI = Path(__file__).resolve().parent
DONNEES = Path(os.environ.get("ASIE_DONNEES", ICI / "donnees"))
PAS = pd.Timedelta(minutes=5)
DEBUT, FIN_EXPLO, DEBUT_COFFRE, FIN = "2012-01-01", "2022-12-31", "2023-01-01", "2026-10-02"
SOUS = [(2012, 2015), (2016, 2019), (2020, 2022)]
N_SIGNES, GRAINE = 1000, 7
NY, HK = "America/New_York", "Asia/Hong_Kong"

# code : (nom, frais d'un aller-retour, unite ('pt' points de prix, 'pb' points de base), $ par unite de prix) - machine 5
MARCHES = {
    "usatechidxusd": ("Nasdaq 100", 1.5, "pt", 2.0),
    "usa500idxusd": ("S&P 500", 0.9, "pt", 5.0),
    "xauusd": ("Or", 2.0, "pb", 10.0),
    "usdjpy": ("Yen", 1.5, "pb", None),
    "audusd": ("Dollar australien", 1.5, "pb", 100000.0),
    "eurusd": ("Euro", 1.5, "pb", 125000.0),
    "gbpusd": ("Livre", 1.5, "pb", 62500.0),
}
LONG_SEUL = ["usatechidxusd", "usa500idxusd", "xauusd"]
SORTIES = {"19:00": ("19:00", 0), "21:00": ("21:00", 0), "23:30": ("23:30", 0)}


# ------------------------------------------------------------------ donnees (comme la machine 5)
class Marche:
    def __init__(self, code):
        d = pd.concat([pd.read_csv(x) for x in sorted(DONNEES.glob(f"{code}_*_5m.csv.gz"))])
        d = d.drop_duplicates("t", keep="last").sort_values("t")
        t = pd.to_datetime(d["t"], utc=True)
        self.code, self.t0 = code, pd.Timestamp(DEBUT, tz="UTC")
        fin = t.max().floor("D") + pd.Timedelta(days=1)
        self.n = int((fin - self.t0) / PAS)
        i = ((t - self.t0) / PAS).to_numpy().astype(np.int64)
        ok = (i >= 0) & (i < self.n)
        self.O, self.H, self.L, self.C = (np.full(self.n, np.nan) for _ in range(4))
        for a, col in ((self.O, "o"), (self.H, "h"), (self.L, "l"), (self.C, "c")):
            a[i[ok]] = d[col].to_numpy()[ok]
        self.nom, self.frais, self.unite, self.dollar = MARCHES[code]

    def indice(self, t_utc):
        k = ((t_utc - self.t0) / PAS).to_numpy()
        k = np.where(np.isfinite(k), k, -1).astype(np.int64)
        return np.where((k >= 0) & (k < self.n), k, -1)

    def cout(self, prix):
        return self.frais / prix if self.unite == "pt" else self.frais * 1e-4 + 0 * prix

    def notionnel(self, prix):
        return 12_500_000.0 / prix if self.code == "usdjpy" else self.dollar * prix


def soirs(debut, fin):
    """Soirs du lundi au jeudi (date de New York)."""
    j = pd.date_range(debut, fin, freq="D")
    return j[j.dayofweek < 4]


def utc(jours, fz, hhmm, dj=0):
    h, m = map(int, hhmm.split(":"))
    loc = jours + pd.Timedelta(days=dj) + pd.Timedelta(hours=h, minutes=m)
    return loc.tz_localize(fz, nonexistent="shift_forward", ambiguous="NaT").tz_convert("UTC")


# ------------------------------------------------------------------ cassure avec derniere entree
@njit(cache=True)
def cassures(O, H, L, C, a_, b_, dern_, f_, nb):
    """Fourchette [a, b) ; premiere cloture au-dela de b a dern (exclu) ; entree a l'ouverture suivante ; stop de l'autre
    cote ; sortie a l'ouverture de f. Renvoie sens, prix d'entree, prix de sortie."""
    m = a_.shape[0]
    sens = np.zeros(m, np.int64); pe = np.full(m, np.nan); ps = np.full(m, np.nan)
    for k in range(m):
        a, b, dern, f = a_[k], b_[k], dern_[k], f_[k]
        if a < 0 or b <= a or dern <= b or f <= dern or f >= O.shape[0]:
            continue
        hh, ll, n = -1e300, 1e300, 0
        for i in range(a, b):
            if np.isfinite(H[i]):
                hh = max(hh, H[i]); ll = min(ll, L[i]); n += 1
        if n < nb:
            continue
        pos, e, stop = 0, 0.0, 0.0
        for i in range(b, f):
            if pos == 0:
                if i >= dern or i + 1 >= f or not np.isfinite(C[i]):
                    continue
                if C[i] > hh and np.isfinite(O[i + 1]):
                    pos, e, stop = 1, O[i + 1], ll
                elif C[i] < ll and np.isfinite(O[i + 1]):
                    pos, e, stop = -1, O[i + 1], hh
                if pos != 0:
                    sens[k], pe[k] = pos, e
                continue
            if not np.isfinite(O[i]):
                continue
            if pos == 1 and L[i] <= stop:
                ps[k] = stop if O[i] > stop else O[i]; pos = 2; break
            if pos == -1 and H[i] >= stop:
                ps[k] = stop if O[i] < stop else O[i]; pos = 2; break
        if pos == 1 or pos == -1:
            j = f
            while j < O.shape[0] and not np.isfinite(O[j]) and j < f + 12:
                j += 1
            if j < O.shape[0] and np.isfinite(O[j]):
                ps[k] = O[j]
            else:
                sens[k] = 0
    return sens, pe, ps


# ------------------------------------------------------------------ les 173 strategies
def strategies():
    S = []
    for c in MARCHES:
        for sx in SORTIES:
            sens_possibles = [1] if c in LONG_SEUL else [1, -1]
            for sg in sens_possibles:
                S.append(dict(nom=f"R1 {c} {'achat' if sg > 0 else 'vente'} 18:00->{sx}", famille="R1", marche=c, sens=sg, sortie=sx))
    for c in MARCHES:
        for sig in ("derniere_heure", "seance"):
            for dirn in ("retour", "continuation"):
                for sx in SORTIES:
                    S.append(dict(nom=f"R2 {c} {sig} {dirn} 18:00->{sx}", famille="R2", marche=c, signal=sig, dirn=dirn, sortie=sx))
    for c in MARCHES:
        for rng_min in (15, 30):
            for sx in ("21:00", "23:30", "03:00"):
                S.append(dict(nom=f"R3 {c} fourchette {rng_min} min sortie {sx}", famille="R3", marche=c, fourchette=rng_min, sortie=sx))
    for c in MARCHES:
        for sx in ("HK12:00", "NY03:00"):
            S.append(dict(nom=f"R4 {c} Hong Kong sortie {sx}", famille="R4", marche=c, sortie=sx))
    return S


def jouer(s, M, debut, fin, decalage=0):
    """Trades d'une strategie : DataFrame (jour = soir de New York, r = net, brut = avant frais signe, e = entree)."""
    j = soirs(debut, fin)
    if s["famille"] in ("R1", "R2"):
        i_e = M.indice(utc(j, NY, "18:00")) + decalage
        i_s = M.indice(utc(j, NY, SORTIES[s["sortie"]][0])) + decalage
        if s["famille"] == "R1":
            sens = np.full(len(j), s["sens"], float)
        else:
            i16 = M.indice(utc(j, NY, "16:00"))
            i0 = M.indice(utc(j, NY, "15:00" if s["signal"] == "derniere_heure" else "09:30"))
            ok = (i16 >= 0) & (i0 >= 0)
            a = np.where(ok, M.O[np.clip(i16, 0, M.n - 1)], np.nan); b = np.where(ok, M.O[np.clip(i0, 0, M.n - 1)], np.nan)
            mv = np.sign(a / b - 1)
            sens = np.where(np.isfinite(mv), mv, 0.0) * (-1.0 if s["dirn"] == "retour" else 1.0)
        ok = (i_e >= 0) & (i_s > i_e) & (i_s < M.n) & (sens != 0)
        e = np.where(ok, M.O[np.clip(i_e, 0, M.n - 1)], np.nan); x = np.where(ok, M.O[np.clip(i_s, 0, M.n - 1)], np.nan)
        ok &= np.isfinite(e) & np.isfinite(x)
        brut = sens[ok] * (x[ok] / e[ok] - 1)
        e = e[ok]; jours = j[ok]
    else:
        if s["famille"] == "R3":
            a = M.indice(utc(j, NY, "18:00")); b = a + s["fourchette"] // 5
            dern = M.indice(utc(j, NY, "19:55"))
            f = M.indice(utc(j, NY, "03:00", 1)) if s["sortie"] == "03:00" else M.indice(utc(j, NY, s["sortie"]))
            nb = 2
        else:
            jh = j + pd.Timedelta(days=1)                                 # le soir de New York = le matin suivant a Hong Kong
            a = M.indice(utc(jh, HK, "09:30")); b = M.indice(utc(jh, HK, "10:00"))
            dern = M.indice(utc(jh, HK, "11:25"))
            f = M.indice(utc(jh, HK, "12:00")) if s["sortie"] == "HK12:00" else M.indice(utc(j, NY, "03:00", 1))
            nb = 3
        sg, pe, ps = cassures(M.O, M.H, M.L, M.C, a, b, dern, f, nb)
        ok = (sg != 0) & np.isfinite(pe) & np.isfinite(ps)
        brut = sg[ok] * (ps[ok] / pe[ok] - 1); e = pe[ok]; jours = j[ok]
    cout = np.array([M.cout(v) for v in e]) if len(e) else np.array([])
    return pd.DataFrame({"jour": jours, "brut": brut, "r": brut - cout, "e": e})


def t_stat(x):
    x = np.asarray(x, float)
    if len(x) < 3 or x.std(ddof=1) == 0:
        return 0.0
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x)))


def placebo(s, M, d):
    t_reel = t_stat(d["r"])
    if s["famille"] == "R1":
        ts = [t_stat(jouer(s, M, DEBUT, FIN_EXPLO, decalage=k)["r"]) for k in range(-144, 145) if abs(k) * 5 > 120]
    else:
        rng = np.random.default_rng(GRAINE); brut = d["brut"].to_numpy(); cout = brut - d["r"].to_numpy()
        ts = [t_stat(rng.choice([-1.0, 1.0], len(brut)) * brut - cout) for _ in range(N_SIGNES)]
    ts = np.array(ts)
    return float((ts >= t_reel).mean()), len(ts)


def bilan(d, M):
    an = pd.DatetimeIndex(d["jour"]).year
    dol = d["r"].to_numpy() * np.array([M.notionnel(e) for e in d["e"].to_numpy()])
    return {"t": round(t_stat(d["r"]), 2), "soirs": int(len(d)), "net_moyen_pb": round(float(d["r"].mean()) * 1e4, 2) if len(d) else 0.0,
            "brut_moyen_pb": round(float(d["brut"].mean()) * 1e4, 2) if len(d) else 0.0,
            "dollars_1_contrat": round(float(dol.sum()), 0),
            "sous_periodes": [round(float(d["r"][(an >= a) & (an <= b)].sum()) * 1e4, 1) for a, b in SOUS]}


def benjamini_hochberg(p, q=0.10):
    p = np.asarray(p); o = np.argsort(p); m = len(p)
    ok = p[o] <= q * np.arange(1, m + 1) / m
    k = np.max(np.where(ok)[0]) + 1 if ok.any() else 0
    g = np.zeros(m, bool); g[o[:k]] = True
    return g


def exploration():
    S = strategies(); assert len(S) == 173, len(S)
    marches = {c: Marche(c) for c in MARCHES}
    res = []
    for s in S:
        M = marches[s["marche"]]; d = jouer(s, M, DEBUT, FIN_EXPLO); b = bilan(d, M); b.update(nom=s["nom"], famille=s["famille"])
        if b["soirs"] < 200:
            b.update(p=None, testable=False)
        else:
            p, npl = placebo(s, M, d); b.update(p=p, placebos=npl, testable=True)
        res.append(b)
        print(f"{s['nom']} : t {b['t']:+.2f}, brut {b['brut_moyen_pb']:+.2f} pb, net {b['net_moyen_pb']:+.2f} pb, p {b.get('p')}, {b['soirs']} soirs", flush=True)
    jug = [r for r in res if r["testable"]]
    bh = benjamini_hochberg([r["p"] for r in jug])
    for r in res:
        r["bh"] = r["survivante"] = False
    for r, g in zip(jug, bh):
        r["bh"] = bool(g)
        r["survivante"] = bool(r["t"] >= 2 and r["p"] <= 0.05 and sum(x > 0 for x in r["sous_periodes"]) >= 2 and g)
    surv = [r["nom"] for r in res if r["survivante"]]
    L = [f"Machine 7, exploration 2012 - 2022 : {len(S)} strategies, {len(jug)} testables ; survivantes : {len(surv)}", "",
         "strategie | t | brut moyen (pb) | net moyen (pb) | p placebo | BH 10 % | sous-periodes (pb) | soirs | $ pour 1 contrat | survivante"]
    for r in sorted(res, key=lambda x: -x["t"]):
        L.append(f"{r['nom']} | {r['t']:+.2f} | {r['brut_moyen_pb']:+.2f} | {r['net_moyen_pb']:+.2f} | "
                 + (f"{r['p']:.3f}" if r["testable"] else "non testable") + f" | {'oui' if r['bh'] else 'non'} | "
                 + " / ".join(f"{x:+.1f}" for x in r["sous_periodes"]) + f" | {r['soirs']} | {r['dollars_1_contrat']:+,.0f} | {'OUI' if r['survivante'] else ''}")
    (ICI / "exploration7.txt").write_text("\n".join(L) + "\n")
    (ICI / "exploration7.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    (ICI / "survivantes7.json").write_text(json.dumps(surv, indent=1, ensure_ascii=False))
    print("\n".join(L[:14]))


def coffre():
    surv = json.loads((ICI / "survivantes7.json").read_text())
    if not surv:
        print("Aucune survivante : le coffre 2023 - 2026 reste ferme."); return
    S = {s["nom"]: s for s in strategies()}; m = len(surv); seuil = float(norm.ppf(1 - 0.05 / m))
    marches = {}
    L = [f"Machine 7, coffre 2023 -> {FIN} : {m} survivantes, seuil de Bonferroni t >= {seuil:.2f}, 3 annees positives sur 4", ""]
    res = []
    for nom in surv:
        s = S[nom]; M = marches.setdefault(s["marche"], Marche(s["marche"]))
        d = jouer(s, M, DEBUT_COFFRE, FIN); an = pd.DatetimeIndex(d["jour"]).year
        par_an = {y: round(float(d["r"][an == y].sum()) * 1e4, 1) for y in (2023, 2024, 2025, 2026)}
        t = t_stat(d["r"]); passe = bool(t >= seuil and sum(v > 0 for v in par_an.values()) >= 3)
        res.append(dict(nom=nom, t=round(t, 2), par_an=par_an, soirs=len(d), passe=passe))
        L.append(f"{nom} | t {t:+.2f} | " + " / ".join(f"{y} {v:+.1f}" for y, v in par_an.items()) + f" | {'PASSE' if passe else 'echoue'}")
    (ICI / "coffre7.txt").write_text("\n".join(L) + "\n"); (ICI / "coffre7.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("\n".join(L))


def info():
    """Pour information : volatilite par barre de 5 min de 17 h a 3 h (New York) et premiere heure apres 18 h et 9 h 30."""
    L = ["Machine 7, information : minuit (18 h a New York) contre l'ouverture de New York (9 h 30)", ""]
    heures = [f"{h:02d}:{m:02d}" for h in list(range(17, 24)) + [0, 1, 2, 3] for m in range(0, 60, 5)] + ["09:30", "09:35", "09:40", "10:00"]
    for c in ("usatechidxusd", "usa500idxusd", "xauusd", "usdjpy"):
        M = Marche(c)
        for nom_p, (a, b) in (("2012-2022", (DEBUT, FIN_EXPLO)), ("2023-2026", (DEBUT_COFFRE, FIN))):
            j = soirs(a, b); vol = {}
            for hh in heures:
                dj = 0 if hh in ("09:30", "09:35", "09:40", "10:00") else (1 if int(hh[:2]) <= 3 else 0)
                i = M.indice(utc(j, NY, hh, dj)); i = i[i >= 0]
                x = (M.H[i] - M.L[i]) / M.O[i] * 1e4
                vol[hh] = float(np.nanmean(x)) if np.isfinite(x).any() else float("nan")
            top = sorted(((v, k) for k, v in vol.items() if k not in ("09:30", "09:35", "09:40", "10:00") and np.isfinite(v)), reverse=True)[:5]
            def premiere_heure(hh, dj=0):
                i0 = M.indice(utc(j, NY, hh, dj)); amp, eff = [], []
                for k in i0:
                    if k < 0 or k + 12 > M.n:
                        continue
                    o, h, l, c_ = M.O[k:k + 12], M.H[k:k + 12], M.L[k:k + 12], M.C[k:k + 12]
                    if not (np.isfinite(o[0]) and np.isfinite(c_).sum() >= 10):
                        continue
                    cc = c_[np.isfinite(c_)]
                    chemin = abs(cc[0] - o[0]) + np.abs(np.diff(cc)).sum()
                    amp.append((np.nanmax(h) - np.nanmin(l)) / o[0] * 1e4)
                    if chemin > 0:
                        eff.append(abs(cc[-1] - o[0]) / chemin)
                return np.mean(amp), np.mean(eff), len(amp)
            a18, e18, n18 = premiere_heure("18:00"); a93, e93, n93 = premiere_heure("09:30")
            L.append(f"{MARCHES[c][0]} {nom_p} : barre de 18 h 00 {vol['18:00']:.1f} pb d'amplitude (17 h 55 : {vol.get('17:55', float('nan')):.1f} ; 18 h 05 : {vol['18:05']:.1f} ; "
                     f"18 h 30 : {vol['18:30']:.1f} ; 21 h 30 : {vol['21:30']:.1f} ; 3 h 00 : {vol['03:00']:.1f}) ; barre de 9 h 30 : {vol['09:30']:.1f} pb")
            L.append(f"   5 barres les plus agitees de 17 h a 3 h : " + ", ".join(f"{k} ({v:.1f} pb)" for v, k in top))
            L.append(f"   premiere heure apres 18 h 00 : amplitude {a18:.1f} pb, efficacite {e18:.2f} ({n18} soirs) ; "
                     f"apres 9 h 30 : amplitude {a93:.1f} pb, efficacite {e93:.2f} ({n93} jours)")
        L.append("")
    (ICI / "info7.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    {"exploration": exploration, "coffre": coffre, "info": info}[sys.argv[1]]()
