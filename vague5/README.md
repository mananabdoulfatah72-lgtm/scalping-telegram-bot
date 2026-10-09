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

Ce qui aide, ce qui n'aide pas (effet de chaque levier, toutes les autres choses égales, sur la fenêtre de choix) :
- **Doubler la taille pendant le challenge aide partout** : de +24 à +117 $ par mois. Un challenge perdu coûte peu, et
  un challenge réussi plus vite fait gagner des mois.
- **Doubler la taille sur le compte financé n'aide pas** : de −48 à +15 $. Les comptes sont perdus plus souvent.
- **La réserve fait perdre** : de −15 à −255 $. Les retraits sont plafonnés, donc retirer moins ne se rattrape pas.
- **RSI(2) sur MES plutôt que MNQ (E4)** aide le Static et le S2F : de +14 à +56 $.
- **Enlever A3 chez Topstep fait perdre** : de −33 à −101 $.

Descriptif, Static E4 challenge 2× (choix / vérification) :
- sans filtre : +393 / +393 $ ;
- filtre inutile : +313 / +306 $ ;
- Pro pessimiste (plancher qui remonte après un retrait) : +323 / +293 $ ;
- un retrait dans 26 à 28 % des mois ;
- pires 12 mois de suite : −380 à −540 $ (abonnements payés sans retrait).

Topstep dépend beaucoup plus du filtre : sa meilleure candidate fait +182 $ sans filtre en vérification, contre +393 $
pour le Static.

## Correction de méthode (9 octobre 2026, écrite avant le calcul corrigé)

**Ce qui a été trouvé** (`pourquoi.py`, `deux_comptes.py`, descriptif) :
- Le Static fait peu en 2025 (+191 $ par mois) et en 2026 (+47 $). Une grande partie vient de la limite de 24 mois.
- Beaucoup de comptes Pro achetés en 2023 étaient encore en vie début 2025. Le calcul les « rachetait » de force, et
  les nouvelles évaluations de 2025 échouaient (77 % au seuil).
- Sans cette limite, le Static fait +530 $ par mois sur 2023 - sept. 2026 (2025 : +403 $). Mais ce chiffre est gonflé.
  Le facteur de prix reste celui du jour de l'achat : un compte acheté en 2023 joue encore en 2026 avec des prix
  multipliés par 2,3, soit un NQ deux fois plus cher qu'aujourd'hui.

**La correction** (dans les deux moteurs, sans effet dans l'ancien mode : `vague5.txt` redonné à l'identique) :
- **Chaque trade est joué au niveau d'aujourd'hui de son jour d'entrée.** Le facteur vaut dernière clôture des données
  / clôture de la séance d'avant. La zone prend celui du jour, le RSI(2) garde celui de son entrée jusqu'à sa sortie.
  Les seuils, les frais et les retraits restent en dollars.
- **Plus de limite de 24 mois** : un compte est gardé tant qu'il vit.

**Le calcul corrigé** (`python3 vague5.py jour` → `vague5_jour.txt`) reprend tout le reste à l'identique :
- les mêmes 40 candidates, fenêtres, tirages et dates de départ ;
- le même classement et la même décision.

Il remplace le premier calcul comme résultat principal. Le premier calcul reste publié pour mémoire.

Contrôles ajoutés (`test_vague5.py`) :

6. Le premier jour d'un achat, le mode « jour » redonne exactement le mode « achat », car le facteur est le même ce
   jour-là.
7. Une position du RSI(2) garde le facteur de son entrée : changer le facteur des jours suivants ne change rien jusqu'à
   sa sortie.
8. Un trade de zone prend le facteur de son jour : changer le facteur d'un seul jour ne change que le gain de ce jour.
9. Pas de regard vers le futur : changer les facteurs après la fin d'un compte ne change rien.

## Deuxième correction (9 octobre 2026, après la revue du calcul corrigé, avant le calcul final)

La revue indépendante n'a trouvé aucune erreur dans les facteurs de prix. Elle a trouvé un effet qui fausse le résultat
du Static :
- **Sans la limite de 24 mois, les comptes Pro deviennent presque impossibles à perdre.** On ne retire que 2 000 $ à la
  fois, et la règle des 30 % freine les retraits, donc le solde monte sans fin : en médiane, +82 000 $ au-dessus du
  départ sur 2012-2022, contre un plancher à −1 000 $.
- **Ces comptes ne respectent pas la règle d'activité de DayTraders.** La règle : au moins un jour à +200 $ tous les
  30 jours, sinon le compte peut être coupé et doit être racheté (`research_notes/…/daytraders.md`, page d'aide
  officielle « Minimum Activity Policy »). Le moteur la notait sans l'appliquer. 99 % de ces comptes la violent un
  jour.

**Correction** : la règle d'activité est appliquée sur le Static et le S2F, à l'évaluation et au compte financé. Au bout
de 21 séances de suite sans un jour à +200 $, le compte est coupé et racheté. C'est le cas prudent, parce que la page
dit « peut être coupé ». Topstep n'a pas cette règle.

**Le calcul final** (`python3 vague5.py regles` → `vague5_regles.txt`) reprend tout le reste du calcul corrigé :
- chaque trade au niveau d'aujourd'hui de son jour d'entrée ;
- pas de limite de 24 mois ;
- les mêmes 40 candidates et la même décision.

Il devient le résultat principal. `vague5_jour.txt` reste publié pour mémoire : c'est ce que donnerait le Static si
DayTraders n'appliquait jamais la règle d'activité.

Contrôles ajoutés :
- **7 bis** : le RSI(2) garde son facteur sur MNQ (E0) et sur MES (E4), avec un plancher bas souvent touché, la nuit
  comprise. Les contrôles 6 à 9 ne le vérifiaient que sur MES sans plancher.
- **10** : avec la règle d'activité, le compte est coupé exactement à la 21e séance sans un jour à +200 $.

## Résultat final (9 octobre 2026) : `vague5_regles.txt`, `deux_comptes_regles.txt`

Le calcul est fidèle aux règles connues :
- chaque trade est au niveau d'aujourd'hui de son jour d'entrée ;
- un compte est gardé tant qu'il vit ;
- la règle d'activité de DayTraders est appliquée.

Contrôles : `test_vague5.py` 8 sur 8, `test_static.py` 10 sur 10, `test_vague4.py` 5 sur 5.

**Retenue et validée : Topstep, zone + A3, challenge 2×, financé 2× dès 4 000 $ de coussin.**
- Elle fait +557 $ par mois sur le choix 2012-2022 et **+388 $ en vérification** (2023 +370, 2024 +600, 2025 +170,
  2026 +419). **L'objectif de 500 $ n'est pas atteint avec un seul compte.**
- Le système actuel de Topstep fait +329 $.
- Meilleur Static (E4, challenge 2×, Pro 2×) : +407 / +392 $ (2025 +290, 2026 +7). Meilleur S2F : +309 / +214 $.

**Deux comptes en même temps** (ce Static + ce Topstep, même filtre simulé, mêmes dates de départ) :

| | 2023 | 2024 | 2025 | 2026 (9 mois) | Moyenne |
|---|---|---|---|---|---|
| filtre aussi bon qu'en 2026 | +634 $ | +1 510 $ | +460 $ | +426 $ | **+779 $** |
| sans filtre | +517 $ | +1 050 $ | +222 $ | +23 $ | +482 $ |

- Avec le filtre, 42 % des mois atteignent 500 $ ou plus.
- Un mois sur deux, aucun des deux comptes ne verse rien : les retraits sont de 500 à 2 000 $ à la fois.

**Pourquoi 2025 et 2026 sont faibles** (`pourquoi.txt`) :
- **Le bot gagne moins.** Seul, sans compte, avec le filtre simulé, il fait +1 007 $ par mois en 2023, +699 $ en 2025
  et +605 $ en 2026. La zone sans filtre passe de +770 $ (2023) à +200 $ (2025).
- **Ce n'est pas un marché plus agité** : l'écart entre le plus haut et le plus bas d'une séance est de 1,41 % du prix
  en 2023 et 1,46 % en 2025.
- **Les seuils de perte des comptes amplifient la baisse** : chez Topstep, 80 % des challenges achetés en 2025 ont
  touché le seuil.
