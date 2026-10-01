#!/usr/bin/env python3
"""Tournoi n°7 (README.md) : le mouvement de 9 h 30 - 10 h 30 d'un marche annonce-t-il le reste de la seance d'un
autre ? Partie A sur les 7 marches minute (2016-2026), controle global contre le hasard, coffre 2023-2026 pour les
survivants. Lancer depuis ce dossier : python3 tournoi7.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
R = ICI.parent
sys.path.insert(0, str(R / "tournoi6"))
sys.path.insert(0, str(R / "tournoi"))
import tournoi6 as T6  # noqa: E402
import concurrents as K1  # noqa: E402
import explorer as EX  # noqa: E402

FRAIS_ORDRE = 1.0
MARCHES = {"NQ": (R / "intraday/donnees/nasdaq100_1min.csv.gz", 2.0, 0.25, 570, 960),
           "ES": (R / "intraday/donnees/sp500_1min.csv.gz", 5.0, 0.25, 570, 960), **T6.MARCHES}
SEUIL, N_HASARD = 3.0, 200


def preparer():
    """Par marche, sur les dates de 2016 a 2026 : signal 9 h 30 - 10 h 30, mouvement brut de 10 h 30 a la fin de
    seance (points), frais (points), $ par point, ouverture, jour exploitable."""
    m = {}
    for nom, (fichier, pt, tick, m0, m1) in MARCHES.items():
        J, O, H, L, C, P, X = T6.charger(fichier, m0, m1)
        n = m1 - m0
        complete = P[:, 0] & P[:, n - 1] & (P.sum(axis=1) >= n - 20)
        ok = complete & ~X["echeance"]
        i930, i1029, i1030 = 570 - m0, 629 - m0, 630 - m0
        sig = C[:, i1029] / O[:, i930] - 1
        mouv = C[:, n - 1] - O[:, i1030]
        cout = (2 * FRAIS_ORDRE + 2 * tick * pt) / pt
        # controle : sans stop, suivre = entree_fixe a 10 h 30 jusqu'a la fin de seance
        sens = np.where(ok, np.sign(np.nan_to_num(sig)), 0).astype(np.int64)
        rien = np.full(len(J), np.nan)
        ref = K1.entree_fixe(O, H, L, C, ok, cout, sens, i1030, rien, rien, n - 1)
        assert np.allclose(ref, np.where(ok & (sens != 0), sens * mouv - cout, 0.0))
        g = J >= pd.Timestamp("2016-01-01")
        m[nom] = pd.DataFrame({"sig": sig[g], "mouv": mouv[g], "o": O[g, 0], "ok": ok[g]}, index=J[g])
        m[nom].attrs.update(cout=cout, pt=pt)
    return m


def essais(m, signaux=None):
    """t (rendements quotidiens nets, jours exploitables de la cible) de chaque regle source -> cible, par periode.
    signaux : signaux de remplacement par source (controle contre le hasard)."""
    out = []
    for s in m:
        sg = (signaux or {}).get(s, m[s]["sig"].where(m[s]["ok"]))
        for c in m:
            if c == s:
                continue
            t = m[c]
            x = sg.reindex(t.index)
            jouable = t["ok"] & x.notna()
            for nom_sens, k in (("suivre", 1), ("contrer", -1)):
                sens = np.where(jouable, k * np.sign(x.fillna(0)), 0)
                pts = sens * t["mouv"] - t.attrs["cout"] * np.abs(sens)
                r = (pts / t["o"])[t["ok"]]
                out.append((s, c, nom_sens, r, pts[t["ok"]] * t.attrs["pt"]))
    return out


def stats(r, a, b):
    x = r[(r.index.year >= a) & (r.index.year <= b)]
    return EX.t_stat(x.values), x


def main():
    sortie = []
    ecrire = lambda s="": (print(s, flush=True), sortie.append(s))
    m = preparer()
    ecrire("Controle : la regle simple (10 h 30 -> fin de seance) = entree_fixe des tournois, sur les 7 marches : OK")
    res = essais(m)
    lignes = []
    for s, c, sens, r, dol in res:
        t, x = stats(r, 2016, 2022)
        t1, x1 = stats(r, 2016, 2019)
        t2, x2 = stats(r, 2020, 2022)
        d = dol[(dol.index.year >= 2016) & (dol.index.year <= 2022)]
        lignes.append({"source": s, "cible": c, "sens": sens, "t": t, "t_2016_2019": t1, "t_2020_2022": t2,
                       "jours_trade": int((d != 0).sum()), "dollars_par_trade": float(d[d != 0].mean()),
                       "retenu_etape1": t >= SEUIL and x1.mean() > 0 and x2.mean() > 0})
    df = pd.DataFrame(lignes).sort_values("t", ascending=False)
    ecrire(f"\nPartie A, exploration 2016-2022 : {len(df)} essais (7 sources x 6 cibles x 2 sens). Les 12 meilleurs :")
    for r in df.head(12).itertuples():
        ecrire(f"  {r.source:>3s} -> {r.cible:<3s} {r.sens:7s} t {r.t:+5.2f} (2016-19 {r.t_2016_2019:+5.2f}, 2020-22 {r.t_2020_2022:+5.2f})"
               f" | {r.jours_trade} trades, {r.dollars_par_trade:+6.2f} $ par trade{'  <= etape 1' if r.retenu_etape1 else ''}")
    ecrire(f"  t >= 2 : {int((df.t >= 2).sum())} ; t >= 3 : {int((df.t >= 3).sum())} ; t <= -2 : {int((df.t <= -2).sum())}")
    # controle global : signaux associes a un autre jour de la meme annee
    rng = np.random.default_rng(2026)
    maxi = []
    for k in range(N_HASARD):
        rempl = {}
        for s in m:
            sg = m[s]["sig"].where(m[s]["ok"])
            sg = sg[(sg.index.year >= 2016) & (sg.index.year <= 2022)]
            v = sg.values.copy()
            for a in np.unique(sg.index.year):
                i = np.where(sg.index.year == a)[0]
                v[i] = v[rng.permutation(i)]
            rempl[s] = pd.Series(v, index=sg.index)
        maxi.append(max(stats(r, 2016, 2022)[0] for *_, r, _ in essais(m, rempl)))
    maxi = np.array(maxi)
    p95 = float(np.quantile(maxi, 0.95))
    meilleur = float(df.t.max())
    ecrire(f"\nControle global ({N_HASARD} tirages, signaux d'un autre jour de la meme annee) : meilleur t par tirage,"
           f" mediane {np.median(maxi):+.2f}, 95e centile {p95:+.2f} ; meilleur t reel {meilleur:+.2f}"
           f" => {'PASSE' if meilleur > p95 else 'ne passe pas'} (part des tirages au moins aussi bons : {np.mean(maxi >= meilleur):.0%})")
    surv = df[df.retenu_etape1 & (df.t > p95)]
    ecrire(f"Survivants avant le coffre : {', '.join(f'{r.source}->{r.cible} {r.sens}' for r in surv.itertuples()) or 'aucun'}")
    df.to_csv(ICI / "partieA.csv", index=False, float_format="%.4g")
    np.savetxt(ICI / "hasard_max_t.txt", maxi, fmt="%.4f")
    if len(surv):
        ecrire("\nCoffre 2023-2026 (ouvert une fois) :")
        for r0 in surv.itertuples():
            r = next(x for x in res if x[0] == r0.source and x[1] == r0.cible and x[2] == r0.sens)
            t, x = stats(r[3], 2023, 2026)
            ans = [x[x.index.year == a].sum() > 0 for a in range(2023, 2027)]
            ecrire(f"  {r0.source}->{r0.cible} {r0.sens} : t {t:+.2f}, annees positives {sum(ans)}/4"
                   f" => {'SURVIT' if t >= 2 and sum(ans) >= 3 else 'elimine'}")
    (ICI / "tournoi7.txt").write_text("\n".join(sortie) + "\n")


if __name__ == "__main__":
    main()
