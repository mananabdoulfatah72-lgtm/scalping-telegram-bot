#!/usr/bin/env python3
"""Partie I (README.md) : la zone seule ou avec un ajout (H12 Supertrend, H1 ORB 5 min, H5 cassure de la veille, F3
pivots) dans le challenge Bulenox 50K, minute par minute, departs a chaque seance de 2012 a 2026. Temoins : zone plus
grosse, ajout sans avantage (Supertrend au sens tire a pile ou face chaque jour). Ecrit resultats/i/challenge_ajouts.txt.
Lancer : KB=<branche de recherche extraite> python3 scalping/challenge_ajouts.py"""
import sys

import numpy as np
from numba import njit

import commun as K
import partie_e as E
import partie_f as F
import partie_g as G
import partie_h as H

SORTIE = K.ICI / "resultats" / "i"


# ----------------------------------------------------------------------------------------------- trades
def trades_supertrend(d, ind, ok):
    """Memes decisions que partie_h._barres (regle 12). (seance, minute d'entree, sens, prix, minute de sortie, prix,
    type de sortie : 0 a l'ouverture, 1 dans la minute (stop), 2 a la cloture)."""
    O, C = d["o"], d["c"]
    st = ind[7]
    out = []
    for s in np.flatnonzero(ok):
        pos, px, me = 0.0, 0.0, -1
        for b in range(76):
            i = s * 78 + b
            cible = st[i] if st[i] != 0 else pos
            m = 5 * b + 5
            if cible != pos and pos != 0:
                out.append((s, me, pos, px, m, O[s, m], 0))
                pos = 0.0
            if cible != 0 and pos == 0 and m <= 360:
                pos, px, me = cible, O[s, m], m
        if pos != 0:
            out.append((s, me, pos, px, 384, C[s, 384], 2))
    return out


def _sortie(d, s, m0, p, stop, obj, tick):
    """Comme partie_h._gerer, avec la minute et le type de sortie."""
    O, Hh, L, C = d["o"], d["h"], d["l"], d["c"]
    for m in range(m0, 385):
        if not np.isnan(stop):
            if p > 0 and L[s, m] <= stop:
                return m, min(O[s, m], stop), 1
            if p < 0 and Hh[s, m] >= stop:
                return m, max(O[s, m], stop), 1
        if not np.isnan(obj):
            if p > 0 and (O[s, m] > obj or Hh[s, m] >= obj + tick):
                return m, (max(O[s, m], obj) if O[s, m] > obj else obj), 3
            if p < 0 and (O[s, m] < obj or L[s, m] <= obj - tick):
                return m, (min(O[s, m], obj) if O[s, m] < obj else obj), 3
    return 384, C[s, 384], 2


def trades_seances(d, ok, regle):
    """H1 (ORB 5), H5 (cassure de la veille), F3 (pivots) : memes decisions que partie_h._seances et partie_f._cassure."""
    O, Hh, L, C = d["o"], d["h"], d["l"], d["c"]
    prec = d["prec_meme"]
    tick = float(d["tick"])
    out = []
    for s in np.flatnonzero(ok):
        p1 = prec[s]
        if regle == "H1":
            if C[s, 4] == O[s, 0]:
                continue
            p = 1.0 if C[s, 4] > O[s, 0] else -1.0
            stop = L[s, 0:5].min() if p > 0 else Hh[s, 0:5].max()
            risque = abs(O[s, 5] - stop)
            obj = O[s, 5] + p * 10 * risque if risque > 0 else np.nan
            m0 = 5
        else:
            if p1 < 0:
                continue
            hp, lp, cp = Hh[p1].max(), L[p1].min(), C[p1, -1]
            if regle == "H5":
                hi, lo, stop, fin = hp, lp, O[s, 0], 360
            else:
                piv = (hp + lp + cp) / 3
                hi, lo, stop, fin = 2 * piv - lp, 2 * piv - hp, np.nan, 330
                if O[s, 0] >= hi or O[s, 0] <= lo:
                    continue
            p, m0 = 0.0, -1
            for m in range(0, fin):
                if C[s, m] > hi:
                    p, m0 = 1.0, m + 1
                    break
                if C[s, m] < lo:
                    p, m0 = -1.0, m + 1
                    break
            if p == 0:
                continue
            obj = np.nan
        mx, xp, typ = _sortie(d, s, m0, p, stop if regle != "F3" else np.nan, obj, tick)
        if regle == "F3":
            mx, xp, typ = 384, C[s, 384], 2
        out.append((s, m0, p, O[s, m0], mx, xp, typ))
    return out


def trades_zone(d, tr):
    C = d["c"]
    return [(s, me, float(sg), C[s, me], ms, C[s, ms], 4) for s, me, sg, ms in tr]   # 4 : entree a la cloture de me


def chemins(d, trades):
    """Gain de la seance (1 MNQ, au prix d'aujourd'hui, frais deduits a la sortie) a la cloture de chaque minute, et au pire
    de chaque minute (plus bas pour un achat, plus haut pour une vente)."""
    O, Hh, L, C = d["o"], d["h"], d["l"], d["c"]
    S, N = C.shape
    pt, frais = float(d["pt"]), float(d["frais"])
    ech = float(d["pref"]) / O[:, 0]
    clo, pire = np.zeros((S, N)), np.zeros((S, N))
    for s, me, p, px, mx, xp, typ in trades:
        e = pt * ech[s]
        k0 = me + 1 if typ == 4 else me
        k1 = mx if typ == 0 else mx                      # minutes ouvertes : [k0, k1)
        if k1 > k0:
            ks = np.arange(k0, k1)
            adv = L[s, ks] if p > 0 else Hh[s, ks]
            clo[s, ks] += p * (C[s, ks] - px) * e
            pire[s, ks] += p * (adv - px) * e
        real = p * (xp - px) * e - frais
        adv_x = (L[s, mx] if p > 0 else Hh[s, mx])
        clo[s, mx:] += real
        if typ == 1 or typ == 0:
            pire[s, mx:] += real
        else:
            pire[s, mx] += min(real, p * (adv_x - px) * e - frais)
            pire[s, mx + 1:] += real
    return clo, pire


def verifier(trades, g, d):
    pt, frais = float(d["pt"]), float(d["frais"])
    ech = float(d["pref"]) / d["o"][:, 0]
    tot = np.zeros(len(g))
    vu = np.zeros(len(g), bool)
    for s, me, p, px, mx, xp, typ in trades:
        tot[s] += p * (xp - px) * pt * ech[s] - frais
        vu[s] = True
    ref = np.nan_to_num(g)
    return bool(np.array_equal(vu, np.isfinite(g)) and np.allclose(tot, ref, atol=1e-6))


# ----------------------------------------------------------------------------------------------- challenge
@njit(cache=True)
def _challenge(Zc, Zw, Ac, Aw, fed, jours, departs, z1, z2, a, signe):
    """Resultat de chaque depart : 1 valide, -1 perdu, 0 expire. signe[s] multiplie l'ajout (temoin sans avantage : les
    chemins Ac et Aw sont alors ceux du sens tire)."""
    S, N = Zc.shape
    res = np.zeros(len(departs), np.int64)
    for k in range(len(departs)):
        d0 = departs[k]
        fin = jours[d0] + 30
        d1 = d0
        while d1 < S and jours[d1] < fin:
            d1 += 1
        bal, haut = 50000.0, 50000.0
        plancher = 47500.0
        etat = 0
        for s in range(d0, d1):
            z = z2 if s >= d1 - 5 else z1
            if fed[s]:
                z = 0.0
            jour = 0.0
            fini = False
            for m in range(N):
                pire = z * Zw[s, m] + a * Aw[s, m]
                clo = z * Zc[s, m] + a * Ac[s, m]
                if bal + pire <= plancher:
                    etat = -1
                    fini = True
                    break
                if pire <= -1000.0:
                    jour = -1000.0
                    break
                if bal + clo >= 53050.0:
                    etat = 1
                    fini = True
                    break
                jour = clo
            if fini:
                break
            bal += jour
            haut = max(haut, bal)
            plancher = 50100.0 if haut >= 52600.0 else haut - 2500.0
            if bal <= plancher:
                etat = -1
                break
        res[k] = etat
    return res


def main():
    d = E.jour_nq()
    O, Hh, L, C = d["o"], d["h"], d["l"], d["c"]
    S = C.shape[0]
    ok = d["complete"] & ~d["ech"]
    out_h = H.toutes(d)
    out_f = F.toutes(d)
    h5 = Hh.reshape(S, 78, 5).max(axis=2).reshape(-1)
    l5 = L.reshape(S, 78, 5).min(axis=2).reshape(-1)
    c5 = C[:, 4::5].reshape(-1)
    ind = H._indicateurs(h5, l5, c5)
    tz = trades_zone(d, G.calcul(d)[4])
    tt = {"H12": trades_supertrend(d, ind, ok), "H1": trades_seances(d, ok, "H1"), "H5": trades_seances(d, ok, "H5"),
          "F3": trades_seances(d, ok, "F3")}
    L_ = ["Partie I : challenge Bulenox 50K, zone sans filtre 4 puis 6 MNQ, pas de zone les jours de la Fed, departs a "
          "chaque seance ; valide / perdu / expire (30 jours)", ""]
    ref = {"H12": out_h["H12"][0], "H1": out_h["H1"][0], "H5": out_h["H5"][0], "F3": out_f["F3"][0]}
    for r, t in tt.items():
        okv = verifier(t, ref[r], d)
        L_.append(f"Controle : trades {r} rejoues = gains du banc : {'oui' if okv else 'NON'}")
        if not okv:
            print("\n".join(L_))
            sys.exit(f"{r} : les trades rejoues ne redonnent pas le banc")
    Zc, Zw = chemins(d, tz)
    ch = {r: chemins(d, t) for r, t in tt.items()}
    neg = [(s, me, -p, px, mx, xp, typ) for s, me, p, px, mx, xp, typ in tt["H12"]]
    Nc, Nw = chemins(d, neg)
    fed = np.isin(d["jours"], E.fomc())
    jours = d["jours"].astype("int64")
    fin_dep = d["jours"][-1] - np.timedelta64(30, "D")
    departs_tous = np.flatnonzero((d["jours"] >= np.datetime64("2012-01-01")) & (d["jours"] <= fin_dep))
    departs_23 = departs_tous[d["jours"][departs_tous] >= np.datetime64("2023-01-01")]
    un = np.ones(S)

    def taux(Ac, Aw, a, z1=4.0, z2=6.0):
        out = []
        for dep in (departs_tous, departs_23):
            r = _challenge(Zc, Zw, Ac, Aw, fed, jours, dep, z1, z2, a, un)
            out.append(((r == 1).mean(), (r == -1).mean(), (r == 0).mean()))
        return out

    def ligne(nom, t):
        return (f"{nom:<46} {t[0][0]:7.1%} {t[0][1]:7.1%} {t[0][2]:7.1%}    {t[1][0]:7.1%} {t[1][1]:7.1%} {t[1][2]:7.1%}")

    L_ += ["", f"departs : {len(departs_tous)} (2012 - 2026), dont {len(departs_23)} en 2023 - 2026", "",
           f"{'configuration':<46} {'2012-2026 : valide  perdu  expire':<34} {'2023-2026 : valide  perdu  expire'}"]
    zero = np.zeros_like(Zc)
    base = taux(zero, zero, 0.0)
    L_.append(ligne("zone seule (4 puis 6 MNQ)", base))
    res = {"zone": base}
    for z1, z2 in ((5.0, 7.0), (6.0, 8.0)):
        t = taux(zero, zero, 0.0, z1, z2)
        res[f"zone {int(z1)}/{int(z2)}"] = t
        L_.append(ligne(f"temoin : zone seule {int(z1)} puis {int(z2)} MNQ", t))
    for r in ("H12", "H1", "H5", "F3"):
        for a in (2.0, 4.0):
            t = taux(ch[r][0], ch[r][1], a)
            res[f"{r} {int(a)}"] = t
            L_.append(ligne(f"zone + {r} a {int(a)} MNQ", t))
    tous_c = sum(ch[r][0] for r in ch)
    tous_w = sum(ch[r][1] for r in ch)
    t = taux(tous_c, tous_w, 1.0)
    res["tous 1"] = t
    L_.append(ligne("zone + les quatre a 1 MNQ chacun", t))
    rng = np.random.default_rng(21)
    for a in (2.0, 4.0):
        acc = []
        for _ in range(20):
            sg = rng.choice([-1.0, 1.0], size=S)
            Ac = np.where(sg[:, None] > 0, ch["H12"][0], Nc)
            Aw = np.where(sg[:, None] > 0, ch["H12"][1], Nw)
            acc.append(taux(Ac, Aw, a))
        t = [tuple(np.mean([x[p][i] for x in acc]) for i in range(3)) for p in range(2)]
        res[f"temoin {int(a)}"] = t
        L_.append(ligne(f"temoin : Supertrend au sens tire au sort, {int(a)} MNQ", t))
    L_ += ["", "Decision (README.md, partie I) :"]
    for r in ("H12", "H1", "H5", "F3"):
        for a in (2, 4):
            t = res[f"{r} {a}"]
            c1 = t[0][0] - base[0][0] >= 0.03 and t[1][0] - base[1][0] >= 0.03
            c2 = all(t[0][0] - res[x][0][0] >= 0.03 for x in (f"temoin {a}", "zone 5/7", "zone 6/8"))
            c3 = (t[0][1] - base[0][1]) <= (t[0][0] - base[0][0])
            L_.append(f"  {r} a {a} MNQ : +3 points sur les deux periodes {'oui' if c1 else 'non'} ; mieux que les temoins "
                      f"{'oui' if c2 else 'non'} ; pertes {'oui' if c3 else 'non'} -> {'ADOPTE' if c1 and c2 and c3 else 'non adopte'}")
    SORTIE.mkdir(parents=True, exist_ok=True)
    (SORTIE / "challenge_ajouts.txt").write_text("\n".join(L_) + "\n")
    print("\n".join(L_))


if __name__ == "__main__":
    main()
