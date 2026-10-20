# Entrées en retard de la zone : remèdes testés (règles fixées le 20 octobre 2026, avant tout calcul)

## Demande de l'utilisateur (20 octobre 2026)

Le bot 3 en 1 (challenge Bulenox 50K, 4 MNQ par source, limite de perte du jour à 1 000 $) a acheté alors que le prix
avait déjà fait son mouvement. Le prix a été rejeté au VAH et le bot a fini la journée à −1 002 $, coupé par sa limite de
perte. Le compte est revenu à 0 de gain, avec moins de 17 séances pour valider le challenge.

L'utilisateur décoche la relance du filtre delta (activée le 19 octobre, `relance/README.md` sur la branche de
recherche). Il demande :
- que le bot ne rate plus les gros mouvements, sauf quand le delta est contre ;
- que le bot n'entre plus jamais en retard sur une tendance.

## Ce que fait le bot aujourd'hui (`bot3en1/Bot3en1.Core/Moteur.cs`, branche `claude/keen-babbage-r686cl`)

- Il lit chaque transaction du NQ et ferme une barre chaque minute. La limite de perte et l'objectif sont vérifiés
  deux fois par seconde.
- La zone ne décide qu'aux contrôles de 10 h, 10 h 30, … 15 h 30 (New York), plus la sortie de 16 h :
  - **entrée** : achat si la clôture de la minute du contrôle dépasse max(ouverture, veille) × (1 + σ), vente sous
    min(ouverture, veille) × (1 − σ). σ est le mouvement moyen depuis l'ouverture à cette minute sur les 14 dernières
    séances complètes ;
  - **filtre H1** : l'entrée n'est prise que si le delta des 30 minutes qui finissent à cette minute va dans son sens.
    Sinon, le trade écarté reste « virtuel » jusqu'à sa sortie, et aucun nouveau signal n'est pris pendant ce temps ;
  - **sortie** : à un contrôle, quand le prix repasse sous max(limite haute, VWAP) pour un achat (au-dessus de
    min(limite basse, VWAP) pour une vente), et au plus tard à 16 h.
- Entre deux contrôles, seule la limite de perte du jour protège une position. En 4 MNQ, 125 points du NQ contre la
  position coûtent 1 000 $.
- Déjà mesuré (`zone_optimisation/`, 1er octobre 2026) : avec des contrôles toutes les 15 minutes au lieu de 30, entrées
  et sorties comprises, la zone tombait de t 2,00 à t 0,98 sur 2023-2026.

## Variantes (fixées maintenant)

Toutes partent de la zone V1 du robot (`zone/robot.py` `zone_de_bruit`), avec les mêmes frais (1,5 point par
aller-retour). Une seule chose change à chaque fois.

| Nom | Ce qui change |
|---|---|
| **H1** | rien : le bot avec la relance décochée (référence). Sans delta (15 ans), c'est V1 |
| **E1, entrée à la cassure** | la cassure est cherchée à **chaque fin de minute** de 10 h à 15 h 30 (σ de cette minute), au lieu des seuls contrôles. Filtre H1 sur les 30 minutes qui finissent à la minute de la cassure. Sorties inchangées (contrôles de 30 minutes et 16 h) |
| **E2, tout à la minute** | E1, et la sortie est aussi vérifiée à chaque fin de minute (ligne de sortie de cette minute). Pour ne pas entrer et ressortir aussitôt, l'entrée demande un prix au-delà de la ligne de sortie : au-dessus de max(limite haute, VWAP) pour un achat, sous min(limite basse, VWAP) pour une vente |
| **S1, sortie à la minute** | entrées inchangées (contrôles), sortie vérifiée à chaque fin de minute à partir de la minute qui suit l'entrée |
| **L1, pas de poursuite** | entrées aux contrôles, mais **seulement si le prix n'a pas dépassé la limite de plus d'une fois la marge** (dépassement ≤ 1, c'est-à-dire \|prix − limite\| ≤ référence × σ). Au-delà, le trade n'est pas pris et reste virtuel jusqu'à sa sortie, comme un trade écarté |

Dans toutes les variantes : une seule position à la fois, exécution au prix de clôture de la minute qui décide, pas de
nouvelle entrée pendant qu'un trade écarté (ou non pris) est encore virtuel, plus de zone après 16 h.

**Pour information seulement (aucune décision) :**
- **R** : la relance (bot du 19 octobre), sur les périodes avec le vrai delta ;
- **RL** : la relance, seulement si le dépassement est ≤ 1 au moment de la relance.

## Données

- **15 ans, prix seuls** : barres d'une minute du NQ de la recherche (`intraday/donnees/nasdaq100_1min.csv.gz`,
  2011 - 25 septembre 2026), complétées par celles du robot (`zone/robot/nq_1min.csv.gz` sur main). Sans delta : la zone
  n'est pas filtrée.
- **P1, vrai delta Databento** : 1er avril - 1er octobre 2026 (`orderflow/donnees/nq_secondes_*.csv.gz`, regroupé par
  minute), barres du robot. Mêmes données que `relance/`.
- **P2, vrai delta Rithmic** : 2 - 16 octobre 2026 (`filtre_h1/donnees_rithmic/transactions_NQZ6_rithmic.csv`), barres du
  robot.
- La séance du 20 octobre n'est pas dans les données au moment de ces règles.

## Mesures

1. **15 ans, sans filtre** (H1 = V1, E1, E2, S1, L1) : trades, points, gagnants, t des gains quotidiens nets, sur
   2011-2022 et sur 2023-2026 séparément ; dépassement moyen à l'entrée ; nombre de séances où la perte du jour (réalisée
   + latente, aux plus bas et plus hauts des minutes) atteint 125 points (1 000 $ en 4 MNQ) et 83 points (1 000 $ en
   6 MNQ).
2. **P1 et P2, avec le vrai delta** (H1, E1, E2, S1, L1, et R, RL pour information) : trades, points, pire baisse
   (pertes enchaînées, en points), pire séance.
3. **Challenge depuis 0 avec 16 séances** (la situation de l'utilisateur) : moteur de la vague 13 (`vague13/moteur13.py`,
   version D retenue), sans le RSI(2) de nuit, avec les trades de chaque variante :
   - Bulenox Legacy 50K option 2 : objectif +3 000 $ avec arrêt à +3 050 $, perte maximale 2 500 $ comptée en fin de
     journée, limite de perte du jour du bot 1 000 $, 4 MNQ, 6 MNQ les 5 dernières séances, pas de zone les jours de la
     Fed ;
   - départ à 50 000 $, plus haut de fin de journée à 50 000 $ ;
   - chaque séance de 2012 à 2026 comme premier jour, sans filtre ; résultats aussi pour les départs de 2023 à 2026 ;
   - pour information : P1 avec le vrai delta (peu de départs indépendants).

## Décision (fixée maintenant)

Une variante remplace H1 dans le bot seulement si elle remplit **tout** ce qui suit :
1. 15 ans sans filtre : t des gains quotidiens **supérieur à celui de V1** sur 2011-2022 **et** sur 2023-2026 ;
2. challenge depuis 0 en 16 séances, départs 2012-2026 : **au moins 2 points de validés de plus** que V1, et pas moins que
   V1 sur les départs 2023-2026 ;
3. P1 : au moins autant de points que H1 ;
4. P2 : pas moins bien que H1.

Si plusieurs passent : celle qui valide le plus souvent sur les départs 2012-2026. Si aucune ne passe, le bot reste H1
(relance décochée), et les résultats sont publiés quand même.

**À savoir avant d'y croire :** cette étude est lancée après une mauvaise journée. Une règle qui l'aurait évitée n'est pas
une preuve. C'est pour cela que la décision repose sur 15 ans et sur le challenge, et non sur la journée du 20 octobre.
