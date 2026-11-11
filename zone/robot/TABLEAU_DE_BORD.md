# Robot zone de bruit (MNQ) : tableau de bord (argent virtuel)

Mis a jour le **2026-11-10**. Demarre le 2026-09-25. Aucun argent reel n'est engage.

Historique : rejeu de cette gestion avec les regles Phidias publiques d'octobre 2026, departs 2023-2024 suivis 24 mois (tournoi8/ et zone_deux/ sur la branche de recherche) : zone + RSI(2) environ +254 $ nets par an, rien recu dans 27 % des departs ; zone seule -22 $ par an, rien recu dans 79 %. Sur 12 mois, environ -115 $ par an dans les deux cas : le premier retrait arrive en general apres 12 mois. Une taille plus grande ne fait pas mieux (zone_deux/).

**Challenge n°2 en cours : +2,476 $ sur +4 000 $ ; marge avant la limite 2,500 $**

Voyant VERT (fourchette normale) : +934 $ pour 1 MNQ apres 32 seance(s) ; le backtest attendait +368 $, alerte sous -1,516 $ (ligne des 5 %). Prochain bilan a 60 seances.

| Mesure | Valeur |
|---|---|
| Tentatives de challenge | 2 (n°1 perdu, n°2 en cours) |
| Recu en retraits virtuels (80 %) | 0 $ |
| Gain de la strategie pour 1 MNQ depuis le depart | +934 $ |
| RSI(2) (second moteur, dans le compte depuis le 1er octobre 2026) pour 1 MNQ | -1,032 $ |
| Rebond (suivi a part, hors compte) pour 1 MNQ depuis le 1er octobre 2026 | +735 $ |

## Pour la seance du 2026-11-11 (a utiliser en direct)

Cloture de la veille (16 h New York) : **27,835.25**. Apres l'ouverture de 9 h 30 : haut = max(ouverture, veille) x (1 + mouvement) ; bas = min(ouverture, veille) x (1 - mouvement). A chaque heure ci-dessous : cloture de la minute au-dessus du haut -> achat ; sous le bas -> vente ; en position, sortie si le prix repasse la limite ou le VWAP. Tout fermer a 15 h 59 (New York).

| Controle (New York) | Heure de Paris | Mouvement moyen | Haut = x | Bas = x |
|---|---|---|---|---|
| 10h00 | 16h00 | 0.613% | 1.00613 | 0.99387 |
| 10h30 | 16h30 | 0.748% | 1.00748 | 0.99252 |
| 11h00 | 17h00 | 0.880% | 1.00880 | 0.99120 |
| 11h30 | 17h30 | 0.758% | 1.00758 | 0.99242 |
| 12h00 | 18h00 | 0.884% | 1.00884 | 0.99116 |
| 12h30 | 18h30 | 0.937% | 1.00937 | 0.99063 |
| 13h00 | 19h00 | 1.027% | 1.01027 | 0.98973 |
| 13h30 | 19h30 | 1.023% | 1.01023 | 0.98977 |
| 14h00 | 20h00 | 1.067% | 1.01067 | 0.98933 |
| 14h30 | 20h30 | 1.080% | 1.01080 | 0.98920 |
| 15h00 | 21h00 | 1.061% | 1.01061 | 0.98939 |
| 15h30 | 21h30 | 1.149% | 1.01149 | 0.98851 |

Taille : un jour normal = 319 $ de risque pour 1 MNQ. Sur un compte neuf : f = 0.15 -> Phidias (coussin 2 500 $) 1 MNQ, Topstep (coussin 2 000 $) 1 MNQ ; f = 0.25 -> Phidias (coussin 2 500 $) 1 MNQ, Topstep (coussin 2 000 $) 1 MNQ ; f = 0.35 -> Phidias (coussin 2 500 $) 2 MNQ, Topstep (coussin 2 000 $) 2 MNQ. **En cours de challenge : MNQ = f x (solde - limite de perte) / 319, arrondi en dessous, au moins 1 MNQ** (exemple : f = 0,25, coussin 1 500 $ -> 1 MNQ).

Le VWAP est celui de la seance americaine, calcule depuis 9 h 30 (pas depuis la reouverture de 18 h). On ne regarde le prix qu'aux heures de controle : pas de stop place dans le marche.

## Second moteur dans le compte : RSI(2) sur le NQ (depuis le 1er octobre 2026)

RSI(2) : pas de position. Pas d'achat possible le 2026-11-11 (il faudrait un prix au-dessus de 28,156.53, moyenne des 200, et un RSI(2) sous 10, soit un prix sous 25,531.35).

Regle (tournoi8/ sur la branche de recherche) : achat a 15 h 50 si la cloture de 15 h 49 est au-dessus de la moyenne des 200 clotures et si le RSI de Wilder sur 2 clotures est sous 10 ; vente a 15 h 50 quand la cloture depasse la moyenne des 5. Position gardee la nuit et le week-end. Taille : comme la zone, f x coussin / racine(2), au moins 1 MNQ. Seul survivant du tournoi des strategies de plusieurs jours ; independant de la zone.

## Bot 3 en 1 : zone filtree par le delta + RSI(2), 1 MNQ chacun (challenge 50K virtuel a part)

**Bot 3 en 1 (zone filtree par le delta + RSI(2), 1 MNQ chacun, depuis le 2026-10-02) : challenge n°1, +0 $ sur +4 000 $, marge avant la limite 2,500 $ ; EN PAUSE : 27 seance(s) en attente du vrai delta (transactions Databento indisponibles ; le bot rattrapera tout seul quand elles reviendront).**

Demande de l'utilisateur du 2 octobre 2026 : la zone de bruit ne garde que les trades dont le delta des 30 minutes va dans leur sens, plus le RSI(2), 1 MNQ chacun, taille fixe. Rejeu d'avril a septembre 2026 (mois ou le filtre a ete trouve, donc flatteur) : challenge reussi en 3 a 4 mois selon le mois de depart, marge la plus basse 50 $ le 29 juillet 2026 a 15 h 59 (rejeu minute par minute du 3 octobre 2026 ; le premier rejeu, a la journee, disait 414 $). Le bot n'utilise que le vrai delta (transactions Databento) : sans lui, il se met en pause et rattrape quand les donnees reviennent. Une approximation par le prix aurait fait perdre le challenge le 29 juillet.

| Date | Phase | Resultat du jour | Solde | Zone gardee (1 MNQ) | Trades ecartes | RSI(2) (1 MNQ) | Evenement |
|---|---|---|---|---|---|---|---|
| 2026-10-02 | challenge n°1 | +0 $ | 50,000 $ | +0 $ | 0/0 | +0 $ |  |

## Filtre order flow (H1) : delta des 30 dernieres minutes (suivi a part)

Un trade de zone n'est garde que si le delta (achats agressifs - ventes agressives) des 30 minutes qui finissent a la minute du signal va dans son sens. Confirme au coffre le 2 octobre 2026 (orderflow/ sur la branche de recherche : trades gardes +67 points, ecartes -35 points, t = 2,34), mais sur peu de trades ecartes (20 en 6 mois). Sur 15 ans, une approximation gratuite du delta (mouvement du prix sur 30 min) ne le confirme pas : effet faible, t = 1,62 (filtre_h1/ sur la recherche). Suivi ici a part, le compte virtuel garde la zone d'origine. **En direct : a chaque signal de la zone, regarder le delta cumule des 30 dernieres minutes sur ta plateforme ; s'il va contre le trade, ne pas le prendre.**

Pas encore de trade de zone mesure depuis le 2026-10-01.

## Second moteur : rebond apres forte baisse (suivi a part, hors compte)

Pas d'achat le 2026-11-11. Derniere seance complete : +0.33% (ouverture -> cloture) ; seuil des 10 % les plus bas : -1.19%. Ajoute le 1er octobre 2026 a la demande de l'utilisateur. Non valide statistiquement : ses gains passes viennent surtout de deux krachs (2020 et 2025) ; voir zone/README.md.

## Derniers jours

| Date | Phase | MNQ zone | RSI(2) MNQ | Resultat du jour | Solde | Zone pour 1 MNQ | RSI(2) pour 1 MNQ | Rebond (a part, 1 MNQ) | Evenement |
|---|---|---|---|---|---|---|---|---|---|
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
| 2026-10-21 | challenge n°1 | 1 | 1 | +378 $ | 50,088 $ | -364 $ | +742 $ | +0 $ |  |
