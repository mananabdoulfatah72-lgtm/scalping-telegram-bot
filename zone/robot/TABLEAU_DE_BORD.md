# Robot zone de bruit (MNQ) : tableau de bord (argent virtuel)

Mis a jour le **2026-09-30**. Demarre le 2026-09-25. Aucun argent reel n'est engage.

Historique : rejeu de cette gestion avec les regles Phidias publiques d'octobre 2026 (zone_retrait/ sur la branche de recherche), departs 2023-2024 suivis 24 mois : environ 160 $ recus par an pour 1,1 challenge paye par an (164 $ chacun), rien recu dans 79 % des departs. Aucune autre gestion testee (128) ne fait mieux de facon fiable.

**Challenge n°1 en cours : -276 $ sur +4 000 $ ; marge avant la limite 2,224 $**

| Mesure | Valeur |
|---|---|
| Tentatives de challenge | 1 (n°1 en cours) |
| Recu en retraits virtuels (80 %) | 0 $ |
| Gain de la strategie pour 1 MNQ depuis le depart | -276 $ |
| Rebond (second moteur suivi a part, hors compte) pour 1 MNQ depuis le 1er octobre 2026 | +0 $ |

## Trades du 2026-09-30

- achat 10h00 a 30,849.25 -> sortie 12h30 a 30,835.50

## Pour la seance du 2026-10-01 (a utiliser en direct)

Cloture de la veille (16 h New York) : **30,693.75**. Apres l'ouverture de 9 h 30 : haut = max(ouverture, veille) x (1 + mouvement) ; bas = min(ouverture, veille) x (1 - mouvement). A chaque heure ci-dessous : cloture de la minute au-dessus du haut -> achat ; sous le bas -> vente ; en position, sortie si le prix repasse la limite ou le VWAP. Tout fermer a 15 h 59 (New York).

| Controle (New York) | Heure de Paris | Mouvement moyen | Haut = x | Bas = x |
|---|---|---|---|---|
| 10h00 | 16h00 | 0.290% | 1.00290 | 0.99710 |
| 10h30 | 16h30 | 0.399% | 1.00399 | 0.99601 |
| 11h00 | 17h00 | 0.413% | 1.00413 | 0.99587 |
| 11h30 | 17h30 | 0.454% | 1.00454 | 0.99546 |
| 12h00 | 18h00 | 0.489% | 1.00489 | 0.99511 |
| 12h30 | 18h30 | 0.503% | 1.00503 | 0.99497 |
| 13h00 | 19h00 | 0.580% | 1.00580 | 0.99420 |
| 13h30 | 19h30 | 0.568% | 1.00568 | 0.99432 |
| 14h00 | 20h00 | 0.538% | 1.00538 | 0.99462 |
| 14h30 | 20h30 | 0.545% | 1.00545 | 0.99455 |
| 15h00 | 21h00 | 0.539% | 1.00539 | 0.99461 |
| 15h30 | 21h30 | 0.601% | 1.00601 | 0.99399 |

Taille : un jour normal = 205 $ de risque pour 1 MNQ. Sur un compte neuf : f = 0.15 -> Phidias (coussin 2 500 $) 1 MNQ, Topstep (coussin 2 000 $) 1 MNQ ; f = 0.25 -> Phidias (coussin 2 500 $) 3 MNQ, Topstep (coussin 2 000 $) 2 MNQ ; f = 0.35 -> Phidias (coussin 2 500 $) 4 MNQ, Topstep (coussin 2 000 $) 3 MNQ. **En cours de challenge : MNQ = f x (solde - limite de perte) / 205, arrondi en dessous, au moins 1 MNQ** (exemple : f = 0,25, coussin 1 500 $ -> 1 MNQ).

Le VWAP est celui de la seance americaine, calcule depuis 9 h 30 (pas depuis la reouverture de 18 h). On ne regarde le prix qu'aux heures de controle : pas de stop place dans le marche.

## Second moteur : rebond apres forte baisse (suivi a part, hors compte)

Pas d'achat le 2026-10-01. Derniere seance complete : -0.02% (ouverture -> cloture) ; seuil des 10 % les plus bas : -1.13%. Ajoute le 1er octobre 2026 a la demande de l'utilisateur. Non valide statistiquement : ses gains passes viennent surtout de deux krachs (2020 et 2025) ; voir zone/README.md.

## Derniers jours

| Date | Phase | MNQ | Resultat du jour | Solde | Pour 1 MNQ | Rebond (a part, 1 MNQ) | Evenement |
|---|---|---|---|---|---|---|---|
| 2026-09-30 | challenge n°1 | 1 | -30 $ | 49,724 $ | -30 $ | +0 $ |  |
| 2026-09-29 | challenge n°1 | 1 | +0 $ | 49,754 $ | +0 $ | +0 $ |  |
| 2026-09-28 | challenge n°1 | 1 | -246 $ | 49,754 $ | -246 $ | +0 $ |  |
