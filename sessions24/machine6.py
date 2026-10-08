#!/usr/bin/env python3
"""Machine 5, vague 2 (README.md) : 368 strategies sur 13 familles de phenomenes a heure fixe ou d'evenement, 8 marches
HistData en barres de 5 minutes (UTC). Exploration 2012-2022 (G9 : 2013-2022) avec placebos, coffre 2023 - 2026 une
seule fois. Lancer depuis ce dossier : python3 machine6.py exploration | coffre"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

import machine5 as M5
from machine5 import (DEVISES, INDICES, LONDRES, MARCHES, NY, PAS, TOKYO, Marche, benjamini_hochberg, heure_utc,
                      jour_de_trading, t_stat, trades_fenetre)

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "fonds"))
DEBUT, FIN_EXPLO, DEBUT_COFFRE, FIN = "2012-01-01", "2022-12-31", "2023-01-01", "2026-12-31"
TIRAGES_DATES, N_SIGNES, GRAINE = 500, 1000, 6
CALENDRIER = ("G1", "G2", "G3", "G4", "G10", "G13")
REACTION = ("G6", "G7", "G8", "G9", "G11", "G12")
RARES = ("G1", "G2", "G3", "G4", "G5", "G6", "G9", "G10", "G13")
SEPT = DEVISES + ["xauusd"] + INDICES


def usd(c):
    """Sens du trade quand le dollar monte."""
    return 1 if c == "usdjpy" else -1


# ------------------------------------------------------------------ calendriers
def ouvres(debut=DEBUT, fin=FIN):
    return pd.bdate_range(debut, fin)


def fins_de_mois(j, n=1):
    s = pd.Series(j, index=j)
    return pd.DatetimeIndex(s.groupby(j.to_period("M")).tail(n).to_numpy())


def debuts_de_mois(j):
    s = pd.Series(j, index=j)
    return pd.DatetimeIndex(s.groupby(j.to_period("M")).head(1).to_numpy())


def gotobi(debut=DEBUT, fin=FIN):
    """5, 10, 15, 20, 25 et dernier jour du mois ; veille ouvree si samedi ou dimanche."""
    out = set()
    for m in pd.period_range(debut, fin, freq="M"):
        for d in (5, 10, 15, 20, 25, m.days_in_month):
            x = pd.Timestamp(m.year, m.month, d)
            while x.dayofweek >= 5:
                x -= pd.Timedelta(days=1)
            out.add(x)
    return pd.DatetimeIndex(sorted(out))


def troisiemes_vendredis(debut=DEBUT, fin=FIN):
    return pd.date_range(debut, fin, freq="WOM-3FRI")


def fomc(debut="2013-01-01", fin=FIN):
    import fomc as F
    a = pd.DatetimeIndex(sorted(set(F.annonces())))
    return a[(a >= debut) & (a <= fin)]


# ------------------------------------------------------------------ outils de prix
def prix(M, t_utc):
    """Ouverture de la barre qui commence a t_utc (NaN si absente)."""
    i = M.indice(t_utc)
    return np.where(i >= 0, M.O[np.clip(i, 0, M.n - 1)], np.nan)


def cloture_avant(M, t_utc, recul=36):
    """Derniere cloture connue avant t_utc (jusqu'a `recul` barres en arriere)."""
    i = M.indice(t_utc)
    out = np.full(len(i), np.nan)
    for k, x in enumerate(i):
        if x < 0:
            continue
        for y in range(x - 1, max(-1, x - 1 - recul), -1):
            if np.isfinite(M.C[y]):
                out[k] = M.C[y]
                break
    return out


def ouverture_apres(M, t_utc, avance=200):
    """Premiere ouverture connue a partir de t_utc (jusqu'a `avance` barres) : (prix, indice)."""
    i = M.indice(t_utc)
    p, ii = np.full(len(i), np.nan), np.full(len(i), -1)
    for k, x in enumerate(i):
        if x < 0:
            continue
        for y in range(x, min(M.n, x + avance)):
            if np.isfinite(M.O[y]):
                p[k], ii[k] = M.O[y], y
                break
    return p, ii


def trades(M, t_e, t_s, sens, jour_local):
    """Trades d'entree a t_e et sortie a t_s (ouverture des barres), sens par jour (0 : pas de trade).
    Renvoie un DataFrame (jour_local, jour de trading, r, e)."""
    ie, isx = M.indice(t_e), M.indice(t_s)
    sens = np.asarray(sens, float)
    ie = np.where(np.isfinite(sens) & (sens != 0), ie, -1)
    ok = (ie >= 0) & (isx > ie) & (isx < M.n)
    e = np.where(ok, M.O[np.clip(ie, 0, M.n - 1)], np.nan)
    s = np.where(ok, M.O[np.clip(isx, 0, M.n - 1)], np.nan)
    ok &= np.isfinite(e) & np.isfinite(s)
    r = sens[ok] * (s[ok] / e[ok] - 1) - M.cout(e[ok])
    t = M.t0 + isx[ok] * PAS
    return pd.DataFrame({"jour_local": np.asarray(jour_local)[ok], "jour": jour_de_trading(pd.DatetimeIndex(t)),
                         "r": r, "e": e[ok]})


def mtd(M, j, fz, hhmm):
    """Mouvement depuis le debut du mois a l'heure hhmm (fuseau fz) de chaque jour j : contre l'ouverture de la barre de
    16 h (New York) du dernier jour ouvre du mois precedent."""
    fm = fins_de_mois(ouvres("2011-11-01", FIN))
    prec = fm[np.searchsorted(fm, j.to_period("M").start_time) - 1]
    return prix(M, heure_utc(j, fz, hhmm)) / prix(M, heure_utc(pd.DatetimeIndex(prec), NY, "16:00")) - 1


# ------------------------------------------------------------------ les familles (jours de calendrier : tous les jours ouvres)
def g1_g3(M, j, s, spx):
    """G1/G3 sur les jours j : fenetre avant (15-16 h Londres) ou apres (16-17 h), sans condition ou selon le S&P."""
    u = usd(s["marche"])
    if s["condition"] == "sans":
        base = np.full(len(j), u, float)
    else:
        m = mtd(spx, j, LONDRES, "15:00")
        base = np.where(m > 0, -u, np.where(m < 0, u, np.nan))       # S&P en hausse : le dollar baisse avant le fixing
    if s["fenetre"] == "avant":
        return trades(M, heure_utc(j, LONDRES, "15:00"), heure_utc(j, LONDRES, "16:00"), base, j)
    return trades(M, heure_utc(j, LONDRES, "16:00"), heure_utc(j, LONDRES, "17:00"), -base, j)


def g2(M, j, s, spx):
    u = usd(s["marche"])
    h0, h1 = s["fenetre"]
    if s["condition"] == "sans":
        sens = np.full(len(j), -u, float)
    else:
        fm = fins_de_mois(ouvres("2011-10-01", FIN))
        k = np.searchsorted(fm, j.to_period("M").start_time)
        r = prix(spx, heure_utc(pd.DatetimeIndex(fm[k - 1]), NY, "16:00")) / \
            prix(spx, heure_utc(pd.DatetimeIndex(fm[k - 2]), NY, "16:00")) - 1
        sens = np.where(r > 0, u, np.where(r < 0, -u, np.nan))      # inverse de G1 « avant » : retour des flux
    return trades(M, heure_utc(j, LONDRES, h0), heure_utc(j, LONDRES, h1), sens, j)


def g4(M, j, s, spx):
    u = usd(s["marche"])
    h0, h1 = s["fenetre"]
    sens = u if h1 == "09:55" else -u
    return trades(M, heure_utc(j, TOKYO, h0), heure_utc(j, TOKYO, h1), np.full(len(j), sens, float), j)


def g10(M, j, s, spx):
    a = prix(M, heure_utc(j, NY, "09:30"))
    b = prix(M, heure_utc(j, NY, s["formation"]))
    sg = np.sign(b - a) * (1 if s["variante"] == "continuation" else -1)
    return trades(M, heure_utc(j, NY, s["formation"]), heure_utc(j, NY, "15:55"), sg, j)


def g13(M, j, s, spx):
    m = mtd(M, j, NY, s["fenetre"][0])
    return trades(M, heure_utc(j, NY, s["fenetre"][0]), heure_utc(j, NY, "15:55"), -np.sign(m), j)


# ------------------------------------------------------------------ familles de reaction (sens decide par le marche)
def seuil_glissant(x, n, q, mini):
    """Quantile q de |x| sur les n valeurs valides precedentes (sans la valeur du jour)."""
    a = pd.Series(np.abs(x))
    return a.shift(1).rolling(n, min_periods=mini).quantile(q).to_numpy()


def g6(M, s):
    j = ouvres(DEBUT, FIN)
    j = j[j.dayofweek == 2]
    r = prix(M, heure_utc(j, NY, "10:35")) / prix(M, heure_utc(j, NY, "10:30")) - 1
    sg = np.sign(r) * (1 if s["variante"] == "continuation" else -1)
    if s["condition"] == "grand":
        sg = np.where(np.abs(r) >= seuil_glissant(r, 26, 0.5, 13), sg, 0)
    return trades(M, heure_utc(j, NY, "10:35"), heure_utc(j, NY, s["sortie"]), sg, j)


def g7_g8(M, s):
    j = ouvres(DEBUT, FIN)
    h0, h1 = s["reaction"]
    r = prix(M, heure_utc(j, NY, h1)) / prix(M, heure_utc(j, NY, h0)) - 1
    choc = np.abs(r) >= seuil_glissant(r, 60, s["q"], 40)
    sg = np.where(choc, np.sign(r) * (1 if s["variante"] == "continuation" else -1), 0)
    return trades(M, heure_utc(j, NY, h1), heure_utc(j, NY, s["sortie"]), sg, j)


def g9(M, s):
    j = fomc()
    r = prix(M, heure_utc(j, NY, s["reaction"])) / prix(M, heure_utc(j, NY, "14:00")) - 1
    sg = np.sign(r) * (1 if s["variante"] == "continuation" else -1)
    return trades(M, heure_utc(j, NY, s["reaction"]), heure_utc(j, NY, s["sortie"]), sg, j)


def g11(M, s):
    v = pd.date_range(DEBUT, FIN, freq="W-FRI")
    t_v = heure_utc(v, NY, "17:00")
    c = cloture_avant(M, t_v)
    o, io = ouverture_apres(M, heure_utc(v + pd.Timedelta(days=2), NY, "15:00"))
    g = o / c - 1
    lundi = v + pd.Timedelta(days=3)
    sg = np.sign(g) * (1 if s["variante"] == "continuation" else -1)
    if s["condition"] == "grand":
        sg = np.where(np.abs(g) > seuil_glissant(g, 26, 0.5, 13), sg, 0)
    t_e = pd.DatetimeIndex(M.t0 + np.where(io >= 0, io, 0) * PAS)
    t_e = t_e.where(io >= 0)
    return trades(M, t_e, heure_utc(lundi, NY, s["sortie"]), sg, lundi)


def g12(M, s):
    v = pd.date_range(DEBUT, FIN, freq="W-FRI")
    w = prix(M, heure_utc(v, NY, s["debut"])) / prix(M, heure_utc(v - pd.Timedelta(days=7), NY, "16:00")) - 1
    sg = np.sign(w) * (1 if s["variante"] == "continuation" else -1)
    return trades(M, heure_utc(v, NY, s["debut"]), heure_utc(v, NY, "15:55"), sg, v)


def g5(M, s, decalage=0):
    """Fixings de l'or, tous les jours ouvres ; decalage (en barres) pour le placebo d'heure."""
    j = ouvres(DEBUT, FIN)
    fix = heure_utc(j, LONDRES, s["fixing"])
    d = pd.Timedelta(minutes=s["minutes"])
    dec = pd.Timedelta(minutes=5 * decalage)
    morceaux = []
    if s["cote"] in ("avant", "les deux"):
        morceaux.append(trades(M, fix - d + dec, fix + dec, np.full(len(j), -1.0), j))
    if s["cote"] in ("apres", "les deux"):
        morceaux.append(trades(M, fix + dec, fix + d + dec, np.full(len(j), 1.0), j))
    return pd.concat(morceaux)


# ------------------------------------------------------------------ les 368 strategies
def strategies():
    S = []
    for c in DEVISES:
        for f in ("avant", "apres"):
            for cond in ("sans", "S&P"):
                for n in (1, 2):
                    S.append(dict(nom=f"G1 fin de mois {f} fixing {cond} {n} jour(s) {c}", famille="G1", marche=c,
                                  fenetre=f, condition=cond, n=n))
        for fen in (("08:00", "12:00"), ("15:00", "16:00")):
            for cond in ("sans", "S&P"):
                S.append(dict(nom=f"G2 debut de mois {fen[0]}-{fen[1]} {cond} {c}", famille="G2", marche=c, fenetre=fen,
                              condition=cond))
        for f in ("avant", "apres"):
            for cond in ("sans", "S&P"):
                S.append(dict(nom=f"G3 fin de trimestre {f} fixing {cond} {c}", famille="G3", marche=c, fenetre=f,
                              condition=cond, n=1))
        for fen in (("07:00", "09:55"), ("08:00", "09:55"), ("09:00", "09:55"), ("09:55", "11:00"), ("09:55", "12:00")):
            S.append(dict(nom=f"G4 gotobi {fen[0]}-{fen[1]} {c}", famille="G4", marche=c, fenetre=fen))
    for fx in ("10:30", "15:00"):
        for cote in ("avant", "apres", "les deux"):
            for mn in (30, 60):
                S.append(dict(nom=f"G5 or fixing {fx} {cote} {mn} min", famille="G5", marche="xauusd", fixing=fx,
                              cote=cote, minutes=mn))
    for so in ("11:00", "12:00", "14:30"):
        for v in ("continuation", "retournement"):
            for cond in ("toujours", "grand"):
                S.append(dict(nom=f"G6 petrole EIA sortie {so} {v} {cond}", famille="G6", marche="lightcmdusd", sortie=so,
                              variante=v, condition=cond))
    for c in MARCHES:
        for v in ("continuation", "retournement"):
            for so in ("09:30", "11:00"):
                for q in (0.8, 0.9):
                    S.append(dict(nom=f"G7 choc 8 h 30 {v} sortie {so} centile {int(q * 100)} {c}", famille="G7", marche=c,
                                  reaction=("08:30", "08:35"), variante=v, sortie=so, q=q))
            for so in ("11:00", "12:00"):
                S.append(dict(nom=f"G8 choc 10 h {v} sortie {so} {c}", famille="G8", marche=c, reaction=("10:00", "10:05"),
                              variante=v, sortie=so, q=0.9))
            for rea in ("14:05", "14:15"):
                for so in ("15:00", "15:55"):
                    S.append(dict(nom=f"G9 Fed reaction 14:00-{rea} {v} sortie {so} {c}", famille="G9", marche=c,
                                  reaction=rea, variante=v, sortie=so))
    for c in INDICES:
        for form in ("11:00", "12:00"):
            for v in ("retournement", "continuation"):
                S.append(dict(nom=f"G10 echeance options 9:30-{form} {v} {c}", famille="G10", marche=c, formation=form,
                              variante=v))
        for n in (1, 2):
            for fen in (("15:00", "15:55"), ("15:30", "15:55")):
                S.append(dict(nom=f"G13 fin de mois indice {n} jour(s) {fen[0]}-{fen[1]} {c}", famille="G13", marche=c,
                              n=n, fenetre=fen))
    for c in SEPT:
        for v in ("comblement", "continuation"):
            for so in ("03:00", "09:30"):
                for cond in ("tout", "grand"):
                    S.append(dict(nom=f"G11 ecart du week-end {v} sortie lundi {so} {cond} {c}", famille="G11", marche=c,
                                  variante="continuation" if v == "continuation" else "retournement", sortie=so,
                                  condition=cond))
        for v in ("retournement", "continuation"):
            for deb in ("12:00", "14:00"):
                S.append(dict(nom=f"G12 vendredi {deb}-15:55 {v} {c}", famille="G12", marche=c, variante=v, debut=deb))
    return S


def jours_evenement(s):
    """Jours de l'evenement (fuseau local de la famille) pour les familles de calendrier."""
    j = ouvres(DEBUT, FIN)
    f = s["famille"]
    if f == "G1":
        return fins_de_mois(j, s["n"])
    if f == "G3":
        x = fins_de_mois(j, 1)
        return x[x.month.isin([3, 6, 9, 12])]
    if f == "G2":
        return debuts_de_mois(j)
    if f == "G4":
        return gotobi()
    if f == "G10":
        return troisiemes_vendredis()
    if f == "G13":
        return fins_de_mois(j, s["n"])
    raise ValueError(f)


FONCTIONS = {"G1": g1_g3, "G3": g1_g3, "G2": g2, "G4": g4, "G10": g10, "G13": g13}


def tous_les_jours(s, M, spx):
    """Pour une famille de calendrier : la regle appliquee a TOUS les jours ouvres (sert au reel et au placebo)."""
    return FONCTIONS[s["famille"]](M, ouvres(DEBUT, FIN), s, spx)


def jouer(s, M, spx):
    f = s["famille"]
    if f in FONCTIONS:
        d = tous_les_jours(s, M, spx)
        return d[d["jour_local"].isin(jours_evenement(s))]
    return {"G5": g5, "G6": g6, "G7": g7_g8, "G8": g7_g8, "G9": g9, "G11": g11, "G12": g12}[f](M, s)


def periode(d, debut, fin):
    return d[(d["jour"] >= pd.Timestamp(debut)) & (d["jour"] <= pd.Timestamp(fin))]


def par_jour(d):
    return d.groupby("jour")["r"].sum() if len(d) else pd.Series(dtype=float)


def placebo(s, M, spx, d, debut, fin):
    t_reel = t_stat(par_jour(d))
    f = s["famille"]
    rng = np.random.default_rng(GRAINE)
    if f in FONCTIONS:
        tous = periode(tous_les_jours(s, M, spx), debut, fin)
        ev = set(jours_evenement(s))
        autres = tous[~tous["jour_local"].isin(ev)]
        jl = autres["jour_local"].unique()
        n = d["jour_local"].nunique()
        ts = []
        for _ in range(TIRAGES_DATES):
            pick = rng.choice(jl, size=min(n, len(jl)), replace=False)
            ts.append(t_stat(par_jour(autres[autres["jour_local"].isin(pick)])))
        ts = np.array(ts)
    elif f == "G5":
        ts = np.array([t_stat(par_jour(periode(g5(M, s, k), debut, fin))) for k in range(-144, 144) if abs(k) * 5 > 120])
    else:
        r = d["r"].to_numpy()
        cout = np.array([M.cout(e) for e in d["e"].to_numpy()])
        brut = r + cout
        jours = pd.factorize(d["jour"])[0]
        ts = np.empty(N_SIGNES)
        for i in range(N_SIGNES):
            sg = rng.choice([-1.0, 1.0], len(r))
            ts[i] = t_stat(np.bincount(jours, sg * brut - cout))
    return float((ts >= t_reel).mean()), len(ts)


def sous_periodes(s):
    return [(2013, 2015), (2016, 2019), (2020, 2022)] if s["famille"] == "G9" else [(2012, 2015), (2016, 2019), (2020, 2022)]


def bilan(d, M, s):
    j = par_jour(d)
    an = j.index.year
    dol = d["r"].to_numpy() * np.array([M.notionnel(e) for e in d["e"].to_numpy()])
    return {"t": round(t_stat(j), 2), "jours": int(len(j)), "trades": int(len(d)),
            "pb_par_jour": round(float(j.mean()) * 1e4, 2) if len(j) else 0.0,
            "dollars_1_contrat": round(float(dol.sum()), 0),
            "sous_periodes": [round(float(j[(an >= a) & (an <= b)].sum()) * 1e4, 1) for a, b in sous_periodes(s)]}


def exploration():
    S = strategies()
    assert len(S) == 368, len(S)
    marches = {c: Marche(c) for c in MARCHES}
    spx = marches["usa500idxusd"]
    res = []
    for s in S:
        M = marches[s["marche"]]
        debut = "2013-01-01" if s["famille"] == "G9" else DEBUT
        d = periode(jouer(s, M, spx), debut, FIN_EXPLO)
        b = bilan(d, M, s)
        b.update(nom=s["nom"], famille=s["famille"])
        mini = 60 if s["famille"] in RARES else 200
        if b["jours"] < mini:
            b.update(p=None, placebos=0, testable=False)
            print(f"{s['nom']} : NON TESTABLE ({b['jours']} jours)", flush=True)
        else:
            p, n = placebo(s, M, spx, d, debut, FIN_EXPLO)
            b.update(p=p, placebos=n, testable=True)
            print(f"{s['nom']} : t {b['t']:+.2f}, p {p:.3f}, {b['jours']} jours", flush=True)
        res.append(b)
    jug = [r for r in res if r["testable"]]
    bh = benjamini_hochberg([r["p"] for r in jug])
    for r in res:
        r["bh"], r["survivante"] = False, False
    surv = []
    for r, g in zip(jug, bh):
        r["bh"] = bool(g)
        r["survivante"] = bool(r["t"] >= 2 and r["p"] <= 0.05 and sum(x > 0 for x in r["sous_periodes"]) >= 2 and g)
        if r["survivante"]:
            surv.append(r["nom"])
    L = [f"Machine 5 vague 2, exploration 2012 - 2022 (G9 : 2013 - 2022) : {len(S)} strategies, {len(jug)} testables ;"
         f" survivantes : {len(surv)}", "",
         "strategie | t | p placebo | BH 10 % | sous-periodes (pb) | jours | pb par jour | $ pour 1 contrat | survivante"]
    for r in sorted(res, key=lambda x: -x["t"]):
        if not r["testable"]:
            L.append(f"{r['nom']} | non testable ({r['jours']} jours)")
            continue
        L.append(f"{r['nom']} | {r['t']:+.2f} | {r['p']:.3f} | {'oui' if r['bh'] else 'non'} | "
                 f"{' / '.join(f'{x:+.1f}' for x in r['sous_periodes'])} | {r['jours']} | {r['pb_par_jour']:+.2f} |"
                 f" {r['dollars_1_contrat']:+,.0f} | {'OUI' if r['survivante'] else ''}")
    (ICI / "exploration6.txt").write_text("\n".join(L) + "\n")
    (ICI / "exploration6.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    (ICI / "survivantes6.json").write_text(json.dumps(surv, indent=1, ensure_ascii=False))
    print("\n".join(L[:2]))


def coffre():
    surv = json.loads((ICI / "survivantes6.json").read_text())
    S = {s["nom"]: s for s in strategies()}
    m = max(1, len(surv))
    seuil = norm.ppf(1 - 0.05 / m)
    marches = {c: Marche(c) for c in MARCHES}
    L = [f"Machine 5 vague 2, coffre 2023 - 2026 ouvert une fois : {len(surv)} survivante(s), seuil t {seuil:.2f}", ""]
    res = []
    for nom in surv:
        s = S[nom]
        M = marches[s["marche"]]
        d = periode(jouer(s, M, marches["usa500idxusd"]), DEBUT_COFFRE, FIN)
        j = par_jour(d)
        ans = [round(float(j[j.index.year == y].sum()) * 1e4, 1) for y in (2023, 2024, 2025, 2026)]
        t = t_stat(j)
        complet = s["marche"] != "lightcmdusd"
        ok = complet and t >= seuil and sum(x > 0 for x in ans) >= 3
        res.append({"nom": nom, "t": round(t, 2), "annees_pb": ans, "passe": bool(ok), "coffre_complet": complet})
        L.append(f"{nom} : t {t:+.2f} ; 2023-2026 (pb) {ans} -> {'PASSE' if ok else ('coffre incomplet' if not complet else 'echoue')}")
    (ICI / "coffre6.txt").write_text("\n".join(L) + "\n")
    (ICI / "coffre6.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("\n".join(L))


if __name__ == "__main__":
    {"exploration": exploration, "coffre": coffre}[sys.argv[1]]()
