# Le bot 3 en 1 sur DayTraders Static 50K (règles fixées le 8 octobre 2026, avant le calcul)

## Demande de l'utilisateur (8 octobre 2026)

- Il peut payer des comptes Static 50K de DayTraders (20 à 40 $ avec un code), autant qu'il faut.
- Il faut adapter le bot au Static. Le RSI(2) reste s'il marche sur ce compte et s'il rapporte. Sinon, il sort, et la
  vague 3 cherche ce qui le remplace.
- Le filtre delta reste dans la zone : l'utilisateur lui fait confiance.
- Si une règle bloque chez une firme, on regarde les autres.
- Il veut des résultats concrets, sans fausses hypothèses.

## Ce qu'on sait déjà (avant ce calcul)

- `intraday50k/budget30.txt` : le bot tel quel (1 MNQ par source, RSI(2) gardé la nuit) sur le Static réussit 58 % des
  départs de 2023-2026 en un an et en perd 27 %. Pour les départs de 2025, c'est 33 % réussis et 67 % perdus. Ce
  moteur-là ne voyait pas la nuit : seulement l'écart entre la clôture et l'ouverture.
- **Fait de prix, sans regarder aucun gain** : le NQ vaut environ 30 900 points en septembre 2026, contre 2 300 en 2011
  et 11 000 à 17 000 en 2023. Le plancher du Static est à 1 000 $ sous le départ, soit 500 points de NQ pour 1 MNQ :
  1,6 % du prix aujourd'hui, 22 % en 2011. Les départs anciens, joués au prix de l'époque, ne disent presque rien du
  risque d'aujourd'hui.
- Stop du RSI(2) et coupe-circuit : refusés sur les autres comptes (`protection/`), parce qu'ils coupent le rebond.
- Sur les comptes financés, la règle de régularité bloque les retraits ; un plafond du jour à 500 $ les débloquait
  (`protection/` piste 4), mais il n'avait pas été retenu à cause du nombre de comptes perdus.

## Les règles du compte (relevées sur des sites d'avis le 7 octobre 2026, à confirmer avant l'achat)

Sources : `research_notes/Challenge futures 50K pour bot automatisé/daytraders.md`.

**Évaluation Static 50K** :
- objectif : solde ≥ 53 750 $ (+3 750 $) à la fin d'une journée de trading ;
- plancher fixe à 49 000 $, surveillé en direct, nuit et week-end compris (positions évaluées au prix du marché) ;
- pas de limite par jour, pas de temps limite, nuit et week-end permis, robot permis (sauf haute fréquence) ;
- régularité : le meilleur jour ≤ 50 % du gain au moment de réussir ;
- au moins 2 jours à +200 $ ou plus ;
- prix compté : **30 $**.

**Compte Pro Static** (après la réussite) :
- activation : **130 $** (le prix le plus prudent des sources) ; le compte démarre à 50 000 $ la séance qui suit la
  réussite, sans position ;
- plancher fixe à 49 000 $ (« Pro Static garde la perte fixe de l'évaluation ») ;
- retrait possible à la fin d'une journée si toutes ces conditions sont réunies :
  - solde ≥ 52 600 $ ;
  - au moins 8 jours à +200 $ ou plus depuis le dernier retrait (ou depuis le début) ;
  - meilleur jour ≤ 30 % du gain depuis le dernier retrait (ou depuis le début) ;
- montant : le plus grand multiple de 500 $ qui laisse au moins 52 000 $, au plus 2 000 $ ; 100 % pour le trader ;
- descriptif : la même chose si le plancher remonte à 1 000 $ sous le solde après chaque retrait (cas pessimiste, la
  règle après un retrait n'a pas été trouvée) ;
- descriptif : la part des comptes qui passent 30 jours sans un jour à +200 $ (règle d'activité, mal connue).

**Journée de trading** : de 18 h la veille à 17 h (heure de New York). Le solde de fin de journée est pris à 17 h :
après la barre de 16 h, positions de nuit comprises.

## Le moteur (`moteur_static.py`)

- **Données** : minutes de séance du NQ, de 9 h 30 à 16 h (`intraday/`, comme `protection/`) ; barres d'une heure de la
  nuit (`nuit/donnees/`, Databento) : la barre de 16 h après chaque séance, puis les barres de 18 h à 8 h avant la
  séance suivante, du même contrat seulement. Les 30 minutes de 9 h à 9 h 30 ne sont vues que par l'ouverture de
  9 h 30. Même chose pour le S&P 500 (ES) quand le RSI(2) est joué sur MES.
- **Zone de bruit** : trades du robot (V1, `protection/robot_main.py`), entrée et sortie à la clôture de la minute,
  3 $ de frais par aller-retour et par MNQ. Filtrée par le vrai delta seulement quand il existe (avril - septembre
  2026, à titre descriptif) ; non filtrée pour le choix.
- **RSI(2)** : décisions du robot (15 h 50, prix d'ouverture de la minute), position gardée la nuit et le week-end,
  fermée avant un changement d'échéance (comme le robot). Frais : 1 $ + 1 tick par ordre et par contrat.
- **RSI(2) sur MES** : mêmes décisions (calculées sur le NQ), exécutées sur le MES à l'ouverture de la même minute,
  5 $ par point, 1 $ + 1 tick (2,25 $) par ordre. Nuit en barres d'une heure de l'ES.
- **Valeur du compte** : à chaque minute et à chaque barre d'une heure, le pire point selon la position (plus bas pour
  un achat, plus haut pour une vente). Avec deux contrats différents (zone sur MNQ, RSI(2) sur MES), on additionne
  les deux pires points (prudent).
- **Au niveau d'aujourd'hui** : pour chaque départ, tous les prix du NQ sont multipliés par 30 900 / clôture de la
  séance d'avant le départ (dernière clôture des données / ce prix, exactement), et ceux de l'ES de la même façon
  avec sa dernière clôture. Le facteur reste le même pendant tout le parcours. Les frais restent en dollars. Ce sont
  les mouvements en pourcentage d'une époque, joués au prix d'aujourd'hui. Les mêmes calculs au prix de l'époque
  sont publiés à titre descriptif.
- **Plafond du jour** (seulement sur le compte Pro, variantes « P500 ») : dès que la valeur du compte dépasse de 500 $
  le solde de la fin de journée d'avant, le bot ferme tout et ne trade plus jusqu'à 18 h. Exécution au niveau du
  plafond (à l'ouverture si le prix l'a sauté), 1 tick de glissement en plus. Le RSI(2) reprend à sa décision
  suivante si sa règle veut toujours la position.
- **Coussin** = valeur du compte − plancher, mesuré au moment de la décision (RSI(2) : ouverture de la minute de
  décision ; zone : clôture de la minute d'entrée). Une taille ou un seuil ne joue que sur une **nouvelle** entrée :
  une position ouverte n'est jamais réduite.
- Le compte Pro démarre sans position ; le RSI(2) n'y entre qu'à un nouveau signal d'achat (pas au milieu d'un trade).

## Les variantes (fixées maintenant)

Le bot ne change pas en passant du challenge au compte Pro, sauf le plafond du jour.

| Nom | Zone | RSI(2) |
|---|---|---|
| **E0** | 1 MNQ | 1 MNQ dès le début (le bot tel quel) |
| **E1** | 1 MNQ | aucun |
| **E2** | 1 MNQ | 1 MNQ si le coussin ≥ 2 000 $ à la décision d'achat |
| **E3** | 1 MNQ | 1 MNQ si le coussin ≥ 3 000 $ à la décision d'achat |
| **E4** | 1 MNQ | 1 MES dès le début |
| **E5** | 1 MNQ | 1 MES si le coussin < 3 000 $, 1 MNQ au-delà |
| **E6** | n MNQ | comme E3, n MNQ |

E6 : n = arrondi inférieur de (coussin / 2 000 $), au moins 1 et au plus 3, pour chaque nouvelle entrée de chaque source.

Chaque variante est jouée sans plafond (« P0 ») et avec le plafond de 500 $ sur le compte Pro (« P500 ») : **14 candidates**.

Pourquoi ces variantes : le plancher fixe ne bouge jamais, donc le coussin ne grandit qu'avec les gains. Les variantes
font prendre moins de risque au début (sans RSI(2), ou RSI(2) sur un contrat deux fois plus petit) et plus quand le
coussin a grandi. Aucune n'a été choisie en regardant un résultat.

## Les mesures

- **Départs** : une séance sur cinq où le RSI(2) est à plat à l'ouverture (comme les dossiers précédents). Chaque
  achat est suivi **12 mois (252 séances)** : évaluation, puis compte Pro. 24 mois à titre descriptif.
- **Argent net d'un achat** = retraits reçus dans les 12 mois − 30 $ − 130 $ si l'évaluation est réussie.
- Publié pour chaque candidate : argent net moyen, évaluations réussies et perdues, séances médianes pour réussir,
  part des achats avec au moins un retrait, **part des achats qui rapportent au moins 580 $ nets (environ 500 €)**,
  comptes Pro perdus, délai du premier retrait.

## Le choix (fixé maintenant)

- **Choix** : départs du 1er janvier 2012 au 31 décembre 2021 (suivi fini avant 2023), au niveau d'aujourd'hui. On
  retient la candidate qui a **l'argent net moyen le plus haut**.
- **Vérification** : départs du 1er janvier 2023 au dernier départ qui a 252 séances de suivi (septembre 2025), au
  niveau d'aujourd'hui. La candidate retenue est **validée** si :
  1. son argent net moyen y est positif ;
  2. il est au moins égal à celui de E0 P0 (le bot tel quel).

  Sinon, aucune variante n'est validée, et on le dit.
- **Le RSI(2) reste dans le système Static** si la meilleure variante avec RSI(2) bat E1 (sans RSI(2), même plafond)
  sur le groupe de choix **et** sur le groupe de vérification. Sinon, il sort, et la vague 3 cherche ce qui le remplace.
- **Descriptif seulement** :
  - départs de 2022 ;
  - départs de 2025 ;
  - départs d'avril à septembre 2026 avec le vrai delta ;
  - prix de l'époque ;
  - compte Pro pessimiste ;
  - 24 mois.

## Le filtre delta (descriptif, sans décision)

- Le vrai delta n'existe qu'à partir d'avril 2026. Pour les années d'avant, on reprend la simulation de
  `filtre_h1/scenario.py` : un signal corrélé au résultat de chaque trade de zone, avec la corrélation mesurée en 2026,
  20 % des trades écartés, 20 tirages. Trois scénarios : filtre aussi bon qu'en 2026, deux fois moins bon, inutile.
- Publié pour la candidate retenue et pour E0 : les mêmes mesures dans chaque scénario.
- C'est une simulation, pas un test du filtre. Le choix se fait sans filtre : si le filtre est bon, il ne peut
  qu'améliorer le système. S'il est inutile, le scénario « inutile » montre ce qu'il coûte.

## Les autres firmes (descriptif, si une règle bloque chez DayTraders)

- `intraday50k/financee.py` (Bulenox option 2, Topstep, Tradeify Growth, bot zone + RSI(2) entre deux clôtures),
  rejoué au niveau d'aujourd'hui, avec les mêmes départs de vérification. On mesure l'argent net en 12 mois de la même
  façon (retraits − coûts).

## Précisions écrites pendant le codage, avant tout résultat

- **Entrée du RSI(2)** : à chaque décision où la règle veut la position et où le bot est à plat, il entre si la
  condition de sa variante est remplie à ce moment-là (coussin, taille, instrument). Il peut donc entrer à une
  décision plus tardive du même signal, si le coussin a grandi entre-temps. C'est ce que fait déjà le moteur de
  `protection/`. Exceptions : au départ du compte Pro, et juste après un plafond du jour, le RSI(2) attend la décision
  suivante (Pro : un nouveau signal d'achat).
- **Changement d'échéance de l'ES** : il ne tombe pas toujours le même jour que celui du NQ (12 fois sur 63 depuis
  2011). Sur MES, le RSI(2) est donc aussi fermé à la décision qui précède un changement d'échéance de l'ES, et il
  n'entre pas ce jour-là.
- **Barres d'une heure** : on garde celles du même contrat que la séance (barres de 16 h et 17 h) ou que la séance
  suivante (nuit). Une heure absente ne bouge pas le compte.

## Contrôles avant d'y croire (`test_static.py`)

1. Au prix de l'époque, sans plancher, le moteur redonne le gain de la zone et du RSI(2) d'origine (+10 668,5 $ et
   +11 098,5 $ sur 2023 - septembre 2026) et le gain jour par jour de `protection/` (sans les barres de nuit).
2. Sans les barres de nuit et au prix de l'époque, l'évaluation E0 redonne les issues de `intraday50k/budget30.py`
   (Static, 1 MNQ) départ par départ.
3. Un trade du RSI(2) sur MES et un retrait du compte Pro recalculés à la main.
4. Changer les prix après une date ne change rien avant cette date (pas de regard vers le futur).
5. Un facteur de prix de 1 redonne exactement le calcul au prix de l'époque.

## Correction après la revue de code (8 octobre 2026, avant la publication des résultats)

Une revue de code indépendante (`/code-review`, niveau élevé) a relevé, après un premier calcul :
1. **Plafond et plancher dans la même barre** : le moteur prenait le plafond de +500 $ avant de regarder le plancher.
   C'était favorable aux variantes « P500 ». Corrigé dans le sens prudent : si une minute ou une heure touche les deux,
   le compte est perdu.
2. **Plafond avec deux contrats** (zone sur MNQ, RSI(2) sur MES) : le moteur additionnait les deux meilleurs points,
   qui ne sont pas forcément au même moment. Corrigé : avec deux contrats, le plafond n'est pris que si la valeur à
   l'ouverture ou à la clôture de la minute l'atteint.
3. Règle d'activité comptée au-delà de 12 mois ; nombre d'achats affiché ×20 dans les scénarios du filtre ; contrôle
   du total du RSI(2) annoncé mais pas vérifié ; code en double. Tout est corrigé.

Deux contrôles synthétiques ont été ajoutés (plafond et plancher dans la même minute ; plafond avec deux contrats). Ils
échouent avec l'ancien moteur et passent avec le nouveau. Le calcul a été refait en entier. Premier calcul, pour mémoire :
E0 P500 retenue, +898 $ par achat sur 2012-2021 et +771 $ en vérification. Après correction : +875 $ et +690 $. **La
décision ne change pas.**

## Résultats (8 octobre 2026) : `static.txt`, `lecture.txt`, `autres_firmes.txt`

Contrôles (`test_static.py`, 9 sur 9) :
- zone seule +10 668,5 $ et RSI(2) d'origine +11 098,5 $ (2023 - septembre 2026), identiques à `protection/` ;
- valeur de fin de journée juste sur les 828 séances à plat et sur les 135 séances en position ;
- évaluation identique à `budget30.py` sur les 166 départs, sans la nuit ;
- trade sur MES et retraits recalculés à la main ;
- pas de regard vers le futur ;
- facteur de prix exact ;
- plancher avant plafond.

### La décision (règles fixées avant le calcul)

| Variante (au niveau d'aujourd'hui, 12 mois après l'achat) | Choix 2012-2021 : argent net moyen par achat | Vérification 2023 - sept. 2025 | Évaluation réussie / perdue (vérification) | Achats à +580 $ nets ou plus (vérification) |
|---|---|---|---|---|
| **E0 P500 : le bot tel quel + plafond du jour de 500 $ sur le compte Pro** | **+875 $** | **+690 $** | 48 % / 52 % | 20 % |
| E0 P0 : le bot tel quel | +290 $ | +227 $ | 48 % / 52 % | 12 % |
| E1 P500 : zone seule, plafond 500 $ | +587 $ | +395 $ | 52 % / 42 % | 11 % |
| E4 P500 : RSI(2) sur MES | +751 $ | +977 $ | 63 % / 31 % | 28 % |
| E5 P500 : MES puis MNQ | +709 $ | +1 033 $ | 66 % / 31 % | 31 % |
| E2 P500 : RSI(2) dès 2 000 $ de coussin | +506 $ | +1 082 $ | 69 % / 31 % | 26 % |

- **Retenue : E0 P500, validée** (+690 $ en vérification, contre +227 $ pour le bot tel quel).
- **Le RSI(2) reste** : E0 P500 bat la zone seule (E1 P500) sur les deux périodes (+875 / +690 $ contre +587 / +395 $).
- Ce qui change dans le bot : **rien pendant l'évaluation**. Sur le compte Pro, dès que la journée gagne 500 $, tout
  est fermé jusqu'à 18 h. C'est la règle des 30 % qui bloque les retraits sans ce plafond, comme dans `protection/`
  piste 4.
- Sur 2023 - 2025, les variantes qui prennent moins de risque au début (E2, E4, E5) ont fait mieux qu'E0 P500. Elles
  avaient fait moins bien sur 2012-2021, et la règle choisit sur 2012-2021 : elles ne sont pas retenues.

### Ce qu'il faut savoir avant d'y croire (descriptif)

- **La médiane est de −30 $** dans toutes les variantes : la plupart des achats perdent leur prix (évaluation perdue
  ou pas encore réussie). La moyenne positive vient d'une minorité d'achats qui paient beaucoup : pour E0 P500, 20 à
  25 % des achats rapportent au moins 580 $ nets en 12 mois. Parmi les achats qui retirent, la médiane reçue est de
  4 000 $ (2012-2021) et 2 500 $ (vérification), de 500 $ à 6 000 $ environ.
- **Ça dépend beaucoup de l'année** (`lecture.txt`, E0 P500, par année d'achat) :
  - années où presque tout est perdu : 2014 (+7 $), 2015 et 2016 (−36 $, 87 à 95 % d'évaluations perdues),
    **2025 (−60 $ : 77 % perdues, aucun retrait)** ;
  - bonnes années : +1 300 à +2 400 $ par achat (2013, 2018, 2021, 2023).
- **Avril - septembre 2026 avec le vrai delta** : 15 % d'évaluations réussies, 38 % perdues, 47 % en cours au
  25 septembre. Pas un bon début.
- **Programme « un Static par mois pendant 12 mois »** (360 $ d'achats) :
  - commencé en 2012-2020 : total net médian +10 055 $, mais 23 % des programmes perdent de l'argent ;
  - commencé en 2023 - septembre 2024 : médiane +8 230 $, 10 % perdants.

  Les comptes achetés le même mois font les mêmes trades : ils réussissent ou sautent ensemble.
- **Compte Pro pessimiste** (plancher qui remonte après un retrait) : E0 P500 tombe à +341 $ / +295 $. **La règle du
  plancher après un retrait est donc à demander au support de DayTraders avant d'acheter.**
- **Prix de l'époque** (le NQ valait beaucoup moins) : E0 P500 fait +24 $ / +196 $. Les dollars gagnés suivent le prix
  du NQ.
- **Filtre delta simulé**, E0 P500 :

  | Scénario | Choix 2012-2021 | Vérification |
  |---|---|---|
  | aussi bon qu'en 2026 | +1 402 $ | +1 206 $ |
  | deux fois moins bon | +1 027 $ | +831 $ |
  | inutile | +647 $ | +472 $ |

  Le filtre ne peut être jugé que sur des données réelles : c'est le rôle de la démo.
- **24 mois après l'achat** : E0 P500 fait +2 882 $ (2012-2021) et +2 698 $ par achat (2023 - 2024, 78 achats).
- **Règle d'activité** : environ 14 % des achats ont un compte Pro qui passe 21 séances sans un jour à +200 $. Si
  DayTraders applique strictement cette règle, ces comptes seraient en danger.

### Les autres firmes, au même niveau de prix (`autres_firmes.txt`, mêmes 124 départs de vérification)

| Compte (12 mois) | Argent net moyen par achat | Achats à +580 $ nets ou plus |
|---|---|---|
| DayTraders Static, E0 P500 | +690 $ | 20 % |
| Topstep, zone seule | +594 $ | 23 % |
| Topstep, zone + RSI(2) entre deux clôtures | +162 $ | 17 % |
| Tradeify Growth, zone seule | +178 $ | 11 % |
| Bulenox option 2, zone + RSI(2) | −47 $ | 23 % |

Topstep avec la zone seule arrive près du Static, mais il coûte 49 $ par mois plus 149 $ d'activation, contre 30 $
une fois plus 130 $ d'activation. Le Static reste le compte le moins cher pour ce bot.

## Combien par mois ? (demande du 8 octobre 2026 : sans les frais d'activation ; descriptif, écrit après les résultats)

`par_mois.py` → `par_mois.txt`. Système retenu (E0 P500), au niveau d'aujourd'hui, **sans les 130 $ d'activation**.
Un Static acheté le premier jour possible de chaque mois depuis 2012, chaque compte suivi 24 mois au plus.

Contrôles :
- la somme des retraits datés redonne le total du moteur ;
- les retraits relevés séance par séance sont vérifiés à la main (`test_static.py`) ;
- `static.txt` est inchangé.

**Un compte Pro qui tourne** rapporte en moyenne **518 $ par mois** :

| Scénario | Retrait moyen par mois |
|---|---|
| sans filtre | 518 $ |
| filtre aussi bon qu'en 2026 (simulé) | 616 $ |
| filtre inutile (simulé) | 430 $ |

- La médiane par compte est de 533 $ par mois ; un compte sur deux est entre 178 $ et 645 $.
- 74 % des retraits sont de 2 000 $, le maximum par demande.
- 39 % de ces comptes sont perdus dans les 24 mois.

**Un Static acheté** (retraits moyens, sans filtre ; achats 2012-2021 / 2023 - sept. 2024) :

| Période après l'achat | Retrait moyen par mois |
|---|---|
| mois 1 à 3 | 6 / 8 $ |
| mois 4 à 6 | 74 / 91 $ |
| mois 7 à 12 | 138 / 125 $ |
| mois 13 à 24 | 163 / 104 $ |

Au total, environ 1 050 $ la première année et 2 300 à 3 000 $ sur deux ans.

**Programme « un Static acheté chaque mois »** (30 $ par mois) :

- **Montée en charge** : environ 250 $ par mois au 6e mois, 1 050 $ au 12e, 2 300 à 3 000 $ au 24e (en moyenne).
- **Une fois lancé** (2014 - 2026, sans filtre) :
  - moyenne **2 892 $ par mois**, mais **la moitié des mois à 0 $** ;
  - la plus longue série sans rien : **23 mois** (mi-2015 à mi-2017) ;
  - 5,7 comptes Pro en même temps en moyenne, 11 au plus.
- **Par année** (moyenne par mois, sans filtre / filtre simulé aussi bon qu'en 2026 / filtre inutile) :

  | Année | Sans filtre | Filtre aussi bon qu'en 2026 | Filtre inutile |
  |---|---|---|---|
  | 2016 | 0 $ | 0 $ | 0 $ |
  | 2017 | 83 $ | 496 $ | 121 $ |
  | 2018 | 8 083 $ | 7 438 $ | 3 408 $ |
  | 2022 | 4 583 $ | 6 846 $ | 2 992 $ |
  | 2023 | 5 417 $ | 8 625 $ | 3 033 $ |
  | 2024 | 3 417 $ | 5 804 $ | 2 421 $ |
  | 2025 | 1 417 $ | 2 925 $ | 1 412 $ |
  | 2026 (9 mois) | 333 $ | 1 411 $ | 294 $ |

- **Filtre simulé aussi bon qu'en 2026** :
  - moyenne 4 285 $ par mois, 20 % de mois à 0 $ ;
  - jusqu'à 18 comptes Pro en même temps, au-dessus de la limite de 15 de DayTraders.
- **Filtre inutile** : moyenne 1 921 $ par mois.
- Ces chiffres supposent que le plancher du compte Pro reste à 49 000 $ après un retrait. C'est la question à poser au
  support : dans le cas pessimiste, l'argent reçu est à peu près divisé par deux (section « Ce qu'il faut savoir »).

## Un ou plusieurs Static (demande du 9 octobre 2026 ; descriptif)

`plusieurs.py` → `plusieurs.txt`. Retraits reçus dans les 12 mois qui suivent chaque achat, système retenu, niveau
d'aujourd'hui, activation ignorée. Contrôle : un seul Static acheté en 2012-2021 redonne les 955 $ moyens de
`static.txt`.

- **Plusieurs Static achetés le même jour** font les mêmes trades : c'est N fois le résultat d'un seul. On gagne tout
  ou rien : 67 à 75 % de chances de ne rien toucher, quel que soit leur nombre.
- **Les étaler dans le temps** garde la même moyenne, mais réduit beaucoup le risque de tout rater. Achats 2023-2024,
  sans filtre :

  | Achat | Rien touché | Médiane | Moyenne |
  |---|---|---|---|
  | 5 Static, un mois d'écart | 26 % | 3 000 $ | 4 719 $ |
  | 10 Static, un mois d'écart | 14 % | 7 000 $ | 6 983 $ |

## Le S2F 50K, et ce que le bot peut verser au plus (demande du 9 octobre 2026 ; descriptif)

`s2f.py` → `s2f.txt`. Le moteur sait maintenant jouer le S2F 50K (`regle = 2`, règles relevées le 7 octobre 2026,
`research_notes/.../daytraders.md`, à confirmer) :
- financé tout de suite, sans activation ;
- plancher = plus haut solde de fin de journée − 2 500 $, bloqué à 50 000 $, surveillé en direct ;
- limite du jour douce de 1 250 $ : tout est fermé jusqu'à 18 h, le compte continue ;
- retrait après 10 jours à +200 $, avec :
  - un gain du cycle d'au moins 3 500 $, puis 3 000 $, puis 2 500 $ ;
  - un meilleur jour ≤ 20 % du gain du cycle ;
  - au plus 2 000 $, en gardant 51 000 $.

**Ordre limite du jour / plancher.** Les deux sont du même côté. En descendant, le prix touche d'abord le plus haut
des deux : le compte n'est perdu que si le prix saute directement sous le plancher. Contrôle à la main ajouté dans
`test_static.py` (10 contrôles sur 10). `static.txt` est inchangé.

**Le bot seul**, sans compte, gain sur un mois au niveau d'aujourd'hui :

| Période | Moyenne | Médiane | Mois perdants |
|---|---|---|---|
| 2023-2026 | +883 $ | +754 $ | 28 % |
| 2025-2026 | +659 $ | +251 $ | 39 % |
| 2023-2026, filtre simulé aussi bon qu'en 2026 | +1 130 $ | | |

**C'est le maximum qu'un compte peut verser**, avant les règles des firmes.

**Un S2F 50K** (bot + plafond de 500 $, achats 2023 - sept. 2025, 12 mois) :
- 45 % des comptes font au moins un retrait ;
- 1 419 $ reçus en moyenne, médiane 0 $ ;
- 75 % des comptes perdus dans l'année ;
- argent net moyen +849 $ au prix catalogue de 570 $, +1 077 $ à 342 $.

Ailleurs :
- filtre simulé aussi bon qu'en 2026 : 2 497 $ reçus, net +1 927 $ ;
- achats de 2025 : 114 $ reçus, net −456 $.

Les autres variantes (zone seule, RSI(2) sur MES…) sont dans `s2f.txt`, à titre descriptif. Une variante qui
ferait mieux devrait être testée avec des règles fixées d'avance avant d'être adoptée.
