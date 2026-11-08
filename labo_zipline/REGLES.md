# Labo zipline : la pile « zipline + pandas + Lightweight Charts » à l'essai (règles fixées avant tout calcul, 8 novembre 2026)

Demande : tester la recette qui circule (zipline pour le backtest, pandas pour lire les résultats, Lightweight Charts
pour l'écran) sur le BTC avec une stratégie « signal de tendance, stop et objectif », du 1er janvier 2024 au 31 décembre
2025, et si le BTC ne donne rien, sur les autres marchés.

## Données

L'API publique de Kraken n'est pas joignable depuis cet environnement (accès réseau refusé), et elle ne rend de toute façon
que les 720 dernières bougies journalières (fin 2024 au plus tôt). On prend donc les bougies journalières gratuites que
le radar du projet collecte déjà chez Yahoo (`radar/donnees/jour/yahoo`) : BTC depuis le 17 sept. 2014, ETH depuis le
9 nov. 2017, SOL depuis le 10 avr. 2020, et les fonds indiciels depuis les années 1990 - 2000, jusqu'au 30 oct. 2026.
Volumes des cryptos convertis en unités (dollars ÷ clôture).

Deux bundles zipline : `crypto` (BTC, ETH, SOL, calendrier 24h/24 et 7j/7) et `etf` (QQQ, SPY, IWM, GLD, TLT, SMH,
calendrier de la Bourse de New York).

## La stratégie (identique pour tous les actifs, rien n'est ajusté)

Bougies journalières, achat seulement, sans levier, capital de départ 10 000 $.

- **Tendance** : moyenne exponentielle des clôtures sur 20 jours au-dessus de celle sur 50 jours, **et** clôture au-dessus
  de la moyenne sur 20 jours → achat avec tout le capital (98 %, le reste pour les frais).
- **Stop** : clôture sous le prix d'entrée − 2 × ATR 14 (ATR de Wilder connu le jour de l'entrée) → vente.
- **Objectif** : clôture au-dessus du prix d'entrée + 4 × ATR 14 → vente.
- **Fin de tendance** : moyenne sur 20 jours repassée sous celle sur 50 jours → vente.
- Le stop et l'objectif sont fixés à l'entrée et vérifiés à la clôture du jour (bougies journalières) ; comme toujours
  dans zipline en journalier, l'ordre passé à la clôture d'un jour est exécuté à la clôture du jour suivant (pas de regard
  vers le futur). Après une sortie, on rentre de nouveau dès que la règle d'entrée est vraie.
- **Frais** : cryptos 0,26 % par passage (frais « taker » courants) et 5 points de base de glissement ; fonds indiciels
  0,005 $ par part (1 $ minimum) et 5 points de base.

## Ce qu'on mesure

Pour chaque actif, sur la fenêtre du message (1er janv. 2024 → 31 déc. 2025) **et** sur tout l'historique disponible
(depuis 2016, ou le début des données s'il est plus tard, jusqu'au 30 oct. 2026) : rendement, pire baisse, ratio de
Sharpe, nombre de trades, et les mêmes chiffres pour le simple achat-conservation (acheter le premier jour, ne rien faire).

## Verdict (fixé d'avance)

La stratégie n'a un atout sur un actif que si, **sur tout l'historique disponible** :
1. le t des rendements quotidiens de la stratégie est d'au moins 2 ;
2. elle gagne sur chacune des deux moitiés de la période ;
3. son Sharpe est supérieur à celui de l'achat-conservation du même actif ;
4. sa pire baisse est moins profonde que celle de l'achat-conservation.

Famille de 9 tests (3 cryptos, 6 fonds) corrigée par Benjamini-Hochberg (q = 5 %) sur le p du critère 1. La fenêtre
2024 - 2025 du message est rapportée telle quelle, mais deux ans d'un seul actif ne prouvent rien : elle ne décide pas.

## Réserve écrite d'avance

C'est une règle de tendance classique, pas tirée de nos recherches : elle n'a pas été ajustée sur ces données, mais je
connais l'historique de ces marchés jusqu'à mi-2026. Rien ici ne concerne le compte financé Bulenox (contrats à terme du
Nasdaq en séance) : c'est un essai de la pile d'outils.
