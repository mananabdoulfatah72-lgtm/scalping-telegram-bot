#!/usr/bin/env python3
"""etude_large/bruit/README.md (regles fixees le 22 octobre 2026, avant tout calcul) : retour au VWAP a l'interieur
de la zone du bot, stop sur la limite de la zone ; 3 seuils x NQ, ES ; puis complement de la zone et challenges.

Lancer : python3 etude_large/bruit/etude.py (numba, numpy, pandas ; variable KB comme delta_mesures). Ecrit
resultats.txt."""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(RACINE / "delta_mesures"))
sys.path.insert(0, str(ICI.parent))
import etude as DM  # noqa: E402
import partie_a as PA  # noqa: E402
import partie_d as PD  # noqa: E402
sys.path.insert(0, str(DM.KB / "fonds"))
import fomc  # noqa: E402

N = DM.N
SEUILS = [0.5, 0.75, 0.9]
DEBUT_E, FIN_E = 30, 330                  # 10 h - 15 h
MAX_TRADES = 3
MARCHES = {"NQ": (1.5, 2.0), "ES": (0.9, 5.0)}   # frais en points par aller-retour, $ par point du micro
EXPLO = ("2011-01-01", "2022-12-31")
COFFRE = ("2023-01-01", "2026-10-20")
ES = DM.KB / "intraday" / "donnees" / "sp500_1min.csv.gz"


def fade_jour(C, s, vw, hr, br, k):
    out, pos, n = [], 0, 0
    pe, me = 0.0, 0
    for m in range(DEBUT_E, N):
        p = C[m]
        ub, lb = hr * (1 + s[m]), br * (1 - s[m])
        if pos:
            fin = m == N - 1
            if pos < 0 and (p <= vw[m] or p >= ub or fin):
                out.append((me, pos, pe, m, p))
                pos = 0
            elif pos > 0 and (p >= vw[m] or p <= lb or fin):
                out.append((me, pos, pe, m, p))
                pos = 0
            continue
        if m > FIN_E or n >= MAX_TRADES:
            continue
        if hr * (1 + k * s[m]) < p < ub and p > vw[m]:
            pos, pe, me, n = -1, p, m, n + 1
        elif lb < p < br * (1 - k * s[m]) and p < vw[m]:
            pos, pe, me, n = 1, p, m, n + 1
    return out


def trades(z, k, cout, fed, fin):
    L = []
    for i in z["jouables"]:
        j = z["jours"][i]
        if j in fed or j > pd.Timestamp(fin) or np.isnan(z["sigma"][i, DEBUT_E]):
            continue
        for me, sens, pe, ms, ps in fade_jour(z["C"][i], z["sigma"][i], z["vwap"][i], z["href"][i], z["bref"][i], k):
            L.append(dict(jour=j, minute_entree=me, sens=sens, prix_entree=pe, minute_sortie=ms, prix_sortie=ps,
                          points=sens * (ps - pe) - cout))
    return pd.DataFrame(L)


def quotidien(tr, z, jours):
    ouv = pd.Series(z["C"][:, 0], index=z["jours"])
    if tr.empty:
        return np.zeros(len(jours))
    g = tr.groupby("jour")["points"].sum()
    return (g / ouv.reindex(g.index)).reindex(jours).fillna(0.0).values


def chemins(z, Hm, Lm, tr, jours, cout, pt, ref):
    """Comme partie_d.chemins_zone, pour une liste de trades quelconque : gain cumule par minute (cloture, plus bas,
    plus haut), 1 contrat, en $, au niveau de prix ref."""
    idx = {j: i for i, j in enumerate(z["jours"])}
    pos = {j: k for k, j in enumerate(jours)}
    ch, bas, haut = (np.zeros((len(jours), N)) for _ in range(3))
    for j, g in tr.groupby("jour"):
        if j not in pos:
            continue
        i = idx[j]
        C, H, L = z["C"][i], Hm[i], Lm[i]
        f = ref / C[0]
        c, contre, pour = np.zeros(N), np.zeros(N), np.zeros(N)
        for _, t in g.iterrows():
            me, ms, s, pe = int(t["minute_entree"]), int(t["minute_sortie"]), int(t["sens"]), float(t["prix_entree"])
            c[me:ms] += s * (C[me:ms] - pe) * f
            c[ms:] += s * (float(t["prix_sortie"]) - pe) * f
            c[me:] -= cout
            w = slice(me + 1, ms + 1)
            contre[w] += ((C[w] - L[w]) if s > 0 else (H[w] - C[w])) * f
            pour[w] += ((H[w] - C[w]) if s > 0 else (C[w] - L[w])) * f
        k = pos[j]
        ch[k], bas[k], haut[k] = c * pt, (c - contre) * pt, (c + pour) * pt
    return ch, bas, haut


def main():
    t, sh = PA.t_stat, PA.sharpe
    fed = set(pd.DatetimeIndex(fomc.annonces()))
    rech = pd.read_csv(DM.RECHERCHE)
    robot = pd.read_csv(DM.ROBOT)
    bars = {"NQ": pd.concat([rech, robot[robot["t"] > rech["t"].iloc[-1]]], ignore_index=True), "ES": pd.read_csv(ES)}
    Z = {m: DM.preparer(b) for m, b in bars.items()}
    zn = Z["NQ"]
    jours = pd.DatetimeIndex([zn["jours"][i] for i in zn["jouables"]])
    jours = jours[(jours >= EXPLO[0]) & (jours <= COFFRE[1]) & ~jours.isin(fed)]
    e = (jours >= EXPLO[0]) & (jours <= EXPLO[1])
    c = (jours >= COFFRE[0]) & (jours <= COFFRE[1])
    tz = DM.trades_zone(zn, EXPLO[0], COFFRE[1])
    tz = tz[~tz["jour"].isin(fed)]
    zb = quotidien(tz, zn, jours)
    L = ["Vague le bruit dans la zone (etude_large/bruit/README.md, regles fixees le 22 octobre 2026 avant tout calcul)",
         f"{len(jours)} seances du NQ hors jours de la Fed ({jours[0].date()} - {jours[-1].date()}) ; exploration "
         f"{int(e.sum())}, coffre {int(c.sum())}. ES jusqu'au 25 septembre 2026 (0 ensuite).",
         f"Zone du bot (reference) : t exploration {t(zb[e]):+.2f}, coffre {t(zb[c]):+.2f}, Sharpe coffre {sh(zb[c]):+.2f}", ""]
    lignes, res = [], {}
    for m, (cout, pt) in MARCHES.items():
        for k in SEUILS:
            tr = trades(Z[m], k, cout, fed, COFFRE[1])
            r = quotidien(tr, Z[m], jours)
            res[(m, k)] = (tr, r)
            perd = e & (zb < 0)
            brut = quotidien(tr.assign(points=tr["points"] + cout), Z[m], jours) if not tr.empty else r
            lignes.append(dict(m=m, k=k, n=len(tr), gagnants=float((tr["points"] > 0).mean() * 100) if len(tr) else 0,
                               te=t(r[e]), tc=t(r[c]), tbe=t(brut[e]), tbc=t(brut[c]), corr=float(np.corrcoef(r[e], zb[e])[0, 1]),
                               perd=float(r[perd].mean() * 1e4), duree=float((tr["minute_sortie"] - tr["minute_entree"]).median())
                               if len(tr) else 0))
    df = pd.DataFrame(lignes)
    p = np.array([PA.p_unilateral(x) for x in df["te"]])
    df["bh"] = PA.bh(p)
    df["explo"] = df["bh"] & (df["te"] >= 2.0)
    df["survie"] = df["explo"] & (df["tc"] >= 1.5)
    L.append("  marche  seuil  trades  gagnants  duree (min)  t explo  t coffre  | avant frais : explo  coffre  | corr zone  "
             "jours ou la zone perd (pb)")
    for _, l in df.iterrows():
        L.append(f"  {l['m']:<6} {l['k']:5.2f}  {l['n']:6d}  {l['gagnants']:7.1f} %  {l['duree']:10.0f}  {l['te']:+7.2f}  "
                 f"{l['tc']:+8.2f}  | {l['tbe']:+18.2f}  {l['tbc']:+6.2f}  | {l['corr']:+9.2f}  {l['perd']:+10.2f}"
                 f"{'  SURVIT' if l['survie'] else ''}")
    L.append(f"\nDECISION 1 : {int(df['explo'].sum())} essai(s) passent l'exploration, {int(df['survie'].sum())} survivent "
             "au coffre.")
    surv = df[df["survie"]]
    if surv.empty:
        L.append("DECISION 2 et 3 : non faites (aucune survivante, regle fixee d'avance).")
    for _, l in surv.iterrows():
        tr, r = res[(l["m"], l["k"])]
        w = zb[e].std() / r[e].std()
        comb = zb + w * r
        ok2 = l["corr"] < 0.3 and sh(comb[c]) > sh(zb[c])
        L.append(f"DECISION 2, {l['m']} {l['k']} : corr {l['corr']:+.2f}, Sharpe coffre zone {sh(zb[c]):+.2f} -> zone + "
                 f"bruit {sh(comb[c]):+.2f} : {'complement' if ok2 else 'pas un complement'}")
        if not ok2:
            continue
        # decision 3 : challenges, departs 2012 - 2021 (information) et 2023 - 2026 (decision)
        jd, clo_z, bas_z, haut_z = PD.chemins_zone()
        zm = Z[l["m"]]
        _, _, Hm, Lm, _, _, _, _ = DM.RB.tableaux(bars[l["m"]])
        ref = float(zm["C"][zm["jouables"][-1], N - 1])
        clo_f, bas_f, haut_f = chemins(zm, Hm, Lm, tr, jd, MARCHES[l["m"]][0], MARCHES[l["m"]][1], ref)
        for nom, q in (("Lucid Flex 50K", 1.0), ("Bulenox Legacy 50K opt. 2", 3.0)):
            obj, dd, bloc, dll, nmax, part, *_ = PD.FIRMES[nom]
            for lab, d0, d1 in (("2012 - 2021", PD.DEBUT, PD.FIN_CHOIX), ("2023 - 2026", PD.DEBUT_VERIF, "2026-12-31")):
                dep = np.where((jd >= d0) & (jd <= d1))[0]
                lim = PD.limites_depart(jd, dep, nmax)
                ok = dep + lim < len(jd)
                arg = (q, q, 0, float(obj), float(dd), float(bloc), float(dll), part, True)
                a = PD.tous_les_departs(clo_z, bas_z, haut_z, dep[ok], lim[ok], *arg)[0]
                # zone + bruit, memes contrats chacun : plus bas additionnes (prudent pour le plancher et la limite du
                # jour) ; plus haut = l'une a son plus haut pendant que l'autre est a sa cloture (pour l'objectif)
                hb = np.maximum(haut_z + clo_f, clo_z + haut_f)
                b = PD.tous_les_departs(clo_z + clo_f, bas_z + bas_f, hb, dep[ok], lim[ok], *arg)[0]
                L.append(f"  {nom} ({q:.0f} + {q:.0f}), departs {lab} : zone seule valide {(a == 1).mean() * 100:.0f} % / "
                         f"perdu {(a == -1).mean() * 100:.0f} % ; zone + bruit {(b == 1).mean() * 100:.0f} % / "
                         f"{(b == -1).mean() * 100:.0f} %")
    (ICI / "resultats.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
