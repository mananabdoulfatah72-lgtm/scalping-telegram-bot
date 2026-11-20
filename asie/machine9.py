#!/usr/bin/env python3
"""Machine 9 (asie/README.md) : les pistes de la recherche sur la session asiatique (20 novembre 2026), jugees comme les
machines 5 et 7 : exploration 2012 - 2022 avec placebos et Benjamini-Hochberg, coffre 2023 -> fin des donnees ouvert une
seule fois pour les survivantes.

Donnees : ASIE_DONNEES = un dossier avec les fichiers <code>_<annee>_5m.csv.gz (t en UTC, o, h, l, c ; HistData, prix
acheteur) de sessions24/annees (branche claude/keen-babbage-r686cl) et de donnees_libres/histdata_5min (branche
claude/affectionate-turing-tnz0mn), par exemple avec git show comme dans machine7.py.
Usage : ASIE_DONNEES=<dossier> python3 asie/machine9.py exploration | coffre
"""
import json
import sys
from pathlib import Path

import holidays
import numpy as np
import pandas as pd
from scipy.stats import norm

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import machine7 as M7  # noqa: E402

DEBUT, FIN_EXPLO, DEBUT_COFFRE = M7.DEBUT, M7.FIN_EXPLO, M7.DEBUT_COFFRE
FIN = "2026-10-02"
SOUS = M7.SOUS
TOKYO = "Asia/Tokyo"
REFORME_TSE = pd.Timestamp("2024-11-05")          # cloture de la Bourse de Tokyo : 15 h 00 avant, 15 h 30 depuis
N_SIGNES, GRAINE = 1000, 9

# code : (nom, frais d'un aller-retour, unite, $ par point du contrat vise) ; Nikkei : Micro Nikkei (MNK), 0,50 $ par
# point, 2 ticks de 5 points + 2 $ de frais = environ 2,8 points de base a 50 000 (note de recherche japon.md)
M7.MARCHES.update({"jpxjpy": ("Nikkei 225", 2.8, "pb", 0.5)})


def jours_tokyo(debut, fin):
    """Jours ou la Bourse de Tokyo ouvre : lundi - vendredi, hors jours feries japonais et 31 decembre - 3 janvier."""
    j = pd.date_range(debut, fin, freq="D")
    jp = holidays.Japan(years=range(j[0].year, j[-1].year + 1))
    ferme = np.array([(d.date() in jp) or (d.month == 12 and d.day == 31) or (d.month == 1 and d.day <= 3) for d in j])
    return j[(j.dayofweek < 5) & ~ferme]


def heure_tokyo(jours, spec):
    """spec : 'HH:MM' (heure de Tokyo) ou ('TSE', minutes) = cloture de la Bourse de Tokyo du jour + minutes."""
    if isinstance(spec, str):
        return M7.utc(jours, TOKYO, spec)
    cl = np.where(jours < REFORME_TSE, 15 * 60, 15 * 60 + 30) + spec[1]
    loc = jours + pd.to_timedelta(cl, unit="m")
    return loc.tz_localize(TOKYO).tz_convert("UTC")


_SP = {}


def prix(M, i):
    return np.where(i >= 0, M.O[np.clip(i, 0, M.n - 1)], np.nan)


def jouer(s, M, debut, fin, decalage=0):
    """Trades d'une regle (DataFrame : jour, brut signe avant frais, r net, e prix d'entree)."""
    if s["famille"] == "Z":
        return jouer_zone(s, M, debut, fin)
    j = jours_tokyo(debut, fin)
    i_e = M.indice(heure_tokyo(j, s["entree"])) + decalage
    i_s = M.indice(heure_tokyo(j, s["sortie"])) + decalage
    if s.get("signal_sp"):
        sp = _SP.setdefault("sp", M7.Marche("usa500idxusd"))
        ny = pd.date_range("2011-12-01", fin, freq="D"); fer = holidays.NYSE(years=range(2011, ny[-1].year + 1))
        ny = ny[(ny.dayofweek < 5) & ~np.array([d.date() in fer for d in ny])]
        k = np.searchsorted(ny.values, (j - pd.Timedelta(days=1)).values, side="right") - 1     # derniere seance <= veille
        u, up = ny[np.clip(k, 1, None)], ny[np.clip(k - 1, 0, None)]
        mv = prix(sp, sp.indice(M7.utc(u, M7.NY, "16:00"))) / prix(sp, sp.indice(M7.utc(up, M7.NY, "16:00"))) - 1
        sens = np.where(np.isfinite(mv) & (k >= 1), np.sign(mv), 0.0) * (-1.0 if s["sens"] == "retour" else 1.0)
    elif s.get("signal") is None:
        sens = np.full(len(j), float(s["sens"]))
    else:
        a, b = s["signal"]                                    # mouvement de a a b (a de la veille si a[0] == 'veille')
        if isinstance(a, tuple) and a[0] == "veille":
            ia = np.full(len(j), -1, np.int64); ia[1:] = M.indice(heure_tokyo(j, a[1]))[:-1]
        else:
            ia = M.indice(heure_tokyo(j, a))
        ib = M.indice(heure_tokyo(j, b))
        mv = prix(M, ib) / prix(M, ia) - 1
        sens = np.where(np.isfinite(mv) & (np.abs(mv) >= s.get("seuil", 0.0)), np.sign(mv), 0.0)
        sens *= -1.0 if s["sens"] == "retour" else 1.0
    ok = (i_e >= 0) & (i_s > i_e) & (i_s < M.n) & (sens != 0)
    e, x = prix(M, np.where(ok, i_e, -1)), prix(M, np.where(ok, i_s, -1))
    ok &= np.isfinite(e) & np.isfinite(x)
    brut = sens[ok] * (x[ok] / e[ok] - 1)
    cout = np.array([M.cout(v) for v in e[ok]]) if ok.any() else np.array([])
    sig = mv[ok] if (s.get("signal") is not None or s.get("signal_sp")) else np.full(int(ok.sum()), np.nan)
    return pd.DataFrame({"jour": j[ok], "brut": brut, "r": brut - cout, "e": e[ok], "signal": sig})


# ------------------------------------------------------------------ famille Z : la zone de bruit pendant la seance de Tokyo
CTRL = ["09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "15:00"]
JOURS_BRUIT = 14


def seances_tokyo(M, debut, fin):
    """Pour chaque jour de Bourse : O (ouverture de 9 h 00), C (cloture de la veille), prix aux controles, prix moyen, sortie."""
    j = jours_tokyo(pd.Timestamp(debut) - pd.Timedelta(days=40), fin)
    i0 = M.indice(heure_tokyo(j, "09:00")); icl = M.indice(heure_tokyo(j, ("TSE", 0)))
    ic = np.array([M.indice(heure_tokyo(j, h)) for h in CTRL])            # barres qui commencent a l'heure du controle
    out = []
    for n, jour in enumerate(j):
        a, b = i0[n], icl[n]
        if a < 1 or b <= a or b >= M.n or not np.isfinite(M.O[a]) or not np.isfinite(M.O[b]) or (ic[:, n] < 1).any():
            continue
        ctrl = M.C[ic[:, n] - 1]                                            # cloture de la barre qui finit au controle
        if not np.isfinite(ctrl).all():
            continue
        veille = M.C[icl[n - 1] - 1] if n > 0 and icl[n - 1] > 0 else np.nan
        cl = M.C[a:ic[-1, n]]
        moy = np.array([np.nanmean(cl[:ic[k, n] - a]) for k in range(len(CTRL))])
        nb = 11 if jour < REFORME_TSE else 12                               # controles jusqu'a 30 min avant la cloture
        out.append(dict(jour=jour, O=M.O[a], C=veille, ctrl=ctrl, moy=moy, nb=nb, sortie=M.O[b]))
    return out


def jouer_zone(s, M, debut, fin):
    N_ = seances_tokyo(M, debut, fin); lg = s["largeur"]; trades = []
    for n in range(JOURS_BRUIT, len(N_)):
        x = N_[n]
        if x["jour"] < pd.Timestamp(debut):
            continue
        bruit = np.mean([np.abs(N_[q]["ctrl"] / N_[q]["O"] - 1) for q in range(n - JOURS_BRUIT, n)], axis=0)
        ref_h = max(x["O"], x["C"]) if np.isfinite(x["C"]) else x["O"]
        ref_b = min(x["O"], x["C"]) if np.isfinite(x["C"]) else x["O"]
        haut, bas = ref_h * (1 + lg * bruit), ref_b * (1 - lg * bruit)
        pos, e = 0, 0.0
        for k in range(x["nb"]):
            p = x["ctrl"][k]
            if pos > 0 and p <= max(haut[k], x["moy"][k]):
                trades.append((x["jour"], p / e - 1, e)); pos = 0
            elif pos < 0 and p >= min(bas[k], x["moy"][k]):
                trades.append((x["jour"], -(p / e - 1), e)); pos = 0
            if pos == 0 and k < x["nb"] - 1:
                if p > haut[k]:
                    pos, e = 1, p
                elif p < bas[k]:
                    pos, e = -1, p
        if pos != 0:
            trades.append((x["jour"], pos * (x["sortie"] / e - 1), e))
    d = pd.DataFrame(trades, columns=["jour", "brut", "e"])
    d["r"] = d["brut"] - np.array([M.cout(v) for v in d["e"]]) if len(d) else []
    return d


def par_jour(d):
    return d.groupby("jour")[["brut", "r"]].sum() if len(d) else pd.DataFrame(columns=["brut", "r"])


def placebo(s, M, d):
    t_reel = M7.t_stat(par_jour(d)["r"].to_numpy())
    if s["famille"] != "Z" and s.get("signal") is None and not s.get("signal_sp"):  # la meme fenetre aux autres heures
        ts = [M7.t_stat(par_jour(jouer(s, M, DEBUT, FIN_EXPLO, decalage=k))["r"].to_numpy()) for k in range(-144, 145) if abs(k) * 5 > 120]
    else:                                                 # le sens de chaque trade tire au hasard, somme par jour
        rng = np.random.default_rng(GRAINE); brut = d["brut"].to_numpy(); cout = brut - d["r"].to_numpy()
        ids = pd.factorize(d["jour"])[0]
        ts = [M7.t_stat(np.bincount(ids, rng.choice([-1.0, 1.0], len(brut)) * brut - cout)) for _ in range(N_SIGNES)]
    ts = np.array(ts)
    return float((ts >= t_reel).mean()), len(ts)


def bilan(d, M):
    j = par_jour(d); an = pd.DatetimeIndex(j.index).year
    dol = d["r"].to_numpy() * np.array([M.notionnel(e) for e in d["e"].to_numpy()])
    c0 = (d["brut"] - d["r"]).to_numpy(); e = d["e"].to_numpy(); ids = pd.factorize(d["jour"])[0] if len(d) else np.array([], int)
    t14 = M7.t_stat(np.bincount(ids, d["brut"].to_numpy() - 14.0 / e)) if len(d) else 0.0
    t2x = M7.t_stat(np.bincount(ids, d["brut"].to_numpy() - 2 * c0)) if len(d) else 0.0
    return {"t": round(M7.t_stat(j["r"].to_numpy()), 2), "t_brut": round(M7.t_stat(j["brut"].to_numpy()), 2),
            "t_frais_14_points": round(t14, 2), "t_frais_doubles": round(t2x, 2), "jours": int(len(j)), "trades": int(len(d)),
            "net_moyen_pb": round(float(j["r"].mean()) * 1e4, 2) if len(j) else 0.0,
            "brut_moyen_pb": round(float(j["brut"].mean()) * 1e4, 2) if len(j) else 0.0,
            "dollars_1_contrat": round(float(dol.sum()), 0),
            "sous_periodes": [round(float(j["r"][(an >= a) & (an <= b)].sum()) * 1e4, 1) for a, b in SOUS]}


def strategies():
    """Les 5 regles fixees dans asie/README.md (machine 9) avant tout calcul."""
    fin_osaka = dict(entree=("TSE", -15), sortie=("TSE", 15))
    return [
        dict(nom="N1 fin de seance d'Osaka dans le sens de la journee", famille="N1", marche="jpxjpy", **fin_osaka,
             signal=(("veille", ("TSE", 15)), ("TSE", -15)), sens="continuation"),
        dict(nom="N1v meme fenetre, signal de Gao et al. (veille C+15 -> 9 h 30)", famille="N1", marche="jpxjpy", **fin_osaka,
             signal=(("veille", ("TSE", 15)), "09:30"), sens="continuation"),
        dict(nom="N2 ouverture de Tokyo (9 h 00 -> 9 h 30) contre la seance du S&P 500", famille="N2", marche="jpxjpy",
             entree="09:00", sortie="09:30", signal_sp=True, sens="retour"),
        dict(nom="N2v fin de seance d'Osaka dans le sens de la seance du S&P 500", famille="N2", marche="jpxjpy", **fin_osaka,
             signal_sp=True, sens="continuation"),
        dict(nom="Z zone de bruit pendant la seance de Tokyo (largeur 1,0)", famille="Z", marche="jpxjpy", largeur=1.0),
    ]


def exploration():
    S = strategies()
    marches = {}
    res = []
    for s in S:
        M = marches.setdefault(s["marche"], M7.Marche(s["marche"]))
        d = jouer(s, M, DEBUT, FIN_EXPLO); b = bilan(d, M); b.update(nom=s["nom"], famille=s["famille"])
        if b["jours"] < 200:
            b.update(p=None, testable=False)
        else:
            p, npl = placebo(s, M, d); b.update(p=p, placebos=npl, testable=True)
        res.append(b)
        print(f"{s['nom']} : t {b['t']:+.2f}, brut {b['brut_moyen_pb']:+.2f} pb, net {b['net_moyen_pb']:+.2f} pb, p {b.get('p')}, "
              f"{b['jours']} jours, sous-periodes {b['sous_periodes']}", flush=True)
    jug = [r for r in res if r["testable"]]
    bh = M7.benjamini_hochberg([r["p"] for r in jug]) if jug else []
    for r in res:
        r["bh"] = r["survivante"] = False
    for r, g in zip(jug, bh):
        r["bh"] = bool(g)
        r["survivante"] = bool(r["t"] >= 2 and r["p"] <= 0.05 and sum(x > 0 for x in r["sous_periodes"]) >= 2 and g)
    surv = [r["nom"] for r in res if r["survivante"]]
    L = [f"Machine 9, exploration 2012 - 2022 : {len(S)} regles, {len(jug)} testables ; survivantes : {len(surv)}", "",
         "regle | t | brut moyen (pb) | net moyen (pb) | p placebo | BH 10 % | sous-periodes (pb) | jours | $ pour 1 contrat | survivante"]
    for r in sorted(res, key=lambda x: -x["t"]):
        L.append(f"{r['nom']} | {r['t']:+.2f} | {r['brut_moyen_pb']:+.2f} | {r['net_moyen_pb']:+.2f} | "
                 + (f"{r['p']:.3f}" if r["testable"] else "non testable") + f" | {'oui' if r['bh'] else 'non'} | "
                 + " / ".join(f"{x:+.1f}" for x in r["sous_periodes"]) + f" | {r['jours']} | {r['dollars_1_contrat']:+,.0f} | {'OUI' if r['survivante'] else ''}")
    (ICI / "exploration9.txt").write_text("\n".join(L) + "\n")
    (ICI / "exploration9.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    (ICI / "survivantes9.json").write_text(json.dumps(surv, indent=1, ensure_ascii=False))
    print("\n".join(L))


def coffre():
    surv = json.loads((ICI / "survivantes9.json").read_text())
    if not surv:
        print("Aucune survivante : le coffre 2023 - 2026 reste ferme."); return
    S = {s["nom"]: s for s in strategies()}; m = len(surv); seuil = float(norm.ppf(1 - 0.05 / m))
    marches = {}
    L = [f"Machine 9, coffre 2023 -> {FIN} : {m} survivantes, seuil de Bonferroni t >= {seuil:.2f}, 3 annees positives sur 4", ""]
    res = []
    for nom in surv:
        s = S[nom]; M = marches.setdefault(s["marche"], M7.Marche(s["marche"]))
        d = jouer(s, M, DEBUT_COFFRE, FIN); jj = par_jour(d); an = pd.DatetimeIndex(jj.index).year
        par_an = {y: round(float(jj["r"][an == y].sum()) * 1e4, 1) for y in (2023, 2024, 2025, 2026)}
        t = M7.t_stat(jj["r"].to_numpy()); passe = bool(t >= seuil and sum(v > 0 for v in par_an.values()) >= 3)
        b = bilan(d, M)
        res.append(dict(nom=nom, t=round(t, 2), par_an=par_an, jours=len(d), net_moyen_pb=b["net_moyen_pb"],
                        dollars_1_contrat=b["dollars_1_contrat"], passe=passe))
        L.append(f"{nom} | t {t:+.2f} | net {b['net_moyen_pb']:+.2f} pb | " + " / ".join(f"{y} {v:+.1f}" for y, v in par_an.items())
                 + f" | {b['dollars_1_contrat']:+,.0f} $ | {'PASSE' if passe else 'echoue'}")
    (ICI / "coffre9.txt").write_text("\n".join(L) + "\n"); (ICI / "coffre9.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("\n".join(L))


if __name__ == "__main__":
    {"exploration": exploration, "coffre": coffre}[sys.argv[1]]()
