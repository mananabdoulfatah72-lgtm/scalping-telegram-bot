#!/usr/bin/env python3
"""delta_mesures/README.md (regles fixees le 21 octobre 2026, avant tout calcul).
Mesures 1 et 2 : filtres B (delta brut, le bot), P (proportion du volume) et Z (z-score de la seance) sur P1 (Databento)
et P2 (Rithmic). Le chemin de la zone ne depend pas du filtre (un trade ecarte reste virtuel jusqu'a sa sortie, comme
Moteur.cs) : chaque filtre garde une partie des memes trades de la zone sans filtre.
Mesure 3 (information) : challenge depuis la situation estimee de l'utilisateur, 15 ans sans filtre, seances jouees
par vague4/moteur4.seance4 (sans changement), boucle de vague13/moteur13.defi13 recopiee avec un etat de depart.

Controles : B redonne relance/resultats.txt (H1 et zone sans filtre sur P1 et P2) ; la zone sans filtre sur 15 ans
redonne entree_tardive/ (3 572 trades, +10 721,25 points jusqu'au 19 octobre 2026) ; la boucle recopiee, depuis un
compte neuf, redonne entree_tardive/resultats_challenge.txt (H1 : 3 784 departs, 44,9 % / 38,7 % / 16,4 %).

Lancer : python3 delta_mesures/etude.py (numba, scipy, pandas). Variable KB : branche de recherche extraite, par
exemple git worktree add ../recherche origin/claude/keen-babbage-r686cl. Ecrit resultats.txt et trades.csv."""
import os
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
os.environ.setdefault("NUMBA_CACHE_DIR", str(Path(tempfile.gettempdir()) / "numba_delta_mesures"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ICI = Path(__file__).resolve().parent
KB = Path(os.getenv("KB", str(ICI.parent.parent / "recherche")))
sys.path.insert(0, str(ICI.parent / "zone"))
sys.path.insert(0, str(KB / "vague13"))
sys.path.insert(0, str(KB / "fonds"))
import robot as RB  # noqa: E402  (constantes et fonctions, main() seulement sous __main__)

N, PAS, COUT, JM = RB.N, RB.PAS, RB.COUT, RB.JOURS_MOYENNE
ROBOT = ICI.parent / "zone" / "robot" / "nq_1min.csv.gz"
RECHERCHE = KB / "intraday" / "donnees" / "nasdaq100_1min.csv.gz"
DATABENTO = [KB / "orderflow" / "donnees" / f"nq_secondes_{i}.csv.gz" for i in (1, 2, 3)]
RITHMIC = KB / "filtre_h1" / "donnees_rithmic" / "transactions_NQZ6_rithmic.csv"
P1 = ("2026-04-01", "2026-10-01")
P2 = ("2026-10-02", "2026-10-16")
FIN = "2026-10-20"                        # derniere seance complete (le 21 octobre est partiel)
DERNIERE_ENTREE = 360                     # 15 h 30
# relance/resultats.txt (rejeu C# du bot) et entree_tardive/resultats_delta.txt (barres du robot du 20 octobre)
REFERENCE = {("B", "P1"): (79, 1776.75), ("SANS", "P1"): (99, 982.25), ("B", "P2"): (6, 220.25), ("SANS", "P2"): (7, 669.5)}
# variantes de la decision, puis seuils descriptifs
FILTRES = [("B", "brut", 0.0), ("P", "prop", 0.01), ("Z", "z", 1.0)]
DESCRIPTIFS = [("P 0,5 %", "prop", 0.005), ("P 2 %", "prop", 0.02), ("P 5 %", "prop", 0.05),
               ("Z 0,5", "z", 0.5), ("Z 1,5", "z", 1.5), ("Z 2", "z", 2.0)]
# mesure 3 : situation estimee de l'utilisateur (README), en $ par rapport au solde de depart de 50 000 $
SOLDE, PLUS_HAUT, SEANCES = 49158.0 - 50000.0, 51172.0 - 50000.0, 16
COMPTE = (3000.0, 2500.0, 0, 100.0, 1000.0)     # objectif, perte max, mode fin de journee, blocage, limite du jour
TAILLES = [("1 MNQ", 1, 1, 0), ("2 MNQ", 2, 2, 0), ("3 MNQ", 3, 3, 0), ("4 MNQ", 4, 4, 0),
           ("4 MNQ puis 6 (reglage actuel)", 4, 6, 5)]


def heure(m):
    return f"{(570 + m) // 60}h{(570 + m) % 60:02d}"


# ----------------------------------------------------------------------------- zone (comme Moteur.cs, sans filtre)
def preparer(d):
    """Tableaux de la zone, comme robot.py zone_de_bruit (memes fonctions) : sigma a chaque minute, VWAP, references."""
    jours, O, H, L, C, P, V, echeance = RB.tableaux(d)
    ok = RB.seances_completes(P)
    ouverture = O[:, 0]
    prec = RB.precedente(ok, np.cumsum(echeance))
    veille = np.where(prec >= 0, C[np.maximum(prec, 0), N - 1], np.nan)
    mouvement = np.abs(C / ouverture[:, None] - 1)
    sigma = np.full_like(mouvement, np.nan)
    sigma[ok] = pd.DataFrame(mouvement[ok]).rolling(JM, min_periods=JM).mean().shift(1).values
    typique = (H + L + C) / 3
    cumv = np.cumsum(V, axis=1)
    vwap = np.where(cumv > 0, np.cumsum(typique * V, axis=1) / np.where(cumv > 0, cumv, 1),
                    np.cumsum(typique, axis=1) / np.arange(1, N + 1))
    jouables = np.where(ok & ~np.isnan(veille) & ~np.isnan(sigma[:, PAS]))[0]
    return dict(jours=pd.DatetimeIndex(jours), C=C, sigma=sigma, vwap=vwap, href=np.fmax(ouverture, veille),
                bref=np.fmin(ouverture, veille), jouables=jouables)


def zone_jour(C, sigma, vwap, href, bref):
    """Trades de la zone sans filtre d'une seance : entree aux controles (10 h - 15 h 30) si la cloture sort de la zone,
    sortie a un controle si le prix repasse max(limite haute, VWAP) (achat) ou min(limite basse, VWAP) (vente), ou a
    16 h. Liste de (minute d'entree, sens, prix d'entree, minute de sortie, prix de sortie)."""
    out, virt, t = [], 0, None
    for m in range(PAS, N):
        p = C[m]
        if m == N - 1:
            if virt:
                out.append((*t, m, p))
            break
        if m % PAS:
            continue
        s = sigma[m]
        ub, lb = href * (1 + s), bref * (1 - s)
        if virt and ((virt > 0 and p <= max(ub, vwap[m])) or (virt < 0 and p >= min(lb, vwap[m]))):
            out.append((*t, m, p))
            virt, t = 0, None
        if not virt and m <= DERNIERE_ENTREE:
            sens = 1 if p > ub else (-1 if p < lb else 0)
            if sens:
                virt, t = sens, (m, sens, p)
    return out


def trades_zone(z, debut, fin):
    lignes = []
    for i in z["jouables"]:
        j = z["jours"][i]
        if not (pd.Timestamp(debut) <= j <= pd.Timestamp(fin)):
            continue
        for me, sens, pe, ms, ps in zone_jour(z["C"][i], z["sigma"][i], z["vwap"][i], z["href"][i], z["bref"][i]):
            lignes.append(dict(jour=j, minute_entree=me, sens=sens, prix_entree=pe, minute_sortie=ms, prix_sortie=ps,
                               points=sens * (ps - pe) - COUT))
    return pd.DataFrame(lignes)


# ----------------------------------------------------------------------------- delta
def minutes_databento():
    m = []
    for f in DATABENTO:
        x = pd.read_csv(f, usecols=["t", "achat", "vente"])
        t = x["t"].str
        x["jour"] = pd.to_datetime(t[:10])
        x["minute"] = t[11:13].astype(int) * 60 + t[14:16].astype(int) - 570
        m.append(x.groupby(["jour", "minute"])[["achat", "vente"]].sum().reset_index())
    x = pd.concat(m).groupby(["jour", "minute"])[["achat", "vente"]].sum().reset_index()
    return x.rename(columns={"achat": "achats", "vente": "ventes"})


def minutes_rithmic():
    x = pd.read_csv(RITHMIC)
    x = x.groupby(["jour", "minute"], as_index=False)[["achats", "ventes"]].sum()
    x["jour"] = pd.to_datetime(x["jour"])
    return x


def par_jour(x):
    """jour -> (delta par minute, volume agresseur par minute), 390 valeurs, 0 pour une minute sans transaction."""
    x = x[(x["minute"] >= 0) & (x["minute"] < N)]
    out = {}
    for j, g in x.groupby("jour"):
        d, v = np.zeros(N), np.zeros(N)
        mi = g["minute"].to_numpy()
        d[mi] = (g["achats"] - g["ventes"]).to_numpy()
        v[mi] = (g["achats"] + g["ventes"]).to_numpy()
        out[pd.Timestamp(j)] = (d, v)
    return out


def mesures(tr, deltas):
    """D30, V30, R = D30 / V30 et Z = D30 / (sigma racine(30)) a la minute du signal. Seance sans transaction : tout a 0
    (le trade est ecarte par chaque filtre, comme Moteur.cs avec un delta nul)."""
    D30, V30, R, Z = [], [], [], []
    for r in tr.itertuples():
        d, v = deltas.get(r.jour, (np.zeros(N), np.zeros(N)))
        m = r.minute_entree
        a = max(0, m - 29)
        dd, vv = d[a:m + 1].sum(), v[a:m + 1].sum()
        s = d[:m + 1].std(ddof=1)
        D30.append(dd); V30.append(vv)
        R.append(dd / vv if vv > 0 else 0.0)
        Z.append(dd / (s * np.sqrt(30)) if s > 0 else 0.0)
    return tr.assign(D30=D30, V30=V30, R=R, Z=Z)


def garde(tr, mesure, seuil):
    x = tr["sens"] * (tr["D30"] if mesure == "brut" else tr["R"] if mesure == "prop" else tr["Z"])
    return (x > 0) if mesure == "brut" else (x >= seuil)


def bilan(tr, g):
    x = tr[g].sort_values(["jour", "minute_entree"])
    pts = x["points"].to_numpy()
    c = np.cumsum(pts)
    baisse = float(np.max(np.maximum.accumulate(np.r_[0.0, c]) - np.r_[0.0, c])) if len(c) else 0.0
    jour = x.groupby("jour")["points"].sum()
    return dict(trades=len(x), points=float(pts.sum()), gagnants=float((pts > 0).mean() * 100) if len(pts) else 0.0,
                baisse=baisse, pire=float(jour.min()) if len(jour) else 0.0,
                pire_jour=jour.idxmin().date().isoformat() if len(jour) else "")


# ----------------------------------------------------------------------------- mesure 3 : challenge
def donnees_challenge(bars, z, tr15):
    """Comme entree_tardive/challenge.py donnees, zone et base : minutes comblees par la suivante, prix ramenes au niveau
    de la derniere cloture, jours de la Fed sans zone, RSI(2) et ES absents."""
    import fomc
    jours, O, H, L, C, Pr, V, ech = RB.tableaux(bars)
    der = (N - 1 - np.argmax(Pr[:, ::-1], axis=1)).astype(np.int64)
    O, H, L, C = (pd.DataFrame(a).bfill(axis=1).to_numpy() for a in (O, H, L, C))
    nj = len(jours)
    cl = C[np.arange(nj), der]
    kN = 2.0 * cl[-1] / np.r_[cl[0], cl[:-1]]
    j = pd.DatetimeIndex(jours)
    fed = j.isin(fomc.annonces())
    d = np.searchsorted(j, tr15["jour"].to_numpy())
    me, ms, sens = (tr15[c].to_numpy(np.int64) for c in ("minute_entree", "minute_sortie", "sens"))
    assert np.abs(C[d, me] - tr15["prix_entree"].to_numpy()).max() < 1e-9
    assert np.abs(C[d, ms] - tr15["prix_sortie"].to_numpy()).max() < 1e-9
    gd = (~fed[d]).astype(np.int64)
    o = np.lexsort((me, d))
    d, me, ms, sens, gd = d[o], me[o], ms[o], sens[o], gd[o]
    z_deb = np.searchsorted(d, np.arange(nj)).astype(np.int64)
    z_fin = np.searchsorted(d, np.arange(nj), side="right").astype(np.int64)
    dec, voulu = np.full(nj, -1, np.int64), np.zeros(nj, np.int64)
    nuit, nn = np.full((nj, 1), np.nan), np.zeros(nj, np.int64)
    b = (O, H, L, C, der, z_deb, z_fin, me, ms, sens, gd, dec, voulu, nuit, nuit, nuit, nn, O, H, L, C, nuit, nuit,
         nuit, nn, np.zeros(nj, np.int64))
    return j, kN, b


def defi_depuis(debut, lim, kN, b, q, q_fin, n_fin, cash, pic_eod):
    """Boucle de moteur13.defi13 (sans RSI(2), sans frein, arret a l'objectif + 50 $), depuis un solde et un plus haut de
    fin de journee donnes. Renvoie (1 valide / -1 perdu / 0 expire, seances jouees)."""
    import moteur13 as M13
    e_obj, e_perte, e_mode, e_bloc, e_dll = COMPTE
    fin = min(b[0].shape[0], debut + lim)
    veut, pic_rt = 0, 0.0
    plancher = min(pic_eod - e_perte, e_bloc)
    d = debut
    while d < fin:
        qc = q_fin if n_fin > 0 and lim - (d - debut) <= n_fin else q
        cap = max(e_obj + 50.0 - cash, 0.0)
        perdu, cash, veut, pic_rt, plancher, _ = M13.seance4(d, 0, veut, cash, pic_rt, plancher, e_mode, e_perte, e_bloc,
                                                             e_dll, *b, kN[d], kN[d], qc, 0, cap)
        if perdu:
            return -1, d - debut + 1
        pic_eod = max(pic_eod, cash)
        plancher = min(pic_eod - e_perte, e_bloc)
        d += 1
        if cash >= e_obj:
            return 1, d - debut
    return 0, fin - debut


def challenge(bars, z, tr15, cash, pic_eod, tailles, lim=SEANCES):
    j, kN, b = donnees_challenge(bars, z, tr15)
    debuts = np.arange(np.searchsorted(j, pd.Timestamp("2012-01-01")), len(j) - lim + 1)
    recent = j[debuts] >= pd.Timestamp("2023-01-01")
    res = []
    for nom, q, qf, nf in tailles:
        x = np.array([defi_depuis(int(d), lim, kN, b, q, qf, nf, cash, pic_eod) for d in debuts])
        for per, m in (("2012-2026", np.ones(len(debuts), bool)), ("2023-2026", recent)):
            iss, n = x[m, 0], x[m, 1]
            res.append(dict(taille=nom, departs=per, n=int(m.sum()), valide=(iss == 1).mean() * 100,
                            perdu=(iss == -1).mean() * 100, expire=(iss == 0).mean() * 100,
                            seances_valide=float(np.median(n[iss == 1])) if (iss == 1).any() else float("nan"),
                            seances_perdu=float(np.median(n[iss == -1])) if (iss == -1).any() else float("nan")))
    return res


# ----------------------------------------------------------------------------- principal
def main():
    L = []
    robot = pd.read_csv(ROBOT)
    robot = robot[robot["t"] <= FIN + " 23:59"]
    z = preparer(robot)
    deltas = {**par_jour(minutes_databento()), **par_jour(minutes_rithmic())}
    periodes = {"P1": P1, "P2": P2}
    tous = []
    for per, (a, b) in periodes.items():
        tr = mesures(trades_zone(z, a, b), {j: v for j, v in deltas.items() if pd.Timestamp(a) <= j <= pd.Timestamp(b)})
        tous.append(tr.assign(periode=per))
    tr = pd.concat(tous, ignore_index=True)

    L.append("Mesures 1 et 2 (delta_mesures/README.md) : trades de la zone sans filtre, gardes par chaque filtre.")
    L.append("P1 = Databento 2026-04-01 - 2026-10-01 ; P2 = Rithmic 2026-10-02 - 2026-10-16 ; barres du robot.")
    L.append("Controle contre relance/resultats.txt :")
    ok = True
    for per in periodes:
        x = tr[tr["periode"] == per]
        for nom, g in (("B", garde(x, "brut", 0)), ("SANS", pd.Series(True, index=x.index))):
            n, p = int(g.sum()), float(x.loc[g, "points"].sum())
            rn, rp = REFERENCE[(nom, per)]
            bon = n == rn and abs(p - rp) < 1e-6
            ok &= bon
            L.append(f"  {nom:4} {per} : {n} trades {p:+.2f} pt ; reference {rn} trades {rp:+.2f} -> {'identique' if bon else 'ECART'}")
    if not ok:
        L.append("  -> ECART : resultats non publies")
        print("\n".join(L))
        sys.exit(1)

    for per in list(periodes) + ["P1 + P2"]:
        x = tr if per == "P1 + P2" else tr[tr["periode"] == per]
        L.append(f"\n{per} : {len(x)} trades de zone sans filtre")
        L.append(f"{'filtre':16} {'trades':>6} {'points':>9} {'gagnants':>9} {'pire baisse':>12} {'pire seance':>22}")
        lignes = [("sans filtre", pd.Series(True, index=x.index))]
        lignes += [(f"{n} (decision)", garde(x, m, s)) for n, m, s in FILTRES]
        lignes += [(f"{n} (info)", garde(x, m, s)) for n, m, s in DESCRIPTIFS]
        for nom, g in lignes:
            r = bilan(x, g)
            L.append(f"{nom:16} {r['trades']:6d} {r['points']:+9.2f} {r['gagnants']:8.1f}% {r['baisse']:12.2f}"
                     f" {r['pire']:+10.2f} ({r['pire_jour']})")

    L.append("\nMesure 2 : trades gardes par B mais ecartes par P ou Z")
    gB = garde(tr, "brut", 0)
    decision = {}
    for n, m, s in FILTRES[1:]:
        g = garde(tr, m, s)
        e = tr[gB & ~g]
        moy = float(e["points"].mean()) if len(e) else float("nan")
        L.append(f"  {n} : {len(e)} trades ecartes en plus de B, {e['points'].sum():+.2f} pt, moyenne {moy:+.2f} pt")
        for r in e.itertuples():
            L.append(f"     {r.jour.date()} {heure(r.minute_entree)} {'achat' if r.sens > 0 else 'vente'} {r.points:+8.2f} pt"
                     f" (delta {r.D30:+.0f}, {r.R * 100:+.2f} % du volume, z {r.Z:+.2f})")
        pts = {per: (float(tr.loc[(tr["periode"] == per) & g, "points"].sum()),
                     float(tr.loc[(tr["periode"] == per) & gB, "points"].sum())) for per in periodes}
        c1 = all(v >= vb for v, vb in pts.values())
        c2 = len(e) >= 10 and moy < 0
        decision[n] = (c1 and c2, float(tr.loc[g, "points"].sum()))
        L.append(f"     critere 1 (points >= B sur P1 et P2) : {'oui' if c1 else 'non'}"
                 f" ({', '.join(f'{per} {v:+.2f} contre {vb:+.2f}' for per, (v, vb) in pts.items())})")
        L.append(f"     critere 2 (au moins 10 trades ecartes en plus, moyenne negative) : {'oui' if c2 else 'non'}")
    passent = [n for n, (p, _) in decision.items() if p]
    choix = max(passent, key=lambda n: decision[n][1]) if passent else "B"
    L.append(f"\nDecision fixee a l'avance : {'le bot passe a ' + choix if passent else 'aucune variante ne passe, le bot garde B'}")

    # ------------------------------------------------------------- mesure 3
    L.append("\nMesure 3 (information) : challenge depuis la situation estimee, 15 ans sans filtre")
    rech = pd.read_csv(RECHERCHE)
    bars = pd.concat([rech, robot[robot["t"] > rech["t"].iloc[-1]]], ignore_index=True)
    # controle : zone sans filtre sur 15 ans et challenge depuis un compte neuf, donnees jusqu'au 19 octobre comme
    # entree_tardive/
    b19 = bars[bars["t"] <= "2026-10-19 23:59"]
    z19 = preparer(b19)
    tr19 = trades_zone(z19, "2000-01-01", "2026-10-19")
    # entree_tardive a utilise les barres du robot du 20 octobre au matin ; la barre du 19 octobre a 11 h 30 a ete
    # retelechargee le jour meme (cloture 29 944,75 -> 29 945,75, achat de 11 h 30) : comparaison jusqu'au 16 octobre
    t16 = tr19[tr19["jour"] <= pd.Timestamp("2026-10-16")]
    bon15 = len(t16) == 3571 and abs(t16["points"].sum() - (10721.25 + 38.5)) < 1e-6
    L.append(f"  controle 15 ans jusqu'au 16 octobre : {len(t16)} trades {t16['points'].sum():+.2f} pt ; entree_tardive sans le"
             f" 19 octobre (-38,50 pt) : 3571 trades +10759.75 -> {'identique' if bon15 else 'ECART'} ; le 19 octobre ici"
             f" {tr19['points'].sum() - t16['points'].sum():+.2f} pt (barre de 11 h 30 retelechargee par le robot le 20 octobre)")
    r0 = challenge(b19, z19, tr19, 0.0, 0.0, [("4 puis 6", 4, 6, 5)])[0]
    bonc = r0["n"] == 3784 and round(r0["valide"], 1) == 44.9 and round(r0["perdu"], 1) == 38.7 and round(r0["expire"], 1) == 16.4
    L.append(f"  controle challenge depuis un compte neuf (4 puis 6 MNQ, 16 seances) : {r0['n']} departs, valide"
             f" {r0['valide']:.1f} %, perdu {r0['perdu']:.1f} %, expire {r0['expire']:.1f} % ; entree_tardive 3784,"
             f" 44,9 / 38,7 / 16,4 -> {'identique' if bonc else 'ECART'}")
    z15 = preparer(bars)
    tr15 = trades_zone(z15, "2000-01-01", FIN)
    L.append(f"  situation : solde {50000 + SOLDE:.0f} $, plus haut de fin de journee {50000 + PLUS_HAUT:.0f} $, plancher"
             f" {50000 + min(PLUS_HAUT - COMPTE[1], COMPTE[3]):.0f} $, objectif 53 000 $, {SEANCES} seances, limite du jour 1 000 $")
    L.append(f"  {'taille':32} {'departs':>9} {'valide':>7} {'perdu':>7} {'expire':>7} {'seances (valide / perdu)':>26}")
    for r in challenge(bars, z15, tr15, SOLDE, PLUS_HAUT, TAILLES):
        L.append(f"  {r['taille']:32} {r['departs']:>9} {r['valide']:6.1f}% {r['perdu']:6.1f}% {r['expire']:6.1f}%"
                 f"   {r['seances_valide']:5.0f} / {r['seances_perdu']:5.0f}   ({r['n']} departs)")

    texte = "\n".join(L)
    print(texte)
    (ICI / "resultats.txt").write_text(texte + "\n")
    tr.assign(B=garde(tr, "brut", 0), P=garde(tr, "prop", 0.01), Z=garde(tr, "z", 1.0)).to_csv(
        ICI / "trades.csv", index=False, float_format="%.4f")


if __name__ == "__main__":
    main()
