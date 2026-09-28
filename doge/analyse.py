#!/usr/bin/env python3
"""DOGE : mouvement brutal a 2 h, 13 h et 23 h (heure de Paris) ? Tests fixes dans README.md.

Lancer depuis ce dossier : python3 analyse.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

D = Path(__file__).parent / "donnees"
HEURES = [2, 13, 23]
FRAIS = [0.0010, 0.0020]           # aller-retour : futures perpetuels / comptant
PARIS = "Europe/Paris"


def charger():
    b = pd.read_csv(D / "doge_5min.csv.gz", parse_dates=["t"]).set_index("t")
    grille = pd.date_range(b.index[0], b.index[-1], freq="5min")
    ouv = b["o"].reindex(grille).ffill(limit=3)          # prix a chaque debut de bougie (UTC)
    return ouv


def prix_local(ouv, jours, heure, minute=0):
    """Prix a heure:minute (heure de Paris) pour chaque jour ; NaN si l'heure n'existe pas (changement d'heure)."""
    loc = pd.DatetimeIndex(jours + pd.Timedelta(hours=heure, minutes=minute))
    t = loc.tz_localize(PARIS, nonexistent="NaT", ambiguous="NaT").tz_convert("UTC").tz_localize(None)
    return pd.Series(ouv.reindex(t).values, index=jours)


def regles(ouv, jours, h):
    p0, p5 = prix_local(ouv, jours, h), prix_local(ouv, jours, h, 5)
    p1 = prix_local(ouv, jours + pd.Timedelta(days=1 if h == 23 else 0), (h + 1) % 24).set_axis(jours)
    pm1 = prix_local(ouv, jours - pd.Timedelta(days=1 if h == 0 else 0), (h - 1) % 24).set_axis(jours)
    r = p1 / p0 - 1
    return {
        "toujours acheteur": r,
        "toujours vendeur": -r,
        "suivre l'heure d'avant": np.sign(p0 / pm1 - 1) * r,
        "suivre le depart (5 min)": np.sign(p5 / p0 - 1) * (p1 / p5 - 1),
    }


def main():
    ouv = charger()
    jours = pd.date_range(ouv.index[0].normalize() + pd.Timedelta(days=2), ouv.index[-1].normalize() - pd.Timedelta(days=2))
    print(f"DOGE/USDT, {jours[0].date()} -> {jours[-1].date()} ({len(jours)} jours)\n")
    # 1. mouvement des 15 minutes apres chaque heure, pour toutes les heures
    mv = {}
    for h in range(24):
        a, b = prix_local(ouv, jours, h), prix_local(ouv, jours, h, 15)
        mv[h] = (b / a - 1).abs()
    profil = pd.Series({h: m.mean() for h, m in mv.items()})
    saut = pd.Series({h: (m > 0.01).mean() for h, m in mv.items()})
    print("1. Mouvement moyen (valeur absolue) des 15 minutes apres chaque heure (heure de Paris) :")
    print("   " + " ".join(f"{h}h:{v:.2%}" for h, v in profil.items()))
    for h in HEURES:
        autres = profil.drop(HEURES).mean()
        print(f"   {h:2d} h : {profil[h]:.3%} contre {autres:.3%} en moyenne aux autres heures (x{profil[h] / autres:.2f})"
              f" | jours avec un mouvement de plus de 1 % en 15 min : {saut[h]:.0%} (autres heures : {saut.drop(HEURES).mean():.0%})")
    # 2. regles de trading
    print("\n2. Regles (position jusqu'a l'heure suivante), frais 0,10 % par aller-retour :")
    rng = np.random.default_rng(0)
    autres_h = [h for h in range(24) if h not in HEURES]
    cache = {h: regles(ouv, jours, h) for h in range(24)}
    sortie = {"profil": profil.to_dict(), "regles": {}}
    for h in HEURES:
        for nom, r in cache[h].items():
            r = r.dropna()
            for frais in FRAIS:
                net = r - frais
                t = net.mean() / net.std() * np.sqrt(len(net))
                if frais == FRAIS[0]:
                    # placebo : meme regle, a une heure tiree au hasard parmi les autres, chaque jour
                    tab = pd.DataFrame({k: cache[k][nom] for k in autres_h}).reindex(r.index)
                    choix = rng.integers(0, len(autres_h), size=(500, len(r)))
                    vals = tab.values
                    plac = np.nanmean(vals[np.arange(len(r)), choix], axis=1) - frais
                    cent = float(np.mean(plac < net.mean()))
                    annees = net.groupby(net.index.year).sum()
                    ok = net.mean() > 0 and t >= 2 and cent >= 0.95
                    print(f"   {h:2d} h {nom:26s} : {len(net)} trades | brut {r.mean():+.3%} | net {net.mean():+.3%} par trade (t {t:+.2f})"
                          f" | placebo battu {cent:.0%} | {'EXPLOITABLE' if ok else 'non'}")
                    print("        par annee (somme des trades) : " + " ".join(f"{a}:{v:+.0%}" for a, v in annees.items()))
                    sortie["regles"][f"{h}h {nom}"] = {"trades": int(len(net)), "brut": float(r.mean()), "net": float(net.mean()),
                                                       "t": float(t), "placebo": cent, "exploitable": bool(ok),
                                                       "annees": {int(a): float(v) for a, v in annees.items()}}
                else:
                    print(f"        avec 0,20 % de frais : net {net.mean():+.3%} par trade (t {t:+.2f})")
    Path(__file__).with_name("resultats.json").write_text(json.dumps(sortie, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
