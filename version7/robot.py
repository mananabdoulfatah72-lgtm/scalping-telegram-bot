#!/usr/bin/env python3
"""Robot VERSION 7 en ARGENT VIRTUEL : compte de 50 000 $ (etude secteurs/README.md, branche de recherche).

Regle (inchangee depuis le backtest) : a la cloture du dernier jour de bourse de chaque mois, garder
les 5 actions de la liste technologie ci-dessous au meilleur rendement de t - 6 mois a t - 1 mois
(126 et 21 seances), cotees depuis au moins un an, a 10 % du compte chacune ; les 50 % restants ne sont
pas investis. Entre deux fins de mois, les montants suivent les prix.

Chaque soir de semaine, apres la cloture americaine (GitHub Actions) :
1. telecharge les prix (Yahoo) ;
2. valorise le compte virtuel jour par jour depuis la derniere mise a jour ;
3. le dernier jour de bourse du mois, reequilibre a la cloture (frais 5 points de base par ordre) ;
4. la veille, envoie les ordres a passer : les signaux n'utilisent que des prix deja connus
   (t - 21 et t - 126 seances), donc les ordres du dernier jour sont connus un jour a l'avance ;
5. envoie un resume sur Telegram et met a jour version7/robot/TABLEAU_DE_BORD.md.

Aucun ordre reel n'est passe. Les liquidites virtuelles ne rapportent rien (comme sur un compte de challenge).
Rejeu hors ligne : ROBOT_PRIX=chemin/prix.csv.gz ROBOT_DEBUT=2021-09-29 ROBOT_JUSQU_AU=2026-09-25 \
                   ROBOT_DOSSIER=/tmp/v7 python3 version7/robot.py
"""
import json
import os
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from pandas.tseries.holiday import (AbstractHolidayCalendar, GoodFriday, Holiday, USLaborDay, USMartinLutherKingJr,
                                    USMemorialDay, USPresidentsDay, USThanksgivingDay, nearest_workday,
                                    sunday_to_monday)
from pandas.tseries.offsets import CustomBusinessDay

DOSSIER = Path(os.getenv("ROBOT_DOSSIER", Path(__file__).parent / "robot"))
ETAT, JOURNAL, TABLEAU = DOSSIER / "etat.json", DOSSIER / "journal.csv", DOSSIER / "TABLEAU_DE_BORD.md"
CAPITAL = 50_000.0
# liste fixee dans l'etude (secteurs/univers.py, ACTIONS["XLK"]) ; on ne la change pas
UNIVERS = ["AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "CRM", "AMD", "ADBE", "CSCO", "ACN", "IBM", "INTU",
           "TXN", "QCOM", "AMAT", "NOW", "MU", "LRCX", "KLAC", "ADI"]
SECTEUR = "XLK"                      # detenu seulement si moins de 3 actions sont cotees depuis un an
N, PART_ACTIONS, FRAIS = 5, 0.5, 5e-4
AN, M6, SAUT = 252, 126, 21
# CFD actions, compte swing (a verifier chez la firme) : phase 1 +10 %, perte max 10 % du depart, 5 % par jour
CHALLENGE = {"objectif": 5_000, "perte": 5_000, "jour_max": 2_500}
SAUT_MAX = 0.5                       # un mouvement de plus de 50 % en un jour est traite comme une erreur de donnees
HISTORIQUE = ("backtest sans interets sur les liquidites (comme ce compte) : 2021-2026 (periode ou la version a ete "
              "choisie) +21,6 %/an, pire baisse environ -23 % ; 2006-2021 +12,8 %/an, pire baisse environ -32 %. "
              "Rejetee par le critere 8 (placebo 93 % pour 95 %).")


class Bourse(AbstractHolidayCalendar):
    """Jours feries de la Bourse de New York."""
    rules = [Holiday("Nouvel an", month=1, day=1, observance=sunday_to_monday), USMartinLutherKingJr, USPresidentsDay,
             GoodFriday, USMemorialDay, Holiday("Juneteenth", month=6, day=19, start_date="2022-01-01",
                                                observance=nearest_workday),
             Holiday("Fete nationale", month=7, day=4, observance=nearest_workday), USLaborDay, USThanksgivingDay,
             Holiday("Noel", month=12, day=25, observance=nearest_workday)]


SEANCE = CustomBusinessDay(calendar=Bourse())


def seance_suivante(d):
    return pd.Timestamp(d) + SEANCE


def dernier_du_mois(d):
    """Vrai si d est la derniere seance de son mois d'apres le calendrier de la bourse."""
    return seance_suivante(d).month != pd.Timestamp(d).month


# ----------------------------------------------------------------------------- donnees
def charger_prix():
    """Prix ajustes (rendements) et prix bruts (nombre d'actions), seances x tickers."""
    tickers = UNIVERS + [SECTEUR]
    fin = os.getenv("ROBOT_JUSQU_AU")
    if os.getenv("ROBOT_PRIX"):
        d = pd.read_csv(os.getenv("ROBOT_PRIX"), parse_dates=["date"])
        d = d[d["ticker"].isin(tickers)]
        adj = d.pivot(index="date", columns="ticker", values="adjclose")
        brut = d.pivot(index="date", columns="ticker", values="close")
    else:
        import yfinance as yf
        x = yf.download(tickers, start=str(date.today() - timedelta(days=800)), auto_adjust=False, progress=False,
                        threads=True)
        adj, brut = x["Adj Close"], x["Close"]
    manque = [t for t in tickers if t not in adj.columns]
    if manque:
        raise SystemExit(f"Prix manquants : {manque}")
    jours = adj[UNIVERS].dropna(how="all").index
    if fin:
        jours = jours[jours <= fin]
    if not os.getenv("ROBOT_PRIX"):
        maintenant = pd.Timestamp.now(tz="America/New_York")
        if jours[-1].date() == maintenant.date() and maintenant.hour < 17:
            jours = jours[:-1]           # seance du jour pas encore cloturee : prix provisoire, on l'ignore
        attendue = SEANCE.rollback(pd.Timestamp(maintenant.date()) - pd.Timedelta(days=0 if maintenant.hour >= 17 else 1))
        if jours[-1] < attendue:
            raise SystemExit(f"Prix du {attendue.date()} pas encore publies (derniere seance : {jours[-1].date()}) ; "
                             "rien n'est enregistre, le prochain passage rattrapera")
    adj, brut = adj.reindex(jours)[tickers], brut.reindex(jours)[tickers]
    # toutes les actions de la liste cotent depuis des annees : un trou recent est une erreur de donnees
    trous = [t for t in UNIVERS if adj[t].iloc[-AN - 30:].isna().any() or brut[t].iloc[-1:].isna().any()]
    if trous:
        raise SystemExit(f"Prix incomplets sur la derniere annee pour {trous} ; rien n'est enregistre")
    return adj, brut


def cible(adj, i):
    """Poids voulus a la cloture de la seance i (meme calcul que Etude.s2 puis moitie)."""
    p = adj[UNIVERS]
    ok = p.iloc[i - AN:i + 1].notna().all()
    el = [a for a in UNIVERS if ok[a]]
    if len(el) < 3:
        return {SECTEUR: PART_ACTIONS}
    mom = p.iloc[i - SAUT][el] / p.iloc[i - M6][el] - 1
    choix = list(mom.sort_values(ascending=False).index[:N])
    return {a: PART_ACTIONS / len(choix) for a in choix}


def cible_de_demain(adj):
    """Poids voulus a la prochaine seance (connus des aujourd'hui : prix de t - 21 et t - 126 seances)."""
    p = pd.concat([adj, pd.DataFrame(np.nan, index=[seance_suivante(adj.index[-1])], columns=adj.columns)])
    p.iloc[-1] = p.iloc[-2]              # le prix de demain ne sert pas au choix ; seulement la cotation depuis un an
    return cible(p, len(p) - 1)


# ----------------------------------------------------------------------------- compte virtuel
def nouveau(debut):
    return {"debut": str(debut.date()), "derniere_date": str(debut.date()), "solde": CAPITAL, "plus_haut": CAPITAL,
            "montants": {}, "liquidites": CAPITAL, "dernier_reequilibrage": None, "ordres": [],
            "challenge": {"etat": "en attente du premier achat", "date": None}}


def lire_etat(adj):
    if ETAT.exists():
        return json.loads(ETAT.read_text())
    debut = pd.Timestamp(os.getenv("ROBOT_DEBUT") or adj.index[-1])
    return nouveau(adj.index[adj.index <= debut][-1])


def ordres(montants, solde, w, prix):
    """Ordres pour passer des montants actuels aux poids w (meme calcul pour l'annonce et l'execution)."""
    voulu = {a: w.get(a, 0.0) * solde for a in sorted(set(w) | set(montants))}
    out = []
    for a, v in voulu.items():
        ecart = v - montants.get(a, 0.0)
        if abs(ecart) >= 1.0:
            out.append({"ticker": a, "sens": "Achat" if ecart > 0 else "Vente", "montant": round(abs(ecart), 2),
                        "actions": round(abs(ecart) / prix[a], 2), "prix": round(float(prix[a]), 2)})
    return voulu, out


def reequilibrer(etat, adj, brut, i):
    """Reequilibrage a la cloture de la seance i (frais sur les montants echanges)."""
    voulu, liste = ordres(etat["montants"], etat["solde"], cible(adj, i), brut.iloc[i])
    cout = sum(abs(v - etat["montants"].get(a, 0.0)) for a, v in voulu.items()) * FRAIS
    garde = 1 - cout / etat["solde"]
    etat["solde"] -= cout
    etat["montants"] = {a: v * garde for a, v in voulu.items() if v > 0}
    etat["liquidites"] = etat["solde"] - sum(etat["montants"].values())
    etat["dernier_reequilibrage"] = str(adj.index[i].date())
    etat["ordres"] = liste
    etat["frais_dernier_reequilibrage"] = round(cout, 2)


def avancer(etat, adj, brut):
    """Valorise le compte seance par seance depuis la derniere mise a jour ; reequilibre en fin de mois."""
    lignes = []
    idx = adj.index
    precedent = pd.Timestamp(etat["derniere_date"])
    if precedent not in idx:
        raise SystemExit(f"La derniere seance du compte ({precedent.date()}) n'est pas dans les prix telecharges")
    i0 = idx.get_loc(precedent)
    # fermeture imprevue de la bourse le dernier jour prevu du mois : la vraie derniere seance du mois etait
    # la derniere traitee ; on reequilibre a sa cloture (connue), comme le ferait le backtest
    fait = etat["dernier_reequilibrage"]
    if i0 + 1 < len(idx) and idx[i0 + 1].month != precedent.month and (fait is None or fait[:7] != str(precedent)[:7]):
        avant = etat["solde"]
        reequilibrer(etat, adj, brut, i0)
        lignes.append({"date": str(precedent.date()), "gain": round(etat["solde"] - avant, 2), "solde": round(etat["solde"], 2),
                       "reequilibrage": "oui (rattrape : frais seulement)"})
    for i in range(i0 + 1, len(idx)):
        d = idx[i]
        solde_veille = etat["solde"]
        for a in sorted(etat["montants"]):
            r = adj[a].iloc[i] / adj[a].iloc[i - 1]
            if not np.isfinite(r) or abs(r - 1) > SAUT_MAX:
                raise SystemExit(f"Rendement suspect pour {a} le {d.date()} ({r}) ; rien n'est enregistre")
            etat["montants"][a] *= r
        etat["solde"] = etat["liquidites"] + sum(etat["montants"].values())
        fin_mois = (i + 1 < len(idx) and idx[i + 1].month != d.month) or (i + 1 == len(idx) and dernier_du_mois(d))
        if fin_mois:
            reequilibrer(etat, adj, brut, i)
        etat["plus_haut"] = max(etat["plus_haut"], etat["solde"])
        suivre_challenge(etat, d, etat["solde"] - solde_veille)
        etat["derniere_date"] = str(d.date())
        lignes.append({"date": str(d.date()), "gain": round(etat["solde"] - solde_veille, 2), "solde": round(etat["solde"], 2),
                       "reequilibrage": "oui" if fin_mois else ""})
    return lignes


def suivre_challenge(etat, d, jour):
    """Challenge virtuel (phase 1 d'un compte CFD actions swing), commence au premier achat."""
    ch = etat["challenge"]
    if ch["etat"] == "en attente du premier achat":
        if etat["montants"]:
            ch.update(etat="en cours", date=str(d.date()), depart=etat["solde"])
        return
    if ch["etat"] != "en cours":
        return
    gain = etat["solde"] - ch["depart"]
    if jour <= -CHALLENGE["jour_max"] or gain <= -CHALLENGE["perte"]:
        ch.update(etat="perdu", date=str(d.date()))
    elif gain >= CHALLENGE["objectif"]:
        ch.update(etat="reussi", date=str(d.date()))


# ----------------------------------------------------------------------------- sorties
def texte_ordres(ordres, titre):
    if not ordres:
        return [f"{titre} : aucun changement."]
    return [f"{titre} :"] + [f"- {o['sens']} {o['ticker']} : {o['montant']:,.0f} $"
                             + (f" (environ {o['actions']:,.1f} actions a {o['prix']:,.2f} $)" if o.get("actions") else "")
                             for o in ordres]


def ordres_prevus(etat, adj, brut):
    """Ordres a passer demain a la cloture, si demain est la derniere seance du mois (montants aux prix d'aujourd'hui)."""
    if not dernier_du_mois(seance_suivante(adj.index[-1])):
        return None
    return ordres(etat["montants"], etat["solde"], cible_de_demain(adj), brut.iloc[-1])[1]


def tableau(etat, journal, prevus):
    gain = etat["solde"] - CAPITAL
    ch = etat["challenge"]
    ch_txt = {"en cours": lambda: f"en cours depuis le {ch['date']} : {etat['solde'] - ch['depart']:+,.0f} $ sur +5 000 $ "
                                  f"(perdu a -5 000 $, ou -2 500 $ en un jour)",
              "reussi": lambda: f"REUSSI le {ch['date']}", "perdu": lambda: f"PERDU le {ch['date']}",
              "en attente du premier achat": lambda: "commence au premier achat"}[ch["etat"]]()
    pos = [f"| {a} | {v:,.0f} $ | {v / etat['solde']:.1%} |" for a, v in sorted(etat["montants"].items(), key=lambda x: -x[1])]
    j = journal.tail(10).iloc[::-1]
    lignes = [
        "# Robot version 7 : tableau de bord (argent virtuel)",
        "",
        f"Mis a jour le **{etat['derniere_date']}**. Compte virtuel de 50 000 $ demarre le {etat['debut']}. "
        "Aucun argent reel n'est engage.",
        "",
        "Regle : chaque fin de mois, les 5 actions technologie au meilleur rendement de 6 mois a 1 mois, 10 % "
        "du compte chacune, 50 % non investis.",
        "",
        f"Historique : {HISTORIQUE}",
        "",
        "| Mesure | Valeur |",
        "|---|---|",
        f"| Solde virtuel | **{etat['solde']:,.0f} $** |",
        f"| Gain depuis le depart | {gain:+,.0f} $ ({gain / CAPITAL:+.1%}) |",
        f"| Baisse depuis le plus haut | {etat['solde'] / etat['plus_haut'] - 1:.1%} |",
        f"| Dernier reequilibrage | {etat['dernier_reequilibrage'] or 'aucun (le premier se fait a la fin du mois)'} |",
        f"| Challenge virtuel (CFD actions, phase 1 : +10 % / -10 %, sans frais de financement) | {ch_txt} |",
        "",
        "## Positions",
        "",
        "| Action | Montant | Part du compte |",
        "|---|---|---|",
        *(pos or ["| (aucune) | | |"]),
        f"| Non investi | {etat['liquidites']:,.0f} $ | {etat['liquidites'] / etat['solde']:.1%} |",
        "",
    ]
    if prevus is not None:
        lignes += ["## Ordres a passer demain a la cloture (dernier jour du mois)", ""] + \
                  [f"- {o['sens']} {o['ticker']} : {o['montant']:,.0f} $ (environ {o['actions']:,.1f} actions)" for o in prevus] + [""]
    if etat["ordres"]:
        lignes += [f"## Derniers ordres ({etat['dernier_reequilibrage']}, a la cloture, avant "
                   f"{etat.get('frais_dernier_reequilibrage', 0):,.0f} $ de frais)", ""] + \
                  [f"- {o['sens']} {o['ticker']} : {o['montant']:,.0f} $" for o in etat["ordres"]] + [""]
    lignes += ["<details><summary>10 derniers jours</summary>", "", "| Date | Resultat du jour | Solde |", "|---|---|---|",
               *[f"| {r.date} | {r.gain:+,.0f} $ | {r.solde:,.0f} $ |" for r in j.itertuples()], "", "</details>", ""]
    TABLEAU.write_text("\n".join(lignes))


def envoyer(message):
    jeton, chat = os.getenv("TELEGRAM_TOKEN"), os.getenv("CHAT_ID")
    print(message)
    if not jeton or not chat:
        print("(Telegram non configure : secrets TELEGRAM_TOKEN / CHAT_ID absents)")
        return
    try:
        rep = requests.post(f"https://api.telegram.org/bot{jeton}/sendMessage", data={"chat_id": chat, "text": message},
                            timeout=20)
        if not rep.ok:
            print(f"Erreur Telegram {rep.status_code} : {rep.text[:200]}")
    except requests.RequestException as e:
        print(f"Erreur Telegram : {e}")


def main():
    DOSSIER.mkdir(parents=True, exist_ok=True)
    adj, brut = charger_prix()
    etat = lire_etat(adj)
    lignes = avancer(etat, adj, brut)
    if not lignes and ETAT.exists():
        print(f"Pas de nouvelle seance depuis le {etat['derniere_date']} : rien a faire.")
        return
    ancien = pd.read_csv(JOURNAL) if JOURNAL.exists() else pd.DataFrame(columns=["date", "gain", "solde", "reequilibrage"])
    journal = pd.concat([ancien, pd.DataFrame(lignes)], ignore_index=True) if lignes else ancien
    journal.to_csv(JOURNAL, index=False)
    prevus = ordres_prevus(etat, adj, brut)
    ETAT.write_text(json.dumps(etat, indent=1, ensure_ascii=False))
    tableau(etat, journal, prevus)
    gain = etat["solde"] - CAPITAL
    msg = [f"Robot version 7 (argent virtuel) - {etat['derniere_date']}",
           f"Solde {etat['solde']:,.0f} $ ({gain:+,.0f} $ depuis le {etat['debut']})"]
    if lignes:
        msg.append(f"Depuis le dernier message : {sum(l['gain'] for l in lignes):+,.0f} $ ({len(lignes)} seance(s))")
    if any(l["reequilibrage"] for l in lignes):
        msg += texte_ordres(etat["ordres"], f"Reequilibrage fait a la cloture du {etat['dernier_reequilibrage']}")
    if prevus is not None:
        msg += texte_ordres(prevus, "DEMAIN, dernier jour du mois : ordres a passer a la cloture")
    msg.append("Positions : " + (", ".join(f"{a} {v:,.0f} $" for a, v in sorted(etat["montants"].items())) or "aucune"))
    envoyer("\n".join(msg))


if __name__ == "__main__":
    main()
