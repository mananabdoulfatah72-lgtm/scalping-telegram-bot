#!/usr/bin/env python3
"""Partie J, descriptif : les cassures entre deux controles (J0) que le bot ne voit pas. Pour chacune : le prix est-il
encore hors de la zone au controle suivant (cassure tenue) ou revenu dedans (fausse cassure) ? Gain de chaque groupe et
exemples recents. Ecrit resultats/j/fausses_cassures.txt.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/partie_j_fausses.py"""
import os

import numpy as np
import pandas as pd

import donnees as D
import partie_g as G
import partie_j as J


def main():
    d = D.minutes("NQ", chemin=os.environ["MINUTES"], debut="2011-01-01")
    sigma, vwap, href, bref, jouable = G.zone_tableaux(d)
    C = d["c"]
    t = J._zone_j(d["o"], d["h"], d["l"], C, sigma, vwap, href, bref, jouable, True, 0.0, False, float(d["tick"]), 0)
    fr = float(d["frais"]) / float(d["pt"])
    lignes = []
    for s, me, sens, px, mx, xp, _, _ in t:
        s, me, mx = int(s), int(me), int(mx)
        if me % 30 == 0:
            continue
        mc = (me // 30 + 1) * 30                      # controle suivant
        sg = sigma[s, mc]
        ub, lb = href[s] * (1 + sg), bref[s] * (1 - sg)
        tenue = C[s, mc] > ub if sens > 0 else C[s, mc] < lb
        h = 9 * 60 + 30 + me
        lignes.append(dict(jour=str(d["jours"][s]), heure_ny=f"{h // 60}h{h % 60:02d}", sens="achat" if sens > 0 else "vente",
                           entree=px, prix_controle=C[s, mc], sortie=xp, points=sens * (xp - px) - fr, tenue=bool(tenue)))
    x = pd.DataFrame(lignes)
    an = x["jour"].str[:4].astype(int)
    L = [f"Cassures entre deux controles (10 h - 15 h 30), 2011 - {x['jour'].max()} : {len(x)}"]
    for nom, g in (("fausses (prix revenu dans la zone au controle suivant : le bot ne fait rien)", x[~x.tenue]),
                   ("tenues (encore hors de la zone au controle suivant : le bot entre a ce controle)", x[x.tenue])):
        L.append(f"- {nom} : {len(g)} ({len(g) / len(x):.0%}), {g.points.mean():+.2f} points en moyenne, "
                 f"{(g.points > 0).mean():.0%} gagnantes, total {g.points.sum():+.0f} points ; depuis 2023 : {len(g[an[g.index] >= 2023])}, "
                 f"total {g[an[g.index] >= 2023].points.sum():+.0f} points")
    L += ["", "Fausses cassures depuis le 1er septembre 2026 (heure de New York ; points pour 1 MNQ, frais deduits) :"]
    r = x[(~x.tenue) & (x.jour >= "2026-09-01")]
    for _, l in r.iterrows():
        L.append(f"  {l.jour} {l.heure_ny:>6} {l.sens:<6} a {l.entree:.2f}, au controle suivant {l.prix_controle:.2f}, "
                 f"sortie {l.sortie:.2f} : {l.points:+.2f} points")
    out = J.SORTIE / "fausses_cassures.txt"
    out.write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
