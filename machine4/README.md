# Machine 4 : une très grande recherche de 4e source pour le bot 3 en 1

Demande de l'utilisateur (3 octobre 2026) : en attendant le test du filtre delta sur Rithmic, chercher
parmi un très grand nombre de stratégies celles qui viendraient **compenser ou s'ajouter** au bot 3 en 1
(zone de bruit, RSI(2), filtre delta), quitte à **baisser les exigences**.

## Ce qui change par rapport aux machines précédentes

Les machines 1 à 3 et la machine order flow (≈ 250 000 stratégies) cherchaient **dans la séance**, sur
des barres de 1 à 5 minutes. Le bruit y faisait aussi bien que les vraies données. Celle-ci cherche
ailleurs :

- **à l'échelle de la journée et de plusieurs jours**, positions gardées la nuit (le compte du bot le
  permet déjà pour le RSI(2)) ;
- **sur les 40 futures CME** téléchargés pour `fonds/`, et pas seulement le Nasdaq ;
- avec une famille **croisée** : le mouvement d'un marché (taux, dollar, pétrole…) qui annonce celui
  d'un autre les jours suivants ;
- et elle juge une stratégie sur ce qu'elle **apporte au bot** : elle doit gagner, mais **sans gagner
  et perdre en même temps que lui**.

## Baisser les exigences, honnêtement

Plus on essaie de stratégies, plus la meilleure paraît bonne **par chance**. Sur 360 000 essais,
plusieurs centaines dépasseront t = 3 sur du pur hasard. Tester « des millions » ne fait donc pas
apparaître une vraie piste : ça fait surtout apparaître de fausses. Ce qu'on peut baisser, c'est
l'exigence de **force**. Ce qu'on garde, c'est l'exigence de **réalité** :

1. **Jumeau de bruit.** Exactement la même recherche est refaite 8 fois sur des marchés où l'ordre des
   journées a été tiré au hasard. Toute prévisibilité est détruite, mais la tendance de fond et la
   forme des journées restent. Pour chaque niveau de t, on compte combien de stratégies le dépassent
   sur les vraies données et, en moyenne, sur le bruit. Le rapport donne la **part de fausses pistes
   attendue** à ce niveau (taux de fausses découvertes, Storey 2002).
2. **Deux paliers au coffre** au lieu d'un seul :
   - **retenue** (barre habituelle) : peut entrer dans le bot ;
   - **intéressante** (barre baissée, à la demande de l'utilisateur) : à suivre **en argent virtuel
     seulement**, pas en argent réel.
3. **Mesure du hasard au coffre.** Les règles choisies sur le bruit sont elles aussi passées au coffre,
   sur les vraies données. On sait ainsi combien de fois chaque palier laisse passer une règle choisie
   sans aucune information.

## Règles (fixées le 3 octobre 2026, avant tout calcul)

### Données et exécution

- **Barres journalières Databento** (`fonds/donnees/futures_1d.csv.gz`), contrat le plus échangé, juin
  2010 - septembre 2026. Rendements continus sans saut d'échéance, calculés comme
  `tournoi9/tournoi9.py charger`. Les séances courtes des jours fériés de la Bourse sont fusionnées avec
  la suivante, et les variations de plus de 50 % sont neutralisées. Les indicateurs sont calculés sur la
  série continue.
- **Calendrier commun** : les séances du ES. Si un marché n'a pas de barre une séance, son rendement est
  nul ce jour-là et sa barre suivante porte tout le mouvement. Si un marché a une barre hors du
  calendrier commun, elle est fusionnée avec la séance commune suivante.
- **Décision à la clôture de la séance, exécutée à ce prix** (comme les tournois 8 et 9), plus 1 tick
  de glissement et 1 $ par ordre. La position tenue après la clôture t gagne le rendement de t + 1. Un
  passage d'échéance en position coûte un aller-retour.
- **Famille croisée : décalage d'une séance.** Les marchés ne ferment pas tous à la même heure. Un
  marché source n'est donc utilisé qu'avec sa clôture de la **veille**, pour ne jamais lire une clôture
  postérieure à la décision.
- **1 contrat**, sans ajustement de taille, comme le bot (1 MNQ) :
  - micro pour ES, NQ, RTY, YM (MES, MNQ, M2K, MYM), GC (MGC), SI (SIL, 1 000 onces), HG (MHG),
    CL (MCL), 6E, 6A, 6B (M6E, M6A, M6B), BTC (MBT, 0,1) et ETH (MET, 0,1) ;
  - contrat standard pour les autres.
- **Marchés tradables** : écart-type du gain journalier d'un contrat sur 2011-2022 ≤ 400 $ (un jour
  normal ne doit pas coûter plus de 16 % de la perte maximale de 2 500 $). Les 40 marchés servent tous
  de **sources** pour la famille croisée. Les produits autorisés restent à vérifier chez la prop firm.

### Les 9 familles (paramètres en grille, tout est essayé)

Sens possibles : achats seuls, ventes seules, ou les deux. Le filtre de tendance (aucun, moyenne des
50, des 100 ou des 200 clôtures) n'autorise un achat qu'au-dessus de la moyenne et une vente qu'en
dessous. À chaque clôture, on regarde d'abord la sortie, puis l'entrée. Une entrée dans le sens déjà
tenu prolonge la position, sans frais.

| # | Famille | Entrée (achat ; la vente est le miroir) | Sortie | Grille |
|---|---|---|---|---|
| 1 | RSI court | RSI(n) de Wilder < s | clôture > moyenne des k, ou après h séances | n 2-5, s 5-30 (6), filtre 4, sortie 8 (k 3, 5, 10 ; h 1, 2, 3, 5, 10), sens 3 |
| 2 | IBS | (C − B) / (H − B) de la séance < x | après h séances, ou clôture > moyenne des 5 | x 0,10-0,30 (5), filtre 4, sortie 5 (h 1, 2, 3, 5), sens 3 |
| 3 | Plus bas de n jours | clôture = plus basse des n dernières | clôture = plus haute des k dernières, ou après h séances | n 3, 5, 7, 10, 15, 20 ; sortie 7 (k 3, 5, 7, 10 ; h 3, 5, 10) ; filtre 4 ; sens 3 |
| 4 | Grand mouvement | rendement du jour ≥ z écarts-types (60 séances précédentes) | après h séances | z 1-3 (5), suivre ou contrer, déclencheur hausse, baisse ou les deux, h 1, 2, 3, 5, 10, filtre 4 |
| 5 | Cassure | clôture > plus haute des n précédentes | après h séances, ou clôture < moyenne des m | n 10, 20, 40, 55, 100, 150, 250 ; sortie 7 (h 5, 10, 20, 40 ; m 10, 20, 50) ; sens 3 |
| 6 | Tendance | signe du rendement sur L séances, ou moyenne courte contre longue | chaque jour | L 5, 10, 20, 40, 60, 120, 250 ; couples 5/20, 10/50, 20/100, 50/200 ; sens 3 |
| 7 | Calendrier | jour de la semaine ; fenêtre autour du changement de mois ; veille de jour férié ; semaine de l'échéance des options (3e vendredi) et la suivante ; mois de l'année | — | 10 + 80 (début −5 à −1, longueur 1-8) + 2 + 4 + 24, achat ou vente |
| 8 | Volatilité | volatilité sur 20 séances sous (ou au-dessus de) sa médiane des 250 précédentes | chaque jour | bas ou haut, achat ou vente, filtre aucun ou 200 |
| 9 | Croisée | rendement d'un marché source sur L séances (jusqu'à la veille) ≥ z × écart-type × √L | après h séances | 40 sources × chaque marché tradable ; L 1, 2, 5, 10, 20 ; z 0, 1, 2 ; suivre ou contrer ; déclencheur hausse, baisse ou les deux ; h 1, 2, 5 |

Environ 4 000 stratégies par marché tradable pour les familles 1 à 8, et 270 par couple pour la
famille 9 : **de l'ordre de 360 000 stratégies réelles**, et autant sur chacun des 8 bruits.

### Le jumeau de bruit

- Pour chaque marché séparément, les séances de 2011-2022 sont **permutées au hasard**. Chaque séance
  garde son rendement, sa forme (plus haut et plus bas, pour l'IBS) et son prix de départ réel. Les
  dates, les échéances et le calendrier restent à leur place.
- Les liens d'un jour au suivant, entre marchés et avec le calendrier sont détruits. La tendance de
  fond, elle, reste.
- 8 graines, même programme, mêmes conditions.

### Le tri

1. **Exploration 2011-2022.** Rien après le 31 décembre 2022 n'est chargé. Une stratégie est
   **éligible** si :
   - elle a au moins 50 trades ;
   - son gain est positif sur au moins 2 des 3 périodes 2011-2014, 2015-2018 et 2019-2022 (une période
     sans données ne compte pas comme positive) ;
   - la corrélation de son gain journalier avec celui du bot (zone + RSI(2), 1 MNQ) est d'au plus 0,3
     en valeur absolue.

   Le score est le t du gain journalier net en dollars, jours sans position compris.
2. **Taux de fausses découvertes.** Pour t = 2 ; 2,5 ; 3 ; 3,5 ; 4 ; 4,5 ; 5, on calcule le nombre de
   stratégies éligibles au-dessus de t, réelles et sur bruit (moyenne des 8), et leur rapport. Pour
   chaque candidate, on note ce rapport à son propre t.
3. **10 candidates.** On prend les éligibles par t décroissant, en écartant toute stratégie corrélée à
   plus de 0,5 avec une candidate déjà prise. Même procédure sur chaque bruit (10 × 8 = 80 règles
   « placebo »).
4. **Coffre 2023 - septembre 2026, ouvert une seule fois**, pour les 10 candidates et les 80 placebos,
   sur les vraies données :
   - **retenue** : t ≥ 2,58 (Bonferroni à 5 % pour 10, unilatéral), au moins 3 années positives sur 4
     (2023, 2024, 2025, 2026) et un taux de fausses découvertes d'au plus 30 % à l'exploration ;
   - **intéressante (virtuel seulement)** : t ≥ 1 et au moins 3 années positives sur 4.

   On publie la part des 80 placebos qui passe chaque palier : c'est la chance qu'a une règle choisie
   sans information de passer.
5. **Avec le bot**, pour chaque retenue ou intéressante :
   - corrélation au coffre ;
   - challenge DayTraders Trail 50K (réussis, perdus) avec et sans la stratégie, départs 2011-2022 et
     2023-2026, même code que `protection/piste6.py` (gain de la stratégie ajouté en fin de séance) ;
   - S2F 50K avec plafond de 500 $ : argent reçu en 12 mois.

   Une retenue n'entre dans le bot que si le score Trail (réussis moins perdus) ne baisse ni sur
   2011-2022 ni sur 2023-2026. Une intéressante va au suivi en argent virtuel, quel que soit ce score.
6. Le coffre 2023-2026 a déjà servi aux tournois précédents. Il reste neuf pour ces règles, choisies
   par la machine sur 2011-2022, mais pas pour l'idée générale.
7. La machine est inscrite comme un essai dans `fonds/essais.csv`. Rien n'est ajouté ni changé après
   avoir vu les résultats.

## Fichiers

- `machine4.py` : chargement, indicateurs, les 9 familles (numba), statistiques, bruit, tri, coffre.
- `test_machine4.py` : contrôles (aucun regard vers le futur, coûts d'un trade à la main, décalage de
  la famille croisée, permutation fidèle, rendements sans saut d'échéance).
- `bot_quotidien.csv` : gain de chaque séance du bot seul (zone + RSI(2), 1 MNQ), calculé par
  `protection/piste6.py gains_du_bot`.
- Résultats : `exploration4.txt`, `candidates4.json`, `coffre4.txt`.

## Résultats (3 octobre 2026) : aucune retenue ; 2 intéressantes, autant que le hasard

`machine4.py exploration` → `exploration4.txt`, `candidates4.json` ; `machine4.py coffre` → `coffre4.txt`,
`coffre4.json` ; `avec_bot.py` → `avec_bot.txt`. Tests : `test_machine4.py`, 7 contrôles passés (aucun
regard vers le futur, trade à la main, décalage de la famille croisée, bruit fidèle, échéances, calendrier,
chaque famille prend des positions).

Précisions apparues en codant, avant tout résultat :
- **Marchés tradables.** La règle des 400 $ en garde **16** : ES, NQ, RTY, YM, ZT, ZF, 6E, 6B, 6A, 6C, 6M,
  CL, GC, HG, BTC et ETH. ZN est juste au-dessus (401 $). Il y a donc **232 736 stratégies**, et non
  ≈ 360 000.
- **Signal contraire.** Un signal de sens contraire pendant qu'une position est tenue est ignoré jusqu'à
  la sortie.
- **Gains du bot.** Ils commencent le 5 janvier 2012 (260 séances de préparation). La corrélation avec
  le bot est donc mesurée sur 2012-2022.

### Exploration 2011-2022 : le bruit fait mieux que les vraies données

| Seuil | Éligibles réelles au-dessus | Sur bruit (moyenne des 8) | Part attendue de fausses pistes |
|---|---|---|---|
| t ≥ 2 | 1 220 | 1 696 | > 100 % |
| t ≥ 2,5 | 169 | 386 | > 100 % |
| t ≥ 3 | 33 | 71 | > 100 % |
| t ≥ 3,5 | 6 | 12 | > 100 % |
| t ≥ 4 | 0 | 1,6 | — |

- La meilleure stratégie réelle (t 3,86) fait **moins bien que la meilleure de chacun des 8 bruits**
  (3,87 à 4,67).
- Aucune famille ne se détache nettement. L'IBS a un peu plus d'éligibles que sur bruit (1 899 contre
  1 431), mais sa meilleure (6C) échoue au coffre.

### Coffre 2023 - septembre 2026 (ouvert une fois)

| Candidate | t exploration | t coffre | $/an au coffre | Palier |
|---|---|---|---|---|
| 6E si les porcs (HE) ont bougé sur 5 s., suivre 1 s. | 3,86 | +0,37 | +185 | rejetée |
| 6C IBS < 0,15, 5 séances, achats et ventes | 3,55 | −0,11 | −194 | rejetée |
| **ZF : achat les 5 dernières séances du mois** | 3,51 | **+1,31** | **+1 238** | **intéressante** |
| 6C RSI(3), ventes seules | 3,36 | −0,06 | −23 | rejetée |
| **MYM contre une baisse du gaz (NG) sur 20 s.** | 3,28 | **+1,39** | **+960** | **intéressante** |
| 6E si HE a baissé sur 20 s., suivre 2 s. | 3,24 | −1,47 | −348 | rejetée |
| M6B si NKD a bougé de 2 e.-t. | 3,22 | +0,55 | +44 | rejetée |
| M6A contre le palladium sur 2 s. | 3,21 | +0,34 | +114 | rejetée |
| MHG suit 6N sur 2 s. | 3,20 | +0,02 | +38 | rejetée |
| ZT contre le fioul (HO) sur 20 s. | 3,14 | +0,81 | +993 | rejetée |

- **Aucune retenue.** Aucune n'a t ≥ 2,58 au coffre, et toutes ont plus de 100 % de fausses pistes
  attendues à l'exploration.
- **2 intéressantes sur 10.** Les 80 placebos (règles choisies sur du bruit) passent ce palier **26 % du
  temps**, soit 2,6 sur 10 sans aucune information. Le palier baissé laisse donc passer autant de
  stratégies que le hasard.

### Les deux intéressantes ajoutées au bot (`avec_bot.txt`, descriptif)

| | Trail 2011-2022 : réussis / perdus / score | Trail 2023-2026 | S2F + plafond 500 $ : reçu en 12 mois / retrait |
|---|---|---|---|
| Bot seul | 31,2 / 1,4 / +29,8 | 68,7 / 23,5 / +45,2 | +1 826 $ / 83 % |
| + ZF fin de mois (1 ZF) | 42,3 / 11,7 / +30,6 | 78,3 / 13,3 / **+65,1** | +1 768 $ / 69 % |
| + MYM contre le gaz | 46,6 / 1,2 / +45,3 | 69,9 / 25,9 / +44,0 | +2 001 $ / 80 % |

- **ZF fin de mois** fait mieux sur 2023-2026, une période que la machine n'a pas vue pour cette règle.
  Mais elle fait perdre plus de comptes sur 2011-2022 (11,7 % contre 1,4 %) et donne un retrait moins
  souvent sur S2F.
- **MYM contre le gaz** ne fait mieux que sur 2011-2022, la période où elle a été choisie.

**Pour information** (décidé après le coffre, ce n'est pas un essai : `fin_de_mois_information.txt`) :
l'achat des 5 dernières séances du mois apparaît **sur toute la courbe des taux** en 2011-2022 (ZT
t 2,37, ZF 3,51, ZN 3,08, TN 2,39, ZB 2,56, UB 2,30). C'est cohérent avec l'allongement de duration des
indices obligataires en fin de mois. Sur 2023-2026, il est positif partout mais faible (t 0,4 à 1,3),
et 2023 est négative partout. Ces marchés jouent un seul et même pari, donc ce n'est pas une
confirmation indépendante.

### Conclusion

Même avec la barre baissée, la machine ne trouve rien qui se distingue du hasard. Le seul candidat qui
ait un sens économique et qui aide le challenge sur 2023-2026 est **l'achat d'un ZF les 5 dernières
séances du mois** : 12 trades par an, environ +1 200 $ par an au coffre, non corrélé au bot. Il n'est
**pas prouvé**. Selon la règle, il va au **suivi en argent virtuel**. Comme la règle est entièrement
mécanique, ce suivi peut se faire sur les données postérieures au 25 septembre 2026 sans rien changer
au robot.
