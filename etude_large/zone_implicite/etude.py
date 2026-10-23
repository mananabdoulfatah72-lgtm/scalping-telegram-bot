#!/usr/bin/env python3
"""etude_large/zone_implicite/README.md (regles fixees le 23 octobre 2026, commit da634ef, avant tout calcul et avant
le telechargement du VXN). 5 tests : largeur de la zone tiree du VXN (I1 rapport, I2 pure, I3 elargir seulement) et
taille selon le VXN (T1 ciblage de volatilite, T2 plus gros quand ca bouge).

Deux temps, le coffre n'est ouvert qu'une fois, apres l'ecriture (et le commit) de l'exploration :
  KB=<branche de recherche extraite> python3 etude_large/zone_implicite/etude.py exploration   -> resultats.txt
  KB=<branche de recherche extraite> python3 etude_large/zone_implicite/etude.py coffre        -> ajoute a resultats.txt

Interpretations fixees avant tout calcul (le README ne les precise pas) :
- VXN de cloture d'une seance : la cloture datee de ce jour, sinon la derniere avant (jour ferie du Cboe).
- Les 252 seances de I2 et de la reference de T1 / T2 : les seances completes du NQ, comme la fenetre de 14 de V1.
- Series de test : seances jouables hors jours de la Fed (0 sans trade). Challenges : jours de partie_d.chemins_zone
  (jours de la Fed a 0, comme la zone seule).
- Placebos du coffre : memes 200 permutations par test, tirees apres celles de l'exploration (meme graine)."""
import importlib.util
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
RACINE = ICI.parent.parent
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

N, PAS, PT, COUT = DM.N, DM.PAS, DM.RB.PT, DM.COUT
FIN_EXPLO = pd.Timestamp("2022-12-30")
COFFRE = (pd.Timestamp("2023-01-03"), pd.Timestamp(DM.FIN))
VXN = RACINE / "donnees_libres" / "vxn"
SORTIE = ICI / "resultats.txt"
NPLAC = 200
TESTS = ["I1", "I2", "I3", "T1", "T2"]
# controle a) (pistes/zones_decalees) : V1 sur tous les jours jouables jusqu'au 16 octobre 2026
REF_V1 = ("2026-10-16", 3571, 10759.75)


def f2(x, d=2):
    return f"{x:+.{d}f}".replace(".", ",")


# ----------------------------------------------------------------------------- donnees
def lire_vxn(L):
    """Source du README : Cboe, sinon FRED, sinon Yahoo ; accord entre sources publie."""
    src = {}
    for nom in ("cboe", "fred", "yahoo"):
        p = VXN / f"{nom}.csv.gz"
        if p.exists():
            d = pd.read_csv(p)
            src[nom] = pd.Series(d["c"].astype(float).values, index=pd.to_datetime(d["t"])).sort_index()
            src[nom] = src[nom][~src[nom].index.duplicated(keep="last")]
    L.append("VXN, sources : " + " ; ".join(f"{k} {len(v)} jours {v.index[0].date()} -> {v.index[-1].date()}"
                                          for k, v in src.items()))
    for a, b in (("cboe", "fred"), ("cboe", "yahoo"), ("fred", "yahoo")):
        if a in src and b in src:
            x = pd.concat([src[a], src[b]], axis=1, join="inner").dropna()
            x = x[x.index >= "2011-01-01"]
            L.append(f"  accord {a} / {b} depuis 2011 : {len(x)} jours communs, ecart > 0,1 point sur "
                     f"{(abs(x.iloc[:, 0] - x.iloc[:, 1]) > 0.1).mean() * 100:.2f} % des jours")
    return src


def choisir(src, jours, L):
    j = jours[(jours >= "2011-01-01") & (jours <= COFFRE[1])]
    for nom in ("cboe", "fred", "yahoo"):
        if nom in src:
            cov = np.isin(j.values, src[nom].index.values).mean()
            L.append(f"  couverture des seances du NQ 2011 - 2026 par {nom} : {cov * 100:.1f} %")
            if cov >= 0.95:
                L.append(f"  -> source utilisee : {nom}")
                return src[nom]
    raise SystemExit("VXN absent ou incomplet : rien n'est calcule")


# ----------------------------------------------------------------------------- moteur rapide (meme regle que zone_jour)
@njit(cache=True)
def jour_nb(C, sig, vwap, href, bref, f, derniere):
    tot, nb, virt, pe = 0.0, 0, 0, 0.0
    for m in range(PAS, N):
        p = C[m]
        if m == N - 1:
            if virt != 0:
                tot += (virt * (p - pe) * f - COUT) * PT
                nb += 1
            break
        if m % PAS:
            continue
        s = sig[m]
        ub, lb = href * (1 + s), bref * (1 - s)
        if virt != 0:
            hv = ub if ub > vwap[m] else vwap[m]
            bv = lb if lb < vwap[m] else vwap[m]
            if (virt > 0 and p <= hv) or (virt < 0 and p >= bv):
                tot += (virt * (p - pe) * f - COUT) * PT
                nb += 1
                virt = 0
        if virt == 0 and m <= derniere:
            if p > ub:
                virt, pe = 1, p
            elif p < lb:
                virt, pe = -1, p
    return tot, nb


@njit(cache=True)
def serie_nb(idx, C, SIG, VW, HR, BRF, F, derniere):
    out = np.zeros(len(idx))
    nb = 0
    for k in range(len(idx)):
        i = idx[k]
        g, n = jour_nb(C[i], SIG[k], VW[i], HR[i], BRF[i], F[i], derniere)
        out[k] = g
        nb += n
    return out, nb


def t_alpha(yw, y):
    """t de l'alpha de la regression de yw sur y (moindres carres, erreurs classiques)."""
    n = len(y)
    X = np.column_stack([np.ones(n), y])
    b, *_ = np.linalg.lstsq(X, yw, rcond=None)
    e = yw - X @ b
    s2 = e @ e / (n - 2)
    cov = s2 * np.linalg.inv(X.T @ X)
    return float(b[0] / np.sqrt(cov[0, 0])), float(b[0]), float(b[1])


def rang(reel, plac):
    return int((np.asarray(plac) < reel).sum()) / len(plac) * 100


# ----------------------------------------------------------------------------- preparation commune
def preparer(L):
    rech = pd.read_csv(DM.RECHERCHE)
    robot = pd.read_csv(DM.ROBOT)
    bars = pd.concat([rech, robot[robot["t"] > rech["t"].iloc[-1]]], ignore_index=True)
    z = DM.preparer(bars)
    jours_t, O, Hm, Lm, C, P, V, ech = DM.RB.tableaux(bars)
    ok = DM.RB.seances_completes(P)
    jours = z["jours"]
    fed = set(pd.DatetimeIndex(fomc.annonces()))
    src = lire_vxn(L)
    vx = choisir(src, jours, L)
    cl = vx.reindex(jours, method="ffill").values                 # cloture du jour (ou derniere avant)
    # VXN de la veille : derniere cloture datee strictement avant le jour
    pos = vx.index.searchsorted(jours, side="left") - 1
    vv = np.where(pos >= 0, vx.values[np.maximum(pos, 0)], np.nan)
    mouvement = np.abs(C / O[:, 0][:, None] - 1)
    io = np.where(ok)[0]
    # I1 / I3 : moyenne des clotures du VXN des 14 seances de la fenetre de sigma (memes seances completes, decalees)
    m14 = np.full(len(jours), np.nan)
    m14[io] = pd.Series(cl[io]).rolling(DM.JM, min_periods=DM.JM).mean().shift(1).values
    r = vv / m14
    # I2 : k_m = moyenne sur 252 seances completes precedentes de |C_m/O - 1| / (VXN de la veille / 100)
    k = np.full_like(mouvement, np.nan)
    k[io] = pd.DataFrame(mouvement[io] / (vv[io, None] / 100)).rolling(252, min_periods=252).mean().shift(1).values
    # T1 / T2 : reference = mediane du VXN de la veille sur les 252 seances completes precedentes
    ref_t = np.full(len(jours), np.nan)
    ref_t[io] = pd.Series(vv[io]).rolling(252, min_periods=252).median().shift(1).values
    # seances de test : jouables pour V1 et pour toutes les variantes, hors Fed
    jo = z["jouables"]
    defini = ~np.isnan(r[jo]) & ~np.isnan(k[jo, PAS]) & ~np.isnan(ref_t[jo]) & ~np.isnan(vv[jo])
    jo = jo[defini & ~np.isin(jours[jo], list(fed))]
    jo = jo[jours[jo] <= COFFRE[1]]
    idx_fin = {j: i for i, j in enumerate(jours)}[pd.Timestamp(DM.FIN)]
    ref_prix = float(C[idx_fin, N - 1])
    F = ref_prix / C[:, 0]
    return dict(z=z, bars=bars, C=C, Hm=Hm, Lm=Lm, jours=jours, fed=fed, vv=vv, r=r, k=k, ref_t=ref_t, jo=jo,
                F=F, ref_prix=ref_prix, vx=vx)


def sigmas(d, i, r=None, vv=None):
    """Largeurs des 3 variantes pour les seances i (r et vv permutes pour les placebos)."""
    s = d["z"]["sigma"][i]
    r = d["r"][i] if r is None else r
    vv = d["vv"][i] if vv is None else vv
    return {"I1": s * r[:, None], "I2": d["k"][i] * (vv[:, None] / 100), "I3": s * np.maximum(1.0, r)[:, None]}


def series(d, i, sig):
    z = d["z"]
    return serie_nb(i, d["C"], np.ascontiguousarray(sig), z["vwap"], z["href"], z["bref"], d["F"], DM.DERNIERE_ENTREE)


def poids(d, i):
    a = d["ref_t"][i] / d["vv"][i]
    return {"T1": np.clip(a, 0.5, 2.0), "T2": np.clip(1 / a, 0.5, 2.0)}


def mesurer(d, i, rng, L, titre):
    """Statistiques reelles et placebos d'une periode (seances i)."""
    z = d["z"]
    y, nb_v1 = series(d, i, z["sigma"][i])
    res = {"V1": dict(s=y, nb=nb_v1)}
    for nom, sg in sigmas(d, i).items():
        s, nb = series(d, i, sg)
        res[nom] = dict(s=s, nb=nb, t=PA.t_stat(s - y), ratio=float(np.nanmean(sg[:, PAS] / z["sigma"][i][:, PAS])))
    for nom, w in poids(d, i).items():
        ta, a, b = t_alpha(w * y, y)
        res[nom] = dict(s=w * y, w=w, t=ta, alpha=a, beta=b)
    # placebos
    plac = {t: [] for t in TESTS}
    for _ in range(NPLAC):
        p = rng.permutation(len(i))
        sg = sigmas(d, i, r=d["r"][i][p], vv=d["vv"][i][p])
        for nom in ("I1", "I2", "I3"):
            plac[nom].append(PA.t_stat(series(d, i, sg[nom])[0] - y))
        for nom, w in poids(d, i).items():
            plac[nom].append(t_alpha(w[p] * y, y)[0])
    for t in TESTS:
        res[t]["rang"] = rang(res[t]["t"], plac[t])
    L.append(f"{titre} : {len(i)} seances ({d['jours'][i[0]].date()} -> {d['jours'][i[-1]].date()}), V1 {nb_v1} trades,"
             f" {f2(y.mean(), 1)} $ par seance, t {f2(PA.t_stat(y))}, Sharpe {f2(PA.sharpe(y))}")
    for t in TESTS:
        x = res[t]
        if t.startswith("I"):
            L.append(f"  {t} : {x['nb']} trades, largeur moyenne x {x['ratio']:.2f} a 10 h, {f2(x['s'].mean(), 1)} $ par "
                     f"seance, Sharpe {f2(PA.sharpe(x['s']))}, t de la difference avec V1 {f2(x['t'])}, bat "
                     f"{x['rang']:.1f} % des placebos")
        else:
            L.append(f"  {t} : poids moyen {x['w'].mean():.2f} (min {x['w'].min():.2f}, max {x['w'].max():.2f}), "
                     f"{f2(x['s'].mean(), 1)} $ par seance, Sharpe {f2(PA.sharpe(x['s']))}, alpha {f2(x['alpha'], 1)} $ "
                     f"(t {f2(x['t'])}), beta {x['beta']:.2f}, bat {x['rang']:.1f} % des placebos")
    return res


def par_annee(d, i, res, L):
    an = d["jours"][i].year
    y = res["V1"]["s"]
    L.append("  par annee (V1 $ par seance ; I1 I2 I3 : difference $ par seance ; T1 T2 : serie ponderee moins V1) :")
    for a in sorted(set(an)):
        m = np.asarray(an == a)
        L.append(f"    {a} : V1 {f2(y[m].mean(), 1)} ; " + " ; ".join(
            f"{t} {f2((res[t]['s'][m] - y[m]).mean(), 1)}" for t in TESTS))


# ----------------------------------------------------------------------------- temps 1 : exploration
def exploration():
    L = ["Vague zone implicite (regles : README, commit da634ef)", ""]
    d = preparer(L)
    z = d["z"]
    # controle a) : moteur de V1 et moteur rapide
    tr = DM.trades_zone(z, "2000-01-01", REF_V1[0])
    bon = len(tr) == REF_V1[1] and abs(tr["points"].sum() - REF_V1[2]) < 1e-6
    L.append(f"Controle a) V1 jusqu'au {REF_V1[0]} (jours de la Fed compris) : {len(tr)} trades "
             f"{tr['points'].sum():+.2f} pt, attendu {REF_V1[1]} et +{REF_V1[2]:.2f} -> {'PASSE' if bon else 'ECHEC'}")
    jt = d["jo"]
    yb, _ = series(d, jt, z["sigma"][jt])
    tz = DM.trades_zone(z, "2000-01-01", DM.FIN)
    tz = tz[~tz["jour"].isin(d["fed"])]
    jd, clo_z, _, _ = PD.chemins_zone()
    zs = pd.Series(clo_z[:, -1], index=jd).reindex(d["jours"][jt]).values
    bon2 = np.allclose(yb, zs, atol=1e-6)
    L.append(f"Controle b) moteur rapide contre partie_d.chemins_zone (gain du jour, {len(jt)} seances) : "
             f"{'identique' if bon2 else 'ECART'} ; trades {int(tz['jour'].isin(d['jours'][jt]).sum())}")
    if not (bon and bon2):
        SORTIE.write_text("\n".join(L) + "\n")
        raise SystemExit("controle en echec : rien d'autre n'est calcule")
    e = jt[d["jours"][jt] <= FIN_EXPLO]
    rng = np.random.default_rng(1)
    L.append("")
    res = mesurer(d, e, rng, L, "EXPLORATION")
    p = np.array([PA.p_unilateral(res[t]["t"]) for t in TESTS])
    garde = PA.bh(p, 0.10)
    L.append("")
    L.append("Critere 1 (t >= 2,0 et Benjamini-Hochberg 10 % sur les 5 tests, p unilateral) :")
    for t, pp, g in zip(TESTS, p, garde):
        ok = res[t]["t"] >= 2.0 and g
        L.append(f"  {t} : t {f2(res[t]['t'])}, p {pp:.4f}, BH {'retenu' if g else 'non'} -> {'PASSE' if ok else 'echec'}")
    par_annee(d, e, res, L)
    vxn_now = d["vx"].iloc[-1]
    i_now = d["jo"][-1]
    L += ["", f"Pour information : VXN au {d['vx'].index[-1].date()} {vxn_now:.2f} ; le {d['jours'][i_now].date()}, rapport de "
          f"I1 {d['r'][i_now]:.2f}, largeur I2 / V1 a 10 h {d['k'][i_now, PAS] * d['vv'][i_now] / 100 / z['sigma'][i_now, PAS]:.2f},"
          f" poids T1 {np.clip(d['ref_t'][i_now] / d['vv'][i_now], 0.5, 2):.2f}"]
    SORTIE.write_text("\n".join(L) + "\n")
    print("\n".join(L))


# ----------------------------------------------------------------------------- temps 2 : coffre (une seule fois)
def coffre():
    texte = SORTIE.read_text()
    assert "EXPLORATION" in texte and "COFFRE" not in texte, "exploration absente ou coffre deja ouvert"
    L = ["", "COFFRE 3 janvier 2023 - 20 octobre 2026 (ouvert une seule fois, apres le commit de l'exploration)"]
    Lx = []
    d = preparer(Lx)
    z = d["z"]
    jt = d["jo"]
    e = jt[d["jours"][jt] <= FIN_EXPLO]
    c = jt[(d["jours"][jt] >= COFFRE[0]) & (d["jours"][jt] <= COFFRE[1])]
    rng = np.random.default_rng(1)
    rex = mesurer(d, e, rng, [], "exploration (recalculee, memes placebos)")
    res = mesurer(d, c, rng, L, "COFFRE")
    p = np.array([PA.p_unilateral(rex[t]["t"]) for t in TESTS])
    garde = PA.bh(p, 0.10)
    par_annee(d, c, res, L)
    # challenges
    jd, clo_z, bas_z, haut_z = PD.chemins_zone()
    dep = np.where(jd >= pd.Timestamp(PD.DEBUT_VERIF))[0]
    ij = {j: i for i, j in enumerate(d["jours"])}
    tous = jt[d["jours"][jt] >= pd.Timestamp(PD.DEBUT)]
    chem = {}
    for nom in ("I1", "I2", "I3"):
        lignes = []
        for i in tous:
            sg = sigmas(d, np.array([i]))[nom][0]
            for me, sens, pe, ms, ps in DM.zone_jour(d["C"][i], sg, z["vwap"][i], z["href"][i], z["bref"][i]):
                lignes.append(dict(jour=d["jours"][i], minute_entree=me, sens=sens, prix_entree=pe, minute_sortie=ms,
                                   prix_sortie=ps, points=sens * (ps - pe) - COUT))
        trv = pd.DataFrame(lignes)
        chem[nom] = BR.chemins(z, d["Hm"], d["Lm"], trv, jd, COUT, PT, d["ref_prix"])
        # controle : la fin du chemin redonne la serie du moteur rapide
        fin = pd.Series(chem[nom][0][:, -1], index=jd).reindex(d["jours"][c]).values
        L.append(f"  controle {nom} : chemins contre moteur rapide au coffre -> "
                 f"{'identique' if np.allclose(fin, res[nom]['s'], atol=1e-6) else 'ECART'}")
    wjour = {}
    for nom in ("T1", "T2"):
        w = np.full(len(jd), np.nan)
        for k_, j in enumerate(jd):
            i = ij.get(j)
            if i is not None and not np.isnan(d["ref_t"][i]) and not np.isnan(d["vv"][i]):
                a = d["ref_t"][i] / d["vv"][i]
                w[k_] = np.clip(a if nom == "T1" else 1 / a, 0.5, 2.0)
        wjour[nom] = np.where(np.isnan(w), 1.0, w)
    L.append("")
    L.append("Challenges (moteur de partie_d, departs 2023 - 2026, valide / perdu en %) :")
    ok5 = {t: False for t in TESTS}
    for firme, q in (("Lucid Flex 50K", 1), ("Bulenox Legacy 50K opt. 2", 3)):
        obj, dd, bloc, dll, nmax, part, *_ = PD.FIRMES[firme]
        lim = PD.limites_depart(jd, dep, nmax)
        okd = dep + lim < len(jd)

        def taux(cl, ba, ha, qq):
            a = PD.tous_les_departs(cl, ba, ha, dep[okd], lim[okd], qq, qq, 0, float(obj), float(dd), float(bloc),
                                    float(dll), part, True)[0]
            return (a == 1).mean() * 100, (a == -1).mean() * 100
        base = taux(clo_z, bas_z, haut_z, float(q))
        lig = [f"V1 {q} MNQ {base[0]:.1f} / {base[1]:.1f}"]
        for nom in TESTS:
            if nom in chem:
                cl, ba, ha = chem[nom]
                v = taux(cl, ba, ha, float(q))
            else:
                n = np.clip(np.floor(q * wjour[nom] + 0.5), 1, 2 * q)[:, None]
                v = taux(clo_z * n, bas_z * n, haut_z * n, 1.0)
            passe = v[0] >= base[0] + 2 and v[1] <= base[1] + 3
            ok5[nom] |= passe
            lig.append(f"{nom} {v[0]:.1f} / {v[1]:.1f}{' (passe)' if passe else ''}")
        L.append(f"  {firme} : " + " ; ".join(lig))
    L.append("")
    L.append("DECISION (criteres du README, tous exiges) :")
    for t, g in zip(TESTS, garde):
        x, xe = res[t], rex[t]
        crit = {1: xe["t"] >= 2.0 and g, 2: x["t"] >= 1.5,
                3: xe["rang"] >= 95 and x["rang"] >= 95,
                4: PA.sharpe(xe["s"]) > PA.sharpe(rex["V1"]["s"]) and PA.sharpe(x["s"]) > PA.sharpe(res["V1"]["s"]),
                5: ok5[t]}
        L.append(f"  {t} : " + ", ".join(f"{k} {'oui' if v else 'non'}" for k, v in crit.items())
                 + f" -> {'RETENU' if all(crit.values()) else 'non retenu'}")
    with open(SORTIE, "a") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    {"exploration": exploration, "coffre": coffre}[sys.argv[1]]()
