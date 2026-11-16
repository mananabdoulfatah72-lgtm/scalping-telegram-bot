"""Couche de risque (partie 5 de l'article) pour le compte Master Bulenox : la consigne de la prochaine seance.

Regles (usine/RISQUE.md) :
- un seul bot a la fois sur le compte : le Bot 3 en 1 chaque jour ; apres 2 seances de suite sans aucun trade, la seance
  suivante, le Supertrend NQ seul (G2 manuel) ;
- 1 MNQ ; limite de perte du jour 1 000 $ (Bot 3 en 1) et 400 $ (Supertrend) : la porte 5 et le calcul du 16 novembre
  (`config1mois`) montrent que des limites plus basses ne protegent pas et coutent du gain ;
- frein (reglage « Frein » = 750 du Bot 3 en 1) : la zone passe sur 1 MES tant que la marge est sous 1 750 $, et le secours
  Supertrend aussi (reglage « Frein : ordres sur MES », choix de l'utilisateur du 16 novembre au soir, test R) ;
- arret d'urgence si le reel s'ecarte de l'historique : gain cumule sous la ligne des 5 % de ce qu'attend l'historique
  (G2 manuel, 2015 -> derniere seance) ; ou 4 seances de suite sans trade (la 5e perd le compte) ; ou le solde sous le
  plancher.

Etat du compte : usine/compte.json, mis a jour a la main ou par un message Telegram « solde 49900 » (voir brief.py).
Journal reel : usine/journal_reel.csv (date, solde, a_trade), une ligne par seance.
Usage : KB_MINUTES=... python3 usine/consigne.py
"""
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))

FREIN, LIM_ZONE, LIM_ST, SECOURS_APRES, INACTIVITE = 1750.0, 1000.0, 400.0, 2, 5
Z_ALERTE = 1.645          # ligne des 5 %


def n(x):
    return format(x, ",.0f").replace(",", " ")


def lire_compte():
    return json.loads((ICI / "compte.json").read_text())


def lire_journal():
    f = ICI / "journal_reel.csv"
    if not f.exists():
        return []
    with open(f, encoding="utf-8") as fh:
        return [dict(date=r["date"], solde=float(r["solde"]), a_trade=r["a_trade"].strip().lower() in ("1", "oui", "true"))
                for r in csv.DictReader(fh)]


def attendu():
    """Gain moyen et ecart-type par seance de la configuration jouee (zone 1,0 / 14 jours, Supertrend 10 / 3 en secours,
    G2 manuel), 1 MNQ, sur 2015 -> derniere seance, calcules par le moteur de l'usine."""
    import donnees as Dn
    import moteur as Mo
    D = Dn.charger(); P = Mo.deriver(D)
    z = Mo.k_dollars(P["lg"], P["lb"], P["O"], P["H"], P["L"], *Mo.STRATEGIES["zone"]["f"](P, 1.0, 14), P["ok"], LIM_ZONE)
    s = Mo.k_dollars(P["lg"], P["lb"], P["O"], P["H"], P["L"], *Mo.STRATEGIES["supertrend"]["f"](P, 10, 3.0), P["ok"], LIM_ST)
    debut = int(np.searchsorted(D["J"], "2015-01-01"))
    serie, sans = [], 0
    for d in range(debut, len(D["J"])):
        g, j = (s[0][d], s[2][d]) if sans >= SECOURS_APRES else (z[0][d], z[2][d])
        serie.append(g); sans = 0 if j else sans + 1
    x = np.array(serie)
    return float(x.mean()), float(x.std(ddof=1)), len(x)


def consigne(compte, journal, moyenne, ecart):
    """La consigne de la prochaine seance, et l'etat du voyant. Renvoie (lignes, voyant)."""
    solde, haut, sans = compte["solde"], compte["plus_haut_fin_de_journee"], int(compte.get("seances_sans_trade", 0))
    plancher = min(haut - 2500.0, 50000.0); marge = solde - plancher
    L = [f"Compte : solde {n(solde)} $, plancher {n(plancher)} $, marge {n(marge)} $, {sans} seance(s) de suite sans trade."]
    voyant = "vert"
    if marge <= 0:
        return L + ["ARRET : le solde est sous le plancher, le compte est perdu."], "rouge"
    if sans >= INACTIVITE - 1:
        L.append(f"URGENT : {sans} seances sans trade. Demain, un trade est obligatoire, sinon le compte est perdu (regle d'inactivite).")
    bot = "Supertrend NQ" if sans >= SECOURS_APRES else "Bot 3 en 1"
    if bot == "Supertrend NQ":
        contrat = ("1 MES (frein actif : marge sous 1 750 $ ; coche « Frein : ordres sur MES » et choisis le symbole MES)"
                   if marge < FREIN else "1 MNQ (« Frein : ordres sur MES » decoche)")
        L.append(f"Prochaine seance : SUPERTREND NQ seul (secours apres {sans} seances sans trade). Arrete le Bot 3 en 1 avant 15 h 30 "
                 f"(Paris), lance le Supertrend NQ : {contrat}, limite du jour {n(LIM_ST)} $. Le lendemain, relance le Bot 3 en 1.")
    else:
        taille = "1 MES (frein actif : marge sous 1 750 $)" if marge < FREIN else "1 MNQ"
        L.append(f"Prochaine seance : BOT 3 EN 1, zone sur {taille}, limite du jour {n(LIM_ZONE)} $, reglage « Frein » a 750, "
                 f"« Plus haut de fin de journee deja atteint » = {n(haut)}.")
    if marge < LIM_ZONE:
        L.append(f"Attention : la marge ({n(marge)} $) est plus petite que la limite du jour : une seule mauvaise seance peut coûter "
                 f"le compte. C'est le risque accepte : une limite plus basse ne le reduit pas (calcul du 16 novembre, RISQUE.md).")
    # voyant : gain reel depuis le debut du suivi contre l'historique
    if len(journal) >= 2:
        k = len(journal) - 1
        reel = journal[-1]["solde"] - journal[0]["solde"]
        ligne5 = moyenne * k - Z_ALERTE * ecart * math.sqrt(k)
        ligne25 = moyenne * k - 0.674 * ecart * math.sqrt(k)
        if reel < ligne5:
            voyant = "rouge"
            L.append(f"VOYANT ROUGE : {n(reel)} $ en {k} seances, sous la ligne des 5 % ({n(ligne5)} $). ARRET D'URGENCE : cree le "
                     f"fichier STOP dans C:\\Bot3en1 et cherche la cause (donnees, glissement, marche qui change) avant de reprendre.")
        elif reel < ligne25:
            voyant = "orange"
            L.append(f"Voyant orange : {n(reel)} $ en {k} seances (bas de la fourchette normale, ligne des 5 % a {n(ligne5)} $).")
        else:
            L.append(f"Voyant vert : {n(reel)} $ en {k} seances (l'historique attendait {n(moyenne * k)} $ en moyenne).")
    else:
        L.append("Voyant : pas encore assez de seances reelles dans usine/journal_reel.csv.")
    return L, voyant


def principal():
    m, e, nb = attendu()
    lignes, voyant = consigne(lire_compte(), lire_journal(), m, e)
    lignes.append(f"(Historique de la configuration jouee, 2015 -> derniere seance, {nb} seances : {m:+.1f} $ par seance en moyenne, "
                  f"ecart-type {e:.0f} $.)")
    print("\n".join(lignes))
    return lignes, voyant


if __name__ == "__main__":
    principal()
