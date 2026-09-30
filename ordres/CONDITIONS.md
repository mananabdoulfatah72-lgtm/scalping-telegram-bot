# Order flow : à quel moment et dans quelles conditions ?

Suite de l'étude du 28 septembre (`README.md`), qui mesurait les signaux sur toutes les minutes en même
temps. Question de l'utilisateur, après un message sur un « bureau de trading order flow » (carte de
liquidation, carnet d'ordres, CVD) : **quand la configuration est-elle efficace, à quelle heure,
dans quelles conditions ?**

## Règles (fixées le 30 septembre 2026, avant tout calcul)

**Données** : les 23 séances ES déjà téléchargées (24 août - 25 septembre 2026), transactions avec
leur sens et meilleur acheteur / vendeur. **La carte de liquidation ne peut pas être testée** : elle
n'existe que pour les cryptos à effet de levier (estimée par les sites, pas de vrais ordres). Sur les
futures de la CME, les stops ne sont visibles par personne.

**Signaux** (calculés comme dans `analyse.py`, à la fin de chaque minute de 9 h 31 à 15 h 53) :
1. carnet fort : déséquilibre du 1er niveau dans le décile le plus haut (achat) ou le plus bas (vente) ;
2. OFI fort : même règle sur l'OFI ;
3. delta fort : même règle sur le delta de la minute ;
4. CVD fort : même règle sur le CVD des 15 minutes ;
5. divergence prix / CVD (« l'achat est faux ») : le signal d'absorption de `analyse.py` ;
6. carnet fort **et** CVD des 15 minutes du même côté (« le flux est réel »).

Les déciles sont ceux des 23 séances.

**Mesure** : mouvement du prix milieu sur les 1 et 5 minutes suivantes, dans le sens du signal, en
ticks, à chaque minute où le signal est présent. Frais déduits :
- **2,6 ticks** pour un aller-retour sur MES ;
- **1,4 tick** sur ES (1 tick d'écart + 0,4 tick de commissions).

**Conditions** (4 familles, 15 cases) :
- **heure** : 9 h 31-10 h, 10-11 h, 11-12 h, 12-13 h, 13-14 h, 14-15 h, 15 h-15 h 53 ;
- **volatilité** : amplitude du prix milieu sur les 15 minutes précédentes, par tiers (faible,
  moyenne, forte) ;
- **volume de la minute**, par tiers ;
- **sens de la journée** : signal dans le sens du mouvement depuis 9 h 30, ou contre.

**Tri** : 6 signaux × 2 durées × 15 cases = **180 cas**. Pour chacun :
- le gain net moyen ;
- son t, calculé sur les moyennes de chaque séance (les minutes voisines se ressemblent, la séance
  est l'unité).

Une case est **efficace** si elle remplit toutes ces conditions :
- gain net > 0 ;
- t ≥ 3,45 (Bonferroni, 5 % unilatéral pour 180 cas) ;
- au moins 30 signaux ;
- des signaux sur au moins 10 séances.

Le tri est fait séparément aux frais MES et aux frais ES. Une case efficace ne serait qu'une piste : il
faudrait la confirmer sur des séances jamais vues (après le 25 septembre) avant tout usage.

Les 180 cas sont inscrits dans `fonds/essais.csv`.

## Résultats (30 septembre 2026) : aucune condition efficace, 0 sur 180

`python3 conditions.py` refait tout (`resultats_conditions.txt`, `.csv`, `.json`). 23 séances,
8 832 minutes de décision.

**Aucune case ne passe, ni aux frais MES (2,6 ticks) ni aux frais ES (1,4 tick).** Le meilleur t de
toutes les cases est de +1,58, loin du seuil de 3,45.

Ce qui ressort quand même (à lire comme des tendances, pas comme des preuves) :

| Condition | Effet sur les signaux |
|---|---|
| **Durée** | Sur 5 minutes, le carnet fort vaut +1,4 tick brut, contre +0,6 sur 1 minute. |
| **Volatilité et volume forts** | Les signaux valent le plus : le carnet fort + CVD d'accord fait +3,3 à +3,6 ticks brut sur 5 min. |
| **Volatilité ou volume faibles** | Les signaux ne valent rien (−0,2 à +0,4 tick). |
| **Heure** | 11 h - 13 h est le meilleur moment pour le carnet (+2 à +2,5 ticks sur 5 min). L'ouverture (9 h 31 - 10 h) n'apporte rien. 13 h - 14 h est le pire moment. |
| **« Flux réel » (carnet + CVD d'accord)** | Un peu mieux que le carnet seul (+2,0 ticks contre +1,4 sur 5 min). |
| **Divergence prix / CVD** | Très rare (112 signaux en 23 séances). Aucun t au-dessus de 1,6. |

**En clair** :
- Même dans les meilleures conditions, le mouvement capté ne couvre pas les frais sur MES : il reste
  négatif ou tout juste positif, avec un t proche de 0.
- Sur le contrat ES entier, quelques cases feraient +1,5 à +2 ticks net, mais avec un t de 1 à 1,3 :
  impossible de les distinguer du hasard avec 23 séances.
- Pour savoir si ces cases sont réelles, il faudrait environ 7 fois plus de séances (environ
  160). Cela coûterait de l'ordre de 150 à 200 $ de données Databento.
