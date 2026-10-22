# Vague « annonces de 8 h 30 » : la zone les jours où le dollar saute à 8 h 30 (règles fixées le 22 octobre 2026, avant tout calcul)

## Pourquoi

La seule règle qui ait survécu dans toute la recherche est **« pas de zone les jours d'annonce de la Fed »**
(vague 9 : elle bat les jumeaux de bruit et 100 % des filtres au hasard). Les 29 conditions de la vague 9 ne
contenaient **aucune autre annonce**. Or les annonces les plus fortes pour les marchés américains tombent à **8 h 30**
(emploi, inflation, ventes au détail…), avant l'ouverture : la séance démarre sur une information neuve. Deux effets
sont possibles :
- la séance suit une tendance (l'information se diffuse) : la zone devrait mieux gagner ;
- ou elle oscille autour d'un prix déjà ajusté : la zone devrait perdre, comme les jours de la Fed.

## Données

- Minutes du NQ (2012 - 20 octobre 2026, recherche + robot) et zone du bot, sans les jours de la Fed (comme le bot).
- **Indice du dollar**, barres de 5 minutes 24 h sur 24 (HistData, `donnees_libres/histdata_5min/udxusd_*`, gratuit).

**Jour de choc de 8 h 30** : |ln(prix à 8 h 40 / prix à 8 h 30)| du dollar (clôtures des barres de 8 h 35 - 8 h 40 et
8 h 25 - 8 h 30, heure de New York) au-dessus du 80e centile des 250 séances précédentes. C'est connu à 8 h 40, avant le
premier contrôle de la zone (10 h). Contrôle : la plupart des premiers vendredis du mois (chiffres de l'emploi)
doivent être des jours de choc (au moins 60 %).

## Règles testées (2)

- **S** : pas de zone les jours de choc.
- **D** : 2 MNQ les jours de choc, 1 sinon.

## Décision (fixée maintenant)

Une règle est retenue si **toutes** ces conditions sont remplies :
1. Sharpe des séances (en $ au prix d'aujourd'hui, 1 MNQ de base) plus haut que la zone seule sur l'exploration
   (2012 - 2022) **et** sur le coffre (2023 - 2026) ;
2. sur l'exploration, elle bat au moins 95 % de 200 règles placebo, où les jours de choc sont remplacés par autant de
   jours tirés au hasard dans chaque année.

Si les deux passent : celle qui a le plus haut Sharpe d'exploration. Pour information : la zone les jours de choc et
les autres jours (t, gain moyen), et l'effet sur les challenges Lucid Flex (1 MNQ) et Bulenox (3 MNQ), départs
2023 - 2026, avec le moteur corrigé de la partie D.

## Limites écrites d'avance

- Le dollar saute aussi pour d'autres raisons (banques centrales étrangères, géopolitique) : le choc mesure « une
  nouvelle à 8 h 30 », pas un calendrier exact.
- Environ 20 % des séances sont des jours de choc : environ 700 séances, dont environ 190 au coffre.
