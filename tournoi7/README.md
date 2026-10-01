# Tournoi n°7 : l'information des autres marchés

Jusqu'ici, chaque stratégie ne regardait que le marché qu'elle trade. Les marchés sont pourtant liés :
- les taux, le dollar et le pétrole bougent avec l'appétit pour le risque ;
- l'or réagit au dollar ;
- les petites capitalisations précèdent parfois les grandes.

Ce tournoi cherche une **information venue d'un autre marché** : le premier mouvement de la matinée
sur un marché annonce-t-il le reste de la journée sur un autre ? Si oui, cela fait une source de gain
nouvelle et peu liée à la zone de bruit, utilisable dans le même compte de challenge. Tout reste
intraday, sans position de nuit.

## Règles (fixées le 1er octobre 2026, avant tout calcul)

**Marchés** (barres minute, 2016-2026, séances et frais de `zone_multi/`) : NQ, ES, RTY, YM, GC, CL,
6E. Chacun sert à la fois de source et de cible. Le Russell commence en juillet 2017.

Sources ajoutées dès que le téléchargement du tournoi 5 aura abouti (sinon elles ne sont pas testées) :

| Source | Données | Fenêtre du signal |
|---|---|---|
| ZN (taux à 10 ans) | barres d'une heure | 9 h - 10 h |
| Dollar | panier 6E, 6B, 6J, 6A, 6C, 6S, barres d'une heure, signe inversé (le panier monte quand le dollar baisse) | 9 h - 10 h |
| Bitcoin CME | minutes, depuis 2018 | 9 h 30 - 10 h 30 |

**Règle unique, sans aucun réglage** :
- signal = mouvement de la source entre 9 h 30 et 10 h 30 (heure de New York), soit de l'ouverture de
  la minute de 9 h 30 à la clôture de celle de 10 h 29 ;
- à 10 h 30, la cible est achetée ou vendue :
  - **suivre** : dans le sens du signal ;
  - **contrer** : à l'inverse ;
- sortie à la fin de la séance de la cible : 15 h 59 pour les indices, 13 h 29 pour l'or, 14 h 29 pour
  le pétrole, 14 h 59 pour l'euro.

Conditions de trade :
- source et cible doivent avoir une séance complète ce jour-là ;
- pas de changement d'échéance ni pour l'une ni pour l'autre.

**Essais** : 7 sources × 6 cibles × 2 sens = 84, puis jusqu'à 3 sources × 7 cibles × 2 sens = 42 de plus.
La source n'est jamais sa propre cible : le « momentum de la 1re heure » a déjà été testé.

## Le tri

**1. Exploration 2016-2022** (bitcoin : 2018-2022). Seuil durci pour tant d'essais : **t ≥ 3,0** sur
les gains quotidiens nets, et gain positif sur 2016-2019 et sur 2020-2022.

**2. Contrôle global contre le hasard.** On rejoue tous les essais 200 fois, en associant chaque jour
le signal de la source à un autre jour tiré au hasard dans la même année. L'information du jour même
est ainsi détruite, mais la distribution des signaux est gardée. Le meilleur t réel doit dépasser le
meilleur t de 95 % de ces tirages. Sinon, rien n'est retenu, même au-dessus de 3,0.

**3. Coffre 2023-2026**, ouvert une fois pour les survivants : t ≥ 2 dans le même sens, et au moins 3
années positives sur 4.

**4. Combinaison** : les survivants entrent dans le portefeuille avec la zone de bruit. Le portefeuille
est jugé comme à l'étape 2 du tournoi 6, sur 2023-2026 et dans le challenge.

## Partie B : les familles du tournoi 6 sur le bitcoin

Si les minutes du bitcoin arrivent, les 7 familles du tournoi 6 y sont aussi testées, sur la séance
9 h 30 - 16 h :
- exploration 2018-2022, mêmes critères que le tournoi 6 (t ≥ 2,5, positif sur 2018-2020 et sur
  2021-2022, corrélation à la zone < 0,5) ;
- frais du micro-bitcoin : 2 $ + 2 ticks par aller-retour.

Tous les essais sont inscrits dans `fonds/essais.csv`.

## Résultats, partie A (1er octobre 2026) : aucune information croisée

`tournoi7.py` → `tournoi7.txt`, `partieA.csv`, `hasard_max_t.txt`. Contrôle : la règle simple redonne
exactement `entree_fixe` des tournois sur les 7 marchés.

- **0 essai sur 84 atteint t ≥ 2.** Le meilleur fait t +0,45 (pétrole → Nasdaq, contrer). 33 font
  t ≤ −2 : les frais d'un trade par jour ne sont pas couverts.
- **Le contrôle global est net.** Si l'on prend le signal d'un autre jour de la même année, le meilleur
  des 84 essais fait en médiane t +1,03 sur 200 tirages, et +2,09 au 95e centile. **Le vrai signal du
  jour fait moins bien que le hasard** : le mouvement de 9 h 30 - 10 h 30 d'un marché n'apporte aucune
  information sur la suite de la séance d'un autre. Il l'oriente même plutôt à contre-sens, puisque ces
  marchés bougent ensemble le matin et que leurs après-midi corrigent un peu le matin.
- Rien ne passe : le coffre 2023-2026 n'est pas ouvert, rien n'est combiné avec la zone.

Les sources ZN, dollar et bitcoin, ainsi que la partie B, attendent le téléchargement du tournoi 5.
