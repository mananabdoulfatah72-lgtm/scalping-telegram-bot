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

## Résultat (3 octobre 2026) : `resultats.txt`

**Contrôle** : sans compte et sans protection, avril - 25 septembre 2026 avec le vrai delta, le moteur redonne
exactement +4 366,0 $, comme le rejeu à la journée.

Score = % réussis − % perdus, challenges suivis jusqu'à 252 séances.

| Compte | Protection | 2011 - 2022 : réussis / perdus / score | 2023 - 2026 : réussis / perdus / score |
|---|---|---|---|
| Phidias Premium | **A** | 19,8 / 3,4 / +16,4 | **65,1 / 27,1 / +38,0** |
| | B | 19,8 / 3,4 / +16,4 | 52,4 / 22,9 / +29,5 |
| | C | 23,1 / 0,0 / +23,1 | 33,7 / 21,7 / +12,0 |
| | B + C | 23,1 / 0,0 / +23,1 | 33,7 / 13,9 / +19,9 |
| DayTraders Trail | **A** | 31,2 / 1,4 / +29,8 | **68,7 / 23,5 / +45,2** |
| | B | 26,7 / 4,5 / +22,3 | 66,3 / 14,5 / +51,8 |
| | C | 30,0 / 0,0 / +30,0 | 48,2 / 25,9 / +22,3 |
| | B + C | 28,7 / 1,2 / +27,5 | 31,3 / 25,9 / +5,4 |
| | D | 31,2 / 1,4 / +29,8 | 62,0 / 33,7 / +28,3 |
| | B + C + D | 28,9 / 1,2 / +27,7 | 34,9 / 26,5 / +8,4 |
| DayTraders EOD | **A** | 25,7 / 7,1 / +18,6 | **60,8 / 34,9 / +25,9** |
| | B | 25,5 / 4,9 / +20,6 | 56,6 / 25,9 / +30,7 |
| | C | 27,3 / 2,6 / +24,7 | 34,3 / 60,8 / −26,5 |
| | B + C | 27,1 / 2,6 / +24,5 | 27,7 / 29,5 / −1,8 |

**Décision selon la règle fixée : aucune protection n'est retenue, pour aucun compte.**
- Phidias et EOD : le stop du RSI(2) (C) gagne sur 2011 - 2022, mais s'effondre sur 2023 - 2026. Il est refusé à la
  vérification.
- Trail : rien ne bat A de 3 points sur 2011 - 2022.

**Lecture.**
- Le gain du RSI(2) vient justement des trades qui baissent d'abord puis rebondissent. Le couper pendant la
  baisse supprime le rebond :
  - en 2026, le stop C coupe le trade de juin (5 au 11 juin) et celui de juillet (24 au 30 juillet) avant leur
    rebond ;
  - avec n'importe laquelle des protections, aucun départ d'avril à septembre 2026 ne valide avant le 25 septembre.
- Le coupe-circuit B évite des pertes sur 2023 - 2026 chez DayTraders (Trail : 14,5 % perdus au lieu de 23,5 %).
  Mais il fait moins bien que A sur 2011 - 2022. La règle ne le retient donc pas. On peut le suivre en virtuel,
  sans l'adopter.
- 2011 - 2022 : à 1 MNQ, le NQ valait 2 000 à 16 000 points, les gains en dollars étaient bien plus petits.
  70 % des challenges n'y sont pas finis en 252 séances, ce qui laisse peu d'information pour choisir.
- **Sur 2023 - 2026 (zone non filtrée + RSI(2), sans protection), DayTraders Trail fait au moins aussi bien que
  Phidias** :
  - Trail : 68,7 % réussis, 23,5 % perdus, médiane de 109 séances ;
  - Phidias : 65,1 % réussis, 27,1 % perdus, médiane de 158 séances.
  Le moins bon résultat de DayTraders sur avril - septembre 2026 tient à une seule période de six mois (la règle
  des 50 % après le 11 juin, puis le 29 juillet avant le blocage de la limite).
- Avec le compte EOD de DayTraders, la limite de 1 250 $ par jour fait perdre plus souvent (34,9 %).

## Piste 2 : « zone d'abord », et la phase financée (règles fixées le 3 octobre 2026, avant le calcul)

**Pourquoi.** L'utilisateur ne veut pas payer deux challenges dans l'année. Chez DayTraders Trail, la limite de
perte monte avec le plus haut du compte jusqu'à ce que le compte atteigne +2 500 $. Ensuite, elle reste bloquée
à 50 000 $ (le « coussin »). Les comptes perdus le sont surtout avant ce blocage, souvent pendant un trade du
RSI(2), qui peut baisser plusieurs jours avant de rebondir.

**Variante Z (une seule, fixée avant le calcul) :**
- la zone (filtrée quand le vrai delta existe) trade dès le premier jour ;
- le RSI(2) n'ouvre une position qu'une fois le compte monté à +2 500 $ au-dessus du départ, valeur mesurée à
  la décision de 15 h 50. Une fois ce niveau atteint, le RSI(2) reste autorisé jusqu'à la fin du challenge.
- Comptes, départs et jugement : exactement ceux de la section précédente. Choix sur 2011 - 2022 (score + 3 points
  au moins), vérification sur 2023 - 2026 (au moins aussi bien que A).
- Publié aussi : les départs de 2025 à part (l'année la plus proche d'aujourd'hui), avec un suivi complet de 252
  séances.

**Phase financée DayTraders (compte Pro, après un challenge Trail 50K réussi), rejouée sans rien changer au bot :**
- part le lendemain de la réussite, à 50 000 $ ;
- limite de perte : plus haut atteint en temps réel − 2 500 $, bloquée à 50 000 $ ;
- retrait possible à la clôture si toutes ces conditions sont réunies :
  - au moins 8 jours qualifiants depuis le dernier retrait (jour qualifiant : +200 $ ou plus) ;
  - meilleur jour ≤ 30 % du gain depuis le dernier retrait ;
  - solde ≥ 51 000 $ + 500 $ ;
- montant du retrait : min(2 000 $, solde − 51 000 $), 100 % pour le trader ;
- le compte est suivi 252 séances au plus après la réussite. Publié : part des comptes qui font au moins un
  retrait, montant total reçu, séances jusqu'au premier retrait, part des comptes perdus.
- Sources des règles (sites d'avis et pages d'aide citées par les moteurs de recherche ; le site de DayTraders
  est bloqué depuis cet environnement) : 8 jours, 30 %, 2 000 $, 500 $, coussin de 1 000 $, 100 %. Ces règles
  sont à vérifier avant l'achat.
