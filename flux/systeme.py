#!/usr/bin/env python3
"""Systeme order flow (flux/README.md, regles fixees le 29 octobre 2026 avant tout calcul) : S1 repli absorbe dans le
sens du flux, S2 cassure ratee (acheteurs ou vendeurs pieges), S3 volume d'arret a l'extreme (footprint).

Lancer : KB=<copie de claude/keen-babbage-r686cl> python3 flux/systeme.py  ->  flux/resultats/systeme.txt"""
from pathlib import Path

import numpy as np
import pandas as pd

import donnees as D

ICI = Path(__file__).resolve().parent
TICK, COM, GLISSE = 0.25, 0.5, 0.25           # points de NQ ; 1 $ par ordre MNQ = 0,5 point ; 1 tick de glissement
DEBUT, FIN, DUREE = 30, 330, 30               # signaux de 10 h a 15 h (minutes depuis 9 h 30) ; 30 minutes au plus
R_MIN, R_MAX = 3.0, 0.0012                    # stop d'au moins 3 points ; pas de trade si R > 0,12 % du prix
FIN_A = pd.Timestamp("2026-07-31")
SEUIL_T, PLACEBO = 2.13, 2000


# ---------------------------------------------------------------------------------------------- mesures
def mesures(m, info):
    """Mesures de chaque minute (seance x minute) et seuils glissants des 5 seances d'avant."""
    a, v_ = m["achats"], m["ventes"]
    v = a + v_
    delta = a - v_
    imb = np.where(v > 0, delta / np.where(v > 0, v, 1), 0.0)
    typ = (m["h"] + m["l"] + m["c"]) / 3
    cv = np.cumsum(v, axis=1)
    vwap = np.where(cv > 0, np.cumsum(typ * v, axis=1) / np.where(cv > 0, cv, 1), typ)
    cd = np.cumsum(delta, axis=1)
    d30 = cd - np.concatenate([np.zeros((len(cd), 30)), cd[:, :-30]], axis=1)
    S = len(info)
    q = {k: np.full(S, np.nan) for k in ("q10", "q25", "q75", "q90", "fb90", "fh90")}
    for d in range(5, S):
        x = imb[d - 5:d, 30:].ravel()
        q["q10"][d], q["q25"][d], q["q75"][d], q["q90"][d] = np.percentile(x, [10, 25, 75, 90])
        fb, fh = m["ventes_bas2"][d - 5:d, 30:].ravel(), m["achats_haut2"][d - 5:d, 30:].ravel()
        if np.isfinite(fb).all():
            q["fb90"][d], q["fh90"][d] = np.percentile(fb, 90), np.percentile(fh, 90)
    jouable = (~info["mince"].to_numpy()) & (~info["change"].to_numpy()) & np.isfinite(q["q10"])
    return dict(v=v, delta=delta, imb=imb, vwap=vwap, d30=d30, jouable=jouable, **q)


# ---------------------------------------------------------------------------------------------- signaux
def signaux_s1(m, X, d, sans_flux=False):
    o, h, l, c = m["o"][d], m["h"][d], m["l"][d], m["c"][d]
    out = []
    for t in range(DEBUT, FIN + 1):
        med = np.median(X["v"][d, t - 30:t])
        vol_ok = X["v"][d, t] >= med
        milieu = (h[t] + l[t]) / 2
        if (c[t] > X["vwap"][d, t] and X["d30"][d, t] > 0 and l[t] <= l[t - 5:t].min() and c[t] >= milieu
                and (sans_flux or (X["imb"][d, t] <= X["q10"][d] and vol_ok))):
            out.append((t, 1, l[t] - TICK))
        elif (c[t] < X["vwap"][d, t] and X["d30"][d, t] < 0 and h[t] >= h[t - 5:t].max() and c[t] <= milieu
              and (sans_flux or (X["imb"][d, t] >= X["q90"][d] and vol_ok))):
            out.append((t, -1, h[t] + TICK))
    return out


def signaux_s2(m, X, d, sans_flux=False):
    h, l, c = m["h"][d], m["l"][d], m["c"][d]
    if d == 0:
        return []
    niveaux = [(m["h"][d - 1].max(), 1, DEBUT), (m["l"][d - 1].min(), -1, DEBUT),
               (h[:60].max(), 1, 60), (l[:60].min(), -1, 60)]          # PDH, PDL, IBH, IBL ; 1 = niveau au-dessus
    out = []
    for L, haut, debut in niveaux:
        for b in range(debut, FIN + 1):
            casse = (h[b] >= L + TICK and c[b - 1] <= L) if haut == 1 else (l[b] <= L - TICK and c[b - 1] >= L)
            if not casse:
                continue
            agresse = X["imb"][d, b] >= X["q75"][d] if haut == 1 else X["imb"][d, b] <= X["q25"][d]
            if sans_flux or agresse:
                for f in range(b, min(b + 5, FIN) + 1):
                    if (c[f] <= L - TICK) if haut == 1 else (c[f] >= L + TICK):
                        stop = h[b:f + 1].max() + TICK if haut == 1 else l[b:f + 1].min() - TICK
                        out.append((f, -haut, stop))
                        break
            break                                                        # une seule tentative par niveau
    return sorted(out)


def signaux_s3(m, X, d, sans_flux=False):
    if not np.isfinite(X["fb90"][d]) or not np.isfinite(m["ventes_bas2"][d]).all():
        return []
    h, l, c = m["h"][d], m["l"][d], m["c"][d]
    out = []
    for t in range(DEBUT, FIN + 1):
        if l[t] < l[:t].min() and c[t] >= l[t] + 1.0 and (sans_flux or m["ventes_bas2"][d, t] >= X["fb90"][d]):
            out.append((t, 1, l[t] - TICK))
        elif h[t] > h[:t].max() and c[t] <= h[t] - 1.0 and (sans_flux or m["achats_haut2"][d, t] >= X["fh90"][d]):
            out.append((t, -1, h[t] + TICK))
    return out


SETUPS = {"S1 repli absorbe dans le sens du flux": signaux_s1,
          "S2 cassure ratee (pieges)": signaux_s2,
          "S3 volume d'arret a l'extreme (footprint)": signaux_s3}


# ---------------------------------------------------------------------------------------------- execution
def niveaux_trade(o_e, sens, stop_structure):
    """Entree, stop, objectif et risque d'un trade (None si le risque depasse 0,12 % du prix)."""
    entree = o_e + sens * GLISSE
    if sens > 0:
        stop = np.floor(min(stop_structure, entree - R_MIN) / TICK) * TICK
    else:
        stop = np.ceil(max(stop_structure, entree + R_MIN) / TICK) * TICK
    R = abs(entree - stop)
    if R > R_MAX * entree:
        return None
    objectif = entree + sens * 2 * R
    objectif = np.ceil(objectif / TICK) * TICK if sens > 0 else np.floor(objectif / TICK) * TICK
    return entree, stop, objectif, R


def suivre(m, d, e, sens, entree, stop, objectif):
    """Minute par minute, ordre le plus defavorable. Renvoie (minute de sortie, prix de sortie, motif)."""
    o, h, l, c = m["o"][d], m["h"][d], m["l"][d], m["c"][d]
    fin = min(e + DUREE - 1, D.NM - 1)
    for x in range(e, fin + 1):
        if sens > 0:
            if x > e and o[x] <= stop:
                return x, o[x] - GLISSE, "stop"
            if l[x] <= stop:
                return x, stop - GLISSE, "stop"
            if h[x] >= objectif + TICK:
                return x, objectif, "objectif"
        else:
            if x > e and o[x] >= stop:
                return x, o[x] + GLISSE, "stop"
            if h[x] >= stop:
                return x, stop + GLISSE, "stop"
            if l[x] <= objectif - TICK:
                return x, objectif, "objectif"
    return fin, c[fin] - sens * GLISSE, "temps"


def jouer(m, info, X, fonction, sans_flux=False, jours=None):
    """Trades d'un setup (une position a la fois), avec le resultat du meme trade en sens inverse (placebo)."""
    lignes = []
    for d in range(len(info)):
        if not X["jouable"][d] or (jours is not None and not jours[d]):
            continue
        libre = 0
        for t, sens, stop_s in fonction(m, X, d, sans_flux):
            if t < libre:
                continue
            e = t + 1
            nv = niveaux_trade(m["o"][d, e], sens, stop_s)
            if nv is None:
                continue
            entree, stop, objectif, R = nv
            x, sortie, motif = suivre(m, d, e, sens, entree, stop, objectif)
            net = sens * (sortie - entree) - 2 * COM
            # meme minute d'entree, meme risque, sens inverse (stop et objectif symetriques)
            ent_i = m["o"][d, e] - sens * GLISSE
            stop_i = ent_i + sens * R
            obj_i = ent_i - sens * 2 * R
            xi, sor_i, _ = suivre(m, d, e, -sens, ent_i, stop_i, obj_i)
            net_i = -sens * (sor_i - ent_i) - 2 * COM
            lignes.append(dict(seance=d, jour=info["jour"][d].date(), signal=t, entree_min=e, sortie_min=x, sens=sens,
                               entree=entree, stop=stop, objectif=objectif, R=R, sortie=sortie, motif=motif, net=net,
                               net_inverse=net_i))
            libre = x
    return pd.DataFrame(lignes)


# ---------------------------------------------------------------------------------------------- mesures du resultat
def t_stat(x):
    x = np.asarray(x, float)
    s = x.std(ddof=1) if len(x) > 1 else 0.0
    return float(x.mean() / s * np.sqrt(len(x))) if s > 0 else 0.0


def quotidien(tr, seances, col="net"):
    """Gain net de chaque seance jouable (0 sans trade)."""
    q = pd.Series(0.0, index=seances)
    if len(tr):
        q = q.add(tr.groupby("seance")[col].sum(), fill_value=0.0)
    return q.loc[seances].to_numpy()


def placebo(tr, seances, n=PLACEBO, graine=1):
    if len(tr) == 0:
        return np.zeros(n)
    rng = np.random.default_rng(graine)
    pos = pd.Index(seances).get_indexer(tr["seance"])
    a, b = tr["net"].to_numpy(), tr["net_inverse"].to_numpy()
    ts = np.empty(n)
    for i in range(n):
        x = np.where(rng.random(len(a)) < 0.5, a, b)
        q = np.bincount(pos, weights=x, minlength=len(seances))
        ts[i] = t_stat(q)
    return ts


def resume(tr, seances):
    q = quotidien(tr, seances)
    if len(tr) == 0:
        return dict(n=0, moyen=0.0, gagnants=0.0, t_trade=0.0, t_seance=0.0, total=0.0)
    return dict(n=len(tr), moyen=tr["net"].mean(), gagnants=(tr["net"] > 0).mean(), t_trade=t_stat(tr["net"]),
                t_seance=t_stat(q), total=tr["net"].sum())


# ---------------------------------------------------------------------------------------------- controle a la seconde
def a_la_seconde(S, tr):
    """Descriptif (Databento) : entree au meilleur vendeur (achat) de la premiere seconde de la minute d'entree, stop
    quand le plus bas d'une seconde le touche (sortie au pire du stop - 1 tick et du meilleur acheteur), objectif
    traverse d'un tick, sortie au temps au meilleur acheteur de la derniere seconde."""
    nets = []
    for r in tr.itertuples():
        d, s0 = r.seance, r.entree_min * 60
        if d >= len(S.jours):
            nets.append(np.nan)
            continue
        sens = r.sens
        entree = S.ask[d, s0] if sens > 0 else S.bid[d, s0]
        stop = np.floor((entree - sens * r.R) / TICK) * TICK if sens > 0 else np.ceil((entree - sens * r.R) / TICK) * TICK
        obj = entree + sens * 2 * r.R
        fin = min(s0 + DUREE * 60 - 1, D.NS - 1)
        sortie = None
        for s in range(s0, fin + 1):
            if sens > 0:
                if S.bas[d, s] <= stop:
                    sortie = min(stop - TICK, S.bid[d, s])
                    break
                if S.haut[d, s] >= obj + TICK:
                    sortie = obj
                    break
            else:
                if S.haut[d, s] >= stop:
                    sortie = max(stop + TICK, S.ask[d, s])
                    break
                if S.bas[d, s] <= obj - TICK:
                    sortie = obj
                    break
        if sortie is None:
            sortie = S.bid[d, fin] if sens > 0 else S.ask[d, fin]
        nets.append(sens * (sortie - entree) - 2 * COM)
    return np.array(nets)


# ---------------------------------------------------------------------------------------------- challenge (descriptif)
def challenge(gains_jour_pts, taille, n_seances, solde, haut, tirages=20000, graine=3):
    """Bulenox 50K par tirage des seances (avec remise) : plancher = plus haut de fin de journee - 2 500 $ (bloque a
    50 100 $ des 52 600 $), objectif 53 050 $, limite du jour 1 000 $ (appliquee trade par trade). gains_jour_pts :
    liste, par seance, des gains nets des trades dans l'ordre (points de NQ, 1 MNQ)."""
    rng = np.random.default_rng(graine)
    res = np.zeros(tirages, int)
    for k in range(tirages):
        bal, hh = solde, haut
        plancher = 50100.0 if hh >= 52600 else hh - 2500
        for s in rng.integers(0, len(gains_jour_pts), n_seances):
            jour = 0.0
            for g in gains_jour_pts[s]:
                jour += g * 2 * taille
                if bal + jour <= plancher:
                    res[k] = -1
                    break
                if bal + jour >= 53050:
                    res[k] = 1
                    break
                if jour <= -1000:
                    break
            if res[k]:
                break
            bal += jour
            hh = max(hh, bal)
            plancher = 50100.0 if hh >= 52600 else hh - 2500
            if bal <= plancher:
                res[k] = -1
                break
    return (res == 1).mean(), (res == -1).mean(), (res == 0).mean()


# ---------------------------------------------------------------------------------------------- programme
def main():
    m, info, S = D.seances()
    X = mesures(m, info)
    jours = info["jour"]
    A = (jours <= FIN_A).to_numpy()
    B = ~A
    fp_ok = np.isfinite(m["ventes_bas2"]).all(axis=1)
    L = [f"Systeme order flow NQ (flux/README.md) : {len(info)} seances du {jours.iloc[0].date()} au "
         f"{jours.iloc[-1].date()} ({(info['source'] == 'databento').sum()} Databento, "
         f"{(info['source'] == 'export').sum()} export Rithmic) ; jouables : {X['jouable'].sum()}",
         f"A = jusqu'au {FIN_A.date()} ({(X['jouable'] & A).sum()} seances jouables), "
         f"B = apres ({(X['jouable'] & B).sum()}). Points de NQ par trade, frais compris (1 point = 2 $ par MNQ).", ""]
    tous = {}
    for nom, f in SETUPS.items():
        tr = jouer(m, info, X, f)
        jum = jouer(m, info, X, f, sans_flux=True)
        tous[nom] = tr
        base = X["jouable"] & (fp_ok if nom.startswith("S3") else True)
        sA, sB, sT = (np.flatnonzero(base & p) for p in (A, B, np.ones_like(A)))
        trA, trB = tr[tr["seance"].isin(sA)], tr[tr["seance"].isin(sB)]
        rA, rB, rT = resume(trA, sA), resume(trB, sB), resume(tr, sT)
        pl = placebo(tr, sT)
        bat = (pl < rT["t_seance"]).mean()
        rJ = resume(jum, sT)
        ok = [rA["moyen"] > 0 and rB["moyen"] > 0, rT["t_seance"] >= SEUIL_T, bat >= 0.95, rT["n"] >= 60]
        L.append(nom)
        for lib, r in (("A", rA), ("B", rB), ("A + B", rT)):
            L.append(f"  {lib:<6} {r['n']:4d} trades | net moyen {r['moyen']:+6.2f} pt | gagnants {r['gagnants']:5.1%} | "
                     f"t par trade {r['t_trade']:+5.2f} | t par seance {r['t_seance']:+5.2f} | total {r['total']:+8.1f} pt")
        if len(tr):
            mo = tr["motif"].value_counts(normalize=True)
            L.append(f"  sorties : objectif {mo.get('objectif', 0):.0%}, stop {mo.get('stop', 0):.0%}, temps "
                     f"{mo.get('temps', 0):.0%} ; risque R median {tr['R'].median():.2f} pt ; achats {(tr['sens'] > 0).mean():.0%}")
        L.append(f"  placebo de sens : bat {bat:.1%} des {PLACEBO} tirages (95e centile des placebos : t "
                 f"{np.percentile(pl, 95):+.2f})")
        L.append(f"  jumeau sans order flow (descriptif) : {rJ['n']} trades, net moyen {rJ['moyen']:+.2f} pt, t par seance "
                 f"{rJ['t_seance']:+.2f}")
        L.append(f"  decision : {'RETENU pour le suivi en simulation' if all(ok) else 'non retenu'} "
                 f"(A et B positifs {ok[0]}, t >= {SEUIL_T} {ok[1]}, placebo 95 % {ok[2]}, 60 trades {ok[3]})")
        L.append("")
        tr.to_csv(ICI / "resultats" / f"trades_{nom[:2]}.csv", index=False)

    # ---------------- descriptif
    L.append("DESCRIPTIF (aucune decision)")
    L.append("Mois par mois (net en points, nombre de trades) :")
    for nom, tr in tous.items():
        if len(tr):
            mm = tr.assign(mois=pd.to_datetime(tr["jour"]).dt.strftime("%Y-%m")).groupby("mois")["net"].agg(["sum", "count"])
            L.append(f"  {nom[:2]} : " + " | ".join(f"{i} {r['sum']:+.0f} ({r['count']:.0f})" for i, r in mm.iterrows()))
    L.append("")
    L.append("Execution a la seconde (Databento seulement), memes trades :")
    for nom, tr in tous.items():
        trd = tr[tr["seance"] < len(S.jours)]
        if len(trd):
            ns = a_la_seconde(S, trd)
            L.append(f"  {nom[:2]} : {len(trd)} trades, net moyen a la minute {trd['net'].mean():+.2f} pt, a la seconde "
                     f"{np.nanmean(ns):+.2f} pt, t par trade {t_stat(ns[np.isfinite(ns)]):+.2f}")
    L.append("")
    # les trois ensemble : une position a la fois, le premier signal l'emporte
    ens = pd.concat([tr.assign(setup=n[:2]) for n, tr in tous.items()]).sort_values(["seance", "signal"])
    garde, libre = [], {}
    for r in ens.itertuples():
        if r.signal >= libre.get(r.seance, 0):
            garde.append(r)
            libre[r.seance] = r.sortie_min
    ens = pd.DataFrame(garde)
    sT = np.flatnonzero(X["jouable"])
    rE = resume(ens, sT)
    L.append(f"Les trois ensemble (une position a la fois) : {rE['n']} trades, net moyen {rE['moyen']:+.2f} pt, t par "
             f"seance {rE['t_seance']:+.2f}, total {rE['total']:+.0f} pt ({rE['total'] * 2:+,.0f} $ par MNQ)")
    L.append("")
    L.append("Challenge Bulenox 50K par tirage des seances jouables (A + B), limite du jour 1 000 $, trade par trade :")
    for nom, tr in list(tous.items()) + [("Les trois ensemble", ens)]:
        g = [list(tr[tr["seance"] == s].sort_values("signal")["net"]) for s in sT]
        for solde, haut, lib in ((50000.0, 50000.0, "compte neuf"), (49900.0, 51172.0, "49 900 $, plancher 48 672 $")):
            parts = []
            for taille in (1, 2, 4):
                v, p, e = challenge(g, taille, 30, solde, haut, tirages=4000)
                parts.append(f"{taille} MNQ {v:5.1%} / {p:5.1%} / {e:5.1%}")
            L.append(f"  {nom[:18]:<18} {lib:<28} 30 seances, valide / perdu / pas fini : " + " | ".join(parts))
    texte = "\n".join(L)
    (ICI / "resultats" / "systeme.txt").write_text(texte + "\n")
    print(texte)


if __name__ == "__main__":
    (ICI / "resultats").mkdir(exist_ok=True)
    main()
