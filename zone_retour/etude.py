#!/usr/bin/env python3
"""zone_retour/README.md (regles fixees le 21 octobre 2026, avant tout calcul) : zone sans filtre, V1 (le bot sans le
filtre delta), C1 (entree a chaque minute, sortie des le retour dans la zone), C2 (entrees aux controles, sortie comme
C1), C3 (C1, pas de nouvelle entree avant le controle suivant une sortie).
Mesures : 15 ans (t des gains quotidiens, gagnants, gain et perte moyens, limite du jour), challenge depuis 0, challenge
depuis la situation estimee de l'utilisateur, et pour information 2 - 16 octobre et 13 - 20 octobre 2026.
Donnees, zone et moteur du challenge : ceux de delta_mesures/etude.py (memes controles).

Lancer : python3 zone_retour/etude.py (numba, scipy, pandas ; variable KB comme delta_mesures). Ecrit resultats.txt."""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "delta_mesures"))
import etude as DM  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

N, PAS, COUT = DM.N, DM.PAS, DM.COUT
VARIANTES = ["V1", "C1", "C2", "C3"]
MNQ = 4


def jouer(C, sigma, vwap, href, bref, var):
    """Une seance : liste de (minute d'entree, sens, prix d'entree, minute de sortie, prix de sortie)."""
    out, pos, t, libre = [], 0, None, PAS
    for m in range(PAS, N):
        p = C[m]
        if m == N - 1:
            if pos:
                out.append((*t, m, p))
            break
        controle = m % PAS == 0
        s = sigma[m]
        ub, lb = href * (1 + s), bref * (1 - s)
        if pos:
            if var == "V1":
                sortie = controle and ((pos > 0 and p <= max(ub, vwap[m])) or (pos < 0 and p >= min(lb, vwap[m])))
            else:
                sortie = (pos > 0 and p <= ub) or (pos < 0 and p >= lb)
            if sortie:
                out.append((*t, m, p))
                pos, t = 0, None
                if var == "C3":
                    libre = (m // PAS + 1) * PAS
        if not pos and m <= DM.DERNIERE_ENTREE and (controle if var in ("V1", "C2") else m >= libre):
            sens = 1 if p > ub else (-1 if p < lb else 0)
            if sens:
                pos, t = sens, (m, sens, p)
    return out


def trades(z, var, debut="2000-01-01", fin=DM.FIN):
    lignes = []
    for i in z["jouables"]:
        j = z["jours"][i]
        if not (pd.Timestamp(debut) <= j <= pd.Timestamp(fin)):
            continue
        for me, sens, pe, ms, ps in jouer(z["C"][i], z["sigma"][i], z["vwap"][i], z["href"][i], z["bref"][i], var):
            lignes.append(dict(jour=j, minute_entree=me, sens=sens, prix_entree=pe, minute_sortie=ms, prix_sortie=ps,
                               points=sens * (ps - pe) - COUT))
    return pd.DataFrame(lignes)


def t_stat(x):
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x)))


def limite_jour(bars, tr, q=MNQ, debut="2012-01-01"):
    """Part des seances (2012 - fin, jouees une a une, sans plancher ni objectif, q MNQ) ou la limite du jour coupe le
    bot : comme entree_tardive/challenge.py limite_hors_challenge."""
    import moteur13 as M13
    j, kN, b = DM.donnees_challenge(bars, None, tr)
    e_obj, e_perte, e_mode, e_bloc, e_dll = DM.COMPTE
    seances = np.arange(np.searchsorted(j, pd.Timestamp(debut)), len(j))
    n = 0
    for d in seances:
        r = M13.seance4(int(d), 0, 0, 0.0, 0.0, -1e18, 0, e_perte, 1e9, e_dll, *b, kN[d], kN[d], q, 0, 0.0)
        n += r[1] <= -(e_dll + 3.25 * q)
    return 100 * n / len(seances)


def main():
    L = []
    rech = pd.read_csv(DM.RECHERCHE)
    robot = pd.read_csv(DM.ROBOT)
    robot = robot[robot["t"] <= DM.FIN + " 23:59"]
    bars = pd.concat([rech, robot[robot["t"] > rech["t"].iloc[-1]]], ignore_index=True)
    z = DM.preparer(bars)
    jouables = pd.DataFrame({"jour": z["jours"][z["jouables"]]})
    dernier = float(z["C"][z["jouables"][-1], N - 1])           # derniere cloture : $ au niveau d'aujourd'hui
    res = {v: trades(z, v) for v in VARIANTES}

    # controles : V1 = zone de delta_mesures (et donc entree_tardive), trade par trade
    ref = DM.trades_zone(z, "2000-01-01", DM.FIN)
    k = ["jour", "minute_entree", "sens", "minute_sortie"]
    bon = res["V1"][k].reset_index(drop=True).equals(ref[k].reset_index(drop=True)) and np.allclose(res["V1"]["points"], ref["points"])
    L.append(f"Controle : V1 = zone de delta_mesures/etude.py trade par trade ({len(ref)} trades) -> {'identique' if bon else 'ECART'}")
    if not bon:
        print("\n".join(L))
        sys.exit(1)

    L.append(f"\nMesure 1 : 15 ans sans filtre ({z['jours'][z['jouables'][0]].date()} - {DM.FIN}), {len(jouables)} seances jouables")
    L.append(f"$ pour {MNQ} MNQ au niveau de la derniere cloture ({dernier:.2f}) ; t sur toutes les seances jouables (0 sans trade)")
    L.append(f"{'var':4} {'trades':>6} {'points':>10} {'gagn.':>6} {'gain moy.':>10} {'perte moy.':>11} {'duree med.':>11}"
             f" {'t 2011-2022':>12} {'t 2023-2026':>12} {'limite 1000 $':>14}")
    t_ref, lim = {}, {}
    for v in VARIANTES:
        tr = res[v]
        usd = tr["points"] / tr["prix_entree"] * dernier * 2 * MNQ
        g = tr["points"] > 0
        jour = jouables.merge(tr.groupby("jour")["points"].sum().reset_index(), on="jour", how="left").fillna(0.0)
        t1 = t_stat(jour.loc[jour["jour"].dt.year <= 2022, "points"])
        t2 = t_stat(jour.loc[jour["jour"].dt.year >= 2023, "points"])
        t_ref[v] = (t1, t2)
        lim[v] = limite_jour(bars, tr)
        L.append(f"{v:4} {len(tr):6d} {tr['points'].sum():+10.2f} {g.mean() * 100:5.1f}% {usd[g].mean():+9.0f}$"
                 f" {usd[~g].mean():+10.0f}$ {np.median(tr['minute_sortie'] - tr['minute_entree']):9.0f} mn"
                 f" {t1:+12.2f} {t2:+12.2f} {lim[v]:13.1f}%")
    for v in VARIANTES[1:]:
        tr = res[v]
        d = tr["minute_sortie"] - tr["minute_entree"]
        L.append(f"  {v} : {(d <= 3).mean() * 100:.0f} % des trades durent 3 minutes ou moins ; {len(tr) / len(jouables):.1f} trades par seance jouable")

    L.append("\nMesure 2 : challenge depuis 0 (16 seances, 4 MNQ puis 6 MNQ les 5 dernieres, limite du jour 1 000 $)")
    ch = {}
    for v in VARIANTES:
        for r in DM.challenge(bars, z, res[v], 0.0, 0.0, [("4 puis 6", 4, 6, 5)]):
            ch[(v, r["departs"])] = r
            L.append(f"  {v} {r['departs']} : {r['n']} departs, valide {r['valide']:.1f} %, perdu {r['perdu']:.1f} %,"
                     f" expire {r['expire']:.1f} %, seances pour valider (mediane) {r['seances_valide']:.0f}")

    L.append("\nDecision fixee a l'avance :")
    passent = []
    for v in VARIANTES[1:]:
        c1 = t_ref[v][0] > t_ref["V1"][0] and t_ref[v][1] > t_ref["V1"][1]
        a, b = ch[(v, "2012-2026")]["valide"] - ch[("V1", "2012-2026")]["valide"], ch[(v, "2023-2026")]["valide"] - ch[("V1", "2023-2026")]["valide"]
        c2 = a >= 2 and b >= 0
        if c1 and c2:
            passent.append(v)
        L.append(f"  {v} : t {t_ref[v][0]:+.2f} / {t_ref[v][1]:+.2f} contre V1 {t_ref['V1'][0]:+.2f} / {t_ref['V1'][1]:+.2f}"
                 f" -> {'oui' if c1 else 'non'} ; challenge {a:+.1f} points (2012-2026), {b:+.1f} (2023-2026) -> {'oui' if c2 else 'non'}")
    choix = max(passent, key=lambda v: ch[(v, "2012-2026")]["valide"]) if passent else None
    L.append(f"  -> {'la zone du bot passe a ' + choix if choix else 'aucune variante ne passe, la zone ne change pas'}")

    L.append("\nMesure 3 : depuis la situation estimee (solde 49 158 $, plancher 48 672 $, 16 seances)")
    for v in VARIANTES:
        for r in DM.challenge(bars, z, res[v], DM.SOLDE, DM.PLUS_HAUT, [DM.TAILLES[0], DM.TAILLES[1], DM.TAILLES[4]]):
            if r["departs"] == "2012-2026":
                L.append(f"  {v} {r['taille']:30} : valide {r['valide']:5.1f} %, perdu {r['perdu']:5.1f} %, expire {r['expire']:5.1f} %")

    L.append("\nPour information : 2 - 16 octobre 2026 (points) et 13 - 20 octobre 2026 ($ pour 4 MNQ, sans limite du jour)")
    for v in VARIANTES:
        tr = res[v]
        p2 = tr[(tr["jour"] >= "2026-10-02") & (tr["jour"] <= "2026-10-16")]
        bx = tr[(tr["jour"] >= "2026-10-13") & (tr["jour"] <= "2026-10-20")]
        par_jour = bx.groupby(bx["jour"].dt.strftime("%d/%m"))["points"].sum() * 2 * MNQ - 0.0
        L.append(f"  {v} : 2-16 oct. {len(p2)} trades {p2['points'].sum():+.2f} pt ; 13-20 oct. {len(bx)} trades,"
                 f" {bx['points'].sum() * 2 * MNQ:+.0f} $ (" + ", ".join(f"{d} {x:+.0f}" for d, x in par_jour.items()) + ")")

    texte = "\n".join(L)
    print(texte)
    (ICI / "resultats.txt").write_text(texte + "\n")


if __name__ == "__main__":
    main()
