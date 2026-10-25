#!/usr/bin/env python3
"""Partie H, verification de H12 (Supertrend) apres le calcul (README.md) : version independante du Supertrend, allers-retours,
annees, frais de l epoque, combinaison avec la zone. Lancer : KB=<branche de recherche> python3 scalping/verif_h12.py"""
import partie_h as H, partie_e as E, partie_g as G, commun as K, numpy as np, json
d = E.jour_nq(); O,Hh,L,C = d['o'],d['h'],d['l'],d['c']; S=C.shape[0]
ok = d['complete'] & ~d['ech']; ech = float(d['pref'])/O[:,0]; pt=2.0
h5 = Hh.reshape(S,78,5).max(axis=2).reshape(-1); l5 = L.reshape(S,78,5).min(axis=2).reshape(-1); c5 = C[:,4::5].reshape(-1)
ind = H._indicateurs(h5,l5,c5)
n = len(c5); tr = np.zeros(n); tr[1:] = np.maximum(h5[1:]-l5[1:], np.maximum(abs(h5[1:]-c5[:-1]), abs(l5[1:]-c5[:-1])))
atr = np.zeros(n); atr[1] = tr[1]
for i in range(2, n): atr[i] = (atr[i-1]*9+tr[i])/10
mid = (h5+l5)/2; bu = mid+3*atr; bl = mid-3*atr; fu = bu.copy(); fl = bl.copy(); dr = np.ones(n)
for i in range(2, n):
    fu[i] = bu[i] if (bu[i] < fu[i-1] or c5[i-1] > fu[i-1]) else fu[i-1]
    fl[i] = bl[i] if (bl[i] > fl[i-1] or c5[i-1] < fl[i-1]) else fl[i-1]
    dr[i] = -1 if (dr[i-1] > 0 and c5[i] < fl[i]) else (1 if (dr[i-1] < 0 and c5[i] > fu[i]) else dr[i-1])
st = ind[7]; m = np.arange(n) >= 10
print('Supertrend identique a la version independante : %.3f %%' % (100*(st[m] == dr[m]).mean()))
g3 = H._barres(O,Hh,L,C,ok,ech,pt,3.0,ind,12)[0]; g0 = H._barres(O,Hh,L,C,ok,ech,pt,0.0,ind,12)[0]
nb = (g0-g3)/3.0; f = np.isfinite(g3)
print('allers-retours par seance : moyenne %.2f, mediane %.0f' % (np.nanmean(nb), np.nanmedian(nb)))
an = d['jours'].astype('datetime64[Y]').astype(int)+1970
print('par annee ($, 1 MNQ, frais actuels) :', ' '.join(f'{a}:{np.nansum(g3[an==a]):+.0f}' for a in range(2011, 2027)))
print('avant frais par seance : %.2f $ ; frais par seance : %.2f $' % (np.nanmean(g0), np.nanmean(g0-g3)))
gh = g0 - nb*1.5*pt*ech
for lab, msk in (('2011-2016', an <= 2016), ('2017-2022', (an >= 2017) & (an <= 2022)), ('2023-2026', an >= 2023)):
    x = gh[f & msk]; y = g3[f & msk]
    print(f'{lab} : frais de l epoque t {K.t_stat(x):+.2f} ({x.mean():+.1f} $) | frais actuels t {K.t_stat(y):+.2f} ({y.mean():+.1f} $)')
tr_ = G.calcul(d)[4]; gz = np.zeros(S)
for s, me, sg, ms in tr_: gz[s] += sg*(C[s,ms]-C[s,me])*pt*ech[s]-3.0
for lab, msk in (('2011-2026', an >= 2011), ('2023-2026', an >= 2023)):
    sel = ok & msk & f
    z, h, comb = gz[sel], g3[sel], gz[sel]+g3[sel]
    print(f'{lab} : zone t {K.t_stat(z):.2f} ({z.mean():+.1f} $/j) | supertrend t {K.t_stat(h):.2f} ({h.mean():+.1f}) | les deux t {K.t_stat(comb):.2f} ({comb.mean():+.1f}) | corr {np.corrcoef(z,h)[0,1]:+.2f}')
j = json.load(open('resultats/h/partie_h.json')); x = [r for r in j if r['regle'] == 'H12'][0]
print('jumeaux : 95e permutation %.2f, 95e signe %.2f' % (x['bruit_95'], x['signe_95']))
