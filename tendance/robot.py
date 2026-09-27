#!/usr/bin/env python3
"""Robot de tendance multi-marches en ARGENT VIRTUEL.

Chaque soir de semaine (apres la cloture americaine), via GitHub Actions :
1. telecharge les prix du jour (Yahoo) ;
2. valorise le compte virtuel avec les positions tenues ;
3. le vendredi, recalcule les positions (systeme de tendance 19 marches, contrats micro CME
   entiers optimises pour la taille du compte) et note les ordres a passer ;
4. envoie le resume sur Telegram et sauvegarde l'etat dans tendance/robot/ ;
5. met a jour le tableau de bord tendance/robot/TABLEAU_DE_BORD.md (lisible sur GitHub).

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
SHARPE_HISTORIQUE = 0.56    # resultat du systeme sur les vrais prix 2007-2026 (voir rapport.py)
TABLEAU = DOSSIER / "TABLEAU_DE_BORD.md"
COURBE = DOSSIER / "courbe.svg"


def zone_normale(semaines):
    """Gain attendu ($) et zone ou tombent 8 resultats sur 10, d'apres l'historique."""
    risque_an = VOL_VISEE * CAPITAL_DEPART
    moyen = SHARPE_HISTORIQUE * risque_an * semaines / 52
    ecart = 1.2816 * risque_an * np.sqrt(np.maximum(semaines, 0) / 52)
    return moyen, moyen - ecart, moyen + ecart


def dessiner_courbe(journal):
    """Graphique SVG : gain reel du compte virtuel dans la zone des resultats normaux."""
    j = journal.copy()
    j["date"] = pd.to_datetime(j["date"])
    sem = ((j["date"] - j["date"].iloc[0]).dt.days / 7).values
    gain = (j["solde"] - CAPITAL_DEPART).values
    horizon = max(26.0, np.ceil((sem.max() + 4) / 13) * 13)
    x_sem = np.linspace(0, horizon, 80)
    moy, bas, haut = zone_normale(x_sem)
    ymin = min(bas.min(), gain.min()) * 1.08
    ymax = max(haut.max(), gain.max()) * 1.08
    L, H, g, d, h, b = 760, 340, 64, 20, 20, 44
    X = lambda s: g + (L - g - d) * s / horizon
    Y = lambda v: h + (H - h - b) * (ymax - v) / (ymax - ymin)
    pas = 2000 if ymax - ymin < 16000 else 5000
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L} {H}" width="{L}" height="{H}" '
           'font-family="-apple-system,Segoe UI,sans-serif" font-size="12">',
           f'<rect width="{L}" height="{H}" fill="#fcfcfb"/>']
    for v in np.arange(np.ceil(ymin / pas) * pas, ymax, pas):
        out.append(f'<line x1="{g}" x2="{L - d}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{"#c3c2b7" if v == 0 else "#e1e0d9"}"/>')
        out.append(f'<text x="{g - 8}" y="{Y(v) + 4:.1f}" text-anchor="end" fill="#52514e">{v:+,.0f} $</text>')
    for s in np.arange(0, horizon + 0.1, 13):
        out.append(f'<text x="{X(s):.1f}" y="{H - b + 18}" text-anchor="middle" fill="#52514e">{s:.0f} sem.</text>')
    zone = " ".join(f"{X(a):.1f},{Y(v):.1f}" for a, v in zip(x_sem, haut)) + " " + \
        " ".join(f"{X(a):.1f},{Y(v):.1f}" for a, v in zip(x_sem[::-1], bas[::-1]))
    out.append(f'<polygon points="{zone}" fill="#2a78d6" fill-opacity="0.10"/>')
    out.append('<polyline fill="none" stroke="#898781" stroke-width="1.5" points="'
               + " ".join(f"{X(a):.1f},{Y(v):.1f}" for a, v in zip(x_sem, moy)) + '"/>')
    out.append('<polyline fill="none" stroke="#2a78d6" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" points="'
               + " ".join(f"{X(a):.1f},{Y(v):.1f}" for a, v in zip(sem, gain)) + '"/>')
    out.append(f'<circle cx="{X(sem[-1]):.1f}" cy="{Y(gain[-1]):.1f}" r="4.5" fill="#2a78d6" stroke="#fcfcfb" stroke-width="2"/>')
    out.append(f'<text x="{X(horizon) - 4:.1f}" y="{Y(haut[-1]) - 6:.1f}" text-anchor="end" fill="#52514e">zone normale (8 cas sur 10)</text>')
    out.append(f'<text x="{X(horizon) - 4:.1f}" y="{Y(moy[-1]) - 6:.1f}" text-anchor="end" fill="#52514e">gain moyen attendu</text>')
    out.append("</svg>")
    return "\n".join(out)


def ecrire_tableau(etat, journal):
    """Tableau de bord Markdown mis a jour a chaque lancement (GitHub l'affiche directement)."""
    j = journal.copy()
    semaines = (pd.Timestamp(etat["derniere_date"]) - pd.Timestamp(etat["debut"])).days / 7
    gain = etat["solde"] - CAPITAL_DEPART
    moy, bas, haut = zone_normale(semaines)
    if semaines < 1:
        verdict = "⚪ Trop tot pour juger : le robot vient de demarrer."
    elif gain < bas:
        verdict = "🔴 En dessous de la zone normale : resultat pire que 9 cas sur 10 de l'historique. A surveiller."
    elif gain > haut:
        verdict = "🟢 Au-dessus de la zone normale : meilleur que 9 cas sur 10 de l'historique (la chance y est pour beaucoup)."
    else:
        verdict = "🟡 Dans la zone normale : le robot se comporte comme sur les 20 ans d'historique."
    ph = etat["phidias"]
    if ph["etat"] == "en cours":
        marge = etat["solde"] - (ph["plus_haut"] - PERTE_MAX_PHIDIAS)
        phidias = f"en cours : {gain:+,.0f} $ sur +4 000 $, marge restante {marge:,.0f} $"
    else:
        phidias = f"{ph['etat']} le {ph['date']}"
    positions = [f"| {micro(k)} | {k} | {ordre(k, v, ('Achat', 'Vente')).split()[0]} | {abs(v):.0f} |"
                 for k, v in sorted(etat["positions"].items(), key=lambda x: -abs(x[1]))]
    derniers = j.tail(10).iloc[::-1]
    lignes = [f"| {r.date} | {r.gain:+,.0f} $ | {r.solde:,.0f} $ |" for r in derniers.itertuples()]
    md = [
        "# Robot de tendance : tableau de bord (argent virtuel)",
        "",
        f"Mis a jour le **{etat['derniere_date']}** (demarre le {etat['debut']}). Aucun argent reel n'est engage.",
        "",
        f"**{verdict}**",
        "",
        "| Mesure | Valeur |",
        "|---|---|",
        f"| Solde virtuel | **{etat['solde']:,.0f} $** (depart 50 000 $) |",
        f"| Gain depuis le depart | {gain:+,.0f} $ ({gain / CAPITAL_DEPART:+.1%}) |",
        f"| Baisse depuis le plus haut | {etat['solde'] / etat['plus_haut'] - 1:.1%} |",
        f"| Zone normale a ce stade (8 cas sur 10) | de {bas:+,.0f} $ a {haut:+,.0f} $ (moyenne {moy:+,.0f} $) |",
        f"| Challenge Phidias 50K virtuel | {phidias} |",
        "",
        "![Gain du compte virtuel et zone normale](courbe.svg)",
        "",
        "La zone bleue montre ou tombaient 8 resultats sur 10 dans l'historique 2007-2026, au meme risque "
        "(12 %/an, soit environ 6 000 $ sur 50 000 $). Tant que la ligne reste dedans, le robot se comporte comme prevu. "
        "Des semaines negatives sont normales : il faut plusieurs mois pour juger.",
        "",
        "## Positions tenues",
        "",
        "| Contrat | Marche | Sens | Nombre |",
        "|---|---|---|---|",
        *(positions or ["| - | aucune position | - | - |"]),
        "",
        "Contrats de taux (2YY, 10Y, 30Y) : le sens indique est celui de l'ordre sur le contrat, "
        "inverse de celui des obligations.",
        "",
        "## 10 derniers jours",
        "",
        "| Date | Resultat du jour | Solde |",
        "|---|---|---|",
        *lignes,
        "",
        "Journal complet : [journal.csv](journal.csv). Methode et resultats historiques : [../README.md](../README.md).",
    ]
    TABLEAU.write_text("\n".join(md) + "\n")
    COURBE.write_text(dessiner_courbe(j))


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
        if JOURNAL.exists():
            ecrire_tableau(etat, pd.read_csv(JOURNAL))
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
    ecrire_tableau(etat, pd.read_csv(JOURNAL))

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
