#!/usr/bin/env python3
"""Descriptif : gains jour par jour de la zone et des 4 regles (H12, H1, H5, F3) sur les minutes du robot, 20 seances jamais vues et 12 derniers mois. Lancer : python3 scalping/jour_par_jour.py <nq_1min.csv.gz>"""
import numpy as np, suivi5 as SV, partie_h as H, partie_f as F, partie_g as G, commun as K
d = SV.charger(__import__('sys').argv[1])
O, C = d['o'], d['c']; S = len(d['jours'])
ech = 1.0 / O[:, 0]
def reel(g): return g                              # deja en $ reels (pref / ouverture * ouverture = 1 * points)
out = {**H.toutes(d), **F.toutes(d)}
# ech = pref/O : avec pref = 1, les gains sont en points*2/O ; on remultiplie par l'ouverture pour revenir aux $ reels
fix = lambda g: g
regles = {k: np.nan_to_num(fix(out[k][0])) for k in ('H12', 'H1', 'H5', 'F3')}
tr = G.calcul(d)[4]; zone = np.zeros(S)
for s, me, sg, ms in tr: zone[s] += sg * (C[s, ms] - C[s, me]) * 2 * float(d['pref']) / O[s, 0] - 3.0
def periode(a, b, titre):
    i = np.flatnonzero((d['jours'] >= np.datetime64(a)) & (d['jours'] <= np.datetime64(b)))
    print(titre)
    print('jour         zone(1MNQ)  Supertrend   ORB5  cassure  pivots | ORB5+pivots  les 4')
    for s in i:
        r = [regles[k][s] for k in ('H12', 'H1', 'H5', 'F3')]
        print(f"{str(d['jours'][s])}  {zone[s]:+9.0f}  {r[0]:+9.0f} {r[1]:+7.0f} {r[2]:+7.0f} {r[3]:+7.0f} | {r[1]+r[3]:+9.0f} {sum(r):+8.0f}")
    for nom, x in [('zone', zone[i])] + [(k, regles[k][i]) for k in ('H12', 'H1', 'H5', 'F3')] + [('ORB5+pivots', regles['H1'][i] + regles['F3'][i]), ('les 4', sum(regles[k][i] for k in regles))]:
        eq = np.cumsum(x); dd = (np.maximum.accumulate(np.r_[0, eq]) - np.r_[0, eq]).max()
        print(f"  {nom:<12} total {x.sum():+7.0f} $ ; jours perdants {int((x < 0).sum())} ; pire jour {x.min():+6.0f} $ ; pire baisse {dd:6.0f} $")
    m = (zone[i] != 0) | (sum(regles[k][i] for k in regles) != 0)
    print('  correlation quotidienne zone / (les 4) sur la periode : %+.2f' % np.corrcoef(zone[i], sum(regles[k][i] for k in regles))[0, 1])
periode('2026-09-28', '2026-10-23', '=== 20 seances jamais vues (28 sept. - 23 oct. 2026), $ pour 1 MNQ au prix du jour du suivi, frais compris ===')
i = np.flatnonzero((d['jours'] >= np.datetime64('2025-10-27')) & (d['jours'] <= np.datetime64('2026-10-23')))
print('\n=== 12 derniers mois (27 oct. 2025 - 23 oct. 2026), 1 MNQ ===')
for nom, x in [('zone', zone[i])] + [(k, regles[k][i]) for k in ('H12', 'H1', 'H5', 'F3')] + [('ORB5+pivots', regles['H1'][i] + regles['F3'][i]), ('les 4', sum(regles[k][i] for k in regles))]:
    eq = np.cumsum(x); dd = (np.maximum.accumulate(np.r_[0, eq]) - np.r_[0, eq]).max()
    print(f"  {nom:<12} total {x.sum():+7.0f} $ ; jours perdants {int((x < 0).sum())}/{int((x != 0).sum())} ; pire jour {x.min():+6.0f} $ ; pire baisse {dd:6.0f} $")
