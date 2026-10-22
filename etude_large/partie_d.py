#!/usr/bin/env python3
"""etude_large/README.md, partie D (regles fixees le 22 octobre 2026, avant tout calcul) : les challenges 50K.
D1 : plafond theorique (seances tirees au hasard, loi normale, 26 pas par seance, Sharpe annuel 0 a 3, meilleur
ecart-type quotidien de 100 a 1 500 $).
D2 : la zone du bot (V1 sans filtre, pas de zone les jours de la Fed), minute par minute sur le NQ 2012 - 2026 au niveau
de prix du 20 octobre 2026, 1,5 point de frais par aller-retour ; taille 1 a 10 MNQ avec arret a l'objectif + 50 $ ;
pour Bulenox aussi la version 30 jours (4 MNQ, 6 MNQ les 5 dernieres seances). Choix sur les departs 2012 - 2021,
verification sur 2023 - 2026.
Moteur : plancher = plus haut de fin de journee - perte max, bloque au niveau de blocage ; touche si le compte passe
dessous pendant la seance ; limite du jour : la seance s'arrete a -limite ; regle du meilleur jour : valide seulement si
le meilleur jour <= part x gain total ; sans delai, 126 seances au plus.

Lancer : python3 etude_large/partie_d.py (numba, numpy, pandas ; variable KB comme delta_mesures). Ecrit
resultats_d.txt."""
import os
import sys
import tempfile
from math import ceil
from pathlib import Path

sys.dont_write_bytecode = True
os.environ.setdefault("NUMBA_CACHE_DIR", str(Path(tempfile.gettempdir()) / "numba_etude_large"))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from numba import njit  # noqa: E402

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.path.insert(0, str(RACINE / "delta_mesures"))
import etude as DM  # noqa: E402
sys.path.insert(0, str(DM.KB / "fonds"))
import fomc  # noqa: E402

# nom : objectif, perte max, blocage, limite du jour (0 = aucune), seances max, meilleur jour (0 = aucune regle),
#       prix une fois, prix par mois, activation a la reussite, bots
FIRMES = {
    "Bulenox Legacy 50K opt. 2": (3000, 2500, 100, 1100, 22, 0.0, 19.25, 0.0, 148.0, "permis"),
    "Topstep 50K": (3000, 2000, 0, 1000, 126, 0.5, 0.0, 49.0, 149.0, "Combine oui"),
    "Tradeify Select 50K": (3000, 2000, 100, 0, 126, 0.4, 0.0, 159.0, 0.0, "sous conditions"),
    "Lucid Flex 50K": (3000, 2000, 100, 0, 126, 0.5, 140.0, 0.0, 0.0, "permis"),
    "MyFundedFutures 50K": (3000, 2000, 100, 0, 126, 0.5, 0.0, 125.0, 0.0, "permis, supervise"),
    "Phidias Fundamental 50K": (4000, 2500, 100, 0, 126, 0.0, 116.0, 0.0, 149.0, "?"),
}
SHARPES = [0.0, 1.0, 2.0, 3.0]
SIGMAS = np.arange(100.0, 1501.0, 100.0)
TIRAGES, PAS_JOUR = 10000, 26
TAILLES = list(range(1, 11))
MARGE_ARRET = 50.0
PERDUS_MAX = 0.35
DEBUT, FIN_CHOIX, DEBUT_VERIF = "2012-01-01", "2021-12-31", "2023-01-01"
REF_VAGUE13 = 0.49              # vague13/README.md : D sans filtre, Legacy, achats 2023-2026


@njit(cache=True)
def defi(chemins, debut, q, q_fin, n_fin, obj, dd, bloc, dll, nmax, part, arret):
    """Un challenge depuis la seance debut. chemins : (seances, pas) gain cumule de la seance pour 1 unite.
    Retour : (issue 1 valide / -1 perdu / 0 expire, seances jouees)."""
    bal, haut, meilleur = 0.0, 0.0, 0.0
    n = chemins.shape[0]
    for k in range(nmax):
        d = debut + k
        if d >= n:
            return 0, k
        taille = q_fin if nmax - k <= n_fin else q
        plancher = min(haut - dd, bloc)
        jour = 0.0
        for s in range(chemins.shape[1]):
            g = taille * chemins[d, s]
            eq = bal + g
            if eq <= plancher:
                return -1, k + 1
            jour = g
            if dll > 0 and g <= -dll:
                jour = -dll
                break
            if arret and eq >= obj + MARGE_ARRET:
                tot = eq
                if part <= 0 or (max(meilleur, g) <= part * tot):
                    break
        bal += jour
        if jour > meilleur:
            meilleur = jour
        if bal > haut:
            haut = bal
        if bal >= obj and (part <= 0 or meilleur <= part * bal):
            return 1, k + 1
    return 0, nmax


@njit(cache=True)
def tous_les_departs(chemins, departs, q, q_fin, n_fin, obj, dd, bloc, dll, nmax, part, arret):
    iss = np.zeros(len(departs), np.int64)
    nb = np.zeros(len(departs), np.int64)
    for i in range(len(departs)):
        iss[i], nb[i] = defi(chemins, departs[i], q, q_fin, n_fin, obj, dd, bloc, dll, nmax, part, arret)
    return iss, nb


@njit(cache=True)
def hasard(mu, sigma, nmax, tirages, pas, obj, dd, bloc, dll, part, graine):
    """D1 : chaque tirage a ses propres seances (loi normale, pas pas par seance)."""
    np.random.seed(graine)
    ok = 0
    perdu = 0
    nb = 0.0
    ch = np.zeros((nmax, pas))
    for t in range(tirages):
        for d in range(nmax):
            c = 0.0
            for s in range(pas):
                c += mu / pas + sigma / np.sqrt(pas) * np.random.normal()
                ch[d, s] = c
        r, k = defi(ch, 0, 1.0, 1.0, 0, obj, dd, bloc, dll, nmax, part, True)
        if r == 1:
            ok += 1
            nb += k
        elif r == -1:
            perdu += 1
    return ok / tirages, perdu / tirages, nb / max(ok, 1)


def chemins_zone():
    """Gain cumule minute par minute de la zone du bot pour 1 MNQ, en $, au niveau de prix du 20 octobre 2026, frais
    deduits a l'entree ; 0 les jours de la Fed et les seances sans trade."""
    rech = pd.read_csv(DM.RECHERCHE)
    robot = pd.read_csv(DM.ROBOT)
    bars = pd.concat([rech, robot[robot["t"] > rech["t"].iloc[-1]]], ignore_index=True)
    z = DM.preparer(bars)
    tr = DM.trades_zone(z, DEBUT, DM.FIN)
    fed = set(pd.DatetimeIndex(fomc.annonces()))
    jours = pd.DatetimeIndex([z["jours"][i] for i in z["jouables"]])
    jours = jours[(jours >= DEBUT) & (jours <= DM.FIN)]
    idx = {j: i for i, j in enumerate(z["jours"])}
    ref = float(z["C"][idx[pd.Timestamp(DM.FIN)], DM.N - 1])
    ch = np.zeros((len(jours), DM.N))
    pos = {j: k for k, j in enumerate(jours)}
    for j, g in tr.groupby("jour"):
        if j in fed or j not in pos:
            continue
        C = z["C"][idx[j]]
        f = ref / C[0]
        c = np.zeros(DM.N)
        for _, t in g.iterrows():
            me, ms, s, pe = int(t["minute_entree"]), int(t["minute_sortie"]), int(t["sens"]), float(t["prix_entree"])
            c[me:ms] += s * (C[me:ms] - pe) * f
            c[ms:] += s * (float(t["prix_sortie"]) - pe) * f
            c[me:] -= DM.COUT
        ch[pos[j]] = c * DM.RB.PT
    return jours, ch


def resume(iss, nb, f, firme_couts, nmax):
    once, mois, act = firme_couts
    v = (iss == 1).mean()
    p = (iss == -1).mean()
    e = (iss == 0).mean()
    frais = once + mois * np.ceil(np.maximum(nb, 1) / 21.0)
    cout = frais.mean() / v + act if v > 0 else np.inf
    med = float(np.median(nb[iss == 1])) if v > 0 else float("nan")
    return v, p, e, med, cout


def main():
    L = ["Etude large, partie D (etude_large/README.md, regles fixees le 22 octobre 2026 avant tout calcul)",
         "Regles des firmes : sites d'avis d'octobre 2026, a confirmer au panier (README).", ""]
    # D1
    L.append("D1 : plafond theorique (meilleur ecart-type quotidien pour chaque compte ; valide / perdu, seances "
             "medianes pour valider)")
    L.append("  compte                        " + "".join(f"   Sharpe {s:.0f}          " for s in SHARPES))
    for nom, (obj, dd, bloc, dll, nmax, part, *_ ) in FIRMES.items():
        cases = []
        for S in SHARPES:
            best = None
            for sg in SIGMAS:
                mu = S / np.sqrt(252) * sg
                v, p, n = hasard(mu, sg, nmax, TIRAGES, PAS_JOUR, float(obj), float(dd), float(bloc), float(dll),
                                 part, 7)
                if best is None or v > best[0]:
                    best = (v, p, n, sg)
            cases.append(f"{best[0] * 100:4.0f} % / {best[1] * 100:3.0f} % ({best[3]:4.0f} $)  ")
        L.append(f"  {nom:<30}" + "".join(cases))
    L.append("  (entre parentheses : l'ecart-type quotidien qui valide le plus souvent)")
    L.append("")
    # D2
    jours, ch = chemins_zone()
    an = jours.year
    choix = np.where((jours >= DEBUT) & (jours <= FIN_CHOIX))[0]
    verif = np.where(jours >= DEBUT_VERIF)[0]
    jour_pnl = ch[:, -1]
    L.append(f"D2 : la zone du bot, {len(jours)} seances {jours[0].date()} - {jours[-1].date()} ; 1 MNQ : "
             f"{jour_pnl.sum():+,.0f} $ au niveau d'aujourd'hui, Sharpe {jour_pnl.mean() / jour_pnl.std() * np.sqrt(252):.2f}, "
             f"ecart-type quotidien {jour_pnl.std():.0f} $")
    L.append("")
    lignes = []
    for nom, (obj, dd, bloc, dll, nmax, part, once, mois, act, bots) in FIRMES.items():
        # departs dont le challenge peut aller a son terme dans les donnees
        ok_c = choix[choix + nmax <= len(jours)]
        ok_v = verif[verif + nmax <= len(jours)]
        essais = [(f"{q} MNQ", q, q, 0) for q in TAILLES]
        if nom.startswith("Bulenox"):
            essais.append(("4 puis 6 MNQ (version 30 jours)", 4, 6, 5))
        res = []
        for lab, q, qf, nf in essais:
            a = tous_les_departs(ch, ok_c, float(q), float(qf), nf, float(obj), float(dd), float(bloc), float(dll),
                                 nmax, part, True)
            b = tous_les_departs(ch, ok_v, float(q), float(qf), nf, float(obj), float(dd), float(bloc), float(dll),
                                 nmax, part, True)
            res.append((lab, resume(*a, None, (once, mois, act), nmax), resume(*b, None, (once, mois, act), nmax)))
        admissibles = [r for r in res if r[1][1] <= PERDUS_MAX and not r[0].startswith("4 puis")]
        retenue = max(admissibles, key=lambda r: r[1][0]) if admissibles else None
        L.append(f"{nom} (bots : {bots}) : {len(ok_c)} departs de choix, {len(ok_v)} de verification")
        L.append("  taille                            choix : valide perdu expire | verification : valide perdu expire  "
                 "seances  cout par validation")
        for lab, rc, rv in res:
            mark = " <- retenue" if retenue and lab == retenue[0] else ""
            L.append(f"  {lab:<32} {rc[0] * 100:6.1f} {rc[1] * 100:5.1f} {rc[2] * 100:6.1f} | {rv[0] * 100:6.1f} "
                     f"{rv[1] * 100:5.1f} {rv[2] * 100:6.1f}  {rv[3]:7.0f}  {rv[4]:10,.0f} ${mark}")
        if retenue:
            lignes.append((nom, bots, retenue))
        else:
            L.append("  aucune taille ne perd au plus 35 % des challenges sur le choix")
        if nom.startswith("Bulenox"):
            v = [r for r in res if r[0].startswith("4 puis")][0][2][0]
            L.append(f"  CONTROLE : version 30 jours sur les departs 2023 - 2026 : {v * 100:.1f} % valides ; vague 13 "
                     f"(moteur exact, sans filtre) {REF_VAGUE13 * 100:.0f} % -> "
                     f"{'conforme (+-5 points)' if abs(v - REF_VAGUE13) <= 0.05 else 'ECART'}")
        L.append("")
    L.append("CLASSEMENT (verification 2023 - 2026, taille choisie sur 2012 - 2021) : cout moyen d'un challenge valide")
    for nom, bots, r in sorted(lignes, key=lambda x: x[2][2][4]):
        L.append(f"  {nom:<26} {r[0]:<7} valide {r[2][0] * 100:5.1f} %, perdu {r[2][1] * 100:5.1f} %, "
                 f"{r[2][4]:8,.0f} $ par validation (bots : {bots})")
    (ICI / "resultats_d.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
