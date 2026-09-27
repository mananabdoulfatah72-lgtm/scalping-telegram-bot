#!/usr/bin/env python3
"""Robot de tendance multi-marches en ARGENT VIRTUEL.

Chaque soir de semaine (apres la cloture americaine), via GitHub Actions :
1. telecharge les prix du jour (Yahoo) ;
2. valorise le compte virtuel avec les positions tenues ;
3. le vendredi, recalcule les positions (systeme de tendance 19 marches, contrats micro CME
   entiers optimises pour la taille du compte) et note les ordres a passer ;
4. envoie le resume sur Telegram et sauvegarde l'etat dans tendance/robot/.

Aucun ordre reel n'est passe : aucune cle d'echange n'est necessaire.
Test hors ligne : ROBOT_DONNEES_LOCALES=1 ROBOT_JUSQU_AU=2026-06-30 python3 tendance/robot.py
"""
import json
import os
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import requests

import systeme as S

DOSSIER = Path(os.getenv("ROBOT_DOSSIER", Path(__file__).parent / "robot"))
ETAT = DOSSIER / "etat.json"
JOURNAL = DOSSIER / "journal.csv"
CAPITAL_DEPART = 50_000.0
VOL_VISEE = 0.12            # risque vise : 12 % par an, soit environ 6 000 $ sur 50 000 $
FRAIS = 3.25                # $ par contrat et par ordre (frais + glissement)
OBJECTIF_PHIDIAS, PERTE_MAX_PHIDIAS = 4_000, 2_500


def telecharger(annees=6):
    """Prix de cloture (bruts et ajustes) des ~6 dernieres annees, depuis Yahoo."""
    import yfinance as yf
    tickers = sorted({m.source for m in S.MARCHES} | {m.futures for m in S.MARCHES if m.futures}
                     | {"SPY", "^IRX"})
    debut = (date.today() - timedelta(days=365 * annees)).isoformat()
    df = yf.download(tickers, start=debut, auto_adjust=False, progress=False, threads=True)
    close, adj = df["Close"].copy(), df["Adj Close"].copy()
    manquants = [t for t in tickers if t not in close or close[t].dropna().empty]
    if manquants:
        raise SystemExit(f"Donnees manquantes pour : {', '.join(manquants)}")
    return close, adj


def charger_prix():
    if os.getenv("ROBOT_DONNEES_LOCALES"):
        close, adj = S.charger()
        fin = os.getenv("ROBOT_JUSQU_AU")
        if fin:
            close, adj = close[close.index <= fin], adj[adj.index <= fin]
        return close, adj
    return telecharger()


def lire_etat():
    if ETAT.exists():
        return json.loads(ETAT.read_text())
    return {"debut": None, "derniere_date": None, "solde": CAPITAL_DEPART, "plus_haut": CAPITAL_DEPART,
            "positions": {}, "phidias": {"etat": "en cours", "plus_haut": CAPITAL_DEPART, "date": None}}


def ecrire(etat, lignes):
    DOSSIER.mkdir(parents=True, exist_ok=True)
    ETAT.write_text(json.dumps(etat, indent=2, ensure_ascii=False))
    if lignes:
        nouveau = pd.DataFrame(lignes)
        if JOURNAL.exists():
            nouveau = pd.concat([pd.read_csv(JOURNAL), nouveau])
        nouveau.to_csv(JOURNAL, index=False)


def telegram(message):
    jeton, chat = os.getenv("TELEGRAM_TOKEN"), os.getenv("CHAT_ID")
    print(message)
    if not jeton or not chat:
        print("(Telegram non configure : secrets TELEGRAM_TOKEN / CHAT_ID absents)")
        return
    try:
        rep = requests.post(f"https://api.telegram.org/bot{jeton}/sendMessage",
                            data={"chat_id": chat, "text": message}, timeout=20)
        if not rep.ok:
            print(f"Erreur Telegram {rep.status_code} : {rep.text[:200]}")
    except requests.RequestException as e:
        print(f"Erreur Telegram : {e}")


TAUX = {"2YY", "10Y", "30Y"}   # contrats cotes en taux : ils montent quand les obligations baissent


def micro(nom):
    return next(m.micro for m in S.MARCHES if m.nom == nom)


def ordre(nom, n, verbes=("Acheter", "Vendre")):
    """Texte d'un ordre sur le contrat micro reel (sens inverse pour les contrats de taux)."""
    c = micro(nom)
    sens = -n if c in TAUX else n
    note = " (contrat de taux : sens inverse des obligations)" if c in TAUX else ""
    return f"  {verbes[0] if sens > 0 else verbes[1]} {abs(n):.0f} {c} ({nom}){note}"


def decrire_positions(positions):
    lignes = [ordre(nom, n, ("Achat", "Vente")) for nom, n in sorted(positions.items(), key=lambda x: -abs(x[1])) if n]
    return "\n".join(lignes) if lignes else "  aucune position"


def main():
    close, adj = charger_prix()
    r = S.rendements_futures(close, adj)
    _, pos, _ = S.backtest(r)
    cv = S.valeur_contrat(close).reindex(r.index).ffill()
    etat = lire_etat()

    derniere = pd.Timestamp(etat["derniere_date"]) if etat["derniere_date"] else None
    jours = r.index[r.index > derniere] if derniere is not None else r.index[-1:]
    if len(jours) == 0:
        print("Pas de nouvelle journee de bourse : rien a faire.")
        return
    premier_lancement = etat["debut"] is None
    if premier_lancement:
        etat["debut"] = str(jours[0].date())

    lignes, ordres_semaine, gain_total = [], None, 0.0
    for d in jours:
        i = r.index.get_loc(d)
        n = pd.Series(etat["positions"], dtype=float).reindex(r.columns).fillna(0)
        # 1. gain ou perte du jour avec les positions de la veille
        gain = 0.0
        if derniere is not None:
            gain = float((n * cv.iloc[i - 1] * r.iloc[i].fillna(0)).sum())
        etat["solde"] += gain
        gain_total += gain
        # 2. vendredi (ou premier jour) : nouvelles positions
        ordres = {}
        if d.dayofweek == 4 or not etat["positions"]:
            cible = S.contrats_optimises(r.iloc[:i + 1], pos.iloc[:i + 1], cv.iloc[i], etat["solde"],
                                         VOL_VISEE, (1.0,), np.array([i]))[1.0].iloc[0]
            ordres = {k: float(v) for k, v in (cible - n).items() if v}
            etat["solde"] -= FRAIS * sum(abs(v) for v in ordres.values())
            etat["positions"] = {k: float(v) for k, v in cible.items() if v}
            ordres_semaine = ordres
        etat["plus_haut"] = max(etat["plus_haut"], etat["solde"])
        # 3. suivi d'un challenge Phidias Premium 50K virtuel
        ph = etat["phidias"]
        if ph["etat"] == "en cours":
            ph["plus_haut"] = max(ph["plus_haut"], etat["solde"])
            if etat["solde"] >= CAPITAL_DEPART + OBJECTIF_PHIDIAS:
                ph["etat"], ph["date"] = "reussi", str(d.date())
            elif etat["solde"] <= ph["plus_haut"] - PERTE_MAX_PHIDIAS:
                ph["etat"], ph["date"] = "perdu", str(d.date())
        lignes.append({"date": str(d.date()), "gain": round(gain, 2), "solde": round(etat["solde"], 2),
                       "ordres": json.dumps(ordres, ensure_ascii=False), "nb_positions": len(etat["positions"])})
        etat["derniere_date"] = str(d.date())
        derniere = d

    ecrire(etat, lignes)

    perf = etat["solde"] / CAPITAL_DEPART - 1
    baisse = etat["solde"] / etat["plus_haut"] - 1
    ph = etat["phidias"]
    if ph["etat"] == "en cours":
        marge = etat["solde"] - (ph["plus_haut"] - PERTE_MAX_PHIDIAS)
        suivi = (f"Challenge Phidias 50K virtuel : {etat['solde'] - CAPITAL_DEPART:+,.0f} $ sur +4 000 $, "
                 f"marge restante {marge:,.0f} $")
    else:
        suivi = f"Challenge Phidias 50K virtuel : {ph['etat'].upper()} le {ph['date']}"
    msg = []
    if premier_lancement:
        msg += ["🚀 Demarrage du robot de tendance en ARGENT VIRTUEL (aucun argent reel).",
                "Compte virtuel de 50 000 $, 19 marches futures (contrats micro CME), ordres chaque vendredi soir.",
                "Sur les vrais prix 2007-2026 : Sharpe 0,56, environ +11 %/an pour 20 % de risque,",
                "pire baisse -36 %, 1 annee sur 3 negative. Attends-toi a des semaines perdantes.", ""]
    msg += [f"🤖 Robot tendance (ARGENT VIRTUEL) - {etat['derniere_date']}",
           f"Resultat : {gain_total:+,.0f} $ | solde {etat['solde']:,.0f} $ ({perf:+.1%} depuis le {etat['debut']})",
           f"Baisse depuis le plus haut : {baisse:.1%}", suivi]
    if ordres_semaine is not None:
        msg += ["", "📋 Ordres de la semaine :"]
        msg += [ordre(k, v) for k, v in ordres_semaine.items()] or ["  aucun changement"]
        msg += ["", "Positions tenues :", decrire_positions(etat["positions"])]
    telegram("\n".join(msg))


if __name__ == "__main__":
    main()
