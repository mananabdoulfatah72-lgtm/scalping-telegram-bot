# Tournoi intraday : qui peut rivaliser avec la zone de bruit ?

## Règles (fixées le 30 septembre 2026, avant tout calcul)

Des stratégies intraday connues, **avec les paramètres de leur source, sans aucun réglage**, testées
sur le Nasdaq (NQ) et le S&P 500 (ES). La zone de bruit sert de référence. Chaque stratégie passe
ensuite par la machine de tri (`evolution/`) : exploration, contrôle sur bruit, puis coffre ouvert une
seule fois.

### Les stratégies (14, chacune sur NQ et ES, soit 28 essais)

Séance de 9 h 30 à 16 h (New York), minutes Databento. Tout est fermé à 16 h. Pas de trade le jour d'un
changement d'échéance.

| # | Stratégie | Règle | Source |
|---|---|---|---|
| 1 | Range d'ouverture 15 min | cassure du plus haut / plus bas de 9 h 30-9 h 45, stop de l'autre côté, un trade par jour | Crabel (1990) ; Zarattini, Barbon, Aziz (2024) |
| 2 | Range d'ouverture 30 min | idem, 9 h 30-10 h | idem |
| 3 | Range d'ouverture 60 min | idem, 9 h 30-10 h 30 | idem |
| 4 | Cassure de volatilité de Williams | ouverture ± 0,5 × amplitude de la veille, stop à l'ouverture | Williams (1999) |
| 5 | Étirement de Crabel | ouverture ± moyenne sur 10 jours de min(haut − ouverture, ouverture − bas), stop au niveau opposé | Crabel (1990) |
| 6 | Cassure de la veille | au-dessus du plus haut ou sous le plus bas de la veille, stop au milieu de la veille | classique |
| 7 | Momentum de la 1re heure | à 10 h 30, dans le sens de 9 h 30-10 h 30, jusqu'à la clôture | Gao, Han, Li, Zhou (2018), version 1re heure |
| 8 | Tendance VWAP | toutes les 30 min de 10 h à 15 h 30, du côté du prix par rapport au VWAP du jour | pratique courante |
| 9 | Continuation du gap | gap ≥ 0,25 % : dans le sens du gap à 9 h 31, stop à la clôture de la veille | classique |
| 10 | Comblement du gap | gap entre 0,15 % et 1 % : contre le gap à 9 h 31, objectif la clôture de la veille, stop à une fois le gap | classique |
| 11 | Retournement après 30 min extrêmes | si 9 h 30-10 h dépasse 1,5 fois sa moyenne sur 20 jours, contre ce mouvement jusqu'à la clôture, stop à l'extrême de 9 h 30-10 h | classique |
| 12 | Tournant du mois | achat de 9 h 30 à 16 h le dernier jour de bourse du mois et les 3 premiers | McConnell, Xu (2008), version intraday |
| 13 | Veille de la Fed (le jour même) | les jours d'annonce de la Fed, achat de 9 h 30 à 13 h 55 | Lucca, Moench (2015), partie séance |
| 14 | Achat simple intraday | achat de 9 h 30 à 16 h tous les jours (contrôle) | — |
| réf. | Zone de bruit | celle du robot, code inchangé | Zarattini, Aziz, Barbon (2024) |

Les entrées sur cassure se font au niveau touché, ou à l'ouverture de la minute si le prix l'a sauté.
Si, avant toute entrée, les deux niveaux sont touchés dans la même minute, la journée est sautée. Si le
stop est touché dans la minute d'entrée, il compte. Frais : 1 $ par ordre et 1 tick de glissement par
ordre, soit 1,5 point de NQ ou 0,9 point d'ES par aller-retour.

### Le tri

1. **Exploration (2011-2022)** : t ≥ 2 sur les rendements quotidiens nets (en % du prix, jours sans
   trade compris).
2. **Contrôle sur bruit** : la même stratégie sur 20 versions des données où les minutes de chaque
   séance sont mélangées au hasard (la première minute reste en place). Il faut battre les 20 : son
   t réel doit dépasser le plus haut des 20 t sur bruit.
3. **Coffre 2023-2026, ouvert une seule fois**, pour les survivants des étapes 1 et 2. Le programme
   d'exploration ne charge pas ces années. Un survivant passe s'il a :
   - un t au moins égal à 1,65 en une seule épreuve, avec la correction de Bonferroni pour m
     survivants (seuil z de 0,05 / m : 1,65 si m = 1, 1,96 si m = 2, 2,13 si m = 3, 2,24 si m = 4...) ;
   - un résultat positif au moins 3 années sur 4.
4. **Comparaison avec la zone de bruit** :
   - même tableau pour la zone : exploration, bruit, coffre ;
   - corrélation des résultats quotidiens avec la zone ;
   - si un survivant passe le coffre, combinaison moitié-moitié en risque avec la zone, puis
     simulation du challenge 50K (bot coussin, comme dans `challenge/`).
5. Les 28 essais sont inscrits dans `fonds/essais.csv`. Aucune stratégie, aucun paramètre ni aucun
   marché ne sera ajouté ou changé après avoir vu les résultats.
