# Zone de bruit NQ : retirer plus du compte financé

L'utilisateur veut **retirer plus**. Avec la gestion actuelle du robot, presque aucun départ ne touche
d'argent en 12 mois (`zone_taille/` : médiane 0 $, 93 à 97 % des départs à 0 $). Deux étapes :
corriger les règles de retrait du robot, qui étaient périmées, puis optimiser ce que l'on contrôle.

## 1. Règles de Phidias 50K Fundamental (sources publiques d'octobre 2026, à vérifier sur le site)

Le site officiel est bloqué depuis l'environnement de calcul. Les chiffres viennent de sites d'avis
(fundedtrading.com, propscope.net, quantvps.com, propscorer.com), via des extraits de recherche.

| Règle | Avant (robot) | Maintenant |
|---|---|---|
| Challenge | +4 000 $, perte max 2 500 $ sous le plus haut de fin de journée | inchangé ; prix 164 $ (souvent moins avec un code promo) |
| Limite du compte financé | 2 500 $ sous le plus haut, bloquée à 50 100 $ dès 52 600 $ | inchangé |
| Quand retirer | tous les 21 jours | après **10 jours qualifiants** (jour à au moins +150 $) depuis le dernier retrait |
| Montant | tout ce qui dépasse 52 600 $ | ce qui dépasse 52 600 $, **500 $ minimum, 2 000 $ maximum** par retrait |
| Régularité | meilleure journée ≤ 30 % du gain depuis le dernier retrait | inchangé (le calcul repart à zéro après chaque retrait) |
| Part pour toi | 80 % | 80 % |

Hypothèses à vérifier :
- un jour qualifiant est un jour de gain d'au moins 150 $ pour le compte ;
- il faut garder 52 600 $ après un retrait (2 500 $ au-dessus de la limite bloquée).

Variante, pour information : 10 jours de trading au lieu de 10 jours qualifiants.

## 2. Ce que l'on optimise (fixé le 1er octobre 2026, avant tout calcul)

La stratégie ne change pas : zone corrigée V1 seule, 1 MNQ minimum, au plus 50. Seule la gestion
change.

Taille = f × marge / risque d'un MNQ, avec un f différent selon la phase :

| Réglage | Valeurs | Actuel |
|---|---|---|
| f pendant le challenge | 0,15 ; 0,25 ; 0,35 ; 0,50 | 0,15 |
| f sur le compte financé, avant que la limite soit bloquée (plus haut < 52 600 $) | 0,15 ; 0,25 ; 0,35 ; 0,50 | 0,15 |
| f sur le compte financé, limite bloquée à 50 100 $ | 0,15 ; 0,25 ; 0,35 ; 0,50 | 0,15 |
| marge gardée en plus après un retrait (on retire seulement au-dessus de 52 600 $ + marge) | 0 $ ; 1 000 $ | 0 $ |

Cela fait 128 gestions.

**Mesure.** Un départ par semaine, chaque départ suivi 24 mois. Un compte perdu, challenge ou compte
financé, est remplacé par un nouveau challenge payé 164 $.

**Score** : gain net par an = (80 % des retraits − 164 $ × challenges commencés) / 2.

**Choix** : la gestion au meilleur score moyen sur les départs 2011-2020, dont les 24 mois se
terminent avant 2023.

**Contrôle** : départs de janvier 2023 à septembre 2024, sur 24 mois. Ces départs se chevauchent :
c'est en pratique une seule période de marché. On donne aussi la version 12 mois pour les départs
2023-2025.

**Adoption** : la gestion choisie remplace l'actuelle dans le robot si son score est meilleur sur le
contrôle. Sinon, seules les règles corrigées sont portées. Dans les deux cas, les règles corrigées
entrent dans le robot.

On donne aussi :
- les gestions voisines de la gestion choisie, pour voir si le résultat tient à un réglage précis ;
- la part des départs qui ne reçoivent rien ;
- le nombre de challenges payés ;
- la variante « 10 jours de trading ».

Tous les essais sont inscrits dans `fonds/essais.csv`.

## Résultats (1er octobre 2026) : aucune gestion ne retire plus de façon fiable

`retrait.py` → `retrait.txt`, `grille.csv`. Contrôle de départ : le simulateur rapide donne exactement
les mêmes carrières que `une_journee` du robot, sur 12 carrières tirées au hasard.

| Départs suivis 24 mois | Reçu par an | Challenges payés par an | Gain net par an | Départs sans rien |
|---|---|---|---|---|
| 2011-2020, gestion actuelle (0,15 / 0,15 / 0,15 / 0 $) | 61 $ | 1,49 | −184 $ | 85 % |
| 2011-2020, choisie (0,15 / 0,15 / 0,15 / marge 1 000 $) | 80 $ | 1,49 | −164 $ | 87 % |
| 2023-2024, gestion actuelle | 158 $ | 1,09 | −22 $ | 79 % |
| 2023-2024, choisie | 109 $ | 1,09 | −70 $ | 79 % |

- **Toutes les gestions perdent de l'argent sur 2011-2020** une fois les challenges payés. La médiane
  des 128 fait −497 $ par an. La gestion actuelle est 5e. Les 10 meilleures sont toutes proches
  d'elle : f = 0,15 ou 0,25, et 0,15 une fois la limite bloquée.
- **La choisie ne passe pas le contrôle** : −70 $ par an contre −22 $ pour l'actuelle sur 2023-2024.
  Elle n'est pas adoptée. Seules les règles corrigées sont portées dans le robot.
- **12 mois, départs 2023-2025** : actuelle 197 $ reçus par an, net −114 $ ; choisie 137 $, net
  −175 $.
- **Variante « 10 jours de trading »** (information) : un peu mieux sur 2011-2020 (actuelle −86 $ par
  an), sans changement sur 2023-2024.
- **Challenge à 65,60 $ avec un code promo** (regardé après coup, pour information) : la meilleure
  gestion sur 2011-2020 devient plus agressive (0,25 / 0,25 / 0,15 / 0 $, +126 $ par an). Sur
  2023-2024, elle fait +27 $ par an contre +86 $ pour l'actuelle.

**Pourquoi** :
- La zone gagne 11,5 $ par séance pour 1 MNQ sur 2023-2026, avec un écart-type de 202 $ (Sharpe
  annuel 0,90). Sur 2011-2020 : 1,1 $ pour 58 $ (Sharpe 0,31).
- Avant tout retrait, il faut monter de 2 600 $ sans reculer de 2 500 $, puis faire 10 jours à au
  moins +150 $. À 1 MNQ, 13,6 % des séances y arrivent sur 2023-2026, et 2,1 % sur 2011-2020.
- Avec ce rapport gain/risque, prendre plus de risque fait sauter plus de comptes que cela ne
  rapporte. En prendre moins repousse les retraits au-delà de l'horizon.

La gestion n'est pas le levier. Il faudrait un avantage nettement meilleur, ou plusieurs sources de
gain peu liées entre elles.
