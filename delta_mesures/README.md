# Filtre delta : brut, proportion du volume, z-score de la séance (règles fixées le 21 octobre 2026, avant tout calcul)

## Demande de l'utilisateur (21 octobre 2026)

Le bot 3 en 1 (challenge Bulenox 50K, 4 MNQ, limite de perte du jour à 1 000 $) a touché sa limite de perte deux
séances de suite (20 et 21 octobre). Il reste environ 500 $ avant le plancher du challenge. L'utilisateur veut que le
filtre delta soit plus précis que le seul signe du déséquilibre, et demande de tester trois lectures du delta :
- le delta brut (le bot actuel) ;
- le delta en proportion du volume total ;
- le delta comparé aux bougies récentes de la même séance (z-score).

## Ce que fait le bot aujourd'hui (filtre H1, `bot3en1/Bot3en1.Core/Moteur.cs`, branche `claude/keen-babbage-r686cl`)

À un contrôle (10 h, 10 h 30, … 15 h 30, New York), la zone donne une cassure. Le trade n'est gardé que si le delta
(achats agressifs − ventes agressives) des 30 minutes qui finissent à la minute du contrôle va dans son sens. Sinon il
est écarté. Il reste alors « virtuel » jusqu'à sa sortie, et aucune nouvelle entrée n'est prise pendant ce temps.
Relance décochée.

## À savoir avant le calcul

La proportion du volume et le z-score ont **toujours le même signe que le delta brut**. Sans seuil, elles gardent
exactement les mêmes trades que le bot. Elles ne changent quelque chose que si l'on exige une **force minimale** du
déséquilibre. Chaque variante est donc : le delta va dans le sens du trade **et** il est assez fort.

## Variantes (fixées maintenant)

Fenêtre W : les 30 barres d'une minute qui finissent à la minute du contrôle (comme `Moteur.cs` `Delta`).
d_j = achats − ventes de la minute j ; D30 = somme des d_j sur W ; V30 = achats + ventes sur W.

| Nom | Mesure | Le trade est gardé si |
|---|---|---|
| **B, brut** | D30 | D30 × sens > 0 (le bot actuel) |
| **P, proportion du volume** | R = D30 / V30 | R × sens ≥ **1 %** |
| **Z, z-score de la séance** | Z = D30 / (σ × √30), σ = écart-type des d_j de 9 h 30 à la minute du contrôle (incluse) | Z × sens ≥ **1** |

- Seuil de P : 1 %, le seuil de `zone_neutre/` (branche de recherche), proposé avant tout calcul le 19 octobre.
- Seuil de Z : 1, c'est-à-dire un écart-type. Si les minutes de la séance n'avaient aucun déséquilibre, Z suivrait à peu
  près une loi normale centrée réduite : Z ≥ 1 veut dire un déséquilibre plus fort que dans 84 % des cas.
- Tout le reste est identique au bot : contrôles de 30 minutes, sorties, trade écarté virtuel jusqu'à sa sortie, sortie
  à 16 h, une seule position.
- Pour information seulement (aucune décision) : P à 0,5 %, 2 % et 5 % ; Z à 0,5, 1,5 et 2.

## Données

- **P1, Databento**, 1er avril - 1er octobre 2026 : `orderflow/donnees/nq_secondes_*.csv.gz` (branche de recherche),
  regroupé par minute. C'est la période où le filtre H1 a été trouvé : elle l'avantage.
- **P2, Rithmic**, 2 - 16 octobre 2026 : `filtre_h1/donnees_rithmic/transactions_NQZ6_rithmic.csv` (export de
  l'utilisateur).
- Barres du robot : `zone/robot/nq_1min.csv.gz` (main).
- Les séances du 19, 20 et 21 octobre ne sont pas mesurées : leurs transactions ne sont pas encore exportées.

## Mesures

1. Par période et par variante : trades gardés, points nets (1,5 point de frais par aller-retour), part de gagnants,
   pire baisse, pire séance.
2. Trades gardés par B mais écartés par P ou Z : nombre et gain moyen en points.
3. **Pour information, sans décision sur le filtre** : chances de valider le challenge depuis la situation de
   l'utilisateur. Il n'existe pas de delta avant avril 2026, donc la zone est jouée **sans filtre**, sur 15 ans.
   - Moteur de la vague 13 (`vague13/moteur13.py`, `vague4/moteur4.seance4`, sans changement de la séance), départ à
     chaque séance de 2012 à 2026.
   - Situation estimée, à remplacer par les vrais chiffres : solde 49 158 $ (50 000 + 1 172 − 1 002 − 1 012), plus haut
     de fin de journée 51 172 $, donc plancher 48 672 $ et 486 $ de marge. Objectif 53 000 $, arrêt à +50 $ au-dessus.
   - 16 séances (22 octobre - 12 novembre 2026), limite du jour 1 000 $, pas de zone les jours de la Fed.
   - Le moteur compte le challenge perdu dès que la valeur du compte, aux plus bas des minutes, touche le plancher.
   - Tailles : 1, 2, 3 et 4 MNQ pendant toute la période, puis 4 MNQ et 6 MNQ les 5 dernières séances (le réglage
     actuel).

## Décision (fixée maintenant)

P ou Z remplace B dans le bot **seulement si** :
1. elle fait au moins autant de points que B sur P1 **et** sur P2 ;
2. les trades qu'elle écarte en plus de B (P1 + P2) sont au moins 10, avec un gain moyen négatif.

Si P et Z passent toutes les deux : celle qui fait le plus de points sur P1 + P2. Si aucune ne passe, le bot garde B.

**Limite écrite d'avance** : environ 80 trades gardés en tout. Même une variante qui passe ne serait pas prouvée. Elle
serait seulement « pas pire sur les données qu'on a ».
