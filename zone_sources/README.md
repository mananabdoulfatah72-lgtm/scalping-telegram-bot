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
  selon ces règles, il n'aurait pas été ajouté au robot. Il reste un candidat à suivre en argent virtuel
  pour voir s'il tient sur des mois nouveaux.

**La zone corrigée V1 reste la version de référence.**

## Décision de l'utilisateur (1er octobre 2026) : le rebond entre dans le robot, en test

L'utilisateur choisit d'ajouter S4 au robot de la zone corrigée, en argent virtuel. Ses raisons : le
rebond apporte 8 090 $ sur 2023-2026, une période que la règle n'avait jamais vue, et c'est une
information que la zone n'utilise pas. C'est sa décision, en connaissance de cause : le critère fixé
d'avance n'est pas rempli (t 1,44 contre 2,33). Le suivi en argent virtuel doit maintenant le juger.

Porté dans `zone/robot.py` sur main (fonction `rebond`). Aucun signal de rebond depuis le départ du
robot (25 septembre 2026).

### Revue de code du même jour : la piste S4 n'était pas exécutable telle quelle

S4 écarte les jours de changement de contrat. Or on ne sait qu'un jour est un jour de changement qu'en
voyant ses propres barres, donc pas la veille au soir. Le robot aurait annoncé des achats que le
backtest ne comptait pas : 7 depuis 2017, pour −1 880 $ par MNQ. Le robot suit donc une **version
exécutable** :
- il prend chaque achat qu'il annonce, jours de changement compris ;
- la séance de référence est la dernière séance complète, quel que soit le contrat (le mouvement se
  mesure dans la séance) ;
- seuls les jours de fête et les demi-séances, connus d'avance, sont écartés.

`test_rebond.py` vérifie que l'annonce de la veille est exactement le trade du lendemain : 0 écart sur
3 741 séances. Sur les 364 jours communs avec S4, les gains sont identiques.

| NQ, 1 MNQ, frais réels | Piste S4 | Version exécutable |
|---|---|---|
| rebond seul, 2023-2026 | +8 089 $ | +6 420 $ |
| t de la zone + rebond, 2023-2026 (zone seule : 2,00) | 2,04 | 1,91 |
| t de l'apport du rebond, 2023-2026 | 1,44 | 1,21 |
| t de l'apport du rebond, 2011-2022 | 1,80 | 1,89 |

Une fois exécutable, le rebond **fait baisser** le t de la zone sur 2023-2026, même s'il ajoute des
dollars. Son gain vient de deux krachs suivis d'un rebond : 2020 (+6 408 $) et 2025 (+6 568 $, dont
+4 119 $ le seul 9 avril 2025). Les 14 autres années réunies font environ +300 $. 55 % des achats sont
gagnants. Les pires jours vont jusqu'à −1 066 $ (17 juin 2026).

**Le rebond sort donc du compte de challenge du robot.** Il reste annoncé et compté à part, pour 1 MNQ
(colonne `gain_rebond_1_mnq` du journal). Rejoué sur 2023-2026 avec la taille du robot, le compte qui
l'incluait passait le challenge, mais le compte financé tombait à 0 MNQ dès novembre 2023, contre
octobre 2025 pour la zone seule. Le compte virtuel joue maintenant la zone seule, exactement comme avant
(journal identique sur 2023-2026). Le rebond n'est pas dans le script TradingView.
