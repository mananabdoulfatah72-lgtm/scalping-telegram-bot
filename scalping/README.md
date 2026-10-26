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
- **Séance** : de 18 h à 9 h 20 le lendemain (184 barres, la dernière de 9 h 15 à 9 h 20), datée du matin ; le dimanche soir ouvre la séance du lundi.
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
| 8 | Choix du code absents du README (croisement, marges, σ des signaux, mutation…) | décrits plus bas (« choix du code rendus explicites ») |
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

## Version 4 (25 octobre 2026) : seconde contre-revue, avant tout calcul sur les vraies données

Le second relecteur (commit 638f865) n'a trouvé **ni regard vers le futur, ni fuite du coffre, ni défaut bloquant** ;
ses recalculs indépendants donnent **0 écart** sur 17 597 trades de B, B2 et D (marché et limite), 20 327 de A et
16 197 de C. Corrections :

| # | Défaut | Correction |
|---|---|---|
| 1 | Le bruit par signe perd le niveau des prix (il dérive au hasard : NQ 0,69 à 0,92 fois le vrai, NQ de nuit 0,39 à 0,58), donc le tick y pèse plus lourd : ce bruit était plus dur que le vrai et pouvait abaisser la barrière | chaque mois, toutes les minutes (sauf la première de chaque séance) sont décalées d'une même constante pour que le mouvement du mois soit le vrai : le niveau est exactement le vrai à chaque fin de mois (dans le mois : NQ de 0,82 à 1,12) |
| 2 | Rien n'empêchait d'ouvrir le coffre avant la fin de toutes les explorations | `exploration` inscrit la complétude (4 graines × 3 sortes par marché, parties A et C) ; `ouvrir` refuse si quelque chose manque ; `exploration` refuse une fois le coffre ouvert |
| 3 | Nuit : la barre de 18 h manque souvent en 2023 - 2025 (43 % des nuits du coffre incomplètes) | une nuit est complète si une barre existe avant 18 h 15 ; les premières barres manquantes sont recopiées à plat (décidé sur la seule présence des barres) |
| 4 | Rejet d'un niveau rond comparé en virgule flottante (F5, devises : +8 % à +35 % de signaux) | comparaison à une demi-maille |
| 5 | Stop de la partie C ni arrondi ni comparé à une demi-maille | même règle que le moteur |
| 6 | Partie C : apprise sur les minutes de signal 15 à 360, jouée sur 14 à 359 | une seule convention : minutes de décision 14 à 359 (entrée de 9 h 45 à 15 h 30) |
| 7 | Partie C : pas de modèle 2017 pour le Russell (données depuis juillet 2017) | Russell joué de 2018 à 2022 |
| 8 | Séance de nuit annoncée jusqu'à 9 h 25 | 18 h - 9 h 20 (184 barres) |
| 9 | Libellés (minutes d'événement de nuit, années du bitcoin en C) | corrigés |
| 10 | Test sans regard vers le futur trop faible, sans la partie C | génomes actifs seulement ; test de C ajouté (1 287 probabilités comparées) |

**Règle précisée** (signalée par le relecteur) : stops, objectifs et limites sont arrondis **au tick du micro-contrat**
(un future ne se traite qu'à ce pas), les comparaisons se font à la demi-maille des données. Cela ne change rien quand
les deux grilles sont égales ; c'est plus prudent pour le 6E (données à 0,00005, micro à 0,0001) et pour la nuit
(cotations au millième ou au cent-millième).

**Limites signalées, sans changement** : le bruit par signe efface la dérive de la nuit à l'intérieur de chaque mois
(Boyarchenko et coll.) ; λ = 1 sur ≈ 10⁵ lignes revient presque à ne pas pénaliser le modèle de la partie C ; le
recalage mensuel du bruit par signe laisse dans ce bruit une petite dérive connue sur le mois, présente aussi dans les
vraies données.

Les vraies données, les parties A et C et les machines sont lancées après ces corrections (25 octobre, 0 h 52 UTC) ;
le relecteur vérifie les corrections pendant le calcul, et le coffre ne s'ouvre qu'après sa réponse.

**Vérification des corrections v4 par le relecteur** : les 8 points sont justes (0 écart sur 17 489 trades recalculés
avec l'arrondi au tick du micro ; niveau du bruit par signe exact en fin de mois ; verrou du coffre simulé ; nuits du coffre
du NQ complètes à 97 % en 2024 et 99 % en 2025, contre 54 % et 67 % avant). Le recalage mensuel laisse une petite dérive
suivable dans le bruit par signe (avant frais : +0,24 pb par trade de 30 minutes sur NQ, sous les frais de 0,49 pb) : le
bruit en est un peu plus facile, donc la barrière un peu plus prudente ; il ne peut pas créer de fausse survivante.
Restes corrigés pendant le calcul :
- **F5, niveau rond franchi avec une marge nulle** : comparaison faite en virgule flottante (1,7 % des signaux du 6E
  de jour, environ 1 % la nuit sur 6E, 6B, 6A) ; l'écart au niveau est maintenant compté en mailles entières. Seuls
  les marchés de devises sont touchés (niveaux non entiers) : leurs machines (6E de jour ; 6E, 6B, 6A de nuit) sont
  refaites avec le code corrigé, les autres sont identiques ;
- `ouvrir` recompte la complétude sur les fichiers (au lieu de lire un drapeau) et refuse si un résultat est plus récent
  que la sélection ;
- **Limite de la partie D** : en 2023, seules 55 % des nuits sont complètes sur les 6 marchés (HistData n'a pas les
  barres du milieu de nuit) ; aucune règle ne peut le corriger, le coffre de nuit 2023 est donc plus court.
- Aucun fichier de la version 3 n'est réutilisé : les 43 fichiers de bruit v3 ont été retirés avant le lancement, et
  tous les fichiers de résultats sont postérieurs à 0 h 52.

## Réalisme de la partie D (fixé le 25 octobre 2026, après l'exploration, avant l'ouverture du coffre)

L'exploration de nuit sort nettement du bruit sur le Nasdaq. Mais les données de nuit sont des **cotations de CFD**
(HistData), pas des transactions du future : le bruit de cotation (aller-retour acheteur-vendeur, prix figés aux heures
creuses) peut créer de faux retours à la moyenne, que les deux bruits détruisent et que le coffre, fait des mêmes
cotations, ne peut pas démasquer. Règles fixées avant d'ouvrir le coffre :
1. **Contrôle descriptif** (`realisme_nuit.py`, 2013 - 2022 seulement) : corrélation des rendements horaires de nuit du
   CFD et du vrai future (barres d'une heure Databento du NQ et de l'ES), et autocorrélation d'une heure à la suivante
   dans chaque source.
2. **Une finaliste de nuit retenue ou intéressante au coffre reste en argent virtuel**, jamais dans le robot, tant que
   le même génome n'a pas été confirmé sur de **vraies transactions de nuit du future** (export de nuit de la plateforme
   de l'utilisateur, ou données achetées), avec ses règles de confirmation écrites avant de lire ces transactions.
3. **Descriptif** (`analyse_nuit.py`, exploration seulement) : part des achats et des ventes dans le gain, et
   corrélation avec un simple achat de la nuit (la dérive de nuit connue), pour savoir si une finaliste ne fait
   qu'acheter cette dérive.

## Résultats (25 octobre 2026) : aucune stratégie de scalping ne tient

### Ce qui a été cherché

| Piste | Stratégies distinctes sur les vraies données | Sur les deux bruits |
|---|---|---|
| B, jour, 7 marchés | 296 488 | 592 540 |
| B2, bitcoin CME | 42 510 | 84 578 |
| D, nuit, 6 marchés | 254 127 | 508 291 |
| A, règles des études | 12 tests | 960 jumeaux |
| C, modèle appris chaque année | 8 marchés | 320 jumeaux |

Soit **593 125 stratégies de scalping sur les vraies données** et 1 185 409 sur bruit.

### Exploration (jusqu'au 31 décembre 2022) : `resultats/exploration.txt`, `partie_a.txt`, `appris.txt`

- **Partie A : 0 survivante sur 12.** Aucune règle publiée n'atteint t ≥ 2 après frais (la meilleure, A4 sur NQ : t 1,10).
- **Partie C : 0 sur 8.** Le modèle appris perd sur tous les marchés (t de −2,4 à −29,8).
- **Jour (B)** : le NQ et l'ES ont plus d'éligibles que le bruit par permutation, mais le bruit par signe en a autant ou
  plus sur le NQ (barrière 4,64 contre un meilleur réel de 4,28). RTY, YM, GC, CL, 6E : rien de plus que le bruit.
- **Bitcoin (B2)** : 2,2 éligibles par graine contre 0,5 et 0,2 sur bruit, meilleur score 3,01.
- **Nuit (D)** : le Nasdaq sort nettement du bruit (1 160 éligibles par graine contre 204 et 256 ; 336 au-dessus
  d'un score de 4,5 contre 0 sur bruit ; meilleur 6,54). Les autres marchés de nuit, non.
- Analyse avant coffre (`analyse_nuit.txt`) : la meilleure de nuit n'achète que, mais n'est corrélée qu'à +0,17 avec
  un simple achat de la nuit ; la deuxième ne fait que vendre (−0,26). Réalisme (`realisme_nuit.txt`) : à l'échelle de
  l'heure, le CFD de nuit suit le future (corrélation 0,92 sur le NQ, même volatilité, pas d'autocorrélation en trop).

### Coffre 2023 - 2026, ouvert une fois pour toutes les parties : `resultats/coffre.txt`

m = 16 finalistes, seuil de Bonferroni t ≥ 2,73. **0 retenue, 0 intéressante. Placebos : 0 sur 29.**

| Finaliste | Exploration | Coffre (t) | Gain au coffre, 1 contrat |
|---|---|---|---|
| D NQ, micro-compression puis cassure, achats seuls (nuit) | 6,54 | 0,40 | +1 522 $ |
| D NQ, série de 3 barres, ventes seules (nuit) | 4,37 | 0,01 | +13 $ |
| B NQ, choc d'une minute, ventes seules | 4,28 | −1,51 | −3 453 $ |
| B ES, avalement de 3 minutes, contre | 4,21 | −1,89 | −2 343 $ |
| B ES, mouvement de 10 minutes, contre | 4,15 | −1,25 | −807 $ |
| B YM, choc d'une minute, suivre | 3,86 | −1,40 | −975 $ |
| D ES, micro-compression, achats seuls (nuit) | 3,72 | −0,06 | −62 $ |
| B NQ, mouvement de 3 minutes, ventes seules | 3,27 | 0,11 | +162 $ |
| D GC, série de 3 barres, ventes seules (nuit) | 3,08 | −0,24 | −344 $ |
| B2 BTC, niveau rond franchi, contre | 3,01 | −0,39 | −514 $ |
| D GC, mouvement de 10 barres, contre (nuit) | 2,86 | −0,50 | −1 407 $ |
| B2 BTC, pic de volume, suivre | 2,45 | 0,21 | +242 $ |
| B RTY (2), B YM, B GC | 2,17 à 2,42 | −3,23 à −0,51 | −2 613 à −820 $ |

### Après le coffre (descriptif, pas un test) : `resultats/apres_coffre.txt`

Toutes les stratégies éligibles en exploration ont été jouées sur le coffre.
- **Nuit du NQ** : **aucune des 4 639 choisies sur les vraies données n'atteint t ≥ 2,73 au coffre** (la meilleure
  2,65), et la part qui ferait le palier « intéressant » (t ≥ 1,65 et 3 années positives) est la même que pour celles
  choisies sur bruit : 3,5 % contre 3,8 % (permutation) et 3,3 % (signe). **L'avance de la nuit en exploration était un
  régime de 2013 - 2022, pas une structure qui dure.** (Les médianes, 0,14 contre 0,66 et −0,49, sont tirées par des
  grappes de quasi-clones d'une seule graine : le relecteur final les juge fragiles.)
- **Jour du NQ** : les 498 choisies sur le vrai ont un t médian de 0,77 au coffre, mais **aucune n'atteint le seuil**
  (la meilleure 2,08), et 456 d'entre elles sont des variantes d'une même famille (choc d'une minute) issues de 2 graines.
- ES et YM de jour, ES de nuit : rien.

### Ce qu'on retient

- **Aucune stratégie de scalping ne passe**, ni publiée, ni trouvée par 593 125 essais, ni apprise : sur ces
  marchés, en barres d'une minute ou de cinq, après frais réels, le gain disparaît hors échantillon. C'est ce que
  disent aussi `ordres/` et `orderflow/` (l'information de très court terme vaut moins qu'un aller-retour) et l'étude
  des day traders du mini-Ibovespa (97 % perdent).
- **Relancer des milliers de vagues sur les mêmes données ne changerait pas cette conclusion** : les jumeaux de bruit
  montrent que plus on cherche, plus on trouve du hasard qui ressemble à un avantage, et le coffre 2023 - 2026 est
  maintenant utilisé pour ces familles.
- **Ce qui pourrait encore changer la réponse, avec d'autres données** :
  1. le carnet d'ordres complet (MBO) pour un scalping à cours limite qui capte l'écart, au lieu de le payer
     (environ 100 $ par jour de données) ;
  2. de vraies transactions de nuit du future, pour regarder la nuit sans les cotations CFD ;
  3. le temps : les mois après octobre 2026, que personne n'a vus.

## Contre-revue finale, après le coffre (25 octobre 2026)

Un troisième relecteur indépendant a tout recalculé avec son propre code (sans `moteur.py`) :
- **les 16 finalistes et les 29 placebos au coffre : identiques** (t, trades, gains, années) ;
- **la sélection, recomptée depuis les fichiers** sur les 14 couples piste-marché : finalistes, placebos et barrières
  conformes ; **toutes les éligibles réelles ont été jouées au coffre, aucune n'atteint t ≥ 2,73** : aucune survivante
  n'a pu être oubliée ;
- parties A et C refaites (A3, A4 sur NQ et ES ; modèle appris sur NQ par une autre méthode) : identiques ;
- caches du coffre relus directement dans les fichiers bruts (≈ 1,9 million de barres, 0 prix différent), caches
  identiques avant 2023, frais, échelle et empreinte de `finalistes.json` conformes ;
- sans l'année 2023 (nuits complètes à 55 %), les finalistes de nuit restent à t ≤ 0,43.

**Verdict du relecteur : la conclusion est juste.** Défauts mineurs relevés, sans effet sur les calculs : libellés de
la nuit (« minute » pour des barres de 5 minutes, fins de fenêtre au-delà de 9 h 20) ; lecture des médianes après le
coffre (corrigée plus haut).

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

## Version 5 (25 octobre 2026) : nouvelle vague sur tout l'historique, coffre = l'avenir (règles fixées avant tout calcul de cette vague)

### Demande de l'utilisateur (25 octobre 2026)

- Nouvelle vague de recherche sur toutes les données jusqu'à aujourd'hui, mêmes familles, mêmes faux marchés.
- Nouveau coffre : l'avenir, à partir du 1er novembre 2026, en argent virtuel.
- Pas d'export de transactions de nuit : cette piste est abandonnée.
- Diversifier les marchés ; si possible, des options de scalping « avec un score raisonnable qui ne s'effondre pas au
  coffre ».

### Ce qui change, et pourquoi

Le coffre 2023 - 2026 a été ouvert une fois (version 4). Il devient une période de **contrôle** connue ; le seul juge
neuf est l'avenir. Ce que la version 4 a appris : un t d'exploration élevé ne prédit rien (0 finaliste sur 16 au
coffre). D'où trois changements, et seulement ceux-là :
1. **on choisit sur la tenue en 2023 - 2026**, période que la machine ne voit jamais pendant qu'elle cherche, et non sur
   le t d'entraînement ;
2. **chaque chiffre réel est comparé au même chiffre obtenu sur les deux bruits**, passés par exactement la même
   chaîne (machine, admission, contrôle, sélection) ;
3. **le panier** : la moyenne de toutes les stratégies admises d'un marché, pour voir si une structure faible mais
   réelle, invisible stratégie par stratégie, ressort quand on en met beaucoup ensemble.

Honnêteté sur le point 3 : l'idée vient de la lecture de `apres_coffre.txt` (t médian 0,77 au coffre pour les éligibles
du NQ de jour, contre 0,03 et 0,12 sur bruit). Un calcul descriptif du même panier sur les stratégies de la version 4
(`ensemble_v4.py`) est lancé au moment où ces règles sont écrites ; son résultat n'est pas encore lu. Le panier de la
version 5 sera de toute façon jugé par l'avenir.

### Données et périodes

Caches complets (`cache/complet_*.npz`), déjà relus par la contre-revue finale. Rien de neuf n'est téléchargé.

| Piste | Marchés | Entraînement (seul vu par la machine) | Contrôle (choix) | Coffre |
|---|---|---|---|---|
| B, jour | NQ, ES, RTY, YM, GC, CL, 6E | 2017-01-01 - 2022-12-31 | 2023-01-01 - fin des données (25 au 28 septembre 2026) | l'avenir |
| B2, bitcoin CME | BTC | 2020-01-01 - 2022-12-31 | 2023-01-01 - 30 septembre 2026 | l'avenir |
| D, nuit (CFD HistData) | NQ, ES, GC, 6E, 6B, 6A | 2013-01-01 - 2022-12-31 | 2023-01-01 - 2 octobre 2026 | l'avenir |

### Diversifier les marchés : ce qui est possible

Les 22 autres marchés CME (taux, métaux, énergie, devises, grains, gaz, bitcoin) ont déjà été testés en intraday par
`etude_large/` (branche `claude/affectionate-turing-tnz0mn`, ETF en 5 minutes, 7 familles, 189 essais) : **tout est
négatif après les frais du plus petit contrat CME**, qui y valent 1,5 à 84 points de base par aller-retour contre 1,2 sur
MNQ. Un scalping de quelques minutes y serait encore plus écrasé par les frais, et il n'existe pas de minutes gratuites
de ces futures. `couts.py` (descriptif, sans décision) donne pour chaque marché le coût d'un aller-retour divisé par le
mouvement médian de 15 minutes, sur 2023 - 2026. La machine reste sur ses 14 couples piste-marché.

### La machine

Identique à la version 4 (familles F0 à F9, génome, 60 générations de 200, exécution, frais, prix d'aujourd'hui, deux
bruits). Seules les périodes changent. **6 graines par sorte** (vrai, bruit par permutation, bruit par signe), numérotées
11 à 16, nouvelles (la version 4 utilisait 1 à 4). Les jumeaux de bruit sont fabriqués sur les caches complets : le
bruit couvre aussi la période de contrôle. Fichiers `resultats/v5/machine_<piste>_<marche>_<sorte>_<graine>.npz`.

### Admission, contrôle, sélection

- **Admise** : sur l'entraînement, t ≥ 2 et au moins 200 trades (génomes distincts, toutes graines réunies).
- **Contrôle** (2023 - fin des données) pour chaque admise : t_c des gains quotidiens nets, trades n_c, gain de chaque
  année 2023, 2024, 2025, 2026.
- **Candidate** (une stratégie) : t_c ≥ 1,65 ; n_c ≥ 100 ; au moins 3 années positives sur 4 ; **et t_c strictement
  au-dessus de la barrière du bruit**, le plus haut t_c des admises trouvées sur les deux bruits du même couple
  piste-marché qui remplissent les trois premières conditions (1,65 s'il n'y en a aucune). Au plus 2 candidates par
  couple : les meilleurs t_c, de familles différentes.
- **Placebos** : par couple, les 2 meilleures admises de bruit (familles différentes) qui remplissent les trois premières
  conditions. Elles sont suivies dans l'avenir comme les candidates, sur les vraies données.
- **Panier** (par couple et par sorte) : la moyenne des gains quotidiens de toutes les admises, chacune pour 1/N contrat
  avec ses propres frais (positions non compensées : prudent). **Panier candidat** si son t au contrôle est ≥ 2, avec
  au moins 3 années positives sur 4, et au-dessus des paniers des deux bruits du même couple.
- Pour information : corrélation quotidienne de chaque candidate et de chaque panier avec la zone du bot (trades de
  `filtre_h1/trades_zone.csv`, jusqu'à mars 2026).

### Le coffre : l'avenir

- **Liste figée** dans `resultats/v5/candidats.json` (candidates, placebos, paniers), avec son empreinte sha256 écrite
  ici avant le 1er novembre 2026.
- **Premières séances** : nuit du dimanche 1er novembre 2026 (18 h, New York), séance du lundi 2 novembre 2026.
- **Sources** : NQ de jour, `zone/robot/nq_1min.csv.gz` de `main` (le robot de la zone l'enrichit chaque jour) ; autres
  marchés de jour et bitcoin, minutes de Yahoo (contrats continus), qui ne garde que 30 jours : elles devront être
  relevées au moins toutes les 4 semaines ; nuit, HistData (même source que l'exploration), mois par mois. L'outil de
  relevé n'est écrit que pour les marchés qui ont une candidate ou un panier candidat. Une séance manquante
  est sautée, jamais remplacée par une autre source choisie après coup.
- **Points de lecture** : 1er février, 1er mai, 1er août et 1er novembre 2027, puis tous les 3 mois.
- **Écartée** : t du coffre ≤ −1 avec au moins 50 trades, à un point de lecture.
- **Retenue** (peut aller vers le robot, sur décision de l'utilisateur) : t du coffre ≥ seuil de Bonferroni pour m
  (z unilatéral 0,05/m, m = candidates + paniers candidats), au moins 150 trades, et gain positif sur au moins 2
  trimestres sur 3.
- **Intéressante** (argent virtuel) : t du coffre ≥ 1,65 et au moins 100 trades.
- Les placebos sont lus de la même façon : s'ils passent aussi souvent que les candidates, le palier ne prouve rien.
  Précision (25 octobre, avant le calcul de la sélection) : un placebo n'est suivi que sur un couple piste-marché qui a
  une candidate ou un panier candidat, puisqu'il sert de comparaison sur le même marché ; les autres sont listés, pas
  suivis. Précision de la contre-revue (avant la sélection) : un panier candidat a aussi ses **paniers placebo**, un par
  bruit : toutes les admises de ce bruit, chacune pour 1/N contrat, jouées sur les vraies données à venir.
- **Constantes figées** : prix de référence, valeur du point, tick, grille des prix, frais, pas des niveaux ronds, début
  et longueur de la séance sont écrits dans `candidats.json` pour chaque entrée ; l'outil de relevé les reprend tels
  quels (refaire les caches avec de nouveaux mois changerait, par exemple, le prix de référence de la nuit).
- La nuit garde la règle de réalisme de la version 4 : jamais dans le robot sans confirmation sur de vraies
  transactions de nuit du future.

**Correction d'une promesse.** Avant ces règles, j'avais écrit que 3 mois (200 à 300 trades) suffiraient pour juger.
C'est faux pour un avantage de la taille de celui de la zone : son t monte d'environ 1 par année, donc 3 mois donnent un
t d'environ 0,5. Trois mois servent à **écarter** ce qui perd nettement ; **confirmer** un tel avantage demande 2 à 4
ans. Seule une stratégie nettement plus forte que la zone se confirmerait en quelques mois.

### Contre-revue

Code de la vague et de la sélection relu par un relecteur indépendant avant la lecture du contrôle (25 octobre, la vague
en était à 14 tâches sur 252). **Aucun défaut critique** : la vague est conforme aux règles et ne regarde pas en avant
(il a vérifié que changer les données du contrôle ne change aucune stratégie trouvée, que l'entraînement des bruits
est identique au bit près avec ou sans les mois de contrôle, et que les indicateurs sont causaux). Défauts corrigés,
tous dans `selection5.py`, `couts.py` et ce texte (la vague en cours n'a pas à être relancée) :

| # | Défaut | Correction |
|---|---|---|
| 1 | la précision « placebos suivis seulement sur un couple avec candidate » n'était pas codée | drapeau `suivi` par placebo, compté à part |
| 2 | le journal de la vague affiche le meilleur t du contrôle de chaque tâche | retiré du code ; pour la vague en cours (lancée avec l'ancien code), seules les 2 premières lignes ont été lues (t 1,37 et 1,45), plus rien ensuite avant la sélection |
| 3 | constantes de calcul (prix de référence de la nuit…) pas figées | écrites dans `candidats.json` |
| 4 | un panier candidat n'avait pas de placebo comparable | paniers placebo (ci-dessus) |
| 5 | JSON avec NaN possibles ; fichier des trades de la zone absent sans erreur | JSON strict ; arrêt si le fichier manque |
| 6 | `candidats.json` réécrivable après publication de l'empreinte | refusé sans `--force` |
| 7 | un placebo ne gardait pas sa sorte de bruit ni ses chiffres | ajoutés |
| 8 | écriture des fichiers de la vague non atomique | atomique pour les prochains calculs |
| 9 | un panier de bruit sans aucune admise sortait de la comparaison sans le dire | compte t = 0, affiché |
| 10 | comparaisons réel / bruit asymétriques (12 jeux de bruit contre un vrai) | détail graine par graine affiché (admises, meilleur t, panier) |
| 11 | `couts.py` comptait les fenêtres en barres : sur les ETF peu échangés, la fenêtre s'allongeait | grille de l'horloge, paires complètes seulement |
| 12 | même séance 9 h 30 - 16 h pour tous dans `couts.py` (or et pétrole un peu défavorisés) | noté, ne change aucune conclusion |
| 13 | conclusion des coûts trop forte (voir ci-dessous) | réécrite |
| 14 | mots du panier v4 | précisés ci-dessous |
| 15 | le Russell commence le 10 juillet 2017 : son entraînement aussi | noté |

Sur la question de la première minute réelle gardée dans les bruits : sans effet sur les candidates (aucune entrée
pendant la minute 0, et les minutes suivantes du bruit sont permutées ou de signe tiré au hasard) ; ce que les bruits
gardent du réel (tendance du mois, profil de la journée) ne peut que relever la barrière.

### Lu après l'écriture de ces règles (descriptif)

- **Panier de la version 4** (`ensemble_v4.py` → `resultats/ensemble_v4.txt`, coffre déjà ouvert) : il ne sauve rien.
  NQ de jour : t 5,05 en exploration, **0,74** au coffre (paniers placebo, c'est-à-dire stratégies trouvées sur bruit
  rejouées sur les vraies données : 0,11 et 0,22) ; NQ de nuit 5,95 → 0,25 (placebo par permutation 0,73) ; ES de jour
  4,75 → −2,90 ; YM 3,53 → −1,07 ; ES de nuit 3,16 → −0,81. La tendance positive du NQ de jour vient de stratégies très
  liées entre elles (corrélation moyenne 0,38), donc d'une seule idée. (Dans ce calcul, l'exploration de la nuit est
  mesurée sur 2017 - 2022 et une séance non jouable compte 0.)
- **Coûts par marché** (`couts.py` → `resultats/v5/couts.txt`) : rapport du coût d'un aller-retour au mouvement médian de
  15 minutes, 2023 - 2026, fenêtres sur l'horloge. NQ (MNQ) **0,09**, de loin le plus favorable des marchés à contrat
  micro ; YM, or, ES, bitcoin, Russell 0,23 à 0,28 ; argent 0,34 ; pétrole 0,40 ; cuivre 0,45 ; palladium 0,52 ; soja
  0,73 ; devises 0,88 à 1,93 ; taux 1,06 à 1,64 ; blé et maïs 1,09 et 1,76 ; gaz 1,78. La machine contient déjà le
  pétrole (0,40) et l'euro (1,14) : sur le seul critère des coûts, l'essence (RB, 0,08), le platine (0,24), le Brent
  (0,25), l'argent (0,34), le cuivre (0,45) et le palladium (0,52) pourraient la rejoindre. Mais il n'existe pas de
  minutes gratuites de ces futures, et dans `etude_large/` (ETF en 5 minutes) tout y est négatif après frais ; les
  quelques t positifs avant frais (2,2 à 2,8) viennent d'ETF peu échangés dont ce même README juge les chiffres avant
  frais inexploitables.

## La zone de bruit filtrée : peut-on encore l'optimiser ? (25 octobre 2026, descriptif, aucun nouveau réglage testé)

Demande de l'utilisateur : « une recherche profonde pour optimiser la zone de bruit filtre delta ».

### Tout ce qui a déjà été essayé

| Étude (branche) | Ce qui a été testé | Résultat |
|---|---|---|
| `zone_optimisation/` (recherche) | 108 réglages (largeur 0,75 à 1,5, 7 à 28 jours, contrôles de 15, 30 ou 60 min, 3 stops), choisis en walk-forward de 3 façons | aucune ne bat la zone d'origine hors échantillon ; même le meilleur réglage choisi après coup sur 2023 - 2026 ne fait que t 2,24 contre 2,00 |
| `zone_failles/` (recherche) | données propres (adopté), 1 trade par jour, filtre GEX, achats seuls, stop sur le VWAP | seule la correction des données reste |
| `zone_sources/` (recherche) | confirmation par l'ES, par le volume, tendance de fond, sortie du range de nuit, rebond après forte baisse | aucune retenue |
| `zone_multi/` (recherche) | la zone sur ES, RTY, YM, or, pétrole, euro | toutes négatives après frais ; NQ seul |
| `etude_large/` (affectionate-turing) | un modèle qui combine 10 informations (heure, force de la cassure, volatilité, ES, écart d'ouverture, tendance, VIX, rang du trade), walk-forward sur 2016 - 2026 ; la zone sur 27 marchés | modèle rejeté (il écarte surtout des gagnants) ; aucun autre marché |
| `pistes/`, `phenomenes/`, `zone_implicite/`, `annonces/` (affectionate-turing) | sortie au VWAP, sortie à 16 h, renfort, zones décalées, soirs de résultats, confirmation par VIX, AUD/JPY, taux, dollar, bitcoin, nombres ronds, forme de la cassure, largeur tirée du VXN, ciblage de volatilité, annonces de 8 h 30 | rien ne passe tout ; « pas de zone les jours de la Fed » reste |
| `entree_tardive/` (elegant-ptolemy), `zone_retour/` (affectionate-turing) | entrées en retard, sorties plus rapides, sortie au retour dans la zone | moins bien que le bot |
| `filtre_h1/`, `zone_neutre/`, `relance/`, `delta_mesures/` | le filtre delta : approximations sur 15 ans (t 1,62, non confirmé), delta du QQQ et de London Strategic Edge (refusés), seuil de 1 %, proportion du volume, z-score, relance | le filtre brut reste ; aucune variante ne passe ; **106 trades seulement mesurés avec le vrai delta** |

### Ce que disent les publications (recherche du 25 octobre 2026)

- L'article d'origine (Zarattini, Aziz et Barbon, « Beat the Market », SPY, 2007 - 2024) n'a pas de suite publiée par
  ses auteurs. Il a fini 4e des Quantpedia Awards 2025.
- Une réplication indépendante sur les futures (NQ et ES, Databento, 2010 - 2026, frais réels) trouve la même chose
  que nous : NQ t 2,74 sur toute la période, gagné surtout après 2018 ; ES nul ; après la publication (585 séances),
  NQ t 1,37, non significatif.
- Une autre réplication (SPY et ES) dit que l'avantage s'est comprimé depuis 2025 et que l'optimisation ne survit pas
  au walk-forward (chiffres de son auteur, non vérifiés).
- Un article qui règle tous les paramètres et les sorties (VWAP, « ladder ») annonce un Sharpe au-dessus de 3, mais
  sur l'échantillon où il a réglé : c'est exactement ce que le walk-forward de `zone_optimisation/` a démenti.
- Concretum (même équipe) compare 4 sorties sur un autre ETF : la sortie au VWAP, celle du bot, arrive première.

### Ce que montrent les chiffres jusqu'au 20 octobre 2026 (`zone_annees.py` → `resultats/v5/zone_annees.txt`)

Zone du bot sans filtre, 1 MNQ au prix d'aujourd'hui, frais compris :

| Période | t | $ par séance |
|---|---|---|
| 2011 - 2017 | −2,31 | −13,8 |
| 2018 - 2022 | +2,96 | +29,4 |
| 2023 - 2026 | +2,07 | +20,3 |
| 2025 - 2026 | +0,87 | +14,2 |
| depuis la publication (juin 2024, 582 séances) | +1,05 | +14,4 |

Par année : 2023 t +2,23 ; 2024 +1,02 ; 2025 +0,58 ; 2026 (jusqu'au 20 octobre) +0,74. **La zone gagne toujours, mais
son avantage a environ diminué de moitié depuis 2024**, comme le dit la seconde réplication.

### Conclusion

1. **Aucun réglage ni filtre de prix à ajouter.** Les 108 réglages forment un plateau : le meilleur choisi après coup
   ne gagne presque rien, et ce qui gagnait dans le passé perd ensuite. Avec un avantage qui faiblit, ajouter des
   réglages ajoute surtout du risque de se tromper.
2. **Le filtre delta est le seul levier encore ouvert, mais il manque de données** : 106 trades mesurés avec le vrai
   delta. Sans export, il ne peut être jugé que par les trades réels, au fil de l'eau (environ 220 trades de zone par
   an : la décision fixée à 150 trades arriverait vers fin 2027). Une possibilité sans effort pour l'utilisateur : que le
   bot enregistre lui-même chaque jour le delta de chaque minute, comme il le lit déjà en direct (non fait : à décider).
3. **Les vrais leviers restent ceux déjà trouvés** : un compte sans limite de temps (où l'avantage compte), une petite
   taille sur le compte financé, pas de zone les jours de la Fed.

## Partie E (25 octobre 2026) : ce que font les institutions, les chercheurs et les praticiens (règles fixées avant tout calcul)

### Demande de l'utilisateur

« Lance plusieurs agents en même temps qui repassent tout, y compris les portefeuilles des grands traders,
institutions, banques, hedge funds : qu'est-ce qui est efficace sur le NQ pour du scalping, hors la zone et le filtre
delta ? »

### Les 5 agents (rapports dans `agents/`)

| Agent | Angle | Conclusion |
|---|---|---|
| Flux institutionnels (`agents/flux_institutionnels.md`) | couverture gamma des teneurs de marché, 0DTE, ETF à levier, MOC, fonds de pension, CTA, dérive de nuit, Fed | aucun flux ne donne un scalping fréquent après frais ; Kurth, Eisler, Rej et Bouchaud (2026) montrent que, depuis 2009, le suivi de tendance de court terme ne rapporte plus rien sur les contrats à petit tick comme le NQ, parce que les teneurs de marché rapides neutralisent les flux prévisibles. Restent le régime gamma et quelques fenêtres de calendrier |
| Recherche académique (`agents/academique.md`) | prévisibilité intraday des futures d'indices, avance-retard, saisonnalités, apprentissage automatique, réplications | aucune règle directionnelle quotidienne ne tient après frais et après publication ; un apprentissage automatique sur le MNQ (2021-2025) ne bat pas le hasard ; ce qui reste crédible est événementiel (Fed, annonces) |
| Praticiens (`agents/praticiens.md`) | order flow, Market Profile, ICT, pivots, VWAP, initial balance, gaps, méthodes des prop firms | presque rien n'a de preuve indépendante ; la plupart des « statistiques NQ » vendues sont celles d'une marche aléatoire ; seules la règle des 80 % de Market Profile, le « Oops » de Larry Williams et la cassure des extrêmes de la nuit restent à tester |
| Fonds et HFT (`agents/fonds_hft.md`) | tenue de marché, arbitrage de latence, stat arb, CTA, données sur les day traders | ce que gagnent les pros en scalping demande des microsecondes et des frais 5 à 20 fois plus bas ; moins de 1 % des day traders gagnent de façon durable ; restent les primes autour d'événements programmés, tenues plusieurs heures |
| Audit de toute la recherche passée | tous les dossiers de recherche | inventaire et trous : niveaux multi-jours, calendrier jamais joué en intraday (FOMC), régime, pas d'options ni de carnet |

### Les 10 règles testées (paramètres tels que publiés ou fixés ici, sans réglage)

NQ, 1 contrat micro, gain au prix d'aujourd'hui (comme la machine), frais 1 $ + 1 tick par ordre. Minutes du NQ de la
séance 9 h 30 - 16 h depuis 2011 (même source que la machine) ; nuit : barres de 5 minutes du CFD (HistData), datées
du matin qui suit. Une séance n'est jouée que complète et hors jour de changement de contrat.

| # | Règle | Source |
|---|---|---|
| E1 | **Gamma, d'heure en heure** : à 10 h 30, 11 h 30, 12 h 30, 13 h 30, 14 h 30 et 15 h 30, r = rendement des 60 dernières minutes. Si le GEX du S&P 500 de la veille (SqueezeMetrics) est positif : position **contre** r ; s'il est négatif : **avec** r. Tenue 60 minutes (30 pour la dernière), sans stop | Dim, Eraker, Vilkov (2023-2024) ; Adams et al. (2025) ; Barbon et Buraschi |
| E1b | **Gamma en fin de séance** : à 15 h 30, r = clôture de la veille → 15 h 30 ; si GEX de la veille > 0, position contre r jusqu'à 16 h (sinon pas de trade : le cas « avec » est Baltussen, déjà testé) | Barbon, Beckmeyer, Buraschi, Moerke |
| E2 | **Conférence de presse de la Fed** : jours de réunion programmée avec conférence (2013 - 2018 : mars, juin, septembre, décembre ; depuis 2019 : toutes), r = 13 h 59 → 14 h 29 ; à 14 h 30, position **dans le sens** de r ; sortie à 15 h 30 | Gómez-Cram et Grotteria (JFE 2022) |
| E3 | **Retournement de l'annonce de la Fed** : toutes les réunions programmées depuis 2013 ; à 13 h 50, position **contre** le rendement des 24 h précédentes (13 h 50 la veille → 13 h 50) ; sortie à 16 h | Baglioni et Ribeiro (2022) |
| E4 | **Rééquilibrage 60/40 de fin de mois** : à la clôture de chacun des 5 derniers jours de séance du mois, w = 0,6 (1 + R_actions) / [0,6 (1 + R_actions) + 0,4 (1 + R_obligations)], rendements depuis la dernière clôture du mois précédent (SPY et IEF, clôtures de 16 h des ETF) ; séance suivante du NQ, de 9 h 30 à 16 h : vente si w > 0,6, achat si w < 0,6 | Harvey, Mazzoleni, Melone (NBER 2025) |
| E5 | **Avant les annonces** : la veille d'un rapport sur l'emploi (NFP, 8 h 30) ou d'un ISM manufacturier (10 h), achat à 18 h (réouverture) ; sortie à 8 h 30 (NFP) ou 9 h 20 (ISM, dernière barre de nuit). Dates : NFP = 3e vendredi après la semaine du 12 (règle du BLS) ; ISM = 1er jour de séance du mois | Hu, Pan, Wang, Zhu (JFE 2022) |
| E6 | **Dérive de nuit après une fin de séance vendeuse** : si le rendement de 15 h à 16 h de la veille est dans le tiers le plus bas des 252 séances précédentes, achat de 2 h à 3 h | Boyarchenko, Larsen, Whelan (RFS 2023) |
| E7 | **Règle des 80 % (Market Profile)** : profil TPO de la veille (13 périodes de 30 min, cases de 0,02 % de la clôture de la veille, value area de 70 % construite depuis le POC en ajoutant à chaque pas la case voisine la plus remplie, au-dessus en cas d'égalité). Si l'ouverture est hors de la value area et que deux périodes de 30 min consécutives clôturent dedans : position vers le bord opposé à la clôture de la 2e période (au plus tard 15 h 30) ; objectif = le bord opposé (ordre limite) ; stop au-delà de l'extrême des deux périodes (1 tick) ; sortie à 15 h 55 sinon ; 1 trade par jour | Dalton, *Mind Over Markets* |
| E8 | **« Oops » de Larry Williams** : ouverture sous le plus bas de la veille → achat stop au plus bas de la veille + 1 tick ; ouverture au-dessus du plus haut → vente stop au plus haut − 1 tick ; déclenchement jusqu'à 15 h 30 ; sortie à la clôture de 16 h, sans stop | Williams (1999) |
| E9 | **Cassure des extrêmes de la nuit** : plus haut et plus bas de la nuit (CFD, 18 h - 9 h 20), ramenés au future par le rapport à la dernière clôture de nuit appliqué à l'ouverture de 9 h 30 ; de 9 h 31 à 15 h, première minute qui clôture au-delà : position dans le sens de la cassure ; sortie à 15 h 55 ; 1 trade par jour ; pas de trade si l'ouverture est déjà hors du range | Osler (2005), Mahadzva (2026) |

Exécution : signal à la clôture d'une minute, entrée à l'ouverture de la minute suivante ; ordres stop remplis au
niveau du stop ou à l'ouverture si elle le dépasse ; objectif limite rempli seulement si le prix le traverse d'un tick ;
dans une même minute, stop avant objectif. Barres de 5 minutes pour la nuit (mêmes règles).

### Décision (fixée maintenant)

- Mesure : gains nets par séance où la règle trade ; t de leur moyenne.
- Périodes : depuis le début des données (2011 ; E2 et E3 : 2013 ; E4 : 2016 ; E1 : mai 2011, début du GEX) jusqu'à
  fin 2022, puis 2023 - fin des données. Aussi, pour information : depuis la publication de chaque source.
- Bruit : 40 jumeaux par permutation et 40 par signe (comme la partie A), sur les minutes du NQ et sur la nuit.
- **Retenue** (suivie dans le coffre de l'avenir, puis peut-être le robot, sur décision de l'utilisateur) : t sur toute
  la période ≥ 2,58 (Bonferroni, 10 tests, unilatéral 5 %), gain moyen positif sur les deux périodes, et t au-dessus de
  95 % des jumeaux de chaque bruit.
- **Intéressante** (coffre de l'avenir, argent virtuel) : t ≥ 1,65, positif sur les deux périodes, au-dessus de 90 %
  des jumeaux de chaque bruit.
- Les règles de nuit (E5, E6, E9 en partie) gardent la règle de réalisme de la nuit (CFD, pas de robot sans
  confirmation sur de vraies transactions).
- Ce qui n'est pas testé, et pourquoi : ICT « silver bullet » et FVG (aucune définition mécanique admise ; les tests
  publiés sont négatifs), pivots, bandes de VWAP, initial balance, comblement de gap (preuves nulles ou statistiques de
  marche aléatoire ; voisins de familles déjà testées), dérive pré-FOMC (morte depuis 2015), ETF à levier, MOC,
  0DTE, tenue de marché, arbitrage (données ou latence hors de portée).

### Résultats de la partie E (25 octobre 2026) : `resultats/e/partie_e.txt`

**Aucune des 10 règles n'est retenue, aucune n'est intéressante.** NQ, 1 MNQ au prix d'aujourd'hui, frais compris.

| Règle | Trades | t | Net par trade | ≤ 2022 | ≥ 2023 | Après publication | Bat le bruit | Verdict |
|---|---|---|---|---|---|---|---|---|
| E1 gamma d'heure en heure | 3 773 séances | **−3,92** | −32,5 $ | −3,70 | −1,40 | −0,50 | 2 % | non (les frais de 6 trades par jour écrasent tout) |
| E1b gamma en fin de séance | 3 432 | −1,48 | −4,0 $ | −2,74 | +1,74 | +0,79 | 25 % | non |
| E2 conférence de presse de la Fed | 70 | +1,10 | +75,8 $ | +0,68 | +1,06 | +0,14 | 85 % | non |
| E3 retournement de la Fed | 94 | +0,42 | +29,5 $ | +1,32 | −1,39 | −0,45 | 52 % | non |
| E4 rééquilibrage 60/40 | 569 | +1,24 | +37,6 $ | +1,40 | +0,01 | +0,44 | 95 % | non |
| E5 nuit avant NFP et ISM | 318 | +0,57 | +13,0 $ | +0,70 | −0,06 | +0,24 | 25 % | non |
| E6 dérive de 2 h à 3 h | 1 171 | **+2,75** | +9,5 $ | **+3,25** | **−0,26** | +0,86 | 95 % | non : morte depuis 2023 |
| E7 règle des 80 % | 885 | +0,35 | +3,2 $ | +0,61 | −0,47 | — | 78 % | non |
| E8 « Oops » de Williams | 1 001 | +1,16 | +20,0 $ | +1,02 | +0,57 | — | 92 % | non (sous 1,65) |
| E9 cassure des extrêmes de la nuit | 3 252 | +1,13 | +11,2 $ | +1,00 | +0,54 | — | 90 % | non (sous 1,65) |

- **E6 confirme ce que ses propres auteurs ont publié en 2026** : la dérive de nuit entre 2 h et 3 h existait (t 3,25
  jusqu'en 2022), puis a disparu (t −0,26 depuis 2023).
- **Le régime gamma (E1)** est la pire : changer de sens chaque heure coûte 6 allers-retours par jour, et le proxy GEX
  du S&P 500 ne donne rien.
- **E2, E8 et E9 sont légèrement positives sur les deux périodes** (t 1,1 à 1,2), mais pas plus que ce que donne un
  faux marché sur 10 : ce n'est pas assez pour en faire des candidates.
- Pour information : avec les 15 réunions de la Fed tombées un jour de changement de contrat, E2 fait t 0,57.
- Relecture indépendante arrêtée à la demande de l'utilisateur (économiser la limite de session) ; le code a passé les
  tests de non-regard vers le futur et une vérification à la main de trades E2, E3, E5 et E8.

## Partie F (25 octobre 2026) : les pistes encore inexplorées sur le NQ (règles fixées avant tout calcul)

Demande de l'utilisateur : « si aucune ne passe, cherche les pistes inexplorées sur le NQ ». Source : les trous listés
par l'agent d'audit (`agents/audit.md`) qui ont un mécanisme connu et des données disponibles. Même cadre que la partie
E (NQ depuis 2011, 1 MNQ au prix d'aujourd'hui, frais, exécution, séances complètes hors changement de contrat,
40 + 40 jumeaux de bruit). Les niveaux sur plusieurs jours ne sont calculés que si toutes les séances de référence sont
du même contrat que le jour (sinon pas de trade).

| # | Règle | Idée, source |
|---|---|---|
| F1 | **Cassure du plus haut ou du plus bas de la semaine précédente** (au moins 3 séances) : de 9 h 31 à 15 h, première minute qui clôture au-delà → position dans le sens de la cassure, sortie à 15 h 55 ; 1 trade par jour ; rien si l'ouverture est déjà au-delà | cascades de stops sur les niveaux évidents (Osler 2005) ; jamais testé au-delà de la veille |
| F2 | **Même règle avec le mois précédent** (au moins 15 séances) | idem |
| F3 | **Pivots de parquet, version tendance** : P = (H + B + C) / 3 de la veille, R1 = 2P − B, S1 = 2P − H ; première clôture au-dessus de R1 → achat, sous S1 → vente ; sortie 15 h 55 ; 1 trade par jour | pivots en usage « inversé » (thèse de Lund) ; usage classique déjà sans preuve |
| F4 | **« Turtle Soup » (Raschke et Connors 1995)** : plus bas des 20 séances précédentes, fait il y a au moins 4 séances ; si le prix passe dessous (d'un tick) puis une minute clôture au-dessus, achat à la minute suivante (au plus tard 15 h 30), stop au plus bas du jour − 1 tick, sortie à 16 h ; symétrique en vente | faux départ sur un extrême de 20 jours |
| F5 | **Retournement d'un grand mouvement à fort volume** (Campbell, Grossman, Wang 1993) : à 10 h, 10 h 30 … 15 h 30, r = rendement des 30 dernières minutes, V = volume des 30 minutes / moyenne de la même fenêtre sur les 14 séances complètes précédentes ; si V ≥ 1,5 et \|r\| dans les 20 % les plus forts de la même fenêtre sur les 60 séances complètes précédentes → position contre r pendant 30 minutes | un mouvement poussé par un afflux de liquidité se résorbe |
| F6 | **Régime du matin (ratio de variance de Lo et MacKinlay)** : à 12 h, VR = variance des rendements de 10 minutes / (10 × variance des rendements d'une minute) depuis 9 h 30 ; si VR > 1, position dans le sens du matin (9 h 30 → 12 h), sinon contre ; sortie 15 h 55 | journée de tendance ou de retour |
| F7 | **« Frog in the pan » (Da, Gurun, Warachka 2014)** : à 10 h 30, r = rendement depuis 9 h 30 ; ID = signe(r) × (part des minutes en baisse − part des minutes en hausse) ; si ID < 0 (mouvement fait de nombreux petits pas), position dans le sens de r, sortie 15 h 55 | l'information diffusée petit à petit est sous-estimée |
| F8 | **« Open-Drive » (Dalton)** : si pendant les 15 premières minutes le prix ne repasse jamais sous l'ouverture (d'un tick) et clôture au-dessus à 9 h 45 → achat ; symétrique en vente ; sortie 15 h 55 | type d'ouverture le plus « directionnel » de Market Profile |

**Décision** (comme la partie E, pour 8 tests) : **retenue** si t ≥ 2,50 (Bonferroni), positive avant et après 2023 et
au-dessus de 95 % des jumeaux de chaque bruit ; **intéressante** si t ≥ 1,65, positive sur les deux périodes et
au-dessus de 90 % des jumeaux. Une règle retenue ou intéressante va dans le coffre de l'avenir (argent virtuel).

**Ce qui reste hors de portée, et pourquoi** : murs d'options et 0DTE (intérêt ouvert payant), carnet d'ordres complet
(environ 100 $ par jour), indicateur TICK (pas d'historique), apprentissage non linéaire (un essai publié sur le MNQ en
2026 ne bat pas le hasard), avance d'autres actifs à la minute (aucune preuve publiée, test de 84 combinaisons déjà
pire que le hasard).

### Résultats de la partie F (25 octobre 2026) : `resultats/f/partie_f.txt`

**0 retenue, 1 intéressante (F3), 7 rejetées.** Tests sans regard vers le futur passés avant le calcul.

| Règle | Séances tradées | t | Net par trade | ≤ 2022 | ≥ 2023 | Bat le bruit | Verdict |
|---|---|---|---|---|---|---|---|
| F1 cassure de la semaine précédente | 787 | +0,20 | +3,6 $ | −0,22 | +0,96 | 57 % | non |
| F2 cassure du mois précédent | 173 | +1,13 | +39,6 $ | +0,63 | +1,35 | 95 % | non (sous 1,65) |
| F3 pivots R1/S1, tendance | 1 912 | **+1,69** | +20,6 $ | +1,83 | +0,21 | 98 % | **intéressante** |
| F4 Turtle Soup | 133 | −0,71 | −18,4 $ | −1,78 | +1,11 | 42 % | non |
| F5 retournement à fort volume | 1 343 | −1,41 | −11,3 $ | −1,63 | −0,02 | 8 % | non |
| F6 régime du matin | 3 840 | −1,22 | −8,3 $ | −0,74 | −1,16 | 28 % | non |
| F7 frog in the pan | 2 862 | +1,45 | +14,0 $ | +0,80 | +1,64 | 100 % | non (sous 1,65) |
| F8 Open-Drive | 138 | +1,20 | +41,5 $ | +1,05 | +0,76 | 78 % | non |

**Lecture honnête de F3** (descriptif, après le calcul) :
- elle passe le palier « intéressante » de justesse, mais **depuis 2023 elle est presque nulle** (t 0,21, +5 $ par trade) ;
- son gain vient surtout d'**une seule année** : 2022 fait +31 779 $ sur environ +39 000 $ au total (1 MNQ, 2011 - 2026) ;
  sans 2022, elle est à peu près plate ;
- elle est **corrélée à +0,35 avec la zone** : c'est la même idée (suivre une cassure intraday du NQ), pas un complément ;
- avec 8 tests, en trouver un au-dessus de 1,65 arrive souvent par hasard.

Conformément à la règle fixée, F3 entre dans le coffre de l'avenir en argent virtuel, sans attente particulière. Les
cassures (F2, F3, E9) et le « frog in the pan » (F7, suivre un mouvement fait de petits pas) sont toutes légèrement
positives : elles redisent ce que la zone exploite déjà, l'élan intraday du NQ.

## Partie G (25 octobre 2026) : l'élan intraday du NQ, là où la zone ne le prend pas (règles fixées avant tout calcul)

Demande de l'utilisateur : « creuse l'élan intraday sur le NQ ». Les réglages, sorties et filtres de la zone ont déjà
été épuisés (`zone_optimisation/`, 108 réglages ; voir plus haut). La seule question nouvelle : **l'élan existe-t-il là
où la zone est à plat ?** Si oui, c'est un complément ; sinon, la zone capte déjà tout ce qu'il y a.

**Moteur.** La zone sans filtre recalculée sur les minutes de la partie E (NQ depuis 2011), avec les mêmes règles que
le bot : σ_m = moyenne de \|clôture_m / ouverture − 1\| sur les 14 séances complètes précédentes ; bande haute =
max(ouverture, clôture de la veille du même contrat) × (1 + σ_m), bande basse = min(…) × (1 − σ_m) ; contrôles de 10 h à
15 h 30 ; sortie à un contrôle si le prix repasse max(bande, VWAP). **Contrôle obligatoire avant tout calcul** : elle doit
redonner les trades de la zone vérifiée (`delta_mesures/etude.py`) sur la période commune.

**Carte (descriptif).** À chaque contrôle, après la décision de la zone : sa position (en position, ou à plat) et
l'élan du jour e = (prix − ouverture) / (σ_m × ouverture). Gain des 30 minutes suivantes dans le sens de l'élan, par
case (zone en position ; zone à plat avec \|e\| < 0,5 ; à plat avec 0,5 ≤ \|e\| < 1 ; à plat avec \|e\| ≥ 1), avant et
après 2023.

**Les 3 règles testées** (exécution des parties E et F : entrée à l'ouverture de la minute suivante, 1 MNQ au prix
d'aujourd'hui, frais 1 $ + 1 tick par ordre) :

| # | Règle |
|---|---|
| G1 | À chaque contrôle (10 h - 15 h 30) où la zone est à plat et le prix à l'intérieur de sa bande avec \|e\| ≥ 0,5 : position dans le sens de l'élan pendant 30 minutes (jusqu'à 16 h pour le dernier) |
| G2 | Même condition, première fois de la journée seulement, tenue jusqu'à 15 h 55 |
| G3 | À 12 h, si la zone n'a pas tradé de la matinée et \|e\| ≥ 0,5 : position dans le sens de l'élan jusqu'à 15 h 55 (la tendance lente que la zone ne voit pas) |

**Décision** (comme E et F, pour 3 tests) : retenue si t ≥ 2,13 (Bonferroni), positive avant et après 2023 et au-dessus de
95 % des jumeaux de chaque bruit (40 + 40, la zone recalculée sur chaque jumeau) ; intéressante si t ≥ 1,65, positive sur
les deux périodes et au-dessus de 90 % des jumeaux. Pour information : corrélation avec la zone.

### Résultats de la partie G (25 octobre 2026) : `resultats/g/partie_g.txt`

- **Contrôle** : la zone recalculée redonne les 3 562 trades de la zone vérifiée, à 100 %.
- **Carte de l'élan** (gain moyen des 30 minutes suivantes dans le sens de l'élan du jour, avant frais) :

| État de la zone au contrôle | ≤ 2022 | ≥ 2023 |
|---|---|---|
| **en position** (prix hors de la bande) | **+1,05 pb, t 4,05** | **+1,16 pb, t 2,39** |
| à plat, élan faible (\|e\| < 0,5) | −0,38 pb, t −1,71 | +0,18 pb, t 0,44 |
| à plat, dans la bande, élan net (\|e\| ≥ 0,5) | +0,08 pb, t 0,34 | −0,34 pb, t −0,92 |

- **Règles** : G1 t −2,69 (−16,6 $ par séance), G2 t 0,71, G3 t 0,95 (et −0,22 depuis 2023). **Aucune retenue ni
  intéressante.**

**Ce que ça veut dire :** l'élan intraday du NQ n'existe que **quand le prix est sorti de la bande de bruit**, c'est-à-dire
exactement quand la zone est en position. À l'intérieur de la bande, il n'y a pas d'élan, ni avant ni après 2023. La zone
capte donc déjà tout l'élan intraday mesurable du NQ ; une autre stratégie d'élan ne ferait que la doubler (c'est aussi
ce que montraient les cassures F2, F3, E9 et le « frog in the pan », corrélés à la zone).

## Partie H (25 octobre 2026) : le banc des stratégies simples d'analyse technique (règles fixées avant tout calcul)

Demande de l'utilisateur : « basons-nous sur plus simple : ORB, breakout, analyse technique, des schémas qui se répètent ».
Ces familles ont déjà été testées (`tournoi/`, `tournoi2/`, `evolution3/`, machine de scalping : 0 survivante), mais
jusqu'en 2022 et avec les frais de l'époque. Ici : un seul banc, NQ 2011 - 2026, frais d'aujourd'hui, paramètres
standard, sans aucun réglage.

**Cadre** : comme les parties E à G (1 MNQ au prix d'aujourd'hui, 1 $ + 1 tick par ordre, signal à la clôture d'une
barre, entrée à l'ouverture suivante, stops dans l'ordre le plus défavorable, séances complètes hors changement de
contrat, à plat à 15 h 55 au plus tard, entrées jusqu'à 15 h 30, une position à la fois). Barres de 5 minutes de la séance
(9 h 30 - 16 h), indicateurs calculés en continu d'une séance à l'autre (graphique de séance).

| # | Stratégie (paramètres standard) |
|---|---|
| H1 | ORB 5 min (Zarattini et Aziz 2023) : sens de la 1re barre de 5 min, entrée 9 h 35, stop à l'autre extrême de la barre, objectif 10 fois le risque, sortie 15 h 55 |
| H2 | ORB 15 min : première clôture (1 min) au-delà du range 9 h 30 - 9 h 45, stop à l'autre bord, sortie 15 h 55 |
| H3 | ORB 30 min : même règle avec 9 h 30 - 10 h |
| H4 | ORB 60 min (initial balance) : même règle avec 9 h 30 - 10 h 30 |
| H5 | Cassure du plus haut ou du plus bas de la veille : première clôture au-delà, stop à l'ouverture du jour, sortie 15 h 55 |
| H6 | Donchian 20 / 10 (5 min) : clôture au-dessus du plus haut des 20 barres précédentes → achat ; sortie à la clôture sous le plus bas des 10 barres précédentes ; symétrique |
| H7 | Croisement EMA 9 / EMA 21 (5 min) : achat au croisement haussier, vente au baissier, retournement à chaque croisement |
| H8 | MACD (12, 26, 9) (5 min) : achat quand le MACD croise sa ligne de signal vers le haut, vente vers le bas, retournement |
| H9 | Bollinger (20, 2) retour à la moyenne (5 min) : clôture sous la bande basse → achat, sortie à la moyenne ; symétrique |
| H10 | Bollinger (20, 2) cassure (5 min) : clôture au-dessus de la bande haute → achat, sortie à la moyenne ; symétrique |
| H11 | RSI(2) intraday (5 min) : RSI < 10 → achat, sortie quand RSI > 70 ; RSI > 90 → vente, sortie quand RSI < 30 |
| H12 | Supertrend (10, 3) (5 min) : position dans le sens du Supertrend, retournement à chaque changement |
| H13 | Gap and go : écart d'ouverture d'au moins 0,5 % avec la clôture de la veille → position dans le sens de l'écart à 9 h 31, sortie 15 h 55 |
| H14 | Comblement de gap : même écart → position contre l'écart, objectif la clôture de la veille, sortie 15 h 55 |
| H15 | Jour intérieur : si le range de la veille est à l'intérieur de celui de l'avant-veille, première clôture au-delà du range de la veille → position dans ce sens, sortie 15 h 55 |
| H16 | NR7 + ORB 30 : si la veille a le plus petit range des 7 dernières séances, règle H3 |

**Décision** (comme E et F, pour 16 tests) : retenue si t ≥ 2,73 (Bonferroni), positive avant et après 2023, au-dessus de
95 % des jumeaux de chaque bruit (40 + 40) ; intéressante si t ≥ 1,65, positive sur les deux périodes, au-dessus de 90 %.
Pour information : la zone dans les mêmes conventions (partie G : t 4,21), et la corrélation de chaque stratégie avec
elle.

### Résultats de la partie H (25 octobre 2026) : `resultats/h/partie_h.txt`

**1 retenue (H12 Supertrend), 2 intéressantes (H1 ORB 5 min, H5 cassure de la veille), 13 rejetées.**

| Stratégie | t | Net par séance | ≤ 2022 | ≥ 2023 | Corr. zone | Verdict |
|---|---|---|---|---|---|---|
| H12 Supertrend 10-3 (5 min) | **+2,92** | +28,6 $ | +2,69 | +1,18 | +0,44 | **retenue** |
| H1 ORB 5 min (Zarattini-Aziz) | +2,25 | +12,9 $ | +2,42 | +0,19 | +0,39 | intéressante |
| H5 cassure de la veille | +1,97 | +9,9 $ | +1,32 | +1,68 | +0,50 | intéressante |
| H7 EMA 9 / 21 | +1,53 | +13,0 $ | +2,44 | −1,10 | +0,38 | non |
| H2, H3, H4 ORB 15 / 30 / 60 | +0,18 à +0,67 | | −0,61 à +0,10 | +0,94 à +1,45 | +0,53 à +0,55 | non |
| H10, H13, H15, H16 | +0,39 à +0,72 | | | | | non |
| H6 Donchian | −0,51 | | | | | non |
| H14 comblement de gap | −0,93 | −15,7 $ | | | | non |
| H8 MACD | −2,51 | −21,0 $ | | | | non |
| H11 RSI(2) intraday | −2,69 | −18,2 $ | | | | non |
| H9 Bollinger retour à la moyenne | −2,74 | −19,5 $ | | | | non |

**Vérifications de H12 après le calcul** (`verif_h12.py`) :
- le Supertrend du code est identique, à 100 %, à une version écrite indépendamment ;
- 2,4 allers-retours par séance en moyenne ; +35,9 $ avant frais et 7,3 $ de frais par séance ; positive 12 années sur 16
  (pertes en 2013, 2016 et 2017) ;
- **les frais expliquent l'écart avec `tournoi2/`** (t −0,57 en 2011 - 2022) : avec 1,5 point par aller-retour au prix de
  l'époque, 2011 - 2016 fait t −3,13 ; aux frais d'aujourd'hui, t +1,83. Depuis 2023, les deux conventions donnent
  presque la même chose (t +0,95 et +1,18) ;
- **avec la zone, il n'apporte rien** : sur 2011 - 2026, zone seule t 4,21, Supertrend seul 2,92, les deux ensemble 3,87 ;
  sur 2023 - 2026 : 2,16, 1,18 et 1,72 (corrélation +0,44 à +0,50). C'est une version plus faible du même élan ;
- sur l'ensemble des tests du jour (37 : parties E à H), le seuil de Bonferroni serait 2,99 : H12 (2,92) passerait
  juste en dessous.

**Ce qu'on retient** : sur le NQ, les stratégies simples de **suivi de tendance** sont positives (Supertrend, ORB 5 min,
cassure de la veille, EMA jusqu'en 2022) et celles de **retour à la moyenne** perdent toutes (Bollinger, RSI(2), MACD,
comblement de gap). C'est le même message que la partie G : le NQ en séance est un marché d'élan, et la zone est la
meilleure façon connue de le prendre. H12, H1 et H5 rejoignent le coffre de l'avenir en argent virtuel (avec F3) ; aucune
ne devrait s'ajouter à la zone sur un même compte, puisque la combinaison fait moins bien que la zone seule.

## Partie I (25 octobre 2026) : ajouter le Supertrend, l'ORB 5 min, la cassure de la veille ou les pivots à la zone, dans le challenge Bulenox 50K (règles fixées avant tout calcul)

Demande de l'utilisateur : backtester tout de suite ces ajouts dans le challenge Bulenox 50K où trade la zone, au lieu
d'attendre le suivi virtuel.

**Simulateur** (minute par minute, NQ 2011 - 2026, au prix d'aujourd'hui, frais 1 $ + 1 tick par ordre) :
- compte de 50 000 $, objectif 53 000 $ (le bot s'arrête dès +50 $ au-dessus) ; perte maximale de 2 500 $ sous le plus
  haut de fin de journée, bloquée à 50 100 $ ; perdu si le compte, au pire de chaque minute (plus bas pour un achat,
  plus haut pour une vente), touche ce plancher ; limite de perte du jour 1 000 $ (le bot coupe tout et s'arrête pour la
  journée) ; 30 jours calendaires ;
- zone sans filtre (pas d'historique du delta), 4 MNQ puis 6 MNQ les 5 dernières séances, pas de zone les jours de la Fed ;
- ajouts : H12 Supertrend 10-3, H1 ORB 5 min, H5 cassure de la veille, F3 pivots, avec les règles exactes des parties F
  et H, en parallèle de la zone sur le même compte ;
- départ à chaque séance de 2012 à fin septembre 2026 (et à part : départs 2023 - 2026).

**Contrôle du simulateur** : la zone seule doit donner une part de challenges validés proche de celle du moteur exact
de `zone_retour/` et `delta_mesures/` (44,8 % sur 2012 - 2026, 46,5 % sur 2023 - 2026, à ±5 points).

**Configurations** : zone seule ; zone + chaque ajout à 2 MNQ et à 4 MNQ ; zone + les quatre à 1 MNQ chacun.
**Témoins** (pour séparer l'avantage du simple surcroît de risque, qui aide parfois sur 30 jours) : zone seule plus
grosse (5 puis 7 MNQ, et 6 puis 8) ; zone + un ajout **sans avantage** de même volatilité (le Supertrend dont le sens de
chaque journée est tiré à pile ou face, 20 tirages), à 2 et 4 MNQ.

**Décision** : un ajout entre dans le bot seulement si, à la fois :
1. il valide au moins **3 points** de plus que la zone seule sur les départs 2012 - 2026 **et** sur 2023 - 2026 ;
2. il fait au moins 3 points de mieux que le témoin sans avantage de même taille, et que la zone plus grosse, sur 2012 - 2026 ;
3. il ne fait pas monter la part de challenges perdus de plus que la part validée gagnée.
Sinon, le bot ne change pas. Rappel : le filtre delta du bot n'est pas simulable sur 15 ans.

### Résultats de la partie I (25 octobre 2026) : `resultats/i/challenge_ajouts.txt`

Contrôles : les trades rejoués de chaque ajout redonnent exactement les gains du banc ; la zone seule valide 48,0 %
(2012 - 2026) et 49,9 % (2023 - 2026), contre 44,8 % et 46,5 % pour le moteur exact (écart dans la marge de ±5 points
fixée). 3 761 départs, dont 941 en 2023 - 2026.

| Configuration | Validé 2012-2026 | Perdu | Validé 2023-2026 | Perdu |
|---|---|---|---|---|
| **zone seule (4 puis 6 MNQ)** | **48,0 %** | **45,2 %** | **49,9 %** | **46,1 %** |
| témoin : zone 5 puis 7 / 6 puis 8 | 47,2 % / 48,5 % | 49,3 % / 49,6 % | 48,4 % / 48,2 % | 49,9 % / 50,3 % |
| + Supertrend 2 / 4 MNQ | 46,9 % / 46,4 % | 52,8 % / 53,6 % | 42,9 % / 43,6 % | 56,7 % / 56,4 % |
| + ORB 5 min 2 / 4 MNQ | 50,2 % / 49,4 % | 48,7 % / 50,5 % | 51,3 % / 49,9 % | 48,6 % / 50,1 % |
| + cassure de la veille 2 / 4 MNQ | 48,3 % / 50,2 % | 50,2 % / 49,6 % | 47,9 % / 50,7 % | 50,4 % / 49,0 % |
| + pivots 2 / 4 MNQ | 47,0 % / 46,7 % | 52,1 % / 53,3 % | 47,6 % / 46,4 % | 52,3 % / 53,6 % |
| + les quatre à 1 MNQ chacun | 48,5 % | 51,3 % | 46,7 % | 53,3 % |
| témoin : ajout sans avantage 2 / 4 MNQ | 41,3 % / 40,5 % | 57,9 % / 59,4 % | 39,9 % / 39,3 % | 59,8 % / 60,7 % |

**Décision fixée à l'avance : aucun ajout n'entre dans le bot.** Le meilleur (ORB 5 min à 2 MNQ) ne gagne que +2,2 et +1,4
points de challenges validés, sous les 3 exigés, et fait monter la part de comptes perdus (48,7 % contre 45,2 %). Le
Supertrend fait moins bien que la zone seule, surtout depuis 2023 (42,9 % contre 49,9 %).

- Les ajouts ont bien un avantage : un ajout sans avantage de même volatilité fait perdre 7 points (41 %). Mais dans un
  challenge de 30 jours, leur avantage ne compense pas le risque qu'ils ajoutent : ils remplacent surtout des
  challenges expirés par des challenges perdus.
- C'est le constat de `etude_large/` (partie D) : sur Bulenox 30 jours, la réussite tourne autour de 50 % quelle que soit
  la stratégie ; ajouter des stratégies ou grossir la taille n'y change presque rien.

### Résultats de la version 5 (25 octobre 2026) : `resultats/v5/selection.txt`, `resultats/v5/candidats.json`

252 machines (14 couples piste-marché × 3 sortes × 6 graines), environ 890 000 stratégies distinctes sur les vraies
données et 1,78 million sur les deux bruits. **Empreinte de la liste figée pour le coffre de l'avenir : `candidats.json`
sha256 `3aee9308e03cb6f526a7f1faaf05d065be881f2b773578ed58250bb847c61b0e`** (écrite le 25 octobre, avant le 1er novembre 2026).

| Couple | Admises aux trois conditions : vrai (6 graines) / bruits (12 graines) | Barrière du bruit | Candidates (t au contrôle 2023 - 2026) |
|---|---|---|---|
| B NQ | 113 / 69 | 2,76 | **3,28** (micro-compression, contre, ventes seules, 133 trades) et **2,81** (mouvement de 15 min, suivre, ventes seules, 104 trades) |
| B GC (or) | 51 / 2 | 2,00 | 2,07 (mouvement de 30 min, suivre, achats seuls) et 2,03 (série de 7 barres, suivre) |
| B CL (pétrole) | 9 / 6 | 2,06 | 2,30 (niveau rond franchi, suivre, ventes seules) |
| B RTY | 1 / 0 | 1,65 | 1,95 (pic de volume, suivre, achats seuls) |
| B ES, YM, 6E ; B2 BTC ; nuit (6 marchés) | — | 1,65 à 3,81 | aucune |

- **6 candidates, 0 panier candidat, 4 placebos suivis** (sur les 4 marchés qui ont une candidate). m = 6 : le seuil
  de « retenue » dans l'avenir sera t ≥ 2,39.
- Toutes les candidates sont **sans lien avec la zone** (corrélation de −0,07 à +0,03) : si l'une d'elles se
  confirmait, ce serait un vrai complément.
- **Nuit : rien.** Les bruits y produisent des scores plus hauts que le vrai (barrière 3,81 sur le NQ de nuit).
- Les paniers ne valent rien, comme en version 4 (NQ de jour : t −0,50).
- **À lire avec prudence** : ces candidates ont été choisies parmi des milliers d'admises sur 2023 - 2026, qui devient
  ainsi leur période de choix ; leur t au contrôle est gonflé par ce choix (la barrière du bruit corrige en partie). Elles
  tradent peu (30 à 55 trades par an) : même vraies, elles ne se confirmeront qu'en 2 à 4 ans de suivi. **Aucune n'entre
  dans le bot.**
- Suivi à partir du 2 novembre : le NQ est relevé chaque jour par le robot de `main` ; l'or, le pétrole et le Russell
  demandent un relevé des minutes de Yahoo au moins toutes les 4 semaines (outil à écrire, sur accord de l'utilisateur).

### Suivi virtuel (25 octobre 2026) : `suivi5.py`

Demande de l'utilisateur : passer les candidates en mode virtuel. Plutôt que de traduire le moteur dans le bot C# (qui ne
garde pas les 20 séances de volatilité minute par minute dont elles ont besoin, et qu'il vaut mieux ne pas toucher pendant
le challenge en cours), le suivi joue **le moteur de la recherche lui-même** sur les minutes du NQ que le robot de la zone
enregistre chaque jour sur `main`. Aucun ordre.
- Suivies : les 2 candidates NQ et les 2 placebos NQ de la version 5, H12, H1, H5 et F3. Or, pétrole, Russell : pas de
  relevé de minutes pour l'instant.
- **Contrôle** : sur janvier - septembre 2026, le suivi redonne les trades de la recherche à l'identique (mêmes entrées,
  sorties et gains) pour les 4 génomes.
- Aperçu sur les 20 séances jamais vues du 28 septembre au 23 octobre 2026 (pour information) : candidate 3,28 : 3 trades,
  −131 $ ; candidate 2,81 : aucun trade ; H12 +217 $, H1 +825 $, H5 +281 $, F3 +839 $ (1 MNQ). Bien trop tôt pour conclure.
- Lancement chaque jour de semaine par `workflow_suivi_scalping.yml`, à placer sur `main` avec l'accord de l'utilisateur ;
  résumé sur Telegram chaque samedi.

## Coffre du passé (26 octobre 2026) : les candidates NQ sur 2011 - 2016 (règle fixée avant tout calcul)

L'utilisateur ne veut pas attendre des années de suivi virtuel. Les minutes du NQ de **2011 à 2016** n'ont jamais servi à
la version 5 (entraînement à partir de 2017, choix sur 2023 - 2026) ni à la version 4 (données à partir de 2016,
entraînement à partir de 2017) : c'est un coffre intact, dans le passé, de 6 ans.

- **Testées** : les 2 candidates NQ de la version 5 (génomes et constantes figés de `candidats.json`), sur les minutes de
  la partie E (même fichier que la machine), séances de 2011-01-01 à 2016-12-31, mêmes règles d'exécution et de frais
  (frais d'aujourd'hui, gain au prix d'aujourd'hui).
- **Confirmée dans le passé** : gain moyen positif et t ≥ 1,96 (Bonferroni pour 2 tests, unilatéral 5 %), avec au moins
  100 trades. **Écartée** : t ≤ 0. Entre les deux : pas de conclusion.
- **Comparaisons publiées dans tous les cas** : les 2 placebos NQ (choisis sur bruit), et toutes les admises réelles du
  NQ de la version 5 (t médian sur 2011 - 2016, part au-dessus de 1,96) : si la sélection a du sens, les candidates
  doivent faire mieux que l'admise typique.
- Limite : 2011 - 2016 est un autre marché (NQ entre 2 000 et 5 000 points, moins liquide). Échouer là n'est pas une
  preuve absolue d'échec aujourd'hui ; réussir est une preuve forte.

### Résultat du coffre du passé (26 octobre 2026) : `resultats/v5/coffre_passe.txt`

| Stratégie | Trades 2011 - 2016 | Gain (1 MNQ) | t | Verdict |
|---|---|---|---|---|
| candidate NQ 3,28 (micro-compression, ventes) | 209 | −1 895 $ | **−1,33** | **écartée** |
| candidate NQ 2,81 (mouvement de 15 min, ventes) | 133 | +36 $ | +0,05 | pas de conclusion (rien) |
| placebo 1 (choisi sur bruit) | 151 | +1 126 $ | +0,56 | — |
| placebo 2 (choisi sur bruit) | 261 | +3 523 $ | +1,47 | — |
| toutes les admises réelles du NQ (9 436) | | | médiane −1,26 ; 19 % positives ; 0,5 % ≥ 1,96 | — |

**Les candidates NQ ne tiennent pas hors de leur période de choix.** La première perd sur 2011 - 2016, la seconde est à
zéro, et les deux placebos choisis sur bruit font mieux qu'elles : la sélection de la version 5 sur le NQ n'a donc trouvé
que du hasard. Elles ne seront ni mises dans le bot ni proposées pour l'argent réel ; le suivi virtuel n'a plus d'objet
pour elles. (L'or, le pétrole et le Russell n'ont pas de coffre du passé : leurs minutes commencent en 2016 - 2017.)
