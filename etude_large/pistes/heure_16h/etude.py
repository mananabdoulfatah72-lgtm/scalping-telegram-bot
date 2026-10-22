#!/usr/bin/env python3
"""etude_large/pistes/README.md, piste 2 (regles fixees le 22 octobre 2026, commit a6e791f, avant tout calcul) :
l'heure 16 h 00 - 16 h 59 du NQ (et de l'ES), H1 a H5.

H1 : prolonger la position de zone V1 encore ouverte a 15 h 59 jusqu'a la cloture de la barre de 16 h (test bilateral).
H2 : retour de la journee (NQ) : S = ln(C15:59 / C15:59 de la veille), actif si |S| >= 80e centile des 252 seances
     completes precedentes, position -signe(S) de O16 a C16.
H3 : retour de la derniere demi-heure (NQ) : L = ln(C15:59 / C15:29), meme seuil, position -signe(L).
H4 : H2 sur l'ES (MES).
H5 : signal de H2, prix HistData usatechidxusd 5 minutes : ouverture de la barre de 16 h 00 -> cloture de la barre de
     16 h 10 (16 h 15, compatible Lucid).

Briques reutilisees sans changement : delta_mesures/etude.py (preparer, trades_zone, RECHERCHE, ROBOT, FIN),
zone/robot.py (tableaux, seances_completes, precedente, jour_court), etude_large/partie_d.py (chemins_zone, defi,
tous_les_departs, limites_depart, FIRMES), etude_large/partie_a.py (t_stat, sharpe, p_unilateral), kb/fonds/fomc.py.

Choix d'interpretation fixes AVANT tout calcul (voir aussi resultats.txt) :
- calendrier des series quotidiennes : toutes les seances des minutes du NQ (0 sans trade) ;
- jour t : la minute du signal doit exister (15 h 59, et 15 h 29 pour H3 ; 12 h 59 et 12 h 29 pour le temoin), sans
  exiger la seance complete (ce serait un regard vers le futur pour le temoin de 13 h) ; l'historique du seuil ne
  contient que des seances completes (README) ;
- placebo sur l'exploration ; frais de sensibilite sur l'exploration ET le coffre ; H1 (prolonger) : 0,75 point de
  plus par trade aux frais de sensibilite (la moitie du supplement d'un aller-retour : seule la sortie passe dans
  l'heure peu liquide) ;
- critere 6 en rendements (points / prix), comme la partie C (partie_a.py) ; poids a risque egal sur l'exploration ;
- critere 7 : la zone + la piste doit valider au moins autant que la zone seule (departs 2023 - fin du coffre), a 3 ET
  4 MNQ chez Bulenox (H1 a H4), a 1 MNQ chez Lucid Flex (H5).

Lancer : export KB=<branche de recherche extraite> ; python3 etude_large/pistes/heure_16h/etude.py
Ecrit resultats.txt dans ce dossier."""
import os
import sys
import tempfile

sys.dont_write_bytecode = True
os.environ.setdefault("NUMBA_CACHE_DIR", str(os.path.join(tempfile.gettempdir(), "numba_heure_16h")))

from math import erf, sqrt  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ICI = Path(__file__).resolve().parent
LARGE = ICI.parent.parent
RACINE = LARGE.parent
if str(ICI) in sys.path:
    sys.path.remove(str(ICI))            # ce fichier s'appelle aussi etude.py : jamais importe a la place de DM
sys.path.insert(0, str(RACINE / "delta_mesures"))
import etude as DM  # noqa: E402
sys.path.insert(0, str(LARGE))
import partie_a as PA  # noqa: E402
import partie_d as PD  # noqa: E402
sys.path.insert(0, str(DM.KB / "fonds"))
import fomc  # noqa: E402

RB, N = DM.RB, DM.N
KB = DM.KB
HEURE_NQ = KB / "nuit" / "donnees" / "nasdaq100_1h.csv.gz"
HEURE_ES = KB / "nuit" / "donnees" / "sp500_1h.csv.gz"
MINUTES_ES = KB / "intraday" / "donnees" / "sp500_1min.csv.gz"
HISTDATA = sorted((KB / "sessions24" / "annees").glob("usatechidxusd_*_5m.csv.gz"))

COUT = {"NQ": 1.5, "ES": 0.9}
COUT_SENS = {"NQ": 3.0, "ES": 1.8}
SUPPL_H1 = 0.75                       # H1 prolonger : supplement de sensibilite (sortie seule dans l'heure peu liquide)
PT = {"NQ": 2.0, "ES": 5.0}           # $ par point : MNQ, MES
CENTILE, FENETRE = 0.8, 252
M1559, M1529, M1259, M1229 = N - 1, N - 31, 209, 179
EXPLO = ("2011-01-01", "2022-12-31")
EXPLO_H5 = ("2012-01-01", "2022-12-31")
COFFRE = ("2023-01-01", "2026-09-28")
COFFRE_H5 = ("2023-01-01", "2026-10-02")
CORR = ("2016-01-01", "2022-12-31")
SOUS = [("2011-14", "2011-01-01", "2014-12-31"), ("2015-18", "2015-01-01", "2018-12-31"),
        ("2019-22", "2019-01-01", "2022-12-31"), ("2023-26", "2023-01-01", "2026-12-31")]
N_SIGNES, N_H1, GRAINE = 1000, 200, 16
BULENOX, LUCID = "Bulenox Legacy 50K opt. 2", "Lucid Flex 50K"
TAILLES_BULENOX = [3, 4]


# ----------------------------------------------------------------------------- donnees
def marche(d):
    """Tableaux minute (RB.tableaux) + seances completes, veille du meme contrat, contrat de la seance."""
    jours, O, H, L, C, P, V, ech = RB.tableaux(d)
    ok = RB.seances_completes(P)
    prec = RB.precedente(ok, np.cumsum(ech))
    t = pd.to_datetime(d["t"])
    ij = np.searchsorted(jours.values, t.dt.normalize().values)
    contrat = d.groupby(ij)["contrat"].last().reindex(range(len(jours))).values
    return dict(jours=jours, O=O, H=H, L=L, C=C, P=P, ok=ok, prec=prec, contrat=contrat)


def barres_heure(f, heure):
    """Barre d'une heure commencant a `heure` (heure de New York) : date -> o, h, l, c, contrat."""
    h = pd.read_csv(f)
    t = pd.to_datetime(h["t"])
    b = h[(t.dt.hour == heure) & (t.dt.minute == 0)].copy()
    b.index = pd.to_datetime(b["t"]).dt.normalize()
    return b[["o", "h", "l", "c", "v", "contrat"]]


def histdata():
    """Barres HistData de 5 minutes (UTC) en heure de New York : DataFrame indexe par (date, 'HH:MM')."""
    d = pd.concat([pd.read_csv(f) for f in HISTDATA]).drop_duplicates("t", keep="last")
    t = pd.to_datetime(d["t"]).dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    d = d.assign(jour=t.dt.tz_localize(None).dt.normalize().values, hm=t.dt.strftime("%H:%M").values)
    return d.set_index(["jour", "hm"])[["o", "h", "l", "c"]].sort_index()


def hd_fenetre(hd, debut, fin_barre, barres):
    """Par date : ouverture de la barre `debut`, cloture de la barre `fin_barre`, plus haut / plus bas des barres listees
    (seulement les dates ou les deux barres existent)."""
    o = hd.xs(debut, level="hm")["o"]
    c = hd.xs(fin_barre, level="hm")["c"]
    j = o.index.intersection(c.index)
    hh = pd.concat([hd.xs(b, level="hm")["h"] for b in barres], axis=1, sort=True).max(axis=1)
    ll = pd.concat([hd.xs(b, level="hm")["l"] for b in barres], axis=1, sort=True).min(axis=1)
    return pd.DataFrame({"o": o[j], "c": c[j], "h": hh.reindex(j), "l": ll.reindex(j)})


# ----------------------------------------------------------------------------- signaux
def seuil_passe(val, historique):
    """80e centile des |val| des 252 seances de l'historique (seances completes ou val est defini) strictement avant
    chaque seance (passe seulement)."""
    idx = np.where(historique)[0]
    roll = pd.Series(np.abs(val[idx])).rolling(FENETRE, min_periods=FENETRE).quantile(CENTILE).values
    k = np.searchsorted(idx, np.arange(len(val))) - 1
    return np.where(k >= 0, roll[np.maximum(k, 0)], np.nan)


def signal_jour(M, m):
    """S = ln(C_m / C_m de la veille), veille = derniere seance complete du meme contrat. Renvoie (S, seuil, actif)."""
    C, prec = M["C"], M["prec"]
    S = np.where(prec >= 0, np.log(C[:, m] / C[np.maximum(prec, 0), m]), np.nan)
    hist = M["ok"] & np.isfinite(S)
    thr = seuil_passe(S, hist)
    actif = M["P"][:, m] & np.isfinite(S) & np.isfinite(thr) & (np.abs(S) >= thr) & (S != 0)
    return S, thr, actif


def signal_demi_heure(M, m, m30):
    C = M["C"]
    Lr = np.log(C[:, m] / C[:, m30])
    hist = M["ok"] & np.isfinite(Lr)
    thr = seuil_passe(Lr, hist)
    actif = M["P"][:, m] & M["P"][:, m30] & np.isfinite(thr) & (np.abs(Lr) >= thr) & (Lr != 0)
    return Lr, thr, actif


# ----------------------------------------------------------------------------- trades
def exclu(jours, fed):
    return np.array([RB.jour_court(j) or (j in fed) for j in jours])


def trades_retour(M, sig, barre, mk, fed, prix_signal_min):
    """Position -signe(signal) de l'ouverture a la cloture de la barre d'une heure, seances actives sans exclusion."""
    val, _, actif = sig
    ex = exclu(M["jours"], fed)
    L = []
    for i in np.where(actif & ~ex)[0]:
        j = M["jours"][i]
        if j not in barre.index:
            continue                               # seance sans barre d'une heure
        b = barre.loc[j]
        if b["contrat"] != M["contrat"][i]:
            continue                               # barre d'un autre contrat que les minutes du jour
        p = -int(np.sign(val[i]))
        L.append(dict(jour=j, pos=p, E=float(b["o"]), X=float(b["c"]), Hh=float(b["h"]), Ll=float(b["l"]),
                      signal=float(val[i]), C_sig=float(M["C"][i, prix_signal_min]), i=i))
    return finir(pd.DataFrame(L), mk)


def trades_hd(M, sig, fen, fed):
    """H5 : signal de H2, prix HistData (ouverture de la barre de debut -> cloture de la barre de fin)."""
    val, _, actif = sig
    ex = exclu(M["jours"], fed)
    L = []
    for i in np.where(actif & ~ex)[0]:
        j = M["jours"][i]
        if j not in fen.index:
            continue
        b = fen.loc[j]
        p = -int(np.sign(val[i]))
        L.append(dict(jour=j, pos=p, E=float(b["o"]), X=float(b["c"]), Hh=float(b["h"]), Ll=float(b["l"]),
                      signal=float(val[i]), i=i))
    return finir(pd.DataFrame(L), "NQ")


def finir(t, mk):
    t["brut"] = t["pos"] * (t["X"] - t["E"])
    t["net"] = t["brut"] - COUT[mk]
    t["net_sens"] = t["brut"] - COUT_SENS[mk]
    t["prix"] = t["E"]
    t["marche"] = mk
    return t


def trades_h1(M, z_tr, barre, fed, m_tenue, prix_min):
    """H1 : sens s de la position de zone V1 ouverte a la cloture de la minute m_tenue (15 h 59 : sortie a la cloture),
    gain ajoute = s x (C de la barre - C de la minute) ; retournement = -s x (C - O) - 1,5."""
    ex = set(j for j in z_tr["jour"].unique() if RB.jour_court(j) or j in fed)
    if m_tenue == M1559:
        x = z_tr[z_tr["minute_sortie"] == N - 1]
    else:                                          # temoin : position ouverte a 12 h 59 (entree <= 12 h 30, sortie >= 13 h)
        x = z_tr[(z_tr["minute_entree"] <= m_tenue) & (z_tr["minute_sortie"] > m_tenue)]
    idx = {j: i for i, j in enumerate(M["jours"])}
    L = []
    for r in x.itertuples():
        if r.jour in ex or r.jour not in barre.index:
            continue
        b = barre.loc[r.jour]
        i = idx[r.jour]
        if b["contrat"] != M["contrat"][i]:
            continue
        ref = float(M["C"][i, prix_min])
        if m_tenue == M1559:
            assert abs(ref - r.prix_sortie) < 1e-9
        L.append(dict(jour=r.jour, s=int(r.sens), ref=ref, O=float(b["o"]), X=float(b["c"]), Hh=float(b["h"]),
                      Ll=float(b["l"]), i=i))
    t = pd.DataFrame(L)
    t["ajout"] = t["s"] * (t["X"] - t["ref"])
    t["ajout_sens"] = t["ajout"] - SUPPL_H1
    t["rev_brut"] = -t["s"] * (t["X"] - t["O"])
    t["rev"] = t["rev_brut"] - COUT["NQ"]
    t["rev_sens"] = t["rev_brut"] - COUT_SENS["NQ"]
    return t


# ----------------------------------------------------------------------------- statistiques
def serie(t, col, cal):
    s = pd.Series(0.0, index=cal)
    if len(t):
        assert not t["jour"].duplicated().any()
        s.loc[pd.DatetimeIndex(t["jour"])] = t[col].to_numpy(float)
    return s


def per(s, a, b):
    return s[(s.index >= pd.Timestamp(a)) & (s.index <= pd.Timestamp(b))]


def t_de(s, a, b):
    return PA.t_stat(per(s, a, b).to_numpy())


def p_bilateral(t):
    return 2 * PA.p_unilateral(abs(t))


def t_sommes(S, Q, n):
    """t de series de n valeurs (zeros compris) a partir des sommes S et des sommes de carres Q (vecteurs)."""
    var = (Q - S ** 2 / n) / (n - 1)
    return np.where(var > 0, S / n / np.sqrt(np.maximum(var, 1e-300)) * np.sqrt(n), 0.0)


def placebo_signes(t, a, b, ncal, cout, rng):
    """1 000 tirages du sens au hasard sur les memes seances : t net de la serie quotidienne (zeros compris)."""
    x = t[(t["jour"] >= pd.Timestamp(a)) & (t["jour"] <= pd.Timestamp(b))]
    mv = (x["X"] - x["E"]).to_numpy()
    sg = rng.choice([-1.0, 1.0], size=(N_SIGNES, len(mv)))
    r = sg * mv - cout
    return t_sommes(r.sum(axis=1), (r ** 2).sum(axis=1), ncal)


def placebo_h1(t, a, b, ncal, retour, rng):
    """200 tirages : s remplace par le sens de la zone d'une autre seance (en position a 15 h 59) de la meme annee."""
    x = t[(t["jour"] >= pd.Timestamp(a)) & (t["jour"] <= pd.Timestamp(b))].reset_index(drop=True)
    ans = x["jour"].dt.year.to_numpy()
    s = x["s"].to_numpy()
    mv = (x["X"] - x["O"]).to_numpy() if retour else (x["X"] - x["ref"]).to_numpy()
    groupes = [np.where(ans == y)[0] for y in np.unique(ans)]
    out = np.zeros(N_H1)
    for k in range(N_H1):
        s2 = np.zeros(len(s))
        for g in groupes:
            # pour chaque seance, une AUTRE seance de la meme annee, tiree au hasard
            u = rng.integers(0, len(g) - 1, size=len(g))
            u = u + (u >= np.arange(len(g)))
            s2[g] = s[g[u]]
        r = -s2 * mv - COUT["NQ"] if retour else s2 * mv
        out[k] = t_sommes(np.array([r.sum()]), np.array([(r ** 2).sum()]), ncal)[0]
    return out


# ----------------------------------------------------------------------------- challenges (moteur de la partie D)
def etape_source(t, cal_z, ch, fz, mk, prolong=False):
    """Pas supplementaire (l'heure de la piste) ajoute au chemin de la zone, pour 1 unite, en $ au niveau de prix du
    20 octobre 2026 (meme facteur que chemins_zone). Renvoie (clo, bas, haut) du pas et le nombre de trades hors du
    calendrier de la zone."""
    fin = ch[:, -1].copy()
    clo, bas, haut = fin.copy(), fin.copy(), fin.copy()
    pos = {j: k for k, j in enumerate(cal_z)}
    hors = 0
    for r in t.itertuples():
        k = pos.get(r.jour)
        if k is None:
            hors += 1
            continue
        f = fz[r.jour]
        if prolong:
            p, E, c = r.s, r.ref, 0.0
        else:
            p, E, c = r.pos, r.E, COUT[mk]
        exc = [p * (r.Ll - E), p * (r.Hh - E)]
        clo[k] += (p * (r.X - E) * f - c) * PT[mk]
        bas[k] += (min(min(exc), 0.0) * f - c) * PT[mk]
        haut[k] += (max(max(exc), 0.0) * f - c) * PT[mk]
    return clo, bas, haut, hors


def challenges(cal_z, ch, bs, ht, etape, fin, firme, tailles):
    obj, dd, bloc, dll, nmax, part, *_ = PD.FIRMES[firme]
    garde = cal_z <= pd.Timestamp(fin)
    jz = cal_z[garde]
    a = (ch[garde], bs[garde], ht[garde])
    b = tuple(np.column_stack([x, e[garde]]) for x, e in zip(a, etape))
    verif = np.where(jz >= pd.Timestamp("2023-01-01"))[0]
    lim = PD.limites_depart(jz, verif, nmax)
    ok = verif + lim < len(jz)
    dv, lv = verif[ok], lim[ok]
    res = []
    for q in tailles:
        arg = (float(q), float(q), 0, float(obj), float(dd), float(bloc), float(dll), part, True)
        r = []
        for clo, bas, haut in (a, b):
            iss, _ = PD.tous_les_departs(np.ascontiguousarray(clo), np.ascontiguousarray(bas),
                                         np.ascontiguousarray(haut), dv, lv, *arg)
            r.append(((iss == 1).mean() * 100, (iss == -1).mean() * 100, (iss == 0).mean() * 100))
        res.append((q, len(dv), r[0], r[1]))
    return res


# ----------------------------------------------------------------------------- principal
def main():
    L = ["Piste 2 : l'heure 16 h 00 - 16 h 59 (etude_large/pistes/README.md, regles fixees le 22 octobre 2026, commit "
         "a6e791f, avant tout calcul)", ""]
    fed = set(pd.DatetimeIndex(fomc.annonces()))

    rech = pd.read_csv(DM.RECHERCHE)
    robot = pd.read_csv(DM.ROBOT)
    robot = robot[robot["t"] <= DM.FIN + " 23:59"]
    bars = pd.concat([rech, robot[robot["t"] > rech["t"].iloc[-1]]], ignore_index=True)
    NQ = marche(bars)
    ES = marche(pd.read_csv(MINUTES_ES))
    cal = NQ["jours"]
    h16 = {"NQ": barres_heure(HEURE_NQ, 16), "ES": barres_heure(HEURE_ES, 16)}
    h13 = {"NQ": barres_heure(HEURE_NQ, 13), "ES": barres_heure(HEURE_ES, 13)}
    L.append(f"Donnees : minutes NQ {cal[0].date()} - {cal[-1].date()} ({len(cal)} seances, recherche + robot), minutes ES "
             f"{ES['jours'][0].date()} - {ES['jours'][-1].date()} ({len(ES['jours'])} seances) ; barres d'une heure NQ "
             f"et ES jusqu'au {pd.read_csv(HEURE_NQ)['t'].iloc[-1]} ; {len(fed)} jours de la Fed.")
    hors_es = ES["jours"].difference(cal)
    L.append(f"  seances ES absentes du calendrier NQ : {len(hors_es)} ; seances NQ sans ES : "
             f"{len(cal.difference(ES['jours']))} (le calendrier des series est celui du NQ)")

    # ------------------------------------------------------------- controle a) : alignement, avant tout gain
    L.append("\nCONTROLE a) alignement des barres de 16 h (avant tout gain)")
    for mk, M in (("NQ", NQ), ("ES", ES)):
        b = h16[mk]
        j = M["jours"]
        dans = (j >= pd.Timestamp("2011-01-01")) & j.isin(b.index)
        ii = np.where(dans)[0]
        bb = b.loc[j[ii]]
        meme = bb["contrat"].to_numpy() == M["contrat"][ii]
        p59 = M["P"][ii, M1559]
        ecart = np.abs(bb["o"].to_numpy() - M["C"][ii, M1559])
        tot = int((b.index >= pd.Timestamp("2011-01-01")).sum())
        L.append(f"  {mk} : {len(b)} barres de 16 h en tout, {tot} sur 2011-2026, dont {len(ii)} jointes aux minutes ; "
                 f"meme contrat {meme.mean() * 100:.2f} % ; avec la minute de 15 h 59 presente ({p59.sum()}) : "
                 f"|O16 - C15:59| <= 2 points {np.mean(ecart[p59] <= 2) * 100:.1f} %, mediane {np.median(ecart[p59]):.2f}"
                 f" point, pire {ecart[p59].max():.2f}")
        vol15 = pd.read_csv(HEURE_NQ if mk == "NQ" else HEURE_ES)
        vt = pd.to_datetime(vol15["t"])
        v15 = vol15[vt.dt.hour == 15].set_index(vt[vt.dt.hour == 15].dt.normalize())["v"]
        rap = (b["v"] / v15.reindex(b.index)).dropna()
        L.append(f"     volume median de la barre de 16 h : {rap.median() * 100:.0f} % de celui de la barre de 15 h")

    # ------------------------------------------------------------- moteur de la zone (controle du moteur)
    z = DM.preparer(bars)
    ztr = DM.trades_zone(z, "2000-01-01", DM.FIN)
    t16 = ztr[ztr["jour"] <= pd.Timestamp("2026-10-16")]
    bon = len(t16) == 3571 and abs(t16["points"].sum() - 10759.75) < 1e-6
    L.append(f"\nControle du moteur de la zone (delta_mesures) : jusqu'au 16 octobre 2026 {len(t16)} trades "
             f"{t16['points'].sum():+.2f} points ; reference 3571 trades +10759.75 -> {'identique' if bon else 'ECART'}")
    ztr_nf = ztr[~ztr["jour"].isin(fed)]
    zpts = ztr_nf.groupby("jour")["points"].sum().reindex(cal).fillna(0.0)
    ouv = pd.Series(z["C"][:, 0], index=z["jours"])
    assert (z["jours"] == cal).all()
    zret = zpts / ouv

    # ------------------------------------------------------------- controles b) et c) : HistData
    hd = histdata()
    L.append("\nCONTROLES b) et c) HistData usatechidxusd (UTC -> New York), 2012-2018")
    f1655 = hd_fenetre(hd, "16:00", "16:50", ["16:00"])        # prix de 16 h 55 = cloture de la barre de 16 h 50
    f1700 = hd_fenetre(hd, "16:00", "16:55", ["16:00"])        # prix de 17 h 00 = cloture de la barre de 16 h 55
    db = h16["NQ"]
    j = f1655.index[(f1655.index >= pd.Timestamp("2012-01-01")) & (f1655.index <= pd.Timestamp("2018-12-31"))]
    j = j.intersection(db.index)
    r_hd = f1655.loc[j, "c"] / f1655.loc[j, "o"] - 1
    r_db = db.loc[j, "c"] / db.loc[j, "o"] - 1
    corr_b = float(np.corrcoef(r_hd, r_db)[0, 1])
    h5_ok = corr_b >= 0.9
    L.append(f"  b) correlation rendement HistData 16 h 00 -> 16 h 55 / barre Databento de 16 h : {corr_b:.3f} sur "
             f"{len(j)} seances -> {'H5 gardee (>= 0,9)' if h5_ok else 'H5 ABANDONNEE (< 0,9)'}")
    j2 = f1655.index.intersection(f1700.index)
    j2 = j2[(j2 >= pd.Timestamp("2012-01-01")) & (j2 <= pd.Timestamp("2018-12-31"))]
    a55 = f1655.loc[j2, "c"] / f1655.loc[j2, "o"] - 1
    a00 = f1700.loc[j2, "c"] / f1700.loc[j2, "o"] - 1
    d_pts = (f1700.loc[j2, "c"] - f1655.loc[j2, "c"]).abs()
    L.append(f"  c) correlation sortie a 16 h 55 / sortie a 17 h 00 (depuis 16 h 00) : {np.corrcoef(a55, a00)[0, 1]:.3f} "
             f"sur {len(j2)} seances ; ecart absolu median entre les deux sorties {d_pts.median():.2f} point "
             f"({(d_pts / f1655.loc[j2, 'c']).median() * 1e4:.2f} pb), moyen {d_pts.mean():.2f} point")

    # ------------------------------------------------------------- tests
    sig_h2 = signal_jour(NQ, M1559)
    sig_h3 = signal_demi_heure(NQ, M1559, M1529)
    sig_h4 = signal_jour(ES, M1559)
    tem_h2 = signal_jour(NQ, M1259)
    tem_h3 = signal_demi_heure(NQ, M1259, M1229)
    tem_h4 = signal_jour(ES, M1259)
    f16 = hd_fenetre(hd, "16:00", "16:10", ["16:00", "16:05", "16:10"])
    f13 = hd_fenetre(hd, "13:00", "13:10", ["13:00", "13:05", "13:10"])

    T = {}
    T["H2"] = dict(t=trades_retour(NQ, sig_h2, h16["NQ"], "NQ", fed, M1559),
                   tem=trades_retour(NQ, tem_h2, h13["NQ"], "NQ", fed, M1259), mk="NQ", ex=EXPLO, co=COFFRE)
    T["H3"] = dict(t=trades_retour(NQ, sig_h3, h16["NQ"], "NQ", fed, M1559),
                   tem=trades_retour(NQ, tem_h3, h13["NQ"], "NQ", fed, M1259), mk="NQ", ex=EXPLO, co=COFFRE)
    T["H4"] = dict(t=trades_retour(ES, sig_h4, h16["ES"], "ES", fed, M1559),
                   tem=trades_retour(ES, tem_h4, h13["ES"], "ES", fed, M1259), mk="ES", ex=EXPLO, co=COFFRE)
    T["H5"] = dict(t=trades_hd(NQ, sig_h2, f16, fed), tem=trades_hd(NQ, tem_h2, f13, fed), mk="NQ", ex=EXPLO_H5,
                   co=COFFRE_H5)
    h1 = trades_h1(NQ, ztr, h16["NQ"], fed, M1559, M1559)
    h1t = trades_h1(NQ, ztr, h13["NQ"], fed, M1259, M1259)
    # ES : series sur le calendrier NQ (les seances ES hors calendrier NQ sont comptees plus haut)
    T["H4"]["t"] = T["H4"]["t"][T["H4"]["t"]["jour"].isin(cal)].reset_index(drop=True)
    T["H4"]["tem"] = T["H4"]["tem"][T["H4"]["tem"]["jour"].isin(cal)].reset_index(drop=True)

    rng = np.random.default_rng(GRAINE)
    ncal = lambda a, b: int(((cal >= pd.Timestamp(a)) & (cal <= pd.Timestamp(b))).sum())  # noqa: E731

    # challenges : chemins de la zone (partie D), facteurs de prix
    cal_z, ch_z, bas_z, haut_z = PD.chemins_zone()
    idx = {j_: i for i, j_ in enumerate(z["jours"])}
    ref_nq = float(z["C"][idx[pd.Timestamp(DM.FIN)], N - 1])
    fz = {"NQ": pd.Series(ref_nq / z["C"][:, 0], index=z["jours"])}
    ref_es = float(ES["C"][-1, N - 1])
    fz["ES"] = pd.Series(ref_es / ES["C"][:, 0], index=ES["jours"])
    base_chal = {}

    def chal(t, mk, fin, firme, tailles, prolong=False):
        clo, bas, haut, hors = etape_source(t, cal_z, ch_z, fz[mk], mk, prolong)
        res = challenges(cal_z, ch_z, bas_z, haut_z, (clo, bas, haut), fin, firme, tailles)
        return res, hors

    # controle du moteur des challenges : la zone seule, donnees jusqu'au 20 octobre, redonne la verification de la
    # partie D (resultats_d.txt : Bulenox 908 departs, 3 MNQ 45 % / 31 %, 4 MNQ 49 % / 44 % ; Lucid 804, 1 MNQ 55 / 35)
    vide = (ch_z[:, -1], ch_z[:, -1], ch_z[:, -1])
    rb = challenges(cal_z, ch_z, bas_z, haut_z, vide, DM.FIN, BULENOX, [3, 4])
    rl = challenges(cal_z, ch_z, bas_z, haut_z, vide, DM.FIN, LUCID, [1])
    att = [(908, 45, 31), (908, 49, 44), (804, 55, 35)]
    vu = [(r[1], round(r[2][0]), round(r[2][1])) for r in rb + rl]
    L.append(f"\nControle du moteur des challenges (zone seule jusqu'au 20 octobre, departs 2023-2026) : Bulenox 3 MNQ "
             f"{vu[0]}, 4 MNQ {vu[1]}, Lucid 1 MNQ {vu[2]} (departs, valide %, perdu %) ; partie D {att} -> "
             f"{'identique' if vu == att else 'ECART'}")

    synthese = []

    # ============================================================= H1
    L.append("\n" + "=" * 100)
    L.append("H1 : prolonger la zone (position V1 ouverte a 15 h 59 gardee jusqu'a la cloture de la barre de 16 h), "
             "test bilateral")
    aj = serie(h1, "ajout", cal)
    te, tc = t_de(aj, *EXPLO), t_de(aj, *COFFRE)
    sg = 1 if te >= 0 else -1
    nE = int(((h1["jour"] >= pd.Timestamp(EXPLO[0])) & (h1["jour"] <= pd.Timestamp(EXPLO[1]))).sum())
    nC = int(((h1["jour"] >= pd.Timestamp(COFFRE[0])) & (h1["jour"] <= pd.Timestamp(COFFRE[1]))).sum())
    L.append(f"  seances en position a 15 h 59 (hors Fed, jours courts, seances sans barre) : exploration {nE}, coffre {nC}")
    L.append(f"  gain ajoute (sans frais) : exploration {per(aj, *EXPLO).sum():+.1f} points, "
             f"{h1.loc[h1['jour'] <= pd.Timestamp(EXPLO[1]), 'ajout'].mean():+.3f} point par seance en position, "
             f"t {te:+.2f} (p bilateral {p_bilateral(te):.4f}) ; coffre {per(aj, *COFFRE).sum():+.1f} points, t {tc:+.2f}")
    rv = serie(h1, "rev", cal)
    L.append(f"  retournement -s x (C16 - O16) - 1,5 : t exploration {t_de(rv, *EXPLO):+.2f}, coffre {t_de(rv, *COFFRE):+.2f}")
    retour = sg < 0
    regle = rv if retour else aj
    nom_regle = "retournement (gain ajoute negatif)" if retour else "prolongation (gain ajoute positif)"
    L.append(f"  sens de l'exploration : {nom_regle} ; criteres jugés sur cette regle")
    c1 = abs(te) >= 2 and (t_de(rv, *EXPLO) >= 2 if retour else True)
    c2 = (sg * tc >= 1.5) and (t_de(rv, *COFFRE) >= 1.5 if retour else True)
    pl = placebo_h1(h1, *EXPLO, ncal(*EXPLO), retour, rng)
    t_reel = t_de(regle, *EXPLO)
    c4a = (pl < t_reel).mean() >= 0.95
    tem = serie(h1t, "rev" if retour else "ajout", cal)
    t_tem = t_de(tem, *EXPLO)
    c4b = t_tem < t_reel
    sens_s = serie(h1, "rev_sens" if retour else "ajout_sens", cal)
    c5 = t_de(sens_s, *EXPLO) > 0 and t_de(sens_s, *COFFRE) > 0
    comb = (zpts + regle) / ouv
    shz = (PA.sharpe(per(zret, *EXPLO)), PA.sharpe(per(zret, *COFFRE)))
    shc = (PA.sharpe(per(comb, *EXPLO)), PA.sharpe(per(comb, *COFFRE)))
    c6 = shc[0] > shz[0] and shc[1] > shz[1]
    L.append(f"  1) |t| exploration >= 2{' et retournement t >= 2' if retour else ''} : {'oui' if c1 else 'non'}")
    L.append(f"  2) coffre meme signe, |t| >= 1,5{' et retournement t >= 1,5' if retour else ''} : "
             f"{'oui' if c2 else 'non'} (t coffre {tc:+.2f})")
    L.append(f"  4) placebo (200 tirages, s d'une autre seance de la meme annee, exploration) : t reel {t_reel:+.2f}, "
             f"95e centile {np.quantile(pl, 0.95):+.2f}, mediane {np.median(pl):+.2f}, fait mieux que "
             f"{(pl < t_reel).mean() * 100:.1f} % -> {'oui' if c4a else 'non'}")
    L.append(f"     temoin d'heure (position de zone ouverte a 12 h 59, barre de 13 h) : t exploration {t_tem:+.2f} "
             f"({len(h1t[h1t['jour'] <= pd.Timestamp(EXPLO[1])])} seances), coffre {t_de(tem, *COFFRE):+.2f} -> doit "
             f"faire moins bien que {t_reel:+.2f} : {'oui' if c4b else 'non'}")
    L.append(f"  5) frais de sensibilite ({'3 points' if retour else '0,75 point de plus par seance'}) : t exploration "
             f"{t_de(sens_s, *EXPLO):+.2f}, coffre {t_de(sens_s, *COFFRE):+.2f} -> {'oui' if c5 else 'non'}")
    L.append(f"  6) Sharpe zone seule / zone + {('retournement' if retour else 'prolongation')} : exploration "
             f"{shz[0]:+.2f} / {shc[0]:+.2f}, coffre {shz[1]:+.2f} / {shc[1]:+.2f} -> {'oui' if c6 else 'non'}")
    res, hors = chal(h1, "NQ", COFFRE[1], BULENOX, TAILLES_BULENOX, prolong=not retour) if not retour else \
        chal(h1.assign(pos=-h1["s"], E=h1["O"]), "NQ", COFFRE[1], BULENOX, TAILLES_BULENOX)
    c7 = all(r[3][0] >= r[2][0] for r in res)
    for q, nd, a_, b_ in res:
        base_chal[(BULENOX, q, COFFRE[1])] = a_
        L.append(f"  7) Bulenox {q} MNQ, {nd} departs 2023-2026 : zone seule valide {a_[0]:.1f} % perdu {a_[1]:.1f} % ; "
                 f"zone + H1 valide {b_[0]:.1f} % perdu {b_[1]:.1f} %")
    L.append(f"     (seances H1 hors du calendrier de la zone de la partie D : {hors}) -> {'oui' if c7 else 'non'}")
    ach = h1[h1["s"] > 0]
    ven = h1[h1["s"] < 0]
    for nom, x in (("achats (zone acheteuse)", ach), ("ventes (zone vendeuse)", ven)):
        for pn, (a, b) in (("exploration", EXPLO), ("coffre", COFFRE)):
            y = x[(x["jour"] >= pd.Timestamp(a)) & (x["jour"] <= pd.Timestamp(b))]
            L.append(f"  e) {nom:24} {pn:11} : {len(y):4d} seances, gain ajoute moyen {y['ajout'].mean():+.3f} point, "
                     f"total {y['ajout'].sum():+8.1f}, t {t_de(serie(y, 'ajout', cal), a, b):+.2f}")
    for nom, a, b in SOUS:
        y = h1[(h1["jour"] >= pd.Timestamp(a)) & (h1["jour"] <= pd.Timestamp(b))]
        L.append(f"  e) {nom} : {len(y):4d} seances, gain ajoute moyen {y['ajout'].mean():+.3f} point, "
                 f"t {t_de(aj, a, b):+.2f}")
    pire = h1.loc[h1["ajout"].idxmin()]
    L.append(f"  d) pire seance (gain ajoute) : {pire['jour'].date()} {pire['ajout']:+.2f} points ; 5 plus grands |gain "
             f"ajoute| : " + ", ".join(f"{r.jour.date()} {r.ajout:+.1f}" for r in
                                         h1.reindex(h1["ajout"].abs().sort_values(ascending=False).index).head(5).itertuples()))
    ok_h1 = all([c1, c2, c4a, c4b, c5, c6, c7])
    synthese.append(dict(nom="H1 prolonger la zone (bilateral)", t_explo=te, bilateral=True, t_coffre=tc,
                         p=p_bilateral(te), ok=ok_h1,
                         detail=f"sens {'retournement' if retour else 'prolongation'} ; 1 |t|>=2 {'oui' if c1 else 'non'}"
                                f" ; 2 coffre {'oui' if c2 else 'non'} ; 4 placebo {'oui' if c4a else 'non'}"
                                f" ({(pl < t_reel).mean() * 100:.1f} %) ; temoin 13 h {'oui' if c4b else 'non'}"
                                f" (t {t_tem:+.2f}) ; 5 sensibilite {'oui' if c5 else 'non'} ; 6 Sharpe zone+H1 "
                                f"{'oui' if c6 else 'non'} ({shz[0]:+.2f}/{shc[0]:+.2f}, {shz[1]:+.2f}/{shc[1]:+.2f}) ;"
                                f" 7 Bulenox {'oui' if c7 else 'non'}"))

    # ============================================================= H2 a H5
    noms = {"H2": "H2 retour de la journee (NQ)", "H3": "H3 retour de la derniere demi-heure (NQ)",
            "H4": "H4 retour de la journee (ES, MES)", "H5": "H5 retour de la journee, sortie 16 h 15 (HistData, Lucid)"}
    for k in ("H2", "H3", "H4", "H5"):
        D = T[k]
        t, mk, EX, CO = D["t"], D["mk"], D["ex"], D["co"]
        L.append("\n" + "=" * 100)
        L.append(noms[k] + (" -- ABANDONNEE par le controle b), chiffres pour information" if k == "H5" and not h5_ok else ""))
        s = serie(t, "net", cal)
        te, tc = t_de(s, *EX), t_de(s, *CO)
        x_e = t[(t["jour"] >= pd.Timestamp(EX[0])) & (t["jour"] <= pd.Timestamp(EX[1]))]
        x_c = t[(t["jour"] >= pd.Timestamp(CO[0])) & (t["jour"] <= pd.Timestamp(CO[1]))]
        L.append(f"  seances actives : exploration {len(x_e)} (premiere {x_e['jour'].min().date()}), coffre {len(x_c)}")
        L.append(f"  exploration {EX[0][:4]}-{EX[1][:4]} : net {x_e['net'].mean():+.3f} point par trade "
                 f"({(x_e['net'] / x_e['prix']).mean() * 1e4:+.2f} pb), brut {x_e['brut'].mean():+.3f}, t net {te:+.2f} "
                 f"(p unilateral {PA.p_unilateral(te):.4f}), t brut {t_de(serie(t, 'brut', cal), *EX):+.2f}")
        L.append(f"  coffre {CO[0][:4]} - {CO[1]} : net {x_c['net'].mean():+.3f} point par trade "
                 f"({(x_c['net'] / x_c['prix']).mean() * 1e4:+.2f} pb), t net {tc:+.2f}")
        c1 = te >= 2
        c2 = tc >= 1.5
        ga = x_e.loc[x_e["pos"] > 0, "brut"].sum()
        gv = x_e.loc[x_e["pos"] < 0, "brut"].sum()
        c3 = ga >= 0 and gv >= 0
        pl = placebo_signes(t, *EX, ncal(*EX), COUT[mk], rng)
        c4a = (pl < te).mean() >= 0.95
        tm = serie(D["tem"], "net", cal)
        t_tem = t_de(tm, *EX)
        c4b = t_tem < te
        ss = serie(t, "net_sens", cal)
        c5 = t_de(ss, *EX) > 0 and t_de(ss, *CO) > 0
        sret = serie(t.assign(r=t["net"] / t["prix"]), "r", cal)
        corr = float(np.corrcoef(per(sret, *CORR), per(zret, *CORR))[0, 1])
        w = per(zret, *EX).std() / per(sret, *EX).std()
        comb = zret + w * sret
        shz, shc = PA.sharpe(per(zret, *CO)), PA.sharpe(per(comb, *CO))
        c6 = corr < 0.3 and shc > shz
        L.append(f"  1) t net exploration >= 2 : {'oui' if c1 else 'non'}")
        L.append(f"  2) coffre t net >= 1,5 (meme signe) : {'oui' if c2 else 'non'}")
        L.append(f"  3) mecanisme, exploration avant frais : achats {ga:+.1f} points ({int((x_e['pos'] > 0).sum())} trades), "
                 f"ventes {gv:+.1f} points ({int((x_e['pos'] < 0).sum())} trades) -> {'oui' if c3 else 'non'}")
        L.append(f"  4) placebo (1 000 sens au hasard, memes seances, exploration) : 95e centile {np.quantile(pl, 0.95):+.2f}, "
                 f"fait mieux que {(pl < te).mean() * 100:.1f} % -> {'oui' if c4a else 'non'}")
        L.append(f"     temoin d'heure (signal a 12 h 59, {'13 h 00 - 13 h 15 HistData' if k == 'H5' else 'barre de 13 h'}) :"
                 f" {len(D['tem'][D['tem']['jour'] <= pd.Timestamp(EX[1])])} trades, t exploration {t_tem:+.2f}, coffre "
                 f"{t_de(tm, *CO):+.2f} -> doit faire moins bien que {te:+.2f} : {'oui' if c4b else 'non'}")
        L.append(f"  5) frais de sensibilite ({COUT_SENS[mk]:.1f} points) : t exploration {t_de(ss, *EX):+.2f}, coffre "
                 f"{t_de(ss, *CO):+.2f} -> {'oui' if c5 else 'non'}")
        L.append(f"  6) correlation avec la zone 2016-2022 {corr:+.3f} ; Sharpe coffre zone {shz:+.2f} -> zone + piste a "
                 f"risque egal (poids {w:.2f}) {shc:+.2f} -> {'oui' if c6 else 'non'}")
        if k == "H5":
            res, hors = chal(t, mk, CO[1], LUCID, [1])
            firme = "Lucid Flex"
        else:
            res, hors = chal(t, mk, CO[1], BULENOX, TAILLES_BULENOX)
            firme = "Bulenox"
        c7 = all(r[3][0] >= r[2][0] for r in res)
        for q, nd, a_, b_ in res:
            L.append(f"  7) {firme} {q} MNQ{' + ' + str(q) + ' MES' if mk == 'ES' else ''}, {nd} departs 2023 - {CO[1]} : "
                     f"zone seule valide {a_[0]:.1f} % perdu {a_[1]:.1f} % ; zone + {k} valide {b_[0]:.1f} % perdu "
                     f"{b_[1]:.1f} %")
        L.append(f"     (trades {k} hors du calendrier de la zone de la partie D : {hors}) -> {'oui' if c7 else 'non'}")
        for nom, x in (("achats", t[t["pos"] > 0]), ("ventes", t[t["pos"] < 0])):
            for pn, (a, b) in (("exploration", EX), ("coffre", CO)):
                y = x[(x["jour"] >= pd.Timestamp(a)) & (x["jour"] <= pd.Timestamp(b))]
                L.append(f"  e) {nom:7} {pn:11} : {len(y):4d} trades, brut moyen {y['brut'].mean():+.3f}, net moyen "
                         f"{y['net'].mean():+.3f} point, t net {t_de(serie(y, 'net', cal), a, b):+.2f}")
        for nom, a, b in SOUS:
            y = t[(t["jour"] >= pd.Timestamp(a)) & (t["jour"] <= pd.Timestamp(b))]
            L.append(f"  e) {nom} : {len(y):4d} trades, net moyen {y['net'].mean():+.3f} point, t net {t_de(s, a, b):+.2f}")
        pire = t.loc[t["net"].idxmin()]
        L.append(f"  d) pire trade : {pire['jour'].date()} {'achat' if pire['pos'] > 0 else 'vente'} {pire['net']:+.2f} "
                 f"points ; 5 plus grands |brut| : " + ", ".join(
                     f"{r.jour.date()} {r.brut:+.1f}" for r in t.reindex(t["brut"].abs().sort_values(ascending=False)
                                                                           .index).head(5).itertuples()))
        ok = all([c1, c2, c3, c4a, c4b, c5, c6, c7]) and (h5_ok if k == "H5" else True)
        synthese.append(dict(nom=noms[k], t_explo=te, bilateral=False, t_coffre=tc, p=PA.p_unilateral(te), ok=ok,
                             detail=f"1 t>=2 {'oui' if c1 else 'non'} ; 2 coffre {'oui' if c2 else 'non'} ; 3 mecanisme "
                                    f"{'oui' if c3 else 'non'} (achats {ga:+.0f}, ventes {gv:+.0f} pts bruts) ; 4 placebo "
                                    f"{'oui' if c4a else 'non'} ({(pl < te).mean() * 100:.1f} %) ; temoin 13 h "
                                    f"{'oui' if c4b else 'non'} (t {t_tem:+.2f}) ; 5 sensibilite {'oui' if c5 else 'non'}"
                                    f" ; 6 source {'oui' if c6 else 'non'} (corr {corr:+.2f}, Sharpe {shz:+.2f} -> "
                                    f"{shc:+.2f}) ; 7 {firme} {'oui' if c7 else 'non'}"
                                    + ("" if k != "H5" else f" ; controle b {'oui' if h5_ok else 'NON (abandon)'}")))

    # ------------------------------------------------------------- synthese
    L.append("\n" + "=" * 100)
    L.append("SYNTHESE (p tire du t d'exploration ; Benjamini-Hochberg a 10 % calcule ensuite sur les 17 tests des 5 pistes)")
    L.append(f"  {'test':58} {'t explo':>8} {'p':>8} {'bilat.':>6} {'t coffre':>9}  criteres propres")
    for r in synthese:
        L.append(f"  {r['nom']:58} {r['t_explo']:+8.2f} {r['p']:8.4f} {'oui' if r['bilateral'] else 'non':>6} "
                 f"{r['t_coffre']:+9.2f}  {'TOUS PASSENT' if r['ok'] else 'echec'}")
        L.append(f"      {r['detail']}")
    L.append("")
    L.append("CONTROLE f) regles des firmes (recherche web du 22 octobre 2026) : Lucid (article d'aide officiel "
             "support.lucidtrading.com « Allowed trading times », lu par le moteur de recherche) : positions LucidPro,")
    L.append("  LucidFlex et LucidDirect fermees a 16 h 45 (heure de New York), fermeture automatique, pas d'echec du "
             "compte. Bulenox : seuls des guides tiers disent « toutes les positions fermees a 15 h 59 CT » (16 h 59 a")
    L.append("  New York) ; la page officielle bulenox.com/help n'a pas pu etre ouverte (nom de domaine non resolu depuis "
             "cette machine) : A CONFIRMER au panier avant tout usage.")
    L.append("CONTROLE d) : aucun calendrier des resultats des grandes valeurs dans les donnees gratuites du depot ; les "
             "seances aux plus grands mouvements sont publiees a la place (souvent des soirs de resultats).")
    L.append("")
    L.append("REGARD VERS LE FUTUR (verifie dans le code) : S et L n'utilisent que les clotures de 15 h 59 (et 15 h 29) du "
             "jour et de la veille ; le seuil ne lit que les 252 seances completes STRICTEMENT avant le jour ; la position")
    L.append("  de zone de H1 est celle de 15 h 59 ; l'entree se fait a l'ouverture de 16 h 00 (barre d'une heure ou barre "
             "HistData), apres le signal. Le jour du signal n'a pas besoin d'etre complet (seule sa minute de signal est")
    L.append("  exigee), pour que le temoin de 13 h n'utilise rien d'apres 12 h 59 ; le temoin de H1 garde la limite du "
             "moteur V1 (la zone ne joue que les seances completes, comme le bot).")
    L.append("")
    L.append("CHOIX D'INTERPRETATION (fixes avant tout calcul, a relire) :")
    for x in ["series quotidiennes sur toutes les seances des minutes du NQ (0 sans trade) ; ES ramene au calendrier NQ ;",
              "placebo (signes au hasard, ou s d'une autre seance de la meme annee en position a 15 h 59) sur l'exploration ;",
              "temoin de 13 h : barre d'une heure de 13 h du meme fichier (H5 : barres HistData 13 h 00 -> 13 h 10), signal "
              "de 12 h 59 calcule comme celui de 15 h 59 ; 'moins bien' = t net d'exploration plus bas, du cote gagnant ;",
              "H1 : t du gain ajoute (bilateral) ; le sens de l'exploration choisit la regle jugee (prolonger si t >= 0, "
              "sinon retourner : -s x (C16 - O16) - 1,5 doit passer les memes criteres) ;",
              "frais de sensibilite exiges sur l'exploration ET le coffre ; H1 prolonger : +0,75 point par seance ;",
              "critere 6 en rendements (points / prix d'entree ; zone : points / ouverture), poids a risque egal sur "
              "l'exploration de chaque test ; H1 : Sharpe de zone + regle H1 contre zone seule ;",
              "critere 7 (pas de seuil dans le README) : la zone + la piste doit valider au moins autant que la zone seule, "
              "departs 2023 - fin du coffre, a 3 ET 4 MNQ (Bulenox, H1 a H4 ; MES pour H4), 1 MNQ chez Lucid (H5) ;",
              "controle b : prix de 16 h 55 = cloture de la barre HistData de 16 h 50 ; controle c : 17 h 00 = cloture de "
              "la barre de 16 h 55."]:
        L.append("  - " + x)
    n_ok = sum(r["ok"] for r in synthese)
    L.append("")
    L.append(f"CONCLUSION : {n_ok} test(s) sur 5 passent leurs criteres propres (avant Benjamini-Hochberg). "
             + ("L'heure de 16 h n'apporte ni precision a la zone (H1) ni source independante (H2 a H5) apres frais."
                if n_ok == 0 else "Voir la synthese."))
    texte = "\n".join(L)
    print(texte)
    (ICI / "resultats.txt").write_text(texte + "\n")


if __name__ == "__main__":
    main()
