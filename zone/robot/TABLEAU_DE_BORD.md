# Robot zone de bruit (MNQ) : tableau de bord (argent virtuel)

Mis a jour le **2026-10-05**. Demarre le 2026-09-25. Aucun argent reel n'est engage.

Historique : rejeu de cette gestion avec les regles Phidias publiques d'octobre 2026, departs 2023-2024 suivis 24 mois (tournoi8/ et zone_deux/ sur la branche de recherche) : zone + RSI(2) environ +254 $ nets par an, rien recu dans 27 % des departs ; zone seule -22 $ par an, rien recu dans 79 %. Sur 12 mois, environ -115 $ par an dans les deux cas : le premier retrait arrive en general apres 12 mois. Une taille plus grande ne fait pas mieux (zone_deux/).

**Challenge n°1 en cours : -28 $ sur +4 000 $ ; marge avant la limite 2,472 $**

Voyant VERT (fourchette normale) : -28 $ pour 1 MNQ apres 6 seance(s) ; le backtest attendait +69 $, alerte sous -747 $ (ligne des 5 %). Prochain bilan a 60 seances.

| Mesure | Valeur |
|---|---|
| Tentatives de challenge | 1 (n°1 en cours) |
| Recu en retraits virtuels (80 %) | 0 $ |
| Gain de la strategie pour 1 MNQ depuis le depart | -28 $ |
| RSI(2) (second moteur, dans le compte depuis le 1er octobre 2026) pour 1 MNQ | +0 $ |
| Rebond (suivi a part, hors compte) pour 1 MNQ depuis le 1er octobre 2026 | +0 $ |

## Trades du 2026-10-05

- achat 10h30 a 31,212.75 -> sortie 16h00 a 31,338.50

## Pour la seance du 2026-10-06 (a utiliser en direct)

Cloture de la veille (16 h New York) : **31,338.50**. Apres l'ouverture de 9 h 30 : haut = max(ouverture, veille) x (1 + mouvement) ; bas = min(ouverture, veille) x (1 - mouvement). A chaque heure ci-dessous : cloture de la minute au-dessus du haut -> achat ; sous le bas -> vente ; en position, sortie si le prix repasse la limite ou le VWAP. Tout fermer a 15 h 59 (New York).

| Controle (New York) | Heure de Paris | Mouvement moyen | Haut = x | Bas = x |
|---|---|---|---|---|
| 10h00 | 16h00 | 0.304% | 1.00304 | 0.99696 |
| 10h30 | 16h30 | 0.439% | 1.00439 | 0.99561 |
| 11h00 | 17h00 | 0.429% | 1.00429 | 0.99571 |
| 11h30 | 17h30 | 0.465% | 1.00465 | 0.99535 |
| 12h00 | 18h00 | 0.475% | 1.00475 | 0.99525 |
| 12h30 | 18h30 | 0.493% | 1.00493 | 0.99507 |
| 13h00 | 19h00 | 0.558% | 1.00558 | 0.99442 |
| 13h30 | 19h30 | 0.516% | 1.00516 | 0.99484 |
| 14h00 | 20h00 | 0.482% | 1.00482 | 0.99518 |
| 14h30 | 20h30 | 0.504% | 1.00504 | 0.99496 |
| 15h00 | 21h00 | 0.505% | 1.00505 | 0.99495 |
| 15h30 | 21h30 | 0.571% | 1.00571 | 0.99429 |

Taille : un jour normal = 208 $ de risque pour 1 MNQ. Sur un compte neuf : f = 0.15 -> Phidias (coussin 2 500 $) 1 MNQ, Topstep (coussin 2 000 $) 1 MNQ ; f = 0.25 -> Phidias (coussin 2 500 $) 3 MNQ, Topstep (coussin 2 000 $) 2 MNQ ; f = 0.35 -> Phidias (coussin 2 500 $) 4 MNQ, Topstep (coussin 2 000 $) 3 MNQ. **En cours de challenge : MNQ = f x (solde - limite de perte) / 208, arrondi en dessous, au moins 1 MNQ** (exemple : f = 0,25, coussin 1 500 $ -> 1 MNQ).

Le VWAP est celui de la seance americaine, calcule depuis 9 h 30 (pas depuis la reouverture de 18 h). On ne regarde le prix qu'aux heures de controle : pas de stop place dans le marche.

## Second moteur dans le compte : RSI(2) sur le NQ (depuis le 1er octobre 2026)

RSI(2) : pas de position. Le 2026-10-06 a 15 h 50 New York : ACHAT si le prix de 15 h 49 est entre 27,663.13 (moyenne des 200) et 29,471.66 (RSI(2) sous 10), sauf jour de changement d'echeance.

Regle (tournoi8/ sur la branche de recherche) : achat a 15 h 50 si la cloture de 15 h 49 est au-dessus de la moyenne des 200 clotures et si le RSI de Wilder sur 2 clotures est sous 10 ; vente a 15 h 50 quand la cloture depasse la moyenne des 5. Position gardee la nuit et le week-end. Taille : comme la zone, f x coussin / racine(2), au moins 1 MNQ. Seul survivant du tournoi des strategies de plusieurs jours ; independant de la zone.

## Bot 3 en 1 : zone filtree par le delta + RSI(2), 1 MNQ chacun (challenge 50K virtuel a part)

**Bot 3 en 1 (zone filtree par le delta + RSI(2), 1 MNQ chacun, depuis le 2026-10-02) : challenge n°1, +0 $ sur +4 000 $, marge avant la limite 2,500 $ ; EN PAUSE : 1 seance(s) en attente du vrai delta (transactions Databento indisponibles ; le bot rattrapera tout seul quand elles reviendront).**

Demande de l'utilisateur du 2 octobre 2026 : la zone de bruit ne garde que les trades dont le delta des 30 minutes va dans leur sens, plus le RSI(2), 1 MNQ chacun, taille fixe. Rejeu d'avril a septembre 2026 (mois ou le filtre a ete trouve, donc flatteur) : challenge reussi en 3 a 4 mois selon le mois de depart, marge la plus basse 50 $ le 29 juillet 2026 a 15 h 59 (rejeu minute par minute du 3 octobre 2026 ; le premier rejeu, a la journee, disait 414 $). Le bot n'utilise que le vrai delta (transactions Databento) : sans lui, il se met en pause et rattrape quand les donnees reviennent. Une approximation par le prix aurait fait perdre le challenge le 29 juillet.

| Date | Phase | Resultat du jour | Solde | Zone gardee (1 MNQ) | Trades ecartes | RSI(2) (1 MNQ) | Evenement |
|---|---|---|---|---|---|---|---|
| 2026-10-02 | challenge n°1 | +0 $ | 50,000 $ | +0 $ | 0/0 | +0 $ |  |

## Filtre order flow (H1) : delta des 30 dernieres minutes (suivi a part)

Un trade de zone n'est garde que si le delta (achats agressifs - ventes agressives) des 30 minutes qui finissent a la minute du signal va dans son sens. Confirme au coffre le 2 octobre 2026 (orderflow/ sur la branche de recherche : trades gardes +67 points, ecartes -35 points, t = 2,34), mais sur peu de trades ecartes (20 en 6 mois). Sur 15 ans, une approximation gratuite du delta (mouvement du prix sur 30 min) ne le confirme pas : effet faible, t = 1,62 (filtre_h1/ sur la recherche). Suivi ici a part, le compte virtuel garde la zone d'origine. **En direct : a chaque signal de la zone, regarder le delta cumule des 30 dernieres minutes sur ta plateforme ; s'il va contre le trade, ne pas le prendre.**

Pas encore de trade de zone mesure depuis le 2026-10-01.

## Second moteur : rebond apres forte baisse (suivi a part, hors compte)

Pas d'achat le 2026-10-06. Derniere seance complete : +0.91% (ouverture -> cloture) ; seuil des 10 % les plus bas : -1.10%. Ajoute le 1er octobre 2026 a la demande de l'utilisateur. Non valide statistiquement : ses gains passes viennent surtout de deux krachs (2020 et 2025) ; voir zone/README.md.

## Derniers jours

| Date | Phase | MNQ zone | RSI(2) MNQ | Resultat du jour | Solde | Zone pour 1 MNQ | RSI(2) pour 1 MNQ | Rebond (a part, 1 MNQ) | Evenement |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-05 | challenge n°1 | 1 | 0 | +248 $ | 49,972 $ | +248 $ | +0 $ | +0 $ |  |
| 2026-10-02 | challenge n°1 | 1 | 0 | +0 $ | 49,724 $ | +0 $ | +0 $ | +0 $ |  |
| 2026-10-01 | challenge n°1 | 1 | 0 | +0 $ | 49,724 $ | +0 $ | +0 $ | +0 $ |  |
| 2026-09-30 | challenge n°1 | 1 | 0 | -30 $ | 49,724 $ | -30 $ | +0 $ | +0 $ |  |
| 2026-09-29 | challenge n°1 | 1 | 0 | +0 $ | 49,754 $ | +0 $ | +0 $ | +0 $ |  |
| 2026-09-28 | challenge n°1 | 1 | 0 | -246 $ | 49,754 $ | -246 $ | +0 $ | +0 $ |  |
