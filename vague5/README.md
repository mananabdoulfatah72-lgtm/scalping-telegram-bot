# Vague 5 : 500 à 850 $ par mois avec un seul compte, règles comprises (règles fixées le 9 octobre 2026, avant le calcul des leviers)

## Demande de l'utilisateur (9 octobre 2026)

- Le bot seul fait 500 à 850 $ par mois. Avec les règles d'un compte 50K, il ne reste que 140 à 410 $.
- Il faut trouver comment gagner 500 à 850 $ par mois **avec les règles**, sur un seul compte.
- On peut enlever ce qui ne rapporte pas assez.
- Le filtre delta est à compter comme acquis dans la stratégie.

## Étape 1 : où on part (`socle.py`, `socle.txt`, descriptif)

La mesure est la même partout : **un seul compte à la fois**, racheté dès qu'il est perdu (ou après 24 mois s'il est
encore en vie, parce que le niveau des prix est figé à l'achat). On compte les gains nets par mois du calendrier :
retraits − prix − activation. Les prix sont au niveau d'aujourd'hui. On prend 20 dates de départ, une séance sur cinq,
et 10 tirages du filtre simulé (ρ 0,24). Chaque compte joue le système déjà retenu pour lui.

| Compte | Sans filtre : 2012-2022 / 2023 - sept. 2026 | Filtre aussi bon qu'en 2026 | Filtre inutile |
|---|---|---|---|
| Topstep, zone + A3 | +217 / +141 $ | +337 / +410 $ | +105 / +116 $ |
| Tradeify Growth, zone seule | +74 / +76 $ | +206 / +200 $ | +49 / +61 $ |
| **DayTraders Static, E0 P500** (Pro au plancher fixe) | +356 / +326 $ | **+401 / +434 $** | +262 / +238 $ |
| DayTraders Static, E0 P500 (Pro pessimiste) | +140 / +44 $ | +217 / +163 $ | +117 / +76 $ |
| DayTraders S2F, E0 P500 (570 $, puis 342 $ par rachat) | +294 / +266 $ | +339 / +377 $ | +238 / +242 $ |

Aucun compte n'atteint 500 $ par mois. Seuls 20 à 38 % des mois contiennent un retrait : les retraits arrivent par
paquets de 2 000 $ au plus.

**Tradeify est abandonné** : il fait moitié moins que les autres. Les leviers sont essayés sur Topstep, le Static et
le S2F.

## Étape 2 : les leviers (fixés maintenant, avant tout calcul)

Ce qui coûte de l'argent entre le bot seul et le compte :
- le temps du challenge, sans retrait ;
- les règles de retrait (jours gagnants, régularité, plafonds) ;
- les comptes perdus, avec le gain non retiré.

Trois leviers, les mêmes pour tous les comptes :

1. **Taille du compte financé** :
   - « 1× » : la taille d'aujourd'hui ;
   - « 2× » : chaque jour où le coussin (solde de fin de la veille − plancher) est d'au moins **4 000 $**, chaque
     nouvelle entrée prend deux fois sa taille (zone, RSI(2)), et le plafond du jour est doublé (Static, S2F : 1 000 $).
     En dessous de 4 000 $, on reste en 1×.
2. **Réserve** : laisser **1 000 $** de plus sur le compte à chaque retrait (« R1000 »), ou non (« R0 »). On retire
   moins tout de suite, pour que le compte vive plus longtemps.
3. **Taille du challenge** (Topstep et Static seulement ; le S2F n'a pas de challenge) : 1× ou 2× dès le début (le prix
   d'un challenge perdu est faible, le temps compte).

Plus, pour enlever ce qui rapporte peu :
- Topstep : zone + A3, ou zone seule ;
- Static et S2F : E0 (RSI(2) sur MNQ, le bot tel quel), ou E4 (RSI(2) sur MES).

| Compte | Candidates |
|---|---|
| Topstep | bot (zone + A3, zone seule) × challenge (1×, 2×) × financé (1×, 2×) × réserve (R0, R1000) : 16 |
| DayTraders Static | bot (E0, E4) × évaluation (1×, 2×) × Pro (1×, 2×) × réserve : 16 |
| DayTraders S2F | bot (E0, E4) × financé (1×, 2×) × réserve : 8 |

Les règles de chaque compte ne changent pas (`intraday50k/`, `static50k/`). Le plafond du jour de 500 $ reste sur le
compte Pro du Static et sur le S2F. La taille reste limitée par les règles des firmes (au plus 2 MNQ + 2 MNQ ou 2 MES,
bien sous les maximums des comptes 50K).

## Le jugement (fixé maintenant)

- **Mesure** : gain net moyen par mois d'un seul compte à la fois, avec le **filtre simulé aussi bon qu'en 2026**
  (demande de l'utilisateur).
  - Choix : fenêtre du 3 janvier 2012 au 30 décembre 2022, 10 tirages × 10 dates de départ.
  - Vérification : 2023 - septembre 2026, 10 tirages × 20 dates de départ.
  - Static : compte Pro au plancher fixe (la version pessimiste est montrée à côté).
- **Retenue** : la candidate qui a la mesure la plus haute sur la fenêtre de choix, tous comptes confondus. La meilleure
  de chaque compte est aussi publiée.
- **Validée** si, sur la vérification :
  1. elle fait au moins autant que le système actuel du même compte ;
  2. chaque année est positive, 2026 comprise.

  Sinon, on prend la suivante du classement qui passe ces deux points.
- **Objectif atteint** si la retenue validée fait au moins 500 $ par mois sur la vérification.
- **Publié dans tous les cas, à titre descriptif** :
  - sans filtre et filtre inutile ;
  - le Static pessimiste ;
  - chaque année ;
  - la part des mois avec un retrait ;
  - le nombre de comptes rachetés par an ;
  - les pires 12 mois de suite.

## Contrôles (`test_vague5.py`)

1. Sans levier, les deux moteurs redonnent leurs résultats d'avant : `test_static.py` et `test_vague4.py` passent, et
   l'étape 1 est inchangée.
2. Une taille 2× sans aucune limite redonne exactement deux fois le gain de chaque jour : zone, RSI(2) et frais.
3. Avec la réserve, chaque retrait laisse au moins 1 000 $ de plus sur le compte, et c'est le plus grand retrait
   permis.
4. La taille du compte financé ne change rien au challenge : même issue, même durée.

## Précisions après la revue de code (9 octobre 2026, avant la publication des résultats)

Une revue indépendante du premier calcul a trouvé deux erreurs et une imprécision, toutes corrigées. Tout a été
recalculé.
1. **Topstep : le 2× ne doublait que la zone, pas le RSI(2) de nuit (A3).** Le README dit « zone, RSI(2) ». Corrigé
   dans `moteur4.py`. Le contrôle 2 vérifie maintenant que le gain de zone + A3 double.
2. **La réserve n'avait presque pas d'effet sur Topstep et le S2F.** Elle s'ajoutait au solde gardé, mais la règle
   des 50 % (Topstep) et le plafond de 2 000 $ (S2F) décidaient le plus souvent du retrait. Elle est maintenant
   appliquée telle qu'écrite : **chaque retrait est de 1 000 $ de moins que le plus grand retrait permis**, sur les
   trois comptes. Le contrôle 3 le vérifie retrait par retrait.
3. La colonne « mois avec un gain » est remplacée par **« mois avec un retrait »**, comme demandé plus haut. Le
   contrôle 5 vérifie aussi que le plafond du jour double avec la taille.

Le classement de tête et la décision ne changent pas.

## Résultats (9 octobre 2026) : `vague5.txt`

Contrôles : `test_vague5.py` 5 sur 5, `test_static.py` 10 sur 10, `test_vague4.py` 5 sur 5.

**La retenue** est **Static E4, challenge 2×, financé 1×, R0**, et elle est **validée** :
- sur les deux évaluations, le bot joue deux fois sa taille (2 MNQ de zone, 2 MES de RSI(2)) ;
- sur le compte Pro, il revient à sa taille d'aujourd'hui (zone 1 MNQ, RSI(2) 1 MES), avec le plafond du jour de 500 $ ;
- chaque retrait est le plus grand permis.

| Gains nets par mois, un seul compte à la fois | Choix 2012-2022 | Vérification 2023 - sept. 2026 |
|---|---|---|
| **Static E4, challenge 2×** (filtre aussi bon qu'en 2026) | **+491 $** | **+444 $** (2023 +396, 2024 +1 041, 2025 +191, 2026 +47) |
| Static, système actuel (E0, 1×) | +399 $ | +434 $ |
| meilleure Topstep : zone + A3, challenge 2×, financé 2× | +462 $ | +441 $ |
| Topstep zone + A3, challenge 2×, financé 1× | +455 $ | +448 $ |
| Topstep, système actuel | +344 $ | +410 $ |
| meilleure S2F : E4, 1× | +400 $ | +374 $ |

**L'objectif de 500 $ par mois n'est pas atteint** : 444 $ en vérification.

Ce qui aide, ce qui n'aide pas :
- **Doubler la taille pendant le challenge aide partout.** Un challenge perdu coûte peu, et un challenge réussi plus vite
  fait gagner des mois : Static +70 $ par mois sur le choix, Topstep +110 $.
- **Doubler la taille sur le compte financé n'aide pas** (de −11 à +7 $) : les comptes sont perdus plus souvent.
- **La réserve fait perdre** : de −40 à −255 $ par mois. Les retraits sont plafonnés, donc retirer moins ne se rattrape
  pas.
- **RSI(2) sur MES plutôt que MNQ (E4)** aide le Static (+29 $ sur le choix).
- **Enlever A3 chez Topstep fait perdre** de 80 à 90 $ par mois.

Descriptif, Static E4 challenge 2× (choix / vérification) :
- sans filtre : +393 / +393 $ ;
- filtre inutile : +313 / +306 $ ;
- Pro pessimiste (plancher qui remonte après un retrait) : +323 / +293 $ ;
- un retrait dans 26 à 28 % des mois ;
- pires 12 mois de suite : −380 à −540 $ (abonnements payés sans retrait).

Topstep dépend beaucoup plus du filtre : sa meilleure candidate fait +182 $ sans filtre en vérification, contre +393 $
pour le Static.
