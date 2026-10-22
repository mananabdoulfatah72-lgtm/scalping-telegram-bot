#!/usr/bin/env python3
"""etude_large/phenomenes/README.md, piste D (regles fixees le 22 octobre 2026, commit 929d05e, avant tout calcul) :
forme de la cassure de la zone. A chaque entree de V1 (controle m, sens s), sur les 30 variations d'une minute qui
precedent : ID = signe(M) x (n- - n+) / 30 (Da, Gurun et Warachka 2014) et J = part du plus gros saut. Seuils sur les
entrees de V1 des 252 seances completes precedentes (au moins 100). F1 : garder si ID <= mediane ; F2 : ecarter si
J >= 80e centile. Trade ecarte : virtuel et bloquant (retire de la liste de V1). Serie de decision : $ par seance pour
1 MNQ au prix du 20 octobre 2026 (partie_d.chemins_zone). Placebo de 200 filtres au hasard (meme part ecartee chaque
annee), criteres communs 1 a 5, au moins 40 % de trades gardes.

Lancer : KB=<branche de recherche extraite> python3 etude_large/phenomenes/forme_cassure/etude.py. Ecrit resultats.txt :
l'exploration d'abord (fichier ecrit et ferme), puis le coffre."""
import importlib.util
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

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

N, COUT, PT = DM.N, DM.COUT, DM.RB.PT
EXPLO = ("2012-01-01", "2022-12-30")
COFFRE = ("2023-01-03", DM.FIN)
FENETRE, MIN_ENTREES = 252, 100
PLACEBOS = 200
SORTIE = ICI / "resultats.txt"
ES = DM.KB / "intraday" / "donnees" / "sp500_1min.csv.gz"
FIRMES_TEST = [("Lucid Flex 50K", 1.0), ("Bulenox Legacy 50K opt. 2", 3.0)]


def mesures(z, tr):
    """ID et J de chaque entree (30 variations d'une minute avant le controle, prix du NQ)."""
    idx = {j: i for i, j in enumerate(z["jours"])}
    ID, J, M = [], [], []
    for _, t in tr.iterrows():
        C = z["C"][idx[t["jour"]]]
        m, s = int(t["minute_entree"]), int(t["sens"])
        r = np.diff(C[m - 30:m + 1])
        npos, nneg = int((s * r > 0).sum()), int((s * r < 0).sum())
        mm = s * (C[m] - C[m - 30])
        ID.append(np.sign(mm) * (nneg - npos) / 30.0)
        a = np.abs(r)
        J.append(a.max() / a.sum() if a.sum() > 0 else 1.0)
        M.append(mm)
    return tr.assign(ID=ID, J=J, M=M)


def seuils(z, tr):
    """Mediane de ID et 80e centile de J sur les entrees des 252 seances jouables precedentes (passe seulement)."""
    jou = [z["jours"][i] for i in z["jouables"]]
    rang = {j: k for k, j in enumerate(jou)}
    k_tr = tr["jour"].map(rang).values
    med, p80, n = np.full(len(tr), np.nan), np.full(len(tr), np.nan), np.zeros(len(tr), int)
    for i in range(len(tr)):
        m = (k_tr < k_tr[i]) & (k_tr >= k_tr[i] - FENETRE)
        n[i] = int(m.sum())
        if n[i] >= MIN_ENTREES:
            med[i] = np.median(tr["ID"].values[m])
            p80[i] = np.quantile(tr["J"].values[m], 0.8)
    return tr.assign(med_ID=med, p80_J=p80, n_ref=n)


def dollars(tr, z, ref):
    ouv = pd.Series(z["C"][:, 0], index=z["jours"])
    f = ref / ouv.reindex(tr["jour"]).values
    return (tr["sens"] * (tr["prix_sortie"] - tr["prix_entree"]) * f - COUT).values * PT


def quotidien(tr, valeur, jours):
    if tr.empty:
        return np.zeros(len(jours))
    return pd.Series(valeur, index=tr["jour"].values).groupby(level=0).sum().reindex(jours).fillna(0.0).values


def t_(x):
    return PA.t_stat(x)


def preparer_marche(bars, debut, fin, fed):
    z = DM.preparer(bars)
    tr = DM.trades_zone(z, debut, fin)
    tr = tr[~tr["jour"].isin(fed)].reset_index(drop=True)
    tr = seuils(z, mesures(z, tr))
    actif = ~np.isnan(tr["med_ID"].values)
    garde = {"F1": ~actif | (tr["ID"].values <= tr["med_ID"].values),
             "F2": ~actif | (tr["J"].values < tr["p80_J"].values)}
    return z, tr, garde


def main():
    fed = set(pd.DatetimeIndex(fomc.annonces()))
    rech = pd.read_csv(DM.RECHERCHE)
    robot = pd.read_csv(DM.ROBOT)
    bars = pd.concat([rech, robot[robot["t"] > rech["t"].iloc[-1]]], ignore_index=True)
    z, tr, garde = preparer_marche(bars, "2011-01-01", DM.FIN, fed)
    ref = float(z["C"][{j: i for i, j in enumerate(z["jours"])}[pd.Timestamp(DM.FIN)], N - 1])
    usd = dollars(tr, z, ref)
    jours = pd.DatetimeIndex([z["jours"][i] for i in z["jouables"]])
    jours = jours[(jours >= EXPLO[0]) & (jours <= COFFRE[1]) & ~jours.isin(fed)]
    e = (jours >= EXPLO[0]) & (jours <= EXPLO[1])
    c = (jours >= COFFRE[0]) & (jours <= COFFRE[1])
    tr_e = tr["jour"].between(*EXPLO).values
    tr_c = tr["jour"].between(pd.Timestamp(COFFRE[0]), pd.Timestamp(COFFRE[1])).values
    v1 = quotidien(tr, usd, jours)
    L = ["Piste D : forme de la cassure (etude_large/phenomenes/README.md, commit 929d05e, regles fixees avant tout calcul)",
         f"Zone V1 sans les jours de la Fed : {len(tr)} entrees 2011 - {DM.FIN} ; seances de decision {len(jours)} "
         f"(exploration {int(e.sum())}, coffre {int(c.sum())}) ; prix de reference {ref:.2f}.", ""]
    # controle du moteur (avant tout gain)
    t19 = DM.trades_zone(z, "2000-01-01", "2026-10-16")
    L.append(f"CONTROLE moteur : jusqu'au 16 octobre 2026, {len(t19)} trades {t19['points'].sum():+.2f} points (Fed comprise) ; "
             f"reference 3571 / +10759.75 -> {'identique' if len(t19) == 3571 and abs(t19['points'].sum() - 10759.75) < 1e-6 else 'ECART'}")
    jd, clo_z, bas_z, haut_z = PD.chemins_zone()
    _, _, Hm, Lm, _, _, _, _ = DM.RB.tableaux(bars)
    trc = tr[tr["jour"] >= pd.Timestamp(PD.DEBUT)]
    c0, b0, h0 = BR.chemins(z, Hm, Lm, trc, jd, COUT, PT, ref)
    L.append(f"CONTROLE chemins : zone recomposee contre partie_d.chemins_zone, ecart maximal {np.abs(c0 - clo_z).max():.2e} $")
    # regard vers le futur : ID et J ne lisent que C[m-30 .. m] ; seuils sur les seances strictement precedentes
    rng = np.random.default_rng(1)
    idx = {j: i for i, j in enumerate(z["jours"])}
    change = 0
    for k in rng.choice(len(tr), 300, replace=False):
        t = tr.iloc[k]
        i = idx[t["jour"]]
        C = z["C"][i].copy()
        m = int(t["minute_entree"])
        C[m + 1:] = C[m + 1:] + rng.normal(0, 50, N - m - 1)
        r = np.diff(C[m - 30:m + 1])
        s = int(t["sens"])
        idb = np.sign(s * (C[m] - C[m - 30])) * (int((s * r < 0).sum()) - int((s * r > 0).sum())) / 30
        change += int(idb != t["ID"])
    L.append(f"REGARD VERS LE FUTUR : 300 entrees, prix brouilles apres le controle : {change} ID change(nt) -> "
             f"{'aucun regard vers le futur' if change == 0 else 'PROBLEME'} ; seuils calcules sur les {FENETRE} seances "
             "jouables strictement precedentes")
    L.append("")
    res = {}
    L.append("EXPLORATION 2012 - 2022 (coffre non ouvert)")
    for nom in ("F1", "F2"):
        g = garde[nom]
        filt = quotidien(tr[g], usd[g], jours)
        d = filt - v1
        part_e = g[tr_e].mean()
        # placebo : meme part ecartee chaque annee, entrees tirees au hasard (graine 1)
        rng = np.random.default_rng(1)
        ans = tr["jour"].dt.year.values
        tp = []
        for _ in range(PLACEBOS):
            gp = np.ones(len(tr), bool)
            for y in np.unique(ans[tr_e]):
                ix = np.where((ans == y) & tr_e)[0]
                k = int(round((~g[ix]).sum()))
                gp[rng.choice(ix, size=k, replace=False)] = False
            dp = quotidien(tr[gp], usd[gp], jours) - v1
            tp.append(t_(dp[e]))
        rang = float((np.array(tp) < t_(d[e])).mean())
        res[nom] = dict(d=d, filt=filt, te=t_(d[e]), rang=rang, part_e=part_e, g=g)
        L.append(f"  {nom} : trades gardes {part_e * 100:.1f} % ; Delta {d[e].sum():+,.0f} $ (t {t_(d[e]):+.2f}, p unilateral "
                 f"{PA.p_unilateral(t_(d[e])):.4f}) ; Sharpe filtre {PA.sharpe(filt[e]):+.3f} contre V1 {PA.sharpe(v1[e]):+.3f} ; "
                 f"bat {rang * 100:.1f} % des {PLACEBOS} placebos")
    # controles d'exploration
    ach = tr["sens"].values > 0
    for nom in ("F1", "F2"):
        g = res[nom]["g"]
        lig = []
        for lab, m in (("achats", ach), ("ventes", ~ach)):
            dd = quotidien(tr[~g & m & tr_e], -usd[~g & m & tr_e], jours)
            lig.append(f"{lab} {dd[e].sum():+,.0f} $")
        L.append(f"  controle c) {nom}, Delta par sens (exploration) : " + ", ".join(lig))
    h10 = tr["minute_entree"].values == 30
    L.append(f"  controle c) part des entrees de 10 h ecartees par F2 (exploration) : {(~garde['F2'][h10 & tr_e]).mean() * 100:.1f} % "
             f"(toutes heures : {(~garde['F2'][tr_e]).mean() * 100:.1f} %)")
    tous = pd.DatetimeIndex([z["jours"][i] for i in z["jouables"]])
    rang_jour = pd.Series(tous).groupby(tous.to_period("M")).cumcount().values + 1
    rang = dict(zip(tous, rang_jour))
    jour_mois = np.array([rang.get(d, 0) for d in tr["jour"]])
    ism = (jour_mois == 1) | (jour_mois == 3)
    for lab, m in (("jours ISM (1er et 3e jour de seance du mois)", ism), ("autres jours", ~ism)):
        mm = h10 & tr_e & m
        L.append(f"  controle d) entrees de 10 h, {lab} : {int(mm.sum())}, ecartees par F2 {(~garde['F2'][mm]).mean() * 100:.1f} %, "
                 f"gain moyen {usd[mm].mean():+.1f} $")
    p4 = tr["M"].values > 0
    L.append(f"  controle b) accord de decision F1 / filtre P4 (sens du mouvement des 30 minutes) : "
             f"{(garde['F1'] == p4)[tr_e].mean() * 100:.1f} % des trades d'exploration "
             f"{'(> 80 % : F1 est presque le filtre P4)' if (garde['F1'] == p4)[tr_e].mean() > 0.8 else ''}")
    SORTIE.write_text("\n".join(L) + "\n")
    # ----------------------------------------------------------------------------- coffre, ouvert une seule fois
    L2 = ["", "COFFRE 2023 - 20 octobre 2026 (ouvert apres l'ecriture de l'exploration)"]
    dep = np.where(jd >= pd.Timestamp(PD.DEBUT_VERIF))[0]
    for nom in ("F1", "F2"):
        r = res[nom]
        d, filt, g = r["d"], r["filt"], r["g"]
        tc = t_(d[c])
        crit = {1: r["te"] >= 2.0, 2: tc >= 1.5 and np.sign(d[c].sum()) == np.sign(d[e].sum()), 3: r["rang"] >= 0.95,
                4: PA.sharpe(filt[e]) > PA.sharpe(v1[e]) and PA.sharpe(filt[c]) > PA.sharpe(v1[c]),
                6: r["part_e"] >= 0.4}
        trf = tr[g & (tr["jour"] >= pd.Timestamp(PD.DEBUT)).values]
        cf, bf, hf = BR.chemins(z, Hm, Lm, trf, jd, COUT, PT, ref)
        lig, ok5 = [], False
        for firme, q in FIRMES_TEST:
            obj, dd_, bloc, dll, nmax, part, *_ = PD.FIRMES[firme]
            lim = PD.limites_depart(jd, dep, nmax)
            okd = dep + lim < len(jd)
            arg = (q, q, 0, float(obj), float(dd_), float(bloc), float(dll), part, True)
            a = PD.tous_les_departs(clo_z, bas_z, haut_z, dep[okd], lim[okd], *arg)[0]
            b = PD.tous_les_departs(cf, bf, hf, dep[okd], lim[okd], *arg)[0]
            va, pa_, vb, pb = (a == 1).mean() * 100, (a == -1).mean() * 100, (b == 1).mean() * 100, (b == -1).mean() * 100
            passe = vb >= va + 2 and pb <= pa_ + 3
            ok5 |= passe
            lig.append(f"{firme} {q:.0f} MNQ : zone {va:.1f} / {pa_:.1f} %, filtre {vb:.1f} / {pb:.1f} % -> {'passe' if passe else 'non'}")
        crit[5] = ok5
        propre = all(crit[k] for k in (2, 3, 4, 5, 6)) and r["te"] >= 2.0
        r.update(tc=tc, propre=propre, crit=crit)
        L2.append(f"  {nom} : Delta coffre {d[c].sum():+,.0f} $ (t {tc:+.2f}) ; Sharpe filtre {PA.sharpe(filt[c]):+.3f} contre "
                  f"V1 {PA.sharpe(v1[c]):+.3f} ; trades gardes au coffre {g[tr_c].mean() * 100:.1f} %")
        L2.append("     challenges (departs 2023 - 2026) : " + " ; ".join(lig))
        L2.append("     criteres : " + ", ".join(f"{k} {'oui' if crit[k] else 'non'}" for k in sorted(crit))
                  + f" -> criteres propres {'PASSENT' if propre else 'echec'}")
    # controle e) ES en replication, controle a) vrai delta
    try:
        ze, tre, ge = preparer_marche(pd.read_csv(ES), "2011-01-01", "2026-09-25", fed)
        jes = pd.DatetimeIndex([ze["jours"][i] for i in ze["jouables"]])
        jes = jes[(jes >= EXPLO[0]) & ~jes.isin(fed)]
        ouv = pd.Series(ze["C"][:, 0], index=ze["jours"])
        pts = (tre["sens"] * (tre["prix_sortie"] - tre["prix_entree"]) / ouv.reindex(tre["jour"]).values).values
        for nom in ("F1", "F2"):
            dd = quotidien(tre[~ge[nom]], -pts[~ge[nom]], jes)
            ee, cc = jes <= pd.Timestamp(EXPLO[1]), jes >= pd.Timestamp(COFFRE[0])
            L2.append(f"  controle e) ES {nom} : Delta exploration t {t_(dd[ee]):+.2f}, coffre t {t_(dd[cc]):+.2f}")
    except Exception as exc:  # noqa: BLE001
        L2.append(f"  controle e) ES : non calcule ({exc})")
    vd = pd.read_csv(RACINE / "delta_mesures" / "trades.csv", parse_dates=["jour"])
    mg = vd.merge(tr[["jour", "minute_entree", "ID", "J"]], on=["jour", "minute_entree"], how="inner")
    if len(mg) > 5:
        sd = np.sign(mg["D30"]) * mg["sens"]
        L2.append(f"  controle a) {len(mg)} trades avec le vrai delta (P1, P2) : correlation ID / delta dans le sens du trade "
                  f"{np.corrcoef(mg['ID'], sd)[0, 1]:+.2f}, J / delta {np.corrcoef(mg['J'], sd)[0, 1]:+.2f}")
    with SORTIE.open("a") as f:
        f.write("\n".join(L2) + "\n")
    print("\n".join(L + L2))
    return {k: (res[k]["te"], res[k]["tc"], res[k]["propre"]) for k in res}


if __name__ == "__main__":
    print(main())
