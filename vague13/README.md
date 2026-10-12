# Vague 13 : couper à l'objectif et adapter la taille pendant le challenge de 30 jours (règles fixées le 12 octobre 2026, avant le calcul)

## Demande de l'utilisateur

La version 30 jours de la vague 12 (taille 4 sans frein) valide environ 40 % des challenges Bulenox, et plus de taille
n'aide plus (plafond, `vague12/plafond12.txt`). L'utilisateur veut savoir si l'on peut faire mieux, avec deux leviers
proposés dans la vague 12 :
1. **couper dès l'objectif atteint dans la journée**, au lieu d'attendre le soir ;
2. **une taille qui s'adapte** à la situation du compte.

Le troisième levier (n'acheter que dans certains régimes de marché) est **écarté par l'utilisateur**, parce qu'il est
trop proche de l'optimisation sur le passé.

## Candidates (fixées maintenant)

Comptes : Bulenox Legacy 50K option 2, et Momentum EOD 50K. Mêmes règles que la vague 12, 30 jours calendaires.
Toutes partent de la version de la vague 12 : taille 4, sans frein, mode à plat, pas de zone les jours de la Fed.

| Candidate | Ce qui change pendant le challenge |
|---|---|
| A | rien : la version de la vague 12 (référence) |
| B | **arrêt à l'objectif** : dès que la valeur du compte atteint +3 050 $ (l'objectif + 50 $ pour les frais de sortie), tout est fermé par un ordre limite et plus rien n'est pris jusqu'au soir |
| C | B + **protection** : taille 2 tant que le coussin (solde de la veille − plancher) est sous la moitié de la perte max (1 250 $ Legacy, 1 125 $ Momentum) |
| D | B + **fin de course** : taille 6 pendant les 5 dernières séances des 30 jours, si l'objectif n'est pas atteint (un challenge expiré coûte autant qu'un perdu) |
| E | B + protection + fin de course |
| F | B + **prudence près du but** : taille 2 quand il manque moins de 1 000 $ |

**Priorités**, quand plusieurs règles s'appliquent le même jour : la protection d'abord, puis la fin de course, puis la
prudence près du but. Le Master est inchangé : taille 1, frein, plafond de 500 $ par jour.

L'arrêt à l'objectif réutilise le plafond du jour du moteur, déjà dans le bot pour le Master. Son niveau est
recalculé chaque matin : +3 050 $ moins le solde. La taille 6 demande de relever la borne du réglage « MNQ par source »
du bot, qui est à 5 aujourd'hui.

## Mesures

Comme la vague 12 :
- chaque séance comme jour d'achat ;
- 21 tirages du filtre (10 aussi bons qu'en 2026, 10 deux fois plus faibles, un sans filtre) ;
- choix sur 2012-2021, vérification sur 2023 - août 2026, et 2025 comme test.

Pour chaque candidate :
- challenge validé, perdu ou expiré, séances pour valider ;
- au Master : au moins un retrait, net d'un achat sur 24 mois, achats perdants.

## Jugement (fixé maintenant)

1. **Retenue** : la candidate qui valide le plus souvent en 30 jours sur les achats 2012-2021 (filtre comme 2026). À
   égalité à 1 point près, la plus simple, dans l'ordre A, B, C, F, D, E.
2. **Elle remplace la version de la vague 12 seulement si** :
   - sur les achats 2023 - août 2026 (filtre comme 2026), elle valide au moins **3 points** de plus que A ;
   - **et** sur les achats 2025, elle ne valide pas moins que A (1 point de tolérance).

   Sinon, on garde A.
3. Les deux comptes sont jugés séparément ; on donne aussi les résultats avec le filtre deux fois plus faible et sans
   filtre.

**À savoir avant d'y croire** :
- les leviers ont été proposés après avoir vu le plafond de la vague 12 ;
- 2023-2026 a déjà été regardé souvent ;
- le filtre est simulé ;
- la limite du jour de Bulenox est supposée « douce ».
