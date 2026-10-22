# Vague « taille optimale » : la taille de la zone selon l'état du compte, calculée par programmation dynamique (règles fixées le 22 octobre 2026, avant tout calcul)

## Demande de l'utilisateur (22 octobre 2026)

Il est en plein challenge Bulenox 50K, le bot perd et a touché deux fois la limite du jour. Il veut la meilleure façon
de ne pas perdre ce compte, et, s'il le perd, les meilleurs réglages pour la prochaine prop firm.

## L'idée

Le bot joue une taille fixe (Bulenox : 4 MNQ, 6 MNQ les 5 dernières séances). Or la bonne taille dépend de la
situation : marge au-dessus du plancher, distance à l'objectif, séances restantes. La **programmation dynamique**
calcule, pour chaque situation, la taille qui donne la plus grande chance de valider, à partir de la distribution des
vraies séances de la zone. Les vagues 12 et 13 n'ont testé que quelques règles écrites à la main (protection, fin de
course, prudence près du but) ; jamais la règle optimale.

## Règles (fixées maintenant)

**Séances** : la zone du bot (V1 sans filtre, pas de zone les jours de la Fed), minute par minute, au prix du 20 octobre
2026, 1,5 point de frais par aller-retour : `partie_d.chemins_zone()` (clôture, plus bas et plus haut de chaque minute
pour 1 MNQ). Moteur de chaque séance : celui de `partie_d.defi` (plancher touché au plus bas de la minute, limite du
jour, arrêt à l'objectif + 50 $ au plus haut de la minute).

**Comptes** :
- **Bulenox Legacy 50K option 2** : objectif 3 000 $, perte max 2 500 $ sous le plus haut de fin de journée, bloquée à
  +100 $, limite du jour 1 100 $ (arrête la journée), **21 séances** (médiane de 30 jours calendaires).
- **Lucid Flex 50K** : objectif 3 000 $, perte max 2 000 $ bloquée à +100 $, pas de limite du jour, 126 séances au plus.
  La règle du meilleur jour (50 %) n'entre pas dans le calcul de la politique ; elle est appliquée dans l'évaluation.

**Politique** : état = (solde, plus haut de fin de journée, séances restantes), solde et plus haut sur une grille de
50 $. Tailles permises : 0 (pas de trade ce jour-là, la séance compte quand même), 1, 2, 3, 4, 5, 6 MNQ. La politique
maximise la chance de valider (perdre et expirer comptent pareil). Elle est calculée **uniquement sur les séances
2012 - 2021**, tirées indépendamment.

**Évaluation** sur les vraies suites de séances (pas de tirage), départ à chaque séance :
- **choix** 2012 - 2021 (dans l'échantillon, pour information) ;
- **vérification 2023 - 2026** (hors échantillon).

Comparée aux tailles fixes 1 à 6 MNQ et, chez Bulenox, à la version actuelle (4 puis 6 MNQ).

## Décision (fixée maintenant)

La politique est **retenue** pour un compte si, sur les départs 2023 - 2026 :
1. elle valide au moins **3 points de plus** que la meilleure taille fixe (ou que la version actuelle chez Bulenox,
   si elle est meilleure) ;
2. sans perdre plus de 3 points de challenges en plus que cette référence.

Retenue, elle devient une table de tailles à régler dans le bot (et une table de lecture pour le challenge en cours).
Non retenue, le bot garde sa taille actuelle.

Pour information : la table de la politique pour le challenge Bulenox (taille selon la marge au-dessus du plancher, ce
qui reste à gagner et les séances restantes), et la chance de valider depuis la situation de l'utilisateur dès qu'il
la donne.

## Limites écrites d'avance

- Les séances sont tirées indépendamment : la politique ne voit pas les séries de pertes (régimes).
- Sans filtre delta sur 15 ans (pas de données) ; si le filtre marche, les chances réelles sont un peu meilleures.
- Une politique qui change souvent de taille demande un réglage du bot chaque matin.
- Une grande chance de valider ne veut pas dire un compte sûr : la politique peut accepter plus de comptes perdus si
  elle valide plus.

## Résultats (22 octobre 2026) : `resultats.txt`, `etude.py`

| Compte | Départs réels | Politique optimale : validé / perdu | Meilleure taille fixe | Version actuelle (4 puis 6) |
|---|---|---|---|---|
| Bulenox 50K | 2012 - 2021 (dans l'échantillon) | 46,2 / 47,3 % | 6 MNQ : 47,6 / 49,7 % | 46,3 / 44,9 % |
| Bulenox 50K | **2023 - 2026 (vérification)** | **52,1 / 44,3 %** | 5 MNQ : 49,6 / 48,9 % | **49,9 / 45,3 %** |
| Lucid Flex 50K | 2012 - 2021 (dans l'échantillon) | 40,1 / 42,0 % | 1 MNQ : 51,5 / 29,7 % | — |
| Lucid Flex 50K | **2023 - 2026 (vérification)** | **48,8 / 46,1 %** | **1 MNQ : 54,6 / 35,2 %** | — |

**Décision : non retenue, ni chez Bulenox ni chez Lucid.**
- **Bulenox** : la politique valide 2,2 points de plus que la version actuelle (52,1 % contre 49,9 %) et perd un peu
  moins, mais le seuil fixé était de 3 points. Elle confirme la partie D : avec 30 jours, environ 50 % est un plafond,
  quelle que soit la façon de régler la taille.
- **Lucid** : la politique fait **nettement moins bien** que 1 MNQ fixe, même sur les années où elle a été calculée
  (40 % contre 51,5 %). Tirées au hasard, les séances lui disaient de commencer à 2 MNQ (49,8 % de chances). Sur les
  vraies suites de séances, c'est faux : **les pertes de la zone viennent en séries**, et une taille plus grande se
  fait prendre dans ces séries. C'est pour cela que 1 MNQ fixe reste le meilleur réglage sans limite de temps.

Pour information, la table de la politique de Bulenox (taille selon le solde, le plancher et les séances restantes)
est dans `resultats.txt` ; `python3 etude_large/taille/etude.py <solde> <plancher> <seances>` (en $ par rapport à
50 000 $) donne la chance de valider et la taille conseillée depuis une situation donnée.
