#!/usr/bin/env python3
"""Partie G (README.md) : l'elan intraday du NQ la ou la zone est a plat. Zone sans filtre recalculee sur les minutes de
la partie E (controle contre delta_mesures/etude.py), carte de l'elan par etat de la zone, regles G1 a G3 avec 40 + 40
jumeaux de bruit. Ecrit resultats/g/partie_g.json et resultats/g/partie_g.txt.
Lancer : KB=<branche de recherche extraite> DELTA_MESURES=<dossier delta_mesures> python3 scalping/partie_g.py"""
import json
import multiprocessing as mp
import os
import sys

import numpy as np
import pandas as pd
from numba import njit
from scipy.stats import norm

import bruit as B
import commun as K
import partie_e as E
import partie_f as F

SORTIE = K.ICI / "resultats" / "g"
REGLES = ["G1", "G2", "G3"]
NOMS = {"G1": "elan dans la bande, zone a plat, 30 min", "G2": "elan dans la bande, zone a plat, 1re fois, jusqu'a 15 h 55",
        "G3": "elan du matin sans trade de zone, de 12 h a 15 h 55"}
SEUIL_RETENUE = float(norm.ppf(1 - 0.05 / len(REGLES)))
JUMEAUX = 40


def zone_tableaux(d):
    O, H, L, C, V = d["o"], d["h"], d["l"], d["c"], d["v"]
    ok = d["complete"]
    idx = np.flatnonzero(ok)
    mv = np.abs(C / O[:, [0]] - 1)
    sigma = np.full(C.shape, np.nan)
    for t in range(len(ok)):
        n = int(np.searchsorted(idx, t))
        if n >= 14:
            sigma[t] = mv[idx[n - 14:n]].mean(axis=0)
    prec = d["prec_meme"]
    veille = np.where(prec >= 0, C[np.maximum(prec, 0), -1], np.nan)
    typ = (H + L + C) / 3
    cumv = np.cumsum(V, axis=1)
    vwap = np.where(cumv > 0, np.cumsum(typ * V, axis=1) / np.where(cumv > 0, cumv, 1.0),
                    np.cumsum(typ, axis=1) / np.arange(1, C.shape[1] + 1))
    jouable = ok & np.isfinite(veille) & np.isfinite(sigma[:, 30])
    return sigma, vwap, np.fmax(O[:, 0], veille), np.fmin(O[:, 0], veille), jouable


@njit(cache=True)
def _zone(O, C, sigma, vwap, href, bref, jouable):
    """Zone sans filtre (comme delta_mesures zone_jour) : etat apres la decision de chaque controle (10 h - 15 h 30) et
    trades (seance, minute d'entree, sens, minute de sortie)."""
    S, N = C.shape
    pos = np.zeros((S, 12))
    dedans = np.zeros((S, 12), np.bool_)
    e = np.full((S, 12), np.nan)
    tr = np.zeros((S * 12, 4), np.int64)
    nt = 0
    for s in range(S):
        if not jouable[s]:
            continue
        virt, me = 0, -1
        for m in range(30, N):
            p = C[s, m]
            if m == N - 1:
                if virt != 0:
                    tr[nt, 0], tr[nt, 1], tr[nt, 2], tr[nt, 3] = s, me, virt, m
                    nt += 1
                break
            if m % 30:
                continue
            sg = sigma[s, m]
            ub, lb = href[s] * (1 + sg), bref[s] * (1 - sg)
            if virt != 0 and ((virt > 0 and p <= max(ub, vwap[s, m])) or (virt < 0 and p >= min(lb, vwap[s, m]))):
                tr[nt, 0], tr[nt, 1], tr[nt, 2], tr[nt, 3] = s, me, virt, m
                nt += 1
                virt = 0
            if virt == 0 and m <= 360:
                sens = 1 if p > ub else (-1 if p < lb else 0)
                if sens != 0:
                    virt, me = sens, m
            if m <= 360:
                c = m // 30 - 1
                pos[s, c] = virt
                dedans[s, c] = lb <= p <= ub
                e[s, c] = (p / O[s, 0] - 1) / sg
    return pos, dedans, e, tr[:nt]


@njit(cache=True)
def _regles(O, C, pos, dedans, e, ech, pt, frais, regle):
    S, N = C.shape
    g, cote, entree = np.full(S, np.nan), np.zeros(S), np.full(S, -1, np.int64)
    for s in range(S):
        tot, nb = 0.0, 0
        for c in range(12):
            m = 30 * (c + 1)
            if np.isnan(e[s, c]):
                continue
            if regle == 3:
                if c != 4:
                    continue
                deja = False
                for k in range(5):
                    if pos[s, k] != 0:
                        deja = True
                if deja or abs(e[s, c]) < 0.5:
                    continue
            elif not (pos[s, c] == 0 and dedans[s, c] and abs(e[s, c]) >= 0.5):
                continue
            p = 1.0 if e[s, c] > 0 else -1.0
            x = min(m + 30, N - 1) if regle == 1 else 384
            if x <= m:
                continue
            tot += p * (C[s, x] - O[s, m + 1]) * pt * ech[s] - frais
            if nb == 0:
                cote[s], entree[s] = p, m + 1
            nb += 1
            if regle != 1:
                break
        if nb:
            g[s] = tot
    return g, cote, entree


def calcul(d):
    O, C = d["o"], d["c"]
    sigma, vwap, href, bref, jouable = zone_tableaux(d)
    pos, dedans, e, tr = _zone(O, C, sigma, vwap, href, bref, jouable)
    ech = float(d["pref"]) / O[:, 0]
    pt, frais = float(d["pt"]), float(d["frais"])
    out = {r: _regles(O, C, pos, dedans, e, ech, pt, frais, i + 1) for i, r in enumerate(REGLES)}
    return out, pos, dedans, e, tr


def controle_zone(d, tr):
    """Les trades recalcules doivent redonner ceux de la zone verifiee (delta_mesures/etude.py) sur la periode commune."""
    sys.path.insert(0, os.environ["DELTA_MESURES"])
    import etude as DM                                                            # noqa: E402
    rech = pd.read_csv(DM.RECHERCHE)
    z = DM.preparer(rech)
    fin = str(d["jours"][-1])
    ref = DM.trades_zone(z, "2011-01-01", fin)
    a = {(str(d["jours"][s]), int(me), int(sg), int(ms)) for s, me, sg, ms in tr}
    b = {(str(r.jour.date()), int(r.minute_entree), int(r.sens), int(r.minute_sortie)) for r in ref.itertuples()}
    return len(a), len(b), len(a & b)


def carte(d, pos, dedans, e):
    C = d["c"]
    j = d["jours"]
    L = ["Carte de l'elan (descriptif) : gain moyen des 30 minutes suivantes dans le sens de l'elan du jour, en points de "
         "base, avant frais ; etat de la zone apres sa decision au controle", "",
         "etat                                         periode       controles   moyenne (pb)     t"]
    for nom, f in (("zone en position, dans son sens", lambda p, dd, ee: (p != 0) & (np.sign(ee) == p)),
                   ("zone en position, contre son sens", lambda p, dd, ee: (p != 0) & (np.sign(ee) == -p)),
                   ("zone a plat, |e| < 0,5", lambda p, dd, ee: (p == 0) & (np.abs(ee) < 0.5)),
                   ("zone a plat, dans la bande, |e| >= 0,5", lambda p, dd, ee: (p == 0) & dd & (np.abs(ee) >= 0.5)),
                   ("zone a plat, hors de la bande", lambda p, dd, ee: (p == 0) & ~dd & np.isfinite(ee))):
        for per, msk in (("<= 2022", j <= E.FIN_EXPLO), (">= 2023", j > E.FIN_EXPLO)):
            x = []
            for c in range(12):
                m = 30 * (c + 1)
                sel = msk & np.isfinite(e[:, c]) & f(pos[:, c], dedans[:, c], e[:, c])
                fw = (C[sel, min(m + 30, 389)] / C[sel, m] - 1) * 1e4 * np.sign(e[sel, c])
                x.append(fw)
            x = np.concatenate(x)
            L.append(f"{nom:<44} {per:<10} {len(x):9d}   {x.mean() if len(x) else np.nan:10.2f}   "
                     f"{K.t_stat(x) if len(x) > 2 else np.nan:6.2f}")
    return L


_ETAT = {}


def jumeau(args):
    sorte, k = args
    d = _ETAT["d"]
    dj = B.bruiter(d, (7000 if sorte == "permutation" else 7500) + k, sorte=sorte)
    out = calcul(dj)[0]
    return sorte, {r: F.stats(out[r][0], d["jours"])["t"] for r in REGLES}


def main():
    d = E.jour_nq()
    out, pos, dedans, e, tr = calcul(d)
    na, nb, nab = controle_zone(d, tr)
    L = [f"Controle de la zone recalculee : {na} trades ; zone verifiee {nb} ; communs {nab} ({nab / max(nb, 1):.1%})"]
    if nab / max(nb, 1) < 0.98:
        print("\n".join(L))
        sys.exit("La zone recalculee ne redonne pas la zone verifiee : arret avant tout resultat.")
    L.append("")
    L += carte(d, pos, dedans, e)
    reel = {r: F.stats(out[r][0], d["jours"]) for r in REGLES}
    _ETAT["d"] = d
    with mp.get_context("fork").Pool(int(os.getenv("PROCESSUS", "2"))) as pool:
        bruits = pool.map(jumeau, [(s, k) for s in ("permutation", "signe") for k in range(1, JUMEAUX + 1)])
    # gain quotidien de la zone (memes conventions) pour la correlation
    ech = float(d["pref"]) / d["o"][:, 0]
    gz = np.zeros(len(d["jours"]))
    for s, me, sg, ms in tr:
        gz[s] += sg * (d["c"][s, ms] - d["c"][s, me]) * float(d["pt"]) * ech[s] - float(d["frais"])
    joue = np.zeros(len(d["jours"]), bool)
    joue[np.unique(tr[:, 0])] = True
    res = []
    for r in REGLES:
        v = reel[r]
        tb = np.array([b[r] for s, b in bruits if s == "permutation"], float)
        ts = np.array([b[r] for s, b in bruits if s == "signe"], float)
        bat = float(min(np.nanmean(v["t"] > tb), np.nanmean(v["t"] > ts)))
        deux = v["moy_explo"] > 0 and v["moy_controle"] > 0
        retenue = bool(v["t"] >= SEUIL_RETENUE and deux and bat >= 0.95)
        inter = bool(not retenue and v["t"] >= 1.65 and deux and bat >= 0.90)
        g = np.nan_to_num(out[r][0])
        m = np.isfinite(e[:, 0])
        corr = float(np.corrcoef(g[m], gz[m])[0, 1])
        res.append(dict(regle=r, nom=NOMS[r], **v, bruit_95=float(np.nanquantile(tb, 0.95)),
                        signe_95=float(np.nanquantile(ts, 0.95)), bat_bruit=bat, corr_zone=corr, retenue=retenue,
                        interessante=inter))
    zone_stats = F.stats(np.where(joue, gz, np.nan), d["jours"])
    L += ["", f"Zone sans filtre, memes conventions (seances ou elle trade) : t {zone_stats['t']:.2f}, "
              f"{zone_stats['net']:+.2f} $ par seance ; <= 2022 t {zone_stats['t_explo']:.2f}, >= 2023 t "
              f"{zone_stats['t_controle']:.2f}", "",
          f"Regles (retenue : t >= {SEUIL_RETENUE:.2f}, positive avant et apres 2023, au-dessus de 95 % des jumeaux ; "
          "interessante : t >= 1,65, positive sur les deux periodes, au-dessus de 90 %)",
          "regle  nom                                                  seances    t   net/seance  t <=2022 (moy.)       "
          "t >=2023 (moy.)     corr. zone  bat le bruit  verdict"]
    for x in res:
        verdict = "RETENUE" if x["retenue"] else ("interessante" if x["interessante"] else "non")
        L.append(f"{x['regle']:<5}  {x['nom']:<52} {x['trades']:6d} {x['t']:6.2f} {x['net']:8.2f} $  {x['t_explo']:6.2f} "
                 f"({x['moy_explo']:+7.2f} $)  {x['t_controle']:6.2f} ({x['moy_controle']:+7.2f} $)   {x['corr_zone']:+.2f}"
                 f"        {x['bat_bruit']:5.0%}      {verdict}")
    SORTIE.mkdir(parents=True, exist_ok=True)
    (SORTIE / "partie_g.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    txt = "\n".join(L)
    (SORTIE / "partie_g.txt").write_text(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
