#!/usr/bin/env python3
"""Robot multi-marches en ARGENT VIRTUEL : deux comptes de 50 000 $ suivis cote a cote.

- "melange" (compte principal) : 50/50 tendance + achat permanent, meme risque dans chacun ;
- "tendance" : suivi de tendance seul (le premier robot).

Chaque soir de semaine (apres la cloture americaine), via GitHub Actions :
1. telecharge les prix du jour (Yahoo) ;
2. valorise chaque compte virtuel avec les positions tenues ;
3. le vendredi, recalcule les positions (19 marches, contrats micro CME entiers optimises pour
   la taille du compte) et note les ordres a passer ;
4. envoie le resume sur Telegram, sauvegarde l'etat dans tendance/robot/ et met a jour le
   tableau de bord tendance/robot/TABLEAU_DE_BORD.md (lisible sur GitHub).

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
TABLEAU = DOSSIER / "TABLEAU_DE_BORD.md"
CAPITAL_DEPART = 50_000.0
VOL_VISEE = 0.12            # risque vise : 12 % par an, soit environ 6 000 $ sur 50 000 $
FRAIS = 3.25                # $ par contrat et par ordre (frais + glissement)
OBJECTIF_PHIDIAS, PERTE_MAX_PHIDIAS = 4_000, 2_500

# Resultats sur les vrais prix 2007-2026 (voir rapport.py), au risque de 12 %/an
COMPTES = {
    "melange": {"nom": "Melange 50/50 (tendance + achat permanent)", "sharpe": 0.78,
                "journal": "journal_melange.csv", "courbe": "courbe_melange.svg",
                "historique": "Sharpe 0,78, environ +9 %/an en moyenne, pire baisse -19 %, 3 annees sur 4 positives"},
    "tendance": {"nom": "Tendance seule", "sharpe": 0.56,
                 "journal": "journal.csv", "courbe": "courbe.svg",
                 "historique": "Sharpe 0,56, environ +7 %/an en moyenne, pire baisse -23 %, 13 annees sur 20 positives"},
}


def nouveau_compte():
    return {"debut": None, "derniere_date": None, "solde": CAPITAL_DEPART, "plus_haut": CAPITAL_DEPART,
            "positions": {}, "phidias": {"etat": "en cours", "plus_haut": CAPITAL_DEPART, "date": None}}


def lire_etat():
    etat = json.loads(ETAT.read_text()) if ETAT.exists() else {}
    if "comptes" not in etat:                       # ancien format : un seul compte (tendance)
        etat = {"comptes": {"tendance": etat}} if etat else {"comptes": {}}
    for cle in COMPTES:
        etat["comptes"].setdefault(cle, nouveau_compte())
    return etat


def zone_normale(semaines, sharpe):
    """Gain attendu ($) et zone ou tombent 8 resultats sur 10, d'apres l'historique."""
    risque_an = VOL_VISEE * CAPITAL_DEPART
    moyen = sharpe * risque_an * semaines / 52
    ecart = 1.2816 * risque_an * np.sqrt(np.maximum(semaines, 0) / 52)
    return moyen, moyen - ecart, moyen + ecart


def dessiner_courbe(journal, sharpe):
    """Graphique SVG : gain reel du compte virtuel dans la zone des resultats normaux."""
    j = journal.copy()
    j["date"] = pd.to_datetime(j["date"])
    sem = ((j["date"] - j["date"].iloc[0]).dt.days / 7).values
    gain = (j["solde"] - CAPITAL_DEPART).values
    horizon = max(26.0, np.ceil((sem.max() + 4) / 13) * 13)
    x_sem = np.linspace(0, horizon, 80)
    moy, bas, haut = zone_normale(x_sem, sharpe)
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


def verdict(compte, sharpe):
    semaines = (pd.Timestamp(compte["derniere_date"]) - pd.Timestamp(compte["debut"])).days / 7
    gain = compte["solde"] - CAPITAL_DEPART
    moy, bas, haut = zone_normale(semaines, sharpe)
    if semaines < 1:
        texte = "⚪ Trop tot pour juger : le compte vient de demarrer."
    elif gain < bas:
        texte = "🔴 En dessous de la zone normale : pire que 9 cas sur 10 de l'historique. A surveiller."
    elif gain > haut:
        texte = "🟢 Au-dessus de la zone normale : mieux que 9 cas sur 10 de l'historique (la chance y est pour beaucoup)."
    else:
        texte = "🟡 Dans la zone normale : se comporte comme sur les 20 ans d'historique."
    return texte, moy, bas, haut


def suivi_phidias(compte):
    ph = compte["phidias"]
    if ph["etat"] == "en cours":
        marge = compte["solde"] - (ph["plus_haut"] - PERTE_MAX_PHIDIAS)
        return f"en cours : {compte['solde'] - CAPITAL_DEPART:+,.0f} $ sur +4 000 $, marge restante {marge:,.0f} $"
    return f"{ph['etat']} le {ph['date']}"


def section_tableau(cle, compte):
    info = COMPTES[cle]
    j = pd.read_csv(DOSSIER / info["journal"])
    texte, moy, bas, haut = verdict(compte, info["sharpe"])
    gain = compte["solde"] - CAPITAL_DEPART
    positions = [f"| {micro(k)} | {k} | {ordre(k, v, ('Achat', 'Vente')).split()[0]} | {abs(v):.0f} |"
                 for k, v in sorted(compte["positions"].items(), key=lambda x: -abs(x[1]))]
    derniers = j.tail(10).iloc[::-1]
    lignes = [f"| {r.date} | {r.gain:+,.0f} $ | {r.solde:,.0f} $ |" for r in derniers.itertuples()]
    (DOSSIER / info["courbe"]).write_text(dessiner_courbe(j, info["sharpe"]))
    return [
        f"## {info['nom']}",
        "",
        f"Demarre le {compte['debut']}. Historique 2007-2026 au meme risque : {info['historique']}.",
        "",
        f"**{texte}**",
        "",
        "| Mesure | Valeur |",
        "|---|---|",
        f"| Solde virtuel | **{compte['solde']:,.0f} $** (depart 50 000 $) |",
        f"| Gain depuis le depart | {gain:+,.0f} $ ({gain / CAPITAL_DEPART:+.1%}) |",
        f"| Baisse depuis le plus haut | {compte['solde'] / compte['plus_haut'] - 1:.1%} |",
        f"| Zone normale a ce stade (8 cas sur 10) | de {bas:+,.0f} $ a {haut:+,.0f} $ (moyenne {moy:+,.0f} $) |",
        f"| Challenge Phidias 50K virtuel | {suivi_phidias(compte)} |",
        "",
        f"![Gain du compte et zone normale]({info['courbe']})",
        "",
        "| Contrat | Marche | Sens | Nombre |",
        "|---|---|---|---|",
        *(positions or ["| - | aucune position | - | - |"]),
        "",
        "<details><summary>10 derniers jours</summary>",
        "",
        "| Date | Resultat du jour | Solde |",
        "|---|---|---|",
        *lignes,
        "",
        f"Journal complet : [{info['journal']}]({info['journal']})",
        "",
        "</details>",
        "",
    ]


def ecrire_tableau(etat):
    """Tableau de bord Markdown mis a jour a chaque lancement (GitHub l'affiche directement)."""
    derniere = max(c["derniere_date"] for c in etat["comptes"].values() if c["derniere_date"])
    md = [
        "# Robot multi-marches : tableau de bord (argent virtuel)",
        "",
        f"Mis a jour le **{derniere}**. Deux comptes virtuels de 50 000 $, risque vise 12 %/an "
        "(environ 6 000 $). Aucun argent reel n'est engage.",
        "",
        "| Compte | Solde | Gain | Etat |",
        "|---|---|---|---|",
    ]
    for cle, c in etat["comptes"].items():
        if c["derniere_date"]:
            md.append(f"| {COMPTES[cle]['nom']} | {c['solde']:,.0f} $ | {c['solde'] - CAPITAL_DEPART:+,.0f} $ | "
                      f"{verdict(c, COMPTES[cle]['sharpe'])[0].split(':')[0].strip()} |")
    md += ["", "La zone bleue de chaque graphique montre ou tombaient 8 resultats sur 10 dans l'historique "
           "2007-2026, au meme risque. Tant que la ligne reste dedans, le compte se comporte comme prevu. "
           "Des semaines negatives sont normales : il faut plusieurs mois pour juger.", ""]
    for cle, c in etat["comptes"].items():
        if c["derniere_date"]:
            md += section_tableau(cle, c)
    md += ["Contrats de taux (2YY, 10Y, 30Y) : le sens indique est celui de l'ordre sur le contrat, "
           "inverse de celui des obligations. Methode et resultats historiques : [../README.md](../README.md)."]
    TABLEAU.write_text("\n".join(md) + "\n")


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


def avancer(compte, r, pos, cv):
    """Fait avancer un compte virtuel jusqu'a la derniere journee de bourse disponible.
    Renvoie (lignes du journal, ordres du dernier vendredi ou None, gain de la periode)."""
    derniere = pd.Timestamp(compte["derniere_date"]) if compte["derniere_date"] else None
    jours = r.index[r.index > derniere] if derniere is not None else r.index[-1:]
    if len(jours) and compte["debut"] is None:
        compte["debut"] = str(jours[0].date())
    lignes, ordres_semaine, gain_total = [], None, 0.0
    for d in jours:
        i = r.index.get_loc(d)
        n = pd.Series(compte["positions"], dtype=float).reindex(r.columns).fillna(0)
        # 1. gain ou perte du jour avec les positions de la veille
        gain = float((n * cv.iloc[i - 1] * r.iloc[i].fillna(0)).sum()) if derniere is not None else 0.0
        compte["solde"] += gain
        gain_total += gain
        # 2. vendredi (ou premier jour) : nouvelles positions
        ordres = {}
        if d.dayofweek == 4 or not compte["positions"]:
            cible = S.contrats_optimises(r.iloc[:i + 1], pos.iloc[:i + 1], cv.iloc[i], compte["solde"],
                                         VOL_VISEE, (1.0,), np.array([i]))[1.0].iloc[0]
            ordres = {k: float(v) for k, v in (cible - n).items() if v}
            compte["solde"] -= FRAIS * sum(abs(v) for v in ordres.values())
            compte["positions"] = {k: float(v) for k, v in cible.items() if v}
            ordres_semaine = ordres
        compte["plus_haut"] = max(compte["plus_haut"], compte["solde"])
        # 3. suivi d'un challenge Phidias Premium 50K virtuel
        ph = compte["phidias"]
        if ph["etat"] == "en cours":
            ph["plus_haut"] = max(ph["plus_haut"], compte["solde"])
            if compte["solde"] >= CAPITAL_DEPART + OBJECTIF_PHIDIAS:
                ph["etat"], ph["date"] = "reussi", str(d.date())
            elif compte["solde"] <= ph["plus_haut"] - PERTE_MAX_PHIDIAS:
                ph["etat"], ph["date"] = "perdu", str(d.date())
        lignes.append({"date": str(d.date()), "gain": round(gain, 2), "solde": round(compte["solde"], 2),
                       "ordres": json.dumps(ordres, ensure_ascii=False), "nb_positions": len(compte["positions"])})
        compte["derniere_date"] = str(d.date())
        derniere = d
    return lignes, ordres_semaine, gain_total


def main():
    close, adj = charger_prix()
    r = S.rendements_futures(close, adj)
    pos_melange, pos_tendance = S.positions_melange(r)
    positions = {"melange": pos_melange, "tendance": pos_tendance}
    cv = S.valeur_contrat(close).reindex(r.index).ffill()
    etat = lire_etat()
    DOSSIER.mkdir(parents=True, exist_ok=True)

    blocs, demarrages = [], []
    for cle, info in COMPTES.items():
        compte = etat["comptes"][cle]
        neuf = compte["debut"] is None
        lignes, ordres, gain_total = avancer(compte, r, positions[cle], cv)
        if lignes:
            chemin = DOSSIER / info["journal"]
            journal = pd.DataFrame(lignes)
            if chemin.exists():
                journal = pd.concat([pd.read_csv(chemin), journal])
            journal.to_csv(chemin, index=False)
        if not lignes:
            continue
        if neuf:
            demarrages.append(info)
        bloc = [f"📊 {info['nom']}",
                f"Resultat : {gain_total:+,.0f} $ | solde {compte['solde']:,.0f} $ "
                f"({compte['solde'] / CAPITAL_DEPART - 1:+.1%} depuis le {compte['debut']})",
                f"Baisse depuis le plus haut : {compte['solde'] / compte['plus_haut'] - 1:.1%}",
                f"Challenge Phidias 50K virtuel : {suivi_phidias(compte)}"]
        if ordres is not None:
            bloc += ["Ordres de la semaine :"] + ([ordre(k, v) for k, v in ordres.items()] or ["  aucun changement"])
            bloc += ["Positions tenues :", decrire_positions(compte["positions"])]
        blocs.append("\n".join(bloc))

    ETAT.write_text(json.dumps(etat, indent=2, ensure_ascii=False))
    if any(c["derniere_date"] for c in etat["comptes"].values()):
        ecrire_tableau(etat)
    if not blocs:
        print("Pas de nouvelle journee de bourse : rien a faire.")
        return

    derniere = max(c["derniere_date"] for c in etat["comptes"].values() if c["derniere_date"])
    msg = []
    for info in demarrages:
        msg += [f"🚀 Nouveau compte virtuel : {info['nom']} (50 000 $, aucun argent reel).",
                f"Historique 2007-2026 au meme risque : {info['historique']}.", ""]
    msg += [f"🤖 Robot multi-marches (ARGENT VIRTUEL) - {derniere}", ""]
    msg += ["\n\n".join(blocs)]
    telegram("\n".join(msg))


if __name__ == "__main__":
    main()
