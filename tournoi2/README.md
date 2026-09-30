# Tournoi intraday n°2 : d'autres stratégies que la zone de bruit

## Règles (fixées le 30 septembre 2026, avant tout calcul)

Même principe que le tournoi n°1 (`tournoi/`) :
- **réglages standards de chaque indicateur ou de sa source, sans aucun ajustement** ;
- testé sur le Nasdaq (NQ) et le S&P 500 (ES), séance de 9 h 30 à 16 h, tout fermé à 16 h ;
- pas de trade les jours incomplets ni le jour d'un changement d'échéance ;
- frais de 1,5 point de NQ et 0,9 point d'ES par aller-retour.

### A. Indicateurs populaires (barres de 5 minutes)

Signal à la clôture d'une barre, exécution à l'ouverture de la suivante. Entrées permises de 9 h 35 à
15 h, sorties à tout moment, tout fermé à 16 h. Les indicateurs sont calculés en continu d'une séance
à l'autre, sur les seules barres de la séance.

| # | Stratégie | Règle |
|---|---|---|
| 1 | Croisement de moyennes 9/21 | acheteur si la moyenne exponentielle 9 est au-dessus de la 21, vendeur sinon |
| 2 | Supertrend (10, 3) | du côté de la tendance du Supertrend (écart moyen vrai sur 10 barres, facteur 3) |
| 3 | MACD (12, 26, 9) | acheteur si le MACD est au-dessus de sa ligne de signal, vendeur sinon |
| 4 | Bollinger (20, 2), cassure | achat si la clôture passe au-dessus de la bande haute, sortie sous la moyenne ; vente symétrique |
| 5 | Bollinger (20, 2), retour | achat si la clôture passe sous la bande basse, sortie au-dessus de la moyenne ; vente symétrique |
| 6 | RSI(2) (Connors) | achat si RSI(2) < 10, sortie au-dessus de 50 ; vente si RSI(2) > 90, sortie sous 50 |
| 7 | Canal de Donchian 20 / 10 | achat au-dessus du plus haut des 20 barres précédentes, sortie sous le plus bas des 10 ; vente symétrique |

### B. Schémas étudiés (minutes)

| # | Stratégie | Règle | Source |
|---|---|---|---|
| 8 | NR7 + range d'ouverture 30 min | seulement le lendemain d'un jour à l'amplitude la plus faible des 7 derniers : cassure de 9 h 30-10 h, stop de l'autre côté | Crabel (1990) |
| 9 | Jour intérieur + cassure de la veille | seulement si la veille était comprise dans l'avant-veille : cassure de la veille, stop au milieu | Crabel (1990) |
| 10 | Range d'ouverture 5 min et volume relatif | à 9 h 35, dans le sens de la 1re barre de 5 min si son volume dépasse sa moyenne sur 14 jours ; stop à 10 % de l'amplitude moyenne sur 14 jours | Zarattini, Barbon, Aziz (2024) |
| 11 | Paire NQ / ES en retour à la moyenne | toutes les 30 min de 10 h à 15 h : si l'écart des deux variations depuis 9 h 30 dépasse 1,5 fois son écart-type de fin de séance sur 20 jours, vente du plus fort et achat du plus faible ; sortie quand l'écart repasse 0, ou à 16 h (un seul essai, pour les deux marchés ensemble) | arbitrage statistique classique |
| 12 | Lundi contre vendredi | le lundi, de 9 h 30 à 16 h, à l'inverse de la séance du vendredi | effet week-end |
| 13 | Échéance mensuelle des options | 3e vendredi du mois : à 12 h, à l'inverse du mouvement de 9 h 30-12 h, jusqu'à 16 h | effet « épinglage » |
| 14 | Jour de l'emploi américain | 1er vendredi du mois (approximation) : à 10 h, dans le sens de 9 h 30-10 h, jusqu'à 16 h | réaction aux statistiques |
| 15 | Retournement de la mi-journée | chaque jour : à 12 h, à l'inverse du mouvement de 10 h-12 h, jusqu'à 13 h 30 | calme de la mi-journée |

Nombre d'essais : 14 stratégies × 2 marchés, plus la paire, soit **29**.

### Le tri (identique au tournoi n°1)

1. **Exploration (2011-2022)** : t ≥ 2 sur les rendements quotidiens nets en % du prix, jours sans trade
   compris. Pour la paire : rendement des deux jambes, à montant égal.
2. **Contrôle sur bruit** : battre le plus haut t de 20 versions où les minutes de chaque séance sont
   mélangées au hasard. Pour la paire, le même mélange est appliqué aux deux marchés.
3. **Coffre 2023-2026, ouvert une seule fois** pour les survivants. Il faut un t au moins égal au seuil
   de Bonferroni (1,65 si m = 1, 1,96 si m = 2, 2,13 si m = 3...) et un résultat positif au moins 3
   années sur 4.
4. **Si un survivant passe** :
   - corrélation avec la zone de bruit ;
   - combinaison moitié-moitié avec la zone ;
   - simulation du challenge 50K.
5. Les 29 essais sont inscrits dans `fonds/essais.csv`. Rien n'est ajouté ni changé après avoir vu les
   résultats.

## Résultats (30 septembre 2026) : aucun survivant, 0 sur 29

Code figé avant le calcul (commit 94d8a4a) ; tests dans `test_concurrents2.py`. Détail dans
`exploration.txt` et `exploration.csv`.

**Étape 1 (t ≥ 2 sur 2011-2022) : aucune ne passe.** Les moins mauvaises :

| Stratégie | Marché | t 2011-2022 | 2011-2016 | 2017-2022 | Plus haut t sur bruit | Corrélation avec la zone |
|---|---|---|---|---|---|---|
| Range d'ouverture 5 min + volume relatif | NQ | +1,34 | −0,77 | +2,13 | +2,33 | 0,28 |
| Jour de l'emploi américain | NQ | +0,53 | +1,19 | −0,28 | +2,18 | 0,08 |
| NR7 + range d'ouverture 30 min | NQ | −0,16 | −2,15 | +1,15 | +1,81 | 0,17 |
| Lundi contre vendredi | NQ | −0,32 | −0,89 | +0,22 | −0,32 | −0,01 |

Les 25 autres essais sont négatifs, de −0,5 à −35 :
- **Les 7 indicateurs populaires sur barres de 5 minutes** (moyennes, Supertrend, MACD, Bollinger,
  RSI(2), Donchian) perdent tous sur les deux marchés, de t −0,5 (Supertrend NQ) à t −35 (RSI(2) ES).
  Ils tradent presque tous les jours, souvent plusieurs fois : les frais les écrasent. Face à leurs
  versions sur bruit, rien de net : les moyennes 9/21 et le Supertrend font mieux que la moyenne du
  bruit, le MACD, la cassure de Bollinger et Donchian font moins bien.
- **Les effets de calendrier** perdent tous : lundi contre vendredi, échéance des options (t −2,2 à
  −2,4), jour de l'emploi sur ES, retournement de la mi-journée (t −2,6 et −5,7).
- **La paire NQ / ES** perd nettement (t −3,70, contre +0,48 au mieux sur bruit). L'écart entre le
  Nasdaq et le S&P a tendance à continuer dans la journée, pas à se refermer.
- **Le seul candidat de l'article récent (Zarattini, Barbon, Aziz 2024)**, le range de 5 min avec le
  volume, gagne sur NQ depuis 2017 (t +2,13). Mais il fait t +1,34 sur 12 ans, et une version sur
  bruit fait mieux (+2,33). Sur ES, il perd (t −3,74).

**Pas de survivant, donc le coffre 2023-2026 reste fermé.**

**Ce qu'on retient, avec le tournoi n°1** :
- 57 stratégies intraday testées (28 + 29), sans rien ajuster : **aucune n'atteint t ≥ 2 sur
  2011-2022**, zone de bruit comprise (t 0,62).
- La seule structure réelle du Nasdaq en journée, c'est la **continuation** : un mouvement a tendance
  à se poursuivre. On la voit :
  - dans la zone de bruit, qui bat ses versions sur bruit ;
  - dans la paire, qui perd plus que sur bruit parce que l'écart continue ;
  - dans les bandes de VWAP (`ordres/`), où le retour au VWAP fait moins bien que le hasard.

  Elle n'est rentable après frais que depuis 2017 environ, et la zone de bruit l'exploite le mieux.
- Aucune autre stratégie intraday publiée et testée honnêtement ne donne t ≥ 2. Pour un challenge 50K,
  la zone de bruit sur MNQ reste la seule candidate, et son suivi en argent virtuel décide.
