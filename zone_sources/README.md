# Zone de bruit NQ : de nouvelles sources d'avantage

Les réglages sont épuisés (`zone_optimisation/` : même l'oracle ne gagne presque rien). La zone ne
regarde qu'une chose : le prix du NQ comparé à sa zone. Les pertes viennent des fausses cassures,
coupées en 30 minutes. On cherche donc des **informations que la zone n'utilise pas** et qui pourraient
distinguer une vraie cassure d'une fausse, ou ajouter un gain qui ne dépend pas d'elle.

## Règles (fixées le 1er octobre 2026, avant tout calcul)

Base : la zone corrigée V1 (`zone_failles/journal.py`), NQ, 1,5 point de frais par aller-retour,
mêmes séances. Chaque piste ne change que les **entrées** (S1, S2, S3, S5) ou ajoute un second gain
(S4). Les sorties restent celles de la zone.

| # | Source nouvelle | Règle | Idée |
|---|---|---|---|
| S1 | **Le S&P 500 (ES)** | on n'entre sur NQ que si l'ES est lui aussi hors de sa propre zone de bruit, du même côté, au même contrôle | une cassure suivie par tout le marché est plus solide qu'une cassure du seul Nasdaq |
| S2 | **Le volume** | on n'entre que si le volume des 30 minutes avant le contrôle dépasse sa moyenne à la même heure sur les 14 dernières séances complètes | une cassure avec du monde derrière tient mieux |
| S3 | **La tendance de fond** | achats seulement si la clôture de la veille est au-dessus de sa moyenne sur 50 séances complètes ; ventes seulement en dessous | ne trader que dans le sens de la tendance quotidienne |
| S4 | **Un gain indépendant** | en plus de la zone, achat de 1 MNQ de 9 h 30 à 16 h le lendemain d'une séance dans les 10 % les plus basses (252 séances, tournoi n°4, stratégie 7) | ajouter une source de gain peu liée à la zone |
| S5 | **La séance de nuit** | on n'entre à l'achat que si le prix dépasse aussi le plus haut de la nuit (18 h - 9 h), et à la vente que s'il passe sous le plus bas de la nuit | une cassure qui sort aussi du range de la nuit est une vraie sortie |

**Critères** (comme `zone_failles/`, durcis pour 5 pistes). Une piste est retenue si elle remplit tout
ce qui suit :
1. elle fait mieux que V1 sur NQ en 2011-2016 **et** en 2017-2022 (t des rendements quotidiens
   nets) ;
2. sur 2023-2026, elle fait mieux que V1, avec un t de la différence quotidienne avec V1 d'au moins
   **2,33** : seuil de Bonferroni pour 5 pistes, au lieu de 1,65 pour une seule.

Les pistes retenues sont réunies et la version finale est jugée de la même façon. Si elle passe, elle
est portée dans le robot et le script TradingView après une revue de code.

**À savoir, honnêtement** : 2023-2026 a déjà servi plusieurs fois (zone, variantes, optimisation).
Chaque nouveau test l'use un peu plus. D'où le seuil durci. Même une piste retenue devra être confirmée
par les mois à venir, dans le suivi en argent virtuel.

Tous les essais sont inscrits dans `fonds/essais.csv`.

## Résultats (1er octobre 2026) : aucune source retenue

`sources.py` → `sources.txt`. Contrôle : le moteur sans filtre redonne exactement V1.

| Piste | 2011-2016 | 2017-2022 | 2023-2026 | 2023-2026, 1 MNQ | t de la différence avec V1 (2023-2026) | Verdict |
|---|---|---|---|---|---|---|
| V1 zone corrigée | −2,26 | +2,78 | +2,00 | +10 668 $ | — | référence |
| S1 confirmation par l'ES | −1,42 | +2,92 | +1,48 | +6 882 $ | −1,67 | rejetée |
| S2 confirmation par le volume | −1,84 | +2,98 | +1,64 | +7 468 $ | −1,45 | rejetée |
| S3 tendance de fond | −1,97 | +1,79 | +3,50 | +10 792 $ | 0,00 | rejetée |
| S4 + rebond après forte baisse | −1,88 | +3,44 | +2,04 | +18 758 $ | +1,44 | rejetée (la plus proche) |
| S5 sortie du range de la nuit | −1,80 | +3,71 | +1,92 | +10 428 $ | −0,48 | rejetée |

Ce qu'on en tire :
- **Les confirmations (ES, volume, nuit) aident sur 2011-2022 mais pas depuis 2023.** Elles écartent de
  fausses cassures, mais aussi de bonnes : depuis 2023, une partie des meilleures journées part sans
  l'ES, sans volume particulier ou depuis l'intérieur du range de la nuit.
- **La tendance de fond (S3) fait t 3,50 sur 2023-2026**, mais pour le même gain que V1 avec deux fois
  moins de trades. Elle perd sur 2017-2022, et sa différence avec V1 vaut zéro. C'est l'effet du
  marché haussier, pas un avantage.
- **Le rebond après forte baisse (S4) est la seule piste qui améliore les trois périodes.** Il ajoute
  8 090 $ sur 2023-2026 pour 1 MNQ. C'est un second moteur, peu lié à la zone, qui ne trade qu'environ
  24 jours par an. Mais son apport n'est pas assez sûr pour passer le seuil (t 1,44 contre 2,33 exigé) :
  il n'est pas ajouté au robot. Il reste un candidat à suivre en argent virtuel, à part, pour voir s'il
  tient sur des mois nouveaux.

**La zone corrigée V1 reste la version de référence.**
