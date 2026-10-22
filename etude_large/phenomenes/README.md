# Vague « phénomènes » : 4 pistes, 11 tests, pour ajouter une précision ou une source à la zone (règles fixées le 22 octobre 2026, avant tout calcul)

## Demande de l'utilisateur (22 octobre 2026)

« Réessayez » : relancer la recherche d'une précision ou d'une source qui s'ajoute à la zone de bruit filtrée par le
delta, après l'échec des 17 tests de `pistes/` et de la taille optimale (`taille/`). Données gratuites seulement,
futures CME seulement, à plat avant 16 h 59, bots permis.

## Comment les pistes ont été choisies

Trois chercheurs indépendants ont proposé 15 pistes, chacun sous un angle : les phénomènes récents de structure du
marché (concentration, résultats des méga-capitalisations, options à 0 jour, régime actions-obligations) ; l'information
croisée des autres marchés au moment du contrôle ; les phénomènes que la recherche n'a jamais regardés (forme du chemin,
nombres ronds, barres extrêmes, chiffres de 10 h, bitcoin du week-end). Le juge a fusionné les doublons, les a
confrontés aux dossiers proches (lus : `zone_sources/`, `tournoi7/`, `filtre_h1/`, `vague9/`, `sessions24/`,
`evolution2/`, `evolution3/`, `etude_large/README.md` parties A et B, `annonces/`, `pistes/`, `entree_tardive/` sur
`origin/claude/elegant-ptolemy-g94s8t`, `cerveau/savoir.json`), a ouvert chaque fichier de données, et a gardé
**4 pistes, 11 tests**. Aucun gain n'a été calculé pour faire ce choix.

## Règle commune (fixée maintenant)

- **Zone de référence V1** : `delta_mesures/etude.py` (`preparer`, `zone_jour`, `trades_zone`), sur les minutes du NQ
  de la recherche (`kb/intraday/donnees/nasdaq100_1min.csv.gz`, jusqu'au 25 sept. 2026) complétées par celles du robot
  (`zone/robot/nq_1min.csv.gz`). Séances complètes seulement, pas de zone les jours de la Fed (`fonds/fomc.py`
  `annonces()`), 1 MNQ. **Contrôle obligatoire avant tout gain** : le moteur redonne 3 572 trades et +10 721,25 points
  jusqu'au 19 octobre 2026 (`entree_tardive/`).
- **Trade écarté** par un filtre : il reste virtuel jusqu'à la sortie qu'aurait eue V1 et bloque toute entrée pendant ce
  temps, exactement comme le filtre delta de `Moteur.cs` (relance décochée).
- **Frais** : 1,5 point NQ et 0,9 point ES par aller-retour ; micros des autres marchés : 1 $ par ordre + 1 tick par
  côté.
- **Série de décision** : gain quotidien en $ pour 1 MNQ au niveau de prix du 20 octobre 2026, convention de
  `etude_large/partie_d.py` `chemins_zone` (points bruts × prix de référence ÷ ouverture du jour, moins 1,5 point par
  aller-retour, × 2 $), 0 les séances sans trade ou sans différence. Les points bruts sont publiés pour information.
- **Périodes** : exploration jusqu'au 30 décembre 2022 (début selon les données de chaque piste) ; coffre du 3 janvier
  2023 au 20 octobre 2026 (ou à la fin des données, indiquée pour chaque test). Le coffre n'est ouvert **qu'une fois**,
  après que les résultats d'exploration sont écrits dans `<dossier>/resultats.txt`.
- **Graine des placebos** : `numpy.random.default_rng(1)` dans chaque piste.
- **Critères de succès, tous exigés** :
  1. t net ≥ 2 en exploration **et** retenu par **Benjamini-Hochberg à 10 % sur les 11 tests de la vague** (p tiré du t
     d'exploration ; unilatéral dans le sens prédit, bilatéral pour les tests bilatéraux de la piste C) ;
  2. coffre : même signe, t net ≥ 1,5 ;
  3. le résultat réel bat au moins 95 % de ses placebos (définis pour chaque piste) ;
  4. pour une **précision de la zone** : Sharpe des séances (série de décision) plus haut que celui de la zone seule
     sur l'exploration **et** sur le coffre. Pour une **source** : corrélation quotidienne avec la zone < 0,3 en
     exploration, et Sharpe de zone + source (source ramenée au même écart-type quotidien que la zone en exploration)
     plus haut que la zone seule sur les deux périodes ;
  5. **challenges**, moteur de `etude_large/partie_d.py` (chemins minute par minute, plus hauts et plus bas compris),
     départs 2023 - 2026 : **Lucid Flex 50K à 1 MNQ** et **Bulenox 50K à 3 MNQ** (la version 30 jours, 4 puis 6 MNQ,
     est publiée pour information). Une règle passe sur un compte si elle y valide **au moins 2 points de plus** que la
     zone seule, **sans plus de 3 points de challenges perdus en plus**. Pour une source, la comparaison se fait à la
     fois contre la zone seule à la taille du compte et contre la zone seule à la même exposition maximale (taille de
     la zone + taille de la source). La règle est retenue si elle passe sur au moins un des deux comptes, et elle n'est
     activée que sur le ou les comptes où elle passe.
- Une règle retenue passe ensuite par une **contre-vérification adverse** (agents chargés de la réfuter : regard vers
  le futur, frais, erreurs de calcul), puis par le **robot en argent virtuel**, jamais directement en argent réel.
- À confirmer avant tout usage réel : les heures permises par chaque firme (Bulenox jusqu'à 16 h 59 ? Lucid jusqu'à
  16 h 45 ?) et les marchés lisibles en direct dans le flux Rithmic de la firme.

## Constat de données fait par le juge (fichiers ouverts, aucun gain regardé)

- **Minutes du NQ** : colonnes t,o,h,l,c,v,contrat, heure de New York, barres étiquetées par leur début, 9 h 30 -
  15 h 59. Ce sont les **prix bruts** du contrat du jour (2 238 points le 3 janvier 2011), non ajustés des échéances :
  les nombres ronds de la piste C ont donc un sens. Le contrat ne change jamais pendant une séance (4 041 séances
  vérifiées). Le fichier du robot s'arrête le 21 octobre 2026 à 13 h 27 (séance partielle) : le coffre finit le 20.
- **`kb/vague4/donnees/grandes.csv.gz`** : colonnes jour, ouverture, c30 … c390, valeur ; AAPL, AMZN, AVGO, COST, GOOGL,
  META, MSFT, NFLX, NVDA, TSLA, 2 701 séances chacune, du 4 janvier 2016 au 30 septembre 2026. Non ajusté des splits
  d'un jour à l'autre (NVDA, 10 juin 2024).
- **ETF Alpaca 5 minutes** (`donnees_libres/etf_5min/`) : colonnes t,o,h,l,c,v,n,vw, heure de New York, début de barre,
  du 4 janvier 2016 9 h 30 au 20 octobre 2026 15 h 55, 78 barres par séance pour QQQ, TLT, IEF, UUP (76), GLD. **VXX**
  commence le 18 janvier 2018 à 9 h 40 (prix ajustés des regroupements) ; d'après le chercheur, 19 barres par séance
  seulement en 2018 : il n'est utilisé qu'à partir de 2019.
- **HistData 5 minutes** (`kb/sessions24/annees/`) : colonnes t,o,h,l,c, en UTC. **audusd, usdjpy, eurusd et gbpusd
  s'arrêtent le 2 octobre 2026 à 20 h 55** (et non le 16 octobre) ; usdcad et usdchf (`donnees_libres/histdata_5min/`)
  vont jusqu'au 16 octobre.
- **`donnees_libres/histdata_5min/udxusd` n'est pas l'indice du dollar de 2012 à 2018** : médiane des clôtures 12 947
  en 2012, 17 682 en 2015, 25 034 en 2018, puis 97,15 en 2019. C'est le Dow Jones. **Conséquence pour `annonces/`** : de
  2012 à 2018, le « choc du dollar de 8 h 30 » était en fait un choc du Dow Jones avant l'ouverture. La conclusion (aucune
  règle) n'est pas changée par ce constat, mais la définition n'était pas celle annoncée ; à corriger si la piste des
  annonces de 8 h 30 est reprise. Ce fichier n'est utilisé nulle part dans cette vague.
- **Coinbase BTC 5 minutes** (`donnees_libres/crypto/btc_AAAA_5m.csv.gz`) : colonnes t,o,h,l,c,v, heure de New York
  (`crypto.py` convertit en America/New_York), début de barre, du 1er janvier 2017 au 20 octobre 2026 20 h 00.
- **Barres d'une heure ZN, 6A et 6J** (`kb/tournoi5/donnees/*_1h.csv.gz`) : jusqu'au 30 septembre 2026, pour les
  contrôles de la piste B.
- **Calendrier des résultats des entreprises : absent du disque.** Yahoo est bloqué depuis le conteneur (proxy : 403) et
  yfinance n'y est pas installé. Il doit être téléchargé **avant tout calcul** par le workflow GitHub
  `donnees-libres.yml` (gratuit), voir la piste A.

## Pistes écartées par le juge (pour mémoire)

- **E3, la zone en MES les soirs de résultats (piste P1)** : la différence avec la zone seule vaut exactement 0,8 fois
  celle de E1, jour par jour. Même t, mêmes placebos : ce n'est pas un test de plus. Publiée au challenge pour
  information seulement, avec la piste A.
- **E4, achat de 10 h à 15 h 59 les soirs de résultats (P1)** : prime d'annonce de la famille de la dérive avant la Fed,
  déjà refusée (fonds : Sharpe 0,34 ; protection : +113 $ par an, refusé). Il faudrait environ 16 pb par séance sur
  environ 220 séances pour un t de 2. Chance donnée par le chercheur : 4 %.
- **L2, 2 MNQ dans le sens de la réaction (P2)** : ajoute du risque sur environ 10 trades par an ; le renfort et les
  zones décalées ont montré que plus de risque fait baisser la réussite des challenges.
- **Options à 0 jour, expérience naturelle des échéances (P3)** : idée originale (le calendrier des échéances du SPX de
  2016 - 2022 sépare les lundis et mercredis des mardis et jeudis), mais : le traitement est dilué avant 2022 (environ
  5 à 20 % du volume du SPX) ; le NQ n'est pas le SPX et la date des échéances du lundi et du mercredi sur QQQ reste
  incertaine ; O1 et O2 mesurent une structure, pas un gain ; la règle O4 (« pas d'entrée après 12 h 30 ») est une
  condition d'heure déjà vue (vague9 avant ou après 12 h, zone_optimisation, gains par heure qui s'inversent d'une
  période à l'autre dans l'autopsie) ; environ 40 trades d'après-midi par an et par groupe. **En réserve** comme mesure
  de structure, sans règle.
- **Corrélation des méga-capitalisations (P5)** : confondue avec la volatilité, déjà épuisée (vague9, zone_optimisation,
  information n° 5 du ridge) ; C1 retire un tiers des séances ; la littérature porte sur l'horizon mensuel. Chance : 4 %.
- **La cassure du NQ jouée sur M6A, MBT, MGC (piste 5 croisée)** : tournoi7 a fait 0 sur 84, moins bien que le hasard ;
  les frais du MBT ont mangé un vrai élan (`crypto/`) ; une jambe qui gagne les mêmes jours que la zone est un renfort
  déguisé. Chance : 2 %.
- **Variantes croisées non retenues** : V1b (IAR brut), V1c (signe seul, écarte la moitié des trades), V1d (vote) ; V2b
  (AUD/JPY brut), V2c (dollar synthétique : UUP est déjà dans l'IAR), V2d ; V3b (VXX brut : à 30 minutes, c'est surtout
  −β fois le mouvement du NQ, donc le filtre P4 de `filtre_h1/`), V3c et V3d (coupent en deux une exploration de 4 ans) ;
  V4b (or : signe ambigu, exclu de l'IAR par son propre chercheur), V4c (TLT à signe fixe : le changement de régime de
  2021 - 2022 le casse), V4d ; T2 (2 MNQ, risque) ; T3 (IEF : même information que TLT, gardé en contrôle).
- **Retour après une très grosse barre d'une minute (G1 - G3)** : proche de la famille 14 d'evolution3 (pic de volume,
  « contrer = épuisement », battue par le bruit) et des pics de volume d'`orderflow/` ; les barres extrêmes se
  regroupent en 2020, 2022 et 2025, donc le résultat serait dominé par quelques crises ; les teneurs de marché du NQ
  ramènent sans doute le prix en quelques secondes, avant la minute d'attente. En réserve.
- **Chiffres de 10 h et calendrier ISM (A1 - A3)** : puissance trop faible. Seul le premier contrôle est touché, sur
  environ 25 jours par an, soit 5 à 8 trades par an pour A2 et A3. sessions24 G8 (choc de 10 h, 32 essais) n'a rien
  donné, et `annonces/` montre plutôt que la zone gagne un peu plus les jours de nouvelles. L'idée est reprise en
  **contrôle** de la piste D (la part du plus gros saut d'une minute voit justement la minute de 10 h 00).
- **Bitcoin du week-end vers le NQ du dimanche soir (B1 - B4)** : la famille de l'écart du week-end a échoué sur 7 marchés
  (sessions24 G11), la version MBT a été écartée par le juge de `pistes/` ; avec environ 300 week-ends, il faudrait
  environ 15 points par week-end pour un t de 2 ; heures du dimanche soir à vérifier dans chaque firme ; chevauche le
  RSI(2) de nuit. Chance : 3 %.
- **N4, « mur de prises de bénéfice » devant le prix d'entrée de la zone** : mécanisme opposé à la cascade de N1 et N2, avec
  un seuil de 0,1 σ choisi à la main ; ne pas compter deux fois la même idée. **N3** (niveaux de 500 seulement) passe en
  contrôle : 0 à 16 événements par an avant 2018.
- **F3 (régularité ET petit saut)** : simple conjonction de F1 et F2, la même information comptée deux fois.

## Piste A : Résultats des méga-capitalisations : séance d'attente le soir de la publication, séance d'information le lendemain (fusion de P1 et P2) (`resultats_megacaps/`, précision de la zone, 3 tests)

**Règle exacte**

Valeurs : AAPL, MSFT, NVDA, AMZN, GOOGL, META, AVGO, TSLA, COST, NFLX (les 10 de `grandes.csv.gz`). Les « six » : AAPL,
MSFT, NVDA, AMZN, GOOGL, META.

Calendrier, téléchargé **avant tout calcul** par une étape ajoutée à `.github/workflows/donnees-libres.yml` :
`yfinance.Ticker(x).get_earnings_dates(limit=100)` pour chaque valeur, enregistré dans
`donnees_libres/resultats/calendrier.csv` (valeur, horodatage en heure de New York). Pour chaque valeur et chaque
trimestre civil de 2016 à 2026 sans date Yahoo, la date de la détection par l'écart (ci-dessous) la remplace.

Détection par l'écart (secours et contrôle a) : g_t = ln(ouverture_{t+1} / c390_t) − ln(QQQ ouverture_{t+1} / QQQ
clôture_t), avec l'ouverture QQQ de la barre de 9 h 30 et la clôture QQQ de la barre de 15 h 55. Les nuits de split sont
retirées : |ln(ouverture_{t+1} / c390_t)| > 0,25 et à moins de 0,05 de −ln k, k ∈ {2, 3, 4, 5, 10, 20}. La séance t est
détectée si |g_t| ≥ 3 × la médiane des |g| des 250 séances précédentes et si |g_t| est le plus grand de [t − 30, t + 30]
séances.

Jour E : séance t complète et jouable où au moins une des 10 valeurs publie. Horodatage T (New York) : à 16 h 00 ou plus
tard, ou à 00 h 00 (heure inconnue : les 10 publient après la clôture) → séance du jour de T (la séance précédente si ce
jour n'est pas une séance) ; avant 9 h 30 → séance précédente ; de 9 h 30 à 15 h 59 → séance du jour de T.
Jour E lourd : une des six publie, ou au moins 2 des 10 publient pour la même séance.
Un jour de la Fed qui est aussi un jour E reste un jour de la Fed (aucune zone, différence nulle).

- **A1** : pas de zone les jours E.
- **A2** : pas de zone les jours E lourds.
- **A3 (lendemain)** : jour I = séance t dont la séance précédente est un jour E pour au moins une des six, et dont
  l'écart propre g (même formule, ouverture de t contre c390 de t − 1, nuits de split retirées) vérifie |g| ≥ 0,02 pour
  au moins une de ces publiantes. Sens d = signe de la somme des g des publiantes qui ont |g| ≥ 0,02 (connu à 9 h 30 ;
  somme nulle → pas un jour I). Les jours I, une entrée de zone de sens s ≠ d n'est pas prise (virtuelle et bloquante).

**Variantes**

3 tests : A1, A2, A3 (unilatéraux, sens prédit : la règle fait mieux que la zone seule). E3 (zone en MES les jours E)
publiée pour information au challenge.

**Données**

`donnees_libres/resultats/calendrier.csv` (à télécharger), `kb/vague4/donnees/grandes.csv.gz`,
`donnees_libres/etf_5min/QQQ.csv.gz`, minutes du NQ (recherche + robot), `kb/intraday/donnees/sp500_1min.csv.gz` pour
l'ES, `fonds/fomc.py`, `etude_large/partie_d.py`. Environ 33 jours E par an (prototype du chercheur : 337 soirées sur
2016 - 2026 par la détection), environ 18 jours E lourds, environ 25 à 30 jours I.
**Si le calendrier Yahoo ne peut pas être téléchargé, la piste A n'est que descriptive** : la détection par l'écart
regarde la réaction d'après la séance et jusqu'à 30 séances plus tard, ce qui est un regard vers le futur.

**Contrat et frais**

MNQ, 1,5 point par aller-retour.

**Périodes**

A1 et A2 : exploration du 4 janvier 2016 au 30 décembre 2022, coffre du 3 janvier 2023 au 20 octobre 2026.
A3 : même exploration, coffre jusqu'au 30 septembre 2026 (fin de `grandes.csv.gz`).

**Critères de succès et décision**

Série Δ = règle − zone seule (série de décision). Critères communs 1 à 5 (précision de la zone). Placebos :
- A1 et A2 : 1 000 tirages ; dans chaque année et chaque mois civil, les jours E (ou E lourds) sont remplacés par autant
  de séances jouables tirées au hasard parmi celles du même mois qui ne sont ni des jours E ni des jours de la Fed. Cela
  sépare le jour des résultats de la saison des résultats ;
- A3 : 1 000 tirages ; chaque jour I est remplacé par une séance non I de la même année dont l'écart d'ouverture du NQ,
  |ln(ouverture 9 h 30 / clôture 15 h 59 de la veille)|, est dans le même quintile (quintiles de l'année) que celui du
  jour I, avec d = signe de l'écart d'ouverture du NQ de ce jour. La règle réelle doit battre 95 % des tirages : sinon,
  ce n'est que la règle « dans le sens de l'écart » déjà vue (ridge, vague9).

**Contrôles**

a) Accord du calendrier Yahoo et de la détection sur 2016 - 2026 (une date de l'un retrouvée par l'autre à une séance
   près) : au moins 90 % dans les deux sens. Sinon, publier les dates en désaccord et la part de trimestres comblés par
   la détection ; la décision reste sur le calendrier défini plus haut.
b) Nombre de jours E, E lourds et I par an ; jours E qui sont aussi des jours de la Fed.
c) Résultats par valeur, par heure d'entrée, achats et ventes à part, sur 2016 - 2019, 2020 - 2022 et 2023 - 2026 (la
   concentration monte : l'effet devrait grandir).
d) Mécanisme, en exploration : amplitude (plus haut − plus bas de 10 h à 15 h 59) ÷ (σ de 15 h 59 × référence) les jours E
   et les jours placebo ; gain moyen de la zone les jours E.
e) A3 : gain moyen et t des trades pris contre d, sur chaque période ; |g| de 2 à 5 % séparé de |g| > 5 % ; jours I qui
   sont aussi des jours E.
f) ES en réplication (même signe attendu, plus faible), pour information.

**Pourquoi**

La seule règle qui a survécu dans toute la recherche est « pas de zone les jours de la Fed » : une séance d'attente
avant une annonce programmée, faite de fausses cassures. Les 10 plus grosses valeurs pèsent aujourd'hui environ la moitié
du Nasdaq-100 et publient toutes après 16 h ; une publication d'une grande valeur est devenue une nouvelle de marché
(Ogneva, Xia et Ye 2022 ; Christensen, Veliyev et Timmermann), et avant une annonce programmée les investisseurs
informés attendent (Chae 2005, Journal of Finance). C'est le même mécanisme, avec environ 4 fois plus de jours que la
Fed, sur un calendrier connu des semaines à l'avance. Le lendemain, l'ouverture contient une vraie nouvelle (le saut
d'une valeur qui pèse 5 à 10 % de l'indice) : une cassure dans le sens de la réaction a une cause connue, une cassure
contre elle plus souvent fausse (Chan 2003, JFE).
Contre : la règle de la Fed n'est qu'un petit plus ; retirer 13 % des séances coûte cher chez Bulenox si la zone y est
seulement neutre ; la dérive après résultats a disparu pour les grandes valeurs (Martineau 2022) ; A3 ne touche
qu'environ 10 trades par an. Chance a priori : environ 10 % pour A1 ou A2, 5 % pour A3.

**Pourquoi ce n'est pas déjà testé**

Aucun dossier n'a de calendrier des résultats : `pistes/heure_16h/resultats.txt`, contrôle d) : « aucun calendrier des
resultats des grandes valeurs dans les donnees gratuites du depot ». vague9 (29 conditions) et zone_optimisation
(33 conditions) n'ont que des conditions de marché et la Fed ; vague4 B ne regarde que le sens des 10 valeurs pendant la
séance ; `annonces/` ne porte que sur 8 h 30. Le placebo du même mois sépare le jour de la saison ; celui de l'écart de
même taille sépare A3 de la règle « dans le sens de l'écart » déjà vue.

## Piste B : Le mouvement simultané des autres marchés au contrôle : la cassure est-elle suivie par le risque global ? (fusion des pistes croisées 1 à 4 et de P4) (`confirmation_croisee/`, précision de la zone, 4 tests)

**Règle exacte**

Au contrôle τ (10 h 00 … 15 h 30) où V1 entre dans le sens s (+1 achat, −1 vente).
- Prix d'un marché X à l'instant t : P_X(t) = clôture de la barre de 5 minutes qui finit à t (barre étiquetée t − 5 min,
  début de barre). Pour t = 9 h 30 : ouverture de la barre de 9 h 30. Si cette barre manque et que la dernière barre
  disponible finit plus de 10 minutes avant t, X est absent à ce contrôle. HistData : UTC converti en
  America/New_York avec zoneinfo.
- r_X = ln(P_X(τ) / P_X(τ − 30 min)). r_NQ = ln(P_NQ(τ) / P_NQ(τ − 30 min)), avec P_NQ(t) = clôture de la minute
  étiquetée t − 1 min, et P_NQ(9 h 30) = ouverture de la minute de 9 h 30.
- Fenêtres de référence : les 720 fenêtres (12 contrôles × 60 séances complètes précédant le jour) où X est présent ; il
  en faut au moins 300, sinon X est absent ce jour-là. Sur ces fenêtres : régression des moindres carrés r_X = a + β·r_NQ,
  résidu ε, et ρ = corrélation de r_X et r_NQ.
- z_X résiduel = (r_X − a − β·r_NQ) ÷ écart-type de ε ; z_X brut = r_X ÷ écart-type de r_X.
- Signes fixés avant les données, pour un achat du NQ : VXX −1 ; UUP −1 ; AUD/JPY +1 ; bitcoin +1 ; TLT : e = signe(ρ)
  si |ρ| ≥ 0,10, sinon le TLT n'est pas compté (régime indécis).
- AUD/JPY : ln P = ln(AUDUSD) + ln(USDJPY), clôtures HistData. Contrôle d'heure : pour chaque jour, on prend la séance
  complète précédente et on cherche le décalage δ ∈ {−60, 0, +60} minutes qui maximise la corrélation des 78 rendements
  de 5 minutes (9 h 30 - 16 h) de usatechidxusd avec ceux du NQ ; si δ ≠ 0, les marchés HistData sont absents ce jour-là.
- VXX : seulement à partir du 2 janvier 2019.
- Score du trade et seuil : q = 20e centile du score sur toutes les entrées de V1 sans filtre des 252 séances complètes
  précédentes où le score existe ; tant qu'il y en a moins de 100, q = −0,84. **Le trade est écarté si score ≤ q** ; il
  est gardé si le score n'existe pas (marché absent).

Les 4 tests :
- **B1, indice d'appétit pour le risque** : IAR = moyenne de e_X·z_X résiduel sur VXX, UUP, AUD/JPY, bitcoin et TLT
  présents (et comptés) ; il en faut au moins 3, sinon le trade est gardé. Score = s·IAR.
- **B2, AUD/JPY seul** : score = s·z résiduel de l'AUD/JPY.
- **B3, VXX seul** : score = −s·z résiduel du VXX (pour un achat, un VIX plus bas que son lien habituel avec le prix).
- **B4, TLT au signe du régime** : score = s·e·z brut du TLT ; gardé si e = 0.

**Variantes**

4 tests, unilatéraux (sens prédit : les trades écartés sont moins bons, Δ > 0).

**Données**

`donnees_libres/etf_5min/` VXX, UUP, TLT, IEF (contrôle) ; `kb/sessions24/annees/` audusd, usdjpy, usatechidxusd (UTC) ;
`donnees_libres/crypto/btc_AAAA_5m.csv.gz` (New York) ; minutes du NQ ; `kb/tournoi5/donnees/` ZN, 6A, 6J en barres
d'une heure (contrôles) ; vrai delta P1 (`kb/orderflow/donnees/`) et P2 (`kb/filtre_h1/donnees_rithmic/`), descriptif.
Pièges : VXX clairsemé en 2018 ; HistData décalé certaines semaines (d'où le contrôle d'heure) ; udxusd non utilisé ;
HistData change jusqu'au 2 octobre 2026 seulement.

**Contrat et frais**

MNQ, 1,5 point par aller-retour (la zone ne change pas, le filtre retire seulement des trades).

**Périodes**

- B1 : exploration du 4 janvier 2016 (61e séance) au 30 décembre 2022 ; coffre 2023 → 20 octobre 2026 (AUD/JPY absent
  après le 2 octobre 2026).
- B2 : exploration 2012 (61e séance) - 2022 ; coffre 2023 → 2 octobre 2026.
- B3 : exploration du 2 janvier 2019 (61e séance) au 30 décembre 2022 ; coffre 2023 → 20 octobre 2026.
- B4 : exploration 2016 (61e séance) - 2022 ; coffre 2023 → 20 octobre 2026. Le régime change au milieu de
  l'exploration (ρ surtout négatif en 2016 - 2020, positif depuis), ce qui teste vraiment la règle de signe.

**Critères de succès et décision**

Série Δ = zone filtrée − V1 (série de décision). Critères communs 1 à 5 (précision de la zone), plus :
- placebo : 200 tirages ; pour chaque entrée, le score est remplacé par celui du même contrôle τ d'une autre séance tirée
  au hasard dans la même année (X présent), comparé au même seuil q que le vrai jour ;
- jumeau NQ : la même règle avec score = s·r_NQ ÷ écart-type de r_NQ sur les 720 fenêtres (version continue du filtre P4
  de `filtre_h1/`) doit faire moins bien que le test sur les deux périodes. Sinon, l'information vient du NQ lui-même.

**Contrôles**

a) Part des trades écartés (attendue autour de 20 %), par année.
b) Le bot lirait en direct les futures, pas les ETF ni HistData : accord de signe des rendements d'une heure (10 h -
   16 h, 2016 → 30 septembre 2026) TLT contre ZN, et AUD/JPY HistData contre 6A ÷ 6J, au moins 90 %. En dessous, le test
   correspondant n'est que descriptif. Le VXX et l'UUP ne sont pas des produits CME : il faudrait les lire par l'API
   gratuite d'Alpaca (à vérifier) ; c'est écrit à côté du résultat de B1 et B3.
c) B4 et B1 : Δ séparé sur les jours où ρ_TLT < 0 et ρ_TLT > 0 ; pour information, B4 avec e fixé à −1 puis à +1, et avec
   l'IEF à la place du TLT.
d) Achats et ventes à part ; résultats par heure du contrôle ; jours de chiffres de 8 h 30 à part.
e) Accord avec le vrai filtre delta sur les 99 trades de P1 et les 7 de P2 (descriptif).
f) ES en réplication, pour information.

**Pourquoi**

Un mouvement qui vient d'une information macro (l'appétit pour le risque) se voit en même temps sur plusieurs marchés et
dure ; un mouvement qui vient de la liquidité reste isolé et se retourne plus souvent (Grossman et Miller 1988 ;
Campbell, Grossman et Wang 1993 ; Llorente et al. 2002). Le change de portage (Brunnermeier, Nagel et Pedersen 2008 ;
Ranaldo et Söderlind 2010), le VIX (Whaley 2000 ; Bekaert et Wu 2000) et les taux (Campbell, Sunderam et Viceira 2017 ;
Baele, Bekaert et Inghelbrecht 2010) ont leurs propres acteurs. La zone perd sur les fausses cassures : une cassure que
ni la peur, ni le change, ni les taux ne suivent pendant la même demi-heure est plus souvent fausse. Le résidu retire ce
que le NQ dit de lui-même, et le jumeau NQ le vérifie. C'est la seule information jamais regardée qui soit à la fois
simultanée au contrôle et venue d'autres classes d'actifs, et l'AUD/JPY donne 11 ans d'exploration.
Contre : S1 (confirmation par l'ES) aide avant 2023 et nuit depuis ; depuis 2023, les meilleures journées sont souvent
des nouvelles propres à la tech (IA, Nvidia) que le dollar et l'AUD ne suivent pas ; le résidu d'un marché sur 30
minutes est bruité ; ρ sur 60 séances est bruité au moment même du changement de régime. Chance a priori : environ 5 %
par test.

**Pourquoi ce n'est pas déjà testé**

`zone_sources/` S1 n'interrogeait que l'ES (corrélation ≈ 0,9 avec le NQ). `filtre_h1/` P4 est le mouvement du NQ
lui-même (t 1,62, non confirmé) : c'est le jumeau. `tournoi7/` demandait à une fenêtre fixe de 9 h 30 - 10 h 30 de
prédire seule le reste de la séance d'un autre marché ; ZN, dollar et bitcoin y étaient prévus mais jamais lancés, et
aucune source n'y trie des cassures déjà décidées par la zone. Le ridge (`etude_large/` B) n'a que l'ES et le VIX de la
veille ; vague9, zone_optimisation, tournoi10 et evolution2 n'ont que des niveaux du VIX de la veille. Aucun essai n'a
lu le mouvement simultané du VIX, du change, des taux ou du bitcoin au contrôle de la zone, ni pris un signe qui suit le
régime actions-obligations.

## Piste C : Nombres ronds du NQ : cascade d'ordres stop après le premier franchissement du jour (Osler), ou aimant des prix d'exercice (`nombres_ronds/`, source indépendante, 2 tests)

**Règle exacte**

Prix bruts du contrat du jour, minutes de 9 h 30 à 15 h 59 (étiquetées par leur début). Niveaux L = k × 100 points.
- Franchissement haussier de L à la minute m : C_{m−1} ≤ L < C_m, et aucune clôture de la séance avant m n'est au-dessus
  de L (premier passage du jour au-dessus de ce niveau). Franchissement baissier : C_{m−1} ≥ L > C_m, et aucune clôture
  avant m n'est au-dessous de L. Si une minute franchit plusieurs niveaux, c'est un seul événement.
- Minutes d'événement : de 9 h 45 à 15 h 44 pour N1, de 9 h 45 à 15 h 29 pour N2.
- Un seul trade ouvert à la fois : pendant un trade, les franchissements sont ignorés.
- Trade : 1 MNQ dans le sens du franchissement, entrée à C_m, sortie à C_{m+15} (**N1**) ou à C_{m+30} (**N2**).
- Exclusions : jours de la Fed ; séances incomplètes.
- **Test bilatéral** : si le gain brut moyen d'exploration est négatif (retour, aimant), le test devient « contre le
  franchissement » : gain = −brut − frais, mêmes critères, p bilatéral.

**Variantes**

2 tests : N1 (15 minutes), N2 (30 minutes), niveaux de 100 points.

**Données**

Minutes du NQ 2011 → 20 octobre 2026 (recherche + robot), prix bruts vérifiés (voir le constat de données). Comptage du
chercheur, sans aucun gain : 43 à 96 premiers franchissements par an de 2011 à 2017, 146 à 514 de 2018 à 2022, 342 / 430 /
548 / 461 de 2023 à 2026, soit environ 1 900 événements en exploration et 1 780 au coffre. ES minute
(`sp500_1min.csv.gz`, jusqu'au 25 septembre 2026) en réplication sur ses niveaux de 50 points. Zone : `delta_mesures/`.

**Contrat et frais**

MNQ, 1,5 point par aller-retour ; sensibilité à 3 points. MES pour la réplication, 0,9 point.

**Périodes**

Exploration 2011 - 2022 (surtout 2018 - 2022) ; coffre 3 janvier 2023 → 20 octobre 2026. La règle n'a jamais été
calculée : toutes ses années sont jamais vues.

**Critères de succès et décision**

Critères communs 1 à 5 (source). Placebo : la même règle sur les 99 grilles décalées L = k × 100 + δ, δ = 1 … 99 points ;
la grille ronde doit être plus extrême, du côté gagnant, qu'au moins 95 des 99 grilles, en exploration **et** au coffre.
Elles ont les mêmes franchissements « génériques » (élan ou retour après n'importe quel niveau) : seule la grille ronde
porte les ordres. En plus : t > 0 à 3 points de frais. Au challenge : zone + source à la même taille (1 + 1 MNQ chez
Lucid, 3 + 3 MNQ chez Bulenox), positions additionnées minute par minute.

**Contrôles**

a) Recompter les événements par année (chiffres du chercheur ci-dessus).
b) N3, niveaux de 500 seulement, sortie à 15 minutes, pour information (dose : plus rond, plus d'ordres).
c) 2011 - 2017 contre 2018 - 2022 ; avant et après 2022 (options à 0 jour) ; achats et ventes à part ; par heure.
d) ES en réplication sur des niveaux de 50 points.
e) Événements qui tombent pendant une position de zone, publiés à part ; pire trade publié.

**Pourquoi**

Osler (2003, Journal of Finance ; 2005) a travaillé sur environ 9 700 vrais ordres d'une grande banque : les prises de
bénéfice s'accumulent au nombre rond, les ordres stop juste au-delà, et franchir le nombre rond déclenche une cascade
qui accélère le mouvement. Sur le NQ, les niveaux de 100 points sont ceux de tous les graphiques et de tous les traders
de prop firms. À l'inverse, les prix d'exercice des options sont aussi aux nombres ronds, et la couverture des teneurs de
marché peut coller le prix au niveau (Golez et Jackwerth 2012) : d'où le test bilatéral. Les niveaux sont fixés par
l'arithmétique, pas par le prix passé, et le placebo des grilles décalées isole l'effet « rond » de l'élan générique.
Aucun paramètre réglé, beaucoup d'événements depuis 2018, des trades courts peu liés à la zone.
Contre : preuves faibles et contradictoires sur les indices (Donaldson et Kim 1993 ; Ley et Varian 1994) ; le NQ est
dominé par des algorithmes qui connaissent ces niveaux ; l'effet d'Osler se compte en minutes et en quelques pb, près
des frais ; presque aucun événement avant 2018. Chance a priori : environ 5 %.

**Pourquoi ce n'est pas déjà testé**

Aucune trace de « nombre rond », « niveau rond » ou « Osler » dans la recherche ni dans le dépôt (cherché). Les niveaux
déjà testés viennent tous du prix passé : cassure de la veille (tournoi 1), niveaux et balayages de la veille
(evolution3), range de la nuit (tournoi 4, zone_sources S5), profil de volume (orderflow, evolution2 P1 - P3), murs
d'options (evolution2 W1 - W2). Aucun ne pouvait séparer l'effet du niveau de l'élan générique après un franchissement.

## Piste D : Forme de la cassure : chemin régulier ou saut d'un coup (« la grenouille dans la casserole » appliquée à la séance) (`forme_cassure/`, précision de la zone, 2 tests)

**Règle exacte**

À chaque entrée de V1 au contrôle d'indice m (minute étiquetée 9 h 30 + m, C_m sa clôture), de sens s :
- r_i = C_i − C_{i−1} pour i = m − 29 … m (30 variations ; au contrôle de 10 h 00, de la minute de 9 h 31 à celle de
  10 h 00, avec C_0 = clôture de la minute de 9 h 30) ;
- n+ = nombre de i avec s·r_i > 0 ; n− = nombre avec s·r_i < 0 ; M = s·(C_m − C_{m−30}) ;
- ID = signe(M) × (n− − n+) / 30 (définition de Da, Gurun et Warachka : plus ID est bas, plus le chemin est régulier) ;
- J = max_i |r_i| ÷ Σ_i |r_i| (part du plus gros saut d'une minute ; J = 1 si la somme est nulle).
Seuils, passé seulement : médiane de ID et 80e centile de J sur toutes les entrées de V1 sans filtre des 252 séances
complètes précédentes ; s'il y en a moins de 100, aucun filtre ce jour-là.
- **F1** : l'entrée n'est gardée que si ID ≤ médiane (cassure régulière).
- **F2** : l'entrée est écartée si J ≥ 80e centile (cassure faite d'un seul saut).
Trade écarté : virtuel et bloquant.

**Variantes**

2 tests, unilatéraux (sens prédit : Δ > 0).

**Données**

Minutes du NQ 2011 → 20 octobre 2026 (recherche + robot) ; moteur `delta_mesures/etude.py` ; ES minute en réplication ;
vrai delta P1 (Databento) et P2 (Rithmic), descriptif ; `delta_mesures/trades.csv` (99 trades de P1). Environ 2 800
trades en exploration et 800 au coffre.

**Contrat et frais**

MNQ, 1,5 point par aller-retour.

**Périodes**

Exploration de 2012 (premier jour avec 100 entrées dans les 252 séances précédentes) au 30 décembre 2022 ; coffre
3 janvier 2023 → 20 octobre 2026.

**Critères de succès et décision**

Série Δ = zone filtrée − V1. Critères communs 1 à 5 (précision de la zone), plus : au moins 40 % des trades gardés.
Placebo : 200 filtres au hasard qui écartent, chaque année, la même part des entrées que la règle réelle, avec le même
blocage.

**Contrôles**

a) Corrélation de ID et de J avec le vrai delta des 30 minutes (D30) sur les 99 trades de P1 et les 7 de P2.
b) Corrélation de ID avec l'approximation P1 de `filtre_h1/` (volume × sens de la bougie) et accord de décision avec le
   filtre P4 (sens du mouvement des 30 minutes) : F1 ne doit pas être ce filtre-là. Les deux ont échoué (t 0,39 et
   1,62) ; si F1 prend la même décision que P1 ou P4 dans plus de 80 % des trades, c'est écrit à côté du résultat.
c) Achats et ventes à part ; par heure d'entrée (le 80e centile de J est commun à toutes les heures : publier la part des
   entrées de 10 h écartées par F2).
d) Chiffres de 10 h : part des entrées de 10 h écartées par F2 les 1er et 3e jours de séance du mois (ISM) contre les
   autres jours, et gain de ces entrées (description de l'idée A1 - A3 écartée).
e) ES en réplication (même signe exigé pour en parler).

**Pourquoi**

Da, Gurun et Warachka (2014, Review of Financial Studies) : une information qui arrive par petites touches régulières
passe inaperçue et la tendance continue ; une information qui arrive d'un coup est vite intégrée et l'élan s'arrête.
Transposé à la séance : une cassure faite de 30 minutes régulières dans le sens du trade (jour de tendance, le terrain
où la zone gagne) devrait mieux tenir qu'une cassure faite d'une ou deux minutes géantes, souvent une nouvelle déjà
digérée (l'entrée de 10 h 00 tombe sur la minute des chiffres de 10 h). Deux nombres calculés sur les 30 barres déjà en
mémoire dans `Moteur.cs`, aucune donnée à acheter, une bonne puissance, des seuils fixés d'avance.
Contre : l'effet n'a été montré qu'à l'échelle du mois ; les approximations du delta par les bougies (`filtre_h1/` P1 à
P3, proches de ID) n'ont rien donné ; toutes les conditions de la vague 9 ont échoué depuis 2023 ; le filtre delta capte
peut-être déjà la même information. Chance a priori : environ 6 % (le chercheur disait 8 % ; le juge baisse à cause de
la proximité de `filtre_h1/` P1 - P3).

**Pourquoi ce n'est pas déjà testé**

`filtre_h1/` P4 regarde le sens du mouvement des 30 minutes, P1 - P3 un delta approché par le volume et le sens des
bougies, avec des filtres de signe qui écartent 9 à 16 % des trades : ni la régularité du chemin rangée sur un an, ni la
part du plus gros saut. `entree_tardive/` L1 regarde la taille du dépassement de la limite ; le ridge
(`etude_large/` B), la force de la cassure ; evolution3 (famille 14), les pics de volume en 5 minutes. Les 29 conditions
de la vague 9 et les 33 de zone_optimisation ne portent pas sur la forme du chemin. Aucune occurrence de « frog »,
« grenouille », « part du plus gros saut » dans la recherche (cherché).

## Les 11 tests de la vague (Benjamini-Hochberg à 10 % sur l'ensemble)

| # | Piste | Test | Type | Sens du test | Exploration | Coffre |
|---|---|---|---|---|---|---|
| 1 | A | A1 pas de zone les soirs de résultats des 10 valeurs | précision | unilatéral | 2016 - 2022 | 2023 → 20 oct. 2026 |
| 2 | A | A2 pas de zone les soirs « lourds » | précision | unilatéral | 2016 - 2022 | 2023 → 20 oct. 2026 |
| 3 | A | A3 lendemain : zone seulement dans le sens de la réaction | précision | unilatéral | 2016 - 2022 | 2023 → 30 sept. 2026 |
| 4 | B | B1 indice d'appétit pour le risque (5 marchés, résidus) | précision | unilatéral | 2016 - 2022 | 2023 → 20 oct. 2026 |
| 5 | B | B2 AUD/JPY résiduel | précision | unilatéral | 2012 - 2022 | 2023 → 2 oct. 2026 |
| 6 | B | B3 VXX résiduel | précision | unilatéral | 2019 - 2022 | 2023 → 20 oct. 2026 |
| 7 | B | B4 TLT au signe du régime | précision | unilatéral | 2016 - 2022 | 2023 → 20 oct. 2026 |
| 8 | C | N1 premier franchissement d'un niveau de 100, 15 minutes | source | bilatéral | 2011 - 2022 | 2023 → 20 oct. 2026 |
| 9 | C | N2 la même chose, 30 minutes | source | bilatéral | 2011 - 2022 | 2023 → 20 oct. 2026 |
| 10 | D | F1 cassure régulière seulement (ID ≤ médiane) | précision | unilatéral | 2012 - 2022 | 2023 → 20 oct. 2026 |
| 11 | D | F2 pas de cassure faite d'un seul saut (J < 80e centile) | précision | unilatéral | 2012 - 2022 | 2023 → 20 oct. 2026 |

Fichiers attendus : `<dossier>/etude.py` → `<dossier>/resultats.txt`, l'exploration écrite avant l'ouverture du coffre.
