#!/usr/bin/env python3
"""Etude entree_tardive/README.md (regles fixees le 20 octobre 2026, avant tout calcul), mesures 1 et 2.
1. Validation : H1 sans delta sur 15 ans = zone/robot.py zone_de_bruit, trade par trade ; H1, R et la zone sans filtre
   sur P1 / P2 = relance/resultats.txt (rejeu C# du bot).
2. Mesure 1 (15 ans, sans filtre) et mesure 2 (P1 Databento, P2 Rithmic, vrai delta).
Ecrit resultats_15ans.txt, resultats_delta.txt, trades/<variante>_<periode>.csv, jours_15ans.csv, jours_P1.csv,
jours_P2.csv. Chemins des donnees : variables KB (branche de recherche) et ROBOT (barres du robot) ci-dessous."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ICI))
import moteur_variantes as MV  # noqa: E402

RB = MV.RB
KB = Path(os.getenv("KB", "/tmp/claude-0/-home-user-scalping-telegram-bot/5d4978aa-d2c8-5ecc-8399-6a494818dcdd/scratchpad/kb"))
ROBOT = ICI.parent / "zone" / "robot" / "nq_1min.csv.gz"
RECHERCHE = KB / "intraday" / "donnees" / "nasdaq100_1min.csv.gz"
DATABENTO = [KB / "orderflow" / "donnees" / f"nq_secondes_{i}.csv.gz" for i in (1, 2, 3)]
RITHMIC = KB / "filtre_h1" / "donnees_rithmic" / "transactions_NQZ6_rithmic.csv"
P1 = ("2026-04-01", "2026-10-01")
P2 = ("2026-10-02", "2026-10-16")
SANS_DELTA = ["H1", "E1", "E2", "S1", "L1"]
AVEC_DELTA = ["H1", "E1", "E2", "S1", "L1", "R", "RL"]
SEUILS = (125.0, 83.0)                    # 1 000 $ en 4 MNQ, 1 000 $ en 6 MNQ
REFERENCE = {("H1", "P1"): (79, 1776.8), ("R", "P1"): (83, 1860.5), ("SANS", "P1"): (99, 982.2),
             ("H1", "P2"): (6, 220.2), ("R", "P2"): (7, 657.8), ("SANS", "P2"): (7, 668.0)}


# ----------------------------------------------------------------------------- donnees
def barres_15ans():
    d = pd.read_csv(RECHERCHE)
    r = pd.read_csv(ROBOT)
    return pd.concat([d, r[r["t"] > d["t"].iloc[-1]]], ignore_index=True)


def deltas_databento():
    """Volumes agresseurs par seconde regroupes par minute (minute = heure x 60 + minute - 570), delta 30 min par jour."""
    m = []
    for f in DATABENTO:
        x = pd.read_csv(f, usecols=["t", "achat", "vente"])
        t = x["t"].str
        x["jour"] = pd.to_datetime(t[:10])
        x["minute"] = t[11:13].astype(int) * 60 + t[14:16].astype(int) - 570
        m.append(x.groupby(["jour", "minute"])[["achat", "vente"]].sum().reset_index())
    x = pd.concat(m).groupby(["jour", "minute"])[["achat", "vente"]].sum().reset_index()
    x = x[(x["minute"] >= 0) & (x["minute"] < MV.N)]
    return par_jour(x["jour"], x["minute"], x["achat"] - x["vente"])


def deltas_rithmic():
    x = pd.read_csv(RITHMIC)
    x = x.groupby(["jour", "minute"], as_index=False)[["achats", "ventes"]].sum()
    x = x[(x["minute"] >= 0) & (x["minute"] < MV.N)]
    return par_jour(pd.to_datetime(x["jour"]), x["minute"], x["achats"] - x["ventes"])


def par_jour(jour, minute, delta):
    out = {}
    df = pd.DataFrame({"jour": jour.values, "minute": minute.values, "delta": delta.values})
    for j, g in df.groupby("jour"):
        a = np.zeros(MV.N)
        a[g["minute"].values] = g["delta"].values
        out[pd.Timestamp(j)] = MV.delta_30(a)
    return out


# ----------------------------------------------------------------------------- mesures
def heure(m):
    return f"{(570 + m) // 60}h{(570 + m) % 60:02d}"


def t_stat(x):
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 1 and x.std(ddof=1) > 0 else float("nan")


def baisse(pts):
    c = pic = pire = 0.0
    for x in pts:
        c += x; pic = max(pic, c); pire = max(pire, pic - c)
    return pire


def gardes(tr):
    return tr[tr["garde"]].sort_values(["jour", "minute_entree"])


def valider_robot(d, tr, jr):
    """H1 sans delta contre robot.py zone_de_bruit (memes barres) : trades, points, et pire du jour (brut)."""
    jours, O, H, L, C, P, V, ech = RB.tableaux(d)
    zz, trades, _ = RB.zone_de_bruit(jours, O, H, L, C, P, V, ech)
    ref = []
    for j, liste in trades.items():
        for texte in liste:
            x = RB.MOTIF_ZONE.match(texte)
            me = int(x.group(2)) * 60 + int(x.group(3)) - 570
            ms = min(int(x.group(5)) * 60 + int(x.group(6)) - 570, MV.N - 1)     # 16h00 -> minute 389
            ref.append((pd.Timestamp(j), me, 1 if x.group(1) == "achat" else -1, float(x.group(4).replace(",", "")),
                        ms, float(x.group(7).replace(",", ""))))
    g = gardes(tr)
    moi = [(r.jour, int(r.minute_entree), int(r.sens), round(r.prix_entree, 2), int(r.minute_sortie), round(r.prix_sortie, 2))
           for r in g.itertuples()]
    a, b = set(ref), set(moi)
    pts_ref = float((zz["brut"] - RB.COUT * zz["allers"]).sum())
    jj = jr.set_index("jour")
    pire_ecart = float((zz["pire"] - jj.loc[zz.index, "pire_brut"]).abs().max())
    brut_ecart = float((zz["brut"] - RB.COUT * zz["allers"] - jj.loc[zz.index, "points"]).abs().max())
    hors = float(jj.drop(index=zz.index)["points"].abs().sum())          # jours sans trade chez le robot
    ok = a == b and len(ref) == len(moi) and abs(pts_ref - g["points"].sum()) < 1e-6 and pire_ecart < 1e-6 and hors == 0
    texte = (f"robot.py zone_de_bruit : {len(ref)} trades, {pts_ref:+.2f} pt nets ; H1 sans delta (ce moteur) : {len(moi)} trades,"
             f" {g['points'].sum():+.2f} pt ; trades differents {len(a - b)} (robot seul) / {len(b - a)} (moteur seul) ;"
             f" ecart max par jour : points {brut_ecart:.2e}, pire du jour brut {pire_ecart:.2e}")
    return ok, texte


def mesure_15ans(z, res):
    """res : variante -> (trades, jours). Tableau de la mesure 1."""
    L = ["Mesure 1 : 15 ans, prix seuls, sans filtre delta (H1 = V1). Barres de la recherche 2011 - 25 septembre 2026,"
         " completees par celles du robot jusqu'au 19 octobre 2026.",
         "t = moyenne / ecart-type x racine(n) des gains quotidiens nets (points), sur TOUTES les seances jouables (0 sans trade).",
         "Perte du jour : plus bas de (realise + latent aux plus bas / plus hauts des minutes), 1,5 point compte a l'entree"
         " de chaque trade ; entre parenthese, sans les frais (comme robot.py 'pire').", ""]
    per = {"2011-2022": lambda j: j.dt.year <= 2022, "2023-2026": lambda j: j.dt.year >= 2023}
    tete = (f"{'var':4s} {'trades':>6s} {'points':>10s} {'gagn.':>6s} | {'2011-2022 : tr':>14s} {'points':>9s} {'gagn.':>6s} {'t':>6s} |"
            f" {'2023-2026 : tr':>14s} {'points':>9s} {'gagn.':>6s} {'t':>6s} | {'dep. moy':>8s} | {'jours <= -125':>15s} {'jours <= -83':>15s}")
    L += [tete, "-" * len(tete)]
    t_v1 = {}
    resume = {}
    for var in SANS_DELTA:
        tr, jr = res[var]
        g = gardes(tr)
        cells = []
        for p, f in per.items():
            jj = jr[f(jr["jour"])]
            gg = g[f(g["jour"])]
            t = t_stat(jj["points"])
            cells.append((len(gg), gg["points"].sum(), t, int((gg["points"] > 0).sum())))
            resume[(var, p)] = t
            if var == "H1":
                t_v1[p] = t
        n125 = int((jr["pire"] <= -SEUILS[0]).sum()); n83 = int((jr["pire"] <= -SEUILS[1]).sum())
        b125 = int((jr["pire_brut"] <= -SEUILS[0]).sum()); b83 = int((jr["pire_brut"] <= -SEUILS[1]).sum())
        L.append(f"{var:4s} {len(g):6d} {g['points'].sum():+10.2f} {int((g['points'] > 0).sum()):6d} |"
                 f" {cells[0][0]:14d} {cells[0][1]:+9.1f} {cells[0][3]:6d} {cells[0][2]:+6.2f} |"
                 f" {cells[1][0]:14d} {cells[1][1]:+9.1f} {cells[1][3]:6d} {cells[1][2]:+6.2f} |"
                 f" {g['depassement_entree'].mean():8.3f} | {n125:6d} ({b125:5d})  {n83:6d} ({b83:5d})")
    jr = res["H1"][1]
    L += ["", f"Seances jouables : {len(jr)} ({int((jr['jour'].dt.year <= 2022).sum())} en 2011-2022,"
              f" {int((jr['jour'].dt.year >= 2023).sum())} en 2023-2026)", "",
          "Critere 1 de la decision (t superieur a V1 sur 2011-2022 ET sur 2023-2026) :"]
    for var in SANS_DELTA[1:]:
        ok = resume[(var, "2011-2022")] > t_v1["2011-2022"] and resume[(var, "2023-2026")] > t_v1["2023-2026"]
        L.append(f"  {var} : t {resume[(var, '2011-2022')]:+.2f} / {resume[(var, '2023-2026')]:+.2f} contre V1"
                 f" {t_v1['2011-2022']:+.2f} / {t_v1['2023-2026']:+.2f} -> {'PASSE' if ok else 'ne passe pas'}")
    # descriptif : trades ecartes par L1 (non pris, restes virtuels)
    tl = res["L1"][0]
    nl = tl[~tl["garde"]]
    L += ["", f"L1 : {len(nl)} cassures non prises (depassement > 1), gain moyen du virtuel {nl['points'].mean():+.2f} pt"
              f" (somme {nl['points'].sum():+.1f}) ; prises {int(tl['garde'].sum())}, moyenne {tl[tl['garde']]['points'].mean():+.2f} pt"]
    return L, resume, t_v1


def ligne_delta(nom, tr, jr):
    g = gardes(tr)
    ec = int((~tr["garde"]).sum())
    rel = int(g["relance"].sum())
    if len(jr):
        i = jr["points"].idxmin()
        pire_s = f"{jr.loc[i, 'points']:+8.2f} ({jr.loc[i, 'jour'].date()})"
        pire_j = f"{jr['pire'].min():+8.2f}"
    else:
        pire_s, pire_j = "-", "-"
    return (f"{nom:5s} {len(g):6d} {g['points'].sum():+9.1f} {baisse(g['points'].tolist()):9.1f}  {pire_s:>22s}"
            f"  {pire_j:>9s}  {ec:7d} {rel:8d}"), len(g), round(g["points"].sum(), 1)


def controle_barres_anciennes(ri, db, version="8d8e099"):
    """Explication des ecarts : relance/ a tourne le 19 octobre sur les barres du robot de la mise a jour du 17 octobre
    (commit 8d8e099). Celle du 20 octobre (ceb29b5) a corrige des minutes du 16 octobre. Rejeu avec l'ancienne version
    (lecture seule : git show)."""
    import io
    import subprocess
    try:
        brut = subprocess.run(["git", "-C", str(ICI.parent), "show", f"{version}:zone/robot/nq_1min.csv.gz"],
                              capture_output=True, check=True).stdout
        vieux = pd.read_csv(io.BytesIO(brut), compression="gzip")
    except Exception as e:
        return [f"  (barres du robot {version} indisponibles : {e})"]
    neuf = pd.read_csv(ROBOT)
    a = vieux.merge(neuf, on="t", how="outer", suffixes=("_v", "_n"), indicator=True)
    a = a[a["t"] <= P2[1] + " 23:59"]
    dif = a[(a["_merge"] != "both") | (a[["o_v", "h_v", "l_v", "c_v"]].values != a[["o_n", "h_n", "l_n", "c_n"]].values).any(axis=1)]
    L = ["", f"Explication : barres du robot de la version {version} (17 octobre, utilisee par relance/ le 19 octobre)"
             f" contre la version actuelle : {len(dif)} minutes differentes jusqu'au {P2[1]}"
             f" ({', '.join(sorted(set(dif['t'].str[:10])))})"]
    for r in dif[dif["t"].str[11:].isin(["10:00", "10:30", "15:59"])].itertuples():
        L.append(f"    {r.t} cloture {r.c_v:.2f} (avant) -> {r.c_n:.2f} (maintenant)")
    zv = MV.preparer(vieux)
    for per, (a0, b0), dl in [("P1", P1, db), ("P2", P2, ri)]:
        choisis = {j for j in zv["jours"][zv["jouables"]] if pd.Timestamp(a0) <= j <= pd.Timestamp(b0)}
        for nom, var, deltas in [("H1", "H1", dl), ("R", "R", dl), ("SANS", "H1", None)]:
            tr, _ = MV.jouer_tout(zv, var, nom=nom, deltas=deltas, jours_choisis=choisis)
            g = gardes(tr)
            n, pts = REFERENCE[(nom, per)]
            ok = len(g) == n and f"{g['points'].sum():+.1f}" == f"{pts:+.1f}"
            L.append(f"  avec ces barres : {nom:4s} {per} {len(g)} trades {g['points'].sum():+.1f} pt (reference {n} trades"
                     f" {pts:+.1f}) -> {'identique' if ok else 'ECART'}")
    return L


def main():
    (ICI / "trades").mkdir(exist_ok=True)
    print("chargement des barres (15 ans)")
    d = barres_15ans()
    z = MV.preparer(d)
    res = {}
    for var in SANS_DELTA:
        tr, jr = MV.jouer_tout(z, var)
        res[var] = (tr, jr)
        tr.to_csv(ICI / "trades" / f"{var}_15ans.csv", index=False, float_format="%.10g")
        print(var, "15 ans :", int(tr["garde"].sum()), "trades", round(gardes(tr)["points"].sum(), 2))
    ok_robot, texte_robot = valider_robot(d, *res["H1"])
    print("validation robot.py :", ok_robot, texte_robot)
    jours = res["H1"][1][["jour"]].copy()
    for var in SANS_DELTA:
        jr = res[var][1].set_index("jour")
        jours[var] = jr.loc[jours["jour"], "points"].values
        jours[f"{var}_pire"] = jr.loc[jours["jour"], "pire"].values
        jours[f"{var}_trades"] = jr.loc[jours["jour"], "trades"].values
    jours["jour"] = jours["jour"].dt.strftime("%Y-%m-%d")
    jours.to_csv(ICI / "jours_15ans.csv", index=False, float_format="%.4f")
    L1, resume, t_v1 = mesure_15ans(z, res)
    L1 = [f"Validation : {'OK' if ok_robot else 'ECHEC'} - {texte_robot}", ""] + L1
    (ICI / "resultats_15ans.txt").write_text("\n".join(L1) + "\n")
    print("\n".join(L1))

    # ------------------------------------------------------------------ P1 / P2, vrai delta, barres du robot
    print("chargement du delta (Databento, Rithmic)")
    zr = MV.preparer(pd.read_csv(ROBOT))
    db, ri = deltas_databento(), deltas_rithmic()
    L2 = ["Mesure 2 : vrai delta, barres du robot (zone/robot/nq_1min.csv.gz). P1 = 1er avril - 1er octobre 2026 (Databento,"
          " secondes regroupees par minute), P2 = 2 - 16 octobre 2026 (Rithmic, transactions_NQZ6_rithmic.csv).",
          "Delta 30 min = achats - ventes des minutes max(0, m-29)..m de la seance (Moteur.cs Delta) ; delta nul : trade ecarte.",
          "Pire baisse = plus grande baisse du cumul des points des trades (relance/comparer.py). Pire seance = plus petite"
          " somme des points d'une journee ; pire latent = plus bas de (realise + latent aux plus bas / hauts des minutes).",
          "SANS = H1 sans filtre (reference de relance/resultats.txt). R et RL : pour information seulement.", ""]
    obtenu = {}
    tables_jours = {}
    for per, (a, b), dl in [("P1", P1, db), ("P2", P2, ri)]:
        choisis = {j for j in zr["jours"][zr["jouables"]] if pd.Timestamp(a) <= j <= pd.Timestamp(b)}
        sans_delta = sorted(j.date() for j in choisis if j not in dl)
        tete = f"{'var':5s} {'trades':>6s} {'points':>9s} {'pire b.':>9s}  {'pire seance':>22s}  {'pire lat.':>9s}  {'ecartes':>7s} {'relances':>8s}"
        L2 += [f"{per} ({a} - {b}) : {len(choisis)} seances jouables"
               + (f" ; sans delta (trades ecartes) : {', '.join(map(str, sans_delta))}" if sans_delta else ""), tete, "-" * len(tete)]
        tj = None
        for nom, var, deltas in [(v, v, dl) for v in AVEC_DELTA] + [("SANS", "H1", None)]:
            tr, jr = MV.jouer_tout(zr, var, nom=nom, deltas=deltas, jours_choisis=choisis)
            tr.to_csv(ICI / "trades" / f"{nom}_{per}.csv", index=False, float_format="%.10g")
            texte, n, pts = ligne_delta(nom, tr, jr)
            obtenu[(nom, per)] = (n, pts)
            L2.append(texte)
            if tj is None:
                tj = jr[["jour"]].copy()
            jj = jr.set_index("jour")
            tj[nom] = jj.loc[tj["jour"], "points"].values
            tj[f"{nom}_pire"] = jj.loc[tj["jour"], "pire"].values
            if nom in ("R", "RL"):
                for r in tr[tr["relance"]].itertuples():
                    L2.append(f"      relance {r.jour.date()} {heure(r.minute_entree)} "
                              f"({'achat' if r.sens > 0 else 'vente'}, signal {heure(r.minute_signal)}) {r.points:+.2f} pt,"
                              f" depassement {r.depassement_entree:.2f}")
        tj["jour"] = tj["jour"].dt.strftime("%Y-%m-%d")
        tj.to_csv(ICI / f"jours_{per}.csv", index=False, float_format="%.4f")
        tables_jours[per] = tj
        L2.append("")
    L2.append("Controle contre relance/resultats.txt (rejeu C# du bot) :")
    tout_ok = True
    for (nom, per), (n, pts) in REFERENCE.items():
        on, op = obtenu[(nom, per)]
        ok = on == n and f"{op:+.1f}" == f"{pts:+.1f}"
        tout_ok &= ok
        L2.append(f"  {nom:4s} {per} : reference {n} trades {pts:+.1f} pt ; ici {on} trades {op:+.1f} pt -> {'identique' if ok else 'ECART'}")
    L2.append(f"-> {'tout identique' if tout_ok else 'ecarts : explication ci-dessous'}")
    if not tout_ok:
        L2 += controle_barres_anciennes(ri, db)
    L2 += ["", "Criteres 3 et 4 de la decision (P1 : au moins autant de points que H1 ; P2 : pas moins bien que H1) :"]
    for var in ["E1", "E2", "S1", "L1"]:
        c3 = obtenu[(var, "P1")][1] >= obtenu[("H1", "P1")][1]
        c4 = obtenu[(var, "P2")][1] >= obtenu[("H1", "P2")][1]
        L2.append(f"  {var} : P1 {obtenu[(var, 'P1')][1]:+.1f} contre {obtenu[('H1', 'P1')][1]:+.1f} -> {'oui' if c3 else 'non'} ;"
                  f" P2 {obtenu[(var, 'P2')][1]:+.1f} contre {obtenu[('H1', 'P2')][1]:+.1f} -> {'oui' if c4 else 'non'}")
    (ICI / "resultats_delta.txt").write_text("\n".join(L2) + "\n")
    print("\n".join(L2))


if __name__ == "__main__":
    main()
