#!/usr/bin/env python3
"""Robot ZONE DE BRUIT (Nasdaq, contrats micro MNQ) en ARGENT VIRTUEL, avec un challenge Phidias 50K virtuel
puis, s'il est reussi, un compte finance virtuel (etude : challenge/ sur la branche de recherche).

Regles, identiques au backtest corrige V1 (zone_failles/journal.py sur la branche de recherche ; taille comme
challenge/bot_challenge.py, f = 0,15). Depuis le 1er octobre 2026, un second moteur est suivi A PART, hors du compte de
challenge (rebond apres forte baisse, fonction rebond : gain pour 1 MNQ dans le journal, colonne gain_rebond_1_mnq) :
- seance de 9 h 30 a 16 h (New York) ; toutes les 30 minutes, de 10 h a 15 h 30, on compare le prix a la
  "zone de bruit" : ouverture (ou cloture de la veille) +/- mouvement moyen des 14 dernieres seances a
  cette minute (seances completes seulement, veille = derniere seance complete du meme contrat). Au-dessus : achat ; en dessous : vente ; sortie si le prix repasse la limite ou le prix
  moyen du jour (VWAP) ; tout est ferme a 16 h. Frais : 1,5 point de NQ par aller-retour.
- taille : nombre de MNQ = 0,15 x coussin / ecart-type des gains des 60 dernieres seances (1 MNQ),
  coussin = solde - limite de perte, arrondi en dessous, AU MOINS 1 MNQ (depuis le 1er octobre 2026 : avant, le compte
  tombait a 0 MNQ sous environ 1 400 $ de coussin et restait gele). Plus le compte s'approche de la limite, plus il reduit.
- challenge Phidias 50K Fundamental (regles publiques d'octobre 2026, a verifier ; zone_retrait/ sur la branche de
  recherche) : +4 000 $ a atteindre, perte max 2 500 $ sous le plus haut de fin de journee, 164 $ le challenge.
  Compte finance : limite bloquee a 50 100 $ quand le solde atteint 52 600 $ ; retrait possible apres 10 jours
  qualifiants (au moins +150 $) depuis le dernier retrait, de ce qui depasse 52 600 $ (+ MARGE_RETRAIT), 500 $ minimum
  et 2 000 $ maximum, si la meilleure journee <= 30 % du gain depuis le dernier retrait ; 80 % du retrait pour toi.
  Un compte perdu est remplace par un nouveau challenge le lendemain.

Depuis le 2 octobre 2026, le filtre order flow H1 (delta des 30 minutes avant chaque signal, transactions Databento,
budget 1 $ par mois) est mesure sur chaque trade de zone et suivi a part (filtre_delta.csv, fonction filtre_delta).

Chaque matin de semaine (GitHub Actions ; les barres minute historiques de Databento arrivent environ 8 heures apres
la seance) : telecharge les barres minute NQ (secret DATABENTO_API_KEY), rejoue la seance de la veille, met a jour
zone/robot/ et envoie un resume Telegram. Aucun ordre reel.
Ce suivi se fait apres la cloture : pour trader en vrai, il faudrait les signaux en direct toutes les 30 minutes.

Rejeu hors ligne : ROBOT_MINUTES=chemin/nasdaq100_1min.csv.gz ROBOT_DEBUT=2025-01-02 ROBOT_JUSQU_AU=2025-12-31 \
                   ROBOT_DOSSIER=/tmp/zone python3 zone/robot.py
"""
import json
import os
import re
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
F_CHALLENGE, F_AVANT, F_APRES = 0.15, 0.15, 0.15   # f du challenge, du compte finance avant puis apres le blocage de la limite
MIN_MNQ, MAX_MNQ = 1, 50               # au moins 1 MNQ depuis le 1er octobre 2026 (sinon le compte se gelait a 0)
CAPITAL, OBJECTIF, PERTE = 50_000.0, 4_000.0, 2_500.0
BLOCAGE, SEUIL_RETRAIT, PART, PRIX_CHALLENGE = 50_100.0, 52_600.0, 0.80, 164.0
JOURS_QUALIF, GAIN_QUALIF, RETRAIT_MIN, RETRAIT_MAX, REGULARITE = 10, 150.0, 500.0, 2_000.0, 0.30
MARGE_RETRAIT = 0.0                     # marge gardee en plus des 52 600 $ apres un retrait
PLAFOND_DATABENTO = 2.0                 # $ au maximum par telechargement
FICHIER_CHAT = Path(__file__).resolve().parent.parent / ".telegram_chat"   # conversation Telegram (jamais commitee)
REFERENCE = Path(__file__).parent / "tableau" / "reference.json"         # rejeu 2023-2026 pour 1 MNQ (zone/tableau/)
BILANS = (60, 120)                      # seances apres lesquelles on juge le virtuel (zone/README.md, 1er octobre 2026)
DEBUT_RSI2 = os.getenv("ROBOT_DEBUT_RSI2", "2026-10-01")   # RSI(2) dans le compte : decisions a partir de cette date
RISQUE_RSI2_REF = 233.19                # ecart-type d'un jour en position, 1 MNQ, 2011-2022 (tournoi8/ sur la recherche)
DEBUT_FILTRE = os.getenv("ROBOT_DEBUT_FILTRE", "2026-10-01")   # filtre order flow H1 : trades mesures a partir de cette date
FILTRE = DOSSIER / "filtre_delta.csv"
SECOURS = DOSSIER / "secours_yahoo.json"
# bot 3 en 1 (zone filtree par le delta H1 + RSI(2)), demande de l'utilisateur du 2 octobre 2026 : son propre challenge
DEBUT_COMBINE = os.getenv("ROBOT_DEBUT_COMBINE", "2026-10-02")    # premiere seance jouee
ETAT_C, JOURNAL_C = DOSSIER / "etat_combine.json", DOSSIER / "journal_combine.csv"
TAILLE_COMBINE = 1                       # MNQ par source, fixe (choix de l'utilisateur)
# pas d'approximation du delta : rejouee d'avril a septembre 2026, l'approximation par le mouvement du prix faisait perdre le
# challenge le 29 juillet (elle ratait les trades ecartes des 27 et 28 juillet). Le bot attend le vrai delta.   # seances prises chez Yahoo faute de Databento (remplacees quand il revient)
BUDGET_FILTRE_MOIS, PLAFOND_FENETRE = 1.0, 0.25   # $ par mois (accord de l'utilisateur, 2 octobre 2026) ; $ par fenetre
COLONNES_FILTRE = ["date", "heure", "sens", "achats", "ventes", "delta_30min", "garde", "gain_1_mnq", "cout", "mesure_le", "statut"]
MOTIF_ZONE = re.compile(r"(achat|vente) (\d+)h(\d+) a ([\d,.]+) -> sortie (\d+)h(\d+) a ([\d,.]+)")
HISTORIQUE = ("rejeu de cette gestion avec les regles Phidias publiques d'octobre 2026, departs 2023-2024 suivis 24 mois "
              "(tournoi8/ et zone_deux/ sur la branche de recherche) : zone + RSI(2) environ +254 $ nets par an, rien recu dans "
              "27 % des departs ; zone seule -22 $ par an, rien recu dans 79 %. Sur 12 mois, environ -115 $ par an dans les deux "
              "cas : le premier retrait arrive en general apres 12 mois. Une taille plus grande ne fait pas mieux (zone_deux/)")


# ----------------------------------------------------------------------------- donnees
def telecharger():
    """Ajoute les seances manquantes (Databento, NQ.v.0, barres d'une minute de 9 h 30 a 16 h)."""
    import databento as db
    ancien = pd.read_csv(MINUTES) if MINUTES.exists() else None
    debut = ancien["t"].str[:10].max() if ancien is not None else str((pd.Timestamp.now() - pd.Timedelta(days=200)).date())
    if SECOURS.exists():                    # seances venues de Yahoo pendant une panne : Databento les remplace
        debut = min(debut, json.loads(SECOURS.read_text())["premier_jour"])
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
    SECOURS.unlink(missing_ok=True)
    print(f"Databento : {len(neuf)} minutes du {debut} au {fin[:16]} ({cout:.3f} $)")


def contrat_nq(jour):
    """Contrat que suit NQ.v.0 chez Databento un jour donne : changement le mercredi avant le 3e vendredi de mars, juin,
    septembre et decembre (regle observee de 2024 a 2026). Renvoie (symbole Yahoo, annee, mois d'echeance)."""
    d = pd.Timestamp(jour).normalize()
    for a in (d.year, d.year + 1):
        for mo in (3, 6, 9, 12):
            premier = pd.Timestamp(a, mo, 1)
            vendredi3 = premier + pd.Timedelta(days=(4 - premier.weekday()) % 7 + 14)
            if vendredi3 - pd.Timedelta(days=2) > d:
                return f"NQ{'HMUZ'[mo // 3 - 1]}{a % 100:02d}.CME", a, mo


def telecharger_yahoo():
    """Secours quand Databento refuse : barres d'une minute du contrat en cours chez Yahoo (7 derniers jours ; pas de
    delta, donc pas de filtre H1). Les seances ainsi ajoutees sont notees dans SECOURS ; Databento les remplace des
    qu'il repond. Renvoie le nombre de minutes ajoutees."""
    import yfinance as yf
    ancien = pd.read_csv(MINUTES)
    debut = ancien["t"].str[:10].max()      # la derniere seance enregistree est reprise (peut-etre incomplete)
    sym = contrat_nq(pd.Timestamp.now(tz="America/New_York").tz_localize(None))[0]
    df = pd.DataFrame()
    for s in (sym, "NQ=F"):                 # le contrat precis d'abord, sinon le contrat continu de Yahoo
        df = yf.download(s, interval="1m", period="7d", progress=False, auto_adjust=False)
        if not df.empty:
            break
    if df.empty:
        raise RuntimeError("Yahoo ne renvoie aucune barre")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    t = pd.DatetimeIndex(df.index)
    t = (t.tz_localize("UTC") if t.tz is None else t).tz_convert("America/New_York")
    minute = t.hour * 60 + t.minute
    jour = t.strftime("%Y-%m-%d")
    garde = (minute >= 570) & (minute < 960) & (t.dayofweek < 5) & (jour >= debut)
    if not garde.any():
        return 0
    # numero de contrat : celui de Databento tant que l'echeance est la meme, sinon un numero propre a l'echeance
    ref = contrat_nq(ancien["t"].iloc[-1][:10])[1:]
    ref_id = int(ancien["contrat"].iloc[-1])
    ids = [ref_id if contrat_nq(j)[1:] == ref else 900_000 + contrat_nq(j)[1] * 100 + contrat_nq(j)[2] for j in jour[garde]]
    neuf = pd.DataFrame({"t": t[garde].strftime("%Y-%m-%d %H:%M"), "o": df["Open"].to_numpy(float)[garde],
                         "h": df["High"].to_numpy(float)[garde], "l": df["Low"].to_numpy(float)[garde],
                         "c": df["Close"].to_numpy(float)[garde], "v": df["Volume"].fillna(0).to_numpy()[garde].astype("int64"),
                         "contrat": ids}).dropna()
    tout = pd.concat([ancien[ancien["t"].str[:10] < debut], neuf], ignore_index=True)
    tout = tout.drop_duplicates("t", keep="last").sort_values("t").reset_index(drop=True)
    tout.to_csv(MINUTES, index=False, float_format="%.2f", compression={"method": "gzip", "mtime": 0})
    premier = json.loads(SECOURS.read_text())["premier_jour"] if SECOURS.exists() else debut
    SECOURS.write_text(json.dumps({"premier_jour": min(premier, debut), "symbole": s}))
    print(f"Yahoo (secours) : {len(neuf)} minutes depuis le {debut} ({s})")
    return len(neuf)


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


def seances_completes(P):
    """Seances completes : premiere et derniere minute presentes et au moins 370 minutes sur 390."""
    return P[:, 0] & P[:, N - 1] & (P.sum(axis=1) >= 370)


def precedente(complete, segment=None):
    """Indice de la derniere seance complete avant chaque seance (-1 : aucune) ; avec segment, du meme contrat."""
    idx = np.where(complete, np.arange(len(complete)), -1)
    prec = np.r_[-1, np.maximum.accumulate(idx)[:-1]]
    if segment is not None:
        prec = np.where((prec >= 0) & (segment[np.maximum(prec, 0)] == segment), prec, -1)
    return prec


def zone_de_bruit(jours, O, H, L, C, P, V, echeance):
    """Zone de bruit corrigee (V1, zone_failles/journal.py zone(propre=True) sur la branche de recherche), qui note aussi
    les trades du jour. intraday/strategies.py zone_de_bruit et challenge/ restent la version d'origine (V0) : ne pas
    resynchroniser cette fonction sur eux."""
    ok = seances_completes(P)
    ouverture = O[:, 0]
    # correction V1 (zone_failles/README.md sur la branche de recherche) : les seances incompletes (feries CME,
    # demi-seances) ne servent ni a la moyenne sur 14 jours ni de veille ; veille = derniere seance complete, meme contrat
    prec = precedente(ok, np.cumsum(echeance))
    veille = np.where(prec >= 0, C[np.maximum(prec, 0), N - 1], np.nan)
    mouvement = np.abs(C / ouverture[:, None] - 1)
    sigma = np.full_like(mouvement, np.nan)
    sigma[ok] = pd.DataFrame(mouvement[ok]).rolling(JOURS_MOYENNE, min_periods=JOURS_MOYENNE).mean().shift(1).values
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


def rebond(jours, O, L, C, P):
    """Second moteur, ajoute le 1er octobre 2026 a la demande de l'utilisateur (zone_sources/ sur la branche de
    recherche, piste S4), non valide statistiquement : le suivi virtuel doit le juger. Achat de 1 MNQ a l'ouverture de
    9 h 30, sortie a la cloture (15 h 59), le lendemain d'une seance dont le mouvement ouverture -> cloture est dans les
    10 % les plus bas. Seance de reference = derniere seance complete, quel que soit le contrat (le mouvement se mesure
    dans la seance). Seuil = 10e centile des 252 valeurs precedentes de cette reference, une valeur par seance : apres une
    seance incomplete, la meme reference compte deux fois, comme dans la recherche.
    Regle executable : contrairement a la piste S4, les jours de changement de contrat ne sont pas ecartes (on ne peut pas
    les connaitre la veille) ; seuls les jours de fete et les demi-seances, connus d'avance, le sont.
    Renvoie (trades par seance, achat pour la seance suivante, mouvement de reference, seuil ou None si moins de 252
    valeurs)."""
    complete = seances_completes(P)
    prec = precedente(complete)
    mouv = C[:, N - 1] / O[:, 0] - 1
    rv = np.where(prec >= 0, mouv[np.maximum(prec, 0)], np.nan)
    v = np.isfinite(rv)
    seuil = np.full(len(jours), np.nan)
    seuil[v] = pd.Series(rv[v]).rolling(252, min_periods=252).quantile(0.1).shift(1).values
    signal = (rv <= seuil) & complete                     # NaN : pas de signal
    lignes = {jours[d]: {"brut": C[d, N - 1] - O[d, 0], "pire": min(0.0, L[d].min() - O[d, 0]), "entree": O[d, 0],
                         "sortie": C[d, N - 1]} for d in np.where(signal)[0]}
    # seance suivante : sa reference est la derniere seance complete ; son seuil, les 252 dernieres valeurs
    dernier = np.where(complete)[0][-1]
    valeurs = rv[v]
    if len(valeurs) < 252:
        return lignes, False, float(mouv[dernier]), None
    seuil_demain = float(np.quantile(valeurs[-252:], 0.1))
    return lignes, bool(mouv[dernier] <= seuil_demain), float(mouv[dernier]), seuil_demain


def feries_bourse(annees):
    """Jours feries de la Bourse de New York, avec leurs reports (comme tournoi8/tournoi8.py feries)."""
    out = set()
    for a in annees:
        def nieme(mois, jour_sem, n):
            j = pd.date_range(f"{a}-{mois:02d}-01", periods=31, freq="D")
            return j[(j.month == mois) & (j.dayofweek == jour_sem)][n]

        def reporte(d, samedi_vendredi=True):
            if d.dayofweek == 6:
                return d + pd.Timedelta(days=1)
            if d.dayofweek == 5:
                return d - pd.Timedelta(days=1) if samedi_vendredi else None
            return d
        jours = [reporte(pd.Timestamp(f"{a}-01-01"), samedi_vendredi=False), nieme(1, 0, 2), nieme(2, 0, 2),
                 GoodFriday.dates(f"{a}-01-01", f"{a}-12-31")[0], nieme(5, 0, -1), reporte(pd.Timestamp(f"{a}-07-04")),
                 nieme(9, 0, 0), nieme(11, 3, 3), reporte(pd.Timestamp(f"{a}-12-25"))]
        if a >= 2022:
            jours.append(reporte(pd.Timestamp(f"{a}-06-19")))
        out |= {d.normalize() for d in jours if d is not None}
    return out


def rsi2(jours, O, H, L, C, P, ech):
    """Second moteur DANS le compte depuis le 1er octobre 2026 (tournoi8/ sur la branche de recherche : seul survivant du
    tournoi des strategies de plusieurs jours, coffre 2023-2026 passe, independant de la zone). RSI(2) de Connors sur le
    NQ, achat seulement, 1 decision par seance 10 minutes avant la fin (15 h 50) : achat si cloture (15 h 49) > moyenne
    des 200 clotures et RSI de Wilder sur 2 clotures < 10 ; vente si cloture > moyenne des 5 clotures ; execution a
    l'ouverture de 15 h 50 ; position fermee a la derniere decision d'un contrat. Seances ignorees : jours feries de la
    Bourse, moins de 60 minutes ; la derniere seance n'est gardee que si elle est complete (ou une demi-seance connue).
    Renvoie un tableau par seance (gain, pire moment et risque pour 1 MNQ, position) et l'etat pour la prochaine decision."""
    pres = P
    derniere = N - 1 - np.argmax(pres[:, ::-1], axis=1)
    dec = derniere - 9
    fer = feries_bourse(range(pd.Timestamp(jours[0]).year - 1, pd.Timestamp(jours[-1]).year + 2))
    ok = (pres.sum(axis=1) >= 60) & pres[:, 0] & (dec >= 2) & ~pd.DatetimeIndex(jours).normalize().isin(list(fer))
    if len(ok) and not (pres[-1, N - 1] or jour_court(jours[-1])):
        ok[-1] = False                                      # derniere seance encore incomplete (delai des donnees)
    idx = np.where(ok)[0]
    if len(idx) < 205:
        return None, None
    lig = np.arange(len(jours))[idx]
    dd = dec[idx]
    Px = O[lig, dd]                                         # ouverture de la minute de decision (comblee par la cloture d'avant)
    Cx = C[lig, dd - 1]
    masque = np.arange(N)[None, :] < dd[:, None]
    Hx = np.where(masque, H[lig], -np.inf).max(axis=1)
    Lx = np.where(masque, L[lig], np.inf).min(axis=1)
    seg = np.cumsum(ech)[lig]
    roule = np.r_[seg[1:] != seg[:-1], False]               # la seance suivante est sur un autre contrat
    n = len(idx)
    m200 = pd.Series(Cx).rolling(200).mean().to_numpy()
    m5 = pd.Series(Cx).rolling(5).mean().to_numpy()
    rsi = np.full(n, np.nan)
    d = np.diff(Cx)
    gg, pp = np.maximum(d, 0), np.maximum(-d, 0)
    mg, mp = gg[:2].mean(), pp[:2].mean()
    for i in range(2, n):
        if i > 2:
            mg, mp = (mg + gg[i - 1]) / 2, (mp + pp[i - 1]) / 2
        rsi[i] = 100.0 if mp == 0 else 100 - 100 / (1 + mg / mp)
    pos = np.zeros(n, np.int8)
    tenu = False
    for t in range(n):
        if tenu and Cx[t] > m5[t]:
            tenu = False
        elif not tenu and Cx[t] > m200[t] and rsi[t] < 10:
            tenu = True
        if roule[t]:
            tenu = False
        pos[t] = tenu
    dates = pd.DatetimeIndex(jours[idx])
    actif = np.where(dates >= pd.Timestamp(DEBUT_RSI2), pos, 0)       # dans le compte : decisions depuis DEBUT_RSI2
    cote = 1.0 / PT + 0.25                                  # points par ordre : 1 $ + 1 tick de glissement
    def dollars(q):
        avant = np.r_[0, q[:-1]].astype(float)
        chg = np.abs(q - avant)
        gain = (avant * np.r_[0.0, Px[1:] - Px[:-1]] - chg * cote) * PT
        pire = np.where(avant == 1, (np.minimum(Lx, Px) - np.r_[Px[0], Px[:-1]]) * PT - chg * cote * PT, 0.0)
        return gain, np.minimum(pire, np.minimum(gain, 0.0)), avant
    gain, pire, _ = dollars(actif)
    gain_h, _, avant_h = dollars(pos.astype(np.int8))       # historique complet : sert a estimer le risque d'un MNQ
    risque = np.full(n, RISQUE_RSI2_REF)
    for k in range(n):
        x = gain_h[max(0, k - 252):k][avant_h[max(0, k - 252):k] == 1]
        if len(x) >= 20:
            risque[k] = x.std()
    tab = pd.DataFrame({"gain_rsi2": gain, "pire_rsi2": pire, "risque_rsi2": risque, "pos_rsi2": actif,
                        "prix_rsi2": Px, "mouv_rsi2": np.r_[0, np.diff(actif)]}, index=dates)
    # prochaine decision : seuils sur le prix de 15 h 49 (le RSI de Wilder ne depend que de la derniere cloture)
    def rsi_avec(x):
        dx = x - Cx[-1]
        g2, p2 = (mg + max(dx, 0)) / 2, (mp + max(-dx, 0)) / 2
        return 100.0 if p2 == 0 else 100 - 100 / (1 + g2 / p2)
    bas, haut_ = Cx[-1] * 0.5, Cx[-1] * 1.5
    if rsi_avec(bas) < 10:                                  # le RSI monte avec le prix : plus haut prix ou il reste < 10
        for _ in range(60):
            mil = (bas + haut_) / 2
            bas, haut_ = (mil, haut_) if rsi_avec(mil) < 10 else (bas, mil)
        plafond_rsi = bas
    else:
        plafond_rsi = None
    prochain = {"tenu": bool(pos[-1]), "seance": str(dates[-1].date()), "cloture": float(Cx[-1]),
                "achat_au_dessus": float(Cx[-199:].sum() / 199),                  # cloture > moyenne des 200 (avec elle)
                "achat_au_dessous": None if plafond_rsi is None else float(plafond_rsi),  # RSI(2) < 10
                "vente_au_dessus": float(Cx[-4:].sum() / 4)}                       # cloture > moyenne des 5 (avec elle)
    return tab, prochain


# ----------------------------------------------------------------------------- filtre order flow (H1)
def trades_zone_du_jour(liste):
    """Trades de la zone parmi les lignes du jour : (minute de decision depuis 9 h 30, sens, gain pour 1 MNQ en $ apres
    frais). Les lignes du rebond et du RSI(2) commencent autrement et sont ignorees."""
    out = []
    for texte in liste:
        x = MOTIF_ZONE.match(texte)
        if x:
            sens = 1 if x.group(1) == "achat" else -1
            e, s = float(x.group(4).replace(",", "")), float(x.group(7).replace(",", ""))
            out.append((int(x.group(2)) * 60 + int(x.group(3)) - 570, sens, round((sens * (s - e) - COUT) * PT, 2)))
    return out


def fenetre_delta(date, m):
    """Les 30 minutes qui finissent a la cloture de la minute de decision m (comme orderflow/signaux.py h1_filtre)."""
    fin = pd.Timestamp(f"{date} 09:30", tz="America/New_York") + pd.Timedelta(minutes=m + 1)
    return (fin - pd.Timedelta(minutes=30)).tz_convert("UTC").isoformat(), fin.tz_convert("UTC").isoformat()


def filtre_delta(trades, derniere_date):
    """Filtre order flow H1 (orderflow/ sur la branche de recherche, confirme au coffre le 2 octobre 2026 : t = 2,34) : un
    trade de zone n'est garde que si le delta (achats agressifs - ventes agressives) des 30 minutes qui finissent a la
    cloture de la minute de decision va dans son sens. Transactions Databento (schema trades, NQ.v.0), au plus
    PLAFOND_FENETRE par fenetre et BUDGET_FILTRE_MOIS par mois. Suivi a part : le compte virtuel garde la zone d'origine
    (regle de jugement inchangee). Mesure les trades de zone joues depuis DEBUT_FILTRE qui ne le sont pas encore.
    Renvoie (toutes les lignes, lignes ajoutees, nombre de trades encore a mesurer)."""
    ancien = pd.read_csv(FILTRE, dtype={"garde": str}) if FILTRE.exists() else pd.DataFrame(columns=COLONNES_FILTRE)
    deja = set(zip(ancien["date"].astype(str), ancien["heure"].astype(str)))
    a_faire = []
    for j, liste in sorted(trades.items()):
        date = str(pd.Timestamp(j).date())
        if DEBUT_FILTRE <= date <= derniere_date:
            for m, sens, gain in trades_zone_du_jour(liste):
                heure = f"{(570 + m) // 60}h{(570 + m) % 60:02d}"
                if (date, heure) not in deja:
                    a_faire.append((date, m, heure, sens, gain))
    if not a_faire:
        return ancien, [], 0
    if not (os.getenv("DATABENTO_API_KEY") or "").strip():
        print(f"Filtre delta : cle Databento absente, {len(a_faire)} trade(s) a mesurer au prochain passage")
        return ancien, [], len(a_faire)
    try:
        import databento as db
        client = db.Historical()
    except Exception as e:
        print(f"Filtre delta : Databento indisponible ({type(e).__name__}), {len(a_faire)} trade(s) a mesurer plus tard")
        return ancien, [], len(a_faire)
    maintenant = pd.Timestamp.now(tz="UTC")
    mois = maintenant.strftime("%Y-%m")
    depense = float(pd.to_numeric(ancien.loc[ancien["mesure_le"].astype(str).str[:7] == mois, "cout"], errors="coerce").sum())
    nouveaux = []
    for date, m, heure, sens, gain in a_faire:
        ligne = {"date": date, "heure": heure, "sens": "achat" if sens > 0 else "vente", "gain_1_mnq": gain,
                 "mesure_le": str(maintenant.date())}
        debut, fin = fenetre_delta(date, m)
        args = dict(dataset="GLBX.MDP3", symbols=["NQ.v.0"], stype_in="continuous", schema="trades", start=debut, end=fin)
        try:
            cout = float(client.metadata.get_cost(**args))
            if cout > PLAFOND_FENETRE or depense + cout > BUDGET_FILTRE_MOIS:
                ligne.update(cout=0.0, garde="", statut=f"non mesure : budget (deja {depense:.2f} $ ce mois, fenetre {cout:.3f} $)")
            else:
                df = client.timeseries.get_range(**args).to_df()
                depense += cout
                cote, q = df["side"].astype(str).to_numpy(), df["size"].to_numpy(np.int64)
                a, v = int(q[cote == "B"].sum()), int(q[cote == "A"].sum())     # B : acheteur agressif, A : vendeur
                if a + v == 0:
                    raise ValueError("aucune transaction dans la fenetre")
                x = (a - v) / (a + v)
                ligne.update(achats=a, ventes=v, delta_30min=round(x, 4), garde="oui" if np.sign(x) == sens else "non",
                             cout=round(cout, 4), statut="mesure")
        except Exception as e:                 # donnees pas encore publiees, reseau : nouvel essai au prochain passage
            print(f"Filtre delta {date} {heure} : pas encore mesurable ({type(e).__name__} : {str(e)[:150]})")
            if 400 <= (getattr(e, "http_status", None) or 0) < 500:      # acces refuse : inutile d'insister ce passage
                break
            continue
        nouveaux.append(ligne)
    attente = len(a_faire) - len(nouveaux)
    if nouveaux:
        tout = pd.concat([ancien, pd.DataFrame(nouveaux)], ignore_index=True).reindex(columns=COLONNES_FILTRE)
        tout = tout.sort_values(["date", "heure"], key=lambda c: c.str.zfill(5) if c.name == "heure" else c).reset_index(drop=True)
        tout.to_csv(FILTRE, index=False)
        print(f"Filtre delta : {len(nouveaux)} trade(s) mesure(s), {depense:.3f} $ depenses en {mois} (budget {BUDGET_FILTRE_MOIS:.2f} $)")
        return tout, nouveaux, attente
    return ancien, [], attente


def bilan_filtre(f):
    """Gains pour 1 MNQ depuis DEBUT_FILTRE : zone seule et zone filtree (un trade non mesure compte comme garde)."""
    if f is None or not len(f):
        return None
    garde = f["garde"].astype(str) != "non"
    mois = pd.Timestamp.now(tz="UTC").strftime("%Y-%m")
    return {"trades": int(len(f)), "ecartes": int((~garde).sum()), "non_mesures": int((f["statut"] != "mesure").sum()),
            "zone": float(f["gain_1_mnq"].sum()), "filtree": float(f.loc[garde, "gain_1_mnq"].sum()),
            "depense_mois": float(pd.to_numeric(f.loc[f["mesure_le"].astype(str).str[:7] == mois, "cout"], errors="coerce").sum())}


def texte_filtre(ligne):
    if ligne["statut"] != "mesure":
        return f"filtre delta {ligne['heure']} {ligne['sens']} : {ligne['statut']} (trade garde)"
    return (f"filtre delta {ligne['heure']} {ligne['sens']} : delta 30 min {100 * float(ligne['delta_30min']):+.1f} %"
            f" ({int(ligne['achats']):,} achats, {int(ligne['ventes']):,} ventes) -> "
            + ("GARDE" if ligne["garde"] == "oui" else f"ECARTE ({float(ligne['gain_1_mnq']):+,.0f} $ evites pour 1 MNQ)"
               if float(ligne["gain_1_mnq"]) < 0 else f"ECARTE ({float(ligne['gain_1_mnq']):+,.0f} $ manques pour 1 MNQ)"))


def serie_du_bot(minutes):
    """Gain, pire moment et risque prevu par jour pour 1 MNQ (comme challenge/bot_challenge.py donnees) : zone seule.
    La colonne rebond donne le gain du second moteur pour 1 MNQ, suivi a part : il n'entre pas dans le compte virtuel
    (rejeu 2023-2026 : avec lui, le compte finance tombait a 0 MNQ des novembre 2023)."""
    jours, O, H, L, C, P, V, ech = tableaux(minutes)
    z, trades, completes = zone_de_bruit(jours, O, H, L, C, P, V, ech)
    dollars = (z["brut"] - COUT * z["allers"]) * PT if len(z) else pd.Series(dtype=float)
    gain = dollars.reindex(completes).fillna(0)
    pire = (z["pire"] * PT).reindex(completes).fillna(0).clip(upper=0) if len(z) else gain * 0
    pire = np.minimum(pire, np.minimum(gain, 0))
    risque1 = gain.rolling(60, min_periods=40).std().shift(1)
    risque_demain = gain.rolling(60, min_periods=40).std()             # connu ce soir, utilise demain
    # second moteur (rebond), suivi a part pour 1 MNQ
    gain_rb = pd.Series(0.0, index=gain.index)
    for j, x in rebond(jours, O, L, C, P)[0].items():
        gain_rb[j] = (x["brut"] - COUT) * PT
        trades.setdefault(j, []).append(f"rebond (suivi a part, hors compte) : achat 9h30 a {x['entree']:,.2f} -> sortie 16h00"
                                        f" a {x['sortie']:,.2f}, {gain_rb[j]:+,.0f} $ pour 1 MNQ")
    d = pd.DataFrame({"gain": gain, "pire": pire, "risque1": risque1, "rebond": gain_rb})
    # second moteur dans le compte (RSI(2)) : ses jours s'ajoutent a ceux de la zone (une seance sans zone peut porter un
    # gain du RSI(2), par exemple une demi-seance tenue en position)
    r, _ = rsi2(jours, O, H, L, C, P, ech)
    if r is not None:
        d = d.join(r[["gain_rsi2", "pire_rsi2", "risque_rsi2", "pos_rsi2"]], how="outer")
        d[["gain", "pire", "rebond", "gain_rsi2", "pire_rsi2"]] = d[["gain", "pire", "rebond", "gain_rsi2", "pire_rsi2"]].fillna(0.0)
        d["risque1"] = d["risque1"].ffill()
        d["risque_rsi2"] = d["risque_rsi2"].ffill().fillna(RISQUE_RSI2_REF)
        d["pos_rsi2"] = d["pos_rsi2"].ffill().fillna(0).astype(int)
        for j, x in r[r["mouv_rsi2"] != 0].iterrows():
            trades.setdefault(j, []).append(f"RSI(2) : {'achat' if x['mouv_rsi2'] > 0 else 'vente'} 15h50 a {x['prix_rsi2']:,.2f}"
                                            + (f" ({x['gain_rsi2']:+,.0f} $ ce jour pour 1 MNQ)" if x["mouv_rsi2"] < 0 else ""))
    else:
        d = d.assign(gain_rsi2=0.0, pire_rsi2=0.0, risque_rsi2=RISQUE_RSI2_REF, pos_rsi2=0)
    d = d.dropna()
    return d, trades, jours, float(risque_demain.iloc[-1]) if len(risque_demain) else float("nan")


def niveaux(minutes, r):
    """Niveaux pour la prochaine seance (a utiliser en direct, par exemple avec zone/tradingview/zone_de_bruit.pine) :
    cloture de la veille, mouvement moyen des 14 dernieres seances a chaque controle, taille conseillee."""
    jours, O, H, L, C, P, V, ech = tableaux(minutes)
    if not (P[-1, 0] and P[-1, N - 1]) and not jour_court(jours[-1]):
        jours, O, H, L, C, P, ech = jours[:-1], O[:-1], H[:-1], L[:-1], C[:-1], P[:-1], ech[:-1]   # derniere seance encore incomplete (delai des donnees) : ecartee
    ctrl = list(range(PAS, N, PAS))
    # correction V1 : seules les seances completes comptent (moyenne sur 14 jours et veille)
    complete = seances_completes(P)
    if complete.sum() < JOURS_MOYENNE:
        return None
    Cc, Oc = C[complete], O[complete]
    # meme contrat (comme le backtest V1) : si le contrat a change depuis la derniere seance complete (par exemple une
    # demi-seance qui est aussi le premier jour du nouveau contrat), il n'y a pas de veille valable : pas de trade
    segment = np.cumsum(ech)
    changement = segment[np.where(complete)[0][-1]] != segment[-1]
    sigma = np.abs(Cc[-JOURS_MOYENNE:, :] / Oc[-JOURS_MOYENNE:, :1] - 1)[:, ctrl].mean(axis=0)
    prochaine = pd.Timestamp(jours[-1]) + pd.Timedelta(days=1)
    while jour_ferme(prochaine):
        prochaine += pd.Timedelta(days=1)
    court = jour_court(prochaine)
    raison = "fete ou demi-seance" if court else ("changement de contrat depuis la derniere seance complete" if changement else "")
    heures = []
    for m, sg in zip(ctrl, sigma):
        t_ny = pd.Timestamp(prochaine.date()).tz_localize("America/New_York") + pd.Timedelta(minutes=570 + m)
        heures.append({"ny": t_ny.strftime("%Hh%M"), "paris": t_ny.tz_convert("Europe/Paris").strftime("%Hh%M"), "sigma": float(sg)})
    ok = np.isfinite(r) and r > 0
    taille = lambda c, f: int(np.clip(np.floor(f * c / r), MIN_MNQ, MAX_MNQ)) if ok else 0
    _, rb_demain, rb_mouv, rb_seuil = rebond(jours, O, L, C, P)
    _, rs = rsi2(jours, O, H, L, C, P, ech)
    return {"seance": str(prochaine.date()), "jour_court": court, "pas_de_trade": bool(raison), "raison": raison,
            "rsi2": rs,
            "rebond": {"achat": bool(rb_demain and not court), "mouvement_veille": rb_mouv, "seuil": rb_seuil},
            "veille": None if changement else float(Cc[-1, N - 1]), "controles": heures,
            "risque_1_mnq": r if ok else None,
            "tailles": {f"{f:.2f}": {"Phidias (coussin 2 500 $)": taille(2500, f), "Topstep (coussin 2 000 $)": taille(2000, f)}
                        for f in (0.15, 0.25, 0.35)}}


# ----------------------------------------------------------------------------- comptes virtuels
def nouveau_challenge(etat, date):
    etat["tentatives"].append({"numero": len(etat["tentatives"]) + 1, "debut": date, "fin": None, "issue": "en cours"})
    etat.update(phase="challenge", solde=CAPITAL, haut=CAPITAL, meilleur=0.0, gain_periode=0.0, jours_finance=0, jours_qualifies=0)


def lire_etat(d):
    if ETAT.exists():
        return json.loads(ETAT.read_text())
    debut = pd.Timestamp(os.getenv("ROBOT_DEBUT") or d.index[-1])
    derniere = d.index[d.index <= debut][-1] if (d.index <= debut).any() else d.index[0] - pd.Timedelta(days=1)
    etat = {"debut": str(derniere.date()), "derniere_date": str(derniere.date()), "tentatives": [], "recu_total": 0.0,
            "gain_1_mnq": 0.0}
    nouveau_challenge(etat, None)          # la date de debut est celle de la premiere seance jouee
    return etat


def une_journee(etat, x, date, fixe=None):
    """Joue une seance sur le compte virtuel (challenge ou finance). Renvoie la ligne du journal. fixe : nombre de MNQ
    par source impose (bot 3 en 1) au lieu de la taille selon le coussin."""
    finance = etat["phase"] == "finance"
    if etat["tentatives"][-1]["debut"] is None:
        etat["tentatives"][-1]["debut"] = date
    haut = etat["haut"]
    plancher = (BLOCAGE if haut >= SEUIL_RETRAIT else haut - PERTE) if finance else haut - PERTE
    f = (F_APRES if haut >= SEUIL_RETRAIT else F_AVANT) if finance else F_CHALLENGE
    coussin = etat["solde"] - plancher
    deux = date >= DEBUT_RSI2                                # deux sources : chacune f x coussin / racine(2)
    ks = np.sqrt(2.0) if deux else 1.0
    n = int(np.clip(np.floor(f * coussin / ks / x["risque1"]), MIN_MNQ, MAX_MNQ)) if x["risque1"] > 0 else MIN_MNQ
    n = fixe or n
    jour, creux = n * x["gain"], n * x["pire"]
    g2 = float(x.get("gain_rsi2", 0.0)) if deux else 0.0
    n2 = 0
    if deux:
        r2 = float(x.get("risque_rsi2", RISQUE_RSI2_REF))
        n2 = fixe or (int(np.clip(np.floor(f * coussin / ks / r2), MIN_MNQ, MAX_MNQ)) if r2 > 0 else MIN_MNQ)
        jour, creux = jour + n2 * g2, creux + n2 * float(x.get("pire_rsi2", 0.0))
    ligne = {"date": date, "phase": etat["phase"], "tentative": etat["tentatives"][-1]["numero"], "mnq": n,
             "gain": round(jour, 2), "gain_1_mnq": round(x["gain"], 2), "gain_rebond_1_mnq": round(x["rebond"], 2),
             "retrait": 0.0, "mnq_rsi2": n2 if g2 != 0 or x.get("pos_rsi2", 0) else 0, "gain_rsi2_1_mnq": round(g2, 2)}
    etat["gain_1_mnq"] += x["gain"]
    etat["gain_rsi2_1_mnq"] = etat.get("gain_rsi2_1_mnq", 0.0) + g2
    etat["gain_rebond_1_mnq"] = etat.get("gain_rebond_1_mnq", 0.0) + x["rebond"]
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
        etat.update(phase="finance", solde=CAPITAL, haut=CAPITAL, meilleur=0.0, gain_periode=0.0, jours_finance=0, jours_qualifies=0)
    elif finance:
        etat["jours_finance"] += 1
        etat["meilleur"], etat["gain_periode"] = max(etat["meilleur"], jour), etat["gain_periode"] + jour
        etat["jours_qualifies"] = etat.get("jours_qualifies", 0) + int(jour >= GAIN_QUALIF)
        retrait = min(RETRAIT_MAX, etat["solde"] - SEUIL_RETRAIT - MARGE_RETRAIT)
        if (etat["jours_qualifies"] >= JOURS_QUALIF and retrait >= RETRAIT_MIN and etat["gain_periode"] > 0
                and etat["meilleur"] <= REGULARITE * etat["gain_periode"]):
            etat["recu_total"] += PART * retrait
            etat["solde"] -= retrait
            etat["meilleur"], etat["gain_periode"], etat["jours_qualifies"] = 0.0, 0.0, 0
            ligne.update(retrait=round(PART * retrait, 2), evenement=f"RETRAIT virtuel : {PART * retrait:,.0f} $ pour toi")
    ligne.setdefault("solde", round(etat["solde"], 2))
    return ligne


def jouer_combine(d, trades, filtre):
    """Bot 3 en 1 : zone de bruit filtree par le delta des 30 minutes (H1) + RSI(2), TAILLE_COMBINE MNQ chacun, sur son
    propre challenge 50K virtuel depuis DEBUT_COMBINE. Le delta est TOUJOURS le vrai (transactions Databento,
    filtre_delta.csv) : une seance dont un trade de zone n'est pas encore mesure attend, et les suivantes aussi (le compte
    se joue dans l'ordre). Quand Databento revient, filtre_delta mesure les trades en retard et le bot rattrape tout seul.
    Les jours ou le filtre ecarte des trades, le creux du jour est approche par min(0, gain des trades gardes).
    Renvoie (etat, lignes jouees, seances en attente)."""
    if ETAT_C.exists():
        etat = json.loads(ETAT_C.read_text())
    else:
        etat = {"debut": DEBUT_COMBINE, "derniere_date": str((pd.Timestamp(DEBUT_COMBINE) - pd.Timedelta(days=1)).date()),
                "tentatives": [], "recu_total": 0.0, "gain_1_mnq": 0.0}
        nouveau_challenge(etat, None)
    mesures = {}
    if filtre is not None and len(filtre):
        mesures = {(str(r["date"]), str(r["heure"])): r for r in filtre.to_dict("records")}
    jours = [j for j in d.index if j > pd.Timestamp(etat["derniere_date"]) and str(j.date()) >= DEBUT_COMBINE]
    lignes, attente = [], 0
    for k, j in enumerate(jours):
        date, x = str(j.date()), d.loc[j]
        zt = trades_zone_du_jour(trades.get(j, []))
        gain, ecartes, forces, complet = 0.0, 0, 0, True
        for m, sens, g in zt:
            r = mesures.get((date, f"{(570 + m) // 60}h{(570 + m) % 60:02d}"))
            if r is None:
                complet = False
                break
            if str(r.get("garde")) == "non":
                ecartes += 1
            else:
                gain += g
        if not complet:
            attente = len(jours) - k
            break
        y = {"gain": gain, "pire": float(x["pire"]) if not ecartes else min(0.0, gain), "risque1": float(x["risque1"]),
             "rebond": 0.0, "gain_rsi2": float(x.get("gain_rsi2", 0.0)), "pire_rsi2": float(x.get("pire_rsi2", 0.0)),
             "risque_rsi2": float(x.get("risque_rsi2", RISQUE_RSI2_REF)), "pos_rsi2": int(x.get("pos_rsi2", 0))}
        ligne = une_journee(etat, y, date, fixe=TAILLE_COMBINE)
        ligne.update(trades_zone=len(zt), trades_ecartes=ecartes, non_mesures=forces)
        etat["non_mesures"] = etat.get("non_mesures", 0) + forces
        lignes.append(ligne)
        etat["derniere_date"] = date
    return etat, lignes, attente


def texte_combine(etat, attente):
    plancher = (BLOCAGE if etat["haut"] >= SEUIL_RETRAIT else etat["haut"] - PERTE) if etat["phase"] == "finance" else etat["haut"] - PERTE
    t = etat["tentatives"][-1]
    return (f"Bot 3 en 1 (zone filtree par le delta + RSI(2), {TAILLE_COMBINE} MNQ chacun, depuis le {etat['debut']}) : "
            + (f"challenge n°{t['numero']}, {etat['solde'] - CAPITAL:+,.0f} $ sur +4 000 $" if etat["phase"] == "challenge"
               else f"compte finance, solde {etat['solde']:,.0f} $, recu {etat['recu_total']:,.0f} $")
            + f", marge avant la limite {etat['solde'] - plancher:,.0f} $"
            + (f" ; EN PAUSE : {attente} seance(s) en attente du vrai delta (transactions Databento indisponibles ; le bot rattrapera"
               " tout seul quand elles reviendront)" if attente else ""))


# ----------------------------------------------------------------------------- sorties
def tableau(etat, journal, trades_du_jour, niv=None, filtre=None, combine=None):
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
        *([f"{v['texte']}.", ""] if (v := voyant(journal)) else []),
        "| Mesure | Valeur |",
        "|---|---|",
        f"| Tentatives de challenge | {len(etat['tentatives'])} ("
        + ", ".join(f"n°{x['numero']} {x['issue']}" for x in etat["tentatives"]) + ") |",
        f"| Recu en retraits virtuels (80 %) | {etat['recu_total']:,.0f} $ |",
        f"| Gain de la strategie pour 1 MNQ depuis le depart | {etat['gain_1_mnq']:+,.0f} $ |",
        f"| RSI(2) (second moteur, dans le compte depuis le 1er octobre 2026) pour 1 MNQ | {etat.get('gain_rsi2_1_mnq', 0.0):+,.0f} $ |",
        f"| Rebond (suivi a part, hors compte) pour 1 MNQ depuis le 1er octobre 2026 | {etat.get('gain_rebond_1_mnq', 0.0):+,.0f} $ |",
        "",
    ]
    if trades_du_jour:
        lignes += [f"## Trades du {etat['derniere_date']}", ""] + [f"- {x}" for x in trades_du_jour] + [""]
    if niv and niv["pas_de_trade"]:
        lignes += [f"## Seance du {niv['seance']} : {niv['raison']}, PAS DE TRADE", "",
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
                    + f"{niv['risque_1_mnq']:,.0f}, arrondi en dessous, au moins 1 MNQ** (exemple : f = 0,25, coussin 1 500 $ -> "
                    + f"{max(MIN_MNQ, int(np.floor(0.25 * 1500 / niv['risque_1_mnq'])))} MNQ).") if niv["risque_1_mnq"] else
                   "Taille : pas encore assez d'historique (40 seances).", "",
                   "Le VWAP est celui de la seance americaine, calcule depuis 9 h 30 (pas depuis la reouverture de 18 h). "
                   "On ne regarde le prix qu'aux heures de controle : pas de stop place dans le marche.", ""]
    if niv and "rsi2" in niv:
        lignes += ["## Second moteur dans le compte : RSI(2) sur le NQ (depuis le 1er octobre 2026)", "",
                   texte_rsi2(niv["rsi2"], niv["seance"]), "",
                   "Regle (tournoi8/ sur la branche de recherche) : achat a 15 h 50 si la cloture de 15 h 49 est au-dessus de la"
                   " moyenne des 200 clotures et si le RSI de Wilder sur 2 clotures est sous 10 ; vente a 15 h 50 quand la cloture"
                   " depasse la moyenne des 5. Position gardee la nuit et le week-end. Taille : comme la zone, f x coussin / racine(2),"
                   " au moins 1 MNQ. Seul survivant du tournoi des strategies de plusieurs jours ; independant de la zone.", ""]
    if combine is not None:
        ec, jc, att = combine
        lignes += ["## Bot 3 en 1 : zone filtree par le delta + RSI(2), 1 MNQ chacun (challenge 50K virtuel a part)", "",
                   f"**{texte_combine(ec, att)}.**", "",
                   "Demande de l'utilisateur du 2 octobre 2026 : la zone de bruit ne garde que les trades dont le delta des 30"
                   " minutes va dans leur sens, plus le RSI(2), 1 MNQ chacun, taille fixe. Rejeu d'avril a septembre 2026 (mois ou le"
                   " filtre a ete trouve, donc flatteur) : challenge reussi en 3 a 4 mois selon le mois de depart, marge la plus"
                   " basse 414 $ le 29 juillet 2026. Le bot n'utilise que le vrai delta (transactions Databento) : sans lui, il se met"
                   " en pause et rattrape quand les donnees reviennent. Une approximation par le prix aurait fait perdre le challenge"
                   " le 29 juillet.", ""]
        if len(jc):
            lignes += ["| Date | Phase | Resultat du jour | Solde | Zone gardee (1 MNQ) | Trades ecartes | RSI(2) (1 MNQ) | Evenement |",
                       "|---|---|---|---|---|---|---|---|",
                       *[f"| {r.date} | {r.phase} n°{r.tentative} | {r.gain:+,.0f} $ | {r.solde:,.0f} $ | {r.gain_1_mnq:+,.0f} $ |"
                         f" {int(r.trades_ecartes)}/{int(r.trades_zone)} | {float(r.gain_rsi2_1_mnq):+,.0f} $ |"
                         f" {r.evenement if isinstance(r.evenement, str) else ''} |" for r in jc.tail(10).iloc[::-1].itertuples()], ""]
    bf = bilan_filtre(filtre)
    lignes += ["## Filtre order flow (H1) : delta des 30 dernieres minutes (suivi a part)", "",
               "Un trade de zone n'est garde que si le delta (achats agressifs - ventes agressives) des 30 minutes qui finissent"
               " a la minute du signal va dans son sens. Confirme au coffre le 2 octobre 2026 (orderflow/ sur la branche de"
               " recherche : trades gardes +67 points, ecartes -35 points, t = 2,34), mais sur peu de trades ecartes (20 en 6 mois)."
               " Sur 15 ans, une approximation gratuite du delta (mouvement du prix sur 30 min) ne le confirme pas : effet faible, t = 1,62"
               " (filtre_h1/ sur la recherche). Suivi ici a part, le compte virtuel garde la zone d'origine. **En direct : a chaque signal de la zone, regarder le"
               " delta cumule des 30 dernieres minutes sur ta plateforme ; s'il va contre le trade, ne pas le prendre.**", ""]
    if bf:
        lignes += [f"Depuis le {DEBUT_FILTRE} : zone seule {bf['zone']:+,.0f} $ pour 1 MNQ, zone filtree **{bf['filtree']:+,.0f} $**"
                   f" ({bf['trades']} trades, {bf['ecartes']} ecartes" + (f", {bf['non_mesures']} non mesures" if bf["non_mesures"] else "")
                   + f"). Donnees du filtre ce mois : {bf['depense_mois']:.2f} $ sur {BUDGET_FILTRE_MOIS:.2f} $.", "",
                   "| Date | Heure | Sens | Delta 30 min | Decision | Trade pour 1 MNQ |", "|---|---|---|---|---|---|",
                   *[f"| {r.date} | {r.heure} | {r.sens} | "
                     + (f"{100 * float(r.delta_30min):+.1f} % | " + ("garde" if r.garde == "oui" else "ecarte") if r.statut == "mesure"
                        else f"- | {r.statut}")
                     + f" | {float(r.gain_1_mnq):+,.0f} $ |" for r in filtre.tail(12).iloc[::-1].itertuples()], ""]
    else:
        lignes += [f"Pas encore de trade de zone mesure depuis le {DEBUT_FILTRE}.", ""]
    if niv and niv.get("rebond"):
        rb = niv["rebond"]
        seuil = f"{rb['seuil']:+.2%}" if rb["seuil"] is not None else "pas encore assez d'historique (252 seances)"
        lignes += ["## Second moteur : rebond apres forte baisse (suivi a part, hors compte)", "",
                   (f"**ACHAT le {niv['seance']} a l'ouverture de 9 h 30, sortie a 15 h 59** (1 MNQ, suivi a part, hors compte"
                    " de challenge ; meme un jour de changement de contrat)." if rb["achat"] else f"Pas d'achat le {niv['seance']}.")
                   + f" Derniere seance complete : {rb['mouvement_veille']:+.2%} (ouverture -> cloture) ; seuil des 10 % les plus bas :"
                   + f" {seuil}. Ajoute le 1er octobre 2026 a la demande de l'utilisateur. Non valide statistiquement : ses gains"
                   + " passes viennent surtout de deux krachs (2020 et 2025) ; voir zone/README.md.", ""]
    lignes += ["## Derniers jours", "", "| Date | Phase | MNQ zone | RSI(2) MNQ | Resultat du jour | Solde | Zone pour 1 MNQ |"
               " RSI(2) pour 1 MNQ | Rebond (a part, 1 MNQ) | Evenement |",
               "|---|---|---|---|---|---|---|---|---|---|",
               *[f"| {r.date} | {r.phase} n°{r.tentative} | {r.mnq} | {int(getattr(r, 'mnq_rsi2', 0) or 0)} | {r.gain:+,.0f} $ | {r.solde:,.0f} $ |"
                 f" {r.gain_1_mnq:+,.0f} $ | {float(getattr(r, 'gain_rsi2_1_mnq', 0.0) or 0.0):+,.0f} $ |"
                 f" {getattr(r, 'gain_rebond_1_mnq', 0.0):+,.0f} $ | {r.evenement if isinstance(r.evenement, str) else ''} |"
                 for r in j.itertuples()], ""]
    TABLEAU.write_text("\n".join(lignes))


def chat_telegram(jeton):
    """Conversation Telegram ou envoyer le resume : secret CHAT_ID s'il existe ; sinon celle gardee par un passage
    precedent (fichier .telegram_chat, conserve par le cache de GitHub Actions, jamais commite ni affiche) ; sinon la
    premiere conversation privee qui a ecrit au bot (getUpdates : messages des dernieres 24 heures). Une fois trouvee,
    elle est gardee : un inconnu qui ecrirait ensuite au bot ne la remplace pas."""
    chat = (os.getenv("CHAT_ID") or "").strip()
    if chat:
        return chat
    if FICHIER_CHAT.exists() and FICHIER_CHAT.read_text().strip():
        return FICHIER_CHAT.read_text().strip()
    try:
        rep = requests.get(f"https://api.telegram.org/bot{jeton}/getUpdates", timeout=20)
    except requests.RequestException as e:
        print(f"Erreur Telegram (recherche de la conversation) : {type(e).__name__}")
        return None
    if not rep.ok:
        print(f"Erreur Telegram {rep.status_code} (recherche de la conversation) : {rep.text[:200]}")
        return None
    for u in rep.json().get("result", []):
        for cle in ("message", "edited_message", "my_chat_member"):
            c = (u.get(cle) or {}).get("chat") or {}
            if c.get("type") == "private" and c.get("id"):
                FICHIER_CHAT.write_text(str(c["id"]))
                print("(Telegram : conversation trouvee, gardee pour les prochains envois)")
                return str(c["id"])
    print("(Telegram : le bot n'a recu aucun message depuis 24 h. Envoie-lui un message sur Telegram (par exemple"
          " /start) : le prochain passage trouvera la conversation tout seul)")
    return None


def voyant(journal, nouveaux=1):
    """Regle de jugement du virtuel (zone/README.md, fixee le 1er octobre 2026) : gain cumule pour 1 MNQ depuis le depart
    compare a la fourchette du backtest apres n seances, moyenne x n - z x ecart-type x racine(n) (comme la page) :
    vert au-dessus de la ligne des 25 %, orange entre 5 % et 25 %, rouge sous la ligne des 5 %. Aux bilans (60 puis
    120 seances) : rouge -> arreter le suivi et chercher la cause ; sinon continuer. `nouveaux` : seances jouees par ce
    passage (pour annoncer un bilan franchi pendant un rattrapage)."""
    if not REFERENCE.exists() or not len(journal):
        return None
    r = json.loads(REFERENCE.read_text())
    mu, sd = r["moyenne_zone"], r["ecart_zone"]
    gains = journal["gain_1_mnq"].to_numpy(float)

    def juger(n):
        cumul = float(gains[:n].sum())
        l5, l25 = mu * n - 1.645 * sd * n ** 0.5, mu * n - 0.674 * sd * n ** 0.5
        return cumul, l5, ("vert" if cumul >= l25 else ("orange" if cumul >= l5 else "rouge"))

    n = len(gains)
    cumul, l5, couleur = juger(n)
    v = {"seances": n, "cumul": cumul, "ligne_5": l5, "couleur": couleur, "prochain_bilan": next((b for b in BILANS if b > n), None)}
    sens = {"vert": "fourchette normale", "orange": "bas de la fourchette, arrive 1 fois sur 5 par hasard, pas une alerte",
            "rouge": "sous la ligne des 5 %, ALERTE"}[couleur]
    v["texte"] = (f"Voyant {couleur.upper()} ({sens}) : {cumul:+,.0f} $ pour 1 MNQ apres {n} seance(s) ; le backtest attendait"
                  f" {mu * n:+,.0f} $, alerte sous {l5:+,.0f} $ (ligne des 5 %)")
    for b in BILANS:
        if b <= n:
            cb, lb, kb = juger(b)
            nouveau = "BILAN" if n - nouveaux < b else "Bilan"
            v["texte"] += (f". {nouveau} des {b} seances ({journal['date'].iloc[b - 1]}) : {cb:+,.0f} $ contre {lb:+,.0f} $ -> "
                           + ("ARRETER le suivi et chercher la cause (donnees, glissement, marche change)" if kb == "rouge"
                              else "continuer, rien d'anormal"))
    if v["prochain_bilan"]:
        v["texte"] += f". Prochain bilan a {v['prochain_bilan']} seances"
    return v


def texte_rsi2(rs, seance):
    """Consigne du RSI(2) pour la prochaine decision (15 h 50 New York, 21 h 50 Paris en general)."""
    if rs is None:
        return "RSI(2) : pas encore assez d'historique (205 seances)."
    if rs["tenu"]:
        return (f"RSI(2) : EN POSITION (achat). Le {seance} a 15 h 50 New York : vente si le prix de 15 h 49 depasse"
                f" {rs['vente_au_dessus']:,.2f} (moyenne des 5 clotures) ; sinon garder. Le jour d'un changement d'echeance : vente.")
    a, b = rs["achat_au_dessus"], rs["achat_au_dessous"]
    if b is None or b <= a:
        return (f"RSI(2) : pas de position. Pas d'achat possible le {seance} (il faudrait un prix au-dessus de {a:,.2f},"
                f" moyenne des 200, et un RSI(2) sous 10" + (f", soit un prix sous {b:,.2f})." if b is not None else ")."))
    return (f"RSI(2) : pas de position. Le {seance} a 15 h 50 New York : ACHAT si le prix de 15 h 49 est entre {a:,.2f}"
            f" (moyenne des 200) et {b:,.2f} (RSI(2) sous 10), sauf jour de changement d'echeance.")

def envoyer(message):
    jeton = (os.getenv("TELEGRAM_TOKEN") or "").strip()
    print(message)
    if not jeton:
        print("(Telegram non configure : secret TELEGRAM_TOKEN absent)")
        return
    chat = chat_telegram(jeton)
    if not chat:
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
    source = ""
    if os.getenv("ROBOT_MINUTES"):
        minutes = pd.read_csv(os.getenv("ROBOT_MINUTES"))
    else:
        try:
            telecharger()
        except Exception as e:             # compte verrouille, cle refusee, panne : barres de Yahoo en secours
            raison = (str(e).strip().splitlines() or [type(e).__name__])[0][:200]
            print(f"Databento refuse le telechargement ({raison}) : secours Yahoo")
            try:
                telecharger_yahoo()
                source = f"barres Yahoo en secours (Databento refuse : {raison})"
            except Exception as e2:
                envoyer(f"Robot zone de bruit MNQ : ALERTE, Databento refuse le telechargement des barres ({raison}) et le"
                        f" secours Yahoo echoue ({type(e2).__name__} : {str(e2)[:150]}). Aucune seance ne peut etre rejouee.")
                raise SystemExit(1)
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
    filtre, filtre_neuf, filtre_attente = filtre_delta(trades, etat["derniere_date"])
    etat_c, lignes_c, attente_c = jouer_combine(d, trades, filtre)
    niv = niveaux(minutes, risque_demain)
    f_niv = DOSSIER / "niveaux.json"
    ancien_niv = json.loads(f_niv.read_text()) if f_niv.exists() else None
    if not lignes and not neuf and niv == ancien_niv and not filtre_neuf and not lignes_c:
        print(f"Pas de nouvelle seance depuis le {etat['derniere_date']} : rien a faire.")
        return
    ancien = pd.read_csv(JOURNAL) if JOURNAL.exists() else None
    journal = pd.concat([ancien, pd.DataFrame(lignes)], ignore_index=True) if ancien is not None else pd.DataFrame(lignes)
    if len(journal):
        journal["gain_rebond_1_mnq"] = journal.get("gain_rebond_1_mnq", pd.Series(0.0, index=journal.index)).fillna(0.0)
        for c in ("mnq_rsi2", "gain_rsi2_1_mnq"):
            journal[c] = journal.get(c, pd.Series(0.0, index=journal.index)).fillna(0.0)
        journal["mnq_rsi2"] = journal["mnq_rsi2"].astype(int)
        journal.to_csv(JOURNAL, index=False)
    ETAT.write_text(json.dumps(etat, indent=1, ensure_ascii=False))
    ancien_c = pd.read_csv(JOURNAL_C) if JOURNAL_C.exists() else None
    journal_c = pd.concat([ancien_c, pd.DataFrame(lignes_c)], ignore_index=True) if ancien_c is not None else pd.DataFrame(lignes_c)
    if len(journal_c):
        journal_c.to_csv(JOURNAL_C, index=False)
    ETAT_C.write_text(json.dumps(etat_c, indent=1, ensure_ascii=False))
    du_jour = list(trades.get(pd.Timestamp(etat["derniere_date"]), []))
    if len(filtre):
        du_jour += [texte_filtre(r) for r in filtre[filtre["date"].astype(str) == etat["derniere_date"]].to_dict("records")]
    if niv is not None:
        f_niv.write_text(json.dumps(niv, indent=1, ensure_ascii=False))
    tableau(etat, journal if len(journal) else pd.DataFrame(columns=["date"]), du_jour, niv, filtre, (etat_c, journal_c, attente_c))
    msg = [f"Robot zone de bruit MNQ (argent virtuel) - {etat['derniere_date']}"]
    if lignes:
        msg.append(f"Depuis le dernier message : {sum(l['gain'] for l in lignes):+,.0f} $ ({len(lignes)} seance(s)),"
                   f" {lignes[-1]['mnq']} MNQ le dernier jour")
        msg += [l["evenement"] for l in lignes if l["evenement"]]
    msg.append(f"Phase : {etat['phase']} n°{etat['tentatives'][-1]['numero']}, solde {etat['solde']:,.0f} $"
               f" ({etat['solde'] - CAPITAL:+,.0f} $), recu en tout {etat['recu_total']:,.0f} $")
    if lignes:
        msg += [f"- {x}" for x in du_jour] or ["Aucun trade le dernier jour"]
    msg.append(texte_combine(etat_c, attente_c) + "".join(f". {l['evenement']}" for l in lignes_c if l.get("evenement")))
    if source:
        msg.append(f"Donnees : {source}")
    if filtre_attente:
        msg.append(f"Filtre delta : {filtre_attente} trade(s) de zone pas encore mesure(s) (transactions Databento indisponibles)."
                   " En direct, applique le filtre a la main : delta cumule des 30 dernieres minutes dans le sens du trade")
    if (bf := bilan_filtre(filtre)) is not None:
        msg.append(f"Zone filtree par le delta 30 min (suivi a part) depuis le {DEBUT_FILTRE} : {bf['filtree']:+,.0f} $ pour 1 MNQ"
                   f" (zone seule {bf['zone']:+,.0f} $), {bf['ecartes']} trade(s) ecarte(s) sur {bf['trades']}")
    if (v := voyant(journal, len(lignes))) is not None:
        msg.append(v["texte"])
    if niv is not None and "rsi2" in niv:
        msg.append(texte_rsi2(niv["rsi2"], niv["seance"]))
    if niv is not None and niv["rebond"]["achat"]:
        msg.append(f"Rebond (suivi a part, 1 MNQ, hors compte) : ACHAT {niv['seance']} 9h30 -> 15h59"
                   f" (derniere seance {niv['rebond']['mouvement_veille']:+.2%})")
    if niv is None:
        pass
    elif niv["pas_de_trade"]:
        msg.append(f"Seance du {niv['seance']} : {niv['raison']}, PAS DE TRADE (zone)")
    else:
        msg.append(f"Seance du {niv['seance']} : veille {niv['veille']:,.2f} ; mouvements "
                   + " ".join(f"{c['paris']}:{c['sigma']:.2%}" for c in niv["controles"])
                   + f" ; compte neuf f=0,25 : {niv['tailles']['0.25']['Phidias (coussin 2 500 $)']} MNQ (Phidias)")
    envoyer("\n".join(msg))


if __name__ == "__main__":
    main()
