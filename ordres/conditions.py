#!/usr/bin/env python3
"""Order flow par heure, volatilite, volume et sens de la journee (regles dans CONDITIONS.md).

Lancer depuis ce dossier : python3 conditions.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import analyse as A

FRAIS = {"MES": 2.6, "ES": 1.4}          # ticks par aller-retour
T_MIN = 3.45                              # Bonferroni, 5 % unilateral, 180 cas
HEURES = [(1, 30, "9h31-10h"), (30, 90, "10h-11h"), (90, 150, "11h-12h"), (150, 210, "12h-13h"),
          (210, 270, "13h-14h"), (270, 330, "14h-15h"), (330, 384, "15h-15h53")]


def contexte(g):
    """Par minute : volume, amplitude du prix milieu sur les 15 minutes precedentes, mouvement depuis 9 h 30."""
    mid = ((g["bid"] + g["ask"]) / 2).values
    fin = np.arange(390) * 60 + 59
    vol = (g["achat"].values + g["vente"].values).reshape(390, 60).sum(1)
    s = pd.Series(mid)
    amp15 = (s.rolling(900, min_periods=900).max() - s.rolling(900, min_periods=900).min()).values[fin] / A.TICK
    jour = (mid[fin] - mid[0]) / A.TICK
    return pd.DataFrame({"volume": vol, "amp15": amp15, "jour": jour})


def main():
    jours, grilles, f = A.charger()
    fp = {m: x for m, x in f.groupby("m")}
    morceaux = []
    for i, g in enumerate(grilles):
        d = pd.concat([A.signaux_jour(g, fp), contexte(g)], axis=1)
        d["seance"], d["minute"] = i, np.arange(390)
        morceaux.append(d.iloc[A.DEBUT_DEC:A.FIN_DEC + 1])
    x = pd.concat(morceaux, ignore_index=True)
    # signaux forts : deciles des 23 seances
    sens = {}
    for nom, col in (("carnet fort", "carnet"), ("OFI fort", "ofi"), ("delta fort", "delta1"), ("CVD fort", "cvd15")):
        bas, haut = x[col].quantile(0.1), x[col].quantile(0.9)
        sens[nom] = np.where(x[col] >= haut, 1, np.where(x[col] <= bas, -1, 0))
    sens["divergence prix / CVD"] = x["absorption"].values.astype(int)
    sens["carnet fort + CVD d'accord"] = np.where(np.sign(x["cvd15"].values) == sens["carnet fort"], sens["carnet fort"], 0)
    # conditions
    t_vol = x["amp15"].quantile([1 / 3, 2 / 3]).values
    t_v = x["volume"].quantile([1 / 3, 2 / 3]).values
    tiers = lambda v, t: np.where(v <= t[0], 0, np.where(v <= t[1], 1, 2))
    cases = {}
    for a, b, nom in HEURES:
        cases[("heure", nom)] = (x["minute"] >= a).values & (x["minute"] < b).values
    for k, nom in enumerate(("faible", "moyenne", "forte")):
        cases[("volatilite", nom)] = (tiers(x["amp15"].values, t_vol) == k) & x["amp15"].notna().values
        cases[("volume", nom)] = tiers(x["volume"].values, t_v) == k
    lignes = []
    for sig, s in sens.items():
        dj = np.sign(x["jour"].values)
        cas_sig = dict(cases)
        cas_sig[("sens du jour", "avec")] = (dj != 0) & (dj == s)
        cas_sig[("sens du jour", "contre")] = (dj != 0) & (dj == -s)
        for h in (1, 5):
            fut = x[f"f{h}"].values
            for (fam, nom), m in cas_sig.items():
                sel = m & (s != 0) & ~np.isnan(fut)
                gain = s[sel] * fut[sel]
                par_seance = pd.Series(gain).groupby(x["seance"].values[sel]).mean()
                ligne = {"signal": sig, "duree": h, "famille": fam, "case": nom, "signaux": int(sel.sum()),
                         "seances": int(len(par_seance)), "brut": float(gain.mean()) if len(gain) else np.nan}
                for frais, c in FRAIS.items():
                    ps = par_seance - c
                    t = float(ps.mean() / ps.std() * np.sqrt(len(ps))) if len(ps) > 1 and ps.std() > 0 else np.nan
                    ligne[f"net_{frais}"] = ligne["brut"] - c
                    ligne[f"t_{frais}"] = t
                    ligne[f"efficace_{frais}"] = bool(ligne["brut"] - c > 0 and t >= T_MIN and sel.sum() >= 30 and len(par_seance) >= 10)
                lignes.append(ligne)
    df = pd.DataFrame(lignes)
    assert len(df) == 180, len(df)
    df.to_csv(Path(__file__).with_name("resultats_conditions.csv"), index=False)
    print(f"{len(jours)} seances ES ({jours[0].date()} - {jours[-1].date()}), {len(x)} minutes de decision, 180 cas\n")
    for sig in sens:
        for h in (1, 5):
            d = df[(df["signal"] == sig) & (df["duree"] == h)]
            print(f"{sig} - {h} min : {int(d[d['famille'] == 'heure']['signaux'].sum())} signaux, brut moyen "
                  f"{(d[d['famille'] == 'heure']['brut'] * d[d['famille'] == 'heure']['signaux']).sum() / max(1, d[d['famille'] == 'heure']['signaux'].sum()):+.2f} tick")
            for _, r in d.iterrows():
                print(f"   {r['famille']:12s} {r['case']:10s} | {r['signaux']:5d} signaux, {r['seances']:2d} seances | brut {r['brut']:+6.2f}"
                      f" | net MES {r['net_MES']:+6.2f} (t {r['t_MES']:+6.2f}) | net ES {r['net_ES']:+6.2f} (t {r['t_ES']:+6.2f})"
                      + (" | EFFICACE" if r["efficace_MES"] or r["efficace_ES"] else ""))
    meilleurs = df.sort_values("brut", ascending=False).head(10)
    print("\nLes 10 cases au plus fort mouvement brut :")
    for _, r in meilleurs.iterrows():
        print(f"   {r['signal']:28s} {r['duree']} min | {r['famille']:12s} {r['case']:10s} | {r['signaux']:5d} signaux | brut {r['brut']:+.2f}"
              f" | net ES {r['net_ES']:+.2f} (t {r['t_ES']:+.2f}) | net MES {r['net_MES']:+.2f} (t {r['t_MES']:+.2f})")
    eff = {f: df[df[f"efficace_{f}"]] for f in FRAIS}
    for f in FRAIS:
        print(f"\nCases efficaces aux frais {f} ({FRAIS[f]} ticks) : {len(eff[f])}"
              + "".join(f"\n   {r['signal']} {r['duree']} min {r['famille']} {r['case']}" for _, r in eff[f].iterrows()))
    Path(__file__).with_name("resultats_conditions.json").write_text(json.dumps(
        {"efficaces": {f: eff[f][["signal", "duree", "famille", "case"]].to_dict("records") for f in FRAIS},
         "meilleurs": meilleurs.to_dict("records")}, indent=1, ensure_ascii=False, default=float))


if __name__ == "__main__":
    main()
