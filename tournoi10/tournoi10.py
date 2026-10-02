#!/usr/bin/env python3
"""Tournoi 10 (README.md) : 6 nouvelles progressions sur le NQ (l'ES a titre descriptif), exploration 2011-2022.
Moteur de tournoi8/ (decision a 15 h 50, execution a l'ouverture de la minute de decision, position fermee a la
derniere decision d'un contrat, frais 1 $ + 1 tick par ordre). VIX : seulement jusqu'a la cloture de la veille.
Ecrit exploration10.txt et survivants10.json. Lancer depuis ce dossier : python3 tournoi10.py
Le coffre (2023 - septembre 2026) n'est lu que par coffre10.py."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
R = ICI.parent
sys.path.insert(0, str(R / "tournoi8"))
import tournoi8 as T8                                       # noqa: E402

FIN_EXPLORATION = T8.FIN_EXPLORATION
STRATEGIES = ["T1 VIX tendu", "T2 RSI du VIX", "T3 Mardi de rebond", "T4 Nuit apres une fin de seance en baisse",
              "T5 Nouveau plus haut de 252 seances", "T6 Achat pilote par la volatilite"]
DECISION = ("NQ",)
N_HASARD = T8.N_HASARD


# ----------------------------------------------------------------------------- donnees
def charger(nom, jusqu_au=FIN_EXPLORATION):
    """Seances de tournoi8.charger, plus l'ouverture de 9 h 30 (O0) et la cloture de 14 h 49 (C60, une heure avant
    la cloture de 15 h 49 utilisee pour la decision)."""
    s = T8.charger(nom, jusqu_au)
    fichier = T8.MARCHES[nom][0]
    d = pd.read_csv(fichier)
    jour = d["t"].str[:10]
    d = d[(jour >= T8.MARCHES[nom][3]) & (jour <= jusqu_au)]
    t = pd.to_datetime(d["t"])
    m = (t.dt.hour * 60 + t.dt.minute - 570).to_numpy()
    d = d.assign(jour=t.dt.normalize().to_numpy(), m=m)
    d = d[(d["m"] >= 0) & (d["m"] < 390)]
    o0 = d[d["m"] == 0].groupby("jour")["o"].first()
    par_jour = {j: g.set_index("m")["c"] for j, g in d.groupby("jour")}
    attrs = dict(s.attrs)
    s["O0"] = s["date"].map(o0).to_numpy()
    c60 = []
    for j, C in zip(s["date"], s["C"]):
        g = par_jour[j]
        dec_m = g.index.max() - 9                           # minute de decision (derniere minute - 9)
        avant = g[g.index <= dec_m - 61]
        c60.append(float(avant.iloc[-1]) if len(avant) else np.nan)
    s["C60"] = c60
    s.attrs.update(attrs)
    return s


def vix_veille(dates):
    """Pour chaque date de seance : chiffres du VIX de la derniere seance du VIX strictement avant (cloture de la
    veille) : tendu (3 jours de suite a 5 % au-dessus de la moyenne de 10 jours), RSI(2) du VIX, ouverture > cloture
    precedente."""
    v = pd.read_csv(R / "evolution2" / "donnees" / "vix.csv")
    v["date"] = pd.to_datetime(v["DATE"], format="%m/%d/%Y")
    v = v.sort_values("date").reset_index(drop=True)
    c = v["CLOSE"].to_numpy(float)
    m10 = pd.Series(c).rolling(10).mean().to_numpy()
    au_dessus = c >= 1.05 * m10
    tendu = au_dessus & np.r_[False, au_dessus[:-1]] & np.r_[False, False, au_dessus[:-2]]
    rsi = T8.rsi_wilder(c, 2)
    ouv = v["OPEN"].to_numpy(float) > np.r_[np.nan, c[:-1]]
    k = np.searchsorted(v["date"].to_numpy(), pd.DatetimeIndex(dates).to_numpy(), side="left") - 1
    ok = k >= 0
    kk = np.maximum(k, 0)
    return (np.where(ok, tendu[kk], False), np.where(ok, rsi[kk], np.nan), np.where(ok, ouv[kk], False))


# ----------------------------------------------------------------------------- strategies T1, T2, T3, T5 (positions 0/1)
def positions(s, k):
    C = s["C"].to_numpy()
    n = len(C)
    roule = T8.echeances(s)
    meme = np.r_[False, ~roule[:-1]]
    pos = np.zeros(n, np.int8)
    if k in (0, 1):
        m200 = pd.Series(C).rolling(200).mean().to_numpy()
        r2 = T8.rsi_wilder(C, 2)
        tendu, vrsi, vouv = vix_veille(s["date"])
        entree = (C > m200) & (tendu if k == 0 else ((vrsi > 90) & vouv & (r2 < 30)))
        sortie = r2 > 65
        tenu = False
        for t in range(n):
            if tenu and sortie[t]:
                tenu = False
            elif not tenu and entree[t]:
                tenu = True
            if roule[t]:
                tenu = False
            pos[t] = tenu
    elif k == 2:
        lundi = pd.DatetimeIndex(s["date"]).dayofweek == 0
        baisse = meme & (C < np.r_[np.nan, C[:-1]])
        pos[:] = lundi & baisse & ~roule
    elif k == 4:
        reste = 0
        for t in range(n):
            if t >= 252 and C[t] > np.nanmax(C[t - 252:t]):
                reste = 20
            pos[t] = reste > 0 and not roule[t]
            reste = max(0, reste - 1)
    return pos


# ----------------------------------------------------------------------------- T4 : nuits apres une fin de seance en baisse
def nuits(s):
    """Rendements nets par seance (nuit de t a l'ouverture de t+1), $ par nuit, et nuits eligibles / choisies."""
    P, O0, C, C60 = (s[x].to_numpy() for x in ("P", "O0", "C", "C60"))
    pt, cote = s.attrs["pt"], s.attrs["cote"]
    n = len(P)
    roule = T8.echeances(s)
    fin = C / C60 - 1
    eligible = ~roule & np.r_[~np.isnan(O0[1:]), False] & ~np.isnan(fin)
    choisi = np.zeros(n, bool)
    for t in range(n):
        hist = fin[max(0, t - 252):t]
        hist = hist[~np.isnan(hist)]
        if eligible[t] and len(hist) >= 200 and fin[t] <= np.quantile(hist, 0.20):
            choisi[t] = True
    brut = np.r_[O0[1:] / P[:-1] - 1, 0.0]
    pts = np.r_[O0[1:] - P[:-1], 0.0]
    return brut, pts, eligible, choisi, cote, pt, P


def journal_nuits(s, choix):
    brut, pts, eligible, _, cote, pt, P = nuits(s)
    rend = np.where(choix, brut - 2 * cote / P, 0.0)
    dol = np.where(choix, (pts - 2 * cote) * pt, 0.0)
    return np.nan_to_num(rend), np.nan_to_num(dol)


def hasard_nuits(s, graine):
    _, _, eligible, choisi, *_ = nuits(s)
    rng = np.random.default_rng(graine)
    idx = np.flatnonzero(eligible & (np.arange(len(eligible)) >= 252))
    ts = np.empty(N_HASARD)
    for i in range(N_HASARD):
        ch = np.zeros(len(eligible), bool)
        ch[rng.choice(idx, int(choisi.sum()), replace=False)] = True
        ts[i] = T8.t_stat(journal_nuits(s, ch)[0])
    return ts


# ----------------------------------------------------------------------------- T6 : achat pilote par la volatilite
def pilote(s):
    """Rendements nets quotidiens de l'achat pilote (exposition w) et de l'achat permanent simple (w = 1), et w."""
    P = s["P"].to_numpy()
    cote = s.attrs["cote"]
    n = len(P)
    roule = T8.echeances(s)
    r = np.r_[np.nan, P[1:] / P[:-1] - 1]
    r[np.r_[False, roule[:-1]]] = np.nan                    # pas de rendement a cheval sur deux contrats
    var = pd.Series(r).rolling(22, min_periods=18).var().shift(1).to_numpy()     # rendements jusqu'a la veille
    ref = pd.Series(var).expanding(min_periods=252).median().to_numpy()
    w = np.where(np.isnan(ref) | np.isnan(var) | (var <= 0), np.nan, np.minimum(2.0, ref / var))
    out = {}
    for nom, expo in (("pilote", w), ("permanent", np.where(np.isnan(w), np.nan, 1.0))):
        e = np.nan_to_num(expo)
        e = np.where(roule, 0.0, e)                         # sortie a la derniere decision du contrat
        avant = np.r_[0.0, e[:-1]]
        var_p = np.r_[0.0, P[1:] / P[:-1] - 1]
        out[nom] = avant * var_p - np.abs(e - avant) * cote / P
    debut = int(np.argmax(~np.isnan(w)))
    return out["pilote"], out["permanent"], w, debut


def alpha_t(y, x):
    X = np.c_[np.ones(len(x)), x]
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    s2 = e @ e / (len(y) - 2)
    cov = s2 * np.linalg.inv(X.T @ X)
    return float(b[0]), float(b[0] / np.sqrt(cov[0, 0])), float(b[1])


# ----------------------------------------------------------------------------- references pour les correlations
def rsi2_quotidien(s):
    return T8.journal(s, T8.positions(s, 0))[0]


def zone_quotidien(s):
    z = pd.read_csv(R / "filtre_h1" / "trades_zone.csv").groupby("jour")["points"].sum()
    return s["date"].dt.strftime("%Y-%m-%d").map(z).fillna(0.0).to_numpy()


def correl(a, b):
    m = (a != 0) | (b != 0)
    return round(float(np.corrcoef(a[m], b[m])[0, 1]), 3) if m.sum() > 10 and a[m].std() > 0 and b[m].std() > 0 else 0.0


def main():
    lignes, survivants, res = [], [], {}
    for nom in ("NQ", "ES"):
        s = charger(nom)
        assert s["date"].max() <= pd.Timestamp(FIN_EXPLORATION), "le coffre ne doit pas etre lu"
        lignes += ["", f"{nom} ({'decision' if nom in DECISION else 'descriptif'}) : {len(s)} seances du {s['date'].min().date()}"
                   f" au {s['date'].max().date()}, frais {2 * s.attrs['cote']:.3g} points par aller-retour"]
        ref_rsi, ref_zone = rsi2_quotidien(s), zone_quotidien(s) if nom == "NQ" else None
        for k, strat in enumerate(STRATEGIES):
            if k in (0, 1, 2, 4):
                pos = positions(s, k)
                rend, dol, trades, entrees, sorties = T8.journal(s, pos)
                x = T8.mesures(rend, dol, trades, pos)
                ts = T8.hasard(s, entrees, sorties, 3000 + 100 * k + len(nom))
                x["hasard_battu"] = round(float((ts < x["t"]).mean()), 3)
                ok = x["t"] >= T8.T_MIN and x["hasard_battu"] >= T8.PART_HASARD
                desc = (f"t {x['t']:+.2f}, bat le hasard {x['hasard_battu']:.1%}, {x['trades']} trades, en position {x['en_position']:.0%},"
                        f" {x['dollars_1_micro']:+,.0f} $ pour 1 micro, Sharpe {x['sharpe']:.2f}, perte max {x['perte_max_1_micro']:,.0f} $")
            elif k == 3:
                *_, choisi, _, _, _ = nuits(s)
                rend, dol = journal_nuits(s, choisi)
                ts = hasard_nuits(s, 3300 + len(nom))
                t = T8.t_stat(rend)
                cum = np.cumsum(dol)
                x = {"t": round(t, 3), "hasard_battu": round(float((ts < t).mean()), 3), "nuits": int(choisi.sum()),
                     "dollars_1_micro": round(float(dol.sum()), 1), "perte_max_1_micro": round(float((cum - np.maximum.accumulate(np.r_[0, cum])[1:]).min()), 1),
                     "gagnantes": round(float((dol[choisi] > 0).mean()), 3) if choisi.any() else 0.0,
                     "sharpe": round(float(rend.mean() / rend.std() * np.sqrt(252)), 3) if rend.std() > 0 else 0.0}
                ok = x["t"] >= T8.T_MIN and x["hasard_battu"] >= T8.PART_HASARD
                desc = (f"t {x['t']:+.2f}, bat le hasard {x['hasard_battu']:.1%}, {x['nuits']} nuits, {x['gagnantes']:.0%} gagnantes,"
                        f" {x['dollars_1_micro']:+,.0f} $ pour 1 micro, perte max {x['perte_max_1_micro']:,.0f} $")
            else:
                rp, rb, w, debut = pilote(s)
                a, ta, beta = alpha_t(rp[debut:], rb[debut:])
                sh = lambda r: float(r.mean() / r.std() * np.sqrt(252))
                x = {"t_alpha": round(ta, 3), "alpha_annuel": round(a * 252, 4), "beta": round(beta, 3), "sharpe_pilote": round(sh(rp[debut:]), 3),
                     "sharpe_permanent": round(sh(rb[debut:]), 3), "exposition_moyenne": round(float(np.nanmean(w[debut:])), 3)}
                rend = rp
                ok = x["t_alpha"] >= T8.T_MIN
                desc = (f"t de l'alpha {x['t_alpha']:+.2f} (alpha {100 * x['alpha_annuel']:+.1f} % par an, beta {x['beta']:.2f}) ;"
                        f" Sharpe {x['sharpe_pilote']:.2f} contre {x['sharpe_permanent']:.2f} pour l'achat permanent ; exposition moyenne {x['exposition_moyenne']:.2f}")
            x["correlation_rsi2"] = correl(rend, ref_rsi)
            if ref_zone is not None:
                x["correlation_zone"] = correl(rend, ref_zone)
            x["survit"] = bool(ok) if nom in DECISION else None
            res[f"{nom} {strat}"] = x
            corr = f" ; correlation RSI(2) {x['correlation_rsi2']:+.2f}" + (f", zone {x['correlation_zone']:+.2f}" if ref_zone is not None else "")
            verdict = (" -> SURVIT" if ok else " -> elimine") if nom in DECISION else ""
            lignes.append(f"  {strat} : {desc}{corr}{verdict}")
            if ok and nom in DECISION:
                survivants.append(strat)
            print(lignes[-1], flush=True)
    lignes = ["Tournoi 10 : nouvelles progressions sur le NQ, exploration 2011-2022 (le coffre 2023-2026 n'est pas lu)."] + lignes
    lignes += ["", f"Survivants (NQ) : {', '.join(survivants) if survivants else 'aucun'}"]
    (ICI / "exploration10.txt").write_text("\n".join(lignes) + "\n")
    (ICI / "survivants10.json").write_text(json.dumps({"survivants": survivants, "resultats": res}, indent=1, ensure_ascii=False))
    print("\n".join(lignes[-2:]))


if __name__ == "__main__":
    main()
