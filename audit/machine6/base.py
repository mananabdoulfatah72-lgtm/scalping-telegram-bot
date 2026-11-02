"""Chargement commun : donnees, index des trades par seance, fenetres par periode."""
import numpy as np
import sim

SCR = "/tmp/claude-0/-home-user-scalping-telegram-bot/73d2fc28-0760-5668-987b-2a927564efe7/scratchpad"
D = sim.charger(f"{SCR}/risque/nq.csv", f"{SCR}/audit/c2q1.txt", cache=f"{SCR}/machine6_cache.npz")
J = D["jours"]
nj = len(J)
td = D["t_jour"]
jt_debut = np.searchsorted(td, np.arange(nj), "left").astype(np.int64)
jt_fin = np.searchsorted(td, np.arange(nj), "right").astype(np.int64)
premier = td.min()
annee = np.array([int(j[:4]) for j in J])
def debuts(a, b, nseances=8):
    i = np.where((annee >= a) & (annee <= b) & (np.arange(nj) >= premier))[0]
    return i[i + nseances <= nj].astype(np.int64)
ARGS = (D["O"], D["H"], D["L"], D["C"], jt_debut, jt_fin, D["t_sens"], D["t_me"], D["t_mx"], D["t_e"], D["t_x"], D["t_w"], D["t_niv"])

def prm(T=4, L=1000, G=0, S=0, P=0, B=0, R=0, N=0, Jr=0, O=0, pess=0, gl=0.0, eod=0, pref=28500.0, GC=0):
    return np.array([T, L, G, S, P, B, R, N, Jr, O, pess, gl, eod, pref, GC], float)

def issues(p, deb, pris=None, nseances=8, solde0=50000.0, haut0=51500.0, objectif=53000.0):
    if pris is None:
        pris = np.ones(len(td), np.bool_)
    r, marge = sim.lot(deb, nseances, p, solde0, haut0, *ARGS, pris, objectif, 2500.0, 50100.0)
    ok = r != 9
    r, marge = r[ok], marge[ok]
    vivants = r == 0
    bloques = (vivants & (marge < 300)).sum() / max(1, vivants.sum()) * 100
    return (r == 1).mean() * 100, (r == -1).mean() * 100, (r == 0).mean() * 100, len(r), bloques
