#!/usr/bin/env python3
"""Version 5, descriptif (README.md, « Diversifier les marches ») : pour chaque marche CME, le cout d'un aller-retour sur
le plus petit contrat (2 commissions + 2 ticks, en points de base de la valeur du contrat) divise par le mouvement
median de 5, 15 et 30 minutes pendant la seance americaine, 2023 - fin des donnees. Mouvements : barres de 5 minutes
des ETF qui suivent chaque future (Alpaca, donnees_libres/ de la branche claude/affectionate-turing-tnz0mn) ; niveau de
prix du future : Yahoo, cloture du jour. Contrats et frais : etude_large/marches.py de la meme branche.
Lancer : DONNEES_LIBRES=<chemin de donnees_libres> python3 scalping/couts.py. Ecrit resultats/v5/couts.txt."""
import os
from pathlib import Path

import numpy as np
import pandas as pd

import commun as K

LIBRES = Path(os.getenv("DONNEES_LIBRES", str(K.KB.parent / "donnees_libres")))
SORTIE = K.ICI / "resultats" / "v5"
DEBUT = "2023-01-01"
MICRO, STANDARD = 1.0, 2.5
# etf, future, yahoo, plus petit contrat CME, $ par unite de prix Yahoo, tick, commission par ordre, CME (True) ou non
MARCHES = [
    ("SPY", "ES", "ES", "MES", 5.0, 0.25, MICRO, True), ("QQQ", "NQ", "NQ", "MNQ", 2.0, 0.25, MICRO, True),
    ("DIA", "YM", "YM", "MYM", 0.5, 1.0, MICRO, True), ("IWM", "RTY", "RTY", "M2K", 5.0, 0.1, MICRO, True),
    ("TLT", "ZB", "ZB", "ZB", 1000.0, 1 / 32, STANDARD, True), ("IEF", "ZN", "ZN", "ZN", 1000.0, 1 / 64, STANDARD, True),
    ("IEI", "ZF", "ZF", "ZF", 1000.0, 1 / 128, STANDARD, True), ("SHY", "ZT", "ZT", "ZT", 2000.0, 1 / 256, STANDARD, True),
    ("GLD", "GC", "GC", "MGC", 10.0, 0.1, MICRO, True), ("SLV", "SI", "SI", "SIL", 1000.0, 0.005, MICRO, True),
    ("CPER", "HG", "HG", "MHG", 2500.0, 0.0005, MICRO, True), ("PPLT", "PL", "PL", "PL", 50.0, 0.1, STANDARD, True),
    ("PALL", "PA", "PA", "PA", 100.0, 0.5, STANDARD, True), ("USO", "CL", "CL", "MCL", 100.0, 0.01, MICRO, True),
    ("BNO", "BZ", "BZ", "BZ", 1000.0, 0.01, STANDARD, True), ("UNG", "NG", "NG", "QG", 2500.0, 0.005, STANDARD, True),
    ("UGA", "RB", "RB", "RB", 42000.0, 0.0001, STANDARD, True), ("FXE", "6E", "6E", "M6E", 12500.0, 0.0001, MICRO, True),
    ("FXY", "6J", "6J", "MJY", 1250000.0, 0.000001, MICRO, True), ("FXB", "6B", "6B", "M6B", 6250.0, 0.0001, MICRO, True),
    ("FXA", "6A", "6A", "M6A", 10000.0, 0.0001, MICRO, True), ("FXC", "6C", "6C", "MCD", 10000.0, 0.0001, MICRO, True),
    ("FXF", "6S", "6S", "MSF", 12500.0, 0.0001, MICRO, True), ("CORN", "ZC", "ZC", "XC", 10.0, 0.125, STANDARD, True),
    ("SOYB", "ZS", "ZS", "XK", 10.0, 0.125, STANDARD, True), ("WEAT", "ZW", "ZW", "XW", 10.0, 0.125, STANDARD, True),
    ("BITO", "BTC", "BTC", "MBT", 0.1, 5.0, MICRO, True),
]


def mouvements(etf):
    """Mouvement median sur l'horloge (relecture v5) : chaque jour est mis sur la grille 9 h 30, 9 h 35, ... 15 h 55 ;
    une paire (debut, fin) ne compte que si les deux barres existent (les ETF peu echanges ont des barres manquantes)."""
    b = pd.read_csv(LIBRES / "etf_5min" / f"{etf}.csv.gz", usecols=["t", "c"])
    b = b[b["t"] >= DEBUT]
    t = pd.to_datetime(b["t"])
    m = (t.dt.hour * 60 + t.dt.minute).to_numpy()
    garde = (m >= 570) & (m < 960) & ((m - 570) % 5 == 0)
    jours = b["t"].str[:10].to_numpy()[garde]
    case = (m[garde] - 570) // 5
    c = b["c"].to_numpy(float)[garde]
    uj, ij = np.unique(jours, return_inverse=True)
    grille = np.full((len(uj), 78), np.nan)
    grille[ij, case] = c
    out = {}
    for k, nom in ((1, 5), (3, 15), (6, 30)):
        a, z = grille[:, :-k:k], grille[:, k::k]
        r = np.abs(z / a - 1)[np.isfinite(a) & np.isfinite(z)]
        out[nom] = float(np.median(r)) * 1e4
    return out


def main():
    L = ["Couts d'un aller-retour (plus petit contrat CME, 2 commissions + 2 ticks) compares au mouvement median du "
         "marche, seance americaine, 2023 - fin des donnees (descriptif). Rapport = cout / mouvement median : au-dessus de "
         "0,3 environ, un scalping doit gagner plus d'un tiers du mouvement typique rien que pour payer ses frais.", "",
         "future contrat  cout (pb)  mouvement median 5 / 15 / 30 min (pb)   rapport 5 / 15 / 30 min"]
    lignes = []
    for etf, fut, yah, contrat, unite, tick, com, cme in MARCHES:
        y = pd.read_csv(LIBRES / "yahoo" / "jour" / f"{yah}.csv.gz", usecols=["t", "c"])
        prix = float(y.loc[y["t"] >= DEBUT, "c"].median())
        cout = (2 * com + 2 * tick * unite) / (prix * unite) * 1e4
        mv = mouvements(etf)
        lignes.append((cout / mv[15], f"{fut:<6} {contrat:<6} {cout:9.2f}   {mv[5]:8.1f} {mv[15]:8.1f} {mv[30]:8.1f}"
                                      f"              {cout / mv[5]:5.2f} {cout / mv[15]:5.2f} {cout / mv[30]:5.2f}"))
    L += [x for _, x in sorted(lignes)]
    SORTIE.mkdir(parents=True, exist_ok=True)
    (SORTIE / "couts.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
