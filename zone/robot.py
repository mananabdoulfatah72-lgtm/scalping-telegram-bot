#!/usr/bin/env python3
"""Robot ZONE DE BRUIT (Nasdaq, contrats micro MNQ) en ARGENT VIRTUEL, avec un challenge Phidias 50K virtuel
puis, s'il est reussi, un compte finance virtuel (etude : challenge/ sur la branche de recherche).

Regles, identiques au backtest (intraday/strategies.py zone_de_bruit et challenge/bot_challenge.py, f = 0,15) :
- seance de 9 h 30 a 16 h (New York) ; toutes les 30 minutes, de 10 h a 15 h 30, on compare le prix a la
  "zone de bruit" : ouverture (ou cloture de la veille) +/- mouvement moyen des 14 dernieres seances a
  cette minute. Au-dessus : achat ; en dessous : vente ; sortie si le prix repasse la limite ou le prix
  moyen du jour (VWAP) ; tout est ferme a 16 h. Frais : 1,5 point de NQ par aller-retour.
- taille : nombre de MNQ = 0,15 x coussin / ecart-type des gains des 60 dernieres seances (1 MNQ),
  coussin = solde - limite de perte. Plus le compte s'approche de la limite, plus il reduit.
- challenge Phidias 50K (regles a verifier) : +4 000 $ a atteindre, perte max 2 500 $ sous le plus haut de fin
  de journee. Compte finance : limite bloquee a 50 100 $ quand le solde atteint 52 600 $ ; retrait tous les
  21 jours de ce qui depasse 52 600 $ si la meilleure journee <= 30 % du gain ; 80 % du retrait pour toi.
  Un compte perdu est remplace par un nouveau challenge le lendemain.

Chaque matin de semaine (GitHub Actions ; les barres minute historiques de Databento arrivent environ 8 heures apres
la seance) : telecharge les barres minute NQ (secret DATABENTO_API_KEY), rejoue la seance de la veille, met a jour
zone/robot/ et envoie un resume Telegram. Aucun ordre reel.
Ce suivi se fait apres la cloture : pour trader en vrai, il faudrait les signaux en direct toutes les 30 minutes.

Rejeu hors ligne : ROBOT_MINUTES=chemin/nasdaq100_1min.csv.gz ROBOT_DEBUT=2025-01-02 ROBOT_JUSQU_AU=2025-12-31 \
                   ROBOT_DOSSIER=/tmp/zone python3 zone/robot.py
"""
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from pandas.tseries.holiday import GoodFriday, Holiday, nearest_workday, sunday_to_monday

DOSSIER = Path(os.getenv("ROBOT_DOSSIER", Path(__file__).parent / "robot"))
MINUTES = DOSSIER / "nq_1min.csv.gz"
ETAT, JOURNAL, TABLEAU = DOSSIER / "etat.json", DOSSIER / "journal.csv", DOSSIER / "TABLEAU_DE_BORD.md"
N, PAS, JOURS_MOYENNE = 390, 30, 14
PT, COUT = 2.0, 1.5                     # $ par point de NQ pour 1 MNQ ; points par aller-retour (frais + glissement)
F, MAX_MNQ = 0.15, 50
CAPITAL, OBJECTIF, PERTE = 50_000.0, 4_000.0, 2_500.0
BLOCAGE, SEUIL_RETRAIT, PART, PERIODE = 50_100.0, 52_600.0, 0.80, 21
PLAFOND_DATABENTO = 2.0                 # $ au maximum par telechargement
HISTORIQUE = ("backtest 2011-2026 au meme reglage : une tentative de challenge reussit 39 % du temps et saute 4 % "
              "(les autres n'ont pas fini) ; environ 1 chance sur 3 de valider en 12 mois ; une fois finance, "
              "environ 680 $ recus par an en moyenne, rien dans 86 % des cas")


# ----------------------------------------------------------------------------- donnees
def telecharger():
    """Ajoute les seances manquantes (Databento, NQ.v.0, barres d'une minute de 9 h 30 a 16 h)."""
    import databento as db
    ancien = pd.read_csv(MINUTES) if MINUTES.exists() else None
    debut = ancien["t"].str[:10].max() if ancien is not None else str((pd.Timestamp.now() - pd.Timedelta(days=200)).date())
    client = db.Historical()
    fin = pd.Timestamp(client.metadata.get_dataset_range(dataset="GLBX.MDP3")["end"]).isoformat()
    cout = client.metadata.get_cost(dataset="GLBX.MDP3", symbols=["NQ.v.0"], stype_in="continuous", schema="ohlcv-1m",
                                    start=debut, end=fin)
    if cout > PLAFOND_DATABENTO:
        raise SystemExit(f"Telechargement trop cher ({cout:.2f} $) : rien n'est fait")
    df = client.timeseries.get_range(dataset="GLBX.MDP3", symbols=["NQ.v.0"], stype_in="continuous",
                                     schema="ohlcv-1m", start=debut, end=fin).to_df()
    if df.empty:
        return
    t = pd.to_datetime(df["ts_event"], utc=True) if "ts_event" in df.columns else df.index
    t = pd.DatetimeIndex(t)
    t = (t.tz_localize("UTC") if t.tz is None else t).tz_convert("America/New_York")
    minute = t.hour * 60 + t.minute
    garde = (minute >= 570) & (minute < 960) & (t.dayofweek < 5)
    prix = df[["open", "high", "low", "close"]].astype(float)
    if prix["close"].median() > 1e6:
        prix = prix / 1e9
    neuf = pd.DataFrame({"t": t[garde].strftime("%Y-%m-%d %H:%M"), "o": prix["open"].values[garde],
                         "h": prix["high"].values[garde], "l": prix["low"].values[garde], "c": prix["close"].values[garde],
                         "v": df["volume"].values[garde], "contrat": df["instrument_id"].values[garde]})
    if ancien is not None:                  # la derniere seance deja enregistree est reprise (elle etait peut-etre incomplete)
        ancien = ancien[ancien["t"].str[:10] < debut]
    tout = pd.concat([ancien, neuf], ignore_index=True) if ancien is not None else neuf
    tout = tout.drop_duplicates("t", keep="last").sort_values("t").reset_index(drop=True)
    tout["v"] = tout["v"].astype("int64")
    tout["contrat"] = tout["contrat"].astype("int64")
    avant = pd.read_csv(MINUTES) if MINUTES.exists() else None
    if avant is not None and len(avant) == len(tout) and avant["t"].equals(tout["t"]) and \
            np.allclose(avant[["o", "h", "l", "c"]].values, tout[["o", "h", "l", "c"]].values):
        print("Databento : rien de nouveau")
        return
    # gzip sans date dans l'en-tete : un fichier identique ne cree pas de nouveau commit
    tout.to_csv(MINUTES, index=False, float_format="%.2f", compression={"method": "gzip", "mtime": 0})
    print(f"Databento : {len(neuf)} minutes du {debut} au {fin[:16]} ({cout:.3f} $)")


def tableaux(d):
    """Meme construction que intraday/strategies.py charger : tableaux (seances x 390 minutes)."""
    t = pd.to_datetime(d["t"])
    jour = t.dt.normalize()
    minute = (t.dt.hour * 60 + t.dt.minute - 570).values
    jours = np.sort(jour.unique())
    ij = np.searchsorted(jours, jour.values)
    tab = {}
    for col in "ohlc":
        a = np.full((len(jours), N), np.nan)
        a[ij, minute] = d[col].values
        tab[col] = a
    presentes = ~np.isnan(tab["c"])
    C = pd.DataFrame(tab["c"]).ffill(axis=1).values
    for col in "ohl":
        tab[col] = np.where(np.isnan(tab[col]), C, tab[col])
    V = np.zeros((len(jours), N))
    V[ij, minute] = d["v"].values
    contrat = d.groupby(ij)["contrat"].last().reindex(range(len(jours))).values
    echeance = np.r_[False, contrat[1:] != contrat[:-1]]
    return pd.DatetimeIndex(jours), tab["o"], tab["h"], tab["l"], C, presentes, V, echeance


def zone_de_bruit(jours, O, H, L, C, P, V, echeance):
    """Copie de intraday/strategies.py zone_de_bruit (avec VWAP), qui note aussi les trades du jour."""
    ok = P[:, 0] & P[:, N - 1] & (P.sum(axis=1) >= 370)
    ouverture = O[:, 0]
    veille = np.r_[np.nan, C[:-1, N - 1]]
    veille[echeance] = np.nan
    mouvement = np.abs(C / ouverture[:, None] - 1)
    sigma = pd.DataFrame(mouvement).rolling(JOURS_MOYENNE, min_periods=JOURS_MOYENNE).mean().shift(1).values
    typique = (H + L + C) / 3
    cumv = np.cumsum(V, axis=1)
    prix_moyen = np.where(cumv > 0, np.cumsum(typique * V, axis=1) / np.where(cumv > 0, cumv, 1),
                          np.cumsum(typique, axis=1) / np.arange(1, N + 1))
    haut_ref, bas_ref = np.fmax(ouverture, veille), np.fmin(ouverture, veille)
    lignes, trades = {}, {}
    moments = list(range(PAS, N, PAS))
    heure = lambda m: f"{(570 + m) // 60}h{(570 + m) % 60:02d}"
    for d in np.where(ok & ~np.isnan(veille) & ~np.isnan(sigma[:, PAS]))[0]:
        pos, entree, total, allers, pire, avant, liste = 0, 0.0, 0.0, 0, 0.0, 0, []
        for m in moments:
            if pos:
                creux = L[d, avant + 1:m + 1].min() - entree if pos > 0 else entree - H[d, avant + 1:m + 1].max()
                pire = min(pire, total + creux)
            avant = m
            p = C[d, m]
            ub, lb = haut_ref[d] * (1 + sigma[d, m]), bas_ref[d] * (1 - sigma[d, m])
            if pos > 0 and p <= max(ub, prix_moyen[d, m]):
                total += p - entree; pos = 0; liste[-1] += f" -> sortie {heure(m)} a {p:,.2f}"
            elif pos < 0 and p >= min(lb, prix_moyen[d, m]):
                total += entree - p; pos = 0; liste[-1] += f" -> sortie {heure(m)} a {p:,.2f}"
            if pos == 0 and p > ub:
                pos, entree, allers = 1, p, allers + 1; liste.append(f"achat {heure(m)} a {p:,.2f}")
            elif pos == 0 and p < lb:
                pos, entree, allers = -1, p, allers + 1; liste.append(f"vente {heure(m)} a {p:,.2f}")
        if pos:
            creux = L[d, avant + 1:].min() - entree if pos > 0 else entree - H[d, avant + 1:].max()
            pire = min(pire, total + creux)
            total += pos * (C[d, N - 1] - entree)
            liste[-1] += f" -> sortie 16h00 a {C[d, N - 1]:,.2f}"
        if allers > 0:
            lignes[jours[d]] = {"brut": total, "allers": allers, "pire": min(pire, total, 0.0)}
            trades[jours[d]] = liste
    z = pd.DataFrame.from_dict(lignes, orient="index")
    return z, trades, pd.DatetimeIndex(jours[ok])


def jour_court(d):
    """Fetes americaines ou la bourse CME ferme a 13 h, et demi-seances : le backtest ne les trade pas
    (memes regles que zone/tradingview/zone_de_bruit.pine)."""
    d = pd.Timestamp(d)
    a, m, j, w = d.year, d.month, d.day, d.dayofweek
    ouvre, lundi = w < 5, w == 0
    return bool((m == 1 and lundi and 15 <= j <= 21) or (m == 2 and lundi and 15 <= j <= 21) or (m == 5 and lundi and j >= 25)
                or (m == 9 and lundi and j <= 7)
                or (a >= 2022 and m == 6 and ((j == 19 and ouvre) or (j == 18 and w == 4) or (j == 20 and lundi)))
                or (m == 7 and (((j == 3 or j == 4) and ouvre) or (j == 5 and lundi)))
                or (m == 11 and ((w == 3 and 22 <= j <= 28) or (w == 4 and 23 <= j <= 29))) or (m == 12 and j == 24 and ouvre))


def jour_ferme(d):
    """Jours sans seance : Nouvel an, Vendredi saint, Noel (jours observes)."""
    d = pd.Timestamp(d)
    fetes = [Holiday("an", month=1, day=1, observance=sunday_to_monday), GoodFriday,
             Holiday("noel", month=12, day=25, observance=nearest_workday)]
    return d.dayofweek >= 5 or any(len(h.dates(d, d)) for h in fetes)


def serie_du_bot(minutes):
    """Gain, pire moment et risque prevu par jour pour 1 MNQ (comme challenge/bot_challenge.py donnees)."""
    jours, O, H, L, C, P, V, ech = tableaux(minutes)
    z, trades, completes = zone_de_bruit(jours, O, H, L, C, P, V, ech)
    dollars = (z["brut"] - COUT * z["allers"]) * PT if len(z) else pd.Series(dtype=float)
    gain = dollars.reindex(completes).fillna(0)
    pire = (z["pire"] * PT).reindex(completes).fillna(0).clip(upper=0) if len(z) else gain * 0
    pire = np.minimum(pire, np.minimum(gain, 0))
    risque1 = gain.rolling(60, min_periods=40).std().shift(1)
    d = pd.DataFrame({"gain": gain, "pire": pire, "risque1": risque1}).dropna()
    risque_demain = gain.rolling(60, min_periods=40).std()             # connu ce soir, utilise demain
    return d, trades, jours, float(risque_demain.iloc[-1]) if len(risque_demain) else float("nan")


def niveaux(minutes, r):
    """Niveaux pour la prochaine seance (a utiliser en direct, par exemple avec zone/tradingview/zone_de_bruit.pine) :
    cloture de la veille, mouvement moyen des 14 dernieres seances a chaque controle, taille conseillee."""
    jours, O, H, L, C, P, V, ech = tableaux(minutes)
    if not (P[-1, 0] and P[-1, N - 1]) and not jour_court(jours[-1]):
        jours, O, C = jours[:-1], O[:-1], C[:-1]      # derniere seance encore incomplete (delai des donnees) : ecartee
    ctrl = list(range(PAS, N, PAS))
    if len(jours) < JOURS_MOYENNE:
        return None
    sigma = np.abs(C[-JOURS_MOYENNE:, :] / O[-JOURS_MOYENNE:, :1] - 1)[:, ctrl].mean(axis=0)
    prochaine = pd.Timestamp(jours[-1]) + pd.Timedelta(days=1)
    while jour_ferme(prochaine):
        prochaine += pd.Timedelta(days=1)
    court = jour_court(prochaine)
    heures = []
    for m, sg in zip(ctrl, sigma):
        t_ny = pd.Timestamp(prochaine.date()).tz_localize("America/New_York") + pd.Timedelta(minutes=570 + m)
        heures.append({"ny": t_ny.strftime("%Hh%M"), "paris": t_ny.tz_convert("Europe/Paris").strftime("%Hh%M"), "sigma": float(sg)})
    ok = np.isfinite(r) and r > 0
    taille = lambda c, f: int(min(MAX_MNQ, np.floor(f * c / r))) if ok else 0
    return {"seance": str(prochaine.date()), "jour_court": court, "veille": float(C[-1, N - 1]), "controles": heures,
            "risque_1_mnq": r if ok else None,
            "tailles": {f"{f:.2f}": {"Phidias (coussin 2 500 $)": taille(2500, f), "Topstep (coussin 2 000 $)": taille(2000, f)}
                        for f in (0.15, 0.25, 0.35)}}


# ----------------------------------------------------------------------------- comptes virtuels
def nouveau_challenge(etat, date):
    etat["tentatives"].append({"numero": len(etat["tentatives"]) + 1, "debut": date, "fin": None, "issue": "en cours"})
    etat.update(phase="challenge", solde=CAPITAL, haut=CAPITAL, meilleur=0.0, gain_periode=0.0, jours_finance=0)


def lire_etat(d):
    if ETAT.exists():
        return json.loads(ETAT.read_text())
    debut = pd.Timestamp(os.getenv("ROBOT_DEBUT") or d.index[-1])
    derniere = d.index[d.index <= debut][-1] if (d.index <= debut).any() else d.index[0] - pd.Timedelta(days=1)
    etat = {"debut": str(derniere.date()), "derniere_date": str(derniere.date()), "tentatives": [], "recu_total": 0.0,
            "gain_1_mnq": 0.0}
    nouveau_challenge(etat, None)          # la date de debut est celle de la premiere seance jouee
    return etat


def une_journee(etat, x, date):
    """Joue une seance sur le compte virtuel (challenge ou finance). Renvoie la ligne du journal."""
    finance = etat["phase"] == "finance"
    if etat["tentatives"][-1]["debut"] is None:
        etat["tentatives"][-1]["debut"] = date
    haut = etat["haut"]
    plancher = (BLOCAGE if haut >= SEUIL_RETRAIT else haut - PERTE) if finance else haut - PERTE
    coussin = etat["solde"] - plancher
    n = int(np.clip(np.floor(F * coussin / x["risque1"]), 0, MAX_MNQ)) if x["risque1"] > 0 else 0
    jour, creux = n * x["gain"], n * x["pire"]
    ligne = {"date": date, "phase": etat["phase"], "tentative": etat["tentatives"][-1]["numero"], "mnq": n,
             "gain": round(jour, 2), "gain_1_mnq": round(x["gain"], 2), "retrait": 0.0}
    etat["gain_1_mnq"] += x["gain"]
    if etat["solde"] + creux <= plancher or etat["solde"] + jour <= plancher:
        # le compte est coupe a sa limite : la perte du jour est la distance a la limite
        ligne.update(gain=round(plancher - etat["solde"], 2), solde=round(plancher, 2), evenement="COMPTE PERDU (limite touchee)")
        etat["tentatives"][-1].update(fin=date, issue="perdu" if not finance else "perdu apres financement")
        nouveau_challenge(etat, None)
        return ligne
    etat["solde"] += jour
    etat["haut"] = max(etat["haut"], etat["solde"])
    ligne["evenement"] = ""
    if not finance and etat["solde"] - CAPITAL >= OBJECTIF:
        ligne.update(solde=round(etat["solde"], 2), evenement="CHALLENGE REUSSI : passage au compte finance virtuel")
        etat["tentatives"][-1].update(fin=date, issue="reussi")
        etat.update(phase="finance", solde=CAPITAL, haut=CAPITAL, meilleur=0.0, gain_periode=0.0, jours_finance=0)
    elif finance:
        etat["jours_finance"] += 1
        etat["meilleur"], etat["gain_periode"] = max(etat["meilleur"], jour), etat["gain_periode"] + jour
        if (etat["jours_finance"] % PERIODE == 0 and etat["solde"] > SEUIL_RETRAIT and etat["gain_periode"] > 0
                and etat["meilleur"] <= 0.3 * etat["gain_periode"]):
            retrait = etat["solde"] - SEUIL_RETRAIT
            etat["recu_total"] += PART * retrait
            etat["solde"] -= retrait
            etat["meilleur"], etat["gain_periode"] = 0.0, 0.0
            ligne.update(retrait=round(PART * retrait, 2), evenement=f"RETRAIT virtuel : {PART * retrait:,.0f} $ pour toi")
    ligne.setdefault("solde", round(etat["solde"], 2))
    return ligne


# ----------------------------------------------------------------------------- sorties
def tableau(etat, journal, trades_du_jour, niv=None):
    t = etat["tentatives"][-1]
    if etat["phase"] == "challenge":
        haut = etat["haut"]
        situation = (f"Challenge n°{t['numero']} en cours : {etat['solde'] - CAPITAL:+,.0f} $ sur +4 000 $ ; "
                     f"marge avant la limite {etat['solde'] - (haut - PERTE):,.0f} $")
    else:
        plancher = BLOCAGE if etat["haut"] >= SEUIL_RETRAIT else etat["haut"] - PERTE
        situation = (f"Compte finance virtuel : solde {etat['solde']:,.0f} $, marge avant la limite "
                     f"{etat['solde'] - plancher:,.0f} $, recu en tout {etat['recu_total']:,.0f} $")
    j = journal.tail(15).iloc[::-1]
    lignes = [
        "# Robot zone de bruit (MNQ) : tableau de bord (argent virtuel)",
        "",
        f"Mis a jour le **{etat['derniere_date']}**. Demarre le {etat['debut']}. Aucun argent reel n'est engage.",
        "",
        f"Historique : {HISTORIQUE}.",
        "",
        f"**{situation}**",
        "",
        "| Mesure | Valeur |",
        "|---|---|",
        f"| Tentatives de challenge | {len(etat['tentatives'])} ("
        + ", ".join(f"n°{x['numero']} {x['issue']}" for x in etat["tentatives"]) + ") |",
        f"| Recu en retraits virtuels (80 %) | {etat['recu_total']:,.0f} $ |",
        f"| Gain de la strategie pour 1 MNQ depuis le depart | {etat['gain_1_mnq']:+,.0f} $ |",
        "",
    ]
    if trades_du_jour:
        lignes += [f"## Trades du {etat['derniere_date']}", ""] + [f"- {x}" for x in trades_du_jour] + [""]
    if niv and niv["jour_court"]:
        lignes += [f"## Seance du {niv['seance']} : fete ou demi-seance, PAS DE TRADE", "",
                   "Le backtest ne trade pas ces jours-la. Les niveaux de la seance suivante seront publies apres.", ""]
    elif niv:
        lignes += [f"## Pour la seance du {niv['seance']} (a utiliser en direct)", "",
                   f"Cloture de la veille (16 h New York) : **{niv['veille']:,.2f}**. Apres l'ouverture de 9 h 30 : "
                   "haut = max(ouverture, veille) x (1 + mouvement) ; bas = min(ouverture, veille) x (1 - mouvement). "
                   "A chaque heure ci-dessous : cloture de la minute au-dessus du haut -> achat ; sous le bas -> vente ; "
                   "en position, sortie si le prix repasse la limite ou le VWAP. Tout fermer a 15 h 59 (New York).", "",
                   "| Controle (New York) | Heure de Paris | Mouvement moyen | Haut = x | Bas = x |", "|---|---|---|---|---|",
                   *[f"| {c['ny']} | {c['paris']} | {c['sigma']:.3%} | {1 + c['sigma']:.5f} | {1 - c['sigma']:.5f} |"
                     for c in niv["controles"]], "",
                   (f"Taille : un jour normal = {niv['risque_1_mnq']:,.0f} $ de risque pour 1 MNQ. Sur un compte neuf : "
                    + " ; ".join(f"f = {f} -> " + ", ".join(f"{k} {v} MNQ" for k, v in t.items()) for f, t in niv["tailles"].items())
                    + ". **En cours de challenge : MNQ = f x (solde - limite de perte) / "
                    + f"{niv['risque_1_mnq']:,.0f}, arrondi en dessous** (exemple : f = 0,25, coussin 1 500 $ -> "
                    + f"{int(np.floor(0.25 * 1500 / niv['risque_1_mnq']))} MNQ).") if niv["risque_1_mnq"] else
                   "Taille : pas encore assez d'historique (40 seances).", "",
                   "Le VWAP est celui de la seance americaine, calcule depuis 9 h 30 (pas depuis la reouverture de 18 h). "
                   "On ne regarde le prix qu'aux heures de controle : pas de stop place dans le marche.", ""]
    lignes += ["## Derniers jours", "", "| Date | Phase | MNQ | Resultat du jour | Solde | Pour 1 MNQ | Evenement |",
               "|---|---|---|---|---|---|---|",
               *[f"| {r.date} | {r.phase} n°{r.tentative} | {r.mnq} | {r.gain:+,.0f} $ | {r.solde:,.0f} $ | {r.gain_1_mnq:+,.0f} $ |"
                 f" {r.evenement if isinstance(r.evenement, str) else ''} |" for r in j.itertuples()], ""]
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
    if os.getenv("ROBOT_MINUTES"):
        minutes = pd.read_csv(os.getenv("ROBOT_MINUTES"))
    else:
        telecharger()
        minutes = pd.read_csv(MINUTES)
    if os.getenv("ROBOT_JUSQU_AU"):
        minutes = minutes[minutes["t"].str[:10] <= os.getenv("ROBOT_JUSQU_AU")]
    d, trades, jours, risque_demain = serie_du_bot(minutes)
    # la derniere seance n'est jouee que si elle est complete (sinon les donnees arrivent peut-etre encore)
    if len(jours) and jours[-1] not in d.index and jours[-1] > d.index[-1] and not jour_court(jours[-1]):
        print(f"Seance du {jours[-1].date()} incomplete pour l'instant : elle sera jouee au prochain passage")
    neuf = not ETAT.exists()
    etat = lire_etat(d)
    lignes = []
    for date, x in d[d.index > pd.Timestamp(etat["derniere_date"])].iterrows():
        lignes.append(une_journee(etat, x, str(date.date())))
        etat["derniere_date"] = str(date.date())
    niv = niveaux(minutes, risque_demain)
    f_niv = DOSSIER / "niveaux.json"
    ancien_niv = json.loads(f_niv.read_text()) if f_niv.exists() else None
    if not lignes and not neuf and niv == ancien_niv:
        print(f"Pas de nouvelle seance depuis le {etat['derniere_date']} : rien a faire.")
        return
    ancien = pd.read_csv(JOURNAL) if JOURNAL.exists() else None
    journal = pd.concat([ancien, pd.DataFrame(lignes)], ignore_index=True) if ancien is not None else pd.DataFrame(lignes)
    if len(journal):
        journal.to_csv(JOURNAL, index=False)
    ETAT.write_text(json.dumps(etat, indent=1, ensure_ascii=False))
    du_jour = trades.get(pd.Timestamp(etat["derniere_date"]), [])
    if niv is not None:
        f_niv.write_text(json.dumps(niv, indent=1, ensure_ascii=False))
    tableau(etat, journal if len(journal) else pd.DataFrame(columns=["date"]), du_jour, niv)
    msg = [f"Robot zone de bruit MNQ (argent virtuel) - {etat['derniere_date']}"]
    if lignes:
        msg.append(f"Depuis le dernier message : {sum(l['gain'] for l in lignes):+,.0f} $ ({len(lignes)} seance(s)),"
                   f" {lignes[-1]['mnq']} MNQ le dernier jour")
        msg += [l["evenement"] for l in lignes if l["evenement"]]
    msg.append(f"Phase : {etat['phase']} n°{etat['tentatives'][-1]['numero']}, solde {etat['solde']:,.0f} $"
               f" ({etat['solde'] - CAPITAL:+,.0f} $), recu en tout {etat['recu_total']:,.0f} $")
    if lignes:
        msg += [f"- {x}" for x in du_jour] or ["Aucun trade le dernier jour"]
    if niv is None:
        pass
    elif niv["jour_court"]:
        msg.append(f"Seance du {niv['seance']} : fete ou demi-seance, PAS DE TRADE")
    else:
        msg.append(f"Seance du {niv['seance']} : veille {niv['veille']:,.2f} ; mouvements "
                   + " ".join(f"{c['paris']}:{c['sigma']:.2%}" for c in niv["controles"])
                   + f" ; compte neuf f=0,25 : {niv['tailles']['0.25']['Phidias (coussin 2 500 $)']} MNQ (Phidias)")
    envoyer("\n".join(msg))


if __name__ == "__main__":
    main()
