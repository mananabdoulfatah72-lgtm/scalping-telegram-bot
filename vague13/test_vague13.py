#!/usr/bin/env python3
"""Controles de la vague 13 (README.md). Lancer depuis ce dossier : python3 test_vague13.py.
1. Sans levier (candidate A, et tailles 1 et 4, avec et sans frein), defi13 puis master13 redonnent exactement
   moteur4.parcours4 avec la limite de 30 jours (vague 12) : issue, seances, Master perdu, retraits, recu, 1er retrait,
   retraits seance par seance.
2. Arret a l'objectif : un challenge valide par B finit sa derniere seance a 3 000 $ ou plus, et aucune seance avant
   ne finit a 3 000 $ ou plus (sinon il aurait valide plus tot).
3. Taille adaptative : la taille enregistree suit les regles (protection sous le coussin, fin de course, pres du but)."""
import numpy as np

import regles13 as R

K = R.K


def main():
    P = K.MC.preparer()
    d0, d1, lim, _ = K.achats(P)
    nj = len(P["jours"])
    rng = np.random.default_rng(13)
    jours = rng.choice(np.arange(d0, d1), 250, replace=False)
    b = P["bases"]["fort"][3]
    for compte in ("legacy", "momentum"):
        A = K.COMPTES[compte]
        for q, c_ch in ((4, 0.0), (1, A["frein"]), (4, A["frein"])):
            for d in jours:
                sv = min(K.H, nj - d)
                r0, ret0 = K.un_achat(P, b, int(d), compte, q, c_ch, A["frein"], sv, lim[d])
                ts, tp, tt = np.zeros(lim[d] + 1), np.zeros(lim[d] + 1), np.zeros(lim[d] + 1, np.int64)
                iss, nch, veut, d2 = R.M13.defi13(int(d), int(lim[d]), 4, P["kN"], P["kE"], *b, *A["E"], q, c_ch, 0,
                                                  50.0, 0, 0.0, 0, 0, 0, 0.0, ts, tp, tt)
                assert iss == r0[0], (compte, q, d, iss, r0)
                if iss == 0:
                    continue
                assert nch == r0[1], (compte, q, d, nch, r0)
                if iss == 1:
                    ret = np.zeros(sv)
                    F = A["F"]
                    m = R.M13.master13(int(d), d2, veut, min(nj, int(d) + sv), 4, P["kN"], P["kE"], ret, *b, *F[:9],
                                       F[9], F[10], A["cycle"], A["frein"], A["cap"])
                    assert (bool(m[0]), m[1], m[3], m[4]) == (bool(r0[2]), r0[3], r0[5], r0[6]) and abs(m[2] - r0[4]) < 1e-9, \
                        (compte, q, d, m, r0)
                    assert np.array_equal(ret, ret0), (compte, q, d)
            print(f"ok : {compte}, taille {q}, frein {c_ch:.0f} : defi13 + master13 = parcours4 sur 250 achats")
        n_b = n_a = 0
        for d in jours:
            sv = min(K.H, nj - d)
            ra, _, (sa, pa, qa) = R.un_achat(P, b, int(d), compte, "A", sv, lim[d], traces=True)
            rb, _, (sb, pb, qb) = R.un_achat(P, b, int(d), compte, "B", sv, lim[d], traces=True)
            if rb[0] == 1:
                assert sb[-1] >= 3000.0, (d, sb[-1])
                assert (sb[:-1] < 3000.0).all(), (d, sb)
                n_b += 1
            n_a += ra[0] == 1
            for lettre, regle in (("C", "prot"), ("D", "fin"), ("F", "but")):
                rc, _, (sc, pc, qc) = R.un_achat(P, b, int(d), compte, lettre, sv, lim[d], traces=True)
                avant = np.r_[0.0, sc[:-1]]
                plan_avant = np.r_[-A["E"][1], pc[:-1]]
                reste = lim[d] - np.arange(len(sc))
                attendu = np.full(len(sc), 4)
                if regle == "but":
                    attendu[3000.0 - avant < 1000.0] = 2
                if regle == "fin":
                    attendu[reste <= 5] = 6
                if regle == "prot":
                    attendu[avant - plan_avant < A["E"][1] / 2] = 2
                assert np.array_equal(np.abs(qc), attendu), (compte, lettre, d, qc, attendu)
        print(f"ok : {compte} : arret a l'objectif (B valide {n_b} fois, A {n_a} fois sur 250 ; jamais un jour sous 3 000 $ "
              "avant la validation) ; tailles C, D, F conformes aux regles")
    print("tous les controles passent")


if __name__ == "__main__":
    main()
