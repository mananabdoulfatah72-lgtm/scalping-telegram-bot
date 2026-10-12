#!/usr/bin/env python3
"""Second cerveau : rassemble les connaissances du depot en notes reliees (savoir.json) et assemble la page
(cerveau.html = page.html + savoir.json). Aucune cle, aucun identifiant, aucun numero de conversation n'y entre."""
import csv
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ICI = Path(__file__).resolve().parent
R0 = ICI.parent

CATS = {
    "bot": ("Le bot", "#ffc65c"),
    "recherche": ("Recherche et tournois", "#5aa8ff"),
    "prop": ("Prop firms et comptes", "#ff6fa8"),
    "robustesse": ("Robustesse et Monte Carlo", "#7be08a"),
    "flux": ("Order flow et données", "#4fe3e0"),
    "toi": ("Toi, tes objectifs, tes règles", "#b58cff"),
    "souvenir": ("Souvenirs", "#ffffff"),
}
DOSSIER_CAT = {
    "bot3en1": "bot", "protection": "bot", "filtre_h1": "bot", "zone_failles": "bot", "zone_optimisation": "bot",
    "zone_retrait": "bot", "zone_sources": "bot", "zone_taille": "bot", "zone_multi": "bot", "zone_deux": "bot",
    "orderflow": "flux", "ordres": "flux", "nuit": "flux", "lse": "flux",
    "montecarlo": "robustesse", "robustesse": "robustesse",
    "challenge": "prop", "comptes": "prop", "intraday50k": "prop", "static50k": "prop",
}
for v in range(3, 12):
    DOSSIER_CAT[f"vague{v}"] = "prop"
SECRETS = re.compile(r"(api[_ -]?key|token|password|mot de passe|chat[_ ]?id|secret)\s*[:=]\s*\S+", re.I)

# Notes ecrites a la main : l'etat du projet au 12 octobre 2026 (chiffres de la recherche).
COEUR = [
    ("bot", "Le bot 3 en 1", "Bot de futures sur le Nasdaq, codé en C# pour Quantower (compte Rithmic). Trois morceaux : la zone de bruit sur 1 MNQ, filtrée par le delta des 30 dernières minutes, et le RSI(2) de nuit sur 1 MES. Le « mode à plat » ferme tout à 16 h (New York) pour les comptes qui l'exigent comme Bulenox. Réglages Bulenox : frein 750 $, plafond 500 $/jour sur le Master, limite de perte du jour 1 050 $, pas de zone les jours de la Fed."),
    ("bot", "Zone de bruit", "Stratégie publiée par Zarattini, Aziz et Barbon (2024), paramètres de l'article. Toutes les 30 minutes de 10 h à 15 h 30 (New York), achat si le prix casse au-dessus de max(ouverture, veille) × (1 + mouvement moyen des 14 jours à cette heure), vente sous le bas symétrique. Sortie quand le prix repasse la zone ou le VWAP. Elle gagne moins d'un jour sur deux (46-49 %) mais gagne gros : +335 à +344 $ en moyenne les jours gagnants contre −165 à −190 $ les jours perdants. Elle porte 89 % du risque du bot."),
    ("bot", "Filtre delta 30 minutes", "Au signal de la zone, on regarde le delta (achats agressifs − ventes agressives) des 30 dernières minutes : s'il va contre le trade, on ne le prend pas. Avril-septembre 2026 : 99 trades, 20 écartés à −39,7 points en moyenne. Coffre août-octobre 2026 : 18 gardés à +67,4 points, 5 écartés à −35,2 points, t = 2,34. Sur 15 ans, une approximation gratuite ne le confirme pas (t = 1,62). S'il est réel, le Sharpe passe de 1,33 à 2,04. C'est la plus grosse inconnue : seulement 20 trades écartés."),
    ("bot", "RSI(2) de nuit", "Règle de Connors et Alvarez (2008) : à 15 h 50, achat si la clôture est au-dessus de la moyenne des 200 et le RSI(2) sous 10 ; vente quand la clôture passe au-dessus de la moyenne des 5. Version de nuit : 1 MES acheté à la réouverture de 18 h, revendu à 9 h 30. Environ 1 324 $ par an, Sharpe 0,90 ; il bat des nuits tirées au hasard (p ≈ 0,0003). Indépendant de la zone (corrélation 0,02)."),
    ("bot", "Protections du bot", "Frein : la zone passe sur MES (5 fois plus petit) quand le compte est 750 $ sous son plus haut de fin de journée. Plafond de gain du jour : 500 $ sur le compte Master seulement, pour respecter la règle des 40 % et retirer plus tôt. Pas de zone les jours d'annonce de la Fed (seule confluence qui a battu le hasard parmi 8 178). Limite de perte du jour : 1 050 $."),
    ("prop", "Bulenox 50K option 2", "Le compte choisi. Prix environ 19,25 $ avec code, puis 148 $ d'activation à la réussite. Challenge : objectif +3 000 $, perte max 2 500 $ sous le plus haut de fin de journée, bloquée à +100 $, limite du jour souple 1 100 $. Depuis le 17 août 2026, le challenge est un achat unique valable 30 jours seulement (reset sans prolongation) : le bot tel quel n'y valide qu'environ 5 % des challenges ; la version 30 jours (vague 12) joue taille 4 sans frein pendant le challenge. Master : retrait après 10 jours de trading, meilleur jour ≤ 40 % du gain du cycle, garder 52 600 $, retraits de 1 000 à 1 500 $ (100 % pour toi). Après 3 retraits, compte réel aux règles inconnues. Règles tirées de sites d'avis : à vérifier."),
    ("prop", "Pourquoi 3 700 $ en 24 mois", "Chiffre de l'ancien Monte Carlo, qui supposait un challenge sans limite de temps (faux depuis le 17 août 2026, voir la vague 12). Un achat Bulenox rapportait en médiane environ +3 700 $ nets en 24 mois parce que : les 8 premiers mois ne paient rien (challenge, puis coussin de 2 600 $ à construire), chaque retrait est limité à 1 500 $, et la simulation s'arrête au 3e retrait (compte réel inconnu). Maximum possible : 3 × 1 500 − 167 = 4 333 $. Pendant la phase de retraits, le rythme est d'environ 650-700 $ par mois."),
    ("prop", "Prop firms comparées", "FundedNext Legacy : validation médiane ~5 mois, retraits ~1 087 $ toutes les 1,5 mois, mais plus cher. Bulenox : le meilleur pour un budget ≤ 30 €, 1er retrait vers le mois 8. LucidFlex 100K était le meilleur compromis de la vague 8 mais trop cher. FundedNext Flex 50K : limite de 1 500 $ trop serrée pour 1 MNQ. Topstep et Tradeify ferment chaque soir (d'où le RSI(2) de nuit sur MES). Vague 12 (sans limite de temps) : FundedNext Flex 50K avec la zone sur MES valide 90 % des achats 2023-2026 avec 6 % d'achats perdants, mais coûte 69,99 $, met ~7 mois à valider et perdait 51 % des achats sur 2012-2021 ; Goat EOD valide 80 à 87 % mais lentement, compte financé non simulé."),
    ("robustesse", "Monte Carlo Bulenox", "36 000 achats simulés avec le vrai moteur du bot, 24 mois chacun, faits de vraies séances 2012-2026 tirées par mois entiers. Achats rentables : 76 % si le filtre marche comme en 2026, 62 % s'il est deux fois plus faible, 42 % sans filtre. Validation en ~4 mois. Net médian +3 709 $. Stress « 2025 » : 15 % seulement, et le résultat dépend énormément du tirage du filtre (0 à 64 %). Moteur contrôlé : 5 040 achats sur 5 040 identiques au moteur exact. ATTENTION : ces chiffres supposaient un challenge sans limite de temps. Avec la limite actuelle de 30 jours, le bot tel quel ne valide qu'environ 5 % des challenges (2 % depuis 2023)."),
    ("robustesse", "Labo de robustesse", "PBO (probabilité de suroptimisation) 30 % sur 14 400 bots, sans que le champion devienne jamais perdant. Hors échantillon : Sharpe du bot 1,29 sur 2012-2021, 1,40 sur 2023-2026. Walk-forward : ré-optimiser chaque année fait 5 829 $/an contre 6 943 $/an pour le bot fixe. 100 % des 14 400 variantes gagnent (Sharpe médian 0,98, bot au 99e centile). Zone contre pile ou face : p < 0,0001. Sharpe dégonflé 99,8 % pour la grille."),
    ("robustesse", "Ta courbe (equity curve)", "Sur 2012-2026 au prix d'aujourd'hui, sans les règles du compte : bot avec filtre simulé 9 380 $/an, Sharpe 2,04, baisse max 5 199 $, toutes les années positives (la plus faible 2016 : +1 003 $). Sans filtre : 6 499 $/an, Sharpe 1,33, baisse max 4 590 $, 2016 à −2 440 $. Mélanger l'ordre des jours donne une baisse max de 6 873 $ une fois sur 20 : prévoir plus que l'historique."),
    ("robustesse", "Suroptimisation", "Un backtest suroptimisé colle au bruit du passé et s'effondre ensuite. Défenses utilisées : règles fixées avant le calcul, jumeaux de bruit (la même recherche sur des données mélangées), coffre ouvert une seule fois, années de choix (2012-2021) séparées des années de vérification (2023-2026), PBO et Sharpe dégonflé."),
    ("robustesse", "Walk-forward et hors échantillon", "Hors échantillon : juger un réglage sur des années qui n'ont pas servi à le choisir. Walk-forward : choisir le meilleur réglage sur les années passées, le jouer la période suivante, et recommencer. Efficacité = gain hors échantillon ÷ gain dans l'échantillon. Pour le bot : 63 % avec 3 ans de passé et 12 mois de jeu."),
    ("robustesse", "Sharpe et statistiques", "Sharpe : gain moyen ÷ écart-type, annualisé ; au-dessus de 1 c'est bon. Sortino : ne compte que les baisses. Calmar : gain par an ÷ baisse max. Profit factor : dollars gagnés ÷ dollars perdus. VaR 95 % : un jour sur 20 est pire. Asymétrie positive : gains rares mais gros (signature de la zone)."),
    ("flux", "Databento", "Source des transactions du NQ (vrai delta) pour le filtre. Budget 1 $ par mois. Bloqué tant que le solde du compte Databento n'est pas réglé : le bot 3 en 1 virtuel est en pause depuis le 5 octobre 2026. Le bot C# dans Quantower calcule le vrai delta lui-même depuis le flux Rithmic, gratuitement."),
    ("flux", "Robots virtuels", "Sur la branche main, GitHub lance chaque jour : le robot zone + RSI(2) (challenge virtuel depuis le 25 septembre 2026, −81 $ après 10 séances, dans la normale du backtest), le bot 3 en 1 virtuel (en pause, attend Databento), le robot de tendance multi-marchés et le mélange 50/50. Un bilan quotidien arrive à 15 h 07 (Paris)."),
    ("toi", "Tes objectifs", "Étudiant trader en France, sans revenu. Rester sur un compte 50K, viser environ 1 % par mois (~500 €), ou 2 % tous les 2 mois, même dans les années difficiles comme 2025. Un seul achat de challenge, pas de rachat, budget ≤ 30 €. Veut des résultats vérifiés, sans fausses promesses, et des protections quand le compte perd."),
    ("toi", "Règles de sécurité", "Ne jamais écrire de clé, de jeton ou d'identifiant dans le dépôt, le chat ou ce cerveau. Les clés vivent dans les secrets GitHub. Ne jamais envoyer ses identifiants de prop firm ou de courtier. Le cerveau conseille, il ne passe jamais d'ordre et ne change pas les réglages du bot sans toi."),
    ("toi", "Prochaines étapes", "1. Finir l'essai sur la démo Optimus/Ironbeam (critères de feu vert du README de bot3en1). 2. Demander par écrit à Bulenox : le challenge Legacy à ~19 $ existe-t-il encore et dure-t-il 30 jours ; la limite du jour de 1 100 $ arrête-t-elle seulement la journée ; le trade de nuit 18 h - 9 h 30 est-il permis ; quels frais pour un bot personnel dans Quantower via Rithmic (licence Quantower payante ?). 3. Seulement si tout est oui : acheter le Legacy, régler le bot sur la version 30 jours (MNQ par source 4, frein 0), puis 1 et 750 au Master. 4. Garder 148 $ pour l'activation en cas de réussite."),
    ("prop", "Version 30 jours (vagues 12 et 13)", "Réglée avant le calcul. Pendant le challenge Bulenox : 4 MNQ, tout fermer dès que le compte touche +3 050 $ (arrêt à l'objectif), et 6 MNQ pendant les 5 dernières séances si l'objectif n'est pas atteint ; puis 1 MNQ, frein et plafond 500 $ au Master. Validé en 30 jours : 53 % (achats 2012-2021), 55 % (2023-2026), 45 % (2025), contre 41 / 40 / 32 % pour 4 MNQ seuls et 5 / 2 / 1 % pour le bot tel quel ; 49 % sans filtre delta. Presque tout le gain vient de l'arrêt à l'objectif. Net moyen d'un achat sur 24 mois : +1 552 $ (2012-2020), +2 354 $ (2023-2024) ; 38 à 55 % des achats perdent de l'argent. En 4 MNQ, 22 % des jours de trade touchent la limite de perte du jour. Labo 30 jours : labo30/."),
    ("toi", "Ton second cerveau", "Ce cerveau : chaque neurone est une note de ta recherche, reliée aux notes proches. Quand tu poses une question, il cherche les notes utiles, les allume, et Claude répond à partir d'elles. Dis « retiens que… » et il crée un nouveau neurone dans ta mémoire, privé, qui reste d'une visite à l'autre."),
]


def sans_accent(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


MOTS_VIDES = set("""le la les un une des du de d l a au aux et ou en est sont pas plus pour par sur sous avec sans que qui quoi dans
ce cette ces son sa ses leur leurs il elle ils elles on nous vous je tu se ne y si mais donc car comme tout tous toute
toutes fait faire etre avoir ete deja aussi tres bien peu entre apres avant chaque meme ainsi alors fois mois ans an jour
jours seance seances une deux trois the of and to in is for on with by from at as are be this that it""".split())


def mots(s):
    return [m for m in re.findall(r"[a-z0-9]+", sans_accent(s)) if len(m) > 2 and m not in MOTS_VIDES]


def nettoyer_md(t):
    t = re.sub(r"`([^`]*)`", r"\1", t)
    t = re.sub(r"\*\*([^*]*)\*\*", r"\1", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"^\s*[-*]\s+", "", t, flags=re.M)
    return re.sub(r"\s+", " ", t).strip()


def extrait_readme(f):
    txt = f.read_text(errors="ignore")
    lignes = txt.splitlines()
    titre = lignes[0].lstrip("# ").strip() if lignes else f.parent.name
    blocs, cour = [], []
    for l in lignes[1:]:
        if l.startswith("#") or l.startswith("|") or l.startswith("```"):
            if cour:
                blocs.append(" ".join(cour)); cour = []
            if l.startswith("#"):
                blocs.append("§" + l.lstrip("# ").strip())
            continue
        if l.strip():
            cour.append(l.strip())
        elif cour:
            blocs.append(" ".join(cour)); cour = []
    if cour:
        blocs.append(" ".join(cour))
    debut = next((b for b in blocs if not b.startswith("§")), "")
    concl = ""
    for i, b in enumerate(blocs):
        if b.startswith("§") and re.search(r"(resultat|conclusion|lecture|verdict|bilan|en bref)", sans_accent(b)):
            suite = [x for x in blocs[i + 1:i + 4] if not x.startswith("§")]
            if suite:
                concl = " ".join(suite)
    texte = nettoyer_md(debut)[:480]
    if concl:
        texte += " — " + nettoyer_md(concl)[:520]
    return titre, texte


def construire():
    notes = []
    for cat, t, x in COEUR:
        notes.append({"t": t, "x": x, "c": cat, "d": "cœur"})
    dossiers = {}
    for f in sorted(R0.glob("*/README.md")):
        dos = f.parent.name
        titre, texte = extrait_readme(f)
        cat = DOSSIER_CAT.get(dos, "recherche")
        dossiers[dos] = len(notes)
        notes.append({"t": titre, "x": texte, "c": cat, "d": dos})
    with open(R0 / "fonds" / "essais.csv", newline="") as fh:
        r = csv.reader(fh)
        next(r)
        for x in r:
            if len(x) < 4:
                continue
            date, dos, essai, res = x[0], x[1], x[2], ",".join(x[3:])
            notes.append({"t": essai[:90] + ("…" if len(essai) > 90 else ""), "x": f"Essai du {date} ({dos}) : {essai}. Résultat : {res}",
                          "c": DOSSIER_CAT.get(dos, "recherche"), "d": dos})
    for n in notes:
        assert not SECRETS.search(n["x"]), n["t"]
    # liens : proximite des mots (TF-IDF, cosinus), plus les essais rattaches au README de leur dossier
    toks = [Counter(mots(n["t"] + " " + n["t"] + " " + n["x"])) for n in notes]
    df = Counter(m for t in toks for m in t)
    N = len(notes)
    vec = []
    for t in toks:
        v = {m: (1 + math.log(c)) * math.log(N / df[m]) for m, c in t.items() if df[m] < N * 0.5}
        nrm = math.sqrt(sum(w * w for w in v.values())) or 1
        vec.append({m: w / nrm for m, w in v.items()})
    liens = {}
    for i in range(N):
        sims = []
        for j in range(N):
            if i == j:
                continue
            s = sum(w * vec[j].get(m, 0) for m, w in vec[i].items())
            if s > 0.07:
                sims.append((s, j))
        for s, j in sorted(sims, reverse=True)[:4]:
            a, b = min(i, j), max(i, j)
            liens[(a, b)] = max(liens.get((a, b), 0), s)
    for i, n in enumerate(notes):
        if n["d"] in dossiers and dossiers[n["d"]] != i:
            a, b = sorted((i, dossiers[n["d"]]))
            liens[(a, b)] = max(liens.get((a, b), 0), 0.3)
    for i in range(len(COEUR)):
        for j in range(i + 1, len(COEUR)):
            if COEUR[i][0] == COEUR[j][0]:
                liens[(i, j)] = max(liens.get((i, j), 0), 0.35)
    return {"cats": {k: {"nom": v[0], "couleur": v[1]} for k, v in CATS.items()}, "notes": notes,
            "liens": [[a, b, round(s, 3)] for (a, b), s in sorted(liens.items())], "date": "12 octobre 2026"}


def main():
    s = construire()
    (ICI / "savoir.json").write_text(json.dumps(s, ensure_ascii=False, separators=(",", ":")))
    page = ICI / "page.html"
    if page.exists():
        html = page.read_text().replace("/*SAVOIR*/", json.dumps(s, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))
        (ICI / "cerveau.html").write_text(html)
        print(f"cerveau.html : {len(html) / 1e3:.0f} ko")
    par_cat = Counter(n["c"] for n in s["notes"])
    print(f"{len(s['notes'])} notes, {len(s['liens'])} liens ; {dict(par_cat)}")


if __name__ == "__main__":
    main()
