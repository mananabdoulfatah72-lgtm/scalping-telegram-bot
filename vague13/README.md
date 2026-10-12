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

## Contrôles (`test_vague13.py`)

- **Sans levier**, `defi13` puis `master13` redonnent exactement `moteur4.parcours4` avec la limite de 30 jours, sur
  250 achats par réglage (Legacy et Momentum, taille 4 sans frein, taille 1 frein, taille 4 frein). Issues, séances,
  retraits séance par séance : tout est identique.
- **Arrêt à l'objectif** : un challenge validé finit sa dernière séance à 3 000 $ ou plus, et jamais avant.
- **Taille adaptative** : la taille jouée chaque séance suit exactement les règles de C, D et F.

## Résultats (12 octobre 2026) : `vague13.txt`

### Jugement fixé à l'avance

**Retenue : D (arrêt à l'objectif + fin de course), pour les deux comptes. Elle remplace la version de la vague 12.**

| Bulenox Legacy, filtre comme 2026 | Validé 2012-2021 (choix) | Validé 2023-2026 | Validé 2025 | Perdu 2023-2026 | Net moyen 24 mois (2012-20 / 2023-24) | Achats perdants (2023-24) |
|---|---|---|---|---|---|---|
| A : 4 MNQ (vague 12) | 41 % | 40 % | 32 % | 45 % | +1 149 / +1 814 $ | 52 % |
| B : + arrêt à l'objectif | 51 % | 55 % | 44 % | 36 % | +1 491 / +2 335 $ | 38 % |
| C : + arrêt + protection | 49 % | 55 % | 43 % | 26 % | +1 419 / +2 289 $ | 39 % |
| **D : + arrêt + fin de course** | **53 %** | **55 %** | **45 %** | 37 % | **+1 552 / +2 354 $** | **38 %** |
| E : + arrêt + protection + fin de course | 51 % | 56 % | 44 % | 27 % | +1 466 / +2 351 $ | 38 % |
| F : + arrêt + prudence près du but | 51 % | 55 % | 44 % | 35 % | +1 494 / +2 322 $ | 39 % |

- **Momentum** : D valide 51 % (choix), 52 % (vérification) et 43 % (2025), contre 40, 38 et 30 % pour A.
- **Sans filtre** (Legacy, 2023-2026) : D valide 49 %, contre 32 % pour A.
- **Filtre deux fois plus faible** : D valide 53 %.

### Ce qu'il faut en retenir

- **Presque tout le gain vient de l'arrêt à l'objectif (B).** En 4 MNQ, le compte touche souvent +3 000 $ dans la
  journée puis les rend avant le soir. Fermer tout à ce moment fait gagner 10 à 15 points.
- **La fin de course (D) ajoute 2 points sur le choix et rien sur la vérification** (55 % contre 55 %). Elle demande
  en plus la taille 6 pendant les 5 dernières séances, donc un changement du bot. B est presque aussi bon et plus
  simple.
- **La protection (C, E) perd moins de challenges** (26-27 % contre 36-37 %), mais n'en valide pas plus. Un challenge
  perdu coûte autant qu'un challenge expiré.

### Ce qui pourrait rendre ces chiffres trop beaux

- **L'arrêt suppose qu'un ordre limite à +3 050 $ est rempli dès que la minute touche ce niveau.** En vrai, il peut
  manquer d'un tick.
- **Il faut savoir comment Bulenox compte l'objectif.** Après l'arrêt, le compte reste à plat jusqu'au soir : le
  solde du soir est donc au-dessus de l'objectif, dans les deux lectures.
- **Les leviers ont été proposés après avoir vu le plafond de la vague 12.** 2023-2026 a déjà été regardé souvent,
  et le filtre est simulé.
- **La limite du jour est supposée « douce ».**

### Ce que le bot doit savoir faire

- **Arrêt à l'objectif** : un réglage « solde visé du challenge » (53 050 $). Le bot en déduit chaque matin son plafond
  du jour (solde visé − solde du matin), avec le mécanisme de plafond déjà codé pour le Master.
- **Fin de course (D)** : la date de fin du challenge, et la taille 6 pendant ses 5 dernières séances. La borne de
  « MNQ par source » doit passer de 5 à 6.
