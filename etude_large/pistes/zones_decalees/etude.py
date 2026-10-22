#!/usr/bin/env python3
"""etude_large/pistes/README.md, piste 5 (regles fixees le 22 octobre 2026, commit a6e791f, avant tout calcul) :
copies decalees de la zone. D0 = V1 (controles de 10 h 00 a 15 h 30). D15 = la meme regle exacte (sigma de la minute du
controle sur 14 seances completes, memes limites max/min(ouverture, veille) x (1 +- sigma), VWAP, sortie si C repasse
max(ub, VWAP) ou min(lb, VWAP), meme mecanique de rachat que V1) avec des controles a 10 h 15, 10 h 45 ... 15 h 45 et a
plat a 15 h 59 ; D10 (10 h 10 ... 15 h 40) et D20 (10 h 20 ... 15 h 50) construites de la meme facon. Chaque copie a sa
propre position de 1 MNQ et ses propres frais (1,5 point par aller-retour). Pas de zone les jours de la Fed ni les jours
courts. E2 = D0 + D15 (2 MNQ) contre V1 a 2 MNQ ; E3 = D0 + D10 + D20 (3 MNQ) contre V1 a 3 MNQ.
Tests comptes dans Benjamini-Hochberg : D15 seule, D10 seule, D20 seule (unilateraux, t net >= 2).
Exploration 2011-2022, coffre 2023 -> 20 octobre 2026.

Lancer : KB=<branche de recherche extraite> python3 etude_large/pistes/zones_decalees/etude.py. Ecrit resultats.txt."""
import os
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
os.environ.setdefault("NUMBA_CACHE_DIR", str(Path(tempfile.gettempdir()) / "numba_zones_decalees"))

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent.parent
sys.path = [p for p in sys.path if Path(p or ".").resolve() != ICI]       # ce fichier s'appelle aussi etude.py
sys.path.insert(0, str(RACINE / "delta_mesures"))
import json  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import etude as DM  # noqa: E402
sys.path.insert(0, str(RACINE / "etude_large"))
import partie_d as PD  # noqa: E402
import partie_a as PA  # noqa: E402
sys.path.insert(0, str(DM.KB / "fonds"))
import fomc  # noqa: E402

N, PAS, COUT, PT = DM.N, DM.PAS, DM.COUT, DM.RB.PT
DECALAGES = {"D0": 0, "D10": 10, "D15": 15, "D20": 20}
TESTS = ["D15", "D10", "D20"]                     # ordre du README (les 3 tests comptes dans Benjamini-Hochberg)
ENSEMBLE = {"D15": ("E2", ["D0", "D15"]), "D10": ("E3", ["D0", "D10", "D20"]), "D20": ("E3", ["D0", "D10", "D20"])}
EXPLO = ("2011-01-01", "2022-12-31")
COFFRE = ("2023-01-01", DM.FIN)
LUCID, BULENOX = "Lucid Flex 50K", "Bulenox Legacy 50K opt. 2"
# controle a) : entree_tardive/resultats_15ans.txt (barres du robot du 20 octobre au matin, jusqu'au 19 octobre) ; la
# barre du 19 octobre a 11 h 30 a ete retelechargee depuis (delta_mesures/etude.py) : comparaison jusqu'au 16 octobre,
# 3 572 trades +10 721,25 pt moins le trade du 19 octobre (-38,50 pt) = 3 571 trades +10 759,75 pt
REF_V1 = (3572, 10721.25, "2026-10-16", 3571, 10759.75)
REF_T_V1 = (2.12, 1.86)                           # entree_tardive : t de V1 (jours de la Fed compris)
ROBUSTESSE = DM.KB / "robustesse" / "robustesse.json"
ROB_PERIODE = ("2012-01-03", "2026-09-25")
GRAINE = 20261022


def heure(m):
    return DM.heure(m)


def f2(x, d=2, signe=True):
    """Nombre avec virgule decimale."""
    s = f"{x:+.{d}f}" if signe else f"{x:.{d}f}"
    return s.replace(".", ",")


# ----------------------------------------------------------------------------- une copie de la zone, une seance
def controles(k):
    """Minutes des controles de la copie decalee de k minutes : 10 h 00 + k, 10 h 30 + k, ... (avant 15 h 59)."""
    return list(range(PAS + k, N - 1, PAS))


def zone_copie(C, sigma, vwap, href, bref, k):
    """delta_mesures/etude.py zone_jour avec la grille de controles decalee de k minutes : a chaque controle, sortie si le
    prix repasse max(ub, VWAP) (achat) ou min(lb, VWAP) (vente), puis entree au meme controle si la cloture est hors de
    la zone (rachat de V1) ; a plat a la cloture de 15 h 59. Toutes les informations sont celles de la minute du
    controle (cloture, sigma de cette minute, VWAP jusqu'a cette minute). Liste de (me, sens, pe, ms, ps)."""
    out, pos, t = [], 0, None
    for m in controles(k):
        p = C[m]
        s = sigma[m]
        ub, lb = href * (1 + s), bref * (1 - s)
        if pos and ((pos > 0 and p <= max(ub, vwap[m])) or (pos < 0 and p >= min(lb, vwap[m]))):
            out.append((*t, m, p))
            pos, t = 0, None
        if not pos:
            sens = 1 if p > ub else (-1 if p < lb else 0)
            if sens:
                pos, t = sens, (m, sens, p)
    if pos:
        out.append((*t, N - 1, C[N - 1]))
    return out


def trades_copie(z, idx, k, nom):
    lignes = []
    for i in idx:
        j = z["jours"][i]
        for me, s, pe, ms, ps in zone_copie(z["C"][i], z["sigma"][i], z["vwap"][i], z["href"][i], z["bref"][i], k):
            lignes.append(dict(jour=j, copie=nom, minute_entree=me, sens=s, prix_entree=pe, minute_sortie=ms,
                               prix_sortie=ps, brut=s * (ps - pe), points=s * (ps - pe) - COUT))
    cols = ["jour", "copie", "minute_entree", "sens", "prix_entree", "minute_sortie", "prix_sortie", "brut", "points"]
    return pd.DataFrame(lignes, columns=cols)


def quotidien(tr, jours, col="points"):
    return tr.groupby("jour")[col].sum().reindex(jours).fillna(0.0).to_numpy()


# ----------------------------------------------------------------------------- challenges (moteur de la partie D)
def chemins(z, Hm, Lm, trs):
    """partie_d.chemins_zone generalisee a plusieurs copies dans le meme compte : gain cumule minute par minute en $ au
    niveau de prix du 20 octobre 2026, frais deduits a l'entree de chaque trade de chaque copie ; plus bas et plus haut
    de chaque minute calcules sur la position nette des copies (n MNQ ouverts pendant la minute). Pour une seule copie,
    c'est exactement partie_d.chemins_zone (verifie). trs : trades (jours de la Fed deja retires)."""
    jours = pd.DatetimeIndex([z["jours"][i] for i in z["jouables"]])
    jours = jours[(jours >= PD.DEBUT) & (jours <= DM.FIN)]
    idx = {j: i for i, j in enumerate(z["jours"])}
    ref = float(z["C"][idx[pd.Timestamp(DM.FIN)], N - 1])
    ch, bas, haut = (np.zeros((len(jours), N)) for _ in range(3))
    pos = {j: k for k, j in enumerate(jours)}
    tout = pd.concat(trs, ignore_index=True)
    for j, g in tout.groupby("jour"):
        if j not in pos:
            continue
        i = idx[j]
        C, H, L = z["C"][i], Hm[i], Lm[i]
        f = ref / C[0]
        c, n = np.zeros(N), np.zeros(N)
        for me, ms, s, pe, ps in g[["minute_entree", "minute_sortie", "sens", "prix_entree", "prix_sortie"]].itertuples(
                index=False):
            me, ms, s = int(me), int(ms), int(s)
            c[me:ms] += s * (C[me:ms] - pe) * f
            c[ms:] += s * (ps - pe) * f
            c[me:] -= COUT
            n[me + 1:ms + 1] += s          # ouvert pendant les minutes me+1 .. ms (entree et sortie aux clotures)
        lo, hi = np.maximum(n, 0), np.maximum(-n, 0)
        contre = ((C - L) * lo + (H - C) * hi) * f
        pour = ((H - C) * lo + (C - L) * hi) * f
        k = pos[j]
        ch[k], bas[k], haut[k] = c * PT, (c - contre) * PT, (c + pour) * PT
    return jours, ch, bas, haut


def challenge(jours, clo, bas, haut, firme, q):
    obj, dd, bloc, dll, nmax, part, *_ = PD.FIRMES[firme]
    verif = np.where(jours >= PD.DEBUT_VERIF)[0]
    lim = PD.limites_depart(jours, verif, nmax)
    ok = verif + lim < len(jours)
    iss, nb = PD.tous_les_departs(clo, bas, haut, verif[ok], lim[ok], float(q), float(q), 0, float(obj), float(dd),
                                  float(bloc), float(dll), part, True)
    return dict(n=int(ok.sum()), valide=(iss == 1).mean() * 100, perdu=(iss == -1).mean() * 100,
                expire=(iss == 0).mean() * 100)


# ----------------------------------------------------------------------------- regard vers le futur
def regard_futur(bars, z, univers, rng, n=300):
    """Pour n seances tirees au hasard, une copie et un controle m tires au hasard : on recalcule la zone sur une fenetre
    de 45 seances qui finit a cette seance, une fois telle quelle et une fois avec tout ce qui suit la minute m de la
    seance (o, h, l, c, v) remplace par du bruit. Les decisions jusqu'a m (entrees, sorties) doivent etre identiques, et
    sigma, VWAP et references jusqu'a m aussi. La fenetre telle quelle doit redonner les trades du calcul complet."""
    t = bars["t"].to_numpy()
    jour_txt = bars["t"].str[:10].to_numpy()
    minute = bars["t"].str[11:13].astype(int).to_numpy() * 60 + bars["t"].str[14:16].astype(int).to_numpy() - 570
    debut_jour = {}
    for r, jt in enumerate(jour_txt):
        if jt not in debut_jour:
            debut_jour[jt] = r
    jours_txt = [str(j.date()) for j in z["jours"]]
    tirage = rng.choice(univers, size=n, replace=False)
    changees, suites, fenetre_ok, ecart = 0, 0, 0, 0.0
    for i in tirage:
        nom = list(DECALAGES)[rng.integers(len(DECALAGES))]
        k = DECALAGES[nom]
        m = int(rng.choice(controles(k)))
        a = debut_jour[jours_txt[max(0, i - 45)]]
        b = debut_jour[jours_txt[i + 1]] if i + 1 < len(jours_txt) else len(t)
        w = bars.iloc[a:b].copy()
        zw = DM.preparer(w)
        dw = len(zw["jours"]) - 1
        assert zw["jours"][dw] == z["jours"][i] and dw in set(zw["jouables"])
        ref = zone_copie(z["C"][i], z["sigma"][i], z["vwap"][i], z["href"][i], z["bref"][i], k)
        tw = zone_copie(zw["C"][dw], zw["sigma"][dw], zw["vwap"][dw], zw["href"][dw], zw["bref"][dw], k)
        fenetre_ok += int(len(ref) == len(tw) and all(np.allclose(x, y) for x, y in zip(ref, tw)))
        # brouillage de tout ce qui suit la minute m de la seance
        sel = (jour_txt[a:b] == jours_txt[i]) & (minute[a:b] > m)
        p0 = float(w["c"].to_numpy()[~sel][-1])
        bruit = p0 * np.exp(np.cumsum(rng.normal(0, 0.004, sel.sum())))
        for col in "ohlc":
            w.loc[w.index[sel], col] = bruit * (1 + rng.normal(0, 0.001, sel.sum()))
        w.loc[w.index[sel], "v"] = rng.integers(1, 5000, sel.sum())
        zb = DM.preparer(w)
        tb = zone_copie(zb["C"][dw], zb["sigma"][dw], zb["vwap"][dw], zb["href"][dw], zb["bref"][dw], k)

        def avant(tr):
            return [(me, s, round(pe, 6), ms if ms <= m else None, round(ps, 6) if ms <= m else None)
                    for me, s, pe, ms, ps in tr if me <= m]
        changees += int(avant(tw) != avant(tb))
        suites += int(tw != tb)
        for x in ("sigma", "vwap"):
            ecart = max(ecart, float(np.abs(zw[x][dw, :m + 1] - zb[x][dw, :m + 1]).max()))
        ecart = max(ecart, abs(zw["href"][dw] - zb["href"][dw]), abs(zw["bref"][dw] - zb["bref"][dw]))
    return dict(n=n, changees=changees, suites=suites, fenetre_ok=fenetre_ok, ecart=ecart)


# ----------------------------------------------------------------------------- principal
def main():
    L = []
    rech = pd.read_csv(DM.RECHERCHE)
    robot = pd.read_csv(DM.ROBOT)
    robot = robot[robot["t"] <= DM.FIN + " 23:59"]
    bars = pd.concat([rech, robot[robot["t"] > rech["t"].iloc[-1]]], ignore_index=True)
    z = DM.preparer(bars)
    _, _, Hm, Lm, _, _, _, _ = DM.RB.tableaux(bars)
    fed = set(pd.DatetimeIndex(fomc.annonces()))
    fin = pd.Timestamp(DM.FIN)
    tous = [i for i in z["jouables"] if z["jours"][i] <= fin]
    univers = [i for i in tous if z["jours"][i] not in fed and not DM.RB.jour_court(z["jours"][i])]
    ju = pd.DatetimeIndex([z["jours"][i] for i in univers])
    e = np.asarray((ju >= EXPLO[0]) & (ju <= EXPLO[1]))
    c = np.asarray((ju >= COFFRE[0]) & (ju <= COFFRE[1]))
    n_fed = sum(1 for i in tous if z["jours"][i] in fed)
    n_court = sum(1 for i in tous if DM.RB.jour_court(z["jours"][i]))

    L.append("Piste 5 : copies decalees de la zone (D15, D10, D20 ; ensembles E2 et E3)")
    L.append("Regles : etude_large/pistes/README.md (commit a6e791f, fixees avant tout calcul). NQ minute, chaque copie")
    L.append("1 MNQ, 1,5 point par aller-retour, memes regles que V1 (sigma de la minute du controle sur 14 seances")
    L.append("completes, limites max/min(ouverture, veille) x (1 +- sigma), sortie au VWAP ou a la limite, rachat au meme")
    L.append("controle), seule la grille des controles change ; a plat a 15 h 59. Pas de zone les jours de la Fed ni les")
    L.append("jours courts. Exploration 2011-2022, coffre 2023 -> 20 oct. 2026. Series en points nets par seance (0 sans")
    L.append("trade) ; t = moyenne / ecart-type x racine(seances) ; Sharpe = moyenne / ecart-type x racine(252).")
    L.append("")
    for nom, k in DECALAGES.items():
        ct = controles(k)
        L.append(f"  {nom:3} : {len(ct)} controles {heure(ct[0])}, {heure(ct[1])} ... {heure(ct[-1])} (derniere entree"
                 f" possible {heure(ct[-1])}), sortie forcee 15h59")
    L.append("")
    L.append(f"BASE : minutes de la recherche + robot jusqu'au {DM.FIN} ; {len(univers)} seances de zone ({n_fed} jours de"
             f" la Fed retires, {n_court} jour court parmi les seances completes) : exploration {int(e.sum())}, coffre"
             f" {int(c.sum())}")

    # ------------------------------------------------------------------ controle a)
    L.append("")
    L.append("CONTROLE a) D0 recalculee = V1")
    dm = DM.trades_zone(z, "2000-01-01", DM.FIN)
    d0_tous = trades_copie(z, tous, 0, "D0")
    cle = ["jour", "minute_entree", "sens", "prix_entree", "minute_sortie", "prix_sortie", "points"]
    a1 = dm[cle].reset_index(drop=True)
    a2 = d0_tous[cle].reset_index(drop=True)
    meme = len(a1) == len(a2) and (a1["jour"].values == a2["jour"].values).all() and all(
        np.allclose(a1[k_].to_numpy(float), a2[k_].to_numpy(float)) for k_ in cle[1:])
    L.append(f"  D0 (moteur decale, k = 0) contre delta_mesures trades_zone (V1, tous les jours jouables) : {len(a2)} et"
             f" {len(a1)} trades, {a2['points'].sum():+.2f} et {a1['points'].sum():+.2f} pt -> trade par trade"
             f" {'identique' if meme else 'ECART'}")
    t16 = d0_tous[d0_tous["jour"] <= pd.Timestamp(REF_V1[2])]
    bon16 = len(t16) == REF_V1[3] and abs(t16["points"].sum() - REF_V1[4]) < 1e-6
    L.append(f"  jusqu'au 16 octobre 2026 : {len(t16)} trades {t16['points'].sum():+.2f} pt ; entree_tardive 3 572 trades"
             f" +10 721,25 pt jusqu'au 19 octobre, dont -38,50 pt le 19 (barre de 11 h 30 retelechargee depuis par le robot,"
             f" voir delta_mesures) -> {REF_V1[3]} trades +{REF_V1[4]:.2f} : {'identique' if bon16 else 'ECART'}")
    t19 = d0_tous[d0_tous["jour"] == pd.Timestamp("2026-10-19")]
    L.append(f"  le 19 octobre ici : {len(t19)} trade(s) {t19['points'].sum():+.2f} pt ; le 20 octobre :"
             f" {f2(d0_tous[d0_tous['jour'] == fin]['points'].sum())} pt ; total jusqu'au {DM.FIN} : {len(d0_tous)} trades"
             f" {f2(d0_tous['points'].sum())} pt")
    jt = pd.DatetimeIndex([z["jours"][i] for i in tous])
    sd0 = quotidien(d0_tous, jt)
    e_t, c_t = np.asarray(jt.year <= 2022), np.asarray(jt.year >= 2023)
    L.append(f"  repere du README (V1, jours de la Fed compris, {int(e_t.sum())} et {int(c_t.sum())} seances) : t"
             f" exploration {f2(PA.t_stat(sd0[e_t]))} (entree_tardive {f2(REF_T_V1[0])}), coffre {f2(PA.t_stat(sd0[c_t]))}"
             f" (entree_tardive {f2(REF_T_V1[1])} jusqu'au 19 octobre, avec l'ancienne barre)")
    ok_a = meme and bon16
    L.append(f"  -> controle a) {'PASSE' if ok_a else 'ECHEC'}")
    if not ok_a:
        print("\n".join(L))
        sys.exit(1)

    # ------------------------------------------------------------------ series de la piste
    tr = {nom: trades_copie(z, univers, k, nom) for nom, k in DECALAGES.items()}
    S = {nom: quotidien(tr[nom], ju) for nom in DECALAGES}
    SB = {nom: quotidien(tr[nom], ju, "brut") for nom in DECALAGES}
    S["E2"] = S["D0"] + S["D15"]
    S["E3"] = S["D0"] + S["D10"] + S["D20"]

    # ------------------------------------------------------------------ regard vers le futur
    L.append("")
    L.append("REGARD VERS LE FUTUR")
    rf = regard_futur(bars, z, univers, np.random.default_rng(GRAINE))
    L.append(f"  {rf['n']} cas (seance, copie et controle m tires au hasard) : la fenetre de 45 seances redonne les trades du"
             f" calcul complet dans {rf['fenetre_ok']} cas sur {rf['n']} ; tout ce qui suit m est brouille -> {rf['changees']}"
             f" decision changee jusqu'a m ; la suite change dans {rf['suites']} cas (le brouillage agit) ; ecart max de"
             f" sigma, VWAP (minutes <= m) et references : {rf['ecart']:.1e}")
    L.append("  chaque decision au controle m utilise la cloture de m, le sigma de la minute m (moyenne des 14 seances")
    L.append("  completes precedentes, shift(1)), le VWAP des minutes <= m, l'ouverture du jour et la cloture de la veille ;")
    L.append("  l'execution se fait a la cloture de la minute du controle, comme V1 et le bot. Jours de la Fed : dates")
    L.append("  publiees a l'avance ; jours courts : calendrier. Herite de V1 : la liste des seances completes (>= 370")
    L.append("  minutes, derniere minute presente) est connue le soir ; elle ne retire que des feries et demi-seances.")
    ok_rf = rf["changees"] == 0 and rf["fenetre_ok"] == rf["n"] and rf["ecart"] < 1e-6 and rf["suites"] > 0
    L.append(f"  -> {'aucun regard vers le futur' if ok_rf else 'PROBLEME'}")

    # chemins des challenges : D0 contre partie_d.chemins_zone (calendrier de partie_d : jours jouables 2012 -> 20 oct.
    # 2026, 0 les jours sans zone)
    jc, clo0, bas0, haut0 = chemins(z, Hm, Lm, [tr["D0"]])
    jp, clop, basp, hautp = PD.chemins_zone()
    ecart_ch = max(float(np.abs(clo0 - clop).max()), float(np.abs(bas0 - basp).max()), float(np.abs(haut0 - hautp).max()))
    same_days = len(jc) == len(jp) and (jc == jp).all()
    L.append(f"  chemins des challenges (partie_d generalisee, position nette des copies) avec D0 seule = partie_d."
             f"chemins_zone : {'oui' if same_days and ecart_ch < 1e-6 else 'NON'} (ecart max {ecart_ch:.1e} $)")

    # ------------------------------------------------------------------ resume des copies
    L.append("")
    L.append("LES QUATRE COPIES SEULES (1 MNQ, points nets)")
    L.append(f"  {'copie':5} | {'explo : trades':>14} {'points':>10} {'t net':>7} {'Sharpe':>7} {'t brut':>7} |"
             f" {'coffre : trades':>15} {'points':>10} {'t net':>7} {'Sharpe':>7} {'t brut':>7}")
    resume = {}
    for nom in DECALAGES:
        x = tr[nom]
        je = (x["jour"] >= EXPLO[0]) & (x["jour"] <= EXPLO[1])
        jcf = (x["jour"] >= COFFRE[0]) & (x["jour"] <= COFFRE[1])
        r = dict(tre=int(je.sum()), trc=int(jcf.sum()), pe=float(S[nom][e].sum()), pc=float(S[nom][c].sum()),
                 te=PA.t_stat(S[nom][e]), tc=PA.t_stat(S[nom][c]), she=PA.sharpe(S[nom][e]), shc=PA.sharpe(S[nom][c]),
                 tbe=PA.t_stat(SB[nom][e]), tbc=PA.t_stat(SB[nom][c]))
        resume[nom] = r
        L.append(f"  {nom:5} | {r['tre']:14d} {r['pe']:+10.2f} {r['te']:+7.2f} {r['she']:+7.3f} {r['tbe']:+7.2f} |"
                 f" {r['trc']:15d} {r['pc']:+10.2f} {r['tc']:+7.2f} {r['shc']:+7.3f} {r['tbc']:+7.2f}")
    L.append("  (D0 = V1 sans les jours de la Fed : la reference des comparaisons de la piste)")

    # ------------------------------------------------------------------ ensembles
    L.append("")
    L.append("ENSEMBLES (critere 2 : Sharpe quotidien plus haut que V1 a la meme taille sur les deux periodes ; V1 a 2 ou")
    L.append("3 MNQ a le meme Sharpe que V1 a 1 MNQ, frais compris, puisque tout est multiplie par 2 ou 3)")
    crit2 = {}
    for ens, membres, q in (("E2", ["D0", "D15"], 2), ("E3", ["D0", "D10", "D20"], 3)):
        v = q * S["D0"]
        she, shc = PA.sharpe(S[ens][e]), PA.sharpe(S[ens][c])
        sve, svc = PA.sharpe(v[e]), PA.sharpe(v[c])
        crit2[ens] = (she > sve) and (shc > svc)
        L.append(f"  {ens} = {' + '.join(membres)} : exploration {S[ens][e].sum():+.2f} pt, Sharpe {she:+.3f} contre V1 a {q}"
                 f" MNQ {v[e].sum():+.2f} pt, Sharpe {sve:+.3f} ; coffre {S[ens][c].sum():+.2f} pt, Sharpe {shc:+.3f} contre"
                 f" {v[c].sum():+.2f} pt, Sharpe {svc:+.3f} -> {'oui' if crit2[ens] else 'non'}")
        L.append(f"     ecart-type quotidien : exploration {S[ens][e].std(ddof=1):.2f} contre {v[e].std(ddof=1):.2f} pt ;"
                 f" coffre {S[ens][c].std(ddof=1):.2f} contre {v[c].std(ddof=1):.2f} pt")

    # ------------------------------------------------------------------ challenges
    L.append("")
    L.append("CHALLENGES (moteur de la partie D : plus hauts et plus bas des minutes, niveau de prix du 20 octobre 2026,")
    L.append("departs 2023-2026 dont la fenetre tient dans les donnees ; position nette des copies dans le meme compte)")
    jcE2, cE2, bE2, hE2 = chemins(z, Hm, Lm, [tr["D0"], tr["D15"]])
    jcE3, cE3, bE3, hE3 = chemins(z, Hm, Lm, [tr["D0"], tr["D10"], tr["D20"]])
    assert (jcE2 == jc).all() and (jcE3 == jc).all()
    ch = {}
    for firme in (LUCID, BULENOX):
        ch[(firme, "V1 1 MNQ")] = challenge(jc, clo0, bas0, haut0, firme, 1)
        ch[(firme, "V1 2 MNQ")] = challenge(jc, clo0, bas0, haut0, firme, 2)
        ch[(firme, "V1 3 MNQ")] = challenge(jc, clo0, bas0, haut0, firme, 3)
        ch[(firme, "E2 (D0 + D15)")] = challenge(jc, cE2, bE2, hE2, firme, 1)
        ch[(firme, "E3 (D0 + D10 + D20)")] = challenge(jc, cE3, bE3, hE3, firme, 1)
    for firme in (LUCID, BULENOX):
        L.append(f"  {firme}{' (30 jours, publie)' if firme == BULENOX else ''} :")
        for lab in ("V1 1 MNQ", "V1 2 MNQ", "V1 3 MNQ", "E2 (D0 + D15)", "E3 (D0 + D10 + D20)"):
            r = ch[(firme, lab)]
            L.append(f"     {lab:22} valide {r['valide']:5.1f} %, perdu {r['perdu']:5.1f} %, expire {r['expire']:5.1f} %"
                     f" ({r['n']} departs)")
    v1 = max(("V1 1 MNQ", "V1 2 MNQ"), key=lambda lab: ch[(LUCID, lab)]["valide"])
    rE2, rv1 = ch[(LUCID, "E2 (D0 + D15)")], ch[(LUCID, v1)]
    crit3 = (rE2["valide"] >= rv1["valide"] + 2.0) and (rE2["perdu"] <= rv1["perdu"] + 2.0)
    L.append(f"  critere 3 (Lucid Flex) : E2 valide {rE2['valide']:.1f} % contre la meilleure de V1 a 1 et 2 MNQ ({v1},"
             f" {rv1['valide']:.1f} %) -> {rE2['valide'] - rv1['valide']:+.1f} points valides (au moins +2) ; perdus"
             f" {rE2['perdu']:.1f} % contre {rv1['perdu']:.1f} % -> {rE2['perdu'] - rv1['perdu']:+.1f} points (au plus +2)"
             f" -> {'oui' if crit3 else 'non'}")
    rE3 = ch[(LUCID, "E3 (D0 + D10 + D20)")]
    v13 = max(("V1 1 MNQ", "V1 2 MNQ", "V1 3 MNQ"), key=lambda lab: ch[(LUCID, lab)]["valide"])
    L.append(f"  information (le README ne fixe le critere 3 que pour E2) : E3 valide {rE3['valide']:.1f} % (perdu"
             f" {rE3['perdu']:.1f} %) ; meilleure de V1 a 1, 2 et 3 MNQ : {v13} {ch[(LUCID, v13)]['valide']:.1f} % (perdu"
             f" {ch[(LUCID, v13)]['perdu']:.1f} %)")

    # ------------------------------------------------------------------ decisions par test
    L.append("")
    L.append("TESTS (dans l'ordre du README ; unilateraux ; Benjamini-Hochberg calcule ensuite sur les 17 tests)")
    sortie = []
    for nom in TESTS:
        r = resume[nom]
        ens, membres = ENSEMBLE[nom]
        c1 = r["te"] >= 2.0
        c1b = r["tc"] >= 1.5
        c2 = crit2[ens]
        c3 = crit3 if ens == "E2" else None
        tous_ok = c1 and c1b and c2 and (c3 if c3 is not None else True)
        L.append(f"=== {nom} seule ===")
        L.append(f"  1) exploration : t net {f2(r['te'])} (p unilateral {PA.p_unilateral(r['te']):.4f}) -> t >= 2 :"
                 f" {'oui' if c1 else 'non'} ; coffre : t net {f2(r['tc'])} -> t >= 1,5 : {'oui' if c1b else 'non'}")
        L.append(f"  2) Sharpe de {ens} ({' + '.join(membres)}) plus haut que V1 a {len(membres)} MNQ sur les deux periodes :"
                 f" {'oui' if c2 else 'non'}")
        if c3 is not None:
            L.append(f"  3) Lucid Flex, E2 : {'oui' if c3 else 'non'}")
        else:
            L.append("  3) Lucid Flex : non fixe par le README pour E3 (publie ci-dessus, sans decision)")
        if ens == "E3":
            L.append("     (E3 demande aussi que D10 ET D20 passent chacune seule)")
        L.append(f"  -> criteres propres (hors Benjamini-Hochberg) : {'PASSENT' if tous_ok else 'ECHEC'}")
        sortie.append(dict(nom=nom, t_explo=r["te"], t_coffre=r["tc"], ok=tous_ok, c1=c1, c1b=c1b, c2=c2, c3=c3))

    # ------------------------------------------------------------------ controle b)
    L.append("")
    L.append("CONTROLE b) correlations quotidiennes (points nets, seances de zone)")
    noms = list(DECALAGES)
    for per, msk in (("exploration", e), ("coffre", c)):
        M = np.corrcoef(np.array([S[n_][msk] for n_ in noms]))
        L.append(f"  {per} : " + " ; ".join(f"{noms[a]}/{noms[b]} {f2(M[a, b], 2, False)}"
                                             for a in range(4) for b in range(a + 1, 4)))
    L.append("  (gain de Sharpe possible seulement si la correlation est nettement sous 1)")
    for per, msk in (("exploration", e), ("coffre", c)):
        if True:
            for m_ in ("D10", "D15", "D20"):
                act = msk & ((S[m_] != 0) | (S["D0"] != 0))
                ident = np.mean(S[m_][act] == S["D0"][act])
                L.append(f"  {per} : {m_} fait exactement le meme gain que D0 dans {ident * 100:.1f} % des {int(act.sum())}"
                         f" seances ou l'une des deux trade")

    # ------------------------------------------------------------------ controle c)
    L.append("")
    L.append("CONTROLE c) resultats par heure du controle d'entree (trades, points nets, moyenne par trade)")
    for nom, k in DECALAGES.items():
        x = tr[nom]
        L.append(f"  {nom} :")
        for m in controles(k):
            g = x[x["minute_entree"] == m]
            ge = g[(g["jour"] >= EXPLO[0]) & (g["jour"] <= EXPLO[1])]
            gc = g[(g["jour"] >= COFFRE[0]) & (g["jour"] <= COFFRE[1])]
            L.append(f"     {heure(m):6} exploration {len(ge):4d} trades {ge['points'].sum():+9.2f} pt"
                     f" ({ge['points'].mean() if len(ge) else 0:+6.2f}) | coffre {len(gc):4d} trades"
                     f" {gc['points'].sum():+9.2f} pt ({gc['points'].mean() if len(gc) else 0:+6.2f})")
    L.append("  premier controle de chaque copie (annonces de 10 h : D0 decide a 10 h 00 pile) :")
    for per, (a_, b_) in (("exploration", EXPLO), ("coffre", COFFRE)):
        parts = []
        for nom, k in DECALAGES.items():
            g = tr[nom]
            g = g[(g["minute_entree"] == controles(k)[0]) & (g["jour"] >= a_) & (g["jour"] <= b_)]
            parts.append(f"{nom} {heure(controles(k)[0])} {len(g)} trades {f2(g['points'].sum())} pt")
        L.append(f"     {per} : " + " ; ".join(parts))
    L.append("  sorties forcees a 15 h 59 et entrees au dernier controle :")
    for nom, k in DECALAGES.items():
        x = tr[nom]
        der = x[x["minute_entree"] == controles(k)[-1]]
        clo_ = x[x["minute_sortie"] == N - 1]
        L.append(f"     {nom} : {len(der)} entrees a {heure(controles(k)[-1])} ({f2(der['points'].sum())} pt, toutes"
                 f" periodes) ; {len(clo_)} trades sortis a 15h59 ({f2(clo_['points'].sum())} pt)")

    # ------------------------------------------------------------------ par annee (information)
    L.append("")
    L.append("PAR ANNEE (information, points nets, 1 MNQ par copie)")
    L.append("  annee " + "".join(f"{n_:>10}" for n_ in list(DECALAGES) + ["E2", "E3", "3 x D0"]))
    for an in sorted(set(ju.year)):
        msk = np.asarray(ju.year == an)
        L.append(f"  {an}  " + "".join(f"{S[n_][msk].sum():+10.1f}" for n_ in list(DECALAGES) + ["E2", "E3"])
                 + f"{3 * S['D0'][msk].sum():+10.1f}")

    # ------------------------------------------------------------------ controle d)
    L.append("")
    L.append("CONTROLE d) P1 (Databento 1er avril - 1er oct. 2026) et P2 (Rithmic 2 - 16 oct. 2026), vrai delta : description")
    zr = DM.preparer(robot)
    deltas = {**DM.par_jour(DM.minutes_databento()), **DM.par_jour(DM.minutes_rithmic())}
    ok_ref = True
    tabd = {}
    for per, (a_, b_) in (("P1", DM.P1), ("P2", DM.P2)):
        idx = [i for i in zr["jouables"] if pd.Timestamp(a_) <= zr["jours"][i] <= pd.Timestamp(b_)]
        dd_ = {j: v for j, v in deltas.items() if pd.Timestamp(a_) <= j <= pd.Timestamp(b_)}
        for nom, k in DECALAGES.items():
            x = DM.mesures(trades_copie(zr, idx, k, nom), dd_)
            x = x.assign(B=DM.garde(x, "brut", 0))
            tabd[(per, nom)] = x
            if nom == "D0":
                for lab, g in (("B", x["B"]), ("SANS", pd.Series(True, index=x.index))):
                    rn, rp = DM.REFERENCE[(lab, per)]
                    ok_ref &= int(g.sum()) == rn and abs(float(x.loc[g, "points"].sum()) - rp) < 1e-6
    L.append(f"  controle : D0 sur les barres du robot (tous les jours) redonne relance/resultats.txt (B P1 79 trades"
             f" +1 776,75 ; sans filtre P1 99 / +982,25 ; B P2 6 / +220,25 ; sans filtre P2 7 / +669,50) :"
             f" {'identique' if ok_ref else 'ECART'}")
    L.append("  filtre B de chaque copie : delta des 30 minutes qui finissent a SON controle d'entree, dans le sens du trade ;")
    L.append("  un trade ecarte reste virtuel jusqu'a sa sortie (comme Moteur.cs). Regle de la piste : sans les jours de la Fed.")
    L.append(f"  {'':4} {'copie':5} {'sans filtre : trades':>21} {'points':>9} | {'garde par B : trades':>21} {'points':>9}")
    for per in ("P1", "P2"):
        totS, totB = {}, {}
        for nom in DECALAGES:
            x = tabd[(per, nom)]
            x = x[~x["jour"].isin(fed)]
            g = x["B"].astype(bool)
            totS[nom], totB[nom] = float(x["points"].sum()), float(x.loc[g, "points"].sum())
            L.append(f"  {per:4} {nom:5} {len(x):21d} {totS[nom]:+9.2f} | {int(g.sum()):21d} {totB[nom]:+9.2f}")
        L.append(f"  {per:4} E2 (D0 + D15) sans filtre {totS['D0'] + totS['D15']:+.2f}, avec B {totB['D0'] + totB['D15']:+.2f}"
                 f" ; E3 sans filtre {totS['D0'] + totS['D10'] + totS['D20']:+.2f}, avec B"
                 f" {totB['D0'] + totB['D10'] + totB['D20']:+.2f} ; V1 x 2 avec B {2 * totB['D0']:+.2f}, x 3 {3 * totB['D0']:+.2f}")
    L.append("  (6 mois et 2 semaines : description seulement, aucune decision)")

    # ------------------------------------------------------------------ controle e)
    L.append("")
    L.append("CONTROLE e) rapprochement avec la grille de robustesse (kb/robustesse/robustesse.json)")
    rob = json.loads(ROBUSTESSE.read_text())
    gz = rob["grille"]["zone"]
    shg = np.array(gz["sharpe"])
    base = gz["base"]
    L.append(f"  grille : 180 zones (jours de moyenne x pas de controle x largeur x sortie), {ROB_PERIODE[0]} - {ROB_PERIODE[1]},"
             f" $ par seance au prix d'aujourd'hui, jours de la Fed a 0 ; reglage du bot (14 j, 30 min, x 1, VWAP) Sharpe"
             f" {f2(shg[base], 3)}, au-dessus de {(shg < shg[base]).mean() * 100:.1f} % des 180 zones (le rang de 99 % du"
             f" README est celui des 14 400 bots zone + RSI(2) : {rob['grille']['bots']['rang_sh'] * 100:.1f} %)")
    L.append(f"  mediane des 180 zones {f2(np.median(shg), 3)} ; zones a 30 minutes : mediane"
             f" {f2(np.median([s_ for p_, s_ in zip(gz['params'], shg) if p_[1] == 30]), 3)}")
    jr = pd.DatetimeIndex(z["jours"])
    mr = (jr >= ROB_PERIODE[0]) & (jr <= ROB_PERIODE[1])
    idx_fin = {j: i for i, j in enumerate(z["jours"])}
    rangs = {}
    ref = float(z["C"][idx_fin[fin], N - 1])
    for nom in DECALAGES:
        x = tr[nom]
        o = pd.Series(z["C"][:, 0], index=jr)
        usd = (x["brut"].to_numpy() * PT * ref / o.reindex(x["jour"]).to_numpy() - COUT * PT)
        sr = pd.Series(usd, index=x["jour"].to_numpy()).groupby(level=0).sum().reindex(jr[mr]).fillna(0.0).to_numpy()
        sh_ = PA.sharpe(sr)
        rangs[nom] = (shg < sh_).mean() * 100
        L.append(f"  {nom} : Sharpe {f2(sh_, 3)} sur {int(mr.sum())} seances -> au-dessus de {(shg < sh_).mean() * 100:5.1f} %"
                 f" des 180 zones")
        if nom == "D0":
            eq = rob["equite"]
            zb = np.diff(np.r_[0.0, np.array(eq["series"]["zone_brut"], float)])
            zb = pd.Series(zb, index=pd.DatetimeIndex(eq["dates"])).reindex(jr[mr])
            okc = zb.notna().to_numpy()
            L.append(f"     validation de l'unite : correlation quotidienne D0 / serie zone_brut de robustesse"
                     f" ({int(okc.sum())} seances communes) : {f2(np.corrcoef(sr[okc], zb.to_numpy()[okc])[0, 1], 4, False)}")
    L.append("  (meme periode et meme unite que la grille ; petit ecart de D0 avec le reglage du bot : robustesse ramene le")
    L.append("  niveau de prix par son propre facteur quotidien, ici par la cloture de la premiere minute du jour comme la partie D)")

    # ------------------------------------------------------------------ synthese
    L.append("")
    L.append("SYNTHESE")
    for s_ in sortie:
        L.append(f"  {s_['nom']:4} : t exploration {f2(s_['t_explo'])}, t coffre {f2(s_['t_coffre'])} -> criteres propres"
                 f" {'PASSENT' if s_['ok'] else 'ECHEC'} (explo >= 2 {'oui' if s_['c1'] else 'non'}, coffre >= 1,5"
                 f" {'oui' if s_['c1b'] else 'non'}, Sharpe de l'ensemble {'oui' if s_['c2'] else 'non'}"
                 + (f", Lucid {'oui' if s_['c3'] else 'non'}" if s_['c3'] is not None else ", Lucid non fixe pour E3") + ")")
    L.append("  Decision : une copie decalee n'entre au robot virtuel que si elle passe ses criteres ET Benjamini-Hochberg a")
    L.append("  10 % sur les 17 tests, puis la contre-verification adverse.")
    L.append("")
    L.append("LECTURE")
    L.append(f"  - Les trois copies decalees gagnent avant et apres frais, mais moins que D0 en exploration (t {f2(resume['D10']['te'])},")
    L.append(f"    {f2(resume['D15']['te'])}, {f2(resume['D20']['te'])} contre {f2(resume['D0']['te'])}) ; aucune n'atteint t >= 2. Elles sont tres")
    cors = [np.corrcoef(S["D0"][msk], S[n_][msk])[0, 1] for msk in (e, c) for n_ in ("D10", "D15", "D20")]
    L.append(f"    correlees a D0 ({f2(min(cors), 2, False)} a {f2(max(cors), 2, False)}), si bien que E2 et E3 ont un Sharpe plus bas"
             f" que V1 a la meme taille sur les deux")
    L.append("    periodes : la diversification ne compense pas la perte d'esperance des copies.")
    L.append(f"  - Controle e) : D0 est au-dessus de {rangs['D0']:.0f} % des 180 zones de la grille, les copies decalees entre"
             f" {min(rangs[n_] for n_ in TESTS):.0f} et {max(rangs[n_] for n_ in TESTS):.0f} % :")
    prem = {n_: tr[n_][(tr[n_]["minute_entree"] == controles(k)[0])] for n_, k in DECALAGES.items()}
    pe_ = {n_: float(g[(g["jour"] >= EXPLO[0]) & (g["jour"] <= EXPLO[1])]["points"].sum()) for n_, g in prem.items()}
    pc_ = {n_: float(g[(g["jour"] >= COFFRE[0]) & (g["jour"] <= COFFRE[1])]["points"].sum()) for n_, g in prem.items()}
    L.append("    une partie du resultat de V1 tient a l'horaire :00 / :30. En exploration, le premier controle pese lourd")
    L.append(f"    (10h00 {f2(pe_['D0'])} pt ; 10h10 {f2(pe_['D10'])} ; 10h15 {f2(pe_['D15'])} ; 10h20 {f2(pe_['D20'])}) ; au coffre l'ordre"
             f" change (10h00 {f2(pc_['D0'])} ; 10h10 {f2(pc_['D10'])} ; 10h15 {f2(pc_['D15'])} ; 10h20 {f2(pc_['D20'])}).")
    L.append("  - Chez Lucid Flex, E2 (2 MNQ) valide comme V1 a 2 MNQ et bien moins que V1 a 1 MNQ : l'exposition double pese plus")
    L.append("    que le gain de diversification.")
    L += ["", "ECARTS ET INTERPRETATIONS (aucun reglage apres les chiffres)",
          "  - Derniere entree : V1 permet une entree a son dernier controle (15 h 30). La meme regle exacte permet donc une",
          "    entree a 15 h 40 (D10), 15 h 45 (D15) et 15 h 50 (D20), tenue jusqu'a 15 h 59 (voir le controle c).",
          "  - Controle a) : les chiffres du README (3 572 trades, +10 721 pt) viennent des barres du 20 octobre au matin,",
          "    jusqu'au 19 octobre ; la barre de 11 h 30 du 19 octobre a ete retelechargee depuis (delta_mesures). D0 est donc",
          "    comparee trade par trade a delta_mesures trades_zone, et a entree_tardive jusqu'au 16 octobre (identique).",
          "  - Critere 2 : V1 a 2 ou 3 MNQ a le Sharpe de V1 a 1 MNQ. Series en points nets, comme le repere de V1.",
          "  - Critere 3 : le README ne le fixe que pour E2 (donc pour D15) ; pour E3 (D10, D20), Lucid est publie sans",
          "    decision. \"Sans plus de 2 points de perdus en plus\" est lu contre la meme meilleure V1 (ici V1 a 1 MNQ) ;",
          "    E2 echoue aussi contre V1 a 2 MNQ (valides +0,0 point, il en faut +2).",
          "  - Challenges a plusieurs copies : moteur de la partie D, plus haut et plus bas de chaque minute pris sur la",
          "    position nette des copies (D0 seule redonne partie_d.chemins_zone a 0 $ pres). Frais de chaque copie comptes.",
          "  - Controle d) : regle de la piste sans les jours de la Fed ; la verification de D0 contre relance/ garde tous les",
          "    jours, comme delta_mesures.",
          "  - Controle e) : la grille de robustesse classe des zones seules (180) ; le rang de 99 % cite par le README est",
          "    celui des 14 400 bots zone + RSI(2). Les copies sont placees dans la grille des zones, meme periode et unite."]

    texte = "\n".join(L)
    print(texte)
    (ICI / "resultats.txt").write_text(texte + "\n")


if __name__ == "__main__":
    main()
