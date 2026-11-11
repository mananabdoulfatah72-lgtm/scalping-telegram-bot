"""Partie C : la machine auto-evolutive (SETS), construite comme le message la decrit, puis jugee. Regles : REGLES.md.

Usage : python3 machine.py [nq|btc]   (ecrit resultats/machine_<marche>.txt et .json)
"""
import glob
import json
import sys
import time

import numba as nb
import numpy as np
import pandas as pd

import donnees as D

ESPECES = ("élan", "retour à la moyenne", "cassure de volatilité", "grille de fourchette")
BORNES = np.array([[0, 3], [6, 78], [0.5, 3.0], [1, 6], [0.25, 2.0], [1.0, 2.0], [0.25, 4.0], [0.5, 6.0]])   # 8 genes
ENTIER = np.array([True, True, False, True, False, False, False, False])
POP, GEN, NOUV, GARDE = 96, 40, 8, 8
QMIN, QMAX = 12, 48
CAPITAL = 50000.0


# ------------------------------------------------------------------ donnees
def barres_nq():
    """NQ en barres de 5 minutes : O H L C (seances completes x 78), dates."""
    M = D.nq_minutes(); ok = M["ok"]
    O = M["O"][ok][:, ::5]; C = M["C"][ok][:, 4::5]
    H = M["H"][ok].reshape(-1, 78, 5).max(2); L = M["L"][ok].reshape(-1, 78, 5).min(2)
    return M["J"][ok], O, H, L, C


def barres_btc():
    """Bitcoin en 5 minutes, journees UTC de 288 barres completes."""
    d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(D.AT / "donnees_libres/crypto/btc_*_5m.csv.gz")))])
    col = {c.lower()[0]: c for c in d.columns}
    t = pd.to_datetime(d[col["t"]]); jour = t.dt.strftime("%Y-%m-%d").to_numpy(); b = (t.dt.hour * 12 + t.dt.minute // 5).to_numpy()
    J = np.unique(jour); s = np.searchsorted(J, jour)
    A = {k: np.full((len(J), 288), np.nan) for k in "ohlc"}
    for k in "ohlc":
        A[k][s, b] = d[col[k]].to_numpy(float)
    ok = np.isfinite(A["c"]).all(1)
    return J[ok], A["o"][ok], A["h"][ok], A["l"][ok], A["c"][ok]


def unite(O, C):
    """sig : ecart type des rendements de 5 minutes des 20 seances d'avant ; u = prix x sig x racine(6)."""
    r = np.diff(np.log(np.c_[O[:, :1], C]), axis=1)
    v = (r ** 2).mean(1); S = len(v); sig = np.full(S, np.nan)
    cs = np.r_[0, np.cumsum(v)]
    sig[20:] = np.sqrt((cs[20:-1] - cs[:-21]) / 20)
    return sig


def faux_marche(O, H, L, C, sorte, rng):
    """Jumeau de bruit. 'permutation' : chaque barre (meme heure) vient d'une seance tiree au hasard, les ecarts de nuit
    sont permutes. 'signe' : chaque barre et chaque ecart de nuit est retourne (miroir) une fois sur deux."""
    S, B = C.shape
    rc = np.log(C / O); rh = np.log(H / O); rl = np.log(L / O)
    ro = np.zeros((S, B)); ro[:, 1:] = np.log(O[:, 1:] / C[:, :-1]); ro[1:, 0] = np.log(O[1:, 0] / C[:-1, -1])
    if sorte == "permutation":
        for b in range(B):
            p = rng.permutation(S)
            rc[:, b] = rc[p, b]; rh[:, b] = rh[p, b]; rl[:, b] = rl[p, b]; ro[:, b] = ro[p, b] if b else ro[rng.permutation(S), 0]
    else:
        f = rng.random((S, B)) < 0.5
        rc = np.where(f, -rc, rc); rh2 = np.where(f, -rl, rh); rl = np.where(f, -rh, rl); rh = rh2
        ro = np.where(rng.random((S, B)) < 0.5, -ro, ro)
    # log de l'ouverture de chaque barre : ouverture precedente + rendement de la barre precedente + ecart
    lo = np.empty((S, B)); x = np.log(O[0, 0])
    for s in range(S):
        for b in range(B):
            x += ro[s, b] if (s or b) else 0.0
            lo[s, b] = x; x += rc[s, b]
    o = np.exp(lo)
    return o, o * np.exp(rh), o * np.exp(rl), o * np.exp(rc)


# ------------------------------------------------------------------ moteur
@nb.njit(cache=True)
def jouer(g, O, H, L, C, sig, s0, s1, mult, pref, frais_pct, frais_fixe, tick_pct, arrondi, dernier, tenue_max):
    """Joue un genome sur les seances s0..s1-1. Renvoie le gain par seance, le creux par seance (latent compris),
    et (cycles, gagnants). Une position a la fois ; grille comptee depuis le prix moyen ; perte avant gain dans une barre."""
    esp = int(g[0]); Lb = int(g[1]); seuil = g[2]; niveaux = int(g[3]); esp_u = g[4]; mul = g[5]; tp_u = g[6]; st_u = g[7]
    S, B = C.shape; n = s1 - s0
    gain = np.zeros(n); creux = np.zeros(n); cycles = 0; gagnants = 0
    oc = O.ravel(); hc = H.ravel(); lc = L.ravel(); cc = C.ravel()
    for s in range(max(s0, 21), s1):
        if not np.isfinite(sig[s]) or sig[s] <= 0:
            continue
        u = O[s, 0] * sig[s] * 2.449489742783178
        real = 0.0; bas = 0.0
        d = 0; k = 0; q = 0.0; moy = 0.0; dern = 0.0; e0 = 0.0; deb = 0; cout = 0.0
        for b in range(B):
            i = s * B + b
            # ---- signal a la cloture de la barre precedente, entree a l'ouverture de celle-ci
            if d == 0 and 1 <= b <= dernier and i - 1 - Lb >= 0:
                j = i - 1; sens = 0
                if esp <= 1:
                    z = np.log(cc[j] / cc[j - Lb]) / (sig[s] * np.sqrt(Lb))
                    if z >= seuil: sens = 1
                    elif z <= -seuil: sens = -1
                    if esp == 1: sens = -sens
                elif esp == 2:
                    hh = -1e18; ll = 1e18; am = 0.0
                    for x in range(j - Lb, j):
                        if hc[x] > hh: hh = hc[x]
                        if lc[x] < ll: ll = lc[x]
                        am += hc[x] - lc[x]
                    am /= Lb
                    if hc[j] - lc[j] >= seuil * am:
                        if cc[j] > hh: sens = 1
                        elif cc[j] < ll: sens = -1
                else:
                    m1 = 0.0; m2 = 0.0
                    for x in range(j - Lb + 1, j + 1):
                        m1 += cc[x]; m2 += cc[x] * cc[x]
                    m1 /= Lb; v = m2 / Lb - m1 * m1
                    if v > 0:
                        z = (cc[j] - m1) / np.sqrt(v)
                        if z <= -seuil: sens = 1
                        elif z >= seuil: sens = -1
                if sens != 0:
                    d = sens; k = 1; q = 1.0; moy = oc[i]; dern = oc[i]; e0 = oc[i]; deb = b
                    cout = frais_fixe + frais_pct * mult * pref
            if d == 0:
                continue
            ech = mult * pref / e0
            tick = tick_pct * e0
            # ---- sortie forcee : derniere barre de la seance, ou tenue maximale
            if b == B - 1 or (tenue_max > 0 and b - deb >= tenue_max):
                pnl = d * (oc[i] - moy) * q * ech - cout
                real += pnl; cycles += 1; gagnants += pnl > 0
                if real < bas: bas = real
                d = 0
                continue
            ajoute = False; sorti = False
            # ---- cote defavorable : niveaux de grille puis stop
            while True:
                pire = lc[i] if d > 0 else hc[i]
                stop = moy - d * st_u * u
                if k < niveaux:
                    niv = dern - d * esp_u * u
                    avant = (niv > stop) if d > 0 else (niv < stop)
                    touche = (pire < niv) if d > 0 else (pire > niv)
                    if avant and touche:
                        px = niv
                        if (d > 0 and oc[i] < niv) or (d < 0 and oc[i] > niv):
                            px = oc[i]
                        t = mul ** k
                        if arrondi:
                            t = max(1.0, np.floor(t + 0.5))
                        moy = (moy * q + px * t) / (q + t); q += t; dern = px; k += 1; ajoute = True
                        cout += (frais_fixe + frais_pct * mult * pref) * t
                        continue
                touche_stop = (pire <= stop) if d > 0 else (pire >= stop)
                if touche_stop:
                    px = stop - d * tick
                    if (d > 0 and oc[i] < stop) or (d < 0 and oc[i] > stop):
                        px = oc[i]
                    pnl = d * (px - moy) * q * ech - cout
                    real += pnl; cycles += 1; gagnants += pnl > 0; sorti = True
                break
            if sorti:
                if real < bas: bas = real
                d = 0
                continue
            lat = real + d * ((lc[i] if d > 0 else hc[i]) - moy) * q * ech - cout
            if lat < bas: bas = lat
            # ---- cote favorable : prise de profit (jamais dans une barre ou un niveau vient d'etre rempli)
            if not ajoute:
                obj = moy + d * tp_u * u
                if (d > 0 and hc[i] >= obj + tick) or (d < 0 and lc[i] <= obj - tick):
                    pnl = d * (obj - moy) * q * ech - cout
                    real += pnl; cycles += 1; gagnants += pnl > 0
                    d = 0
        gain[s - s0] = real; creux[s - s0] = bas
    return gain, creux, cycles, gagnants


def score(gain):
    c = np.cumsum(gain); dd = float((np.maximum.accumulate(np.r_[0, c]) - np.r_[0, c]).max())
    return float(gain.sum()), dd


# ------------------------------------------------------------------ evolution
def hasard(rng, esp=None):
    g = BORNES[:, 0] + rng.random(8) * (BORNES[:, 1] - BORNES[:, 0])
    g[ENTIER] = np.floor(BORNES[ENTIER, 0] + rng.random(ENTIER.sum()) * (BORNES[ENTIER, 1] - BORNES[ENTIER, 0] + 1))
    if esp is not None:
        g[0] = esp
    return np.clip(g, BORNES[:, 0], BORNES[:, 1])


def enfant(rng, a, b):
    g = np.where(rng.random(8) < 0.5, a, b); g[0] = a[0]
    for k in range(1, 8):
        if rng.random() < 0.2:
            g[k] += rng.normal(0, 0.1 * (BORNES[k, 1] - BORNES[k, 0]))
            if ENTIER[k]:
                g[k] = np.round(g[k])
    return np.clip(g, BORNES[:, 0], BORNES[:, 1])


class Marche:
    def __init__(self, nom, J, O, H, L, C, hist, ctrl, mult, pref, frais_pct, frais_fixe, tick_pct, dernier, tenue_max):
        self.nom, self.J = nom, J
        self.P = (O, H, L, C)
        self.sig = unite(O, C)
        self.h0, self.h1 = int(np.searchsorted(J, hist[0])), int(np.searchsorted(J, hist[1]))      # histoire de la machine
        self.c0, self.c1 = int(np.searchsorted(J, ctrl[0])), len(J)                                 # controle
        self.coupe = self.h0 + int(0.7 * (self.h1 - self.h0))
        self.k = (mult, pref, frais_pct, frais_fixe, tick_pct)
        self.dernier, self.tenue = dernier, tenue_max

    def jouer(self, g, s0, s1, P=None, sig=None, arrondi=False):
        O, H, L, C = P or self.P
        return jouer(np.asarray(g, float), O, H, L, C, self.sig if sig is None else sig, s0, s1, *self.k, arrondi, self.dernier, self.tenue)


def machine(Mk, graine, P=None, sig=None):
    """Une evolution complete. Renvoie les genomes vivants de la derniere generation (elite) avec leur score de test."""
    rng = np.random.default_rng(graine)
    pop = [hasard(rng, e % 4) for e in range(POP)]
    vus = {}

    def evaluer(g):
        cle = tuple(np.round(g, 4))
        if cle not in vus:
            ga, _, cy, _ = Mk.jouer(g, Mk.h0, Mk.coupe, P, sig)
            net, dd = score(ga)
            sc = net / dd if (cy >= 100 and dd > 0) else -1e9
            gt, _, cyt, wt = Mk.jouer(g, Mk.coupe, Mk.h1, P, sig)
            nt, ddt = score(gt)
            vivant = nt > 0 and ddt <= 0.10 * CAPITAL and cyt > 0 and wt / cyt >= 0.5
            vus[cle] = (sc, vivant, nt / ddt if ddt > 0 else 0.0, nt, ddt, cyt, wt / max(cyt, 1))
        return vus[cle]

    histo = []
    for gen in range(GEN + 1):
        ev = [evaluer(g) for g in pop]
        viv = [i for i in range(POP) if ev[i][1]]
        histo.append(len(viv))
        if gen == GEN:
            break
        ordre = sorted(viv or range(POP), key=lambda i: -ev[i][0])
        suite = [pop[i].copy() for i in ordre[:GARDE]]
        suite += [hasard(rng, e % 4) for e in range(NOUV)]
        # parents : les 6 meilleurs de chaque espece (vivants d'abord)
        parents = {}
        for e in range(4):
            c = [i for i in ordre if int(pop[i][0]) == e][:6]
            if len(c) < 2:
                c = sorted([i for i in range(POP) if int(pop[i][0]) == e], key=lambda i: -ev[i][0])[:6]
            parents[e] = c
        force = np.array([sum(1 for i in ordre[:24] if int(pop[i][0]) == e) for e in range(4)], float) + 1e-9
        deja = np.array([sum(1 for g in suite if int(g[0]) == e) for e in range(4)])
        cible = np.clip(np.round(force / force.sum() * POP), QMIN, QMAX)
        while cible.sum() != POP:                                          # quotas : chaque espece entre 12 et 48 places
            e = int(np.argmax(cible)) if cible.sum() > POP else int(np.argmin(cible))
            cible[e] += -1 if cible.sum() > POP else 1
        for e in range(4):
            for _ in range(int(max(0, cible[e] - deja[e]))):
                if len(parents[e]) >= 2:
                    a, b = rng.choice(parents[e], 2, replace=False)
                    suite.append(enfant(rng, pop[a], pop[b]))
                else:
                    suite.append(hasard(rng, e))
        pop = suite[:POP]
        while len(pop) < POP:
            pop.append(hasard(rng))
    elite = {}
    for g, e in zip(pop, ev):
        if e[1]:
            elite[tuple(np.round(g, 4))] = e
    return [(np.array(k), v) for k, v in elite.items()], histo, len(vus)


# ------------------------------------------------------------------ jugement
def compte_bulenox(gain, creux, plancher=2500.0, dll=1100.0, horizon=60, pas=20):
    """Part des comptes neufs perdus en `horizon` seances (plancher suiveur de fin de journee, arrete au solde de depart,
    controle en temps reel ; limite du jour : la journee est coupee a -dll)."""
    g = np.where(creux <= -dll, -dll - 4.0, gain); c = np.maximum(creux, -dll - 4.0)
    perdus = 0; n = 0
    for i0 in range(0, len(g) - horizon + 1, pas):
        solde = haut = 0.0; mort = False
        for i in range(i0, i0 + horizon):
            pl = min(haut - plancher, 0.0)
            if solde + c[i] <= pl:
                mort = True; break
            solde += g[i]; haut = max(haut, solde)
        perdus += mort; n += 1
    return perdus / max(n, 1)


def juger(Mk, elite):
    out = []
    for g, e in elite:
        ga, _, cy, w = Mk.jouer(g, Mk.c0, Mk.c1)
        gr, cr, _, _ = Mk.jouer(g, Mk.c0, Mk.c1, arrondi=True)
        out.append(dict(g=[float(x) for x in g], test=e[2], net=float(ga.sum()), t=D.tstat(ga), cycles=int(cy), gagnants=w / max(cy, 1),
                        pire_jour=float(gr.min()), grille=compte_bulenox(gr, cr)))
    return out


def principal(nom):
    t0 = time.time()
    if nom == "nq":
        J, O, H, L, C = barres_nq()
        Mk = Marche("NQ, 5 minutes, séance", J, O, H, L, C, ("2017-01-01", "2023-01-01"), ("2023-01-01",), 2.0, D.PREF, 0.0, D.FRAIS, D.TICK / D.PREF, 71, 0)
    else:
        J, O, H, L, C = barres_btc()
        Mk = Marche("bitcoin, 5 minutes, 24 h", J, O, H, L, C, ("2019-01-01", "2023-01-01"), ("2023-01-01",), 1.0, 50000.0, 0.0004, 0.0, 0.0001, 286, 0)
    lignes = [f"Partie C : la machine auto-évolutive sur {Mk.nom}.",
              f"Histoire de la machine : {J[Mk.h0]} → {J[Mk.h1 - 1]} (entraînement jusqu'au {J[Mk.coupe - 1]}, test ensuite). Contrôle jamais vu : {J[Mk.c0]} → {J[-1]}.",
              f"{POP} stratégies par génération, {GEN} générations, 6 graines par sorte de marché.", ""]
    res = {}
    O_, H_, L_, C_ = (x[Mk.h0 - 21:Mk.h1] for x in Mk.P)                   # 21 seances d'avance pour l'unite de volatilite
    for sorte in ("vrai", "permutation", "signe"):
        res[sorte] = []
        for graine in range(1, 7):
            if sorte == "vrai":
                elite, histo, nvus = machine(Mk, graine)
            else:
                rng = np.random.default_rng(1000 * (1 + ("signe" == sorte)) + graine)
                Pf = faux_marche(O_, H_, L_, C_, sorte, rng)
                Mf = Marche("faux", J[Mk.h0 - 21:Mk.h1], *Pf, (J[Mk.h0], "9999"), ("9999",), *Mk.k, Mk.dernier, Mk.tenue)
                Mf.h0, Mf.h1 = 21, len(Pf[0]); Mf.coupe = Mk.coupe - Mk.h0 + 21
                elite, histo, nvus = machine(Mf, graine)
            jug = juger(Mk, elite)                                           # toujours sur les VRAIES donnees de controle
            champ = max(jug, key=lambda x: x["test"]) if jug else None
            r = dict(graine=graine, elite=len(jug), essais=nvus, vivants_par_generation=histo,
                     gain=float(np.mean([x["net"] > 0 for x in jug])) if jug else 0.0,
                     t165=float(np.mean([x["t"] >= 1.65 for x in jug])) if jug else 0.0,
                     grille=float(np.mean([x["grille"] for x in jug])) if jug else None,
                     especes=[int(sum(int(x["g"][0]) == e for x in jug)) for e in range(4)],
                     gagnants_test=float(np.mean([x["gagnants"] for x in jug])) if jug else None, champion=champ)
            res[sorte].append(r)
            c = champ
            lignes.append(f"{sorte:<12} graine {graine} : {nvus:>4} stratégies essayées, élite {len(jug):>3} "
                          f"(élan {r['especes'][0]}, retour {r['especes'][1]}, cassure {r['especes'][2]}, grille {r['especes'][3]}) | au contrôle : "
                          f"{r['gain']:.0%} en gain, {r['t165']:.0%} à t ≥ 1,65"
                          + (f", comptes Bulenox perdus en 60 séances {r['grille']:.0%} | champion : {c['net']:+,.0f} $, t {c['t']:+.2f}, {c['gagnants']:.0%} de gagnants, "
                             f"pire jour {c['pire_jour']:,.0f} $, comptes perdus {c['grille']:.0%}".replace(",", " ") if c else " | pas de champion"))
            print(lignes[-1], f"({time.time() - t0:.0f}s)", flush=True)
    vr = res["vrai"]; br = res["permutation"] + res["signe"]
    part_v = float(np.mean([r["t165"] for r in vr])); max_b = max(r["t165"] for r in br)
    bons = sum(1 for r in vr if r["champion"] and r["champion"]["net"] > 0 and r["champion"]["t"] >= 1.65)
    trouve = all(r["t165"] > max_b for r in vr) and bons >= 4
    tot = lambda rs: sum(r["elite"] for r in rs)
    pond = lambda rs, k: sum(r[k] * r["elite"] for r in rs) / max(tot(rs), 1)
    lignes += ["", f"Vraies données : {tot(vr)} élites, {pond(vr, 'gain'):.0%} en gain au contrôle, {pond(vr, 't165'):.0%} à t ≥ 1,65.",
               f"Faux marchés (placebos) : {tot(br)} élites, {pond(br, 'gain'):.0%} en gain au contrôle, {pond(br, 't165'):.0%} à t ≥ 1,65 ; "
               f"la meilleure machine de bruit monte à {max_b:.0%}.",
               f"Champions réels avec gain positif et t ≥ 1,65 au contrôle : {bons} sur 6.",
               f"Verdict fixé d'avance : {'la machine trouve quelque chose' if trouve else 'TUÉE : la machine ne fait pas mieux que le hasard'}."]
    res["verdict"] = dict(trouve=bool(trouve), part_reelle=part_v, max_bruit=max_b, champions_bons=bons)
    (D.ICI / f"resultats/machine_{nom}.txt").write_text("\n".join(lignes) + "\n")
    json.dump(res, open(D.ICI / f"resultats/machine_{nom}.json", "w"), indent=1, ensure_ascii=False)
    print("\n".join(lignes[-5:]))


if __name__ == "__main__":
    principal(sys.argv[1] if len(sys.argv) > 1 else "nq")
