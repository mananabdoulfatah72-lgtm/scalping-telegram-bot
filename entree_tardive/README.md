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

## Résultats (20 octobre 2026) : `resultats_15ans.txt`, `resultats_delta.txt`, `resultats_challenge.txt`, `decision.txt`

**Vérifications avant de lire les chiffres :**
- H1 sans delta sur 15 ans donne exactement les trades de `zone/robot.py` : 3 572 trades, +10 721,25 points, aucun écart.
- Sur P1, H1, R et la zone sans filtre retrouvent `relance/resultats.txt` : 79 trades et +1 776,8 points, 83 et +1 860,5,
  99 et +982,2. Sur P2, les trois chiffres sont exacts avec les barres du robot du 17 octobre. Le 20 octobre, le robot a
  retéléchargé la séance du 16 octobre, d'où R à +657,0 au lieu de +657,8 et la zone sans filtre à +669,5 au lieu de
  +668,0.
- Une deuxième version du banc, écrite séparément, donne les mêmes trades pour chaque variante et chaque période : mêmes
  minutes, mêmes prix, mêmes points.
- Avant d'y brancher ces trades, le moteur de la vague 13 redonne exactement `vague13.json`.

**1. 15 ans, sans filtre**

| Variante | Trades | Points | t 2011-2022 | t 2023-2026 | Séances à −125 points (1 000 $ en 4 MNQ) |
|---|---|---|---|---|---|
| **H1 (le bot, relance décochée)** | 3 572 | +10 721 | **+2,12** | **+1,86** | 130 |
| E1, entrée à la cassure | 5 525 | +3 037 | +0,22 | +0,65 | 182 |
| E2, tout à la minute | 13 711 | −9 549 | −4,68 | +0,52 | 107 |
| S1, sortie à la minute | 5 188 | +6 093 | +0,82 | +1,57 | 59 |
| L1, pas de poursuite | 3 090 | +7 619 | +1,66 | +1,47 | 96 |

**2. Vrai delta**

| Variante | P1 : trades | P1 : points | P1 : pire baisse | P2 : points |
|---|---|---|---|---|
| **H1** | 79 | **+1 776,8** | 760,2 | +220,2 |
| E1 | 110 | +935,2 | 627,8 | +112,5 |
| E2 | 256 | +449,0 | 1 092,8 | +469,2 |
| S1 | 109 | +495,5 | 692,0 | +567,2 |
| L1 | 71 | +853,5 | 526,0 | +220,2 |
| R (information) | 83 | +1 860,5 | 760,2 | +657,0 |
| RL (information) | 83 | +1 860,5 | 760,2 | +664,2 |

**3. Challenge depuis 0 avec 16 séances** (chaque séance de 2012 à 2026 comme premier jour, sans filtre)

| Variante | Validé | Perdu | Expiré | Validé (départs 2023-2026) | Séances coupées par la limite du jour |
|---|---|---|---|---|---|
| **H1** | **44,9 %** | 38,7 % | 16,4 % | 46,5 % | 11,1 % |
| E1 | 44,4 % | 44,7 % | 11,0 % | 47,9 % | 13,3 % |
| E2 | 38,4 % | 47,9 % | 13,7 % | 40,6 % | 9,2 % |
| S1 | 41,0 % | 37,1 % | 21,9 % | 41,8 % | 7,1 % |
| L1 | 40,3 % | 34,0 % | 25,7 % | 41,8 % | 9,1 % |

**Décision fixée à l'avance : aucune variante ne passe** (aucune ne remplit même le critère 1, le 2 ou le 3). Le bot reste
H1 : la zone telle qu'elle est, relance du filtre delta décochée.

**Ce qu'il faut retenir :**
- **Entrer dès la cassure (E1) fait prendre beaucoup plus de fausses cassures.** Le gain s'effondre (t +0,22 et +0,65),
  et les journées à −1 000 $ sont plus nombreuses (182 contre 130). Tout décider à la minute (E2) est pire encore : la
  moitié des trades durent moins de 4 minutes et paient les frais.
- **En moyenne, une entrée « tardive » n'est pas une mauvaise entrée.** Les 482 cassures que L1 refuse (prix déjà à plus
  d'une marge de la limite) auraient rapporté +6,44 points en moyenne, contre +2,47 pour celles qu'il garde. Les fortes
  cassures sont les meilleurs trades de la zone. Le 20 octobre est un cas défavorable, pas la règle.
- **Sortir à la minute (S1) divise par deux les journées à −1 000 $** (59 contre 130 sur 15 ans), mais coupe trop tôt
  les bons trades : il valide moins souvent le challenge (41,0 % contre 44,9 %).
- **En partant de 0 avec 16 séances, le bot actuel (H1) reste celui qui valide le plus souvent** : environ 45 % de
  validés, 39 % de perdus, 16 % d'expirés.
- **La relance** : 5 relances en 136 séances avec le vrai delta, trop peu pour juger. En challenge sur P1 (information,
  départs qui se chevauchent), elle valide 39,4 % contre 41,7 % pour H1. Même la relance du 16 octobre, qui a motivé
  son adoption, est descendue à −130,75 points avant de gagner : en 4 MNQ, la limite de 1 000 $ l'aurait coupée.

**Limites :**
- L'étude est lancée après une mauvaise journée. Ses règles ont été fixées avant tout calcul.
- Sur 15 ans, la zone n'est pas filtrée : il n'existe pas de vrai delta avant avril 2026.
- Pour le challenge :
  - les prix sont ramenés au niveau d'aujourd'hui (facteur de la vague 4) ;
  - l'arrêt à +3 050 $ suppose un ordre limite rempli dès que la minute touche ce niveau ;
  - les départs se chevauchent, donc un écart de 1 ou 2 points ne veut rien dire.
- La séance du 20 octobre n'est pas encore dans les données.

**Relancer :**

```
git worktree add ../recherche origin/claude/keen-babbage-r686cl   # donnees de la branche de recherche (ou variable KB)
python3 entree_tardive/etude.py       # mesures 1 et 2, environ 15 s
python3 entree_tardive/challenge.py   # mesure 3, numba et scipy requis, environ 25 s
```
