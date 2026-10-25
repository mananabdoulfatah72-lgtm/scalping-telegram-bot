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

## Version 2 des règles (24 octobre 2026, avant tout calcul) : trois pistes de plus

L'utilisateur demande d'explorer toutes les pistes qui pourraient donner un scalping gagnant. Rien n'a encore été
calculé sur les vraies données (seuls des contrôles du moteur sur données bruitées ou fabriquées ont tourné). Les
parties A et B ne changent pas. Trois pistes s'ajoutent, et **le coffre n'est ouvert qu'une fois, pour toutes les
parties ensemble**, après toutes les explorations : m = nombre total de finalistes (A, B, B2, C, D), un seul seuil de
Bonferroni.

### Partie B2 : le bitcoin CME (micro MBT), 8e marché de la machine

Minutes du bitcoin CME (`tournoi5/donnees/bitcoin_1min.csv.gz`, depuis décembre 2017), séance 9 h 30 - 16 h, micro MBT
(0,1 bitcoin : 0,1 $ par point, tick de 5 points), frais 3 $ par aller-retour (2 $ de commission et 2 ticks, comme
`tournoi6/`), prix de référence 84 000, niveaux ronds de 1 000. Même machine que la partie B (familles F0 à F9 sans F7,
4 graines réelles et 4 sur bruit, mêmes critères). Entraînement de février 2018 à 2020 (préparation : décembre 2017 et
janvier 2018), validation 2021 - 2022.

### Partie C : un modèle appris, réentraîné chaque année sur le passé seulement

- Marchés : les 8 de B et B2.
- **Variables à la clôture de la minute t** (toutes connues à t) : mouvements de 1, 5, 15 et 30 minutes en unités σ ;
  écart au VWAP en unités σ √30 ; position dans l'amplitude du jour ; distances au plus haut, au plus bas et à la
  clôture de la veille en unités u ; volume rapporté à la médiane de la même minute ; régime rg ; heure (t / N et son
  carré) ; corps de la bougie rapporté à son amplitude ; pour NQ et ES, mouvement de 5 minutes de l'autre indice.
- **Cible** : signe de ln(clôture de t + 15 ÷ ouverture de t + 1).
- **Modèle** : régression logistique avec pénalité L2 fixée (λ = 1 sur variables centrées réduites sur l'apprentissage),
  apprise sur une minute sur cinq, de 9 h 45 à 15 h 30, de toutes les séances jouables des années précédentes (depuis
  2016 ; bitcoin depuis 2018).
- **Trading** : de 9 h 45 à 15 h 30 (pour l'or, le pétrole et l'euro : de 15 minutes après l'ouverture à 30 minutes
  avant la fin, précisé avant tout calcul), sans position : achat au marché si p ≥ 0,55, vente si p ≤ 0,45 ; sortie à la
  clôture de t + 15 ou au stop de 2 u (ordre le plus défavorable). Le modèle de l'année Y est appris sur les années
  avant Y.
- **Exploration** 2017 - 2022 (bitcoin : 2019 - 2022) : t ≥ 2, Benjamini-Hochberg à 10 % sur les 8 marchés, et bat 95 %
  de 20 jumeaux de bruit (tout le procédé refait sur données bruitées). Les survivants sont finalistes.
- **Coffre** : modèles des années 2023 à 2026 appris sur toutes les années d'avant (coffre compris pour les années
  suivantes : c'est le fonctionnement réel d'un modèle réentraîné chaque année).

### Partie D : la nuit (18 h - 9 h 25, New York), barres de 5 minutes

- Données : HistData 5 minutes (`sessions24/annees/`, cotations du comptant et des CFD, en UTC, converties en heure de
  New York), 2012 - 2026. Marchés : Nasdaq 100 (usatechidxusd → MNQ), S&P 500 (usa500idxusd → MES), or (xauusd → MGC),
  euro (eurusd → M6E), livre (gbpusd → M6B), dollar australien (audusd → M6A). Le yen (pas de micro aux mêmes
  conditions) et le pétrole (données arrêtées en 2023) sont exclus.
- **Séance** : de 18 h à 9 h 25 le lendemain (184 barres), datée du matin ; le dimanche soir ouvre la séance du lundi.
  Complète : première et dernière barre présentes, au plus 18 barres manquantes. Pas de volume dans ces données :
  VWAP remplacé par la moyenne des prix typiques, familles F6 (volume) et F7 (autre indice) retirées.
- **Frais** des micros au prix d'aujourd'hui (dernière cotation des fichiers) : MNQ 3 $, MES 4,50 $, MGC 4 $, M6E 4,50 $,
  M6B 3,25 $, M6A 4 $ par aller-retour.
- **Même moteur et même machine**, l'unité de temps étant la barre de 5 minutes : durées de 1 à 30 barres (5 minutes à
  2 h 30) ; fenêtres d'entrée et minutes d'événement en barres depuis 18 h : 19 h, 20 h, 21 h, 2 h, 3 h, 4 h, 7 h, 8 h,
  8 h 30, 9 h (ouvertures de Tokyo, Francfort, Londres, chiffres américains), plus les mêmes décalages fixes que F9.
- Entraînement 2013 - 2018 (préparation 2012), validation 2019 - 2022, coffre 2023 - octobre 2026. Mêmes critères,
  4 graines réelles et 4 sur bruit par marché, 2 finalistes par marché, placebos.

### Contre-revue

Le code des parties B2, C et D est relu par un relecteur indépendant avant d'être lancé, comme celui des parties A et B.

## Version 3 (25 octobre 2026) : corrections de la contre-revue, avant tout calcul sur les vraies données

Le relecteur indépendant (commit da57d3a) n'a trouvé **aucun défaut bloquant, aucun regard vers le futur ni aucune fuite du
coffre**. Ses recalculs indépendants donnent 0 écart sur 26 897 trades de la partie B et 19 565 de la partie A, une fois le
défaut 4 reproduit. Corrections apportées avant toute exploration :

| # | Défaut | Correction |
|---|---|---|
| 1 | Ordre limite rempli quand l'ouverture **touche** la limite | rempli seulement si l'ouverture est **strictement** au-delà, ou si la limite est traversée d'un tick |
| 2 | Stops hors de la grille des prix (sortie à un prix impossible, environ 0,1 à 0,25 $ offerts par trade) | stops arrondis vers la perte, objectifs en s'éloignant de l'entrée, sur la grille des données |
| 3 | Bruit du 6E arrondi à 0,0001 alors que les données cotent par 0,00005 (bruit plus grossier que le vrai) | bruit arrondi à la grille des données (`pas`) ; le tick traversé et les frais restent ceux du micro |
| 4 | σ de l'autre indice démarré à 0 le lendemain d'une séance absente (F7 trop facile, 24 séances) | NaN : pas de signal F7 tant que σ n'est pas connu |
| 5 | Objectif permis dans la minute d'un remplissage limite à l'ouverture | jamais d'objectif dans la minute d'un remplissage limite |
| 6 | Ordre limite rempli dans les 2 dernières minutes | ordre annulé |
| 7 | Comparaisons de prix en virgule flottante (RTY, GC, CL, 6E) | comparaisons à une demi-maille de la grille ; niveaux ronds en pas entiers |
| 9 | Niveau rond sauté par un écart non marqué « touché » (A5a) | niveaux entre la clôture précédente et la barre marqués touchés |
| 10 | Seuils de A1 et A3 calculés dès 100 séances | 252 séances complètes, comme écrit |
| 11 | Test sans regard vers le futur trop étroit | il change aussi les séances suivantes et l'autre indice (NQ, GC, BTC, 6E de nuit : ok) |
| 12 | Coffre rouvrable avec `--relire` et une liste de finalistes modifiée | empreinte sha256 de `finalistes.json` gardée ; `--relire` refusé si elle change |

**Règles précisées ou changées (avant tout calcul)** :
- **Second jumeau de bruit, par signe** (le relecteur a montré que la permutation détruit le regroupement de la
  volatilité : la corrélation des |r| successifs passe de 0,37 à 0,13 sur le NQ, et l'espace de recherche est plus
  large sur le vrai, ce qui peut abaisser la barrière). Chaque minute garde sa barre mais est retournée avec la
  probabilité 1/2 : volatilité, regroupement, volume et saisonnalité gardés, sens détruit (NQ et ES reçoivent les
  mêmes signes). **Machines** : 4 graines de plus sur ce bruit par marché ; la **barrière** est le meilleur score
  éligible des deux bruits. **Parties A et C** : il faut battre 95 % des jumeaux de **chacun** des deux bruits
  (40 + 40 pour A, 20 + 20 pour C). **Placebos** : les 2 meilleurs de chaque bruit par marché.
- **Régime** : rg = σ_t ÷ médiane de σ à la même minute des 20 séances complètes d'avant (au lieu de σ du jour depuis
  l'ouverture, que le pic d'ouverture rendait presque toujours « agité »). Seuils 1,2 et 0,8 inchangés.
- **Bitcoin (B2 et C)** : avant le micro MBT (mai 2021), seul le contrat de 5 bitcoins existait et la plupart des
  minutes sont sans transaction (moins de 2 % de séances complètes en 2018 - 2019). Séance complète = première et dernière
  minute présentes et au moins 300 minutes échangées sur 390. B2 : entraînement janvier 2020 - juin 2021, validation
  juillet 2021 - décembre 2022. C : années jouées 2021 - 2022, modèle appris depuis 2020.
- **Choix du code rendus explicites** (relevés par le relecteur, identiques sur le vrai et sur le bruit) :
  - F1, F4 et F7 ne donnent un signal qu'au **croisement** du seuil (la minute précédente ne le remplissait pas) ;
  - F2 exige en plus un mouvement total ≥ Z σ √n ; F5 une marge ≥ Z σ × prix au-delà du niveau franchi ;
  - les signaux utilisent σ connu avant la minute t (σ_{t−1}) ; l'unité u des stops utilise σ_t ;
  - la limite d'entrée est arrondie en s'éloignant du marché ;
  - la fenêtre de 10 h à 15 h 30 s'applique aussi à A5b ;
  - mutation : la famille change avec la probabilité 0,125 (nouveaux paramètres), chaque autre gène avec 0,25 ; les
    enfants d'un croisement sont aussi mutés.

**Limites signalées par le relecteur, sans changement** : au prix d'aujourd'hui, un tick de 2017 pèse 3 à 5 fois plus
qu'au coffre (règle du tick traversé et arrondis plus sévères en exploration, donc prudent) ; 4 des 15 minutes
d'événement de F9 tombent hors de la séance de l'or et du pétrole (gènes inertes).

Une seconde contre-revue relit ces corrections et le code des parties B2, C et D avant leur lancement. Les machines sur
**bruit seulement** sont lancées pendant cette relecture (elles ne disent rien des vraies données) ; les vraies données,
les parties A et C et le coffre attendent la fin de la relecture.

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
