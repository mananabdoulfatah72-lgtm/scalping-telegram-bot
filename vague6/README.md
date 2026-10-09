# Vague 6 : des comptes aux règles plus favorables, et une taille 3× pendant le challenge (règles fixées le 9 octobre 2026, avant le calcul)

## Demande de l'utilisateur

1. Chercher des comptes aux règles plus favorables à ce bot : plafond de retrait plus haut, pas de règle d'activité,
   plancher qui ne bouge pas.
2. Pousser la taille pendant le challenge à 3×, puisque le 2× a aidé partout.

« On ne s'arrête pas tant qu'on n'a pas trouvé et tout testé. »

## Point de départ (vague 5, calcul final)

Un seul compte à la fois, racheté dès qu'il est perdu, avec le filtre simulé aussi bon qu'en 2026. La meilleure
candidate est Topstep (zone + A3, challenge 2×, financé 2×) : **+557 $ par mois sur 2012-2022, +388 $ sur 2023 -
sept. 2026**. Le Static fait +407 / +392 $.

## Partie A : les comptes trouvés (`regles_firmes.md`, sources citées)

Trois comptes acceptent les robots entièrement automatiques et ont des retraits plus larges que ceux déjà testés :

| Compte | Ce qui change par rapport à Topstep et au Static |
|---|---|
| **DayTraders S2L Core 50K** | compte live : tout ce qui dépasse 51 000 $ peut être retiré chaque jour, sans plafond (80 %) ; pas de régularité ni de règle d'activité une fois live ; nuit permise |
| **FundedNext Legacy 50K** | jusqu'à 6 000 $ par retrait (au lieu de 2 000 $) ; pas de régularité ni de limite du jour sur le compte financé |
| **LucidFlex 50K** | comme Topstep, mais sans limite du jour ; prix payé une fois |

Écartés : TradeDay 2.0 (50 % pour le trader sur le compte simulé), Tradeify Select / Lightning (plafonds
contradictoires), et les firmes qui interdisent les robots sur le compte financé.

## Les règles simulées (choix prudents quand les sources se contredisent)

**DayTraders S2L Core** (moteur du Static, `regle = 3`, bot E4 : zone 1 MNQ + RSI(2) sur 1 MES gardé la nuit) :
- **Évaluation** :
  - objectif +3 000 $, au moins 8 jours à +200 $, meilleur jour ≤ 25 % du gain ;
  - plancher 2 000 $ sous le plus haut **suivi en direct** (plus hauts des minutes et des barres de nuit, positions
    comprises), qui s'arrête au solde de départ ;
  - limite du jour douce de 1 000 $ (tout fermé jusqu'à 18 h) ;
  - règle d'activité de DayTraders appliquée ;
  - **229 $** par essai, sans activation.
- **Compte live** :
  - même plancher suivi en direct, à partir du départ du compte live, jusqu'au solde de départ ; un retrait ne baisse pas
    le plus haut retenu (prudent) ;
  - limite du jour douce de 1 000 $ ;
  - à partir de la 8e séance, à chaque fin de journée : retrait de tout ce qui dépasse 51 000 $ + la réserve choisie,
    s'il fait au moins 500 $ ; **80 %** pour le trader ;
  - pas de régularité, pas de règle d'activité.

**FundedNext Legacy** (moteur de Topstep, bot zone + A3) :
- challenge : objectif +3 000 $, plancher 2 000 $ en fin de journée bloqué au départ, pas de limite du jour,
  régularité 40 %, **200 $** par essai ;
- compte financé : même plancher ; pas de limite du jour ; retrait après 5 jours à +200 $ ; 50 % du gain au plus,
  6 000 $ au plus, 250 $ au moins ; **80 %** pour le trader.
- Prudent : le plafond de 50 % reste même après 30 jours de référence (il est levé en vrai).

**LucidFlex** (moteur de Topstep, bot zone + A3) :
- évaluation : objectif +3 000 $, plancher 2 000 $ en fin de journée bloqué à +100 $, pas de limite du jour,
  régularité 50 %, **140 $** par essai ;
- compte financé : même plancher ; pas de limite du jour ; 5 jours à +150 $ par cycle ; 50 % du gain au plus,
  2 000 $ au plus, 500 $ au moins ; **90 %** pour le trader.

Topstep et le Static gardent leurs règles de la vague 5 : règle d'activité appliquée au Static.

## Partie B : les candidates (fixées maintenant)

| Compte | Bot | Taille du challenge | Taille du compte financé | Réserve | Nombre |
|---|---|---|---|---|---|
| Topstep | zone + A3 | 1×, 2×, **3×** | 1×, 2× (dès 4 000 $ de coussin) | aucune | 6 |
| LucidFlex | zone + A3 | 1×, 2×, 3× | 1×, 2× | aucune | 6 |
| FundedNext Legacy | zone + A3 | 1×, 2×, 3× | 1×, 2× | aucune | 6 |
| DayTraders Static | E4 | 1×, 2×, 3× | 1×, 2× | aucune | 6 |
| DayTraders S2L | E4 | 1×, 2×, 3× | 1×, 2× | 0, 1 000 $, 2 000 $ | 18 |

42 candidates :
- 3× = trois fois chaque nouvelle entrée, zone et RSI(2) ;
- la réserve n'est essayée que sur le S2L, le seul compte où les retraits n'ont pas de plafond (elle avait fait perdre
  ailleurs en vague 5).

## Méthode et jugement (comme la vague 5, calcul final)

- **Méthode** :
  - chaque trade au niveau d'aujourd'hui de son jour d'entrée ;
  - un compte est gardé tant qu'il vit ;
  - un seul compte à la fois, racheté dès qu'il est perdu.
- **Mesure** : gain net par mois du calendrier (retraits × part du trader − prix), avec le filtre simulé aussi bon qu'en
  2026.
- **Fenêtres** :
  - choix 2012-2022 (10 tirages × 10 dates de départ) ;
  - vérification 2023 - sept. 2026 (10 tirages × 20 dates).
- **Retenue** : la meilleure sur la fenêtre de choix, tous comptes confondus.
- **Validée** si, sur la vérification :
  1. elle fait au moins +388 $ par mois (la retenue de la vague 5) ;
  2. chaque année est positive.

  Sinon, on passe à la suivante.
- **Objectif atteint** si la retenue validée fait au moins 500 $ par mois en vérification.
- **À savoir avant d'y croire** :
  - la vérification 2023-2026 a déjà servi plusieurs fois (vagues 4 et 5) : un gain nouveau y est moins sûr ;
  - les règles des nouveaux comptes viennent de sites d'avis.
- **Descriptif** :
  - sans filtre et filtre inutile ;
  - chaque année ;
  - la part des mois avec un retrait ;
  - S2L avec une limite du jour **définitive** (compte perdu à −1 000 $ dans la journée), car une source dit « aucune »
    et l'autre ne précise pas.

## Contrôles (`test_vague6.py`)

1. Sans S2L, le moteur redonne les résultats d'avant : `test_static.py`, `test_vague4.py` et `test_vague5.py` passent,
   et `vague5_regles.txt` est redonné à l'identique.
2. S2L sur un marché synthétique, recalculé à la main :
   - le plancher suit le plus haut de la journée (un compte qui finit la journée en hausse peut être perdu par un creux
     de 2 000 $ sous son plus haut du jour), et s'arrête au solde de départ ;
   - l'évaluation est réussie à la bonne séance (8 jours, 25 %) ;
   - les retraits commencent à la 8e séance live et laissent 51 000 $ + la réserve ;
   - la limite du jour ferme tout à −1 000 $.
3. FundedNext et LucidFlex : les paramètres passés au moteur sont ceux écrits ici ; un retrait de FundedNext peut
   dépasser 2 000 $.
4. La taille 3× donne trois fois le gain d'un jour sans limite.
