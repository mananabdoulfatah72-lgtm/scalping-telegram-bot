#!/usr/bin/env python3
"""Le carry sur devises : l'ecart de taux d'interet predit-il le mouvement de la devise ?

Formule testee (video "jsfinancials") : variation de la devise = a + b x (taux etranger - taux US) + bruit.
- Si les marches etaient "parfaits" (parite des taux non couverte), b = -1 : la devise a taux eleve
  baisse exactement de l'ecart de taux, et il n'y a rien a gagner.
- Si b >= 0, acheter la devise a taux eleve rapporte l'ecart de taux (le "carry").

Strategie : chaque debut de mois, acheter les devises dont le taux a 3 mois depasse celui des
Etats-Unis (mois precedent), vendre les autres ; meme risque par devise ; frais compris.
Rendements : ETF de devises moins le taux court US (= rendement d'un futures, carry compris).
Contrats : micro-futures FX de la CME (M6A, M6E, M6B, MJY, MCD, MSF).

Lancer depuis ce dossier : python3 carry.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

import systeme as S

DEVISES = {"Dollar australien": "AU", "Euro": "EZ", "Livre sterling": "GB", "Yen": "JP",
           "Dollar canadien": "CA", "Franc suisse": "CH"}


def charger():
    close, adj = S.charger()
    marches = [m for m in S.MARCHES if m.nom in DEVISES]
    r = S.rendements_futures(close, adj, marches)
    taux = pd.read_csv(Path(__file__).parent / "donnees" / "taux_3m.csv", index_col=0, parse_dates=True)
    taux = taux.ffill(limit=12)                                   # series OCDE parfois en retard de quelques mois
    ecart = pd.DataFrame({nom: taux[p] - taux["US"] for nom, p in DEVISES.items()})   # % par an
    return r, ecart, marches


def strategie(r, ecart, marches, mode="serie", cible=0.10):
    """mode 'serie' : signe de l'ecart de taux (la formule) ; 'croise' : ecart moins la moyenne des 6."""
    signal = ecart.shift(1)                                       # connu au debut du mois
    if mode == "croise":
        signal = signal.sub(signal.mean(axis=1), axis=0)
    signal = np.sign(signal)
    mensuel = signal.reindex(r.index, method="ffill")
    vol = S.volatilite(r)
    n = r.notna().sum(axis=1).replace(0, np.nan)
    pos = mensuel * (cible / vol).div(np.sqrt(n), axis=0)        # meme risque par devise
    periode = r.index.to_period("M").asi8
    reeq = np.r_[True, periode[1:] != periode[:-1]]
    pos = pos.where(pd.Series(reeq, index=r.index), np.nan).ffill().fillna(0)
    cout = np.array([m.cout_pb for m in marches]) / 1e4
    frais = (pos.diff().abs() * cout).sum(axis=1).shift(1).fillna(0)
    return (pos.shift(1) * r.fillna(0)).sum(axis=1) - frais


def regression(r, ecart):
    """Regression de la formule sur des donnees mensuelles : variation de change = a + b x ecart."""
    mensuel = (1 + r.fillna(0)).resample("ME").prod() - 1           # rendement futures (spot + carry)
    ec = ecart.resample("ME").last().shift(1).reindex(mensuel.index)
    spot = mensuel - ec / 1200                                      # on retire le carry du mois
    x, y = ec.stack(), spot.stack()
    ok = x.notna() & y.notna()
    x, y = x[ok] / 100, y[ok] * 12                                  # en fraction par an
    b = np.cov(x, y)[0, 1] / x.var()
    res = y - (y.mean() - b * x.mean()) - b * x
    se = np.sqrt(res.var() / (x.var() * (len(x) - 2)))
    return b, b / se, len(x)


def ligne(x, nom, debut="2007-01-01", fin=None):
    x = x[x.index >= debut]
    if fin:
        x = x[x.index < fin]
    x = x[x.ne(0).idxmax():]
    sh = x.mean() / x.std() * np.sqrt(252)
    cum = (1 + x).cumprod()
    print(f"  {nom:44s} Sharpe {sh:+5.2f} | gain/an {x.mean() * 252:+6.1%} pour un risque de {x.std() * np.sqrt(252):5.1%}"
          f" | pire baisse {(cum / cum.cummax() - 1).min():6.1%}")
    return sh


def main():
    r, ecart, marches = charger()
    b, t, n = regression(r, ecart)
    print(f"Formule : variation de change = a + b x ecart de taux ; b = {b:+.2f} (t = {t:+.2f}, {n} mois-devises)")
    print("  (b = -1 : aucun gain possible ; b >= 0 : le carry rapporte)")
    print("\nStrategie carry sur 6 devises (micro-futures CME), re-equilibrage mensuel :")
    serie = strategie(r, ecart, marches, "serie")
    croise = strategie(r, ecart, marches, "croise")
    ligne(serie, "Signe de l'ecart de taux (la formule), 2007-2026")
    for a, z in [("2007-01-01", "2013-01-01"), ("2013-01-01", "2020-01-01"), ("2020-01-01", None)]:
        ligne(serie, f"   {a[:4]}-{(z or '2027')[:4]}", a, z)
    ligne(croise, "Version croisee (vs moyenne des 6), 2007-2026")
    annees = serie[serie.index >= "2007"].groupby(serie[serie.index >= "2007"].index.year).apply(lambda y: (1 + y).prod() - 1)
    print("  par annee : " + " ".join(f"{a}:{v:+.0%}" for a, v in annees.items()))
    # combinaison avec les systemes deja testes
    rr = S.rendements_futures(*S.charger())
    tendance = S.backtest(rr)[0]
    achat = S.backtest(rr, toujours_acheteur=True)[0]
    d = pd.DataFrame({"carry": serie, "tendance": tendance, "achat": achat})
    d = d[d.index >= "2007-01-01"]
    print("\nCorrelations :")
    print(d.corr().round(2).to_string())
    z = d / d.std()
    ligne((z["tendance"] + z["achat"]) / 2 * 0.01, "Melange 50/50 actuel (tendance + achat)")
    ligne((z["tendance"] + z["achat"] + z["carry"]) / 3 * 0.01, "Melange a 3 : tendance + achat + carry")


if __name__ == "__main__":
    main()
