#!/usr/bin/env python3
"""Donnees de la vue ARENE du terminal (F9) : classement des bots, des variantes et des quatre pistes de l'arene
(ml/arene/resultats/etape1-3.json), courbes, resultats par seance pour rejouer le compte finance dans la page, et le
diagnostic des premieres annees (pas une regle : il sert a lire les pistes retenues).
Lancer depuis n'importe ou : MINUTES_NQ=... CACHE_DOSSIER=... python3 terminal/prep3.py <dossier de l'arene>"""
import glob
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "ml/arene")); sys.path.insert(0, str(R / "ml"))
import bots as BT  # noqa: E402

S = Path("/tmp/claude-0/-home-user-scalping-telegram-bot/73d2fc28-0760-5668-987b-2a927564efe7/scratchpad")
ARENE = Path(sys.argv[1]) if len(sys.argv) > 1 else S / "arene"
ARENE3 = Path(sys.argv[2]) if len(sys.argv) > 2 else None          # dossier de l'arene apres la vague 3 (courbes V1 - V7)
ARENE4 = Path(sys.argv[3]) if len(sys.argv) > 3 else None          # dossier de l'arene apres la vague 4 (courbes W1 - W3)
ARENE5 = Path(sys.argv[4]) if len(sys.argv) > 4 else None          # dossier de l'arene apres la vague 5 (courbes P1 - P3)
ARENE6 = Path(sys.argv[5]) if len(sys.argv) > 5 else None          # apres la vague 6 (M1 - M3, L1 - L4)
ARENE7 = Path(sys.argv[6]) if len(sys.argv) > 6 else None          # apres la vague 7 (S1 - S3)
ARENE8 = Path(sys.argv[7]) if len(sys.argv) > 7 else None          # apres la vague 8 (R1 - R3, F1 - F4)
RES = R / "ml/arene/resultats"
E1 = json.load(open(RES / "etape1.json")); E2 = json.load(open(RES / "etape2.json")); E3 = json.load(open(RES / "etape3.json"))["resultats"]
relief = json.load(open(ARENE / "relief.json"))

B = BT.Base(os.environ["CACHE_DOSSIER"])
aj = B.an[B.test]; n = len(B.test); d17 = int(np.argmax(aj >= 2017))
jours = [B.J[s] for s in B.test]

# ------------------------------------------------------------------ trades des bots rejouables dans la page
zt = BT.zone(B); xt = BT.xgboost(B); st = BT.supertrend(B)
sensp = lambda g: 0 if not np.isfinite(B.p[g]) else (1 if B.p[g] > 0.5 else -1)
F = B.X["F"]
# vague 2 du labo zipline (labo_zipline/VAGUE2.md, Z12) : pas de trade le jour J si le VIX etait >= VIX a 3 mois a la cloture de J-1
_v = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(R / "radar/donnees/jour/yahoo/*.csv.gz")))])
_v = _v[_v.serie.isin(["^VIX:c", "^VIX3M:c"])].pivot_table(index="date", columns="serie", values="valeur"); _v.index = pd.to_datetime(_v.index)
_e = (_v["^VIX:c"] - _v["^VIX3M:c"]).dropna(); _j = pd.to_datetime([B.J[s] for s in range(len(B.J))])
INVERSE = (_e.reindex(_j.union(_e.index)).ffill().shift(1).reindex(_j) >= 0).to_numpy()
TR = {
    "zone": zt, "xgb": xt, "st": st,
    "B3": [t for t in zt if sensp(BT.bougie_avant(t[0], t[2])) == t[1]],
    "B2": [t for t in st if sensp(BT.bougie_avant(t[0], t[2])) == t[1]],
    "B1": BT.xgboost(B, filtre=lambda i: F[i, 18] == (1 if B.p[i] > 0.5 else -1)),
}
TR["Z12"] = [x for x in zt if not INVERSE[x[0]]]
TR["B3Z12"] = [x for x in TR["B3"] if not INVERSE[x[0]]]
ECHELLES = ("zone", "B3")                      # tailles 2 et 3 MNQ seulement pour ces deux-la (piste A)
rejeu = {}
for k, tr in TR.items():
    e = {}
    for t in ((1, 2, 3) if k in ECHELLES else (1,)):
        r, d, ntr = BT.journees(B, tr, t, min(400.0 * t, 1100.0))
        e[f"r{t}"] = [round(float(x), 1) for x in r[B.test]]; e[f"d{t}"] = [round(float(x), 1) for x in d[B.test]]
        if t == 1:
            e["tr"] = "".join("1" if x > 0 else "0" for x in ntr[B.test])
    rejeu[k] = e
# controle : la page rejoue avec ces nombres arrondis au dixieme ; le Python les rejoue aussi pour comparer
v_zone = BT.vie(np.vstack([np.array(rejeu["zone"]["r1"])] * 3), np.vstack([np.array(rejeu["zone"]["d1"])] * 3),
                np.array([c == "1" for c in rejeu["zone"]["tr"]]))
print("controle zone arrondie : net/an", round(v_zone["net_an"]), "(etape 1 :", round(E1["zone"]["net_an"]), ")")


# ------------------------------------------------------------------ diagnostic des premieres annees (comme verif3)
def parcours(Rx, Dx, Tx, s2v, s3v, gv, i0, i1):
    phase = 1; solde = haut = base_ = 50000.0; meil = 0.0; jr = 0; nret = 0; ret = fr = 0.0; g = 0; dq = 0; prem = -1
    for i in range(i0, i1):
        pl = min(haut - 2500, 50100); t = 0
        if phase == 1:
            m = solde - pl; t = 2 if m >= s3v[i] else 1 if m >= s2v[i] else 0
        else:
            if dq % 20 == 0:
                fr += 100
            dq += 1
        if solde + Dx[t, i] <= pl:
            if phase == 1:
                g += 1
            phase = 0; dq = 0; solde = haut = base_ = 50000.0; meil = 0.0; jr = 0
            continue
        solde += Rx[t, i]; haut = max(haut, solde)
        if phase == 0:
            if solde >= 53000:
                fr += 148; phase = 1; solde = haut = base_ = 50000.0; meil = 0.0; jr = 0; nret = 0
            continue
        jr += Tx[i]; meil = max(meil, Rx[t, i])
        dispo = solde - (50000 + gv[i])
        if nret < 3:
            dispo = min(dispo, 1500)
        if jr >= 10 and dispo >= 1000 and solde - base_ > 0 and meil <= 0.4 * (solde - base_):
            ret += dispo; solde -= dispo; base_ = solde; meil = 0.0; jr = 0; nret += 1
            if prem < 0:
                prem = i - i0
    return ret - fr, g, prem


def tab(k):
    e = rejeu[k]; ts = (1, 2, 3) if f"r3" in e else (1, 1, 1)
    return (np.vstack([np.array(e[f"r{t}"]) for t in ts]), np.vstack([np.array(e[f"d{t}"]) for t in ts]), np.array([c == "1" for c in e["tr"]]))


CHOIX_A = {}                                    # choix de la piste A en marche avant (journal de l'etape 3)
ECH = {"fixe 1 MNQ": (1e12, 1e12), "E1": (3500.0, 5000.0), "E2": (4000.0, 6000.0), "E3": (5000.0, 1e12)}
for Y, txt in E3["A"]["choix"].items():
    ech = next(k for k in ECH if txt.split(", ")[1].startswith(k)) if "fixe" not in txt else "fixe 1 MNQ"
    CHOIX_A[int(Y)] = (ech, float(txt.rsplit("coussin ", 1)[1].split(" ")[0]))
s2A = np.full(n, 1e12); s3A = np.full(n, 1e12); gA = np.full(n, 2600.0)
for Y, (ech, c) in CHOIX_A.items():
    q = aj == Y; s2A[q], s3A[q] = ECH[ech]; gA[q] = c
un = np.full(n, 1e12); g26 = np.full(n, 2600.0)
cas = {"A": (*tab("zone"), s2A, s3A, gA), "zone": (*tab("zone"), un, un, g26), "B3": (*tab("B3"), un, un, g26),
       "xgb": (*tab("xgb"), un, un, g26), "st": (*tab("st"), un, un, g26), "Z12": (*tab("Z12"), un, un, g26),
       "B3Z12": (*tab("B3Z12"), un, un, g26)}
diag = []
for nom_h, h, deb in (("1 an", 250, d17), ("2 ans", 500, d17), ("1 an, départs 2023 - 2025", 250, int(np.argmax(aj >= 2023)))):
    for k, (Rx, Dx, Tx, a_, b_, c_) in cas.items():
        v = np.array([parcours(Rx, Dx, Tx, a_, b_, c_, i0, i0 + h) for i0 in range(deb, n - h, 20)], float)
        diag.append(dict(horizon=nom_h, id=k, departs=len(v), net=float(v[:, 0].mean()), grille=float((v[:, 1] > 0).mean()),
                         sans_retrait=float((v[:, 2] < 0).mean()), premier=float(np.median(v[v[:, 2] >= 0, 2])) if (v[:, 2] >= 0).any() else None))
for x in diag:
    print(x["horizon"], x["id"], round(x["net"]), f"{x['grille']:.0%}", f"{x['sans_retrait']:.0%}", x["premier"])

# ------------------------------------------------------------------ classement
COUL = {"st": "#3cc8ff", "zone": "#b48cff", "xgb": "#ffa028", "B1": "#7fe0a0", "B2": "#2fd16f", "B3": "#f2f2ee", "B4": "#9be36b",
        "C1": "#e6e05a", "C2": "#c9c46a", "A": "#ffffff", "usine-st": "#1f8fb8", "usine-zone": "#8a6cc4", "usine-xgb": "#c27a1e",
        "usine-toutes": "#8d8d95", "Z12": "#5ad1c8", "B3Z12": "#c8f0ff"}
CHAMPS = ("par_seance", "t", "t_apres", "pire_baisse", "survie_60", "grille_250", "net_an", "grilles_an", "periode", "annees_pos")
lignes = []
courbes_extra = {}


def ajout(ident, nom, famille, verdict, raison, m, periode="2014 - 2026", **x):
    raison = re.sub(r"(\d)\.(\d)", r"\1,\2", raison or "")
    lignes.append(dict(id=ident, nom=nom, famille=famille, verdict=verdict, raison=raison, periode_mesure=periode,
                       couleur=COUL.get(ident, "#ff8f5a" if ident.startswith("D") else "#8d8d95"),
                       **{c: (None if m.get(c) is None else float(m[c])) for c in CHAMPS}, **x))


NOMS = {"st": "Supertrend NQ", "zone": "Bot 3 en 1 (zone)", "xgb": "XGBoost NQ"}
for k in ("zone", "st", "xgb"):
    ajout(k, NOMS[k], "Bots de base", "référence", "", E1[k])
for k, u in E2["usines"].items():
    nom = {"st": "Usine Supertrend", "zone": "Usine Bot 3 en 1", "xgb": "Usine XGBoost", "toutes": "Usine globale (171 réglages)"}[k]
    raison = ("adoptée par la règle, mais l'écart avec le bot de base n'est pas significatif (t apparié 0,23) : bruit"
              if u["adoptee"] else f"hors échantillon : net {u['usine']['net_an']:,.0f} $ par an contre {u['base']['net_an']:,.0f} $ pour la référence".replace(",", " "))
    ajout(f"usine-{k}", nom + " · variantes en marche avant", "Étape 2 · variantes", "bruit" if u["adoptee"] else "tué", raison, u["usine"], "2017 - 2026")
for k in ("B1", "B2", "B3", "B4", "C1", "C2"):
    r = E3[k]; fam = "Étape 3 · B consensus et régimes" if k[0] == "B" else "Étape 3 · C nouvelles études"
    verdict = "retenu" if r.get("retenu") else "tué"
    raison = r.get("raison") or ("" if r.get("retenu") else "ne survit pas à la correction des tests multiples")
    if k == "B1":
        raison = "moins risqué que XGBoost seul, mais rapporte moins que lui et beaucoup moins que le Bot 3 en 1"
    if k == "B2":
        raison = "moins risqué que le Supertrend seul, mais 0,73 compte grillé par an : loin du Bot 3 en 1"
    if k == "B3":
        raison = "deux fois moins de comptes neufs grillés dans l'année que le Bot 3 en 1, même argent ; à confirmer sur les séances neuves"
    ajout(k, r["nom"], fam, verdict, raison, r, "2017 - 2026" if k == "B4" else "2014 - 2026")
a = E3["A"]
ajout("A", "A · gestion du capital (Bot 3 en 1, échelle de taille, coussin)", "Étape 3 · A capital", "adopté (règle)",
      "adoptée par la règle (net hors échantillon +37 %), mais le gain ne vient qu'après 2 ans : moins de retraits les deux premières années",
      dict(net_an=a["net_an"], grilles_an=a["grilles_an"]), "2017 - 2026", choix=a["choix"], reference=a["reference"])
V2 = json.load(open(R / "labo_zipline/resultats_vague2.json"))["resultats"]
for k, tr in (("Z12", TR["Z12"]), ("B3Z12", TR["B3Z12"])):
    rr, dd, nn = BT.journees(B, tr, 1, 400.0); m = BT.mesures(B, rr, dd, nn)
    if k == "Z12":
        ajout(k, "Z12 · Bot 3 en 1 sans les jours de VIX inversé", "Labo zipline · vague 2 (effets publiés)", "retenu" if V2["Z12"]["retenu"] else "tué",
              f"ne trade pas quand le VIX était au-dessus du VIX à 3 mois la veille ({V2['Z12']['seances_evitees']} séances sur 3 196) ; "
              "comptes neufs grillés dans l'année 13 % au lieu de 22 % depuis 2017, 22 % au lieu de 31 % depuis 2023", m)
    else:
        ajout(k, "B3 + Z12 · accord XGBoost et VIX normal", "Labo zipline · vague 2 (effets publiés)", "indicatif",
              "combinaison des deux pistes retenues, décidée après avoir vu leurs résultats : à confirmer sur les séances neuves", m)
    courbes_extra[k] = [round(float(x), 1) for x in np.cumsum(rr[B.test])[::5]]
V3 = json.load(open(RES / "vague3.json"))["candidats"]
rel3 = json.load(open(ARENE3 / "relief.json"))["courbes"] if ARENE3 else {}
for k, r in V3.items():
    raison = "; ".join(r["raisons"])
    if k == "V6":
        raison = ("le plus proche : mieux que le Supertrend sur le t (2,58), depuis 2023 (1,52 contre 0,53), la survie (60 % contre 46 %) "
                  "et les comptes grillés (0,95 contre 1,21 par an), mais sa pire baisse (−14 752 $) dépasse la limite écrite d'avance")
    ajout(k, r["nom"], "Vague 3 · un Supertrend en mieux", "retenu" if r["retenu"] else "tué", raison, r)
    if rel3.get(k):
        courbes_extra[k] = rel3[k]
V4 = json.load(open(RES / "vague4.json"))["candidats"]
rel4 = json.load(open(ARENE4 / "relief.json"))["courbes"] if ARENE4 else {}
for k, r in V4.items():
    raison = "; ".join(r["raisons"])
    if k == "W1":
        raison = ("le meilleur Supertrend trouvé : sur 2017 - 2026 t 3,96 (Supertrend 1,97), depuis 2023 1,99 (0,53), survie 82 % (45 %), 0,75 master grillé par an (1,25), "
                  "net 4 470 $ par an (2 756 $), solide sur 10 graines du modèle ; écarté seulement parce qu'il trade 75 % des séances au lieu de 80 %")
    ajout(k, r["nom"], "Vague 4 · le même Supertrend, en mieux", "retenu" if r["retenu"] else ("presque" if k == "W1" else "tué"), raison, r, "2017 - 2026")
    if rel4.get(k):
        courbes_extra[k] = rel4[k]
COUL.update({"W1": "#f9c74f", "W2": "#f8961e", "W3": "#f94144"})
V5 = json.load(open(RES / "vague5.json"))["tests"]
rel5 = json.load(open(ARENE5 / "relief.json"))["courbes"] if ARENE5 else {}
for k, r in V5.items():
    raison = "; ".join(r["raisons"])
    if k == "P3":
        raison = ("retenu : W1 sans la variable VIX (c'est le bot W1 NQ, en papier dans Quantower) ; version de production (variables connues "
                  "à la décision) sur 2017 - 2026 : t 3,13, survie 82 %, 0,41 master grillé par an, net 3 774 $ par an")
    if k == "P1":
        raison = "rapporte le plus (8 680 $ par an, 84 % des séances) mais grille encore 46 % des comptes neufs dans l'année : " + raison
    ajout(k, r["nom"], "Vague 5 · l'activité de W1 avec la sécurité de Z12", "retenu" if r["retenu"] else "tué", raison, r, "2017 - 2026")
    if rel5.get(k):
        courbes_extra[k] = rel5[k]
COUL.update({"P1": "#ffffff", "P2": "#e9c46a", "P3": "#f4a261"})
V6 = json.load(open(RES / "vague6.json")); rel6 = json.load(open(ARENE6 / "relief.json"))["courbes"] if ARENE6 else {}
for k, r in list(V6["tri"].items()) + list(V6["politiques"].items()):
    raison = "; ".join(r["raisons"])
    if k == "M3":
        raison = "aucun compte neuf grillé dans l'année sur 2017 - 2026, mais ne trade qu'une séance sur cinq : " + raison
    ajout(k, r["nom"], "Vague 6 · trier d'autres signaux, démarrer prudemment", "retenu" if r["retenu"] else "tué", raison, r, "2017 - 2026")
    if rel6.get(k): courbes_extra[k] = rel6[k]
V7 = json.load(open(RES / "vague7.json")); rel7 = json.load(open(ARENE7 / "relief.json"))["courbes"] if ARENE7 else {}
for k, r in V7["tests"].items():
    ajout(k, r["nom"], "Vague 7 · le modèle règle la taille de Z12", "retenu" if r["retenu"] else "tué", "; ".join(r["raisons"]), r, "2017 - 2026")
    if rel7.get(k): courbes_extra[k] = rel7[k]
V8 = json.load(open(RES / "vague8.json")); rel8 = json.load(open(ARENE8 / "relief.json"))["courbes"] if ARENE8 else {}
for k, r in V8["tests"].items():
    raison = "; ".join(r["raisons"])
    if k == "F1":
        raison = ("deux fois moins de comptes neufs grillés dans l'année que Z12 (7 % contre 16 %), 0,02 master grillé par an, t 4,56 ; "
                  "écarté de peu parce qu'il rapporte 6 % de moins (3 088 $ contre 3 279 $). C'est déjà la règle de ton vrai bot (pas de zone les jours de la Fed)")
    ajout(k, r["nom"], "Vague 8 · journées sans Z12, filtres de journée", "presque" if k == "F1" else ("retenu" if r["retenu"] else "tué"), raison, r, "2014 - 2026")
    if rel8.get(k): courbes_extra[k] = rel8[k]
COUL.update({"R1": "#b5e48c", "R2": "#99d98c", "R3": "#76c893", "F1": "#48cae4", "F2": "#0096c7", "F3": "#0077b6", "F4": "#023e8a"})
COUL.update({"M1": "#ffd166", "M2": "#ffa028", "M3": "#90e0ef", "L1": "#ffffff", "L2": "#e0e0e0", "L3": "#e9c46a", "L4": "#d4a373",
             "S1": "#ffffff", "S2": "#f9c74f", "S3": "#90e0ef"})
COUL.update({"V1": "#ffd166", "V2": "#f4a261", "V3": "#e76f51", "V4": "#b5e48c", "V5": "#90e0ef", "V6": "#48cae4", "V7": "#00b4d8"})
for L_ in lignes:
    if L_["id"] in COUL:
        L_["couleur"] = COUL[L_["id"]]
d = E3["D"]
ajout("D", "D · portefeuille Supertrend 7 marchés", "Étape 3 · D autres marchés", "tué",
      f"t {d['t']:.2f}, Sharpe {d['sharpe']:.2f} contre {d['sharpe_nq']:.2f} pour le NQ seul".replace(".", ","), dict(t=d["t"]), "2016 - 2026")
marches = [dict(id=k[2:], par_seance=E3[k]["par_seance"], t=E3[k]["t"], t_1619=E3[k]["t_1619"], t_2022=E3[k]["t_2022"], t_2326=E3[k]["t_2326"])
           for k in E3 if k.startswith("D-")]

courbes = {k: relief["courbes"][k] for k in relief["courbes"] if relief["courbes"][k]}
courbes.update(courbes_extra)
# Z12 dans la station (F0) : VIX et VIX a 3 mois de la veille pour les seances du 11 aout au 2 nov., et Z12 / Bot 3 en 1
# de 1 a 5 MNQ sur 2014 - 2026 (ml/arene/z12_tailles.py)
ZT = json.load(open(R / "ml/arene/resultats/z12_tailles.json"))
station_z12 = dict(vix={j: [a, b, c] for j, a, b, c in zip(ZT["periode"]["jours"], ZT["periode"]["vix"], ZT["periode"]["vix3m"], ZT["periode"]["inverse"])},
                   tailles={k: {tt: {c: x for c, x in e.items() if c not in ("jours_periode", "trades_periode")} for tt, e in v.items()} for k, v in ZT["tailles"].items()},
                   arene_periode={k: v["1"]["periode"] for k, v in ZT["tailles"].items()})
# W1 (bot en papier) dans la station : decisions hors echantillon pour 2026 (modele appris sur 2011 - 2025, variables de production)
import w1 as W1m  # noqa: E402
STw = sorted(BT.supertrend(B), key=lambda x_: (x_[0], x_[2]))
Xw, yw, anw = W1m.variables_prod(B, STw)
pw = W1m.probas(Xw, yw, anw, annees=[2026]); seuil26 = float(yw[anw < 2026].mean())
signaux_w1 = {}
for t_, pp in zip(STw, pw):
    jj = B.J[t_[0]]
    if jj >= "2026-08-11" and np.isfinite(pp):
        signaux_w1.setdefault(jj, []).append([int(t_[2]), round(float(pp), 3), bool(pp > seuil26)])
WP = json.load(open(R / "ml/arene/resultats/w1_prod.json"))
station_w1 = dict(signaux=signaux_w1, seuil=seuil26, diagnostic=WP["diagnostic"])
print("W1 station :", sum(len(v) for v in signaux_w1.values()), "signaux,", sum(x[2] for v in signaux_w1.values() for x in v), "gardés, seuil", round(seuil26, 3))
D3 = dict(station_z12=station_z12, station_w1=station_w1, jours=jours, jours_courbes=relief["jours"], courbes=courbes, lignes=lignes, rejeu=rejeu, diag=diag, marches=marches,
          choix_A={str(k): v for k, v in CHOIX_A.items()}, debut_2017=d17,
          noms_rejeu={"zone": "Bot 3 en 1 (zone)", "B3": "B3 · Bot 3 en 1 + accord XGBoost", "xgb": "XGBoost NQ", "st": "Supertrend NQ",
                      "B1": "B1 · XGBoost + accord Supertrend", "B2": "B2 · Supertrend + accord XGBoost",
                      "Z12": "Z12 · Bot 3 en 1 sans VIX inversé", "B3Z12": "B3 + Z12 (indicatif)"})
(S / "terminal").mkdir(exist_ok=True)
json.dump(D3, open(S / "terminal/donnees3.json", "w"), separators=(",", ":"), allow_nan=False)
print("donnees3.json", round(os.path.getsize(S / "terminal/donnees3.json") / 1e3), "ko")
