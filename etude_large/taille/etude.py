#!/usr/bin/env python3
"""etude_large/taille/README.md (regles fixees le 22 octobre 2026, avant tout calcul) : taille de la zone selon l'etat
du compte (solde, plus haut de fin de journee, seances restantes), par programmation dynamique sur les seances
2012 - 2021, evaluee sur les vraies suites de seances 2012 - 2021 (information) et 2023 - 2026 (decision), Bulenox et
Lucid Flex. Moteur d'une seance : celui de partie_d.defi (plancher au plus bas de la minute, limite du jour, arret a
l'objectif + 50 $ au plus haut de la minute).

Lancer : python3 etude_large/taille/etude.py [solde plancher seances] (numba, numpy, pandas ; variable KB comme
delta_mesures). Les trois nombres optionnels (en $ par rapport a 50 000 $, et seances restantes) donnent la chance de
valider et la taille conseillee depuis cette situation chez Bulenox. Ecrit resultats.txt."""
import os
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
os.environ.setdefault("NUMBA_CACHE_DIR", str(Path(tempfile.gettempdir()) / "numba_etude_large"))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from numba import njit  # noqa: E402

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent))
import partie_d as PD  # noqa: E402

PAS = 50.0
TAILLES = np.arange(0, 7)
COMPTES = {  # nom : objectif, perte max, blocage, limite du jour, seances, meilleur jour (evaluation), delai de partie_d
    "Bulenox Legacy 50K opt. 2": (3000.0, 2500.0, 100.0, 1100.0, 21, 0.0, -30),
    "Lucid Flex 50K": (3000.0, 2000.0, 100.0, 0.0, 126, 0.5, 126),
}
CIBLE = PD.MARGE_ARRET


@njit(cache=True)
def premier(arr, seuil, croissant):
    """Premier indice ou arr (monotone) atteint seuil : arr >= seuil (croissant) ou arr <= seuil (decroissant) ;
    len(arr) si jamais."""
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        if (arr[mid] >= seuil) if croissant else (arr[mid] <= seuil):
            hi = mid
        else:
            lo = mid + 1
    return lo


@njit(cache=True)
def seance(rmin, rmax, clo_fin, q, b, f, obj, dll):
    """Une seance a q MNQ depuis le solde b et le plancher f, comme partie_d.defi : -1 perdu, 1 objectif atteint dans
    la seance, 0 sinon ; et le gain de la seance. Ordre a une meme minute : plancher, limite du jour, objectif."""
    if q == 0:
        return 0, 0.0
    n = len(rmin)
    tf = premier(rmin, (f - b) / q, False)
    td = premier(rmin, -dll / q, False) if dll > 0 else n
    tu = premier(rmax, (obj + CIBLE - b) / q, True)
    t = min(tf, td, tu)
    if t == n:
        return 0, q * clo_fin
    if tf == t:
        return -1, 0.0
    if td == t:
        return 0, -dll
    return 1, obj + CIBLE - b


@njit(cache=True)
def transitions(rmin, rmax, clo_fin, bgrid, hgrid, obj, dd, bloc, dll):
    """Pour chaque etat (solde, plus haut) et chaque taille : probabilite de perdre, de valider, et loi de l'etat du
    lendemain (indices compresses)."""
    nb, nh, nj = len(bgrid), len(hgrid), len(clo_fin)
    ns = nb * nh
    nq = 7
    p_perdu = np.zeros((ns, nq))
    p_valide = np.zeros((ns, nq))
    debut = np.zeros(ns * nq + 1, np.int64)
    cible_idx = np.empty(ns * nq * 64, np.int64)
    cible_p = np.empty(ns * nq * 64)
    pos = 0
    tmp = np.zeros(ns)
    for ib in range(nb):
        for ih in range(nh):
            s = ib * nh + ih
            b, h = bgrid[ib], hgrid[ih]
            f = min(h - dd, bloc)
            for q in range(nq):
                k = s * nq + q
                debut[k] = pos
                if b <= f:
                    p_perdu[s, q] = 1.0
                    continue
                touches = np.empty(nj, np.int64)
                nt = 0
                for j in range(nj):
                    r, g = seance(rmin[j], rmax[j], clo_fin[j], q, b, f, obj, dll)
                    if r == -1:
                        p_perdu[s, q] += 1.0 / nj
                        continue
                    b2 = b + g
                    if r == 1 or b2 >= obj:
                        p_valide[s, q] += 1.0 / nj
                        continue
                    h2 = min(max(h, b2), hgrid[nh - 1])
                    jb = int(round((b2 - bgrid[0]) / PAS))
                    jb = min(max(jb, 0), nb - 1)
                    jh = int(round((h2 - hgrid[0]) / PAS))
                    jh = min(max(jh, 0), nh - 1)
                    i2 = jb * nh + jh
                    if tmp[i2] == 0.0:
                        touches[nt] = i2
                        nt += 1
                    tmp[i2] += 1.0 / nj
                if pos + nt > len(cible_idx):
                    nouv = max(2 * len(cible_idx), pos + nt)
                    a = np.empty(nouv, np.int64)
                    a[:pos] = cible_idx[:pos]
                    cible_idx = a
                    c = np.empty(nouv)
                    c[:pos] = cible_p[:pos]
                    cible_p = c
                for t in range(nt):
                    cible_idx[pos] = touches[t]
                    cible_p[pos] = tmp[touches[t]]
                    tmp[touches[t]] = 0.0
                    pos += 1
    debut[ns * nq] = pos
    return p_perdu, p_valide, debut, cible_idx[:pos], cible_p[:pos]


@njit(cache=True)
def resoudre(p_perdu, p_valide, debut, cible_idx, cible_p, nmax):
    """V[n, s] : meilleure chance de valider avec n seances restantes ; Q[n, s] : taille qui l'atteint."""
    ns, nq = p_perdu.shape
    V = np.zeros((nmax + 1, ns))
    Q = np.zeros((nmax + 1, ns), np.int64)
    for n in range(1, nmax + 1):
        for s in range(ns):
            best, bq = -1.0, 0
            for q in range(nq):
                k = s * nq + q
                v = p_valide[s, q]
                for t in range(debut[k], debut[k + 1]):
                    v += cible_p[t] * V[n - 1, cible_idx[t]]
                if q == 0:
                    v = V[n - 1, s]
                if v > best + 1e-12:
                    best, bq = v, q
            V[n, s] = best
            Q[n, s] = bq
    return V, Q


@njit(cache=True)
def defi_politique(clo, bas, haut, debut, nmax, Q, bgrid, hgrid, obj, dd, bloc, dll, part):
    """Comme partie_d.defi, la taille de chaque seance lue dans la politique Q[seances restantes, etat]."""
    bal, sommet, meilleur = 0.0, 0.0, 0.0
    n, nh = clo.shape[0], len(hgrid)
    cible = obj + CIBLE
    for k in range(nmax):
        d = debut + k
        if d >= n:
            return 0, k
        jb = min(max(int(round((bal - bgrid[0]) / PAS)), 0), len(bgrid) - 1)
        jh = min(max(int(round((min(sommet, hgrid[nh - 1]) - hgrid[0]) / PAS)), 0), nh - 1)
        reste = min(nmax - k, Q.shape[0] - 1)
        taille = Q[reste, jb * nh + jh]
        plancher = min(sommet - dd, bloc)
        jour = taille * clo[d, clo.shape[1] - 1]
        for s in range(clo.shape[1]):
            if bal + taille * bas[d, s] <= plancher:
                return -1, k + 1
            if dll > 0 and taille * bas[d, s] <= -dll:
                jour = -dll
                break
            if bal + taille * haut[d, s] >= cible:
                g = cible - bal
                if part <= 0 or max(meilleur, g) <= part * cible:
                    jour = g
                    break
        bal += jour
        if jour > meilleur:
            meilleur = jour
        if bal > sommet:
            sommet = bal
        if bal >= obj and (part <= 0 or meilleur <= part * bal):
            return 1, k + 1
    return 0, nmax


def taux(iss):
    return (iss == 1).mean() * 100, (iss == -1).mean() * 100, (iss == 0).mean() * 100


def main():
    jours, clo, bas, haut = PD.chemins_zone()
    rmin = np.minimum.accumulate(bas, axis=1)
    rmax = np.maximum.accumulate(haut, axis=1)
    fin = clo[:, -1]
    choix = (jours >= PD.DEBUT) & (jours <= PD.FIN_CHOIX)
    L = ["Vague taille optimale (etude_large/taille/README.md, regles fixees le 22 octobre 2026 avant tout calcul)",
         f"Seances de la zone (1 MNQ, prix d'aujourd'hui, jours de la Fed a 0) : {len(jours)} ; politique calculee sur "
         f"les {int(choix.sum())} seances 2012 - 2021 seulement.", ""]
    situation = [float(x) for x in sys.argv[1:4]] if len(sys.argv) >= 4 else None
    for nom, (obj, dd, bloc, dll, nmax, part, delai) in COMPTES.items():
        bgrid = np.arange(-dd, obj + CIBLE + PAS / 2, PAS)
        hgrid = np.arange(0.0, dd + bloc + PAS / 2, PAS)
        tr = transitions(rmin[choix], rmax[choix], fin[choix], bgrid, hgrid, obj, dd, bloc, dll)
        nm = nmax + 1 if nmax < 100 else nmax          # Bulenox : une seance de marge (delais reels de 20 a 22)
        V, Q = resoudre(*tr, nm)
        s0 = int(round((0 - bgrid[0]) / PAS)) * len(hgrid) + 0
        L.append(f"{nom} : chance de valider depuis un compte neuf selon la politique (tirages 2012 - 2021) : "
                 f"{V[nmax, s0] * 100:.1f} % ; taille du premier jour : {Q[nmax, s0]} MNQ")
        L.append("  departs reels    | politique : valide perdu expire | meilleure taille fixe   | version actuelle")
        decision = []
        for lab, d0, d1 in (("2012 - 2021", PD.DEBUT, PD.FIN_CHOIX), ("2023 - 2026", PD.DEBUT_VERIF, "2026-12-31")):
            dep = np.where((jours >= d0) & (jours <= d1))[0]
            lim = PD.limites_depart(jours, dep, delai)
            ok = dep + lim < len(jours)
            dep, lim = dep[ok], lim[ok]
            pol = np.array([defi_politique(clo, bas, haut, d, l, Q, bgrid, hgrid, obj, dd, bloc, dll, part)[0]
                            for d, l in zip(dep, lim)])
            fixes = {}
            for q in range(1, 7):
                a = PD.tous_les_departs(clo, bas, haut, dep, lim, float(q), float(q), 0, obj, dd, bloc, dll, part, True)[0]
                fixes[q] = taux(a)
            qbest = max(fixes, key=lambda q: fixes[q][0])
            act = None
            if nom.startswith("Bulenox"):
                a = PD.tous_les_departs(clo, bas, haut, dep, lim, 4.0, 6.0, 5, obj, dd, bloc, dll, part, True)[0]
                act = taux(a)
            tp = taux(pol)
            L.append(f"  {lab} ({len(dep)}) | {tp[0]:5.1f} {tp[1]:5.1f} {tp[2]:6.1f}       | {qbest} MNQ {fixes[qbest][0]:5.1f} "
                     f"{fixes[qbest][1]:5.1f} {fixes[qbest][2]:5.1f} | " + (f"{act[0]:5.1f} {act[1]:5.1f} {act[2]:5.1f}" if act else "-"))
            L.append("     tailles fixes (valide / perdu) : " + ", ".join(f"{q} MNQ {fixes[q][0]:.0f}/{fixes[q][1]:.0f}"
                                                                    for q in range(1, 7)))
            if lab.startswith("2023"):
                ref = fixes[qbest]
                if act and act[0] > ref[0]:
                    ref = act
                decision = (tp[0] >= ref[0] + 3 and tp[1] <= ref[1] + 3, tp, ref)
        ok, tp, ref = decision
        L.append(f"  DECISION : politique {'RETENUE' if ok else 'NON RETENUE'} (verification : {tp[0]:.1f} % valides / "
                 f"{tp[1]:.1f} % perdus contre {ref[0]:.1f} / {ref[1]:.1f} pour la meilleure reference)")
        if nom.startswith("Bulenox"):
            L.append("\n  Table de la politique (Bulenox) : taille en MNQ selon le solde (lignes, $ au-dessus de 50 000) et le "
                     "plancher (colonnes, $ par rapport a 50 000), pour quelques nombres de seances restantes :")
            soldes = np.arange(-2000, 3000, 250.0)
            planchers = np.arange(-2500, 101, 300.0)
            for n in (21, 15, 10, 5, 2):
                L.append(f"   {n} seances restantes ; plancher : " + " ".join(f"{p:+6.0f}" for p in planchers))
                for b in soldes:
                    cases = []
                    for p in planchers:
                        h = min(p + dd, dd + bloc) if p < bloc else dd + bloc
                        if b <= p or (p < bloc and b > h):
                            cases.append("     .")
                            continue
                        jb = int(round((b - bgrid[0]) / PAS))
                        jh = int(round((min(h, hgrid[-1]) - hgrid[0]) / PAS))
                        cases.append(f"{Q[n, jb * len(hgrid) + jh]:6d}")
                    L.append(f"   solde {b:+6.0f}                     " + " ".join(cases))
            if situation:
                b, p, n = situation
                h = min(p + dd, dd + bloc) if p < bloc else dd + bloc
                jb = int(round((b - bgrid[0]) / PAS))
                jh = int(round((min(h, hgrid[-1]) - hgrid[0]) / PAS))
                s = jb * len(hgrid) + jh
                n = int(min(n, nm))
                L.append(f"\n  SITUATION DONNEE : solde {b:+.0f} $, plancher {p:+.0f} $, {n} seances : chance de valider "
                         f"{V[n, s] * 100:.1f} % avec la politique ; taille conseillee aujourd'hui : {Q[n, s]} MNQ")
        L.append("")
    (ICI / "resultats.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
