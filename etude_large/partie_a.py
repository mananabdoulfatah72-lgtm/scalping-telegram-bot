#!/usr/bin/env python3
"""etude_large/README.md, parties A et C (regles fixees le 22 octobre 2026, avant tout calcul).
A : 7 strategies intraday (A1 zone, A2a Gao, A2b Baltussen, A3a OPR 5 min, A3b OPR 30 min, A4 periodicite, A5 zone
inversee) x 29 ETF Alpaca 5 minutes (27 decidables), seance 9 h 30 - 16 h, frais du plus petit contrat CME au prix de
la veille. Exploration 2016 - 2022, coffre 2023 - 20 octobre 2026.
C : complement de la zone du bot (NQ minute, sans les jours de la Fed), correlation et Sharpe a risque egal.

Lancer : python3 etude_large/partie_a.py (numpy, pandas ; variable KB : branche de recherche extraite, comme
delta_mesures). Ecrit resultats_a.txt et essais_a.csv."""
import os
import sys
from math import erf, sqrt
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
ETF = RACINE / "donnees_libres" / "etf_5min"
YAHOO = RACINE / "donnees_libres" / "yahoo" / "jour"
sys.path.insert(0, str(ICI))
from marches import MARCHES  # noqa: E402

NB = 78                                   # barres de 5 minutes, 9 h 30 - 16 h
CONTROLES = list(range(5, 72, 6))         # cloture de la barre de 10 h, 10 h 30, ..., 15 h 30
B1530 = 71                                # cloture a 15 h 30
JM = 14                                   # seances de la moyenne de la zone
EXPLO = ("2016-01-01", "2022-12-31")
COFFRE = ("2023-01-01", "2026-10-20")
STRATEGIES = ["A1 zone", "A2a Gao", "A2b Baltussen", "A3a OPR 5 min", "A3b OPR 30 min", "A4 periodicite",
              "A5 zone inversee"]


# ----------------------------------------------------------------------------- donnees
def calendrier():
    """Seances completes de la bourse americaine : celles ou SPY a sa barre de 15 h 55 (les demi-seances sont exclues,
    comme seances_completes du bot)."""
    d = pd.read_csv(ETF / "SPY.csv.gz", usecols=["t"])
    t = pd.to_datetime(d["t"])
    j = t.dt.normalize()
    der = t.groupby(j).max()
    return pd.DatetimeIndex(der.index[(der.dt.hour == 15) & (der.dt.minute == 55)])


def tableaux(etf, jours):
    """Tableaux seances x 78 barres (o, h, l, c, v), barres manquantes remplies par la cloture precedente de la seance
    (v = 0). Une seance est jouable si une barre existe avant 10 h. Ouverture = ouverture de la premiere barre."""
    d = pd.read_csv(ETF / f"{etf}.csv.gz")
    t = pd.to_datetime(d["t"])
    jour = t.dt.normalize().values
    b = ((t.dt.hour * 60 + t.dt.minute - 570) // 5).values
    i = np.searchsorted(jours.values, jour)
    ok = (i < len(jours)) & (b >= 0) & (b < NB)
    ok &= jours.values[np.minimum(i, len(jours) - 1)] == jour
    i, b, d = i[ok], b[ok], d[ok]
    tab = {}
    for col in "ohlcv":
        a = np.full((len(jours), NB), np.nan)
        a[i, b] = d[col].values
        tab[col] = a
    present = ~np.isnan(tab["c"])
    C = pd.DataFrame(tab["c"]).ffill(axis=1).values
    premiere = np.argmax(present, axis=1)
    jouable = present[:, :6].any(axis=1)
    O0 = tab["o"][np.arange(len(jours)), premiere]
    # avant la premiere barre : prix d'ouverture (aucune information perdue, aucun prix du futur)
    C = np.where(np.isnan(C), O0[:, None], C)
    H = np.where(np.isnan(tab["h"]), C, tab["h"])
    L = np.where(np.isnan(tab["l"]), C, tab["l"])
    V = np.nan_to_num(tab["v"])
    return dict(O0=np.where(jouable, O0, np.nan), H=H, L=L, C=C, V=V, jouable=jouable)


def niveau_future(yahoo, jours):
    """Cloture Yahoo du future la veille de chaque seance (derniere connue avant le jour)."""
    y = pd.read_csv(YAHOO / f"{yahoo}.csv.gz", usecols=["t", "c"])
    y["t"] = pd.to_datetime(y["t"])
    y = y.dropna().sort_values("t")
    idx = np.searchsorted(y["t"].values, jours.values) - 1
    v = np.where(idx >= 0, y["c"].values[np.maximum(idx, 0)], np.nan)
    return pd.Series(v).bfill().values          # avant le premier jour Yahoo : premier niveau connu


def preparer(x):
    """Zone : sigma a chaque barre (14 seances jouables precedentes), VWAP, veille, references."""
    C, H, L, V, O0, ok = x["C"], x["H"], x["L"], x["V"], x["O0"], x["jouable"]
    n = len(C)
    veille = np.full(n, np.nan)
    der = -1
    for k in range(n):
        if der >= 0:
            veille[k] = C[der, NB - 1]
        if ok[k]:
            der = k
    mouv = np.abs(C / O0[:, None] - 1)
    sigma = np.full_like(mouv, np.nan)
    sigma[ok] = pd.DataFrame(mouv[ok]).rolling(JM, min_periods=JM).mean().shift(1).values
    typ = (H + L + C) / 3
    cv = np.cumsum(V, axis=1)
    vwap = np.where(cv > 0, np.cumsum(typ * V, axis=1) / np.where(cv > 0, cv, 1),
                    np.cumsum(typ, axis=1) / np.arange(1, NB + 1))
    x.update(veille=veille, sigma=sigma, vwap=vwap, href=np.fmax(O0, veille), bref=np.fmin(O0, veille))
    return x


# ----------------------------------------------------------------------------- strategies (rendement net d'une seance)
def a1_zone(x, k, cout, inverse=False):
    """A1 (inverse=False) ou A5 (inverse=True). Retourne (rendement net, nombre d'allers-retours)."""
    C, s, vw, hr, br = x["C"][k], x["sigma"][k], x["vwap"][k], x["href"][k], x["bref"][k]
    if np.isnan(hr) or np.isnan(s[CONTROLES[0]]):
        return 0.0, 0
    r, n, pos, pe, se = 0.0, 0, 0, 0.0, 0.0
    for m in CONTROLES:
        p = C[m]
        ub, lb = hr * (1 + s[m]), br * (1 - s[m])
        if pos:
            if not inverse:
                sortie = (pos > 0 and p <= max(ub, vw[m])) or (pos < 0 and p >= min(lb, vw[m]))
            else:
                sortie = ((pos < 0 and (p <= vw[m] or p >= pe * (1 + se))) or
                          (pos > 0 and (p >= vw[m] or p <= pe * (1 - se))))
            if sortie:
                r += pos * (p / pe - 1) - cout
                pos = 0
        if not pos:
            sens = 1 if p > ub else (-1 if p < lb else 0)
            if sens:
                pos, pe, se, n = (-sens if inverse else sens), p, s[m], n + 1
    if pos:
        r += pos * (C[NB - 1] / pe - 1) - cout
    return r, n


def a2(x, k, cout, b_signal):
    v, C = x["veille"][k], x["C"][k]
    if np.isnan(v):
        return 0.0, 0
    sens = np.sign(C[b_signal] / v - 1)
    if sens == 0:
        return 0.0, 0
    return sens * (C[NB - 1] / C[B1530] - 1) - cout, 1


def sortie_stop(x, k, debut, sens, pe, stop, objectif):
    """Premiere barre apres debut qui touche le stop (prioritaire) ou l'objectif ; sinon 16 h."""
    H, L, C = x["H"][k], x["L"][k], x["C"][k]
    for m in range(debut, NB):
        if sens > 0:
            if L[m] <= stop:
                return stop
            if H[m] >= objectif:
                return objectif
        else:
            if H[m] >= stop:
                return stop
            if L[m] <= objectif:
                return objectif
    return C[NB - 1]


def a3a(x, k, cout):
    O, C, H, L = x["O0"][k], x["C"][k][0], x["H"][k][0], x["L"][k][0]
    sens = np.sign(C - O)
    if sens == 0:
        return 0.0, 0
    stop = L if sens > 0 else H
    risque = abs(C - stop)
    if risque <= 0:
        return 0.0, 0
    ps = sortie_stop(x, k, 1, sens, C, stop, C + sens * 10 * risque)
    return sens * (ps / C - 1) - cout, 1


def a3b(x, k, cout):
    H, L, C = x["H"][k], x["L"][k], x["C"][k]
    hh, ll = H[:6].max(), L[:6].min()
    for m in range(6, NB - 1):
        sens = 1 if C[m] > hh else (-1 if C[m] < ll else 0)
        if sens:
            stop = ll if sens > 0 else hh
            ps = sortie_stop(x, k, m + 1, sens, C[m], stop, np.inf if sens > 0 else -np.inf)
            return sens * (ps / C[m] - 1) - cout, 1
    return 0.0, 0


def a4_tout(x, couts):
    """A4 pour toutes les seances : rendements des 13 demi-heures, signe de leur moyenne sur les 40 seances jouables
    precedentes. Frais : un demi aller-retour par unite de position changee (entree, retournements, sortie)."""
    C, O0, ok = x["C"], x["O0"], x["jouable"]
    fins = np.arange(5, NB, 6)
    prix = np.column_stack([O0, C[:, fins]])
    r = prix[:, 1:] / prix[:, :-1] - 1                    # 13 demi-heures
    moy = np.full_like(r, np.nan)
    moy[ok] = pd.DataFrame(r[ok]).rolling(40, min_periods=40).mean().shift(1).values
    sens = np.sign(np.nan_to_num(moy))
    chemin = np.column_stack([np.zeros(len(r)), sens, np.zeros(len(r))])
    tours = np.abs(np.diff(chemin, axis=1)).sum(axis=1) / 2
    net = (sens * r).sum(axis=1) - tours * couts
    net = np.where(ok & ~np.isnan(moy).any(axis=1), net, 0.0)
    n = np.where(ok & ~np.isnan(moy).any(axis=1), (np.abs(np.diff(chemin, axis=1)) > 0).sum(axis=1) // 2, 0)
    return net, n


def series(etf, jours, cout_rt):
    """Rendement net de chaque seance pour les 7 strategies (0 sans trade ou seance non jouable)."""
    x = preparer(tableaux(etf, jours))
    n = len(jours)
    out = {s: np.zeros(n) for s in STRATEGIES}
    nt = {s: 0 for s in STRATEGIES}
    for k in range(n):
        if not x["jouable"][k]:
            continue
        c = cout_rt[k]
        for s, f in (("A1 zone", lambda: a1_zone(x, k, c)), ("A5 zone inversee", lambda: a1_zone(x, k, c, True)),
                     ("A2a Gao", lambda: a2(x, k, c, 5)), ("A2b Baltussen", lambda: a2(x, k, c, B1530)),
                     ("A3a OPR 5 min", lambda: a3a(x, k, c)), ("A3b OPR 30 min", lambda: a3b(x, k, c))):
            r, m = f()
            out[s][k] = r
            nt[s] += m
    out["A4 periodicite"], n4 = a4_tout(x, cout_rt)
    nt["A4 periodicite"] = int(n4.sum())
    return out, nt, x


# ----------------------------------------------------------------------------- statistiques
def t_stat(r):
    r = np.asarray(r, float)
    sd = r.std(ddof=1)
    return float(r.mean() / sd * np.sqrt(len(r))) if sd > 0 else 0.0


def p_unilateral(t):
    return 0.5 * (1 - erf(t / sqrt(2)))


def bh(p, q=0.10):
    """Benjamini-Hochberg : masque des hypotheses retenues."""
    p = np.asarray(p)
    o = np.argsort(p)
    seuil = q * np.arange(1, len(p) + 1) / len(p)
    ok = p[o] <= seuil
    kmax = np.where(ok)[0].max() + 1 if ok.any() else 0
    garde = np.zeros(len(p), bool)
    garde[o[:kmax]] = True
    return garde


def sharpe(r):
    r = np.asarray(r, float)
    return float(r.mean() / r.std(ddof=1) * np.sqrt(252)) if r.std(ddof=1) > 0 else 0.0


# ----------------------------------------------------------------------------- zone du bot (NQ minute)
def zone_bot(jours):
    """Rendement quotidien net de la zone du bot (V1 sans filtre, sans les jours de la Fed) sur les minutes du NQ
    (recherche 2011 - 2026, completees par le robot jusqu'au 20 octobre), aligne sur le calendrier des ETF."""
    sys.path.insert(0, str(RACINE / "delta_mesures"))
    import etude as DM
    sys.path.insert(0, str(DM.KB / "fonds"))
    import fomc
    rech = pd.read_csv(DM.RECHERCHE)
    robot = pd.read_csv(DM.ROBOT)
    bars = pd.concat([rech, robot[robot["t"] > rech["t"].iloc[-1]]], ignore_index=True)
    z = DM.preparer(bars)
    tr = DM.trades_zone(z, "2016-01-01", DM.FIN)
    fed = set(pd.DatetimeIndex(fomc.annonces()))
    tr = tr[~tr["jour"].isin(fed)]
    ouverture = pd.Series(z["C"][:, 0], index=z["jours"])
    r = (tr.groupby("jour")["points"].sum() / ouverture.reindex(tr.groupby("jour").size().index)).reindex(jours)
    return r.fillna(0.0).values, len(tr)


# ----------------------------------------------------------------------------- principal
def main():
    jours = calendrier()
    jours = jours[jours <= pd.Timestamp(COFFRE[1])]
    e = (jours >= EXPLO[0]) & (jours <= EXPLO[1])
    c = (jours >= COFFRE[0]) & (jours <= COFFRE[1])
    lignes, toutes = [], {}
    for etf, fut, yah, contrat, mult, tick, comm, decide in MARCHES:
        F = niveau_future(yah, jours)
        cout = (2 * comm + 2 * tick * mult) / (F * mult)
        r, nt, x = series(etf, jours, cout)
        rb, _, _ = series(etf, jours, np.zeros_like(cout))          # avant frais (information)
        for s in STRATEGIES:
            rs = r[s]
            ok = x["jouable"]
            toutes[(etf, s)] = rs
            lignes.append(dict(etf=etf, future=fut, contrat=contrat, strategie=s, decide=decide,
                               seances=int(ok.sum()), trades=nt[s], frais_pb=float(np.median(cout[ok]) * 1e4),
                               t_explo=t_stat(rs[e]), moy_explo_pb=float(rs[e].mean() * 1e4),
                               t_coffre=t_stat(rs[c]), t_brut_explo=t_stat(rb[s][e]),
                               t_brut_coffre=t_stat(rb[s][c]),
                               moy_coffre_pb=float(rs[c].mean() * 1e4), sharpe_explo=sharpe(rs[e]),
                               sharpe_coffre=sharpe(rs[c])))
        print(f"{etf} fait", flush=True)
    df = pd.DataFrame(lignes)
    zb, ntz = zone_bot(jours)
    for i, l in df.iterrows():
        rs = toutes[(l["etf"], l["strategie"])]
        df.loc[i, "corr_zone"] = float(np.corrcoef(rs[e], zb[e])[0, 1]) if rs[e].std() > 0 else np.nan
        perd = e & (zb < 0)
        df.loc[i, "moy_jours_zone_perd_pb"] = float(rs[perd].mean() * 1e4)
    dec = df["decide"].values
    p = np.array([p_unilateral(t) for t in df["t_explo"]])
    df["p_explo"] = p
    df["bh10"] = False
    df.loc[dec, "bh10"] = bh(p[dec])
    df["explo_ok"] = df["bh10"] & (df["t_explo"] >= 2.0)
    df["survie"] = df["explo_ok"] & (df["t_coffre"] >= 1.5)
    df.to_csv(ICI / "essais_a.csv", index=False, float_format="%.4f")
    ecrire(df, toutes, zb, ntz, e, c, jours)


def ecrire(df, toutes, zb, ntz, e, c, jours):
    L = ["Etude large, parties A et C (etude_large/README.md, regles fixees le 22 octobre 2026 avant tout calcul)",
         f"Seances : {len(jours)} ({jours[0].date()} - {jours[-1].date()}) ; exploration {int(e.sum())}, coffre "
         f"{int(c.sum())}. Rendements nets par seance (0 sans trade), frais du plus petit contrat CME au prix de la veille.",
         ""]
    q = toutes[("QQQ", "A1 zone")]
    corr = float(np.corrcoef(q, zb)[0, 1])
    L.append(f"CONTROLE : correlation des seances A1 QQQ 5 min / zone du bot NQ minute (2016 - 2026, {ntz} trades du bot) "
             f": {corr:.2f} -> {'methode acceptee (>= 0,6)' if corr >= 0.6 else 'A1 et A5 seulement descriptives (< 0,6)'}")
    L.append(f"  zone du bot NQ minute : t exploration {t_stat(zb[e]):+.2f}, t coffre {t_stat(zb[c]):+.2f} ; "
             f"A1 QQQ : t {t_stat(q[e]):+.2f} / {t_stat(q[c]):+.2f}")
    L.append("")
    dec = df[df["decide"]]
    L.append(f"DECISION A : {int(dec['explo_ok'].sum())} essai(s) sur {len(dec)} passent l'exploration (t >= 2 et BH 10 %) ; "
             f"{int(dec['survie'].sum())} survivent au coffre (t >= 1,5).")
    for _, l in dec[dec["explo_ok"]].iterrows():
        L.append(f"  {l['strategie']:<18} {l['etf']:>5} ({l['contrat']}) : t explo {l['t_explo']:+.2f} -> coffre "
                 f"{l['t_coffre']:+.2f} {'SURVIT' if l['survie'] else 'echoue au coffre'}")
    L.append("")
    L.append("Tableau complet (t net exploration 2016-2022 | t net coffre 2023-2026), par strategie :")
    for s in STRATEGIES:
        x = df[df["strategie"] == s]
        L.append(f"\n{s} : mediane des t explo {x['t_explo'].median():+.2f}, coffre {x['t_coffre'].median():+.2f} ; "
                 f"t > 0 sur les deux periodes : {int(((x['t_explo'] > 0) & (x['t_coffre'] > 0)).sum())} marches sur {len(x)}")
        L.append(f"  avant frais : mediane des t explo {x['t_brut_explo'].median():+.2f}, coffre {x['t_brut_coffre'].median():+.2f} ; "
                 f"t brut > 0 sur les deux periodes : {int(((x['t_brut_explo'] > 0) & (x['t_brut_coffre'] > 0)).sum())} marches")
        L.append("  ETF    contrat  trades  frais(pb)  t explo  t coffre  Sharpe coffre  corr zone  jours ou la zone perd (pb)"
                 "  | avant frais : t explo  t coffre")
        for _, l in x.sort_values("t_explo", ascending=False).iterrows():
            L.append(f"  {l['etf']:<6} {l['contrat']:<7} {l['trades']:>6}  {l['frais_pb']:>8.1f}  {l['t_explo']:+7.2f}  "
                     f"{l['t_coffre']:+8.2f}  {l['sharpe_coffre']:+13.2f}  {l['corr_zone']:+9.2f}  "
                     f"{l['moy_jours_zone_perd_pb']:+10.2f}  | {l['t_brut_explo']:+7.2f}  {l['t_brut_coffre']:+7.2f}"
                     f"{'' if l['decide'] else '  (information)'}")
    # partie C
    L.append("\nPARTIE C : complement de la zone")
    surv = dec[dec["survie"]]
    if surv.empty:
        L.append("  Aucune survivante de A : pas de complement a juger (critere fixe d'avance).")
    for _, l in surv.iterrows():
        rs = toutes[(l["etf"], l["strategie"])]
        w = zb[e].std() / rs[e].std()
        comb = zb + w * rs
        ok = (l["corr_zone"] < 0.3) and sharpe(comb[c]) > sharpe(zb[c])
        L.append(f"  {l['strategie']} {l['etf']} : corr {l['corr_zone']:+.2f}, Sharpe coffre zone {sharpe(zb[c]):+.2f} "
                 f"-> zone + complement {sharpe(comb[c]):+.2f} : {'RETENU' if ok else 'non retenu'}")
    # information : les meilleurs complements possibles sur l'exploration (correlation negative et gain les jours ou la
    # zone perd), avec leur coffre
    L.append("\n  Pour information, les 10 essais qui gagnent le plus les jours ou la zone perd (exploration), et leur coffre :")
    for _, l in dec.sort_values("moy_jours_zone_perd_pb", ascending=False).head(10).iterrows():
        L.append(f"  {l['strategie']:<18} {l['etf']:>5} : {l['moy_jours_zone_perd_pb']:+.2f} pb ces jours-la, corr "
                 f"{l['corr_zone']:+.2f}, t explo {l['t_explo']:+.2f}, t coffre {l['t_coffre']:+.2f}")
    (ICI / "resultats_a.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L[:20]))


if __name__ == "__main__":
    main()
