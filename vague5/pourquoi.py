#!/usr/bin/env python3
"""Pourquoi 2025 et 2026 rapportent peu (descriptif, demande de l'utilisateur du 9 octobre 2026). Ecrit pourquoi.txt :
1. le bot seul, sans compte : gain sur 21 seances au niveau d'aujourd'hui, par annee de depart, source par source ;
2. l'agitation du NQ par annee (ecart moyen entre plus haut et plus bas d'une seance, en % et en $ par MNQ aujourd'hui) ;
3. les comptes de la vague 5 par annee d'achat : challenges reussis / perdus, comptes finances perdus, retraits."""
import multiprocessing as mp

import numpy as np
import pandas as pd

import vague5 as W

U, MS, D4, M4, CP, F = W.U, W.MS, W.D4, W.M4, W.CP, W.F
STATIC = dict(compte="Static", bot="E4", ch=2, fi=1, re=0)
TOPSTEP = dict(compte="Topstep", bot="zone + A3", ch=2, fi=2, re=0)
BON = "filtre aussi bon qu'en 2026 (simule)"


def bot_seul(args):
    """Gain sur 21 seances de chaque depart (sans compte), pour une source et un tirage du filtre."""
    source, i = args
    DS = W.G["DS"]
    g = W.G["gardes"][i] if i >= 0 else None
    nz = len(DS["Z"])
    if source == "RSI(2) seul (1 MES)":
        g = np.zeros(nz, bool)
    b = U.base(DS, g)
    v = "E1" if source == "zone seule (1 MNQ)" else "E4"
    out = {}
    for d in U.departs(DS, 1):
        if d + 21 > len(DS["jours"]) or DS["jours"][d].year < 2012:
            continue
        tr = np.zeros(21)
        U.achat(DS, b, d, v, perte=1e12, objectif=1e12, h2=21, trace=tr)
        out[d] = tr[-1]
    return out


def parcours_static(D, b, d, h):
    r = U.achat(D, b, d, STATIC["bot"], plafond=500.0, h1=h, h2=h, leviers=(2, 1, W.SEUIL, 0.0))
    issue = int(r[MS.ISSUE])
    fin = int(r[MS.FIN_EVAL]) if issue == -1 else (int(r[MS.FIN_PRO]) if r[MS.PRO_PERDU] == 1 else h)
    return issue, int(r[MS.FIN_EVAL]), bool(r[MS.PRO_PERDU] == 1), fin, r[MS.RECU2]


def parcours_topstep(D, b, d, h):
    e, f_ = CP.COMPTES["Topstep"][:7], F.FINANCES["Topstep"]["f"]
    fn, fe = D4.facteurs(D, d)
    r = M4.parcours4(d, 4, 2.0 * fn, 5.0 * fe, np.zeros(0), *b, *e, *f_, h, 2, 2, W.SEUIL, 0.0)
    return int(r[0]), int(r[1]), bool(r[2]), int(r[6]), r[4] * F.FINANCES["Topstep"]["part"]


def comptes(args):
    """Chaines d'un tirage : chaque compte achete (date, issue du challenge, seances du challenge, finance perdu, fin)."""
    nom, i = args
    D = W.G["D4"]
    j = D["jours"]
    w0, w1 = int(np.searchsorted(j, pd.Timestamp("2023-01-01"))), len(j)
    g = W.G["gardes"][i]
    if nom == "Static":
        b, f = U.base(W.G["DS"], g), parcours_static
        DD = W.G["DS"]
    else:
        b, f = D4.base(D, g), parcours_topstep
        DD = D
    rows = []
    for k in range(20):
        d = w0 + 5 * k
        while True:
            while d < w1 and D["ouvert"][d] != 0:
                d += 1
            if d >= w1:
                break
            h = min(W.H2, w1 - d)
            issue, nch, perdu, fin, recu = f(DD, b, d, h)
            rows.append((k, j[d], issue, nch, perdu, fin, recu, j[min(d + fin, w1) - 1]))
            d += fin
    return rows


def main():
    W.G["D4"] = W.D4.charger()
    W.G["DS"] = W.DN.charger()
    D, DS = W.G["D4"], W.G["DS"]
    j = D["jours"]
    rho = W.S.rho_2026()
    W.G["gardes"] = W.S.gardes_simules(D, rho)[:W.TIRAGES]
    L = ["Pourquoi 2025 et 2026 rapportent peu (descriptif). Niveau d'aujourd'hui ; filtre simule aussi bon qu'en 2026"
         f" (rho {rho:.2f}, {W.TIRAGES} tirages) quand il est indique.", ""]
    # 1. le bot seul
    sources = ["zone seule (1 MNQ)", "RSI(2) seul (1 MES)", "zone + RSI(2) (Static E4)"]
    taches = [(s, -1) for s in sources] + [(s, i) for s in sources[::2] for i in range(W.TIRAGES)]
    with mp.get_context("fork").Pool(4) as p:
        res = p.map(bot_seul, taches)
    L += ["=== 1. Le bot seul, sans compte : gain moyen sur 21 seances (un mois) selon l'annee de depart",
          "source | " + " | ".join(str(y) for y in range(2019, 2027))]
    for s in sources:
        for filtre in ([False, True] if s != "RSI(2) seul (1 MES)" else [False]):
            xs = [r for (src, i), r in zip(taches, res) if src == s and (i >= 0) == filtre]
            ser = pd.concat([pd.Series(x) for x in xs])
            an = pd.Series([j[d].year for d in ser.index], index=ser.index)
            m = ser.groupby(an.values).mean()
            L.append(f"{s}{', filtre simule' if filtre else ''} | " + " | ".join(f"{m.get(y, np.nan):+,.0f} $"
                                                                               for y in range(2019, 2027)))
    # 2. agitation du NQ
    der = D["derniere"]
    nj = len(j)
    hh = np.array([np.nanmax(D["H"][d, :der[d] + 1]) for d in range(nj)])
    ll = np.array([np.nanmin(D["L"][d, :der[d] + 1]) for d in range(nj)])
    cl = D["cl_nq"]
    ecart = pd.Series((hh - ll) / cl, index=j)
    L += ["", "=== 2. Agitation du NQ : ecart moyen entre le plus haut et le plus bas de la seance (9 h 30 - 16 h)",
          "annee | en % du prix | en $ par MNQ au prix d'aujourd'hui"]
    for y in range(2019, 2027):
        e = ecart[ecart.index.year == y].mean()
        L.append(f"{y} | {e:.2%} | {e * cl[-1] * 2.0:,.0f} $")
    # 3. les comptes par annee d'achat
    for nom in ("Static", "Topstep"):
        with mp.get_context("fork").Pool(4) as p:
            rows = sum(p.map(comptes, [(nom, i) for i in range(W.TIRAGES)]), [])
        df = pd.DataFrame(rows, columns=["k", "achat", "issue", "nch", "perdu", "fin", "recu", "date_fin"])
        df["an"] = df["achat"].dt.year
        L += ["", f"=== 3. {W.nom(STATIC if nom == 'Static' else TOPSTEP)} : comptes achetes par annee d'achat (un seul"
                  " compte a la fois, 20 departs x 10 tirages)",
              "annee d'achat | achats | challenge reussi | seuil touche | seances avant le seuil (mediane) | finance"
              " perdu (parmi les reussis) | vie du finance (mediane, seances) | retraits recus par achat"]
        for y, g in df.groupby("an"):
            ok, ko = g["issue"] == 1, g["issue"] == -1
            vie = (g["fin"] - g["nch"])[ok]
            L.append(f"{y} | {len(g)} | {ok.mean():.0%} | {ko.mean():.0%} | {g['nch'][ko].median():.0f} |"
                     f" {g['perdu'][ok].mean():.0%} | {vie.median():.0f} | {g['recu'].mean():,.0f} $")
    (W.ICI / "pourquoi.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
