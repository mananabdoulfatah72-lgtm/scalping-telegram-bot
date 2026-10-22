#!/usr/bin/env python3
"""etude_large/README.md, partie D (regles fixees le 22 octobre 2026, avant tout calcul) : les challenges 50K.
D1 : plafond theorique (seances tirees au hasard, loi normale, 26 pas par seance, Sharpe annuel 0 a 3, meilleur
ecart-type quotidien de 100 a 1 500 $).
D2 : la zone du bot (V1 sans filtre, pas de zone les jours de la Fed), minute par minute sur le NQ 2012 - 2026 au niveau
de prix du 20 octobre 2026, 1,5 point de frais par aller-retour ; taille 1 a 10 MNQ avec arret a l'objectif + 50 $ ;
pour Bulenox aussi la version 30 jours (4 MNQ, 6 MNQ les 5 dernieres seances). Choix sur les departs 2012 - 2021,
verification sur 2023 - 2026.
Moteur : plancher = plus haut de fin de journee - perte max, bloque au niveau de blocage ; touche si le compte passe
dessous pendant la seance (plus bas de chaque minute) ; limite du jour : la seance s'arrete a -limite (plus bas de la
minute) ; arret a l'objectif + 50 $ sur le plus haut de la minute ; regle du meilleur jour : valide seulement si le
meilleur jour <= part x gain total ; Bulenox : 30 jours calendaires ; sans delai, 126 seances au plus.
Corrections de la contre-revue du 22 octobre 2026 : plus hauts et plus bas des minutes (le README les annoncait, la
premiere version ne lisait que les clotures), vrai delai de 30 jours calendaires (au lieu de 22 seances), Tradeify a
159 $ une fois comme dans le README (au lieu de 159 $ par mois), grille d'ecart-type de D1 elargie a 5 000 $ et 78 pas
par seance.

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
    "Bulenox Legacy 50K opt. 2": (3000, 2500, 100, 1100, -30, 0.0, 19.25, 0.0, 148.0, "permis"),   # -30 : jours
    "Topstep 50K": (3000, 2000, 0, 1000, 126, 0.5, 0.0, 49.0, 149.0, "Combine oui"),
    "Tradeify Select 50K": (3000, 2000, 100, 0, 126, 0.4, 159.0, 0.0, 0.0, "sous conditions"),
    "Lucid Flex 50K": (3000, 2000, 100, 0, 126, 0.5, 140.0, 0.0, 0.0, "permis"),
    "MyFundedFutures 50K": (3000, 2000, 100, 0, 126, 0.5, 0.0, 125.0, 0.0, "permis, supervise"),
    "Phidias Fundamental 50K": (4000, 2500, 100, 0, 126, 0.0, 116.0, 0.0, 149.0, "?"),
}
SHARPES = [0.0, 1.0, 2.0, 3.0]
SIGMAS = np.r_[np.arange(100.0, 1501.0, 100.0), 2000.0, 3000.0, 5000.0]
TIRAGES, PAS_JOUR = 5000, 78
SEANCES_30_JOURS = 21           # mediane des seances dans 30 jours calendaires (D1)
TAILLES = list(range(1, 11))
MARGE_ARRET = 50.0
PERDUS_MAX = 0.35
DEBUT, FIN_CHOIX, DEBUT_VERIF = "2012-01-01", "2021-12-31", "2023-01-01"
REF_VAGUE13 = 0.49              # vague13/README.md : D sans filtre, Legacy, achats 2023-2026
REF_README = (0.53, 0.55)       # chiffres cites par le README (vague 13 AVEC le filtre simule : reference erronee)


@njit(cache=True)
def defi(clo, bas, haut, debut, q, q_fin, n_fin, obj, dd, bloc, dll, nmax, part, arret):
    """Un challenge depuis la seance debut, nmax seances au plus. clo, bas, haut : (seances, pas) gain cumule de la
    seance pour 1 unite, a la cloture, au plus bas et au plus haut de chaque pas.
    Retour : (issue 1 valide / -1 perdu / 0 expire, seances jouees)."""
    bal, sommet, meilleur = 0.0, 0.0, 0.0
    n = clo.shape[0]
    cible = obj + MARGE_ARRET
    for k in range(nmax):
        d = debut + k
        if d >= n:
            return 0, k
        taille = q_fin if nmax - k <= n_fin else q
        plancher = min(sommet - dd, bloc)
        jour = taille * clo[d, clo.shape[1] - 1]
        for s in range(clo.shape[1]):
            if bal + taille * bas[d, s] <= plancher:
                return -1, k + 1
            if dll > 0 and taille * bas[d, s] <= -dll:
                jour = -dll
                break
            if arret and bal + taille * haut[d, s] >= cible:
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


@njit(cache=True)
def tous_les_departs(clo, bas, haut, departs, limites, q, q_fin, n_fin, obj, dd, bloc, dll, part, arret):
    iss = np.zeros(len(departs), np.int64)
    nb = np.zeros(len(departs), np.int64)
    for i in range(len(departs)):
        iss[i], nb[i] = defi(clo, bas, haut, departs[i], q, q_fin, n_fin, obj, dd, bloc, dll, limites[i], part, arret)
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
        r, k = defi(ch, ch, ch, 0, 1.0, 1.0, 0, obj, dd, bloc, dll, nmax, part, True)
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
    _, _, Hm, Lm, _, _, _, _ = DM.RB.tableaux(bars)        # memes seances, memes minutes que z
    tr = DM.trades_zone(z, DEBUT, DM.FIN)
    fed = set(pd.DatetimeIndex(fomc.annonces()))
    jours = pd.DatetimeIndex([z["jours"][i] for i in z["jouables"]])
    jours = jours[(jours >= DEBUT) & (jours <= DM.FIN)]
    idx = {j: i for i, j in enumerate(z["jours"])}
    ref = float(z["C"][idx[pd.Timestamp(DM.FIN)], DM.N - 1])
    ch = np.zeros((len(jours), DM.N))
    bas = np.zeros((len(jours), DM.N))
    haut = np.zeros((len(jours), DM.N))
    pos = {j: k for k, j in enumerate(jours)}
    for j, g in tr.groupby("jour"):
        if j in fed or j not in pos:
            continue
        i = idx[j]
        C, H, L = z["C"][i], Hm[i], Lm[i]
        f = ref / C[0]
        c, contre, pour = np.zeros(DM.N), np.zeros(DM.N), np.zeros(DM.N)
        for _, t in g.iterrows():
            me, ms, s, pe = int(t["minute_entree"]), int(t["minute_sortie"]), int(t["sens"]), float(t["prix_entree"])
            c[me:ms] += s * (C[me:ms] - pe) * f
            c[ms:] += s * (float(t["prix_sortie"]) - pe) * f
            c[me:] -= DM.COUT
            # minutes me+1 .. ms : le trade est ouvert pendant la minute (entree a la cloture de me, sortie a celle de ms)
            w = slice(me + 1, ms + 1)
            contre[w] += ((C[w] - L[w]) if s > 0 else (H[w] - C[w])) * f
            pour[w] += ((H[w] - C[w]) if s > 0 else (C[w] - L[w])) * f
        k = pos[j]
        ch[k], bas[k], haut[k] = c * DM.RB.PT, (c - contre) * DM.RB.PT, (c + pour) * DM.RB.PT
    return jours, ch, bas, haut


def resume(iss, nb, f, firme_couts, nmax):
    once, mois, act = firme_couts
    v = (iss == 1).mean()
    p = (iss == -1).mean()
    e = (iss == 0).mean()
    frais = once + mois * np.ceil(np.maximum(nb, 1) / 21.0)
    cout = frais.mean() / v + act if v > 0 else np.inf
    med = float(np.median(nb[iss == 1])) if v > 0 else float("nan")
    return v, p, e, med, cout


def limites_depart(jours, departs, nmax):
    """Seances jouables par depart : nmax, ou pour un delai en jours (nmax < 0) les seances avant depart + |nmax| jours."""
    if nmax > 0:
        return np.full(len(departs), nmax, np.int64)
    fin = jours[departs] + pd.Timedelta(days=-nmax)
    return (np.searchsorted(jours.values, fin.values) - departs).astype(np.int64)


def main():
    L = ["Etude large, partie D (etude_large/README.md, regles fixees le 22 octobre 2026 avant tout calcul ; "
         "corrigee apres la contre-revue du 22 octobre, voir l'en-tete de partie_d.py)",
         "Regles et prix des firmes : sites d'avis d'octobre 2026, a confirmer au panier (README). Lucid 140 $ une fois "
         "(vague 6) et MyFundedFutures 125 $ par mois sont des hypotheses.", ""]
    # D1
    L.append("D1 : seances tirees au hasard (loi normale, 78 pas par seance) ; pour chaque compte et chaque Sharpe, "
             "l'ecart-type quotidien (100 a 5 000 $) qui valide le plus souvent : valide % / perdu % (ecart-type)")
    L.append("  compte                        " + "".join(f"  Sharpe {s_:.0f}                " for s_ in SHARPES))
    d1 = {}
    for nom, (obj, dd, bloc, dll, nmax, part, *_ ) in FIRMES.items():
        nm = SEANCES_30_JOURS if nmax < 0 else nmax
        cases = []
        for S in SHARPES:
            best = None
            for sg in SIGMAS:
                v, pp, n = hasard(S / np.sqrt(252) * sg, sg, nm, TIRAGES, PAS_JOUR, float(obj), float(dd), float(bloc),
                                  float(dll), part, 7)
                d1[(nom, S, sg)] = v
                if best is None or v > best[0]:
                    best = (v, pp, n, sg)
            cases.append(f"{best[0] * 100:3.0f} % / {best[1] * 100:3.0f} % ({best[3]:5.0f} $)   ")
        L.append(f"  {nom:<30}" + "".join(cases))
    b0 = "Bulenox Legacy 50K opt. 2"
    L.append(f"  Bulenox sans avantage (Sharpe 0) : {d1[(b0, 0.0, 1000.0)] * 100:.0f} % valides a 1 000 $ d'ecart-type, "
             f"{d1[(b0, 0.0, 2000.0)] * 100:.0f} % a 2 000 $, {d1[(b0, 0.0, 5000.0)] * 100:.0f} % a 5 000 $ : sur 30 jours, "
             "la chance de valider monte avec le risque meme sans aucun avantage.")
    L.append("")
    # D2
    jours, clo, bas, haut = chemins_zone()
    choix = np.where((jours >= DEBUT) & (jours <= FIN_CHOIX))[0]
    verif = np.where(jours >= DEBUT_VERIF)[0]
    jp = clo[:, -1]
    L.append(f"D2 : la zone du bot, {len(jours)} seances {jours[0].date()} - {jours[-1].date()} ; 1 MNQ : "
             f"{jp.sum():+,.0f} $ au niveau d'aujourd'hui, Sharpe {jp.mean() / jp.std() * np.sqrt(252):.2f}, "
             f"ecart-type quotidien {jp.std():.0f} $ (4 MNQ : {4 * jp.std():.0f} $)")
    L.append("Les departs se chevauchent et la verification couvre environ 3,8 ans : un ecart de moins de 10 points entre "
             "deux lignes n'est pas significatif, sauf s'il vient d'une regle differente sur les memes seances.")
    L.append("")
    lignes = []
    for nom, (obj, dd, bloc, dll, nmax, part, once, mois, act, bots) in FIRMES.items():
        lim_c, lim_v = limites_depart(jours, choix, nmax), limites_depart(jours, verif, nmax)
        okc, okv = choix + lim_c < len(jours), verif + lim_v < len(jours)
        dc, lc, dv, lv = choix[okc], lim_c[okc], verif[okv], lim_v[okv]
        essais = [(f"{q} MNQ", q, q, 0) for q in TAILLES]
        if nom.startswith("Bulenox"):
            essais.append(("4 puis 6 MNQ (version 30 jours)", 4, 6, 5))
        res = []
        for lab, q, qf, nf in essais:
            arg = (float(q), float(qf), nf, float(obj), float(dd), float(bloc), float(dll), part, True)
            a_ = tous_les_departs(clo, bas, haut, dc, lc, *arg)
            b_ = tous_les_departs(clo, bas, haut, dv, lv, *arg)
            res.append((lab, resume(*a_, None, (once, mois, act), nmax), resume(*b_, None, (once, mois, act), nmax), b_,
                        a_))
        admissibles = [r for r in res if r[1][1] <= PERDUS_MAX and not r[0].startswith("4 puis")]
        retenue = max(admissibles, key=lambda r: r[1][0]) if admissibles else None
        L.append(f"{nom} (bots : {bots}) : {len(dc)} departs de choix, {len(dv)} de verification")
        L.append("  taille                            choix : valide perdu expire | verification : valide perdu expire  "
                 "seances  cout par validation")
        for lab, rc, rv, _, _ in res:
            mark = " <- retenue" if retenue and lab == retenue[0] else ""
            L.append(f"  {lab:<32} {rc[0] * 100:6.0f} {rc[1] * 100:5.0f} {rc[2] * 100:6.0f} | {rv[0] * 100:6.0f} "
                     f"{rv[1] * 100:5.0f} {rv[2] * 100:6.0f}  {rv[3]:7.0f}  {rv[4]:10,.0f} ${mark}")
        if retenue:
            lignes.append((nom, bots, retenue))
            iss = retenue[3][0]
            ans = jours[dv].year
            par_an = ", ".join(f"{y} : {(iss[ans == y] == 1).mean() * 100:.0f} %" for y in sorted(set(ans)))
            issc = retenue[4][0]
            ansc = jours[dc].year
            taux = [(issc[ansc == y] == 1).mean() * 100 for y in sorted(set(ansc))]
            L.append(f"  retenue, valides par annee de depart : {par_an} ; choix 2012 - 2021 : de {min(taux):.0f} a "
                     f"{max(taux):.0f} % selon l'annee")
        else:
            L.append("  aucune taille ne perd au plus 35 % des challenges sur le choix")
        if nom.startswith("Bulenox"):
            r46 = [r for r in res if r[0].startswith("4 puis")][0]
            vc, vv = r46[1][0], r46[2][0]
            L.append(f"  CONTROLE fixe dans le README : 53 % (choix) et 55 % (verification) a +-5 points -> {vc * 100:.0f} % et "
                     f"{vv * 100:.0f} % : {'conforme' if abs(vc - REF_README[0]) <= 0.05 and abs(vv - REF_README[1]) <= 0.05 else 'ECHEC'}."
                     " Ces deux chiffres de la vague 13 comprennent le filtre delta simule (erreur du README) ;")
            L.append(f"  la reference comparable, sans filtre, est {REF_VAGUE13 * 100:.0f} % sur les achats 2023 - 2026 -> "
                     f"{vv * 100:.0f} % : {'conforme (+-5 points)' if abs(vv - REF_VAGUE13) <= 0.05 else 'ECART'}.")
        L.append("")
    L.append("CLASSEMENT (verification 2023 - 2026, taille choisie sur 2012 - 2021) : cout moyen d'un challenge valide")
    for nom, bots, r in sorted(lignes, key=lambda x: x[2][2][4]):
        L.append(f"  {nom:<26} {r[0]:<7} valide {r[2][0] * 100:3.0f} %, perdu {r[2][1] * 100:3.0f} %, "
                 f"{r[2][4]:6,.0f} $ par validation (bots : {bots})")
    (ICI / "resultats_d.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
