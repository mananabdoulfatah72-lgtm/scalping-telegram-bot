#!/usr/bin/env python3
"""Tournoi n°6 (README.md) : 7 familles des tournois 1 et 4 sur RTY, YM, GC, CL, 6E, etape 1 sur 2016-2022, puis, si
une source est retenue, portefeuille avec la zone de bruit NQ juge une fois sur 2023-2026.
Lancer depuis ce dossier : python3 tournoi6.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

ICI = Path(__file__).resolve().parent
R = ICI.parent
for d in ("tournoi", "tournoi4", "zone_failles"):
    sys.path.insert(0, str(R / d))
import concurrents as K1  # noqa: E402
import explorer as EX  # noqa: E402
import journal as Z  # noqa: E402

NAN = np.nan
FRAIS_ORDRE = 1.0
# nom : (fichier, $ par point, tick, debut et fin de seance en minutes, heure de New York)   (comme zone_multi/)
MARCHES = {
    "RTY": (R / "zone_multi/donnees/russell_1min.csv.gz", 5.0, 0.10, 570, 960),
    "YM": (R / "zone_multi/donnees/dow_1min.csv.gz", 0.5, 1.0, 570, 960),
    "GC": (R / "zone_multi/donnees/or_1min.csv.gz", 10.0, 0.10, 500, 810),
    "CL": (R / "zone_multi/donnees/petrole_1min.csv.gz", 100.0, 0.01, 540, 870),
    "6E": (R / "zone_multi/donnees/euro_1min.csv.gz", 12500.0, 0.0001, 500, 900),
}
FAMILLES = ["Range d'ouverture 30 min", "Cassure de Williams", "Etirement de Crabel", "Cassure de la veille",
            "Momentum de la 1re heure", "Retournement apres 30 min extremes", "Rebond apres une forte baisse"]


def charger(fichier, m0, m1):
    """Tableaux (seances x minutes de la seance) ; comme zone_multi/analyse.py charger, avec le contrat."""
    n = m1 - m0
    d = pd.read_csv(fichier)
    t = pd.to_datetime(d["t"])
    minute = (t.dt.hour * 60 + t.dt.minute - m0).values
    garde = (minute >= 0) & (minute < n)
    d, t, minute = d[garde], t[garde], minute[garde]
    jour = t.dt.normalize()
    jours = np.sort(jour.unique())
    ij = np.searchsorted(jours, jour.values)
    tab = {}
    for col in "ohlc":
        a = np.full((len(jours), n), NAN)
        a[ij, minute] = d[col].values
        tab[col] = a
    P = ~np.isnan(tab["c"])
    C = pd.DataFrame(tab["c"]).ffill(axis=1).values
    for col in "ohl":
        tab[col] = np.where(np.isnan(tab[col]), C, tab[col])
    contrat = d.groupby(ij)["contrat"].last().reindex(range(len(jours))).values
    ech = np.r_[False, contrat[1:] != contrat[:-1]]
    return pd.DatetimeIndex(jours), tab["o"], tab["h"], tab["l"], C, P, {"echeance": ech, "contrat": contrat}


@njit(cache=True)
def cassure_n(O, H, L, C, ok, cout, haut, bas, stop_achat, stop_vente, debut):
    """concurrents.cassure pour une seance de n minutes (sortie a la derniere minute de la seance)."""
    nd, n = O.shape
    out = np.zeros(nd)
    for d in range(nd):
        if not ok[d] or np.isnan(haut[d]) or np.isnan(bas[d]):
            continue
        pos = 0
        e = 0.0
        stop = 0.0
        fini = False
        for m in range(debut, n):
            if pos == 0:
                up = H[d, m] > haut[d]
                dn = L[d, m] < bas[d]
                if up and dn:
                    fini = True
                    break
                if up:
                    pos, e, stop = 1, max(haut[d], O[d, m]), stop_achat[d]
                    if L[d, m] <= stop:
                        out[d] = (stop - e) - cout
                        fini = True
                        break
                elif dn:
                    pos, e, stop = -1, min(bas[d], O[d, m]), stop_vente[d]
                    if H[d, m] >= stop:
                        out[d] = (e - stop) - cout
                        fini = True
                        break
            else:
                if pos > 0 and L[d, m] <= stop:
                    out[d] = (min(stop, O[d, m]) - e) - cout
                    fini = True
                    break
                if pos < 0 and H[d, m] >= stop:
                    out[d] = (e - max(stop, O[d, m])) - cout
                    fini = True
                    break
        if not fini and pos != 0:
            out[d] = pos * (C[d, n - 1] - e) - cout
    return out


def familles(O, H, L, C, complete, ok, contrat, cout):
    """Points nets par seance pour chaque famille (memes formules que concurrents.toutes et strategies4)."""
    nd, n = O.shape
    prec = K1.precedente(complete, contrat)
    o0 = O[:, 0]
    hj, lj = H.max(axis=1), L.min(axis=1)
    h_v, l_v = K1.de_la(hj, prec), K1.de_la(lj, prec)
    rien = np.full(nd, NAN)
    res = {}
    hh, ll = H[:, :30].max(axis=1), L[:, :30].min(axis=1)
    res["Range d'ouverture 30 min"] = cassure_n(O, H, L, C, ok, cout, hh, ll, ll, hh, 30)
    amp = h_v - l_v
    res["Cassure de Williams"] = cassure_n(O, H, L, C, ok, cout, o0 + 0.5 * amp, o0 - 0.5 * amp, o0, o0, 0)
    etir = K1.glissant_complet(np.minimum(hj - o0, o0 - lj), complete, 10)
    res["Etirement de Crabel"] = cassure_n(O, H, L, C, ok, cout, o0 + etir, o0 - etir, o0 - etir, o0 + etir, 0)
    mil = (h_v + l_v) / 2
    res["Cassure de la veille"] = cassure_n(O, H, L, C, ok, cout, h_v, l_v, mil, mil, 0)
    s1h = np.nan_to_num(np.sign(C[:, 59] - o0)).astype(np.int64)
    res["Momentum de la 1re heure"] = K1.entree_fixe(O, H, L, C, ok, cout, s1h, 60, rien, rien, n - 1)
    r30 = C[:, 29] / o0 - 1
    moy30 = K1.glissant_complet(np.abs(r30), complete, 20)
    s_ext = np.where(np.abs(r30) > 1.5 * moy30, -np.sign(r30), 0).astype(np.int64)
    stop_ext = np.where(r30 > 0, H[:, :30].max(axis=1), L[:, :30].min(axis=1))
    res["Retournement apres 30 min extremes"] = K1.entree_fixe(O, H, L, C, ok, cout, s_ext, 30, stop_ext, rien, n - 1)
    rv = K1.de_la(C[:, n - 1] / o0 - 1, prec)
    v = np.isfinite(rv)
    seuil = np.full(nd, NAN)
    seuil[v] = pd.Series(rv[v]).rolling(252, min_periods=252).quantile(0.1).shift(1).values
    f7 = np.nan_to_num(rv <= seuil, nan=0).astype(bool)
    base = K1.entree_fixe(O, H, L, C, ok, cout, np.ones(nd, np.int64), 0, rien, rien, n - 1)
    res["Rebond apres une forte baisse"] = np.where(f7, base, 0.0)
    res["Achat simple (controle)"] = base
    return res


def main():
    sortie = []
    ecrire = lambda s="": (print(s, flush=True), sortie.append(s))
    # controle du code sur NQ
    import strategies4 as S4
    J, O, H, L, C, P, X = EX.charger("nasdaq100")
    cout_nq = K1.st.cout_aller_retour("nasdaq100")
    ref, ok_nq = K1.toutes(J, O, H, L, C, P, X, cout_nq)
    complete_nq = K1.st.journees_completes(P)
    mien = familles(O, H, L, C, complete_nq, ok_nq, X["contrat"], cout_nq)
    for nom in FAMILLES[:6]:
        assert np.allclose(mien[nom], ref[nom]), nom
    prec = S4.K1.precedente(complete_nq, X.get("contrat"))
    rv = S4.K1.de_la(C[:, 389] / O[:, 0] - 1, prec)
    f7 = np.nan_to_num(rv <= S4.quantile_valides(rv, 0.1), nan=0).astype(bool)
    rien = np.full(len(J), NAN)
    reb = np.where(f7, S4.K1.entree_fixe(O, H, L, C, ok_nq, cout_nq, np.ones(len(J), np.int64), 0, rien, rien, 389), 0.0)
    assert np.allclose(mien["Rebond apres une forte baisse"], reb)
    ecrire("Controle : sur NQ, les 7 familles generalisees redonnent exactement les tournois 1 et 4 : OK")
    # zone de bruit NQ (V1, robot) pour la correlation et le portefeuille : $ par jour pour 1 MNQ
    Jz, Oz, Hz, Lz, Cz, Pz, Xz = EX.charger("nasdaq100", fin=None)
    bz, az = Z.zone(Jz, Oz, Hz, Lz, Cz, Pz, Xz)
    okz = K1.st.journees_completes(Pz) & ~Xz["echeance"]
    zone = pd.Series(np.where(okz, (bz - 1.5 * az) * 2.0, 0.0), index=Jz)[okz]
    ecrire("\nEtape 1 : 2016-2022 (Russell : juillet 2017 - 2022), gains nets, 1 micro")
    lignes, series = [], {}
    for m, (fichier, pt, tick, m0, m1) in MARCHES.items():
        Jm, Om, Hm, Lm, Cm, Pm, Xm = charger(fichier, m0, m1)
        n = m1 - m0
        complete = Pm[:, 0] & Pm[:, n - 1] & (Pm.sum(axis=1) >= n - 20)
        ok = complete & ~Xm["echeance"]
        cout = (2 * FRAIS_ORDRE + 2 * tick * pt) / pt
        res = familles(Om, Hm, Lm, Cm, complete, ok, Xm["contrat"], cout)
        an = Jm.year
        for nom, pts in res.items():
            dol = pd.Series(pts * pt, index=Jm)[ok]
            series[(m, nom)] = dol
            r = pd.Series(pts / Om[:, 0], index=Jm)[ok]
            dev = r[(r.index.year >= 2016) & (r.index.year <= 2022)]
            a1, a2 = dev[dev.index.year <= 2019], dev[dev.index.year >= 2020]
            corr = float(dol.reindex(zone.index).dropna().corr(zone.reindex(dol.index).dropna())) if len(dol) else NAN
            tr = (dol[(dol.index.year >= 2016) & (dol.index.year <= 2022)] != 0)
            lig = {"marche": m, "famille": nom, "t": EX.t_stat(dev.values), "t_2016_2019": EX.t_stat(a1.values),
                   "t_2020_2022": EX.t_stat(a2.values), "jours_trade": int(tr.sum()),
                   "dollars_par_jour_trade": float(dol[(dol.index.year >= 2016) & (dol.index.year <= 2022)][tr].mean()) if tr.any() else 0.0,
                   "corr_zone": corr}
            lig["retenue"] = (nom != "Achat simple (controle)" and lig["t"] >= 2.5 and a1.mean() > 0 and a2.mean() > 0
                              and abs(corr) < 0.5)
            lignes.append(lig)
    df = pd.DataFrame(lignes)
    for m in MARCHES:
        ecrire(f"\n  {m}")
        for r in df[df.marche == m].itertuples():
            ecrire(f"    {r.famille:36s} t {r.t:+5.2f} (2016-19 {r.t_2016_2019:+5.2f}, 2020-22 {r.t_2020_2022:+5.2f}) | {r.jours_trade:4d} jours de trade,"
                   f" {r.dollars_par_jour_trade:+7.2f} $ par jour de trade | corr. zone {r.corr_zone:+.2f}{'  <= RETENUE' if r.retenue else ''}")
    df.to_csv(ICI / "etape1.csv", index=False, float_format="%.4g")
    ret = df[df.retenue]
    hors = df[df.famille != "Achat simple (controle)"]
    ecrire(f"\n{len(hors)} essais. t >= 2 : {int((hors.t >= 2).sum())} ; t >= 2,5 : {int((hors.t >= 2.5).sum())} ; t <= -2 : {int((hors.t <= -2).sum())}."
           f" Attendu par hasard pour t >= 2 : environ {0.023 * len(hors):.1f}.")
    ecrire(f"Sources retenues : {', '.join(f'{r.marche} {r.famille}' for r in ret.itertuples()) or 'aucune'}")
    if not len(ret):
        ecrire("Aucune source retenue : arret (README). 2023-2026 n'est pas regarde pour ces sources.")
    (ICI / "tournoi6.txt").write_text("\n".join(sortie) + "\n")
    return ret, series, zone


if __name__ == "__main__":
    main()
