# Combiner les pistes qui tiennent : règles fixées avant le calcul (15 novembre 2026)

**La demande.** Combiner toutes les pistes efficaces pour voir s'il y a un potentiel à ajouter à l'automatisation
sur Quantower.

**Les pistes, d'après `terminal_backtest/comparatif.json`** (NQ, 1 MNQ, 20 févr. 2012 → 25 sept. 2026). « Hors
marché » : une fois retirée la part du gain qui vient de la simple hausse du NQ.

| Piste | Gain par an | t | t hors marché | Sort |
|---|---|---|---|---|
| Zone de bruit (Bot 3 en 1) | +4 050 $ | 4,85 | 5,01 | gardée |
| Supertrend 10-3 en 5 minutes, limite 400 $ | +3 986 $ | 2,15 | 2,15 | gardée |
| Nuit (16 h → 9 h 30) | +5 772 $ | 3,06 | 1,81 | gardée pour information |
| Les 7 stratégies quotidiennes du terminal, dont le dual momentum | — | — | au plus 1,70 | écartées : aucune ne tient hors marché, et elles gardent la position plusieurs jours |

## Combinaisons testées (aucune autre)

| | Combinaison | Compte |
|---|---|---|
| A | Zone 1 MNQ seule | Bulenox (repère) |
| B | Supertrend 1 MNQ seul, limite du jour 400 $ | Bulenox (repère) |
| C | Zone 1 MNQ + Supertrend 1 MNQ, sur le même compte | Bulenox |
| D | Zone 2 MNQ + Supertrend 1 MNQ, sur le même compte | Bulenox |
| E | Zone + Supertrend + Nuit, 1 MNQ chacun | information seulement |
| F | Zone + Nuit, 1 MNQ chacun | information seulement |

Chaque bot garde sa propre limite de perte du jour : 400 $ pour le Supertrend, 1 000 $ pour la zone.

## Mesures

1. **Gain par séance** (1 MNQ, prix d'aujourd'hui, 3 $ de frais par aller-retour), 20 févr. 2012 → 25 sept. 2026 :
   corrélations entre les pistes ; pour chaque combinaison : gain par an, t, t depuis 2023, pire baisse, pire
   séance, années perdantes.
2. **Compte Master Bulenox**, option 2 : plancher recalculé en fin de journée (plus haut solde de fin de journée
   moins 2 500 $, bloqué à 50 100 $), compte perdu si sa valeur touche le plancher pendant la séance.
   - Départ : solde 51 000 $, plancher 49 200 $. 250 séances. Un départ à chaque séance de 2011 à novembre 2026,
     puis seulement depuis 2023.
   - Issues : 53 600 $ atteint en fin de journée (premier retrait possible) ; perdu par le plancher ; perdu par
     l'inactivité (5 séances de suite sans aucun trade) ; ni l'un ni l'autre.
   - Valeur du compte en séance : somme des positions des deux bots, lue au plus bas et au plus haut de chaque
     minute.
   - La nuit n'entre pas dans ce simulateur : il n'a que les minutes de 9 h 30 à 16 h. Les combinaisons E et F
     n'ont donc que la mesure 1.
3. **Contrôle du simulateur** : A et B seuls doivent redonner, à 2 points près, les résultats déjà publiés avec
   l'ancien simulateur (plancher en fin de journée, 250 séances, départs depuis 2011) : B = 43 % de retraits et 55 %
   de Masters perdus ; A sans la règle d'inactivité = 67 % et 20 %.

## Critère, fixé avant le calcul

C ou D est **retenue** si, sur les départs depuis 2011 **et** sur ceux depuis 2023, elle a à la fois :
1. aucun Master perdu par inactivité ;
2. au moins 10 points de Masters perdus en moins que le Supertrend seul (B) ;
3. au moins autant de premiers retraits que le Supertrend seul (B).

Sinon elle n'est pas retenue. E et F sont publiées pour information, sans décision.

## Résultats de la première vague (calculés après avoir fixé les règles) : `combinaison.py`, `combinaison.txt`

**Contrôle du simulateur : passé.** B seul donne 43,0 % de retraits et 55,6 % de Masters perdus (attendu 43 et 55) ;
A sans la règle d'inactivité donne 66,5 % et 19,8 % (attendu 67 et 20).

**Gain par séance** (1 MNQ, 21 févr. 2012 → 25 sept. 2026, 3 633 séances) :

| Combinaison | Gain par an | t | t depuis 2023 | Pire baisse | Pire séance | Années perdantes |
|---|---|---|---|---|---|---|
| A. Zone 1 MNQ seule | +4 046 $ | 4,85 | 2,12 | −3 275 $ | −1 008 $ | 1 (2025) |
| B. Supertrend 1 MNQ seul | +3 986 $ | 2,15 | 0,48 | −13 038 $ | −424 $ | 4 (2013, 2017, 2024, 2025) |
| C. Zone 1 + Supertrend 1 | +8 032 $ | 3,49 | 1,13 | −10 178 $ | −1 415 $ | 3 (2013, 2017, 2025) |
| D. Zone 2 + Supertrend 1 | +11 729 $ | 4,03 | 1,28 | −13 308 $ | −1 444 $ | 2 (2017, 2025) |
| E. Zone + Supertrend + Nuit | +13 711 $ | 4,54 | 2,05 | −18 340 $ | −4 930 $ | 0 |
| F. Zone + Nuit | +9 724 $ | 4,75 | 2,59 | −16 473 $ | −4 522 $ | 1 (2022) |
| Nuit seule (information) | +5 679 $ | 3,06 | 1,90 | −21 376 $ | −3 918 $ | 2 (2016, 2022) |

Corrélations entre les gains du jour : zone et Supertrend **0,37** (ils gagnent et perdent souvent les mêmes jours) ;
zone et nuit 0,01 ; Supertrend et nuit 0,05 ; nuit et NQ 0,49.

**Compte Master, option 2, depuis 51 000 $ / 49 200 $, 250 séances** (53 600 $ atteint / perdu par le plancher /
perdu par l'inactivité, en %) :

| Combinaison | Départs depuis 2011 | Départs depuis 2023 |
|---|---|---|
| A. Zone seule | 4,7 / 1,0 / **94,3** | 0,0 / 2,5 / **97,5** |
| A sans la règle d'inactivité (repère) | 66,5 / 19,8 / — | 46,1 / 35,4 / — |
| B. Supertrend seul | 43,0 / 55,6 / 0 | 43,8 / 56,2 / 0 |
| C. Zone 1 + Supertrend 1 | 50,6 / 49,4 / 0 | 54,5 / 45,5 / 0 |
| D. Zone 2 + Supertrend 1 | 47,0 / 53,0 / 0 | 49,7 / 50,3 / 0 |

**Verdict : ni C ni D n'est retenue.** C règle l'inactivité et fait mieux que le Supertrend seul (6 à 11 points de
Masters perdus en moins, 8 à 11 points de retraits en plus), mais il lui manque 4 points sur les départs depuis 2011
pour passer la condition 2, et le Master reste perdu près d'une fois sur deux. D est moins bonne que C : doubler la
zone accélère les pertes autant que les gains.

## Deuxième vague : le Supertrend seulement en secours (règles écrites le 15 novembre 2026, après la première vague, avant tout calcul de celle-ci)

**L'idée.** Dans C, le Supertrend trade tous les jours et apporte presque toute la baisse. Or il ne sert au compte
que pour une chose : éviter l'inactivité quand la zone reste silencieuse. Ici il ne tourne que ces jours-là. C'est
un vrai trade de stratégie, pas une « activité artificielle ».

| | Combinaison |
|---|---|
| G2 | Zone 1 MNQ tous les jours ; Supertrend 1 MNQ (limite 400 $) seulement la séance qui suit 2 séances de suite sans aucun trade |
| G3 | La même, après 3 séances de suite sans aucun trade |

- Le compteur de séances sans trade repart de 0 au début de chaque compte simulé et dès qu'un des deux bots trade.
- Le Supertrend de secours tourne toute la séance, comme d'habitude. Sa décision est connue la veille.
- Même simulateur, mêmes départs, même compte que la première vague.

**Critère (le même)** : G2 ou G3 est retenue si, sur les départs depuis 2011 et sur ceux depuis 2023, elle n'a aucun
Master perdu par inactivité, au moins 10 points de Masters perdus en moins que le Supertrend seul, et au moins
autant de premiers retraits que lui.
