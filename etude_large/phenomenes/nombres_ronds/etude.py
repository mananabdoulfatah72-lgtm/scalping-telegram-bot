#!/usr/bin/env python3
"""etude_large/phenomenes/README.md, piste C (regles fixees le 22 octobre 2026, commit 929d05e, avant tout calcul) :
nombres ronds du NQ (Osler 2003). Premier franchissement du jour d'un niveau L = k x 100 (prix bruts du contrat du jour),
de 9 h 45 a 15 h 44 (N1) ou 15 h 29 (N2) ; 1 MNQ dans le sens du franchissement, sortie 15 (N1) ou 30 (N2) minutes plus
tard ; un trade a la fois ; pas les jours de la Fed. Test bilateral : si le gain brut moyen d'exploration est negatif,
le test devient contre le franchissement. Placebo : 99 grilles decalees (L = k x 100 + delta). Criteres communs 1 a 5
(source). Serie de decision : $ par seance pour 1 MNQ au prix du 20 octobre 2026.

Lancer : KB=<branche de recherche extraite> python3 etude_large/phenomenes/nombres_ronds/etude.py. Ecrit resultats.txt :
l'exploration d'abord (fichier ecrit et ferme), puis le coffre.
Interpretation fixee avant tout calcul (le README ne le dit pas) : un trade est ouvert jusqu'a sa minute de sortie
comprise ; un nouveau franchissement n'est pris qu'a partir de la minute suivante."""
import importlib.util
import os
import sys
import tempfile
from math import erf, sqrt
from pathlib import Path

sys.dont_write_bytecode = True
os.environ.setdefault("NUMBA_CACHE_DIR", str(Path(tempfile.gettempdir()) / "numba_etude_large"))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from numba import njit  # noqa: E402

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent.parent
sys.path.insert(0, str(RACINE / "delta_mesures"))
sys.path.insert(0, str(RACINE / "etude_large"))
import etude as DM  # noqa: E402
import partie_a as PA  # noqa: E402
import partie_d as PD  # noqa: E402
sys.path.insert(0, str(DM.KB / "fonds"))
import fomc  # noqa: E402

_s = importlib.util.spec_from_file_location("bruit_etude", RACINE / "etude_large" / "bruit" / "etude.py")
BR = importlib.util.module_from_spec(_s)
_s.loader.exec_module(BR)

N, PT = DM.N, DM.RB.PT
EXPLO = ("2011-01-01", "2022-12-30")
COFFRE = ("2023-01-03", DM.FIN)
TESTS = {"N1": (15, 374, 15), "N2": (15, 359, 30)}     # premiere minute, derniere minute d'evenement, duree
ES = DM.KB / "intraday" / "donnees" / "sp500_1min.csv.gz"
SORTIE = ICI / "resultats.txt"


@njit(cache=True)
def evenements(C, pas, delta, m0, m1, duree):
    """Trades d'une seance : (minute d'entree, sens, minute de sortie). Premier franchissement du jour d'un niveau
    k x pas + delta : a la minute m, la cloture depasse le plus haut des clotures d'avant et un niveau est dans
    [plus haut d'avant, C[m]) (achat) ; symetrique a la baisse. Un trade a la fois."""
    out = []
    haut, bas = C[0], C[0]
    libre = 0
    for m in range(1, N):
        h0, b0, p = haut, bas, C[m]
        if p > haut:
            haut = p
        if p < bas:
            bas = p
        if m < m0 or m > m1 or m < libre:
            continue
        sens = 0
        if p > h0:
            k = np.ceil((h0 - delta) / pas)          # plus petit niveau >= h0
            if k * pas + delta < p:
                sens = 1
        elif p < b0:
            k = np.floor((b0 - delta) / pas)         # plus grand niveau <= b0
            if k * pas + delta > p:
                sens = -1
        if sens != 0:
            out.append((m, sens, m + duree))
            libre = m + duree + 1
    return out


def trades(C, jours, idx, pas, delta, test, cout):
    m0, m1, duree = TESTS[test]
    L = []
    for i in idx:
        for me, s, ms in evenements(C[i], float(pas), float(delta), m0, m1, duree):
            L.append((jours[i], me, s, C[i, me], ms, C[i, ms]))
    tr = pd.DataFrame(L, columns=["jour", "minute_entree", "sens", "prix_entree", "minute_sortie", "prix_sortie"])
    tr["brut"] = tr["sens"] * (tr["prix_sortie"] - tr["prix_entree"])
    return tr


def usd(tr, ouv, ref, cout, signe):
    f = ref / ouv.reindex(tr["jour"]).values
    return (signe * tr["brut"].values * f - cout) * PT


def quotidien(tr, v, jours):
    if len(tr) == 0:
        return np.zeros(len(jours))
    return pd.Series(v, index=tr["jour"].values).groupby(level=0).sum().reindex(jours).fillna(0.0).values


def p_bilateral(t):
    return 1 - erf(abs(t) / sqrt(2))


def main():
    fed = set(pd.DatetimeIndex(fomc.annonces()))
    rech = pd.read_csv(DM.RECHERCHE)
    robot = pd.read_csv(DM.ROBOT)
    bars = pd.concat([rech, robot[robot["t"] > rech["t"].iloc[-1]]], ignore_index=True)
    jt, O, Hm, Lm, C, P, V, ech = DM.RB.tableaux(bars)
    complete = DM.RB.seances_completes(P)
    z = DM.preparer(bars)
    idx = [i for i in np.where(complete)[0] if jt[i] not in fed and jt[i] <= pd.Timestamp(DM.FIN)]
    jours = pd.DatetimeIndex([jt[i] for i in idx])
    ouv = pd.Series(C[:, 0], index=jt)
    ref = float(C[list(jt).index(pd.Timestamp(DM.FIN)), N - 1])
    e = (jours >= EXPLO[0]) & (jours <= EXPLO[1])
    c = (jours >= COFFRE[0]) & (jours <= COFFRE[1])
    # zone du bot (serie de decision), sur les memes seances
    tz = DM.trades_zone(z, "2011-01-01", DM.FIN)
    tz = tz[~tz["jour"].isin(fed)]
    fz = ref / ouv.reindex(tz["jour"]).values
    zone = quotidien(tz, (tz["sens"] * (tz["prix_sortie"] - tz["prix_entree"]) * fz - DM.COUT).values * PT, jours)
    L = ["Piste C : nombres ronds du NQ (etude_large/phenomenes/README.md, commit 929d05e, regles fixees avant tout calcul)",
         f"{len(jours)} seances completes hors jours de la Fed ({jours[0].date()} - {jours[-1].date()}) ; exploration "
         f"{int(e.sum())}, coffre {int(c.sum())} ; prix de reference {ref:.2f} ; prix bruts du contrat du jour.",
         "Interpretation fixee avant tout calcul : un trade est ouvert jusqu'a sa minute de sortie comprise.", ""]
    t1 = trades(C, jt, idx, 100, 0, "N1", 1.5)
    ans = t1["jour"].dt.year
    L.append("CONTROLE a) premiers franchissements pris (N1, un trade a la fois) par annee : "
             + ", ".join(f"{a} {n}" for a, n in ans.value_counts().sort_index().items()))
    # regard vers le futur : la decision a la minute m ne lit que C[0..m]
    rng = np.random.default_rng(1)
    chg = 0
    for i in rng.choice(idx, 200, replace=False):
        base = evenements(C[i], 100.0, 0.0, 15, 374, 15)
        for (me, s, ms) in base[:1]:
            Cb = C[i].copy()
            Cb[me + 1:] += rng.normal(0, 30, N - me - 1)
            alt = evenements(Cb, 100.0, 0.0, 15, 374, 15)
            chg += int(not alt or alt[0][:2] != (me, s))
    L.append(f"REGARD VERS LE FUTUR : 200 seances, prix brouilles apres le premier evenement : {chg} decision(s) changee(s) -> "
             f"{'aucun regard vers le futur' if chg == 0 else 'PROBLEME'}")
    L.append("")
    res = {}
    L.append("EXPLORATION 2011 - 2022 (coffre non ouvert)")
    for test in TESTS:
        tr = trades(C, jt, idx, 100, 0, test, 1.5)
        te_ = tr["jour"].between(*EXPLO).values
        signe = 1.0 if tr["brut"].values[te_].mean() >= 0 else -1.0
        s = quotidien(tr, usd(tr, ouv, ref, 1.5, signe), jours)
        s3 = quotidien(tr, usd(tr, ouv, ref, 3.0, signe), jours)
        te = PA.t_stat(s[e])
        # placebos : 99 grilles decalees, meme orientation
        tp_e, tp_c = [], []
        for d in range(1, 100):
            tq = trades(C, jt, idx, 100, d, test, 1.5)
            sq = quotidien(tq, usd(tq, ouv, ref, 1.5, signe), jours)
            tp_e.append(PA.t_stat(sq[e]))
            tp_c.append(PA.t_stat(sq[c]))
        rang_e = int((np.array(tp_e) < te).sum())
        corr = float(np.corrcoef(s[e], zone[e])[0, 1])
        res[test] = dict(tr=tr, s=s, s3=s3, signe=signe, te=te, tp_c=tp_c, rang_e=rang_e, corr=corr, te_=te_)
        L.append(f"  {test} ({'dans le sens' if signe > 0 else 'CONTRE le sens'} du franchissement) : {int(te_.sum())} trades, brut "
                 f"moyen {tr['brut'].values[te_].mean():+.2f} pt ; t net {te:+.2f} (p bilateral {p_bilateral(te):.4f}) ; "
                 f"t a 3 points de frais {PA.t_stat(s3[e]):+.2f} ; la grille ronde bat {rang_e} grilles decalees sur 99 ; "
                 f"correlation avec la zone {corr:+.2f}")
        brut_e = tr[te_]
        for lab, m in (("achats", brut_e["sens"] > 0), ("ventes", brut_e["sens"] < 0)):
            L.append(f"     controle c) {lab} : {int(m.sum())} trades, brut moyen {brut_e['brut'][m].mean():+.2f} pt")
        for lab, a, b in (("2011 - 2017", 2011, 2017), ("2018 - 2022", 2018, 2022)):
            m = brut_e["jour"].dt.year.between(a, b)
            L.append(f"     controle c) {lab} : {int(m.sum())} trades, brut moyen {brut_e['brut'][m].mean():+.2f} pt")
        hres = brut_e.groupby((brut_e["minute_entree"] + 570) // 60)["brut"].agg(["count", "mean"])
        L.append("     controle c) par heure (trades, brut moyen) : " + ", ".join(f"{h} h {int(r['count'])} {r['mean']:+.2f}"
                                                                         for h, r in hres.iterrows()))
    tn3 = trades(C, jt, idx, 500, 0, "N1", 1.5)
    m3 = tn3["jour"].between(*EXPLO).values
    L.append(f"  controle b) N3, niveaux de 500, 15 minutes : {int(m3.sum())} trades en exploration, brut moyen "
             f"{tn3['brut'].values[m3].mean():+.2f} pt")
    SORTIE.write_text("\n".join(L) + "\n")
    # ----------------------------------------------------------------------------- coffre, ouvert une seule fois
    L2 = ["", "COFFRE 2023 - 20 octobre 2026 (ouvert apres l'ecriture de l'exploration)"]
    jd, clo_z, bas_z, haut_z = PD.chemins_zone()
    dep = np.where(jd >= pd.Timestamp(PD.DEBUT_VERIF))[0]
    for test, r in res.items():
        s, tr = r["s"], r["tr"]
        tc = PA.t_stat(s[c])
        rang_c = int((np.array(r["tp_c"]) < tc).sum())
        w = zone[e].std() / s[e].std() if s[e].std() > 0 else 0.0
        comb = zone + w * s
        crit = {1: abs(r["te"]) >= 2.0,
                2: tc >= 1.5 and r["te"] > 0,
                3: r["rang_e"] >= 95 and rang_c >= 95,
                4: r["corr"] < 0.3 and PA.sharpe(comb[e]) > PA.sharpe(zone[e]) and PA.sharpe(comb[c]) > PA.sharpe(zone[c]),
                "3 points": PA.t_stat(r["s3"][e]) > 0 and PA.t_stat(r["s3"][c]) > 0}
        # challenges : zone + source a la meme taille, contre la zone seule a la taille du compte et a la meme exposition
        trs = tr[tr["jour"] >= pd.Timestamp(PD.DEBUT)].copy()
        trs["sens"] = (trs["sens"] * r["signe"]).astype(int)
        cs, bs, hs = BR.chemins(z, Hm, Lm, trs, jd, 1.5, PT, ref)
        lig, ok5 = [], False
        for firme, q in (("Lucid Flex 50K", 1.0), ("Bulenox Legacy 50K opt. 2", 3.0)):
            obj, dd, bloc, dll, nmax, part, *_ = PD.FIRMES[firme]
            lim = PD.limites_depart(jd, dep, nmax)
            okd = dep + lim < len(jd)
            def taux(cl, ba, ha, qq):
                a = PD.tous_les_departs(cl, ba, ha, dep[okd], lim[okd], qq, qq, 0, float(obj), float(dd), float(bloc),
                                        float(dll), part, True)[0]
                return (a == 1).mean() * 100, (a == -1).mean() * 100
            z1, z2, zs = taux(clo_z, bas_z, haut_z, q), taux(clo_z, bas_z, haut_z, 2 * q), \
                taux(clo_z + cs, bas_z + bs, np.maximum(haut_z + cs, clo_z + hs), q)
            passe = all(zs[0] >= ref_[0] + 2 and zs[1] <= ref_[1] + 3 for ref_ in (z1, z2))
            ok5 |= passe
            lig.append(f"{firme} : zone {q:.0f} MNQ {z1[0]:.1f}/{z1[1]:.1f}, zone {2 * q:.0f} MNQ {z2[0]:.1f}/{z2[1]:.1f}, "
                       f"zone + source {zs[0]:.1f}/{zs[1]:.1f} -> {'passe' if passe else 'non'}")
        crit[5] = ok5
        propre = all(crit[k] for k in (2, 3, 4, 5, "3 points"))
        r.update(tc=tc, propre=propre)
        L2.append(f"  {test} : t net coffre {tc:+.2f} ; la grille ronde bat {rang_c} grilles sur 99 au coffre ; Sharpe zone "
                  f"{PA.sharpe(zone[c]):+.2f} -> zone + source {PA.sharpe(comb[c]):+.2f} ; t a 3 points {PA.t_stat(r['s3'][c]):+.2f}")
        L2.append("     challenges (departs 2023 - 2026, valide / perdu) : " + " ; ".join(lig))
        L2.append("     criteres : " + ", ".join(f"{k} {'oui' if v else 'non'}" for k, v in crit.items())
                  + f" -> criteres propres {'PASSENT' if propre else 'echec'}")
        tcf = tr[tr["jour"] >= pd.Timestamp(COFFRE[0])]
        pire = tcf.loc[(tcf["brut"] * r["signe"]).idxmin()] if len(tcf) else None
        if pire is not None:
            L2.append(f"     controle e) pire trade du coffre : {pire['jour'].date()} {pire['minute_entree']} min, "
                      f"{r['signe'] * pire['brut']:+.2f} pt")
    # controle d) ES, niveaux de 50
    try:
        be = pd.read_csv(ES)
        je, Oe, He, Le, Ce, Pe, Ve, ee = DM.RB.tableaux(be)
        ce = DM.RB.seances_completes(Pe)
        ide = [i for i in np.where(ce)[0] if je[i] not in fed]
        jes = pd.DatetimeIndex([je[i] for i in ide])
        oue = pd.Series(Ce[:, 0], index=je)
        for test in TESTS:
            tr = trades(Ce, je, ide, 50, 0, test, 0.9)
            v = (res[test]["signe"] * tr["brut"].values / oue.reindex(tr["jour"]).values)
            d = quotidien(tr, v - 0.9 / oue.reindex(tr["jour"]).values, jes)
            ee_, cc_ = jes <= pd.Timestamp(EXPLO[1]), jes >= pd.Timestamp(COFFRE[0])
            L2.append(f"  controle d) ES niveaux de 50, {test} (meme orientation) : t net exploration {PA.t_stat(d[ee_]):+.2f}, "
                      f"coffre {PA.t_stat(d[cc_]):+.2f}")
    except Exception as exc:  # noqa: BLE001
        L2.append(f"  controle d) ES : non calcule ({exc})")
    with SORTIE.open("a") as f:
        f.write("\n".join(L2) + "\n")
    print("\n".join(L + L2))
    return {k: (r["te"], r["tc"], r["propre"]) for k, r in res.items()}


if __name__ == "__main__":
    print(main())
