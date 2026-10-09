#!/usr/bin/env python3
"""Vague 5, etape 1 (descriptif, README.md) : le meme chiffre pour chaque compte deja simule - un seul compte a la fois,
rachete des qu'il est perdu, gains nets par mois du calendrier (retraits - prix - activation) - avec le systeme deja
retenu sur ce compte, au niveau d'aujourd'hui, sans filtre et avec le filtre delta simule. Sert a choisir le compte sur
lequel chercher. Ecrit socle.txt."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
R0 = ICI.parent
sys.path.insert(0, str(R0 / "vague4"))
sys.path.insert(0, str(R0 / "static50k"))
import donnees4 as D4  # noqa: E402
import moteur4 as M4  # noqa: E402
import vague4 as V  # noqa: E402
import donnees as DN  # noqa: E402
import moteur_static as MS  # noqa: E402
import outils as U  # noqa: E402

S, CP, F = V.S, V.CP, V.F
MOIS, H2, DEPARTS, TIRAGES = 21, 504, 20, 10
PRIX_STATIC, ACTIVATION_PRO = 30.0, 130.0


def lien_intraday(D, b, nc, rsi):
    """Un achat chez Topstep ou Tradeify (moteur de la vague 4). Renvoie une fonction (d, h) -> (flux, fin)."""
    e, f_ = CP.COMPTES[nc][:7], F.FINANCES[nc]["f"]
    prix, mensuel, activation = F.FINANCES[nc]["prix"]
    part = F.FINANCES[nc]["part"]

    def lien(d, h):
        fn, fe = D4.facteurs(D, d)
        ret = np.zeros(h)
        r = M4.parcours4(d, rsi, 2.0 * fn, 5.0 * fe, ret, *b, *e, *f_, h)
        fl = ret * part
        for k in range(int(np.ceil(r[1] / MOIS)) if mensuel else 1):
            fl[MOIS * k] -= prix
        if r[0] == 1:
            fl[r[1] - 1] -= activation
        return fl, r[6]
    return lien


def lien_static(D, b, variante, cap, regle, prix):
    """Un Static (regle 0 : Pro au plancher fixe ; 1 : Pro pessimiste) ou un S2F (regle 2). prix : (premier achat,
    rachats)."""
    def lien(d, h, premier):
        ret = np.zeros(h)
        r = U.achat(D, b, d, variante, plafond=cap, pessimiste=1 if regle == 1 else 0, h1=h, h2=h, retraits=ret,
                    s2f=regle == 2)
        fl = ret.copy()
        fl[0] -= prix[0] if premier else prix[1]
        if regle != 2 and r[MS.ISSUE] == 1:
            fl[int(r[MS.FIN_EVAL]) - 1] -= ACTIVATION_PRO
        if r[MS.ISSUE] == -1:
            fin = int(r[MS.FIN_EVAL])
        elif r[MS.PRO_PERDU] == 1:
            fin = int(r[MS.FIN_PRO])
        else:
            fin = h
        return fl, fin
    return lien


def chaine(D, lien, d, w1, statique):
    """Un seul compte a la fois, de d a w1. Renvoie les flux par seance et le nombre d'achats."""
    flux, n = np.zeros(len(D["jours"])), 0
    while True:
        while d < w1 and D["ouvert"][d] != 0:
            d += 1
        if d >= w1:
            return flux, n
        h = min(H2, w1 - d)
        fl, fin = lien(d, h, n == 0) if statique else lien(d, h)
        assert 1 <= fin <= h
        flux[d:d + h] += fl
        n += 1
        d += fin


def mesurer(D, liens, w0, w1, statique):
    j = D["jours"]
    mc = pd.PeriodIndex(j[w0:w1], freq="M")
    M_, nb = [], []
    for lien in liens:
        for k in range(DEPARTS):
            fl, n = chaine(D, lien, w0 + 5 * k, w1, statique)
            m_ = pd.Series(fl[w0:w1]).groupby(mc).sum()
            m_[m_.index < mc[5 * k]] = np.nan
            M_.append(m_)
            nb.append(n / ((w1 - w0 - 5 * k) / 252))
    tous = pd.concat(M_, axis=1)
    moy = tous.mean(axis=1)
    v = tous.stack()
    an = moy.groupby(moy.index.year).mean()
    return (f"{moy.mean():+,.0f} $ | {(v > 0).mean():.0%} | {np.mean(nb):.1f} | {tous.mean().min():+,.0f} a"
            f" {tous.mean().max():+,.0f} $ | " + ", ".join(f"{y} {x:+,.0f}" for y, x in an.items()))


def main():
    D4_ = D4.charger()
    DS_ = DN.charger()
    j = D4_["jours"]
    assert (DS_["jours"] == j).all()
    rho = S.rho_2026()
    gb, gi = S.gardes_simules(D4_, rho)[:TIRAGES], S.gardes_simules(D4_, 0.0)[:TIRAGES]
    scen = {"sans filtre": [None], "filtre aussi bon qu'en 2026 (simule)": gb, "filtre inutile (simule)": gi}
    fen = {"2012 - 2022": ("2012-01-01", "2023-01-01"), "2023 - sept. 2026": ("2023-01-01", None)}
    systemes = [
        ("Topstep, zone + A3", "i", ("Topstep", 4)),
        ("Tradeify Growth, zone seule", "i", ("Tradeify Growth", 0)),
        ("DayTraders Static, E0 P500 (Pro au plancher fixe)", "s", ("E0", 500.0, 0, (PRIX_STATIC, PRIX_STATIC))),
        ("DayTraders Static, E0 P500 (Pro pessimiste)", "s", ("E0", 500.0, 1, (PRIX_STATIC, PRIX_STATIC))),
        ("DayTraders S2F, E0 P500 (570 $ puis 342 $)", "s", ("E0", 500.0, 2, (570.0, 342.0))),
    ]
    L = [f"Vague 5, etape 1 (descriptif) : un seul compte a la fois, rachete des qu'il est perdu (ou apres 24 mois), gains"
         f" nets par mois du calendrier, niveau d'aujourd'hui ; {DEPARTS} departs x {TIRAGES} tirages du filtre simule"
         f" (rho {rho:.2f}). Donnees jusqu'au {j[-1].date()}.",
         "systeme | scenario | fenetre | moyenne par mois | mois > 0 | achats par an | selon le depart | par annee"]
    for nom, genre, p in systemes:
        for sc, gardes in scen.items():
            for fw, (a, z) in fen.items():
                w0 = int(np.searchsorted(j, pd.Timestamp(a)))
                w1 = len(j) if z is None else int(np.searchsorted(j, pd.Timestamp(z)))
                if genre == "i":
                    liens = [lien_intraday(D4_, D4.base(D4_, g), *p) for g in gardes]
                    x = mesurer(D4_, liens, w0, w1, False)
                else:
                    liens = [lien_static(DS_, U.base(DS_, g), *p) for g in gardes]
                    x = mesurer(DS_, liens, w0, w1, True)
                L.append(f"{nom} | {sc} | {fw} | {x}")
                print(L[-1], flush=True)
    (ICI / "socle.txt").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
