# Le bot dans un challenge futures « intraday » à prix normal (règles fixées le 8 octobre 2026, avant le calcul)

## Demande de l'utilisateur (8 octobre 2026)

Pas de S2F DayTraders à 342 $. Il veut le bot dans des challenges 50K « normaux » à prix raisonnable (Bulenox,
Apex, Alpha…). Si le RSI(2) l'empêche parce qu'il garde des positions la nuit, il faut l'enlever et chercher une
autre source d'avantage adaptée à ces challenges. Si la limite de perte suivie pendant la journée pose problème, il
faut le regarder aussi.

## Ce qu'on sait déjà

- Les firmes qui acceptent un robot entièrement automatique sur des futures CME obligent toutes à être à plat chaque
  jour (`research_notes/Challenge futures 50K pour bot automatisé/`, rapport du 7 octobre). Heures limites relevées
  le 8 octobre 2026 (sites d'avis, à confirmer) : Topstep 16 h 10, Tradeify et Lucid 16 h 45, Bulenox et Apex
  16 h 59 (heure de New York).
- **La journée de trading de ces firmes commence à 18 h (réouverture) et finit à leur heure limite.** Acheter à 18 h
  et revendre avant l'heure limite du lendemain respecte donc la règle « pas de position après la clôture »
  (déjà noté dans `nuit/`).
- Le RSI(2) gagne surtout pendant la nuit et le week-end (`tournoi8/sans_weekend.txt` : +32 points en moyenne du
  vendredi 15 h 50 au lundi 9 h 30).
- Plus de 90 stratégies intraday ont déjà été testées sans survivant (tournois 1 à 7, `evolution*/`, machine 3,
  `ordres/`, `orderflow/`, `zone_failles/`, `zone_sources/`). Seule la zone de bruit (et son filtre delta) a tenu.
  Ce dossier ne refait pas ces recherches.

## Partie 1 : le RSI(2) « entre deux clôtures »

**Signaux** : exactement ceux du robot (`protection/robot_main.py`, `rsi2`). Décision à 15 h 50 (10 minutes avant la
dernière minute un jour court) : achat si la clôture de 15 h 49 dépasse la moyenne des 200 et si le RSI(2) de
Wilder est sous 10 ; vente si la clôture dépasse la moyenne des 5 ; position fermée avant un changement d'échéance.

**Exécution (la seule chose qui change)** :
- l'achat se fait **le soir de la décision, à l'ouverture de la barre de 18 h** (heure de New York) qui suit
  (dimanche 18 h pour une décision du vendredi). S'il n'y a pas de barre de 18 h avant la séance suivante (jour
  férié, trou de données), à l'ouverture de la première barre horaire disponible avant 9 h 30, sinon à 9 h 30 ;
- **chaque séance, la position est fermée à la clôture de la dernière minute** (15 h 59, ou la dernière minute d'un
  jour court), sauf si la décision de 15 h 50 la vend plus tôt (à l'ouverture de 15 h 50) ;
- si la règle veut toujours la position, elle est **rachetée le soir même à 18 h** ;
- pas de position de nuit si la barre de 18 h n'est pas du même contrat que la séance du lendemain ;
- frais : 1 $ + 1 tick par ordre, comme le robot ; chaque jour tenu coûte donc un aller-retour de plus.

**Données** : barres d'une heure du NQ (contrat le plus échangé, `nuit/donnees/nasdaq100_1h.csv.gz`, Databento,
jusqu'au 28 septembre 2026) pour la nuit ; minutes de séance (`intraday/`) pour la journée.

**Mesures** (1 MNQ, du premier signal au 25 septembre 2026) : gain en dollars, t des gains quotidiens nets, gain
année par année, part de la nuit (18 h → 9 h 30) et de la séance (9 h 30 → 15 h 59), comparés à l'original (même
code que `tournoi8/sans_weekend.py`).

**Règle** : le RSI(2) entre deux clôtures est **utilisable** si, sur toute la période :
1. t ≥ 2 ;
2. au moins la moitié des dollars de l'original ;
3. un gain positif sur 2023 - septembre 2026.

Sinon, le RSI(2) sort du bot pour ces challenges. Ce n'est pas une nouvelle découverte : les signaux du RSI(2) ont
déjà été choisis sur toute la période (`tournoi8/`). On mesure seulement ce qu'il reste de son avantage quand il doit
être à plat chaque jour.

**Si le RSI(2) n'est pas utilisable**, une recherche d'une autre source se fera dans un dossier à part, avec ses
propres règles écrites avant le calcul. Elle ne reprendra aucune famille déjà testée.

## Partie 2 : les comptes 50K

**Bots** (1 MNQ par source, taille fixe) :
- **Z** : zone de bruit seule, non filtrée (le vrai delta n'existe qu'à partir d'avril 2026) ;
- **Z + R** : zone + RSI(2) entre deux clôtures, seulement si la partie 1 le déclare utilisable ;
- **descriptif** : la même chose avec la zone filtrée par le delta simulé, comme `filtre_h1/scenario.py`
  (corrélation mesurée en 2026, 20 tirages).

**Règles des comptes** (relevées le 8 octobre 2026 sur des sites d'avis ; les pages officielles ne s'ouvrent pas d'ici) :

| Compte 50K | Objectif | Perte max | Suivi | Blocage du plancher | Limite du jour | Régularité (challenge) | Jours mini | Temps limite | Robot entièrement automatique |
|---|---|---|---|---|---|---|---|---|---|
| Bulenox option 1 | 3 000 $ | 2 500 $ | en direct, gains latents compris | 50 100 $ | aucune | aucune | 1 | aucun (abonnement mensuel) | oui (robot personnel) |
| Bulenox option 2 | 3 000 $ | 2 500 $ | fin de journée | 50 100 $ | 1 100 $ (douce) | aucune | 1 | aucun (abonnement mensuel) | oui (robot personnel) |
| Tradeify Growth | 3 000 $ | 2 000 $ | fin de journée | 50 100 $ | 1 250 $ (douce) | aucune | 1 | aucun | oui (algo personnel, exclusif) |
| Tradeify Select | 3 000 $ | 2 000 $ | fin de journée | 50 100 $ | aucune | 40 % | 3 | aucun | oui (algo personnel, exclusif) |
| Lucid Flex | 3 000 $ | 2 000 $ | fin de journée | 50 100 $ | aucune (option sans limite) | 50 % | 1 | aucun | oui |
| Topstep | 3 000 $ | 2 000 $ | fin de journée | 50 000 $ | 1 000 $ (douce) | 50 % | 1 | aucun (abonnement mensuel) | oui (API, depuis son propre ordinateur, pas de VPS) |
| Apex EOD (descriptif) | 3 000 $ | 2 000 $ | fin de journée | 50 100 $ | aucune | aucune | 1 | 30 jours (21 séances) | douteux sur le compte financé |

- « Fin de journée » : le plancher ne monte qu'avec le solde de clôture, mais il est **surveillé en direct** (une
  baisse dans la journée sous le plancher fait perdre le compte, positions de nuit comprises).
- « Douce » : à la limite, tout est fermé et le bot ne trade plus jusqu'à la réouverture du soir. La journée de la
  limite commence à 18 h la veille.
- Régularité : le meilleur jour ne doit pas dépasser ce pourcentage du gain total au moment de réussir (sinon il
  faut gagner plus).

**Simulation** : moteur minute par minute de `protection/` (mêmes trades de zone, mêmes frais), avec la nuit en
barres d'une heure pour le RSI(2). Dans une barre, le plus haut compte avant le plus bas. Les 30 minutes de 9 h à
9 h 30 ne sont connues que par la barre de 8 h et l'ouverture de 9 h 30 (approximation).

**Départs** : une séance sur cinq, RSI(2) à plat, suivis jusqu'à 252 séances (21 pour Apex). Publiés par compte et
par bot :
- réussis, perdus, pas finis, séances médianes jusqu'à la réussite, sur 2011-2022 et sur 2023 - 2026 ;
- les départs de 2025 à part ;
- le mois de 2026 où le vrai delta existe (avril - septembre), à titre descriptif.

**Choix** : rien n'est « retenu » ici. C'est une comparaison de comptes pour que l'utilisateur choisisse. Le score
(réussis − perdus) sur 2011-2022 classe les comptes ; 2023 - 2026 sert de contrôle.

La phase financée (retraits) n'est simulée qu'ensuite, pour les deux ou trois comptes en tête, avec des règles de
retrait relevées séparément.
