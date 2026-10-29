# Méthodes de scalping des praticiens (prop firms, communautés, ICT, Market Profile, order flow) : ce qui est vérifié

Agent « praticiens », 25 octobre 2026. Angle : méthodes enseignées par les traders, les prop firms et la communauté pour
scalper le NQ, et preuves indépendantes disponibles.

## 0. Limites de ce rapport (à lire d'abord)

- Dans cette session, WebFetch et curl étaient bloqués pour presque tous les sites (SSRN, arXiv, Quantpedia,
  QuantifiedStrategies, Concretum, Oxfordstrat, TheChartist : refus du proxy). Tous les chiffres viennent des
  résumés du moteur de recherche. Je n'ai pas pu relire les textes intégraux. Les chiffres marqués « (non vérifié) »
  sont à confirmer à la source avant usage.
- Le quota de recherches web a été épuisé en fin de travail. Une référence (Barber et al.) est donc citée de mémoire et
  marquée comme telle.
- Calcul personnel (léger) : deux petites simulations de marche aléatoire (scripts dans
  `/tmp/claude-0/-home-user-scalping-telegram-bot/4861520c-7c70-542c-a1db-763e9dd91dac/scratchpad/agents/sim/`)
  pour donner le **taux de base sans aucun avantage** de statistiques très citées (initial balance, comblement de gap,
  règle des 80 %). C'est la référence à battre : une « probabilité de 80 % » ne vaut rien si le hasard donne déjà
  80 %.

## 1. Verdict global

1. **Presque rien de ce qu'enseignent les communautés n'a de preuve indépendante après frais.** ICT / smart money,
   footprint, absorption, divergence de delta, « opening drive », « first pullback », pivots, bandes de VWAP : aucune
   étude sérieuse ne montre un gain net. Les seuls tests systématiques trouvés sont négatifs ou insignifiants.
2. **Les seules versions « vérifiées » des méthodes de Bear Bull Traders sont les articles d'Andrew Aziz (fondateur de
   BBT) avec Carlo Zarattini** (ORB 5 min, VWAP, zone de bruit). L'utilisateur les a déjà, ou les a déjà testés.
3. **Beaucoup de « statistiques NQ » vendues (Edgeful, NQStats, indicateurs TradingView) ne sont que la géométrie d'une
   marche aléatoire.** Le tableau du §4 compare ces chiffres publiés au hasard simulé.
4. **Résultat académique récurrent et utile :** les niveaux connus (supports et résistances, nombres ronds, plus
   hauts et plus bas balayés) produisent plus souvent une **continuation** qu'un retournement après franchissement. Ce
   résultat va à l'inverse de la lecture ICT du « balayage de liquidité ». Sources : Osler 2005 pour les cascades de
   stops, Mahadzva 2026 pour les balayages en FX. Cette famille (suivre la cassure de niveaux) est déjà largement
   couverte par la machine évolutive.
5. **Règles réellement différentes de la liste « déjà testé » et testables avec des barres d'une minute :**
   - la règle des 80 % sur la value area TPO de la veille ;
   - le « Oops » de Larry Williams (ouverture au-delà de l'extrême de la veille, puis retour à l'intérieur) ;
   - la continuation après franchissement du plus haut ou du plus bas de la nuit (Globex), qui demande les CFD de
     5 minutes en 24 h/24 ;
   - en dernier, pour clore le débat, le « silver bullet » ICT.

   Aucune n'a de preuve solide. Ce sont des tests bon marché, avec une probabilité a priori faible.

## 2. Classement des règles (de la plus à la moins prometteuse)

Conventions : MNQ = 2 $ par point ; frais ≈ 3 $ l'aller-retour (≈ 1,5 point). Écart-type d'une séance RTH du NQ en
2023-2026 ≈ 1,1 à 1,3 % ≈ 200 à 300 points (ordre de grandeur, à recalculer sur les données).

### Règle 1 : « règle des 80 % » de Market Profile (value area TPO de la veille)

- **Règle standard (Dalton, *Mind Over Markets* ; origine : *Profile Reports*, Dalton Capital Management, 1987-1991) :**
  - **Profil de la veille.** TPO de la séance RTH, périodes de 30 minutes de 9 h 30 à 16 h (13 lettres). La value
    area (VA) contient 70 % des TPO, construite depuis le POC en s'étendant du côté qui a le plus de TPO. Sur la
    largeur, les sources hésitent entre 68 et 70 %.
  - **Condition d'ouverture.** Le jour J, l'ouverture RTH se fait hors de la VA de la veille, au-dessus de VAH ou
    sous VAL.
  - **Signal.** Le prix revient dans la VA et y est « accepté » pendant deux périodes de 30 minutes consécutives.
    Le sens de « dans la VA » varie : la période trade dans la VA, ou bien elle clôture dedans. Il faut fixer la
    définition avant le test.
  - **Entrée et objectif.** Entrée à la clôture de la 2e période. Objectif : le bord opposé de la VA.
  - **Stop.** Aucun stop canonique n'est publié. La variante la plus citée place le stop au-delà de l'extrême des
    périodes d'acceptation. Fixer ce choix a priori.
  - **Sortie.** Au plus tard à 15 h 55.
- **Données :** les TPO ne demandent que le plus haut et le plus bas de chaque tranche de 30 minutes. On les calcule
  donc **exactement** avec les barres d'une minute, sans volume par prix. La variante « volume profile » ne se calcule
  qu'en approximation, en répartissant le volume de chaque barre sur son range.
- **Preuves :**
  - Aucune étude auditée sur ES ou NQ.
  - Forums : taux de réalisation d'environ 60 à 62 % (backtest TradeStation sur NexusFi, sans taille d'échantillon ni
    frais), très sensible à la définition de « l'acceptation ». Le chiffre « 80 % » n'a jamais été mesuré
    publiquement.
  - **Base aléatoire (ma simulation, vol en U, gap de nuit ≈ 0,6 écart-type) :** VA médiane ≈ 0,71 écart-type du
    jour. Après le signal, le bord opposé est touché avant 16 h dans **44 à 47 %** des cas, sans aucun avantage.
  - Si le chiffre de 60 % des forums tenait sur NQ, ce serait un excès réel d'environ 13 à 16 points de
    pourcentage. C'est la seule statistique de la communauté trouvée qui ne se réduit pas immédiatement au hasard.
    Elle n'est pas vérifiée.
  - Indirectement : Yu, Rentzler et Wolf (2005, *Journal of Investment Management*) trouvent que, sur le future
    NASDAQ-100, le rendement de la nuit est surtout suivi de **retournements** en séance. Données anciennes, sans
    frais.
- **Mécanisme supposé :** retour vers la zone de prix « acceptée » la veille, c'est-à-dire le retournement d'un
  déséquilibre de la nuit que les participants de la séance ne valident pas.
- **Gain par trade :** objectif ≈ largeur de VA ≈ 140 à 200 points ≈ 280 à 400 $ par MNQ. Les frais (3 $) ne pèsent
  qu'environ 1 % ; ils ne sont pas le problème. La seule question est de savoir si le taux de succès dépasse la base
  aléatoire, stop compris. Fréquence simulée : un signal dans environ 25 à 35 % des séances, soit 60 à 90 par an.
- **Déjà couvert ?** Non. La machine a testé la clôture, le plus haut et le plus bas de la veille, ainsi que
  « retour au VWAP dans la zone ». La VA et la condition d'acceptation n'ont pas été testées. Le recoupement avec
  « comblement de gap » et Grant-Wolf-Yu (retournement après forte ouverture, négatif) reste partiel.
- **Jugement :** preuve **faible** (forums), mais c'est le meilleur candidat de cet angle. Comparer impérativement au
  taux de base, par exemple en recalculant la règle sur des jours permutés.

### Règle 2 : « Oops » de Larry Williams (ouverture au-delà de l'extrême de la veille, puis réintégration)

- **Règle standard (Williams, *Long-Term Secrets to Short-Term Trading*, 1999) :**
  - **Achat.** L'ouverture RTH se fait **sous le plus bas RTH de la veille**. Ordre d'achat stop au plus bas de la
    veille (+1 tick).
  - **Vente.** Cas symétrique : ouverture au-dessus du plus haut de la veille, vente stop à ce plus haut.
  - **Sortie.** À la clôture du jour, sans stop dans la version d'origine. Selon Rogue Quant, ajouter un stop
    dégrade le résultat sur presque tous les marchés.
- **Preuves :**
  - Rogue Quant (Substack) : PF 6,94 et 80 % de gagnants sur les achats S&P 500, sur un petit échantillon,
    apparemment sans frais (non vérifié).
  - The Chartist (Radge) : en échantillon 1987-1998 (les trades du livre), puis 17 ans hors échantillon. Résultats
    non lisibles ici.
  - Oxfordstrat : test sur 42 futures depuis 1980 (chiffres non lus).
  - Unger Academy : l'effet est moins pertinent sur les marchés quasi 24 h/24 (DAX).
  - Appui académique indirect : Fung, Mok et Lam (2000) et Grant, Wolf et Yu (2005) trouvent des retournements après
    de grosses variations à l'ouverture, mais quasi annulés par les coûts dans GWY. Yu, Rentzler et Wolf (2005) :
    retournement du rendement de la nuit sur NQ.
- **Mécanisme :** l'ouverture se fait sous un niveau évident, les vendeurs de la nuit sont piégés quand le prix
  repasse au-dessus, puis viennent les rachats à découvert. Variante « piège de stops » d'Osler, mais côté
  retournement.
- **Gain par trade :** détention jusqu'à la clôture, mouvement moyen de l'ordre de 0,3 à 0,5 écart-type du jour
  (≈ 60 à 150 points ≈ 120 à 300 $ par MNQ). Frais ≈ 1 à 2 %. Peu de trades : quelques dizaines par an et par côté.
  La puissance statistique sera faible.
- **Déjà couvert ?** Partiellement : les niveaux de la veille (suivre ou contrer) et GWY ont été testés. La
  combinaison précise « ouverture au-delà de l'extrême de la veille puis réintégration » n'apparaît pas dans la liste.
- **Jugement :** preuve **faible** (tests de blogs, souvent anciens, décroissance probable depuis la publication en
  1999). À tester tel quel, sans réglage.

### Règle 3 : franchissement du plus haut ou du plus bas de la nuit (Globex) puis continuation

C'est l'inverse du « liquidity sweep » ICT.

- **Règle :**
  - Calculer le plus haut et le plus bas de la séance de nuit (18 h - 9 h 30 heure de New York) avec les CFD NQ de
    5 minutes (HistData). Dans les barres RTH d'une minute du NQ, ces niveaux n'existent pas.
  - Pendant la séance RTH, premier franchissement d'un de ces niveaux : entrer **dans le sens** de la cassure.
  - Sortie à durée fixe ou à 15 h 55. La littérature ne donne pas de paramètre standard ; fixer un seul jeu de
    paramètres a priori.
- **Preuves :**
  - Mahadzva (2026, SSRN 7430998, *Smart Money or Costly Folklore?*). Six règles ICT/SMC codées mécaniquement,
    testées sur EURUSD, GBPUSD, AUDUSD et USDJPY en intrajournalier : walk-forward, bootstrap, permutation et
    échantillon réservé. Aucun soutien aux concepts « tels qu'enseignés ». Trois règles de balayage construites
    indépendamment concluent à la **continuation** dans 65 des 66 sélections. Prépublication, chiffres tirés du
    résumé.
  - Osler (2005, staff report NY Fed n° 150) : les tendances accélèrent quand le prix atteint les niveaux où les
    stops sont concentrés. L'effet est significatif pendant des heures, pas des jours.
  - La thèse de Lund sur les pivots en FX va dans le même sens : rien dans l'usage classique, mais un gain sur deux
    paires sur trois en usage **inversé**, donc en suivant la cassure. Thèse d'étudiant, preuve faible.
  - Aucune preuve directe sur le NQ.
- **Gain par trade :** mouvement de suivi de l'ordre de quelques dizaines de points, soit des frais de 3 à 10 %.
- **Déjà couvert ?** En grande partie. La machine a testé « suivre » sur le plus haut et le plus bas de la veille,
  le range d'ouverture et les nombres ronds. Les 526 stratégies de sessions ont couvert Asie, Londres et New York à
  l'échelle de la séance. Seul l'extrême **de la nuit** comme déclencheur intrajournalier semble nouveau.
- **Jugement :** preuve **faible** (FX, prépublication). Mécanisme crédible (cascades de stops), mais l'effet est
  probablement déjà capté par la zone de bruit, qui est elle-même un « suivi de cassure ».

### Règle 4 : comblement du gap d'ouverture (« gap fill »)

- **Règle standard :** si l'ouverture RTH ≠ la clôture RTH de la veille, entrer à l'ouverture vers la clôture de la
  veille. Objectif : la clôture de la veille (Edgeful propose aussi 50 % du gap). Sortie à 15 h 55 sinon.
- **Preuves :**
  - Edgeful, NQ, 6 derniers mois : gaps haussiers comblés ≈ 51 %, gaps baissiers ≈ 55 %. ES ≈ 63 à 64 %.
  - **Base aléatoire (formule exacte, marche aléatoire) :** probabilité de toucher un niveau situé à d écarts-types
    du jour = 2·(1−Φ(d)). Un gap de 0,25 écart-type donne 80 %, 0,5 donne 62 %, 0,75 donne 45 %. Les taux NQ
    publiés sont **compatibles avec le hasard**.
  - Plastun, Sibande, Gupta et Wohar (2020), indices américains 1928-2018 : le jour du gap, le prix va plutôt **dans
    le sens du gap**, contrairement au « mythe que les gaps se comblent ». Caporale et Plastun (2017) : pas
    d'anomalie hors FX.
- **Déjà couvert ?** Oui en substance : la clôture de la veille comme niveau, et GWY (négatif).
- **Jugement :** **aucune** preuve d'avantage net. Les « taux de comblement » sont du hasard présenté comme une
  statistique.

### Règle 5 : ICT « silver bullet » (10 h - 11 h) et fair value gaps (FVG)

- **Règle la plus standard (Huddleston, « ICT ») :**
  - Entre 10 h et 11 h (New York), attendre un balayage d'un plus haut ou d'un plus bas récent, puis un changement
    de structure.
  - Entrer en limite au bord du premier FVG formé dans le sens du retournement. Un FVG est une configuration de trois
    bougies dont la 1re et la 3e ne se recouvrent pas.
  - Stop au-delà de la bougie qui forme le FVG ; objectif à 2R, parfois TP2 à 3R.
- **Preuves :**
  - Aucune étude académique sur indices.
  - Projet GitHub de backtest mécanique « silver bullet » sur NQ en barres de 5 minutes, avec 10 $ de frais par
    trade : **PF 0,51 sur 27 trades**. Sur ES, PF 0,87 ; sur pétrole, 0,67. Échantillon minuscule, non vérifié.
  - Backtrex (éditeur de logiciel) : FVG sur Nasdaq (FVG en 1 h, déclencheur 15 min, filtre 4 h), PF 1,08 sur
    852 trades, +38 % en 10 ans contre +527 % pour l'achat-conservation.
  - Mahadzva 2026 : aucun soutien en FX. Le blog qui résume l'étude ajoute : dans une marche aléatoire simulée,
    83,4 % des FVG haussiers sont revisités en 20 barres, contre 83,5 % pour des niveaux aléatoires à la même
    distance. Le « FVG qui attire le prix » est donc un artefact.
  - Les « 65 à 75 % de gagnants » des sites de promotion ne donnent aucune méthode.
- **Gain par trade :** sur barres d'une minute, risque de 10 à 20 points (20 à 40 $), soit des frais de 8 à 15 % du
  risque.
- **Déjà couvert ?** Pas exactement : la famille « bougies » de la machine ne contient pas le FVG. Le balayage puis
  retournement correspond à « contrer » les plus hauts et bas récents, déjà négatif.
- **Jugement :** **marketing**. Les preuves disponibles sont négatives. Testable en une heure pour clore le sujet,
  rien de plus.

### Règle 6 : cassure de l'initial balance (IB, 9 h 30 - 10 h 30) et extensions

- **Règle standard (Market Profile) :** acheter le franchissement du plus haut de l'IB (vendre celui du plus bas),
  objectif 1,5× ou 2× l'IB, stop à l'autre bord ou au milieu de l'IB.
- **Preuves :**
  - Statistiques NQStats (environ 10 ans, non publiées) : un bord casse avant midi dans 83 % des cas, avant 16 h dans
    96 %. Si l'IB clôture dans sa moitié haute, le haut casse dans 82 % des cas ; moitié basse, le bas casse dans
    76 %.
  - Edgeful et Liquidity Finder : un seul bord cassé dans 76 à 84 % des cas (6 mois).
  - **Base aléatoire (ma simulation, vol en U) :** 91 % avant midi, 98 % avant 16 h, un seul bord dans 70 %. Haut
    cassé si clôture dans la moitié haute : 83 % ; bas cassé si moitié basse : 82 %. Les chiffres vendus sont
    **ceux du hasard**. Le NQ casse même un peu moins avant midi que le hasard (83 % contre 91 %), signe léger de
    contenance, pas de cassure exploitable.
  - Howard (2026, SSRN 6350238) : cassure de value area (« Setup 2 ») sur l'E-mini S&P, 6 284 événements,
    janvier 2025 - janvier 2026, données à la seconde. Moyenne **−2,2 ticks, non significative**. Tous les stops de
    prix testés dégradent le résultat. Les événements des 30 premières minutes sont nettement pires.
  - Firich (2012, WSEAS) affirme un avantage de l'IB, avec une méthodologie floue (contrats et horaires non
    précisés).
  - Un EA vendu sur MQL5 annonce PF 1,36 : marketing.
- **Déjà couvert ?** Oui : l'IB est un ORB de 60 minutes. Les ORB de 5, 15 et 30 minutes et l'ORB 30 publié sont
  négatifs.
- **Jugement :** **aucune** preuve d'avantage net.

### Règle 7 : bandes de VWAP (écarts-types) et VWAP de tendance

- **Retournement aux bandes :** vendre au contact de VWAP + 2σ (acheter à −2σ), objectif le VWAP.
  - Seul test trouvé : DAX, barres de 15 min, oct. 2016 - oct. 2026, 8 943 trades, **PF 0,64**, −98,6 %
    (Backtrex).
  - Aucune étude sur NQ. Les arguments du type « les contacts de 2σ l'après-midi sont plus fiables » (NexusFi) ne
    sont pas testés.
- **Tendance VWAP (Zarattini et Aziz 2023, « VWAP: The Holy Grail for Day Trading Systems ») :** long si le prix
  est au-dessus du VWAP, court en dessous, sur barres d'une minute de QQQ, 2018-2023.
  - Résultat publié : +671 % net de commissions, Sharpe 2,1.
  - Réplications QuantConnect contradictoires : un rapport montre −11,6 % par an, Sharpe −0,6, environ 12 trades
    par jour ; un autre +40 % par an. Les frais et l'exécution expliquent l'écart.
  - Les mêmes auteurs ont ensuite proposé la zone de bruit, une version améliorée que l'utilisateur a déjà.
- **Déjà couvert ?** Oui (distance au VWAP, retour au VWAP, zone de bruit avec stop VWAP).
- **Jugement :** **aucune** preuve pour les bandes. Pour la tendance VWAP, preuve faible et dominée par ce qui
  existe.

### Règle 8 : pivots de parquet (P = (H+B+C)/3, R1 = 2P−B, S1 = 2P−H, etc.)

- **Règle standard :** contrer le premier contact de R1 ou S1, objectif P. La variante « tendance » achète au-dessus
  de R1.
- **Preuves :**
  - Bulkowski (actions, barres d'une minute) : les pivots standard « fonctionnent » dans 51 à 60 % des cas, à peine
    mieux qu'une pièce.
  - Unger Academy : la version retournement perd sur toute la période. La version tendance donne une courbe plus
    lisse, mais un trade moyen trop petit pour couvrir frais et glissement.
  - Thèse de Lund (FX) : aucun soutien dans l'usage classique.
  - QuantInsti le reconnaît : il n'existe presque pas d'étude académique.
  - Le fond académique sur les supports et résistances est réel mais minuscule :
    - Osler (2000) : rebond sur les niveaux publiés par des banques ≈ 60,8 %, contre ≈ 56,2 % sur des niveaux
      arbitraires ;
    - Kavajecz et Odders-White (2004) : les niveaux coïncident avec la profondeur du carnet ;
    - Garzarelli et al. (2014), Chung et Bellotti (2021) : rebonds plus probables que des traversées.
  - Aucune de ces études ne démontre un gain après frais.
- **Déjà couvert ?** Pour l'essentiel (niveaux de la veille, nombres ronds d'Osler). Les niveaux R1/S1 eux-mêmes
  n'ont pas été testés, mais l'a priori est très faible.
- **Jugement :** **aucune** preuve.

### Règle 9 : order flow (footprint, absorption, imbalances empilées, divergence de delta)

- **Règles standard (communauté, Axia, Jigsaw, éditeurs) :**
  - **Imbalance :** une imbalance est un rapport achats agressifs / ventes agressives ≥ 3:1 en diagonale. Trois
    niveaux ou plus d'affilée forment une « imbalance empilée » : suivre le mouvement.
  - **Divergence de delta :** nouveau plus haut du prix sans nouveau plus haut du delta cumulé : contrer.
  - **Absorption :** gros volume agressif sans progression du prix : contrer.
- **Preuves :**
  - Aucun backtest public avec taille d'échantillon, frais ou hors échantillon. Les éditeurs affirment « 75 à 80 %
    de gagnants » sans méthode (FuturesHive). Même les praticiens écrivent que la divergence « n'est pas un signal »
    hors niveaux clés (NexusFi).
  - Côté académique, le déséquilibre de flux explique surtout le mouvement **simultané** (Cont, Kukanov et Stoikov
    2014). Sur l'E-mini, le lien flux-rendement est fort à la seconde (arXiv 2508.06788), mais le pouvoir prédictif
    décroît très vite.
  - Le seul résultat « net de frais » trouvé utilise le **flux d'options** des 10 premières minutes pour prédire le
    reste de la journée (KAIST). Cette donnée est absente ici.
  - Le test de l'utilisateur (6 mois à la seconde) a conclu que l'information de très court terme vaut moins qu'un
    aller-retour.
- **Données :** l'absorption demande le carnet (absent). Le footprint et le delta demandent le côté agresseur
  (6 mois seulement, aucun vrai hors échantillon possible).
- **Jugement :** **aucune** preuve, en partie **marketing**. Pas testable sérieusement avec les données disponibles.
  Déjà exploré pour la partie testable.

### Règle 10 : opening drive, first pullback, types d'ouverture de Dalton, setups SMB et Bear Bull Traders

- **Opening drive et types d'ouverture (Dalton).** Open-Drive, Open-Test-Drive, Open-Rejection-Reverse et
  Open-Auction sont des classifications qualitatives. Aucune étude de fréquence ou de rendement n'a été trouvée, à
  part un indicateur TradingView qui donne ses propres fréquences « sans valeur prédictive ».
- **First pullback (Raschke, Brooks).** Aucune preuve indépendante.
- **SMB « Fashionably Late » (fiche SMB, 2024).**
  - Règle : l'EMA 9 se retourne et croise un VWAP plat ou de pente opposée ; entrée immédiate. Le stop et
    l'objectif viennent d'un « mouvement mesuré » (du plus bas du jour au point de croisement, reporté depuis
    l'entrée).
  - Conçu pour les actions. Aucun backtest publié.
- **Bear Bull Traders (Aziz, *How to Day Trade for a Living*).** ABCD, bull flag, VWAP, moyennes mobiles,
  « red-to-green », ORB. Les seules versions testées formellement sont les articles Zarattini-Aziz : ORB 5 min,
  VWAP, zone de bruit, et l'ORB « stocks in play » sur actions, qui n'a pas d'équivalent sur le NQ.
- **Topstep.** Aucune méthode propriétaire vérifiée. Ses propres statistiques 2025 (auto-déclarées, non auditées) :
  16,8 % des Combines achevés ; 33,3 % des comptes financés touchent un paiement ; 0,71 % des participants
  atteignent un compte « Live ».
- **Déjà couvert ?** Oui pour la partie testable : momentum de k minutes, ORB, croisements VWAP et moyennes, séries
  de barres.
- **Jugement :** **aucune** preuve. Méthodes discrétionnaires sans définition mécanique standard.

### Règle 11 : statistiques descriptives vendues (naked POC, « London sweep », probabilités ALN)

- NQStats ALN, Edgeful, naked POC « magnet » : ce sont des fréquences historiques, sans comparaison au hasard, sans
  frais et sans hors échantillon. Pour les naked POC, même les éditeurs reconnaissent qu'il n'y a pas de chiffre
  ferme.
- **Jugement :** **marketing ou descriptif**. Ce ne sont pas des règles de trading.

## 3. Contexte académique général (pourquoi il faut être sceptique)

- **Marshall, Cahan et Cahan (2008), *Journal of Empirical Finance*.** 7 846 règles techniques intrajournalières
  (filtres, moyennes mobiles, supports et résistances, canaux, OBV) sur SPDR en barres de 5 minutes, 2002-2003.
  42 règles sont significatives à 1 % avant correction, **aucune** après correction de l'espionnage des données.
- **Schulmeister (2009).** 2 580 modèles techniques sur le S&P 500. En barres de 30 minutes : 8,8 % par an **brut**
  de 1983 à 2000, puis performance moindre de 2001 à 2007. En données quotidiennes, non rentables depuis le début des
  années 1990. Les avantages techniques s'érodent et migrent vers les hautes fréquences, puis disparaissent.
- **Park et Irwin (thèse, Illinois).** Les règles techniques sur futures américains ne sont pas rentables après
  correction de l'espionnage des données sur environ 20 ans.
- **Chague, De-Losso et Giovannetti (2019-2020), « Day Trading for a Living? ».** Mini-indice brésilien :
  97 % des day traders ayant persisté plus de 300 jours perdent de l'argent ; 1,1 % gagnent plus que le salaire
  minimum ; aucun apprentissage.
- **Barber, Lee, Liu et Odean (Taïwan).** Moins de 1 % des day traders sont rentables de façon prévisible après
  frais. Chiffre cité **de mémoire**, non revérifié dans cette session faute de quota.
- **Statistiques de prop firms (Topstep 2025, auto-déclarées).** Elles concordent : la grande majorité des
  utilisateurs de ces méthodes ne gagnent pas.

## 4. Taux de base du hasard contre « statistiques » vendues (mes simulations, à recalculer sur le vrai NQ)

| Statistique | Chiffre vendu (NQ) | Marche aléatoire (vol en U) | Lecture |
|---|---|---|---|
| Un bord de l'IB cassé avant midi | 83 % (NQStats) | 91 % | Hasard, voire moins de cassures que le hasard |
| Un bord de l'IB cassé avant 16 h | 96 % (NQStats) | 98 % | Hasard |
| Un seul bord de l'IB cassé | 76 à 84 % (Edgeful) | 70 % | Proche du hasard |
| Haut cassé si l'IB clôture dans sa moitié haute | 82 % (NQStats) | 83 % | Hasard |
| Gap comblé dans la séance | 51 à 55 % (Edgeful) | 45 à 80 % selon la taille du gap | Hasard |
| Revisite d'un FVG en 20 barres | « magnet » | 83,4 % pour un FVG, 83,5 % pour un niveau aléatoire (blog sur Mahadzva) | Artefact |
| Règle des 80 % : bord opposé atteint | « 80 % », forums 60 à 62 % | 44 à 47 % | **Seul écart possible**, à vérifier |

Scripts : `/tmp/claude-0/-home-user-scalping-telegram-bot/4861520c-7c70-542c-a1db-763e9dd91dac/scratchpad/agents/sim/rw_base.py`
et `/tmp/claude-0/-home-user-scalping-telegram-bot/4861520c-7c70-542c-a1db-763e9dd91dac/scratchpad/agents/sim/rw_80rule.py`.
Hypothèses : 390 minutes, volatilité 1,8× la 1re demi-heure, 1,4× la 2e et 1,3× la dernière demi-heure, gap de nuit
d'écart-type 0,6 fois celui du jour, bins de 0,5 minute-sigma. Ce sont des ordres de grandeur. Le bon test consiste à
recalculer la base sur les vraies données, par exemple par permutation des jours.

## 5. Protocole conseillé pour les règles 1 à 3 (et 5 pour clore)

1. Figer la règle exacte avant de regarder : définition de l'acceptation, stop et sortie à 15 h 55. Une seule
   variante, ou deux au maximum, déclarées à l'avance.
2. Échantillon d'apprentissage 2011-2022 sans optimisation ; hors échantillon 2023-2026. Frais de 3 $ par
   aller-retour MNQ, plus 1 tick de glissement supplémentaire sur les ordres stop.
3. Comparer le taux de succès et le P&L à une référence aléatoire : mêmes heures d'entrée et mêmes stops et objectifs
   sur des jours permutés, ou niveaux décalés aléatoirement (méthode d'Osler). Un taux de « réalisation » sans cette
   référence ne prouve rien.
4. Pour la règle 3, les extrêmes de la nuit viennent des CFD (HistData). Vérifier l'alignement horaire et l'écart de
   base CFD - future, ou ne garder que les niveaux relatifs.

## 6. Sources

- Mahadzva, S. (2026), *Smart Money or Costly Folklore? A Systematic Evaluation of ICT/Smart-Money-Concepts Trading
  Rules in G10 FX*, SSRN 7430998 : https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7430998
- Howard, T. (2026), *Stop Distance, Exit Methodology, and Signal Preservation in Intraday Value Area Breakouts:
  Evidence from E-mini S&P 500 Futures*, SSRN 6350238 : https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6350238
- NexusFi, règle des 80 % : https://nexusfi.com/a/concepts/80-percent-rule et https://nexusfi.com/showthread.php?p=910061
- Firich, J. (2012), *Futures Trading Based on Market Profile Day Timeframe Structures*, WSEAS :
  https://www.wseas.us/e-library/conferences/2012/Zlin/FAA/FAA-12.pdf
- Yu, Rentzler, Wolf (2005), *NASDAQ-100 Index Futures: Intraday Momentum or Reversal?*, JOIM :
  https://joim.com/article/nasdaq-100-index-futures-intraday-momentum-or-reversal/
- Grant, Wolf, Yu (2005), *Intraday price reversals in the US stock index futures market: A 15-year study*, JBF :
  https://ideas.repec.org/a/eee/jbfina/v29y2005i5p1311-1327.html
- Plastun, Sibande, Gupta, Wohar (2020), *Price gap anomaly in the US stock market: the whole story* :
  https://repository.up.ac.za/handle/2263/78336 ; Caporale et Plastun (2017) :
  https://bura.brunel.ac.uk/handle/2438/14372
- Edgeful, comblement de gap et IB : https://www.edgeful.com/blog/posts/half-gaps-vs-full-gaps ,
  https://www.edgeful.com/blog/posts/initial-balance-breakout-report ; revue Liquidity Finder :
  https://liquidityfinder.com/insight/technology/edgeful-review-for-futures-prop-firm-traders-150-reports-and-a-daily-process
- Statistiques IB de NQStats reprises dans un indicateur TradingView : https://in.tradingview.com/script/nKBYfMTA ;
  ALN : https://in.tradingview.com/script/KNTFWlm2-ALN-Sessions-NQ-Stats-x-CantoLab/
- Backtest silver bullet sur GitHub : https://github.com/cjosh4toyotas-stack/silver-bullet-backtest
- Backtrex, FVG Nasdaq et bandes de VWAP sur le DAX : https://backtrex.com/en/backtests/ict-fair-value-gap-nasdaq ,
  https://backtrex.com/en/backtests/vwap-band-fade-dax
- Zarattini et Aziz (2023), VWAP : https://concretumgroup.com/volume-weighted-average-price-vwap-the-holy-grail-for-day-trading-systems/ ;
  réplications QuantConnect : https://www.quantconnect.com/reports/2dd44a5c1394e0ba3de9c7f4d7dc0716 ,
  https://www.quantconnect.com/forum/discussion/16706
- Zarattini, Aziz, Barbon (2024), *Beat the Market* (zone de bruit), SSRN 4824172
- SMB, « Fashionably Late » : https://www.smbtraining.com/blog/wp-content/uploads/2024/04/The-Fashionably-Late-Scalp-Cheat-Sheet.pdf
- Oops : https://roguequant.substack.com/p/i-backtested-larry-williams-trading ,
  https://www.thechartist.com.au/the-oops-pattern-in-sample-out-of-sample/ ,
  https://oxfordstrat.com/trading-strategies/bull-oops-pattern/ , https://ungeracademy.com/?p=7737
- Pivots : https://thepatternsite.com/PivotPoints.html ,
  https://ungeracademy.com/blog/pivot-points-in-systematic-trading-a-test-to-see-when-they-do-not-work-part-2 ,
  https://blog.quantinsti.com/pivot-point-strategy/ , https://www.lunduniversity.lu.se/lup/publication/8979805
- Osler (2000), *Support for Resistance* : https://www.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.pdf ;
  Osler (2002/2005), *Stop-loss orders and price cascades* : https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf
- Kavajecz et Odders-White (2004), RFS : https://ideas.repec.org/a/oup/rfinst/v17y2004i4p1043-1071.html
- Chung et Bellotti (2021), arXiv 2101.07410 : https://ideas.repec.org/p/arx/papers/2101.07410.html ;
  Garzarelli et al. (2014), Sci. Rep. : https://www.arxiv.org/abs/1110.5197
- Marshall, Cahan, Cahan (2008), JEF, résumé CXO : https://www.cxoadvisory.com/?p=1253
- Schulmeister (2009) : https://www.wifo.ac.at/publication/111781/
- Park et Irwin, thèse Illinois : https://www.ideals.illinois.edu/items/84261
- Order flow : https://arxiv.org/pdf/2508.06788 ; flux d'options (KAIST) : https://dspace.kaist.ac.kr/handle/10203/292245 ;
  NexusFi footprint : https://nexusfi.com/a/strategies/advanced-footprint-chart-patterns ;
  https://www.futureshive.com/blog/footprint-charts-complete-guide-2025
- Chague, De-Losso, Giovannetti, *Day Trading for a Living?* : https://quantpedia.com/retail-day-trading-is-an-uphill-battle/
- Statistiques Topstep 2025 : https://fortunly.com/statistics/prop-firm-challenge-pass-rate-statistics/ ,
  https://tradecovex.com/guides/how-many-combines-passed-express-topstep-2025
- Types d'ouverture de Dalton (indicateur) : https://kr.tradingview.com/script/CERMLJMk-Open-Type-with-Measured-Outcomes/
