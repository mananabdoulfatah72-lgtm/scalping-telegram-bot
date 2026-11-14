"""Chaque bot du depot, rejoue du 13 octobre 2026 (1re seance du challenge Bulenox 50K) au 13 novembre 2026, puis passe
dans les regles du challenge : objectif +3 000 $, perte max suivie 2 500 $ en fin de journee (plancher bloque a 50 100 $),
echec des que le compte touche le plancher pendant la seance (audit/risque.py). Frais 3 $ par MNQ, limite du jour 1 000 $
a 4 MNQ (reglage du bot), 1 point de glissement a la sortie forcee."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

S = Path(__file__).parent
sys.path.insert(0, os.environ.get("CHANTIER", str(S / "lm/chantier")))   # chantier/ de claude/loving-mccarthy-u21aw6
import rejeu_periode as RP  # noqa: E402

DEBUT, FIN, EXPIRE = "2026-10-13", "2026-11-13", "2026-11-11"   # 30 jours calendaires depuis l'achat (12-13 oct)
RP.FIN = FIN
FRAIS, GLISSE, LIMITE = 3.0, 1.0, 1000.0
O = S / "rejeu"
MAIN = S.parent
Mn = RP.minutes(MAIN / "zone/robot/nq_1min.csv.gz")
JOURS = sorted(j for j in Mn if DEBUT <= j <= FIN)


def chemins(tr, k=1.0, limite=None):
    """Par seance : (resultat, pire moment realise + latent). Limite du jour coupee sur les plus bas / hauts des minutes."""
    out = {}
    for j in JOURS:
        real, pire, arret = 0.0, 0.0, False
        for _, s, a, b, e, x in [t for t in tr if t[0] == j]:
            if arret:
                break
            _, H, L = Mn[j]
            for m in range(a, b + 1):
                lat = real + s * ((L[m] if s > 0 else H[m]) - e) * 2 * k - FRAIS * k
                pire = min(pire, lat)
                if limite is not None and lat <= -limite:
                    real = -limite - GLISSE * 2 * k - FRAIS * k; arret = True; pire = min(pire, real)
                    break
            if arret:
                break
            real += s * (x - e) * 2 * k - FRAIS * k
            pire = min(pire, real)
        out[j] = (real, pire)
    return out


def challenge(jours):
    """jours : {date: (resultat, pire du jour)}. Renvoie (issue, date, solde final, plus bas du solde)."""
    solde, haut, bas = 50000.0, 50000.0, 50000.0
    for j in JOURS:
        g, p = jours.get(j, (0.0, 0.0))
        plancher = min(haut - 2500, 50100)
        bas = min(bas, solde + p)
        if solde + p <= plancher:
            return "PERDU", j, solde + p, bas
        solde += g
        if solde >= 53000:
            return "VALIDE", j, solde, bas
        haut = max(haut, solde)
    return "en cours", JOURS[-1], solde, bas


def ligne(nom, jours, notes=""):
    tot = sum(g for g, _ in jours.values())
    pire = min((g for g, _ in jours.values()), default=0.0)
    issue, date, solde, bas = challenge(jours)
    if issue == "VALIDE" and date > EXPIRE:
        issue = "VALIDE hors delai"
    return dict(bot=nom, total=round(tot), pire_jour=round(pire), challenge=issue, le=date, solde=round(solde), notes=notes)


R = []
BOT = [("actuel_sans_delta", "Bot 3 en 1 - reglages actuels (zone + C2 + Q1)"), ("origine_sans_delta", "Bot 3 en 1 - zone d'origine"),
       ("regle_26oct", "Bot 3 en 1 - regle du 26 oct"), ("regle_27oct", "Bot 3 en 1 - regle du 27 oct (stop 70)")]
for cle, nom in BOT:
    tr, rsi = RP.trades_bot(O / f"bot_{cle}.txt")
    tr = [t for t in tr if DEBUT <= t[0] <= FIN]
    R.append(ligne(nom + " 1 MNQ", chemins(tr), f"{len(tr)} trades"))
    R.append(ligne(nom + " 4 MNQ", chemins(tr, 4.0, LIMITE), f"{len(tr)} trades"))
    if cle == "actuel_sans_delta":
        g, ouv = [], None
        for j, s, px in rsi:
            if s == "achat":
                ouv = (j, px)
            elif ouv:
                g.append((j, (px - ouv[1]) * 2 - FRAIS)); ouv = None
        rsi_j = {j: (x, min(0.0, x)) for j, x in g if DEBUT <= j <= FIN}
        R.append(ligne("RSI(2) du bot (nuit) 1 MNQ", rsi_j, f"{len(rsi_j)} trades, tenu la nuit : interdit chez Bulenox"))
for cle, nom in (("supertrend", "Supertrend NQ 10-3"), ("W1", "W1 (Supertrend + modele)"), ("XGBoost", "XGBoost NQ")):
    tr = [t for t in RP.trades_csv(O / f"{cle}_trades.csv") if DEBUT <= t[0] <= FIN]
    R.append(ligne(nom + " 1 MNQ", chemins(tr), f"{len(tr)} trades"))
    R.append(ligne(nom + " 4 MNQ", chemins(tr, 4.0, LIMITE), f"{len(tr)} trades"))

# machine de veille : resultat du jour seulement (pas de chemin dans la seance), converti au prix du jour
v = pd.read_csv(O / "veille_journal.csv").dropna()
v = v[(v.jour >= DEBUT) & (v.jour <= FIN)]
NOMS = {"H1": "ORB 5 minutes", "H5": "Cassure de la veille", "F3": "Pivots R1/S1", "S2b": "S2b cassure ratee",
        "R1": "Radar achat 13 h 30", "R2": "Radar achat 13 h", "L2": "L2 contre-mouvement 15 h 30", "W1i": "W1i lundi bitcoin"}
for k, nom in NOMS.items():
    x = v[v.strategie == k]
    for t in (1, 4):
        jj = {}
        for j, g in zip(x.jour, x.gain_dollars_par_mnq):
            if j in Mn:
                r = ((g + FRAIS) * Mn[j][0][0] / 30900.0 - FRAIS) * t
                r = max(r, -LIMITE - 5 * t) if t == 4 else r
                jj[j] = (r, min(0.0, r))
        R.append(ligne(f"{nom} {t} MNQ", jj, f"{len(jj)} seances, fin de journee seulement"))

# robots de main : leur journal du jour (fin de journee)
for f, col, nom, note in (("zone/robot/journal.csv", "gain_1_mnq", "Robot zone (main) 1 MNQ", ""),
                          ("zone/robot/journal.csv", "gain_rebond_1_mnq", "Robot zone : rebond 1 MNQ", ""),
                          ("zone/robot/journal.csv", "gain_rsi2_1_mnq", "Robot zone : RSI(2) 1 MNQ", "tenu la nuit"),
                          ("zone/robot/journal.csv", "gain", "Robot zone : son compte challenge", "zone + RSI(2) + rebond"),
                          ("tendance/robot/journal.csv", "gain", "Tendance seule (19 marches)", "garde la nuit : interdit chez Bulenox"),
                          ("tendance/robot/journal_melange.csv", "gain", "Melange tendance + achat", "garde la nuit : interdit chez Bulenox"),
                          ("version7/robot/journal.csv", "gain", "Version 7 (5 actions tech)", "actions, pas des futures")):
    d = pd.read_csv(MAIN / f)
    d = d[(d.date >= DEBUT) & (d.date <= FIN)]
    R.append(ligne(nom, {j: (g, min(0.0, g)) for j, g in zip(d.date, d[col].astype(float))}, note))

t = pd.DataFrame(R).sort_values("total", ascending=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)
print(f"Seances : {JOURS[0]} -> {JOURS[-1]} ({len(JOURS)}) ; NQ {Mn[JOURS[0]][0][0]:.0f} -> {Mn[JOURS[-1]][0][-1]:.0f}")
print(t.to_string(index=False))
t.to_csv(S / "bilan_challenge.csv", index=False)
