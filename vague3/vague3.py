#!/usr/bin/env python3
"""Vague 3 (README.md) : 7 sources de plusieurs jours sur le NQ (l'ES a titre descriptif), exploration 2011-2022
seulement. Memes donnees, meme execution et meme controle au hasard que tournoi8/. Ecrit exploration3.txt,
exploration3.csv et survivants3.json. Lancer depuis ce dossier : python3 vague3.py
Le coffre (2023-2026) est lu seulement par coffre3.py."""
import json
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
R = ICI.parent
sys.path.insert(0, str(R / "tournoi8"))
sys.path.insert(0, str(R / "fonds"))
import fomc  # noqa: E402
import tournoi8 as T8  # noqa: E402

FIN_EXPLORATION = T8.FIN_EXPLORATION
SOURCES = ["W1 semaine de l'echeance des options", "W2 semaines paires du cycle de la Fed",
           "W3 reequilibrage de fin de mois, achat", "W4 reequilibrage de fin de mois, vente", "W5 RSI(2) vendeur",
           "W6 ecart NQ / ES", "W7 novembre - avril"]
N_HASARD, T_MIN, PART_HASARD = T8.N_HASARD, T8.T_MIN, T8.PART_HASARD


# ----------------------------------------------------------------------------- calendriers (connus d'avance)
def troisiemes_vendredis(annees):
    out = []
    for a in annees:
        for m in range(1, 13):
            v = pd.date_range(pd.Timestamp(a, m, 1), periods=31, freq="D")
            v = v[(v.month == m) & (v.dayofweek == 4)]
            out.append(v[2])
    return pd.DatetimeIndex(out)


@lru_cache(maxsize=4)
def _zn(jusqu_au):
    """ZN (contrat le plus echange) : indice de rendement cumule, chaine jour par jour sur un meme contrat (un jour de
    changement de contrat compte pour 0 : pas d'ecart de prix entre deux echeances)."""
    f = pd.read_csv(R / "fonds/donnees/futures_1d.csv.gz")
    z = f[(f["symbole"] == "ZN.v.0") & (f["date"] <= jusqu_au)].sort_values("date")
    c, k = z["c"].to_numpy(), z["contrat"].to_numpy()
    r = np.r_[0.0, np.where(k[1:] == k[:-1], c[1:] / c[:-1] - 1, 0.0)]
    return pd.Series(np.cumprod(1 + r), index=pd.to_datetime(z["date"]))


def zn(dates, jusqu_au, veille=True):
    """Indice du ZN (_zn) de la derniere seance strictement avant chaque date (veille=True), ou de la derniere seance
    jusqu'a la date comprise (veille=False)."""
    z = _zn(jusqu_au)
    i = np.searchsorted(z.index.values, pd.DatetimeIndex(dates).values, side="left" if veille else "right") - 1
    return np.where(i >= 0, z.to_numpy()[np.maximum(i, 0)], np.nan)


def indice_es(s, es):
    """ES : indice de rendement cumule des clotures de 15 h 49, chaine seance par seance sur un meme contrat (aux dates de
    s ; un changement de contrat compte pour 0)."""
    e = es.set_index("date")
    c = e["C"].to_numpy()
    k = e["contrat"].to_numpy()
    r = np.r_[0.0, np.where(k[1:] == k[:-1], c[1:] / c[:-1] - 1, 0.0)]
    return pd.Series(np.cumprod(1 + r), index=e.index).reindex(pd.DatetimeIndex(s["date"])).to_numpy()


def ecart_mois(es_i, zv, zj, a, dec):
    """Ecart de rendement ES - ZN depuis la fin du mois d'avant (seance a) jusqu'a la decision (seance dec)."""
    return (es_i[dec] / es_i[a] - 1) - (zv[dec] / zj[a] - 1)


# ----------------------------------------------------------------------------- positions (signe : +1 achat, -1 vente)
def tenir_si_suivante(s, dedans):
    """Position a la decision t si la seance t+1 est « dedans » (le rendement de t a t+1 lui appartient)."""
    roule = T8.echeances(s)
    pos = np.zeros(len(s), np.int8)
    pos[:-1] = dedans[1:] & ~roule[:-1]
    return pos


def w1_echeance(s):
    d = pd.DatetimeIndex(s["date"])
    fer = set(T8.feries(range(2010, 2028)))
    dedans = np.zeros(len(s), bool)
    for v in troisiemes_vendredis(range(d.year.min(), d.year.max() + 1)):
        fin = v - pd.Timedelta(days=1) if v in fer else v              # 3e vendredi ferie : la veille
        lundi = v - pd.Timedelta(days=4)
        dedans |= (d >= lundi) & (d <= fin)
    return tenir_si_suivante(s, dedans)


def semaines_fed(dates, annonces):
    """Semaine du cycle de la Fed de chaque seance : semaine 0 = de la veille de l'annonce a 3 seances apres ;
    semaine k = seances 5k - 1 a 5k + 3 apres l'annonce. -1 : hors des semaines 0 a 6."""
    d = pd.DatetimeIndex(dates)
    ia = np.searchsorted(d.values, pd.DatetimeIndex(annonces).values)          # seance de chaque annonce (ou suivante)
    ia = ia[(ia < len(d))]
    ia = ia[d[ia].isin(annonces)]                                              # annonces tombees un jour de seance
    sem = np.full(len(d), -1)
    for i in range(len(d)):
        prec = ia[ia <= i + 1]                                                 # la veille de l'annonce compte (k = -1)
        if len(prec) == 0:
            continue
        k = i - prec[-1]
        w = (k + 1) // 5
        if 0 <= w <= 6:
            sem[i] = w
    return sem


def w2_fed(s):
    sem = semaines_fed(s["date"], fomc.annonces())
    return tenir_si_suivante(s, (sem >= 0) & (sem % 2 == 0))


def reequilibrage(s, es, zv, zj, sens):
    """W3 (sens +1) / W4 (sens -1) : fenetre des 5 dernieres seances du mois ; ecart de rendement ES - ZN depuis la fin du
    mois d'avant, mesure a la 5e seance avant la fin, compare aux 60 mois d'avant (au moins 36). es : indice de l'ES
    (indice_es) ; zv : indice du ZN de la veille de chaque seance (a la decision) ; zj : indice du ZN du jour (base : fin
    du mois d'avant, connue a la decision). Indices chaines sur un meme contrat : pas de saut d'echeance."""
    d = pd.DatetimeIndex(s["date"])
    roule = T8.echeances(s)
    mois = d.to_period("M")
    pos = np.zeros(len(s), np.int8)
    ecarts = []                                                                # ecarts des mois passes
    fins = np.flatnonzero(np.r_[mois[1:] != mois[:-1], False])                 # derniere seance de chaque mois complet
    for a, b in zip(fins[:-1], fins[1:]):
        dec = b - 4                                                            # 5e seance avant la fin du mois
        if dec <= a:
            continue
        e = ecart_mois(es, zv, zj, a, dec)
        if np.isnan(e):
            continue
        hist = np.array(ecarts[-60:])
        if len(hist) >= 36:
            q = (hist < e).mean()
            if (sens == 1 and q < 0.2) or (sens == -1 and q >= 0.8):
                for t in range(dec, b):
                    pos[t] = sens if not roule[t] else 0
        ecarts.append(e)
    return pos


def w5_rsi_vendeur(s):
    C = s["C"].to_numpy()
    roule = T8.echeances(s)
    m200 = pd.Series(C).rolling(200).mean().to_numpy()
    m5 = pd.Series(C).rolling(5).mean().to_numpy()
    r2 = T8.rsi_wilder(C, 2)
    pos = np.zeros(len(C), np.int8)
    tenu = False
    for t in range(len(C)):
        if tenu and C[t] < m5[t]:
            tenu = False
        elif not tenu and C[t] < m200[t] and r2[t] > 90:
            tenu = True
        if roule[t]:
            tenu = False
        pos[t] = -1 if tenu else 0
    return pos


def w6_ecart(p):
    """p : seances communes NQ / ES (colonnes C_nq, C_es, roule). Achat NQ / vente ES 5 seances apres un signal."""
    r = (p["C_nq"] / p["C_nq"].shift() - 1 - (p["C_es"] / p["C_es"].shift() - 1)).to_numpy()
    meme = np.r_[False, ~p["roule"].to_numpy()[:-1]]
    r = np.where(meme, r, np.nan)
    roule = p["roule"].to_numpy()
    pos = np.zeros(len(p), np.int8)
    reste = 0
    for t in range(len(p)):
        hist = r[max(0, t - 252):t]
        hist = hist[~np.isnan(hist)]
        if not np.isnan(r[t]) and len(hist) >= 200 and r[t] <= np.quantile(hist, 0.10):
            reste = 5
        pos[t] = 1 if (reste > 0 and not roule[t]) else 0
        reste = max(0, reste - 1)
    return pos


def w7_hiver(s):
    d = pd.DatetimeIndex(s["date"])
    return tenir_si_suivante(s, np.isin(d.month, [11, 12, 1, 2, 3, 4]))


# ----------------------------------------------------------------------------- journaux
def journal(s, pos):
    """Comme tournoi8.journal, avec un signe (+1 achat, -1 vente)."""
    P = s["P"].to_numpy()
    pt, cote = s.attrs["pt"], s.attrs["cote"]
    avant = np.r_[0, pos[:-1]].astype(float)
    var = np.r_[0.0, P[1:] / P[:-1] - 1]
    pts = np.r_[0.0, P[1:] - P[:-1]]
    chg = np.abs(pos.astype(float) - avant)
    rend = avant * var - chg * cote / P
    dol = (avant * pts - chg * cote) * pt
    entrees, sorties = trades_de(pos)
    tr = np.array([(np.sign(pos[a]) * (P[b] - P[a]) - 2 * cote) * pt for a, b in zip(entrees, sorties)])
    return rend, dol, tr, entrees, sorties


def journal_paire(p, pos):
    """Achat NQ et vente ES pour le meme montant : rendement = variation NQ - variation ES, frais des deux jambes.
    $ pour 1 MNQ contre le meme montant d'ES."""
    Pn, Pe = p["P_nq"].to_numpy(), p["P_es"].to_numpy()
    avant = np.r_[0, pos[:-1]].astype(float)
    var = np.r_[0.0, Pn[1:] / Pn[:-1] - 1] - np.r_[0.0, Pe[1:] / Pe[:-1] - 1]
    chg = np.abs(pos.astype(float) - avant)
    rend = avant * var - chg * (p.attrs["cote_nq"] / Pn + p.attrs["cote_es"] / Pe)
    dol = rend * np.r_[Pn[0], Pn[:-1]] * 2.0                    # notionnel d'un MNQ au debut de la periode
    entrees, sorties = trades_de(pos)
    tr = np.array([dol[a:b + 1].sum() for a, b in zip(entrees, sorties)])
    return rend, dol, tr, entrees, sorties


def trades_de(pos):
    avant = np.r_[0, pos[:-1]]
    entrees = np.flatnonzero((pos != 0) & (avant == 0))
    sorties = np.flatnonzero((pos == 0) & (avant != 0))
    return entrees[:len(sorties)], sorties


def hasard(rend_de, interdit, entrees, sorties, sens, graine):
    """1 000 placements au hasard des memes trades (memes durees, meme sens)."""
    durees = (sorties - entrees).astype(np.int64)
    ts = np.empty(N_HASARD)
    for i in range(N_HASARD):
        pos = T8.placer(durees, interdit, graine + i) * np.int8(sens)
        ts[i] = T8.t_stat(rend_de(pos))
    return ts


# ----------------------------------------------------------------------------- chargement
def charger(jusqu_au=FIN_EXPLORATION):
    nq, es = T8.charger("NQ", jusqu_au), T8.charger("ES", jusqu_au)
    p = nq[["date", "P", "C", "contrat"]].merge(es[["date", "P", "C", "contrat"]], on="date", suffixes=("_nq", "_es"))
    p["roule"] = np.r_[(p["contrat_nq"].to_numpy()[1:] != p["contrat_nq"].to_numpy()[:-1])
                       | (p["contrat_es"].to_numpy()[1:] != p["contrat_es"].to_numpy()[:-1]), True]
    p.attrs.update(cote_nq=nq.attrs["cote"], cote_es=es.attrs["cote"])
    return nq, es, p


def es_aligne(s, es):
    """Cloture de 15 h 49 de l'ES aux memes dates que s (NaN si absente)."""
    return es.set_index("date")["C"].reindex(pd.DatetimeIndex(s["date"])).to_numpy()


def positions(k, s, es, p, jusqu_au):
    if k == 0:
        return w1_echeance(s)
    if k == 1:
        return w2_fed(s)
    if k in (2, 3):
        return reequilibrage(s, indice_es(s, es), zn(s["date"], jusqu_au), zn(s["date"], jusqu_au, False),
                             1 if k == 2 else -1)
    if k == 4:
        return w5_rsi_vendeur(s)
    if k == 5:
        return w6_ecart(p)
    return w7_hiver(s)


def evaluer(k, nom, s, es, p, jusqu_au, avec_hasard=True):
    pos = positions(k, s, es, p, jusqu_au)
    if k == 5:
        rend, dol, tr, e, so = journal_paire(p, pos)
        interdit = p["roule"].to_numpy()
        rend_de = lambda q: journal_paire(p, q)[0]  # noqa: E731
    else:
        rend, dol, tr, e, so = journal(s, pos)
        interdit = T8.echeances(s)
        rend_de = lambda q: journal(s, q)[0]  # noqa: E731
    x = T8.mesures(rend, dol, tr, np.abs(pos))
    x.update(marche=nom, source=SOURCES[k])
    if avec_hasard and len(e):
        sens = int(np.sign(pos[e[0]]))
        ts = hasard(rend_de, interdit, e, so, sens, 3000 * (k + 1) + 17 * len(nom))
        x["hasard_part_battue"] = round(float((ts < x["t"]).mean()), 3)
        x["hasard_t_95"] = round(float(np.quantile(ts, 0.95)), 3)
    dates = p["date"] if k == 5 else s["date"]
    return x, pd.Series(dol, index=pd.DatetimeIndex(dates)), pd.Series(rend, index=pd.DatetimeIndex(dates))


def serie_rsi2(jusqu_au):
    """$ par seance du RSI(2) (tournoi8, NQ), pour la correlation (celle avec la zone est calculee par coffre3.py : la
    zone de protection/ lit toutes les annees)."""
    nq = T8.charger("NQ", jusqu_au)
    _, dol, _, _, _ = T8.journal(nq, T8.positions(nq, 0))
    return pd.Series(dol, index=pd.DatetimeIndex(nq["date"]))


def main():
    nq, es, p = charger()
    assert nq["date"].max() <= pd.Timestamp(FIN_EXPLORATION) and es["date"].max() <= pd.Timestamp(FIN_EXPLORATION)
    rsi = serie_rsi2(FIN_EXPLORATION)
    sortie, survivants = [], []
    for k in range(len(SOURCES)):
        for nom, s in (("NQ", nq), ("ES", es)):
            if k == 5 and nom == "ES":
                continue
            x, dol, _ = evaluer(k, nom, s, es, p, FIN_EXPLORATION)
            x["corr_rsi2"] = round(float(dol.corr(rsi.reindex(dol.index).fillna(0))), 3)
            decision = nom == "NQ"
            survit = decision and x["t"] >= T_MIN and x.get("hasard_part_battue", 0) >= PART_HASARD
            x.update(tri=decision, survit=survit)
            sortie.append(x)
            if survit:
                survivants.append({"source": k, "nom": SOURCES[k]})
            print(f"{nom} {SOURCES[k]:40s} t {x['t']:+5.2f} hasard {x.get('hasard_part_battue', 0):5.1%} "
                  f"{x['trades']:4d} trades {x['dollars_1_micro']:+8.0f} $ {'SURVIT' if survit else ''}", flush=True)
    pd.DataFrame(sortie).to_csv(ICI / "exploration3.csv", index=False)
    L = [f"Exploration 2011-2022 ; NQ : {len(nq)} seances, ES : {len(es)}, paire : {len(p)}. Survie (NQ) : t >= 2 et t au-dessus"
         " de 95 % des 1 000 placements au hasard des memes trades.", "",
         "marche | source | t | Sharpe | bat le hasard | t 95 % hasard | trades | en position | $ pour 1 micro | perte max $ |"
         " corr. RSI(2) | verdict"]
    for x in sortie:
        L.append(f"{x['marche']} | {x['source']} | {x['t']:+.2f} | {x['sharpe']:+.2f} | {x.get('hasard_part_battue', 0):.1%} |"
                 f" {x.get('hasard_t_95', 0):+.2f} | {x['trades']} | {x['en_position']:.0%} | {x['dollars_1_micro']:+,.0f} |"
                 f" {x['perte_max_1_micro']:+,.0f} | {x['corr_rsi2']:+.2f} | "
                 + ("SURVIT" if x["survit"] else ("elimine" if x["tri"] else "(descriptif)")))
    L += ["", f"Survivants : {len(survivants)}" + "".join(f"\n  {v['nom']}" for v in survivants)]
    (ICI / "exploration3.txt").write_text("\n".join(L) + "\n")
    (ICI / "survivants3.json").write_text(json.dumps(survivants, indent=1, ensure_ascii=False))
    print("\n".join(L))


if __name__ == "__main__":
    main()
