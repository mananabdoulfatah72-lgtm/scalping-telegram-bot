# Machine évolutive n°3 : 5 marchés, 7 hypothèses, sélection naturelle

L'utilisateur veut une exploration en masse, sur plusieurs marchés : des stratégies qui naissent, mutent,
sont testées, puis gardées ou éliminées. La machine n°1 (`evolution/`) le faisait sur NQ et ES seulement,
avec 4 espèces : rien n'a survécu, et la même machine faisait aussi bien sur du bruit. Celle-ci couvre
**5 autres marchés** et **7 familles d'hypothèses**, avec les mêmes contrôles.

## Règles (fixées le 1er octobre 2026, avant tout calcul)

### Marchés et données

Barres de 5 minutes construites depuis les minutes Databento de `zone_multi/`. Frais : 1 $ par ordre et
1 tick de glissement par ordre, sur le contrat micro.

| Marché | Micro | Séance (New York) | Barres par séance |
|---|---|---|---|
| Russell 2000 (RTY) | M2K | 9 h 30 - 16 h | 78 |
| Dow Jones (YM) | MYM | 9 h 30 - 16 h | 78 |
| Or (GC) | MGC | 8 h 20 - 13 h 30 | 62 |
| Pétrole (CL) | MCL | 9 h - 14 h 30 | 66 |
| Euro (6E) | M6E | 8 h 20 - 15 h | 80 |

Une séance n'est gardée que si elle est complète : première et dernière minute présentes, au plus
20 minutes manquantes. Pas de trade le jour d'un changement d'échéance.

| Période | Dates | Rôle |
|---|---|---|
| Entraînement | 2016 - 2019 (Russell : juillet 2017 - 2019) | la sélection naturelle |
| Validation | 2020 - 2022 | la porte : on vit ou on meurt |
| **Coffre** | **2023 - septembre 2026** | **ouvert une seule fois, à la fin, pour les finalistes** |

Pendant l'évolution, le programme **ne charge pas** les données d'après le 31 décembre 2022.

### Le génome : 7 familles × 2 sens, 11 gènes

| Famille | Hypothèse : à la clôture de la barre j, signal si… |
|---|---|
| 0 Écart à la moyenne | le prix s'écarte de sa moyenne sur L barres de plus de Z écarts-types |
| 1 Cassure de canal | le prix sort du plus haut ou du plus bas des L barres précédentes, de plus de Z × écart-type |
| 2 Range d'ouverture | le prix sort du range des L premières barres de la séance, de plus de Z × écart-type |
| 3 Écart au VWAP | le prix s'écarte du VWAP de la séance de plus de Z × écart-type |
| 4 Mouvement depuis l'ouverture | le mouvement depuis l'ouverture dépasse Z × écart-type |
| 5 Gap | l'écart entre l'ouverture et la clôture de la séance précédente dépasse Z fois sa moyenne sur 20 séances (entrée possible dès la première barre) |
| 6 Niveaux de la veille | le prix dépasse le plus haut ou passe sous le plus bas de la séance précédente, de plus de Z × écart-type |

« Écart-type » : celui des variations de prix sur les 20 dernières barres.

| Gène | Valeurs |
|---|---|
| famille | 0 à 6 |
| inverse | 0 : suivre le signal ; 1 : le contrer (retour à la moyenne) |
| marché | RTY, YM, GC, CL, 6E |
| L | 2 à 120 barres (range d'ouverture : 1 à 12) |
| Z | 0,25 à 3 |
| sens | les deux, achat seul, vente seule |
| stop | 0,10 % à 1,50 % du prix |
| objectif | 0,10 % à 3 % du prix |
| début | première barre où l'on peut entrer (de la 2e à la barre de 75 % de la séance) |
| durée | sortie forcée après 3 à 60 barres, et toujours à la fin de la séance |
| filtre | aucun, jours agités seulement, jours calmes seulement (amplitude de la veille comparée aux 20 séances d'avant) |

Exécution, comme la machine n°1 :
- signal à la clôture de la barre j, entrée à l'ouverture de la barre j + 1 ;
- une position à la fois ;
- le stop est vérifié avant l'objectif ;
- si le prix saute le stop, sortie à l'ouverture ;
- tout est fermé à la fin de la séance.

Un test vérifie qu'une barre future ne change aucun signal passé.

### La boucle

- 128 stratégies par génération.
- Élites gardées : les 4 meilleures et la meilleure de chaque famille.
- 105 descendants : 15 par famille, par tournoi dans la famille, croisement uniforme et mutation
  gaussienne (p = 0,18).
- Le reste est fait d'immigrants tirés au hasard.
- 80 générations, 8 graines.

**Fitness** (entraînement) : Sharpe annualisé des rendements quotidiens nets, réduit en proportion sous
150 trades.

**Porte** (validation 2020-2022) : Sharpe ≥ 0,5 et au moins 100 trades. Une stratégie qui ne passe pas
est « éliminée » ; une qui passe est « déployée » (gardée en vie).

### Les contrôles

1. **Évolution sur du bruit.** Même programme, 8 graines, sur des séances dont les barres de 5 minutes
   sont remises dans le désordre. Le résultat du jour et la volatilité sont gardés, toute structure
   intraday est détruite. On mesure ainsi ce que la sélection produit par hasard.
2. **Finalistes, fixés par une règle.** Pour chaque marché : parmi toutes les stratégies réelles
   évaluées avec une fitness ≥ 0,5 et qui passent la porte, celle au meilleur Sharpe de validation.
   Cela fait au plus 5 finalistes. Un finaliste n'est gardé que si son Sharpe de validation dépasse le
   meilleur obtenu sur bruit pour le même marché, avec le même filtre.
3. **Coffre, une seule fois.** Un finaliste passe s'il remplit tout ce qui suit :
   - t ≥ 2,5 sur 2023-2026 (correction pour 5 finalistes) ;
   - au moins 3 années positives sur 4.
4. **Combinaison.** Les survivants entrent dans le portefeuille avec la zone de bruit, jugé comme à
   l'étape 2 du tournoi 6 (2023-2026 et challenge).

Toutes les stratégies évaluées sont comptées dans `fonds/essais.csv`.

**Suivi** : une page au style de la machine n°1 rejoue chaque évolution génération par génération :
- naissances, mutations, morts et déploiements ;
- leader par marché ;
- comparaison avec le bruit.
