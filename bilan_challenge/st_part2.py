import numpy as np
import pandas as pd

import st_detail as X

J, T, nj = X.J, X.T, X.nj
td = T[:, 0].astype(int)


def journee(dd, t, lim, reel):
    """Resultat d'une seance (limite du jour, sans plancher) et pire moment latent de la seance."""
    jv, pire, arret = 0.0, 0.0, False
    for i in range(X.jd[dd], X.jf[dd]):
        if arret:
            break
        s, me, mx, e, sortie = int(T[i, 1]), int(T[i, 2]), int(T[i, 3]), T[i, 4], T[i, 5]
        k = 1.0 if reel else 28500.0 / e
        for mm in range(me + 1, mx + 1):
            o, adv = X.O[dd, mm], (X.L[dd, mm] if s > 0 else X.H[dd, mm])
            lat = t * (2 * s * (adv - e) * k - 3.0); pire = min(pire, jv + lat)
            if lim and jv + lat <= -lim:
                niv = e + s * ((-lim - jv) / t + 3.0) / (2 * k)
                sortie = (min(o, niv) - 1.0) if s > 0 else (max(o, niv) + 1.0); arret = True
                break
        jv += t * (2 * s * (sortie - e) * k - 3.0)
    return jv, pire


# A. la periode du challenge, en vrais dollars, compte Option 1 depuis 50 000 $
d0 = int(np.searchsorted(J, "2026-10-13")); n = nj - d0
print(f"\nA. Periode {J[d0]} -> {J[-1]} ({n} seances), vrais dollars, compte Option 1 depuis 50 000 $ (plus haut 50 000 $)")
for t, lim in ((1, 400), (1, 0), (2, 800), (2, 400), (3, 1200), (4, 1000)):
    tot = sum(journee(dd, t, lim, True)[0] for dd in range(d0, nj))
    tr = []
    r = X.fenetre(d0, n, t, lim if lim else 1e9, 50000.0, 50000.0, True, tr)
    issue = {1: "VALIDE", -1: "PERDU", 0: "en cours"}[r[0]]
    print(f"  {t} MNQ, limite {lim or 'aucune'} : periode entiere {tot:+,.0f} $ ; challenge {issue} le {J[d0 + r[2]] if r[2] < n else J[-1]}, "
          f"solde {r[1]:,.0f} $, plus haut latent {r[3]:,.0f} $")
    if (t, lim) in ((1, 400), (2, 800)):
        pd.DataFrame(tr, columns=["jour", "sens", "m_in", "m_out", "entree", "sortie", "gain", "pire_latent", "fin", "solde", "plancher"]).to_csv(
            X.S / f"trace_{t}mnq.csv", index=False)

# detail jour par jour a 2 MNQ / 800 (sans arret a l'objectif)
print("\n  Jour par jour, 2 MNQ, limite 800 $ (vrais dollars, sans arret a l'objectif) :")
cum = 0.0
for dd in range(d0, nj):
    g, p = journee(dd, 2, 800, True); cum += g; ntr = X.jf[dd] - X.jd[dd]
    print(f"   {J[dd]}  {ntr} trade(s)  jour {g:+7,.0f} $  pire moment {p:+7,.0f} $  cumul {cum:+8,.0f} $")

# B. 15 ans a 1 MNQ (gains au prix d'aujourd'hui, 28 500 points), limite 400 $ comme le reglage par defaut
for t, lim in ((1, 400), (2, 800)):
    jours = [(J[dd], *journee(dd, t, lim, False)) for dd in range(nj) if X.complete[dd]]
    j = pd.DataFrame(jours, columns=["jour", "g", "pire"]); j["an"] = j.jour.str[:4]
    s = j.g.to_numpy(); cum = np.cumsum(s); dd_max = (cum - np.maximum.accumulate(cum)).min()
    perd = (s < 0).astype(int); serie = best = 0; somme = pire_somme = 0.0
    for v in s:
        if v < 0:
            serie += 1; somme += v
        elif v > 0:
            serie = 0; somme = 0.0
        best = max(best, serie); pire_somme = min(pire_somme, somme)
    print(f"\nB. 15 ans, {t} MNQ, limite {lim} $ ({len(j)} seances) : {s.mean():+.1f} $/seance, t {s.mean() / s.std() * np.sqrt(len(s)):.2f} ; "
          f"seances gagnantes {(s > 0).mean() * 100:.0f} %, perdantes {(s < 0).mean() * 100:.0f} % ; pire seance {s.min():+,.0f} $ ; "
          f"plus longue serie de seances perdantes {best} ; pire serie {pire_somme:+,.0f} $ ; plus forte baisse du cumul {dd_max:+,.0f} $")
    a = j.groupby("an").g.agg(["sum", "count"])
    print("   par annee : " + " ; ".join(f"{k} {v['sum']:+,.0f}" for k, v in a.iterrows()))
    rec = j[j.jour >= "2023-01-01"].g.to_numpy()
    print(f"   depuis 2023 : {rec.mean():+.1f} $/seance, t {rec.mean() / rec.std() * np.sqrt(len(rec)):.2f}, plus forte baisse "
          f"{(np.cumsum(rec) - np.maximum.accumulate(np.cumsum(rec))).min():+,.0f} $")
k = 28500.0 / T[:, 4]; r1 = (2 * T[:, 1] * (T[:, 5] - T[:, 4]) * k - 3.0)
print(f"   trades a 1 MNQ (sans limite) : {len(r1)}, gagnants {(r1 > 0).mean() * 100:.0f} %, gain moyen {r1[r1 > 0].mean():+.0f} $, "
      f"perte moyenne {r1[r1 < 0].mean():+.0f} $, pire trade {r1.min():+,.0f} $, meilleur {r1.max():+,.0f} $")

# C. chances depuis 51 000 $ (Option 1), departs a chaque seance
print("\nC. Depuis 51 000 $ (Option 1, objectif 53 000 $), departs a chaque seance : reussi / perdu / ni l'un ni l'autre (%)")
for haut0 in (51000.0, 51500.0, 51800.0):
    for a0, nom in (("2011", "2011-2026"), ("2023", "2023-2026")):
        for ns in (22, 66):
            deb = np.array([i for i in range(nj) if J[i] >= a0 and X.complete[i] and i + ns <= nj], np.int64)
            ligne = []
            for t, lim in ((1, 400), (2, 800), (2, 400), (3, 1200), (4, 1000)):
                r, _ = X.sim.lot(deb, ns, X.prm(t, lim), 51000.0, haut0, *X.ARGS, np.ones(len(T), np.bool_), 53000.0, 2500.0, 50100.0)
                r = r[r != 9]
                ligne.append(f"{t} MNQ/{lim} {(r == 1).mean() * 100:4.0f} /{(r == -1).mean() * 100:3.0f} /{(r == 0).mean() * 100:3.0f}")
            print(f"  plancher {haut0 - 2500:,.0f} $ | departs {nom} | {ns} seances : " + " | ".join(ligne))
