# XGBoost NQ : le setup quant (4 novembre 2026)

Stratégie Quantower à part, comme Supertrend NQ. Elle s'installe avec la même ligne PowerShell et apparaît dans le
Strategies manager sous le nom **XGBoost NQ (M2, 15 min)**. C'est le modèle M2 du labo ML (`ml/`), le seul résultat qui a
passé toutes les règles fixées d'avance.

## Le setup : 21 informations assemblées comme le font les quants

À la clôture de chaque bougie de 15 minutes du NQ (séance de New York, 15 h 30 - 22 h à Paris) :

| Famille | Ce qui est mesuré |
|---|---|
| Momentum | rendement des 15 dernières minutes, de la dernière heure, des 4 dernières heures, depuis l'ouverture, sur 5 séances |
| Tendance | écart EMA 8 - EMA 55, sens du Supertrend 10-3 et distance à sa ligne, MACD |
| Retour à la moyenne | position dans les bandes de Bollinger 20-2, RSI 14, distance au VWAP |
| Volatilité | ATR 14 / prix, rang de la largeur de Bollinger sur 500 bougies, volatilité du jour / moyenne des 20 dernières séances |
| Volume | VWAP de la séance (prix moyen pondéré par le volume) |
| Structure de séance | gap d'ouverture, séance de la veille, position dans la zone de bruit |
| Calendrier | heure de la journée, jour de la semaine |

**La formule** : 10 modèles XGBoost (100 arbres de décision chacun) ont appris sur 15 ans comment ces 21 informations
se combinent. Chacun donne une probabilité que le NQ soit plus haut 1 heure plus tard ; le bot fait la moyenne des 10.

**La règle** :
- probabilité **> 55 %** : achat 1 MNQ ; **< 45 %** : vente 1 MNQ ; entre les deux : rien ;
- une seule position à la fois, gardée **1 heure** (encore 1 heure si le signal suivant va dans le même sens) ;
- dernière entrée à la clôture de 15 h (New York), tout est fermé au plus tard à 15 h 55 ;
- ordres au marché sur MNQ, prix lus sur le NQ.

Protections : limite de perte du jour (tout fermé, plus de trade jusqu'au lendemain), arrêt définitif à l'objectif du
challenge, fichier `C:\XGBoostNQ\STOP`, position fermée à la main jamais rouverte avant le signal suivant, reprise après une
relance, messages Telegram à chaque ordre. La probabilité de chaque bougie est écrite dans `C:\XGBoostNQ\journal.txt`
(et apparaît dans le flux de la station en direct).

## Les chiffres (hors échantillon, 1 MNQ, 3 $ de frais, une position à la fois)

Marche en avant purgée : chaque année est testée par des modèles qui ne l'ont jamais vue.

| Période | $ par séance | t |
|---|---|---|
| 2014 - 2026 | +22,7 | **3,61** |
| 2014 - 2022 | — | 3,34 |
| 2023 - 2026 | +17,3 | 1,49 |

- Avec un seul modèle au lieu de 10, t 2014-2026 va de 2,6 à 4,1 selon le tirage, toujours positif : l'avantage tient. Depuis
  2023 il est faible (de −0,3 à +1,6 selon le tirage), comme celui du Supertrend (0,9).
- Les vérifications : étiquettes mélangées → plus aucun gain (le calcul ne voit pas le futur) ; entrée à la bougie suivante →
  même résultat ; frais doublés → t vers 2 (l'avantage est mince, 3 $ par aller-retour compte).

**Sur ton challenge** (départ à chaque séance de 2023 à juin 2026, 1 MNQ, limite 400 $) :

| Compte | Objectif atteint | Plancher touché |
|---|---|---|
| Ton compte actuel (50 000 $, plancher 49 000 $, objectif 53 050 $) | 27 % | 73 % |
| Compte neuf 50K, plancher suiveur en direct (Option 1) | 37 % | 62 % |
| Compte neuf 50K, plancher suiveur en fin de journée | **53 %** | 46 % |

Le Supertrend fait à peu près pareil sur ton compte actuel (26 % / 74 %). Ce qui change le plus les chances, ce n'est pas la
stratégie, c'est la règle du plancher : suivi en fin de journée plutôt qu'en direct.

## Réglages dans Quantower

| Réglage | Quoi mettre |
|---|---|
| Compte | ton compte Bulenox |
| NQ (prix et barres) | **NQZ6** (NQH7 après le changement d'échéance de décembre) |
| MNQ (ordres) | **MNQZ6** |
| MNQ par trade | **1** |
| Limite de perte du jour | **400** |
| Objectif | **53050** (solde à atteindre ; 0 = aucun) |
| Dossier | `C:\XGBoostNQ` |
| Telegram | les mêmes jeton et numéro que tes autres bots |

**Un seul bot par compte** : arrête Bot 3 en 1 et Supertrend NQ avant de lancer XGBoost NQ (sinon ils se disputent la même
position MNQ). Lance-le avant 15 h 30 (Paris) ; lancé plus tard, il rejoue la séance sans ordre et reprend au signal suivant.

Il a besoin de l'historique du robot (au moins 30 séances, téléchargé tout seul au lancement) : avec 5 semaines, ses 21
variables sont déjà identiques à celles du test.

## Vérifications faites

- Moteur C# (`XGBoost.Core`) contre Python (`ml/xgb_final.py`) : 21 variables et probabilité identiques sur 25 714 bougies
  (écart maximal 0,00000014), 6 163 signaux identiques sur 2023 - 2026 (`XGBoost.Replay`).
- Démarrage avec seulement l'historique du robot (depuis septembre 2025) : identique dès novembre 2025.
- Stratégie Quantower dans l'imitation de l'API (`XGBoost.TestQuantower`), séances d'août à novembre 2026 jouées
  transaction par transaction : mêmes 124 ordres que le moteur ; limite du jour, position fermée à la main, relance, fichier
  STOP et objectif se comportent comme prévu.
- Le modèle a appris jusqu'au 2 novembre 2026 : tout ce qu'il fera ensuite est réellement nouveau pour lui. Il n'a pas encore
  tourné dans le vrai Quantower : surveille la première séance.
