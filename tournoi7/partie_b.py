#!/usr/bin/env python3
"""Tournoi n°7, suite (README.md) : sources ZN, dollar et bitcoin (signal 9 h - 10 h ou 9 h 30 - 10 h 30, trade des 7
cibles de 10 h 30 a la fin de seance), controle global contre le hasard ; partie B : familles du tournoi 6 sur le
bitcoin (9 h 30 - 16 h). Lancer depuis ce dossier, une fois tournoi5/donnees/ rempli : python3 partie_b.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
R = ICI.parent
sys.path.insert(0, str(ICI))
import tournoi7 as T7  # noqa: E402

T6 = T7.T6
DON = R / "tournoi5/donnees"
DEVISES = ["6E", "6B", "6J", "6A", "6C", "6S"]


def barre_9h(nom):
    """Mouvement de la barre d'une heure qui commence a 9 h (New York), par date ; NaN si absente."""
    h = pd.read_csv(DON / f"{nom}_1h.csv.gz")
    t = pd.to_datetime(h["t"])
    h = h[t.dt.hour == 9].assign(j=t[t.dt.hour == 9].dt.normalize())
    h = h.drop_duplicates("j", keep="last").set_index("j")
    return h["c"] / h["o"] - 1


def signaux_ajoutes():
    s = {}
    if (DON / "ZN_1h.csv.gz").exists():
        s["ZN"] = barre_9h("ZN")
    if all((DON / f"{d}_1h.csv.gz").exists() for d in DEVISES):
        panier = pd.concat([barre_9h(d) for d in DEVISES], axis=1)
        s["Dollar"] = -panier.mean(axis=1).where(panier.notna().sum(axis=1) >= 4)
    if (DON / "bitcoin_1min.csv.gz").exists():
        J, O, H, L, C, P, X = T6.charger(DON / "bitcoin_1min.csv.gz", 570, 960)
        ok = P[:, 0] & P[:, 389] & (P.sum(axis=1) >= 370) & ~X["echeance"]
        s["BTC"] = pd.Series(np.where(ok, C[:, 59] / O[:, 0] - 1, np.nan), index=J)
    return {k: v.dropna() for k, v in s.items()}


def main():
    sortie = []
    ecrire = lambda s="": (print(s, flush=True), sortie.append(s))
    m = T7.preparer()
    ajout = signaux_ajoutes()
    ecrire(f"Sources ajoutees disponibles : {', '.join(ajout) or 'aucune'}")
    lignes, res = [], []
    for s, sg in ajout.items():
        for c, t in m.items():
            x = sg.reindex(t.index)
            jouable = t["ok"] & x.notna()
            for nom_sens, k in (("suivre", 1), ("contrer", -1)):
                sens = np.where(jouable, k * np.sign(x.fillna(0)), 0)
                pts = sens * t["mouv"] - t.attrs["cout"] * np.abs(sens)
                r = (pts / t["o"])[t["ok"]]
                a0 = 2018 if s == "BTC" else 2016
                tt, x0 = T7.stats(r, a0, 2022)
                t1, x1 = T7.stats(r, a0, 2019 if a0 == 2016 else 2020)
                t2, x2 = T7.stats(r, 2020 if a0 == 2016 else 2021, 2022)
                res.append((s, c, nom_sens, r))
                lignes.append({"source": s, "cible": c, "sens": nom_sens, "t": tt, "t_1": t1, "t_2": t2,
                               "jours_trade": int((pts[t["ok"]][(r.index.year >= a0) & (r.index.year <= 2022)] != 0).sum()),
                               "retenu_etape1": tt >= T7.SEUIL and x1.mean() > 0 and x2.mean() > 0})
    df = pd.DataFrame(lignes).sort_values("t", ascending=False)
    if len(df):
        ecrire(f"\n{len(df)} essais. Les 10 meilleurs (exploration jusqu'a 2022) :")
        for r in df.head(10).itertuples():
            ecrire(f"  {r.source:>6s} -> {r.cible:<3s} {r.sens:7s} t {r.t:+5.2f} ({r.t_1:+5.2f}, {r.t_2:+5.2f}) | {r.jours_trade} trades"
                   f"{'  <= etape 1' if r.retenu_etape1 else ''}")
        ecrire(f"  t >= 2 : {int((df.t >= 2).sum())} ; t >= 3 : {int((df.t >= 3).sum())} ; t <= -2 : {int((df.t <= -2).sum())}")
        rng = np.random.default_rng(2027)
        maxi = []
        for k in range(T7.N_HASARD):
            best = -9
            for s, sg in ajout.items():
                g = sg[(sg.index.year <= 2022)]
                v = g.values.copy()
                for a in np.unique(g.index.year):
                    i = np.where(g.index.year == a)[0]
                    v[i] = v[rng.permutation(i)]
                gp = pd.Series(v, index=g.index)
                for c, t in m.items():
                    x = gp.reindex(t.index)
                    jouable = t["ok"] & x.notna()
                    for kk in (1, -1):
                        sens = np.where(jouable, kk * np.sign(x.fillna(0)), 0)
                        pts = sens * t["mouv"] - t.attrs["cout"] * np.abs(sens)
                        r = (pts / t["o"])[t["ok"]]
                        best = max(best, T7.stats(r, 2018 if s == "BTC" else 2016, 2022)[0])
            maxi.append(best)
        maxi = np.array(maxi)
        p95 = float(np.quantile(maxi, 0.95))
        ecrire(f"Controle global : meilleur t par tirage, mediane {np.median(maxi):+.2f}, 95e centile {p95:+.2f} ;"
               f" meilleur t reel {df.t.max():+.2f} => {'PASSE' if df.t.max() > p95 else 'ne passe pas'}")
        surv = df[df.retenu_etape1 & (df.t > p95)]
        ecrire(f"Survivants avant le coffre : {', '.join(f'{r.source}->{r.cible} {r.sens}' for r in surv.itertuples()) or 'aucun'}")
        for r0 in surv.itertuples():
            r = next(x for x in res if x[:3] == (r0.source, r0.cible, r0.sens))[3]
            t, x = T7.stats(r, 2023, 2026)
            ans = [x[x.index.year == a].sum() > 0 for a in range(2023, 2027)]
            ecrire(f"  coffre {r0.source}->{r0.cible} {r0.sens} : t {t:+.2f}, annees positives {sum(ans)}/4"
                   f" => {'SURVIT' if t >= 2 and sum(ans) >= 3 else 'elimine'}")
        df.to_csv(ICI / "sources_ajoutees.csv", index=False, float_format="%.4g")
    # partie B : familles du tournoi 6 sur le bitcoin
    f = DON / "bitcoin_1min.csv.gz"
    if f.exists():
        J, O, H, L, C, P, X = T6.charger(f, 570, 960)
        complete = P[:, 0] & P[:, 389] & (P.sum(axis=1) >= 370)
        ok = complete & ~X["echeance"]
        pt, tick = 0.1, 5.0
        cout = (2 * 1.0 + 2 * tick * pt) / pt
        fam = T6.familles(O, H, L, C, complete, ok, X["contrat"], cout)
        zone = T7.T6  # noqa
        ecrire("\nPartie B : familles du tournoi 6 sur le bitcoin CME (9 h 30 - 16 h), exploration 2018-2022 :")
        for nom, pts in fam.items():
            r = pd.Series(pts / O[:, 0], index=J)[ok]
            t, x = T7.stats(r, 2018, 2022)
            t1, x1 = T7.stats(r, 2018, 2020)
            t2, x2 = T7.stats(r, 2021, 2022)
            ret = nom != "Achat simple (controle)" and t >= 2.5 and x1.mean() > 0 and x2.mean() > 0
            ecrire(f"  {nom:36s} t {t:+5.2f} (2018-20 {t1:+5.2f}, 2021-22 {t2:+5.2f}){'  <= RETENUE (corr. zone a verifier)' if ret else ''}")
    (ICI / "partie_b.txt").write_text("\n".join(sortie) + "\n")


if __name__ == "__main__":
    main()
