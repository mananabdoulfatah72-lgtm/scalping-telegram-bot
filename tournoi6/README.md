# Tournoi n°6 : des sources de gain sur d'autres marchés, à combiner avec la zone de bruit

La zone de bruit seule ne suffit pas pour retirer de l'argent d'un compte financé (`zone_retrait/`).
Son rapport gain/risque est trop faible. Il faut plusieurs sources de gain peu liées, qui tradent
ensemble sur le même compte de challenge 50K. Chaque source doit être intraday : le compte Phidias
Fundamental n'autorise pas les positions de nuit.

## Ce qui est déjà connu

- La zone de bruit perd sur les 5 autres marchés (`zone_multi/`).
- Sur ces mêmes marchés, plusieurs familles ont déjà échoué (`tournoi5/`, familles B et C) :
  - le momentum de fin de séance ;
  - le rapport EIA du pétrole.
- Les familles ci-dessous ont été testées sur NQ et ES (tournois 1 et 4), **jamais sur les autres
  marchés**.

## Règles (fixées le 1er octobre 2026, avant tout calcul)

**Marchés** : les 5 déjà téléchargés, sans nouveau coût. Les séances, les micros et les frais sont
ceux de `zone_multi/`.

| Marché | Micro | Séance (New York) | Frais par aller-retour |
|---|---|---|---|
| Russell 2000 (RTY) | M2K | 9 h 30 - 16 h | 2 $ + 2 ticks = 3 $ |
| Dow Jones (YM) | MYM | 9 h 30 - 16 h | 3 $ |
| Or (GC) | MGC | 8 h 20 - 13 h 30 | 4 $ |
| Pétrole (CL) | MCL | 9 h - 14 h 30 | 4 $ |
| Euro (6E) | M6E | 8 h 20 - 15 h | 4,50 $ |

**Familles** : règles reprises telles quelles des tournois 1 et 4, avec la séance de chaque marché à
la place de 9 h 30 - 16 h. Aucun réglage par marché.

| # | Famille | Règle |
|---|---|---|
| 1 | Range d'ouverture 30 min | cassure du plus haut ou du plus bas des 30 premières minutes, stop de l'autre côté, un trade par jour, sortie en fin de séance |
| 2 | Cassure de Williams | ouverture ± 0,5 × amplitude de la séance précédente, stop à l'ouverture |
| 3 | Étirement de Crabel | ouverture ± moyenne sur 10 séances de min(haut − ouverture, ouverture − bas), stop au niveau opposé |
| 4 | Cassure de la veille | au-dessus du plus haut ou sous le plus bas de la séance précédente, stop au milieu de celle-ci |
| 5 | Momentum de la 1re heure | après 60 minutes, dans le sens de la 1re heure, jusqu'à la fin de la séance |
| 6 | Retournement après 30 min extrêmes | si les 30 premières minutes dépassent 1,5 fois leur moyenne sur 20 séances : contre ce mouvement, stop à l'extrême de ces 30 minutes, jusqu'à la fin |
| 7 | Rebond après une forte baisse | si la séance précédente (ouverture → clôture) est dans les 10 % les plus basses (252 séances) : achat de l'ouverture à la fin |
| 8 | Achat simple de la séance | contrôle seulement, jamais retenu |

Cela fait 7 familles × 5 marchés = 35 essais, plus 5 contrôles.

Communs à tous les essais :
- séance complète = première et dernière minute présentes, et au plus 20 minutes manquantes ;
- séance précédente = dernière séance complète du même contrat ;
- pas de trade le jour d'un changement d'échéance.

**Contrôle du code** : sur NQ avec la séance 9 h 30 - 16 h, les fonctions généralisées doivent redonner
exactement les résultats des tournois 1 et 4 pour les mêmes familles.

### Étape 1 : choix des sources (2016-2022 ; Russell à partir de juillet 2017)

Une source est retenue si elle remplit tout ce qui suit :
- t des gains nets quotidiens ≥ 2,5 (seuil durci : 35 essais) ;
- gain positif sur 2016-2019 et sur 2020-2022 ;
- corrélation quotidienne avec la zone de bruit NQ inférieure à 0,5.

**Si aucune source n'est retenue, on s'arrête là** : rien n'est ajouté, et 2023-2026 n'est pas regardé
pour ces sources.

### Étape 2 : le portefeuille, jugé une seule fois sur 2023-2026

Portefeuille = zone de bruit NQ + sources retenues, chacune au même risque : gain du jour divisé par
son écart-type des 60 séances précédentes. Il est adopté dans le robot s'il remplit tout ce qui suit :
- t quotidien ≥ 2 sur 2023-2026 ;
- Sharpe supérieur à celui de la zone seule sur 2023-2026 ;
- dans le challenge (règles Phidias et gestion du robot, `zone_retrait/`), gain net par an meilleur
  que la zone seule pour les départs 2023-2024.

Pour le challenge, chaque source reçoit un budget de f × marge / √(nombre de sources), au moins
1 micro. Le pire moment du jour est la somme des pires moments de chaque source, ce qui est prudent.

Tous les essais sont inscrits dans `fonds/essais.csv`.

### Ajout (1er octobre 2026, avant de recevoir les données du tournoi 5)

Le tournoi 5 avait fixé ses règles le 30 septembre, mais son téléchargement avait été annulé :
- familles A1 et A2 : fixing des devises ;
- famille D1 : bitcoin CME ;
- familles E1 et E2 : adjudications du Trésor sur le ZN.

Le téléchargement est relancé, avec le même plafond de 25 $. Ces 5 essais sont jugés par les règles
du tournoi 5 : t ≥ 2 sur la période d'exploration, plus son contrôle propre. Une stratégie qui passe
entre directement dans le portefeuille de l'étape 2 ci-dessus, avec la zone de bruit, et se juge de la
même façon sur 2023-2026. Rien d'autre ne change.

## Résultats (1er octobre 2026) : aucune source retenue, arrêt à l'étape 1

`tournoi6.py` → `tournoi6.txt`, `etape1.csv`. Contrôle : sur NQ, les 7 familles généralisées
redonnent exactement les tournois 1 et 4.

- **0 essai sur 35 atteint t ≥ 2** (environ 1 était attendu par hasard). **15 font t ≤ −2** : sur ces
  marchés, ces règles ne gagnent pas assez pour payer les frais.
- **L'euro (6E) est le pire** : toutes les cassures font entre t −3 et −5,6.
- **Seule famille positive** : le « rebond après une forte baisse », sur les indices actions. Russell
  t +1,23, Dow t +1,80 ; sur NQ t +1,80 et ES +1,48 sur 2011-2022 (tournoi 4). Il reste partout sous
  le seuil, et ces indices baissent et rebondissent ensemble : ce n'est pas une source peu liée.
- Les autres familles sont négatives ou nulles sur l'or, le pétrole et l'euro. Leur corrélation avec la
  zone est presque nulle, mais une source sans avantage n'apporte rien au portefeuille.

Comme prévu, 2023-2026 n'est pas regardé pour ces sources, et rien n'est ajouté au robot.
