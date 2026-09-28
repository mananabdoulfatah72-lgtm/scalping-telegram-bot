# Secteurs américains : recherche d'abord, stratégie ensuite

Reproduction de la méthode « recherche → hypothèses → critères fixés → backtest → journal des
rejets → essayer de tuer le survivant », avec trois corrections :

1. **Le choix du secteur est lui-même testé** : on vérifie sur 25 ans si « le secteur le plus fort des
   3-6 derniers mois » continue à battre le marché ensuite (sinon l'étape 1 ne sert à rien).
2. **Chaque version essayée compte** comme un essai (fichier `fonds/essais.csv`) : plus on essaie,
   plus une version passe par hasard. On ne corrige pas une stratégie jusqu'à ce qu'elle passe.
3. **Pas d'actions ajoutées parce qu'elles ont déjà monté** : l'univers est fixé à l'avance
   (`univers.py`). Les listes d'actions sont celles d'aujourd'hui (biais de survie) : les stratégies
   sur ETF sont plus fiables que celles sur actions avant 2020.

## Protocole (fixé le 28 septembre 2026, avant de télécharger les données)

### Étape 1 — Recherche, sans stratégie

Pour chaque secteur (ETF SPDR), au 25 septembre 2026 : rendement relatif à SPY sur 3 et 6 mois,
momentum 12-1 mois, position par rapport à la moyenne 200 jours, volatilité, bêta, sensibilité aux
taux (rendements hebdomadaires sur 2 ans comparés à la variation du taux 10 ans), baisse depuis le
plus haut d'un an. Classement par la moyenne des rangs de force relative 3 mois et 6 mois.

Taux de base historique (1999-2026) : chaque mois, acheter le secteur le plus fort (et les 3 plus
forts) sur 3 et 6 mois, et mesurer l'écart avec SPY le mois suivant. Aussi : chaque fois qu'un secteur
dépasse SPY de plus de 10 points sur 3 mois, que fait-il les 1 et 3 mois suivants ?

### Étape 2 — Quatre stratégies pour le secteur classé premier

Quatre paris différents, écrits ici avant de connaître le secteur gagnant (E = ETF du secteur,
L = ses actions dans `univers.py`) :

1. **Rotation** : chaque fin de mois, détenir E si son rendement sur 6 mois dépasse celui de SPY
   **et** s'il est au-dessus de sa moyenne 200 jours ; sinon détenir SPY. Pari : la force relative
   d'un secteur persiste (Moskowitz et Grinblatt, 1999).
2. **Momentum dans le secteur** : chaque fin de mois, les 5 actions de L au meilleur rendement de
   t − 6 mois à t − 1 mois, à poids égal. Pari : les gagnants continuent de gagner (Jegadeesh et
   Titman, 1993).
3. **Faible risque** : chaque fin de mois, les 5 actions de L à la plus faible volatilité propre sur
   6 mois (écart par rapport à E), pondérées par l'inverse de leur volatilité. Pari : les actions
   calmes rapportent plus par unité de risque (Ang et al., 2006 ; Frazzini et Pedersen, 2014).
4. **Moteur macro** : détenir E quand son moteur économique est favorable (variation sur 3 mois),
   sinon SPY. Moteurs : Énergie → pétrole en hausse ; Matériaux et Industrie → cuivre en hausse ;
   Finance → écart de taux 10 ans − 3 mois en hausse ; Services publics, Immobilier, Technologie,
   Communication, Consommation cyclique → taux 10 ans en baisse ; Santé et Consommation de base →
   SPY sous sa moyenne 200 jours (refuge). Pari : le secteur suit son moteur avec retard.

Frais : 5 points de base par ordre sur les actions, 3 sur les ETF (commission + écart), doublés pour
le test de résistance. Capital de référence 100 000 $.

### Étape 3 — Critères d'acceptation (fixés avant tout backtest)

Une stratégie passe si elle remplit **tous** ces critères :

1. Bat SPY après frais sur les 12 derniers mois (26 septembre 2025 - 25 septembre 2026).
2. Bat encore SPY sur ces 12 mois avec frais et glissement doublés.
3. Pire baisse inférieure à 30 % sur toute l'histoire testée.
4. Sharpe supérieur à 1,0 sur les 12 derniers mois.
5. Aucune action ne fait plus de 40 % des gains des 12 derniers mois.
6. Résultats identiques sur deux exécutions.
7. **Ajouté** : bat SPY après frais sur **toute** l'histoire disponible (depuis 2006 au plus tôt ;
   un an seul, c'est surtout du hasard).
8. **Ajouté** : fait mieux que 95 % des placebos sur toute l'histoire (même nombre de positions,
   choisies ou datées au hasard).

Les critères 1 à 6 sont ceux du texte d'origine ; 7 et 8 sont ajoutés parce qu'un an de données ne
permet pas de distinguer un avantage du hasard. Aucune stratégie n'est modifiée après les résultats :
un échec est inscrit au journal des rejets.

## Versions 5 et 6 (fixées le 28 septembre 2026, après le rejet des 4 premières, avant leur test)

Les 4 stratégies échouent toutes au critère 3 (pire baisse de −51 % à −59 %, en 2008). Une seule
correction est essayée, la plus classique contre les krachs (Faber, 2007) : **quand SPY clôture le mois
sous sa moyenne 200 jours, tout passe en liquidités** (rémunérées au taux court), sinon la stratégie
s'applique normalement.

5. **Version 5** = stratégie 4 (moteur macro) + ce filtre.
6. **Version 6** = stratégie 2 (momentum des actions) + ce filtre.

Mêmes 8 critères, mêmes frais. Placebo de la version 5 : la même suite de positions décalée au hasard
dans le temps ; de la version 6 : 5 actions tirées au hasard, avec le même filtre. Ce sont les essais
5 et 6 de cette étude : s'ils échouent, on s'arrête là.
