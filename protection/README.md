# Protéger le compte du bot 3 en 1 (règles fixées le 3 octobre 2026, avant le calcul)

## Pourquoi

Le bot 3 en 1 (zone de bruit filtrée par le vrai delta + RSI(2), 1 MNQ chacun) a frôlé la perte le 29 juillet
2026. Rejoué minute par minute, il est descendu à 50 $ de la limite de Phidias. Chez DayTraders (compte Trail),
la moitié des départs de juin et juillet sont perdus. L'utilisateur demande une protection contre ce genre de
journée, et des résultats chez DayTraders aussi proches que possible de ceux de Phidias.

Une règle choisie en regardant le 29 juillet serait trompeuse : elle sauverait ce jour-là par construction. Les
protections ci-dessous sont donc fixées **avant** tout calcul. Elles sont jugées sur 15 ans de zone + RSI(2), là où
le vrai delta n'existe pas (zone non filtrée). Avril - septembre 2026, avec le vrai delta, n'est montré qu'à titre
descriptif.

## Le moteur

- `robot_main.py` : copie de `zone/robot.py` de main (commit a3c585f). Ce sont les mêmes fonctions que le robot :
  `tableaux`, `zone_de_bruit` (V1) et `rsi2`.
- Données : `intraday/donnees/nasdaq100_1min.csv.gz` (NQ, 1 minute, de 9 h 30 à 16 h), du 3 janvier 2011 au
  25 septembre 2026. La nuit n'y est pas : une position du RSI(2) ne voit que l'écart entre la clôture et
  l'ouverture suivante.
- Positions, en MNQ :
  - zone : 1 MNQ, entrée à la clôture de la minute du signal, sortie à la clôture de la minute de sortie ;
  - RSI(2) : 1 MNQ, entrée et sortie à l'ouverture de la minute de décision (15 h 50).
- Frais, comme le robot :
  - zone : 1,5 point par aller-retour ;
  - RSI(2) : 1 $ + 1 tick par ordre.
- Valeur du compte minute par minute : plus haut et plus bas de chaque minute selon la position nette. Dans une
  même minute, le plus haut compte avant le plus bas (le cas le plus dur pour une limite qui suit le plus haut).
- Une sortie déclenchée par une protection est exécutée au niveau de déclenchement. Si le prix ouvre déjà
  au-delà, elle est exécutée à l'ouverture. Elle paie 1 tick de glissement en plus des frais.

## Les comptes

| | Phidias Premium 50K | DayTraders Trail 50K | DayTraders EOD 50K |
|---|---|---|---|
| Objectif | +4 000 $ | +3 000 $ | +3 000 $ |
| Limite de perte | plus haut solde de fin de journée − 2 500 $ | plus haut atteint en temps réel − 2 500 $, bloquée à 50 000 $ | plus haut solde de fin de journée − 2 000 $ |
| Surveillance | en temps réel | en temps réel | en temps réel |
| Limite par jour | aucune | aucune | 1 250 $ sous la clôture de la veille : compte perdu |
| Régularité | aucune | meilleur jour ≤ 50 % du gain | meilleur jour ≤ 50 % du gain |
| Jours minimum | 1 | 2 jours à +200 $ ou plus | 2 jours à +200 $ ou plus |

- Le solde de fin de journée compte la position du RSI(2) à la dernière clôture de la séance.
- On ne sait pas si la limite de l'EOD arrête de monter à 50 000 $ : le compte est joué sans blocage, et avec un
  blocage à 50 000 $ à titre descriptif.

## Les protections (fixées avant le calcul)

- **A, aucune** : le bot tel qu'il est.
- **B, coupe-circuit à 300 $** : dès que la valeur du compte arrive à 300 $ de la limite de perte (ou de la limite
  par jour, la plus proche des deux), le bot ferme tout et ne trade plus de la journée. Le lendemain, il reprend :
  - la zone normalement ;
  - le RSI(2) à sa décision suivante, si sa règle est toujours en position.
- **C, stop du RSI(2) à 600 $** : un trade du RSI(2) est fermé s'il perd 600 $ (300 points, environ 2,5 fois
  l'écart-type d'un jour en position). Le RSI(2) attend ensuite que sa règle sorte avant de pouvoir racheter.
- **B + C** : les deux ensemble.
- **D, plafond du jour à 1 400 $** (comptes DayTraders seulement, à cause de la règle des 50 %) : dès que le gain du
  jour atteint 1 400 $, le bot ferme tout et ne trade plus de la journée. Le RSI(2) reprend à sa décision suivante.
  Joué seul et avec B + C.

## Le jugement

- Départs : une séance sur cinq, quand le RSI(2) est à plat à l'ouverture. Chaque challenge est suivi jusqu'à sa
  réussite, sa perte, ou 252 séances au plus.
- Score d'une protection, pour chaque compte : % de challenges réussis − % de challenges perdus.
- Choix sur les départs de **2011 - 2022**. Une protection est retenue pour un compte si son score dépasse celui de
  A d'au moins 3 points. Si plusieurs le font, on prend le meilleur score.
- Vérification sur les départs de **2023 - 2026** : la protection retenue doit y faire au moins aussi bien que A
  (score). Sinon, on garde A.
- Publié dans tous les cas : réussis, perdus, pas finis, séances médianes jusqu'à la réussite, pour chaque compte
  et chaque protection. Avril - septembre 2026 avec le vrai delta (départ le 1er de chaque mois et à chaque
  séance), à titre descriptif.
