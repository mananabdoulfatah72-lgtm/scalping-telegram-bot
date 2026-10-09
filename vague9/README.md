# Vague 9 : confluences sur la zone, jugées sur l'objectif du 50K (règles fixées le 9 octobre 2026, avant le calcul)

## Demande de l'utilisateur

Rester sur un 50K. Trouver une alliance de confluences, bots ou variantes, comme la zone + le filtre delta, qui fasse
valider le challenge sans brûler le compte. Des mois de perte sont acceptés si les gains les compensent largement.
**Objectif : 1 % par mois (ou 2 % tous les 2 mois), y compris dans des années comme 2025.** Chercher en grand.

## Ce qui a déjà été cherché (pour ne pas le refaire)

- **Stratégies seules** : plus de 800 000, intraday et journalières, sur 7 futures en 5 minutes, 40 futures CME en
  journalier et 8 marchés 24 h (`fonds/essais.csv`).
- **4e source jugée sur ce qu'elle apporte au bot** : déjà faite par la machine 4 (232 736 stratégies, 16 futures,
  jumeau de bruit) ; rien de mieux que le hasard.
- **Conditions de la zone** : 33 conditions regardées une par une (`zone_optimisation/`), sans en faire de règle. La
  zone y gagne surtout les jours agités, mais depuis 2023 elle gagne presque partout.

**Ce qui est nouveau ici :**
1. Les conditions sont **combinées par 1, 2 ou 3** (confluences).
2. Chacune est jugée **directement sur l'objectif du 50K**, et non sur le t d'un trade.
3. Deux façons d'appliquer une confluence : ne prendre que les trades qui la remplissent, ou prendre les autres en
   **MES** au lieu du MNQ.
4. Le hasard est mesuré par un **jumeau de bruit de toute la recherche**, et par des **filtres tirés au hasard** sur la
   vérification.

## Le bot de départ

- Zone 1 MNQ, filtre delta simulé aussi bon qu'en 2026 (10 tirages), plus le RSI(2) de nuit sur 1 MES (A3).
- Chaque trade au niveau d'aujourd'hui de son jour.
- Le calcul rapide redonne exactement le moteur (écart < 1e-12 $, en MNQ comme en MES).

## L'objectif mesuré (celui de l'utilisateur)

Pour chaque départ (une séance sur cinq), on suit 12 mois (252 séances) d'un compte 50K :
- plancher 2 000 $ sous le plus haut de fin de séance, bloqué à +100 $ (règle LucidFlex), contrôlé chaque soir ;
- **objectif tenu** = le compte ne touche jamais le plancher **et** finit les 12 mois à au moins **+6 000 $** (12 %,
  soit 1 % par mois), sans retrait.

Groupes de départs :

| Groupe | Départs |
|---|---|
| Choix | janvier 2012 - décembre 2021 |
| Vérification | janvier 2023 - septembre 2025 (12 mois suivis jusqu'en septembre 2026) |
| 2025 | janvier - septembre 2025 (rapporté à part) |

Bot de départ (fin de séance seulement, donc un peu optimiste) :

| Groupe | Objectif tenu | Compte perdu | Gain médian sur 12 mois |
|---|---|---|---|
| Choix | 66 % | 17 % | +8 350 $ |
| Vérification | 87 % | 10 % | +9 461 $ |
| 2025 | 51 % | 38 % | +3 330 $ |

## Les conditions (toutes connues avant l'entrée du trade)

**Par séance :**
- séances agitées (mouvement moyen des 14 séances d'avant dans le tiers haut de l'année passée) ;
- séances pas calmes (hors tiers bas) ;
- grand écart d'ouverture (tiers haut) ; écart d'ouverture pas petit ;
- veille en hausse ; veille en baisse ;
- VIX haut (tiers haut) ; VIX pas bas ; VIX en déport (≥ VIX 3 mois) ;
- GEX sous sa médiane ;
- pas un jour de la Fed ;
- NQ au-dessus ou au-dessous de sa moyenne 50 jours ;
- pas le lundi ; vendredi ;
- nuit agitée (tiers haut) ;
- zone gagnante sur ses 20, ou ses 60, séances d'avant (courbe de la zone elle-même, filtre compris).

**Par trade :**
- 1er trade du jour ;
- achats ; ventes ;
- contre la séance de la veille ; dans son sens ;
- entrée avant ou après 12 h ;
- dans le sens de la moyenne 50 jours ; contre elle ;
- dans le sens de l'écart d'ouverture ; contre lui.

29 conditions. Chaque confluence est un ET de 1, 2 ou 3 conditions : 4 089 confluences × 2 façons de les appliquer
(trades non retenus pas pris, ou pris en MES) = **8 178 règles**. Les paires contradictoires (achats et ventes…)
donnent simplement des règles sans trade.

## Jugement

1. **Choix.** On retient la règle qui tient l'objectif le plus souvent sur les départs 2012-2021 (moyenne des 10
   tirages).
2. **Jumeau de bruit.** Toute la recherche est refaite 10 fois avec des conditions mélangées au hasard (mêmes
   fréquences, ordre des séances ou des trades tiré au hasard). La meilleure règle réelle doit faire mieux, sur le
   choix, que la meilleure règle d'au moins 9 jumeaux sur 10. Sinon, son avance sur le choix est du hasard.
3. **Vérification** (départs 2023 - sept. 2025) :
   - objectif tenu plus souvent que le bot de départ (87 %) ;
   - compte perdu moins souvent (10 %) ;
   - mieux que 90 % de 200 filtres tirés au hasard qui gardent la même part des trades, appliqués de la même façon.
4. Si elle passe, elle est **recalculée avec le moteur exact** (plancher contrôlé minute par minute, retraits) sur
   LucidFlex, Topstep et FundedNext Legacy 50K, avant d'en parler comme d'un résultat.
5. On publie aussi les 20 meilleures du choix avec leur vérification, et les départs de 2025.

**À savoir avant d'y croire :**
- 2023-2026 a déjà été regardé de nombreuses fois ;
- les 33 conditions de `zone_optimisation` ont été vues sur les deux périodes, ce qui rend la vérification moins
  neuve.
