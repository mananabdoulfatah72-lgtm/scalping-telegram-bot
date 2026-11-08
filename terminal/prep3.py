#!/usr/bin/env python3
"""Donnees de la vue ARENE du terminal (F9) : classement des bots, des variantes et des quatre pistes de l'arene
(ml/arene/resultats/etape1-3.json), courbes, resultats par seance pour rejouer le compte finance dans la page, et le
diagnostic des premieres annees (pas une regle : il sert a lire les pistes retenues).
Lancer depuis n'importe ou : MINUTES_NQ=... CACHE_DOSSIER=... python3 terminal/prep3.py <dossier de l'arene>"""
import json
import os
import re
import sys
from pathlib import Path

import numpy as np

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "ml/arene")); sys.path.insert(0, str(R / "ml"))
import bots as BT  # noqa: E402

S = Path("/tmp/claude-0/-home-user-scalping-telegram-bot/73d2fc28-0760-5668-987b-2a927564efe7/scratchpad")
ARENE = Path(sys.argv[1]) if len(sys.argv) > 1 else S / "arene"
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
TR = {
    "zone": zt, "xgb": xt, "st": st,
    "B3": [t for t in zt if sensp(BT.bougie_avant(t[0], t[2])) == t[1]],
    "B2": [t for t in st if sensp(BT.bougie_avant(t[0], t[2])) == t[1]],
    "B1": BT.xgboost(B, filtre=lambda i: F[i, 18] == (1 if B.p[i] > 0.5 else -1)),
}
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
       "xgb": (*tab("xgb"), un, un, g26), "st": (*tab("st"), un, un, g26)}
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
        "usine-toutes": "#8d8d95"}
CHAMPS = ("par_seance", "t", "t_apres", "pire_baisse", "survie_60", "grille_250", "net_an", "grilles_an", "periode", "annees_pos")
lignes = []


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
d = E3["D"]
ajout("D", "D · portefeuille Supertrend 7 marchés", "Étape 3 · D autres marchés", "tué",
      f"t {d['t']:.2f}, Sharpe {d['sharpe']:.2f} contre {d['sharpe_nq']:.2f} pour le NQ seul".replace(".", ","), dict(t=d["t"]), "2016 - 2026")
marches = [dict(id=k[2:], par_seance=E3[k]["par_seance"], t=E3[k]["t"], t_1619=E3[k]["t_1619"], t_2022=E3[k]["t_2022"], t_2326=E3[k]["t_2326"])
           for k in E3 if k.startswith("D-")]

courbes = {k: relief["courbes"][k] for k in relief["courbes"] if relief["courbes"][k]}
D3 = dict(jours=jours, jours_courbes=relief["jours"], courbes=courbes, lignes=lignes, rejeu=rejeu, diag=diag, marches=marches,
          choix_A={str(k): v for k, v in CHOIX_A.items()}, debut_2017=d17,
          noms_rejeu={"zone": "Bot 3 en 1 (zone)", "B3": "B3 · Bot 3 en 1 + accord XGBoost", "xgb": "XGBoost NQ", "st": "Supertrend NQ",
                      "B1": "B1 · XGBoost + accord Supertrend", "B2": "B2 · Supertrend + accord XGBoost"})
(S / "terminal").mkdir(exist_ok=True)
json.dump(D3, open(S / "terminal/donnees3.json", "w"), separators=(",", ":"), allow_nan=False)
print("donnees3.json", round(os.path.getsize(S / "terminal/donnees3.json") / 1e3), "ko")
