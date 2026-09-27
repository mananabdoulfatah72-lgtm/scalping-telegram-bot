#!/usr/bin/env python3
"""Moteur du fonds : juge chaque source avec les 5 regles du README (version 2 : placebo qui retire
seulement ce que la source pretend savoir, seuil 95 %), puis combine les sources validees a risque
egal, avec 12 % de risque vise pour le portefeuille. Les resultats de la phase 2 (regles v1, ETF)
se reproduisent avec le commit 6426016.

Lancer depuis ce dossier : python3 moteur.py   (ecrit resultats.json)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, norm, skew

import sources as SRC

ICI = Path(__file__).parent
JOURS_AN = 252
RISQUE_SOURCE, RISQUE_FONDS = 0.10, 0.12
PLACEBOS = {"tendance40": 500, "carry40": 300, "momentum40": 300, "valeur40": 300, "zone": 1000, "volgeree": 500,
            "tom": 500, "fomc": 1000}
SEUIL_PLACEBO = 0.95


def au_risque(x, cible, n=252, mini=126, plafond=10.0):
    """Ciblage de volatilite ex ante : x * cible / sigma, sigma = ecart-type des n derniers jours (connu la veille)."""
    vol = x.rolling(n, min_periods=mini).std().shift(1) * np.sqrt(JOURS_AN)
    return (x * (cible / vol).clip(upper=plafond)).dropna()


def sharpe(x):
    return float(x.mean() / x.std() * np.sqrt(JOURS_AN)) if x.std() > 0 else 0.0


def sharpe_degonfle(x, n_essais):
    """Probabilite que le vrai Sharpe soit positif compte tenu du nombre d'essais (Bailey, Lopez de Prado 2014)."""
    sr, t = x.mean() / x.std(), len(x)
    g = 0.5772156649
    sr0 = np.sqrt(1 / t) * ((1 - g) * norm.ppf(1 - 1 / n_essais) + g * norm.ppf(1 - 1 / (n_essais * np.e)))
    denom = np.sqrt(1 - skew(x) * sr + (kurtosis(x, fisher=False) - 1) / 4 * sr ** 2)
    return float(norm.cdf((sr - sr0) * np.sqrt(t - 1) / denom)), float(sr0 * np.sqrt(JOURS_AN))


def baisse_max(x):
    eq = (1 + x).cumprod()
    return float((eq / eq.cummax() - 1).min())


def juger(src, valides, n_essais, rng):
    net, placebo = src.construire()
    x = au_risque(net, RISQUE_SOURCE)
    x = x[x.index >= x.ne(0).idxmax()]
    b = np.linspace(0, len(x), 4).astype(int)
    tiers = [x.iloc[b[i]:b[i + 1]] for i in range(3)]
    apres = x[x.index >= src.publication]
    res = {
        "nom": src.nom, "principe": src.principe, "reference": src.reference, "publication": src.publication,
        "debut": str(x.index[0].date()), "fin": str(x.index[-1].date()), "annees": round(len(x) / JOURS_AN, 1),
        "sharpe": sharpe(x), "rendement_an": float(x.mean() * JOURS_AN), "baisse_max": baisse_max(x),
        "t": float(x.mean() / x.std() * np.sqrt(len(x))),
        "tiers": [{"debut": str(t.index[0].date()), "fin": str(t.index[-1].date()), "sharpe": sharpe(t)} for t in tiers],
        "apres_publication": sharpe(apres) if len(apres) >= 2 * JOURS_AN else None,
        "annees_apres": round(len(apres) / JOURS_AN, 1),
    }
    res["dsr"], res["sharpe_hasard_essais"] = sharpe_degonfle(x, n_essais)
    regles = {
        "1 rentable": res["sharpe"] >= 0.20,
        "2 reguliere": sum(t["sharpe"] > 0 for t in res["tiers"]) >= 2,
        "3 apres publication": res["apres_publication"] is None or res["apres_publication"] > 0,
    }
    if placebo is not None:
        ps = []
        for _ in range(PLACEBOS[src.cle]):
            p = au_risque(placebo(rng), RISQUE_SOURCE)
            ps.append(sharpe(p[(p.index >= x.index[0]) & (p.index <= x.index[-1])]))
        ps = np.array(ps)
        res["placebo_moyen"] = float(ps.mean())
        res["placebo_centile"] = float(np.mean(ps < res["sharpe"]))
        regles["4 pas un hasard"] = res["placebo_centile"] >= SEUIL_PLACEBO
    else:
        res["placebo_centile"] = None
    corr = {k: float(x.corr(v.reindex(x.index))) for k, v in valides.items()}
    res["correlations"] = corr
    regles["5 nouvelle"] = all(abs(c) <= 0.6 for c in corr.values())
    res["regles"] = regles
    res["validee"] = all(regles.values())
    res["annees_detail"] = {int(a): float((1 + g).prod() - 1) for a, g in x.groupby(x.index.year)}
    return res, x


def SRC_au_risque(fabrique):
    x = au_risque(fabrique()[0], RISQUE_SOURCE)
    return x[x.index >= x.ne(0).idxmax()]


def portefeuille(series):
    d = pd.DataFrame(series)
    moyenne = d.mean(axis=1, skipna=True).dropna()          # poids egaux parmi les sources disponibles
    return au_risque(moyenne, RISQUE_FONDS)


def resume(x):
    ans = x.groupby(x.index.year).apply(lambda y: (1 + y).prod() - 1)
    return {"debut": str(x.index[0].date()), "sharpe": sharpe(x), "rendement_an": float(x.mean() * JOURS_AN),
            "risque": float(x.std() * np.sqrt(JOURS_AN)), "baisse_max": baisse_max(x),
            "annees_positives": float((ans > 0).mean()), "pire_annee": float(ans.min()),
            "annees": {int(a): float(v) for a, v in ans.items()}}


def main():
    n_essais = len(pd.read_csv(ICI / "essais.csv"))
    rng = np.random.default_rng(2026)
    valides, tout, jugements = {}, {}, {}
    for src in SRC.SOURCES:
        res, x = juger(src, valides, n_essais, rng)
        jugements[src.cle] = res
        tout[src.cle] = x
        if res["validee"]:
            valides[src.cle] = x
        r = res["regles"]
        print(f"\n{src.nom} ({res['debut']} -> {res['fin']}, {res['annees']} ans) : "
              f"{'VALIDEE' if res['validee'] else 'rejetee'}")
        print(f"  Sharpe {res['sharpe']:+.2f} | gain/an {res['rendement_an']:+.1%} a 10 % de risque | pire baisse {res['baisse_max']:.0%}"
              f" | t {res['t']:+.2f} | Sharpe degonfle {res['dsr']:.0%} (hasard avec {n_essais} essais : {res['sharpe_hasard_essais']:.2f})")
        print("  tiers : " + " | ".join(f"{t['debut'][:4]}-{t['fin'][:4]} {t['sharpe']:+.2f}" for t in res["tiers"])
              + f" | apres publication ({res['annees_apres']} ans) : "
              + (f"{res['apres_publication']:+.2f}" if res["apres_publication"] is not None else "trop court"))
        if res["placebo_centile"] is not None:
            print(f"  placebo : fait mieux que {res['placebo_centile']:.0%} des versions au hasard (placebo moyen {res['placebo_moyen']:+.2f})")
        if res["correlations"]:
            print("  correlations avec les sources validees : " + ", ".join(f"{k} {v:+.2f}" for k, v in res["correlations"].items()))
        print("  regles : " + " | ".join(f"{k} {'oui' if v else 'NON'}" for k, v in r.items()))
    fonds = portefeuille(valides)
    etf = {k: SRC_au_risque(f) for k, f in (("achat", SRC.achat), ("tendance", SRC.tendance))}
    ancien = portefeuille(etf)
    debut = fonds.index[0]
    ancien = ancien[ancien.index >= debut]
    sortie = {"essais": n_essais, "sources": jugements, "validees": list(valides),
              "fonds": resume(fonds), "melange_actuel": resume(ancien),
              "correlations": pd.DataFrame(tout).corr().round(2).to_dict(),
              "courbe_fonds": {str(k.date()): float(v) for k, v in (1 + fonds).cumprod().resample("W-FRI").last().items()}}
    print(f"\nSources validees : {', '.join(valides)}")
    for nom, s in [("Fonds (sources validees)", sortie["fonds"]), ("Melange actuel du robot (ETF)", sortie["melange_actuel"])]:
        print(f"{nom:36s} depuis {s['debut']} : Sharpe {s['sharpe']:.2f} | gain/an {s['rendement_an']:+.1%} | risque {s['risque']:.1%}"
              f" | pire baisse {s['baisse_max']:.0%} | annees positives {s['annees_positives']:.0%} | pire annee {s['pire_annee']:+.1%}")
    print("\nCorrelations entre toutes les sources :")
    print(pd.DataFrame(tout).corr().round(2).to_string())
    (ICI / "resultats.json").write_text(json.dumps(sortie, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
