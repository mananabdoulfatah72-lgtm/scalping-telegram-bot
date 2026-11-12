"""Parties G et H (REGLES.md) : copier les institutions (rapports de la CFTC), les heures de la nuit, la nuit de
secours contre l'inactivite, et le compte depuis son etat actuel.

Usage : python3 variantes.py g | h1 | h2 | h3     (ecrit resultats/partie_g.txt, partie_h1.txt, partie_h2.txt, partie_h3.txt)
"""
import json
import sys

import numpy as np
import pandas as pd

import compte as Cp
import donnees as D
import nuit as Nn

SORTIE = D.ICI / "resultats"
E = 2 * D.PREF                                        # $ pour 100 % de variation, 1 MNQ au prix d'aujourd'hui
n0 = lambda x: f"{x:,.0f}".replace(",", " ")


def ecrire(nom, lignes, donnees):
    (SORTIE / f"{nom}.txt").write_text("\n".join(lignes) + "\n")
    json.dump(donnees, open(SORTIE / f"{nom}.json", "w"), indent=1, ensure_ascii=False, default=float)
    print("\n".join(lignes))


# ====================================================================== partie G : copier les institutions
def signaux_cot():
    """Les cinq signaux hebdomadaires de flux/cot.py (partie 7), sans rien changer."""
    d = pd.read_csv(D.OP / "flux/donnees/cot/cot_nq.csv")
    t = pd.DataFrame({"date": pd.to_datetime(d["Report_Date_as_YYYY-MM-DD"], format="mixed"), "oi": d.Open_Interest_All.astype(float),
                      "am": d.Asset_Mgr_Positions_Long_All - d.Asset_Mgr_Positions_Short_All,
                      "lf": d.Lev_Money_Positions_Long_All - d.Lev_Money_Positions_Short_All,
                      "dl": d.Dealer_Positions_Long_All - d.Dealer_Positions_Short_All})
    t = t.sort_values(["date", "oi"]).drop_duplicates("date", keep="last").set_index("date").sort_index()
    for k in ("am", "lf", "dl"):
        t[k] = t[k] / t["oi"]
    b = pd.DataFrame(index=t.index)
    b["G1"] = np.sign(t["am"].diff(4)); b["G2"] = np.sign(t["lf"].diff(4))
    z = (t["lf"] - t["lf"].rolling(52).mean()) / t["lf"].rolling(52).std()
    b["G3"] = np.where(z >= 1.5, -1, np.where(z <= -1.5, 1, 0))
    b["G4"] = np.sign(t["dl"].diff(4)); b["G5"] = np.where(b["G1"] == b["G2"], b["G1"], 0)
    return b.fillna(0.0)


NOMS_G = {"G1": "suivre les gestionnaires d'actifs", "G2": "suivre les fonds à levier", "G3": "contre les fonds à levier trop chargés",
          "G4": "suivre les banques et teneurs de marché", "G5": "gestionnaires et fonds à levier d'accord"}


def partie_g():
    X = Nn.construire(); M = D.nq_minutes(); J = X["J"]; jou = np.isfinite(X["entree"])
    b = signaux_cot(); pub = (b.index + pd.Timedelta(days=3)).to_numpy()
    ri = (np.searchsorted(pub, pd.to_datetime(J).to_numpy(), side="left") - 1)[jou]      # dernier rapport publie avant le jour de trading
    rn = X["sortie"] / X["entree"] - 1; rj = M["C"][:, D.N - 1] / M["O"][:, 0] - 1
    R = {"nuit": rn[jou], "entier": ((1 + rn) * (1 + rj) - 1)[jou]}
    jj = J[jou]; ex = jj <= D.FIN_EXPLO; rng = np.random.default_rng(2026); n = len(b)
    L = [f"Partie G : copier les institutions et les banques (rapports hebdomadaires de la CFTC, E-mini Nasdaq-100).",
         f"{n} rapports du {b.index[0].date()} au {b.index[-1].date()} ; {int(jou.sum())} jours de trading du {jj[0]} au {jj[-1]} ; 1 MNQ au prix d'aujourd'hui, frais 3 $.", ""]
    res = {}; ps = []
    for e in ("nuit", "entier"):
        a = R[e] * E - D.FRAIS
        res[f"achat_{e}"] = dict(t=D.tstat(a), t_ex=D.tstat(a[ex]), t_ct=D.tstat(a[~ex]), moy=float(a.mean()))
    for h in NOMS_G:
        s = b[h].to_numpy()
        for e in ("nuit", "entier"):
            sens = np.where(ri >= 0, s[np.maximum(ri, 0)], 0.0)
            g = np.where(sens != 0, sens * R[e] * E - D.FRAIS, 0.0)
            pl = []
            for _ in range(1000):
                sp = np.roll(s, int(rng.integers(8, n - 8)))
                x = np.where(ri >= 0, sp[np.maximum(ri, 0)], 0.0)
                pl.append(D.tstat(np.where(x != 0, x * R[e] * E - D.FRAIS, 0.0)))
            achat = R[e] * E - D.FRAIS
            m = dict(t=D.tstat(g), t_ex=D.tstat(g[ex]), t_ct=D.tstat(g[~ex]), moy=float(g.mean()), moy_ex=float(g[ex].mean()), moy_ct=float(g[~ex].mean()),
                     achats=int((sens > 0).sum()), ventes=int((sens < 0).sum()), rien=int((sens == 0).sum()), total=float(g.sum()),
                     placebo95=float(np.percentile(pl, 95)), bat_placebos=float(np.mean(np.array(pl) < D.tstat(g))), t_contre_achat=D.tstat(g - achat))
            res[f"{h}_{e}"] = m; ps.append(D.p_unilateral(m["t"]))
    passe = D.bh(ps); retenus = []
    for k, (cle, m) in enumerate([(c, v) for c, v in res.items() if not c.startswith("achat")]):
        h, e = cle.split("_")
        ok = m["t"] >= 2 and passe[k] and m["moy_ex"] > 0 and m["moy_ct"] > 0 and m["t"] > m["placebo95"]
        m["bh"] = bool(passe[k]); m["retenu"] = bool(ok)
        if ok:
            retenus.append(cle)
        L.append(f"{h} {NOMS_G[h]}, {e} : t {m['t']:+.2f} (exploration {m['t_ex']:+.2f}, contrôle {m['t_ct']:+.2f}), {m['moy']:+.1f} $ par jour, "
                 f"total {n0(m['total'])} $ ; {m['achats']} achats, {m['ventes']} ventes, {m['rien']} jours sans position ; 95e centile des placebos {m['placebo95']:+.2f} "
                 f"(bat {m['bat_placebos']:.0%}) ; contre « acheter tous les jours » t {m['t_contre_achat']:+.2f} → {'RETENU' if ok else 'éliminé'}")
        if e == "entier":
            L.append("")
    for e in ("nuit", "entier"):
        a = res[f"achat_{e}"]
        L.append(f"Référence, acheter tous les jours ({e}) : t {a['t']:+.2f} (exploration {a['t_ex']:+.2f}, contrôle {a['t_ct']:+.2f}), {a['moy']:+.1f} $ par jour.")
    L += ["", "Retenus : " + (", ".join(retenus) if retenus else "aucun")]
    res["retenus"] = retenus
    ecrire("partie_g", L, res)


# ====================================================================== partie H1 : les heures de la nuit
FEN = {"A": "A · Asie : 18 h (New York) → 8 h (Paris)", "E": "E · ouverture de l'Europe : 8 h → 9 h (Paris)",
       "M": "M · matin : 9 h (Paris) → 9 h 30 (New York)", "EM": "EM · 8 h (Paris) → 9 h 30 (New York)"}


def barres(nom="usatechidxusd"):
    t, o, h, l, c = D.cfd(nom)
    par = pd.to_datetime(t * 60, unit="s", utc=True).tz_convert("Europe/Paris")
    return o, l, (par.hour * 60 + par.minute).to_numpy()


def gain_chemin(ob, lb, e, x, stop, frais, E=E, tick=D.TICK / D.PREF):
    """Meme calcul que nuit.gains : stop lu sur les plus bas des barres, rempli a son niveau moins 1 tick (ou a l'ouverture)."""
    r = x / e - 1; bas = lb.min() / e - 1; stp = False
    if stop > 0:
        niv = e * (1 - stop); k = np.nonzero(lb <= niv)[0]
        if len(k):
            k = k[0]; px = ob[k] if (k > 0 and ob[k] < niv) else niv
            r = px / e - 1 - tick; bas = min(-stop, r); stp = True
    g = r * E - frais
    return g, min(bas * E - frais, g), stp


def gains_fenetre(X, Bq, nom, stop, frais=D.FRAIS):
    """Gain, pire moment et stop de la fenetre `nom` pour chaque seance (NaN si la fenetre n'est pas jouable cette nuit-la)."""
    o, l, mp = Bq; S = len(X["J"]); g = np.full(S, np.nan); creux = np.full(S, np.nan); stp = np.zeros(S, bool)
    for s in range(S):
        idx = X["idx"][s]
        if idx is None:
            continue
        m = mp[idx]; fin = len(idx)
        j8 = np.nonzero((m >= 480) & (m < 510))[0]; j9 = np.nonzero((m >= 540) & (m < 570))[0]
        j8 = j8[0] if len(j8) else -1; j9 = j9[0] if len(j9) else -1
        a, b = {"A": (0, j8), "E": (j8, j9), "M": (j9, fin), "EM": (j8, fin), "T": (0, fin)}[nom]
        if a < 0 or b < 0 or b <= a:
            continue
        x = X["sortie"][s] if b == fin else o[idx[b]]
        g[s], creux[s], stp[s] = gain_chemin(o[idx[a:b]], l[idx[a:b]], o[idx[a]], x, stop, frais, X.get("E", E), X.get("tick", D.TICK / D.PREF))
    return g, creux, stp


def par_heure(X, Bq):
    """Variation moyenne de chaque heure de Paris, en $ pour 1 MNQ, sans frais."""
    o, l, mp = Bq; S = len(X["J"]); P = np.full((S, 17), np.nan)
    for s in range(S):
        idx = X["idx"][s]
        if idx is None:
            continue
        m = mp[idx]
        for hh in range(16):
            k = np.nonzero((m >= 60 * hh) & (m < 60 * hh + 30))[0]
            if len(k):
                P[s, hh] = o[idx[k[0]]]
        if np.isfinite(P[s, 15]):
            P[s, 16] = X["sortie"][s]
    return (P[:, 1:] / P[:, :-1] - 1) * E


def partie_h1():
    X = Nn.construire(); Bq = barres(); J = X["J"]; jou = np.isfinite(X["entree"])
    g0, _, _ = Nn.gains(X, 0.005); gt, _, _ = gains_fenetre(X, Bq, "T", 0.005)
    ecart = float(np.nanmax(np.abs(g0[jou] - gt[jou])))
    L = ["Partie H1 : quelles heures de la nuit ? 1 MNQ au prix d'aujourd'hui, frais 3 $, données corrigées.",
         f"Nuits jouables : {int(jou.sum())} du {J[jou][0]} au {J[jou][-1]}. Contrôle du code : la fenêtre entière redonne la partie N à {ecart:.4f} $ près.", "",
         f"{'variante':<58}{'nuits':>6}{'t':>7}{'t expl':>8}{'t ctrl':>8}{'t a 6$':>8}{'$/nuit':>8}{'$/an':>8}{'pire':>8}{'annees+':>8}{'stops':>6}  verdict"]
    res = {}; ps = []
    for nom in FEN:
        for stop in (0.0, 0.005):
            g, creux, stp = gains_fenetre(X, Bq, nom, stop); g6, _, _ = gains_fenetre(X, Bq, nom, stop, 6.0)
            garde = np.isfinite(g) & jou
            m = Nn.mesure(X, g, garde); m["t6"] = Nn.mesure(X, g6, garde)["t"]; m["stoppees"] = int(stp.sum())
            m["ecart_type"] = float(np.where(garde, g, 0.0)[jou].std(ddof=1))
            res[f"{nom}_{stop}"] = m; ps.append(D.p_unilateral(m["t"]))
    passe = D.bh(ps); retenues = []
    for k, (cle, m) in enumerate(res.items()):
        nom, stop = cle.split("_"); stop = float(stop)
        cond = [m["t"] >= 2 and passe[k], m["moy_ex"] > 0 and m["moy_ct"] > 0, m["t6"] >= 1.5, m["annees_pos"] >= 10, m["pire"] > -1100]
        m["bh"] = bool(passe[k]); m["retenue"] = bool(all(cond))
        raison = "RETENUE" if all(cond) else "échoue : " + ", ".join(x for x, c in zip(("t/BH", "deux périodes", "frais 6 $", "années", "pire nuit"), cond) if not c)
        if all(cond):
            retenues.append((m["t"], nom, stop))
        etiq = f"{FEN[nom]}, {'sans stop' if stop == 0 else 'stop 0,50 %'}"
        L.append(f"{etiq:<58}{m['n']:>6}{m['t']:>7.2f}{m['t_ex']:>8.2f}{m['t_ct']:>8.2f}{m['t6']:>8.2f}{m['moy']:>8.1f}{m['par_an']:>8.0f}{m['pire']:>8.0f}"
                 f"{m['annees_pos']:>5}/{m['annees']:<2}{m['stoppees']:>6}  {raison}")
    retenues.sort(reverse=True)
    res["meilleure"] = dict(fenetre=retenues[0][1], stop=retenues[0][2]) if retenues else None
    L += ["", "Meilleure variante retenue : " + (f"{FEN[retenues[0][1]]}, {'sans stop' if retenues[0][2] == 0 else 'stop 0,50 %'}" if retenues else "aucune"), "",
          "Pour information : variation moyenne heure par heure (heure de Paris, $ pour 1 MNQ, sans frais ni stop).",
          f"{'heure (Paris)':<18}{'nuits':>6}{'$ moyen':>9}{'t':>7}{'expl. $':>9}{'t':>7}{'ctrl $':>9}{'t':>7}"]
    H = par_heure(X, Bq)[jou]; ex = J[jou] <= D.FIN_EXPLO; hh = {}
    for k in range(16):
        v = H[:, k]; f = np.isfinite(v)
        nom = f"{k} h → {k + 1} h" if k < 15 else "15 h → 15 h 30"
        hh[nom] = dict(n=int(f.sum()), moy=float(np.nanmean(v)), t=D.tstat(v[f]), moy_ex=float(np.nanmean(v[ex])), t_ex=D.tstat(v[ex & f]),
                       moy_ct=float(np.nanmean(v[~ex])), t_ct=D.tstat(v[~ex & f]))
        x = hh[nom]
        L.append(f"{nom:<18}{x['n']:>6}{x['moy']:>9.1f}{x['t']:>7.2f}{x['moy_ex']:>9.1f}{x['t_ex']:>7.2f}{x['moy_ct']:>9.1f}{x['t_ct']:>7.2f}")
    res["par_heure"] = hh
    ecrire("partie_h1", L, res)


# ====================================================================== partie H2 : le secours dans le compte
def secours_tp(B, k):
    """Secours toujours possible : la nuit qui precede la seance est prise des que le compte a passe k jours de trading
    sans trade. Un jour sans donnees ou le compteur vaut k recoit un trade de secours a 0 $ (apres[i] = jours sans trade
    qui restent ensuite avant la seance i)."""
    js = {t[0] for t in B.zf}; prise = np.zeros(len(B.J), bool); apres = np.full(B.n, -1); vide = 0; trous = 0
    for i, s in enumerate(B.test):
        for _ in range(B.gap[i] if i > 0 else 0):
            if vide >= k:
                vide = 0; apres[i] = 0; trous += i >= B.d17
            else:
                vide += 1
                if apres[i] >= 0:
                    apres[i] += 1
        pris = vide >= k
        prise[s] = pris
        vide = 0 if (pris or s in js) else vide + 1
    return prise, apres, int(trous)


def modules(X, Bq):
    jou = np.isfinite(X["entree"]); out = {}
    for nom, stop in (("S50", 0.005), ("S75", 0.0075)):
        g, creux, _ = Nn.gains(X, stop)
        out[nom] = (f"la nuit entière, stop {stop * 100:.2f} %".replace(".", ","), g, creux, jou)
    f = SORTIE / "partie_h1.json"
    best = json.load(open(f)).get("meilleure") if f.exists() else None
    if best:
        g, creux, _ = gains_fenetre(X, Bq, best["fenetre"], best["stop"])
        out["H1"] = (f"{FEN[best['fenetre']]}, {'sans stop' if best['stop'] == 0 else 'stop 0,50 %'}", g, creux, np.isfinite(g) & jou)
    return out


def partie_h2():
    B = Cp.Banc("2026-10-02"); X = Nn.construire(); Bq = barres(); Mo = modules(X, Bq); depuis = B.test[B.d17:]
    L = ["Partie H2 : le module de nuit dans le compte Master Bulenox 50K (2017 → 2 octobre 2026, un Master neuf toutes les 20 séances).",
         "Secours « toujours possible » : un trade de secours qui tombe dans un trou du fichier compte comme un trade à 0 $.", ""]
    res = {}
    m0 = B.mesurer(B.zf); ms0 = B.mesurer(B.zf, inactivite=False)
    L += [Cp.resume("T0 · le bot seul (Z12F, limite 1 000 $, frein)", m0),
          f"    sans la règle d'inactivité : {ms0['trois']:.0%} au 3e retrait, {ms0['plancher']:.0%} perdus par le plancher, touché {n0(ms0['touche_master'])} $", ""]
    res["T0"] = dict(**m0, sans_regle=ms0)
    cas = [(nom, "secours", k) for nom in Mo for k in (2, 3, 4)] + ([("H1", "toutes", 0)] if "H1" in Mo else [])
    for nom, mode, k in cas:
        desc, g, creux, jouable = Mo[nom]
        if mode == "secours":
            prise, apres, trous_gap = secours_tp(B, k)
            ident = f"{nom}-k{k}"; titre = f"{ident} · le bot + {desc}, en secours après {k} jours sans trade"
        else:
            prise, apres, trous_gap = jouable.copy(), None, 0
            ident = f"{nom}-toutes"; titre = f"{ident} · le bot + {desc}, chaque nuit"
        gn = np.where(prise & jouable, g, 0.0); cn = np.where(prise & jouable, creux, 0.0)
        m = B.mesurer(B.zf, gn=gn, cn=cn, tn=prise, apres=apres); ms = B.mesurer(B.zf, gn=gn, cn=cn, tn=prise, inactivite=False, apres=apres)
        nuits = int(prise[depuis].sum()); trous = int((prise & ~jouable)[depuis].sum()) + trous_gap
        ok = m["inactivite"] == 0 and m["plancher"] <= 0.20 and m["touche_master"] > 0
        dec = [B.mesurer(B.zf, gn=gn, cn=cn, tn=prise, apres=apres, depart=d) for d in (5, 10, 15)]      # pour information : autres dates de depart
        tr3 = [m["trois"]] + [x["trois"] for x in dec]; pl3 = [m["plancher"]] + [x["plancher"] for x in dec]; in3 = [m["inactivite"]] + [x["inactivite"] for x in dec]
        res[ident] = dict(module=nom, mode=mode, k=k, nom=titre, **m, sans_regle=ms, nuits=nuits, trous=trous, gain_nuits=float(gn[depuis].sum()), adoptee=bool(ok),
                          departs_decales=dict(trois=tr3, plancher=pl3, inactivite=in3))
        L += [Cp.resume(titre, m),
              f"    trades de nuit depuis 2017 : {nuits + trous_gap} ({(nuits + trous_gap) / len(depuis):.0%} des séances), dont {trous} dans un trou (comptés à 0 $) ; "
              f"gain total de ces nuits {n0(gn[depuis].sum())} $ ; sans la règle d'inactivité : {ms['trois']:.0%} au 3e retrait, {ms['plancher']:.0%} perdus par le plancher",
              f"    → {'ADOPTÉE' if ok else 'non adoptée'} (perdus par inactivité {m['inactivite']:.0%} ; perdus avant le 3e retrait {m['plancher'] + m['inactivite']:.0%}, règle ≤ 20 % ; "
              f"touché {n0(m['touche_master'])} $ ; {m['episodes']} dates de perte distinctes{' : chiffre fragile' if m['episodes'] < 3 else ''})",
              f"    pour information, Masters lancés 5, 10 ou 15 séances plus tard : 3e retrait {min(tr3):.0%} à {max(tr3):.0%}, plancher {min(pl3):.0%} à {max(pl3):.0%}, "
              f"inactivité {min(in3):.0%} à {max(in3):.0%}", ""]
    adopt = [(v["trois"], -v["plancher"], k) for k, v in res.items() if v.get("adoptee")]
    tous = [(-(v["plancher"] + v["inactivite"]), v["trois"], k) for k, v in res.items() if k != "T0"]
    meilleur = max(adopt)[2] if adopt else max(tous)[2]
    res["meilleur"] = meilleur
    L.append(f"Mieux classé : {meilleur} ({'adopté' if adopt else 'aucun adopté : le moins de comptes perdus'}).")
    ecrire("partie_h2", L, res)


# ====================================================================== partie H3 : depuis l'etat actuel du compte
def partie_h3(solde0=50700.0, haut0=51800.0):
    B = Cp.Banc("2026-10-02"); X = Nn.construire(); Bq = barres(); Mo = modules(X, Bq)
    h2 = json.load(open(SORTIE / "partie_h2.json")); best = h2["meilleur"]; nom, k = h2[best]["module"], h2[best]["k"]
    desc, g, creux, jouable = Mo[nom]
    prise, apres, _ = secours_tp(B, k) if h2[best]["mode"] == "secours" else (jouable.copy(), None, 0)
    gn = np.where(prise & jouable, g, 0.0); cn = np.where(prise & jouable, creux, 0.0)
    js = {t[0] for t in B.zf}; T0 = np.array([s in js for s in B.test]); T1 = T0 | prise[B.test]

    def rejouer(R0, D0, R1, D1, T, ap):
        issue = []
        for i0 in range(B.d17, B.n - 120, 5):
            solde, haut, vide, fin = solde0, haut0, 0, "rien"
            for i in range(i0, i0 + 120):
                if i > i0:
                    vide = ap[i] if (ap is not None and ap[i] >= 0) else vide + B.gap[i]
                if vide >= 5:
                    fin = "inactivité"; break
                pl = min(haut - 2500.0, 50000.0)
                R, Dp = (R1, D1) if solde - pl < 1750.0 else (R0, D0)
                if solde + Dp[i] <= pl:
                    fin = "plancher"; break
                solde += R[i]; haut = max(haut, solde)
                vide = 0 if T[i] else vide + 1
                if vide >= 5:
                    fin = "inactivité"; break
                if solde >= 53600.0:
                    fin = "retrait"; break
            issue.append(fin)
        issue = np.array(issue)
        return {x: float((issue == x).mean()) for x in ("plancher", "inactivité", "retrait", "rien")}

    pl0 = min(haut0 - 2500, 50000)
    L = [f"Partie H3 (descriptif) : le compte dans son état actuel : solde {n0(solde0)} $, plus haut de fin de journée {n0(haut0)} $, plancher {n0(pl0)} $, marge {n0(solde0 - pl0)} $.",
         "Rejoué depuis chaque séance de 2017 à octobre 2026, 120 séances au plus, règle d'inactivité comptée (5 jours de trading sans trade = compte perdu).",
         f"Frein : demi-taille (MES au lieu de MNQ) tant que la marge est sous 1 750 $. Secours : {best} ({desc}).", "",
         f"{'cas':<52}{'perdu : plancher':>17}{'perdu : inactivité':>20}{'solde ≥ 53 600 $':>18}{'ni l un ni l autre':>20}"]
    res = {}
    for taille in (1.0, 2.0):
        for nomc, a, b, T, ap in ((f"{taille:.0f} MNQ, le bot seul", None, None, T0, None), (f"{taille:.0f} MNQ, le bot + le secours de nuit", gn, cn, T1, apres)):
            R0, D0 = B.journees(B.zf, taille, 1000.0, a, b); R1, D1 = B.journees(B.zf, taille / 2, 1000.0, a, b)
            r = rejouer(R0, D0, R1, D1, T, ap); res[nomc] = r
            L.append(f"{nomc:<52}{r['plancher']:>16.0%} {r['inactivité']:>19.0%} {r['retrait']:>17.0%} {r['rien']:>19.0%}")
    ecrire("partie_h3", L, res)


# ====================================================================== descriptif : combien par mois
def partie_mois():
    """Gain par mois du bot seul et du bot avec la nuit de secours (stop 0,50 %, apres 2 jours), 1 MNQ, sans frein ni plancher."""
    B = Cp.Banc("2026-10-02"); X = Nn.construire(); jou = np.isfinite(X["entree"])
    g, creux, _ = Nn.gains(X, 0.005); prise, _, _ = secours_tp(B, 2)
    gn = np.where(prise & jou, g, 0.0); cn = np.where(prise & jou, creux, 0.0)
    mois = np.array([j[:7] for j in B.jours[B.d17:]]); res = {}
    L = ["Descriptif : gain par mois, 1 MNQ au prix d'aujourd'hui, frais compris, 2017 → 2 octobre 2026 (sans frein ni plancher).", ""]
    for nom, a, b in (("le bot seul", None, None), ("le bot + la nuit de secours", gn, cn)):
        R, _ = B.journees(B.zf, 1.0, 1000.0, a, b); R = R[B.d17:]
        r = pd.Series(R).groupby(mois).sum(); an = r.groupby(r.index.str[:4]).sum()
        c = np.cumsum(R); d = []
        for i in range(0, len(c) - 1, 5):
            k = np.nonzero(c[i:] - (c[i - 1] if i else 0.0) >= 2900)[0]
            d.append(k[0] + 1 if len(k) else np.nan)
        d = np.array(d)
        res[nom] = dict(mois=len(r), moyenne=float(r.mean()), mediane=float(r.median()), perdants=float(np.mean(r < 0)), pire=float(r.min()), meilleur=float(r.max()),
                        quart_bas=float(r.quantile(.25)), quart_haut=float(r.quantile(.75)), par_an={k: float(v) for k, v in an.items()},
                        seances_2900=dict(mediane=float(np.nanmedian(d)), rapide=float(np.nanpercentile(d, 25)), lent=float(np.nanpercentile(d, 75)), jamais=float(np.mean(np.isnan(d)))))
        x = res[nom]
        L += [f"{nom} : {x['mois']} mois ; moyenne {x['moyenne']:+.0f} $, médiane {x['mediane']:+.0f} $, {x['perdants']:.0%} de mois perdants, pire mois {n0(x['pire'])} $, "
              f"meilleur {n0(x['meilleur'])} $ ; un mois sur quatre sous {x['quart_bas']:+.0f} $, un sur quatre au-dessus de {x['quart_haut']:+.0f} $",
              "    par an : " + ", ".join(f"{k} {n0(v)} $" for k, v in x["par_an"].items()),
              f"    séances pour gagner 2 900 $ (plancher non compté) : médiane {x['seances_2900']['mediane']:.0f}, un quart en moins de {x['seances_2900']['rapide']:.0f}, "
              f"un quart en plus de {x['seances_2900']['lent']:.0f}, jamais atteint {x['seances_2900']['jamais']:.0%}", ""]
    ecrire("mois", L, res)


if __name__ == "__main__":
    for q in sys.argv[1:] or ["g", "h1", "h2", "h3", "mois"]:
        {"g": partie_g, "h1": partie_h1, "h2": partie_h2, "h3": partie_h3, "mois": partie_mois}[q]()
        print()
