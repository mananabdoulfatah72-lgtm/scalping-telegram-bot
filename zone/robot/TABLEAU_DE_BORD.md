# Robot zone de bruit (MNQ) : tableau de bord (argent virtuel)

Mis a jour le **2026-11-11**. Demarre le 2026-09-25. Aucun argent reel n'est engage.

Historique : rejeu de cette gestion avec les regles Phidias publiques d'octobre 2026, departs 2023-2024 suivis 24 mois (tournoi8/ et zone_deux/ sur la branche de recherche) : zone + RSI(2) environ +254 $ nets par an, rien recu dans 27 % des departs ; zone seule -22 $ par an, rien recu dans 79 %. Sur 12 mois, environ -115 $ par an dans les deux cas : le premier retrait arrive en general apres 12 mois. Une taille plus grande ne fait pas mieux (zone_deux/).

**Challenge n°2 en cours : +2,285 $ sur +4 000 $ ; marge avant la limite 2,309 $**

Voyant VERT (fourchette normale) : +744 $ pour 1 MNQ apres 33 seance(s) ; le backtest attendait +380 $, alerte sous -1,534 $ (ligne des 5 %). Prochain bilan a 60 seances.

| Mesure | Valeur |
|---|---|
| Tentatives de challenge | 2 (n°1 perdu, n°2 en cours) |
| Recu en retraits virtuels (80 %) | 0 $ |
| Gain de la strategie pour 1 MNQ depuis le depart | +744 $ |
| RSI(2) (second moteur, dans le compte depuis le 1er octobre 2026) pour 1 MNQ | -1,032 $ |
| Rebond (suivi a part, hors compte) pour 1 MNQ depuis le 1er octobre 2026 | +735 $ |

## Trades du 2026-11-11

- achat 12h00 a 28,613.00 -> sortie 13h00 a 28,629.25
- achat 13h30 a 28,682.50 -> sortie 14h30 a 28,573.75

## Pour la seance du 2026-11-12 (a utiliser en direct)

Cloture de la veille (16 h New York) : **28,484.25**. Apres l'ouverture de 9 h 30 : haut = max(ouverture, veille) x (1 + mouvement) ; bas = min(ouverture, veille) x (1 - mouvement). A chaque heure ci-dessous : cloture de la minute au-dessus du haut -> achat ; sous le bas -> vente ; en position, sortie si le prix repasse la limite ou le VWAP. Tout fermer a 15 h 59 (New York).

| Controle (New York) | Heure de Paris | Mouvement moyen | Haut = x | Bas = x |
|---|---|---|---|---|
| 10h00 | 16h00 | 0.619% | 1.00619 | 0.99381 |
| 10h30 | 16h30 | 0.708% | 1.00708 | 0.99292 |
| 11h00 | 17h00 | 0.876% | 1.00876 | 0.99124 |
| 11h30 | 17h30 | 0.750% | 1.00750 | 0.99250 |
| 12h00 | 18h00 | 0.914% | 1.00914 | 0.99086 |
| 12h30 | 18h30 | 0.963% | 1.00963 | 0.99037 |
| 13h00 | 19h00 | 1.030% | 1.01030 | 0.98970 |
| 13h30 | 19h30 | 1.032% | 1.01032 | 0.98968 |
| 14h00 | 20h00 | 1.054% | 1.01054 | 0.98946 |
| 14h30 | 20h30 | 1.036% | 1.01036 | 0.98964 |
| 15h00 | 21h00 | 1.004% | 1.01004 | 0.98996 |
| 15h30 | 21h30 | 1.098% | 1.01098 | 0.98902 |

Taille : un jour normal = 321 $ de risque pour 1 MNQ. Sur un compte neuf : f = 0.15 -> Phidias (coussin 2 500 $) 1 MNQ, Topstep (coussin 2 000 $) 1 MNQ ; f = 0.25 -> Phidias (coussin 2 500 $) 1 MNQ, Topstep (coussin 2 000 $) 1 MNQ ; f = 0.35 -> Phidias (coussin 2 500 $) 2 MNQ, Topstep (coussin 2 000 $) 2 MNQ. **En cours de challenge : MNQ = f x (solde - limite de perte) / 321, arrondi en dessous, au moins 1 MNQ** (exemple : f = 0,25, coussin 1 500 $ -> 1 MNQ).

Le VWAP est celui de la seance americaine, calcule depuis 9 h 30 (pas depuis la reouverture de 18 h). On ne regarde le prix qu'aux heures de controle : pas de stop place dans le marche.

## Second moteur dans le compte : RSI(2) sur le NQ (depuis le 1er octobre 2026)

RSI(2) : pas de position. Pas d'achat possible le 2026-11-12 (il faudrait un prix au-dessus de 28,168.38, moyenne des 200, et un RSI(2) sous 10, soit un prix sous 24,285.30).

Regle (tournoi8/ sur la branche de recherche) : achat a 15 h 50 si la cloture de 15 h 49 est au-dessus de la moyenne des 200 clotures et si le RSI de Wilder sur 2 clotures est sous 10 ; vente a 15 h 50 quand la cloture depasse la moyenne des 5. Position gardee la nuit et le week-end. Taille : comme la zone, f x coussin / racine(2), au moins 1 MNQ. Seul survivant du tournoi des strategies de plusieurs jours ; independant de la zone.

## Bot 3 en 1 : zone filtree par le delta + RSI(2), 1 MNQ chacun (challenge 50K virtuel a part)

**Bot 3 en 1 (zone filtree par le delta + RSI(2), 1 MNQ chacun, depuis le 2026-10-02) : challenge n°1, +0 $ sur +4 000 $, marge avant la limite 2,500 $ ; EN PAUSE : 28 seance(s) en attente du vrai delta (transactions Databento indisponibles ; le bot rattrapera tout seul quand elles reviendront).**

Demande de l'utilisateur du 2 octobre 2026 : la zone de bruit ne garde que les trades dont le delta des 30 minutes va dans leur sens, plus le RSI(2), 1 MNQ chacun, taille fixe. Rejeu d'avril a septembre 2026 (mois ou le filtre a ete trouve, donc flatteur) : challenge reussi en 3 a 4 mois selon le mois de depart, marge la plus basse 50 $ le 29 juillet 2026 a 15 h 59 (rejeu minute par minute du 3 octobre 2026 ; le premier rejeu, a la journee, disait 414 $). Le bot n'utilise que le vrai delta (transactions Databento) : sans lui, il se met en pause et rattrape quand les donnees reviennent. Une approximation par le prix aurait fait perdre le challenge le 29 juillet.

| Date | Phase | Resultat du jour | Solde | Zone gardee (1 MNQ) | Trades ecartes | RSI(2) (1 MNQ) | Evenement |
|---|---|---|---|---|---|---|---|
| 2026-10-02 | challenge n°1 | +0 $ | 50,000 $ | +0 $ | 0/0 | +0 $ |  |

## Filtre order flow (H1) : delta des 30 dernieres minutes (suivi a part)

Un trade de zone n'est garde que si le delta (achats agressifs - ventes agressives) des 30 minutes qui finissent a la minute du signal va dans son sens. Confirme au coffre le 2 octobre 2026 (orderflow/ sur la branche de recherche : trades gardes +67 points, ecartes -35 points, t = 2,34), mais sur peu de trades ecartes (20 en 6 mois). Sur 15 ans, une approximation gratuite du delta (mouvement du prix sur 30 min) ne le confirme pas : effet faible, t = 1,62 (filtre_h1/ sur la recherche). Suivi ici a part, le compte virtuel garde la zone d'origine. **En direct : a chaque signal de la zone, regarder le delta cumule des 30 dernieres minutes sur ta plateforme ; s'il va contre le trade, ne pas le prendre.**

Pas encore de trade de zone mesure depuis le 2026-10-01.

## Second moteur : rebond apres forte baisse (suivi a part, hors compte)

Pas d'achat le 2026-11-12. Derniere seance complete : +0.46% (ouverture -> cloture) ; seuil des 10 % les plus bas : -1.19%. Ajoute le 1er octobre 2026 a la demande de l'utilisateur. Non valide statistiquement : ses gains passes viennent surtout de deux krachs (2020 et 2025) ; voir zone/README.md.

## Derniers jours

| Date | Phase | MNQ zone | RSI(2) MNQ | Resultat du jour | Solde | Zone pour 1 MNQ | RSI(2) pour 1 MNQ | Rebond (a part, 1 MNQ) | Evenement |
|---|---|---|---|---|---|---|---|---|---|
| 2026-11-11 | challenge n°2 | 1 | 0 | -191 $ | 52,285 $ | -191 $ | +0 $ | +0 $ |  |
| 2026-11-10 | challenge n°2 | 1 | 0 | +0 $ | 52,476 $ | +0 $ | +0 $ | +0 $ |  |
| 2026-11-09 | challenge n°2 | 1 | 1 | +2,436 $ | 52,476 $ | +521 $ | +1,916 $ | +0 $ |  |
| 2026-11-06 | challenge n°2 | 1 | 1 | +40 $ | 50,040 $ | -482 $ | +522 $ | -186 $ |  |
| 2026-11-05 | challenge n°1 | 1 | 1 | -1,376 $ | 47,952 $ | +1,554 $ | -3,456 $ | +0 $ | COMPTE PERDU (limite touchee) |
| 2026-11-04 | challenge n°1 | 1 | 1 | -357 $ | 49,328 $ | -865 $ | +508 $ | +0 $ |  |
| 2026-11-03 | challenge n°1 | 1 | 1 | +107 $ | 49,684 $ | -160 $ | +268 $ | +66 $ |  |
| 2026-11-02 | challenge n°1 | 1 | 1 | -636 $ | 49,578 $ | -101 $ | -535 $ | +0 $ |  |
| 2026-10-30 | challenge n°1 | 1 | 1 | -31 $ | 50,214 $ | -30 $ | -2 $ | +0 $ |  |
| 2026-10-29 | challenge n°1 | 1 | 0 | +0 $ | 50,244 $ | +0 $ | +0 $ | +0 $ |  |
| 2026-10-28 | challenge n°1 | 1 | 0 | +0 $ | 50,244 $ | +0 $ | +0 $ | +0 $ |  |
| 2026-10-27 | challenge n°1 | 1 | 0 | +74 $ | 50,244 $ | +74 $ | +0 $ | +0 $ |  |
| 2026-10-26 | challenge n°1 | 1 | 0 | -233 $ | 50,171 $ | -233 $ | +0 $ | +0 $ |  |
| 2026-10-23 | challenge n°1 | 1 | 0 | -48 $ | 50,404 $ | -48 $ | +0 $ | +183 $ |  |
| 2026-10-22 | challenge n°1 | 1 | 0 | +364 $ | 50,452 $ | +364 $ | +0 $ | +0 $ |  |
