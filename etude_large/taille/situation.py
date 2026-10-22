#!/usr/bin/env python3
"""Chance de valider depuis la situation donnee par l'utilisateur le 22 octobre 2026 (solde 48 891 $, plancher
48 488 $, 16 seances jusqu'au 12 novembre), Bulenox, vraies suites de seances. Lancer depuis la racine du depot :
python3 etude_large/taille/situation.py (variable KB comme delta_mesures)."""
import sys, importlib.util; sys.dont_write_bytecode=True
sys.path.insert(0,'etude_large')
import numpy as np
from numba import njit
import partie_d as PD
spec=importlib.util.spec_from_file_location('taille_etude','etude_large/taille/etude.py'); T=importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
obj, dd, bloc, dll = 3000.0, 2500.0, 100.0, 1100.0
B0, F0, N0 = 48891-50000.0, 48488-50000.0, 16
H0 = F0 + dd
jours, clo, bas, haut = PD.chemins_zone()
rmin=np.minimum.accumulate(bas,axis=1); rmax=np.maximum.accumulate(haut,axis=1); fin=clo[:,-1]
choix=(jours>=PD.DEBUT)&(jours<=PD.FIN_CHOIX)
bgrid=np.arange(-dd,obj+50+25,50.0); hgrid=np.arange(0.0,dd+bloc+25,50.0)
tr=T.transitions(rmin[choix],rmax[choix],fin[choix],bgrid,hgrid,obj,dd,bloc,dll)
V,Q=T.resoudre(*tr,22)
nh=len(hgrid)
s=int(round((B0-bgrid[0])/50))*nh+int(round((H0-hgrid[0])/50))
print(f"Politique (tirages 2012-2021) : chance {V[N0,s]*100:.1f} %, taille conseillee aujourd'hui {Q[N0,s]} MNQ")

@njit
def defi_etat(clo,bas,haut,debut,nmax,q,qf,nf,bal,sommet,obj,dd,bloc,dll,Qp,bgrid,hgrid,usepol):
    n=clo.shape[0]; nh=len(hgrid); cible=obj+50.0
    for k in range(nmax):
        d=debut+k
        if d>=n: return 0,k
        if usepol:
            jb=min(max(int(round((bal-bgrid[0])/50.0)),0),len(bgrid)-1)
            jh=min(max(int(round((min(sommet,hgrid[nh-1])-hgrid[0])/50.0)),0),nh-1)
            taille=Qp[min(nmax-k,Qp.shape[0]-1), jb*nh+jh]
        else:
            taille=qf if nmax-k<=nf else q
        plancher=min(sommet-dd,bloc)
        jour=taille*clo[d,clo.shape[1]-1]
        for t in range(clo.shape[1]):
            if bal+taille*bas[d,t]<=plancher: return -1,k+1
            if dll>0 and taille*bas[d,t]<=-dll:
                jour=-dll; break
            if bal+taille*haut[d,t]>=cible:
                jour=cible-bal; break
        bal+=jour
        if bal>sommet: sommet=bal
        if bal>=obj: return 1,k+1
    return 0,nmax

for lab,d0,d1 in (("departs 2012-2026",PD.DEBUT,"2026-12-31"),("departs 2023-2026",PD.DEBUT_VERIF,"2026-12-31")):
    dep=np.where((jours>=d0)&(jours<=d1))[0]; dep=dep[dep+N0<len(jours)]
    print('\n',lab,len(dep),'departs ; valide / perdu / expire ; seances avant la perte (mediane)')
    essais=[(f"{q} MNQ",q,q,0,False) for q in range(1,7)]+[("4 puis 6 (bot actuel)",4,6,5,False),("politique optimale",0,0,0,True)]
    for nom,q,qf,nf,up in essais:
        r=[defi_etat(clo,bas,haut,d,N0,float(q),float(qf),nf,B0,H0,obj,dd,bloc,dll,Q,bgrid,hgrid,up) for d in dep]
        iss=np.array([x[0] for x in r]); nb=np.array([x[1] for x in r])
        med=np.median(nb[iss==-1]) if (iss==-1).any() else float('nan')
        print(f"  {nom:<24} {(iss==1).mean()*100:5.1f} {(iss==-1).mean()*100:5.1f} {(iss==0).mean()*100:5.1f}   {med:.0f}")
