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

## Contrôles avant d'y croire (`test_static.py`)

1. Au prix de l'époque, sans plancher, le moteur redonne le gain de la zone et du RSI(2) d'origine (+10 668,5 $ et
   +11 098,5 $ sur 2023 - septembre 2026) et le gain jour par jour de `protection/` (sans les barres de nuit).
2. Sans les barres de nuit et au prix de l'époque, l'évaluation E0 redonne les issues de `intraday50k/budget30.py`
   (Static, 1 MNQ) départ par départ.
3. Un trade du RSI(2) sur MES et un retrait du compte Pro recalculés à la main.
4. Changer les prix après une date ne change rien avant cette date (pas de regard vers le futur).
5. Un facteur de prix de 1 redonne exactement le calcul au prix de l'époque.
