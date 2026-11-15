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
