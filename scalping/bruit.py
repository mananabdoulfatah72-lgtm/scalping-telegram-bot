#!/usr/bin/env python3
"""Jumeaux de bruit (README.md).

- **Permutation** (regles du 24 octobre) : pour chaque annee et chaque minute de la seance (sauf la premiere), la barre
  de la meme minute d'une autre seance complete de la meme annee, tiree par permutation (rapports ouverture, plus haut,
  plus bas, cloture a la cloture precedente, et volume). Garde la saisonnalite de la journee, detruit tout lien entre
  les minutes (y compris le regroupement de la volatilite).
- **Signe** (version 3, 25 octobre, avant tout calcul) : chaque minute (sauf la premiere) garde sa propre barre mais
  est retournee avec la probabilite 1/2 (rapports inverses, plus haut et plus bas echanges). Garde la volatilite minute
  par minute, son regroupement, le volume et la saisonnalite ; detruit le sens (elan, retour, niveaux, avance d'un
  marche sur l'autre).

Chaque seance complete part de la cloture bruitee de la seance complete precedente avec le vrai ecart d'ouverture ; les
prix sont enchaines puis arrondis a la grille des donnees (`pas`). NQ et ES recoivent le meme tirage sur leurs seances
communes."""
import numpy as np


def _rapports(d):
    O, H, L, C = d["o"], d["h"], d["l"], d["c"]
    prevc = np.empty_like(C)
    prevc[:, 1:] = C[:, :-1]
    prevc[:, 0] = O[:, 0]
    return O / prevc, H / prevc, L / prevc, C / prevc


def _enchainer(d, ro, rh, rl, rc, v):
    O, H, L, C, V = d["o"], d["h"], d["l"], d["c"], d["v"]
    S, n = C.shape
    complete = d["complete"]
    O2, H2, L2, C2 = O.copy(), H.copy(), L.copy(), C.copy()
    der = -1
    for s in range(S):
        if not complete[s]:
            continue
        o0 = C2[der, n - 1] * (O[s, 0] / C[der, n - 1]) if der >= 0 else O[s, 0]     # vrai ecart d'ouverture
        f = o0 / O[s, 0]
        O2[s, 0], H2[s, 0], L2[s, 0], C2[s, 0] = O[s, 0] * f, H[s, 0] * f, L[s, 0] * f, C[s, 0] * f
        cc = np.cumprod(np.r_[C2[s, 0], rc[s, 1:]])
        C2[s, 1:] = cc[1:]
        O2[s, 1:] = cc[:-1] * ro[s, 1:]
        H2[s, 1:] = cc[:-1] * rh[s, 1:]
        L2[s, 1:] = cc[:-1] * rl[s, 1:]
        der = s
    pas = float(d["pas"]) if "pas" in d else float(d["tick"])
    r = lambda x: np.round(x / pas) * pas                                     # noqa: E731
    O2, H2, L2, C2 = r(O2), r(H2), r(L2), r(C2)
    H2 = np.maximum(H2, np.maximum(O2, C2))
    L2 = np.minimum(L2, np.minimum(O2, C2))
    out = dict(d)
    out.update(o=O2, h=H2, l=L2, c=C2, v=np.where(complete[:, None], v, V))
    return out


def _permuter(d, perms):
    S, n = d["c"].shape
    ro, rh, rl, rc = _rapports(d)
    src = np.tile(np.arange(S)[:, None], (1, n))
    for g, p in perms:
        src[g, 1:] = p
    cols = np.arange(n)[None, :]
    out = _enchainer(d, ro[src, cols], rh[src, cols], rl[src, cols], rc[src, cols], d["v"][src, cols])
    out["src"] = src
    return out


def _retourner(d, signes):
    """signes (S, n) de +1 / -1 ; la premiere minute n'est jamais retournee. Version 4 (seconde relecture) : chaque mois,
    toutes les minutes 1 a n-1 des seances completes sont decalees d'une meme constante pour que le mouvement du mois soit
    le vrai ; le
    niveau des prix reste donc celui des vraies donnees a chaque fin de mois (sans cela il derive au hasard, ce qui
    change le poids du tick)."""
    ro, rh, rl, rc = _rapports(d)
    m = signes < 0
    m[:, 0] = False
    ro2 = np.where(m, 1 / ro, ro)
    rc2 = np.where(m, 1 / rc, rc)
    rh2 = np.where(m, 1 / rl, rh)
    rl2 = np.where(m, 1 / rh, rl)
    mois = d["jours"].astype("datetime64[M]")
    cpl = d["complete"]
    for mm in np.unique(mois[cpl]):
        idx = np.flatnonzero((mois == mm) & cpl)
        dec = (np.log(rc[idx, 1:]).sum() - np.log(rc2[idx, 1:]).sum()) / rc2[idx, 1:].size
        f = np.exp(dec)
        for a in (ro2, rh2, rl2, rc2):
            a[idx, 1:] *= f
    out = _enchainer(d, ro2, rh2, rl2, rc2, d["v"])
    out["signes"] = np.where(m, -1, 1)
    return out


def groupes_annee(jours, complete, communs=None):
    ans = jours.astype("datetime64[Y]")
    gr = []
    for a in np.unique(ans):
        idx = np.flatnonzero((ans == a) & complete)
        if communs is None:
            gr.append(idx)
        else:
            c = np.isin(jours[idx], communs)
            gr.append(idx[c])
            gr.append(idx[~c])
    return gr


def bruiter(d, graine, sorte="permutation"):
    """Un marche seul."""
    rng = np.random.default_rng(graine)
    n = d["c"].shape[1]
    if sorte == "signe":
        return _retourner(d, rng.choice(np.array([-1, 1]), size=d["c"].shape))
    perms = [(g, np.stack([rng.permutation(g) for _ in range(n - 1)], axis=1))
             for g in groupes_annee(d["jours"], d["complete"]) if len(g)]
    return _permuter(d, perms)


def bruiter_paire(dq, de, graine, sorte="permutation"):
    """NQ et ES : meme tirage sur leurs seances completes communes (meme seance source, ou meme signe, pour la meme
    minute du meme jour)."""
    rng = np.random.default_rng(graine)
    n = dq["c"].shape[1]
    assert de["c"].shape[1] == n
    if sorte == "signe":
        tous = np.union1d(dq["jours"], de["jours"])
        sg = rng.choice(np.array([-1, 1]), size=(len(tous), n))
        q = _retourner(dq, sg[np.searchsorted(tous, dq["jours"])])
        e = _retourner(de, sg[np.searchsorted(tous, de["jours"])])
        return q, e
    communs = np.intersect1d(dq["jours"][dq["complete"]], de["jours"][de["complete"]])
    gq = groupes_annee(dq["jours"], dq["complete"], communs)
    ge = groupes_annee(de["jours"], de["complete"], communs)
    perms_q, perms_e = [], []
    for a, b in zip(gq, ge):
        if len(a) == 0 and len(b) == 0:
            continue
        ja, jb = dq["jours"][a], de["jours"][b]
        if len(a) and np.isin(ja, communs).all() and len(b) and np.isin(jb, communs).all():
            assert (ja == jb).all()
            p = np.stack([rng.permutation(len(a)) for _ in range(n - 1)], axis=1)
            perms_q.append((a, a[p]))
            perms_e.append((b, b[p]))
        else:
            if len(a):
                perms_q.append((a, np.stack([rng.permutation(a) for _ in range(n - 1)], axis=1)))
            if len(b):
                perms_e.append((b, np.stack([rng.permutation(b) for _ in range(n - 1)], axis=1)))
    return _permuter(dq, perms_q), _permuter(de, perms_e)
