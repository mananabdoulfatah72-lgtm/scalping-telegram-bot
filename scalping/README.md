# Machine scalping : une stratégie de scalping indépendante de la zone (règles fixées le 24 octobre 2026, avant tout calcul)

## Demande de l'utilisateur (24 octobre 2026)

Trouver une stratégie de **scalping** indépendante de la zone de bruit : parcourir les études publiées et des centaines de
milliers de stratégies, faire passer chacune par toutes les étapes avant de la dire solide, avec une contre-revue
indépendante (#ultrareview), et ne pas revenir les mains vides.

**Ce qui est promis, et ce qui ne l'est pas.** Une machine obligée de trouver finit par trouver du hasard. La règle reste
donc celle du projet : tout est fixé ici avant le calcul, le hasard est mesuré par un jumeau de bruit, et le coffre
2023-2026 n'est ouvert qu'une fois. Les meilleures candidates sont publiées dans tous les cas avec leur vrai statut
(retenue, intéressante, rejetée), et le taux de réussite des placebos dit ce que vaut chaque statut.

## Ce qui est déjà connu (branche de recherche `claude/keen-babbage-r686cl`)

- `ordres/` (ES, 23 séances) et `orderflow/` (NQ, avril - octobre 2026) : le déséquilibre du carnet et l'OFI prédisent la
  minute suivante, mais l'information vaut **moins qu'un tick**, alors qu'un aller-retour au marché coûte 2,6 ticks sur
  MES. Aucune stratégie order flow autonome ne bat le hasard après frais (41 567 combinaisons).
- Machines 1 et 3 (`evolution/`, `evolution3/`, barres de 5 minutes, 7 marchés, ≈ 163 000 stratégies sur vraies données) :
  le bruit trouve autant de « bonnes » stratégies que les vraies données. Tournois 1 à 7 : 0 survivante sur plus de
  200 essais de règles publiées ou classiques.
- La zone de bruit vient d'un article (Zarattini, Aziz, Barbon 2024), testée sans réglage ; aucune machine ne l'a trouvée.

**Ce qui est nouveau ici** : la résolution d'une minute (et non 5), des durées de 1 à 30 minutes, des stops et objectifs
en unités de volatilité vérifiés dans la minute dans l'ordre le plus défavorable, des entrées à cours limité (rempli
seulement si le prix traverse la limite), des familles propres au scalping (choc d'une minute, séries de barres,
micro-compression, niveaux ronds et niveaux du jour, pic de volume, avance du S&P sur le Nasdaq à la minute, bougies,
minutes d'événement), les frais au niveau de prix d'aujourd'hui, et un **bruit qui garde la saisonnalité de la journée**.

## Études publiées retenues pour la partie A (recherche du 24 octobre 2026)

- Fung, Mok, Lam (2000, Journal of Banking and Finance) ; Grant, Wolf, Yu (2005, JBF) : retournement après un grand
  mouvement d'ouverture sur les futures d'indices ; l'effet faiblit fortement après frais.
- Étude des minutes extrêmes du Nasdaq-100 (actions) : 31 % d'une minute extrême (1 sur 1 000) se retourne la minute
  suivante.
- Ederington, Lee (1993, Journal of Finance) : l'ajustement aux annonces se fait dans la première minute ; étude des
  chiffres de 10 h sur les futures d'indices : trade de 10 h 01 à 10 h 02 dans le sens du saut.
- Peng, Wang (2008, Nikkei) : élan à 1 minute, retour à la moyenne à 10 minutes.
- Osler (2003, Journal of Finance) : prises de bénéfice regroupées sur les nombres ronds (rebond), stops juste au-delà
  (accélération à la cassure). Mesuré sur les devises seulement.
- Chague, De-Losso, Giovannetti (2019) : 97 % des day traders du mini-Ibovespa suivis 300 jours perdent de l'argent.

## Données (gratuites, déjà dans le projet)

Minutes Databento, prix bruts du contrat du jour, heure de New York, branche de recherche (variable `KB`) :

| Marché | Micro | Séance | $ par point | Tick | Frais par aller-retour | Prix de référence |
|---|---|---|---|---|---|---|
| Nasdaq 100 (NQ) | MNQ | 9 h 30 - 16 h | 2 | 0,25 | 3,00 $ | 30 900 |
| S&P 500 (ES) | MES | 9 h 30 - 16 h | 5 | 0,25 | 4,50 $ | 7 805 |
| Russell 2000 (RTY) | M2K | 9 h 30 - 16 h | 5 | 0,10 | 3,00 $ | 2 851 |
| Dow Jones (YM) | MYM | 9 h 30 - 16 h | 0,5 | 1 | 3,00 $ | 52 057 |
| Or (GC) | MGC | 8 h 20 - 13 h 30 | 10 | 0,10 | 4,00 $ | 4 178 |
| Pétrole (CL) | MCL | 9 h - 14 h 30 | 100 | 0,01 | 4,00 $ | 92,2 |
| Euro (6E) | M6E | 8 h 20 - 15 h | 12 500 | 0,0001 | 4,50 $ | 1,142 |

- Frais : 1 $ de commission et 1 tick de glissement par ordre (comme tout le projet).
- **Au prix d'aujourd'hui** : chaque trade gagne côté × (sortie − entrée) × $ par point × (prix de référence ÷ ouverture
  de la séance) − frais. Les frais pèsent donc partout ce qu'ils pèsent aujourd'hui (0,5 pb sur MNQ). Les prix de
  référence sont fixés ici (dernières clôtures connues) et ne changent plus.
- Séance complète : première et dernière minute présentes, au plus 20 minutes manquantes (recopiées à plat, volume 0).
  Pas de trade le jour d'un changement de contrat. Tout est fermé à la dernière minute de la séance.

| Période | Dates | Rôle |
|---|---|---|
| Préparation | 2016 | indicateurs seulement, jamais comptée |
| Entraînement | 2017 - 2020 (Russell : depuis le 10 juillet 2017) | sélection de la machine |
| Validation | 2021 - 2022 | la porte |
| **Coffre** | **2023 - fin des données (25 septembre 2026 pour NQ et ES)** | **ouvert une seule fois** |

Les programmes d'exploration lisent un cache coupé au 31 décembre 2022 : le coffre est hors de leur portée. 2011 - 2016
n'est pas utilisé : à 2 300 points, un tick du NQ valait 13 fois plus de son prix qu'aujourd'hui, ce qui change la
mécanique d'une minute.

## Exécution simulée (commune aux parties A et B)

- Signal à la clôture de la minute t, avec les seules données connues à ce moment.
- **Entrée au marché** : ouverture de la minute t + 1.
- **Entrée à cours limité** : limite à clôture(t) − côté × j × u, valable W minutes ; remplie seulement si une minute
  suivante **traverse** la limite d'au moins un tick (plus bas < limite pour un achat), au prix limite, ou à l'ouverture
  si elle s'ouvre déjà au-delà. Frais complets quand même.
- **Unité de volatilité u** : σ_t × √15 × prix, où σ_t est l'écart-type des rendements d'une minute (moyenne exponentielle
  des carrés, demi-vie 30 minutes, démarrée chaque matin sur la variance de la séance complète précédente). Stops et
  objectifs valent au moins 2 ticks.
- **Dans chaque minute, l'ordre le plus défavorable** : ouverture au-delà du stop → sortie à l'ouverture ; sinon stop
  touché → sortie au stop ; sinon objectif traversé d'au moins un tick → sortie à l'objectif. La minute où une limite est
  remplie peut toucher le stop, jamais l'objectif.
- Sortie forcée à la clôture de la minute t_entrée + H − 1 (durée H), et à la dernière minute de la séance. Pas de
  nouvelle entrée pendant une position ; pas d'entrée dans les 2 dernières minutes.

## Partie A : les règles des études, fixées, sans réglage (6 règles × NQ et ES = 12 tests)

| # | Règle | Source |
|---|---|---|
| A1 | Si \|ouverture → clôture de 9 h 44\| est dans les 10 % les plus grands des 252 séances complètes d'avant : contre ce mouvement à l'ouverture de 9 h 45, sortie à la dernière minute, sans stop | Grant, Wolf, Yu (2005) |
| A2 | Si \|rendement d'une minute\| dépasse le 99,9e centile des minutes des 20 séances complètes d'avant : contre lui, 1 minute | minutes extrêmes du Nasdaq-100 |
| A3 | Si \|rendement de la minute de 10 h 00\| est dans les 10 % les plus grands des 252 séances d'avant : dans son sens de 10 h 01 à 10 h 02 | chiffres de 10 h |
| A4 | Toutes les 10 minutes : si le mouvement des 10 dernières minutes dépasse 2 écarts-types des mouvements de 10 minutes des 20 séances d'avant, contre lui pendant 10 minutes | Peng, Wang (2008) |
| A5a | Niveaux ronds (NQ : multiples de 100 ; ES : de 25), entrées de 10 h à 15 h 30, premier contact de chaque niveau dans la séance : ordre à cours limité sur le niveau, contre l'arrivée du prix (rempli si traversé d'un tick), stop à 0,15 % au-delà, objectif 0,30 % en retour, 30 minutes au plus | Osler (2003), rebond |
| A5b | Mêmes niveaux : clôture d'une minute au-delà du niveau de 0,05 % au moins (la précédente était de l'autre côté) : dans le sens de la cassure à l'ouverture suivante, stop au niveau, objectif 0,30 %, 30 minutes au plus | Osler (2003), cassure |

**Tri de la partie A** :
1. Exploration 2017 - 2022 : t des gains nets quotidiens ≥ 2, **et** retenue par Benjamini-Hochberg à 10 % sur les
   12 tests ;
2. bat 95 % de 40 jumeaux de bruit (même règle sur 40 versions bruitées des données, voir plus bas) ;
3. coffre : t ≥ seuil de Bonferroni pour l'ensemble des finalistes des parties A et B, et au moins 3 années positives sur
   4 (2023, 2024, 2025, 2026).

## Partie B : la machine évolutive de scalping

### Les familles (signal à la clôture de la minute t)

| # | Famille | Signal (z en écarts-types σ) |
|---|---|---|
| F0 | Choc d'une minute | \|rendement de la minute\| ≥ Z σ_t |
| F1 | Mouvement de k minutes | \|mouvement des k dernières minutes\| ≥ Z σ_t √k, k ∈ {2, 3, 5, 10, 15, 30} |
| F2 | Série de barres | n clôtures de suite dans le même sens, n de 3 à 8 |
| F3 | Micro-compression puis cassure | amplitude des k dernières minutes < Q σ_t √k × prix, puis clôture au-delà de leur plus haut ou plus bas |
| F4 | Écart au VWAP | \|clôture − VWAP de la séance\| ≥ Z σ_t √30 × prix |
| F5 | Niveau franchi ou rejeté | niveau : plus haut, plus bas ou clôture de la séance précédente ; plus haut ou plus bas des 5, 15 ou 30 premières minutes ; plus haut ou plus bas du jour ; niveau rond (NQ 100, ES 25, RTY 25, YM 250, GC 10, CL 1, 6E 0,005). Type : clôture au-delà (la précédente en deçà) ou rejet (mèche au-delà, clôture revenue) |
| F6 | Pic de volume | volume ≥ M fois la médiane de la même minute sur les 10 séances d'avant, M de 2 à 8 ; sens de la bougie |
| F7 | Avance de l'autre indice (NQ et ES seulement) | l'autre indice a bougé de Z σ √k ou plus sur k minutes (k ∈ {1, 2, 3, 5}) et la cible d'au moins D σ √k de moins dans ce sens : dans le sens de l'autre |
| F8 | Bougie | sur des bougies de 1, 3 ou 5 minutes : mèche (≥ W de l'amplitude, clôture dans le tiers opposé) ou avalement (corps qui couvre le corps précédent en sens inverse), après un mouvement de k minutes ≥ Z σ √k |
| F9 | Minute d'événement | à une minute fixe (9 h 31, 9 h 35, 9 h 45, 10 h, 10 h 01, 10 h 30, 11 h, 12 h, 13 h, 14 h, 14 h 30, 15 h, 15 h 30, 15 h 45, 15 h 50 ; pour GC, CL et 6E, mêmes écarts depuis leur ouverture) : sens du mouvement des k dernières minutes si \|z\| ≥ Z (Z de 0 à 3) |

### Le génome

| Gène | Valeurs |
|---|---|
| famille et ses paramètres | voir le tableau |
| sens | suivre le signal ou le contrer |
| côtés | les deux, achats seuls, ventes seules |
| fenêtre d'entrée | début 1, 15, 30, 60, 120 ou 180 minutes après l'ouverture ; fin 60, 120, 210, 300 minutes ou 5 minutes avant la fin |
| régime | tous ; agité (σ du jour jusqu'ici > 1,2 fois la médiane des 20 séances d'avant) ; calme (< 0,8 fois) |
| tendance | toute ; seulement dans le sens de clôture − ouverture du jour ; seulement contre |
| entrée | au marché, ou à cours limité j ∈ {0,1 ; 0,25 ; 0,5} u, valable W ∈ {1, 3, 5} minutes |
| stop | a ∈ [0,3 ; 3] u |
| objectif | aucun, ou b ∈ [0,3 ; 5] u |
| durée H | 1, 2, 3, 5, 10, 15, 20 ou 30 minutes |
| pause après une sortie | 0, 5 ou 15 minutes |

### La boucle

- **Une machine par marché** (7), **4 graines sur les vraies données et 4 sur bruit** (chaque graine de bruit a ses propres
  données bruitées). Population 200, 60 générations : 20 élites, 160 descendants (mutation de chaque gène avec la
  probabilité 0,25, ou croisement avec un parent de la même famille), 20 immigrants. Soit 672 000 évaluations.
- **Fitness** : t des gains nets quotidiens sur l'entraînement (jours sans trade compris), multiplié par
  min(1, trades / 200).
- **Éligible** : t entraînement ≥ 2 avec au moins 200 trades, et t validation ≥ 1 avec au moins 50 trades.
- **Score** : t sur 2017 - 2022 (entraînement et validation ensemble).
- Toutes les stratégies distinctes évaluées sont comptées et publiées.

### Le jumeau de bruit (nouveau : garde la saisonnalité de la journée)

Pour chaque année, chaque minute de la séance (sauf la première) prend la barre de la même minute d'une autre séance de
la même année, tirée par une permutation : rapports ouverture, plus haut, plus bas, clôture à la clôture précédente, et
volume. Chaque séance part de la clôture bruitée de la veille avec le vrai écart d'ouverture, puis les prix sont
enchaînés et arrondis au tick. On garde ainsi la volatilité, le volume et la dérive moyenne de chaque minute de la
journée, mais on détruit tout lien entre une minute et les suivantes. NQ et ES reçoivent la même permutation (même
séance source pour la même minute), ce qui garde leur lien au même instant et détruit l'avance de l'un sur l'autre.

### Finalistes, paliers et placebos

- **Barrière du bruit**, par marché : le plus haut score des stratégies éligibles trouvées sur bruit (toutes graines).
- **Taux de fausses pistes** : pour chaque seuil de score, nombre d'éligibles réelles au-dessus, comparé à la moyenne sur
  bruit.
- **Finalistes** : par marché, les 2 meilleures éligibles réelles par score, de familles différentes (14 au plus), plus
  les survivantes de la partie A. m = leur nombre.
- **Placebos** : par marché, les 2 meilleures éligibles trouvées sur bruit, de familles différentes, jouées sur le vrai
  coffre.
- **Coffre, une seule fois** :
  - **retenue** (peut aller vers le robot) : au-dessus de la barrière du bruit en exploration, t au coffre ≥ seuil de
    Bonferroni pour m (z unilatéral 0,05/m), et au moins 3 années positives sur 4 ;
  - **intéressante** (argent virtuel seulement) : t au coffre ≥ 1,65 et au moins 3 années positives sur 4 ;
  - la part des placebos qui passe chaque palier est publiée : si elle est comparable à celle des finalistes, le palier
    ne prouve rien.

### Pour une stratégie retenue ou intéressante (descriptif)

Corrélation quotidienne avec la zone ; challenges Lucid Flex 50K (1 et 2 contrats) et Bulenox 50K 30 jours (3 contrats,
et 4 puis 6), seule et avec la zone, départs du coffre, moteur minute par minute (plus hauts et plus bas compris).

## Contre-revue indépendante (#ultrareview)

1. **Avant l'exploration** : un relecteur indépendant reprend le code (données, moteur, bruit, exécution, coupure du
   coffre, conformité à ces règles). Ses défauts sont corrigés et listés ici avant tout résultat.
2. **Après le coffre** : un second relecteur recalcule de son côté les chiffres décisifs.

## Limites écrites d'avance

- Minutes seulement : le scalping à la seconde et l'apport de liquidité demandent le carnet ordre par ordre (MBO,
  environ 100 $ par jour, hors budget). Les 6 mois de secondes du NQ ont déjà servi (`orderflow/`).
- Pas de séance de nuit (les minutes ne couvrent que la séance du jour).
- Un vrai remplissage peut coûter plus qu'un tick dans un marché rapide ; un ordre limite traversé d'un tick peut ne pas
  être rempli en entier.
- Environ 670 000 évaluations : des centaines de « bonnes » stratégies apparaîtront par hasard. C'est le rôle du jumeau
  de bruit et du coffre.
