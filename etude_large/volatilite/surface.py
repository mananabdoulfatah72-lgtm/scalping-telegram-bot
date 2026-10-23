#!/usr/bin/env python3
"""Surface de volatilite implicite du QQQ et du SPY, a partir des chaines d'options gratuites de Yahoo (une photo, pas
d'historique : donnees_libres/options/, telechargees par .github/workflows/donnees-options.yml).

Pour chaque echeance (7 a 400 jours) :
- prix median entre l'achat et la vente (cotations a 0 ou fourchette trop large retirees) ;
- forward F par la parite call-put sur les 5 prix d'exercice les plus proches du cours (dividendes compris) ;
- volatilite implicite recalculee (Black sur le forward, actualisation au taux a 13 semaines ^IRX) sur les options
  hors de la monnaie seulement (puts sous F, calls au-dessus) ;
- ajustement SVI de la variance totale w(k) = a + b (rho (k - m) + racine((k - m)^2 + s^2)), k = ln(K / F).
Ecrit surface.json et surface.html (surface_page.html avec les donnees inserees). Description, pas une regle testee.

Lancer depuis la racine : python3 etude_large/volatilite/surface.py"""
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.optimize import brentq, least_squares  # noqa: E402
from scipy.stats import norm  # noqa: E402

ICI = Path(__file__).resolve().parent
OPT = ICI.parent.parent / "donnees_libres" / "options"
YAHOO = ICI.parent.parent / "donnees_libres" / "yahoo" / "jour"
VXN = ICI.parent.parent / "donnees_libres" / "vxn" / "cboe.csv.gz"
GRILLE_M = np.round(np.arange(0.80, 1.1201, 0.01), 2)      # prix d'exercice en part du cours
JOURS = (7, 400)


def black(F, K, T, s, call):
    v = s * np.sqrt(T)
    d1 = np.log(F / K) / v + v / 2
    d2 = d1 - v
    return F * norm.cdf(d1) - K * norm.cdf(d2) if call else K * norm.cdf(-d2) - F * norm.cdf(-d1)


def vol_impl(p, F, K, T, call):
    intr = max(F - K, 0.0) if call else max(K - F, 0.0)
    if not p > intr + 1e-4:
        return np.nan
    try:
        return brentq(lambda s: black(F, K, T, s, call) - p, 1e-3, 5.0, xtol=1e-7)
    except ValueError:
        return np.nan


def svi(p, k):
    a, b, rho, m, s = p
    return a + b * (rho * (k - m) + np.sqrt((k - m) ** 2 + s * s))


def ajuster(k, w):
    p0 = [max(w.min() * 0.8, 1e-5), 0.1, -0.5, 0.0, 0.1]
    r = least_squares(lambda p: svi(p, k) - w, p0, bounds=([-1, 1e-4, -0.999, -1, 1e-3], [1, 5, 0.999, 1, 2]))
    return r.x, float(np.sqrt(np.mean(r.fun ** 2)))


def une(sj, date, r):
    d = pd.read_csv(OPT / f"{sj}.csv.gz")
    cours = pd.read_csv(OPT / f"{sj}_cours.csv.gz")
    S = float(cours["c"].iloc[-1])
    d["mid"] = (d["bid"] + d["ask"]) / 2
    ok = (d["bid"] > 0) & (d["ask"] >= d["bid"]) & ((d["ask"] - d["bid"]) <= 0.6 * d["mid"]) & (d["mid"] >= 0.05)
    d = d[ok].copy()

    def forward(g, T, ref):
        D = np.exp(-r * T)
        c = g[g["type"] == "C"].set_index("strike")["mid"]
        p = g[g["type"] == "P"].set_index("strike")["mid"]
        communs = c.index.intersection(p.index)
        if len(communs) < 3:
            return np.nan, D, c, p
        proches = communs[np.argsort(np.abs(communs - ref))[:5]]
        return float(np.median([K + (c[K] - p[K]) / D for K in proches])), D, c, p

    source = "cloture Yahoo"
    if np.isnan(S):
        # cloture du jour absente chez Yahoo : cours tire de la parite call-put de l'echeance la plus proche
        ref = float(cours["c"].dropna().iloc[-1])
        e1 = min((e for e in d["echeance"].unique() if (pd.Timestamp(e) - date).days >= 1),
                 key=lambda e: pd.Timestamp(e))
        T1 = (pd.Timestamp(e1) - date).days / 365.0
        F1 = forward(d[d["echeance"] == e1], T1, ref)[0]
        S = F1 * np.exp(-r * T1)
        source = f"parite call-put de l'echeance du {e1}"
    lignes, points = [], []
    for e, g in d.groupby("echeance"):
        jours = (pd.Timestamp(e) - date).days
        if not JOURS[0] <= jours <= JOURS[1]:
            continue
        T = jours / 365.0
        F, D, c, p = forward(g, T, S)
        if np.isnan(F):
            continue
        hors = pd.concat([p[p.index < F].rename("prix").to_frame().assign(call=False),
                          c[c.index >= F].rename("prix").to_frame().assign(call=True)])
        hors = hors[(hors.index / F >= 0.6) & (hors.index / F <= 1.35)]
        iv = np.array([vol_impl(pr / D, F, K, T, cl) for K, pr, cl in zip(hors.index, hors["prix"], hors["call"])])
        K = hors.index.values.astype(float)
        m = ~np.isnan(iv) & (iv > 0.03) & (iv < 2.0)
        if m.sum() < 8:
            continue
        k, w = np.log(K[m] / F), iv[m] ** 2 * T
        par, err = ajuster(k, w)
        kg = np.log(GRILLE_M * S / F)
        wg = svi(par, kg)
        if np.any(wg <= 0) or err > 0.25 * np.median(w):
            continue
        ivg = np.sqrt(wg / T)
        lignes.append(dict(date=e, jours=int(jours), F=round(F, 3), n=int(m.sum()), iv=[round(x, 4) for x in ivg],
                           m_min=round(float(K[m].min() / S), 3), m_max=round(float(K[m].max() / S), 3),
                           atm=round(float(np.sqrt(svi(par, np.log(S / F)) / T)), 4), erreur=round(err / np.median(w), 4)))
        for Ki, vi in zip(K[m], iv[m]):
            if GRILLE_M[0] - 0.005 <= Ki / S <= GRILLE_M[-1] + 0.005:
                points.append([round(float(Ki / S), 4), int(jours), round(float(vi), 4)])
    return dict(spot=round(S, 2), source_cours=source, echeances=lignes, points=points)


def main():
    irx = pd.read_csv(OPT / "irx.csv.gz")
    r = float(irx["c"].iloc[-1]) / 100
    cours = pd.read_csv(OPT / "QQQ_cours.csv.gz")
    date = pd.Timestamp(cours["t"].iloc[-1])
    out = dict(date=str(date.date()), taux=round(r, 4), grille_m=GRILLE_M.tolist(), sj={})
    for sj in ("QQQ", "SPY"):
        out["sj"][sj] = une(sj, date, r)
        e = out["sj"][sj]["echeances"]
        print(f"{sj} : cours {out['sj'][sj]['spot']}, {len(e)} echeances ({e[0]['jours']} a {e[-1]['jours']} jours), "
              f"{len(out['sj'][sj]['points'])} cotations ; ATM 30 j environ "
              f"{min(e, key=lambda x: abs(x['jours'] - 30))['atm']:.3f} ; erreur SVI mediane "
              f"{np.median([x['erreur'] for x in e]):.3f}")
    vx = pd.read_csv(VXN)
    vi = pd.read_csv(YAHOO / "VIX.csv.gz")
    out["vxn"] = [str(vx["t"].iloc[-1]), round(float(vx["c"].iloc[-1]), 2)]
    out["vix"] = [str(vi["t"].iloc[-1]), round(float(vi["c"].iloc[-1]), 2)]
    texte = json.dumps(out, separators=(",", ":"))
    (ICI / "surface.json").write_text(texte + "\n")
    page = (ICI / "surface_page.html").read_text()
    assert "/*DONNEES*/null" in page
    (ICI / "surface.html").write_text(page.replace("/*DONNEES*/null", texte))


if __name__ == "__main__":
    main()
