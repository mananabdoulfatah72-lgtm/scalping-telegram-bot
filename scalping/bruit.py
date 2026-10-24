#!/usr/bin/env python3
"""Jumeau de bruit (README.md) : pour chaque annee et chaque minute de la seance (sauf la premiere), la barre de la
meme minute d'une autre seance complete de la meme annee, tiree par permutation (rapports ouverture, plus haut, plus bas,
cloture a la cloture precedente, et volume). Chaque seance complete part de la cloture bruitee de la seance complete
precedente avec le vrai ecart d'ouverture ; les prix sont enchaines puis arrondis au tick. NQ et ES recoivent la meme
permutation sur leurs seances communes."""
import numpy as np


def _permutations(rng, groupes, n):
    """groupes : liste de tableaux d'indices de seances (une permutation par groupe et par minute 1..n-1).
    Renvoie src (S, n) : seance source de chaque minute (-1 : inchangee)."""
    return [(g, np.stack([rng.permutation(g) for _ in range(n - 1)], axis=1)) for g in groupes if len(g)]


def _appliquer(d, perms, tick):
    O, H, L, C, V = d["o"], d["h"], d["l"], d["c"], d["v"]
    S, n = C.shape
    prevc = np.empty_like(C)
    prevc[:, 1:] = C[:, :-1]
    prevc[:, 0] = O[:, 0]
    ro, rh, rl, rc = O / prevc, H / prevc, L / prevc, C / prevc
    src = np.tile(np.arange(S)[:, None], (1, n))
    for g, p in perms:
        src[g, 1:] = p
    cols = np.arange(n)[None, :]
    ro, rh, rl, rc, v = ro[src, cols], rh[src, cols], rl[src, cols], rc[src, cols], V[src, cols]
    complete = d["complete"]
    O2, H2, L2, C2 = O.copy(), H.copy(), L.copy(), C.copy()
    der = -1
    for s in range(S):
        if not complete[s]:
            continue
        if der >= 0:
            o0 = C2[der, n - 1] * (O[s, 0] / C[der, n - 1])          # vrai ecart d'ouverture
        else:
            o0 = O[s, 0]
        f = o0 / O[s, 0]
        O2[s, 0], H2[s, 0], L2[s, 0], C2[s, 0] = O[s, 0] * f, H[s, 0] * f, L[s, 0] * f, C[s, 0] * f
        cc = np.cumprod(np.r_[C2[s, 0], rc[s, 1:]])
        C2[s, 1:] = cc[1:]
        O2[s, 1:] = cc[:-1] * ro[s, 1:]
        H2[s, 1:] = cc[:-1] * rh[s, 1:]
        L2[s, 1:] = cc[:-1] * rl[s, 1:]
        der = s
    r = lambda x: np.round(x / tick) * tick                                   # noqa: E731
    O2, H2, L2, C2 = r(O2), r(H2), r(L2), r(C2)
    H2 = np.maximum(H2, np.maximum(O2, C2))
    L2 = np.minimum(L2, np.minimum(O2, C2))
    out = dict(d)
    out.update(o=O2, h=H2, l=L2, c=C2, v=np.where(complete[:, None], v, V), src=src)
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


def bruiter(d, graine):
    """Un marche seul."""
    rng = np.random.default_rng(graine)
    n = d["c"].shape[1]
    return _appliquer(d, _permutations(rng, groupes_annee(d["jours"], d["complete"]), n), float(d["tick"]))


def bruiter_paire(dq, de, graine):
    """NQ et ES : meme permutation sur leurs seances completes communes (meme seance source pour la meme minute)."""
    rng = np.random.default_rng(graine)
    n = dq["c"].shape[1]
    assert de["c"].shape[1] == n
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
    q = _appliquer(dq, perms_q, float(dq["tick"]))
    e = _appliquer(de, perms_e, float(de["tick"]))
    return q, e
