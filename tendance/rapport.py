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

    print("\n4. Est-ce vraiment la tendance ? Comparaison et test du hasard (2007-2026)")
    reel = base[base.index >= "2007-01-01"]
    origine = S.prevision
    S.prevision = lambda r, vitesses=(16, 32, 64): pd.DataFrame(10.0, index=r.index, columns=r.columns).where(r.notna())
    achat = S.backtest(r)[0]
    S.prevision = origine
    achat = achat[achat.index >= "2007-01-01"]
    melange = (reel / reel.std() + achat / achat.std()) / 2
    melange *= 0.20 / (melange.std() * np.sqrt(S.JOURS_AN))     # ramene a 20 % de risque par an
    ligne(achat, "acheter tout, tout le temps")
    ligne(melange, "melange 50/50 tendance + acheter tout")
    print(f"  correlation tendance / acheter tout : {reel.corr(achat):.2f}")
    R, Q = r.fillna(0).values, pos.values
    i0 = np.searchsorted(r.index, pd.Timestamp("2007-01-01"))
    rng = np.random.default_rng(1)
    placebos = []
    for _ in range(1000):   # positions decalees au hasard dans le temps, marche par marche
        Z = np.column_stack([np.roll(Q[:, j], rng.integers(252, len(R) - 252)) for j in range(Q.shape[1])])
        g = (Z[:-1] * R[1:]).sum(axis=1)[i0:]
        placebos.append(g.mean() / g.std() * np.sqrt(S.JOURS_AN))
    placebos = np.array(placebos)
    vrai = reel.mean() / reel.std() * np.sqrt(S.JOURS_AN)
    print(f"  test du hasard : placebos en moyenne {placebos.mean():.2f}, {np.mean(placebos >= vrai):.1%} font aussi bien que {vrai:.2f}")

    print("\n5. Phidias Premium 50K, challenge demarre chaque semaine depuis 2008 (vrais prix)")
    P.main()


if __name__ == "__main__":
    main()
