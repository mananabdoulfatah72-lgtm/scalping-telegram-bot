#!/usr/bin/env python3
"""etude_large/crypto/README.md (regles fixees le 22 octobre 2026, avant le telechargement des donnees) : la cassure
des 30 premieres minutes (A3b de la partie A) sur le bitcoin Coinbase 2017 - 2026.
Test 1 : regle inchangee sur P0 (2017 - septembre 2021, jamais vue). Test 2 : 24 variantes en walk-forward 2018 - 2026.
Test 3 : placebo d'heure. Test 4 (si 1 ou 2 reussit) : complement de la zone. ETH : descriptif.

Lancer : python3 etude_large/crypto/etude.py (numpy, pandas ; variable KB comme delta_mesures pour la zone du bot).
Ecrit resultats.txt."""
import itertools
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(ICI.parent))
import partie_a as PA  # noqa: E402

DONNEES = RACINE / "donnees_libres" / "crypto"
NB = PA.NB
P0 = ("2017-01-03", "2021-09-30")
P1 = ("2021-10-01", "2026-10-20")
REF = "2026-10-20"
# contrat : (unite du contrat, tick en $ par unite de prix x unite, commission par ordre)
CONTRATS = {"BTC": (0.1, 0.5, 2.5), "ETH": (0.1, 0.05, 2.5)}
GRILLE = list(itertools.product([3, 6, 12], ["autre extreme", "milieu"], [29, 71], ["16 h", "2 x range"]))
PLACEBOS = [0, 180, 360, 720, 780]           # debut de la fenetre, minutes apres minuit (New York)


def lire(actif):
    f = sorted(DONNEES.glob(f"{actif.lower()}_*_5m.csv.gz"))
    d = pd.concat([pd.read_csv(x) for x in f], ignore_index=True)
    d["t"] = pd.to_datetime(d["t"])
    return d.drop_duplicates("t").sort_values("t").reset_index(drop=True)


def tableaux(d, jours, debut=570):
    """Comme partie_a.tableaux, pour une fenetre de 78 barres de 5 minutes qui commence a debut (minutes apres
    minuit, New York)."""
    jour = d["t"].dt.normalize().values
    b = ((d["t"].dt.hour * 60 + d["t"].dt.minute - debut) // 5).values
    i = np.searchsorted(jours.values, jour)
    ok = (i < len(jours)) & (b >= 0) & (b < NB)
    ok &= jours.values[np.minimum(i, len(jours) - 1)] == jour
    i, b, x = i[ok], b[ok], d[ok]
    tab = {}
    for col in "ohlcv":
        a = np.full((len(jours), NB), np.nan)
        a[i, b] = x[col].values
        tab[col] = a
    present = ~np.isnan(tab["c"])
    C = pd.DataFrame(tab["c"]).ffill(axis=1).values
    premiere = np.argmax(present, axis=1)
    jouable = present[:, :6].any(axis=1)
    O0 = tab["o"][np.arange(len(jours)), premiere]
    C = np.where(np.isnan(C), O0[:, None], C)
    H = np.where(np.isnan(tab["h"]), C, tab["h"])
    L = np.where(np.isnan(tab["l"]), C, tab["l"])
    return dict(O0=np.where(jouable, O0, np.nan), H=H, L=L, C=C, V=np.nan_to_num(tab["v"]), jouable=jouable)


def cassure(x, k, cout, nr, stop_mode, derniere, sortie):
    """Cassure du range des nr premieres barres : premiere cloture au-dela, de la barre nr a derniere ; stop a l'autre
    extreme ou au milieu du range ; sortie a 16 h ou a l'objectif de 2 fois la hauteur du range."""
    H, L, C = x["H"][k], x["L"][k], x["C"][k]
    hh, ll = H[:nr].max(), L[:nr].min()
    for m in range(nr, min(derniere, NB - 2) + 1):
        sens = 1 if C[m] > hh else (-1 if C[m] < ll else 0)
        if sens:
            stop = (ll if sens > 0 else hh) if stop_mode == "autre extreme" else (hh + ll) / 2
            if sortie == "16 h":
                obj = np.inf if sens > 0 else -np.inf
            else:
                obj = C[m] + sens * 2 * (hh - ll)
            ps = PA.sortie_stop(x, k, m + 1, sens, C[m], stop, obj)
            return sens * (ps / C[m] - 1) - cout
    return 0.0


def serie(x, cout, *variante):
    out = np.zeros(len(x["C"]))
    for k in np.where(x["jouable"])[0]:
        out[k] = cassure(x, k, cout, *variante)
    return out


FIXE = (6, "autre extreme", NB - 2, "16 h")          # A3b de la partie A


def periode(jours, a, b):
    return (jours >= a) & (jours <= b)


def main():
    jours = PA.calendrier()
    jours = jours[(jours >= P0[0]) & (jours <= P1[1])]
    m0, m1 = periode(jours, *P0), periode(jours, *P1)
    t = PA.t_stat
    L = ["Vague bitcoin (etude_large/crypto/README.md, regles fixees le 22 octobre 2026 avant le telechargement)", ""]
    btc = lire("BTC")
    x = tableaux(btc, jours)
    pref = float(x["C"][np.where(jours == pd.Timestamp(REF))[0][0], NB - 1])
    u, tick, comm = CONTRATS["BTC"]
    cout = (2 * comm + 2 * tick) / (u * pref)
    L.append(f"BTC Coinbase : {len(btc)} barres, {btc['t'].iloc[0]} -> {btc['t'].iloc[-1]} ; seances jouables P0 "
             f"{int(x['jouable'][m0].sum())} / {int(m0.sum())}, P1 {int(x['jouable'][m1].sum())} / {int(m1.sum())} ; "
             f"prix du {REF} {pref:,.0f} $ ; frais MBT {cout * 1e4:.2f} pb par aller-retour")
    # controle : Coinbase contre BITO sur P1 (BITO depuis le 19 octobre 2021)
    jb = jours[m1]
    rb, _, xb = PA.series("BITO", jb, np.full(len(jb), cout))
    r_cb = serie(x, cout, *FIXE)
    ok = xb["jouable"]
    corr = float(np.corrcoef(rb["A3b OPR 30 min"][ok], r_cb[m1][ok])[0, 1])
    L.append(f"CONTROLE : correlation des seances A3b Coinbase / BITO sur P1 ({int(ok.sum())} seances) : {corr:.2f} -> "
             f"{'donnees acceptees (>= 0,7)' if corr >= 0.7 else 'ECART (< 0,7)'}")
    L.append("")
    # test 1
    brut = serie(x, 0.0, *FIXE)
    double = serie(x, 2 * cout, *FIXE)
    t1 = t(r_cb[m0])
    L += ["TEST 1 : regle inchangee (A3b) sur P0, jamais vue",
          f"  P0 2017 - sept. 2021 : t net {t1:+.2f} (avant frais {t(brut[m0]):+.2f}, frais doubles {t(double[m0]):+.2f}), "
          f"Sharpe {PA.sharpe(r_cb[m0]):+.2f}, {int((r_cb[m0] != 0).sum())} trades",
          f"  P1 oct. 2021 - 2026 : t net {t(r_cb[m1]):+.2f} (avant frais {t(brut[m1]):+.2f}, frais doubles "
          f"{t(double[m1]):+.2f}) ; BITO dans la partie A : +1,64 / +1,87",
          "  par annee (t net) : " + ", ".join(f"{y} {t(r_cb[jours.year == y]):+.2f}" for y in range(2017, 2027)),
          f"  -> {'CONFIRMEE (t >= 2,0 sur P0)' if t1 >= 2.0 else 'NON CONFIRMEE (t < 2,0 sur P0)'}", ""]
    # test 2
    series_v = {v: serie(x, cout, *v) for v in GRILLE}
    oos = np.zeros(len(jours))
    choix = []
    for Y in range(2018, 2027):
        avant = (jours >= P0[0]) & (jours.year < Y)
        best = max(GRILLE, key=lambda v: t(series_v[v][avant]))
        an = jours.year == Y
        oos[an] = series_v[best][an]
        choix.append((Y, best, t(series_v[best][avant])))
    wf = jours.year >= 2018
    t2 = t(oos[wf])
    p0w, p1w = wf & m0, wf & m1
    ok2 = t2 >= 2.0 and oos[p0w].sum() > 0 and oos[p1w].sum() > 0
    L.append("TEST 2 : 24 variantes, walk-forward (variante choisie chaque annee sur les annees precedentes)")
    for Y, v, tv in choix:
        L.append(f"  {Y} : range {v[0] * 5} min, stop {v[1]}, derniere entree {'12 h' if v[2] == 29 else '15 h 30'}, "
                 f"sortie {v[3]} (t passe {tv:+.2f}) -> t de l'annee {t(series_v[v][jours.year == Y]):+.2f}")
    L += [f"  serie hors echantillon 2018 - 2026 : t net {t2:+.2f} ; gain P0 {oos[p0w].sum() * 1e4:+.0f} pb, P1 "
          f"{oos[p1w].sum() * 1e4:+.0f} pb ; regle fixe sur 2018 - 2026 : t {t(r_cb[wf]):+.2f}",
          f"  -> {'RETENUE' if ok2 else 'NON RETENUE'}"]
    tous = sorted(GRILLE, key=lambda v: -t(series_v[v]))
    L.append("  pour information (choisi apres coup, donc gonfle), les 5 meilleures variantes sur 2017 - 2026 :")
    for v in tous[:5]:
        L.append(f"    range {v[0] * 5} min, stop {v[1]}, derniere entree {'12 h' if v[2] == 29 else '15 h 30'}, "
                 f"sortie {v[3]} : t {t(series_v[v]):+.2f} (P0 {t(series_v[v][m0]):+.2f}, P1 {t(series_v[v][m1]):+.2f})")
    L.append(f"  mediane des 24 variantes : t {np.median([t(series_v[v]) for v in GRILLE]):+.2f}")
    L.append("")
    # test 3
    L.append("TEST 3 : placebo d'heure (regle fixe, range de 30 minutes, fenetre de 6 h 30), t net 2017 - 2026")
    L.append(f"  9 h 30 (la vraie) : {t(r_cb):+.2f}")
    for deb in PLACEBOS:
        xp = tableaux(btc, jours, deb)
        L.append(f"  {deb // 60:02d} h {deb % 60:02d} : {t(serie(xp, cout, *FIXE)):+.2f}")
    L.append("")
    # test 4
    if t1 >= 2.0 or ok2:
        r = oos if ok2 and not t1 >= 2.0 else r_cb
        zb, _ = PA.zone_bot(jours)
        c1 = float(np.corrcoef(r[m1], zb[m1])[0, 1])
        w = zb[m0].std() / r[m0].std()
        comb = zb + w * r
        ok4 = c1 < 0.3 and PA.sharpe(comb[m1]) > PA.sharpe(zb[m1])
        L += ["TEST 4 : complement de la zone",
              f"  correlation avec la zone sur P1 {c1:+.2f} ; Sharpe P1 zone {PA.sharpe(zb[m1]):+.2f}, zone + bitcoin "
              f"{PA.sharpe(comb[m1]):+.2f} -> {'complement RETENU' if ok4 else 'complement non retenu'}", ""]
    else:
        L += ["TEST 4 : non fait (ni le test 1 ni le test 2 ne reussit, regle fixee d'avance)", ""]
    # ETH descriptif
    try:
        eth = lire("ETH")
        xe = tableaux(eth, jours)
        pe = float(xe["C"][np.where(jours == pd.Timestamp(REF))[0][0], NB - 1])
        u, tick, comm = CONTRATS["ETH"]
        ce = (2 * comm + 2 * tick) / (u * pe)
        re, be = serie(xe, ce, *FIXE), serie(xe, 0.0, *FIXE)
        L += ["ETH (descriptif) : A3b, frais du Micro Ether "
              f"{ce * 1e4:.0f} pb par aller-retour",
              f"  P0 : t net {t(re[m0]):+.2f}, avant frais {t(be[m0]):+.2f} ; P1 : t net {t(re[m1]):+.2f}, avant frais "
              f"{t(be[m1]):+.2f}"]
    except (ValueError, IndexError) as e:
        L.append(f"ETH : donnees absentes ({e})")
    (ICI / "resultats.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
