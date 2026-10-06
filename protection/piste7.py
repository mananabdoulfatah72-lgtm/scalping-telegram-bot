#!/usr/bin/env python3
"""Piste 7 (README.md) : le melange 50/50 du robot de tendance (moitie tendance, moitie achat permanent ; M100 a la
taille du robot, M30 a l'echelle 0,3) ajoute au bot (zone non filtree + RSI(2), 1 MNQ chacun), exactement comme la
piste 6 (gain du jour ajoute a la cloture). Jugement sur DayTraders Trail 50K ; descriptif : S2F 50K + plafond 500 $.
Ecrit piste7.txt et piste7.json. Lancer depuis ce dossier : python3 piste7.py"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import piste6 as P6
import protection as P

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "tendance"))


def melange(jours, echelle):
    """Gain du jour du melange du robot (contrats entiers pour 50 000 $, 12 %/an) a l'echelle donnee de sa grille,
    recu le jour t+1 pour les positions fixees le vendredi (meme calcul que piste6.tendance)."""
    import challenge_phidias as CP
    import systeme as S
    close, adj = S.charger()
    r = S.rendements_futures(close, adj, S.MARCHES)
    pos, _ = S.positions_melange(r, marches=S.MARCHES)
    cv = S.valeur_contrat(close, S.MARCHES).iloc[-1]
    periode = r.index.to_period("W-FRI").asi8
    semaines = np.where(np.r_[periode[:-1] != periode[1:], True])[0]
    grille = S.contrats_optimises(r, pos, cv, CP.CAPITAL, 0.12, CP.ECHELLES, semaines)
    e = float(CP.ECHELLES[int(np.argmin(np.abs(CP.ECHELLES - echelle)))])
    N = grille[e].values
    R = r.fillna(0).values
    cvv = cv[r.columns].values
    idx = {t: j for j, t in enumerate(semaines)}
    n = np.zeros(R.shape[1])
    gain = np.zeros(len(R))
    for t in range(len(R) - 1):
        if t in idx and t >= 260:
            cible = N[idx[t]]
            gain[t + 1] -= np.abs(cible - n).sum() * CP.FRAIS
            n = cible
        gain[t + 1] += float((n * cvv * R[t + 1]).sum())
    s = pd.Series(gain, index=pd.DatetimeIndex(r.index).normalize()).groupby(level=0).sum()
    return s.reindex(pd.DatetimeIndex(jours)).fillna(0.0).to_numpy()


def main():
    jours, O, H, L, C, Z, dec, voulu, ouvert = P.donnees()
    nj = len(jours)
    dates = pd.DatetimeIndex(jours)
    zt = P.tableaux_zone(Z, nj, np.ones(len(Z), bool))
    a = (O, H, L, C) + tuple(zt) + (dec, voulu, ouvert)
    fz, fr = P.FRAIS_ZONE, P.FRAIS_RSI
    cands = {"bot seul": np.zeros(nj), "+ M100 (melange du robot)": melange(jours, 1.0),
             "+ M30 (melange a 0,3)": melange(jours, 0.3)}
    bot = P6.gains_du_bot(*a, fz, fr)
    possibles = [d for d in range(260, nj) if ouvert[d] == 0]
    departs = possibles[::P.PAS_DEPART]
    expl = [d for d in departs if dates[d] <= pd.Timestamp("2022-12-31")]
    coffre = [d for d in departs if dates[d] >= pd.Timestamp("2023-01-01")]
    complets = [d for d in possibles if dates[d] >= pd.Timestamp("2023-01-01") and d + P.MAX_SEANCES <= nj][::2]
    L_ = [f"Piste 7 : melange comme 4e source ; {nj} seances du {dates[0].date()} au {dates[-1].date()}", "",
          "source | gain par an (1 unite) | correlation quotidienne avec le bot | pire jour | Trail 2011-2022 : reussis / perdus / score |"
          " Trail 2023-2026 : idem | S2F + plafond 500 $ : recu en 12 mois / au moins un retrait"]
    res = {}
    for nom, x in cands.items():
        ans = (dates[-1] - dates[260]).days / 365.25
        par_an = x[260:].sum() / ans
        corr = float(np.corrcoef(x[260:], bot[260:])[0, 1]) if x[260:].std() > 0 else float("nan")

        def bil(ds):
            r = np.array([P6.trail(int(d), P.MAX_SEANCES, *a, x, fz, fr)[0] for d in ds])
            return round(100 * (r == 1).mean(), 1), round(100 * (r == -1).mean(), 1), round(100 * ((r == 1).mean() - (r == -1).mean()), 1)
        b1, b2 = bil(expl), bil(coffre)
        s = [P6.s2f(int(d), P.MAX_SEANCES, *a, x, fz, fr) for d in complets]
        recu, ret = float(np.mean([q[2] - 57.0 for q in s])), float(np.mean([q[1] > 0 for q in s]))
        par_annee = {int(y): float(v) for y, v in pd.Series(x[260:], index=dates[260:]).groupby(dates[260:].year).sum().items()}
        res[nom] = {"par_an": par_an, "corr": corr, "pire_jour": float(x.min()), "trail_2011_2022": b1, "trail_2023_2026": b2,
                    "s2f_recu_12_mois": recu, "s2f_retrait": ret, "par_annee": par_annee}
        L_.append(f"{nom} | {par_an:+,.0f} $ | {corr:+.2f} | {x.min():+,.0f} $ | {b1[0]} / {b1[1]} / {b1[2]:+.1f} | "
                  f"{b2[0]} / {b2[1]} / {b2[2]:+.1f} | {recu:+,.0f} $ / {ret:.0%}")
    base1, base2 = res["bot seul"]["trail_2011_2022"][2], res["bot seul"]["trail_2023_2026"][2]
    L_.append("")
    for nom in list(cands)[1:]:
        s1, s2 = res[nom]["trail_2011_2022"][2], res[nom]["trail_2023_2026"][2]
        ok = s1 >= base1 + 3 and s2 >= base2
        res[nom]["retenue"] = bool(ok)
        L_.append(f"-> {nom} : score 2011-2022 {s1:+.1f} contre {base1:+.1f}, 2023-2026 {s2:+.1f} contre {base2:+.1f} :"
                  f" {'RETENUE' if ok else 'PAS RETENUE'}")
        L_.append("   gain par annee : " + ", ".join(f"{y} {v:+,.0f}" for y, v in res[nom]["par_annee"].items()))
    (ICI / "piste7.txt").write_text("\n".join(L_) + "\n")
    (ICI / "piste7.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("\n".join(L_))


if __name__ == "__main__":
    main()
