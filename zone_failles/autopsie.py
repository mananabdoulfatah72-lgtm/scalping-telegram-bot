#!/usr/bin/env python3
"""Autopsie de la zone de bruit sur 2011-2022 (les annees 2023-2026 ne sont pas chargees) : ou gagne-t-elle, ou
perd-elle ? Rien n'est decide ici : ce rapport sert a choisir les variantes a tester (README.md).

Lancer depuis ce dossier : python3 autopsie.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import journal as Z

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tournoi"))
sys.path.insert(0, str(R / "evolution2"))
from explorer import charger, t_stat  # noqa: E402
import tournoi3 as T3  # noqa: E402

ICI = Path(__file__).resolve().parent
MARCHES = {"NQ": ("nasdaq100", 2.0), "ES": ("sp500", 5.0)}


def ligne(nom, t, cout, o0, jours_ok):
    """Resume d'un groupe de trades : nombre, brut et net moyens par trade (points et $ pour 1 micro), t des jours."""
    if len(t) == 0:
        return f"  {nom:34s} | aucun trade"
    net = t["brut"] - cout
    r = pd.Series(0.0, index=jours_ok)
    r = r.add((net / o0[t["d"].values]).groupby(t["jour"].values).sum(), fill_value=0.0).reindex(jours_ok).fillna(0)
    rb = pd.Series(0.0, index=jours_ok).add((t["brut"] / o0[t["d"].values]).groupby(t["jour"].values).sum(), fill_value=0.0).reindex(jours_ok).fillna(0)
    return (f"  {nom:34s} | {len(t):5d} trades, gagnants {(t['brut'] > cout).mean():4.0%} | brut {t['brut'].mean():+7.2f} pts,"
            f" net {net.mean():+7.2f} pts par trade | t avant frais {t_stat(rb.values):+5.2f}, apres frais {t_stat(r.values):+5.2f}")


def main():
    Q = T3.lire_quotidien()
    sortie = []
    ecrire = lambda s="": (print(s, flush=True), sortie.append(s))
    for marche, (fichier, pt) in MARCHES.items():
        J, O, H, L, C, P, X = charger(fichier)
        assert J.max() <= pd.Timestamp("2022-12-31")
        cout = st_cout = Z.st.cout_aller_retour(fichier)
        t = Z.journal(J, O, H, L, C, P, X)
        # verification : meme resultat que le backtest de reference
        ref = Z.st.zone_de_bruit(J, O, H, L, C, P, X)
        par_jour = t.groupby("jour")["brut"].sum()
        assert np.allclose(par_jour.reindex(ref.index).values, ref["brut"].values) and (t.groupby("jour").size().reindex(ref.index).values == ref["allers"].values).all()
        ok = Z.st.journees_completes(P) & ~X["echeance"]
        t = t[ok[t["d"].values]].copy()                    # jours retenus par les tournois (pas de changement d'echeance)
        jours_ok = pd.DatetimeIndex(J[ok])
        o0 = O[:, 0]
        an = t["jour"].dt.year
        ecrire(f"=== {marche} (1 micro = {pt:g} $ par point ; frais {cout:.2f} pts par aller-retour) ===")
        ecrire(ligne("Tout 2011-2022", t, cout, o0, jours_ok))
        for a, b in ((2011, 2016), (2017, 2022)):
            ecrire(ligne(f"{a}-{b}", t[(an >= a) & (an <= b)], cout, o0, jours_ok[(jours_ok.year >= a) & (jours_ok.year <= b)]))
        ecrire("  -- frais en % du prix : " + " ".join(f"{a}:{cout / np.nanmean(o0[pd.DatetimeIndex(J).year == a]) * 1e4:.1f}pb"
                                                     for a in range(2011, 2023)))
        ecrire("  -- par rang du trade dans la journee")
        for k in (1, 2, 3):
            ecrire(ligne(f"trade n°{k}{'+' if k == 3 else ''}", t[t["rang"] >= 3] if k == 3 else t[t["rang"] == k], cout, o0, jours_ok))
        ecrire("  -- par heure d'entree")
        for m in range(30, 390, 30):
            h = 570 + m
            ecrire(ligne(f"entree a {h // 60}h{h % 60:02d}", t[t["m_entree"] == m], cout, o0, jours_ok))
        ecrire("  -- par sens")
        ecrire(ligne("achats", t[t["sens"] > 0], cout, o0, jours_ok))
        ecrire(ligne("ventes", t[t["sens"] < 0], cout, o0, jours_ok))
        ecrire("  -- par sortie")
        ecrire(ligne("sortie sur stop suiveur", t[t["raison"] == "stop"], cout, o0, jours_ok))
        ecrire(ligne("sortie a la cloture", t[t["raison"] == "cloture"], cout, o0, jours_ok))
        ecrire("  -- par duree du trade")
        dur = t["m_sortie"] - t["m_entree"]
        ecrire(ligne("30 min", t[dur <= 30], cout, o0, jours_ok))
        ecrire(ligne("1 h a 2 h", t[(dur > 30) & (dur <= 120)], cout, o0, jours_ok))
        ecrire(ligne("plus de 2 h", t[dur > 120], cout, o0, jours_ok))
        ecrire("  -- selon la volatilite (sigma a l'entree, tiers)")
        q = t["sigma"].quantile([1 / 3, 2 / 3]).values
        for nom, m in (("calme", t["sigma"] <= q[0]), ("moyenne", (t["sigma"] > q[0]) & (t["sigma"] <= q[1])), ("agitee", t["sigma"] > q[1])):
            ecrire(ligne(f"volatilite {nom}", t[m], cout, o0, jours_ok))
        vr = T3.veille(J, Q["vix_ratio"])[t["d"].values]
        g = T3.veille(J, Q["gex"])
        gmed = T3.quantile_252(g, 0.5)
        ecrire("  -- selon le marche des options (veille)")
        ecrire(ligne("VIX en contango (< 1)", t[vr < 1], cout, o0, jours_ok))
        ecrire(ligne("VIX en deport (>= 1)", t[vr >= 1], cout, o0, jours_ok))
        ecrire(ligne("GEX sous sa mediane (252 j)", t[(g < gmed)[t["d"].values]], cout, o0, jours_ok))
        ecrire(ligne("GEX au-dessus de sa mediane", t[(g >= gmed)[t["d"].values]], cout, o0, jours_ok))
        ecrire("  -- journees a allers-retours")
        n_j = t.groupby("jour").size()
        ecrire(ligne("jours a 1 trade", t[t["jour"].isin(n_j[n_j == 1].index)], cout, o0, jours_ok))
        ecrire(ligne("jours a 2 trades ou plus", t[t["jour"].isin(n_j[n_j >= 2].index)], cout, o0, jours_ok))
        ecrire("  -- donnees : jours touches par une seance incomplete (ferie CME, fermeture anticipee)")
        comp = Z.st.journees_completes(P)
        veille_incomplete = np.r_[False, ~comp[:-1]]
        fenetre_incomplete = pd.Series(~comp).rolling(14, min_periods=1).sum().shift(1).fillna(0).values > 0
        ecrire(ligne("veille = seance incomplete", t[veille_incomplete[t["d"].values]], cout, o0, jours_ok))
        ecrire(ligne("sigma calcule avec une seance incomplete", t[fenetre_incomplete[t["d"].values]], cout, o0, jours_ok))
        ecrire(ligne("jours propres", t[~fenetre_incomplete[t["d"].values] & ~veille_incomplete[t["d"].values]], cout, o0, jours_ok))
        ecrire("  -- taille : fixe (1 contrat) contre taille inverse de la volatilite (regle de l'article, cible de volatilite)")
        net_j = pd.Series(((t["brut"] - cout) / o0[t["d"].values]).values, index=t["d"].values).groupby(level=0).sum().reindex(np.where(ok)[0]).fillna(0)
        vol14 = pd.Series(C[:, 389] / np.r_[np.nan, C[:-1, 389]] - 1).rolling(14, min_periods=14).std().shift(1).values
        poids = 1 / vol14[net_j.index.values]
        poids = poids / np.nanmean(poids)
        m = np.isfinite(poids)
        ecrire(f"  taille fixe : t {t_stat(net_j.values[m]):+.2f} | taille / volatilite 14 j : t {t_stat((net_j.values * poids)[m]):+.2f}")
        ecrire()
    (ICI / "autopsie.txt").write_text("\n".join(sortie) + "\n")


if __name__ == "__main__":
    main()
