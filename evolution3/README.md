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

## Version 2 des règles (1er octobre 2026, toujours avant tout calcul)

L'utilisateur demande d'explorer aussi le RSI, le MACD, les bandes de Bollinger, l'order flow, l'ICT/SMC,
d'autres sources d'information, et de juger aussi le risque (pertes, Sharpe). Aucune évolution n'a encore
tourné : les règles sont élargies ici, avant de lancer quoi que ce soit. Tout ce qui n'est pas changé
ci-dessous reste comme plus haut.

### 7 marchés au lieu de 5

On ajoute le **Nasdaq 100 (NQ, micro MNQ, 2 $ le point)** et le **S&P 500 (ES, micro MES, 5 $ le point)**,
séance 9 h 30 - 16 h, barres d'une minute Databento de `intraday/` (2011-2026). Mêmes frais (1 $ par ordre,
1 tick de glissement par ordre), mêmes périodes : entraînement **2016-2019** (les années 2011-2015 ne sont
pas utilisées), validation 2020-2022, coffre 2023 - septembre 2026.

Le coffre 2023-2026 du NQ a déjà servi à d'autres tests (zone de bruit, tournois). Il reste valable pour
juger une stratégie nouvelle, choisie sans le regarder ; chaque ouverture est comptée dans le registre.

### 16 familles au lieu de 7

Les 7 familles de départ restent. La famille 0 (écart à la moyenne sur L barres de plus de Z écarts-types)
est exactement la **bande de Bollinger** (L, Z) ; la famille 1 est la **cassure de Donchian**, la famille 2
l'**ORB**, la famille 3 les **bandes de VWAP**. On ajoute :

| Famille | Hypothèse : à la clôture de la barre j, signal d'achat si… (vente : le symétrique) |
|---|---|
| 7 RSI | le RSI de Wilder sur L barres dépasse 50 + 15 × Z (vente : passe sous 50 − 15 × Z). « Suivre » = momentum ; « contrer » = le classique surachat / survente |
| 8 MACD | l'histogramme du MACD (moyennes exponentielles L et 26/12 × L, signal 9/12 × L) dépasse Z × 0,1 × √L × écart-type (≈ Z écarts-types de l'histogramme d'une marche au hasard) |
| 9 Bollinger squeeze | les bandes étaient resserrées à la barre j − 1 (écart-type sur L barres < 0,8 × sa moyenne des 100 barres d'avant) et la clôture sort de la bande moyenne + Z écarts-types |
| 10 Balayage de liquidité (ICT) | le plus bas de la barre passe sous le plus bas des L barres précédentes d'au moins (Z − 0,25) × 0,5 × écart-type, mais la barre clôture au-dessus de ce niveau (chasse aux stops puis rejet). « Suivre » = acheter le rejet, comme l'ICT |
| 11 Balayage de la veille (ICT) | même chose avec le plus bas (vente : le plus haut) de la séance précédente |
| 12 Fair value gap (ICT/SMC) | un FVG haussier s'est formé (plus bas de la barre k > plus haut de la barre k − 2, écart ≥ Z × 0,5 × écart-type) il y a au plus L barres, et le prix revient dedans sans clôturer sous son bas. Un seul trade par FVG ; un FVG est oublié si une clôture passe sous son bas |
| 13 Order flow estimé | la pression acheteuse estimée sur L barres, Σ volume × (2 × clôture − haut − bas) / (haut − bas) divisé par Σ volume, dépasse Z × 0,5 / √L |
| 14 Pic de volume | le volume de la barre dépasse (1 + Z) fois le volume moyen de la même barre sur les 20 séances jouables d'avant, et la barre est haussière (clôture > ouverture). « Suivre » = continuation ; « contrer » = épuisement |
| 15 Marché leader (nouvelle source) | le marché leader a monté sur les L dernières barres plus que ce marché, en écarts-types : z(leader) − z(marché) > Z, avec z = rendement sur L barres / (écart-type des rendements de 5 minutes sur 20 barres × √L). Leaders : NQ ← ES, ES ← NQ, RTY ← ES, YM ← ES, CL ← ES, GC ← euro, euro ← or. Pas de signal quand le leader n'a pas de cours à cette heure-là |

**Ce qui n'est pas testé ici, et pourquoi :**
- **Le vrai order flow** (sens des transactions, footprint, carnet) a déjà été testé dans `ordres/` sur
  les transactions du ES avec leur sens : aucun signal ne battait les frais. Les barres d'une minute
  n'ont pas le sens des transactions ; la famille 13 n'en est qu'une estimation.
- **Les order blocks** (ICT) n'ont pas de définition unique et mesurable ; les balayages et les FVG
  couvrent les idées ICT qu'on peut écrire sans ambiguïté. Les « kill zones » sont couvertes par les
  gènes début et durée.

Le gène L va de 2 à 120 barres pour toutes les nouvelles familles (âge maximal du FVG pour la famille 12).
Il ne sert pas aux familles 11 et 14.

### Boucle, finalistes et coffre ajustés

- **256 stratégies par génération** ; élites : les 4 meilleures et la meilleure de chaque famille ;
  **14 descendants par famille** ; le reste en immigrants. 80 générations, 8 graines, et 8 graines sur
  bruit.
- Bruit : les séances du marché sont mélangées comme plus haut ; le volume moyen par barre est recalculé
  sur le bruit ; le marché leader garde ses vrais cours. Le lien entre les deux est donc détruit.
- Finalistes : au plus un par marché, soit **au plus 7**. Même règle qu'avant, et toujours la barrière
  du meilleur Sharpe de validation obtenu sur bruit pour le même marché.
- **Coffre, une seule fois** : t ≥ **2,6** sur 2023-2026 (correction pour 7 finalistes), au moins
  3 années positives sur 4.
- On publie aussi, pour chaque finaliste et sur chaque période : Sharpe, **perte maximale** (en $ pour
  1 micro et en % de 50 000 $), part de jours gagnants, gain moyen et perte moyenne par trade. Ces mesures
  servent à décrire, pas à choisir : la sélection reste celle écrite ci-dessus.
