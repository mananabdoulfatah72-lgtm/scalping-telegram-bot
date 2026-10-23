# Étude large : tous les marchés futures, la zone combinée sur 15 ans, et les challenges 50K (règles fixées le 22 octobre 2026, avant tout calcul)

## Demande de l'utilisateur (21 octobre 2026)

- Partir du principe que le compte Bulenox actuel est perdu (486 $ de marge, `delta_mesures/`).
- Faire l'étude large proposée : combiner sur 15 ans ce qu'on sait déjà de la zone (heure, force de la cassure,
  volatilité, S&P 500), avec une vraie vérification sur des années que le modèle n'a pas vues.
- Tester tout ce qui est tradable en futures : actifs, produits, marchés. Tester d'autres études et variantes que la
  zone. Chercher une stratégie comme la zone, qui vienne la compenser, pour un plus gros avantage.
- Uniquement des données gratuites (`donnees_libres/`), rien de payant.
- Dire quelles stratégies et quels challenges 50K conviennent (Bulenox ou d'autres).
- Une contre-revue indépendante de tout le travail (#ultrareview), pour que le résultat ne soit pas faux.

## Ce qui est déjà fait (carte de la recherche, branche `claude/keen-babbage-r686cl`, `cerveau/savoir.json`)

Pas refait ici : zone sur NQ, ES, RTY, YM, GC, CL, 6E (`zone_multi/`) ; 75 stratégies intraday classiques sur NQ et ES
(tournois 1 à 4, dont Gao, Baltussen, OPR 5 minutes) ; 35 essais sur 5 autres marchés (tournoi 6) ; information
croisée entre 7 marchés (tournoi 7) ; 232 736 stratégies journalières sur 16 futures (machine 4) ; 526 stratégies de
sessions sur 8 marchés HistData (machine 5) ; 8 178 confluences sur la zone (vague 9) ; filtres delta, entrées en
retard, sortie au retour dans la zone (`delta_mesures/`, `zone_retour/`). Seuls la zone sur NQ, la règle « pas de zone
les jours de la Fed » et le RSI(2) de nuit ont survécu.

**Ce qui est nouveau ici :**
1. 22 marchés jamais testés en intraday, grâce aux ETF gratuits (Alpaca, 5 minutes, 2016 - 2026) : la courbe des taux
   (ZB, ZN, ZF, ZT), l'argent, le cuivre, le platine, le palladium, le Brent, le gaz, l'essence, 6 devises, le maïs, le
   soja, le blé, le bitcoin. Les 5 familles de A sur ces 22 marchés n'ont jamais été mesurées.
2. Un modèle qui combine les informations de la zone (et non des conditions prises une à une), vérifié en
   walk-forward : chaque année est prédite par un modèle qui ne l'a jamais vue.
3. Les mathématiques des challenges : quelle chance de valider, au mieux, même avec une très bonne stratégie, selon les
   règles de chaque firme.

## Partie A : 7 stratégies × 27 marchés (2016 - 2026, 5 minutes, séance 9 h 30 - 16 h de New York)

**Données** : `donnees_libres/etf_5min/` (Alpaca, flux SIP, ajusté des splits). Chaque ETF représente le future qu'il
suit (tableau dans `marches.py`). Les ETF ne couvrent que la séance américaine : toutes les stratégies de A sont
intraday, à plat à 16 h, comme l'exigent Bulenox, Topstep et les comptes « intraday ».

**Marchés** (27) : SPY→ES, QQQ→NQ, DIA→YM, IWM→RTY, TLT→ZB, IEF→ZN, IEI→ZF, SHY→ZT, GLD→GC, SLV→SI, CPER→HG,
PPLT→PL, PALL→PA, USO→CL, BNO→BZ, UNG→NG, UGA→RB, FXE→6E, FXY→6J, FXB→6B, FXA→6A, FXC→6C, FXF→6S, CORN→ZC,
SOYB→ZS, WEAT→ZW, BITO→BTC. UUP (dollar, ICE) et VXX (VIX, CFE) ne sont pas des produits CME : mesurés pour
information, hors décision.

**Frais** (par aller-retour, dans le prix du jour) : commission 1 $ par ordre sur un micro, 2,50 $ sur un contrat
standard, plus 1 tick de glissement à l'entrée et 1 à la sortie, sur le plus petit contrat CME du marché (`marches.py`).
Le niveau de prix du future vient de Yahoo (`donnees_libres/yahoo/jour/`, clôture de la veille).

**Stratégies** (paramètres des articles, aucun réglage) :

| Nom | Règle |
|---|---|
| **A1 zone** | Zone de bruit (Zarattini, Aziz et Barbon 2024), comme le bot : σ_m = moyenne sur les 14 séances complètes précédentes de \|clôture_m / ouverture − 1\| ; limites max(ouverture, veille) × (1 + σ_m) et min(ouverture, veille) × (1 − σ_m) ; contrôles de 10 h à 15 h 30 toutes les 30 minutes ; sortie à un contrôle si le prix repasse max(limite haute, VWAP) (achat) ou min(limite basse, VWAP) (vente) ; à plat à 16 h. |
| **A2a Gao** | Gao, Han, Li et Zhou (2018) : signe du rendement de la clôture de la veille à 10 h → position de 15 h 30 à 16 h. |
| **A2b Baltussen** | Baltussen, Da, Lammers et Martens (2021) : signe du rendement de la clôture de la veille à 15 h 30 → position de 15 h 30 à 16 h. |
| **A3a OPR 5 min** | Zarattini et Aziz (2023) : sens de la première barre de 5 minutes, entrée à 9 h 35, stop à l'autre extrême de la barre, objectif 10 fois le risque, à plat à 16 h. |
| **A3b OPR 30 min** | Cassure du plus haut ou du plus bas de 9 h 30 - 10 h (première cassure, une seule entrée, à la clôture de la barre qui casse), stop à l'autre extrême, à plat à 16 h. |
| **A4 périodicité** | Heston, Korajczyk et Sadka (2010) : pour chaque demi-heure de la séance, position du signe du rendement moyen de cette même demi-heure sur les 40 séances précédentes. |
| **A5 zone inversée** | Le complément naturel de la zone, qui perd sur les fausses cassures : mêmes signaux que A1, sens contraire ; sortie à un contrôle quand le prix revient au VWAP, stop à un contrôle si le prix s'écarte encore de σ_m depuis l'entrée, à plat à 16 h. |

**Mesure** : rendement net de chaque séance (0 sans trade), t de la moyenne. **Exploration** : 2016 - 2022.
**Coffre** : 2023 - 20 octobre 2026, ouvert une seule fois, après les décisions d'exploration.

**Survie (toutes les conditions) :**
1. exploration : t net ≥ 2,0, et retenu par Benjamini-Hochberg à 10 % sur les 189 essais décidables (p unilatéral) ;
2. coffre : t net ≥ 1,5, même sens.

**Contrôle de la méthode** : A1 sur QQQ doit ressembler à la zone du bot sur les minutes du NQ (corrélation des
séances 2016 - 2026 ≥ 0,6). Sinon, les 5 minutes des ETF sont jugées trop grossières pour les stratégies de type zone,
et A1 / A5 sont seulement descriptives.

## Partie C : un complément de la zone

Une survivante de A est retenue comme complément si :
1. corrélation de ses séances avec la zone du bot (NQ minute, 1 MNQ) < 0,3 sur 2016 - 2022 ;
2. zone + survivante, à risque égal (même écart-type quotidien sur 2016 - 2022), a un Sharpe plus haut que la zone
   seule sur le coffre.

Pour information : pour chacun des 189 essais, corrélation avec la zone et gain moyen les jours où la zone perd.

## Partie B : la zone combinée sur 15 ans, en walk-forward

**Trades** : zone du bot sans filtre sur le NQ (V1, minutes 2011 - 25 septembre 2026, dernier jour des minutes ES),
sans les jours d'annonce de la Fed (comme le bot). **Informations** au moment de l'entrée (rien d'après) :

| | Information |
|---|---|
| 1-3 | heure du contrôle : 10 h, 10 h 30 - 11 h 30, 12 h - 13 h 30, 14 h - 15 h 30 (3 indicatrices) |
| 4 | force de la cassure : (prix − limite) / (σ × référence), dans le sens du trade |
| 5 | volatilité : log(σ de 10 h / médiane de σ de 10 h sur les 252 séances précédentes) |
| 6 | S&P 500 : l'ES est aussi hors de sa propre zone, dans le même sens, au même contrôle (0 ou 1) |
| 7 | écart d'ouverture du NQ, dans le sens du trade, en σ de 10 h |
| 8 | tendance : rendement du NQ sur 20 séances, dans le sens du trade |
| 9 | VIX de la veille (log, Yahoo) |
| 10 | trade de la séance : premier trade du jour ou non (0 ou 1) |

**Modèle** : régression ridge (λ = nombre de trades d'apprentissage × 1,0, informations centrées réduites sur
l'apprentissage) du gain net du trade en multiples de σ × référence. **Walk-forward** : pour chaque année Y de 2016 à
2026, apprentissage sur tous les trades des années < Y (depuis 2011), puis on ne garde en Y que les trades prédits
positifs. Un trade écarté reste suivi « à blanc » jusqu'à sa sortie, comme le bot.

**Adoption (toutes les conditions)** sur 2016 - 2026, hors échantillon :
1. t de la différence quotidienne (gardés − tous) ≥ 2,0 ;
2. différence positive sur 2016 - 2022 et sur 2023 - 2026 ;
3. au moins 50 % des trades gardés.

## Partie D : les challenges 50K

**Règles supposées** (sites d'avis d'octobre 2026, les pages officielles ne répondent pas depuis la machine : à
confirmer au panier ou par écrit) :

| Compte | Prix | Objectif | Perte max (fin de journée) | Limite du jour | Délai | Meilleur jour | Bots |
|---|---|---|---|---|---|---|---|
| Bulenox Legacy 50K, option 2 | ≈ 19 $ avec code, 148 $ d'activation | 3 000 $ | 2 500 $, bloquée à +100 $ | 1 100 $ (arrête la journée) | 30 jours (22 séances) | — | permis |
| Topstep 50K Combine | 49 $ par mois, 149 $ d'activation | 3 000 $ | 2 000 $, bloquée au départ | 1 000 $ (arrête la journée) | aucun | < 50 % | Combine oui |
| Tradeify Select 50K | ≈ 159 $ | 3 000 $ | 2 000 $, bloquée à +100 $ | — | aucun | ≤ 40 % | sous conditions |
| Lucid Flex 50K | paiement unique | 3 000 $ | 2 000 $, bloquée à +100 $ | — | aucun | ≤ 50 % | permis |
| MyFundedFutures 50K | abonnement de 30 jours | 3 000 $ | 2 000 $, bloquée à +100 $ | — | aucun | ≤ 50 % | permis, supervisé |
| Phidias Fundamental 50K | ≈ 116 $, 149 $ d'activation | 4 000 $ | 2 500 $, bloquée à +100 $ | — | aucun | — | ? |
| Apex 50K EOD | — | 3 000 $ | 2 000 $ | 1 000 $ | 30 jours | — | **interdit** au compte financé |
| Take Profit Trader 50K | ≈ 150 $ par mois | 3 000 $ | 2 000 $ | — | aucun | < 50 % | **interdit** |
| Alpha Futures Advanced 50K | 139 $ par mois | 4 000 $ | 1 750 $ | — | aucun | 50 % | **interdit** |

Apex, Take Profit Trader et Alpha Futures interdisent les bots (au moins au compte financé) : ils ne conviennent pas
au bot et ne sont pas simulés. Le plancher est le plus haut de fin de journée moins la perte max ; il est touché si le
compte passe dessous **pendant** la séance. Sans délai, le challenge est suivi au plus 126 séances (6 mois).

**D1, le plafond** : séances tirées au hasard, loi normale, Sharpe annuel 0, 1, 2 et 3 ; pour chaque compte et chaque
Sharpe, l'écart-type quotidien (100 à 1 500 $) qui maximise la chance de valider. Cela dit ce que la meilleure
stratégie possible peut espérer de chaque compte.

**D2, le bot réel** : la zone du bot (sans filtre, pas de zone les jours de la Fed), minute par minute sur le NQ
2012 - 2026, au niveau de prix d'aujourd'hui (20 octobre 2026), 1,5 point de frais par aller-retour. Chaque séance
donne son gain, son point le plus bas et son point le plus haut. Taille de 1 à 10 MNQ, avec arrêt dès que l'objectif
est atteint dans la séance. Pour Bulenox, aussi la version 30 jours actuelle (4 MNQ, 6 MNQ les 5 dernières séances).
Départ à chaque séance. **Choix** de la taille sur les départs 2012 - 2021 (la plus haute chance de valider avec au plus
35 % de challenges perdus), **vérification** sur les départs 2023 - 2026.

**Classement** des comptes sur la vérification : coût moyen d'un challenge validé = (prix + abonnements des mois
utilisés) ÷ part validée. La phase financée (retraits) n'est pas simulée ici (voir vagues 5 à 13).

**Contrôle** : pour Bulenox, la version 30 jours doit redonner à ±5 points la part validée du moteur exact de la
vague 13 (53 % sur les achats 2012 - 2021, 55 % sur 2023 - 2026).

## Limites écrites d'avance

- Les ETF ne sont pas les futures : même sens et même séance, mais les ETF de matières premières (USO, UNG, CORN…)
  suivent moins bien que ceux des indices et des taux. Un résultat de A sur un ETF devrait être revérifié sur le
  future avant d'y risquer de l'argent.
- Les années 2016 - 2026 du NQ ont déjà servi à toute la recherche : pour la zone, aucune année n'est vraiment neuve.
  Le walk-forward empêche le modèle de voir l'année qu'il prédit, mais les 10 informations ont été choisies par une
  recherche qui, elle, a vu ces années.
- Les règles des firmes viennent de sites tiers et changent souvent.
- Exécution à la clôture de la barre qui décide : légèrement optimiste, le glissement compté (1 tick) peut ne pas
  suffire dans un mouvement rapide.

## Fichiers

- `marches.py` : les 29 marchés, contrats et frais.
- `partie_a.py` → `resultats_a.txt`, `essais_a.csv` (parties A et C).
- `partie_b.py` → `resultats_b.txt`.
- `partie_d.py` → `resultats_d.txt`.
- `crypto/` : la vague bitcoin, lancée après ces résultats (protocole et décision fixés avant ses données).

## Résultats (22 octobre 2026)

### Contre-revue indépendante (#ultrareview)

Un relecteur indépendant a repris le code et les chiffres. Il a **recalculé de son côté** 8 essais de A (identiques au
centième), les chemins minute par minute de D (écart 2e-13) et le moteur des challenges (identique). **Aucun regard
vers le futur, rien qui puisse créer ou cacher une survivante.** Il a trouvé des défauts, tous corrigés avant ces
résultats :
- **D** : le moteur ne lisait que les clôtures des minutes (le README annonçait les plus hauts et plus bas) et Bulenox
  était limité à 22 séances au lieu de 30 jours calendaires (21 séances en médiane). Les deux rendaient Bulenox environ
  5 points trop favorable. Corrigé.
- **D** : Tradeify était compté 159 $ par mois ; le README dit 159 $. Corrigé (une fois).
- **D** : le « plafond » de D1 s'arrêtait à 1 500 $ d'écart-type ; sans avantage, la chance de valider Bulenox monte
  encore au-delà. Grille élargie à 5 000 $, 78 pas par séance au lieu de 26.
- **D** : le contrôle fixé citait 53 % / 55 % pour la vague 13 ; ces chiffres comprennent le **filtre delta simulé**.
  La référence comparable sans filtre est 49 % (achats 2023 - 2026). Les deux sont donnés dans `resultats_d.txt`.
- **A** : les demi-séances n'étaient pas exclues (Alpaca garde des transactions après 13 h) ; le prix négatif du
  pétrole du 20 avril 2020 donnait des frais négatifs. Corrigés. Les grains ferment à 14 h 20 et les ETF peu échangés
  ont des prix figés : leurs chiffres avant frais ne sont pas des pistes (note dans `resultats_a.txt`).
- **B** : la veille et la tendance utilisaient l'ancien contrat le lendemain d'un changement d'échéance. Corrigé.

Aucune de ces corrections ne change une décision.

### A : 0 survivante sur 189

- **Contrôle** : la zone recalculée sur QQQ en 5 minutes suit celle du bot sur les minutes du NQ (corrélation 0,88) :
  la méthode est acceptée.
- **Aucun des 189 essais ne passe l'exploration** (t ≥ 2 et Benjamini-Hochberg à 10 %). Le seul t ≥ 2 est la zone
  sur QQQ (+2,12, puis +2,57 au coffre), c'est-à-dire le bot lui-même ; seul parmi 189, il ne passe pas la correction
  pour essais multiples (il faudrait t ≥ 3,27).
- Après frais, presque tout est négatif : sur les taux, les devises, les grains et le gaz, le mouvement d'une
  demi-heure est à peine plus grand que les frais du plus petit contrat CME (médiane des t de −5 à −18 selon la
  stratégie).
- **Avant frais, quelques phénomènes connus existent** : l'élan de fin de séance sur les obligations longues (A2b TLT,
  t +3,2 puis +2,6) et sur l'or (+2,3 puis +3,0), comme dans Baltussen et al. (2021). Les frais du ZB et du MGC les
  dépassent.
- **Le plus proche du seuil après frais** : la cassure des 30 premières minutes sur le bitcoin (A3b BITO → MBT), t net
  +1,64 puis +1,87. Il est étudié à part, sur des années jamais vues (`crypto/`).

### C : pas de complément

Aucune survivante. Pour information, la zone inversée gagne bien les jours où la zone perd (+26 pb sur QQQ), mais elle
perd au total (t −5,6) : c'est le miroir de la zone, pas un complément.

### B : la zone combinée sur 15 ans n'est pas adoptée

Hors échantillon 2016 - 2026 (chaque année prédite par un modèle qui ne l'a pas vue) :

| | t | 2016-2022 | 2023-2026 | $ pour 1 MNQ au prix d'aujourd'hui |
|---|---|---|---|---|
| Tous les trades (le bot sans filtre) | **+3,05** | +2,29 | +2,06 | **+48 427 $** |
| Trades gardés par le modèle (43 %) | +2,60 | +2,38 | +1,13 | +29 855 $ |
| Trades écartés (57 %) | | | | +18 573 $ |

Les trois conditions échouent (t de la différence −1,59 ; différence négative sur les deux périodes ; 43 % gardés).
Le modèle écarte surtout des trades gagnants. La seule information stable sur les deux périodes est l'écart
d'ouverture dans le sens du trade (corrélation +0,08 puis +0,06 avec le résultat) : bien trop faible pour filtrer.

### D : ce que les règles de chaque challenge laissent à un avantage

**D1, séances tirées au hasard** : la meilleure chance de valider, pour la meilleure prise de risque, selon la
qualité de la stratégie (Sharpe annuel). Validé / perdu :

| Compte | Sans avantage (Sharpe 0) | Sharpe 1 (≈ le bot) | Sharpe 2 | Sharpe 3 |
|---|---|---|---|---|
| **Bulenox 50K (30 jours)** | **50 % / 50 %** | 52 % / 48 % | 55 % / 45 % | 61 % / 35 % |
| Topstep 50K | 28 % / 72 % | 43 % / 55 % | 63 % / 36 % | 83 % / 8 % |
| Lucid Flex 50K | 27 % / 73 % | 43 % / 56 % | 63 % / 37 % | 82 % / 8 % |
| Tradeify Select 50K | 25 % / 75 % | 43 % / 56 % | 63 % / 37 % | 82 % / 8 % |
| MyFundedFutures 50K | 27 % / 73 % | 43 % / 56 % | 63 % / 37 % | 82 % / 8 % |
| Phidias Fundamental 50K | 40 % / 60 % | 42 % / 58 % | 63 % / 28 % | 82 % / 14 % |

**Chez Bulenox, l'avantage ne compte presque pas.** Avec 30 jours, la meilleure façon de valider est de prendre
beaucoup de risque, et une stratégie sans aucun avantage valide déjà une fois sur deux. Même un avantage exceptionnel
(Sharpe 3, trois fois le bot) ne ferait que 61 %. **Sans limite de temps, c'est l'inverse** : sans avantage on ne
valide qu'une fois sur quatre, et chaque point de Sharpe ajoute environ 20 points de challenges validés.

**D2, le bot réel** (zone sans filtre, pas de zone les jours de la Fed, 2012 - 2026, au prix d'aujourd'hui : Sharpe
1,14, 287 $ d'écart-type par jour pour 1 MNQ). Taille choisie sur les départs 2012 - 2021 (la plus haute chance de
valider avec au plus 35 % de perdus), jugée sur 2023 - 2026 :

| Compte | Taille | Validé | Perdu | Séances (médiane) | Coût par validation | Validé selon l'année de départ (2023 / 24 / 25 / 26) | Bots |
|---|---|---|---|---|---|---|---|
| Bulenox 50K | 3 MNQ | 45 % | 31 % | 10 | **191 $** | 61 / 44 / 32 / 41 % | permis |
| Bulenox 50K, version 30 jours | 4 → 6 MNQ | 50 % | 45 % | 7 | 187 $ | | permis |
| **Lucid Flex 50K** | **1 MNQ** | **55 %** | 35 % | 68 | **256 $** | 80 / 59 / 16 / 83 % | permis |
| Phidias Fundamental 50K | 1 MNQ | 46 % | **20 %** | 72 | 401 $ | 60 / 50 / 27 / 50 % | ? |
| Tradeify Select 50K | 1 MNQ | 36 % | 35 % | 59 | 441 $ | 80 / 35 / 0 / 10 % | sous conditions |
| Topstep 50K | 1 MNQ | 48 % | 41 % | 66 | 534 $ | 73 / 53 / 8 / 83 % | Combine seulement |
| MyFundedFutures 50K | 1 MNQ | 55 % | 35 % | 68 | 856 $ | 80 / 59 / 16 / 83 % | permis, supervisé |

- **Contrôle** : la version 30 jours de Bulenox valide 50 % sur 2023 - 2026, comme le moteur exact de la vague 13 sans
  filtre (49 %). Le contrôle écrit dans le README (53 % / 55 %) échoue, mais il citait par erreur les chiffres avec le
  filtre simulé.
- **Le bot chez Bulenox ne fait pas mieux que le hasard** (45 à 50 % contre 50 % sans avantage). Bulenox arrive
  premier sur le coût seulement parce qu'il est très peu cher (19 $ + 148 $ d'activation).
- **Chez Lucid Flex, le bot double sa chance par rapport au hasard** (55 % contre 27 %), avec 1 MNQ seulement, mais il
  lui faut environ 3 mois (68 séances).
- **Les années comptent énormément** : un challenge commencé en 2025 ne validait que 16 % du temps chez Lucid, 32 %
  chez Bulenox. Un écart de moins de 10 points entre deux comptes n'est pas significatif.
- Prix de Lucid (140 $ une fois) et de MyFundedFutures (125 $ par mois) : hypothèses à vérifier. La phase financée
  (retraits) n'est pas simulée ici (vagues 5 à 13).

## Verdict

1. **Aucune nouvelle source d'avantage** sur 22 nouveaux marchés et 7 familles de stratégies (189 essais), aucun
   modèle qui améliore la zone sur 15 ans, aucun complément. La zone du NQ reste la seule source qui tienne, et elle
   tient bien : t +3,05 hors échantillon sur 2016 - 2026.
2. **Ce n'est pas le bot qui fait perdre les challenges Bulenox, ce sont leurs 30 jours** : à ce délai, n'importe
   quelle stratégie valide environ une fois sur deux. Perdre un challenge sur deux y est normal, et aucun filtre ne
   peut le changer.
3. **Les challenges qui conviennent au bot** : ceux **sans limite de temps**, à perte max de fin de journée, qui
   permettent les bots. C'est là que l'avantage du bot compte. Lucid Flex 50K, en 1 MNQ, valide 55 % des challenges
   (contre 27 % au hasard) pour environ 256 $ par validation, mais met environ 3 mois. Bulenox reste le moins cher par
   validation, mais c'est un pile ou face. Apex, Take Profit Trader et Alpha Futures interdisent les bots.
4. **À confirmer par écrit avant tout achat** : bots permis (au challenge **et** au compte financé), délai, prix, règle
   du meilleur jour.

## Vagues suivantes (22 octobre 2026), chacune avec ses règles fixées avant ses données

| Vague | Idée | Résultat |
|---|---|---|
| `crypto/` | La cassure des 30 minutes du bitcoin (la plus proche du seuil en A), confirmée sur 2017 - 2021 jamais vu, puis réglée en walk-forward (24 variantes) | **Non confirmée** (t +0,70 sur les années jamais vues ; walk-forward +0,73). Vrai élan avant frais à l'ouverture américaine (BTC et ETH, absent aux autres heures), mangé par les frais du MBT et absent en 2025 - 2026 |
| `bruit/` | Le complément de la zone : retour au VWAP à l'intérieur de la zone, stop sur sa limite (NQ, ES, 3 seuils) | **0 sur 6.** Rien à gagner avant frais à l'intérieur de la zone : c'est bien du bruit |
| `annonces/` | Les annonces de 8 h 30, repérées par le saut du dollar : pas de zone, ou 2 MNQ, ces jours-là | **Aucune règle retenue** (placebos battus à 68 % et 23 %, il fallait 95 %) |
| `pistes/` | 5 pistes choisies par 3 chercheurs et un juge (17 tests) : sortie au VWAP, heure de 16 h, renfort, or à Londres, zones décalées | **Aucune ne passe tout.** Le renfort (1 MNQ de plus quand le trade tient) passe la correction pour 17 tests, le coffre et les placebos, mais fait baisser la réussite des challenges (comme une taille plus grande). La sortie au VWAP du bot réel ne change rien : les backtests restent valables |
| `taille/` | La taille selon l'état du compte, calculée par programmation dynamique | **Non retenue.** Bulenox : +2,2 points (52 % contre 50 %), sous le seuil de 3 ; plafond confirmé. Lucid : moins bien que 1 MNQ fixe, car les pertes de la zone viennent en séries |
| `phenomenes/` | 4 pistes récentes ou peu connues, 11 tests : soirs de résultats des grandes valeurs, confirmation par les autres marchés (VIX, AUD/JPY, taux, dollar, bitcoin), nombres ronds du NQ, forme de la cassure | **Aucun test retenu.** L'idée inversée née de l'exploration (cassures que l'AUD/JPY ne confirme pas) est rejetée par le coffre (t +0,12) |
| `volatilite/` | Page 3D : la courbe des volatilités implicites du S&P 500 (VIX9D, VIX, VIX3M) depuis 2011, la prime de volatilité, et la zone selon le régime de volatilité de la veille | **Description, pas un test.** Contango 93 % des semaines ; VIX au-dessus de la volatilité réalisée du mois suivant de 3,4 points (83 % du temps) ; lien zone / VIX instable entre 2012 - 2022 et 2023 - 2026 |

Ces trois vagues confirment le verdict : la zone du NQ, sans les jours de la Fed, reste la seule source d'avantage qui
tienne. Ce qui change vraiment les chances, c'est le compte choisi (point 3 du verdict), pas un filtre de plus.
