#!/usr/bin/env python3
"""Audit du bot 3 en 1 (audit/README.md) : lit les sorties de Bot3en1.Replay (une ligne par entree ou sortie de la zone)
et calcule, pour chaque jeu de reglages, les trades, le gain par periode (en $ pour 1 MNQ au prix de reference du
projet, 30 900 points, frais de 3 $ l'aller-retour comme le rejeu), le t par seance et la plus forte baisse.

Lancer : python3 audit/rejeux.py <dossier des sorties du rejeu> <nom> [<nom> ...]"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PREF = 30900.0
LIGNE = re.compile(r"^(\d{4}-\d{2}-\d{2}) (achat|vente|sortie|stop)\b.*? a ([0-9.]+)")


def trades(fichier):
    out, ouvert = [], None
    for l in Path(fichier).read_text().splitlines():
        m = LIGNE.match(l)
        if not m:
            continue
        j, quoi, prix = m.group(1), m.group(2), float(m.group(3))
        if quoi in ("achat", "vente"):
            ouvert = (j, 1 if quoi == "achat" else -1, prix, l)
        elif ouvert is not None:
            j0, s, e, txt = ouvert
            brut = (s * (prix - e) - 1.5) * 2
            out.append(dict(jour=pd.Timestamp(j0), sens=s, entree=e, sortie=prix, brut=brut, ajuste=brut * PREF / e,
                            entree_txt=txt.split(" ", 1)[1], sortie_txt=l.split(" ", 1)[1]))
            ouvert = None
    return pd.DataFrame(out)


def stats(t, debut, fin):
    x = t[(t["jour"] >= debut) & (t["jour"] <= fin)]
    j = x.groupby("jour")["ajuste"].sum()
    if len(j) < 2:
        return len(x), x["ajuste"].sum(), np.nan, np.nan
    cum = j.cumsum()
    return len(x), j.sum(), j.mean() / j.std(ddof=1) * np.sqrt(len(j)), (cum - cum.cummax()).min()


PERIODES = [("2011-2018", "2011-01-01", "2018-12-31"), ("2019-2022", "2019-01-01", "2022-12-31"),
            ("2023-2026", "2023-01-01", "2026-12-31"), ("12-30 oct. 2026", "2026-10-12", "2026-10-30")]


def main():
    d = Path(sys.argv[1])
    L = ["| Réglages | Période | Trades | Gain (prix d'aujourd'hui) | t par séance | Plus forte baisse |", "|---|---|---|---|---|---|"]
    for nom in sys.argv[2:]:
        t = trades(d / f"{nom}.txt")
        for per, a, b in PERIODES:
            n, g, tt, dd = stats(t, a, b)
            L.append(f"| {nom} | {per} | {n} | {g:+,.0f} $ | {tt:+.2f} | {dd:+,.0f} $ |")
    print("\n".join(L))


if __name__ == "__main__":
    main()
