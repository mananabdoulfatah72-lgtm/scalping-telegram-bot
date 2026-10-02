#!/usr/bin/env python3
"""Tournoi 9 (README.md) : une troisieme source sur l'or, le petrole, l'euro et le ZN. Exploration 2011-2022 seulement.

Barres journalieres Databento (seance CME complete), rendements continus sans saut d'echeance (meme calcul que
fonds/sources.py futures40), indicateurs sur la serie continue. Decision a la cloture, executee a ce prix (+ 1 tick et
1 $ par ordre) ; un passage d'echeance en position coute un aller-retour. Controle : 1 000 placements au hasard des memes
trades (meme sens, meme duree). Ecrit exploration9.txt, exploration9.csv, survivants9.json.
Lancer depuis ce dossier : python3 tournoi9.py"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

ICI = Path(__file__).resolve().parent
R = ICI.parent
sys.path.insert(0, str(R / "tournoi8"))
from tournoi8 import feries  # noqa: E402

FIN_EXPLORATION = "2022-12-31"
# racine : ($ par point du contrat trade, tick du contrat trade)
CONTRATS = {"GC": (10.0, 0.1), "CL": (100.0, 0.01), "6E": (12500.0, 0.0001), "ZN": (1000.0, 1 / 64)}
NOMS = {"GC": "or (MGC)", "CL": "petrole (MCL)", "6E": "euro (M6E)", "ZN": "obligation 10 ans (ZN)"}
STRATEGIES = ["RSI(2) symetrique", "Double 7 symetrique", "Rebond de 5 jours symetrique", "Fin de mois des obligations"]
ESSAIS = [(k, m) for k in range(3) for m in CONTRATS] + [(3, "ZN")]
N_HASARD, T_MIN, PART_HASARD = 1000, 2.0, 0.95


def charger(racine, jusqu_au=FIN_EXPLORATION):
    """Une ligne par seance : date, cloture du contrat le plus echange, rendement continu (le jour d'un changement de
    contrat : rendement du nouveau contrat depuis la veille), changement de contrat. Rien apres `jusqu_au` n'est lu."""
    d = pd.read_csv(R / "fonds/donnees/futures_1d.csv.gz", parse_dates=["date"])
    d = d[(d["date"] <= pd.Timestamp(jusqu_au)) & d["symbole"].isin([f"{racine}.v.0", f"{racine}.v.1"])]
    c0 = d[d.symbole.str.endswith(".0")].set_index("date")
    c1 = d[d.symbole.str.endswith(".1")].set_index("date").reindex(c0.index)
    meme = (c0["contrat"] == c0["contrat"].shift(1)).to_numpy()
    roule = (c0["contrat"] == c1["contrat"].shift(1)).to_numpy() & ~meme
    r = np.where(meme, c0["c"] / c0["c"].shift(1) - 1, np.where(roule, c0["c"] / c1["c"].shift(1) - 1, np.nan))
    r = np.where(np.abs(r) > 0.5, np.nan, r)
    s = pd.DataFrame({"date": c0.index, "prix": c0["c"].to_numpy(), "r": np.nan_to_num(r), "change": ~meme}).reset_index(drop=True)
    s.loc[0, "change"] = False
    # seances courtes des jours feries de la Bourse (le CME ouvre parfois) : leur rendement est reporte sur la seance
    # suivante, et elles disparaissent (une decision par vraie seance)
    fer = s["date"].isin(list(feries(range(2009, 2028)))).to_numpy()
    r_, ch_ = s["r"].to_numpy().copy(), s["change"].to_numpy().copy()
    for i in np.flatnonzero(fer):
        if i + 1 < len(s):
            r_[i + 1] = (1 + r_[i]) * (1 + r_[i + 1]) - 1
            ch_[i + 1] = ch_[i + 1] or ch_[i]
    s = s.assign(r=r_, change=ch_)[~fer].reset_index(drop=True)
    s["A"] = np.cumprod(1 + s["r"].to_numpy())             # serie continue (indicateurs)
    pt, tick = CONTRATS[racine]
    s.attrs.update(racine=racine, pt=pt, cote=1.0 + tick * pt)   # $ par ordre : 1 $ + 1 tick
    return s


def rsi_wilder(c, n):
    out = np.full(len(c), np.nan)
    d = np.diff(c)
    g, p = np.maximum(d, 0), np.maximum(-d, 0)
    mg, mp = g[:n].mean(), p[:n].mean()
    for i in range(n, len(c)):
        if i > n:
            mg, mp = (mg * (n - 1) + g[i - 1]) / n, (mp * (n - 1) + p[i - 1]) / n
        out[i] = 100.0 if mp == 0 else 100 - 100 / (1 + mg / mp)
    return out


def derniers_du_mois(dates):
    """dernier[k] : la seance qui suit la seance k (prochain jour ouvre hors feries, d'apres le calendrier) est la
    derniere seance de son mois."""
    fer = np.array(sorted(feries(range(2009, 2028))), dtype="datetime64[D]")
    j = np.asarray(pd.DatetimeIndex(dates).values.astype("datetime64[D]"))
    suivant = np.busday_offset(j, 1, roll="forward", holidays=fer)
    apres = np.busday_offset(suivant, 1, roll="forward", holidays=fer)
    return pd.DatetimeIndex(suivant).month != pd.DatetimeIndex(apres).month


def positions(s, k):
    """Position (-1, 0, 1) tenue de la cloture t a la cloture t+1."""
    A, r = s["A"].to_numpy(), s["r"].to_numpy()
    n = len(A)
    pos = np.zeros(n, np.int8)
    if k in (0, 1):
        m200 = pd.Series(A).rolling(200).mean().to_numpy()
        if k == 0:
            rsi, m5 = rsi_wilder(A, 2), pd.Series(A).rolling(5).mean().to_numpy()
            ent_a, sor_a = (A > m200) & (rsi < 10), A > m5
            ent_v, sor_v = (A < m200) & (rsi > 90), A < m5
        else:
            mn, mx = pd.Series(A).rolling(7).min().to_numpy(), pd.Series(A).rolling(7).max().to_numpy()
            ent_a, sor_a = (A > m200) & (A <= mn), A >= mx
            ent_v, sor_v = (A < m200) & (A >= mx), A <= mn
        p = 0
        for t in range(n):
            if p == 1 and sor_a[t]:
                p = 0
            elif p == -1 and sor_v[t]:
                p = 0
            elif p == 0 and ent_a[t]:
                p = 1
            elif p == 0 and ent_v[t]:
                p = -1
            pos[t] = p
    elif k == 2:
        sens, reste = 0, 0
        for t in range(n):
            h = r[max(0, t - 252):t]
            if len(h) >= 200 and t > 0:
                if r[t] <= np.quantile(h, 0.10):
                    sens, reste = 1, 5
                elif r[t] >= np.quantile(h, 0.90):
                    sens, reste = -1, 5
            pos[t] = sens if reste > 0 else 0
            reste = max(0, reste - 1)
    elif k == 3:
        pos[:] = derniers_du_mois(s["date"]).astype(np.int8)
    return pos


def journal(s, pos):
    """Rendement net (fraction du prix) et $ net pour 1 contrat, realises a chaque seance ; $ de chaque trade."""
    r, prix = s["r"].to_numpy(), s["prix"].to_numpy()
    chg_contrat = s["change"].to_numpy()
    pt, cote = s.attrs["pt"], s.attrs["cote"]
    avant = np.r_[0, pos[:-1]].astype(float)
    ordres = np.abs(pos - avant) + 2 * (avant != 0) * chg_contrat          # passage d'echeance en position : aller-retour
    pp = np.r_[prix[0], prix[:-1]]
    dol = avant * r * pp * pt - ordres * cote
    rend = avant * r - ordres * cote / (pp * pt)
    # trades : suites de positions de meme signe
    bords = np.flatnonzero(np.diff(np.r_[0, pos, 0]) != 0)
    trades, debuts, durees, sens = [], [], [], []
    t = 0
    while t < len(bords) - 1:
        a = bords[t]
        if pos[a] != 0:
            b = a
            while b < len(pos) and pos[b] == pos[a]:
                b += 1
            trades.append(dol[a:b + 1].sum() if b < len(pos) else dol[a:].sum())
            debuts.append(a); durees.append(b - a); sens.append(int(pos[a]))
        t += 1
    return rend, dol, np.array(trades), np.array(debuts), np.array(durees, np.int64), np.array(sens, np.int64)


def t_stat(x):
    s = x.std()
    return float(x.mean() / s * np.sqrt(len(x))) if s > 0 else 0.0


@njit(cache=True)
def placer(durees, sens, n, graine):
    """Memes trades (duree, sens) a des departs tires au hasard, sans chevauchement, une seance libre entre deux."""
    np.random.seed(graine)
    pos = np.zeros(n, np.int8)
    for q in np.random.permutation(durees.shape[0]):
        d = durees[q]
        for _ in range(20000):
            a = np.random.randint(1, n - d - 1)
            libre = pos[a - 1] == 0 and pos[a + d] == 0
            if libre:
                for k in range(a, a + d):
                    if pos[k] != 0:
                        libre = False
                        break
            if libre:
                for k in range(a, a + d):
                    pos[k] = sens[q]
                break
    return pos


def mesures(rend, dol, trades, pos):
    cum = np.cumsum(dol)
    pic = np.maximum.accumulate(np.r_[0.0, cum])[1:]
    g, p = trades[trades > 0], trades[trades <= 0]
    return {"t": round(t_stat(rend), 3), "sharpe": round(float(rend.mean() / rend.std() * np.sqrt(252)) if rend.std() > 0 else 0.0, 3),
            "dollars_1_contrat": round(float(dol.sum()), 1), "perte_max_1_contrat": round(float((cum - pic).min()), 1),
            "en_position": round(float((pos != 0).mean()), 3), "trades": int(len(trades)),
            "trades_gagnants": round(float(len(g) / len(trades)), 3) if len(trades) else 0.0,
            "gain_moyen": round(float(g.mean()), 1) if len(g) else 0.0, "perte_moyenne": round(float(p.mean()), 1) if len(p) else 0.0}


def evaluer(s, k, debut="2011-01-01", hasard=True, graine=0):
    pos = positions(s, k)
    garde = (s["date"] >= pd.Timestamp(debut)).to_numpy()
    rend, dol, trades, debuts, durees, sens = journal(s, pos)
    dedans = garde[debuts] if len(debuts) else np.array([], bool)
    x = mesures(rend[garde], dol[garde], trades[dedans], pos[garde])
    if hasard:
        i0 = int(np.argmax(garde))
        sg = s.iloc[i0:].reset_index(drop=True)
        sg.attrs = s.attrs
        d, sn = durees[dedans], sens[dedans]
        ts = np.array([t_stat(journal(sg, placer(d, sn, len(sg), graine + i))[0]) for i in range(N_HASARD)])
        x["hasard_part_battue"] = round(float((ts < x["t"]).mean()), 3)
        x["hasard_t_95"] = round(float(np.quantile(ts, 0.95)), 3)
    return x, pos, rend, dol


def main():
    sortie, survivants = [], []
    donnees = {m: charger(m) for m in CONTRATS}
    for m, s in donnees.items():
        assert s["date"].max() <= pd.Timestamp(FIN_EXPLORATION)
    for k, m in ESSAIS:
        x, *_ = evaluer(donnees[m], k, graine=1000 * (k + 1) + 37 * len(m) + ord(m[0]))
        survit = x["t"] >= T_MIN and x["hasard_part_battue"] >= PART_HASARD
        x.update(strategie=STRATEGIES[k], marche=m, survit=survit)
        sortie.append(x)
        if survit:
            survivants.append({"strategie": k, "marche": m, "nom": f"{STRATEGIES[k]} - {NOMS[m]}"})
        print(f"{STRATEGIES[k]:30s} {NOMS[m]:24s} t {x['t']:+5.2f}  bat le hasard {x['hasard_part_battue']:6.1%} (t 95 % {x['hasard_t_95']:+.2f})"
              f"  {x['trades']:4d} trades  {x['dollars_1_contrat']:+9.0f} $  {'SURVIT' if survit else ''}", flush=True)
    pd.DataFrame(sortie).to_csv(ICI / "exploration9.csv", index=False)
    lignes = ["Exploration 2011-2022 (survie : t >= 2 et t reel au-dessus de 95 % des 1 000 placements au hasard des memes trades).", "",
              f"{'strategie':30s} {'marche':24s} {'t':>6s} {'Sharpe':>6s} {'bat hasard':>10s} {'trades':>6s} {'en pos.':>7s} {'gagnants':>8s}"
              f" {'gain moy':>8s} {'perte moy':>9s} {'total $':>9s} {'perte max $':>11s}"]
    for x in sortie:
        lignes.append(f"{x['strategie']:30s} {NOMS[x['marche']]:24s} {x['t']:+6.2f} {x['sharpe']:+6.2f} {x['hasard_part_battue']:10.1%} {x['trades']:6d}"
                      f" {x['en_position']:7.1%} {x['trades_gagnants']:8.0%} {x['gain_moyen']:+8.0f} {x['perte_moyenne']:+9.0f}"
                      f" {x['dollars_1_contrat']:+9.0f} {x['perte_max_1_contrat']:+11.0f}  {'SURVIT' if x['survit'] else 'elimine'}")
    lignes += ["", f"Survivants : {len(survivants)}"] + [f"  {v['nom']}" for v in survivants]
    (ICI / "exploration9.txt").write_text("\n".join(lignes) + "\n")
    (ICI / "survivants9.json").write_text(json.dumps(survivants, indent=1, ensure_ascii=False))
    print("\n".join(lignes[-(len(survivants) + 1):]))


if __name__ == "__main__":
    main()
