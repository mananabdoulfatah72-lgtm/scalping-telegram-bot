# Vague 4 : remplacer le RSI(2) sur les challenges qui ferment chaque soir (règles fixées le 9 octobre 2026, avant le calcul)

## Pourquoi

Demande de l'utilisateur (9 octobre 2026) :
- garder le RSI(2) seulement sur un challenge 50K pas cher où il tient bien le mois ;
- sinon, le remplacer par une autre source qui s'ajoute à la zone seule, filtre delta compris si possible.

Ce qu'on sait déjà (au niveau d'aujourd'hui, achats 2023 - sept. 2025, argent net par achat en 12 mois) :
- **DayTraders Static** : zone + RSI(2) +690 $, zone seule +395 $. Le RSI(2) aide : on le garde (`static50k/`).
- **Topstep** : zone seule +594 $, zone + RSI(2) entre deux clôtures +162 $.
- **Tradeify Growth** : zone seule +178 $, zone + RSI(2) +43 $.

Sur ces deux comptes, qui obligent à tout fermer chaque soir, le RSI(2) gêne : c'est là qu'il faut un remplaçant.
Bulenox n'est pas étudié : il perd de l'argent avec ou sans RSI(2).

## Les comptes

Topstep 50K et Tradeify Growth 50K, challenge puis compte financé. Les règles, les prix et les retraits sont
exactement ceux de `intraday50k/` (`comptes.py`, `financee.py`), relevés le 8 octobre 2026 :
- tout est fermé à la dernière minute de la séance ;
- une position peut être prise le soir, à partir de 18 h, pour la journée de trading suivante.

## La base

La zone de bruit seule, 1 MNQ, au niveau d'aujourd'hui (prix multipliés comme dans `static50k/`). Elle est non filtrée
pour le choix ; le filtre delta simulé de `static50k/` est montré à titre descriptif.

## Partie A : le RSI(2) adapté à ces comptes (signaux du robot inchangés)

| Nom | Ce qui change |
|---|---|
| **A1** | entre deux clôtures, comme `intraday50k/`, mais sur **1 MES** au lieu de 1 MNQ (signaux calculés sur le NQ, prix de l'ES) |
| **A2** | **de nuit seulement** : achat à la barre de 18 h, vente à l'ouverture de 9 h 30 ; 1 MNQ |
| **A3** | de nuit seulement, sur 1 MES |

- Achat et vente comme dans `intraday50k/` : ouverture de la barre de 18 h (ou de la première barre de la nuit),
  même contrat seulement. A1 : vente à la décision de 15 h 50 ou à la dernière minute. A2 et A3 : vente à l'ouverture
  de 9 h 30.
- Frais : 1 $ + 1 tick par ordre (MNQ 1,50 $ ; MES 2,25 $). Nuit de l'ES en barres d'une heure, comme pour le NQ.
- **À savoir** : A2 et A3 viennent d'un résultat déjà vu. Dans `intraday50k/`, le RSI(2) entre deux clôtures gagnait
  tout la nuit et perdait en séance. Une règle plus stricte leur est donc appliquée (ci-dessous).

## Partie B : de nouvelles sources, avec de nouvelles données

Données nouvelles pour le projet : minutes des 10 plus grosses valeurs du Nasdaq 100 (AAPL, MSFT, NVDA, AMZN, META,
GOOGL, AVGO, TSLA, COST, NFLX), Alpaca (flux SIP, gratuit), 2016 - septembre 2026, de 9 h 30 à 16 h. La liste est fixe :
- elle connaît la suite (biais du survivant) ;
- les règles ci-dessous ne regardent que le **sens** du mouvement de chaque valeur dans la journée, pas son
  rendement à long terme.

| Nom | Règle (NQ, 1 MNQ, sortie à 15 h 55) |
|---|---|
| **B1** | Largeur à 10 h : si au moins 9 des 10 valeurs sont au-dessus de leur ouverture de 9 h 30, achat ; si au plus 1, vente |
| **B2** | La même chose à 11 h |
| **B3** | Hausse étroite à 10 h 30 : si le NQ est au-dessus de son ouverture mais 3 valeurs ou moins le sont, vente ; s'il est dessous mais 7 valeurs ou plus sont au-dessus, achat |

- Entrée à la clôture de la minute de décision.
- Frais : 1,5 point de NQ par aller-retour (comme la zone).
- **Tri**, comme `sessions24/` :
  - exploration 2016-2022 ;
  - la source survit si t ≥ 2 et si son t dépasse 95 % de 1 000 tirages au hasard du sens de chaque trade ;
  - coffre 2023 - septembre 2026 ouvert une fois pour les survivantes : t ≥ seuil de Bonferroni et positif 3 années
    sur 4.
- Une survivante est ensuite ajoutée à la zone sur les deux comptes, avec la règle de la partie A.

- **Précisions écrites avant les données** :
  - pas de trade un jour de clôture anticipée : la sortie de 15 h 55 n'existe pas ;
  - la largeur est comptée parmi les valeurs connues ce jour-là, à condition d'en avoir au moins 8 sur 10 ;
  - les seuils (9 sur 10, 1 sur 10, 3 et 7) s'appliquent à la part, ramenée à 10.

## Le jugement (fixé maintenant)

Pour chaque compte et chaque candidate :
- **mesure** : argent net par achat en 12 mois (retraits − abonnements − activation), au niveau d'aujourd'hui,
  départs une séance sur cinq ;
- **périodes** :
  - choix 2012-2021 (partie B : 2016-2021) ;
  - vérification 2023 - septembre 2025.

Une candidate **remplace le RSI(2)** sur un compte si son argent net dépasse celui de la zone seule :
- d'au moins 100 $ sur la période de choix **et** au moins égal sur la vérification ;
- pour A2 et A3 (idée venue d'un résultat déjà vu) : d'au moins 100 $ sur les **deux** périodes.

Si plusieurs candidates passent, on garde la meilleure de la période de choix. Si aucune ne passe, le système de
ces comptes reste **la zone seule (+ filtre)**.

Publié dans tous les cas, à titre descriptif :
- les achats de 2025 ;
- les retraits par mois d'un compte financé en vie ;
- le filtre delta simulé.

## Contrôles avant d'y croire (`test_vague4.py`)

1. Sans RSI(2) et avec le RSI(2) entre deux clôtures sur MNQ, le nouveau moteur redonne exactement les issues de
   `intraday50k/financee.py` (même départ, même compte).
2. Un trade de nuit seulement (A2) et un trade sur MES (A1) recalculés à la main.
3. Partie B : la décision de la largeur recalculée à la main un jour donné ; pas de regard vers le futur.

## Résultats (9 octobre 2026) : `partie_a.txt`, `partie_b.txt`

Contrôles (`test_vague4.py`, 4 sur 4) :
- le nouveau moteur redonne `financee.py` sur 248 parcours ;
- un trade de nuit seulement et un trade sur MES sont recalculés à la main ;
- la nuit de l'ES suit la même règle que celle du NQ ;
- la largeur d'un jour est recalculée à la main, sans regard vers le futur.

Une revue de code indépendante a demandé des corrections, toutes faites avant ces résultats :
- la limite du jour suit la position nette, comme `financee.py` ;
- le tableau des retraits par mois a été ajouté ;
- les contrôles de la partie B ont été ajoutés.

Les chiffres de la partie A sont inchangés par ces corrections.

### Partie A : un RSI(2) plus petit et de nuit seulement (12 mois après l'achat, niveau d'aujourd'hui)

| Compte | Bot | Argent net moyen : choix 2012-2021 | Vérification 2023 - sept. 2025 | Challenge réussi (vérif.) | Au moins un retrait (vérif.) |
|---|---|---|---|---|---|
| Topstep | zone seule | +638 $ | +594 $ | 55 % | 43 % |
| Topstep | zone + RSI(2) entre deux clôtures MNQ | +299 $ | +162 $ | 48 % | 25 % |
| Topstep | A1 : RSI(2) entre deux clôtures MES | +531 $ | +563 $ | 61 % | 41 % |
| Topstep | A2 : RSI(2) de nuit seulement MNQ | +400 $ | +941 $ | 52 % | 34 % |
| **Topstep** | **A3 : RSI(2) de nuit seulement MES** | **+830 $** | **+803 $** | **65 %** | **52 %** |
| Tradeify Growth | zone seule | +78 $ | +178 $ | 55 % | 19 % |
| Tradeify Growth | A3 | +340 $ | +259 $ | 65 % | 35 % |

**Décision (règles fixées avant le calcul)** :
- **Topstep : A3 remplace le RSI(2)**. Il bat la zone seule de plus de 100 $ sur les deux périodes, ce qu'exigeait la
  règle stricte (+192 $ et +209 $).
- **Tradeify Growth : la zone seule reste**. A3 fait mieux sur le choix (+262 $), mais seulement de +81 $ en
  vérification, sous les 100 $ demandés.

À savoir :
- **A3 seul**, sans compte, au niveau d'aujourd'hui :
  - environ +128 $ par mois sur 2023-2026, avec 22 % de mois perdants ;
  - son pire mois : −732 $. Le RSI(2) sur MNQ entre deux clôtures descendait à −2 847 $.

  Il rapporte peu, mais il est régulier : c'est pour ça qu'il ne gêne pas les règles de Topstep.
- **Achats de 2025** : rien ne marche (−129 à −141 $ par achat).
- **Compte financé en vie** : environ 400 $ de retraits par mois en moyenne chez Topstep. Mais la plupart des comptes
  financés sont perdus dans l'année : leur limite suit le solde, et les retraits la rapprochent.
- **Filtre delta simulé, Topstep, vérification** :

  | Scénario | Zone + A3 | Zone seule | Challenges réussis (zone + A3) | Au moins un retrait (zone + A3) | Retraits par mois en vie (zone + A3) |
  |---|---|---|---|---|---|
  | filtre aussi bon qu'en 2026 | +2 397 $ (médiane +2 005 $) | +1 540 $ | 79 % | 75 % | 581 $ |
  | filtre inutile | +804 $ | +648 $ | | | |

### Partie B : largeur des grandes valeurs (exploration 2016-2022) : aucune survivante

| Source | Trades | t | Bat le hasard | Verdict |
|---|---|---|---|---|
| B1 largeur à 10 h | 408 | +0,79 | 87,8 % | éliminée |
| B2 largeur à 11 h | 475 | −0,13 | 58,1 % | éliminée |
| B3 hausse étroite à 10 h 30 | 66 | −0,75 | 30,7 % | éliminée |

Le coffre n'est pas ouvert. La largeur des 10 plus grosses valeurs n'apporte rien de plus que le mouvement du NQ.

### Ce que ça veut dire pour le bot

- **Topstep** : la zone (+ filtre), plus le RSI(2) **de nuit seulement sur 1 MES** :
  - achat à 18 h si la règle le veut ;
  - vente à l'ouverture de 9 h 30.

  C'est à ajouter au bot. Pour l'instant, le bot ne sait faire que le RSI(2) sur MNQ, gardé la nuit.
- **Tradeify** : la zone (+ filtre) seule.
- **DayTraders Static** : le bot tel quel (zone + filtre + RSI(2)), plus le plafond de 500 $ sur le compte Pro.
