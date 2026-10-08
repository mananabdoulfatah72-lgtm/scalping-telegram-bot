#!/usr/bin/env python3
"""Machine 5 (README.md) : 176 strategies de sessions (Asie, Londres, New York) sur 9 marches, barres de 5 minutes
Dukascopy en UTC. Exploration 2012-2022 avec placebos, coffre 2023 - 2026 une seule fois pour les survivantes.
Lancer depuis ce dossier : python3 machine5.py exploration | coffre"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit
from scipy.stats import norm

ICI = Path(__file__).resolve().parent
DONNEES = ICI / "donnees"
PAS = pd.Timedelta(minutes=5)
DEBUT, FIN_EXPLO, DEBUT_COFFRE = "2012-01-01", "2022-12-31", "2023-01-01"
SOUS = [(2012, 2015), (2016, 2019), (2020, 2022)]
N_SIGNES = 1000
GRAINE = 5

# code : (nom, frais d'un aller-retour, unite des frais ('pt' points de prix, 'pb' points de base), $ par unite de prix)
MARCHES = {
    "usatechidxusd": ("Nasdaq 100", 1.5, "pt", 2.0),
    "usa500idxusd": ("S&P 500", 0.9, "pt", 5.0),
    "usa30idxusd": ("Dow Jones", 3.0, "pt", 0.5),
    "eurusd": ("Euro", 1.5, "pb", 125000.0),
    "gbpusd": ("Livre", 1.5, "pb", 62500.0),
    "usdjpy": ("Yen", 1.5, "pb", None),
    "audusd": ("Dollar australien", 1.5, "pb", 100000.0),
    "xauusd": ("Or", 2.0, "pb", 10.0),
    "lightcmdusd": ("Petrole WTI", 4.0, "pb", 100.0),
}
INDICES = ["usatechidxusd", "usa500idxusd", "usa30idxusd"]
DEVISES = ["eurusd", "gbpusd", "usdjpy", "audusd"]
TOKYO, LONDRES, NY, FRANCFORT = "Asia/Tokyo", "Europe/London", "America/New_York", "Europe/Berlin"
SESSIONS = {"Tokyo": (TOKYO, "09:00", "15:00"), "Londres": (LONDRES, "08:00", "16:30"), "New York": (NY, "09:30", "16:00")}


# ------------------------------------------------------------------ donnees
class Marche:
    """Prix d'un marche sur une grille reguliere de 5 minutes en UTC (NaN quand il n'y a pas de barre)."""

    def __init__(self, code, d=None):
        self.code = code
        if d is None:
            f = DONNEES / f"{code}_5m.csv.gz"
            if f.exists():
                d = pd.read_csv(f)
            else:                                                   # une annee par fichier (sessions24/annees/)
                d = pd.concat([pd.read_csv(x) for x in sorted((ICI / "annees").glob(f"{code}_*_5m.csv.gz"))])
                d = d.drop_duplicates("t", keep="last").sort_values("t")
        t = pd.to_datetime(d["t"], utc=True)
        self.t0 = pd.Timestamp(DEBUT, tz="UTC")
        fin = t.max().floor("D") + pd.Timedelta(days=1)
        n = int((fin - self.t0) / PAS)
        i = ((t - self.t0) / PAS).to_numpy().astype(np.int64)
        ok = (i >= 0) & (i < n)
        self.n = n
        self.O, self.H, self.L, self.C = (np.full(n, np.nan) for _ in range(4))
        for a, col in ((self.O, "o"), (self.H, "h"), (self.L, "l"), (self.C, "c")):
            a[i[ok]] = d[col].to_numpy()[ok]
        nom, frais, unite, dollar = MARCHES.get(code, (code, 0.0, "pb", 1.0))
        self.nom, self.frais, self.unite, self.dollar = nom, frais, unite, dollar

    def indice(self, t_utc):
        """Indice de grille d'heures UTC (DatetimeIndex aware) ; -1 hors grille."""
        k = ((t_utc - self.t0) / PAS).to_numpy()
        k = np.where(np.isfinite(k), k, -1).astype(np.int64)
        return np.where((k >= 0) & (k < self.n), k, -1)

    def cout(self, prix):
        """Frais d'un aller-retour, en rendement, pour une entree a `prix`."""
        return self.frais / prix if self.unite == "pt" else self.frais * 1e-4

    def notionnel(self, prix):
        """Valeur en $ d'un contrat (pour passer des rendements aux dollars)."""
        if self.code == "usdjpy":
            return 12_500_000.0 / prix
        return self.dollar * prix


def jours_locaux(fz, debut, fin):
    """Jours de semaine (lundi-vendredi) dans le fuseau fz."""
    j = pd.date_range(debut, fin, freq="D")
    return j[j.dayofweek < 5]


def heure_utc(jours, fz, hhmm, decalage_jours=0):
    """Heure locale hhmm des jours (dates naives) dans le fuseau fz -> DatetimeIndex UTC."""
    h, m = map(int, hhmm.split(":"))
    loc = (jours + pd.Timedelta(days=decalage_jours) + pd.Timedelta(hours=h, minutes=m))
    return loc.tz_localize(fz, nonexistent="shift_forward", ambiguous="NaT").tz_convert("UTC")


def jour_de_trading(t_utc):
    """Jour de trading CME (18 h - 17 h, heure de New York) d'une heure UTC."""
    return (t_utc.tz_convert(NY) + pd.Timedelta(hours=6)).tz_localize(None).normalize()


# ------------------------------------------------------------------ trades a fenetre fixe
def trades_fenetre(M, i_entree, i_sortie, sens):
    """Trades d'une fenetre fixe : achat (sens +1) ou vente (-1) a l'ouverture de la barre i_entree, sortie a l'ouverture
    de la barre i_sortie. Renvoie (indices de sortie, rendement net) pour les trades dont les deux barres existent."""
    ok = (i_entree >= 0) & (i_sortie > i_entree) & (i_sortie < M.n)
    e = np.where(ok, M.O[np.clip(i_entree, 0, M.n - 1)], np.nan)
    s = np.where(ok, M.O[np.clip(i_sortie, 0, M.n - 1)], np.nan)
    ok &= np.isfinite(e) & np.isfinite(s)
    sens = np.broadcast_to(sens, e.shape)
    r = sens[ok] * (s[ok] / e[ok] - 1) - M.cout(e[ok])
    return i_sortie[ok], r, e[ok]


# ------------------------------------------------------------------ cassures (une par session, stop de l'autre cote)
@njit(cache=True)
def cassures(O, H, L, C, debut_f, fin_f, fin_s, nb):
    """Pour chaque session k : fourchette des barres [debut_f[k], fin_f[k]) ; de fin_f[k] a fin_s[k], premiere cloture
    de 5 min au-dessus (achat) ou au-dessous (vente) ; entree a l'ouverture de la barre suivante ; stop de l'autre cote
    (sortie au stop, ou a l'ouverture si elle est deja au-dela) ; sinon sortie a l'ouverture de fin_s[k]. Renvoie, par
    session : sens (0 : pas de trade), prix d'entree, prix de sortie, barre de sortie."""
    m = debut_f.shape[0]
    sens = np.zeros(m, np.int64)
    pe, ps = np.full(m, np.nan), np.full(m, np.nan)
    bs = np.full(m, -1, np.int64)
    for k in range(m):
        a, b, f = debut_f[k], fin_f[k], fin_s[k]
        if a < 0 or b <= a or f <= b or f >= O.shape[0]:
            continue
        hh, ll, n = -1e300, 1e300, 0
        for i in range(a, b):
            if np.isfinite(H[i]):
                hh = max(hh, H[i])
                ll = min(ll, L[i])
                n += 1
        if n < nb:
            continue
        pos, e, stop = 0, 0.0, 0.0
        for i in range(b, f):
            if pos == 0:
                if i + 1 >= f or not np.isfinite(C[i]):
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
                ps[k], bs[k] = (stop if O[i] > stop else O[i]), i
                pos = 2
                break
            if pos == -1 and H[i] >= stop:
                ps[k], bs[k] = (stop if O[i] < stop else O[i]), i
                pos = 2
                break
        if pos == 1 or pos == -1:
            j = f
            while j < O.shape[0] and not np.isfinite(O[j]) and j < f + 12:
                j += 1
            if j < O.shape[0] and np.isfinite(O[j]):
                ps[k], bs[k] = O[j], j
            else:
                sens[k] = 0
    return sens, pe, ps, bs


# ------------------------------------------------------------------ les 176 strategies
def strategies():
    """Liste des strategies : dict(nom, famille, marche, genre, ...)."""
    S = []
    fix = {"Tokyo 9 h 55": (TOKYO, "09:55"), "BCE 14 h 15": (FRANCFORT, "14:15"), "WM/Reuters 16 h": (LONDRES, "16:00")}
    for c in DEVISES:
        dollar_monte = 1 if c == "usdjpy" else -1          # sens du trade quand le dollar monte
        for nf, (fz, h) in fix.items():
            for v in ("avant", "apres", "les deux"):
                S.append(dict(nom=f"F1 fixing {nf} {v} {c}", famille="F1", marche=c, genre="fixing", fz=fz, h=h,
                              variante=v, sens=dollar_monte))
    for c in INDICES:
        for fen in (("08:00", "09:00"), ("09:00", "10:00"), ("08:00", "10:00")):
            for cond in (False, True):
                S.append(dict(nom=f"F2 Europe {fen[0]}-{fen[1]}{' apres baisse de NY' if cond else ''} {c}",
                              famille="F2", marche=c, genre="europe", fen=fen, cond=cond))
    for c in MARCHES:
        for ns in ("Tokyo", "Londres", "New York"):
            if ns == "New York" and c in INDICES:
                continue
            for r in (30, 60):
                S.append(dict(nom=f"F3 cassure {ns} {r} min {c}", famille="F3", marche=c, genre="cassure", session=ns, r=r))
    for c in MARCHES:
        for sortie in ("12:00", "16:30"):
            S.append(dict(nom=f"F4 Asie -> Londres sortie {sortie} {c}", famille="F4", marche=c, genre="asie", sortie=sortie))
    for c in MARCHES:
        for paire in (("Tokyo", "Londres"), ("Londres", "New York"), ("New York", "Tokyo")):
            for v in ("continuation", "retournement"):
                S.append(dict(nom=f"F5 {paire[0]} -> {paire[1]} {v} {c}", famille="F5", marche=c, genre="suite",
                              paire=paire, variante=v))
    S.append(dict(nom="F6 or achat hors New York (18 h - 8 h 20)", famille="F6", marche="xauusd", genre="or", cote="nuit"))
    S.append(dict(nom="F6 or vente heures COMEX (8 h 20 - 13 h 30)", famille="F6", marche="xauusd", genre="or", cote="jour"))
    return S


def evenements(s, debut, fin):
    """Pour une strategie a fenetre fixe : liste de (i_entree, i_sortie, sens) en heures UTC, avant indexation."""
    if s["genre"] == "fixing":
        j = jours_locaux(s["fz"], debut, fin)
        E = heure_utc(j, s["fz"], s["h"])
        out = []
        if s["variante"] in ("avant", "les deux"):
            out.append((E - pd.Timedelta(minutes=60), E, s["sens"]))
        if s["variante"] in ("apres", "les deux"):
            out.append((E, E + pd.Timedelta(minutes=60), -s["sens"]))
        return out
    if s["genre"] == "europe":
        j = jours_locaux(FRANCFORT, debut, fin)
        return [(heure_utc(j, FRANCFORT, s["fen"][0]), heure_utc(j, FRANCFORT, s["fen"][1]), 1)]
    if s["genre"] == "or":
        j = jours_locaux(NY, debut, fin)
        if s["cote"] == "nuit":
            return [(heure_utc(j, NY, "18:00", -1), heure_utc(j, NY, "08:20"), 1)]
        return [(heure_utc(j, NY, "08:20"), heure_utc(j, NY, "13:30"), -1)]
    raise ValueError(s["genre"])


def condition_europe(M, j_frankfurt):
    """Pour F2 conditionnel : la seance de New York qui precede le matin de Francfort a baisse (ouverture 9 h 30 ->
    ouverture de la barre de 16 h, jour de semaine new-yorkais d'avant)."""
    veille = pd.DatetimeIndex([d - pd.offsets.BDay(1) for d in j_frankfurt])
    a, b = M.indice(heure_utc(veille, NY, "09:30")), M.indice(heure_utc(veille, NY, "16:00"))
    pa = np.where(a >= 0, M.O[np.clip(a, 0, M.n - 1)], np.nan)
    pb = np.where(b >= 0, M.O[np.clip(b, 0, M.n - 1)], np.nan)
    return pb < pa


def jouer(s, M, debut, fin, decalage=0):
    """Trades d'une strategie entre debut et fin (dates). decalage (en barres) : placebo d'heure pour les fenetres fixes.
    Renvoie un DataFrame : jour (de trading), rendement net, prix d'entree."""
    if s["genre"] in ("fixing", "europe", "or"):
        res = []
        for te, ts, sens in evenements(s, debut, fin):
            ie, isx = M.indice(te), M.indice(ts)
            dans = (ie >= 0) & (isx >= 0) & (ie + decalage >= 0) & (isx + decalage < M.n)
            ie = np.where(dans, ie + decalage, -1)
            isx = np.where(dans, isx + decalage, -1)
            garde = np.ones(len(ie), bool)
            if s["genre"] == "europe" and s["cond"]:
                garde = condition_europe(M, jours_locaux(FRANCFORT, debut, fin))
            ie = np.where(garde, ie, -1)
            b, r, e = trades_fenetre(M, ie, isx, np.full(len(ie), sens))
            res.append(pd.DataFrame({"barre": b, "r": r, "e": e}))
        d = pd.concat(res)
    elif s["genre"] in ("cassure", "asie"):
        if s["genre"] == "cassure":
            fz, h0, h1 = SESSIONS[s["session"]]
            j = jours_locaux(fz, debut, fin)
            a = M.indice(heure_utc(j, fz, h0))
            b = np.where(a >= 0, a + s["r"] // 5, -1)
            f = M.indice(heure_utc(j, fz, h1))
            nb = s["r"] // 5 - 1
        else:
            j = jours_locaux(LONDRES, debut, fin)
            a = M.indice(heure_utc(j, LONDRES, "00:00"))
            b = M.indice(heure_utc(j, LONDRES, "07:00"))
            f = M.indice(heure_utc(j, LONDRES, s["sortie"]))
            nb = 60
        sens, pe, ps, bs = cassures(M.O, M.H, M.L, M.C, a, b, f, nb)
        ok = sens != 0
        r = sens[ok] * (ps[ok] / pe[ok] - 1) - M.cout(pe[ok])
        d = pd.DataFrame({"barre": bs[ok], "r": r, "e": pe[ok]})
    elif s["genre"] == "suite":
        p, q = s["paire"]
        fzq, hq0, hq1 = SESSIONS[q]
        fzp, hp0, hp1 = SESSIONS[p]
        jq = jours_locaux(fzq, debut, fin)
        tq0, tq1 = heure_utc(jq, fzq, hq0), heure_utc(jq, fzq, hq1)
        if (p, q) == ("Tokyo", "Londres"):
            tp0, tp1 = heure_utc(jq, TOKYO, hp0), heure_utc(jq, TOKYO, hp1)
        elif (p, q) == ("Londres", "New York"):
            tp0, tp1 = heure_utc(jq, LONDRES, hp0), tq0           # Londres n'est pas finie a 9 h 30 : jusqu'a 9 h 30
        else:                                                     # New York de la veille (jour de semaine) -> Tokyo
            veille = pd.DatetimeIndex([d_ - pd.offsets.BDay(1) for d_ in jq])
            tp0, tp1 = heure_utc(veille, NY, hp0), heure_utc(veille, NY, hp1)
        ip0, ip1 = M.indice(tp0), M.indice(tp1)
        o0 = np.where(ip0 >= 0, M.O[np.clip(ip0, 0, M.n - 1)], np.nan)
        o1 = np.where(ip1 >= 0, M.O[np.clip(ip1, 0, M.n - 1)], np.nan)
        signe = np.sign(o1 - o0)
        if s["variante"] == "retournement":
            signe = -signe
        valide = ~(tp1.isna() | tq0.isna())
        assert (tp1[valide] <= tq0[valide]).all()                 # le signal ne lit rien apres l'entree
        ie, isx = M.indice(tq0), M.indice(tq1)
        ie = np.where(np.isfinite(signe) & (signe != 0), ie, -1)
        b, r, e = trades_fenetre(M, ie, isx, np.nan_to_num(signe))
        d = pd.DataFrame({"barre": b, "r": r, "e": e})
    else:
        raise ValueError(s["genre"])
    if d.empty:
        return pd.DataFrame(columns=["jour", "r", "e"])
    t = M.t0 + d["barre"].to_numpy() * PAS
    d["jour"] = jour_de_trading(pd.DatetimeIndex(t))
    return d.drop(columns="barre")


def par_jour(d):
    return d.groupby("jour")["r"].sum() if len(d) else pd.Series(dtype=float)


def t_stat(x):
    x = np.asarray(x, float)
    if len(x) < 3:
        return 0.0
    s = x.std(ddof=1)
    return 0.0 if s == 0 else x.mean() / s * np.sqrt(len(x))


def placebo(s, M, d):
    """p du placebo (part des placebos qui font au moins aussi bien) et nombre de placebos."""
    t_reel = t_stat(par_jour(d))
    if s["genre"] in ("fixing", "europe", "or"):
        ts = []
        for k in range(-144, 144):
            if abs(k) * 5 <= 120:
                continue
            ts.append(t_stat(par_jour(jouer(s, M, DEBUT, FIN_EXPLO, decalage=k))))
        ts = np.array(ts)
    else:
        rng = np.random.default_rng(GRAINE)
        r = d["r"].to_numpy()
        brut = r + np.array([M.cout(e) for e in d["e"].to_numpy()])         # avant frais : le sens au hasard
        cout = brut - r
        jours = pd.factorize(d["jour"])[0]
        ts = np.empty(N_SIGNES)
        for i in range(N_SIGNES):
            sg = rng.choice([-1.0, 1.0], len(r))
            ts[i] = t_stat(np.bincount(jours, sg * brut - cout))
    return float((ts >= t_reel).mean()), len(ts)


def bilan(d, M):
    j = par_jour(d)
    an = j.index.year
    dol = d["r"].to_numpy() * np.array([M.notionnel(e) for e in d["e"].to_numpy()])
    return {"t": round(t_stat(j), 2), "jours": int(len(j)), "rend_moyen_pb": round(float(j.mean()) * 1e4, 2) if len(j) else 0,
            "dollars_1_contrat": round(float(dol.sum()), 0),
            "sous_periodes": [round(float(j[(an >= a) & (an <= b)].sum()) * 1e4, 1) for a, b in SOUS]}


def benjamini_hochberg(p, q=0.10):
    p = np.asarray(p)
    o = np.argsort(p)
    m = len(p)
    seuil = q * np.arange(1, m + 1) / m
    ok = p[o] <= seuil
    k = np.max(np.where(ok)[0]) + 1 if ok.any() else 0
    garde = np.zeros(m, bool)
    garde[o[:k]] = True
    return garde


def exploration():
    S = strategies()
    assert len(S) == 176, len(S)
    marches = {c: Marche(c) for c in MARCHES}
    lignes, res = [], []
    for s in S:
        M = marches[s["marche"]]
        d = jouer(s, M, DEBUT, FIN_EXPLO)
        b = bilan(d, M)
        p, npl = placebo(s, M, d)
        b.update(nom=s["nom"], famille=s["famille"], p=p, placebos=npl)
        res.append(b)
        print(f"{s['nom']} : t {b['t']:+.2f}, p {p:.3f}, {b['jours']} jours", flush=True)
    bh = benjamini_hochberg([r["p"] for r in res])
    surv = []
    for r, g in zip(res, bh):
        r["bh"] = bool(g)
        r["survivante"] = bool(r["t"] >= 2 and r["p"] <= 0.05 and sum(x > 0 for x in r["sous_periodes"]) >= 2 and g)
        if r["survivante"]:
            surv.append(r["nom"])
    L = [f"Machine 5, exploration {DEBUT[:4]} - {FIN_EXPLO[:4]} : {len(S)} strategies ; survivantes : {len(surv)}", "",
         "strategie | t | p placebo | BH 10 % | sous-periodes (pb) | jours | $ pour 1 contrat | survivante"]
    for r in sorted(res, key=lambda x: -x["t"]):
        L.append(f"{r['nom']} | {r['t']:+.2f} | {r['p']:.3f} | {'oui' if r['bh'] else 'non'} | "
                 f"{' / '.join(f'{x:+.1f}' for x in r['sous_periodes'])} | {r['jours']} | {r['dollars_1_contrat']:+,.0f} |"
                 f" {'OUI' if r['survivante'] else ''}")
    (ICI / "exploration5.txt").write_text("\n".join(L) + "\n")
    (ICI / "exploration5.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    (ICI / "survivantes5.json").write_text(json.dumps(surv, indent=1, ensure_ascii=False))
    print("\n".join(L[:3]))


def coffre():
    surv = json.loads((ICI / "survivantes5.json").read_text())
    S = {s["nom"]: s for s in strategies()}
    m = max(1, len(surv))
    seuil = norm.ppf(1 - 0.05 / m)
    marches = {}
    L = [f"Machine 5, coffre {DEBUT_COFFRE} - 2026 ouvert une fois : {len(surv)} survivante(s), seuil t {seuil:.2f}", ""]
    res = []
    for nom in surv:
        s = S[nom]
        M = marches.setdefault(s["marche"], Marche(s["marche"]))
        d = jouer(s, M, DEBUT_COFFRE, "2026-12-31")
        j = par_jour(d)
        ans = [round(float(j[j.index.year == y].sum()) * 1e4, 1) for y in (2023, 2024, 2025, 2026)]
        t = t_stat(j)
        ok = t >= seuil and sum(x > 0 for x in ans) >= 3
        res.append({"nom": nom, "t": round(t, 2), "annees_pb": ans, "passe": bool(ok)})
        L.append(f"{nom} : t {t:+.2f} ; 2023-2026 (pb) {ans} -> {'PASSE' if ok else 'echoue'}")
    (ICI / "coffre5.txt").write_text("\n".join(L) + "\n")
    (ICI / "coffre5.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("\n".join(L))


if __name__ == "__main__":
    {"exploration": exploration, "coffre": coffre}[sys.argv[1]]()
