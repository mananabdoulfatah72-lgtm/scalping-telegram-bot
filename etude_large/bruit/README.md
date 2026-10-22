# Vague « le bruit dans la zone » : jouer le retour au VWAP à l'intérieur de la zone, en relais de la zone (règles fixées le 22 octobre 2026, avant tout calcul)

## Demande de l'utilisateur (22 octobre 2026)

Des variantes extérieures qui viennent s'ajouter au bot, de nouvelles pistes, avec un raisonnement de quant.

## L'idée

La zone de Zarattini, Aziz et Barbon (2024) sépare deux régimes : **à l'intérieur** de la zone, les mouvements sont du
bruit ; **au-delà**, une tendance commence et la zone la suit. Le bot ne joue que le second régime, et il perd les
jours sans tendance (fausses cassures). Le complément logique joue le premier : vendre près du haut de la zone, viser
le VWAP, et couper **exactement là où la zone achète**. Les deux se relaient au même prix : si le prix casse, la
vente est coupée et la zone prend l'achat.

**Pas encore testé** : la recherche a testé des retours à la moyenne génériques (bandes de VWAP sur l'ES dans
`ordres/`, Bollinger et retournement de mi-journée dans `tournoi2/`, versions « contrer » de `evolution3/`), tous
perdants, et la zone inversée (partie A, A5 : vendre **la cassure**). Jamais un retour à la moyenne borné par la zone
elle-même, avec le stop sur sa limite.

## Règles (fixées maintenant)

**Données** : minutes du NQ (2011 - 20 octobre 2026, recherche + robot) et de l'ES (2011 - 25 septembre 2026,
recherche), séance 9 h 30 - 16 h. Zone du bot à chaque minute m : limite haute UB = max(ouverture, veille) × (1 + σ_m),
limite basse LB = min(ouverture, veille) × (1 − σ_m) (`delta_mesures/etude.py`, `preparer`). Pas de trade les jours
d'annonce de la Fed (comme le bot).

**Seuil d'entrée k** (3 variantes) : 0,5, 0,75 et 0,9. Seuil de vente : max(ouverture, veille) × (1 + k σ_m) ; seuil
d'achat : min(ouverture, veille) × (1 − k σ_m).

À chaque clôture de minute de 10 h à 15 h, sans position :
- **vente** si la clôture est au-dessus du seuil de vente, sous UB, et au-dessus du VWAP ;
- **achat** si la clôture est sous le seuil d'achat, au-dessus de LB, et sous le VWAP.

Sortie à la clôture de la première minute où :
- le prix revient au VWAP (objectif) ;
- ou la clôture passe UB pour une vente, LB pour un achat (stop, là où la zone entre) ;
- ou 15 h 59.

Au plus 3 trades par séance. Frais par aller-retour : 1,5 point sur le NQ (MNQ), 0,9 point sur l'ES (MES), comme toute
la recherche.

**6 essais** : 3 seuils × 2 marchés (NQ, ES). Mesure : rendement net de chaque séance (0 sans trade), t de la moyenne.
**Exploration** 2011 - 2022, **coffre** 2023 - 2026.

## Décision (fixée maintenant)

1. **Survie** : t net ≥ 2,0 en exploration et retenu par Benjamini-Hochberg à 10 % sur les 6 essais, puis t net ≥ 1,5
   au coffre.
2. **Complément** : corrélation avec la zone du bot (NQ, sans les jours de la Fed) < 0,3 en exploration, et Sharpe de
   zone + survivante (à risque égal) plus haut que la zone seule au coffre.
3. **Challenges** (moteur de la partie D, avec les plus hauts et plus bas des minutes), si 1 et 2 réussissent : Lucid
   Flex 50K (zone 1 MNQ + survivante 1 contrat) et Bulenox 50K (zone 3 MNQ + survivante 3 contrats) contre la zone
   seule. **Ajoutée au bot** (en argent virtuel d'abord) si, sur les départs 2023 - 2026, elle valide au moins 3 points
   de plus que la zone seule sans perdre plus de 3 points de challenges en plus.

Pour information : corrélation avec la zone, et gain moyen les jours où la zone perd.

## Limites écrites d'avance

- 2023 - 2026 a servi souvent pour la zone du NQ ; pour cette stratégie, c'est la première mesure.
- Exécution à la clôture de la minute qui décide, sans glissement en plus des frais comptés.
