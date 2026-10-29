#!/usr/bin/env python3
"""S2b avec un stop elargi (flux/README.md) : ecart de 0, 2, 4, 6, 8 points, objectif 2 R du nouveau risque (a) ou
objectif inchange (b). Choix sur avril - juillet, jugement sur 3 aout - 27 octobre.

Lancer : KB=<copie de claude/keen-babbage-r686cl> FLUX_EXPORTS=flux/donnees python3 flux/stop_s2b.py"""
from pathlib import Path

import numpy as np
import pandas as pd

import detail_s2b as S
import donnees as D
import systeme as Y

ICI = Path(__file__).resolve().parent
TICK = 0.25
SANS_VEILLE = pd.Timestamp("2026-10-19")
FIN_A, FIN_B = pd.Timestamp("2026-07-31"), pd.Timestamp("2026-10-27")


def jouer(m, info, X, ecart, obj_fixe):
    Y.DUREE = 60
    lignes = []
    for d in range(len(info)):
        if not X["jouable"][d] or info["jour"][d] == SANS_VEILLE:
            continue
        libre = 0
        for t, sens, stop_s in S.signaux_s2b(m, X, d):
            if t < libre:
                continue
            e = t + 1
            ent = m["o"][d, e] + sens * TICK
            st0 = (np.floor(min(stop_s, ent - Y.R_MIN) / TICK) * TICK if sens > 0
                   else np.ceil(max(stop_s, ent + Y.R_MIN) / TICK) * TICK)
            R0 = abs(ent - st0)
            if R0 > Y.R_MAX * ent:
                continue
            st = st0 - sens * ecart
            R = abs(ent - st)
            ob = ent + sens * 2 * (R0 if obj_fixe else R)
            ob = np.ceil(ob / TICK) * TICK if sens > 0 else np.floor(ob / TICK) * TICK
            x, sortie, motif = Y.suivre(m, d, e, sens, ent, st, ob)
            lignes.append(dict(seance=d, jour=info["jour"][d], signal=t, sens=sens, R=R, motif=motif,
                               net=sens * (sortie - ent) - 2 * Y.COM))
            libre = x
    return pd.DataFrame(lignes)


def main():
    m, info, _ = D.seances()
    X = Y.mesures(m, info)
    jours = info["jour"]
    jou = X["jouable"] & (jours != SANS_VEILLE).to_numpy() & (jours <= FIN_B).to_numpy()
    A = np.flatnonzero(jou & (jours <= FIN_A).to_numpy())
    B = np.flatnonzero(jou & (jours > FIN_A).to_numpy())
    variantes = [(0.0, False)] + [(e, f) for e in (2.0, 4.0, 6.0, 8.0) for f in (False, True)]
    res = {}
    for ecart, fixe in variantes:
        tr = jouer(m, info, X, ecart, fixe)
        res[(ecart, fixe)] = tr
    ref = res[(0.0, False)]
    attendu = pd.read_csv(ICI / "resultats" / "trades_S2b.csv")
    attendu = attendu[pd.to_datetime(attendu["jour"]) <= FIN_B]
    assert len(ref) == len(attendu) and np.allclose(ref["net"].to_numpy(), attendu["net"].to_numpy()), "S2b d'origine non retrouvee"
    nom = lambda e, f: "S2b d'origine" if e == 0 else f"stop +{e:g} pt, objectif {'inchange' if f else '2 R du nouveau risque'}"
    L = ["S2b avec un stop elargi. Choix sur avril - juillet (t par seance), jugement sur 3 aout - 27 octobre. "
         "Points de NQ nets de frais ; 1 point = 2 $ par MNQ.", "",
         f"{'variante':<48} | {'A : trades, net moyen, t':<26} | {'B : trades, total, net moyen, t':<36} | stops | risque median par MNQ"]
    scoreA = {}
    for (e, f), tr in res.items():
        a, b = tr[tr["seance"].isin(A)], tr[tr["seance"].isin(B)]
        tA, tB = Y.t_stat(Y.quotidien(a, A)), Y.t_stat(Y.quotidien(b, B))
        scoreA[(e, f)] = tA
        L.append(f"{nom(e, f):<48} | {len(a):3d}, {a['net'].mean():+6.2f}, {tA:+5.2f}      | {len(b):3d}, {b['net'].sum():+7.1f}, "
                 f"{b['net'].mean():+6.2f}, {tB:+5.2f}       | {(tr['motif'] == 'stop').mean():4.0%} | {2 * tr['R'].median():.0f} $")
    choix = max(scoreA, key=scoreA.get)
    trc, b0 = res[choix], ref
    bc, br = trc[trc["seance"].isin(B)], b0[b0["seance"].isin(B)]
    tc, tr0 = Y.t_stat(Y.quotidien(bc, B)), Y.t_stat(Y.quotidien(br, B))
    adopte = choix != (0.0, False) and bc["net"].sum() > br["net"].sum() and tc > tr0
    L += ["", f"Choisie sur avril - juillet : {nom(*choix)} (t {scoreA[choix]:+.2f} contre {scoreA[(0.0, False)]:+.2f} pour S2b d'origine)",
          f"Sur aout - 27 octobre : {bc['net'].sum():+.1f} pts, t {tc:+.2f} ; S2b d'origine {br['net'].sum():+.1f} pts, t {tr0:+.2f}",
          f"Decision fixee a l'avance : {'ADOPTEE, elle remplace S2b dans le bot' if adopte else 'S2b reste telle quelle'}"]
    nv = lambda tr: tr[tr["jour"] > SANS_VEILLE]
    L += ["", "Seances neuves (20 - 27 octobre), descriptif : " + " ; ".join(
        f"{nom(e, f)} {nv(tr)['net'].sum():+.1f} pts ({(nv(tr)['motif'] == 'stop').sum()} stop(s) sur {len(nv(tr))})" for (e, f), tr in res.items())]
    texte = "\n".join(L)
    (ICI / "resultats" / "stop_s2b.txt").write_text(texte + "\n")
    print(texte)


if __name__ == "__main__":
    main()
