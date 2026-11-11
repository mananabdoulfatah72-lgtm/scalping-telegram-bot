"""Parties A (regimes), B (volatilite implicite contre realisee), E (rotation), F (EMA / RSI / ATR en H1). Regles : REGLES.md.

Usage : python3 divers.py [A|B|E|F]   (sans argument : les quatre ; ecrit resultats/partie_<x>.txt)
"""
import json
import sys

import numpy as np
import pandas as pd

import compte as Cp
import donnees as D
import nuit as Nn
from systeme.regime import ETATS, etats

SORTIE = D.ICI / "resultats"
RNG = np.random.default_rng(20261111)


def ecrire(nom, lignes, donnees=None):
    (SORTIE / f"{nom}.txt").write_text("\n".join(lignes) + "\n")
    if donnees is not None:
        json.dump(donnees, open(SORTIE / f"{nom}.json", "w"), indent=1, ensure_ascii=False)
    print("\n".join(lignes), flush=True)


def jours_de(B, tr, limite=1000.0):
    """Gain par seance (toutes les seances du fichier) d'une liste de trades (seance, sens, m_debut, m_fin, entree, sortie)."""
    S = len(B.J); z = np.zeros(S)
    a = lambda k, ty: np.array([x[k] for x in tr], dtype=ty)
    r, _ = Cp._journees(S, a(0, np.int64), a(1, np.int64), a(2, np.int64), a(3, np.int64), a(4, np.float64), a(5, np.float64),
                        B.M["H"], B.M["L"], 1.0, limite, D.FRAIS, D.PREF, Cp.GLISSE, z, z.copy())
    return r


def supertrend(B):
    st = pd.read_csv(D.OP / "ml/st_trades.csv"); pos = {j: i for i, j in enumerate(B.J)}; out = []
    for r in st.itertuples():
        s = pos.get(r.jour)
        if s is not None:
            out.append((s, int(r.sens), int(r.m_in), 384 if r.m_out >= 385 else int(r.m_out) - 1, float(r.entree), float(r.sortie)))
    return sorted(out, key=lambda t: (t[0], t[2]))


def retour_moyenne(M):
    """A 10 h 30, contre le mouvement depuis l'ouverture s'il depasse 0,5 ecart type quotidien ; sortie 15 h 55."""
    ok = np.nonzero(M["ok"])[0]; C = M["C"]; O = M["O"]; g = np.full(len(M["J"]), np.nan)
    r = np.diff(np.log(C[ok, D.N - 1]))
    for i in range(21, len(ok)):
        s = ok[i]; sd = r[i - 21:i - 1].std(ddof=1)                   # 20 rendements connus a la cloture de la veille
        mv = C[s, 59] / O[s, 0] - 1
        if abs(mv) >= 0.5 * sd:
            sens = -np.sign(mv); e = O[s, 60]; x = C[s, 384]
            g[s] = sens * (x - e) * 2 * D.PREF / e - D.FRAIS
        else:
            g[s] = 0.0
    return g


def t3(v, J):
    ex = J <= D.FIN_EXPLO
    return D.tstat(v), D.tstat(v[ex]), D.tstat(v[~ex])


# ====================================================================== partie A
def partie_a():
    B = Cp.Banc("2026-11-02"); M = B.M; J = B.J; ok = np.nonzero(M["ok"])[0]
    V = D.clotures(("VIX", "VIX3M")); tous = pd.Index(J)
    veille = V.reindex(tous.union(V.index)).sort_index().ffill().shift(1).reindex(tous)
    e_ok = etats(M["C"][ok, D.N - 1], veille["VIX"].to_numpy()[ok], veille["VIX3M"].to_numpy()[ok])
    etat = np.array([None] * len(J), dtype=object); etat[ok] = e_ok
    X = Nn.construire(); g0, _, _ = Nn.gains(X, 0.0)
    strat = {"zone (C2 + Q1)": np.where(M["ok"] & (J <= "2026-11-02"), jours_de(B, B.zone), np.nan),
             "nuit sans stop": g0,
             "Supertrend 10-3": np.where(M["ok"] & (J <= "2026-11-02"), jours_de(B, supertrend(B)), np.nan),
             "retour à la moyenne": np.where(J <= "2026-11-02", retour_moyenne(M), np.nan)}
    defini = np.array([e is not None for e in etat])
    L = ["Partie A : les régimes. État connu la veille. 1 MNQ au prix d'aujourd'hui, frais compris.", ""]
    part = {e: float(np.mean(etat[defini] == e)) for e in ETATS}
    L.append("Part des séances : " + ", ".join(f"{e} {part[e]:.0%}" for e in ETATS) + f" ({int(defini.sum())} séances, depuis {J[defini][0]}).")
    L += ["", "A1 (descriptif) : gain moyen par séance et t, par état. Exploration jusqu'en 2022 | contrôle depuis 2023.",
          f"{'':<22}" + "".join(f"{e:^30}" for e in ETATS)]
    res = {"parts": part, "A1": {}}
    for nom, p in strat.items():
        lig = f"{nom:<22}"; res["A1"][nom] = {}
        for e in ETATS:
            cel = []
            for per in (J <= D.FIN_EXPLO, J > D.FIN_EXPLO):
                g = np.isfinite(p) & (etat == e) & per
                cel.append(f"{p[g].mean():+6.1f}$ t{D.tstat(p[g]):+5.2f}" if g.sum() > 5 else "      —      ")
                res["A1"][nom].setdefault(e, []).append(dict(n=int(g.sum()), moy=float(p[g].mean()) if g.sum() else None, t=D.tstat(p[g]) if g.sum() > 5 else None))
            lig += f"{cel[0]} | {cel[1]}  "
        L.append(lig)
    # A2 : couper la strategie dans les etats perdants, en marche avant
    an = np.array([int(j[:4]) for j in J])

    def marche_avant(p, et):
        actif = np.ones(len(J), bool)
        for Y in range(2017, 2027):
            for e in ETATS:
                avant = np.isfinite(p) & (et == e) & (an < Y)
                if avant.sum() >= 60 and p[avant].mean() < 0:
                    actif[(an == Y) & (et == e)] = False
        return actif

    def blocs(et):
        idx = np.nonzero(defini)[0]; nb = int(np.ceil(len(idx) / 20)); perm = RNG.permutation(nb); out = et.copy()
        src = np.concatenate([idx[b * 20:(b + 1) * 20] for b in perm])[:len(idx)]
        out[idx[:len(src)]] = et[src]
        return out

    L += ["", "A2 (marche avant, 2017 - 2026) : la stratégie est coupée dans les états où elle perdait les années d'avant."]
    res["A2"] = {}
    for nom in ("zone (C2 + Q1)", "nuit sans stop"):
        p = strat[nom]; fen = np.isfinite(p) & defini & (an >= 2017)
        actif = marche_avant(p, etat); f = np.where(actif, p, 0.0)
        gain = float(f[fen].sum() - p[fen].sum()); tf, ta = D.tstat(f[fen]), D.tstat(p[fen])
        plac = []
        for _ in range(500):
            ep = blocs(etat); ap = marche_avant(p, ep); plac.append(float(np.where(ap, p, 0.0)[fen].sum() - p[fen].sum()))
        bat = float(np.mean(np.array(plac) < gain))
        adopte = tf > ta and gain > 0 and bat >= 0.95
        coupes = int((~actif & fen).sum())
        res["A2"][nom] = dict(t_toujours=ta, t_filtre=tf, gain=gain, seances_coupees=coupes, bat_placebos=bat, adopte=bool(adopte))
        L.append(f"  {nom:<16} : toujours active t {ta:.2f}, total {p[fen].sum():+,.0f} $ ; filtrée t {tf:.2f}, total {f[fen].sum():+,.0f} $ "
                 f"({coupes} séances coupées, écart {gain:+,.0f} $) ; bat {bat:.0%} des 500 placebos → {'ADOPTÉ' if adopte else 'non adopté'}".replace(",", " "))
    # A3 : retour a la moyenne seulement quand le marche est CALME
    p = strat["retour à la moyenne"]; g = np.isfinite(p) & defini
    v = np.where(etat == "CALME", p, 0.0)[g]; t, te, tc = t3(v, J[g])
    retenu = t >= 2 and v[J[g] <= D.FIN_EXPLO].mean() > 0 and v[J[g] > D.FIN_EXPLO].mean() > 0
    tt, tte, ttc = t3(p[g], J[g])
    res["A3"] = dict(t=t, t_explo=te, t_controle=tc, retenu=bool(retenu), t_toutes_seances=tt)
    L += ["", f"A3 : retour à la moyenne seulement en état CALME : t {t:.2f} (exploration {te:.2f}, contrôle {tc:.2f}), {v.sum():+,.0f} $ au total → "
              f"{'RETENU' if retenu else 'tué'}. Sur toutes les séances : t {tt:.2f} ({tte:.2f} / {ttc:.2f}).".replace(",", " ")]
    ecrire("partie_a", L, res)


# ====================================================================== partie B
def partie_b():
    M = D.nq_minutes(); J = M["J"]; ok = np.nonzero(M["ok"])[0]; O, H, L_, C = M["O"], M["H"], M["L"], M["C"]
    X = Nn.construire()
    V = D.clotures(("VXN",))["VXN"]; vx = V.reindex(pd.Index(J).union(V.index)).sort_index().ffill().reindex(pd.Index(J)).to_numpy()
    cl = C[ok, D.N - 1]; r = np.diff(np.log(cl)); Jo = J[ok]
    L = ["Partie B : volatilité implicite (VXN) contre volatilité réalisée du NQ.", ""]
    # B0 : la prime
    prime = []; pnl = []; dates = []
    for i in range(len(ok) - 22):
        if np.isfinite(vx[ok[i]]):
            prime.append(vx[ok[i]] - r[i:i + 21].std(ddof=1) * np.sqrt(252) * 100)
            pnl.append((0.8 * vx[ok[i]] / 100 / np.sqrt(252) - abs(np.exp(r[i]) - 1)) * 2 * D.PREF); dates.append(Jo[i + 1])
    prime = np.array(prime); pnl = np.array(pnl); dates = np.array(dates)
    c = np.cumsum(pnl); dd = (np.maximum.accumulate(c) - c).max()
    grille = sum(1 for i0 in range(0, len(pnl) - 60, 20) if (lambda x: (np.maximum.accumulate(np.r_[0, x]) - np.r_[0, x]).max() >= 2500)(np.cumsum(pnl[i0:i0 + 60])))
    nd = len(range(0, len(pnl) - 60, 20))
    L += [f"B0 (descriptif, {len(prime)} séances depuis {dates[0]}) : le VXN dépasse la volatilité réalisée des 21 séances suivantes de {prime.mean():.1f} points en moyenne, "
          f"{(prime > 0).mean():.0%} du temps.",
          f"   Vente chaque soir d'un straddle à un jour au prix du VXN, pour la valeur d'un MNQ : {pnl.mean():+.1f} $ par jour, t {D.tstat(pnl):.2f}, "
          f"{(pnl > 0).mean():.0%} de jours gagnants, pire jour {pnl.min():,.0f} $, pire baisse {dd:,.0f} $ ; "
          f"{grille / nd:.0%} des comptes neufs toucheraient −2 500 $ en 60 séances.".replace(",", " "),
          "   Ce n'est pas jouable chez Bulenox (ni options ni futures VIX), et le prix d'un vrai straddle à un jour n'est pas le VXN : chiffre indicatif.", ""]
    res = dict(B0=dict(prime=float(prime.mean()), part_positive=float((prime > 0).mean()), straddle_moy=float(pnl.mean()), straddle_t=D.tstat(pnl),
                       pire_jour=float(pnl.min()), pire_baisse=float(dd), comptes_touches=grille / nd))
    # B1 : la nuit quand la peur est chere (reprise de la partie N)
    nj = json.load(open(SORTIE / "nuit.json"))
    L += [f"B1 : la nuit seulement quand VXN ÷ réalisée dépasse sa médiane (F3) : sans stop t {nj['F3_0.0']['t']:.2f} "
          f"(exploration {nj['F3_0.0']['t_ex']:.2f}, contrôle {nj['F3_0.0']['t_ct']:.2f}), {nj['F3_0.0']['moy']:.1f} $ par nuit ; "
          f"toutes les nuits : t {nj['F0_0.0']['t']:.2f}, {nj['F0_0.0']['moy']:.1f} $ par nuit. Le filtre ne retient pas de meilleures nuits : il en retient moins.", ""]
    # B2 : vendre les deux cotes, version futures
    tick = D.TICK; g = np.full(len(J), np.nan)
    veille_vxn = np.full(len(J), np.nan)
    for i in range(1, len(ok)):
        veille_vxn[ok[i]] = vx[ok[i - 1]]
    for s in ok:
        if not np.isfinite(veille_vxn[s]) or J[s] > "2026-10-30":
            continue
        o = O[s, 0]; w = veille_vxn[s] / 100 / np.sqrt(252) * o; haut, bas = o + w, o - w; g[s] = 0.0
        for m in range(5, 331):
            th = H[s, m] >= haut + tick; tb = L_[s, m] <= bas - tick
            if th and tb:
                break
            if th or tb:
                sens = -1 if th else 1; niv = haut if th else bas
                e = O[s, m] if (th and O[s, m] > niv) or (tb and O[s, m] < niv) else niv
                stop = o - sens * 1.5 * w; x = C[s, 384]
                for k in range(m, 385):
                    pire = H[s, k] if sens < 0 else L_[s, k]
                    if (sens < 0 and pire >= stop) or (sens > 0 and pire <= stop):
                        ouv = O[s, k]
                        x = ouv if (k > m and ((sens < 0 and ouv > stop) or (sens > 0 and ouv < stop))) else stop - sens * tick
                        break
                g[s] = sens * (x - e) * 2 * D.PREF / e - D.FRAIS
                break
    res["B2"] = {}; ps = []
    for nom, masque in (("B2a toutes les séances", np.ones(len(J), bool)), ("B2b seulement si la peur est chère", X["cher"])):
        jou = np.isfinite(g); v = np.where(masque, g, 0.0)[jou]; t, te, tc = t3(v, J[jou]); ps.append(D.p_unilateral(t))
        res["B2"][nom] = dict(t=t, t_explo=te, t_controle=tc, trades=int((v != 0).sum()), total=float(v.sum()), par_trade=float(v[v != 0].mean()))
    passe = D.bh(ps)
    for k, (nom, m) in enumerate(res["B2"].items()):
        ret = m["t"] >= 2 and passe[k] and m["t_explo"] > 0 and m["t_controle"] > 0; m["retenue"] = bool(ret)
        L.append(f"{nom} : {m['trades']} trades, {m['par_trade']:+.1f} $ par trade, t {m['t']:.2f} (exploration {m['t_explo']:.2f}, contrôle {m['t_controle']:.2f}), "
                 f"total {m['total']:+,.0f} $ → {'RETENUE' if ret else 'tuée'}".replace(",", " "))
    ecrire("partie_b", L, res)


# ====================================================================== partie E
MARCHES = (("NQ", None, 2.0, D.PREF, 3.0), ("ES", "intraday/donnees/sp500_1min.csv.gz", 5.0, 7805.0, 4.5),
           ("RTY", "zone_multi/donnees/russell_1min.csv.gz", 5.0, 2851.0, 3.0), ("YM", "zone_multi/donnees/dow_1min.csv.gz", 0.5, 52057.0, 3.0),
           ("or", "zone_multi/donnees/or_1min.csv.gz", 10.0, 4178.0, 4.0), ("pétrole", "zone_multi/donnees/petrole_1min.csv.gz", 100.0, 92.2, 4.0),
           ("euro", "zone_multi/donnees/euro_1min.csv.gz", 12500.0, 1.142, 4.5))
NM = 236                                                                  # minutes de 9 h 30 a 13 h 25


def fenetre(chemin):
    f = D.CACHE / ("fen_" + chemin.split("/")[-1].replace(".csv.gz", ".npz"))
    if f.exists():
        z = np.load(f); return z["J"], z["O"], z["C"], z["ok"]
    d = D.minutes_marche(chemin); jour = d.t.str[:10].to_numpy()
    m = (d.t.str[11:13].astype(int) * 60 + d.t.str[14:16].astype(int) - 570).to_numpy(); g = (m >= 0) & (m < NM)
    d, jour, m = d[g], jour[g], m[g]; J = np.unique(jour); s = np.searchsorted(J, jour)
    O = np.full((len(J), NM), np.nan); C = O.copy(); O[s, m] = d.o.to_numpy(); C[s, m] = d.c.to_numpy()
    ok = np.isfinite(C[:, 0]) & np.isfinite(C[:, NM - 1]) & (np.isfinite(C).sum(1) >= 220)
    for i in np.nonzero(ok)[0]:
        c = pd.Series(C[i]).ffill().to_numpy(); t = ~np.isfinite(O[i]); O[i, t] = c[t]; C[i] = c
    np.savez_compressed(f, J=J, O=O, C=C, ok=ok)
    return J, O, C, ok


def partie_e():
    M = D.nq_minutes(); dat = {"NQ": (M["J"], M["O"][:, :NM], M["C"][:, :NM], M["ok"])}
    for nom, ch, *_ in MARCHES[1:]:
        dat[nom] = fenetre(ch)
    commun = sorted(set.intersection(*[set(dat[n][0][dat[n][3]]) for n in dat])); Jc = np.array(commun)
    K = len(MARCHES); S = len(Jc); O = np.empty((K, S, NM)); C = np.empty((K, S, NM))
    for k, (nom, *_) in enumerate(MARCHES):
        idx = np.searchsorted(dat[nom][0], Jc); O[k] = dat[nom][1][idx]; C[k] = dat[nom][2][idx]
    mv = np.log(C[:, :, NM - 2] / O[:, :, 0])                               # mouvement 9 h 30 -> 13 h 24
    trades = []                                                            # (seance, brut $, frais)
    for s in range(60, S):
        sd = mv[:, s - 60:s].std(axis=1, ddof=1)
        pos = -1; sens = 0; e = 0.0; best = 0.0
        m = 15
        while m < NM - 1:
            controle = m % 15 == 0 and m <= 210
            if pos >= 0:                                                   # stop suiveur sur la cloture de la minute precedente
                c = C[pos, s, m - 1]; best = max(best, c) if sens > 0 else min(best, c)
                if (sens > 0 and c <= best * np.exp(-0.5 * sd[pos])) or (sens < 0 and c >= best * np.exp(0.5 * sd[pos])):
                    x = O[pos, s, m]; _, _, mult, ref, fr = MARCHES[pos]
                    trades.append((s, sens * (x - e) * mult * ref / e, fr)); pos = -1
            if controle:
                sc = np.log(C[:, s, m - 1] / O[:, s, 0]) / sd
                men = int(np.argmax(np.abs(sc))); cible = (men, int(np.sign(sc[men]))) if abs(sc[men]) >= 1 else None
                if pos >= 0 and (cible is None and abs(sc[pos]) < 0.5 or np.sign(sc[pos]) != sens or (cible is not None and cible[0] != pos)):
                    x = O[pos, s, m]; _, _, mult, ref, fr = MARCHES[pos]
                    trades.append((s, sens * (x - e) * mult * ref / e, fr)); pos = -1
                if pos < 0 and cible is not None:
                    pos, sens = cible; e = O[pos, s, m]; best = e
            m += 1
        if pos >= 0:
            x = C[pos, s, NM - 2]; _, _, mult, ref, fr = MARCHES[pos]
            trades.append((s, sens * (x - e) * mult * ref / e, fr))
    ts = np.array([t[0] for t in trades]); brut = np.array([t[1] for t in trades]); fr = np.array([t[2] for t in trades])
    jour = np.zeros(S); np.add.at(jour, ts, brut - fr); v = jour[60:]; Jv = Jc[60:]
    t, te, tc = t3(v, Jv)
    plac = []
    for _ in range(1000):
        sg = RNG.choice([-1.0, 1.0], len(brut)); j = np.zeros(S); np.add.at(j, ts, sg * brut - fr); plac.append(D.tstat(j[60:]))
    bat = float(np.mean(np.array(plac) < t))
    retenue = t >= 2 and v[Jv <= D.FIN_EXPLO].mean() > 0 and v[Jv > D.FIN_EXPLO].mean() > 0 and bat >= 0.95
    L = ["Partie E : la rotation entre 7 marchés (NQ, ES, RTY, YM, or, pétrole, euro), 1 micro, 9 h 30 - 13 h 25.",
         f"{len(v)} séances communes du {Jv[0]} au {Jv[-1]}, {len(brut)} trades ({len(brut) / len(v):.1f} par séance).",
         f"Avant frais : {brut.sum() / len(v):+.1f} $ par séance ; frais : {fr.sum() / len(v):.1f} $ par séance ; net : {v.mean():+.1f} $ par séance.",
         f"t {t:.2f} (exploration {te:.2f}, contrôle {tc:.2f}) ; total {v.sum():+,.0f} $ ; bat {bat:.0%} des 1 000 placebos → {'RETENUE' if retenue else 'tuée'}".replace(",", " ")]
    ecrire("partie_e", L, dict(t=t, t_explo=te, t_controle=tc, trades=len(brut), net_par_seance=float(v.mean()), brut_par_seance=float(brut.sum() / len(v)),
                               bat_placebos=bat, retenue=bool(retenue)))


# ====================================================================== partie F
def heures(nom):
    t, o, h, l, c = D.cfd(nom); _, mn, _ = D.heure_ny(t)
    g = ~((mn >= 1015) & (mn < 1080))                                      # rien entre 16 h 55 et 18 h (New York)
    d = pd.DataFrame(dict(k=t[g] // 60, t=t[g], o=o[g], h=h[g], l=l[g], c=c[g])).groupby("k").agg(t=("t", "first"), o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"))
    dj, mn2, _ = D.heure_ny(d.t.to_numpy())
    jt = np.where(mn2 >= 1080, (pd.to_datetime(dj) + pd.Timedelta(days=1)).strftime("%Y-%m-%d"), dj)   # journee de trading
    return d.index.to_numpy(), d.o.to_numpy(), d.h.to_numpy(), d.l.to_numpy(), d.c.to_numpy(), np.asarray(jt)


def indicateurs(h, l, c):
    n = len(c); e50 = np.empty(n); e200 = np.empty(n); rsi = np.full(n, 50.0); atr = np.full(n, np.nan)
    e50[0] = e200[0] = c[0]; a50, a200 = 2 / 51, 2 / 201
    tr = np.maximum(h - l, np.maximum(abs(h - np.r_[c[0], c[:-1]]), abs(l - np.r_[c[0], c[:-1]])))
    mg = mp = 0.0
    for i in range(1, n):
        e50[i] = e50[i - 1] + a50 * (c[i] - e50[i - 1]); e200[i] = e200[i - 1] + a200 * (c[i] - e200[i - 1])
        ch = c[i] - c[i - 1]; mg = (mg * 13 + max(ch, 0)) / 14; mp = (mp * 13 + max(-ch, 0)) / 14
        rsi[i] = 100 - 100 / (1 + mg / mp) if mp > 0 else 100.0
        atr[i] = tr[1:i + 1].mean() if i <= 14 else (atr[i - 1] * 13 + tr[i]) / 14
    med = pd.Series(atr).rolling(240, min_periods=240).median().shift(1).to_numpy()
    return e50, e200, rsi, atr, med


def partie_f():
    L = ["Partie F : EMA 50 / 200, RSI(14) et ATR(14) en barres d'une heure, 1 micro, à plat de 16 h 55 à 18 h.", ""]
    res = {}; ps = []
    for nom, code, mult, ref, frais, tick in (("or (MGC)", "xauusd", 10.0, 4178.0, 4.0, 0.10), ("Nasdaq (MNQ)", "usatechidxusd", 2.0, D.PREF, 3.0, 0.25)):
        k, o, h, l, c, jt = heures(code); n = len(c)
        e50, e200, rsi, atr, med = indicateurs(h, l, c)
        suite = np.r_[np.diff(k) == 1, False]                              # la barre suivante suit sans coupure
        tr = []; d = 0; pertes = 0; jour_p = ""
        for i in range(260, n):
            if d != 0:
                tk = tick / ref * e; sorti = False
                if (d > 0 and o[i] <= stop) or (d < 0 and o[i] >= stop):
                    x = o[i]; sorti = True
                elif (d > 0 and l[i] <= stop) or (d < 0 and h[i] >= stop):
                    x = stop - d * tk; sorti = True
                elif (d > 0 and h[i] >= obj + tk) or (d < 0 and l[i] <= obj - tk):
                    x = obj; sorti = True
                elif not suite[i]:
                    x = c[i]; sorti = True
                if sorti:
                    g = d * (x - e) * mult * ref / e
                    tr.append((jt[i], g))
                    if jt[i] != jour_p:
                        jour_p = jt[i]; pertes = 0
                    pertes = pertes + 1 if g - frais < 0 else 0
                    d = 0
                else:
                    meil = max(meil, c[i]) if d > 0 else min(meil, c[i])
                    if d * (meil - e) >= 1.5 * a0:
                        stop = max(stop, meil - 1.5 * a0) if d > 0 else min(stop, meil + 1.5 * a0)
            if d == 0 and suite[i] and i + 1 < n and suite[i + 1] and np.isfinite(med[i]) and atr[i] >= med[i]:
                if jt[i + 1] != jour_p:
                    jour_p = jt[i + 1]; pertes = 0
                if pertes < 3:
                    if c[i] > e50[i] > e200[i] and rsi[i] >= 55:
                        d = 1
                    elif c[i] < e50[i] < e200[i] and rsi[i] <= 45:
                        d = -1
                    if d != 0:
                        e = o[i + 1]; a0 = atr[i]; stop = e - d * 1.5 * a0; obj = e + d * 3 * a0; meil = e
        Jt = np.unique(jt[260:]); idx = np.searchsorted(Jt, np.array([t[0] for t in tr])); brut = np.array([t[1] for t in tr])
        jour = np.zeros(len(Jt)); np.add.at(jour, idx, brut - frais)
        t, te, tc = t3(jour, Jt)
        plac = []
        for _ in range(1000):
            j = np.zeros(len(Jt)); np.add.at(j, idx, RNG.choice([-1.0, 1.0], len(brut)) * brut - frais); plac.append(D.tstat(j))
        bat = float(np.mean(np.array(plac) < t)); ps.append(D.p_unilateral(t))
        an = np.array([x[:4] for x in Jt]); pos = sum(jour[an == a].sum() > 0 for a in sorted(set(an)))
        c_ = np.cumsum(jour); dd = float((np.maximum.accumulate(c_) - c_).max())
        res[nom] = dict(trades=len(brut), gagnants=float((brut - frais > 0).mean()), t=t, t_explo=te, t_controle=tc, total=float(jour.sum()), par_trade=float((brut - frais).mean()),
                        bat_placebos=bat, annees_pos=int(pos), annees=len(set(an)), pire_baisse=dd, debut=str(Jt[0]), fin=str(Jt[-1]),
                        moy_explo=float(jour[Jt <= D.FIN_EXPLO].mean()), moy_controle=float(jour[Jt > D.FIN_EXPLO].mean()))
    passe = D.bh(ps)
    for k, (nom, m) in enumerate(res.items()):
        ret = m["t"] >= 2 and passe[k] and m["moy_explo"] > 0 and m["moy_controle"] > 0 and m["bat_placebos"] >= 0.95; m["retenue"] = bool(ret)
        L.append(f"{nom} ({m['debut']} → {m['fin']}) : {m['trades']} trades, {m['gagnants']:.0%} de gagnants, {m['par_trade']:+.1f} $ par trade, total {m['total']:+,.0f} $, "
                 f"pire baisse {m['pire_baisse']:,.0f} $, {m['annees_pos']} années positives sur {m['annees']} ; t {m['t']:.2f} (exploration {m['t_explo']:.2f}, contrôle {m['t_controle']:.2f}) ; "
                 f"bat {m['bat_placebos']:.0%} des placebos → {'RETENUE' if ret else 'tuée'}".replace(",", " "))
    ecrire("partie_f", L, res)


if __name__ == "__main__":
    quoi = sys.argv[1:] or ["A", "B", "E", "F"]
    for q in quoi:
        {"A": partie_a, "B": partie_b, "E": partie_e, "F": partie_f}[q]()
        print()
