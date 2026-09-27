#!/usr/bin/env python3
"""Reproduit les resultats du systeme de tendance multi-marches (voir README.md).

Lancer depuis ce dossier : python3 rapport.py   (environ 1 minute)
"""
import numpy as np
import pandas as pd

import challenge_phidias as P
import systeme as S


def ligne(net, nom, debut="2007-01-01", fin=None):
    x = net[net.index >= debut]
    if fin:
        x = x[x.index < fin]
    st = S.stats(x, nom)
    print(f"  {nom:44s} Sharpe {st['sharpe']:5.2f} | gain/an {st['rendement_an']:6.1%} pour un risque de "
          f"{st['vol_an']:5.1%} | pire baisse {st['pire_baisse']:6.1%} | annees positives {st['annees_positives']:4.0%}")


def main():
    close, adj = S.charger()
    r = S.rendements_futures(close, adj)
    base, pos, _ = S.backtest(r)
    fams = ["actions", "obligations", "devises", "metaux", "energie", "crypto"]

    print("1. Systeme ideal (19 marches, positions divisibles a l'infini)")
    ligne(base, "2007-2026")
    for a, b in [("2007-01-01", "2013-01-01"), ("2013-01-01", "2020-01-01"), ("2020-01-01", None), ("2023-01-01", None)]:
        ligne(base, f"{a[:4]}-{(b or '2027')[:4]}", a, b)

    print("\n2. Robustesse (memes donnees, reglages differents)")
    for v in [(16,), (32,), (64,), (8, 16, 32), (32, 64)]:
        ligne(S.backtest(r, vitesses=v)[0], f"vitesses {v}")
    ligne(S.backtest(r, frequence="M")[0], "re-equilibrage mensuel")
    ligne(S.backtest(r, multi_couts=3)[0], "couts x3")
    for fam in fams:
        ligne(S.backtest(r, exclure=(fam,))[0], f"sans {fam}")
    crypto = S.backtest(r, exclure=tuple(f for f in fams if f != "crypto"))[0]
    ligne(crypto, "BTC + ETH seuls, depuis 2021", "2021-01-01")

    print("\n3. Compte 50K : les contrats micro d'aujourd'hui")
    cv = S.valeur_contrat(close).iloc[-1]
    vol = r[r.index >= "2016"].std() * np.sqrt(S.JOURS_AN)
    for m in S.MARCHES:
        print(f"  {m.micro:4s} {m.nom:18s} 1 contrat = {cv[m.nom]:8,.0f} $ | risque/an {cv[m.nom] * vol[m.nom]:7,.0f} $")
    ms = P.univers(False)
    r14 = S.rendements_futures(close, adj, ms)
    ligne(S.backtest(r14, marches=ms)[0], "14 marches sans gros contrats", "2008-01-01")

    print("\n4. Phidias Premium 50K, challenge demarre chaque semaine depuis 2008 (vrais prix)")
    P.main()


if __name__ == "__main__":
    main()
