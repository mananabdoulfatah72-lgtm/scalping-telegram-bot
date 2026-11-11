"""Partie N : la nuit (achat 18 h, vente 9 h 30) avec stop et filtres. Regles : REGLES.md.

Usage : python3 nuit.py   (ecrit resultats/nuit.txt et le cache nuits.npz utilise par compte.py)
"""
import datetime as dt
import json

import numpy as np
import pandas as pd

import donnees as D

STOPS = (0.0, 0.005, 0.0075, 0.010)
FILTRES = ("F0", "F1", "F2", "F3")
SORTIE = D.ICI / "resultats"; SORTIE.mkdir(exist_ok=True)


def construire():
    """Une ligne par seance complete du NQ : la nuit qui la precede (lue sur le CFD) et les filtres connus a l'entree."""
    M = D.nq_minutes()
    J, ok, O, C = M["J"], M["ok"], M["O"], M["C"]
    t, o, h, l, c = D.cfd()
    dj, mn, _ = D.heure_ny(t)
    ordi = pd.to_datetime(dj).map(dt.date.toordinal).to_numpy()
    soir = mn >= 1080; matin = mn < 570
    nid = np.where(soir, ordi + 1, np.where(matin, ordi, -1))          # jour de trading auquel la barre de nuit appartient
    S = len(J)
    ordJ = pd.to_datetime(J).map(dt.date.toordinal).to_numpy()
    entree = np.full(S, np.nan); sortie = np.full(S, np.nan); nb = np.zeros(S, int)
    chemins = [None] * S
    debut = np.searchsorted(nid_tri := np.sort(nid[nid >= 0]), ordJ)  # noqa: F841 (seulement pour verifier le tri)
    pos = np.nonzero(nid >= 0)[0]; cle = nid[pos]
    ordre = np.argsort(cle, kind="stable"); pos = pos[ordre]; cle = cle[ordre]
    a = np.searchsorted(cle, ordJ, "left"); b = np.searchsorted(cle, ordJ, "right")
    i930 = {}
    for k in np.nonzero(mn == 570)[0]:
        i930[ordi[k]] = k
    for s in range(S):
        if not ok[s] or b[s] - a[s] < 150:
            continue
        idx = pos[a[s]:b[s]]
        k0 = idx[0]
        if not (soir[k0] and mn[k0] < 1110 and ordi[k0] == ordJ[s] - 1):   # entree entre 18 h et 18 h 30, la veille au soir
            continue
        k1 = i930.get(ordJ[s])
        if k1 is None:
            continue
        entree[s] = o[k0]; sortie[s] = o[k1]; nb[s] = len(idx)
        chemins[s] = (o[idx], l[idx])
    # filtres connus a l'entree (cloture de la veille de la seance s)
    V = D.clotures()
    tous = pd.Index(J)
    veille = V.reindex(tous.union(V.index)).sort_index().ffill().shift(1).reindex(tous)
    comp = np.nonzero(ok)[0]
    cl = C[comp, D.N - 1]; r = np.diff(np.log(cl))                       # rendements cloture a cloture des seances completes
    rv = np.full(len(comp), np.nan)
    for i in range(20, len(comp)):
        rv[i] = r[i - 20:i].std(ddof=1) * np.sqrt(252) * 100              # connu a la cloture de la seance comp[i]
    rv_veille = np.full(S, np.nan); baisse = np.zeros(S, bool); dern = np.full(S, -1)
    for i in range(1, len(comp)):
        s, p = comp[i], comp[i - 1]
        rv_veille[s] = rv[i - 1]; baisse[s] = C[p, D.N - 1] < O[p, 0]; dern[s] = p
    ratio = veille["VXN"].to_numpy() / rv_veille
    med = pd.Series(ratio[comp]).rolling(252, min_periods=252).median().shift(1).to_numpy()
    cher = np.zeros(S, bool); cher[comp] = ratio[comp] > med
    inverse = (veille["VIX"] >= veille["VIX3M"]).to_numpy()
    jour = np.full(S, np.nan); jour[ok] = C[ok, D.N - 1] / O[ok, 0] - 1
    return dict(J=J, ok=ok, entree=entree, sortie=sortie, nb=nb, chemins=chemins, inverse=inverse, baisse=baisse, cher=cher,
                ratio=ratio, jour=jour, vix=veille["VIX"].to_numpy(), vxn=veille["VXN"].to_numpy(), rv=rv_veille)


def gains(X, stop, frais=D.FRAIS):
    """Gain en $ de chaque nuit jouable pour 1 MNQ au prix d'aujourd'hui, et pire moment de la nuit (latent, en $)."""
    S = len(X["J"]); g = np.full(S, np.nan); creux = np.full(S, np.nan); stoppe = np.zeros(S, bool)
    tick = D.TICK / D.PREF
    for s in range(S):
        e = X["entree"][s]
        if not np.isfinite(e):
            continue
        ob, lb = X["chemins"][s]
        r = X["sortie"][s] / e - 1; bas = lb.min() / e - 1
        if stop > 0:
            niv = e * (1 - stop)
            k = np.nonzero(lb <= niv)[0]
            if len(k):
                k = k[0]
                px = ob[k] if (k > 0 and ob[k] < niv) else niv
                r = px / e - 1 - tick; bas = min(-stop, r); stoppe[s] = True
        g[s] = r * D.PREF * 2 - frais; creux[s] = min(bas * D.PREF * 2 - frais, g[s])
    return g, creux, stoppe


def masque(X, f):
    jouable = np.isfinite(X["entree"])
    if f == "F0":
        return jouable
    if f == "F1":
        return jouable & ~X["inverse"]
    if f == "F2":
        return jouable & X["baisse"]
    return jouable & X["cher"]


def mesure(X, g, garde):
    jouable = np.isfinite(X["entree"]); J = X["J"]
    v = np.where(garde, g, 0.0)[jouable]; jj = J[jouable]
    ex = jj <= D.FIN_EXPLO
    an = np.array([x[:4] for x in jj]); annees = sorted(set(an))
    pos = sum(v[an == a].sum() > 0 for a in annees)
    pris = v[garde[jouable]]
    return dict(n=int(garde[jouable].sum()), t=D.tstat(v), t_ex=D.tstat(v[ex]), t_ct=D.tstat(v[~ex]), moy=float(pris.mean()) if len(pris) else 0.0,
                moy_ex=float(v[ex].mean()), moy_ct=float(v[~ex].mean()), total=float(v.sum()), pire=float(pris.min()) if len(pris) else 0.0,
                sous_1100=int((pris <= -1100).sum()), annees_pos=int(pos), annees=len(annees), par_an=float(v.sum() / len(annees)))


def principal():
    X = construire()
    jouable = np.isfinite(X["entree"])
    lignes = [f"Partie N : la nuit (achat 18 h, vente 9 h 30), 1 MNQ au prix d'aujourd'hui, frais 3 $.",
              f"Nuits jouables : {int(jouable.sum())} du {X['J'][jouable][0]} au {X['J'][jouable][-1]} "
              f"(exploration {int((X['J'][jouable] <= D.FIN_EXPLO).sum())}, controle {int((X['J'][jouable] > D.FIN_EXPLO).sum())}).", ""]
    res = {}; ps = []
    for stop in STOPS:
        g, creux, stp = gains(X, stop); g6, _, _ = gains(X, stop, 6.0)
        for f in FILTRES:
            m = mesure(X, g, masque(X, f)); m["t6"] = mesure(X, g6, masque(X, f))["t"]
            m["stoppees"] = int((stp & masque(X, f)).sum()); res[(stop, f)] = m; ps.append(D.p_unilateral(m["t"]))
    passe = D.bh(ps)
    lignes.append(f"{'variante':<16}{'nuits':>6}{'t':>7}{'t expl':>8}{'t ctrl':>8}{'t a 6$':>8}{'$/nuit':>8}{'$/an':>8}{'pire':>8}{'<-1100':>7}{'annees+':>8}{'stops':>6}  verdict")
    retenues = []
    for k, ((stop, f), m) in enumerate(res.items()):
        cond = [m["t"] >= 2 and passe[k], m["moy_ex"] > 0 and m["moy_ct"] > 0, m["t6"] >= 1.5, m["annees_pos"] >= 10, m["pire"] > -1100]
        m["bh"] = bool(passe[k]); m["retenue"] = bool(all(cond))
        raison = "" if all(cond) else "echoue : " + ", ".join(n for n, c in zip(("t/BH", "deux periodes", "frais 6 $", "annees", "pire nuit"), cond) if not c)
        if all(cond):
            retenues.append((m["t"], stop, f))
        nom = f"{f} stop {stop * 100:.2f}%" if stop else f"{f} sans stop"
        lignes.append(f"{nom:<16}{m['n']:>6}{m['t']:>7.2f}{m['t_ex']:>8.2f}{m['t_ct']:>8.2f}{m['t6']:>8.2f}{m['moy']:>8.1f}{m['par_an']:>8.0f}{m['pire']:>8.0f}{m['sous_1100']:>7}"
                      f"{m['annees_pos']:>5}/{m['annees']:<2}{m['stoppees']:>6}  {'RETENUE' if all(cond) else raison}")
    # information : le jour sur les memes dates, et la difference
    g0, _, _ = gains(X, 0.0)
    jr = X["jour"][jouable] * D.PREF * 2 - D.FRAIS; nu = g0[jouable]
    lignes += ["", f"Pour information, memes dates : jour 9 h 30 -> 15 h 59 (achat) t {D.tstat(jr):.2f}, {jr.mean():.1f} $ par seance ; "
                   f"nuit sans stop t {D.tstat(nu):.2f}, {nu.mean():.1f} $ ; difference nuit - jour t {D.tstat(nu - jr):.2f} ; "
                   f"correlation nuit / jour suivant {np.corrcoef(nu, jr)[0, 1]:+.2f}."]
    retenues.sort(reverse=True)
    choix = []
    for t_, stop, f in retenues:                      # 2 meilleures avec des filtres differents
        if f not in [c[1] for c in choix] and len(choix) < 2:
            choix.append((stop, f))
    lignes += ["", "Retenues pour le compte : " + (", ".join(f"{f} stop {s * 100:.2f}%" for s, f in choix) if choix else "aucune")]
    (SORTIE / "nuit.txt").write_text("\n".join(lignes) + "\n")
    json.dump({f"{f}_{s}": m for (s, f), m in res.items()} | {"choix": choix}, open(SORTIE / "nuit.json", "w"), indent=1)
    print("\n".join(lignes))
    return X, res, choix


if __name__ == "__main__":
    principal()
