# Arène, vague 3 : un Supertrend en mieux (règles fixées avant tout calcul, 9 novembre 2026)

Demande : « quelque chose qui se rapproche du Supertrend NQ mais en mieux », qui trade presque tous les jours (Z12 se
repose certains jours) et qui est moins souvent négatif. Le Supertrend NQ trade chaque séance mais s'essouffle : t 2,30
sur 2014 - 2026 et seulement 0,53 depuis 2023, 46 % des comptes financés neufs encore en vie après 60 séances,
1,21 master grillé par an.

Même cadre que l'arène (`bots.py`) : séances complètes 2014 - 2 nov. 2026, minute par minute, 1 MNQ, limite du bot 400 $,
3 $ de frais, 1 point de glissement à une sortie forcée, compte financé Bulenox Master 50K Option 2 et vie réelle
(retraits, constance 40 %, requalification payée), dollars au prix d'aujourd'hui.

## Les 7 candidats (tous suivent la tendance du jour et tradent presque chaque séance)

| | Candidat | Règle |
|---|---|---|
| V1 | Cassure des 5 premières minutes (Zarattini et Aziz, 2023) | si la bougie 9 h 30 - 9 h 35 est haussière, achat à l'ouverture de 9 h 35, stop au plus bas de cette bougie ; baissière, vente, stop au plus haut ; objectif 10 fois le risque ; sinon sortie à 16 h ; bougie sans corps : pas de trade |
| V2 | Cassure des 15 premières minutes | même règle avec la plage 9 h 30 - 9 h 45 (sens : clôture contre ouverture de la plage, stop à l'autre bout de la plage) |
| V3 | Cassure des 30 premières minutes | même règle avec la plage 9 h 30 - 10 h |
| V4 | Élan de la dernière demi-heure (Gao, Han, Li et Zhou, 2018) | à 15 h 30, achat si le NQ a monté de la clôture de la veille à 10 h, vente s'il a baissé ; sortie à 16 h |
| V5 | Supertrend sur bougies de 15 minutes | le Supertrend NQ (10, 3) calculé sur des bougies de 15 minutes au lieu de 5 (moins de faux signaux), mêmes horaires |
| V6 | Supertrend avec la VWAP | le Supertrend NQ ne prend un achat que si le prix est au-dessus de la VWAP de la séance, une vente que s'il est dessous |
| V7 | Supertrend sans les jours de VIX inversé | le Supertrend NQ ne trade pas le jour J si le VIX était au-dessus ou égal au VIX à 3 mois à la clôture de J − 1 (la règle de Z12) |

Stops : un stop sort au prix du stop (ou à l'ouverture si elle est déjà au-delà), le chemin s'arrête à la minute d'avant ;
si le stop et l'objectif sont touchés dans la même minute, on compte le stop.

## « Mieux que le Supertrend NQ » : toutes ces conditions (2014 - 2026)

1. t des résultats par séance d'au moins 2, et survie à Benjamini-Hochberg (q = 5 %) sur les 7 ;
2. positif sur 2014 - 2022 **et** sur 2023 - 2026 ;
3. avec 6 $ de frais, t d'au moins 1,5 ;
4. au moins 9 années positives sur 13 ;
5. trade au moins 80 % des séances (comme le Supertrend) ;
6. sur le compte financé : survie à 60 séances d'au moins 56 % (10 points de plus que le Supertrend), au plus
   0,97 master grillé par an (20 % de moins que lui), pire baisse pas plus de 25 % plus profonde que la sienne ;
7. pour V1 - V3 (publiées en 2023) : positif aussi depuis le 1er juin 2023, après la publication.

On rapporte aussi la part des séances positives, des semaines positives, des mois positifs, la pire semaine, et la période
du 11 août au 2 novembre 2026 (à titre d'information : trois mois ne décident rien).

## Ensuite, sur le même compte que Z12

Pour chaque candidat retenu : **Z12 + candidat** sur le même compte, 1 MNQ chacun, limite commune de 400 $ (moteur
d'ensemble de l'arène). Gardé seulement si, face à Z12 seul : survie à 60 séances au moins égale, pas plus de masters
grillés par an, et plus de séances tradées.

## Réserve

V1 - V4 viennent d'études publiées ; V5 - V7 sont des améliorations du Supertrend proposées avant de voir leur résultat.
Les règles du Supertrend ont elles-mêmes été choisies en regardant ce même historique.
