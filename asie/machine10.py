#!/usr/bin/env python3
"""Machine 10 (asie/README.md) : deux familles jamais testees dans le projet, aux frais d'aujourd'hui.
B : l'elan de fin de seance (Baltussen et al. 2021) a l'heure de reglement propre a chaque marche (or 13 h 30, argent
13 h 25, petrole 14 h 30, devises 15 h, heure de New York), et non a 15 h 30 - 16 h comme dans l'etude large.
T : le retournement de l'ouverture de Tokyo apres la seance americaine (vu sur le Nikkei par la machine 9, t 5,45 avant
frais), joue sur des contrats peu chers (MNQ, MES, MGC).
Usage : ASIE_DONNEES=<dossier HistData 5 min UTC> python3 asie/machine10.py exploration | coffre
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
import machine9 as M9  # noqa: E402

DEBUT, FIN_EXPLO, DEBUT_COFFRE, FIN = M7.DEBUT, M7.FIN_EXPLO, M7.DEBUT_COFFRE, M9.FIN
NY = M7.NY
N_SIGNES, GRAINE = 1000, 10

# code : (nom, $ d'un aller-retour : 2 ticks + commissions, nominal en $ d'un contrat selon le prix)
CONTRATS = {
    "usatechidxusd": ("Nasdaq 100 (MNQ)", 3.0, lambda p: 2.0 * p),
    "usa500idxusd": ("S&P 500 (MES)", 4.0, lambda p: 5.0 * p),
    "xauusd": ("Or (MGC)", 4.0, lambda p: 10.0 * p),
    "xagusd": ("Argent (SIL)", 12.0, lambda p: 1000.0 * p),
    "bcousd": ("Petrole (CL ; Brent HistData en approximation)", 25.0, lambda p: 1000.0 * p),
    "eurusd": ("Euro (6E)", 17.5, lambda p: 125000.0 * p),
    "gbpusd": ("Livre (6B)", 17.5, lambda p: 62500.0 * p),
    "usdjpy": ("Yen (6J)", 17.5, lambda p: 12_500_000.0 / p),
    "audusd": ("Dollar australien (6A)", 15.0, lambda p: 100000.0 * p),
    "usdcad": ("Dollar canadien (6C)", 15.0, lambda p: 100000.0 / p),
    "usdchf": ("Franc suisse (6S)", 17.5, lambda p: 125000.0 / p),
    "nzdusd": ("Dollar neo-zelandais (6N)", 15.0, lambda p: 100000.0 * p),
}
REGLEMENT = {"xauusd": "13:30", "xagusd": "13:25", "bcousd": "14:30", "eurusd": "15:00", "gbpusd": "15:00", "usdjpy": "15:00",
             "audusd": "15:00", "usdcad": "15:00", "usdchf": "15:00", "nzdusd": "15:00"}
_M = {}


def marche(code):
    """Cotations HistData ; frais en points de base au prix d'aujourd'hui (dernier prix avant la fin du coffre)."""
    if code not in _M:
        M7.MARCHES.setdefault(code, (CONTRATS[code][0], 0.0, "pb", 1.0))
        M = M7.Marche(code)
        i_fin = M.indice(pd.DatetimeIndex([pd.Timestamp(FIN, tz="UTC")]))[0]
        dernier = M.C[:i_fin][np.isfinite(M.C[:i_fin])][-1]
        nom, dollars, nominal = CONTRATS[code]
        M.nom, M.unite, M.frais = nom, "pb", dollars / nominal(dernier) * 1e4
        M.notionnel = (lambda f: (lambda p: f(p)))(nominal)
        _M[code] = M
    return _M[code]


def jours_ny(debut, fin):
    j = pd.date_range(debut, fin, freq="D"); fer = holidays.NYSE(years=range(j[0].year, j[-1].year + 1))
    return j[(j.dayofweek < 5) & ~np.array([d.date() in fer for d in j])]


def hhmm_moins(h, minutes):
    t = pd.Timestamp("2000-01-01 " + h) - pd.Timedelta(minutes=minutes)
    return t.strftime("%H:%M")


def jouer(s, M, debut, fin):
    if s["famille"] == "T":
        M9_s = dict(s, famille="N2")
        return M9.jouer(M9_s, M, debut, fin)
    j = jours_ny(debut, fin); reg = REGLEMENT[s["marche"]]; avant = hhmm_moins(reg, 30)
    i_e = M.indice(M7.utc(j, NY, avant)); i_s = M.indice(M7.utc(j, NY, reg))
    ia = np.full(len(j), -1, np.int64); ia[1:] = M.indice(M7.utc(j, NY, reg))[:-1]       # reglement de la veille
    mv = M9.prix(M, i_e) / M9.prix(M, ia) - 1
    sens = np.where(np.isfinite(mv), np.sign(mv), 0.0)
    ok = (i_e >= 0) & (i_s > i_e) & (sens != 0)
    e, x = M9.prix(M, np.where(ok, i_e, -1)), M9.prix(M, np.where(ok, i_s, -1))
    ok &= np.isfinite(e) & np.isfinite(x)
    brut = sens[ok] * (x[ok] / e[ok] - 1)
    return pd.DataFrame({"jour": j[ok], "brut": brut, "r": brut - np.array([M.cout(v) for v in e[ok]]), "e": e[ok], "signal": mv[ok]})


def strategies():
    S = [dict(nom=f"T {CONTRATS[c][0]} : ouverture de Tokyo (9 h 00 -> 9 h 30) contre la seance du S&P 500", famille="T", marche=c,
              entree="09:00", sortie="09:30", signal_sp=True, sens="retour") for c in ("usatechidxusd", "usa500idxusd", "xauusd")]
    S += [dict(nom=f"B {CONTRATS[c][0]} : elan de fin de seance, {hhmm_moins(REGLEMENT[c], 30)} -> {REGLEMENT[c]} (New York)",
               famille="B", marche=c) for c in REGLEMENT]
    return S


def bilan(d, M):
    b = M9.bilan(d, M)
    b["frais_pb"] = round(M.frais, 2)
    return b


def placebo(d):
    t_reel = M7.t_stat(d["r"].to_numpy())
    rng = np.random.default_rng(GRAINE); brut = d["brut"].to_numpy(); cout = brut - d["r"].to_numpy()
    ts = np.array([M7.t_stat(rng.choice([-1.0, 1.0], len(brut)) * brut - cout) for _ in range(N_SIGNES)])
    return float((ts >= t_reel).mean())


def exploration():
    S = strategies(); res = []
    for s in S:
        M = marche(s["marche"]); d = jouer(s, M, DEBUT, FIN_EXPLO); b = bilan(d, M); b.update(nom=s["nom"], famille=s["famille"])
        b["testable"] = b["jours"] >= 200
        b["p"] = placebo(d) if b["testable"] else None
        res.append(b)
        print(f"{s['nom']} : frais {b['frais_pb']} pb, brut {b['brut_moyen_pb']:+.2f} pb (t {b['t_brut']:+.2f}), net {b['net_moyen_pb']:+.2f} pb "
              f"(t {b['t']:+.2f}), p {b['p']}, {b['jours']} jours, sous-periodes {b['sous_periodes']}", flush=True)
    jug = [r for r in res if r["testable"]]
    bh = M7.benjamini_hochberg([r["p"] for r in jug])
    for r in res:
        r["bh"] = r["survivante"] = False
    for r, g in zip(jug, bh):
        r["bh"] = bool(g)
        r["survivante"] = bool(r["t"] >= 2 and r["p"] <= 0.05 and sum(x > 0 for x in r["sous_periodes"]) >= 2 and g)
    surv = [r["nom"] for r in res if r["survivante"]]
    L = [f"Machine 10, exploration 2012 - 2022 : {len(S)} regles ; survivantes : {len(surv)}", "",
         "regle | frais (pb) | brut moyen (pb, t) | net moyen (pb) | t net | p placebo | BH 10 % | sous-periodes (pb) | jours | $ pour 1 contrat | survivante"]
    for r in sorted(res, key=lambda x: -x["t"]):
        L.append(f"{r['nom']} | {r['frais_pb']} | {r['brut_moyen_pb']:+.2f} ({r['t_brut']:+.2f}) | {r['net_moyen_pb']:+.2f} | {r['t']:+.2f} | "
                 + (f"{r['p']:.3f}" if r["testable"] else "-") + f" | {'oui' if r['bh'] else 'non'} | "
                 + " / ".join(f"{x:+.1f}" for x in r["sous_periodes"]) + f" | {r['jours']} | {r['dollars_1_contrat']:+,.0f} | {'OUI' if r['survivante'] else ''}")
    (ICI / "exploration10.txt").write_text("\n".join(L) + "\n")
    (ICI / "exploration10.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    (ICI / "survivantes10.json").write_text(json.dumps(surv, indent=1, ensure_ascii=False))
    print("\n".join(L))


def coffre():
    surv = json.loads((ICI / "survivantes10.json").read_text())
    if not surv:
        print("Aucune survivante : le coffre 2023 - 2026 reste ferme."); return
    S = {s["nom"]: s for s in strategies()}; m = len(surv); seuil = float(norm.ppf(1 - 0.05 / m))
    L = [f"Machine 10, coffre 2023 -> {FIN} : {m} survivantes, seuil de Bonferroni t >= {seuil:.2f}, 3 annees positives sur 4", ""]
    res = []
    for nom in surv:
        s = S[nom]; M = marche(s["marche"]); d = jouer(s, M, DEBUT_COFFRE, FIN); jj = M9.par_jour(d)
        an = pd.DatetimeIndex(jj.index).year
        par_an = {y: round(float(jj["r"][an == y].sum()) * 1e4, 1) for y in (2023, 2024, 2025, 2026)}
        t = M7.t_stat(jj["r"].to_numpy()); passe = bool(t >= seuil and sum(v > 0 for v in par_an.values()) >= 3)
        b = bilan(d, M)
        res.append(dict(nom=nom, t=round(t, 2), par_an=par_an, jours=len(jj), net_moyen_pb=b["net_moyen_pb"], brut_moyen_pb=b["brut_moyen_pb"],
                        dollars_1_contrat=b["dollars_1_contrat"], passe=passe))
        L.append(f"{nom} | t {t:+.2f} | brut {b['brut_moyen_pb']:+.2f} pb, net {b['net_moyen_pb']:+.2f} pb | "
                 + " / ".join(f"{y} {v:+.1f}" for y, v in par_an.items()) + f" | {b['dollars_1_contrat']:+,.0f} $ | {'PASSE' if passe else 'echoue'}")
    (ICI / "coffre10.txt").write_text("\n".join(L) + "\n"); (ICI / "coffre10.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("\n".join(L))


if __name__ == "__main__":
    {"exploration": exploration, "coffre": coffre}[sys.argv[1]]()
